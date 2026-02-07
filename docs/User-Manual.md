# D365 FO License Agent - User Manual

**Version:** 1.0.0
**Last Updated:** 2026-02-07
**Target Audience:** License Administrators, IT Managers, Finance Controllers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [License Optimization Workflow](#license-optimization-workflow)
5. [Security & Compliance Features](#security--compliance-features)
6. [New User License Wizard](#new-user-license-wizard)
7. [Reports & Analytics](#reports--analytics)
8. [Recommendation Management](#recommendation-management)
9. [Administration Settings](#administration-settings)
10. [FAQ](#faq)

---

## Introduction

The D365 FO License Agent helps you:

- **Reduce license costs by 15-25%** through AI-powered recommendations
- **Detect security risks** like segregation of duties (SoD) violations and privilege creep
- **Optimize license assignments** for new users based on their required access
- **Maintain compliance** with automated SoD monitoring and access reviews

This manual covers how to use the web application to review recommendations, approve license changes, monitor security alerts, and generate compliance reports.

---

## Getting Started

### Accessing the Application

1. **Navigate to:** https://d365-license-agent.azurestaticapps.net (or your custom domain)
2. **Login with:** Your organization's Microsoft 365 credentials (Azure AD authentication)
3. **Landing Page:** Executive Dashboard (shows key metrics and top opportunities)

### User Roles

| Role | Permissions | Typical Users |
|------|-------------|---------------|
| **Viewer** | View dashboard, recommendations, reports (read-only) | Finance controllers, auditors |
| **Operator** | View + approve/reject recommendations | IT managers, license admins |
| **Administrator** | Full access + configuration settings | IT security, system admins |

Contact your IT administrator if you need role changes.

---

## Dashboard Overview

The **Executive Dashboard** is your home page, providing a high-level view of license optimization and security status.

![Dashboard Screenshot Placeholder]

### Key Metrics Cards

1. **Total License Cost**
   - **What it shows:** Current monthly license spend across all D365 FO users
   - **Color coding:**
     - 🟢 Green (-%) = Cost decreased vs. last month
     - 🔴 Red (+%) = Cost increased
   - **Example:** "$180,000/month" with "-3.2%" means you're spending $180K monthly, down 3.2% from last month

2. **Monthly Savings**
   - **What it shows:** Savings achieved from implemented recommendations in the current month
   - **Details:** Click card to see breakdown by recommendation type
   - **Example:** "$12,500" means you saved $12,500 this month by implementing agent recommendations

3. **YTD Savings**
   - **What it shows:** Cumulative savings year-to-date (January 1 to today)
   - **Use case:** Report to CFO in quarterly business reviews
   - **Example:** "$75,000" in February means you saved $75K since January 1

4. **Users Analyzed**
   - **What it shows:** Total D365 FO users analyzed by the agent
   - **Pending count:** Number of users with pending recommendations awaiting your review
   - **Example:** "1,234 users analyzed, 156 with pending recommendations"

### Cost Trend Chart

**Purpose:** Visualize license cost over time to spot trends and validate savings.

**How to read:**

- **Blue line:** Actual monthly license cost
- **Dotted gray line:** Forecasted cost (if no optimizations applied)
- **Gap between lines:** Realized savings

**Interactive features:**

- Hover over data points to see exact values
- Click legend items to show/hide specific series
- Use date range picker (top-right) to change time period

### Top Opportunities Table

**Purpose:** Quick view of the 5 highest-value optimization opportunities.

| Column | Meaning |
|--------|---------|
| **Algorithm** | Which AI algorithm detected this opportunity (e.g., "2.2 - Read-Only Users") |
| **User Count** | How many users would be affected by this recommendation |
| **Monthly Savings** | Potential monthly savings if all users in this category are optimized |
| **Annual Savings** | Potential annual savings (Monthly × 12) |

**Actions:**

- Click row to view detailed user list and approve/reject recommendations
- Click **"View All Opportunities"** button to see full list (50+ potential opportunities)

### Security Alerts Panel

**Purpose:** Display critical security issues requiring immediate attention.

**Alert Severities:**

- 🔴 **CRITICAL** - Requires immediate action (e.g., SoD violation allowing fraud)
- 🟠 **HIGH** - Requires action within 24 hours (e.g., anomalous access at 2 AM)
- 🟡 **MEDIUM** - Review within 1 week (e.g., privilege creep over 18 months)

**Alert Types:**

| Type | What It Means | Example |
|------|---------------|---------|
| **SOD_VIOLATION** | User has conflicting roles that enable fraud | User can both create vendors AND approve payments to those vendors |
| **ANOMALOUS_ACCESS** | Unusual access pattern detected | User accessed critical financial forms at 2 AM on Saturday (normally works 9-5 weekdays) |
| **PRIVILEGE_CREEP** | User accumulated excessive roles over time without review | User started with 2 roles in 2024, now has 12 roles in 2026 without any access review |
| **ORPHANED_ACCOUNT** | Inactive account still consuming a license | User hasn't logged in for 180 days but still assigned Operations license |

**Actions:**

- Click alert to view details and remediation options
- Click **"Acknowledge"** if you've investigated and determined it's a false positive
- Click **"Remediate"** to launch guided workflow (e.g., remove conflicting role, disable account)

---

## License Optimization Workflow

This section covers the end-to-end process for reviewing and implementing license optimization recommendations.

### Step 1: Review Recommendation

1. **Navigate to:** Algorithms page (sidebar menu)
2. **Filter recommendations:**
   - **Algorithm Type:** Cost Optimization, Security, Behavior
   - **Priority:** High, Medium, Low
   - **Status:** Pending, Approved, Rejected, Implemented
3. **Select recommendation:** Click row to view details

**Recommendation Detail View:**

![Recommendation Details Screenshot Placeholder]

**Key Information:**

- **User Details:**
  - Name: John Doe
  - Email: john.doe@contoso.com
  - Current License: Operations Activity ($90/month)
  - Current Roles: Purchasing Agent, Inventory Clerk

- **AI Analysis:**
  - Algorithm: 2.2 - Read-Only User Detection
  - Confidence: 92%
  - Recommendation: Downgrade to Team Members ($60/month)
  - Monthly Savings: $30
  - Annual Savings: $360

- **Supporting Evidence:**
  - Activity Period Analyzed: Last 90 days
  - Total Operations: 1,234
  - Write Operations: 23 (1.9%)
  - Read Operations: 1,211 (98.1%)
  - Forms Accessed: PurchTable (read-only), VendTable (read-only), InventTable (read-only)

- **AI Explanation (Natural Language):**
  > "John Doe primarily accesses D365 FO in a read-only capacity, viewing purchase orders and vendor information without making updates. Over the past 90 days, only 1.9% of his actions involved writing data (e.g., updating a PO line). All forms he accesses regularly are available with a Team Members license. Downgrading would save $360 annually while maintaining his required access."

### Step 2: Validate Recommendation

**Before approving, verify:**

1. **Business Context:**
   - Is this user's role changing soon? (e.g., temporary read-only assignment)
   - Does this user need write access during month-end close? (seasonal pattern)

2. **Form Eligibility:**
   - Check **"Forms Accessed"** list
   - Verify all forms are Team Members-eligible (green checkmark = eligible)
   - If red X appears, user needs Operations license for that form

3. **Confidence Score:**
   - **> 90%** = Very safe to approve
   - **80-90%** = Safe, but review evidence
   - **< 80%** = Review carefully, consider rejecting if any doubts

**Talk to the User (Optional but Recommended):**

Before downgrading a user, consider sending them a quick message:

> "Hi John, our license optimization analysis shows you primarily use D365 FO in read-only mode. We're planning to adjust your license to Team Members (you'll keep all current access, just more cost-effective). Let me know if you have concerns. Thanks!"

### Step 3: Approve or Reject

**To Approve:**

1. Click **"Approve"** button
2. (Optional) Add approval comment: "Validated with user, confirmed read-only usage"
3. Confirm approval
4. **What happens next:**
   - Recommendation moves to "Approved" status
   - License change queued for next sync window (nightly at 2 AM)
   - User receives email notification (if configured)
   - User's license downgraded in Microsoft 365 Admin Center
   - Savings tracked and reflected in dashboard within 24 hours

**To Reject:**

1. Click **"Reject"** button
2. **Required:** Add rejection reason (e.g., "User needs write access during month-end close")
3. Confirm rejection
4. **What happens next:**
   - Recommendation archived
   - User retains current license
   - Agent learns from rejection (won't re-recommend for this user unless usage pattern changes)

### Step 4: Monitor Implementation

1. **Navigate to:** Recommendations > Implementation Status
2. **View in-progress implementations:**
   - **Queued:** Approved, waiting for sync window
   - **In Progress:** License change currently being applied
   - **Completed:** Successfully implemented
   - **Failed:** Implementation failed (requires manual intervention)

3. **Handle Failures:**
   - Click failed recommendation to view error details
   - Common failures:
     - User not found in Microsoft 365 (synced user deleted)
     - Insufficient licenses available (need to purchase more Team Members licenses)
     - API rate limit exceeded (retry automatically in 1 hour)

---

## Security & Compliance Features

### Segregation of Duties (SoD) Monitoring

**Purpose:** Detect and remediate role conflicts that enable fraud or errors.

**How to Use:**

1. **Navigate to:** Security > SoD Violations
2. **Review active violations:**

**Example Violation:**

| User | Role 1 | Role 2 | Conflict Rule | Severity | Detected |
|------|--------|--------|---------------|----------|----------|
| jane.smith@contoso.com | AP Clerk | Vendor Master Maintainer | SOD-AP-001 | CRITICAL | 2026-02-05 |

**Risk:** Jane can create a vendor and approve payment to that vendor (fraud risk)

**Remediation Options:**

1. **Remove Role:** Click "Remove Role 2" → Jane loses "Vendor Master Maintainer" role
2. **Create Exception:** Click "Create Exception" → Acknowledge risk, add justification (e.g., "Small company, only AP person, monthly manager review compensating control")
3. **Assign Compensating Control:** Click "Assign Control" → Add monthly manager review requirement

**Best Practice:** Resolve CRITICAL violations within 24 hours, HIGH within 1 week.

### Privilege Creep Detection

**Purpose:** Identify users who accumulated excessive roles over time without review.

**How It Works:**

- Agent analyzes role assignment history
- Flags users who gained 5+ roles in 12 months without access review
- Recommends role cleanup

**Review Process:**

1. **Navigate to:** Security > Privilege Creep
2. **Select user:** Click row to see role accumulation timeline
3. **Review each role:**
   - Last used date (if form access data available)
   - Assignment reason (from assignment history)
   - Business justification
4. **Remove unused roles:** Click "Remove" next to roles user hasn't used in 90+ days

### Anomalous Access Monitoring

**Purpose:** Detect unusual access patterns (e.g., after-hours access, sudden spikes).

**Alert Example:**

> **User:** mike.wilson@contoso.com
> **Pattern:** Accessed 15 critical financial forms between 2 AM - 4 AM Saturday
> **Normal Pattern:** Accesses 3-5 forms, 9 AM - 5 PM weekdays
> **Risk Level:** HIGH

**Actions:**

1. **Investigate:** Click "View Details" → See list of forms accessed, actions taken
2. **Contact User:** Verify legitimate business reason (e.g., month-end close requires weekend work)
3. **Acknowledge or Escalate:** If legitimate, click "Acknowledge." If suspicious, click "Escalate to Security Team"

---

## New User License Wizard

**Purpose:** Determine the optimal license for a new D365 FO user based on their required access.

**When to Use:** Hiring a new employee, contractor, or transferring someone to a role requiring D365 FO access.

### Step-by-Step Walkthrough

**Step 1: Specify Required Menu Items**

1. **Navigate to:** Wizard > New User License
2. **Enter user information:**
   - User email: newuser@contoso.com
   - Department: Procurement
   - Job title: Purchasing Coordinator

3. **Select required menu items** (forms/functions the user needs access to):

   **Example:** For a Purchasing Coordinator, select:
   - ☑ All purchase orders (PurchTable)
   - ☑ Purchase requisitions (PurchReqTable)
   - ☑ Vendor master (VendTable) - read-only
   - ☑ Product information management (InventTable) - read-only
   - ☐ General ledger (LedgerJournalTable) - not needed

4. **Click "Next"**

**Step 2: Review Recommendations**

Agent analyzes your menu item selections and presents optimal license + role combination:

**Recommendation Results:**

![Wizard Results Screenshot Placeholder]

**Option 1: Team Members (Recommended) - $60/month**

- **Roles to Assign:**
  - Purchasing Coordinator (custom role)
  - Vendor Information (read-only)
- **Access Provided:**
  - ✅ All selected menu items accessible
  - ✅ No SoD conflicts detected
  - ✅ Minimum license tier required
- **Annual Cost:** $720

**Option 2: Operations Activity - $90/month**

- **Roles to Assign:**
  - Purchasing Agent (standard role)
- **Access Provided:**
  - ✅ All selected menu items accessible
  - ✅ Additional write access to vendor master (not required per your selections)
  - ⚠ Over-provisioned (includes access beyond requirements)
- **Annual Cost:** $1,080
- **Annual Waste:** $360

**Step 3: Select and Provision**

1. **Select:** Click "Choose Option 1" (Team Members recommended)
2. **Review role assignments:**
   - Agent shows which D365 FO security roles will be assigned
   - Verify roles match job requirements
3. **Provision:**
   - Click "Provision User"
   - Agent creates user in D365 FO, assigns roles, assigns license in Microsoft 365
   - User receives welcome email with login instructions

**Time Saved:** Without agent: 2-3 hours researching roles, testing access. With agent: 5 minutes.

---

## Reports & Analytics

### Cost Allocation Report

**Purpose:** Allocate D365 FO license costs to departments for chargeback/showback.

**Generate Report:**

1. **Navigate to:** Reports > Cost Allocation
2. **Select parameters:**
   - Report period: 2026-01 (January 2026)
   - Allocation method: By user count OR by license cost
   - Format: Excel OR PDF
3. **Click "Generate"**

**Sample Output:**

| Department | User Count | License Cost | % of Total |
|------------|------------|--------------|------------|
| Procurement | 45 | $5,400 | 3.0% |
| Finance | 120 | $21,600 | 12.0% |
| Warehouse | 230 | $13,800 | 7.7% |
| Sales | 89 | $16,020 | 8.9% |
| **TOTAL** | **484** | **$56,820** | **31.5%** |

**Use Case:** Attach to department budget reports, track license spend by cost center.

### Savings Trend Report

**Purpose:** Demonstrate ROI of license optimization program over time.

**Key Metrics:**

- Monthly savings trend (line chart)
- Savings by algorithm type (pie chart)
- Approval vs. rejection rate (bar chart)
- Projected 12-month savings (if current approval rate continues)

**Audience:** CFO, IT leadership, quarterly business reviews

### Compliance Audit Report

**Purpose:** Demonstrate SoD compliance and access review completion for auditors.

**Includes:**

- **SoD Violations:** Current count, resolved count, average resolution time
- **Access Reviews:** % of users reviewed in past 12 months
- **Orphaned Accounts:** Count, total cost savings from disabling
- **High-Privilege Users:** List of users with 10+ roles, last review date

**Compliance Checklist:**

- ☑ All CRITICAL SoD violations resolved
- ☑ All HIGH SoD violations resolved or exceptions documented
- ☑ 95%+ of users access reviewed annually
- ☑ Zero orphaned accounts with active licenses
- ☑ All high-privilege users reviewed quarterly

**Export:** PDF format for audit documentation, Excel for detailed analysis.

---

## Recommendation Management

### Bulk Actions

**Purpose:** Approve or reject multiple recommendations at once (saves time for high-volume scenarios).

**How to Use:**

1. **Navigate to:** Algorithms page
2. **Filter to desired recommendations** (e.g., Algorithm 2.2, Priority: High)
3. **Select multiple rows:** Click checkboxes next to each recommendation
4. **Click "Bulk Approve"** or **"Bulk Reject"**
5. **Add comment** (applies to all selected recommendations)
6. **Confirm**

**Best Practice:** Only use bulk actions for recommendations with:
- High confidence (> 90%)
- Same algorithm type
- Similar business context (e.g., all users in same department)

**⚠ Caution:** Review individually for:
- CRITICAL security alerts
- Recommendations affecting executives or high-privilege users
- Recommendations with confidence < 80%

### Rollback Procedure

**Purpose:** Undo a license change if user reports issues after downgrade.

**Scenario:** You downgraded John Doe from Operations to Team Members. John now reports he can't access a critical form during month-end close.

**Rollback Steps:**

1. **Navigate to:** Recommendations > Implementation Status
2. **Filter to:** Completed, User: john.doe@contoso.com
3. **Select recommendation:** Click row
4. **Click "Rollback"**
5. **Select rollback speed:**
   - **Fast Restore (< 5 minutes):** Uses cached license assignment state
   - **Standard Restore (< 1 hour):** Re-provisions license via Microsoft 365 API
6. **Confirm rollback**
7. **Verify:** John receives Operations license within selected timeframe

**Post-Rollback:**

- Agent marks recommendation as "Rejected - User Reported Issue"
- Agent learns from rollback (won't re-recommend for this user)
- You receive email with details for root cause analysis

**SLA:** Fast restore completes 99% of the time within target. If it fails, standard restore is automatic fallback.

---

## Administration Settings

### Algorithm Configuration

**Purpose:** Tune algorithm parameters to match your organization's risk tolerance and business needs.

**Example: Algorithm 2.2 (Read-Only Detection)**

**Navigate to:** Admin > Algorithm Settings > 2.2

**Tunable Parameters:**

| Parameter | Default | Your Setting | Description |
|-----------|---------|--------------|-------------|
| **Lookback Days** | 90 | 180 | Days of user activity to analyze (increase for seasonal businesses) |
| **Write Threshold %** | 5% | 3% | Max % of write operations to qualify as read-only (lower = more aggressive) |
| **Min Activity Events** | 10 | 50 | Minimum activity events required (increase to reduce false positives) |
| **Confidence Threshold** | 85% | 90% | Minimum confidence to generate recommendation (higher = fewer but safer recommendations) |

**When to Adjust:**

- **Seasonal Business:** Increase Lookback Days to 180-365 to capture full seasonal cycle
- **High User Count:** Increase Confidence Threshold to 95% to reduce approval workload
- **Aggressive Savings Target:** Decrease Write Threshold to 2% (but expect more false positives)

### Notification Settings

**Configure email notifications for:**

- **Daily Digest:** Summary of new recommendations, security alerts (sent 8 AM daily)
- **Real-Time Alerts:** CRITICAL security alerts (sent immediately)
- **Weekly Summary:** Savings achieved, approval rate, top opportunities (sent Monday 9 AM)

**Recipients:**

- Add multiple email addresses (e.g., license-admins@contoso.com)
- Configure per alert type (security team gets security alerts, finance team gets savings reports)

### License Pricing

**Purpose:** Enter your actual Microsoft license costs (including discounts) for accurate savings calculations.

**Navigate to:** Admin > License Pricing

**Update prices:**

| License Type | List Price | Your Price | Currency |
|--------------|------------|------------|----------|
| Team Members | $60 | $54 | USD |
| Operations Activity | $90 | $85 | USD |
| Finance | $180 | $165 | USD |

**After updating:** Dashboard recalculates all savings metrics with your prices.

---

## FAQ

### Can I downgrade a user's license without them noticing?

**Answer:** For true read-only downgrades (Operations → Team Members), users typically don't notice any difference in their day-to-day D365 FO experience. However, we recommend notifying users as a courtesy and to avoid confusion if they later need write access.

**Best Practice:** Send brief email notification: "We've optimized your D365 license to better match your usage. No changes to your daily access. Contact IT if you have questions."

---

### What happens if I downgrade a user and they lose access they actually need?

**Answer:** Use the **Rollback feature** (see Recommendation Management > Rollback Procedure). You can restore the user's original license in under 5 minutes using Fast Restore.

**Prevention:** Before approving, review the "Forms Accessed" list in the recommendation detail. If you see a form with a red X (not Team Members-eligible), DO NOT approve the downgrade.

---

### How often does the agent analyze users?

**Answer:**

- **Daily Incremental Scan:** Agent processes new activity data every night (analyzes users with activity in last 24 hours)
- **Weekly Full Scan:** Every Sunday 2 AM, agent re-analyzes all users with full 90-day lookback
- **On-Demand Scan:** Click "Analyze Now" button for specific user to trigger immediate analysis

**Data Freshness:** Recommendations reflect data up to 24 hours old (data syncs from D365 FO nightly).

---

### Can the agent delete user accounts or make changes without my approval?

**Answer:** **No.** The agent NEVER makes changes without human approval. All recommendations go through your review and explicit approval. The agent is an analysis and recommendation engine, not an autopilot.

**Exception:** Auto-approve rules (optional feature, disabled by default). If enabled, you can configure rules like "Auto-approve all Algorithm 2.2 recommendations with confidence > 95%." Even with auto-approve, you receive email notification and can rollback within 72 hours.

---

### What if a recommendation has low confidence (e.g., 65%)?

**Answer:** Low confidence typically means:
- User has mixed usage pattern (some days read-only, some days write-heavy)
- Insufficient activity data (new user, only 2 weeks of data)
- Edge case scenario (uses form that's borderline Team Members-eligible)

**Recommendation:** **Reject** low-confidence recommendations unless you have additional business context that validates the recommendation. Agent learns from your rejections and improves over time.

---

### How do I know the SoD conflict matrix is accurate for my organization?

**Answer:** The agent ships with a **default matrix of 27 conflict rules** based on Microsoft best practices. However, you should customize it:

1. **Navigate to:** Admin > SoD Matrix Configuration
2. **Review each rule:** Does it apply to your organization? (e.g., small company might accept some conflicts large company wouldn't)
3. **Disable irrelevant rules:** Click "Disable" next to rules that don't apply
4. **Add custom rules:** Click "Add Rule" to define organization-specific conflicts

**Best Practice:** Work with your external auditor to validate your SoD matrix annually.

---

### Can I use the agent for multiple D365 FO environments (dev, UAT, production)?

**Answer:** Yes. Deploy separate agent instances for each environment:

| Environment | Agent URL | Database | Purpose |
|-------------|-----------|----------|---------|
| Development | dev-agent.contoso.com | SQL-Dev | Testing recommendations, algorithm tuning |
| UAT | uat-agent.contoso.com | SQL-UAT | Pre-production validation |
| Production | agent.contoso.com | SQL-Prod | Live recommendations |

**Cost:** Each environment requires separate Azure resources (~$70-145/month per environment).

**Recommendation:** Use dev/UAT for testing algorithm parameters before deploying to production.

---

### What data does the agent collect? Is it secure?

**Answer:**

**Data Collected:**
- User IDs (email addresses)
- D365 FO security role assignments
- Form access logs (form name, timestamp, read/write action)
- License assignments

**Data NOT Collected:**
- Record field values (e.g., purchase order amounts)
- Customer names, vendor names
- Financial data, personal data beyond user ID

**Security:**
- **Encryption:** All data encrypted in transit (TLS 1.2+) and at rest (AES-256)
- **Access Control:** Role-based access (Viewer/Operator/Administrator)
- **Audit Log:** All actions logged (who approved/rejected what, when)
- **Data Residency:** Data stored in Azure region matching your D365 FO region (e.g., US data in East US 2)

**Compliance:** Agent architecture supports SOC 2, GDPR, HIPAA compliance (requires proper configuration per your organization's requirements).

---

**End of User Manual**

---

## Quick Reference Card

Print this card and keep at your desk for quick access to common tasks.

| Task | Where to Go | Key Action |
|------|-------------|------------|
| **View top savings opportunities** | Dashboard | Review "Top Opportunities" table, click row for details |
| **Approve license downgrade** | Algorithms page | Filter to pending, click row, click "Approve" |
| **Rollback a license change** | Recommendations > Implementation Status | Find completed recommendation, click "Rollback" |
| **Resolve SoD violation** | Security > SoD Violations | Click row, choose remediation option |
| **Recommend license for new user** | Wizard > New User License | Enter menu items, review recommendation, provision |
| **Generate savings report** | Reports > Savings Trend | Select date range, click "Generate" |
| **Tune algorithm sensitivity** | Admin > Algorithm Settings | Select algorithm, adjust parameters, save |
| **Get help** | Help icon (top-right) | Open help docs, submit support ticket |

**Support:** license-agent-support@contoso.com | Help docs: https://agent.contoso.com/help
