#!/usr/bin/env bash
# ============================================================================
# D365 FO License Agent - Azure Infrastructure Deployment
# ============================================================================
# Deploys all Azure resources using Bicep templates.
#
# Prerequisites:
#   - Azure CLI installed (az --version)
#   - Logged in (az login)
#   - Subscription selected (az account set --subscription <id>)
#
# Usage:
#   ./deploy.sh                          # Deploy with defaults (dev)
#   ./deploy.sh --environment staging    # Deploy staging environment
#   ./deploy.sh --environment prod       # Deploy production
#   ./deploy.sh --what-if                # Preview changes (dry run)
#
# Environment Variables (optional overrides):
#   AZURE_SUBSCRIPTION_ID  - Target subscription
#   AZURE_LOCATION         - Azure region (default: eastus2)
#   SQL_ADMIN_LOGIN        - SQL admin username
#   SQL_ADMIN_PASSWORD     - SQL admin password
# ============================================================================

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="${SCRIPT_DIR}/main.bicep"
PARAMETERS_FILE="${SCRIPT_DIR}/parameters.json"

# Defaults
ENVIRONMENT="${ENVIRONMENT:-dev}"
BASE_NAME="d365licagent"
LOCATION="${AZURE_LOCATION:-eastus2}"
RESOURCE_GROUP="${BASE_NAME}-${ENVIRONMENT}-rg"
WHAT_IF=false

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
  case $1 in
    --environment|-e)
      ENVIRONMENT="$2"
      RESOURCE_GROUP="${BASE_NAME}-${ENVIRONMENT}-rg"
      shift 2
      ;;
    --resource-group|-g)
      RESOURCE_GROUP="$2"
      shift 2
      ;;
    --location|-l)
      LOCATION="$2"
      shift 2
      ;;
    --what-if)
      WHAT_IF=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--environment dev|staging|prod] [--resource-group name] [--location region] [--what-if]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# ============================================================================
# Validation
# ============================================================================

echo "=== D365 FO License Agent - Infrastructure Deployment ==="
echo ""
echo "  Environment:    ${ENVIRONMENT}"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  Location:       ${LOCATION}"
echo "  Template:       ${TEMPLATE_FILE}"
echo "  Parameters:     ${PARAMETERS_FILE}"
echo "  What-If:        ${WHAT_IF}"
echo ""

# Check Azure CLI
if ! command -v az &> /dev/null; then
  echo "ERROR: Azure CLI (az) is not installed."
  echo "Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
  exit 1
fi

# Check login
if ! az account show &> /dev/null; then
  echo "ERROR: Not logged in to Azure CLI."
  echo "Run: az login"
  exit 1
fi

# Show current subscription
echo "  Subscription:   $(az account show --query '{name:name, id:id}' -o tsv)"
echo ""

# Prompt SQL credentials if not set
if [[ -z "${SQL_ADMIN_LOGIN:-}" ]]; then
  read -rp "SQL Admin Login: " SQL_ADMIN_LOGIN
fi
if [[ -z "${SQL_ADMIN_PASSWORD:-}" ]]; then
  read -rsp "SQL Admin Password: " SQL_ADMIN_PASSWORD
  echo ""
fi

# ============================================================================
# Create Resource Group (if not exists)
# ============================================================================

echo "--- Creating resource group: ${RESOURCE_GROUP} ---"
az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --tags project=D365FOLicenseAgent environment="${ENVIRONMENT}" managedBy=bicep \
  --output none

echo "  Resource group ready."

# ============================================================================
# Deploy Infrastructure
# ============================================================================

DEPLOY_CMD="az deployment group create"

if [[ "${WHAT_IF}" == "true" ]]; then
  DEPLOY_CMD="az deployment group what-if"
  echo ""
  echo "--- What-If Preview (no changes will be made) ---"
else
  echo ""
  echo "--- Deploying infrastructure ---"
fi

${DEPLOY_CMD} \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMETERS_FILE}" \
  --parameters \
    baseName="${BASE_NAME}" \
    environment="${ENVIRONMENT}" \
    location="${LOCATION}" \
    sqlAdminLogin="${SQL_ADMIN_LOGIN}" \
    sqlAdminPassword="${SQL_ADMIN_PASSWORD}" \
  --verbose

# ============================================================================
# Post-Deployment: Show Outputs
# ============================================================================

if [[ "${WHAT_IF}" != "true" ]]; then
  echo ""
  echo "=== Deployment Complete ==="
  echo ""
  echo "--- Resource Outputs ---"
  az deployment group show \
    --resource-group "${RESOURCE_GROUP}" \
    --name "$(basename "${TEMPLATE_FILE}" .bicep)" \
    --query properties.outputs \
    --output table 2>/dev/null || echo "(outputs will be available after deployment completes)"

  echo ""
  echo "--- Next Steps ---"
  echo "1. Update DNS for custom domains"
  echo "2. Configure Azure AD app registration for authentication"
  echo "3. Push container image: docker push <acr>.azurecr.io/d365-license-agent:latest"
  echo "4. Deploy Function App code: func azure functionapp publish <func-name>"
  echo "5. Link Static Web App to GitHub repo for CI/CD"
  echo ""
fi
