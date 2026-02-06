# Algorithm 2.5: License Minority Detection & Optimization

**Project**: D365 FO License & Security Optimization Agent
**Last Updated**: 2026-02-05
**Category**: Cost Optimization
**Priority**: High
**Complexity**: Medium

---

## 📋 Overview

### **Purpose**

Detect users who hold multiple licenses but have **highly skewed usage patterns** - predominantly using one license type while rarely accessing features from another license. Optimize by:
1. Identifying "license minority" access (e.g., 90% SCM, 10% Finance)
2. Questioning necessity of low-usage license access
3. Suggesting read-only alternatives (if applicable)
4. Reducing license costs through license downgrade or role modification

### **Business Value**

| Impact | Description |
|--------|-------------|
| **Cost Savings** | 10-40% per affected user (license downgrade) |
| **Security** | Principle of least privilege |
| **User Productivity** | Ensure access is actually needed |
| **License Efficiency** | Right-size licenses based on actual needs |

### **Use Case Example**

**Scenario**: John Doe has SCM + Finance licenses ($360/month)
- **Access**: 10 forms total (9 SCM forms, 1 Finance form)
- **Usage** (Last 90 days):
  - SCM forms: 850 accesses (94.4%)
  - Finance form: 50 accesses (5.6%)

**Analysis**:
- User primarily uses SCM (94.4% of usage)
- Only 1 Finance form accessed, and rarely (5.6%)
- **Question**: Does John really need that Finance form?
- **Option A**: Remove Finance form → Downgrade to SCM-only ($180/month) = **Save $180/month**
- **Option B**: If needed, convert to Read-Only → May not require Finance license = **Save $180/month**

**Result**: 50% license cost reduction with minimal impact

---

## 🔍 Algorithm Design

### **Input Data Required**

- `UserRoleAssignments`: User's assigned roles
- `SecurityConfigurationData`: Form → License type mapping
- `UserActivityData`: Actual form access (last 90 days)
- `AccessLevelData`: Read vs. Write access per form

### **Output Structure**

```
License Minority Analysis Report:
├── User: [Name/ID]
├── Current Licenses: [SCM, Finance] ($360/month)
├── Total Forms Accessed: N
├── Usage Distribution by License:
│   ├── SCM: 9 forms, 850 accesses (94.4%)
│   └── Finance: 1 form, 50 accesses (5.6%)
├── Minority License: Finance (5.6% usage)
├── Minority Forms Analysis:
│   ├── Form: [Finance Form Name]
│   │   ├── Access Count: 50
│   │   ├── Actions: [Read: 45, Write: 5]
│   │   ├── Last Accessed: [Date]
│   │   └── License Required: Finance (Full or Read-Only?)
├── Optimization Opportunities:
│   ├── Option 1: Remove Finance form access
│   │   ├── Impact: User loses access to [Form]
│   │   ├── New License: SCM-only ($180/month)
│   │   └── Savings: $180/month (50%)
│   │
│   ├── Option 2: Convert to Read-Only access
│   │   ├── Impact: User retains read-only access
│   │   ├── New License: SCM + Finance-Read (may not require Finance license)
│   │   ├── Feasibility: [Yes/No] (check if read-only needs license)
│   │   └── Savings: $180/month (50%)
│   │
│   └── Option 3: Keep current license
│       ├── Rationale: Business justification provided
│       └── No savings
├── Recommendation: [Option 1/2/3]
├── Confidence: [High/Medium/Low]
└── Next Steps: [Confirm with user/manager]
```

---

## 📝 Pseudocode

### **Main Algorithm**

