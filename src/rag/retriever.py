from langchain_chroma import Chroma
from .embeddings import get_embeddings

def get_retriever(persist_directory="chroma_db", k=4):
    embeddings = get_embeddings()
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    retriever = db.as_retriever(search_kwargs={"k": k})
    return retriever