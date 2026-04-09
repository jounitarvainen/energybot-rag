import os
from dotenv import load_dotenv
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from typing import List
from .embeddings import get_embeddings

load_dotenv()

class AzureSearchRetriever(BaseRetriever):
    vector_store: AzureSearch
    k: int = 4

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        return self.vector_store.similarity_search(query=query, k=self.k)

def get_retriever(k=4):
    embeddings = get_embeddings()
    vector_store = AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query,
        search_type="similarity"
    )
    return AzureSearchRetriever(vector_store=vector_store, k=k)