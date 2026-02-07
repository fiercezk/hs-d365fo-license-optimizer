// ============================================================================
// Azure Static Web Apps - Free Tier (Next.js Frontend)
// ============================================================================
// Hosts the Next.js 15 web application with global CDN.
// Free tier: 100GB bandwidth/month, custom domains, integrated Azure AD auth.
//
// Per Requirements/18: $0/month (Free tier).
// ============================================================================

param resourcePrefix string
param location string
param tags object

@description('API backend URL for the linked Azure Functions.')
param apiBackendUrl string

// ============================================================================
// Static Web App
// ============================================================================

resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: '${resourcePrefix}-swa'
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    buildProperties: {
      appLocation: '/apps/web'
      outputLocation: '.next'
      apiLocation: '' // API handled by separate Azure Functions
    }
    stagingEnvironmentPolicy: 'Enabled'
  }
}

// ============================================================================
// Linked Backend (Azure Functions API)
// ============================================================================

resource linkedBackend 'Microsoft.Web/staticSites/linkedBackends@2023-12-01' = {
  parent: staticWebApp
  name: 'api-backend'
  properties: {
    backendResourceId: '' // Set at deployment time or via az staticwebapp backends link
    region: location
  }
}

// ============================================================================
// App Settings
// ============================================================================

resource appSettings 'Microsoft.Web/staticSites/config@2023-12-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    NEXT_PUBLIC_API_URL: apiBackendUrl
    NEXT_PUBLIC_APP_ENV: 'production'
  }
}

// ============================================================================
// Outputs
// ============================================================================

output id string = staticWebApp.id
output name string = staticWebApp.name
output defaultHostname string = staticWebApp.properties.defaultHostname
