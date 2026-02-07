# Infrastructure - Azure Bicep Templates

Azure infrastructure-as-code for the D365 FO License & Security Optimization Agent.

## Architecture

```
Azure Static Web Apps (Free)     Azure Functions Flex Consumption
  Next.js 15 frontend      -->     TypeScript API Layer
  shadcn/ui + Tailwind              /api/v1/* endpoints
  $0/month                           $5-20/month
        |                                |
        |                    +-----------+-----------+
        |                    |                       |
  Azure SQL Serverless    Container Apps Jobs    Azure OpenAI
  Auto-pause, T-SQL       Python batch engine    GPT-4o-mini
  $5-30/month             $10-30/month           $50-100/month
```

Total Phase 1 cost: **~$70-145/month**

## Files

| File | Description |
|------|-------------|
| `main.bicep` | Main orchestration template (deploys all modules) |
| `parameters.json` | Parameter file with placeholder values |
| `deploy.sh` | Deployment script with CLI argument support |
| `modules/monitoring.bicep` | Log Analytics + Application Insights |
| `modules/sql-serverless.bicep` | Azure SQL Database (Serverless, auto-pause) |
| `modules/functions.bicep` | Azure Functions Flex Consumption (API layer) |
| `modules/container-apps.bicep` | Container Apps Environment + batch/on-demand jobs |
| `modules/container-registry.bicep` | Azure Container Registry (Basic, for Docker images) |
| `modules/static-web-app.bicep` | Azure Static Web Apps (Next.js hosting) |
| `modules/openai.bicep` | Azure OpenAI Service (GPT-4o-mini deployment) |
| `modules/keyvault.bicep` | Azure Key Vault (secret management) |

## Prerequisites

1. Azure CLI installed: `az --version`
2. Logged in: `az login`
3. Subscription selected: `az account set --subscription <subscription-id>`
4. Bicep CLI installed: `az bicep install`

## Deployment

### Quick Start (dev environment)

```bash
cd infrastructure

# Preview changes (dry run)
./deploy.sh --what-if

# Deploy
./deploy.sh
```

### Environment-Specific Deployment

```bash
# Staging
./deploy.sh --environment staging

# Production
./deploy.sh --environment prod --location westus2
```

### Manual Deployment

```bash
# Create resource group
az group create --name d365licagent-dev-rg --location eastus2

# Deploy
az deployment group create \
  --resource-group d365licagent-dev-rg \
  --template-file main.bicep \
  --parameters parameters.json \
  --parameters sqlAdminLogin=myadmin sqlAdminPassword=MyP@ssw0rd!
```

## Configuration

### Required Parameters

Edit `parameters.json` before deployment:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `sqlAdminLogin` | SQL Server admin username | `sqladmin` |
| `sqlAdminPassword` | SQL Server admin password | `MyStr0ngP@ss!` |

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `baseName` | `d365licagent` | Resource name prefix |
| `location` | `eastus2` | Azure region |
| `environment` | `dev` | Environment: dev, staging, prod |
| `openAiModelName` | `gpt-4o-mini` | OpenAI model to deploy |
| `openAiCapacity` | `30` | Tokens per minute (thousands) |

## Post-Deployment

After successful deployment:

1. **Configure Azure AD** authentication for the Static Web App and Functions
2. **Push Docker image** for the Python batch engine to ACR
3. **Deploy Function App** code using `func azure functionapp publish`
4. **Link GitHub** repository to Static Web App for CI/CD
5. **Run database migrations** against Azure SQL
6. **Test endpoints** via the Functions URL

## Cost Breakdown (Phase 1)

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| Static Web Apps | $0 | Free tier |
| Azure Functions | $5-10 | Pay-per-execution |
| Container Apps | $5-15 | Scale to zero |
| Azure SQL | $5-15 | Auto-pause when idle |
| Azure OpenAI | $50-100 | GPT-4o-mini bulk |
| Key Vault | ~$0 | Effectively free |
| Container Registry | $5 | Basic tier |
| **Total** | **$70-145** | |
