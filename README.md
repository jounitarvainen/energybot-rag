# EnergyBot — RAG-pohjainen Q&A energiadokumenteista

EnergyBot on tekoälypohjainen kysymys-vastaus-sovellus, joka hakee vastaukset 
suomalaisista energiasektorin dokumenteista. Sovellus käyttää 
Retrieval-Augmented Generation (RAG) -arkkitehtuuria — se ei arvaa tai keksi 
tietoa, vaan perustaa vastauksensa aina lähdeaineistoon ja kertoo mistä 
dokumentista tieto löytyy.

## Arkkitehtuuri
```
Käyttäjä → Streamlit UI → LangChain RetrievalQA
                               ↓                ↓
                          ChromaDB          Azure OpenAI
                        (vektorihaku)        (GPT-4o)
                               ↑
                    text-embedding-3-small
                               ↑
                      Azure Blob Storage
                        (PDF-dokumentit)
```

## Teknologiavalinnat

| Komponentti | Teknologia | Perustelu |
|---|---|---|
| LLM | Azure OpenAI GPT-4o | Enterprise-tason turvallisuus, data ei poistu Azure-ympäristöstä |
| Embeddings | text-embedding-3-small | Kustannustehokas, riittävä tarkkuus prototyypille |
| Vektoritietokanta | ChromaDB (paikallinen) | Nopea kehitys ilman infrastruktuurikustannuksia |
| Framework | LangChain | Modulaarinen RAG-putki, helppo laajentaa |
| UI | Streamlit | Nopea prototyyppi, selkeä ei-tekniselle käyttäjälle |
| Dokumenttien tallennus | Azure Blob Storage | Skaalautuva, integroituu luontevasti Azure-ekosysteemiin |
| IaC | Bicep | Natiivi Azure-työkalu, toistettava ympäristön luonti |

## Projektin rakenne
```
energybot-rag/
├── src/
│   ├── app.py              # Streamlit UI
│   ├── ingest.py           # Dokumenttien indeksointi
│   └── rag/
│       ├── embeddings.py   # Azure OpenAI embedding-funktio
│       ├── retriever.py    # ChromaDB-haku
│       └── chain.py        # LangChain RetrievalQA chain
├── infra/
│   ├── main.bicep          # Bicep päätemplaatti
│   ├── modules/
│   │   ├── openai.bicep    # Azure OpenAI + mallit
│   │   └── storage.bicep   # Storage Account + container
│   └── parameters/
│       └── dev.bicepparam  # Kehitysympäristön parametrit
├── .env                    # API-avaimet (ei GitHubissa)
├── requirements.txt
└── README.md
```

## Azure-ympäristö
```
Resource Group: rg-rag-energybot-dev (Sweden Central)
├── Azure OpenAI Service (aoai-energybot-dev)
│   ├── gpt-4o
│   └── text-embedding-3-small
└── Storage Account (stragenergybotdev)
    └── Container: documents
```

## Asennus ja käyttöönotto

### Vaatimukset
- Python 3.11 tai 3.12
- Azure-tilaus
- Azure CLI

### 1. Kloonaa repositorio
```bash
git clone https://github.com/KÄYTTÄJÄNIMI/energybot-rag.git
cd energybot-rag
```

### 2. Luo virtuaaliympäristö
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Luo Azure-ympäristö
```bash
az login
az group create --name rg-rag-energybot-dev --location swedencentral

az deployment group create \
  --resource-group rg-rag-energybot-dev \
  --template-file infra/main.bicep \
  --parameters infra/parameters/dev.bicepparam
```

### 4. Konfiguroi ympäristömuuttujat

Luo `.env`-tiedosto projektin juureen:
```env
AZURE_OPENAI_ENDPOINT=https://aoai-energybot-dev.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_EMBEDDING_API_VERSION=2024-12-01-preview
AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
AZURE_STORAGE_CONTAINER_NAME=documents
```

### 5. Lataa dokumentit ja indeksoi
```bash
python src/ingest.py
```

### 6. Käynnistä sovellus
```bash
streamlit run src/app.py
```

## Lähdeaineisto

Sovellus käyttää seuraavia julkisia suomalaisia energiadokumentteja:

- **Fingrid** — Toimintakertomus ja tilinpäätös 2024, SASB-raportti 2025, Palkitsemisraportit 2024–2025
- **Energiateollisuus ry** — Kaukolämpötilastot 2023–2024, Sähkövuosi 2025
- **Fingrid-lehti** — 3/2024

## Jatkokehitys

- [ ] Azure AI Search — hybrid search (semantic + keyword)
- [ ] Azure Container Apps — pilviympäristöön deployment
- [ ] Dokumenttien automaattinen päivitys Blob Storage triggerillä