```
FUNCTION DetectLicenseMinorityUsers(minorityThreshold = 15)
  BEGIN
    // minorityThreshold: % usage below which license is considered "minority"
    // Default: 15% (user uses license < 15% of the time)

    minorityUsers ← []

    // Get all users with multiple licenses
    multiLicenseUsers ← GetUsersWithMultipleLicenses()

    FOR EACH user IN multiLicenseUsers
      // Get user's activity
      userActivity ← GetUserActivity(user.id, days=90)

      // Get forms accessed by user
      formsAccessed ← GET_UNIQUE_MENU_ITEMS(userActivity)

      // Group forms by license type
      formsByLicense ← GroupFormsByLicense(formsAccessed)

      // Skip if only 1 license type
      IF COUNT(formsByLicense) < 2 THEN
        CONTINUE
      END IF

      // Calculate usage per license
      usageByLicense ← {}
      FOR EACH license IN formsByLicense.KEYS
        licenseForms ← formsByLicense[license]
        accessCount ← 0

        FOR EACH form IN licenseForms
          accessCount ← accessCount + COUNT(userActivity.FILTER(menuItem = form))
        END FOR

        usageByLicense[license] ← {
          'formCount': COUNT(licenseForms),
          'accessCount': accessCount
        }
      END FOR

      // Calculate percentages
      totalAccess ← SUM(usageByLicense.LICENSE.accessCount)

      FOR EACH license IN usageByLicense.KEYS
        usageByLicense[license].percentage ← (usageByLicense[license].accessCount / totalAccess) * 100
      END FOR

      // Identify minority license(s)
      minorityLicenses ← []
      FOR EACH license IN usageByLicense.KEYS
        IF usageByLicense[license].percentage < minorityThreshold THEN
          minorityLicenses.APPEND({
            'license': license,
            'percentage': usageByLicense[license].percentage,
            'formCount': usageByLicense[license].formCount,
            'accessCount': usageByLicense[license].accessCount
          })
        END IF
      END FOR

      // Skip if no minority licenses found
      IF COUNT(minorityLicenses) = 0 THEN
        CONTINUE
      END IF

      // Analyze optimization opportunities for each minority license
      optimizationOptions ← []

      FOR EACH minority IN minorityLicenses
        options ← AnalyzeMinorityLicenseOptimization(
          user: user.id,
          minorityLicense: minority.license,
          formsByLicense: formsByLicense,
          userActivity: userActivity,
          usageData: usageByLicense
        )

        optimizationOptions.APPEND(options)
      END FOR

      // Get current license cost
      currentLicenses ← GetUserLicenses(user.id)
      currentCost ← CalculateLicenseCost(currentLicenses)

      // Calculate potential savings
      potentialSavings ← CalculatePotentialSavings(optimizationOptions)

      // Determine recommendation
      recommendation ← GenerateRecommendation(
        optimizationOptions,
        potentialSavings,
        usageByLicense
      )

      // Create report
      minorityUsers.APPEND({
        'userId': user.id,
        'userName': user.name,
        'currentLicenses': currentLicenses,
        'currentCostPerMonth': currentCost,
        'totalFormsAccessed': COUNT(formsAccessed),
        'usageDistribution': usageByLicense,
        'minorityLicenses': minorityLicenses,
        'optimizationOptions': optimizationOptions,
        'potentialSavingsPerMonth': potentialSavings,
        'savingsPercentage': (potentialSavings / currentCost) * 100,
        'recommendation': recommendation,
        'confidence': AssessConfidence(minorityLicenses, usageByLicense),
        'nextSteps': GenerateNextSteps(user, optimizationOptions)
      })
    END FOR

    // Sort by savings
    minorityUsers.SORT_BY_DESCENDING('potentialSavingsPerMonth')

    RETURN minorityUsers
  END
END FUNCTION
```

---

### **Sub-Algorithm: Analyze Minority License Optimization**

