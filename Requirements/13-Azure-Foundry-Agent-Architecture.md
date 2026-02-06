# Azure AI Agent Architecture

**Project**: D365 FO License & Security Optimization Agent
**Component**: Azure AI Agent
**Last Updated**: February 6, 2026
**Status**: Requirements Definition
**Version**: 1.0

---

## 📋 Table of Contents

1. [Agent Overview](#agent-overview)
2. [Architecture Components](#architecture-components)
3. [Functional Requirements](#functional-requirements)
4. [Data Processing Pipeline](#data-processing-pipeline)
5. [Algorithm Execution Engine](#algorithm-execution-engine)
6. [Scheduling & Automation](#scheduling--automation)
7. [Integration with Web App](#integration-with-web-app)
8. [Non-Functional Requirements](#non-functional-requirements)
9. [Security & Compliance](#security--compliance)
10. [Monitoring & Observability](#monitoring--observability)

---

## Agent Overview

### **Purpose**

> **Platform Naming Clarification**: The agent is built on Azure AI services, leveraging **Azure AI Foundry** (formerly Azure AI Studio) for AI/ML capabilities, and **Azure AI Agent Service** for agent orchestration. Throughout this document, "Azure AI Agent" refers to this combination of services. References to "Azure Foundry Agent" in other documents refer to this same component.

The Azure AI Agent is the **AI-powered processing engine** that:
- **Ingests** data from 4 core D365 FO sources + 1 optional (Entra ID via Microsoft Graph API)
- **Executes** 34 optimization algorithms (11 in Phase 1)
- **Generates** recommendations and insights
- **Schedules** automated analysis runs
- **Integrates** with web app for visualization
- **Maintains** audit trail for compliance

### **Key Capabilities**

| Capability | Description | Value |
|------------|-------------|--------|
| **Real-Time Processing** | Analyze data continuously or on-demand | Up-to-date insights |
| **Batch Processing** | Scheduled full-organization analysis | Comprehensive reporting |
| **Algorithm Orchestration** | Execute 34 algorithms in optimal sequence | Maximum optimization |
| **Recommendation Engine** | Generate prioritized, actionable recommendations | High-confidence insights |
| **Data Integration** | Connect to D365 FO, Azure App Insights | Seamless data flow |
| **Audit Logging** | Maintain complete audit trail | SOX/GDPR compliance |

---

## Architecture Components

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    D365 FO Environment                       │
│  • Security Configuration (OData/API)                        │
│  • User-Role Assignments (OData/API)                         │
│  • Audit Logs (OData/API)                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure Application Insights                       │
│  • User Activity Telemetry (Continuous Export / Stream)     │
│  • Custom Events (Read/Write/Delete tracking)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│     Microsoft Graph API (Optional — Phase 2)                 │
│  • Entra ID License Data (per-user SKUs)                     │
│  • Tenant License Inventory                                  │
│  • Requires admin consent: User.Read.All, Directory.Read.All │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure AI Agent                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. Data Ingestion Layer                                 │  │
│  │    • OData Connectors (D365 FO)                        │  │
│  │    • Event Hubs (App Insights streaming)                │  │
│  │    • Data Storage (Data Lake / SQL)                    │  │
│  │    • Data Normalization & Validation                   │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 2. Algorithm Execution Engine                           │  │
│  │    • Algorithm Orchestrator                             │  │
│  │    • 34 Algorithm Implementations                      │  │
│  │    • Parallel Processing                                 │  │
│  │    • Result Aggregation                                │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 3. Recommendation Engine                                │  │
│  │    • Confidence Scoring                                 │  │
│  │    • Priority Ranking                                   │  │
│  │    • Multi-Option Generation                            │  │
│  │    • Business Impact Calculation                        │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 4. Scheduling & Automation                             │  │
│  │    • Scheduled Batch Jobs                               │  │
│  │    • Event-Triggered Analysis                          │  │
│  │    • On-Demand Analysis                                 │  │
│  │    • Continuous Monitoring                               │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 5. API & Integration Layer                              │  │
│  │    • REST APIs (for Web App)                             │  │
│  │    • Webhook Support                                   │  │
│  │    • Real-Time Streaming                               │  │
│  │    • Batch Export                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 6. Audit & Compliance Layer                             │  │
│  │    • Audit Logging                                     │  │
│  │    • Change History                                    │  │
│  │    • Compliance Reports                                 │  │
│  │    • Data Lineage                                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Web Application                            │
│  • Dashboards                                              │
│  • Reports                                                │
│  • User Interface                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Functional Requirements

### **FR-Agent-1: Data Ingestion**

**The agent shall**:

- **FR-Agent-1.1**: Ingest Security Configuration data from D365 FO via OData
  - Update frequency: Real-time when changes occur
  - Data freshness: < 1 hour (full delta sync). Initial full load may take 2-4 hours for 700K+ records.
  - Volume: ~700K records

- **FR-Agent-1.2**: Ingest User-Role Assignment data from D365 FO via OData
  - Update frequency: Real-time when changes occur
  - Data freshness: < 1 hour old
  - Volume: 200-200K records

- **FR-Agent-1.3**: Ingest User Activity Telemetry from Azure App Insights
  - Update frequency: Continuous streaming
  - Data freshness: < 15 minutes old
  - Volume: 10K-10M events/day

- **FR-Agent-1.4**: Ingest Audit Logs from D365 FO and Azure App Insights
  - Update frequency: Real-time streaming
  - Data freshness: < 15 minutes old
  - Volume: Variable

- **FR-Agent-1.5**: Validate and normalize all ingested data
  - Schema validation
  - Data type checking
  - Reference data integrity
  - Error logging and alerting

- **FR-Agent-1.6** ⭐ NEW: Ingest Entra ID license data from Microsoft Graph API (OPTIONAL)
  - Update frequency: Daily (batch sync)
  - Data freshness: < 24 hours
  - Endpoints: `/v1.0/subscribedSkus`, `/v1.0/users/{id}/licenseDetails`
  - Permissions: `User.Read.All`, `Directory.Read.All` (admin consent required)
  - SKU-to-License mapping: Configurable per customer tenant
  - Graceful degradation: Agent operates fully if Graph API not configured
  - Supports both direct and group-based license assignments in Entra

**Acceptance Criteria**:
- All 4 core data sources successfully ingested (5th optional)
- Data freshness SLAs met (above targets)
- Validation errors < 0.1% of records
- Failed ingestions trigger alerts

### OData Throttling Mitigation Strategy

D365 FO OData endpoints enforce priority-based throttling. With 700K+ security configuration records, the following strategies mitigate throttling risks:

1. **Delta Sync (Primary)**: After initial full load, use D365 FO Change Tracking (delta links) to retrieve only changed records. Reduces volume by 95%+ on subsequent syncs.

2. **Off-Peak Scheduling**: Schedule full refreshes during D365 FO non-business hours (configurable per customer timezone). Batch operations receive lower throttling priority during peak hours.

3. **Batched Extraction**: Use OData `$batch` requests to bundle multiple queries. Pagination via `$top`/`$skip` with 5,000 records per page.

4. **Retry with Exponential Backoff**: Handle `429 Too Many Requests` responses with exponential backoff (1s, 2s, 4s, 8s, max 60s). Track retry metrics for capacity planning.

5. **Data Lake Export (Alternative)**: For customers with D365 FO Data Lake Export enabled, bypass OData entirely by reading from Azure Data Lake Storage Gen2. Eliminates throttling concerns completely.

6. **Performance Impact Assessment**: OData extraction should not exceed 10% of D365 FO's available API capacity. Monitor via D365 FO Priority-based throttling diagnostics page (`/api/throttling/diagnostics`).

| Strategy | When to Use | Throttling Risk | Data Freshness |
|----------|-------------|-----------------|----------------|
| Delta Sync | Default for incremental updates | Very Low | < 1 hour |
| Off-Peak Full Load | Weekly full refresh | Low | 4-6 hours (scheduled) |
| Batched Extraction | Initial load, large datasets | Medium | 2-4 hours |
| Data Lake Export | Available environments | None | Depends on export config |
| Retry + Backoff | All OData calls (automatic) | N/A (mitigation) | Adds latency on 429s |

---

### **FR-Agent-2: Algorithm Execution**

**The agent shall**:

- **FR-Agent-2.1**: Execute Phase 1 algorithms (11 algorithms)
  - Execute algorithms in optimal sequence
  - Support parallel processing where possible
  - Generate results per algorithm

- **FR-Agent-2.2**: Orchestrate algorithm dependencies
  - Algorithm 2.1 (Role Composition) → Algorithm 2.2 (User Segmentation)
  - Algorithm 2.3 (Role Splitting) → Algorithm 2.5 (License Minority)
  - Algorithm 2.6 (Cross-Role) → Algorithm 2.4 (Multi-Role)

- **FR-Agent-2.3**: Support on-demand algorithm execution
  - Trigger: User request via Web App
  - Execute: Selected algorithm(s)
  - Response Time: < 30 seconds for single user analysis

- **FR-Agent-2.4**: Support scheduled batch execution
  - Schedule: Daily/weekly/monthly full analysis
  - Time Window: Non-business hours (configurable)
  - Notification: Results ready when complete

- **FR-Agent-2.5**: Maintain algorithm state between executions
  - Cache: Role compositions, user segments
  - History: Previous results for trend analysis
  - Configuration: Algorithm parameters

**Acceptance Criteria**:
- All 11 Phase 1 algorithms executable
- Dependencies correctly resolved
- On-demand execution < 30 seconds
- Scheduled execution completes within 2 hours (10K users)

---

### **FR-Agent-3: Recommendation Engine**

**The agent shall**:

- **FR-Agent-3.1**: Generate confidence scores for all recommendations
  - HIGH (> 80): Safe to implement
  - MEDIUM (60-80): Validate with user
  - LOW (< 60): Manual review required

- **FR-Agent-3.2**: Provide multiple optimization options per scenario
  - Option 1: Remove access
  - Option 2: Convert to read-only
  - Option 3: Keep current
  - Each option with impact and savings

- **FR-Agent-3.3**: Calculate business impact for recommendations
  - Cost savings (monthly/annual)
  - Risk assessment
  - Implementation effort
  - User impact

- **FR-Agent-3.4**: Prioritize recommendations by business value
  - Primary: Savings potential
  - Secondary: Complexity
  - Tertiary: Risk reduction

- **FR-Agent-3.5**: Generate implementation guidance
  - Step-by-step instructions
  - Required approvals
  - Rollback procedures
  - Validation checkpoints

**Acceptance Criteria**:
- All recommendations include confidence score
- All recommendations include multiple options
- Business impact calculations accurate (±5%)
- Implementation guidance clear and actionable

---

### **FR-Agent-4: Scheduling & Automation**

**The agent shall**:

- **FR-Agent-4.1**: Support scheduled batch analysis
  - Daily: Incremental updates (last 24 hours)
  - Weekly: Full organization scan
  - Monthly: Compliance reports
  - Configurable schedules

- **FR-Agent-4.2**: Support event-triggered analysis
  - Event: Security configuration change
  - Event: Role assignment change
  - Event: Anomalous activity detected
  - Response: Run relevant algorithms within 15 minutes

- **FR-Agent-4.3**: Support continuous monitoring
  - Monitor: User activity patterns
  - Alert: Anomalies detected (SoD violations, role changes)
  - Response: Real-time notifications

- **FR-Agent-4.4**: Maintain execution history
  - Log: All algorithm executions
  - Track: Execution time, resource usage
  - Audit: Who ran what, when, why

**Acceptance Criteria**:
- Scheduled jobs execute on time
- Event-triggered analysis < 15 minutes
- Continuous monitoring with < 5% false positives
- Complete audit trail maintained

---

### **FR-Agent-5: API & Integration**

**The agent shall**:

- **FR-Agent-5.1**: Provide REST APIs for Web App integration
  - GET /api/recommendations - Get all recommendations
  - GET /api/recommendations/{userId} - Get user-specific recommendations
  - GET /api/algorithms - Get available algorithms
  - POST /api/analyze - Trigger on-demand analysis
  - GET /api/reports/{reportType} - Get specific report
  - POST /api/v1/suggest-license ⭐ NEW - New user license recommendation (Algorithm 4.7)

- **FR-Agent-5.2**: Support real-time data streaming
  - WebSocket: Live analysis progress
  - SSE: Server-Sent Events for updates
  - Push notifications: Alerts and anomalies

- **FR-Agent-5.3**: Support batch export
  - Format: JSON, CSV, PDF
  - Content: Recommendations, reports, audit logs
  - Schedule: On-demand or scheduled

- **FR-Agent-5.4**: Maintain API versioning
  - Versioning: URL-based (/api/v1/, /api/v2/)
  - Deprecation policy: 6-month notice
  - Backward compatibility: Maintain for 2 versions

**Acceptance Criteria**:
- All APIs documented with OpenAPI/Swagger
- API response time < 2 seconds (95th percentile)
- Real-time streaming latency < 1 second
- Batch export completes within 5 minutes

---

### **FR-Agent-6: Audit & Compliance**

**The agent shall**:

- **FR-Agent-6.1**: Maintain immutable audit trail
  - Log: All algorithm executions
  - Log: All recommendations generated
  - Log: All user approvals/rejections
  - Retention: 7+ years (compliance)

- **FR-Agent-6.2**: Track data lineage
  - Source: Data origin (D365 FO, App Insights)
  - Transformation: Processing steps applied
  - Destination: Where data stored
  - Timestamp: When processed

- **FR-Agent-6.3**: Generate compliance reports
  - SOX Section 404: Access control evidence
  - GDPR: Data access documentation
  - ISO 27001: Security monitoring evidence
  - Custom: Organization-specific requirements

- **FR-Agent-6.4**: Support audit queries
  - Query: "What recommendations were implemented?"
  - Query: "Who approved this change?"
  - Query: "Show license changes for Q1 2026"

**Acceptance Criteria**:
- Audit trail 100% complete and immutable
- Data lineage documented for all data
- Compliance reports auto-generated weekly
- Audit queries respond < 5 seconds

---

## Data Processing Pipeline

### **Pipeline Stages**

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Ingestion                                         │
│ • Connect to D365 FO (OData)                                │
│ • Stream from App Insights (Event Hub)                      │
│ • Validate and normalize data                                 │
│ • Store in Data Lake / SQL                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Processing                                         │
│ • Enrich data (add license types, calculate permissions)      │
│ • Aggregate metrics (user-level, role-level, org-level)      │
│ • Detect anomalies (statistical analysis)                    │
│ • Update caches and materialized views                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Algorithm Execution                                │
│ • Execute algorithms in optimal sequence                    │
│ • Parallel processing where possible                         │
│ • Aggregate results                                        │
│ • Generate recommendations                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: Storage                                            │
│ • Recommendations: Optimized for query                       │
│ • Audit Logs: Immutable store                                │
│ • Materialized Views: Fast access                            │
│ • Time-Series Data: Trend analysis                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: Exposure (API)                                      │
│ • REST APIs for Web App                                     │
│ • Real-time streaming                                       │
│ • Batch export                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Algorithm Execution Engine

### **Execution Modes**

**1. On-Demand Mode**
- **Trigger**: User request via Web App
- **Scope**: Single user, single role, or custom scope
- **Response Time**: < 30 seconds
- **Use Case**: Administrator investigating specific user

**2. Scheduled Batch Mode**
- **Trigger**: Schedule (daily/weekly/monthly)
- **Scope**: Full organization
- **Execution Time**: < 2 hours (10K users)
- **Use Case**: Comprehensive overnight analysis

**3. Event-Triggered Mode**
- **Trigger**: Configuration change, anomaly detected
- **Scope**: Affected users/roles
- **Response Time**: < 15 minutes
- **Use Case**: Real-time security monitoring

**4. Continuous Monitoring Mode**
- **Trigger**: Always running
- **Scope**: All activity events
- **Response**: Real-time alerts
- **Use Case**: Anomaly detection

### **Algorithm Sequencing**

**Optimal Execution Order** (Phase 1):

```
1. Data Ingestion (4 core sources + optional Entra ID)
   ↓
2. Data Processing & Enrichment
   ↓
3. Algorithm 1.1: Role License Composition (cache for reuse)
   ↓
4. Algorithm 3.5: Orphaned Account Detection
   ├── Output: List of orphaned accounts
   └── Action: Remove licenses
   ↓
5. Algorithm 1.4: Component Removal Recommender
   ├── Output: Menu items to remove
   └── Action: Update roles
   ↓
6. Algorithm 2.2: Read-Only User Detector
   ├── Output: Read-only users list
   └── Action: License downgrade recommendations
   ↓
7. Algorithm 2.5: License Minority Detection (NEW)
   ├── Output: Multi-license minority analysis
   └── Action: License optimization options
   ↓
8. Algorithm 2.6: Cross-Role License Optimization (NEW)
   ├── Output: Role combination analysis
   └── Action: Systemic optimization recommendations
   ↓
9. Algorithm 1.3: Role Splitting Recommender
   ├── Output: Roles to split
   └── Action: Create license-specific variants
   ↓
10. Algorithm 2.4: Multi-Role Optimization
    ├── Output: Unused roles
    └── Action: Remove unused roles
    ↓
11. Algorithm 5.3: Time-Based Access Analyzer
    ├── Output: After-hours access report
    └── Action: Security alerts
    ↓
12. Algorithm 3.1: SoD Violation Detector
    ├── Output: SoD conflicts
    └── Action: Compliance alerts
    ↓
13. Algorithm 4.4: License Trend Analysis
    ├── Output: 12-month forecast
    └── Action: Budget planning
    ↓
14. Algorithm 4.7: New User License Recommendation ⭐ NEW
    ├── Output: Menu-items-first license suggestions
    └── Action: Optimal role + license recommendations
    ↓
15. Result Aggregation & Prioritization
    ├── Combine all algorithm outputs
    ├── Deduplicate recommendations
    ├── Rank by business value
    └── Generate final recommendations
    ↓
16. Store in Database & Expose via API
```

---

## Scheduling & Automation

### **Scheduled Jobs**

| Job | Frequency | Time Window | Scope | Duration |
|-----|-----------|-------------|-------|----------|
| **Incremental Update** | Daily | 2-4 AM | Last 24h changes | 30 min |
| **Full Analysis** | Weekly | Sunday 2-6 AM | All users | 2 hours |
| **Compliance Report** | Monthly | 1st of month, 3 AM | All users | 1 hour |
| **Trend Analysis** | Monthly | 15th of month, 3 AM | Historical | 30 min |
| **Data Refresh** | Continuous | Real-time | All sources | Ongoing |

### **Event-Triggers**

| Event | Trigger | Algorithm(s) | Response Time |
|-------|---------|-------------|--------------|
| **Security Config Change** | D365 FO update | Re-run affected algorithms | 15 min |
| **Role Assignment Change** | User role added/removed | Re-run user analysis | 15 min |
| **Anomalous Activity** | Pattern detected | Alert + analysis | 5 min |
| **New User Activity** | App Insights event | Update user metrics | Real-time |

---

## Integration with Web App

### **API Contract**

**Base URL**: `https://api.agent.example.com/v1`

### **API Endpoints**

#### **Recommendations API**

```
GET /api/v1/recommendations
```
**Description**: Get all recommendations

**Query Parameters**:
- `type`: (optional) LICENSE, SECURITY, COMPLIANCE, ALL
- `priority`: (optional) HIGH, MEDIUM, LOW
- `status`: (optional) PENDING, APPROVED, REJECTED, IMPLEMENTED
- `limit`: (optional) Default 100
- `offset`: (optional) For pagination

**Response**:
```json
{
  "recommendations": [
    {
      "id": "REC-2025-001",
      "type": "LICENSE_DOWNGRADE",
      "algorithm": "2.2-Read-Only-User-Detector",
      "userId": "john.doe@contoso.com",
      "userName": "John Doe",
      "priority": "HIGH",
      "confidence": 95,
      "currentLicense": "Commerce",
      "recommendedLicense": "Team Members",
      "currentCost": 180,
      "recommendedCost": 60,
      "monthlySavings": 120,
      "annualSavings": 1440,
      "readPercentage": 99.76,
      "writeOperations": 2,
      "options": [
        {
          "optionId": "OPT-001",
          "type": "DOWNGRADE_LICENSE",
          "description": "Downgrade from Commerce to Team Members license",
          "impact": "User will have read-only access to most functions",
          "feasibility": "HIGH",
          "implementationEffort": "LOW"
        }
      ],
      "status": "PENDING",
      "createdAt": "2025-02-06T10:30:00Z",
      "expiresAt": "2025-03-06T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 500,
    "limit": 100,
    "offset": 0
  }
}
```

---

```
POST /api/v1/analyze
```
**Description**: Trigger on-demand analysis

**Request Body**:
```json
{
  "scope": "USER",
  "userId": "john.doe@contoso.com",
  "algorithms": ["2.2", "2.5", "2.4"],
  "includeDetails": true
}
```

**Response**:
```json
{
  "analysisId": "ANAL-2025-001",
  "status": "IN_PROGRESS",
  "estimatedCompletion": "2025-02-06T10:35:00Z",
  "resultsUrl": "/api/v1/analysis/ANAL-2025-001"
}
```

---

```
POST /api/v1/suggest-license
```
**Description**: Get license recommendation for a new user based on required menu items (Algorithm 4.7)

**Request Body**:
```json
{
  "requiredMenuItems": [
    "LedgerJournalTable",
    "CustTable",
    "VendInvoiceJour",
    "BankReconciliation"
  ],
  "includeSODCheck": true
}
```

**Response**:
```json
{
  "recommendations": [
    {
      "rank": 1,
      "roles": ["Accountant", "AP Clerk"],
      "roleCount": 2,
      "licenseRequired": "Team Members",
      "monthlyCost": 60,
      "menuItemCoverage": "100%",
      "sodConflicts": [],
      "confidence": "HIGH",
      "note": "Theoretical — will be validated after 30 days of usage"
    },
    {
      "rank": 2,
      "roles": ["Finance Manager"],
      "roleCount": 1,
      "licenseRequired": "Finance",
      "monthlyCost": 180,
      "menuItemCoverage": "100%",
      "sodConflicts": [],
      "confidence": "HIGH",
      "note": "Theoretical — will be validated after 30 days of usage"
    }
  ],
  "inputMenuItems": 4,
  "generatedAt": "2026-02-06T10:30:00Z"
}
```

---

```
GET /api/v1/reports/{reportType}
```
**Report Types**:
- `license-optimization`: License cost savings opportunities
- `security-compliance`: SoD violations, access review
- `user-activity`: User access patterns and trends
- `role-analysis`: Role usage and optimization
- `trend-analysis`: License trends and forecasts

**Response**: Report data (JSON/PDF/CSV)

---

### **WebSocket Events**

**Event: analysis.progress**
```json
{
  "eventType": "analysis.progress",
  "analysisId": "ANAL-2025-001",
  "timestamp": "2025-02-06T10:31:00Z",
  "data": {
    "algorithm": "2.2-Read-Only-User-Detector",
    "progress": 45,
    "status": "RUNNING",
    "usersProcessed": 4500,
    "totalUsers": 10000,
    "estimatedCompletion": "2025-02-06T10:35:00Z"
  }
}
```

**Event: recommendation.generated**
```json
{
  "eventType": "recommendation.generated",
  "timestamp": "2025-02-06T10:35:00Z",
  "data": {
    "recommendationId": "REC-2025-001",
    "userId": "john.doe@contoso.com",
    "type": "LICENSE_DOWNGRADE",
    "savings": 120
  }
}
```

**Event: alert.triggered**
```json
{
  "eventType": "alert.triggered",
  "timestamp": "2025-02-06T10:32:00Z",
  "data": {
    "alertId": "ALERT-2025-001",
    "severity": "HIGH",
    "type": "SOD_VIOLATION",
    "userId": "jane.smith@contoso.com",
    "description": "User has conflicting roles: AP Clerk + Vendor Master"
  }
}
```

---

## Non-Functional Requirements

### **Performance**

| Requirement | Target | Measurement |
|-------------|--------|------------|
| **API Response Time** | < 2 seconds (95th percentile) | API monitoring |
| **Algorithm Execution (Single User)** | < 30 seconds | Agent logs |
| **Algorithm Execution (Full Org)** | < 2 hours (10K users) | Agent logs |
| **Data Freshness** | < 15 minutes (user activity) | Time stamps |
| **Data Freshness** | < 1 hour (security config) | Time stamps |
| **Concurrent Users** | 50+ simultaneous API calls | Load testing |

---

### **Scalability**

| Requirement | Target | Notes |
|-------------|--------|-------|
| **User Count** | Support up to 50,000 users | Horizontal scaling |
| **Event Volume** | Process 10M events/day | Stream processing |
| **Data Retention** | 7+ years (compliance) | Partitioned storage |
| **Algorithm Complexity** | 34 algorithms | Modular architecture |
| **API Requests** | 1000+ requests/second | API Gateway autoscaling |

---

### **Reliability**

| Requirement | Target | Measurement |
|-------------|--------|------------|
| **Availability** | 99.5% uptime | Uptime monitoring |
| **Data Accuracy** | > 99% recommendation accuracy | Audit validation |
| **Error Rate** | < 0.1% failed API calls | Error tracking |
| **Recovery Time** | RTO < 1 hour | Disaster recovery testing |
| **Recovery Point** | RPO < 15 minutes | Backup frequency |

---

### **Security**

**Authentication & Authorization**:
- Azure AD integration
- OAuth 2.0 / OpenID Connect
- Role-Based Access Control (RBAC)
- Multi-Factor Authentication (MFA)

**Data Security**:
- TLS 1.3 in transit
- Encryption at rest (Azure managed keys)
- PII data protection
- GDPR compliance

**API Security**:
- Rate limiting (100 req/min per user)
- API keys management
- IP whitelist (configurable)
- Request signing

---

## Security & Compliance

### **Data Privacy**

**PII Data Handling**:
- Identify PII: User IDs, email addresses, names
- Encrypt PII: At rest and in transit
- Access Control: Role-based permissions
- Audit Log: Who accessed what PII, when
- Data Retention: Follow organizational policy
- Right to Erasure: GDPR compliance

**Data Residency**:
- Store data in geo-compliant region
- Cross-border transfer compliance
- Data classification (Public, Internal, Confidential)

---

### **Audit Trail**

**Immutable Logging**:
- All algorithm executions logged
- All recommendations generated logged
- All approvals/rejections logged
- All data accesses logged
- Logs stored in append-only storage

**Log Content**:
- Timestamp
- User ID (who)
- Action (what)
- Result (outcome)
- Rationale (why)
- IP address
- Session ID

**Retention**: 7+ years (compliance requirement)

---

### **Compliance Reports**

**SOX Section 404**:
- Access control documentation
- Role assignment history
- Access review evidence
- Change management audit trail

**GDPR**:
- Data access documentation
- Data processing records
- Consent management (if applicable)
- Data breach notification capability

**ISO 27001**:
- Security monitoring evidence
- Access review logs
- Incident response documentation
- Risk assessment results

---

## Monitoring & Observability

### **Metrics to Track**

**Agent Performance**:
- Algorithm execution time
- API response time
- Error rates
- Resource utilization (CPU, memory, storage)

**Business Metrics**:
- Recommendations generated
- Recommendations accepted
- Cost savings realized
- Users optimized

**Data Quality Metrics**:
- Data freshness
- Data completeness
- Data accuracy
- Validation error rates

**Alerts**:
- Algorithm execution failed
- Data ingestion failed
- API error rate spike
- Resource exhaustion

---

## Technical Stack (To Be Confirmed in Design Phase)

### **Azure Services (Candidate)**

**Compute**:
- Azure Functions (serverless)
- Azure Kubernetes Service (AKS) - if needed
- Azure Batch (for heavy processing)

**Data Storage**:
- Azure SQL Database
- Azure Data Lake Storage Gen2
- Azure Cosmos DB (recommendations store)

**Integration**:
- Azure Event Hubs (streaming)
- Azure API Management (API gateway)
- Azure Logic Apps (orchestration)

**Monitoring**:
- Azure Application Insights
- Azure Monitor
- Azure Log Analytics

**Security**:
- Azure Key Vault
- Azure Active Directory
- Azure Policy

---

## Deployment Architecture

### **Environment Strategy**

**Development**: Azure subscription (dev)
**Testing**: Azure subscription (test)
**Production**: Azure subscription (prod)

**Deployment Pipeline**:
- CI/CD pipeline (Azure DevOps)
- Infrastructure as Code (Terraform/Bicep)
- Automated testing
- Staged rollout (Blue-Green)

---

## Open Questions (To Be Addressed in Design Phase)

### **Technical Decisions**

| Question | Options | Priority |
|----------|---------|----------|
| **Compute Platform** | Azure Functions vs AKS vs Batch | High |
| **Database Type** | Azure SQL vs Cosmos DB vs PostgreSQL | High |
| **API Management** | APIM vs API Gateway vs Kong | Medium |
| **Streaming** | Event Hubs vs Kafka vs Service Bus | Medium |
| **Orchestration** | Logic Apps vs Durable Functions vs Custom | Medium |

### **Business Decisions**

| Question | Options | Priority |
|----------|---------|----------|
| **Data Retention** | 7 years vs. 10 years vs. Custom | High |
| **Scheduling** | Fixed times vs. Configurable vs. Auto-optimized | Medium |
| **Multi-Tenancy** | Single org vs. Multi-org | Low |
| **API Versioning Strategy** | URL-based vs. Header-based | Low |

---

## Document Status

**Status**: Requirements Definition - Agent Architecture
**Dependencies**:
- Requirements/05-Functional-Requirements.md (Features)
- Requirements/12-Final-Phase1-Selection.md (Algorithms)
- Requirements/14-Web-Application-Requirements.md (Web App)

**Next Steps**:
1. Validate technical stack selection
2. Design data architecture
3. Define API contracts in detail (OpenAPI/Swagger)
4. Design deployment architecture
5. Plan scaling strategy

---

**End of Azure AI Agent Architecture**
