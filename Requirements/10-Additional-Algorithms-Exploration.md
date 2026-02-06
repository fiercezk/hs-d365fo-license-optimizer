# Algorithm 2.6: Cross-Role License Optimization

**Project**: D365 FO License & Security Optimization Agent
**Last Updated**: 2026-02-05
**Category**: Cost Optimization
**Priority**: High
**Complexity**: Medium

---

## 📋 Overview

### **Purpose**

Optimize license assignments by analyzing **combinations of roles** across the organization to identify:
1. **Common role combinations** that create high license requirements
2. **Alternative role structures** that could reduce license costs
3. **Cross-user patterns** where slight role modifications yield significant savings
4. **License cost centers** (specific roles or combinations driving high costs)

**Key Insight**: Instead of optimizing users individually, analyze **patterns across all users** to find systemic optimization opportunities.

---

## 🎯 Business Value

| Impact | Description |
|--------|-------------|
| **Systemic Savings** | 10-25% across affected departments |
| **Role Standardization** | Reduce role proliferation |
| **License Planning** | Better forecasting for new hires |
| **Organizational Insights** | Understand license cost drivers |

### **Use Case Examples**

**Example 1: Common High-Cost Combination**
- **Finding**: 50 users have "Accountant" + "Purchasing Clerk" roles
- **Current**: All 50 require Finance + SCM license ($360/month each)
- **Analysis**: Only 5 users actually use both Finance and SCM features
- **Optimization**: Create "Finance-Accountant" and "SCM-Purchasing" roles
- **Result**: 45 users downgrade to single license
- **Savings**: $8,100/month ($97,200/year)

**Example 2: License Cost Center**
- **Finding**: "CFO" role includes 15 high-privilege menu items across Finance + SCM
- **Impact**: 10 executives with CFO role = $3,600/month ($43,200/year)
- **Optimization**: Create "CFO-Read" variant with read-only access to SCM items
- **Result**: 7 executives only read SCM data → downgrade
- **Savings**: $1,260/month ($15,120/year)

---

## 🔍 Algorithm Design

### **Input Data Required**

- `UserRoleAssignments`: All user → role mappings
- `SecurityConfigurationData`: Role → Menu Item → License mappings
- `UserActivityData`: Actual usage patterns (90 days)
- `OrganizationalStructure`: Department, cost center data

### **Output Structure**

```
Cross-Role Optimization Report:
├── Role Combination: [Role A] + [Role B]
├── User Count: N (X% of organization)
├── Current License Assignment:
│   ├── All users require: [Finance + SCM] ($360/month)
│   └── Total monthly cost: $X
├── Usage Pattern Analysis:
│   ├── Users using both licenses: N1 (X%)
│   ├── Users using only Role A features: N2 (Y%)
│   └── Users using only Role B features: N3 (Z%)
├── Optimization Opportunities:
│   ├── Option 1: Split into separate roles
│   │   ├── Create: [Role A-Only], [Role B-Only]
│   │   ├── Users affected: N2 + N3
│   │   └── Savings: $Y/month (Z%)
│   │
│   ├── Option 2: Create license-specific variants
│   │   ├── Create: [Role A-Read], [Role A-Write]
│   │   ├── Users affected: N
│   │   └── Savings: $Y/month (Z%)
│   │
│   └── Option 3: Add approval workflow for high-cost combination
│       ├── Require: Manager approval for [Role A] + [Role B]
│       └── Impact: Reduce future role assignments
├── Recommendation: [Option 1/2/3]
├── Implementation Effort: [Low/Medium/High]
└── Priority: [High/Medium/Low]
```

---

## 📝 Pseudocode

### **Main Algorithm**

```
FUNCTION OptimizeCrossRoleLicenses()
  BEGIN
    optimizations ← []

    // Get all unique role combinations
    allUsers ← GetAllUsers()
    roleCombinations ← {}

    FOR EACH user IN allUsers
      userRoles ← GetUserRoles(user.id)
      roleCombinationKey ← SORT(userRoles).JOIN('+')

      IF roleCombinations.CONTAINS(roleCombinationKey) THEN
        roleCombinations[roleCombinationKey].users.APPEND(user.id)
      ELSE
        roleCombinations[roleCombinationKey] ← {
          'roles': userRoles,
          'users': [user.id]
        }
      END IF
    END FOR

    // Analyze each role combination
    FOR EACH combination IN roleCombinations.VALUES
      // Skip single-role combinations
      IF COUNT(combination.roles) < 2 THEN
        CONTINUE
      END IF

      // Skip if too few users
      IF COUNT(combination.users) < 5 THEN
        CONTINUE
      END IF

      // Analyze this combination
      analysis ← AnalyzeRoleCombination(
        roles: combination.roles,
        users: combination.users
      )

      IF analysis.hasOptimizationOpportunity THEN
        optimizations.APPEND(analysis)
      END IF
    END FOR

    // Sort by potential savings
    optimizations.SORT_BY_DESCENDING('potentialSavings')

    RETURN optimizations
  END
END FUNCTION
```