```
FUNCTION AnalyzeMinorityLicenseOptimization(user, minorityLicense, formsByLicense, userActivity, usageData)
  BEGIN
    options ← []

    // Get forms requiring the minority license
    minorityForms ← formsByLicense[minorityLicense]

    FOR EACH form IN minorityForms
      // Get detailed activity for this form
      formActivity ← userActivity.FILTER(menuItem = form)

      accessCount ← COUNT(formActivity)
      readCount ← COUNT(formActivity.FILTER(action IN ['Read', 'View']))
      writeCount ← COUNT(formActivity.FILTER(action IN ['Write', 'Update', 'Create', 'Delete']))

      lastAccessDate ← MAX(formActivity.timestamp)

      // Get access level for this form (from security config)
      currentAccessLevel ← GetFormAccessLevel(user, form)  // Read/Write/Delete

      // Option 1: Remove access entirely
      optionRemove ← {
        'type': 'REMOVE_ACCESS',
        'form': form,
        'description': 'Remove access to ' + form,
        'impact': 'User will no longer access ' + form,
        'accessCount': accessCount,
        'lastAccessed': lastAccessDate,
        'feasibility': AssessRemovalFeasibility(form, accessCount, lastAccessDate)
      }

      // Option 2: Convert to Read-Only (if currently has write access)
      optionReadOnly ← NULL
      IF currentAccessLevel IN ['Write', 'Update', 'Delete'] AND
         readCount > (writeCount * 5) THEN  // 5x more reads than writes

        // Check if read-only access requires license
        readOnlyLicenseRequired ← DoesReadOnlyRequireLicense(form)

        optionReadOnly ← {
          'type': 'CONVERT_TO_READ_ONLY',
          'form': form,
          'description': 'Convert ' + form + ' access to Read-Only',
          'impact': 'User will have read-only access to ' + form,
          'currentAccessLevel': currentAccessLevel,
          'proposedAccessLevel': 'Read',
          'readCount': readCount,
          'writeCount': writeCount,
          'readPercentage': (readCount / accessCount) * 100,
          'licenseImpact': readOnlyLicenseRequired
            ? 'Still requires ' + minorityLicense + ' license'
            : 'May not require ' + minorityLicense + ' license (read-only)',
          'feasibility': readOnlyLicenseRequired ? 'LOW' : 'HIGH'
        }
      END IF

      // Option 3: Keep current access
      optionKeep ← {
        'type': 'KEEP_CURRENT',
        'form': form,
        'description': 'Keep current access to ' + form,
        'impact': 'No change',
        'rationale': 'Business justification needed'
      }

      options.APPEND({
        'form': form,
        'accessCount': accessCount,
        'readCount': readCount,
        'writeCount': writeCount,
        'lastAccessed': lastAccessDate,
        'options': [optionRemove, optionReadOnly, optionKeep].FILTER(x => x IS NOT NULL)
      })
    END FOR

    RETURN options
  END
END FUNCTION
```

---

### **Helper Functions**

```
FUNCTION DoesReadOnlyRequireLicense(form)
  BEGIN
    // Check if form is Team Members eligible (read-only without full license)
    IF form IN TEAM_MEMBERS_ELIGIBLE_FORMS THEN
      RETURN FALSE  // Read-only does NOT require full license
    // Check if form is Operations Activity eligible (needs Activity license, not full)
    ELSE IF form IN OPERATIONS_ACTIVITY_ELIGIBLE_FORMS THEN
      RETURN 'OPERATIONS_ACTIVITY'  // Needs Activity license, not full
    ELSE
      RETURN TRUE  // Even read-only requires full license for this form
    END IF
  END
END FUNCTION

```

> **⚠️ Critical Dependency**: The `TEAM_MEMBERS_ELIGIBLE_FORMS` and `OPERATIONS_ACTIVITY_ELIGIBLE_FORMS` lookup tables are critical dependencies that must be validated against Microsoft's official D365 FO licensing documentation before production use. Incorrect form classification will lead to invalid downgrade recommendations that could break user access. See `15-Default-SoD-Conflict-Matrix.md` for a similar configuration-driven approach. These tables should be admin-reviewable and overridable per customer environment.

