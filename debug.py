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
kysymys = "paikallinen sähköntuotanto reservimarkkinat"
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

from langchain_openai import AzureChatOpenAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0
)

prompt_template = """Olet energia-alan asiantuntija. Vastaa kysymykseen alla olevan kontekstin perusteella.
Jos vastaus ei löydy kontekstista, sano selkeästi että tieto ei löydy dokumenteista.
Mainitse aina mistä dokumentista tieto löytyy.

Konteksti:
{context}

Kysymys: {question}

Vastaus:"""

prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=db.as_retriever(search_kwargs={"k": 4}),
    return_source_documents=True,
    chain_type_kwargs={"prompt": prompt}
)

tulos = chain.invoke({"query": "Miten paikallinen sähköntuotanto vaikuttaa reservimarkkinoihin?"})
print("\n=== GPT-4O VASTAUS ===")
print(tulos["result"])