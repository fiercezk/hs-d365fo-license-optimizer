# Requirements Documentation - Index

**Project**: D365 FO License & Security Optimization Agent
**Last Updated**: 2026-02-06
**Status**: Phase 1 Finalization Complete ✅

---

## ⚠️ Important Correction

**All data sources are DYNAMIC/LIVE** - Technical implementation details (OData, pipelines, sync strategies) will be defined in a later phase. This documentation focuses on **what data is available** and **capabilities it enables**, not **how we'll retrieve it**.

---

## 📑 Document Structure

| # | Document | Description | Status |
|---|----------|-------------|--------|
| **01** | [Data Sources Overview](./01-Data-Sources-Overview.md) | Data types and capabilities | ✅ Complete |
| **02** | [Security Configuration Data](./02-Security-Configuration-Data.md) | Security objects, roles, licenses | ✅ Complete |
| **03** | [User-Role Assignment Data](./03-User-Role-Assignment-Data.md) | User-to-role mappings | ✅ Complete |
| **04** | [User Activity Telemetry Data](./04-User-Activity-Telemetry-Data.md) | User actions, sessions, usage | ✅ Complete |
| **05** | [Functional Requirements](./05-Functional-Requirements.md) | Core capabilities, MVP features, success metrics | ✅ Complete |
| **06** | [Algorithms & Decision Logic](./06-Algorithms-Decision-Logic.md) | 8 core algorithms for role analysis & user optimization | ✅ Complete |
| **07** | [Advanced Algorithms Expansion](./07-Advanced-Algorithms-Expansion.md) | 24 advanced algorithms incl. 3.9, 4.7 (security, compliance, cost) | ✅ Complete |
| **08** | [Algorithm Review Summary](./08-Algorithm-Review-Summary.md) | Complete portfolio review, prioritization, ROI analysis (34 algorithms) | ✅ Complete |
| **09** | [License Minority Detection Algorithm](./09-License-Minority-Detection-Algorithm.md) | Algorithm 2.5: Multi-license user optimization (10-40% savings) | ✅ Complete |
| **10** | [Additional Algorithms Exploration](./10-Additional-Algorithms-Exploration.md) | Algorithm 2.6: Cross-Role License Optimization | ✅ Complete |
| **11** | [License Trend Analysis Algorithm](./11-License-Trend-Analysis-Algorithm.md) | Algorithm 4.4: Trend analysis & prediction | ✅ Complete |
| **12** | [Final Phase 1 Selection](./12-Final-Phase1-Selection.md) | **11 algorithms selected for Phase 1 implementation** | ✅ Complete |
| **13** | [Azure Foundry Agent Architecture](./13-Azure-Foundry-Agent-Architecture.md) | **AI-powered processing engine** - Complete agent specification | ✅ Complete |
| **14** | [Web Application Requirements](./14-Web-Application-Requirements.md) | **User interface & dashboard** - Complete UI/UX specification | ✅ Complete |
| **15** | [Default SoD Conflict Matrix](./15-Default-SoD-Conflict-Matrix.md) | **Industry-standard SoD rules** - 27+ conflict rules across 7 categories | ✅ Complete |
| **16** | [Rollback & Fast-Restore Procedures](./16-Rollback-Fast-Restore-Procedures.md) | **Rollback procedures** - SLA, escalation, observation mode, safeguards | ✅ Complete |
| **17** | [Agent Process Flow](./17-Agent-Process-Flow.md) | **End-to-end process flow** - 22 processes, triggers, RACI, safeguards | ✅ Complete |
| **18** | [Tech Stack Recommendation](./18-Tech-Stack-Recommendation.md) | **Tech stack advisory** - 9-layer architecture, 4-tier cost model ($70-145/mo Phase 1) | ✅ Complete |

---

## 🎯 Key Principles

### **1. All Data is Dynamic**

| Data Source | Nature | Access Method | Refresh | To Be Determined |
|-------------|--------|---------------|---------|-----------------|
| **Security Configuration** | Live | D365 FO | Real-time | ⏳ Technical approach |
| **User-Role Assignments** | Live | D365 FO | Real-time | ⏳ Technical approach |
| **User Activity** | Live | Azure App Insights | Real-time | ⏳ Technical approach |
| **Audit Logs** | Live | Azure App Insights / D365 FO | Real-time | ⏳ Technical approach |

**Important**: We are documenting **data content and capabilities**, not **technical implementation**.

---

### **2. Data Formats Are Tentative**

Current schemas are based on available samples and understanding. **Actual formats will be finalized in later phase** based on:
- Technical feasibility
- Performance requirements
- Azure service capabilities
- D365 FO constraints

### **3. Focus on Capabilities, Not Implementation**

This documentation answers:
- ✅ What data is available?
- ✅ What analysis can we do with it?
- ✅ What business value does it provide?

It does NOT answer:
- ❌ How exactly will we fetch the data? (later phase)
- ❌ What Azure services will we use? (later phase)
- ❌ What are the data schemas? (to be finalized)

---

## 📊 Data Sources Overview

