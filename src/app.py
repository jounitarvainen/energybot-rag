import streamlit as st
from dotenv import load_dotenv
from rag.chain import get_chain

load_dotenv()

@st.cache_resource
def load_qa_chain():
        return get_chain()

st.title("EnergyBot - Kysy energia-alan dokumenteista")
st.caption("Kysy suomalaisista energia-alan dokumenteista. EnergyBot hakee vastaukset dokumenteista, eikä keksi tietoa itse.")

st.info("**Esimerkkikysymyksiä:**\n"
        "- Mikä oli Suomen kaukoälämmön kokonaistuotanto vuonna 2024?\n"
        "- Miten Fingridin palkintajärjestelmä toimii?\n" \
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