```
FUNCTION AssessRemovalFeasibility(form, accessCount, lastAccessDate)
  BEGIN
    feasibilityScore ← 100
    reasons ← []

    // Factor 1: Usage frequency
    IF accessCount < 10 THEN
      feasibilityScore ← feasibilityScore - 20
      reasons.APPEND('Very low usage (' + accessCount + ' accesses in 90 days)')
    ELSE IF accessCount < 50 THEN
      feasibilityScore ← feasibilityScore - 10
      reasons.APPEND('Low usage (' + accessCount + ' accesses in 90 days)')
    END IF

    // Factor 2: Recency of access
    daysSinceAccess ← DAYS_BETWEEN(TODAY(), lastAccessDate)

    IF daysSinceAccess > 60 THEN
      feasibilityScore ← feasibilityScore - 30
      reasons.APPEND('Not accessed in ' + daysSinceAccess + ' days')
    ELSE IF daysSinceAccess > 30 THEN
      feasibilityScore ← feasibilityScore - 15
      reasons.APPEND('Last accessed ' + daysSinceAccess + ' days ago')
    END IF

    // Factor 3: Form criticality
    formCriticality ← GetFormCriticality(form)  // Business-critical, Optional, etc.

    IF formCriticality = 'BUSINESS_CRITICAL' THEN
      feasibilityScore ← feasibilityScore - 40
      reasons.APPEND('Form is business-critical')
    ELSE IF formCriticality = 'OPTIONAL' THEN
      feasibilityScore ← feasibilityScore + 10
      reasons.APPEND('Form is optional')
    END IF

    // Convert score to feasibility level
    IF feasibilityScore >= 70 THEN
      RETURN {
        'level': 'HIGH',
        'score': feasibilityScore,
        'reasons': reasons
      }
    ELSE IF feasibilityScore >= 40 THEN
      RETURN {
        'level': 'MEDIUM',
        'score': feasibilityScore,
        'reasons': reasons
      }
    ELSE
      RETURN {
        'level': 'LOW',
        'score': feasibilityScore,
        'reasons': reasons
      }
    END IF
  END
END FUNCTION

FUNCTION CalculatePotentialSavings(optimizationOptions)
  BEGIN
    // Calculate best-case savings (all minority licenses removed)

    totalSavings ← 0

    FOR EACH optionSet IN optimizationOptions
      FOR EACH option IN optionSet.options
        IF option.type = 'REMOVE_ACCESS' AND option.feasibility.level IN ['HIGH', 'MEDIUM'] THEN
          // Calculate savings if this license can be removed
          licenseCost ← GetLicenseCost(option.license)
          totalSavings ← totalSavings + licenseCost
          BREAK  // Only count once per form
        END IF
      END FOR
    END FOR

    RETURN totalSavings
  END
END FUNCTION

FUNCTION GenerateRecommendation(optimizationOptions, potentialSavings, usageByLicense)
  BEGIN
    IF potentialSavings = 0 THEN
      RETURN {
        'action': 'KEEP_CURRENT',
        'rationale': 'No viable optimization options found'
      }
    END IF

    // Find dominant license (highest usage)
    dominantLicense ← NULL
    dominantPercentage ← 0

    FOR EACH license IN usageByLicense.KEYS
      IF usageByLicense[license].percentage > dominantPercentage THEN
        dominantPercentage ← usageByLicense[license].percentage
        dominantLicense ← license
      END IF
    END FOR

    // Count high-feasibility removal options
    highFeasibilityCount ← 0
    FOR EACH optionSet IN optimizationOptions
      FOR EACH option IN optionSet.options
        IF option.type = 'REMOVE_ACCESS' AND option.feasibility.level = 'HIGH' THEN
          highFeasibilityCount ← highFeasibilityCount + 1
          BREAK
        END IF
      END FOR
    END FOR

    // Generate recommendation
    IF highFeasibilityCount > 0 AND potentialSavings > 100 THEN
      RETURN {
        'action': 'REMOVE_MINORITY_LICENSES',
        'rationale': 'User primarily uses ' + dominantLicense + ' (' + dominantPercentage + '%). Minority license access can be safely removed.',
        'expectedSavings': potentialSavings,
        'confidence': 'HIGH'
      }
    ELSE IF potentialSavings > 50 THEN
      RETURN {
        'action': 'REVIEW_WITH_USER',
        'rationale': 'User has minority license usage. Confirm with user if access is still required.',
        'expectedSavings': potentialSavings,
        'confidence': 'MEDIUM'
      }
    ELSE
      RETURN {
        'action': 'KEEP_CURRENT',
        'rationale': 'Minority license usage is low but business justification may exist.',
        'expectedSavings': 0,
        'confidence': 'LOW'
      }
    END IF
  END
END FUNCTION

FUNCTION AssessConfidence(minorityLicenses, usageByLicense)
  BEGIN
    confidenceScore ← 0

    // Factor 1: How skewed is the usage?
    dominantPercentage ← 0
    FOR EACH license IN usageByLicense.KEYS
      dominantPercentage ← MAX(dominantPercentage, usageByLicense[license].percentage)
    END FOR

    IF dominantPercentage >= 85 THEN
      confidenceScore ← confidenceScore + 40  // Very skewed
    ELSE IF dominantPercentage >= 70 THEN
      confidenceScore ← confidenceScore + 20  // Moderately skewed
    END IF

    // Factor 2: How low is minority usage?
    lowestMinorityPercentage ← 100
    FOR EACH minority IN minorityLicenses
      lowestMinorityPercentage ← MIN(lowestMinorityPercentage, minority.percentage)
    END FOR

    IF lowestMinorityPercentage <= 5 THEN
      confidenceScore ← confidenceScore + 40  // Very low usage
    ELSE IF lowestMinorityPercentage <= 10 THEN
      confidenceScore ← confidenceScore + 20  // Low usage
    END IF

    // Factor 3: How many minority forms?
    totalMinorityForms ← SUM(minorityLicenses.formCount)
    IF totalMinorityForms = 1 THEN
      confidenceScore ← confidenceScore + 20  // Only 1 form
    END IF

    IF confidenceScore >= 80 THEN
      RETURN 'HIGH'
    ELSE IF confidenceScore >= 50 THEN
      RETURN 'MEDIUM'
    ELSE
      RETURN 'LOW'
    END IF
  END
END FUNCTION
```