---

### **Sub-Algorithm: Analyze Role Combination**

```
FUNCTION AnalyzeRoleCombination(roles, users)
  BEGIN
    analysis ← {
      'roleCombination': roles,
      'userCount': COUNT(users),
      'currentLicense': GetRequiredLicenseForRoles(roles),
      'currentCost': 0,
      'usagePatterns': {},
      'optimizationOptions': [],
      'hasOptimizationOpportunity': FALSE
    }

    // Calculate current cost
    licenseCost ← GetLicenseCost(analysis.currentLicense)
    analysis.currentCost ← licenseCost * COUNT(users)

    // Determine required license for each role
    roleLicenses ← {}
    FOR EACH role IN roles
      roleLicenses[role] ← GetRequiredLicenseForRole(role)
    END FOR

    // Calculate highest license
    highestLicense ← GetHighestLicense(roleLicenses.VALUES)

    // Check if all roles require same license
    uniqueLicenses ← GET_UNIQUE(roleLicenses.VALUES)

    IF COUNT(uniqueLicenses) = 1 THEN
      // All roles require same license - no cross-license optimization
      RETURN analysis
    END IF

    // Analyze usage patterns for each user
    usagePatterns ← {
      'usesAllLicenses': [],     // Users using features from all licenses
      'usesSingleLicense': {},    // Key: license, Value: list of users
      'usesMultipleLicenses': []  // Users using multiple but not all
    }

    FOR EACH user IN users
      userActivity ← GetUserActivity(user, days=90)
      licensesUsed ← GetLicensesUsed(userActivity, roles)

      IF COUNT(licensesUsed) = COUNT(uniqueLicenses) THEN
        // User uses all licenses
        usagePatterns.usesAllLicenses.APPEND(user)
      ELSE IF COUNT(licensesUsed) = 1 THEN
        // User uses only one license
        license ← licensesUsed.FIRST
        IF NOT usagePatterns.usesSingleLicense.CONTAINS_KEY(license) THEN
          usagePatterns.usesSingleLicense[license] ← []
        END IF
        usagePatterns.usesSingleLicense[license].APPEND(user)
      ELSE
        // User uses multiple but not all licenses
        usagePatterns.usesMultipleLicenses.APPEND({
          'user': user,
          'licensesUsed': licensesUsed
        })
      END IF
    END FOR

    analysis.usagePatterns ← usagePatterns

    // Identify optimization opportunities

    // Opportunity 1: Users who only use one license
    FOR EACH license IN usagePatterns.usesSingleLicense.KEYS
      singleLicenseUsers ← usagePatterns.usesSingleLicense[license]

      IF COUNT(singleLicenseUsers) >= 3 THEN  // Threshold
        savingsPerUser ← licenseCost - GetLicenseCost(license)
        totalSavings ← savingsPerUser * COUNT(singleLicenseUsers)

        analysis.optimizationOptions.APPEND({
          'type': 'SPLIT_ROLES',
          'description': 'Create separate ' + license + '-only role variant',
          'affectedUsers': COUNT(singleLicenseUsers),
          'users': singleLicenseUsers,
          'currentLicense': analysis.currentLicense,
          'recommendedLicense': license,
          'savingsPerUser': savingsPerUser,
          'totalSavings': totalSavings,
          'savingsPercentage': (totalSavings / analysis.currentCost) * 100,
          'feasibility': AssessFeasibility(singleLicenseUsers, license)
        })

        analysis.hasOptimizationOpportunity ← TRUE
      END IF
    END FOR

    // Opportunity 2: Create role variants by license type
    roleVariants ← {}
    FOR EACH role IN roles
      roleLicense ← roleLicenses[role]

      // Analyze if role can be split by license
      canSplit ← CanRoleBeSplitByLicense(role)

      IF canSplit THEN
        roleVariants[role] ← {
          'originalRole': role,
          'currentLicense': roleLicense,
          'canCreate': true
        }
      END IF
    END FOR

    IF COUNT(roleVariants) > 0 THEN
      // Calculate potential savings from creating variants
      variantSavings ← 0

      FOR EACH user IN users
        userActivity ← GetUserActivity(user, days=90)
        licensesUsed ← GetLicensesUsed(userActivity, roles)

        IF COUNT(licensesUsed) < COUNT(uniqueLicenses) THEN
          // User could use variant role
          highestUsedLicense ← GetHighestLicense(licensesUsed)
          variantSavings ← variantSavings + (licenseCost - GetLicenseCost(highestUsedLicense))
        END IF
      END FOR

      IF variantSavings > (analysis.currentCost * 0.10) THEN  // > 10% savings
        analysis.optimizationOptions.APPEND({
          'type': 'CREATE_ROLE_VARIANTS',
          'description': 'Create license-specific variants for roles',
          'variants': roleVariants,
          'affectedUsers': COUNT(users),
          'totalSavings': variantSavings,
          'savingsPercentage': (variantSavings / analysis.currentCost) * 100,
          'feasibility': 'MEDIUM'
        })

        analysis.hasOptimizationOpportunity ← TRUE
      END IF
    END IF

    // Opportunity 3: Add approval workflow for high-cost combination
    IF analysis.currentCost > 500 AND COUNT(users) > 10 THEN
      analysis.optimizationOptions.APPEND({
        'type': 'ADD_APPROVAL_WORKFLOW',
        'description': 'Require manager approval for ' + roles.JOIN(' + '),
        'affectedUsers': COUNT(users),
        'currentMonthlyCost': analysis.currentCost,
        'impact': 'Reduce future assignments of high-cost combination',
        'savingsPercentage': 'Prevent future cost growth',
        'feasibility': 'LOW'
      })
    END IF

    // Calculate best potential savings
    IF COUNT(analysis.optimizationOptions) > 0 THEN
      bestOption ← analysis.optimizationOptions.MAX_BY('totalSavings')
      analysis.potentialSavings ← bestOption.totalSavings
      analysis.bestOption ← bestOption
    END IF

    RETURN analysis
  END
END FUNCTION
```

