# Functional Requirements - D365 FO License & Security Optimization Agent

**Project**: Building an AI-powered agent on Azure Foundry for D365 FO license and security optimization
**Last Updated**: 2026-02-05
**Status**: Requirements Definition Phase
**Version**: 1.0

---

## 📑 Table of Contents

1. [Vision & Goals](#vision--goals)
2. [Target Users & Stakeholders](#target-users--stakeholders)
3. [Core Capabilities](#core-capabilities)
4. [MVP Features (Phase 1)](#mvp-features-phase-1)
5. [Future Features (Phase 2+)](#future-features-phase-2)
6. [Non-Functional Requirements](#non-functional-requirements)
7. [Success Metrics](#success-metrics)

---

## Vision & Goals

### **Vision**

To build an **intelligent agent** that:
- **Analyzes** D365 FO license assignments and security configurations in real-time
- **Optimizes** license costs through data-driven, actionable recommendations
- **Monitors** security compliance and role assignments continuously
- **Automates** license management and governance workflows

### **Primary Goals**

| Goal | Description | Success Measure |
|------|-------------|-----------------|
| **Cost Optimization** | Reduce unnecessary license spend | Achieve 15-30% license cost reduction |
| **Security Compliance** | Maintain proper security governance | Zero compliance violations |
| **Operational Efficiency** | Automate manual reviews | Reduce analysis time by 80% |
| **Risk Management** | Proactive security monitoring | Detect issues before audits |

---

## Target Users & Stakeholders

### **Primary Users**

| User Type | Role | Needs | Priority Features |
|-----------|------|-------|-------------------|
| **System Administrators** | D365 FO Admins | Quick insights, actionable recommendations | License optimization dashboards, compliance alerts |
| **Security Officers** | Compliance Managers | Audit support, violation detection | SoD reports, access reviews, change tracking |
| **IT Management** | CIO, IT Directors | Cost dashboards, ROI metrics | Executive summaries, cost savings reports |
| **Finance/Procurement** | Budget Owners | License cost analysis, forecasting | Budget planning, cost allocation reports |
| **Line Managers** | Department Heads | Team license optimization | Team license reports, approval workflows |

### **Stakeholders**

| Stakeholder | Interest | Success Criteria |
|-------------|----------|-----------------|
| **CFO/Finance** | Cost control | License budget adherence |
| **CISO** | Security posture | Zero critical violations |
| **Audit Team** | Compliance evidence | Automated reports available |
| **Department Heads** | Team optimization | Right-sized licenses for teams |
| **End Users** | Appropriate access | Licenses match job requirements |

---

## Core Capabilities

### **Capability 1: License Optimization** ⭐

**Description**: Analyze and optimize license assignments based on actual usage and theoretical requirements

**Key Features**:
- Calculate theoretical license requirement per user (based on roles)
- Analyze actual usage patterns (from telemetry)
- Identify over-licensed users (assigned > required)
- Identify inactive users (no activity in 90+ days)
- Recommend license downgrades
- Calculate cost savings

**User Story**:
> "As a System Administrator, I want to see which users are over-licensed so I can reduce license costs while maintaining productivity."

---

### **Capability 2: Security Monitoring** 🔒

**Description**: Monitor security configurations and detect potential issues proactively

**Key Features**:
- Detect anomalous role changes (unauthorized, after-hours, rapid assignments)
- Identify segregation of duties (SoD) violations
- Track "Not Entitled" access (compliance gaps)
- Monitor role proliferation (too many custom roles)
- Alert on suspicious user activities
- Maintain audit trail

**User Story**:
> "As a Security Officer, I want to be alerted immediately when high-privilege roles are assigned without approval, so I can prevent security breaches."

---

### **Capability 3: Role Management** 📋

**Description**: Analyze and optimize security role definitions and assignments

**Key Features**:
- Analyze role usage patterns
- Identify similar roles (consolidation opportunities)
- Detect roles with excessive privileges
- Review custom role definitions
- Recommend role standardization
- Track role assignment changes

**User Story**:
> "As a System Administrator, I want to identify redundant custom roles so I can consolidate them and simplify security management."

---

### **Capability 4: Reporting & Analytics** 📊

**Description**: Provide comprehensive reports and dashboards for decision-making

**Key Features**:
- License cost dashboards
- Security health scorecards
- User access review reports
- Change history/audit trails
- Executive summaries with ROI
- Compliance reports (SOX, GDPR, ISO)
- Trend analysis and forecasting

**User Story**:
> "As a CFO, I want a monthly report showing license cost trends, optimization opportunities, and ROI from license rightsizing initiatives."

---

### **Capability 5: New User License Suggestion** ⭐ NEW

**Description**: Recommend the optimal license for new users based on their required menu items, before they have any usage history. Admin specifies needed menu items, agent determines which roles provide that access with the lowest license requirement.

**Key Features**:
- Menu-items-first recommendation (Menu Items → Roles → License)
- Reverse-index of Security Configuration for fast lookup
- Greedy set-covering to find minimum role combinations
- Top-3 role+license recommendations ranked by cost
- SoD cross-validation with Algorithm 3.1 on recommended roles
- Theoretical flag — validated after 30 days of actual usage

**User Story**:
> "As a System Administrator onboarding a new user, I want to specify which forms/menu items they need and get an optimal license recommendation, so I don't default to the most expensive license."

**Algorithms**: 4.7 (New User License Recommendation Engine)
**Phase**: Phase 1 (MVP scope — searchable form, top-3 recommendations, SoD check)

---

### **Capability 6: Entra ID License Sync Verification (Optional)** ⭐ NEW

**Description**: Detect mismatches between tenant-level Entra ID licensing and D365 FO role-based licensing. Requires optional Microsoft Graph API integration with admin consent.

**Key Features**:
- Ghost license detection (Entra license, no D365 FO roles)
- Compliance gap detection (D365 FO roles, wrong/missing Entra license)
- Over-provisioning detection (enterprise Entra license for Team Members usage)
- Stale entitlement detection (disabled D365 FO users with active Entra licenses)

**User Story**:
> "As an IT Director, I want to see where our Entra ID licenses are out of sync with D365 FO role assignments, so I can eliminate wasted spend and close compliance gaps."

**Algorithms**: 3.9 (Entra-D365 License Sync Validator)
**Phase**: Phase 2 (requires Microsoft Graph API as new data source)
**Prerequisite**: Customer grants Graph API admin consent (optional — agent works fully without it)

---

## MVP Features (Phase 1)

### **Priority: High** 🔴

#### **Feature 1.1: License Requirement Calculator** ⭐⭐⭐

**Description**: Calculate the theoretical license requirement for each user based on their assigned roles

**Functional Requirements**:
- FR-1.1.1: System shall fetch all roles assigned to each user
- FR-1.1.2: System shall identify the highest license type required across all roles
- FR-1.1.3: System shall compare theoretical requirement vs. current assignment
- FR-1.1.4: System shall display required license for each user

**Acceptance Criteria**:
- System correctly calculates license for 100% of users
- Performance: Calculation completes in < 30 seconds for 10K users
- Data accuracy: Matches D365 FO User License Estimator report

**User Story**:
```
As a System Administrator,
I want to see each user's calculated license requirement based on their roles,
So that I can identify who is over-licensed.
```

---

#### **Feature 1.2: Read-Only User Detection** ⭐⭐⭐

**Description**: Identify users who primarily perform read-only operations (downgrade candidates)

**Functional Requirements**:
- FR-1.2.1: System shall analyze user activity over configurable time period (default: 90 days)
- FR-1.2.2: System shall calculate Read vs. Write operation percentage
- FR-1.2.3: System shall identify users with Read percentage > 95%
- FR-1.2.4: System shall recommend Team Members license for read-only users
- FR-1.2.5: System shall estimate cost savings per user

**Acceptance Criteria**:
- Identifies 100% of read-only users (false positives < 5%)
- Configurable threshold (default 95%, adjustable 80-99%)
- Performance: Analysis completes in < 2 minutes

**User Story**:
```
As a System Administrator,
I want to see which users only read data (not write),
So that I can downgrade them to Team Members licenses and save money.
```

---

#### **Feature 1.3: Inactive User Detection** ⭐⭐⭐

**Description**: Automatically identify users with no recent activity

**Functional Requirements**:
- FR-1.3.1: System shall detect users with no activity in configurable period (default: 90 days)
- FR-1.3.2: System shall list current license assigned to inactive users
- FR-1.3.3: System shall calculate potential cost savings from license removal
- FR-1.3.4: System shall support configurable inactivity thresholds (10, 30, 60, 90, 120 days)

**Acceptance Criteria**:
- Identifies all inactive users accurately
- Configurable time ranges (5 options)
- Weekly automated report generation

**User Story**:
```
As a System Administrator,
I want to automatically identify users who haven't logged in for 90+ days,
So that I can remove their licenses and reduce costs.
```

---

#### **Feature 1.4: Compliance Gap Detection** ⭐⭐

**Description**: Identify security objects where access exists but license doesn't cover (Entitled = 0)

**Functional Requirements**:
- FR-1.4.1: System shall identify "Not Entitled" security objects (Entitled = 0)
- FR-1.4.2: System shall group by role and license type
- FR-1.4.3: System shall prioritize by number of users affected
- FR-1.4.4: System shall recommend remediation actions

**Acceptance Criteria**:
- Detects 100% of Not Entitled access
- Prioritizes by business impact (user count, sensitivity)
- Daily automated scanning

**User Story**:
```
As a Security Officer,
I want to see where users have access that their licenses don't cover,
So that I can remediate compliance gaps before audits.
```

---

#### **Feature 1.5: License Cost Dashboard** ⭐⭐

**Description**: Provide real-time visibility into license costs and optimization opportunities

**Functional Requirements**:
- FR-1.5.1: System shall display current license costs by license type
- FR-1.5.2: System shall show total users per license type
- FR-1.5.3: System shall display optimization opportunities (potential savings)
- FR-1.5.4: System shall track month-over-month cost trends
- FR-1.5.5: Dashboard shall update daily (or on-demand)

**Acceptance Criteria**:
- Dashboard loads in < 5 seconds
- Data is < 24 hours old
- Shows at least 5 key metrics

**User Story**:
```
As a CFO,
I want a dashboard showing current license costs and savings opportunities,
So that I can track budget adherence and ROI of optimization efforts.
```

---

### **MVP Priority Summary**

| Feature | Priority | Complexity | Value |
|---------|----------|------------|-------|
| 1.1 License Requirement Calculator | 🔴 High | Medium | High |
| 1.2 Read-Only User Detection | 🔴 High | Low | High |
| 1.3 Inactive User Detection | 🔴 High | Low | High |
| 1.4 Compliance Gap Detection | 🟡 Medium | Medium | Medium |
| 1.5 License Cost Dashboard | 🔴 High | Low | High |

**Estimated MVP Development Time**: 4-6 weeks

---

## Future Features (Phase 2+)

### **Phase 2: Advanced Optimization** (3-4 months)

#### **Feature 2.1: Device License Optimization**
- Identify shared device scenarios (warehouse, POS)
- Recommend device vs. user licenses
- Calculate cost savings opportunities

#### **Feature 2.2: Role Consolidation Analysis**
- Detect similar roles (>80% overlap)
- Recommend role merges
- Estimate management overhead reduction

#### **Feature 2.3: License Forecasting**
- Predict future license needs based on:
  - Headcount changes (HR feed)
  - Seasonal patterns (historical analysis)
  - Project-based demand (project management)
- ML-based demand prediction

#### **Feature 2.4: Cross-Application License Optimization**
- Analyze users with roles across Finance + SCM
- Recommend combined Finance + SCM license
- Estimate savings vs. separate licenses

---

### **Phase 3: Automation & Workflow** (6-9 months)

#### **Feature 3.1: Automated Recommendations**
- Auto-generate recommendations
- Route to managers for approval
- Track recommendation status

#### **Feature 3.2: Change Request Automation**
- Create tickets in ITSM (ServiceNow, JIRA)
- Generate scripts for manual execution
- Track implementation status

#### **Feature 3.3: Scheduled Reporting**
- Weekly/monthly automated reports
- Email reports to stakeholders
- Compliance report generation

---

### **Phase 4: AI/ML Advanced Analytics** (9-12 months)

#### **Feature 4.1: Predictive Analytics**
- License demand forecasting (ML models)
- Anomaly detection (unsupervised learning)
- Usage pattern recognition

#### **Feature 4.2: Natural Language Queries**
- Ask questions: "How many users need Finance licenses?"
- Auto-generate insights and recommendations

---

## Non-Functional Requirements

### **Performance**

| Requirement | Metric | Target |
|-------------|--------|--------|
| **Query Response** | Dashboard load time | < 5 seconds |
| **Analysis Speed** | License calculation (10K users) | < 30 seconds |
| **Data Freshness** | Security config data | < 1 hour old |
| **Data Freshness** | User activity data | < 15 minutes old |
| **Concurrent Users** | Simultaneous dashboard users | 50+ |

### **Scalability**

| Requirement | Metric | Target |
|-------------|--------|--------|
| **User Count** | Support organization size | Up to 50,000 users |
| **Event Volume** | User activity events per day | Up to 10M events/day |
| **Data Retention** | Historical data retention | 7+ years (compliance) |
| **Growth** | Annual data growth | Handle 50% year-over-year growth |

### **Reliability**

| Requirement | Metric | Target |
|-------------|--------|--------|
| **Availability** | Uptime | 99.5% (excluding maintenance) |
| **Data Accuracy** | Calculation accuracy | > 99% |
| **Recovery Time** | RTO (Recovery Time Objective) | < 4 hours |
| **Recovery Point** | RPO (Recovery Point Objective) | < 1 hour |

### **Security**

| Requirement | Description |
|-------------|-----------|
| **Authentication** | Azure AD integration, MFA support |
| **Authorization** | RBAC (role-based access control) |
| **Data Encryption** | TLS in transit, TDE at rest |
| **Audit Logging** | Log all data access and changes |
| **Privacy** | PII data protection, GDPR compliance |

---

## Success Metrics

### **Business Metrics**

| Metric | Current (Baseline) | Target (6 months) | Target (12 months) |
|--------|-------------------|-------------------|--------------------|
| **License Cost Reduction** | $0 (baseline) | 15% reduction | 25% reduction |
| **Time Savings** | Manual analysis (hours) | 80% reduction | 90% reduction |
| **Compliance Issues** | Unknown | 100% detected | 100% remediated |
| **User Satisfaction** | N/A | > 4/5 rating | > 4.5/5 rating |

### **Technical Metrics**

| Metric | Target |
|--------|--------|
| **Dashboard Adoption** | 80% of target users access weekly |
| **Recommendation Acceptance** | > 70% of recommendations implemented |
| **False Positive Rate** | < 5% for downgrade recommendations |
| **Data Freshness SLA** | 95% of queries use data < 24 hours old |

---

## Example User Workflows

### **Workflow 1: Identify Over-Licensed Users**

```
1. Administrator opens License Optimization Dashboard
2. System filters: "Show over-licensed users"
3. System displays:
   - User: john.doe@contoso.com
   - Current License: Commerce ($180/month)
   - Required License: Team Members ($60/month)
   - Actual Usage: 99.76% read-only (847 read, 2 write)
   - Recommendation: Downgrade to Team Members
   - Estimated Savings: $120/month
4. Administrator reviews details
5. Administrator clicks "Recommend Change"
6. System generates change request
7. Manager receives approval request
8. Manager approves/rejects
9. If approved: System schedules license change
```

---

### **Workflow 2: Detect Compliance Gaps**

```
1. Security Officer opens Compliance Dashboard
2. System filters: "Show Not Entitled access"
3. System displays:
   - Role: Accountant
   - Menu Items with Not Entitled access: 15
   - Users Affected: 8
   - Risk Level: High
4. Security Officer clicks "Investigate"
5. System shows detailed breakdown:
   - Which menu items
   - Which users
   - Why not entitled (license missing)
6. Security Officer exports report for audit
7. System tracks remediation status
```

---

### **Workflow 3: Monthly Executive Report**

```
1. System automatically runs analysis on 1st of month
2. System generates:
   - Total license cost: $450,000
   - Optimization implemented: $50,000 savings (11% reduction)
   - Opportunities remaining: $30,000 potential savings
   - Compliance status: 0 critical issues
   - Top 3 recommendations
3. System emails report to CFO, CIO, Security Officer
4. Stakeholders review at monthly meeting
```

---

## Requirements Prioritization Matrix

| Feature | Business Value | Technical Complexity | User Impact | Priority Phase |
|---------|----------------|-------------------|-------------|----------------|
| 1.1 License Calculator | High | Medium | High | MVP (Phase 1) |
| 1.2 Read-Only Detection | High | Low | High | MVP (Phase 1) |
| 1.3 Inactive Users | High | Low | Medium | MVP (Phase 1) |
| 1.4 Compliance Gaps | Medium | Medium | High | MVP (Phase 1) |
| 1.5 Cost Dashboard | High | Low | High | MVP (Phase 1) |
| 2.1 Device Optimization | Medium | Medium | Medium | Phase 2 |
| 2.2 Role Consolidation | Medium | High | Medium | Phase 2 |
| 2.3 License Forecasting | High | High | Medium | Phase 2 |
| 3.1 Auto-Recommendations | High | High | High | Phase 3 |
| 4.1 ML Analytics | High | High | High | Phase 4 |

---

## Functional Requirements Checklist

### **Phase 1 (MVP) - Must Have**

- [x] Document data sources and capabilities
- [ ] FR-1.1: License requirement calculator
- [ ] FR-1.2: Read-only user detection
- [ ] FR-1.3: Inactive user detection
- [ ] FR-1.4: Compliance gap detection
- [ ] FR-1.5: License cost dashboard
- [ ] User authentication (Azure AD)
- [ ] Basic RBAC (3 roles: Admin, Analyst, Viewer)
- [ ] Data refresh mechanism (TBD technical approach)
- [ ] Export to CSV/PDF functionality
- [ ] Weekly automated reports

### **Phase 2 - Should Have**

- [ ] Device license optimization
- [ ] Role consolidation analysis
- [ ] License forecasting (rule-based initially)
- [ ] Advanced filtering and search
- [ ] Trend analysis charts
- [ ] Department-level rollups
- [ ] Multi-language support

### **Phase 3+ - Nice to Have**

- [ ] ML-based forecasting
- [ ] Natural language query interface
- [ ] Automated remediation workflows
- [ ] ITSM integration (ServiceNow, JIRA)
- [ ] Advanced anomaly detection
- [ ] Predictive analytics
- [ ] Mobile app

---

## Open Questions

### **To Be Addressed in Design Phase**

| Question | Impact | Priority |
|----------|--------|----------|
| What is target organization size? | Scalability requirements | High |
| What are cost savings targets? | Success metrics | High |
| Who approves license changes? | Workflow design | High |
| What compliance standards apply? | Reporting requirements | Medium |
| What is the budget for this project? | Resource allocation | High |
| Who are the executive sponsors? | Stakeholder alignment | High |

---

## Next Steps

### **Immediate Actions** (This Week)

1. **Review Requirements** with stakeholders
   - Validate assumptions
   - Gather feedback
   - Prioritize features

2. **Create User Stories** for MVP features
   - Detailed acceptance criteria
   - Wireframes/mockups for dashboards

3. **Define Success Metrics** with stakeholders
   - Cost saving targets
   - Time savings expectations
   - Compliance requirements

4. **Technical Feasibility Assessment**
   - Validate data availability (4 sources confirmed ✅)
   - Identify technical constraints
   - Rough cost estimation

### **Future Phases**

- **Phase 2**: Technical design (data access methods, Azure services)
- **Phase 3**: Implementation (MVP features)
- **Phase 4**: Testing and validation
- **Phase 5**: Production deployment

---

## Document Status

**Status**: Requirements Definition - Draft v1.0
**Next Review**: After stakeholder feedback
**Dependencies**: None (business requirements independent of technical implementation)

---

**End of Functional Requirements Document**
