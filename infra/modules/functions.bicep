param location string
param functionAppName string
param appServicePlanName string
param storageAccountName string
param tags object
param azureOpenAiEndpoint string
param azureOpenAiDeploymentName string
param azureOpenAiEmbeddingDeployment string
param azureOpenAiApiVersion string
param azureOpenAiEmbeddingApiVersion string
param documentStorageAccountName string
@secure()
param azureOpenAiApiKey string

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true
  }
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource documentStorageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: documentStorageAccountName
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  tags: tags
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      pythonVersion: '3.12'
      linuxFxVersion: 'Python|3.12'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${documentStorageAccount.name};AccountKey=${documentStorageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: azureOpenAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
          value: azureOpenAiDeploymentName
        }
        {
          name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
          value: azureOpenAiEmbeddingDeployment
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: azureOpenAiApiVersion
        }
        {
          name: 'AZURE_OPENAI_EMBEDDING_API_VERSION'
          value: azureOpenAiEmbeddingApiVersion
        }
        {
          name: 'CHROMA_DB_PATH'
          value: '/mnt/chroma_db'
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: azureOpenAiApiKey
      }
      ]
    }
  }
}

output functionAppName string = functionApp.name
output functionAppId string = functionApp.id