---

## 📊 Example Scenarios

### **Example 1: Clear Minority License**

**User**: John Doe
**Current Licenses**: SCM + Finance ($360/month)
**Analysis Period**: Last 90 days

**Usage Breakdown**:
```
Total Forms Accessed: 10
├── SCM Forms: 9 forms
│   └── Total Accesses: 850 (94.4%)
└── Finance Forms: 1 form (BankReconciliation)
    └── Total Accesses: 50 (5.6%)
```

**Finance Form Details**:
```
Form: BankReconciliation
├── Total Accesses: 50
├── Read Operations: 45 (90%)
├── Write Operations: 5 (10%)
├── Last Accessed: 7 days ago
└── Current Access: Read/Write
```

**Optimization Options**:
```
Option 1: Remove BankReconciliation Access
├── Impact: User loses access to bank reconciliation
├── Feasibility: MEDIUM (used weekly, but low volume)
├── New License: SCM-only ($180/month)
└── Savings: $180/month (50% reduction)

Option 2: Convert to Read-Only
├── Impact: User retains read-only access (90% of usage)
├── Feasibility: Depends on form eligibility
├── Form Eligibility Check:
│   ├── BankReconciliation IN TEAM_MEMBERS_ELIGIBLE_FORMS? → Check required
│   ├── If YES → License can drop to Team Members ($60/month)
│   ├── If NO, IN OPERATIONS_ACTIVITY_ELIGIBLE_FORMS? → Check required
│   │   ├── If YES → License drops to SCM + Operations Activity
│   │   └── If NO → Read-only still requires Finance license (no savings)
└── Savings: $0-$180/month depending on form eligibility

Option 3: Keep Current
└── Rationale: User needs bank reconciliation access
```