### **Source 1: Security Configuration Data**

**What It Contains**:
- Complete mapping of security roles to security objects
- License entitlement status
- Security object types (menu items, entities, actions, outputs)

**Sample Data**: `FinalAnalysisData.csv` (704,661 records) - this is a sample/representation of the live data

**Capabilities**:
- Calculate theoretical license requirement per role
- Identify compliance gaps
- Role comparison and consolidation
- Detect high-license privilege concentration

**Access**: Live from D365 FO (technical approach TBD)

---

### **Source 2: User-Role Assignment Data**

**What It Contains**:
- Which users have which roles assigned
- User details (name, email, department, etc.)
- Role assignment history

**Sample Data**: Not provided yet (will be from D365 FO)

**Capabilities**:
- Map users to roles
- Calculate license requirement per user
- Track role assignment changes
- Identify users with excessive roles

**Access**: Live from D365 FO (technical approach TBD)

---

### **Source 3: User Activity Telemetry**

**What It Contains**:
- User → Menu Item → Action (Read/Write/Delete)
- Timestamps, session context
- Device/client information

**Sample Data**: `UserLogSample.png` (visual representation)

**Key Feature**: **Read vs. Write action tracking** ⭐ (Critical for licensing!)

**Capabilities**:
- Identify read-only users (downgrade candidates)
- Detect inactive users
- Feature adoption tracking
- Session/workflow analysis
- Real-time anomaly detection

**Access**: Live from Azure Application Insights (technical approach TBD)

---

### **Source 4: Audit Logs**

**What It Contains**:
- Who made what security changes
- When changes were made
- What changed (old value → new value)
- License impact of changes

**Sample Data**: Not provided yet

**Capabilities**:
- Detect unauthorized role changes
- Track security configuration evolution
- Maintain compliance audit trail
- Analyze change patterns

**Access**: Live from D365 FO and/or Azure App Insights (technical approach TBD)

---

### **Source 5: Microsoft Entra ID License Data (Optional)**

> **Status**: Optional data source — requires Microsoft Graph API access with admin consent. Algorithm 3.9 (Entra-D365 License Sync Validator) depends on this source. The agent operates fully without it; customers who grant access get additional mismatch detection.

**What It Contains**:
- Per-user assigned D365 license SKUs from Entra ID (tenant-level)
- Tenant-level license inventory (purchased vs. consumed quantities)
- License assignment type (direct vs. group-based)

**Graph API Endpoints**:

| Endpoint | Data | Purpose |
|----------|------|---------|
| `GET /v1.0/subscribedSkus` | Tenant D365 SKUs, purchased/consumed quantity | License inventory |
| `GET /v1.0/users/{id}/licenseDetails` | Per-user assigned licenses with SKU IDs | User-level license data |
| `GET /v1.0/users?$filter=assignedLicenses/any(...)` | Users filtered by D365 license SKUs | Bulk D365-licensed user query |

**Permissions Required**: `User.Read.All`, `Directory.Read.All` (application-level, admin consent)

**Capabilities**:
- Detect ghost licenses (Entra license but no D365 FO roles)
- Detect compliance gaps (D365 FO roles but wrong/missing Entra license)
- Detect over-provisioned Entra licenses (enterprise tier for Team Members usage)
- Detect stale Entra entitlements (disabled D365 FO users still licensed in Entra)

**Configuration Required**: SKU-to-License mapping table (Entra SKU GUIDs vary per tenant/EA agreement)

**Access**: Microsoft Graph API via OAuth 2.0 app registration (technical approach TBD)

---

## 💡 Combined Analysis Power

### **What All 5 Sources Enable Together** (4 core + 1 optional)

| Capability | Data Sources Required | Business Value |
|------------|----------------------|----------------|
| **Calculate theoretical license per user** | Security Config + User-Role Assignments | Baseline requirement |
| **Analyze actual usage patterns** | User Activity + User-Role Assignments | What users ACTUALLY do |
| **Read vs. Write distinction** | User Activity | ⭐ Critical for licensing! |
| **Inactive user detection** | User Activity | Cost optimization |
| **Compliance gap detection** | Security Config (Entitlement status) | Risk management |
| **License downgrade eligibility** | All 4 | High-confidence recommendations |
| **Role consolidation** | Security Config + User Activity | Optimization |
| **Forecasting** | User Activity + Audit Logs | Predictive analytics |
| **Anomaly detection** | Activity + Audit Logs | Security monitoring |
| **Entra-D365 license sync** | Entra License Data + User-Role + Security Config | Mismatch detection (optional) |

---

## 🔗 Data Relationship

