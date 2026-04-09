import os
import fitz
import time
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.schema import Document
from rag.embeddings import get_embeddings

load_dotenv()

def download_blobs(local_dir="temp_docs"):
    os.makedirs(local_dir, exist_ok=True)
    client = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))
    container_client = client.get_container_client(os.getenv("AZURE_STORAGE_CONTAINER_NAME"))
    blobs = list(container_client.list_blobs())
    for blob in blobs:
        if not blob.name.endswith(".pdf"):
            continue
        path = os.path.join(local_dir, os.path.basename(blob.name))
        with open(path, "wb") as f:
            f.write(container_client.download_blob(blob).readall())
        print(f"  Downloaded {blob.name} to {path}")
    return local_dir

def load_and_split(local_dir):
    documents = []
    for filename in os.listdir(local_dir):
        if filename.endswith(".pdf"):
            path = os.path.join(local_dir, filename)
            doc = fitz.open(path)
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    documents.append(Document(
                        page_content=text,
                        metadata={"source": filename, "page": page_num + 1}
                    ))
            print(f"  Purettu: {filename} ({len(doc)} sivua)")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    print(f"\nYhteensä {len(chunks)} chunkkia indeksoitavana")
    return chunks

def build_index(chunks):
    embeddings = get_embeddings()
    batch_size = 50
    print(f"\nIndeksoidaan {len(chunks)} chunkkia erissä ({batch_size} kerrallaan)...")

    db = None
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"  Erä {i//batch_size + 1}/{-(-len(chunks)//batch_size)}: chunkit {i+1}–{min(i+batch_size, len(chunks))}")
        if db is None:
            db = AzureSearch.from_documents(
                documents=batch,
                embedding=embeddings,
                azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
                azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
                index_name=os.getenv("AZURE_SEARCH_INDEX_NAME")
            )
        else:
            db.add_documents(batch)
        time.sleep(2)

    print("Indeksi valmis.")

if __name__ == "__main__":
    print("Starting document indexing...")
    local_dir = download_blobs()
    chunks = load_and_split(local_dir)
    build_index(chunks)
    print("Document indexing completed.")