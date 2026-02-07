// ============================================================================
// Azure Key Vault - Secret Management
// ============================================================================
// Centralized secret storage for connection strings, API keys, and
// credentials. All services reference secrets from Key Vault.
//
// Per Requirements/18: ~$0.03/10K operations (effectively free).
// ============================================================================

param resourcePrefix string
param location string
param tags object

@description('SQL connection string to store as secret.')
@secure()
param sqlConnectionString string

// ============================================================================
// Key Vault
// ============================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: take('${resourcePrefix}-kv', 24)
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true // Use Azure RBAC instead of vault access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 7 // Minimum for dev; 90 for prod
    enablePurgeProtection: false // Enable in prod
    publicNetworkAccess: 'Enabled'
  }
}

// ============================================================================
// Secrets
// ============================================================================

resource sqlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'sql-connection-string'
  properties: {
    value: sqlConnectionString
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

output vaultId string = keyVault.id
output vaultName string = keyVault.name
output vaultUri string = keyVault.properties.vaultUri
