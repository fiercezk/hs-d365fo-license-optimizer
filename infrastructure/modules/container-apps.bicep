// ============================================================================
// Azure Container Apps - Environment + Batch Job
// ============================================================================
// Runs the Python algorithm batch engine as scheduled jobs.
// Scale to zero when idle. No timeout limit (supports 2hr+ batch runs).
//
// Architecture:
//   Container Apps Environment (shared networking/logging)
//   -> Container Apps Job (cron-triggered batch algorithm execution)
//
// Per Requirements/18: ~$10-30/month depending on frequency.
// ============================================================================

param resourcePrefix string
param location string
param tags object

@description('Log Analytics workspace ID for environment logging.')
param logAnalyticsWorkspaceId string

@description('Container Registry login server (e.g., myacr.azurecr.io).')
param containerRegistryLoginServer string

@description('Container Registry name for credentials.')
param containerRegistryName string

@description('Application Insights connection string.')
param appInsightsConnectionString string

@description('SQL connection string for algorithm data access.')
param sqlConnectionString string

// ============================================================================
// Container Apps Environment
// ============================================================================

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${resourcePrefix}-cae'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2023-09-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2023-09-01').primarySharedKey
      }
    }
    zoneRedundant: false // Enable in prod
  }
}

// ============================================================================
// Container Apps Job: Batch Algorithm Engine
// ============================================================================
// Scheduled cron job running the Python algorithm batch.
// Default: Daily at 2 AM UTC (off-peak for most D365 FO customers).
// Can also be triggered manually via Azure Portal or API.
// ============================================================================

resource batchAlgorithmJob 'Microsoft.App/jobs@2024-03-01' = {
  name: '${resourcePrefix}-batch'
  location: location
  tags: union(tags, { 'azd-service-name': 'batch-engine' })
  properties: {
    environmentId: containerAppsEnvironment.id
    configuration: {
      triggerType: 'Schedule'
      scheduleTriggerConfig: {
        cronExpression: '0 2 * * *' // Daily at 2:00 AM UTC
        parallelism: 1
        replicaCompletionCount: 1
      }
      replicaTimeout: 7200 // 2 hours max (matches SLA for 10K user batch)
      replicaRetryLimit: 1
      registries: [
        {
          server: containerRegistryLoginServer
          username: listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-11-01-preview').username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-11-01-preview').passwords[0].value
        }
        {
          name: 'sql-connection-string'
          value: sqlConnectionString
        }
        {
          name: 'app-insights-connection-string'
          value: appInsightsConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'batch-engine'
          image: '${containerRegistryLoginServer}/d365-license-agent:latest'
          resources: {
            cpu: json('2.0') // 2 vCPUs for batch processing
            memory: '4Gi' // 4GB RAM for pandas/numpy operations
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'SQL_CONNECTION_STRING'
              secretRef: 'sql-connection-string'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'app-insights-connection-string'
            }
            {
              name: 'BATCH_MODE'
              value: 'full_organization'
            }
            {
              name: 'MAX_WORKERS'
              value: '4'
            }
          ]
        }
      ]
    }
  }
}

// ============================================================================
// Container Apps Job: On-Demand Analysis
// ============================================================================
// Manually triggered job for single-user or custom-scope analysis.
// Responds to API requests from the Functions layer.
// ============================================================================

resource onDemandJob 'Microsoft.App/jobs@2024-03-01' = {
  name: '${resourcePrefix}-ondemand'
  location: location
  tags: union(tags, { 'azd-service-name': 'on-demand-engine' })
  properties: {
    environmentId: containerAppsEnvironment.id
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 300 // 5 minutes max for single-user analysis
      replicaRetryLimit: 2
      registries: [
        {
          server: containerRegistryLoginServer
          username: listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-11-01-preview').username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-11-01-preview').passwords[0].value
        }
        {
          name: 'sql-connection-string'
          value: sqlConnectionString
        }
        {
          name: 'app-insights-connection-string'
          value: appInsightsConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'on-demand-engine'
          image: '${containerRegistryLoginServer}/d365-license-agent:latest'
          resources: {
            cpu: json('1.0') // 1 vCPU sufficient for single-user
            memory: '2Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'SQL_CONNECTION_STRING'
              secretRef: 'sql-connection-string'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'app-insights-connection-string'
            }
            {
              name: 'BATCH_MODE'
              value: 'on_demand'
            }
          ]
        }
      ]
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

output environmentId string = containerAppsEnvironment.id
output environmentName string = containerAppsEnvironment.name
output batchJobName string = batchAlgorithmJob.name
output onDemandJobName string = onDemandJob.name
