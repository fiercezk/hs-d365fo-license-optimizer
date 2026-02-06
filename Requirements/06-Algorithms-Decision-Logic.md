# Algorithms & Decision Logic - Advanced Scenarios

**Project**: D365 FO License & Security Optimization Agent
**Last Updated**: 2026-02-05
**Status**: Requirements Definition Phase
**Version**: 1.0

---

## 📑 Table of Contents

1. [Scenario 1: Role Analysis & Splitting](#scenario-1-role-analysis--splitting)
2. [Scenario 2: User-Level Behavioral Optimization](#scenario-2-user-level-behavioral-optimization)
3. [Decision Trees](#decision-trees)
4. [Configurable Parameters](#configurable-parameters)
5. [Example Calculations](#example-calculations)

---

## Scenario 1: Role Analysis & Splitting

### Overview

Analyze roles to identify license cost optimization opportunities through:
- Role splitting (separate roles by license type)
- Component removal (remove unnecessary high-license menu items)
- User segment analysis (who uses which parts)

---

### Algorithm 1.1: Role License Composition Analyzer

**Purpose**: For each role, determine how many menu items require each license type

**Input**:
- `SecurityConfigurationData`: Role → Menu Item → License Type mapping
- `RoleList`: List of all roles to analyze

**Output**:
```
For each role:
  ├── Role Name
  ├── Total Menu Items: N
  ├── License Composition:
  │   ├── Commerce License Items: N1 (percentage %)
  │   ├── Finance License Items: N2 (percentage %)
  │   ├── SCM License Items: N3 (percentage %)
  │   ├── Operations – Activity Items: N4 (percentage %)
  │   └── Team Members Items: N5 (percentage %)
  └── Highest License: [License Type]
```

**Pseudocode**:

```
FUNCTION AnalyzeRoleLicenseComposition(roleName)
  BEGIN
    // Get all menu items for this role
    menuItems ← GetMenuItemsForRole(roleName)

    // Initialize counters for each license type
    licenseCounts ← {
      'Commerce': 0,
      'Finance': 0,
      'SCM': 0,
      'Operations Activity': 0,
      'Team Members': 0,
      'None': 0
    }

    // Count menu items by license type
    FOR EACH menuItem IN menuItems
      licenseType ← menuItem.LicenseType

      // Handle combined licenses (Finance + SCM)
      IF licenseType CONTAINS 'Finance' AND licenseType CONTAINS 'SCM' THEN
        licenseCounts['Finance'] ← licenseCounts['Finance'] + 1
        licenseCounts['SCM'] ← licenseCounts['SCM'] + 1
      ELSE
        licenseCounts[licenseType] ← licenseCounts[licenseType] + 1
      END IF
    END FOR

    // Calculate percentages
    totalItems ← COUNT(menuItems)
    FOR EACH licenseType IN licenseCounts
      licenseCounts[licenseType] ← {
        'count': licenseCounts[licenseType],
        'percentage': (licenseCounts[licenseType] / totalItems) * 100
      }
    END FOR

    // Determine highest license
    highestLicense ← GetHighestLicenseType(licenseCounts)

    RETURN {
      'roleName': roleName,
      'totalItems': totalItems,
      'licenseComposition': licenseCounts,
      'highestLicense': highestLicense
    }
  END
END FUNCTION
```

---

### Algorithm 1.2: User Segment Analyzer

**Purpose**: For a given role, analyze which users actually use which license-type features

**Input**:
- `UserRoleAssignments`: Users assigned to the role
- `UserActivityData`: User activity (last 90 days)
- `SecurityConfigurationData`: Menu item → License mapping
- `RoleName`: Role to analyze

**Output**:
```
For role X:
  ├── Total Users: N
  ├── User Segments:
  │   ├── Commerce-Only Users: N1 (%)
  │   ├── Finance-Only Users: N2 (%)
  │   ├── SCM-Only Users: N3 (%)
  │   ├── Mixed-Usage Users: N4 (%)
  │   └── Inactive Users: N5 (%)
  └── Detailed Breakdown per User
```

**Pseudocode**:

```
FUNCTION AnalyzeUserSegments(roleName)
  BEGIN
    // Get all users with this role
    users ← GetUsersWithRole(roleName)

    // Initialize user segments
    userSegments ← {
      'Commerce-Only': [],
      'Finance-Only': [],
      'SCM-Only': [],
      'Operations-Only': [],
      'Team-Members-Only': [],
      'Mixed-Usage': [],
      'Inactive': []
    }

    // Get license type for each menu item
    menuItemLicenses ← BuildMenuItemLicenseMap()

    FOR EACH user IN users
      // Get user's activity in last 90 days
      userActivity ← GetUserActivity(user.id, days=90)

      IF COUNT(userActivity) = 0 THEN
        userSegments['Inactive'].APPEND(user)
        CONTINUE
      END IF

      // Track which license types user actually used
      licensesUsed ← EMPTY_SET

      FOR EACH activity IN userActivity
        menuItem ← activity.menuItem
        licenseType ← menuItemLicenses[menuItem]

        // Add to set of licenses used
        licensesUsed.ADD(licenseType)
      END FOR

      // Categorize user based on licenses used
      IF COUNT(licensesUsed) = 1 THEN
        license ← licensesUsed.FIRST
        segmentName ← license + '-Only'
        userSegments[segmentName].APPEND(user)
      ELSE IF COUNT(licensesUsed) > 1 THEN
        userSegments['Mixed-Usage'].APPEND(user)
      END IF
    END FOR

    // Calculate statistics
    totalUsers ← COUNT(users)
    FOR EACH segment IN userSegments
      segmentStats[segment] ← {
        'count': COUNT(userSegments[segment]),
        'percentage': (COUNT(userSegments[segment]) / totalUsers) * 100
      }
    END FOR

    RETURN {
      'roleName': roleName,
      'totalUsers': totalUsers,
      'userSegments': segmentStats,
      'detailedBreakdown': userSegments
    }
  END
END FUNCTION
```

---

### Algorithm 1.3: Role Splitting Recommender

**Purpose**: Recommend splitting a role into multiple roles by license type

**Input**:
- `RoleLicenseComposition`: From Algorithm 1.1
- `UserSegments`: From Algorithm 1.2
- `LicenseCosts`: Cost per license type per month

**Output**:
```
Recommendation for Role X:
  ├── Split?: YES/NO
  ├── Rationale: [Explanation]
  ├── Proposed New Roles:
  │   ├── Role X - Commerce
  │   │   ├── Menu Items: N1
  │   │   ├── Users: N2
  │   │   └── Potential Savings: $Y/month
  │   └── Role X - Finance
  │       ├── Menu Items: N3
  │       ├── Users: N4
  │       └── Potential Savings: $Z/month
  └── Implementation Effort: [Low/Medium/High]
```

**Pseudocode**:

```
FUNCTION RecommendRoleSplit(roleName)
  BEGIN
    // Get analysis data
    roleComposition ← AnalyzeRoleLicenseComposition(roleName)
    userSegments ← AnalyzeUserSegments(roleName)

    recommendations ← []

    // Check if role has multiple license types
    significantLicenses ← GetLicenseTypesWithPercentage(
      roleComposition.licenseComposition,
      minPercentage = 10  // Configurable threshold
    )

    IF COUNT(significantLicenses) < 2 THEN
      RETURN {
        'shouldSplit': FALSE,
        'rationale': 'Role primarily uses one license type (' + roleComposition.highestLicense + ')'
      }
    END IF

    // For each license type, evaluate if it should be separated
    FOR EACH licenseType IN significantLicenses
      // Get segment name for this license
      segmentName ← licenseType + '-Only'

      // Check if we have users only using this license type
      exclusiveUsers ← userSegments.detailedBreakdown[segmentName]

      IF COUNT(exclusiveUsers) > 0 THEN
        // Calculate potential savings
        currentLicenseCost ← GetLicenseCost(roleComposition.highestLicense)
        newLicenseCost ← GetLicenseCost(licenseType)
        savingsPerUser ← currentLicenseCost - newLicenseCost
        totalSavings ← savingsPerUser * COUNT(exclusiveUsers)

        recommendations.APPEND({
          'licenseType': licenseType,
          'exclusiveUserCount': COUNT(exclusiveUsers),
          'menuItemCount': roleComposition.licenseComposition[licenseType].count,
          'potentialSavingsPerMonth': totalSavings,
          'savingsPerUser': savingsPerUser
        })
      END IF
    END FOR

    IF COUNT(recommendations) = 0 THEN
      RETURN {
        'shouldSplit': FALSE,
        'rationale': 'No user segment exclusively uses a single license type. All users have mixed usage patterns.'
      }
    END IF

    // Calculate total potential savings
    totalSavings ← SUM(recommendations.potentialSavingsPerMonth)

    RETURN {
      'shouldSplit': TRUE,
      'rationale': 'Role can be split to optimize license costs based on actual usage patterns.',
      'proposedRoles': recommendations,
      'totalPotentialSavingsPerMonth': totalSavings,
      'implementationEffort': EstimateEffort(recommendations)
    }
  END
END FUNCTION
```

---

### Algorithm 1.4: Component Removal Recommender

**Purpose**: Recommend removing low-value, high-license menu items from a role

**Input**:
- `RoleLicenseComposition`: From Algorithm 1.1
- `UserActivityData`: User activity by menu item
- `RoleName`: Role to analyze
- `UserSegments`: User segment data

**Output**:
```
Recommendation for Role X:
  ├── Remove Components?: YES/NO
  ├── Components to Remove:
  │   ├── Menu Item: [Name]
  │   │   ├── License Type: [License]
  │   │   ├── Users Affected: N
  │   │   ├── Usage Frequency: Low (< 5% users)
  │   │   └── Impact: [Low/Medium/High]
  └── Expected Outcome: [Description]
```

**Pseudocode**:

```
FUNCTION RecommendComponentRemoval(roleName)
  BEGIN
    // Get all users with this role
    users ← GetUsersWithRole(roleName)

    // Get role's menu items and their license types
    roleMenuItems ← GetMenuItemsForRole(roleName)

    removalCandidates ← []

    FOR EACH menuItem IN roleMenuItems
      // Skip if not a high-license item
      IF menuItem.LicenseType NOT IN ['Commerce', 'Finance', 'SCM'] THEN
        CONTINUE
      END IF

      // Check how many users actually used this menu item
      usersWhoUsed ← 0
      FOR EACH user IN users
        userActivity ← GetUserActivity(user.id, days=90)
        IF userActivity.CONTAINS(menuItem) THEN
          usersWhoUsed ← usersWhoUsed + 1
        END IF
      END FOR

      // Calculate usage percentage
      usagePercentage ← (usersWhoUsed / COUNT(users)) * 100

      // If low usage, consider for removal
      IF usagePercentage < 5 THEN  // Configurable threshold
        // Determine impact
        impact ← AssessRemovalImpact(menuItem, usersWhoUsed)

        removalCandidates.APPEND({
          'menuItem': menuItem.name,
          'licenseType': menuItem.LicenseType,
          'usersAffected': usersWhoUsed,
          'usagePercentage': usagePercentage,
          'impact': impact,
          'recommendation': 'REMOVE - Low usage, high license requirement'
        })
      END IF
    END FOR

    // Sort by impact (low impact first)
    removalCandidates.SORT_BY('impact')

    RETURN {
      'shouldRemove': COUNT(removalCandidates) > 0,
      'componentsToRemove': removalCandidates,
      'expectedOutcome': 'Remove ' + COUNT(removalCandidates) + ' low-usage, high-license menu items to reduce overall license requirement.'
    }
  END
END FUNCTION
```

---

## Scenario 2: User-Level Behavioral Optimization

### Overview

Analyze individual user behavior to identify optimization opportunities through:
- Permission vs. actual usage comparison
- Read-only user detection
- Role usage pattern analysis
- Multi-role optimization

---

### Algorithm 2.1: Permission vs. Usage Analyzer

**Purpose**: Compare what a user CAN do (permissions) vs. what they ACTUALLY do (usage)

**Input**:
- `UserId`: User to analyze
- `UserRoleAssignments`: User's assigned roles
- `SecurityConfigurationData`: Role → Menu Item → License mapping
- `UserActivityData`: User's actual activity (last 90 days)

**Output**:
```
For User X:
  ├── Assigned License: [License Type]
  ├── Assigned Roles: [List]
  ├── Theoretical Permissions:
  │   ├── Menu Items Available: N1
  │   ├── Write Operations Allowed: N2
  │   └── Read Operations Allowed: N3
  ├── Actual Usage (Last 90 Days):
  │   ├── Unique Menu Items Used: N4
  │   ├── Write Operations: N5 (percentage %)
  │   └── Read Operations: N6 (percentage %)
  ├── Permission Utilization: X%
  ├── Optimization Opportunities: [List]
  └── Cost Impact: [Analysis]
```

**Pseudocode**:

```
FUNCTION AnalyzePermissionVsUsage(userId)
  BEGIN
    // Get user's assigned roles
    userRoles ← GetUserRoles(userId)

    // Get all menu items user has access to (theoretical)
    theoreticalPermissions ← EMPTY_SET
    FOR EACH role IN userRoles
      roleMenuItems ← GetMenuItemsForRole(role)
      theoreticalPermissions.ADD_ALL(roleMenuItems)
    END FOR

    // Get user's actual activity
    userActivity ← GetUserActivity(userId, days=90)

    // Analyze actual usage
    actualMenuItemsUsed ← EMPTY_SET
    writeOperations ← 0
    readOperations ← 0

    FOR EACH activity IN userActivity
      actualMenuItemsUsed.ADD(activity.menuItem)

      IF activity.action IN ['Write', 'Update', 'Create', 'Delete'] THEN
        writeOperations ← writeOperations + 1
      ELSE IF activity.action = 'Read' THEN
        readOperations ← readOperations + 1
      END IF
    END FOR

    // Calculate metrics
    permissionUtilization ← (COUNT(actualMenuItemsUsed) / COUNT(theoreticalPermissions)) * 100
    totalOperations ← writeOperations + readOperations
    writePercentage ← (writeOperations / totalOperations) * 100
    readPercentage ← (readOperations / totalOperations) * 100

    // Identify optimization opportunities
    opportunities ← []

    // Check 1: Read-only user
    IF readPercentage > 95 THEN
      opportunities.APPEND({
        'type': 'DOWNGRADE_LICENSE',
        'description': 'User is 95%+ read-only. Consider Team Members license.',
        'potentialSavings': CalculateSavings(currentLicense, 'Team Members')
      })
    END IF

    // Check 2: Unused menu items (theoretical permissions)
    unusedPermissions ← theoreticalPermissions.MINUS(actualMenuItemsUsed)
    IF COUNT(unusedPermissions) > (COUNT(theoreticalPermissions) * 0.5) THEN
      opportunities.APPEND({
        'type': 'REDUCE_PERMISSIONS',
        'description': 'User uses less than 50% of available menu items. Consider role cleanup.',
        'unusedItemCount': COUNT(unusedPermissions)
      })
    END IF

    // Check 3: Specific license type usage
    usedLicenses ← GetLicensesForMenuItems(actualMenuItemsUsed)
    assignedLicense ← GetHighestLicenseForRoles(userRoles)

    IF assignedLicense NOT IN usedLicenses AND usedLicenses.CONTAINS('Team Members') THEN
      opportunities.APPEND({
        'type': 'DOWNGRADE_LICENSE',
        'description': 'User only uses Team Members license features. Current license: ' + assignedLicense,
        'potentialSavings': CalculateSavings(assignedLicense, 'Team Members')
      })
    END IF

    RETURN {
      'userId': userId,
      'assignedLicense': assignedLicense,
      'assignedRoles': userRoles,
      'theoreticalPermissions': {
        'menuItemsAvailable': COUNT(theoreticalPermissions),
        'uniqueItems': theoreticalPermissions
      },
      'actualUsage': {
        'menuItemsUsed': COUNT(actualMenuItemsUsed),
        'writeOperations': writeOperations,
        'writePercentage': writePercentage,
        'readOperations': readOperations,
        'readPercentage': readPercentage
      },
      'permissionUtilization': permissionUtilization,
      'optimizationOpportunities': opportunities
    }
  END
END FUNCTION
```

---

### Algorithm 2.2: Read-Only User Detector (Enhanced)

**Purpose**: Identify users who primarily perform read operations with high confidence

**Input**:
- `UserActivityData`: User activity for all users (last 90 days)
- `SecurityConfigurationData`: Menu item → License mapping

**Output**:
```
Read-Only Users:
  ├── User: [Name]
  │   ├── Current License: [License]
  │   ├── Read Operations: N1 (%)
  │   ├── Write Operations: N2 (%)
  │   ├── Recommendation: [Team Members | Operations Activity | No Downgrade]
  │   ├── Confidence: [Low/Medium/High]
  │   └── Estimated Savings: $X/month
  └── [Detailed breakdown per user]
```

**Pseudocode**:

```
FUNCTION DetectReadOnlyUsers(allUsers, readThreshold = 95)
  BEGIN
    readOnlyCandidates ← []

    FOR EACH user IN allUsers
      // Get user activity
      userActivity ← GetUserActivity(user.id, days=90)

      IF COUNT(userActivity) = 0 THEN
        CONTINUE  // Skip inactive users (handled separately)
      END IF

      // Count operations by type
      readOps ← 0
      writeOps ← 0

      FOR EACH activity IN userActivity
        IF activity.action IN ['Write', 'Update', 'Create', 'Delete'] THEN
          writeOps ← writeOps + 1
        ELSE IF activity.action = 'Read' THEN
          readOps ← readOps + 1
        END IF
      END FOR

      totalOps ← readOps + writeOps
      readPercentage ← (readOps / totalOps) * 100

      // Check if meets threshold
      IF readPercentage >= readThreshold THEN
        // Analyze write operations to assess confidence
        confidence ← AssessReadOnlyConfidence(userActivity, writeOps)

        // Get current license
        currentLicense ← GetUserLicense(user.id)

        // NEW: Validate Team Members form eligibility
        accessedForms ← GetUniqueFormsAccessed(userActivity)
        teamMembersEligibleForms ← GetTeamMembersEligibleForms()
        nonEligibleForms ← accessedForms.MINUS(teamMembersEligibleForms)

        IF COUNT(nonEligibleForms) = 0 THEN
          recommendedLicense ← 'Team Members'
        ELSE IF AllFormsEligibleForActivity(nonEligibleForms) THEN
          recommendedLicense ← 'Operations Activity'
        ELSE
          recommendedLicense ← currentLicense  // Cannot downgrade
        END IF

        // Calculate savings based on determined license
        potentialSavings ← CalculateSavings(currentLicense, recommendedLicense)

        readOnlyCandidates.APPEND({
          'userId': user.id,
          'userName': user.name,
          'currentLicense': currentLicense,
          'readOperations': readOps,
          'readPercentage': readPercentage,
          'writeOperations': writeOps,
          'writePercentage': (writeOps / totalOps) * 100,
          'recommendation': recommendedLicense,
          'nonEligibleForms': nonEligibleForms,
          'confidence': confidence,
          'estimatedSavingsPerMonth': potentialSavings
        })
      END IF
    END FOR

    // Sort by savings (highest first)
    readOnlyCandidates.SORT_BY_DESCENDING('estimatedSavingsPerMonth')

    RETURN readOnlyCandidates
  END
END FUNCTION

FUNCTION AssessReadOnlyConfidence(userActivity, writeOpCount)
  BEGIN
    // Analyze write operations to determine confidence
    confidenceFactors ← []

    IF writeOpCount = 0 THEN
      RETURN 'HIGH - 100% read-only, zero write operations'
    END IF

    IF writeOpCount <= 2 THEN
      confidenceFactors.APPEND('HIGH - Only ' + writeOpCount + ' write operations in 90 days')
    ELSE IF writeOpCount <= 10 THEN
      confidenceFactors.APPEND('MEDIUM - ' + writeOpCount + ' write operations in 90 days')
    ELSE
      confidenceFactors.APPEND('LOW - ' + writeOpCount + ' write operations in 90 days')
    END IF

    // Check if writes are self-service updates (acceptable for Team Members)
    selfServiceWrites ← 0
    FOR EACH activity IN userActivity
      IF activity.action IN ['Write', 'Update'] AND
         activity.menuItem CONTAINS 'My' OR
         activity.menuItem CONTAINS 'SelfService' THEN
        selfServiceWrites ← selfServiceWrites + 1
      END IF
    END FOR

    IF selfServiceWrites = writeOpCount THEN
      confidenceFactors.APPEND('HIGH - All writes are self-service operations')
    END IF

    RETURN confidenceFactors.JOIN('; ')
  END
END FUNCTION
```

---

### Team Members License Form Eligibility

> **⚠️ TODO**: The `TEAM_MEMBERS_ELIGIBLE_FORMS` list below needs validation against current Microsoft D365 FO documentation. This is a critical dependency for Algorithm 2.2's downgrade recommendations.

**Background**: Team Members licenses in D365 FO can ONLY access a designated subset of forms. Even if a user is 99% read-only, they **cannot** be downgraded to Team Members if they access forms outside the eligible list.

**Eligible Form Categories** (Team Members):
- **Employee Self-Service**: `HcmESSWorkspace`, `HcmMyExpenses`, `HcmMyLeaveRequests`, `HcmMyTimeRegistration`
- **Approval Workflows**: Standard workflow approval forms across all modules
- **Specific Inquiry Forms**: Designated read-only inquiry forms per Microsoft documentation
- **Address Book**: `DirPartyTable` (read-only), contact information lookups

**NOT Eligible for Team Members** (even in read-only):
- `GeneralJournalEntry` — General Ledger posting form
- `CustTable` — Customer master data
- `VendTable` — Vendor master data
- `PurchTable` — Purchase order form
- `SalesTable` — Sales order form
- `InventJournalTable` — Inventory journal form
- Most module-specific transaction and master data forms

**Configuration Requirement**:
```
TEAM_MEMBERS_ELIGIBLE_FORMS configuration table:
├── FormName: D365 FO form name
├── Module: Functional module
├── AccessLevel: Read | ReadWrite
├── Source: Microsoft documentation reference
└── LastValidated: Date of last validation
```

**Operations Activity Eligible Forms**: A separate `OPERATIONS_ACTIVITY_ELIGIBLE_FORMS` table is needed for forms that don't qualify for Team Members but may qualify for the Operations Activity license tier (activity-based access rather than full license).

> **Status**: Form eligibility lists need to be compiled from Microsoft's official licensing guide and validated in a D365 FO test environment. This is a pre-production blocker for Algorithm 2.2 recommendations.

---

### Algorithm 2.3: Role Segmentation by Usage Pattern

**Purpose**: For a role with mixed licenses (e.g., Finance + SCM), analyze if users segment by usage

**Input**:
- `RoleName`: Role to analyze
- `UserActivityData`: Activity for all users with this role
- `SecurityConfigurationData`: Menu item → License mapping
- `UserRoleAssignments`: User → Role mapping

**Output**:
```
Role: [Name] (Mixed License)
├── Total Users: N
├── Usage Segmentation:
│   ├── Finance-Only Users: N1 (%)
│   ├── SCM-Only Users: N2 (%)
│   ├── Mixed Users: N3 (%)
├── Recommendations:
│   ├── Option A: Split into 2 roles (Finance, SCM)
│   │   ├── Users Affected: N4
│   │   └── Estimated Savings: $X/month
│   └── Option B: Create Finance-Read variant
│       ├── Users for Read variant: N5
│       └── Estimated Savings: $Y/month
```

**Pseudocode**:

```
FUNCTION AnalyzeRoleUsageSegmentation(roleName)
  BEGIN
    // Get all users with this role
    users ← GetUsersWithRole(roleName)

    // Get menu items for this role by license type
    roleMenuItems ← GetMenuItemsForRole(roleName)
    menuItemsByLicense ← GroupMenuItemsByLicense(roleMenuItems)

    // Initialize user segments
    financeOnlyUsers ← []
    scmOnlyUsers ← []
    mixedUsers ← []

    FOR EACH user IN users
      // Get user's activity
      userActivity ← GetUserActivity(user.id, days=90)

      // Track which license types user accessed
      licensesAccessed ← EMPTY_SET

      FOR EACH activity IN userActivity
        // Find which license this menu item requires
        menuItemLicense ← FindLicenseForMenuItem(activity.menuItem, menuItemsByLicense)

        IF menuItemLicense = 'Finance' THEN
          licensesAccessed.ADD('Finance')
        ELSE IF menuItemLicense = 'SCM' THEN
          licensesAccessed.ADD('SCM')
        END IF
      END FOR

      // Categorize user
      IF licensesAccessed.CONTAINS_ONLY('Finance') THEN
        financeOnlyUsers.APPEND(user)
      ELSE IF licensesAccessed.CONTAINS_ONLY('SCM') THEN
        scmOnlyUsers.APPEND(user)
      ELSE IF COUNT(licensesAccessed) > 1 THEN
        mixedUsers.APPEND(user)
      END IF
    END FOR

    // Calculate percentages
    totalUsers ← COUNT(users)
    financeOnlyPct ← (COUNT(financeOnlyUsers) / totalUsers) * 100
    scmOnlyPct ← (COUNT(scmOnlyUsers) / totalUsers) * 100
    mixedPct ← (COUNT(mixedUsers) / totalUsers) * 100

    // Generate recommendations
    recommendations ← []

    // Recommendation 1: Split roles if we have significant single-license usage
    IF financeOnlyPct > 20 OR scmOnlyPct > 20 THEN
      splitSavings ← CalculateSplitSavings(
        financeOnlyUsers,
        scmOnlyUsers,
        currentLicense: 'Finance + SCM'
      )

      recommendations.APPEND({
        'option': 'Split into separate Finance and SCM roles',
        'usersAffected': COUNT(financeOnlyUsers) + COUNT(scmOnlyUsers),
        'estimatedSavingsPerMonth': splitSavings,
        'implementation': 'Create Role-Finance and Role-SCM, reassign exclusive users'
      })
    END IF

    // Recommendation 2: Create read-only variant if applicable
    readVariantAnalysis ← AnalyzeReadVariantOpportunity(
      mixedUsers,
      menuItemsByLicense
    )

    IF readVariantAnalysis.potentialSavings > 0 THEN
      recommendations.APPEND({
        'option': 'Create read-only variant for Finance portion',
        'usersAffected': readVariantAnalysis.userCount,
        'estimatedSavingsPerMonth': readVariantAnalysis.potentialSavings,
        'implementation': 'Create Role-Finance-Read with read-only access to Finance menu items'
      })
    END IF

    RETURN {
      'roleName': roleName,
      'totalUsers': totalUsers,
      'usageSegmentation': {
        'financeOnly': {
          'count': COUNT(financeOnlyUsers),
          'percentage': financeOnlyPct
        },
        'scmOnly': {
          'count': COUNT(scmOnlyUsers),
          'percentage': scmOnlyPct
        },
        'mixed': {
          'count': COUNT(mixedUsers),
          'percentage': mixedPct
        }
      },
      'recommendations': recommendations
    }
  END
END FUNCTION
```

---

### Algorithm 2.4: Multi-Role Optimization

**Purpose**: For users with multiple roles, analyze if role consolidation or license optimization is possible

**Input**:
- `UserId`: User to analyze
- `UserRoleAssignments`: User's assigned roles
- `UserActivityData`: User's actual activity
- `SecurityConfigurationData`: Role → License mapping

**Output**:
```
Multi-Role User Analysis: [User]
├── Assigned Roles: N
├── Current License: [Highest]
├── Role Usage:
│   ├── Role 1: [Usage %]
│   ├── Role 2: [Usage %]
│   └── Role 3: [Usage %]
├── Optimization Options:
│   ├── Option 1: Remove unused roles
│   ├── Option 2: Consolidate similar roles
│   └── Option 3: Downgrade license based on actual usage
└── Cost Impact: [Analysis]
```

**Pseudocode**:

```
FUNCTION OptimizeMultiRoleUser(userId)
  BEGIN
    // Get user's roles
    userRoles ← GetUserRoles(userId)

    IF COUNT(userRoles) <= 1 THEN
      RETURN {
        'isMultiRole': FALSE,
        'message': 'User has only one role. No multi-role optimization needed.'
      }
    END IF

    // Get user's activity
    userActivity ← GetUserActivity(userId, days=90)

    // Analyze usage for each role
    roleUsage ← []
    unusedRoles ← []

    FOR EACH role IN userRoles
      // Get menu items for this role
      roleMenuItems ← GetMenuItemsForRole(role)

      // Check how many role menu items user actually accessed
      accessedMenuItems ← 0
      FOR EACH activity IN userActivity
        IF roleMenuItems.CONTAINS(activity.menuItem) THEN
          accessedMenuItems ← accessedMenuItems + 1
        END IF
      END FOR

      // Calculate usage percentage
      usagePercentage ← (accessedMenuItems / COUNT(roleMenuItems)) * 100

      roleUsage.APPEND({
        'roleName': role,
        'totalMenuItems': COUNT(roleMenuItems),
        'accessedMenuItems': accessedMenuItems,
        'usagePercentage': usagePercentage
      })

      // Track unused roles
      IF usagePercentage = 0 THEN
        unusedRoles.APPEND(role)
      END IF
    END FOR

    // Determine current license (highest among roles)
    currentLicense ← GetHighestLicenseForRoles(userRoles)

    // Determine actual license needed based on usage
    accessedMenuItems ← GetUniqueMenuItemsFromActivity(userActivity)
    requiredLicense ← GetRequiredLicenseForMenuItems(accessedMenuItems)

    // Generate optimization recommendations
    recommendations ← []

    // Option 1: Remove unused roles
    IF COUNT(unusedRoles) > 0 THEN
      recommendations.APPEND({
        'option': 'Remove unused roles',
        'rolesToRemove': unusedRoles,
        'impact': 'Remove ' + COUNT(unusedRoles) + ' unused roles. No access impact.',
        'licenseImpact': 'No change (current license based on active roles)'
      })
    END IF

    // Option 2: License downgrade
    IF requiredLicense != currentLicense THEN
      savings ← CalculateSavings(currentLicense, requiredLicense)
      recommendations.APPEND({
        'option': 'Downgrade license based on actual usage',
        'currentLicense': currentLicense,
        'recommendedLicense': requiredLicense,
        'estimatedSavingsPerMonth': savings,
        'impact': 'Downgrade from ' + currentLicense + ' to ' + requiredLicense
      })
    END IF

    // Option 3: Consolidate similar roles (if applicable)
    consolidationAnalysis ← AnalyzeRoleConsolidationOpportunity(userRoles, userActivity)
    IF consolidationAnalysis.hasOpportunity THEN
      recommendations.APPEND(consolidationAnalysis.recommendation)
    END IF

    RETURN {
      'userId': userId,
      'isMultiRole': TRUE,
      'assignedRoles': userRoles,
      'roleCount': COUNT(userRoles),
      'currentLicense': currentLicense,
      'roleUsage': roleUsage,
      'requiredLicenseBasedOnUsage': requiredLicense,
      'optimizationRecommendations': recommendations
    }
  END
END FUNCTION
```

---

## Decision Trees

### Decision Tree 1: Role Splitting

```
START: Role Analysis
│
├─ Does role have menu items from multiple license types?
│  │
│  ├─ NO → Don't split. Single license type role.
│  │
│  └─ YES → Check user segments
│     │
│     ├─ Do users segment by license type? (e.g., some only use Finance, some only SCM)
│     │  │
│     │  ├─ YES → Recommend splitting into separate roles
│     │  │   ├─ Calculate savings per segment
│     │  │   └─ Create variant roles
│     │  │
│     │  └─ NO → Check if small number of menu items drive high license
│     │      │
│     │      ├─ YES → Recommend component removal (Algorithm 1.4)
│     │      │
│     │      └─ NO → Don't split. High mixed usage.
│     │
└─ END
```

### Decision Tree 2: License Downgrade

```
START: User License Analysis
│
├─ Get user's read vs. write percentage (last 90 days)
│  │
├─ Is read percentage > 95%?
│  │
│  ├─ YES → Candidate for license downgrade
│  │  │
│  │  ├─ Analyze write operations
│  │  │  ├─ Are writes self-service only? (e.g., "MyProfile", "MyPreferences")
│  │  │  │  ├─ YES → HIGH confidence
│  │  │  │  └─ NO → MEDIUM confidence
│  │  │
│  │  └─ Check Team Members form eligibility ⭐ NEW
│  │     │
│  │     ├─ Get all forms user accessed
│  │     ├─ Compare against TEAM_MEMBERS_ELIGIBLE_FORMS
│  │     │
│  │     ├─ ALL forms eligible for Team Members?
│  │     │  └─ YES → Recommend Team Members license
│  │     │
│  │     ├─ Some forms NOT eligible for Team Members?
│  │     │  └─ Check OPERATIONS_ACTIVITY_ELIGIBLE_FORMS
│  │     │     ├─ ALL non-TM forms eligible for Activity?
│  │     │     │  └─ YES → Recommend Operations Activity license
│  │     │     └─ NO → Cannot downgrade (keep current license)
│  │     │
│  │     └─ NO eligible forms match?
│  │        └─ Keep current license (false positive)
│  │
│  ├─ NO (mixed read/write) → Check actual license requirements
│  │  │
│  │  └─ Get highest license type from actually accessed menu items
│  │     │
│  │     ├─ Is actual license < assigned license?
│  │     │  ├─ YES → Recommend downgrade
│  │     │  └─ NO → Correctly licensed
│  │
└─ END
```

### Decision Tree 3: Component Removal

```
START: Component Removal Analysis
│
├─ For each menu item in role:
│  │
│  ├─ Is menu item high-license type? (Finance, SCM, Commerce)
│  │  │
│  │  ├─ NO → Skip removal (low impact)
│  │  │
│  │  └─ YES → Check usage percentage
│  │     │
│  │     ├─ Is usage < 5% of users with this role?
│  │     │  │
│  │     │  ├─ YES → Candidate for removal
│  │     │  │  │
│  │     │  │  ├─ Assess impact:
│  │     │  │  │  ├─ Is menu item critical? (e.g., approval, posting)
│  │     │  │  │  │  ├─ YES → Flag for manual review
│  │     │  │  │  │  └─ NO → Recommend removal
│  │     │  │  │  │
│  │     │  │  │  └─ Who are the users?
│  │     │  │     └─ Can they be assigned a different role?
│  │     │  │
│  │     │  └─ NO → Don't remove (widely used)
│  │     │
└─ END
```

---

## Configurable Parameters

### Thresholds

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `READ_ONLY_THRESHOLD` | 95% | 80-99% | Minimum read percentage to consider user as read-only |
| `LOW_USAGE_THRESHOLD` | 5% | 1-10% | Maximum usage percentage to flag menu item for removal |
| `INACTIVE_DAYS` | 90 | 30-365 | Days of inactivity to flag user as inactive |
| `MIN_SEGMENT_SIZE` | 20% | 10-50% | Minimum % of users to recommend role split |
| `MIN_LICENSE_PERCENTAGE` | 10% | 5-25% | Minimum % of menu items to consider license type significant |
| `ACTIVITY_ANALYSIS_DAYS` | 90 | 30-180 | Days to look back for user activity analysis. Cross-reference with 12-month seasonal profile to avoid false positives during off-seasons. |

### License Costs (Monthly)

| License Type | List Price | Customer Override | Effective Price | Used For |
|--------------|-----------|-------------------|-----------------|----------|
| `TEAM_MEMBERS` | $60 | _(configurable)_ | = Override or $60 | Read-only users |
| `OPERATIONS_ACTIVITY` | ~$90 | _(configurable)_ | = Override or ~$90 | Activity-based users |
| `FINANCE` | $180 | _(configurable)_ | = Override or $180 | Finance full users |
| `SCM` | $180 | _(configurable)_ | = Override or $180 | SCM full users |
| `COMMERCE` | $180 | _(configurable)_ | = Override or $180 | Commerce full users |
| `FINANCE_SCM` | $210 | _(configurable)_ | = Override or $210 | Combined Finance + SCM |

**Pricing Configuration**:
- **Default**: Microsoft list prices (shown above)
- **Override**: Customers can configure actual EA/CSP negotiated rates via the admin settings
- **Currency**: Configurable (default USD)
- **Update frequency**: Annual review recommended (Microsoft fiscal year pricing changes)
- **All savings calculations use Effective Price**, not List Price, when overrides are configured
- **Function**: `GetEffectiveLicenseCost(licenseType)` returns Customer Override if set, else List Price

```
FUNCTION GetEffectiveLicenseCost(licenseType)
  BEGIN
    customerOverride ← GetCustomerPriceOverride(licenseType)
    IF customerOverride IS NOT NULL THEN
      RETURN customerOverride
    ELSE
      RETURN GetListPrice(licenseType)
    END IF
  END
END FUNCTION
```

> **Note**: All `CalculateSavings()` function calls throughout this document use `GetEffectiveLicenseCost()` internally. When customer overrides are configured, savings projections automatically reflect actual negotiated rates rather than list prices.

### Seasonal Awareness

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `SEASONAL_LOOKBACK_MONTHS` | 12 | 6-24 | Months of history to analyze for seasonal patterns |
| `SEASONAL_INACTIVITY_THRESHOLD` | 60 | 30-90 | Consecutive inactive days to trigger seasonal pattern detection |
| `SEASONAL_FREEZE_DAYS_BEFORE_CLOSE` | 5 | 3-10 | Business days before period close to freeze license changes |
| `SEASONAL_FREEZE_DAYS_AFTER_CLOSE` | 5 | 3-10 | Business days after period close to freeze license changes |

**Seasonal Profile Concept**:

Users can be tagged with seasonal usage profiles based on 12-month rolling activity analysis:

| Profile | Description | Example Users |
|---------|-------------|---------------|
| `YEAR_ROUND` | Consistent activity throughout the year | Most operational users |
| `SEASONAL_Q4` | Heavy usage in Q4, light otherwise | Budget planners |
| `SEASONAL_YEAR_END` | Active Dec-Jan for year-end close | Accounting/GL staff |
| `SEASONAL_AUDIT` | Active during audit periods | Internal audit, compliance |
| `SEASONAL_CUSTOM` | Admin-defined seasonal period | Custom business cycles |

**Seasonal Detection Logic**:
```
FUNCTION DetectSeasonalProfile(userId, lookbackMonths = 12)
  BEGIN
    monthlyActivity ← GetMonthlyActivityCounts(userId, lookbackMonths)

    // Identify months with >60 days inactivity followed by intensive usage
    inactiveMonths ← monthlyActivity.FILTER(count = 0 OR count < 5)
    activeMonths ← monthlyActivity.FILTER(count > 50)

    IF COUNT(inactiveMonths) >= 3 AND COUNT(activeMonths) >= 2 THEN
      // User has seasonal pattern
      peakMonths ← activeMonths.GET_MONTH_NUMBERS()
      RETURN ClassifySeasonalProfile(peakMonths)
    ELSE
      RETURN 'YEAR_ROUND'
    END IF
  END
END FUNCTION
```

**Seasonal Risk Indicator**:
- `SEASONAL_RISK_HIGH`: Recommendation to downgrade coincides with user's known active season approaching within 60 days
- `SEASONAL_RISK_MEDIUM`: User has seasonal profile but not approaching active season
- `SEASONAL_RISK_LOW`: User is `YEAR_ROUND` or approaching off-season

**Admin-Configurable Seasonal Periods**:
- **Year-end close**: December-January (default, configurable)
- **Budget cycle**: September-October (configurable)
- **Audit period**: Fully configurable per organization
- **Custom periods**: Admin can define any recurring period

> **Important**: Before flagging a user as inactive or read-only (Algorithms 2.2, inactive user detection), check their seasonal profile. If the current period is their known off-season, **reduce confidence** and add a seasonal risk warning to the recommendation. This prevents incorrectly downgrading users who will need full access in their upcoming active season.

---

## Example Calculations

### Example 1: Role Splitting

**Scenario**: Accountant role with 150 menu items
- 120 menu items → Finance license
- 30 menu items → SCM license
- 100 users assigned
- Analysis shows:
  - 90 users only use Finance menu items
  - 5 users only use SCM menu items
  - 5 users use both

**Calculation**:

```
Current State:
├─ All 100 users require Finance + SCM license
├─ Cost per user: $210/month
└─ Total monthly cost: $21,000

After Split:
├─ Accountant-Finance role: 90 users
│  ├─ License: Finance ($180/month)
│  └─ Cost: $16,200/month
│
├─ Accountant-SCM role: 5 users
│  ├─ License: SCM ($180/month)
│  └─ Cost: $900/month
│
└─ Accountant-Full role: 5 users
   ├─ License: Finance + SCM ($210/month)
   └─ Cost: $1,050/month

Total After Split: $18,150/month
Monthly Savings: $21,000 - $18,150 = $2,850
Annual Savings: $34,200
```

---

### Example 2: Component Removal

**Scenario**: Purchasing Agent role with 15 menu items
- 14 menu items → SCM license
- 1 menu item → Finance license (Bank reconciliation)
- 50 users assigned
- Analysis shows:
  - Only 2 users (4%) used Bank reconciliation in last 90 days

**Calculation**:

```
Current State:
├─ All 50 users require Finance + SCM license (due to 1 Finance menu item)
├─ Cost per user: $210/month
└─ Total monthly cost: $10,500

After Component Removal:
├─ Remove Bank reconciliation from Purchasing Agent role
├─ 48 users: SCM license only ($180/month)
│  └─ Cost: $8,640/month
│
├─ 2 users: Add dedicated Finance role + SCM
│  └─ Cost: $210/month × 2 = $420/month
│
└─ Total: $9,060/month

Monthly Savings: $10,500 - $9,060 = $1,440
Annual Savings: $17,280
Implementation Effort: Low (remove 1 menu item from role)
```

---

### Example 3: Read-Only User Detection

**Scenario**: User John Doe with Commerce license
- Assigned role: Accountant
- Last 90 days activity:
  - 847 Read operations (99.76%)
  - 2 Write operations (0.24%)
  - Analysis: Both writes were "MyProfile" updates (self-service)

**Calculation**:

```
Current State:
├─ License: Commerce ($180/month)
├─ Annual cost: $2,160
└─ Usage: 99.76% read-only

Analysis:
├─ Read percentage: 99.76% (> 95% threshold) ✅
├─ Write operations: 2 (self-service updates) ✅
├─ Confidence: HIGH
└─ Recommendation: Downgrade to Team Members

After Downgrade:
├─ License: Team Members ($60/month)
├─ Annual cost: $720
└─ Users retain access: All read operations, self-service writes

Annual Savings: $2,160 - $720 = $1,440
Risk: LOW (self-service writes allowed in Team Members)
```

---

### Example 4: Multi-Role Optimization

**Scenario**: User Jane Smith with 3 roles
- Role 1: Accountant (Finance license) - 100 menu items
- Role 2: Purchasing Clerk (SCM license) - 50 menu items
- Role 3: Budget Viewer (Team Members license) - 20 menu items
- Current license: Finance + SCM ($210/month) - highest required
- Last 90 days:
  - Accessed 95/100 Accountant menu items
  - Accessed 2/50 Purchasing Clerk menu items
  - Accessed 18/20 Budget Viewer menu items

**Calculation**:

```
Current State:
├─ Roles: 3
├─ License: Finance + SCM ($210/month)
├─ Annual cost: $2,520
└─ Role usage:
   ├─ Accountant: 95% (actively using)
   ├─ Purchasing Clerk: 4% (barely using)
   └─ Budget Viewer: 90% (actively using)

Recommendation:
├─ Remove Purchasing Clerk role (only 4% usage)
├─ Keep Accountant + Budget Viewer
├─ Required license: Finance ($180/month)
└─ Annual cost: $2,160

Annual Savings: $2,520 - $2,160 = $360
Implementation Effort: Low (remove 1 unused role)
```

---

## 📝 Key Implementation Notes

### Data Requirements

All algorithms require access to:
1. **Security Configuration Data** (Live)
   - Role → Menu Item → License mapping
   - Entitlement status

2. **User-Role Assignment Data** (Live)
   - User → Role mappings
   - User details

3. **User Activity Telemetry** (Live)
   - User → Menu Item → Action (Read/Write)
   - Timestamps
   - Session context

### Performance Considerations

- **Caching**: Cache menu item → license mappings (infrequently changes)
- **Batch Processing**: Process users in batches for role analysis
- **Incremental Updates**: Update analysis daily/weekly (not real-time)
- **Pre-aggregation**: Pre-calculate role license compositions

### Confidence Levels

**HIGH Confidence Recommendations**:
- Read-only users (> 95% read, < 5 writes, all self-service)
- Large user segments (> 50 users) with clear usage patterns
- Low-usage component removal (< 2% users affected)

**MEDIUM Confidence Recommendations**:
- Read-only users (90-95% read)
- Medium user segments (20-50 users)
- Component removal (2-5% users affected)

**LOW Confidence Recommendations**:
- Read-only users (80-90% read)
- Small user segments (< 20 users)
- Component removal (> 5% users affected) - requires manual review

---

## 🚀 Next Steps

### Phase 1: Requirements ✅
- [x] Document data sources and capabilities
- [x] Define core functional requirements
- [x] Design algorithms for optimization scenarios
- [x] Create decision trees
- [ ] Validate algorithms with stakeholders

### Phase 2: Technical Design (Future) ⏳
- [ ] Determine data access methods
- [ ] Select Azure services
- [ ] Design data architecture
- [ ] Define performance optimization strategies

### Phase 3: Implementation (Future) ⏳
- [ ] Implement algorithms
- [ ] Build recommendation engine
- [ ] Create dashboards and UI
- [ ] Test and validate

---

## 📚 Related Documentation

- `05-Functional-Requirements.md` - Core functional requirements
- `02-Security-Configuration-Data.md` - Security data source
- `03-User-Role-Assignment-Data.md` - User-role data source
- `04-User-Activity-Telemetry-Data.md` - Telemetry data source

---

**Document Status**: Requirements Definition - Algorithm Design Complete ✅
**Next Review**: After stakeholder validation
**Note**: All algorithms use pseudocode. Actual implementation will be designed in technical phase.

---

**End of Algorithms & Decision Logic Document**
