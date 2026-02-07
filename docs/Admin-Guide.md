# D365 FO License Agent - Administrator Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-07
**Target Audience:** D365 Finance & Operations Administrators, IT Security Teams

---

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [D365 FO Environment Setup](#d365-fo-environment-setup)
4. [Azure Environment Setup](#azure-environment-setup)
5. [Data Integration Configuration](#data-integration-configuration)
6. [Agent Configuration](#agent-configuration)
7. [Security & Permissions](#security--permissions)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Troubleshooting](#troubleshooting)
10. [Appendix](#appendix)

---

## Introduction

The D365 FO License Agent is an AI-powered optimization system that analyzes Microsoft Dynamics 365 Finance & Operations (D365 FO) security configuration, user activity telemetry, and license assignments to:

- **Reduce license costs by 15-25%** through intelligent downgrade recommendations
- **Detect security risks** including SoD violations, privilege creep, anomalous access
- **Automate compliance** with segregation of duties (SoD) rules
- **Recommend optimal licenses** for new users based on required menu items

This guide covers the administrative setup and configuration required to deploy and operate the agent.

---

## Prerequisites

### Microsoft Dynamics 365 FO

- **Version:** D365 FO 10.0.38 or later
- **Environment Type:** Production or UAT (Tier 2+)
- **Access Level:** System Administrator role in D365 FO
- **License Types:** Must use Named User licenses (not Concurrent)

### Azure Subscription

- **Subscription:** Active Azure subscription with Owner or Contributor access
- **Region:** East US 2 (recommended) or any Azure region supporting:
  - Azure Functions Flex Consumption
  - Azure SQL Serverless
  - Azure OpenAI (GPT-4o-mini)
  - Azure Static Web Apps
  - Azure Container Apps

### Technical Skills

- **Required:** D365 FO security configuration knowledge, Azure portal navigation
- **Recommended:** X++ development (for telemetry instrumentation), Azure CLI usage, REST API concepts

---

## D365 FO Environment Setup

### 1. Enable OData Endpoints

The agent retrieves security configuration and user-role assignments via OData v4.

**Steps:**

1. Navigate to **System Administration > Setup > System parameters > OData**
2. Enable **Allow OData to be called from external systems**
3. Verify the endpoint URL:
   ```
   https://<your-tenant>.operations.dynamics.com/data
   ```
4. Test connectivity using Postman or curl:
   ```bash
   curl -H "Authorization: Bearer <token>" \
     "https://<tenant>.operations.dynamics.com/data/SecurityPrivileges?\$top=5"
   ```

### 2. Create Azure AD App Registration for OData Access

**Purpose:** Allow the agent to authenticate to D365 FO OData endpoints using OAuth.

**Steps:**

1. **Azure Portal > Azure Active Directory > App registrations > New registration**
   - Name: `D365-License-Agent-OData-Client`
   - Supported account types: Single tenant
   - Redirect URI: Leave blank (service-to-service)

2. **Certificates & secrets > New client secret**
   - Description: `D365 OData Access`
   - Expiration: 24 months (set calendar reminder to rotate before expiry)
   - **SAVE THE SECRET VALUE** - you cannot retrieve it later

3. **API permissions > Add a permission > Dynamics ERP**
   - Select **Delegated permissions** OR **Application permissions** (depending on your D365 FO version)
   - Add permission: `Dynamics.ERP.Read` (or equivalent)
   - **Grant admin consent** for the permission

4. **Record these values** (needed for agent configuration):
   ```
   Tenant ID:     [from Overview tab]
   Client ID:     [from Overview tab, also called Application ID]
   Client Secret: [from step 2]
   ```

5. **Add App to D365 FO Users**
   - In D365 FO: **System Administration > Users > Users**
   - Create a new user with User ID = `<Client ID from Azure AD>`
   - Assign security role: **System Administrator** (or custom role with read-only access to SecurityPrivileges, SecurityRoles, SecurityUserRoleOrganization tables)
   - Enable the user

### 3. Configure Eligible Forms Lists

The agent uses two configuration tables to determine license eligibility:

**TEAM_MEMBERS_ELIGIBLE_FORMS** - Forms accessible with Team Members license
**OPERATIONS_ACTIVITY_ELIGIBLE_FORMS** - Forms requiring Operations license

**⚠️ CRITICAL:** These tables are **NOT validated by Microsoft**. You must validate them against your tenant's actual license agreements.

**Setup:**

1. Create these tables in your D365 FO environment (SQL or X++):

   ```sql
   CREATE TABLE TEAM_MEMBERS_ELIGIBLE_FORMS (
       FormName NVARCHAR(255) PRIMARY KEY,
       ModuleName NVARCHAR(100),
       Description NVARCHAR(500),
       LastReviewedDate DATE
   );

   CREATE TABLE OPERATIONS_ACTIVITY_ELIGIBLE_FORMS (
       FormName NVARCHAR(255) PRIMARY KEY,
       ModuleName NVARCHAR(100),
       Description NVARCHAR(500),
       LastReviewedDate DATE
   );
   ```

2. Populate with your tenant's eligible forms (see Appendix A for starter list)

3. **Validation Process:**
   - Export your current license agreements from Microsoft VLSC portal
   - Cross-reference form lists with Microsoft's official documentation
   - Test downgrade scenarios in UAT environment before production use
   - Review with Microsoft account team quarterly

### 4. Export Security Configuration Baseline

**Purpose:** Provide the agent with initial security configuration data.

**OData Entities to Export:**

| Entity | Endpoint | Purpose |
|--------|----------|---------|
| SecurityPrivileges | `/data/SecurityPrivileges` | Menu items, forms, privileges |
| SecurityRoles | `/data/SecurityRoles` | Role definitions |
| SecurityRoleDuty | `/data/SecurityRoleDuty` | Role → Duty mappings |
| SecurityDutyPrivilege | `/data/SecurityDutyPrivilege` | Duty → Privilege mappings |
| SecurityUserRoleOrganization | `/data/SecurityUserRoleOrganization` | User → Role assignments |

**Export Script (PowerShell):**

```powershell
# Install required module
Install-Module -Name MSAL.PS -Force

# Get OAuth token
$token = Get-MsalToken `
    -ClientId "<Client ID>" `
    -TenantId "<Tenant ID>" `
    -ClientSecret (ConvertTo-SecureString "<Client Secret>" -AsPlainText -Force) `
    -Scopes "https://<tenant>.operations.dynamics.com/.default"

# Export SecurityPrivileges
$headers = @{ Authorization = "Bearer $($token.AccessToken)" }
$baseUrl = "https://<tenant>.operations.dynamics.com/data"

Invoke-RestMethod -Uri "$baseUrl/SecurityPrivileges" -Headers $headers -OutFile "SecurityPrivileges.json"
Invoke-RestMethod -Uri "$baseUrl/SecurityRoles" -Headers $headers -OutFile "SecurityRoles.json"
# ... repeat for other entities
```

---

## Azure Environment Setup

### 1. Deploy Infrastructure with Bicep

The agent uses Infrastructure as Code (IaC) via Azure Bicep templates.

**Steps:**

1. **Clone repository:**
   ```bash
   git clone https://github.com/fiercezk/hs-d365fo-license-optimizer.git
   cd hs-d365fo-license-optimizer
   ```

2. **Configure parameters:**
   Edit `infrastructure/parameters.json`:
   ```json
   {
     "parameters": {
       "environment": { "value": "dev" },
       "location": { "value": "eastus2" },
       "sqlAdminPassword": { "value": "<strong-password>" },
       "appInsightsName": { "value": "appi-d365-license-dev" }
     }
   }
   ```

3. **Login to Azure:**
   ```bash
   az login
   az account set --subscription "<Subscription ID>"
   ```

4. **Run what-if analysis** (preview changes):
   ```bash
   cd infrastructure
   ./deploy.sh --environment dev --what-if
   ```

5. **Deploy infrastructure:**
   ```bash
   ./deploy.sh --environment dev
   ```

6. **Verify deployment:**
   ```bash
   az resource list --resource-group rg-d365-license-agent-dev --output table
   ```

   Expected resources:
   - Azure Functions App
   - Azure SQL Serverless Database
   - Azure Container Registry
   - Azure Static Web App
   - Azure OpenAI Service
   - Application Insights
   - Key Vault

### 2. Configure Azure Key Vault Secrets

Store sensitive credentials in Azure Key Vault (deployed by Bicep template).

**Secrets to create:**

```bash
# D365 FO OData credentials
az keyvault secret set --vault-name kv-d365-license-dev \
  --name "D365-TenantId" --value "<Tenant ID>"

az keyvault secret set --vault-name kv-d365-license-dev \
  --name "D365-ClientId" --value "<Client ID>"

az keyvault secret set --vault-name kv-d365-license-dev \
  --name "D365-ClientSecret" --value "<Client Secret>"

az keyvault secret set --vault-name kv-d365-license-dev \
  --name "D365-ODataBaseUrl" --value "https://<tenant>.operations.dynamics.com/data"

# SQL Database connection string
az keyvault secret set --vault-name kv-d365-license-dev \
  --name "SqlConnectionString" --value "<from deployment outputs>"

# Azure OpenAI API key
az keyvault secret set --vault-name kv-d365-license-dev \
  --name "OpenAI-ApiKey" --value "<from deployment outputs>"
```

---

## Data Integration Configuration

### 1. OData Delta Sync Configuration

**Purpose:** Efficiently sync security configuration changes without full refreshes.

**Configuration (appsettings.json):**

```json
{
  "ODataSync": {
    "Enabled": true,
    "InitialSyncOnStartup": true,
    "ScheduleCron": "0 0 2 * * *",
    "DeltaTokenStoragePath": "/data/delta-tokens",
    "Entities": [
      "SecurityPrivileges",
      "SecurityRoles",
      "SecurityUserRoleOrganization"
    ],
    "BatchSize": 1000,
    "ThrottlingRetryCount": 3,
    "ThrottlingBackoffSeconds": 60
  }
}
```

**How Delta Sync Works:**

1. **Initial Sync:** Agent fetches all records and stores a delta token
2. **Subsequent Syncs:** Agent sends `$deltatoken=<token>` in OData query
3. **D365 Returns:** Only changed records since last sync
4. **Token Update:** Agent stores new delta token for next sync

**Monitoring:**

Check Application Insights logs for:
```kusto
traces
| where message contains "OData Delta Sync"
| project timestamp, message, customDimensions.entityName, customDimensions.recordCount
```

### 2. Application Insights Telemetry Configuration

**Purpose:** Capture user activity (read/write operations) for behavioral analysis.

**⚠️ Requires X++ instrumentation deployment** (see `X++ Instrumentation Guide`)

**Validation:**

1. Deploy X++ telemetry code to D365 FO
2. Perform test actions: Navigate to a form, execute a transaction
3. Check Application Insights Live Metrics (Azure Portal)
4. Run KQL query to verify data:

   ```kusto
   customEvents
   | where name == "FormOpened" or name == "FormAction"
   | where timestamp > ago(1h)
   | project timestamp, name, user=customDimensions.userId, form=customDimensions.formName
   | take 10
   ```

Expected output:
```
timestamp                   name          user                    form
2026-02-07T10:15:32.123Z   FormOpened    john.doe@contoso.com    PurchTable
2026-02-07T10:15:45.456Z   FormAction    john.doe@contoso.com    PurchTable (action: Save)
```

---

## Agent Configuration

### 1. Algorithm Parameters

Each of the 34 algorithms has configurable parameters stored in the database (`AlgorithmConfig` table).

**Default Configuration (Algorithm 2.2 - Read-Only Detection):**

```sql
INSERT INTO AlgorithmConfig (AlgorithmId, ParameterName, ParameterValue, Description)
VALUES
    ('2.2', 'LookbackDays', '90', 'Days of activity history to analyze'),
    ('2.2', 'WriteThresholdPercent', '5', 'Max % of write operations to qualify as read-only'),
    ('2.2', 'MinActivityEvents', '10', 'Minimum activity events required for analysis'),
    ('2.2', 'ConfidenceThresholdPercent', '85', 'Minimum confidence to recommend downgrade');
```

**Tuning Recommendations:**

- **LookbackDays:** Increase to 180 for seasonal businesses (e.g., retail during holiday season)
- **WriteThresholdPercent:** Decrease to 3% for aggressive savings, increase to 10% for conservative approach
- **MinActivityEvents:** Increase to 50 for high-volume environments to reduce false positives

### 2. License Pricing Configuration

**File:** `data/config/pricing.json`

Edit to match your actual Microsoft license costs (including any discounts):

```json
{
  "licenseTypes": {
    "TEAM_MEMBERS": {
      "monthlyPrice": 60.00,
      "annualPrice": 720.00,
      "currency": "USD"
    },
    "OPERATIONS_ACTIVITY": {
      "monthlyPrice": 90.00,
      "annualPrice": 1080.00,
      "currency": "USD"
    },
    "FINANCE": {
      "monthlyPrice": 180.00,
      "annualPrice": 2160.00,
      "currency": "USD"
    },
    "SCM": {
      "monthlyPrice": 180.00,
      "annualPrice": 2160.00,
      "currency": "USD"
    },
    "COMMERCE": {
      "monthlyPrice": 180.00,
      "annualPrice": 2160.00,
      "currency": "USD"
    },
    "DEVICE": {
      "monthlyPrice": 80.00,
      "annualPrice": 960.00,
      "currency": "USD",
      "isDeviceLicense": true
    }
  }
}
```

**Updating Pricing:**

1. Edit `pricing.json`
2. Restart Azure Functions app OR trigger cache clear:
   ```bash
   curl -X POST https://<function-app>.azurewebsites.net/api/admin/clear-cache \
     -H "Authorization: Bearer <admin-token>"
   ```
3. Verify update in Web App dashboard (metrics should recalculate)

### 3. SoD Conflict Matrix Configuration

**File:** `data/config/sod_matrix.json`

Default matrix includes 27 conflict rules across 7 categories. Customize for your organization:

**Example:**

```json
{
  "conflicts": [
    {
      "id": "SOD-AP-001",
      "category": "Accounts Payable",
      "role1": "Accounts Payable Clerk",
      "role2": "Vendor Master Maintainer",
      "severity": "CRITICAL",
      "description": "User can create vendor and approve payment to that vendor",
      "riskType": "FRAUD",
      "enabled": true
    },
    {
      "id": "SOD-CUSTOM-001",
      "category": "Custom",
      "role1": "Your Custom Role 1",
      "role2": "Your Custom Role 2",
      "severity": "HIGH",
      "description": "Custom conflict rule for your organization",
      "riskType": "SEGREGATION_OF_DUTIES",
      "enabled": true
    }
  ]
}
```

**Testing SoD Rules:**

```bash
# Trigger SoD scan for specific user
curl -X POST https://<function-app>.azurewebsites.net/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "algorithms": ["3.1"],
    "userId": "test-user@contoso.com"
  }'
```

---

## Security & Permissions

### 1. Azure RBAC Assignments

**Principle of Least Privilege:**

| Role | Azure Resource | Permissions | Rationale |
|------|----------------|-------------|-----------|
| Managed Identity (Functions) | Key Vault | `Key Vault Secrets User` | Read OData credentials |
| Managed Identity (Functions) | SQL Database | `db_datareader`, `db_datawriter` | Store recommendations |
| Managed Identity (Container Apps) | Container Registry | `AcrPull` | Pull Docker images |
| Administrators | Resource Group | `Contributor` | Manage infrastructure |
| Developers | Resource Group | `Reader` | View resources, logs |
| End Users | Static Web App | `Reader` (via Azure AD auth) | View recommendations |

### 2. Network Security

**Recommendations:**

1. **Enable Private Endpoints:**
   - SQL Database: Private endpoint to VNet
   - Key Vault: Private endpoint, disable public access
   - Storage Account: Private endpoint for delta token storage

2. **Restrict Function App Access:**
   - Enable **IP Restrictions** to allow only:
     - D365 FO IP ranges (if agent-initiated callbacks)
     - Your corporate VPN/office IP ranges
     - Azure Front Door (if using CDN)

3. **Enable Azure Front Door with WAF:**
   - Protect web app from DDoS, bot attacks
   - Enforce HTTPS, modern TLS (1.2+)

### 3. Data Residency & Compliance

**GDPR Compliance:**

- **User Data:** Agent processes user IDs, role assignments, activity logs
- **Retention Policy:** Configure in `appsettings.json`:
  ```json
  {
    "DataRetention": {
      "ActivityLogDays": 90,
      "RecommendationHistoryDays": 365,
      "AuditLogDays": 2555
    }
  }
  ```
- **Right to Erasure:** Provide API endpoint for user data deletion:
  ```bash
  DELETE /api/v1/users/{userId}/data
  ```

**SOC 2 Audit Trail:**

- All recommendation approvals/rejections logged with:
  - Admin user ID
  - Timestamp
  - Recommendation ID
  - Action (approve/reject)
  - Justification text
- Audit logs stored in SQL `AuditLog` table (immutable, append-only)

---

## Monitoring & Alerts

### 1. Application Insights Dashboards

**Preconfigured Dashboards:**

1. **Algorithm Performance Dashboard**
   - Execution time per algorithm
   - Success/failure rates
   - Data volume processed

2. **Cost Savings Dashboard**
   - Total savings (monthly, YTD)
   - Savings by algorithm
   - Approval rate (approved vs. rejected recommendations)

3. **Security Alerts Dashboard**
   - SoD violations (CRITICAL/HIGH/MEDIUM)
   - Privilege creep detections
   - Anomalous access events

**Access Dashboards:**

Azure Portal > Application Insights > Dashboards (pinned to portal home)

### 2. Alert Rules

**Critical Alerts (PagerDuty/Email):**

| Alert | Condition | Action |
|-------|-----------|--------|
| **Algorithm Failure** | 5 consecutive failures for any algorithm | Email IT Security Team |
| **OData Sync Failure** | Delta sync fails for 2+ consecutive runs | Email D365 Admin, page on-call |
| **CRITICAL SoD Violation** | New CRITICAL severity SoD conflict detected | Immediate email to CISO |
| **Deployment Failure** | Infrastructure deployment fails | Email DevOps team |

**Configure Alert (Azure CLI):**

```bash
az monitor metrics alert create \
  --name "Algorithm-Failure-Alert" \
  --resource-group rg-d365-license-agent-dev \
  --scopes /subscriptions/<sub>/resourceGroups/rg-d365-license-agent-dev/providers/Microsoft.Insights/components/appi-d365-license-dev \
  --condition "count customEvents | where name == 'AlgorithmFailed' | count > 5" \
  --window-size 5m \
  --action email IT-Security@contoso.com
```

### 3. Performance Monitoring

**Key Metrics to Monitor:**

1. **Batch Job Duration:** Algorithm execution time (target: < 30 min for full portfolio scan)
2. **API Response Time:** Web app API latency (target: p95 < 500ms)
3. **Database Performance:** Query execution time, DTU usage (auto-pause SQL Serverless)
4. **Cost:** Daily Azure cost trend (set budget alert at 120% of expected cost)

**KQL Queries for Monitoring:**

```kusto
// Algorithm execution time trend
customEvents
| where name == "AlgorithmCompleted"
| summarize avg(todouble(customDimensions.durationMs)) by bin(timestamp, 1h), tostring(customDimensions.algorithmId)
| render timechart

// API latency percentiles
requests
| where url contains "/api/"
| summarize p50=percentile(duration, 50), p95=percentile(duration, 95), p99=percentile(duration, 99) by bin(timestamp, 5m)
| render timechart
```

---

## Troubleshooting

### Issue: OData Authentication Fails

**Symptoms:**
- Algorithm 2.2 fails with error: `401 Unauthorized`
- Application Insights logs show: `OData request failed: Unauthorized`

**Resolution:**

1. Verify App Registration client secret is not expired:
   ```bash
   az ad app credential list --id <Client ID>
   ```
   If expired, create new secret and update Key Vault.

2. Check D365 FO user account is enabled:
   - D365 FO > System Administration > Users
   - Search for user with ID = `<Client ID>`
   - Verify **Enabled** = Yes

3. Test OAuth token acquisition manually:
   ```bash
   curl -X POST https://login.microsoftonline.com/<Tenant ID>/oauth2/v2.0/token \
     -d "client_id=<Client ID>" \
     -d "scope=https://<tenant>.operations.dynamics.com/.default" \
     -d "client_secret=<Client Secret>" \
     -d "grant_type=client_credentials"
   ```
   Expected: JSON response with `access_token` field.

---

### Issue: No User Activity Data in Application Insights

**Symptoms:**
- Algorithm 4.1 (Device License) returns "Insufficient data"
- KQL query for `customEvents` returns 0 rows

**Resolution:**

1. **Verify X++ instrumentation is deployed:**
   - Check D365 FO environment model list for `LicenseAgentTelemetry` model
   - If missing, deploy X++ instrumentation (see X++ Instrumentation Guide)

2. **Check Application Insights connection string:**
   - D365 FO > System Administration > System parameters > Telemetry
   - Verify **Instrumentation Key** matches Azure Application Insights resource

3. **Test telemetry manually:**
   - Navigate to any D365 FO form
   - Immediately run KQL query:
     ```kusto
     customEvents
     | where timestamp > ago(5m)
     | where name == "FormOpened"
     ```
   - If still empty, check firewall allows D365 FO → Azure Application Insights (*.applicationinsights.azure.com)

---

### Issue: High Azure SQL DTU Usage / No Auto-Pause

**Symptoms:**
- SQL Database cost higher than expected
- Azure Portal shows database never auto-pauses (expected: pause after 1 hour idle)

**Resolution:**

1. **Check for open connections:**
   ```sql
   SELECT session_id, login_name, status, last_request_start_time
   FROM sys.dm_exec_sessions
   WHERE is_user_process = 1;
   ```

2. **Review connection pooling settings:**
   - Azure Functions connection string should include `Max Pool Size=10`
   - Connection timeout: 30 seconds

3. **Enable auto-pause:**
   ```bash
   az sql db update \
     --resource-group rg-d365-license-agent-dev \
     --server sql-d365-license-dev \
     --name sqldb-d365-license-dev \
     --auto-pause-delay 60
   ```

---

## Appendix

### Appendix A: Starter TEAM_MEMBERS_ELIGIBLE_FORMS List

**⚠️ UNVALIDATED - Validate against your Microsoft license agreement before production use**

Sample forms commonly included in Team Members license:

```sql
INSERT INTO TEAM_MEMBERS_ELIGIBLE_FORMS (FormName, ModuleName, Description, LastReviewedDate)
VALUES
    ('AssetTable', 'Asset Management', 'View fixed assets', '2026-02-07'),
    ('CustTable', 'Accounts Receivable', 'View customer master', '2026-02-07'),
    ('VendTable', 'Accounts Payable', 'View vendor master', '2026-02-07'),
    ('InventTable', 'Inventory Management', 'View item master', '2026-02-07'),
    ('ProjTable', 'Project Management', 'View projects', '2026-02-07'),
    ('HcmWorker', 'Human Resources', 'View employee information (self-service)', '2026-02-07'),
    ('SalesTable', 'Sales and Marketing', 'View sales orders (read-only)', '2026-02-07'),
    ('PurchTable', 'Procurement', 'View purchase orders (read-only)', '2026-02-07');
```

**Validation Process:**

1. Export this list to Excel
2. Share with Microsoft account team for official validation
3. Cross-reference with Microsoft's [Named User License Guide](https://www.microsoft.com/licensing/product-licensing/dynamics365)
4. Test downgrade scenarios in UAT before production

### Appendix B: Support Contacts

- **Microsoft Dynamics 365 Support:** Submit ticket via LCS (Lifecycle Services)
- **Azure Support:** Azure Portal > Help + Support > New Support Request
- **Agent GitHub Issues:** https://github.com/fiercezk/hs-d365fo-license-optimizer/issues
- **Security Incidents:** CISO@contoso.com

---

**End of Administrator Guide**
