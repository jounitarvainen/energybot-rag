import os
import logging
import fitz
import azure.functions as func
import time
import base64
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile
)
from azure.core.credentials import AzureKeyCredential
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.schema import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_classic.vectorstores import AzureSearch
from azure.data.tables import TableServiceClient, TableEntity

app = func.FunctionApp()

def get_embeddings():
    return AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")
    )

def get_stored_etag(filename):
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    table_client = TableServiceClient.from_connection_string(connection_string).get_table_client("etagcache")
    try:
        entity = table_client.get_entity(partition_key="energybot", row_key=filename)
        return entity["etag"]
    except Exception:
        return None

def store_etag(filename, etag):
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    table_client = TableServiceClient.from_connection_string(connection_string).get_table_client("etagcache")
    entity = {
        "PartitionKey": "energybot",
        "RowKey": filename,
        "etag": etag
    }
    table_client.upsert_entity(entity=entity)

def extract_chunks(blob_data, filename):
    doc = fitz.open(stream=blob_data, filetype="pdf")
    documents = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            documents.append(Document(
                page_content=text,
                metadata={"source": filename, "page": page_num + 1}
            ))
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(documents)

def update_index(chunks, filename):
    embeddings = get_embeddings()
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

    # Lisätään uudet chunkit
    batch_size = 50
    db = None
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        if db is None:
            db = AzureSearch.from_documents(
                documents=batch,
                embedding=embeddings,
                azure_search_endpoint=endpoint,
                azure_search_key=key,
                index_name=index_name
            )
        else:
            db.add_documents(batch)
        logging.info(f"Indeksoitu erä {i//batch_size + 1}/{-(-len(chunks)//batch_size)}")
        time.sleep(2)

    logging.info(f"Lisätty {len(chunks)} uutta chunkia: {filename}")
    
@app.blob_trigger(
    arg_name="myblob",
    path="documents/hot-folder/{name}",
    connection="AzureWebJobsStorage"
)
def blob_trigger(myblob: func.InputStream):
    blob_name = myblob.name.split("hot-folder/")[-1]
    logging.info(f"Blob trigger käynnistyi: {blob_name}")

    if not blob_name.endswith(".pdf"):
        logging.info(f"Ohitetaan ei-PDF tiedosto: {blob_name}")
        return

    # ETag-tarkistus
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    blob_service = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service.get_blob_client(container="documents", blob=f"hot-folder/{blob_name}")
    current_etag = blob_client.get_blob_properties().etag
    stored_etag = get_stored_etag(blob_name)

    if current_etag == stored_etag:
        logging.info(f"Tiedosto ei muuttunut, ohitetaan: {blob_name}")
        return

    logging.info(f"Uusi tai muuttunut tiedosto, indeksoidaan: {blob_name}")

    # Indeksoidaan
    blob_data = myblob.read()
    chunks = extract_chunks(blob_data, blob_name)
    logging.info(f"Purettu {len(chunks)} chunkia: {blob_name}")
    update_index(chunks, blob_name)
    logging.info(f"Indeksi päivitetty: {blob_name}")

    # Tallennetaan uusi ETag
    store_etag(blob_name, current_etag)
    logging.info(f"ETag tallennettu: {blob_name}")

    # Siirretään processed-kansioon ja poistetaan hot-folderista
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    client = BlobServiceClient.from_connection_string(connection_string)
    container_client = client.get_container_client("documents")

    source_blob = container_client.get_blob_client(f"hot-folder/{blob_name}")
    target_blob = container_client.get_blob_client(f"processed/{blob_name}")
    target_blob.start_copy_from_url(source_blob.url)
    logging.info(f"Kopioitu processed-kansioon: {blob_name}")

    source_blob.delete_blob()
    logging.info(f"Poistettu hot-folderista: {blob_name}")