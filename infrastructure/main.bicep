// ============================================================================
// D365 FO License & Security Optimization Agent - Main Infrastructure
// ============================================================================
// Deploys all Azure resources for the License Agent platform.
//
// Architecture (per Requirements/18-Tech-Stack-Recommendation.md):
//   Layer 1: Azure Static Web Apps (Next.js frontend)
//   Layer 2: Azure Functions Flex Consumption (TypeScript API)
//   Layer 3: Azure Container Apps Jobs (Python batch algorithms)
//   Layer 4: Azure SQL Serverless (data store)
//   Layer 5: Azure AI Foundry + OpenAI (recommendation explanations)
//   Layer 9: Key Vault, Container Registry, monitoring
//
// Usage:
//   az deployment group create \
//     --resource-group <rg-name> \
//     --template-file main.bicep \
//     --parameters parameters.json
// ============================================================================

targetScope = 'resourceGroup'

// ============================================================================
// Parameters
// ============================================================================

@description('Base name for all resources. Used as prefix.')
@minLength(3)
@maxLength(20)
param baseName string

@description('Azure region for deployment.')
param location string = resourceGroup().location

@description('Environment name: dev, staging, prod.')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure SQL administrator login.')
@secure()
param sqlAdminLogin string

@description('Azure SQL administrator password.')
@secure()
param sqlAdminPassword string

@description('Azure OpenAI model deployment name for GPT-4o-mini.')
param openAiModelName string = 'gpt-4o-mini'

@description('Azure OpenAI model version.')
param openAiModelVersion string = '2024-07-18'

@description('Capacity for Azure OpenAI deployment (tokens per minute in thousands).')
param openAiCapacity int = 30

@description('Tags applied to all resources.')
param tags object = {
  project: 'D365FOLicenseAgent'
  environment: environment
  managedBy: 'bicep'
}

// ============================================================================
// Variables
// ============================================================================

var resourcePrefix = '${baseName}-${environment}'
var uniqueSuffix = uniqueString(resourceGroup().id, baseName)

// ============================================================================
// Module: Monitoring (deployed first - others depend on it)
// ============================================================================

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-${uniqueSuffix}'
  params: {
    resourcePrefix: resourcePrefix
    location: location
    tags: tags
  }
}

// ============================================================================
// Module: Key Vault
// ============================================================================

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault-${uniqueSuffix}'
  params: {
    resourcePrefix: resourcePrefix
    location: location
    tags: tags
    sqlConnectionString: sqlDatabase.outputs.connectionString
  }
}

// ============================================================================
// Module: Azure SQL Serverless
// ============================================================================

module sqlDatabase 'modules/sql-serverless.bicep' = {
  name: 'sql-${uniqueSuffix}'
  params: {
    resourcePrefix: resourcePrefix
    location: location
    tags: tags
    adminLogin: sqlAdminLogin
    adminPassword: sqlAdminPassword
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

// ============================================================================
// Module: Container Registry (for Container Apps images)
// ============================================================================

module containerRegistry 'modules/container-registry.bicep' = {
  name: 'acr-${uniqueSuffix}'
  params: {
    resourcePrefix: resourcePrefix
    location: location
    tags: tags
  }
}

// ============================================================================
// Module: Container Apps Environment + Batch Jobs
// ============================================================================

module containerApps 'modules/container-apps.bicep' = {
  name: 'containerapps-${uniqueSuffix}'
  params: {
    resourcePrefix: resourcePrefix
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    containerRegistryName: containerRegistry.outputs.name
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    sqlConnectionString: sqlDatabase.outputs.connectionString
  }
}

// ============================================================================
// Module: Azure Functions Flex Consumption (API Layer)
// ============================================================================

module functions 'modules/functions.bicep' = {
  name: 'functions-${uniqueSuffix}'
  params: {
    resourcePrefix: resourcePrefix
    location: location
    tags: tags
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    appInsightsInstrumentationKey: monitoring.outputs.appInsightsInstrumentationKey
    sqlConnectionString: sqlDatabase.outputs.connectionString
    keyVaultUri: keyVault.outputs.vaultUri
  }
}

// ============================================================================
// Module: Static Web App (Next.js Frontend)
// ============================================================================

module staticWebApp 'modules/static-web-app.bicep' = {
  name: 'swa-${uniqueSuffix}'
  params: {
    resourcePrefix: resourcePrefix
    location: location
    tags: tags
    apiBackendUrl: functions.outputs.functionAppUrl
  }
}

// ============================================================================
// Module: Azure OpenAI (GPT-4o-mini for explanations)
// ============================================================================

module openAi 'modules/openai.bicep' = {
  name: 'openai-${uniqueSuffix}'
  params: {
    resourcePrefix: resourcePrefix
    location: location
    tags: tags
    modelName: openAiModelName
    modelVersion: openAiModelVersion
    capacity: openAiCapacity
  }
}

// ============================================================================
// Outputs
// ============================================================================

output staticWebAppUrl string = staticWebApp.outputs.defaultHostname
output functionAppUrl string = functions.outputs.functionAppUrl
output sqlServerFqdn string = sqlDatabase.outputs.serverFqdn
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer
output openAiEndpoint string = openAi.outputs.endpoint
output keyVaultUri string = keyVault.outputs.vaultUri
output appInsightsName string = monitoring.outputs.appInsightsName
