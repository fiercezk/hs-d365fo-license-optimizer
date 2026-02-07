# Data Integration Architecture

Typed connectors for the four core data sources that feed the 34 license optimization algorithms.

## Architecture

```
D365 FO (OData v4)                Azure App Insights (KQL)
  SecurityRolePermissions            customEvents
  UserSecurityRoles                  D365FO_UserActivity
         |                                  |
         v                                  v
  D365ODataClient                  AppInsightsClient
  (odata_client.py)                (app_insights_client.py)
         |                                  |
         +----------------------------------+
                        |
                        v
                  DataTransformer
                  (data_transformer.py)
                        |
            +-----------+-----------+
            |           |           |
        DataFrame    Reverse     Quality
        (pandas)     Index       Report
            |           |           |
            v           v           v
     34 Algorithms  Algo 4.7   Confidence
                    Wizard     Scoring
```

## Files

| File | Description |
|------|-------------|
| `__init__.py` | Module exports |
| `odata_client.py` | D365 FO OData v4 client with OAuth, pagination, delta sync |
| `app_insights_client.py` | Azure App Insights KQL query client |
| `data_transformer.py` | Data transformation layer (OData/KQL -> pandas/indices) |

## Data Sources

### 1. D365 FO Security Configuration (OData)

**Entity**: `SecurityRolePermissions`
**Volume**: ~700,000 records
**Refresh**: Daily delta sync (5-minute initial, <15s incremental)

Maps security roles to menu items to license requirements. This is the foundational
data that tells us "which roles require which licenses."

```python
from src.integrations import D365ODataClient

client = D365ODataClient()
for record in client.get_security_config():
    print(f"{record.security_role} -> {record.aot_name} ({record.license_type})")
```

### 2. D365 FO User-Role Assignments (OData)

**Entity**: `UserSecurityRoles`
**Volume**: 200 - 200,000 records
**Refresh**: Real-time on change, daily batch sync

Maps users to their assigned security roles. Combined with security config,
this tells us "which license each user needs based on their roles."

```python
for assignment in client.get_user_role_assignments(company="USMF"):
    print(f"{assignment.user_name} -> {assignment.role_name}")
```

### 3. Azure Application Insights (KQL)

**Table**: `customEvents` (name: "D365FO_UserActivity")
**Volume**: 10K - 10M events/day
**Refresh**: Continuous streaming (<15 minute freshness)

Tracks what users ACTUALLY do - every form they open, every read/write operation.
This is the behavioral data that drives license optimization recommendations.

```python
from src.integrations import AppInsightsClient

client = AppInsightsClient()

# Algorithm 2.2: Read-Only User Detection
ratios = client.get_user_readwrite_ratios(days=90)
for user in ratios:
    if user["read_percentage"] > 95:
        print(f"{user['user_id']}: {user['read_percentage']}% read-only")
```

### 4. Microsoft Graph API (Optional, Phase 2)

**Endpoints**: `/v1.0/subscribedSkus`, `/v1.0/users/{id}/licenseDetails`
**Permissions**: `User.Read.All`, `Directory.Read.All` (admin consent)
**Refresh**: Daily batch

Used by Algorithm 3.9 (Entra-D365 License Sync Validator) to detect mismatches
between Entra ID license assignments and D365 FO role requirements. Not
implemented in this module yet - add when Graph API integration is needed.

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `D365_BASE_URL` | D365 FO environment URL | `https://contoso.operations.dynamics.com` |
| `D365_TENANT_ID` | Azure AD tenant ID | `12345678-1234-1234-1234-123456789abc` |
| `D365_CLIENT_ID` | Azure AD app registration client ID | `abcdef01-2345-6789-abcd-ef0123456789` |
| `D365_CLIENT_SECRET` | Azure AD app registration client secret | `your-secret-here` |
| `APP_INSIGHTS_APP_ID` | Application Insights Application ID | `12345678-abcd-efgh-ijkl-123456789abc` |
| `APP_INSIGHTS_API_KEY` | Application Insights API Key | `your-api-key-here` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_INSIGHTS_WORKSPACE_ID` | Log Analytics Workspace ID (alternative auth) | - |

## Data Transformation

The `DataTransformer` class converts raw data into algorithm-ready formats:

```python
from src.integrations import D365ODataClient, AppInsightsClient, DataTransformer

odata = D365ODataClient()
insights = AppInsightsClient()
transformer = DataTransformer()

# Build DataFrames for algorithms
security_df = transformer.security_config_to_dataframe(
    list(odata.get_security_config())
)
roles_df = transformer.user_roles_to_dataframe(
    list(odata.get_user_role_assignments())
)
activity = insights.get_user_activity("john.doe@contoso.com")
activity_df = transformer.activity_to_dataframe(activity)

# Assess data quality before running algorithms
quality = transformer.assess_data_quality(security_df, roles_df, activity_df)
print(f"Data quality: {quality['overall_score']:.0%}")
print(f"Issues: {quality['issues']}")
```

## OData Throttling Mitigation

D365 FO enforces priority-based throttling on OData endpoints. The client implements:

1. **Delta sync**: Change tracking for incremental updates (95% volume reduction)
2. **Pagination**: Server-driven with `$top=5000` per page
3. **Exponential backoff**: Automatic retry on HTTP 429 (1s, 2s, 4s)
4. **Token caching**: OAuth tokens cached until expiry minus 5 minutes

See Requirements/13 for full throttling mitigation strategy.

## Azure AD App Registration

To connect to D365 FO OData, you need an Azure AD app registration with:

1. **API Permissions**: Dynamics 365 Finance & Operations > `Odata.ReadWrite.All`
2. **Grant Type**: Client Credentials (application permission, not delegated)
3. **Admin Consent**: Required by tenant admin

For Application Insights, either:
- Create an API key in the Azure Portal, or
- Use managed identity with Log Analytics workspace
