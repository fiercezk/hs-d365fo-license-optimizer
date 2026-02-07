// ============================================================================
// Azure Container Registry - Basic Tier
// ============================================================================
// Stores Docker images for Container Apps Jobs (Python batch engine).
// Basic tier: $5/month, 10GB storage. Sufficient for Phase 1.
//
// Per Requirements/18: ~$5/month.
// ============================================================================

param resourcePrefix string
param location string
param tags object

// ============================================================================
// Container Registry
// ============================================================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: take(replace('${resourcePrefix}acr', '-', ''), 50)
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true // Required for Container Apps pull; use managed identity in prod
    publicNetworkAccess: 'Enabled'
    policies: {
      retentionPolicy: {
        status: 'disabled' // Enable in prod to manage image lifecycle
      }
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

output id string = containerRegistry.id
output name string = containerRegistry.name
output loginServer string = containerRegistry.properties.loginServer
