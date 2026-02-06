# Rollback & Fast-Restore Procedures - D365 FO License & Security Optimization Agent

**Project**: D365 FO License & Security Optimization Agent
**Component**: Operational Procedures - Rollback & Recovery
**Last Updated**: 2026-02-06
**Status**: Requirements Definition
**Version**: 1.0
**Category**: Operational Procedures
**Priority**: Critical

---

## Table of Contents

1. [Purpose](#purpose)
2. [Design Principles](#design-principles)
3. [Fast-Restore SLA](#fast-restore-sla)
4. [Temporary License Elevation](#temporary-license-elevation)
5. [Escalation Path](#escalation-path)
6. [Communication Templates](#communication-templates)
7. [Observation Mode (Shadow Mode)](#observation-mode-shadow-mode)
8. [Rollback Tracking & Feedback Loop](#rollback-tracking--feedback-loop)
9. [Period-End Safeguards](#period-end-safeguards)
10. [Web Application Integration](#web-application-integration)
11. [Success Metrics](#success-metrics)
12. [Related Documentation](#related-documentation)

---

## Purpose

Define what happens when a license optimization recommendation is wrong or causes user access issues. This document establishes rollback procedures, fast-restore SLAs, escalation paths, and safeguards to ensure user productivity is never permanently impacted by optimization changes.

No optimization saves money if it blocks a user from doing their job. The cost of a single day of lost productivity for a finance team member during month-end close far exceeds any license savings. This document exists to guarantee that the License & Security Optimization Agent operates with a robust safety net at all times.

### Scope

This document covers:

- **Reactive procedures**: What to do when a user reports an access issue caused by optimization
- **Proactive safeguards**: Period-end freezes, observation mode, and validation gates that prevent issues before they occur
- **Feedback mechanisms**: How every rollback improves the system over time
- **Communication protocols**: How users, managers, and administrators are kept informed throughout the process

### Audience

| Role | Relevance |
|------|-----------|
| **D365 System Administrators** | Primary operators of rollback procedures |
| **Help Desk (Tier 1)** | First responders to user access issues |
| **License Manager** | Owns root cause analysis and algorithm tuning |
| **IT Management** | SLA oversight and escalation authority |
| **End Users** | Self-service restore capabilities |
| **Line Managers** | Approval workflows and team-level freeze requests |

---

## Design Principles

These principles govern all rollback and restore decisions. When in doubt, apply them in order of priority.

1. **User productivity is paramount** -- No optimization is worth sustained loss of access. A user blocked from their work costs the organization more per hour than any license savings. When in conflict, always choose restoring access over preserving an optimization.

2. **Fast restore over perfect analysis** -- Restore first, investigate later. The moment a user reports an access issue linked to an optimization change, the immediate action is to restore their access. Root cause analysis happens after the user is unblocked.

3. **Observation before action** -- Shadow mode validates before implementation. Every algorithm must prove its recommendations are accurate in observation mode before being permitted to execute changes. This prevents categories of errors from ever reaching production.

4. **Feedback loops** -- Every rollback improves the system. Rollback data feeds directly into algorithm confidence scoring. The system learns from its mistakes and becomes more conservative where it has been wrong before.

5. **Transparency** -- Users know what changed and why. Every optimization change is communicated in advance, and every restore is confirmed immediately. Users should never wonder why their access changed.

6. **Defense in depth** -- Multiple safeguards, not just one. Period-end freezes, observation mode, confidence thresholds, manager approvals, and self-service restore buttons all work together. No single safeguard failure should result in unrecoverable user impact.

---

## Fast-Restore SLA

### SLA Definitions

Clear, measurable targets for restoring user access after an optimization-related issue.

| Priority | Description | Restore Target | Maximum Allowed | Escalation Trigger |
|----------|-------------|---------------|-----------------|-------------------|
| **P1 - Critical** | User completely blocked from essential job functions | 1 hour | 2 hours | Auto-escalate to D365 Admin after 30 minutes |
| **P2 - High** | User blocked from non-essential but regular functions | 2 hours | 4 hours | Auto-escalate to D365 Admin after 1 hour |
| **P3 - Medium** | User has degraded access but can perform core work | 4 hours | 8 hours | Standard escalation path |
| **P4 - Low** | User notices change but workflow is not impacted | Next business day | 2 business days | Normal support queue |

### Priority Classification Guidelines

**P1 - Critical** applies when:
- User cannot access ANY D365 FO module required for their primary job function
- Finance user blocked during active period-end close (automatic P1 regardless of function)
- User blocked from a time-sensitive regulatory or compliance activity
- Multiple users affected by the same optimization change simultaneously

**P2 - High** applies when:
- User cannot access a specific module they use regularly (but not their primary function)
- User can work but must use manual workarounds that significantly slow productivity
- Manager reports that a team member's optimization change is causing downstream delays

**P3 - Medium** applies when:
- User lost access to a module they use occasionally (less than weekly)
- User can still perform all core functions but lost convenience features
- Access change causes minor inconvenience without blocking any workflow

**P4 - Low** applies when:
- User notices a license change notification but reports no actual workflow impact
- User proactively inquires about a change but confirms no access issues
- Cosmetic or reporting-only changes (dashboard visibility, non-functional permissions)

### SLA Clock Rules

- **Clock starts**: When the issue is reported through any channel (web app, help desk, email)
- **Clock stops**: When the user confirms access is restored OR when temporary elevation is granted (whichever comes first)
- **Business hours**: SLA clock runs during business hours only (configurable per organization timezone)
- **After-hours P1**: P1 issues reported after hours trigger on-call notification; clock starts at next business hour unless on-call responds first

---

## Temporary License Elevation

Temporary license elevation is the primary fast-restore mechanism. Rather than requiring full investigation before restoring access, the system grants immediate temporary access while the root cause is analyzed.

### Elevation Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Maximum duration** | 30 calendar days | Configurable per organization, 30-day default |
| **Automatic grant** | Enabled | System can auto-grant when user triggers "Request Access Restore" |
| **Approval required** | No (for auto-grant) | Manual elevations require Tier 1 or above approval |
| **License level** | Original pre-optimization license | Restores exactly what the user had before the change |
| **Tracking** | Full audit trail | Every elevation logged with reason, approver, expiry, and resolution |

### Elevation Lifecycle

```
[User Reports Issue] --> [Temporary Elevation Granted] --> [Investigation Period]
                                                                    |
                                                          +---------+---------+
                                                          |                   |
                                                  [Permanent Restore]  [Confirmed Downgrade]
                                                          |                   |
                                                  [Close Ticket]     [User Acknowledges]
                                                                              |
                                                                      [Close Ticket]
```

### Automatic Grant Process

1. User clicks "Request Access Restore" in the web application
2. System verifies the user had a recent optimization change (within last 90 days)
3. If verified: Temporary elevation is granted immediately (no human approval needed)
4. Help desk ticket is auto-created with P2 priority
5. D365 Admin, License Manager, and user's direct manager are notified
6. Investigation begins in parallel -- user is already unblocked

### Alerting & Expiry Management

| Alert | Timing | Recipients | Action Required |
|-------|--------|-----------|-----------------|
| **Elevation granted** | Immediately | User, Help Desk, D365 Admin, Manager | Investigation begins |
| **7-day warning** | 7 days before expiry | D365 Admin, License Manager | Resolution decision needed |
| **3-day warning** | 3 days before expiry | D365 Admin, License Manager, User | Escalate if unresolved |
| **1-day warning** | 1 day before expiry | All stakeholders | Final resolution required |
| **Expiry** | On expiry date | All stakeholders | Auto-extend if no resolution documented |

### Resolution Outcomes

Every temporary elevation MUST resolve to one of two outcomes:

1. **Permanent Restore**: The optimization recommendation was incorrect. User's license is permanently restored to the pre-optimization level. The recommendation is flagged as `ROLLED_BACK` and feeds into the feedback loop.

2. **Confirmed Downgrade with User Acknowledgment**: The optimization was correct, but the user needed time to adjust workflow or the timing was wrong. User formally acknowledges the downgrade is acceptable. If the user does NOT acknowledge, the elevation is extended and the case is escalated to the License Manager.

---

## Escalation Path

### Full Escalation Chain

#### Tier 0: User Self-Service

**User** reports access issue via one of three channels:

- **Web app "Request Access Restore" button** (preferred, fastest)
  - One-click temporary elevation
  - Auto-creates ticket with full context
  - SLA timer starts immediately

- **Help desk ticket**
  - User submits standard support ticket
  - Must be triaged by Tier 1 within 15 minutes
  - SLA timer starts on ticket creation

- **Direct email to license manager**
  - Accepted but discouraged (no automatic tracking)
  - License manager forwards to help desk for proper tracking
  - SLA timer starts when help desk acknowledges

#### Tier 1: Help Desk (Target: 15 minutes)

Within 15 minutes of receiving the report, Help Desk must:

1. **Verify the issue is license-related** (not a system outage, network issue, or unrelated D365 problem)
2. **Check the optimization change log**: Was this user recently changed by the optimization agent?
3. **If YES -- optimization-related**:
   - Trigger temporary license elevation immediately (no further approval needed)
   - Confirm with user that access is restored
   - Log the incident with full details
   - Route to Tier 2 for investigation
4. **If NO -- not optimization-related**:
   - Route to standard D365 support queue
   - Inform user that this is not related to license optimization
   - Close the optimization-specific ticket

#### Tier 2: D365 Administrator (Target: 30 minutes)

Within 30 minutes of receiving an escalated ticket, the D365 Admin must:

1. **Review the specific recommendation** that caused the change
   - Which algorithm generated it?
   - What was the confidence score?
   - What data supported the recommendation?
2. **Validate whether the rollback is appropriate**
   - Was the recommendation based on accurate data?
   - Did the user's role or responsibilities change recently?
   - Is there a pattern (multiple users affected by the same algorithm)?
3. **Execute full license restore if needed**
   - If temporary elevation is insufficient, perform permanent restore
   - Update the recommendation status to `ROLLED_BACK`
4. **Flag the recommendation** in the system
   - Mark as `ROLLED_BACK` with reason category
   - Add notes for Tier 3 root cause analysis
   - If multiple rollbacks from the same algorithm, flag for urgent Tier 3 review

#### Tier 3: License Manager (Target: 1 business day)

Within 1 business day, the License Manager must:

1. **Root cause analysis**
   - Was this an algorithm error, data quality issue, business exception, or seasonal pattern?
   - Review the full recommendation chain: data inputs, algorithm logic, confidence score, approval workflow
2. **Update algorithm confidence** for this user pattern
   - Reduce confidence score by 10-20% for the specific pattern
   - If 3+ rollbacks exist for the same pattern, disable the algorithm for that pattern pending full review
3. **Determine corrective action**
   - Algorithm bug: File defect, implement fix, re-validate in observation mode
   - Data quality: Identify stale or incorrect data source, implement data quality check
   - Business exception: Add exception rule for this user/role pattern
   - Seasonal: Link to seasonal awareness calendar (see Algorithm documentation)
4. **Implement permanent fix**
   - Update algorithm rules, confidence thresholds, or exception lists as needed
   - Document the fix and expected impact
   - Verify fix through observation mode before re-enabling

### Escalation Timeout Auto-Actions

| Timeout | Auto-Action |
|---------|------------|
| Tier 1 exceeds 15 minutes | Auto-notify D365 Admin directly |
| Tier 2 exceeds 30 minutes (P1) | Auto-notify IT Management |
| Tier 2 exceeds 1 hour (P2) | Auto-notify IT Management |
| Tier 3 exceeds 1 business day | Auto-notify License Manager's supervisor |
| Temporary elevation expiring without resolution | Auto-extend 7 days and escalate to IT Management |

---

## Communication Templates

### Template 1: Pre-Change Notification

**Sent**: 5 business days before scheduled license optimization change
**Channel**: Email + Web application notification
**Recipients**: Affected user, user's direct manager

```
Subject: Upcoming License Optimization - Action May Be Required by [DATE]

Dear [USER_NAME],

As part of our ongoing D365 Finance & Operations license optimization program,
we have identified an opportunity to optimize your license assignment.

WHAT IS CHANGING:
Your current license ([CURRENT_LICENSE_TYPE]) is being reviewed for potential
adjustment to ([RECOMMENDED_LICENSE_TYPE]) based on your usage patterns over
the past [OBSERVATION_PERIOD] days.

WHEN:
This change is scheduled for [CHANGE_DATE] at [CHANGE_TIME] [TIMEZONE].

WHY:
Our analysis shows that your current usage patterns align with a
[RECOMMENDED_LICENSE_TYPE] license. Specifically:
- [REASON_1]
- [REASON_2]
- [REASON_3]

WHAT TO EXPECT:
- You will retain access to: [RETAINED_MODULES]
- You may lose access to: [REMOVED_MODULES]
- If you need any of the removed modules, please let us know before the
  change date.

HOW TO OBJECT OR ESCALATE:
If you believe this change will impact your ability to do your job, you have
several options:
1. Click "Object to Change" in the web application: [WEB_APP_URL]
2. Reply to this email with your concerns
3. Contact the Help Desk at [HELP_DESK_CONTACT]
4. Speak with your manager, [MANAGER_NAME], who has also been notified

Your objection will be reviewed within 2 business days, and the change will
be paused until resolution.

CONTACT:
- Help Desk: [HELP_DESK_EMAIL] | [HELP_DESK_PHONE]
- License Manager: [LICENSE_MANAGER_EMAIL]
- Web Application: [WEB_APP_URL]

Thank you for your cooperation in helping us optimize our D365 licensing costs.

Best regards,
D365 License Optimization Team
```

---

### Template 2: Post-Change Follow-Up

**Sent**: 1 business day after the license optimization change was applied
**Channel**: Email + Web application notification
**Recipients**: Affected user

```
Subject: License Optimization Applied - Please Verify Your Access

Dear [USER_NAME],

The license optimization change described in our previous communication has
been applied as of [CHANGE_DATE].

WHAT CHANGED:
- Previous license: [PREVIOUS_LICENSE_TYPE]
- New license: [NEW_LICENSE_TYPE]
- Modules affected: [AFFECTED_MODULES]

HOW TO REPORT ISSUES:
If you experience ANY access issues or cannot perform your regular work:

1. FASTEST: Click "Request Access Restore" in the web application:
   [WEB_APP_URL]
   This will immediately restore your previous access while we investigate.

2. Contact Help Desk: [HELP_DESK_EMAIL] | [HELP_DESK_PHONE]
   Reference ticket: [OPTIMIZATION_TICKET_ID]

3. Reply to this email describing the issue.

ACCESS RESTORE GUARANTEE:
If this change causes any disruption to your work, your previous access will
be restored within [SLA_TARGET] of your report. You will NOT be left without
access to tools you need.

YOUR FEEDBACK MATTERS:
Please take 30 seconds to let us know how this change affected you:
[FEEDBACK_SURVEY_URL]

Your feedback directly improves our optimization accuracy for all users.

Best regards,
D365 License Optimization Team
```

---

### Template 3: Emergency Restore Confirmation

**Sent**: Immediately upon access restore (temporary or permanent)
**Channel**: Email + Web application notification + SMS (if P1)
**Recipients**: Affected user, user's direct manager, Help Desk

```
Subject: ACCESS RESTORED - Your D365 Access Has Been Reinstated

Dear [USER_NAME],

Your D365 Finance & Operations access has been restored as of
[RESTORE_TIMESTAMP].

CONFIRMATION:
- Your license has been restored to: [RESTORED_LICENSE_TYPE]
- All previously available modules are accessible immediately
- No further action is required from you at this time

WHAT HAPPENED:
A recent license optimization change ([OPTIMIZATION_TICKET_ID]) affected your
access to [AFFECTED_MODULES]. Upon your report, we have restored your full
access per our fast-restore guarantee.

WE APOLOGIZE FOR THE INCONVENIENCE:
We take access disruptions seriously. Your report has been logged and will be
used to improve our optimization accuracy. Our goal is to optimize costs
without ever impacting your ability to do your work.

NEXT STEPS:
- Restoration type: [TEMPORARY / PERMANENT]
- If TEMPORARY: Your access is guaranteed for [ELEVATION_DURATION] days while
  we investigate. You will be contacted before any further changes.
- If PERMANENT: The optimization recommendation has been reversed. No further
  changes will be made to your license without a new review cycle.

STILL HAVING ISSUES?
If your access is not fully restored or you encounter additional problems:
- Web application: [WEB_APP_URL]
- Help Desk: [HELP_DESK_EMAIL] | [HELP_DESK_PHONE]
- Your ticket: [TICKET_ID]

Best regards,
D365 License Optimization Team
```

---

### Template 4: Monthly Optimization Summary

**Sent**: First business day of each month
**Channel**: Email
**Recipients**: Line managers, IT Management, License Manager

```
Subject: Monthly License Optimization Report - [MONTH] [YEAR]

Dear [MANAGER_NAME],

Here is the monthly summary of D365 license optimization activities for your
team and the organization.

YOUR TEAM ([DEPARTMENT_NAME]):
- Users optimized this month: [TEAM_OPTIMIZED_COUNT] of [TEAM_TOTAL_COUNT]
- License cost savings (team): [TEAM_SAVINGS_AMOUNT] ([TEAM_SAVINGS_PERCENT]%)
- Rollbacks requested: [TEAM_ROLLBACK_COUNT]
- Average satisfaction score: [TEAM_SATISFACTION_SCORE]/5.0

ORGANIZATION SUMMARY:
- Total users optimized: [ORG_OPTIMIZED_COUNT]
- Total license savings: [ORG_SAVINGS_AMOUNT] ([ORG_SAVINGS_PERCENT]%)
- Total rollbacks: [ORG_ROLLBACK_COUNT] ([ORG_ROLLBACK_PERCENT]% rollback rate)
- Organization satisfaction: [ORG_SATISFACTION_SCORE]/5.0
- SLA adherence: [SLA_ADHERENCE_PERCENT]%

ROLLBACK ANALYSIS:
- Algorithm errors: [ALGO_ERROR_COUNT]
- Data quality issues: [DATA_QUALITY_COUNT]
- Business exceptions: [BUSINESS_EXCEPTION_COUNT]
- Seasonal adjustments: [SEASONAL_COUNT]
- User preference overrides: [USER_PREF_COUNT]

UPCOMING CHANGES:
- Scheduled optimizations next month: [NEXT_MONTH_COUNT]
- Users in observation mode: [OBSERVATION_COUNT]
- Freeze periods: [FREEZE_PERIODS]

ACTIONS AVAILABLE:
- Review pending recommendations for your team: [WEB_APP_URL]
- Request team freeze for upcoming projects: [FREEZE_REQUEST_URL]
- View detailed report: [DETAILED_REPORT_URL]

Best regards,
D365 License Optimization Team
```

---

## Observation Mode (Shadow Mode)

### Overview

Observation mode (also called shadow mode) is a mandatory validation phase for every algorithm before it is permitted to execute license changes in production. During observation mode, the system generates recommendations but does NOT execute them. Instead, it tracks whether the recommendations would have been correct.

### Observation Parameters

| Parameter | Default Value | Configurable | Notes |
|-----------|--------------|-------------|-------|
| **Duration** | 30 days | Yes (30-60 days) | Minimum 30 days, no maximum |
| **Behavior** | Generate recommendations only | No | Never executes changes during observation |
| **Tracking** | Full recommendation log | No | All recommendations recorded with timestamps |
| **Validation** | Continuous | No | Compares recommendations against actual user behavior |
| **Exit threshold** | 95% accuracy | Yes (90-99%) | Must meet threshold to exit observation |
| **Per-algorithm** | Independent | No | Each algorithm has its own observation state |

### How Observation Mode Works

1. **Algorithm generates recommendation**: "User X should be downgraded from Operations to Team Members license"
2. **Recommendation is logged but NOT executed**: User X retains their current license
3. **System monitors User X's actual behavior** during the observation period:
   - Did User X access modules that would have been removed?
   - How frequently? How recently?
   - Would User X have been blocked from any work?
4. **At end of observation period**: Compare all recommendations against actual usage
   - If User X never accessed the modules: Recommendation was CORRECT (true positive)
   - If User X accessed the modules: Recommendation was WRONG (false positive)

### Validation Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **True Positive Rate** | Correct downgrade recommendations / Total downgrade recommendations | > 95% |
| **False Positive Rate** | Incorrect recommendations that would have blocked users | < 5% |
| **False Positive Impact** | Number of work hours that would have been lost | 0 hours (target) |
| **Coverage** | Percentage of users evaluated during observation | > 80% |

### Algorithm State Machine

```
+---------------------+          +---------------------+          +---------------------+
|                     |          |                     |          |                     |
|  Algorithm Created  +--------->+  Observation Mode   +--------->+  Validation Review  |
|                     |          |                     |          |                     |
+---------------------+          +---------+-----------+          +---------+-----------+
                                           |                               |
                                           |                      +--------+--------+
                                           |                      |                 |
                                           |               +------v------+   +------v------+
                                           |               |             |   |             |
                                           |               | Active Mode |   |   Back to   |
                                           |               |             |   | Observation |
                                           |               +-------------+   +------+------+
                                           |                                        |
                                           +----------------------------------------+
```

**State Transitions:**

| From | To | Trigger | Requirements |
|------|----|---------|-------------|
| Algorithm Created | Observation Mode | Algorithm deployed | Automatic on deployment |
| Observation Mode | Validation Review | Observation period complete | Minimum 30 days elapsed |
| Validation Review | Active Mode | Accuracy meets threshold | Accuracy >= 95%, License Manager approval |
| Validation Review | Back to Observation | Accuracy below threshold | Accuracy < 95% or License Manager rejects |
| Back to Observation | Observation Mode | Algorithm updated | New observation period begins (minimum 30 days) |
| Active Mode | Observation Mode | Algorithm updated OR 3+ rollbacks | Any code change or excessive rollbacks triggers re-observation |

### Observation Mode Exit Criteria

An algorithm may exit observation mode and enter active mode ONLY when ALL of the following are met:

1. Minimum observation duration has elapsed (default: 30 days)
2. Recommendation accuracy is at or above threshold (default: 95%)
3. Zero false positives that would have caused P1 (Critical) user impact
4. License Manager has reviewed the observation report and approved activation
5. No active period-end freeze is in effect

---

## Rollback Tracking & Feedback Loop

### Rollback Data Capture

Every rollback MUST be logged with the following data fields:

| Field | Description | Example |
|-------|------------|---------|
| `rollback_id` | Unique identifier | `RB-2026-0142` |
| `user_id` | Affected user | `jane.doe@contoso.com` |
| `original_recommendation_id` | The recommendation that was rolled back | `REC-2026-3847` |
| `algorithm_id` | Algorithm that generated the recommendation | `2.2-readonly-detector` |
| `algorithm_version` | Version of the algorithm at time of recommendation | `1.3.2` |
| `confidence_score` | Confidence score of the original recommendation | `0.87` |
| `change_date` | When the optimization change was applied | `2026-01-15T09:00:00Z` |
| `report_date` | When the user reported the issue | `2026-01-16T14:30:00Z` |
| `restore_date` | When access was restored | `2026-01-16T15:12:00Z` |
| `time_to_restore` | Duration from report to restore | `42 minutes` |
| `priority` | Issue priority classification | `P2 - High` |
| `rollback_category` | Root cause category (see below) | `SEASONAL` |
| `rollback_reason` | Detailed explanation | `User accesses GL module only during quarter-end close` |
| `resolution_type` | Permanent restore or confirmed downgrade | `PERMANENT_RESTORE` |
| `investigation_notes` | Tier 3 root cause analysis notes | Free text |

### Rollback Categories

| Category | Code | Description | Algorithm Impact |
|----------|------|------------|-----------------|
| **Algorithm Error** | `ALGORITHM_ERROR` | The algorithm made an incorrect recommendation based on the data available. Logic flaw or edge case not handled. | Confidence reduced 20%. Bug filed. Algorithm returns to observation mode if 3+ occurrences. |
| **Data Quality** | `DATA_QUALITY` | The underlying usage data was stale, incomplete, or incorrect. The algorithm logic was sound but inputs were wrong. | Confidence reduced 10%. Data source investigation required. Data quality check added. |
| **Business Exception** | `BUSINESS_EXCEPTION` | The user has a legitimate but unusual need that does not follow standard patterns. Examples: cross-functional project, temporary assignment, specialized role. | Confidence reduced 10%. Exception rule added for this user/role pattern. |
| **Seasonal** | `SEASONAL` | The user was in an off-season period when the observation was made. They need the access during specific periods (e.g., month-end, year-end, audit season). | Confidence reduced 15%. Linked to seasonal awareness calendar. Algorithm updated to check seasonal patterns. |
| **User Preference** | `USER_PREFERENCE` | The user objected to the change and business management approved the override. The recommendation may have been technically correct but was overridden for business reasons. | Confidence unchanged. Override logged. Not counted against algorithm accuracy. |

### Feedback Loop Mechanics

**Confidence Score Adjustment:**

- Each rollback reduces the algorithm's confidence score for the specific user pattern that triggered the rollback
- Reduction amount depends on rollback category (see table above)
- Confidence scores are bounded: minimum 0.0, maximum 1.0
- Recommendations below confidence threshold (default: 0.70) require manual approval before execution

**Automatic Circuit Breaker:**

- 3 or more rollbacks for the same algorithm + pattern combination within a 90-day window triggers an automatic disable
- The algorithm is disabled for that specific pattern (not globally) pending License Manager review
- License Manager must investigate, implement a fix, and re-enable through observation mode
- Circuit breaker resets after the algorithm completes a new observation cycle with >= 95% accuracy

**Monthly Rollback Review:**

The License Manager must conduct a monthly rollback review covering:

1. Total rollbacks by category and algorithm
2. Trends: Are rollbacks increasing or decreasing?
3. Patterns: Are specific user groups, departments, or roles disproportionately affected?
4. Algorithm health: Which algorithms have the highest rollback rates?
5. Action items: Specific improvements to implement before next review
6. Report distribution: Summary shared with IT Management

---

## Period-End Safeguards

### Month-End / Quarter-End / Year-End Freeze

Period-end activities in finance and operations environments frequently involve access to modules and functions that are used infrequently during normal operations. Running optimization changes during these periods creates unacceptable risk of blocking critical financial processes.

#### Freeze Rules

| Rule | Detail |
|------|--------|
| **Scope** | ALL license optimization changes are frozen during freeze windows |
| **Includes** | New recommendations, pending approvals, scheduled executions |
| **Excludes** | Temporary elevations (restore actions are NEVER frozen) |
| **Applies to** | Month-end close, quarter-end close, year-end close, audit periods |
| **Configuration** | Freeze dates configurable per organization in admin settings |
| **Override** | Senior management (IT Director or above) can override with documented approval and business justification |

#### Default Freeze Calendar

| Period | Freeze Start | Freeze End | Approximate Duration |
|--------|-------------|-----------|---------------------|
| **Month-end** | Last 5 business days of month | First 5 business days of next month | ~10 business days |
| **Quarter-end** | Last 7 business days of quarter | First 7 business days of next quarter | ~14 business days |
| **Year-end** | December 15 | January 15 | ~1 month |
| **Audit period** | Configurable per organization | Configurable per organization | Varies |

#### Rationale

During period-end close:
- Finance users access GL posting, consolidation, and reporting modules that may be unused the rest of the month
- Operations users run inventory close, production close, and cost roll-up processes
- Compliance users generate regulatory reports and audit evidence
- Cross-functional users perform reconciliations that span multiple modules

An optimization algorithm observing 25 days of non-use could incorrectly conclude a user does not need GL posting access -- when in reality they need it for 5 critical days per month. The freeze window prevents this class of errors entirely.

#### Freeze Override Process

1. Senior management submits override request via web application or email
2. Request must include: business justification, affected users, risk acknowledgment
3. License Manager reviews and documents the override
4. Override is logged in the audit trail with full approval chain
5. Any rollbacks during an override period are flagged as high-priority for review

---

## Web Application Integration

### "Request Access Restore" Button

The primary self-service mechanism for users experiencing optimization-related access issues.

#### Visibility Rules

- Button is visible to any user who had a license optimization change within the last 90 days
- Button appears on the user's D365 FO home page AND in the License Optimization web application
- Button is prominently displayed (not buried in menus) with clear labeling
- Button is NOT visible to users who have not been affected by optimization changes

#### User Flow

```
[User clicks "Request Access Restore"]
         |
         v
[System verifies recent optimization change exists]
         |
    +----+----+
    |         |
   YES        NO
    |         |
    v         v
[Reason selection      [Message: "No recent
 dropdown + optional    optimization changes
 text field]            found. Contact Help
    |                   Desk for other issues."]
    v
[One-click submit]
    |
    v
[Temporary license elevation granted IMMEDIATELY]
    |
    v
[Confirmation displayed to user]
    |
    v
[P2 ticket auto-created with SLA timer started]
    |
    v
[Notifications sent to: Help Desk, D365 Admin, License Manager, User's Manager]
```

#### Reason Selection Dropdown

| Option | Description |
|--------|------------|
| Cannot access a module I need | Blocked from a specific D365 module |
| Cannot perform my regular tasks | General workflow disruption |
| Preparing for period-end activities | Need access for upcoming close process |
| Project or temporary assignment requires access | Cross-functional or special project need |
| Other (please describe) | Free text required |

#### Button Behavior

- **One-click**: After reason selection, a single click triggers the restore
- **Immediate**: Temporary license elevation is granted within seconds (automated, no human in the loop)
- **SLA timer**: P2 clock starts automatically upon submission
- **Auto-resolve**: If no further action is taken within 48 hours and user has not reported additional issues, the ticket is auto-closed (temporary elevation remains active for full duration)

### Manager Dashboard

The manager dashboard provides line managers with visibility and control over optimization changes affecting their direct reports.

#### Dashboard Features

| Feature | Description |
|---------|------------|
| **Team optimization overview** | View all optimization changes for direct reports (pending, applied, rolled back) |
| **Approve/reject recommendations** | Review and approve or reject pending optimization recommendations for team members |
| **Request team freeze** | Request a freeze on all optimization changes for the team during project periods or other business events |
| **Rollback history** | View all rollbacks for team members with categories and resolution status |
| **Satisfaction metrics** | Team-level satisfaction scores from post-change surveys |
| **Cost savings summary** | Team-level license cost savings achieved through optimization |
| **Upcoming changes** | Calendar view of scheduled optimization changes for team members |

#### Team Freeze Request

Managers can request a temporary freeze on all optimization changes for their team:

- **Duration**: Up to 30 days (extensions require IT Management approval)
- **Reason required**: Project name, business justification
- **Approval**: Auto-approved for up to 14 days; 15-30 days requires License Manager approval
- **Scope**: Applies to all direct reports in the manager's D365 organizational hierarchy
- **Notification**: License Manager and IT Management notified of all team freezes

---

## Success Metrics

### Key Performance Indicators

| Metric | Target | Measurement Method | Reporting Frequency |
|--------|--------|-------------------|-------------------|
| **Fast-restore SLA adherence** | > 95% | P1 and P2 tickets restored within target time / Total P1 and P2 tickets | Weekly |
| **Rollback rate** | < 5% | Total rollbacks / Total optimization changes executed | Monthly |
| **User satisfaction post-change** | > 90% positive | Post-change survey responses (4 or 5 out of 5) | Monthly |
| **Observation mode accuracy** | > 95% | True positives / Total recommendations during observation | Per algorithm, per observation cycle |
| **Mean time to restore (MTTR)** | < 2 hours | Average time from issue report to access restoration across all priorities | Monthly |
| **Period-end incident rate** | 0 | P1/P2 tickets caused by optimization during freeze windows | Quarterly |
| **Feedback loop effectiveness** | Decreasing trend | Rollback rate trend over 6-month rolling window | Quarterly |
| **Communication effectiveness** | < 2% objection rate | Pre-change objections / Total pre-change notifications sent | Monthly |

### Metric Thresholds and Actions

| Metric | Green | Yellow | Red | Red Action |
|--------|-------|--------|-----|-----------|
| SLA adherence | >= 95% | 90-94% | < 90% | Escalate to IT Management, review staffing |
| Rollback rate | < 5% | 5-10% | > 10% | Pause all active algorithms, full review |
| User satisfaction | >= 90% | 80-89% | < 80% | Pause new optimizations, user outreach |
| MTTR | < 2 hrs | 2-4 hrs | > 4 hrs | Process review, staffing assessment |
| Observation accuracy | >= 95% | 90-94% | < 90% | Algorithm stays in observation, investigation |

---

## Related Documentation

| Document | Relevance |
|----------|-----------|
| [06-Algorithms-Decision-Logic.md](./06-Algorithms-Decision-Logic.md) | Algorithm definitions and confidence scoring referenced by rollback procedures |
| [12-Final-Phase1-Selection.md](./12-Final-Phase1-Selection.md) | Phase 1 algorithm selection and implementation priority |
| [14-Web-Application-Requirements.md](./14-Web-Application-Requirements.md) | Web application UI requirements including the "Request Access Restore" button and manager dashboard |

---

## Document Status

| Item | Status |
|------|--------|
| Fast-Restore SLA | Defined |
| Temporary License Elevation | Defined |
| Escalation Path | Defined |
| Communication Templates | Defined |
| Observation Mode | Defined |
| Rollback Tracking | Defined |
| Period-End Safeguards | Defined |
| Web Application Integration | Defined |
| Success Metrics | Defined |

---

**End of Document**

*This document is part of the D365 FO License & Security Optimization Agent requirements suite. All procedures defined herein are subject to review and refinement during implementation.*