---

### **Helper Functions**

```
FUNCTION GetLicensesUsed(userActivity, roles)
  BEGIN
    // Determine which licenses user actually uses

    licensesUsed ← EMPTY_SET

    // Get menu items accessed by user
    accessedMenuItems ← GET_UNIQUE_MENU_ITEMS(userActivity)

    // Get menu items for user's roles
    roleMenuItems ← {}
    FOR EACH role IN roles
      roleMenuItems[role] ← GetMenuItemsForRole(role)
    END FOR

    // For each accessed menu item, find which role and license it belongs to
    FOR EACH menuItem IN accessedMenuItems
      // Find which role provides this menu item
      FOR EACH role IN roles
        IF roleMenuItems[role].CONTAINS(menuItem) THEN
          // Get license for this menu item
          license ← GetLicenseForMenuItem(menuItem)
          licensesUsed.ADD(license)
          BREAK
        END IF
      END FOR
    END FOR

    RETURN licensesUsed
  END
END FUNCTION

FUNCTION CanRoleBeSplitByLicense(role)
  BEGIN
    // Check if role has menu items from multiple licenses

    roleMenuItems ← GetMenuItemsForRole(role)
    licensesInRole ← EMPTY_SET

    FOR EACH menuItem IN roleMenuItems
      license ← GetLicenseForMenuItem(menuItem)
      licensesInRole.ADD(license)
    END FOR

    // If role has menu items from multiple licenses, it can be split
    RETURN COUNT(licensesInRole) > 1
  END
END FUNCTION

FUNCTION AssessFeasibility(users, targetLicense)
  BEGIN
    // Assess how feasible it is to move users to target license

    feasibilityScore ← 100
    factors ← []

    // Factor 1: How strongly do users use the target license?
    strongUsageCount ← 0
    FOR EACH user IN users
      userActivity ← GetUserActivity(user, days=90)
      targetLicenseUsage ← COUNT(userActivity.FILTER(license = targetLicense))
      totalUsage ← COUNT(userActivity)

      IF (targetLicenseUsage / totalUsage) > 0.80 THEN
        strongUsageCount ← strongUsageCount + 1
      END IF
    END FOR

    IF (strongUsageCount / COUNT(users)) > 0.70 THEN
      feasibilityScore ← feasibilityScore + 20
      factors.APPEND('Strong usage of target license')
    END IF

    // Factor 2: How long have users had this role combination?
    // (If long time, might be business justification)
    avgAssignmentDuration ← CalculateAverageAssignmentDuration(users)
    IF avgAssignmentDuration > 365 THEN  // More than 1 year
      feasibilityScore ← feasibilityScore - 10
      factors.APPEND('Long-standing role combination (>1 year)')
    END IF

    // Factor 3: Are users in same department?
    // (Easier to implement change within one department)
    departments ← GET_UNIQUE_DEPARTMENTS(users)
    IF COUNT(departments) <= 2 THEN
      feasibilityScore ← feasibilityScore + 10
      factors.APPEND('Users in few departments (' + COUNT(departments) + ')')
    END IF

    // Convert score to feasibility level
    IF feasibilityScore >= 80 THEN
      RETURN {
        'level': 'HIGH',
        'score': feasibilityScore,
        'factors': factors
      }
    ELSE IF feasibilityScore >= 60 THEN
      RETURN {
        'level': 'MEDIUM',
        'score': feasibilityScore,
        'factors': factors
      }
    ELSE
      RETURN {
        'level': 'LOW',
        'score': feasibilityScore,
        'factors': factors
      }
    END IF
  END
END FUNCTION
```

