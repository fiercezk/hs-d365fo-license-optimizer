# Advanced Algorithms Expansion - D365 FO License & Security Optimization

**Project**: D365 FO License & Security Optimization Agent
**Last Updated**: 2026-02-05
**Status**: Requirements Definition - Advanced Algorithm Research
**Version**: 1.0

---

## 📑 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Algorithm Inventory](#algorithm-inventory)
3. [High-Priority Security & Compliance Algorithms](#high-priority-security--compliance-algorithms)
4. [High-Priority Cost Optimization Algorithms](#high-priority-cost-optimization-algorithms)
5. [Medium-Priority Algorithms](#medium-priority-algorithms)
6. [Advanced ML-Based Algorithms](#advanced-ml-based-algorithms)
7. [Algorithm Selection Framework](#algorithm-selection-framework)
8. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

### Current State

**Documented Algorithms** (in `06-Algorithms-Decision-Logic.md`):
- 8 core algorithms for role analysis and user optimization
- Focus: License cost optimization through behavioral analysis

### Research Findings

Based on comprehensive analysis of:
- D365 FO licensing model and optimization patterns
- Microsoft's native security capabilities and gaps
- Security reports and audit requirements
- Industry best practices for access governance

**Identified**: 22 additional high-value algorithms across 6 major categories

### Value Proposition

| Algorithm Category | Count | Business Value | Implementation Complexity |
|-------------------|-------|----------------|---------------------------|
| **Security & Compliance** | 8 | Critical (SOX, GDPR, ISO) | Medium |
| **Cost Optimization** | 6 | High (15-30% savings) | Low-Medium |
| **User Behavior Analytics** | 4 | High (security + cost) | Medium |
| **Advanced Analytics** | 4 | Medium-High | High |

**Total Potential Value**: $500K - $2M+ annual savings for enterprise deployments

---

## Algorithm Inventory

### Previously Documented (8 Algorithms)

| ID | Algorithm | Category | Priority | Document |
|----|-----------|----------|----------|----------|
| 1.1 | Role License Composition Analyzer | Cost | High | 06 |
| 1.2 | User Segment Analyzer | Cost | High | 06 |
| 1.3 | Role Splitting Recommender | Cost | High | 06 |
| 1.4 | Component Removal Recommender | Cost | High | 06 |
| 2.1 | Permission vs. Usage Analyzer | Cost | High | 06 |
| 2.2 | Read-Only User Detector | Cost | High | 06 |
| 2.3 | Role Segmentation by Usage Pattern | Cost | High | 06 |
| 2.4 | Multi-Role Optimization | Cost | High | 06 |

### Newly Identified (22 Algorithms)

| ID | Algorithm | Category | Business Value | Complexity | Phase |
|----|-----------|----------|----------------|------------|-------|
| **SECURITY & COMPLIANCE** |||||
| 3.1 | Segregation of Duties (SoD) Violation Detector | Critical | SOX/GDPR compliance | Medium | MVP+ |
| 3.2 | Anomalous Role Change Detector | Critical | Security breach prevention | Medium | MVP+ |
| 3.3 | Privilege Creep Detector | High | Security hygiene | Medium | Phase 2 |
| 3.4 | Toxic Combination Detector | Critical | Fraud prevention | High | Phase 2 |
| 3.5 | Orphaned Account Detector | High | Security risk reduction | Low | MVP |
| 3.6 | Emergency Account Monitor | Critical | Audit compliance | Medium | MVP+ |
| 3.7 | Service Account Analyzer | High | Security governance | Medium | Phase 2 |
| 3.8 | Access Review Automation | High | Audit efficiency | High | Phase 3 |
| 3.9 | Entra-D365 License Sync Validator ⭐ NEW | High | Cost + compliance | Medium | Phase 2 |
| **COST OPTIMIZATION** |||||
| 4.1 | Device License Opportunity Detector | High | 20-40% savings | Low | Phase 2 |
| 4.2 | License Attach Optimizer | High | 10-25% savings | Medium | Phase 2 |
| 4.3 | Cross-Application License Analyzer | High | 5-15% savings | Medium | Phase 2 |
| 4.4 | License Demand Forecaster | High | Budget optimization | High | Phase 3 |
| 4.5 | Seasonal Pattern Analyzer | Medium | Capacity planning | Medium | Phase 3 |
| 4.6 | Project-Based License Planner | Medium | Project cost tracking | High | Phase 3 |
| 4.7 | New User License Recommendation Engine ⭐ NEW | High | Prevent over-licensing | Medium-High | Phase 1 |
| **USER BEHAVIOR** |||||
| 5.1 | Session Anomaly Detector | High | Security (hijacking) | Medium | Phase 2 |
| 5.2 | Geographic Access Pattern Analyzer | High | Security (unusual locations) | Medium | Phase 2 |
| 5.3 | Time-Based Access Analyzer | High | Security (after-hours) | Low | MVP+ |
| 5.4 | Contractor Access Tracker | High | Compliance | Low | MVP |
| **ROLE MANAGEMENT** |||||
| 6.1 | Stale Role Detector | Medium | Maintenance | Low | Phase 2 |
| 6.2 | Permission Explosion Detector | High | Security + cost | Medium | Phase 2 |
| 6.3 | Duplicate Role Consolidator | High | Simplification | Medium | Phase 2 |
| 6.4 | Role Hierarchy Optimizer | Medium | Management | High | Phase 3 |
| **ADVANCED ANALYTICS** |||||
| 7.1 | License Utilization Trend Analyzer | Medium | Visibility | Low | Phase 2 |
| 7.2 | Cost Allocation Engine | High | Financial accuracy | Medium | Phase 2 |
| 7.3 | What-If Scenario Modeler | High | Planning | High | Phase 3 |
| 7.4 | ROI Calculator for Optimization | High | Business justification | Medium | Phase 2 |

---

## High-Priority Security & Compliance Algorithms

### Algorithm 3.1: Segregation of Duties (SoD) Violation Detector ⭐⭐⭐⭐⭐

**Purpose**: Automatically detect users with conflicting role assignments that violate internal controls and compliance requirements (SOX, ISO 27001, GDPR).

**Business Value**:
- **Compliance**: SOX Section 404 requires SoD for financial processes
- **Risk Reduction**: Prevent fraud (e.g., vendor creation + payment approval)
- **Audit Readiness**: Automated evidence for auditors
- **Cost Avoidance**: Fines for compliance violations

**Input Data Required**:
- `UserRoleAssignments`: User → Role mappings
- `SODConflictMatrix`: Configurable rule table defining conflicting role pairs
- `SecurityConfigurationData`: Role → Privilege mappings
- `UserActivityData`: Actual usage patterns (for severity scoring)

**Output Structure**:
```
SoD Violation Report:
├── Violation ID: [Unique]
├── User: [Name/ID]
├── Conflicting Roles: [Role A] + [Role B]
├── Conflict Type: [e.g., "AP Clerk + Vendor Master", "Cash Receipt + Bank Reconciliation"]
├── Severity: [Critical/High/Medium/Low]
├── Risk Description: [Explanation of fraud risk]
├── Last Activity: [Date] (for both roles)
├── Recommendation: [Remediation action]
└── Regulatory Impact: [SOX/GDPR/ISO reference]
```

**Pseudocode**:

```
FUNCTION DetectSODViolations()
  BEGIN
    violations ← []

    // Load conflict matrix (configurable rules)
    conflictMatrix ← LoadSODConflictRules()

    // Get all user-role assignments
    userRoles ← GetAllUserRoleAssignments()

    FOR EACH user IN userRoles
      userRoleList ← user.roles

      // Check all role combinations for conflicts
      FOR i ← 0 TO COUNT(userRoleList) - 1
        FOR j ← i + 1 TO COUNT(userRoleList) - 1
          roleA ← userRoleList[i]
          roleB ← userRoleList[j]

          // Check if this pair conflicts
          IF conflictMatrix.HasConflict(roleA, roleB) THEN
            conflictType ← conflictMatrix.GetConflictType(roleA, roleB)

            // Determine severity based on usage
            severity ← CalculateSODSeverity(user, roleA, roleB)

            violations.APPEND({
              'userId': user.id,
              'userName': user.name,
              'roleA': roleA,
              'roleB': roleB,
              'conflictType': conflictType,
              'severity': severity,
              'riskDescription': ExplainRisk(conflictType),
              'lastActivityRoleA': GetLastActivityDate(user.id, roleA),
              'lastActivityRoleB': GetLastActivityDate(user.id, roleB),
              'recommendation': GenerateRemediation(user, roleA, roleB),
              'regulatoryImpact': GetRegulatoryReferences(conflictType)
            })
          END IF
        END FOR
      END FOR
    END FOR

    // Sort by severity
    violations.SORT_BY_DESCENDING('severity')

    RETURN violations
  END
END FUNCTION

FUNCTION CalculateSODSeverity(user, roleA, roleB)
  BEGIN
    severityScore ← 0

    // Factor 1: Both roles actively used?
    activityA ← GetLastActivityDate(user.id, roleA)
    activityB ← GetLastActivityDate(user.id, roleB)
    daysSinceA ← DAYS_BETWEEN(TODAY(), activityA)
    daysSinceB ← DAYS_BETWEEN(TODAY(), activityB)

    IF daysSinceA < 90 AND daysSinceB < 90 THEN
      severityScore ← severityScore + 50  // Both active = HIGH RISK
    ELSE IF daysSinceA < 90 OR daysSinceB < 90 THEN
      severityScore ← severityScore + 25  // One active = MEDIUM RISK
    END IF

    // Factor 2: Conflict type severity
    conflictSeverity ← GetConflictTypeSeverity(roleA, roleB)
    severityScore ← severityScore + conflictSeverity

    // Convert score to severity level
    IF severityScore >= 80 THEN
      RETURN 'CRITICAL'
    ELSE IF severityScore >= 60 THEN
      RETURN 'HIGH'
    ELSE IF severityScore >= 40 THEN
      RETURN 'MEDIUM'
    ELSE
      RETURN 'LOW'
    END IF
  END
END FUNCTION
```

**Sample SOD Conflict Matrix** (Configurable):

```
| Role A              | Role B             | Conflict Type          | Severity |
|---------------------|--------------------|------------------------|----------|
| AP Clerk            | Vendor Master      | Create + Pay Vendor    | Critical |
| AR Clerk            | Customer Master    | Create + Collect       | Critical |
| Cash Receipt        | Bank Reconciliation| Receive + Reconcile    | High     |
| General Journal     | Ledger Accountant  | Post + Review          | High     |
| Purchasing Agent    | Vendor Master      | Create + Approve       | High     |
| Warehouse Manager   | Inventory Count     | Move + Count           | Medium   |
| Sales Order Clerk   | Customer Master    | Create + Order         | Medium   |
```

---

### Algorithm 3.2: Anomalous Role Change Detector ⭐⭐⭐⭐⭐

**Purpose**: Detect suspicious or unauthorized role assignment changes that could indicate security breaches or insider threats.

**Business Value**:
- **Security**: Detect compromised accounts (attackers adding roles)
- **Insider Threat**: Identify privilege escalation before damage
- **Compliance**: Maintain audit trail for all changes
- **Operational**: Catch accidental role assignments

**Input Data Required**:
- `AuditLogs`: Role assignment changes (who, when, what)
- `UserRoleAssignments`: Current state
- `UserActivityData`: Post-change behavior
- `BaselineData`: Normal change patterns (by time, approver)

**Output Structure**:
```
Anomalous Role Change Alert:
├── Change ID: [Unique]
├── User Affected: [Name/ID]
├── Role Changed: [Role Name]
├── Action: [Assigned/Removed]
├── Changed By: [Admin/Service Account]
├── Timestamp: [DateTime]
├── Anomaly Score: [0-100]
├── Anomaly Reasons: [List of detected anomalies]
│   ├── "After-hours assignment (2 AM Saturday)"
│   ├── "No approval workflow"
│   ├── "High-privilege role assigned to new user"
│   └── "Changed by service account (rare pattern)"
├── Risk Level: [Critical/High/Medium/Low]
└── Recommendation: [Action]
```

**Pseudocode**:

```
FUNCTION DetectAnomalousRoleChanges(timeRange = '7 days')
  BEGIN
    anomalies ← []

    // Get recent role changes
    roleChanges ← GetAuditLogEntries(
      category: 'UserRoleAssignment',
      timeRange: timeRange
    )

    // Build baseline from historical data
    baseline ← BuildChangeBaseline(
      historicalData: 'last 12 months',
      dimensions: ['hour_of_day', 'day_of_week', 'changed_by', 'role_type']
    )

    FOR EACH change IN roleChanges
      anomalyScore ← 0
      anomalyReasons ← []

      // Check 1: Time-based anomaly
      hour ← EXTRACT_HOUR(change.timestamp)
      dayOfWeek ← EXTRACT_DAY_OF_WEEK(change.timestamp)

      IF hour < 6 OR hour > 18 THEN  // Outside business hours
        anomalyScore ← anomalyScore + 30
        anomalyReasons.APPEND('After-hours change at ' + change.timestamp)
      END IF

      IF dayOfWeek IN ['Saturday', 'Sunday'] THEN
        anomalyScore ← anomalyScore + 20
        anomalyReasons.APPEND('Weekend change')
      END IF

      // Check 2: Approver anomaly
      IF NOT baseline.IsCommonApprover(change.changedBy, change.role) THEN
        anomalyScore ← anomalyScore + 25
        anomalyReasons.APPEND('Changed by unusual approver: ' + change.changedBy)
      END IF

      // Check 3: Role privilege level
      rolePrivilege ← GetRolePrivilegeLevel(change.role)
      IF rolePrivilege = 'HIGH' AND change.action = 'ASSIGNED' THEN
        // Check if user is new (< 30 days old)
        userAge ← GetUserAge(change.userAffected)
        IF userAge < 30 THEN
          anomalyScore ← anomalyScore + 35
          anomalyReasons.APPEND('High-privilege role assigned to new user (' + userAge + ' days old)')
        END IF
      END IF

      // Check 4: Rapid successive changes
      recentChangesForUser ← COUNT(GetChangesForUser(
        user: change.userAffected,
        timeWindow: '1 hour'
      ))
      IF recentChangesForUser > 3 THEN
        anomalyScore ← anomalyScore + 20
        anomalyReasons.APPEND('Rapid role changes: ' + recentChangesForUser + ' in 1 hour')
      END IF

      // Check 5: Missing approval
      IF NOT change.hasApprovalWorkflow THEN
        requiredApproval ← IsApprovalRequired(change.role)
        IF requiredApproval THEN
          anomalyScore ← anomalyScore + 30
          anomalyReasons.APPEND('High-privilege role assigned without approval')
        END IF
      END IF

      // Check 6: Service account usage
      IF IsServiceAccount(change.changedBy) THEN
        serviceAccountUsage ← baseline.GetServiceAccountUsageFrequency(change.changedBy)
        IF serviceAccountUsage < 5 THEN  // Very rare
          anomalyScore ← anomalyScore + 40
          anomalyReasons.APPEND('Changed by service account (rare pattern)')
        END IF
      END IF

      // Create alert if score exceeds threshold
      IF anomalyScore >= 50 THEN
        riskLevel ← CalculateRiskLevel(anomalyScore)

        anomalies.APPEND({
          'changeId': change.id,
          'userAffected': change.userAffected,
          'roleChanged': change.role,
          'action': change.action,
          'changedBy': change.changedBy,
          'timestamp': change.timestamp,
          'anomalyScore': anomalyScore,
          'anomalyReasons': anomalyReasons,
          'riskLevel': riskLevel,
          'recommendation': GenerateRecommendation(change, anomalyScore)
        })
      END IF
    END FOR

    // Sort by anomaly score
    anomalies.SORT_BY_DESCENDING('anomalyScore')

    RETURN anomalies
  END
END FUNCTION
```

**Risk Level Calculation**:

```
IF anomalyScore >= 90 → CRITICAL (Immediate investigation required)
IF anomalyScore >= 70 → HIGH (Investigation within 24 hours)
IF anomalyScore >= 50 → MEDIUM (Investigation within 7 days)
IF anomalyScore < 50 → LOW (Informational)
```

---

### Algorithm 3.3: Privilege Creep Detector ⭐⭐⭐

**Purpose**: Identify users who have gradually accumulated excessive roles/privileges over time (privilege creep), creating security risks and unnecessary license costs.

**Business Value**:
- **Security**: Reduce attack surface (excessive privileges)
- **Cost**: Remove unused high-license roles
- **Compliance**: Principle of least privilege
- **Maintenance**: Easier user management

**Input Data Required**:
- `UserRoleAssignments`: Current state + history (12+ months)
- `AuditLogs`: Role assignment history with timestamps
- `UserActivityData`: Actual usage per role
- `SecurityConfigurationData`: License requirements

**Output Structure**:
```
Privilege Creep Report:
├── User: [Name/ID]
├── Current Roles: N (list)
├── Current License: [Highest required]
├── Role Growth Timeline:
│   ├── Month 1: 2 roles
│   ├── Month 6: 5 roles (+3)
│   └── Month 12: 8 roles (+3 more)
├── Unused Roles: N (roles with 0 activity in 90 days)
├── Privilege Creep Score: [0-100]
├── License Impact: [Over-licensed by X]
├── Security Risk: [High/Medium/Low]
└── Recommendation: [Clean up X roles, save $Y/month]
```

**Pseudocode**:

```
FUNCTION DetectPrivilegeCreep(lookbackMonths = 12)
  BEGIN
    privilegeCreepUsers ← []

    // Get all users
    allUsers ← GetAllActiveUsers()

    FOR EACH user IN allUsers
      // Get role history over time
      roleHistory ← GetUserRoleHistory(
        user: user.id,
        monthsBack: lookbackMonths
      )

      // Skip users with stable roles
      IF COUNT(roleHistory) <= 2 THEN
        CONTINUE
      END IF

      // Analyze role growth pattern
      roleCountTimeline ← BuildRoleCountTimeline(roleHistory)

      // Calculate privilege creep score
      creepScore ← CalculateCreepScore(roleHistory, roleCountTimeline)

      // Get current state
      currentRoles ← GetCurrentUserRoles(user.id)
      unusedRoles ← GetUnusedRoles(user.id, currentRoles, days=90)

      // Calculate license impact
      currentLicense ← GetRequiredLicenseForRoles(currentRoles)
      neededLicense ← GetRequiredLicenseForRoles(currentRoles.MINUS(unusedRoles))
      licenseOverage ← currentLicense - neededLicense

      // Generate recommendation
      IF COUNT(unusedRoles) > 0 OR creepScore > 60 THEN
        potentialSavings ← CalculateSavings(currentLicense, neededLicense)

        privilegeCreepUsers.APPEND({
          'userId': user.id,
          'userName': user.name,
          'currentRoles': currentRoles,
          'roleCount': COUNT(currentRoles),
          'currentLicense': currentLicense,
          'roleGrowthTimeline': roleCountTimeline,
          'unusedRoles': unusedRoles,
          'unusedRoleCount': COUNT(unusedRoles),
          'privilegeCreepScore': creepScore,
          'licenseImpact': {
            'currentLicense': currentLicense,
            'neededLicense': neededLicense,
            'overage': licenseOverage
          },
          'securityRisk': AssessSecurityRisk(currentRoles, unusedRoles),
          'recommendation': {
            'action': 'Remove ' + COUNT(unusedRoles) + ' unused roles',
            'rolesToRemove': unusedRoles,
            'potentialSavingsPerMonth': potentialSavings
          }
        })
      END IF
    END FOR

    // Sort by privilege creep score
    privilegeCreepUsers.SORT_BY_DESCENDING('privilegeCreepScore')

    RETURN privilegeCreepUsers
  END
END FUNCTION

FUNCTION CalculateCreepScore(roleHistory, roleCountTimeline)
  BEGIN
    score ← 0

    // Factor 1: Total role growth
    initialRoles ← roleCountTimeline.FIRST.roleCount
    finalRoles ← roleCountTimeline.LAST.roleCount
    roleGrowth ← finalRoles - initialRoles

    IF roleGrowth >= 5 THEN
      score ← score + 40
    ELSE IF roleGrowth >= 3 THEN
      score ← score + 25
    ELSE IF roleGrowth >= 2 THEN
      score ← score + 10
    END IF

    // Factor 2: Rate of growth (accelerating?)
    growthRate ← CalculateGrowthRate(roleCountTimeline)
    IF growthRate > 1.5 THEN  // Accelerating
      score ← score + 20
    END IF

    // Factor 3: Role additions vs. removals (net growth)
    additions ← COUNT(roleHistory.FILTER(action = 'ASSIGNED'))
    removals ← COUNT(roleHistory.FILTER(action = 'REMOVED'))
    netGrowth ← additions - removals

    IF netGrowth >= 5 THEN
      score ← score + 30
    ELSE IF netGrowth >= 3 THEN
      score ← score + 15
    END IF

    // Factor 4: Role churn (frequent changes)
    IF COUNT(roleHistory) > 10 THEN
      score ← score + 10  // High churn
    END IF

    RETURN MIN(score, 100)  // Cap at 100
  END
END FUNCTION
```

---

### Algorithm 3.4: Toxic Combination Detector ⭐⭐⭐⭐⭐

**Purpose**: Detect dangerous combinations of privileges that could enable fraud, even if not explicit SoD violations (e.g., three roles that together create a risk).

**Business Value**:
- **Fraud Prevention**: Detect non-obvious risk combinations
- **Advanced Compliance**: Beyond basic SoD
- **Risk Management**: Proactive threat identification

**Input Data Required**:
- `UserRoleAssignments`: User → Role mappings
- `ToxicCombinationRules`: Configurable multi-role risk patterns
- `SecurityConfigurationData`: Role → Privilege mappings

**Output Structure**:
```
Toxic Combination Alert:
├── User: [Name/ID]
├── Toxic Combination: [Role A] + [Role B] + [Role C]
├── Risk Type: [e.g., "Full Procure-to-Pay", "Complete Order-to-Cash"]
├── Risk Description: [Explanation of fraud risk]
├── Combined Privileges: [List of dangerous capabilities]
├── Severity: [Critical/High/Medium]
└── Recommendation: [Split roles, add approvals]
```

**Pseudocode**:

```
FUNCTION DetectToxicCombinations()
  BEGIN
    toxicAlerts ← []

    // Load toxic combination rules
    toxicRules ← LoadToxicCombinationRules()

    // Get all user-role assignments
    userRoles ← GetAllUserRoleAssignments()

    FOR EACH user IN userRoles
      userRoleSet ← SET(user.roles)

      // Check against all toxic combination rules
      FOR EACH rule IN toxicRules
        // Check if user has all roles in the toxic combination
        IF userRoleSet.CONTAINS_ALL(rule.roles) THEN
          // Get combined privileges
          combinedPrivileges ← GetCombinedPrivileges(rule.roles)

          toxicAlerts.APPEND({
            'userId': user.id,
            'userName': user.name,
            'toxicCombination': rule.roles,
            'riskType': rule.riskType,
            'riskDescription': rule.description,
            'combinedPrivileges': combinedPrivileges,
            'severity': rule.severity,
            'recommendation': rule.remediation
          })
        END IF
      END FOR
    END FOR

    RETURN toxicAlerts
  END
END FUNCTION
```

**Sample Toxic Combination Rules**:

```
| Combination                    | Risk Type                   | Severity |
|--------------------------------|-----------------------------|----------|
| Purchasing + Vendor + AP Clerk | Full Procure-to-Pay         | Critical |
| Sales Order + Customer + AR    | Complete Order-to-Cash      | Critical |
| General Journal + Ledger + Approver | Full Journal Cycle  | High     |
| Inventory + Warehouse + Sales  | Pick + Ship + Bill          | High     |
| Bank Reconciliation + Cash + Treasury | Full Cash Mgmt | High     |
```

---

### Algorithm 3.5: Orphaned Account Detector ⭐⭐⭐

**Purpose**: Identify user accounts with no active manager, inactive status, or missing ownership (orphaned accounts pose security risks).

**Business Value**:
- **Security**: Orphaned accounts easily compromised
- **Compliance**: Requires active owner for all accounts
- **Maintenance**: Clean up inactive accounts
- **License Cost**: Remove licenses for orphaned accounts

**Input Data Required**:
- `UserDirectory`: User details (manager, status, department)
- `UserRoleAssignments`: Current assignments
- `UserActivityData`: Last activity date
- `OrganizationHierarchy`: Manager relationships

**Output Structure**:
```
Orphaned Account Report:
├── User: [Name/ID]
├── Status: [Active/Inactive]
├── Manager: [None/Invalid]
├── Department: [Unknown/Deleted]
├── Last Activity: [Date]
├── Roles Assigned: N
├── License Cost: $X/month
├── Orphan Type: [No Manager/Inactive/No Dept/All]
├── Risk Level: [High/Medium]
└── Recommendation: [Assign manager/Disable/Remove license]
```

**Pseudocode**:

```
FUNCTION DetectOrphanedAccounts()
  BEGIN
    orphanedAccounts ← []

    // Get all users
    allUsers ← GetAllUsers()

    FOR EACH user IN allUsers
      orphanReasons ← []

      // Check 1: No manager assigned
      IF user.managerId IS NULL OR user.managerId IS INVALID THEN
        orphanReasons.APPEND('No valid manager')
      END IF

      // Check 2: Inactive status
      IF user.status = 'INACTIVE' THEN
        orphanReasons.APPEND('User status is Inactive')
      END IF

      // Check 3: No department or department deleted
      IF user.departmentId IS NULL OR NOT DepartmentExists(user.departmentId) THEN
        orphanReasons.APPEND('No valid department')
      END IF

      // Check 4: Manager is inactive
      IF user.managerId IS NOT NULL THEN
        manager ← GetUser(user.managerId)
        IF manager.status = 'INACTIVE' THEN
          orphanReasons.APPEND('Manager is inactive')
        END IF
      END IF

      // Check 5: No activity in 180+ days
      lastActivity ← GetLastActivityDate(user.id)
      daysSinceActivity ← DAYS_BETWEEN(TODAY(), lastActivity)

      IF daysSinceActivity > 180 THEN
        orphanReasons.APPEND('No activity in ' + daysSinceActivity + ' days')
      END IF

      // Flag as orphaned if any reasons found
      IF COUNT(orphanReasons) > 0 THEN
        // Get current license
        userRoles ← GetCurrentUserRoles(user.id)
        licenseCost ← GetLicenseCost(userRoles)

        // Assess risk
        IF user.status = 'ACTIVE' AND COUNT(userRoles) > 0 THEN
          riskLevel ← 'HIGH'  // Active orphaned account = security risk
        ELSE
          riskLevel ← 'MEDIUM'
        END IF

        orphanedAccounts.APPEND({
          'userId': user.id,
          'userName': user.name,
          'status': user.status,
          'manager': user.manager,
          'department': user.department,
          'lastActivity': lastActivity,
          'daysSinceActivity': daysSinceActivity,
          'rolesAssigned': userRoles,
          'roleCount': COUNT(userRoles),
          'licenseCostPerMonth': licenseCost,
          'orphanType': ClassifyOrphanType(orphanReasons),
          'orphanReasons': orphanReasons,
          'riskLevel': riskLevel,
          'recommendation': GenerateOrphanRemediation(user, orphanReasons)
        })
      END IF
    END FOR

    // Sort by risk level
    orphanedAccounts.SORT('riskLevel')

    RETURN orphanedAccounts
  END
END FUNCTION
```

---

### Algorithm 3.6: Emergency Account Monitor ⭐⭐⭐⭐

**Purpose**: Monitor emergency/break-glass accounts for inappropriate usage, ensure proper audit trail, and detect potential abuse.

**Business Value**:
- **Compliance**: SOX requires emergency account monitoring
- **Security**: Detect stolen emergency credentials
- **Audit**: Evidence for emergency access reviews
- **Risk Management**: Limit inappropriate usage

**Input Data Required**:
- `EmergencyAccountList`: Pre-defined list of emergency accounts
- `UserActivityData`: All activity by emergency accounts
- `AuditLogs`: Emergency access check-outs
- `ApprovalData`: Emergency access approvals

**Output Structure**:
```
Emergency Account Usage Report:
├── Account: [Name/ID]
├── Usage Session: [Session ID]
├── Access Type: [Break-glass/Emergency]
├── Start Time: [DateTime]
├── Duration: [X hours]
├── Approved By: [Manager]
├── Justification: [Ticket/Incident]
├── Activities Performed: N
├── High-Risk Actions: [List]
├── Inappropriate Usage: [Detected/None]
└── Recommendation: [Review required/Revoke/Normal]
```

**Pseudocode**:

```
FUNCTION MonitorEmergencyAccounts()
  BEGIN
    alerts ← []

    // Get emergency accounts
    emergencyAccounts ← GetEmergencyAccounts()

    // Get recent activity for emergency accounts
    timeRange ← 'last 7 days'
    activityData ← GetUserActivity(
      users: emergencyAccounts,
      timeRange: timeRange
    )

    FOR EACH account IN emergencyAccounts
      accountActivity ← activityData.FILTER(user = account.id)

      // Group by session
      sessions ← GroupBySession(accountActivity)

      FOR EACH session IN sessions
        // Check for proper approval
        approval ← GetEmergencyAccessApproval(account.id, session.startTime)

        IF approval IS NULL THEN
          alerts.APPEND({
            'account': account.name,
            'session': session.id,
            'issue': 'Emergency account used without approval',
            'severity': 'CRITICAL',
            'recommendation': 'IMMEDIATE: Investigate unauthorized access'
          })
          CONTINUE
        END IF

        // Analyze session for inappropriate usage
        inappropriateUsage ← AnalyzeEmergencySession(session, approval)

        IF inappropriateUsage.detected THEN
          alerts.APPEND({
            'account': account.name,
            'session': session.id,
            'accessType': account.type,
            'startTime': session.startTime,
            'duration': session.duration,
            'approvedBy': approval.approver,
            'justification': approval.justification,
            'activitiesPerformed': COUNT(session.activities),
            'highRiskActions': inappropriateUsage.highRiskActions,
            'inappropriateUsage': inappropriateUsage.reasons,
            'severity': inappropriateUsage.severity,
            'recommendation': inappropriateUsage.recommendation
          })
        END IF
      END FOR
    END FOR

    RETURN alerts
  END
END FUNCTION

FUNCTION AnalyzeEmergencySession(session, approval)
  BEGIN
    issues ← []
    severity ← 'LOW'

    // Check 1: Duration too long
    expectedDuration ← approval.expectedDurationHours
    actualDuration ← session.durationHours

    IF actualDuration > (expectedDuration * 2) THEN
      issues.APPEND('Session duration ' + actualDuration + 'h exceeds expected ' + expectedDuration + 'h')
      severity ← 'HIGH'
    END IF

    // Check 2: Activities outside approval scope
    approvedScope ← approval.authorizedActivities
    actualActivities ← GET_UNIQUE_MENU_ITEMS(session.activities)

    outsideScope ← actualActivities.MINUS(approvedScope)

    IF COUNT(outsideScope) > 0 THEN
      issues.APPEND('Performed ' + COUNT(outsideScope) + ' activities outside approved scope')
      severity ← 'CRITICAL'
    END IF

    // Check 3: High-risk actions
    highRiskActions ← session.activities.FILTER(
      menuItem IN ['BankReconciliation', 'GeneralJournalPost', 'VendorPayment']
    )

    IF COUNT(highRiskActions) > 0 AND NOT approval.includesHighRisk THEN
      issues.APPEND('Performed ' + COUNT(highRiskActions) + ' high-risk actions without authorization')
      severity ← 'CRITICAL'
    END IF

    // Check 4: Time-based anomaly
    IF session.startTime NOT IN approval.authorizedTimeWindow THEN
      issues.APPEND('Access outside authorized time window')
      severity ← 'MEDIUM'
    END IF

    // Check 5: Justification mismatch
    IF approval.justification.CONTAINS('system outage') THEN
      normalActivities ← session.activities.FILTER(action = 'Read')
      IF COUNT(normalActivities) / COUNT(session.activities) > 0.8 THEN
        issues.APPEND('Justification was system outage but mostly read activities')
        severity ← 'MEDIUM'
      END IF
    END IF

    IF COUNT(issues) > 0 THEN
      RETURN {
        'detected': TRUE,
        'reasons': issues,
        'highRiskActions': highRiskActions,
        'severity': severity,
        'recommendation': GenerateEmergencyRecommendation(severity, issues)
      }
    ELSE
      RETURN {
        'detected': FALSE,
        'reasons': [],
        'highRiskActions': [],
        'severity': 'LOW',
        'recommendation': 'Normal emergency usage'
      }
    END IF
  END
END FUNCTION
```

---

## High-Priority Cost Optimization Algorithms

### Algorithm 4.1: Device License Opportunity Detector ⭐⭐⭐⭐

**Purpose**: Identify scenarios where device licenses would be more cost-effective than user licenses (shared workstations, warehouse, POS).

**Business Value**:
- **Cost Savings**: Device licenses ~50% cheaper than multiple user licenses
- **Scenarios**: Warehouse, manufacturing, retail POS, shared workstations
- **ROI**: 20-40% license cost reduction in applicable scenarios

**Input Data Required**:
- `UserActivityData`: Login patterns by device/user
- `UserSessionData`: Session duration and concurrency
- `UserRoleAssignments`: Current license assignments
- `DeviceInventory`: Available devices and locations

**Output Structure**:
```
Device License Opportunity Report:
├── Location: [Warehouse/Factory/Store]
├── Devices: N (device names/IDs)
├── Current Users: N
├── Current License Cost: $X/month
├── Device License Analysis:
│   ├── Peak Concurrent Users: N
│   ├── Average Concurrent Users: N
│   ├── User Rotation: High/Medium/Low
│   └── Device License Eligibility: [Yes/No]
├── Recommendation: [Replace N user licenses with N device licenses]
├── Projected Savings: $Y/month (Z%)
└── Implementation Effort: [Low/Medium/High]
```

**Pseudocode**:

```
FUNCTION DetectDeviceLicenseOpportunities()
  BEGIN
    opportunities ← []

    // Get all devices with multiple users
    devices ← GetAllDevices()

    FOR EACH device IN devices
      // Get user activity for this device
      deviceUsers ← GetUsersForDevice(device.id, timeRange='90 days')

      // Skip devices with < 3 users (not worth it)
      IF COUNT(deviceUsers) < 3 THEN
        CONTINUE
      END IF

      // Analyze usage patterns
      usagePattern ← AnalyzeDeviceUsagePattern(device.id, deviceUsers)

      // Check if device license is applicable
      IF IsDeviceLicenseEligible(usagePattern) THEN
        // Calculate current cost
        currentLicenseCost ← 0
        FOR EACH user IN deviceUsers
          userLicense ← GetUserLicense(user.id)
          currentLicenseCost ← currentLicenseCost + GetLicenseCost(userLicense)
        END FOR

        // Calculate device license cost
        // Device license cost typically = (highest user license) × 0.5
        highestUserLicense ← GetHighestLicense(deviceUsers)
        deviceLicenseCost ← GetLicenseCost(highestUserLicense) * 0.5

        // Calculate savings
        monthlySavings ← currentLicenseCost - deviceLicenseCost
        savingsPercentage ← (monthlySavings / currentLicenseCost) * 100

        opportunities.APPEND({
          'device': device.name,
          'deviceId': device.id,
          'location': device.location,
          'deviceType': device.type,  // Warehouse, POS, etc.
          'currentUsers': COUNT(deviceUsers),
          'userList': deviceUsers,
          'currentLicenseCostPerMonth': currentLicenseCost,
          'deviceLicenseCostPerMonth': deviceLicenseCost,
          'monthlySavings': monthlySavings,
          'savingsPercentage': savingsPercentage,
          'usagePattern': usagePattern,
          'peakConcurrentUsers': usagePattern.peakConcurrent,
          'averageConcurrentUsers': usagePattern.avgConcurrent,
          'userRotation': usagePattern.rotationLevel,
          'eligibility': 'ELIGIBLE',
          'recommendation': 'Replace ' + COUNT(deviceUsers) + ' user licenses with 1 device license',
          'implementationEffort': AssessImplementationEffort(device),
          'roi_months': CalculateROI(currentLicenseCost, deviceLicenseCost, implementationCost)
        })
      END IF
    END FOR

    // Sort by savings
    opportunities.SORT_BY_DESCENDING('monthlySavings')

    RETURN opportunities
  END
END FUNCTION

FUNCTION IsDeviceLicenseEligible(usagePattern)
  BEGIN
    // Criteria for device license eligibility:

    // 1. High user rotation (multiple users share device)
    IF usagePattern.uniqueUsers < 3 THEN
      RETURN FALSE
    END IF

    // 2. Low concurrency (not used simultaneously by multiple users)
    IF usagePattern.peakConcurrent > 1 THEN
      RETURN FALSE  // Multiple users at same time = need user licenses
    END IF

    // 3. Device is shared (not dedicated to one user)
    IF usagePattern.dedicatedUserPercentage > 80 THEN
      RETURN FALSE  // One user dominates = user license better
    END IF

    // 4. Device type is eligible
    IF usagePattern.deviceType NOT IN ['Warehouse', 'Manufacturing', 'POS', 'ShopFloor', 'Kiosk'] THEN
      RETURN FALSE
    END IF

    // All criteria met
    RETURN TRUE
  END
END FUNCTION

FUNCTION AnalyzeDeviceUsagePattern(deviceId, users)
  BEGIN
    // Get session data for this device
    sessions ← GetDeviceSessions(deviceId, days=90)

    // Calculate metrics
    uniqueUsers ← COUNT(users)
    totalSessionHours ← SUM(sessions.duration)

    // Calculate concurrency
    concurrentSessions ← CalculateConcurrentSessions(sessions)
    peakConcurrent ← MAX(concurrentSessions)
    avgConcurrent ← AVERAGE(concurrentSessions)

    // Calculate user rotation
    userSessionCounts ← {}
    FOR EACH user IN users
      userSessionCounts[user.id] ← COUNT(sessions.FILTER(user = user.id))
    END FOR

    dominantUserSessions ← MAX(userSessionCounts)
    dedicatedUserPercentage ← (dominantUserSessions / COUNT(sessions)) * 100

    // Classify rotation level
    IF dedicatedUserPercentage > 80 THEN
      rotationLevel ← 'LOW'  // One user dominates
    ELSE IF dedicatedUserPercentage > 50 THEN
      rotationLevel ← 'MEDIUM'
    ELSE
      rotationLevel ← 'HIGH'  // True shared device
    END IF

    RETURN {
      'uniqueUsers': uniqueUsers,
      'totalSessions': COUNT(sessions),
      'totalSessionHours': totalSessionHours,
      'peakConcurrent': peakConcurrent,
      'avgConcurrent': avgConcurrent,
      'dedicatedUserPercentage': dedicatedUserPercentage,
      'rotationLevel': rotationLevel,
      'deviceType': GetDeviceType(deviceId)
    }
  END
END FUNCTION
```

**Sample Output**:

```
Device License Opportunity Analysis

Location: Warehouse - Chicago
├── Device: WHC-SCANNER-01 to WHC-SCANNER-15 (15 devices)
├── Current Users: 45 warehouse workers
├── Current Licenses:
│   └── 45 × Operations – Activity licenses @ $90 = $4,050/month
├── Device License Option:
│   └── 15 × Device licenses @ $45 = $675/month
├── Monthly Savings: $3,375 (83% reduction)
├── Annual Savings: $40,500
├── Implementation Effort: Low
└── ROI: 2 months
```

---

### Algorithm 4.2: License Attach Optimizer ⭐⭐⭐⭐

**Purpose**: Optimize license assignments using attach licenses (base license + attach) vs. multiple full licenses.

**Business Value**:
- **Cost Savings**: Attach licenses cheaper than multiple full licenses
- **Flexibility**: Mix and match license types
- **Complexity**: Requires careful analysis to ensure cost savings

**Input Data Required**:
- `UserRoleAssignments`: User → Role mappings
- `SecurityConfigurationData`: Role → License requirements
- `LicensePricingTable`: Full vs. Attach pricing
- `UserActivityData`: Actual usage by license area

**Output Structure**:
```
License Attach Optimization Report:
├── User: [Name/ID]
├── Current License Assignment:
│   ├── License A: Finance ($180)
│   └── License B: SCM ($180)
├── Total Current Cost: $360/month
├── Optimized Assignment (Attach Model):
│   ├── Base License: Finance ($180)
│   └── Attach License: SCM ($30)
├── Total Optimized Cost: $210/month
├── Monthly Savings: $150 (42%)
├── Feasibility: [Feasible/Not Feasible]
└── Recommendation: [Switch to attach model]
```

**Pseudocode**:

```
FUNCTION OptimizeLicenseAttach()
  BEGIN
    optimizations ← []

    // Get all users with multiple license types
    multiLicenseUsers ← GetUsersWithMultipleLicenses()

    // Get license pricing table
    pricing ← GetLicensePricing()

    FOR EACH user IN multiLicenseUsers
      userLicenses ← GetUserLicenses(user.id)

      // Skip if only 1 license
      IF COUNT(userLicenses) <= 1 THEN
        CONTINUE
      END IF

      // Try all combinations of base + attach
      bestOption ← NULL
      bestSavings ← -1

      FOR EACH baseLicense IN userLicenses
        // Calculate cost with this as base
        baseCost ← pricing[baseLicense].full

        // Add attach costs for other licenses
        attachCost ← 0
        feasible ← TRUE

        FOR EACH otherLicense IN userLicenses
          IF otherLicense != baseLicense THEN
            // Check if attach available
            IF pricing[otherLicense].attachAvailable THEN
              attachCost ← attachCost + pricing[otherLicense].attach
            ELSE
              feasible ← FALSE
              BREAK
            END IF
          END IF
        END FOR

        IF feasible THEN
          totalCost ← baseCost + attachCost
          currentCost ← SUM(pricing[license].full FOR license IN userLicenses)
          savings ← currentCost - totalCost

          IF savings > bestSavings THEN
            bestSavings ← savings
            bestOption ← {
              'baseLicense': baseLicense,
              'attachLicenses': userLicenses.MINUS([baseLicense]),
              'totalCost': totalCost
            }
          END IF
        END IF
      END FOR

      // Add recommendation if savings found
      IF bestOption IS NOT NULL AND bestSavings > 0 THEN
        currentCost ← SUM(pricing[license].full FOR license IN userLicenses)

        optimizations.APPEND({
          'userId': user.id,
          'userName': user.name,
          'currentLicenses': userLicenses,
          'currentCostPerMonth': currentCost,
          'optimizedBaseLicense': bestOption.baseLicense,
          'optimizedAttachLicenses': bestOption.attachLicenses,
          'optimizedCostPerMonth': bestOption.totalCost,
          'monthlySavings': bestSavings,
          'savingsPercentage': (bestSavings / currentCost) * 100,
          'feasibility': 'FEASIBLE',
          'recommendation': 'Switch to base+attach model'
        })
      END IF
    END FOR

    // Sort by savings
    optimizations.SORT_BY_DESCENDING('monthlySavings')

    RETURN optimizations
  END
END FUNCTION
```

**Sample License Pricing** (Illustrative):

```
| License Type        | Full License | Attach License | Savings |
|---------------------|--------------|----------------|---------|
| Finance             | $180         | N/A (Base)     | -       |
| SCM                 | $180         | $30            | 83%     |
| Commerce            | $180         | $30            | 83%     |
| Operations – Activity | $90       | N/A            | -       |
```

**Example**:

```
Current: Finance ($180) + SCM ($180) = $360/month
Optimized: Finance ($180) + SCM-Attach ($30) = $210/month
Savings: $150/month (42% reduction)
```

---

### Algorithm 4.3: Cross-Application License Analyzer ⭐⭐⭐

**Purpose**: Identify users with roles across Finance and SCM who could benefit from combined Finance+SCM license.

**Business Value**:
- **Cost Savings**: Combined license ($210) cheaper than separate ($360)
- **Simplicity**: One license instead of two
- **Automatic**: Should be applied by Microsoft, but verify

**Input Data Required**:
- `UserRoleAssignments`: User → Role mappings
- `SecurityConfigurationData`: Role → Application (Finance/SCM)
- `LicensePricingTable`: Individual vs. Combined pricing

**Output Structure**:
```
Cross-Application License Analysis:
├── User: [Name/ID]
├── Current Assignment:
│   ├── Finance License: $180
│   └── SCM License: $180
│   └── Total: $360/month
├── Optimized Assignment:
│   └── Finance + SCM Combined: $210/month
├── Monthly Savings: $150 (42%)
├── Already Optimized: [Yes/No]
└── Recommendation: [Apply combined license]
```

**Pseudocode**:

```
FUNCTION AnalyzeCrossApplicationLicenses()
  BEGIN
    analysis ← []

    // Get all users with both Finance and SCM access
    crossAppUsers ← GetUsersWithFinanceAndSCM()

    FOR EACH user IN crossAppUsers
      // Check current license assignment
      currentLicense ← GetUserLicense(user.id)

      // Count menu items by application
      financeMenuItems ← GetUserMenuItemsByApp(user.id, 'Finance')
      scmMenuItems ← GetUserMenuItemsByApp(user.id, 'SCM')

      // Determine if combined license applicable
      IF COUNT(financeMenuItems) > 0 AND COUNT(scmMenuItems) > 0 THEN
        // Calculate costs
        separateCost ← 180 + 180  // Finance + SCM
        combinedCost ← 210  // Finance + SCM combined
        savings ← separateCost - combinedCost

        analysis.APPEND({
          'userId': user.id,
          'userName': user.name,
          'currentLicense': currentLicense,
          'financeMenuItemCount': COUNT(financeMenuItems),
          'scmMenuItemCount': COUNT(scmMenuItems),
          'separateCost': separateCost,
          'combinedCost': combinedCost,
          'monthlySavings': savings,
          'savingsPercentage': (savings / separateCost) * 100,
          'alreadyOptimized': (currentLicense = 'Finance + SCM'),
          'recommendation': IF currentLicense != 'Finance + SCM'
            THEN 'Apply Finance + SCM combined license'
            ELSE 'Already optimized'
        })
      END IF
    END FOR

    RETURN analysis
  END
END FUNCTION
```

---

## Medium-Priority Algorithms

### Algorithm 5.1: Session Anomaly Detector ⭐⭐⭐

**Purpose**: Detect anomalous session patterns indicating account hijacking, credential sharing, or security breaches.

**Input Data Required**:
- `UserSessionData`: Session start, end, duration, location
- `UserActivityData`: Actions within sessions
- `BaselineData`: Normal session patterns per user

**Detection Patterns**:
1. **Impossible Travel**: Login from New York, then London within 2 hours
2. **Concurrent Sessions**: Same user from different IP addresses simultaneously
3. **Session Duration**: Unusually long/short sessions
4. **Activity Volume**: Abnormal action count per session
5. **Time Pattern**: Login at unusual times for this user

**Output**:
```
Session Anomaly Alert:
├── User: [Name]
├── Session: [ID]
├── Anomaly Type: [Impossible Travel/Concurrent/Duration]
├── Severity: [Critical/High/Medium]
├── Details: [Explanation]
└── Recommendation: [Investigate/Revoke credentials]
```

---

### Algorithm 6.1: Stale Role Detector ⭐⭐

**Purpose**: Identify roles that haven't been assigned to any active users in 6+ months (candidates for removal).

**Input Data Required**:
- `SecurityRoles`: All defined roles
- `UserRoleAssignments`: Current assignments
- `AuditLogs`: Role assignment history

**Output**:
```
Stale Role Report:
├── Role: [Name]
├── Type: [Custom/Standard]
├── Last Assignment: [Date]
├── Current Assignments: 0
├── Days Since Last Used: N
├── Recommendation: [Review for deletion]
└── Impact: [Low risk - no users affected]
```

---

### Algorithm 6.3: Duplicate Role Consolidator ⭐⭐⭐

**Purpose**: Find similar custom roles that could be consolidated (e.g., "Accountant", "Accountant II", "Senior Accountant").

**Input Data Required**:
- `SecurityRoles`: All role definitions
- `SecurityConfigurationData`: Role → Menu Item mappings
- `UserRoleAssignments`: User assignments

**Algorithm**:
```
For each pair of custom roles:
  1. Calculate menu item overlap percentage
  2. If overlap > 80%, flag for consolidation
  3. Calculate impact (users affected, maintenance reduction)
```

**Output**:
```
Duplicate Role Analysis:
├── Role Pair: [Role A] + [Role B]
├── Overlap: 92% (273/295 menu items)
├── Differences: [List of unique menu items in each]
├── Users Affected: N
├── Recommendation: [Merge roles, create variant for unique items]
└── Maintenance Savings: [Reduce role count by 1]
```

---

## Advanced ML-Based Algorithms

### Algorithm 7.3: What-If Scenario Modeler ⭐⭐⭐⭐

**Purpose**: Model license cost impact of hypothetical changes (reorg, new project, system expansion).

**Input**:
- Current license state
- Scenario parameters (headcount change, new system, etc.)

**Capabilities**:
- "Add 50 warehouse workers for new facility"
- "Acquire company with 200 users"
- "Deploy new Finance module to 500 users"
- "Remove custom role X from all users"

**Output**:
```
What-If Scenario Analysis:
├── Scenario: [Description]
├── Current State:
│   └── Total License Cost: $450,000/month
├── Projected State:
│   └── Total License Cost: $520,000/month
├── Net Change: +$70,000/month (+15.6%)
├── Detailed Breakdown:
│   ├── Finance: +50 licenses @ $180 = +$9,000
│   ├── SCM: +30 licenses @ $180 = +$5,400
│   └── Operations: +20 licenses @ $90 = +$1,800
└── Recommendations: [Optimization opportunities]
```

---

## Algorithm Selection Framework

### Decision Matrix

| Algorithm | Business Value | Complexity | Data Availability | Priority Phase |
|-----------|----------------|------------|-------------------|----------------|
| **SoD Violation Detector** | Critical (SOX) | Medium | ✅ Available | MVP+ |
| **Anomalous Role Change** | Critical (Security) | Medium | ✅ Available | MVP+ |
| **Privilege Creep** | High | Medium | ✅ Available | Phase 2 |
| **Toxic Combination** | Critical (Fraud) | High | ✅ Available | Phase 2 |
| **Orphaned Account** | High | Low | ✅ Available | MVP |
| **Emergency Account** | Critical (Audit) | Medium | ⚠️ Need config | MVP+ |
| **Device License** | High (20-40% savings) | Low | ✅ Available | Phase 2 |
| **License Attach** | High (10-25% savings) | Medium | ✅ Available | Phase 2 |
| **Cross-App License** | High (5-15% savings) | Low | ✅ Available | Phase 2 |
| **License Forecaster** | High | High | ⚠️ Need HR feed | Phase 3 |
| **Session Anomaly** | High (Security) | Medium | ✅ Available | Phase 2 |
| **Stale Role** | Medium | Low | ✅ Available | Phase 2 |
| **Duplicate Role** | High | Medium | ✅ Available | Phase 2 |
| **What-If Modeler** | High | High | ✅ Available | Phase 3 |

**Legend**:
- ✅ Available: Data source exists
- ⚠️ Need config: Requires additional configuration or setup
- Complexity: Algorithm complexity (Low/Medium/High)

---

## Implementation Roadmap

### MVP+ (Immediate Value - 3-4 months)

**Algorithms**:
1. Orphaned Account Detector (Algorithm 3.5)
2. Time-Based Access Analyzer (Algorithm 5.3)
3. Contractor Access Tracker (Algorithm 5.4)

**Value**: Quick wins, low complexity, immediate security + cost impact

### Phase 2: Security & Compliance (6-9 months)

**Algorithms**:
1. SoD Violation Detector (Algorithm 3.1)
2. Anomalous Role Change Detector (Algorithm 3.2)
3. Privilege Creep Detector (Algorithm 3.3)
4. Toxic Combination Detector (Algorithm 3.4)
5. Emergency Account Monitor (Algorithm 3.6)

**Value**: Compliance readiness, fraud prevention, audit automation

### Phase 2: Cost Optimization (6-9 months)

**Algorithms**:
1. Device License Opportunity Detector (Algorithm 4.1)
2. License Attach Optimizer (Algorithm 4.2)
3. Cross-Application License Analyzer (Algorithm 4.3)
4. Duplicate Role Consolidator (Algorithm 6.3)

**Value**: Significant cost savings (20-40% in applicable scenarios)

### Phase 3: Advanced Analytics (9-12 months)

**Algorithms**:
1. License Demand Forecaster (Algorithm 4.4)
2. Session Anomaly Detector (Algorithm 5.1)
3. Geographic Access Pattern Analyzer (Algorithm 5.2)
4. What-If Scenario Modeler (Algorithm 7.3)

**Value**: Predictive capabilities, advanced security monitoring

---

## Algorithm 3.9: Entra-D365 License Sync Validator ⭐⭐⭐⭐ NEW

**Purpose**: Detect mismatches between tenant-level Entra ID licensing and D365 FO role-based licensing. Licenses exist at two independent levels (Entra ID managed by IT/Identity, D365 FO managed by functional admins) that can drift out of sync.

**Category**: Security & Compliance (3.x series)
**Phase**: Phase 2 (requires new data source — Microsoft Graph API)
**Complexity**: Medium
**Value**: Cost savings (ghost licenses, over-provisioned) + compliance (gaps)

**Business Value**:
- **Cost Recovery**: Detect ghost licenses (Entra license assigned, no D365 FO roles)
- **Compliance**: Detect users with D365 FO roles but missing/wrong Entra license
- **Over-Provisioning**: Detect users with enterprise Entra license who only need Team Members
- **Stale Entitlements**: Detect disabled D365 FO users still consuming Entra licenses

**Input Data Required**:
- `EntraLicenseData`: Per-user assigned licenses from Microsoft Graph API (NEW — 5th data source)
- `UserRoleAssignments`: Current D365 FO role assignments
- `SecurityConfigurationData`: Role → License type mapping (reuses Algorithm 1.1)
- `UserDirectory`: User status (active/disabled) in D365 FO

**New Data Source**: Microsoft Graph API (optional, requires admin consent)

| Endpoint | Data | Purpose |
|----------|------|---------|
| `GET /v1.0/subscribedSkus` | Tenant D365 SKUs, purchased/consumed quantity | License inventory |
| `GET /v1.0/users/{id}/licenseDetails` | Per-user assigned licenses with SKU IDs | What Entra thinks the user has |
| `GET /v1.0/users?$filter=assignedLicenses/any(...)` | Users filtered by D365 license SKUs | Bulk query for D365-licensed users |

**Permissions needed**: `User.Read.All`, `Directory.Read.All` (application-level, admin consent)

**Mismatch Types**:

| # | Mismatch | Entra License | D365 FO Roles | Risk | Action |
|---|----------|--------------|---------------|------|--------|
| **M1** | Ghost License | Has D365 license | No roles in D365 FO | Wasted spend | Remove Entra license or assign roles |
| **M2** | Compliance Gap | No/wrong D365 license | Has roles requiring higher license | Audit risk | Assign correct Entra license |
| **M3** | Over-Provisioned | Enterprise (Finance+SCM) | Roles only need Team Members | Overpaying at tenant level | Downgrade Entra license |
| **M4** | Stale Entitlement | Has D365 license | User disabled in D365 FO | Orphaned license | Remove Entra license |

**Output Structure**:
```
Entra-D365 Sync Mismatch Report:
├── User: [Name/ID]
├── Mismatch Type: [M1/M2/M3/M4]
├── Entra License: [SKU name and tier]
├── D365 FO Theoretical License: [from Algorithm 1.1]
├── D365 FO Roles: [list or empty]
├── D365 FO Status: [Active/Disabled]
├── Severity: [Critical/High/Medium]
├── Monthly Cost Impact: [$X]
├── Recommendation: [action]
└── Regulatory Impact: [compliance reference if applicable]
```

**Pseudocode**:

```
FUNCTION ValidateEntraD365LicenseSync()
  BEGIN
    mismatches ← []

    // Get all users with Entra D365 licenses
    entra_licensed_users ← GraphAPI.GetUsersWithD365Licenses()

    // Get all users with D365 FO roles
    d365_users ← GetAllUserRoleAssignments()

    // Build lookup maps
    entra_map ← BuildMap(entra_licensed_users, key=userId)
    d365_map ← BuildMap(d365_users, key=userId)

    // Check all Entra-licensed users
    FOR EACH user IN entra_licensed_users:
      entra_license ← entra_map[user.id].licenseType
      d365_roles ← d365_map.GET(user.id, default=EMPTY)
      theoretical_license ← Algorithm_1_1(d365_roles)  // Reuse existing

      // M1: Ghost License — Entra license but no D365 FO roles
      IF entra_license EXISTS AND d365_roles IS EMPTY:
        mismatches.APPEND({
          'type': 'M1_GHOST_LICENSE',
          'severity': 'MEDIUM',
          'savings': GetLicenseCost(entra_license),
          'recommendation': 'Remove Entra license or assign D365 FO roles'
        })

      // M3: Over-Provisioned — Entra license tier > theoretical
      ELSE IF entra_license.tier > theoretical_license.tier:
        tier_diff_cost ← GetLicenseCost(entra_license) - GetLicenseCost(theoretical_license)
        mismatches.APPEND({
          'type': 'M3_OVER_PROVISIONED',
          'severity': 'MEDIUM',
          'savings': tier_diff_cost,
          'recommendation': 'Downgrade Entra license to ' + theoretical_license
        })
      END IF

      // M4: Stale Entitlement — D365 FO user disabled but Entra license active
      IF user.d365_status == DISABLED AND entra_license EXISTS:
        mismatches.APPEND({
          'type': 'M4_STALE_ENTITLEMENT',
          'severity': 'MEDIUM',
          'savings': GetLicenseCost(entra_license),
          'recommendation': 'Remove Entra license (user disabled in D365 FO)'
        })
      END IF
    END FOR

    // Check all D365 FO users with roles (for M2)
    FOR EACH user IN d365_users:
      IF user.roles IS NOT EMPTY:
        entra_license ← entra_map.GET(user.id, default=NULL)
        theoretical_license ← Algorithm_1_1(user.roles)

        // M2: Compliance Gap — has roles but no/wrong Entra license
        IF entra_license IS NULL:
          mismatches.APPEND({
            'type': 'M2_COMPLIANCE_GAP',
            'severity': 'HIGH',
            'savings': 0,  // This is a compliance issue, not savings
            'recommendation': 'Assign Entra license: ' + theoretical_license
          })
        ELSE IF entra_license.tier < theoretical_license.tier:
          mismatches.APPEND({
            'type': 'M2_COMPLIANCE_GAP',
            'severity': 'HIGH',
            'savings': 0,
            'recommendation': 'Upgrade Entra license from ' + entra_license + ' to ' + theoretical_license
          })
        END IF
      END IF
    END FOR

    mismatches.SORT_BY('severity', 'savings')
    RETURN mismatches
  END
END FUNCTION
```

**SKU-to-License Mapping Table** (configurable per customer):

| Entra SKU ID (GUID) | Entra SKU Name | D365 FO License Type |
|---------------------|---------------|---------------------|
| `guid-1` | Dynamics 365 Finance | Finance |
| `guid-2` | Dynamics 365 Supply Chain Management | SCM |
| `guid-3` | Dynamics 365 Commerce | Commerce |
| `guid-4` | Dynamics 365 Team Members | Team Members |
| `guid-5` | Dynamics 365 Finance + SCM | Finance + SCM |

*Note: SKU GUIDs vary by tenant and EA/CSP agreement. This table must be configurable per customer deployment.*

**Risks & Mitigations**:

| Risk | Severity | Mitigation |
|------|----------|------------|
| Graph API requires admin consent — customer IT may resist | HIGH | Make Entra integration optional; agent works without it |
| SKU GUIDs differ per tenant — no universal mapping | MEDIUM | Configurable mapping table per customer deployment |
| Graph API rate limits (20,000 req/10min) | LOW | Delta sync + batch queries; volume is low (user count) |
| Some customers use group-based licensing in Entra | MEDIUM | Support both direct and group-based assignment detection |

**Estimated Additional Savings**: 3-8% on top of existing 15-25%, from ghost licenses, over-provisioning, and stale entitlements.

---

## Algorithm 4.7: New User License Recommendation Engine ⭐⭐⭐⭐ NEW

**Purpose**: Recommend the optimal license for new users based on their required menu items list, before they have any usage history. Inverts the current flow: Menu Items → Roles → License (instead of Roles → Menu Items → License).

**Category**: Cost Optimization (4.x series)
**Phase**: Phase 1 (MVP — greedy set-covering approximation)
**Complexity**: Medium-High
**Value**: Prevents over-licensing at source; estimated 5-15% savings on new user licenses

**Business Value**:
- **Prevent Over-Licensing at Source**: Data-driven license selection instead of "just in case" defaults
- **Optimal Role Selection**: Find minimum role combination covering required menu items
- **SoD Cross-Validation**: Ensure recommended roles don't create SoD conflicts (via Algorithm 3.1)
- **Cost Transparency**: Show license cost implications before provisioning

**Input Data Required**:
- `SecurityConfigurationData`: Menu item → Role → License mapping (existing, 700K records)
- `LicensePricingTable`: Configurable per customer (existing)
- `SODConflictMatrix`: For cross-validation with Algorithm 3.1 (existing)
- `RequiredMenuItems`: Admin-specified list of menu items the new user needs (new input)

**New Data Structure**: Reverse-index of Security Configuration (menu item → roles that provide it)

```
REVERSE_INDEX:
  MenuItemA → [Role1, Role2, Role5]
  MenuItemB → [Role2, Role3]
  MenuItemC → [Role1, Role4, Role6]
  ...
```
*Built from existing Security Config data (700K records) — one-time computation, cached.*

**Output Structure**:
```
New User License Recommendation:
├── Input Menu Items: N items specified
├── Recommendation #1 (Lowest Cost):
│   ├── Roles: [Role A, Role C]
│   ├── License Required: Team Members
│   ├── Monthly Cost: $60
│   ├── Menu Item Coverage: 100% (all N items)
│   ├── SoD Conflicts: None
│   └── Confidence: HIGH
├── Recommendation #2 (Fewest Roles):
│   ├── Roles: [Role B]
│   ├── License Required: Commerce
│   ├── Monthly Cost: $180
│   ├── Menu Item Coverage: 100%
│   ├── SoD Conflicts: None
│   └── Confidence: HIGH
├── Recommendation #3 (Common Pattern):
│   ├── Roles: [Role A, Role D]
│   ├── License Required: Finance
│   ├── Monthly Cost: $180
│   ├── Menu Item Coverage: 100%
│   ├── SoD Conflicts: 1 warning (Role A + Role D)
│   └── Confidence: MEDIUM
└── Note: "Theoretical recommendation — will be validated after 30 days of usage"
```

**Pseudocode**:

```
FUNCTION SuggestLicenseForNewUser(required_menu_items[])
  BEGIN
    // Step 1: Build reverse-index (cached, one-time)
    IF reverse_index IS NOT CACHED:
      reverse_index ← BuildReverseIndex(SecurityConfigurationData)
      CACHE(reverse_index)
    END IF

    // Step 2: Find which roles provide each required menu item
    candidate_roles ← {}
    FOR EACH menu_item IN required_menu_items:
      roles_with_item ← reverse_index.GET(menu_item, default=EMPTY)
      IF roles_with_item IS EMPTY:
        WARN("Menu item '" + menu_item + "' not found in any role")
        CONTINUE
      END IF
      candidate_roles[menu_item] ← roles_with_item
    END FOR

    // Step 3: Find MINIMUM role combinations covering all menu items
    // (Greedy set-covering approximation — not exhaustive)
    optimal_role_sets ← GreedySetCover(candidate_roles, max_results=10)

    // Step 4: For each role set, calculate license and cost
    recommendations ← []
    FOR EACH role_set IN optimal_role_sets:
      license ← Algorithm_1_1(role_set)
      cost ← pricing_table[license]

      // Step 5: Cross-validate with SoD (Algorithm 3.1)
      sod_conflicts ← CheckSODConflicts(role_set)

      coverage ← CalculateCoverage(role_set, required_menu_items, reverse_index)

      recommendations.APPEND({
        'roles': role_set,
        'roleCount': COUNT(role_set),
        'licenseRequired': license,
        'monthlyCost': cost,
        'menuItemCoverage': coverage,
        'sodConflicts': sod_conflicts,
        'confidence': IF COUNT(sod_conflicts) == 0 THEN 'HIGH' ELSE 'MEDIUM'
      })
    END FOR

    // Step 6: Rank by lowest cost, then fewest roles, then fewest SoD conflicts
    recommendations.SORT_BY(cost ASC, roleCount ASC, sodConflictCount ASC)

    // Return top 3
    RETURN recommendations[0:3]
  END
END FUNCTION

FUNCTION GreedySetCover(candidate_roles, max_results)
  BEGIN
    // Greedy approximation to minimum set cover (NP-hard problem)
    uncovered ← SET(candidate_roles.KEYS())  // All menu items to cover
    selected_roles ← []
    all_solutions ← []

    WHILE uncovered IS NOT EMPTY:
      // Find role that covers the most uncovered menu items
      best_role ← NULL
      best_coverage ← 0

      FOR EACH role IN GetAllCandidateRoles(candidate_roles):
        covered_by_role ← CountCoveredItems(role, uncovered, candidate_roles)
        IF covered_by_role > best_coverage:
          best_coverage ← covered_by_role
          best_role ← role
        END IF
      END FOR

      IF best_role IS NULL:
        BREAK  // No role can cover remaining items
      END IF

      selected_roles.APPEND(best_role)
      uncovered ← uncovered.MINUS(GetCoveredItems(best_role, candidate_roles))
    END WHILE

    all_solutions.APPEND(selected_roles)

    // Generate alternative solutions by varying starting role
    // (limited to max_results to bound computation)
    FOR i ← 1 TO MIN(max_results - 1, COUNT(GetAllCandidateRoles(candidate_roles))):
      alt_solution ← GreedySetCoverVariant(candidate_roles, exclude_first=i)
      IF alt_solution IS NOT NULL AND alt_solution NOT IN all_solutions:
        all_solutions.APPEND(alt_solution)
      END IF
    END FOR

    RETURN all_solutions
  END
END FUNCTION
```

**Integration Points**:

| Integration | How | Trigger |
|-------------|-----|---------|
| **Web App** | "New User License Wizard" — admin selects menu items, gets top-3 recommendations | Manual (admin initiates) |
| **API Endpoint** | `POST /api/v1/suggest-license` — accepts menu item list, returns recommendations | REST API |
| **Bulk Onboarding** | Upload CSV of new users + planned menu items → batch recommendations | Phase 2 deferral |

**Phase 1 MVP Scope**:
- Build reverse-index of Security Config data (menu items → roles)
- Implement greedy set-covering approximation (not exhaustive search)
- Web App: Simple form — admin selects menu items from searchable list, gets top-3 role+license recommendations
- SoD cross-validation with Algorithm 3.1 on recommended role combinations
- **Deferred to Phase 2**: Bulk CSV onboarding, department pattern learning, event-driven triggers

**Risks & Mitigations**:

| Risk | Severity | Mitigation |
|------|----------|------------|
| Set-covering is NP-hard for large role sets | MEDIUM | Greedy approximation + limit to top-10 candidates; D365 FO has < 200 roles typically |
| Admin may not know exact menu items needed | LOW | Offer searchable list with descriptions; role-based input as fallback |
| Recommendations may create SoD conflicts | MEDIUM | Cross-validate with Algorithm 3.1 before presenting |
| No usage data to validate recommendation | LOW | Flag as "theoretical — validated after 30 days of usage" |

---

## Summary

### Total Algorithm Count

- **Previously Documented**: 8 algorithms (Document 06)
- **Expansion**: 24 algorithms (This document, including 3.9 and 4.7)
- **Additional Detailed Specs**: 2.5 (Doc 09), 2.6 (Doc 10), 4.4 (Doc 11)
- **Total Portfolio**: 34 algorithms

### By Category

| Category | Count |
|----------|-------|
| **Cost Optimization** | 12 |
| **Security & Compliance** | 9 |
| **User Behavior & Analytics** | 4 |
| **Role Management** | 4 |
| **Advanced Analytics** | 5 |

### Business Value

- **Minimum Estimated Savings**: $500K/year for enterprise deployments
- **Maximum Estimated Savings**: $2M+/year for large organizations
- **Compliance Value**: SOX, GDPR, ISO 27001 readiness
- **Security Value**: Fraud prevention, breach detection

---

## 📚 Related Documentation

- `06-Algorithms-Decision-Logic.md` - Original 8 algorithms (role analysis, user optimization)
- `05-Functional-Requirements.md` - Core functional requirements
- `memory/D365-FO-License-Optimization-Patterns.md` - Optimization patterns reference
- `memory/D365-FO-Security-Reports-Guide.md` - Security reports reference

---

**Document Status**: Advanced Algorithm Research Complete ✅
**Total Algorithms Documented**: 34 (8 core + 24 advanced, including 3.9 and 4.7)
**Next Phase**: Prioritization and technical design

---

**End of Advanced Algorithms Expansion**
