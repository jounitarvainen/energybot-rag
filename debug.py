import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

db = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)

# Montako dokumenttia indeksissä?
count = db._collection.count()
print(f"Chunkkeja ChromaDB:ssä: {count}")

# Löytyykö relevantteja chunkkeja?
kysymys = "kaukolämmön kokonaistuotanto 2024"
tulokset = db.similarity_search(kysymys, k=4)
print(f"\nHaulla '{kysymys}' löytyi {len(tulokset)} chunkkia:\n")
for i, doc in enumerate(tulokset):
    print(f"--- Chunk {i+1} ---")
    print(f"Lähde: {doc.metadata.get('source')} sivu {doc.metadata.get('page')}")
    print(f"Teksti: {doc.page_content[:200]}")
    print()

# Tulostetaan mitä GPT-4o tarkalleen saa kontekstiksi
print("=== KOKO KONTEKSTI JOKA MENEE GPT-4O:LLE ===\n")
for i, doc in enumerate(tulokset):
    print(f"[Chunk {i+1} - {doc.metadata.get('source')} s.{doc.metadata.get('page')}]")
    print(doc.page_content)
    print()