param location string
param vnetName string
param tags object

resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    subnets: [
      {
        name: 'subnet-apps'
        properties: {
          addressPrefix: '10.0.1.0/24'
          delegations: [
            {
              name: 'containerApps'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: 'subnet-functions'
        properties: {
          addressPrefix: '10.0.2.0/24'
          delegations: [
            {
              name: 'functions'
              properties: {
                serviceName: 'Microsoft.Web/serverFarms'
              }
            }
          ]
        }
      }
      {
        name: 'subnet-private-endpoints'
        properties: {
          addressPrefix: '10.0.3.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

resource privateEndpointOpenAI 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-openai'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: vnet.properties.subnets[2].id
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-openai-connection'
        properties: {
          privateLinkServiceId: resourceId('Microsoft.CognitiveServices/accounts', 'aoai-energybot-dev')
          groupIds: ['account']
        }
      }
    ]
  }
}

resource privateEndpointStorage 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-storage'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: vnet.properties.subnets[2].id
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-storage-connection'
        properties: {
          privateLinkServiceId: resourceId('Microsoft.Storage/storageAccounts', 'stragenergybotdev')
          groupIds: ['blob']
        }
      }
    ]
  }
}

output vnetId string = vnet.id
output appsSubnetId string = vnet.properties.subnets[0].id
output functionsSubnetId string = vnet.properties.subnets[1].id
output privateEndpointsSubnetId string = vnet.properties.subnets[2].id
