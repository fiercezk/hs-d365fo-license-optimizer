// ============================================================================
// Azure Functions - Flex Consumption Plan (TypeScript API Layer)
// ============================================================================
// Serverless API backend serving REST endpoints for the web application.
// Node.js 22 LTS + TypeScript. Pay-per-execution with pre-provisioned instances.
//
// Endpoints served:
//   GET  /api/v1/recommendations
//   GET  /api/v1/recommendations/{userId}
//   POST /api/v1/analyze
//   POST /api/v1/suggest-license
//   GET  /api/v1/reports/{reportType}
//   GET  /api/v1/agent/health
//
// Per Requirements/18: ~$5-20/month at Phase 1 volume.
// ============================================================================

param resourcePrefix string
param location string
param tags object

@description('Application Insights connection string for APM.')
param appInsightsConnectionString string

@description('Application Insights instrumentation key.')
param appInsightsInstrumentationKey string

@description('SQL Database connection string.')
param sqlConnectionString string

@description('Key Vault URI for secrets.')
param keyVaultUri string

// ============================================================================
// Storage Account (required by Azure Functions)
// ============================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: take(replace('${resourcePrefix}funcsa', '-', ''), 24)
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// ============================================================================
// App Service Plan - Flex Consumption
// ============================================================================

resource flexPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${resourcePrefix}-func-plan'
  location: location
  tags: tags
  kind: 'functionapp'
  sku: {
    tier: 'FlexConsumption'
    name: 'FC1'
  }
  properties: {
    reserved: false
  }
}

// ============================================================================
// Function App
// ============================================================================

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: '${resourcePrefix}-func'
  location: location
  tags: union(tags, { 'azd-service-name': 'api' })
  kind: 'functionapp'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: flexPlan.id
    httpsOnly: true
    siteConfig: {
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${az.environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'node'
        }
        {
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '~22'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsightsInstrumentationKey
        }
        {
          name: 'SQL_CONNECTION_STRING'
          value: sqlConnectionString
        }
        {
          name: 'KEY_VAULT_URI'
          value: keyVaultUri
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
      ]
      cors: {
        allowedOrigins: [
          'https://*.azurestaticapps.net'
          'http://localhost:3000' // Local development
        ]
        supportCredentials: true
      }
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

output functionAppId string = functionApp.id
output functionAppName string = functionApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output functionAppPrincipalId string = functionApp.identity.principalId
