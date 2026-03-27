import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import streamlit as st

load_dotenv()

@st.cache_resource
def load_qa_chain():
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), 
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")
    )
    db = Chroma(
        collection_name="energybot_docs",
        embedding_function=embeddings,
        persist_directory="chroma_db"
    )
    retriever = db.as_retriever(search_kwargs={"k": 3})
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.2
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
        chain_type_kwargs={"prompt": prompt},
    )
    return chain

st.title("EnergyBot - Kysy energia-alan dokumenteista")
st.caption("Kysy suomalaisista energia-alan dokumenteista. EnergyBot hakee vastaukset dokumenteista, eikä keksi tietoa itse.")

st.info("**Esimerkkikysymyksiä:**\n"
        "- Mikä iku Suomen kaukoälämmön kokonaistuotanto vuonna 2024?\n"
        "- Miten Fingridin palkintäjärjestelmä toimii?\n" \
        "- Mikä on sähkönkulutuksen trendi Suomessa?")

question = st.text_input("Kirjoita kysymyksesi tähän:")

if question:
    with st.spinner("Hakee vastausta dokumenteista..."):
        chain = load_qa_chain()
        result = chain.invoke({"query": question})
        st.markdown("### Vastaus dokumenteista:")
        st.write(result["result"])
        st.markdown("### Lähteet:") 
        sources = set()
        for doc in result["source_documents"]:
            source = doc.metadata.get("source", "Tuntematon lähde")
            page = doc.metadata.get("page", "Tuntematon sivu")
            sources.add(f"{source} (sivu {page})")
        for source in sources:
            st.write(f"- {source}")