import os
from langchain_openai import AzureChatOpenAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from .retriever import get_retriever

def get_chain():
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.2
    )
    prompt = PromptTemplate(
        template="""Olet energia-alan asiantuntija. Vastaa kysymykseen alla olevan kontekstin perusteella.
Jos vastaus ei löydy kontekstista, sano selkeästi että tieto ei löydy dokumenteista.
Mainitse aina mistä dokumentista tieto löytyy.

Konteksti:
{context}

Kysymys: {question}

Vastaus:""",
        input_variables=["context", "question"]
    )
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=get_retriever(),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )