targetScope = 'resourceGroup'

param location string = resourceGroup().location
param environment string = 'dev'
param project string = 'energybot'

param openAiAccountName string = 'aoai-${project}-${environment}'
param storageAccountName string = 'str${project}${environment}'
param containerName string = 'documents'
param gptDeploymentName string = 'gpt-4o'
param embeddingsDeploymentName string = 'text-embedding-3-small'

var tags = {
  project: '${project}-rag'
  environment: environment
  owner: 'jouni.tarvainen'
  purpose: 'portfolio'
}

module openAi './modules/openai.bicep' = {
  name: 'openAiDeployment'
  params: {
    location: location
    openAiAccountName: openAiAccountName
    tags: tags
    getDeploymentName: gptDeploymentName
    embeddingsDeploymentName: embeddingsDeploymentName
  }
}

module storage './modules/storage.bicep' = {
  name: 'storageDeployment'
  params: {
    location: location
    storageAccountName: storageAccountName
    containerName: containerName
    tags: tags
  }
}

output openAiEndpoint string = openAi.outputs.openAiEndpoint
output storageAccountName string = storage.outputs.storageAccountName
