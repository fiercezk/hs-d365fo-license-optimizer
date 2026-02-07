// ============================================================================
// Azure OpenAI Service (GPT-4o-mini for explanations)
// ============================================================================
// Provides natural language recommendation explanations and conversational
// interface. The LLM NEVER makes license decisions -- algorithms are
// deterministic. The LLM only generates human-readable explanations.
//
// Models:
//   GPT-4o-mini: Bulk operations (recommendation explanations) - $0.15/1M input
//   GPT-4o:      Complex queries (conversational interface) - deployed separately
//
// Per Requirements/18: ~$50-100/month (Phase 1 dev).
// ============================================================================

param resourcePrefix string
param location string
param tags object

@description('GPT model deployment name.')
param modelName string = 'gpt-4o-mini'

@description('GPT model version.')
param modelVersion string = '2024-07-18'

@description('Deployment capacity in thousands of tokens per minute.')
param capacity int = 30

// ============================================================================
// Azure OpenAI Account
// ============================================================================

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: '${resourcePrefix}-oai'
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${resourcePrefix}-oai'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow' // Restrict in prod
    }
  }
}

// ============================================================================
// Model Deployment: GPT-4o-mini (bulk operations)
// ============================================================================

resource gpt4oMiniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAiAccount
  name: modelName
  sku: {
    name: 'Standard'
    capacity: capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

// ============================================================================
// Outputs
// ============================================================================

output accountId string = openAiAccount.id
output accountName string = openAiAccount.name
output endpoint string = openAiAccount.properties.endpoint
output deploymentName string = gpt4oMiniDeployment.name