---

## 📊 Example Scenarios

### **Example 1: Finance + SCM Combination**

**Role Combination**: Accountant + Purchasing Clerk
**User Count**: 50 users
**Current License**: Finance + SCM ($360/month each)
**Total Cost**: $18,000/month

**Usage Analysis**:
```
Users using both Finance and SCM: 5 (10%)
├─ High utilization of both licenses
└─ Keep current assignment

Users using only Finance: 35 (70%)
├─ 95%+ usage of Finance features
├─ 5% usage of SCM features (accidental clicks)
└─ Can downgrade to Finance-only

Users using only SCM: 10 (20%)
├─ 90%+ usage of SCM features
├─ 10% usage of Finance features (inquiry only)
└─ Can downgrade to SCM-only
```

**Optimization Options**:

**Option 1: Split Roles** (RECOMMENDED)
```
Create:
├─ Accountant-Finance (35 users)
├─ Purchasing Clerk-SCM (10 users)
└─ Accountant-Purchasing-Full (5 users)

Cost:
├─ 35 × Finance ($180) = $6,300
├─ 10 × SCM ($180) = $1,800
└─ 5 × Finance + SCM ($360) = $1,800

Total: $9,900/month
Savings: $8,100/month (45%)
Annual: $97,200
```

**Option 2: Create License Variants**
```
Create:
├─ Accountant-Finance
├─ Accountant-SCM
└─ Purchasing Clerk-SCM

Assign variants based on actual usage
Result: Similar savings as Option 1
```

**Recommendation**: Option 1 (Split Roles)
**Confidence**: HIGH
**Implementation Effort**: Medium
**ROI**: 8-10 months

---

### **Example 2: Three-Role Combination**

**Role Combination**: Sales Manager + Customer Master + AR Clerk
**User Count**: 25 users
**Current License**: Commerce + Finance ($360/month each)
**Total Cost**: $9,000/month

**Analysis**:
```
Role → License Mapping:
├─ Sales Manager → Commerce
├─ Customer Master → Commerce
└─ AR Clerk → Finance

All users assigned: Commerce + Finance ($360/month)
```

**Usage Patterns**:
```
Users using both Commerce and Finance: 3 (12%)
├─ Legitimate need for both
└─ Keep current assignment

Users using only Commerce: 20 (80%)
├─ Customer management, sales orders
├─ No AR/Collections work
└─ Can downgrade to Commerce-only

Users using only Finance: 2 (8%)
├─ AR work only
├─ No sales/customers
└─ Can downgrade to Finance-only
```

**Optimization**:
```
Before: 25 × $360 = $9,000/month
After:
├─ 20 × Commerce ($180) = $3,600
├─ 2 × Finance ($180) = $360
└─ 3 × Commerce + Finance ($360) = $1,080

Total: $5,040/month
Savings: $3,960/month (44%)
Annual: $47,520
```

---

### **Example 3: Department-Level Optimization**

**Role Combination**: Project Manager + Timesheet User + Expense User
**Department**: Engineering (100 users)
**Current License**: Operations + Activity + Finance ($270/month each)
**Total Cost**: $27,000/month

**Analysis**:
```
License Usage by User Type:
├─ Project Managers (20 users):
│   └─ Use Finance features (expense approval)
│
├─ Team Members (70 users):
│   └─ Only enter time (Operations license sufficient)
│
└─ Finance Approvers (10 users):
    └─ Review and approve expenses (need Finance)
```

**Optimization**:
```
Current: 100 × $270 = $27,000/month

Optimized:
├─ 70 Team Members → Operations ($90) = $6,300
├─ 20 Project Managers → Operations + Activity ($120) = $2,400
└─ 10 Finance Approvers → Finance ($180) = $1,800

Total: $10,500/month
Savings: $16,500/month (61%)
Annual: $198,000
```

