# Infrastructure as Code — Bicep

## Rakenne

- `main.bicep` — päätemplaatti
- `modules/openai.bicep` — Azure OpenAI + mallit
- `modules/storage.bicep` — Storage Account + container
- `parameters/dev.bicepparam` — kehitysympäristön parametrit

## Uuden ympäristön luonti
```powershell
az group create --name rg-rag-energybot-dev --location swedencentral

az deployment group create \
  --resource-group rg-rag-energybot-dev \
  --template-file infra/main.bicep \
  --parameters infra/parameters/dev.bicepparam
```

## Huomiot

- Azure OpenAI -kiintiö on tilauskohtainen — ilmaiskredittitilauksella
  voidaan luoda vain yksi resurssi kerrallaan
- Verkkorajoitukset (IP-whitelist) pitää asettaa manuaalisesti
  Portalissa deployment jälkeen