**Recommendation**:
```
Action: CONVERT_TO_READ_ONLY (pending form eligibility validation)
Confidence: MEDIUM (was HIGH, reduced pending TEAM_MEMBERS_ELIGIBLE_FORMS validation)
Rationale: User primarily performs read operations (90%). Savings depend on
           whether BankReconciliation is eligible for Team Members or
           Operations Activity license. Must validate against form eligibility
           tables before implementing.
Expected Savings: $0-$180/month ($0-$2,160/year) — pending validation
Next Steps: 1. Validate BankReconciliation form eligibility
           2. Contact user + manager to confirm read-only access is sufficient
```

---

### **Example 2: Multiple Minority Forms**

**User**: Jane Smith
**Current Licenses**: Commerce + SCM + Finance ($540/month)
**Analysis Period**: Last 90 days

**Usage Breakdown**:
```
Total Forms Accessed: 25
├── Commerce Forms: 20 forms, 2,500 accesses (89.3%)
├── SCM Forms: 4 forms, 250 accesses (8.9%)
└── Finance Forms: 1 form, 50 accesses (1.8%)
```

**Minority Licenses**:
- SCM: 8.9% usage (below 15% threshold)
- Finance: 1.8% usage (below 15% threshold)

**Optimization Analysis**:

**SCM Forms** (4 forms, 250 accesses):
```
Form: WarehouseInventory
├── Accesses: 200 (80%)
├── Read: 180, Write: 20
├── Feasibility: MEDIUM (regular use)

Form: ShippingOrder
├── Accesses: 30 (12%)
├── Read: 30, Write: 0
├── Feasibility: HIGH (read-only, low usage)

Form: PurchaseRequisition
├── Accesses: 15 (6%)
├── Read: 15, Write: 0
├── Feasibility: HIGH (read-only, very low usage)

Form: VendorMaster
├── Accesses: 5 (2%)
├── Read: 5, Write: 0
├── Feasibility: HIGH (read-only, minimal usage)
```

**Finance Forms** (1 form, 50 accesses):
```
Form: BudgetInquiry
├── Accesses: 50
├── Read: 50, Write: 0
├── Feasibility: HIGH (read-only)
```

**Optimization Options**:
```
Option 1: Remove all minority forms
├── Remove: 4 SCM forms + 1 Finance form
├── New License: Commerce-only ($180/month)
├── Savings: $360/month (67% reduction)
└── Feasibility: LOW (some forms used regularly)

Option 2: Convert minority forms to Read-Only
├── Convert: All 5 forms (4 already read-only)
├── Form Eligibility Check Required:
│   ├── WarehouseInventory, ShippingOrder, PurchaseRequisition, VendorMaster
│   │   → Check against TEAM_MEMBERS_ELIGIBLE_FORMS / OPERATIONS_ACTIVITY_ELIGIBLE_FORMS
│   └── BudgetInquiry → Check against TEAM_MEMBERS_ELIGIBLE_FORMS
├── Best Case: All forms Team Members eligible → Commerce-only ($180/month)
├── Savings: $0-$360/month (0-67%) depending on form eligibility
└── Feasibility: MEDIUM (pending form eligibility validation)

Option 3: Partial removal (keep WarehouseInventory)
├── Keep: WarehouseInventory (80% of SCM usage)
├── Remove: 3 SCM forms + 1 Finance form
├── New License: Commerce + SCM ($360/month)
├── Savings: $180/month (33% reduction)
└── Feasibility: MEDIUM
```

