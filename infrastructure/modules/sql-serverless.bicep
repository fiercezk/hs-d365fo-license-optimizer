// ============================================================================
// Azure SQL Database - Serverless (General Purpose)
// ============================================================================
// Auto-pause after 1 hour of inactivity = $0 when idle.
// Auto-scale: 0.5 - 4 vCores on demand.
// D365 FO ecosystem alignment: T-SQL dialect, same tooling.
//
// Per Requirements/18: ~$5-30/month depending on usage.
// ============================================================================

param resourcePrefix string
param location string
param tags object

@secure()
@description('SQL Server administrator login.')
param adminLogin string

@secure()
@description('SQL Server administrator password.')
param adminPassword string

@description('Log Analytics workspace ID for diagnostics.')
param logAnalyticsWorkspaceId string

@description('Minimum vCore capacity (auto-scale floor).')
param minCapacity int = 1 // 0.5 vCores (expressed as 1 = 0.5 vCores in serverless)

@description('Maximum vCore capacity (auto-scale ceiling).')
param maxSizeGB int = 32

@description('Auto-pause delay in minutes. -1 to disable auto-pause.')
param autoPauseDelayMinutes int = 60

// ============================================================================
// SQL Server (logical server)
// ============================================================================

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: '${resourcePrefix}-sql'
  location: location
  tags: tags
  properties: {
    administratorLogin: adminLogin
    administratorLoginPassword: adminPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled' // Restrict in prod via firewall rules
  }
}

// ============================================================================
// Allow Azure services to access (for Functions, Container Apps)
// ============================================================================

resource firewallAllowAzure 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ============================================================================
// SQL Database - Serverless (General Purpose)
// ============================================================================

resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: '${resourcePrefix}-db'
  location: location
  tags: tags
  sku: {
    name: 'GP_S_Gen5_1' // General Purpose Serverless, Gen5, 1 vCore max
    tier: 'GeneralPurpose'
    family: 'Gen5'
    capacity: minCapacity
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: int(maxSizeGB) * 1073741824 // Convert GB to bytes
    autoPauseDelay: autoPauseDelayMinutes
    minCapacity: json('0.5') // Minimum 0.5 vCores
    zoneRedundant: false // Enable in prod for HA
    requestedBackupStorageRedundancy: 'Local' // Geo for prod
  }
}

// ============================================================================
// Diagnostics: send SQL metrics to Log Analytics
// ============================================================================

resource sqlDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: sqlDatabase
  name: 'sql-diagnostics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'SQLInsights'
        enabled: true
      }
      {
        category: 'QueryStoreRuntimeStatistics'
        enabled: true
      }
      {
        category: 'Errors'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'Basic'
        enabled: true
      }
    ]
  }
}

// ============================================================================
// Outputs
// ============================================================================

output serverId string = sqlServer.id
output serverName string = sqlServer.name
output serverFqdn string = sqlServer.properties.fullyQualifiedDomainName
output databaseName string = sqlDatabase.name
output connectionString string = 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=${sqlDatabase.name};Encrypt=true;TrustServerCertificate=false;Connection Timeout=30;'
