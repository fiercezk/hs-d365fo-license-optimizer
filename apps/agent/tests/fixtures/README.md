# Test Fixtures - D365 FO License Agent

Test data for Algorithm 2.2 (Read-Only User Detection) and other Phase 1 algorithms.

## Files

### CSV Data Files (Synthetic D365 FO Data)

- **`security_config_sample.csv`** - Security configuration mapping roles to menu items, access levels, and license requirements
- **`user_roles_sample.csv`** - User-to-role assignments
- **`user_activity_log_sample.csv`** - User activity telemetry (read/write operations)

### JSON Test Scenarios

- **`test_scenario_obvious_optimization.json`** - High read-only user (99.76%) with expensive license → clear downgrade candidate
- **`test_scenario_edge_case.json`** - 50/50 read-write split → no action (requires full license)
- **`test_scenario_already_optimized.json`** - Team Members license correctly assigned → no change needed

## Data Structure

### Security Config (security_config_sample.csv)

| Column | Description | Example |
|--------|-------------|---------|
| securityrole | Security role name | `Accountant` |
| AOTName | Menu item / entity name | `GeneralJournalEntry` |
| AccessLevel | Read/Write/Delete/Update | `Write` |
| LicenseType | Required license | `Finance` |
| Priority | License cost (monthly) | `180` |
| Entitled | Access covered by license | `1` = Yes, `0` = No |
| NotEntitled | Access NOT covered | `1` = Risk |
| securitytype | Object type | `MenuItemDisplay` |

### User Roles (user_roles_sample.csv)

| Column | Description | Example |
|--------|-------------|---------|
| user_id | Unique user identifier | `USR001` |
| user_name | Display name | `John Doe` |
| email | Email address | `john.doe@contoso.com` |
| company | Legal entity | `USMF` |
| department | Department | `Finance` |
| role_id | Role identifier | `ROLE_ACCT` |
| role_name | Role display name | `Accountant` |
| assigned_date | When assigned | `2024-01-15` |
| status | Active/Inactive | `Active` |

### Activity Log (user_activity_log_sample.csv)

| Column | Description | Example |
|--------|-------------|---------|
| user_id | User identifier | `USR001` |
| timestamp | When action occurred | `2026-01-15 09:00:00` |
| menu_item | What was accessed | `CustomerList` |
| action | Read/Write operation | `Read` |
| session_id | Session identifier | `sess-001` |
| license_tier | License required for this action | `Team Members` |
| feature | Module/functional area | `Accounts Receivable` |

## Test Scenarios

### Scenario 1: Obvious Optimization ✅

**User**: USR001 (John Doe)
**Current**: Commerce license ($180/month)
**Activity**: 847 reads, 2 writes (99.76% read-only)
**Writes**: Self-service only (profile update, time entry)
**Expected**: Downgrade to Team Members ($60/month)
**Savings**: $1,440/year
**Confidence**: 0.95 (high)

### Scenario 2: Edge Case ⚠️

**User**: USR002 (Jane Smith)
**Current**: SCM license ($180/month)
**Activity**: 250 reads, 250 writes (50/50 split)
**Writes**: 245 transactional (PO, invoices, inventory)
**Expected**: No change (requires full license)
**Savings**: $0
**Confidence**: 0.85 (high, but no action)

### Scenario 3: Already Optimized ✅

**User**: USR005 (Carol Martinez)
**Current**: Team Members ($60/month)
**Activity**: 315 reads, 5 writes (98.44% read-only)
**Writes**: All self-service (time, expenses, profile)
**Expected**: No change (correctly assigned)
**Savings**: $0
**Confidence**: 0.90 (high)

## Usage in Tests

```python
import pandas as pd
import json

# Load CSV data
security_config = pd.read_csv("tests/fixtures/security_config_sample.csv")
user_roles = pd.read_csv("tests/fixtures/user_roles_sample.csv")
activity_log = pd.read_csv("tests/fixtures/user_activity_log_sample.csv")

# Load test scenario
with open("tests/fixtures/test_scenario_obvious_optimization.json") as f:
    scenario = json.load(f)

# Run algorithm
result = algorithm_2_2_readonly_detector(
    user_id=scenario["user"]["user_id"],
    activity_log=activity_log,
    security_config=security_config,
    user_roles=user_roles,
)

# Assert expectations
assert result["action"] == scenario["expected_recommendation"]["action"]
assert result["confidence_score"] >= 0.90
```

## Data Validation

All test data validated against:
- Doc 02: Security Configuration Data structure
- Doc 03: User-Role Assignment Data structure
- Doc 04: User Activity Telemetry structure
- Doc 06: Algorithm 2.2 pseudocode requirements

**Last Updated**: 2026-02-06