**Recommendation**:
```
Action: CONVERT_TO_READ_ONLY (Option 2) — pending form eligibility validation
Confidence: MEDIUM (was HIGH, reduced pending form eligibility validation)
Rationale: All minority form access is read-heavy or read-only.
           Actual savings depend on whether minority forms are eligible
           for Team Members or Operations Activity license tiers.
           Must validate against TEAM_MEMBERS_ELIGIBLE_FORMS and
           OPERATIONS_ACTIVITY_ELIGIBLE_FORMS before implementing.
Expected Savings: $0-$360/month ($0-$4,320/year) — pending validation
Next Steps: 1. Validate all 5 minority forms against eligibility tables
           2. Confirm with user that read-only access is sufficient
           3. Implement role changes to restrict write access
```

---

### **Example 3: Low Confidence Scenario**

**User**: Mike Johnson
**Current Licenses**: Finance + SCM ($360/month)
**Analysis Period**: Last 90 days

**Usage Breakdown**:
```
Total Forms Accessed: 12
├── Finance Forms: 8 forms, 600 accesses (75%)
└── SCM Forms: 4 forms, 200 accesses (25%)
```

**SCM Forms** (25% usage - above 15% threshold):
```
Form: ProductionOrder
├── Accesses: 100 (50%)
├── Read: 40, Write: 60
├── Frequency: Daily
└── Criticality: HIGH

Form: WarehouseManagement
├── Accesses: 60 (30%)
├── Read: 20, Write: 40
├── Frequency: Weekly
└── Criticality: HIGH

Form: InventoryCount
├── Accesses: 30 (15%)
├── Read: 30, Write: 0
├── Frequency: Monthly
└── Criticality: MEDIUM

Form: ShippingDetails
├── Accesses: 10 (5%)
├── Read: 10, Write: 0
├── Frequency: Rarely
└── Criticality: LOW
```

**Analysis**:
```
Minority Threshold Check: 25% > 15%
→ SCM is NOT a minority license (above threshold)

However, 1 form (ShippingDetails) has very low usage:
├── Accesses: 10 (5% of SCM usage, 1.25% of total)
├── Read-only access
├── Feasibility: HIGH for removal
```

**Optimization Options**:
```
Option 1: Remove ShippingDetails form only
├── Impact: Minimal (1.25% of total usage)
├── New License: Still Finance + SCM (other forms require SCM)
└── Savings: $0 (license still required)

Option 2: Keep current access
├── Rationale: SCM usage is 25% (not minority)
├── User actively uses ProductionOrder and WarehouseManagement
└── Recommendation: No license change
```

**Recommendation**:
```
Action: KEEP_CURRENT
Confidence: LOW (for license optimization)
Rationale: SCM license is not a minority (25% usage). User actively
           uses multiple SCM forms with write access. Only 1 form
           (ShippingDetails) has low usage, but removing it won't
           eliminate SCM license requirement.

Alternative Action: Remove ShippingDetails form access
├── Impact: Minimal loss of functionality
├── Savings: $0 (license still required)
└── Benefit: Simplify access, principle of least privilege
```

---

## 🎯 Key Features

### **1. Configurable Threshold**

**Default**: 15% minority threshold
- If license usage < 15%, flag as minority
- Adjustable per organization (10%, 20%, etc.)

```
Examples:
├── Conservative: 10% (only clear minorities)
├── Standard: 15% (balanced)
└── Aggressive: 20% (catch more opportunities)
```

### **2. Read-Only Optimization**

**Key Insight**: Read-only access often doesn't require expensive licenses

**Decision Logic**:
```
IF user has > 90% read operations THEN
  → Recommend read-only access conversion
  → Check if read-only requires license
  → If NO → License can be removed
  → If YES → Still provides security benefit
END IF
```

### **3. Multi-Level Analysis**

**Form-Level Analysis**:
- Access count
- Read vs. Write breakdown
- Last accessed date
- Access frequency (daily, weekly, monthly, rarely)

**License-Level Analysis**:
- Total forms per license
- Total accesses per license
- Usage percentage

**User-Level Analysis**:
- Overall recommendation
- Confidence score
- Potential savings

### **4. Feasibility Assessment**

**HIGH Feasibility** for removal:
- Very low usage (< 10 accesses)
- Not accessed in 60+ days
- Form is optional (not business-critical)
- Read-only access

