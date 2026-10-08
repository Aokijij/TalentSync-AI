targetScope = 'subscription'

@description('Región del ensayo externo. No reutiliza el grupo de producción.')
param location string = 'eastus2'

@secure()
@minLength(32)
@description('Contraseña administrativa PostgreSQL; nunca se entrega a la aplicación.')
param postgresAdminPassword string

resource group 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-talentsync-staging'
  location: location
  tags: {
    project: 'TalentSync AI'
    environment: 'staging'
    managedBy: 'Bicep'
  }
}

module foundation 'foundation.bicep' = {
  name: 'talentsync-staging-foundation'
  scope: group
  params: {
    location: location
    postgresAdminPassword: postgresAdminPassword
  }
}

// No connection strings, storage keys or credentials in outputs.
output resourceGroupName string = group.name
output registryName string = foundation.outputs.registryName
output environmentName string = foundation.outputs.environmentName
output postgresHost string = foundation.outputs.postgresHost
output identityResourceId string = foundation.outputs.identityResourceId