```
┌─────────────────────────────────────────────────────────────┐
│                    D365 FO Environment                       │
│  • Security Configuration (Live)                             │
│  • User-Role Assignments (Live)                             │
│  • Audit Logs (Live)                                        │
└─────────────────────────────────────────────────────────────┘
                            +
┌─────────────────────────────────────────────────────────────┐
│              Azure Application Insights                       │
│  • User Activity Telemetry (Live)                           │
│  • Custom Events (Read/Write/Delete)                        │
└─────────────────────────────────────────────────────────────┘
                            +
┌─────────────────────────────────────────────────────────────┐
│          Microsoft Graph API (Optional — Phase 2)            │
│  • Entra ID License Data (per-user SKUs)                     │
│  • Tenant License Inventory (purchased/consumed)             │
└─────────────────────────────────────────────────────────────┘
                            =
┌─────────────────────────────────────────────────────────────┐
│                   Agent Data Processing                       │
│  • Ingest data from all sources (method TBD)                │
│  • Process and analyze (approach TBD)                       │
│  • Generate recommendations (algorithms TBD)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Sample Combined Analysis

### **Scenario: Identify Over-Licensed User**

**Data Required**:
1. **Security Configuration**: Accountant role requires Commerce license
2. **User-Role Assignments**: John Doe has Accountant role
3. **User Activity**: John Doe's actual usage (last 90 days)
   - 847 Read operations (99.76%)
   - 2 Write operations (0.24%)

**Analysis**:
```
John Doe:
├─ Assigned License: Commerce ($180/month)
├─ Theoretical Requirement: Commerce (from Accountant role)
└─ Actual Usage: 99.76% read-only

Conclusion:
→ 99.76% read operations = Could use Team Members license
→ Only 2 writes were self-service updates
→ Recommendation: Downgrade to Team Members
→ Estimated Savings: $120/month ($1,440/year)
```

---

## 📋 Current Status

### **Completed** ✅

- [x] Understanding of all 4 core data sources + 1 optional (Entra ID via Graph API)
- [x] Sample data reviewed (FinalAnalysisData.csv, UserLogSample.png)
- [x] Data content and capabilities documented
- [x] Business use cases identified
- [x] Sample analysis queries provided
- [x] Functional requirements defined (MVP features)
- [x] Advanced algorithms designed (role analysis, user optimization)
- [x] Decision trees documented
- [x] Example calculations created

### **Not In Scope** ⏰ (Later Phases)

- [ ] Technical implementation approach (how to fetch data)
- [ ] Azure service selection (which services to use)
- [ ] Data pipeline design (ingestion, processing)
- [ ] Data schema finalization (exact column names, types)
- [ ] Performance optimization strategies
- [ ] Security implementation details
- [ ] Cost estimation

---

## 🚀 Next Steps

### **Phase 1: Requirements Definition** (Current)
- Define functional requirements based on available data
- Identify MVP capabilities
- Prioritize features
- Create user stories

### **Phase 2: Data Access Strategy** (Future)
- Design technical approach for each data source
- Select Azure services
- Define integration patterns
- Finalize data schemas

### **Phase 3: Implementation** (Future)
- Build data pipelines
- Implement agent logic
- Test and validate
- Deploy to production

---

## 📞 Questions?

If you have questions about:
- **Data content**: What fields are available? What can we analyze?
- **Capabilities**: What analysis is possible? What business value?
- **Use cases**: How can we solve specific problems?

→ Those are in scope for this phase

If you have questions about:
- **Technical implementation**: How to connect? What services to use?
- **Data formats**: Exact schemas? Field names?
- **Performance**: How fast? How much storage?
- **Security**: Authentication? Encryption?

→ Those will be addressed in later phases

---

## 📝 Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-05 | Initial creation | Claude (AI Assistant) |
| 1.1 | 2025-02-05 | **CORRECTION**: All data is dynamic/live. Removed implementation details. | Claude (AI Assistant) |
| 1.2 | 2026-02-06 | **Critical Review Updates**: Added docs 15-16 (SoD Matrix, Rollback Procedures). Updated telemetry with X++ instrumentation. Added Team Members form eligibility to Algorithm 2.2. Added seasonal awareness, configurable pricing. Revised savings projections to 15-25%. Updated architecture with OData throttling. | Claude (AI Assistant) |
| 1.3 | 2026-02-06 | **Agent Process Flow**: Added doc 17 — comprehensive end-to-end process flow with 22 processes (incl. P-22 New User License Suggestion), 5 diagrams, RACI matrix, trigger matrix, safeguard map, and error handling flows. | Claude (AI Assistant) |
| 1.4 | 2026-02-06 | **New Capabilities**: Added Algorithm 3.9 (Entra-D365 Sync Validator) and 4.7 (New User License Recommendation). Added Microsoft Graph API as optional 5th data source. Portfolio updated to 34 algorithms, 11 Phase 1. | Claude (AI Assistant) |
| 1.5 | 2026-02-06 | **Tech Stack Recommendation**: Added doc 18 — complete tech stack advisory with 9-layer architecture, 4-tier cost model, SLA validation, and risk callouts. Phase 1 cost: ~$70-145/month. | Claude (AI Assistant) |

---

**Status**: Phase 1 Finalization Complete ✅
**Next Phase**: Technical Design / Data Access Strategy
**Note**: Technical implementation approach will be defined in later phase

**🎉 Requirements Complete**: See [README.md](./README.md) for executive summary and Phase 1 selection!

---

**End of Requirements Documentation Index**