**Recommendation**: Reassign roles based on job function
**Confidence**: HIGH
**Implementation Effort**: Medium-High
**ROI**: 3-4 months

---

## 🎯 Key Features

### **1. Cross-User Pattern Recognition**

Instead of analyzing users individually, identify:
- **Common role combinations** (e.g., "Accountant + Purchasing Clerk")
- **Systemic optimization opportunities** (affecting many users)
- **Organizational patterns** (department-specific role usage)

### **2. License Impact Analysis**

For each role combination:
- Calculate current license cost
- Analyze actual license usage
- Identify cost reduction opportunities
- Generate multiple optimization options

### **3. Feasibility Assessment**

Evaluate implementation difficulty:
- **HIGH**: Strong usage patterns, few departments affected
- **MEDIUM**: Moderate usage, multiple departments
- **LOW**: Weak patterns, widespread impact, high risk

### **4. Multiple Optimization Strategies**

1. **Split Roles**: Create license-specific role variants
2. **Reassign Users**: Move users to appropriate single-license roles
3. **Create Variants**: Build read-only, lite versions of roles
4. **Add Approvals**: Require approval for high-cost combinations

---

## 💡 Business Value

### **Cost Impact**

| Organization Size | Affected Users | Avg. Savings | Annual Savings |
|-------------------|----------------|--------------|----------------|
| Small (500 users) | 50 (10%) | $150/user | $90,000 |
| Medium (2,000 users) | 200 (10%) | $150/user | $360,000 |
| Large (10,000 users) | 1,000 (10%) | $150/user | $1,800,000 |

### **Operational Benefits**

- ✅ **Role Standardization**: Reduce custom role proliferation
- ✅ **License Planning**: Better forecasting for new hires
- ✅ **Cost Visibility**: Understand which role combinations drive costs
- ✅ **Scalability**: Systemic optimization vs. individual fixes

### **Strategic Value**

- **Organizational Insights**: Understand how licenses are used across the org
- **Change Management**: Department-by-department rollout
- **Continuous Improvement**: Ongoing monitoring of role assignments

---

## ⚙️ Configurable Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `MIN_USERS_THRESHOLD` | 5 | 3-20 | Minimum users for combination analysis |
| `MIN_SAVINGS_PERCENTAGE` | 10% | 5-25% | Minimum savings to recommend optimization |
| `MIN_SINGLE_LICENSE_USERS` | 3 | 2-10 | Minimum users to create role variant |
| `STRONG_USAGE_PERCENTAGE` | 80% | 70-90% | Usage % to consider "strong" license usage |
| `LONG_STANDING_DAYS` | 365 | 180-730 | Days to consider role "long-standing" |

---

## 🔗 Integration with Other Algorithms

**Complementary Algorithms**:

1. **Algorithm 2.4: Multi-Role Optimization**
   - Focuses on individual users with many roles
   - Cross-Role Optimization focuses on patterns across users

2. **Algorithm 2.5: License Minority Detection**
   - Identifies users with skewed license usage
   - Cross-Role Optimization identifies systemic patterns

3. **Algorithm 1.3: Role Splitting Recommender**
   - Splits individual roles by license type
   - Cross-Role Optimization analyzes role combinations

**Recommended Sequence**:
```
1. Run Cross-Role License Optimization (Algorithm 2.6)
   → Identify systemic optimization opportunities

2. Run License Minority Detection (Algorithm 2.5)
   → Optimize remaining individual users

3. Run Multi-Role Optimization (Algorithm 2.4)
   → Clean up users with excessive roles
```

---

## 📝 Summary

### **Algorithm Value**

**Impact**: 10-25% savings for affected combinations
**Scope**: 10-20% of users (those with multi-role assignments)
**Complexity**: Medium
**Priority**: High (Phase 1)

### **Key Differentiators**

1. ✅ **Systemic Optimization**: Analyzes patterns across all users
2. ✅ **Role Combination Analysis**: Identifies high-cost role combinations
3. ✅ **Multiple Strategies**: Split roles, create variants, reassign users
4. ✅ **Department-Level**: Can optimize by department or cost center
5. ✅ **High ROI**: Affects many users simultaneously

### **Implementation Priority**

**Phase 1**: Include (high ROI, systemic impact)
**Data Requirements**: ✅ All available
**Development Effort**: 2-3 weeks

---

**End of Algorithm 2.6: Cross-Role License Optimization**
