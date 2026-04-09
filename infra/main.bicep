targetScope = 'resourceGroup'

param location string = resourceGroup().location
param environment string = 'dev'
param project string = 'energybot'

param openAiAccountName string = 'aoai-${project}-${environment}'
param storageAccountName string = 'str${project}${environment}'
param funcStorageAccountName string = 'stfuncenergybotdev'
param containerName string = 'documents'
param gptDeploymentName string = 'gpt-4o'
param embeddingDeploymentName string = 'text-embedding-3-small'
param functionAppName string = 'func-${project}-${environment}'
param appServicePlanName string = 'asp-${project}-${environment}'
param fileShareName string = 'chroma-index'
@secure()
param azureOpenAiApiKey string

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
    embeddingsDeploymentName: embeddingDeploymentName
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

module funcStorage 'modules/funcStorage.bicep' = {
  name: 'funcStorageDeployment'
  params: {
    location: location
    storageAccountName: funcStorageAccountName
    tags: tags
  }
}

module fileShare 'modules/fileshare.bicep' = {
  name: 'fileShareDeployment'
  params: {
    storageAccountName: storageAccountName
    fileShareName: fileShareName
  }
  dependsOn: [storage]
}

module functions 'modules/functions.bicep' = {
  name: 'functionsDeployment'
  params: {
    location: location
    functionAppName: functionAppName
    appServicePlanName: appServicePlanName
    storageAccountName: funcStorageAccountName
    tags: tags
    azureOpenAiEndpoint: openAi.outputs.openAiEndpoint
    azureOpenAiDeploymentName: gptDeploymentName
    azureOpenAiEmbeddingDeployment: embeddingDeploymentName
    azureOpenAiApiVersion: '2024-12-01-preview'
    azureOpenAiEmbeddingApiVersion: '2024-12-01-preview'
    documentStorageAccountName: storageAccountName
    azureOpenAiApiKey: azureOpenAiApiKey
  }
  dependsOn: [funcStorage, fileShare]
}

output openAiEndpoint string = openAi.outputs.openAiEndpoint
output storageAccountName string = storage.outputs.storageAccountName