**MEDIUM Feasibility** for removal:
- Low usage (10-50 accesses)
- Not accessed in 30-60 days
- Form is moderately critical

**LOW Feasibility** for removal:
- Regular usage (50+ accesses)
- Recently accessed
- Form is business-critical
- Heavy write usage

---

## 🚀 Implementation Workflow

### **Step 1: Detection**
- Run analysis on all multi-license users
- Identify minority license users
- Generate detailed reports

### **Step 2: Validation**
- Contact users with minority license access
- Confirm necessity of access
- Document business justification

### **Step 3: Optimization**
- Implement read-only conversions (if applicable)
- Remove unnecessary access
- Update license assignments

### **Step 4: Verification**
- Monitor user productivity post-change
- Confirm no access issues
- Track realized savings

---

## 📈 Business Impact

### **Cost Savings**

| Scenario | Users | Avg. Savings | Total Annual Savings |
|----------|-------|--------------|---------------------|
| Conservative | 5% of 1,000 | $100/month | $60,000 |
| Moderate | 10% of 1,000 | $150/month | $180,000 |
| Aggressive | 15% of 1,000 | $180/month | $324,000 |

### **Security Benefits**

- ✅ Principle of least privilege
- ✅ Reduced attack surface
- ✅ Better access governance
- ✅ Audit compliance

### **Operational Benefits**

- ✅ Simplified license management
- ✅ Clearer access rights
- ✅ Easier audits
- ✅ Reduced license sprawl

---

## ⚙️ Configurable Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `MINORITY_THRESHOLD` | 15% | 5-30% | Usage % below which license is "minority" |
| `ANALYSIS_PERIOD_DAYS` | 90 | 30-180 | Days to analyze user activity |
| `MIN_ACCESS_COUNT` | 10 | 1-100 | Minimum accesses to consider form "used" |
| `READ_ONLY_PERCENTAGE` | 90 | 80-99% | Read % to recommend read-only conversion |
| `LAST_ACCESS_DAYS` | 60 | 30-180 | Days since last access to assess feasibility |

---

## 🔗 Integration with Other Algorithms

**Complementary Algorithms**:

1. **Algorithm 2.2: Read-Only User Detector**
   - Use this to identify users who are 95%+ read-only ACROSS ALL FORMS
   - License Minority Detection handles license-specific read-only analysis

2. **Algorithm 2.4: Multi-Role Optimization**
   - Use this to identify unused roles
   - License Minority Detection analyzes usage BY LICENSE TYPE

3. **Algorithm 1.3: Role Splitting Recommender**
   - Split roles by license type
   - License Minority Detection suggests removing minority license forms

**Recommended Sequence**:
```
1. Run Read-Only User Detector (Algorithm 2.2)
   → Identify users who are entirely read-only

2. Run License Minority Detection (Algorithm 2.5)
   → Optimize remaining multi-license users

3. Run Multi-Role Optimization (Algorithm 2.4)
   → Clean up unused roles
```

---

## 📝 Summary

### **Algorithm Value**

**Impact**: 10-40% savings per affected user
**Scope**: 5-15% of multi-license users
**Complexity**: Medium
**Priority**: High

### **Key Differentiators**

1. ✅ **License-level granularity**: Analyzes usage by license type, not just forms
2. ✅ **Read-only optimization**: Leverages D365 FO read-only licensing rules
3. ✅ **Feasibility assessment**: Considers usage patterns, recency, criticality
4. ✅ **Multi-option recommendations**: Provides remove, read-only, and keep options
5. ✅ **Confidence scoring**: Helps prioritize which users to contact first

### **Implementation Priority**

**MVP**: Include in initial release (high ROI, common scenario)
**Data Requirements**: ✅ All available (Security Config, User Activity, Roles)
**Development Effort**: 2-3 weeks

---

**End of Algorithm 2.5: License Minority Detection & Optimization**
