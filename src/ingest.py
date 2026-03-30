import os
import fitz
import time
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_classic.schema import Document
from rag.embeddings import get_embeddings

load_dotenv()

def download_blobs(local_dir="temp_docs"):
    os.makedirs(local_dir, exist_ok=True)
    client = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))
    container_client = client.get_container_client(os.getenv("AZURE_STORAGE_CONTAINER_NAME"))
    blobs = list(container_client.list_blobs())
    for blob in blobs:
        path = os.path.join(local_dir, blob.name)
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

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)
    print(f"\nYhteensä {len(chunks)} chunkkia indeksoitavana")
    return chunks

def build_index(chunks):
    embeddings = get_embeddings()

    batch_size = 50
    print("\nBuilding index {len(chunks)} chunk in batches of {batch_size}...")
    db = None
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"  Processing batch {i//batch_size + 1} ({len(batch)} chunkkia)...")
        if db is None:
            db = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory="chroma_db"
            )
        else:
            db.add_documents(batch)
        time.sleep(3)  # Vältä nopeaa peräkkäistä API-kutsua

    print("Index built successfully. Pesisted to chroma_db directory.")
    return db
    
if __name__ == "__main__":
    print("Starting document indexing...")
    local_dir = download_blobs()
    chunks = load_and_split(local_dir)
    build_index(chunks)
    print("Document indexing completed.")