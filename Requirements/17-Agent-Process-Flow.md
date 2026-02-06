# Agent Process Flow - D365 FO License & Security Optimization Agent

**Project**: D365 FO License & Security Optimization Agent
**Component**: End-to-End Process Flow & Operational Map
**Last Updated**: February 6, 2026
**Status**: Requirements Definition
**Version**: 1.0
**Category**: Process Architecture

---

## Table of Contents

1. [Purpose & How to Read This Document](#1-purpose--how-to-read-this-document)
2. [Process Inventory](#2-process-inventory)
3. [Agent Lifecycle Overview](#3-agent-lifecycle-overview)
4. [Phase 1: Data Acquisition](#4-phase-1-data-acquisition)
5. [Phase 2: Analysis & Recommendation](#5-phase-2-analysis--recommendation)
6. [Phase 3: Validation & Approval](#6-phase-3-validation--approval)
7. [Phase 4: Implementation & Communication](#7-phase-4-implementation--communication)
8. [Phase 5: Monitoring & Continuous Improvement](#8-phase-5-monitoring--continuous-improvement)
9. [Web Application Processes (Cross-Cutting)](#9-web-application-processes-cross-cutting)
10. [Trigger Matrix](#10-trigger-matrix)
11. [Safeguard & Control Point Map](#11-safeguard--control-point-map)
12. [Actor-Process RACI Matrix](#12-actor-process-raci-matrix)
13. [Process Dependencies & Data Flow](#13-process-dependencies--data-flow)
14. [Error Handling & Recovery Flows](#14-error-handling--recovery-flows)
15. [Appendix](#15-appendix)

---

## 1. Purpose & How to Read This Document

### 1.1 Purpose

This document provides the **comprehensive end-to-end process flow** for the D365 FO License & Security Optimization Agent. While the 16 prior requirements documents define individual components — data sources, algorithms, architecture, web application, SoD matrix, and rollback procedures — this document shows **how all components work together as a unified operational system**.

Think of this document as the **map**. The prior 16 documents are the **detailed terrain guides** for each region. This document connects them into a single navigable landscape.

### 1.2 Audience Guide

| Audience | What to Read | Why |
|----------|-------------|-----|
| **Executive / Sponsor** | Sections 1, 3 (lifecycle diagram), 11 (safeguards) | Understand end-to-end flow and safety net |
| **Compliance / Audit** | Sections 6 (validation), 8 (monitoring), 11 (safeguards), 12 (RACI) | Understand controls, gates, and accountability |
| **Developer / Engineer** | Sections 4-8 (phase details), 10 (triggers), 13 (dependencies), 14 (error handling) | Understand technical flow and integration points |
| **System Administrator** | Sections 4 (data), 7 (implementation), 8 (monitoring), 9 (web app), 10 (triggers) | Understand operational procedures and configuration |
| **Support / Help Desk** | Sections 7 (communication), 8 (rollback & escalation), 9 (web app) | Understand user-facing flows and escalation |

### 1.3 Cross-Reference to Prior Documents

| Document | Content | Referenced In Sections |
|----------|---------|----------------------|
| [01 - Data Sources Overview](./01-Data-Sources-Overview.md) | 4 data sources and capabilities | 2, 4, 13 |
| [02 - Security Configuration Data](./02-Security-Configuration-Data.md) | Security objects, roles, licenses | 4, 5 |
| [03 - User-Role Assignment Data](./03-User-Role-Assignment-Data.md) | User-to-role mappings | 4, 5 |
| [04 - User Activity Telemetry Data](./04-User-Activity-Telemetry-Data.md) | User actions, sessions, telemetry | 4, 5, 8 |
| [05 - Functional Requirements](./05-Functional-Requirements.md) | Core capabilities, MVP features | 5, 6, 7, 9 |
| [06 - Algorithms & Decision Logic](./06-Algorithms-Decision-Logic.md) | 8 core algorithms with pseudocode | 5, 10, 13 |
| [07 - Advanced Algorithms Expansion](./07-Advanced-Algorithms-Expansion.md) | 24 advanced algorithms (incl. 3.9, 4.7) | 5, 10 |
| [08 - Algorithm Review Summary](./08-Algorithm-Review-Summary.md) | Complete portfolio review (34 algorithms) | 2, 5 |
| [09 - License Minority Detection](./09-License-Minority-Detection-Algorithm.md) | Algorithm 2.5 detailed specification | 5 |
| [10 - Additional Algorithms Exploration](./10-Additional-Algorithms-Exploration.md) | Algorithm 2.6 detailed specification | 5 |
| [11 - License Trend Analysis](./11-License-Trend-Analysis-Algorithm.md) | Algorithm 4.4 detailed specification | 5 |
| [12 - Final Phase 1 Selection](./12-Final-Phase1-Selection.md) | 10 algorithms selected for Phase 1 | 2, 3, 5 |
| [13 - Azure AI Agent Architecture](./13-Azure-Foundry-Agent-Architecture.md) | 6-layer agent architecture, APIs, scheduling | 3, 4, 5, 7, 8, 10 |
| [14 - Web Application Requirements](./14-Web-Application-Requirements.md) | Dashboards, reports, user interface | 6, 7, 9 |
| [15 - Default SoD Conflict Matrix](./15-Default-SoD-Conflict-Matrix.md) | 27 SoD rules across 7 categories | 5, 11 |
| [16 - Rollback & Fast-Restore Procedures](./16-Rollback-Fast-Restore-Procedures.md) | SLA, escalation, observation mode | 6, 7, 8, 11 |

---

## 2. Process Inventory

### 2.1 Master Process List

| Process ID | Process Name | Type | Phase | Trigger Type | Source Documents |
|-----------|-------------|------|-------|-------------|-----------------|
| **P-01** | Data Ingestion & Sync (4 core + 1 optional) | Core Pipeline | 1 | Scheduled + Event | 01, 02, 03, 04, 13 |
| **P-02** | Data Normalization & Validation | Core Pipeline | 1 | System-Automatic | 13 |
| **P-03** | Algorithm Execution Pipeline | Core Pipeline | 2 | Scheduled + On-Demand | 06, 07, 12, 13 |
| **P-04** | Recommendation Generation | Core Pipeline | 2 | System-Automatic | 05, 06, 13 |
| **P-05** | Observation Mode (Shadow Mode) | Validation | 3 | System-Automatic | 16 |
| **P-06** | Approval Workflow | Validation | 3 | Event-Based | 05, 14, 16 |
| **P-07** | License Change Execution | Core Pipeline | 4 | Event-Based | 05, 13, 16 |
| **P-08** | Post-Implementation Monitoring | Monitoring | 5 | System-Automatic | 13, 16 |
| **P-09** | Rollback & Fast-Restore | Recovery | 5 | Event-Based + Manual | 16 |
| **P-10** | OData Throttling Management | Supporting | 1 | System-Automatic | 13 |
| **P-11** | Dashboard Rendering & Refresh | Cross-Cutting | Web App | Event-Based | 14 |
| **P-12** | Recommendation Review & Action | Cross-Cutting | Web App | Manual | 14, 16 |
| **P-13** | Report Generation & Distribution | Cross-Cutting | Web App | Scheduled + Manual | 14 |
| **P-14** | User Notification & Communication | Supporting | 4 | Event-Based | 16 |
| **P-15** | SoD Violation Detection & Workflow | Validation | 2 | Scheduled + Event | 07, 15 |
| **P-16** | Configuration Management | Supporting | 4 | Manual | 06, 13, 14, 15 |
| **P-17** | Escalation Management | Recovery | 5 | System-Automatic | 16 |
| **P-18** | Temporary License Elevation | Recovery | 5 | Event-Based + Manual | 16 |
| **P-19** | Period-End Safeguard | Validation | 3 | Scheduled | 16 |
| **P-20** | Circuit Breaker & Auto-Disable | Safety | 5 | System-Automatic | 16 |
| **P-21** | Rollback Tracking & Feedback Loop | Analytics | 5 | System-Automatic | 16 |
| **P-22** | New User License Suggestion ⭐ NEW | Cross-Cutting | Web App + 2 | Manual + Event | 05, 07, 14, 15 |

### 2.2 Process Classification

| Classification | Process IDs | Count | Description |
|---------------|------------|-------|-------------|
| **Core Pipeline** | P-01, P-02, P-03, P-04, P-07 | 5 | Primary data-to-action pipeline |
| **Validation & Safety** | P-05, P-06, P-19 | 3 | Pre-execution gates and checks |
| **Recovery** | P-09, P-17, P-18, P-20 | 4 | Restore, escalate, and protect |
| **Supporting** | P-10, P-14, P-16 | 3 | Infrastructure and communication |
| **Analytics** | P-08, P-21 | 2 | Monitoring and learning |
| **Cross-Cutting (Web App)** | P-11, P-12, P-13, P-22 | 4 | User interface processes |
| **Compliance** | P-15 | 1 | Regulatory detection |
| **TOTAL** | | **22** | |

### 2.3 Trigger Type Summary

| Trigger Type | Processes | Description |
|-------------|----------|-------------|
| **Scheduled** | P-01, P-03, P-13, P-15, P-19 | Time-based execution (daily, weekly, monthly) |
| **Event-Based** | P-01, P-06, P-07, P-09, P-11, P-14, P-15, P-18 | Triggered by system or user events |
| **Manual** | P-03, P-09, P-12, P-13, P-16, P-18 | Initiated by human actors |
| **System-Automatic** | P-02, P-04, P-05, P-08, P-10, P-17, P-20, P-21 | Triggered automatically by system state |

### 2.4 Actor / System Registry

| Actor | Type | Role | Participates In |
|-------|------|------|-----------------|
| **Azure AI Agent** | System | Processing engine, algorithm execution | P-01 through P-05, P-08, P-10, P-15, P-20, P-21 |
| **D365 FO Environment** | System | Source system for security config, roles, audit | P-01, P-07 |
| **Azure Application Insights** | System | Source system for user activity telemetry | P-01 |
| **OData API** | System | Data extraction interface | P-01, P-10 |
| **Data Lake / SQL Store** | System | Normalized data storage | P-01, P-02 |
| **Recommendation Engine** | System | Generates prioritized recommendations | P-04 |
| **Notification Service** | System | Email, web app, SMS notifications | P-14 |
| **Web Application** | System | User interface and dashboards | P-11, P-12, P-13 |
| **Audit Log Store** | System | Immutable audit trail | P-06, P-07, P-08, P-09 |
| **Circuit Breaker** | System | Automatic algorithm disable | P-20 |
| **D365 System Administrator** | Human | Operates rollback, manages config | P-07, P-09, P-12, P-16, P-17 |
| **License Manager** | Human | Root cause analysis, algorithm tuning | P-06, P-09, P-16, P-17, P-21 |
| **Security Officer** | Human | Compliance review, SoD oversight | P-06, P-12, P-15 |
| **Help Desk (Tier 1)** | Human | First responder, triage | P-09, P-17, P-18 |
| **IT Management** | Human | SLA oversight, escalation authority | P-17 |
| **Line Manager** | Human | Team approval, freeze requests | P-06, P-12 |
| **End User** | Human | Self-service restore, feedback | P-09, P-12, P-18 |
| **CFO / Finance** | Human | Budget approval, executive oversight | P-13 |
| **Auditor (External)** | Human | Compliance review, evidence requests | P-13, P-15 |

---

## 3. Agent Lifecycle Overview

### 3.1 Primary Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AGENT LIFECYCLE: END-TO-END FLOW                     │
└─────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ PHASE 1: DATA ACQUISITION                                          │
  │                                                                     │
  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
  │  │ D365 FO      │   │ Azure App    │   │ P-10: OData          │   │
  │  │ (OData)      │──>│ Insights     │──>│ Throttle Mgmt        │   │
  │  │ P-01: Ingest │   │ P-01: Ingest │   └──────────────────────┘   │
  │  └──────┬───────┘   └──────┬───────┘                               │
  │         └──────────┬───────┘                                        │
  │                    ▼                                                 │
  │         ┌──────────────────┐                                        │
  │         │ P-02: Normalize  │                                        │
  │         │ & Validate       │                                        │
  │         └────────┬─────────┘                                        │
  └──────────────────┼─────────────────────────────────────────────────┘
                     ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ PHASE 2: ANALYSIS & RECOMMENDATION                                  │
  │                                                                     │
  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
  │  │ P-03: Algorithm   │  │ P-04: Generate   │  │ P-15: SoD      │   │
  │  │ Execution Pipeline│─>│ Recommendations  │  │ Detection      │   │
  │  │ (10 algorithms)   │  │ (confidence,     │  │ (27 rules)     │   │
  │  └──────────────────┘  │  priority, cost)  │  └────────────────┘   │
  │                        └────────┬──────────┘                        │
  └─────────────────────────────────┼───────────────────────────────────┘
                                    ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ PHASE 3: VALIDATION & APPROVAL                                      │
  │                                                                     │
  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
  │  │ P-05: Observation │  │ P-06: Approval   │  │ P-19: Period-  │   │
  │  │ Mode (30+ days)   │─>│ Workflow         │<─│ End Safeguard  │   │
  │  │ (>= 95% accuracy) │  │ (manager/admin)  │  │ (freeze check) │   │
  │  └──────────────────┘  └────────┬──────────┘  └────────────────┘   │
  └─────────────────────────────────┼───────────────────────────────────┘
                                    ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ PHASE 4: IMPLEMENTATION & COMMUNICATION                             │
  │                                                                     │
  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
  │  │ P-07: License     │  │ P-14: User       │  │ P-16: Config   │   │
  │  │ Change Execution  │  │ Notification     │  │ Management     │   │
  │  │ (audit trail)     │  │ (pre/post/emerg) │  │ (parameters)   │   │
  │  └────────┬─────────┘  └──────────────────┘  └────────────────┘   │
  └───────────┼─────────────────────────────────────────────────────────┘
              ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ PHASE 5: MONITORING & CONTINUOUS IMPROVEMENT                        │
  │                                                                     │
  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐  │
  │  │ P-08:      │ │ P-09:      │ │ P-17:      │ │ P-18: Temp     │  │
  │  │ Post-Impl  │ │ Rollback & │ │ Escalation │ │ License        │  │
  │  │ Monitoring │ │ Restore    │ │ Mgmt       │ │ Elevation      │  │
  │  └────────────┘ └────────────┘ └────────────┘ └────────────────┘  │
  │  ┌────────────┐ ┌────────────────────┐                             │
  │  │ P-20:      │ │ P-21: Rollback     │                             │
  │  │ Circuit    │ │ Tracking &         │──── FEEDBACK ───┐           │
  │  │ Breaker    │ │ Feedback Loop      │                 │           │
  │  └────────────┘ └────────────────────┘                 │           │
  └────────────────────────────────────────────────────────┼───────────┘
                                                           │
              ┌────────────────────────────────────────────┘
              ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ FEEDBACK LOOP: Rollback data feeds back to Phase 2 algorithms,     │
  │ adjusting confidence scores, disabling patterns, and improving      │
  │ recommendation accuracy over time.                                  │
  └─────────────────────────────────────────────────────────────────────┘

  ╔═════════════════════════════════════════════════════════════════════╗
  ║ CROSS-CUTTING: WEB APPLICATION (P-11, P-12, P-13)                  ║
  ║ Provides dashboards, review interfaces, and reports across all     ║
  ║ phases. Users interact with every phase through the web app.       ║
  ╚═════════════════════════════════════════════════════════════════════╝
```

### 3.2 Phase Summary

| Phase | Name | Processes | Purpose | Typical Duration |
|-------|------|-----------|---------|-----------------|
| **1** | Data Acquisition | P-01, P-02, P-10 | Ingest, throttle-manage, normalize, and validate data from all 4 sources | Continuous + 2-4 hour full loads |
| **2** | Analysis & Recommendation | P-03, P-04, P-15 | Execute 10 Phase 1 algorithms, generate prioritized recommendations, detect SoD violations | < 2 hours (full org scan) |
| **3** | Validation & Approval | P-05, P-06, P-19 | Shadow-validate recommendations, route for approval, enforce period-end freezes | 30-60 days (observation) + approval SLA |
| **4** | Implementation & Communication | P-07, P-14, P-16 | Execute approved license changes, notify users, maintain configuration | < 1 day per batch |
| **5** | Monitoring & Improvement | P-08, P-09, P-17, P-18, P-20, P-21 | Monitor outcomes, restore access when needed, escalate, learn from rollbacks | Ongoing |
| **Web App** | Cross-Cutting | P-11, P-12, P-13 | Render dashboards, enable review actions, generate reports | Continuous |

### 3.3 End-to-End Timing

| Stage | Activity | Duration | Cumulative |
|-------|----------|----------|-----------|
| **Initial Setup** | Data source connection, initial full load | 1-3 days | Day 1-3 |
| **First Analysis** | Algorithm execution on full organization | 2-4 hours | Day 3-4 |
| **Observation** | Shadow mode validation for each algorithm | 30-60 days | Day 4-64 |
| **First Approvals** | Manager/admin review and approval | 1-5 business days | Day 64-69 |
| **First Changes** | License change execution + notification | 1-2 business days | Day 69-71 |
| **Post-Monitoring** | Validate no user impact, measure savings | 7-14 days | Day 71-85 |
| **Confirmed Value** | Savings validated, feedback loop active | Ongoing | Day 85+ |

**Total time from deployment to confirmed value**: ~60-90 days

---

## 4. Phase 1: Data Acquisition

### 4.1 P-01: Data Ingestion & Sync

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-01 |
| **Trigger** | Scheduled (daily full, continuous streaming) + Event-based (config change) |
| **Actors** | Azure AI Agent (Data Ingestion Layer), D365 FO, Azure App Insights |
| **Inputs** | D365 FO OData endpoints (security config, user-role, audit logs), Azure App Insights telemetry stream |
| **Source Docs** | [01](./01-Data-Sources-Overview.md), [02](./02-Security-Configuration-Data.md), [03](./03-User-Role-Assignment-Data.md), [04](./04-User-Activity-Telemetry-Data.md), [13](./13-Azure-Foundry-Agent-Architecture.md) |

**Actions**:

1. **Security Configuration Ingestion** (OData from D365 FO)
   - Initial full load: ~700K records, 2-4 hours
   - Incremental delta sync: Changed records only (< 1 hour, 95%+ reduction via Change Tracking)
   - Frequency: Delta every hour; full refresh weekly (off-peak)
   - Data freshness target: < 1 hour

2. **User-Role Assignment Ingestion** (OData from D365 FO)
   - Volume: 200-200K records depending on org size
   - Frequency: Delta every hour; event-triggered on role changes
   - Data freshness target: < 1 hour

3. **User Activity Telemetry Ingestion** (Azure App Insights)
   - Source: X++ custom instrumentation → App Insights custom events
   - Volume: 10K-10M events/day
   - Delivery: Continuous streaming via Event Hub
   - Data freshness target: < 15 minutes
   - Key fields: User ID, Menu Item/Form, Action (Read/Write/Delete/Create), Timestamp, Session ID

4. **Audit Log Ingestion** (D365 FO + App Insights)
   - Source: Security changes, role assignments, configuration modifications
   - Volume: Variable
   - Delivery: Continuous streaming
   - Data freshness target: < 15 minutes

**Outputs**: Raw data stored in Data Lake / SQL for processing by P-02

**Gates**:
- Gate 1 (OData Capacity): OData extraction must not exceed 10% of D365 FO's available API capacity
- All ingestion failures trigger alerts to D365 System Administrator

**Error Handling**:
- 429 (Too Many Requests): Exponential backoff (1s, 2s, 4s, 8s, max 60s) — handled by P-10
- Connection failure: Retry 3x, then alert; continue with cached data
- Schema mismatch: Log validation error, alert administrator, skip malformed records

---

### 4.2 P-02: Data Normalization & Validation

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-02 |
| **Trigger** | System-Automatic (runs after each P-01 ingestion batch) |
| **Actors** | Azure AI Agent (Data Ingestion Layer) |
| **Inputs** | Raw ingested data from P-01 |
| **Source Docs** | [13](./13-Azure-Foundry-Agent-Architecture.md) |

**Actions**:

1. **Schema Validation**: Verify all required fields present and correctly typed
2. **Data Type Checking**: Ensure dates, enums, numeric fields conform to expected formats
3. **Reference Data Integrity**: Validate foreign keys (user IDs exist, role names match)
4. **Deduplication**: Remove duplicate records from delta sync overlap
5. **Enrichment**: Add license type mappings to menu items, calculate derived fields
6. **Aggregation**: Pre-compute user-level and role-level metrics for algorithm consumption
7. **Materialized Views**: Update cached aggregations (role compositions, user activity summaries)

**Outputs**: Normalized, validated, enriched data ready for algorithm execution (P-03)

**Gates**:
- Gate 2 (Data Quality): Validation errors must be < 0.1% of total records; if exceeded, alert and pause algorithm execution

**Error Handling**:
- Validation errors below threshold: Log and skip individual records; continue processing
- Validation errors above 0.1%: Pause downstream processing, alert D365 Admin, generate data quality report
- Missing reference data: Flag affected records, exclude from analysis, notify administrator

---

### 4.3 P-10: OData Throttling Management

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-10 |
| **Trigger** | System-Automatic (runs alongside P-01 OData operations) |
| **Actors** | Azure AI Agent (Data Ingestion Layer) |
| **Inputs** | OData API response headers, throttling diagnostics |
| **Source Docs** | [13](./13-Azure-Foundry-Agent-Architecture.md) |

**Actions**:

1. **Monitor API Capacity**: Track D365 FO throttling diagnostics (`/api/throttling/diagnostics`)
2. **Apply Strategy Selection**: Choose optimal extraction strategy based on current load

| Strategy | When Applied | Throttling Risk | Data Freshness |
|----------|-------------|-----------------|----------------|
| Delta Sync | Default for incremental updates | Very Low | < 1 hour |
| Off-Peak Full Load | Weekly full refresh | Low | 4-6 hours (scheduled) |
| Batched Extraction | Initial load, large datasets | Medium | 2-4 hours |
| Data Lake Export | Where available (bypass OData) | None | Config-dependent |
| Retry + Backoff | On 429 responses (automatic) | N/A (mitigation) | Adds latency |

3. **Pagination Management**: Use `$top`/`$skip` with 5,000 records per page; use `$batch` for bundled queries
4. **Performance Enforcement**: Ensure extraction stays below 10% of D365 FO API capacity

**Outputs**: Managed OData extraction flow respecting D365 FO throttling limits

**Error Handling**:
- 429 response: Exponential backoff (1s → 2s → 4s → 8s → max 60s); log retry metrics
- Sustained throttling: Switch to off-peak scheduling; alert administrator
- Data Lake Export availability: Automatically prefer when configured (eliminates throttling entirely)

---

### 4.4 Data Acquisition Sub-Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ DATA ACQUISITION PIPELINE                                            │
└──────────────────────────────────────────────────────────────────────┘

 ┌─────────────────┐          ┌──────────────────────┐
 │ D365 FO         │          │ Azure App Insights   │
 │ ┌─────────────┐ │          │ ┌──────────────────┐ │
 │ │ Security    │ │          │ │ User Activity    │ │
 │ │ Config      │ │          │ │ Telemetry        │ │
 │ │ (~700K rec) │ │          │ │ (10K-10M/day)    │ │
 │ └──────┬──────┘ │          │ └────────┬─────────┘ │
 │ ┌──────┴──────┐ │          │          │            │
 │ │ User-Role   │ │          └──────────┼────────────┘
 │ │ Assignments │ │                     │
 │ └──────┬──────┘ │                     │
 │ ┌──────┴──────┐ │                     │
 │ │ Audit Logs  │ │                     │
 │ └──────┬──────┘ │                     │
 └────────┼────────┘                     │
          │                              │
          ▼                              ▼
 ┌────────────────┐          ┌───────────────────┐
 │ P-10: OData    │          │ Event Hub /       │
 │ Throttle Mgmt  │          │ Streaming Ingest  │
 │ (backoff,      │          │ (continuous)      │
 │  batching,     │          └─────────┬─────────┘
 │  delta sync)   │                    │
 └────────┬───────┘                    │
          │                            │
          └──────────┬─────────────────┘
                     ▼
          ┌──────────────────┐
          │ P-02: Normalize  │
          │ & Validate       │
          │ ┌──────────────┐ │
          │ │ Schema check │ │
          │ │ Dedup        │ │
          │ │ Enrich       │ │   Gate 2: < 0.1% errors
          │ │ Aggregate    │─┼──────────────────────>
          │ └──────────────┘ │
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │ Data Lake / SQL  │
          │ (Ready for       │
          │  Phase 2)        │
          └──────────────────┘
```

**Input/Output Summary**:

| Process | Inputs | Outputs | Frequency |
|---------|--------|---------|-----------|
| P-01 | 4 external data sources | Raw data in staging | Continuous + scheduled |
| P-02 | Raw staged data | Normalized, enriched, validated data | After each P-01 batch |
| P-10 | OData API state | Managed extraction flow | During all OData operations |

---

## 5. Phase 2: Analysis & Recommendation

### 5.1 P-03: Algorithm Execution Pipeline

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-03 |
| **Trigger** | Scheduled (daily incremental, weekly full) + On-demand (user request via web app) |
| **Actors** | Azure AI Agent (Algorithm Execution Engine) |
| **Inputs** | Normalized data from P-02, algorithm configuration parameters, cached role compositions |
| **Source Docs** | [06](./06-Algorithms-Decision-Logic.md), [07](./07-Advanced-Algorithms-Expansion.md), [12](./12-Final-Phase1-Selection.md), [13](./13-Azure-Foundry-Agent-Architecture.md) |

**Actions**:

Execute 10 Phase 1 algorithms in optimal dependency order:

| Step | Algorithm | ID | Type | Depends On | Parallel? |
|------|-----------|-----|------|-----------|-----------|
| 1 | Role License Composition Analyzer | 1.1 | Prerequisite | Data (P-02) | — |
| 2 | Orphaned Account Detector | 3.5 | Security | 1.1 | Yes (with Step 3) |
| 3 | Component Removal Recommender | 1.4 | Cost | 1.1 | Yes (with Step 2) |
| 4 | Read-Only User Detector | 2.2 | Cost | 1.1 | — |
| 5 | License Minority Detection | 2.5 | Cost | 2.2 | — |
| 6 | Cross-Role License Optimization | 2.6 | Cost | 2.2 | — |
| 7 | Role Splitting Recommender | 1.3 | Cost | 1.1 + user segments | — |
| 8 | Multi-Role Optimization | 2.4 | Cost | 2.6 | — |
| 9 | Time-Based Access Analyzer | 5.3 | Security | Data (P-02) | Yes (with Step 7-8) |
| 10 | SoD Violation Detector | 3.1 | Compliance | Data (P-02) + SoD matrix | Yes (with Step 7-8) |
| 11 | License Trend Analysis | 4.4 | Strategic | Steps 2-10 completed | — |
| 12 | Result Aggregation & Deduplication | — | Pipeline | All steps | — |

**Execution Modes**:

| Mode | Trigger | Scope | Response Time | Schedule |
|------|---------|-------|---------------|----------|
| On-Demand | User via web app | Single user, role, or custom | < 30 seconds | N/A |
| Daily Incremental | Schedule (2-4 AM) | Last 24h changes | ~30 minutes | Daily |
| Weekly Full Scan | Schedule (Sunday 2-6 AM) | All users | < 2 hours (10K users) | Weekly |
| Event-Triggered | Config/role change | Affected users/roles | < 15 minutes | On event |

**Outputs**: Algorithm results per user/role, stored for recommendation generation (P-04)

**Gates**:
- Gate 3 (Algorithm Confidence): Recommendations below confidence threshold 0.70 require manual approval

**Error Handling**:
- Single algorithm failure: Log error, skip algorithm, continue pipeline; alert License Manager
- Data staleness: If source data is > 24 hours old, flag all recommendations with "stale data" warning
- Timeout: Full org scan timeout after 4 hours; partial results stored, alert generated

---

### 5.2 P-04: Recommendation Generation

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-04 |
| **Trigger** | System-Automatic (runs after P-03 completes) |
| **Actors** | Azure AI Agent (Recommendation Engine) |
| **Inputs** | Algorithm results from P-03 |
| **Source Docs** | [05](./05-Functional-Requirements.md), [06](./06-Algorithms-Decision-Logic.md), [13](./13-Azure-Foundry-Agent-Architecture.md) |

**Actions**:

1. **Confidence Scoring**: Assign HIGH (>80), MEDIUM (60-80), LOW (<60) to each recommendation
2. **Multi-Option Generation**: For each recommendation, provide:
   - Option 1: Optimal change (e.g., downgrade to Team Members)
   - Option 2: Conservative change (e.g., downgrade to Operations Activity)
   - Option 3: No change (keep current license)
3. **Business Impact Calculation**:
   - Monthly/annual cost savings (using `GetEffectiveLicenseCost()` — customer overrides when configured)
   - Risk assessment (impact to user workflow)
   - Implementation effort (Low/Medium/High)
4. **Priority Ranking**: Primary by savings, secondary by complexity, tertiary by risk reduction
5. **Deduplication**: Merge overlapping recommendations from different algorithms
6. **Seasonal Risk Check**: Cross-reference with user seasonal profiles; flag recommendations during known off-seasons with reduced confidence
7. **Implementation Guidance**: Generate step-by-step instructions, required approvals, rollback procedures

**Outputs**: Prioritized recommendation list with confidence scores, options, business impact, and implementation guidance

**Error Handling**:
- Conflicting recommendations from different algorithms: Flag for manual review by License Manager
- Missing pricing data: Use list prices as fallback; flag recommendation with "list price used" warning

---

### 5.3 P-15: SoD Violation Detection & Workflow

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-15 |
| **Trigger** | Scheduled (weekly) + Event-based (role assignment change) |
| **Actors** | Azure AI Agent, Security Officer |
| **Inputs** | User-role assignment data (P-02), SoD Conflict Matrix (27 default rules + custom rules) |
| **Source Docs** | [07](./07-Advanced-Algorithms-Expansion.md), [15](./15-Default-SoD-Conflict-Matrix.md) |

**Actions**:

1. **Load Conflict Matrix**: 27 default rules across 7 categories (AP, AR, GL, Procurement, Inventory, Cash Mgmt, System Admin) + any custom rules
2. **Merge Custom Rules**: Custom overrides default where Rule IDs match
3. **Scan All Users**: For each user, get all assigned roles; for each role pair, check against merged matrix
4. **Generate Violation Records**: Include severity (Critical/High/Medium), risk description, regulatory reference
5. **Apply Scoring Factors**: Activity factor, transaction volume, compensating controls, user position
6. **Route Critical/High Violations**: Notify Security Officer immediately; Critical violations have 24-hour SLA
7. **Generate Compliance Report**: Sortable violation report for auditors

**Outputs**: SoD violation report, compliance alerts, remediation recommendations

**Gates**: Zero tolerance for unacknowledged Critical violations beyond 24 hours

**Error Handling**:
- Role mapping mismatch: Flag as "unmapped role pair" for administrator configuration
- Missing compensating control documentation: Default to base severity (no reduction)

---

### 5.4 Analysis & Recommendation Sub-Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ ANALYSIS & RECOMMENDATION PIPELINE                                    │
└──────────────────────────────────────────────────────────────────────┘

 Normalized Data (from Phase 1)
          │
          ▼
 ┌────────────────────────────────────────────────────────────────┐
 │ P-03: ALGORITHM EXECUTION                                      │
 │                                                                 │
 │  Step 1: Role License Composition (1.1) ─── prerequisite       │
 │           │                                                     │
 │           ├──> Step 2: Orphaned Accounts (3.5) ─┐              │
 │           ├──> Step 3: Component Removal (1.4) ──┤ parallel    │
 │           │                                      │              │
 │           ▼                                      │              │
 │  Step 4: Read-Only Detector (2.2)                │              │
 │           │                                      │              │
 │           ├──> Step 5: License Minority (2.5)    │              │
 │           ├──> Step 6: Cross-Role (2.6)          │              │
 │           │         │                            │              │
 │           │         ▼                            │              │
 │           │    Step 8: Multi-Role (2.4)          │              │
 │           │                                      │              │
 │           ├──> Step 7: Role Splitting (1.3)      │              │
 │           │                                      │              │
 │  Step 9:  Time-Based Access (5.3)  ──────────────┤ parallel    │
 │  Step 10: SoD Violations (3.1)   ───────────────┤ parallel    │
 │                                                  │              │
 │           ▼                                      ▼              │
 │  Step 11: License Trend Analysis (4.4) ◄── all results        │
 │           │                                                     │
 │  Step 12: Result Aggregation & Dedup                           │
 └───────────┼─────────────────────────────────────────────────────┘
             ▼
 ┌────────────────────────────────────────────────────────────────┐
 │ P-04: RECOMMENDATION GENERATION                                │
 │                                                                 │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
 │  │ Confidence   │  │ Multi-Option │  │ Business Impact      │ │
 │  │ Scoring      │  │ Generation   │  │ Calculation          │ │
 │  │ (H/M/L)      │  │ (3 options)  │  │ (savings, risk)      │ │
 │  └──────────────┘  └──────────────┘  └──────────────────────┘ │
 │                                                                 │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
 │  │ Priority     │  │ Seasonal     │  │ Implementation       │ │
 │  │ Ranking      │  │ Risk Check   │  │ Guidance             │ │
 │  └──────────────┘  └──────────────┘  └──────────────────────┘ │
 └───────────┼─────────────────────────────────────────────────────┘
             ▼
    Prioritized Recommendations → Phase 3
```

---

## 6. Phase 3: Validation & Approval

### 6.1 P-05: Observation Mode (Shadow Mode)

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-05 |
| **Trigger** | System-Automatic (every new or updated algorithm enters observation) |
| **Actors** | Azure AI Agent, License Manager |
| **Inputs** | Generated recommendations (from P-04), actual user behavior (from P-01/P-02) |
| **Source Docs** | [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Generate Without Executing**: Recommendations are logged but NOT applied; users retain current licenses
2. **Track Actual Behavior**: Monitor whether users access modules that would have been removed
3. **Validate Over Time**: Compare all recommendations against actual usage over observation period
4. **Compute Accuracy Metrics**:

| Metric | Definition | Target |
|--------|-----------|--------|
| True Positive Rate | Correct recommendations / Total recommendations | > 95% |
| False Positive Rate | Incorrect recommendations (would have blocked users) | < 5% |
| False Positive Impact | Work hours that would have been lost | 0 hours |
| Coverage | % of users evaluated during observation | > 80% |

5. **State Transitions**:

| From | To | Trigger | Requirements |
|------|----|---------|-------------|
| Algorithm Created | Observation Mode | Deployment | Automatic |
| Observation Mode | Validation Review | Period complete | Minimum 30 days |
| Validation Review | Active Mode | Accuracy OK | >= 95%, License Manager approval |
| Validation Review | Back to Observation | Accuracy low | < 95% or rejected |
| Active Mode | Observation Mode | 3+ rollbacks OR code change | Re-observation required |

**Outputs**: Observation report with accuracy metrics, ready for License Manager review

**Gates**:
- Gate 4 (Observation Accuracy): Must achieve >= 95% accuracy
- Zero false positives that would have caused P1 (Critical) user impact
- License Manager approval required to exit observation

**Error Handling**:
- Insufficient data coverage: Extend observation period until >= 80% coverage achieved
- Algorithm update during observation: Reset observation timer; new 30-day minimum begins

---

### 6.2 P-06: Approval Workflow

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-06 |
| **Trigger** | Event-Based (recommendation ready for approval after observation) |
| **Actors** | Line Manager, D365 System Administrator, License Manager, Security Officer |
| **Inputs** | Validated recommendations from P-05, user context, business impact data |
| **Source Docs** | [05](./05-Functional-Requirements.md), [14](./14-Web-Application-Requirements.md), [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Route to Approver**: Based on recommendation type and confidence:
   - HIGH confidence: Route to D365 Admin for batch approval
   - MEDIUM confidence: Route to Line Manager + D365 Admin
   - LOW confidence: Route to License Manager for manual review
2. **Display in Web App**: Approver sees recommendation details, options, business impact, implementation guidance
3. **Approval Actions**: Approve, Reject (with reason), Defer (with date), Request More Info
4. **Bulk Approval**: Multiple HIGH-confidence recommendations can be approved in batch
5. **Audit Trail**: Every approval/rejection logged with approver, timestamp, reason
6. **Period-End Check**: Before allowing approval, verify no active freeze window (P-19)

**Outputs**: Approved or rejected recommendations; approved items proceed to P-07

**Gates**:
- Gate 5 (Period-End Freeze): No approvals processed during active freeze windows
- Gate 6 (Approval Authority): Approver must have correct role permissions

**Error Handling**:
- Approver unavailable > 5 business days: Auto-escalate to next tier
- Approval during freeze window: Reject with message "Period-end freeze active until [date]"

---

### 6.3 P-19: Period-End Safeguard

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-19 |
| **Trigger** | Scheduled (calendar-based freeze windows) |
| **Actors** | Azure AI Agent, D365 System Administrator, IT Management (override authority) |
| **Inputs** | Organization freeze calendar, current date |
| **Source Docs** | [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Check Freeze Calendar**: Determine if current date falls within a freeze window:

| Period | Freeze Start | Freeze End | Duration |
|--------|-------------|-----------|----------|
| Month-end | Last 5 business days | First 5 business days of next month | ~10 days |
| Quarter-end | Last 7 business days | First 7 business days of next quarter | ~14 days |
| Year-end | December 15 | January 15 | ~1 month |
| Audit period | Configurable | Configurable | Varies |

2. **Block New Executions**: All license optimization changes are frozen during freeze windows
3. **Block Pending Approvals**: Pending approvals are paused (not rejected)
4. **Preserve Restores**: Temporary elevations and rollbacks are NEVER frozen
5. **Manager Team Freeze**: Line managers can request additional freeze for their team (up to 30 days; > 14 days requires License Manager approval)

**Outputs**: Freeze/no-freeze state consumed by P-06 and P-07

**Override Process**:
1. IT Director or above submits override request
2. Must include: business justification, affected users, risk acknowledgment
3. License Manager documents override; logged in audit trail
4. Rollbacks during override periods flagged as high-priority

**Error Handling**:
- Calendar misconfiguration: Default to freeze (safe fallback)
- Override without documentation: Reject; require formal justification

---

## 7. Phase 4: Implementation & Communication

### 7.1 P-07: License Change Execution

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-07 |
| **Trigger** | Event-Based (approval granted in P-06) |
| **Actors** | Azure AI Agent, D365 System Administrator |
| **Inputs** | Approved recommendations from P-06 |
| **Source Docs** | [05](./05-Functional-Requirements.md), [13](./13-Azure-Foundry-Agent-Architecture.md), [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Pre-Execution Verification**:
   - Re-verify no active period-end freeze (P-19)
   - Re-verify circuit breaker is not tripped for this algorithm/pattern (P-20)
   - Confirm user still exists and has same role assignments
2. **Execute License Change**:
   - Update user license assignment in D365 FO
   - Record change in audit log (who, what, when, why, approved by)
3. **Store Rollback Snapshot**:
   - Capture pre-change state (previous license, previous roles)
   - Store for fast-restore capability
4. **Trigger Post-Change Notification** (P-14)
5. **Activate Post-Implementation Monitoring** (P-08)

**Outputs**: License change applied, rollback snapshot stored, audit trail recorded

**Gates**:
- Gate 5 re-check (Period-End)
- Gate 7 re-check (Circuit Breaker)

**Error Handling**:
- D365 FO API failure: Retry 3x with backoff; if still failing, mark recommendation as "execution failed," alert D365 Admin
- User not found: Mark as "user deleted/disabled"; close recommendation
- Concurrent modification: Detect and resolve; re-analyze before retry

---

### 7.2 P-14: User Notification & Communication

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-14 |
| **Trigger** | Event-Based (triggered by P-07 license change, P-09 rollback, P-18 elevation) |
| **Actors** | Notification Service, End User, Line Manager |
| **Inputs** | Change details, user contact info, notification templates |
| **Source Docs** | [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Pre-Change Notification** (5 business days before scheduled change):
   - Template: What's changing, when, why, how to object
   - Channels: Email + web app notification
   - Recipients: Affected user + direct manager

2. **Post-Change Follow-Up** (1 business day after change applied):
   - Template: What changed, how to report issues, "Request Access Restore" instructions
   - Channels: Email + web app notification
   - Recipients: Affected user

3. **Emergency Restore Confirmation** (immediately upon access restore):
   - Template: Access confirmed restored, apology, next steps
   - Channels: Email + web app notification + SMS (for P1)
   - Recipients: Affected user, manager, Help Desk

4. **Monthly Optimization Summary** (first business day of each month):
   - Template: Team/org savings, rollback stats, upcoming changes
   - Channels: Email
   - Recipients: Line managers, IT Management, License Manager

**Outputs**: Notifications delivered through configured channels

**Error Handling**:
- Email delivery failure: Retry; fallback to web app notification only
- Invalid contact info: Alert D365 Admin; notification logged as "undeliverable"

---

### 7.3 P-16: Configuration Management

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-16 |
| **Trigger** | Manual (administrator changes settings) |
| **Actors** | D365 System Administrator, License Manager |
| **Inputs** | Configuration parameters, SoD matrix rules, pricing overrides |
| **Source Docs** | [06](./06-Algorithms-Decision-Logic.md), [13](./13-Azure-Foundry-Agent-Architecture.md), [14](./14-Web-Application-Requirements.md), [15](./15-Default-SoD-Conflict-Matrix.md) |

**Actions**:

1. **Algorithm Parameters**: Adjust thresholds via web app admin interface:

| Parameter | Default | Range |
|-----------|---------|-------|
| `READ_ONLY_THRESHOLD` | 95% | 80-99% |
| `LOW_USAGE_THRESHOLD` | 5% | 1-10% |
| `INACTIVE_DAYS` | 90 | 30-365 |
| `MIN_SEGMENT_SIZE` | 20% | 10-50% |
| `ACTIVITY_ANALYSIS_DAYS` | 90 | 30-180 |
| `CONFIDENCE_THRESHOLD` | 0.70 | 0.50-0.95 |

2. **License Pricing Overrides**: Configure actual EA/CSP negotiated rates (overrides list prices)
3. **SoD Matrix Management**: Add/modify/disable conflict rules; severity adjustments with compensating controls
4. **Scheduling Configuration**: Adjust batch job times, freeze calendar dates, observation durations
5. **Seasonal Period Configuration**: Define custom seasonal periods per organization

**Outputs**: Updated configuration consumed by all processes; changes audit-logged

**Error Handling**:
- Invalid parameter range: Reject with validation message
- All configuration changes require confirmation dialog
- Critical changes (disabling SoD rules, reducing confidence thresholds) require Security Officer approval

---

## 8. Phase 5: Monitoring & Continuous Improvement

### 8.1 P-08: Post-Implementation Monitoring

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-08 |
| **Trigger** | System-Automatic (activated after each P-07 license change) |
| **Actors** | Azure AI Agent |
| **Inputs** | User activity data (ongoing), change records from P-07 |
| **Source Docs** | [13](./13-Azure-Foundry-Agent-Architecture.md), [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Monitor Changed Users**: Track activity of users who received license changes
2. **Detect Access Failures**: Watch for patterns indicating blocked access:
   - Repeated failed access attempts to removed modules
   - User behavior changes (drop in activity, shift in patterns)
3. **Measure Savings**: Track actual cost savings vs. projected savings
4. **Generate Monitoring Report**: Daily summary of post-change status
5. **Auto-Flag Issues**: If anomalous patterns detected, auto-create P2 ticket

**Outputs**: Monitoring data, auto-generated tickets when issues detected

**Gates**:
- Gate 8 (Post-Implementation Monitoring Active): Monitoring must be confirmed active before any change is considered complete

**Error Handling**:
- Monitoring data gap: Alert D365 Admin; extend monitoring period

---

### 8.2 P-09: Rollback & Fast-Restore

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-09 |
| **Trigger** | Event-Based (user reports issue) + Manual (administrator-initiated) |
| **Actors** | End User, Help Desk (Tier 1), D365 System Administrator (Tier 2), License Manager (Tier 3) |
| **Inputs** | User issue report, rollback snapshot from P-07, SLA targets |
| **Source Docs** | [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Receive Issue Report** (via web app button, help desk ticket, or email)
2. **Classify Priority**:

| Priority | Description | Restore Target | Maximum |
|----------|-------------|---------------|---------|
| P1 - Critical | Blocked from essential functions | 1 hour | 2 hours |
| P2 - High | Blocked from regular functions | 2 hours | 4 hours |
| P3 - Medium | Degraded but can perform core work | 4 hours | 8 hours |
| P4 - Low | Noticed change, no workflow impact | Next business day | 2 business days |

3. **Execute Restore**: Restore user to pre-change license from rollback snapshot
4. **Confirm With User**: Verify access is fully restored
5. **Log Rollback**: Capture full rollback data for P-21 feedback loop
6. **Route to Investigation**: Forward to Tier 2/3 for root cause analysis

**Outputs**: User access restored, rollback logged, investigation initiated

**Error Handling**:
- Rollback snapshot not found: Escalate to D365 Admin for manual restore from D365 FO records
- Restore failure: Escalate to P1 regardless of original priority; on-call notification triggered

---

### 8.3 P-17: Escalation Management

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-17 |
| **Trigger** | System-Automatic (SLA timeout triggers) |
| **Actors** | Help Desk, D365 System Administrator, License Manager, IT Management |
| **Inputs** | Open tickets, SLA clock, escalation rules |
| **Source Docs** | [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

| Escalation Tier | Actor | Target Time | Responsibilities |
|----------------|-------|-------------|-----------------|
| **Tier 0** | End User | Immediate | Self-service restore via web app; report issue |
| **Tier 1** | Help Desk | 15 minutes | Triage, verify optimization-related, trigger temp elevation |
| **Tier 2** | D365 Admin | 30 minutes | Review recommendation, validate rollback, full license restore |
| **Tier 3** | License Manager | 1 business day | Root cause analysis, algorithm confidence update, corrective action |

**Timeout Auto-Actions**:

| Timeout | Auto-Action |
|---------|------------|
| Tier 1 exceeds 15 min | Auto-notify D365 Admin directly |
| Tier 2 exceeds 30 min (P1) | Auto-notify IT Management |
| Tier 2 exceeds 1 hour (P2) | Auto-notify IT Management |
| Tier 3 exceeds 1 business day | Auto-notify License Manager's supervisor |
| Temp elevation expiring without resolution | Auto-extend 7 days + escalate to IT Management |

**Outputs**: Escalated tickets, management notifications, resolution actions

**Error Handling**:
- All escalation contacts unreachable: Auto-grant temporary elevation; generate P1 management alert

---

### 8.4 P-18: Temporary License Elevation

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-18 |
| **Trigger** | Event-Based (user clicks "Request Access Restore") + Manual (Help Desk grants) |
| **Actors** | End User, Help Desk, D365 System Administrator |
| **Inputs** | User request, recent optimization change history |
| **Source Docs** | [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Verify Recent Change**: Confirm user had optimization change within last 90 days
2. **Grant Elevation**: Restore to original pre-optimization license (automatic, no human approval)
3. **Set Expiry**: Maximum 30 calendar days (configurable)
4. **Create Ticket**: Auto-create P2 help desk ticket
5. **Notify Stakeholders**: Help Desk, D365 Admin, License Manager, user's manager
6. **Track Expiry Alerts**:

| Alert | Timing | Recipients |
|-------|--------|-----------|
| Elevation granted | Immediately | All stakeholders |
| 7-day warning | 7 days before expiry | D365 Admin, License Manager |
| 3-day warning | 3 days before expiry | All stakeholders |
| 1-day warning | 1 day before expiry | All stakeholders |
| Expiry | On expiry date | All stakeholders |

7. **Resolve**: Must resolve to either Permanent Restore or Confirmed Downgrade with user acknowledgment

**Outputs**: Temporary license elevation granted, ticket created, stakeholders notified

**Error Handling**:
- No recent change found: Display message "No recent optimization changes found. Contact Help Desk for other issues."
- Elevation still unresolved at expiry: Auto-extend 7 days + escalate

---

### 8.5 P-20: Circuit Breaker & Auto-Disable

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-20 |
| **Trigger** | System-Automatic (rollback count exceeds threshold) |
| **Actors** | Azure AI Agent, License Manager |
| **Inputs** | Rollback tracking data from P-21 |
| **Source Docs** | [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Monitor Rollback Counts**: Track rollbacks per algorithm + pattern combination within 90-day window
2. **Trip Circuit Breaker**: 3 or more rollbacks for same algorithm + pattern → automatic disable
3. **Scope**: Disabled for specific pattern only (not globally)
4. **Notify License Manager**: Immediate notification with rollback history and pattern details
5. **Require Investigation**: License Manager must investigate, implement fix, and re-enable through observation mode (P-05)
6. **Reset**: Circuit breaker resets after algorithm completes new observation cycle with >= 95% accuracy

**Outputs**: Algorithm pattern disabled, investigation required

**Error Handling**:
- Bulk rollbacks from unrelated cause (e.g., D365 update): License Manager can manually override circuit breaker with documented justification

---

### 8.6 P-21: Rollback Tracking & Feedback Loop

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-21 |
| **Trigger** | System-Automatic (after every P-09 rollback) |
| **Actors** | Azure AI Agent, License Manager |
| **Inputs** | Rollback data from P-09, algorithm metadata |
| **Source Docs** | [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Capture Rollback Data**: Log comprehensive rollback record:
   - `rollback_id`, `user_id`, `original_recommendation_id`, `algorithm_id`, `algorithm_version`
   - `confidence_score`, `change_date`, `report_date`, `restore_date`, `time_to_restore`
   - `priority`, `rollback_category`, `rollback_reason`, `resolution_type`

2. **Classify Rollback Category**:

| Category | Code | Confidence Reduction |
|----------|------|---------------------|
| Algorithm Error | `ALGORITHM_ERROR` | -20% |
| Data Quality | `DATA_QUALITY` | -10% |
| Business Exception | `BUSINESS_EXCEPTION` | -10% |
| Seasonal | `SEASONAL` | -15% |
| User Preference | `USER_PREFERENCE` | 0% (override, not error) |

3. **Adjust Confidence Score**: Reduce algorithm confidence for the specific pattern
4. **Feed to Circuit Breaker** (P-20): Increment rollback counter
5. **Generate Monthly Rollback Report**: Total by category, trends, patterns, algorithm health
6. **Update Seasonal Profiles**: If categorized as SEASONAL, update user's seasonal awareness profile

**Outputs**: Updated confidence scores, circuit breaker data, monthly reports, improved algorithm accuracy over time

**Error Handling**:
- Uncategorized rollback: Default to `BUSINESS_EXCEPTION`; alert License Manager for proper classification

---

### 8.7 Rollback & Recovery Sub-Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ ROLLBACK & RECOVERY FLOW                                              │
└──────────────────────────────────────────────────────────────────────┘

 [User Reports Access Issue]
          │
          ├── Web App "Request Access Restore" (fastest)
          ├── Help Desk Ticket
          └── Email to License Manager
          │
          ▼
 ┌────────────────────┐
 │ P-09: CLASSIFY     │
 │ PRIORITY           │
 │ P1: 1hr | P2: 2hr  │
 │ P3: 4hr | P4: NBD  │
 └─────────┬──────────┘
           │
           ▼
 ┌────────────────────┐     ┌────────────────────┐
 │ P-18: TEMPORARY    │────>│ P-14: NOTIFY       │
 │ LICENSE ELEVATION  │     │ User + stakeholders │
 │ (immediate, auto)  │     └────────────────────┘
 └─────────┬──────────┘
           │
           ├──────────────────────────────────────┐
           │                                      │
           ▼                                      ▼
 ┌────────────────────┐              ┌────────────────────┐
 │ P-17: ESCALATION   │              │ INVESTIGATION      │
 │ Tier 0 → 1 → 2 → 3│              │ (parallel)         │
 │ (auto-timeout)     │              │ Root cause         │
 └─────────┬──────────┘              │ analysis           │
           │                         └─────────┬──────────┘
           ▼                                   │
 ┌────────────────────┐                        │
 │ RESOLUTION:        │◄───────────────────────┘
 │ ┌────────────────┐ │
 │ │ Permanent      │ │     ┌────────────────────┐
 │ │ Restore        │ │────>│ P-21: FEEDBACK     │
 │ └────────────────┘ │     │ LOOP               │
 │ ┌────────────────┐ │     │ - Classify category│
 │ │ Confirmed      │ │────>│ - Adjust confidence│
 │ │ Downgrade      │ │     │ - Update profiles  │
 │ └────────────────┘ │     └─────────┬──────────┘
 └────────────────────┘               │
                                      ▼
                           ┌────────────────────┐
                           │ P-20: CIRCUIT      │
                           │ BREAKER CHECK      │
                           │ 3+ rollbacks =     │
                           │ auto-disable       │
                           └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │ FEEDBACK TO        │
                           │ PHASE 2 ALGORITHMS │
                           │ (improved accuracy)│
                           └────────────────────┘
```

---

## 9. Web Application Processes (Cross-Cutting)

### 9.1 P-11: Dashboard Rendering & Refresh

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-11 |
| **Trigger** | Event-Based (user navigates to dashboard, data refresh event) |
| **Actors** | Web Application, Azure AI Agent (API Layer) |
| **Inputs** | Current recommendations, algorithm results, monitoring data |
| **Source Docs** | [14](./14-Web-Application-Requirements.md) |

**Actions**:

1. **Render Dashboards** (4 primary dashboards):
   - Executive Summary: Key metrics, cost trends, top opportunities, alerts
   - License Optimization: Recommendations table, filters, bulk actions
   - Security & Compliance: SoD violations, compliance scorecard, security events
   - Read-Only User Analysis: Detailed read-only user detection with distribution charts

2. **Real-Time Updates**: WebSocket connection for live data:
   - `analysis.progress`: Algorithm execution progress
   - `recommendation.generated`: New recommendation created
   - `alert.triggered`: Security alert
   - `report.completed`: Scheduled report ready

3. **Data Freshness**: Dashboard data < 24 hours old; real-time alerts < 1 minute

**Outputs**: Rendered dashboards visible to authenticated users per RBAC

---

### 9.2 P-12: Recommendation Review & Action

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-12 |
| **Trigger** | Manual (user navigates to Recommendations section) |
| **Actors** | D365 System Administrator, Security Officer, Line Manager |
| **Inputs** | Recommendation list from P-04 |
| **Source Docs** | [14](./14-Web-Application-Requirements.md), [16](./16-Rollback-Fast-Restore-Procedures.md) |

**Actions**:

1. **Browse Recommendations**: Filter by status, type, confidence, department
2. **View Detail**: Expand recommendation for user details, options, business impact
3. **Take Action**: Approve, Reject (with reason), Defer, Request More Info
4. **Bulk Actions**: Select multiple, approve/reject/export selected
5. **Self-Service Restore**: End users access "Request Access Restore" button
6. **Manager Dashboard**: Line managers review team optimizations, request team freeze

**Outputs**: Approved/rejected recommendations flow to P-06; restore requests flow to P-18

---

### 9.3 P-13: Report Generation & Distribution

| Attribute | Detail |
|-----------|--------|
| **Process ID** | P-13 |
| **Trigger** | Scheduled (daily/weekly/monthly) + Manual (on-demand request) |
| **Actors** | Web Application, Azure AI Agent, D365 Admin, Security Officer, CFO |
| **Inputs** | All algorithm results, monitoring data, rollback data |
| **Source Docs** | [14](./14-Web-Application-Requirements.md) |

**Actions**:

1. **Generate Reports** (4 report types):

| Report | Audience | Frequency | Format |
|--------|----------|-----------|--------|
| License Cost Optimization | CIO, Finance | Monthly | PDF, Excel, CSV |
| Security Compliance (SOX/GDPR/ISO) | Security Officer, Auditors | Weekly + on-demand | PDF, CSV, Excel |
| User Activity Analysis | Admin, Security, Managers | Monthly | PDF, Excel, CSV |
| Trend Analysis & Forecasting | CIO, Finance, IT Management | Monthly | PDF, Excel, Interactive |

2. **Distribute**: Auto-email to configured recipients on schedule
3. **Store**: Archive in report library with version history and access control
4. **Custom Reports**: Users can configure custom parameters, filters, sections

**Outputs**: Generated reports distributed and archived

---

### 9.4 Web Application Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ WEB APPLICATION — CROSS-CUTTING INTERACTIONS                          │
└──────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   WEB APPLICATION   │
                    │  (P-11, P-12, P-13) │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │ Phase 1:     │    │ Phase 2:     │    │ Phase 3:     │
 │ Data Status  │    │ Algorithm    │    │ Approval     │
 │ & Quality    │    │ Results &    │    │ Workflow     │
 │ Indicators   │    │ Recommen-    │    │ Interface    │
 │              │    │ dations      │    │              │
 └──────────────┘    └──────────────┘    └──────────────┘
         │                     │                     │
         ▼                     ▼                     ▼
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │ Phase 4:     │    │ Phase 5:     │    │ Config &     │
 │ Change       │    │ Monitoring,  │    │ Admin        │
 │ Status &     │    │ Rollback,    │    │ Settings     │
 │ Notifications│    │ Feedback     │    │ (P-16)       │
 └──────────────┘    └──────────────┘    └──────────────┘

 ROLES & ACCESS:
 ┌───────────────────────────────────────────────────────┐
 │ Viewer:  Dashboards, Reports (read-only)              │
 │ Analyst: + Create recommendations, export             │
 │ Admin:   + Approve, configure, manage users           │
 └───────────────────────────────────────────────────────┘
```

### 9.4 P-22: New User License Suggestion ⭐ NEW

**Trigger**: Manual (admin initiates via Web App) or Event (role assignment on new user)
**Algorithm**: 4.7 (New User License Recommendation Engine)
**Source**: Doc 05 (Capability 5), Doc 07 (Algorithm 4.7), Doc 14 (New User Wizard), Doc 15 (SoD cross-validation)

**Process Flow**:

| Step | Actor | Action | System Response | Output |
|------|-------|--------|----------------|--------|
| 1 | Admin | Opens New User License Wizard in Web App | Loads searchable menu item catalog | Wizard screen |
| 2 | Admin | Selects required menu items for the new user | System caches selections | Menu item list |
| 3 | Admin | Clicks "Get Recommendations" | System calls `POST /api/v1/suggest-license` | API request |
| 4 | Agent | Builds reverse-index (if not cached) from Security Config | One-time computation from 700K records | Cached index |
| 5 | Agent | Runs greedy set-covering to find minimum role combinations | Greedy approximation, up to 10 candidates | Role sets |
| 6 | Agent | For each role set, calculates license via Algorithm 1.1 | Reuses existing license composition logic | License types |
| 7 | Agent | Cross-validates each role set against SoD matrix (Algorithm 3.1) | Flags conflicting role combinations | SoD warnings |
| 8 | Agent | Ranks by cost (ASC), role count (ASC), SoD conflicts (ASC) | Top-3 recommendations returned | Ranked list |
| 9 | Web App | Displays top-3 recommendations with cost, roles, SoD status | Interactive table with expand/details | Wizard results |
| 10 | Admin | Selects a recommendation and applies (or exports for approval) | Role assignment initiated or PDF generated | Action taken |

**Safeguard**: All recommendations flagged as "Theoretical — will be validated after 30 days of actual usage data."

**Data Sources**: Security Configuration (existing), License Pricing Table (existing), SoD Conflict Matrix (existing)

**Error Handling**:
- If a menu item is not found in any role: Warning displayed, remaining items processed
- If no role combination covers all items: Partial coverage shown with gap list
- If all top-3 have SoD conflicts: Warning escalated, admin must acknowledge

---

## 10. Trigger Matrix

### 10.1 Scheduled Triggers

| Process | Schedule | Time Window | Scope | Duration |
|---------|----------|-------------|-------|----------|
| P-01 (Data Ingestion - Full) | Weekly | Sunday 2-6 AM | All data sources | 2-4 hours |
| P-01 (Data Ingestion - Delta) | Hourly | Continuous | Changed records | < 30 min |
| P-01 (Telemetry Streaming) | Continuous | 24/7 | All activity events | Ongoing |
| P-03 (Algorithm - Incremental) | Daily | 2-4 AM | Last 24h changes | ~30 min |
| P-03 (Algorithm - Full) | Weekly | Sunday 2-6 AM | All users | < 2 hours |
| P-13 (Compliance Report) | Monthly | 1st of month, 3 AM | All users | ~1 hour |
| P-13 (Trend Report) | Monthly | 15th of month, 3 AM | Historical | ~30 min |
| P-15 (SoD Scan) | Weekly | Sunday 6-7 AM | All user-role pairs | ~30 min |
| P-19 (Freeze Check) | Daily | Midnight | Calendar evaluation | < 1 min |

### 10.2 Event-Based Triggers

| Process | Event Source | Event | Response Time |
|---------|-------------|-------|---------------|
| P-01 | D365 FO | Security configuration change | < 15 min |
| P-01 | D365 FO | Role assignment change | < 15 min |
| P-06 | P-05 | Recommendation exits observation mode | On completion |
| P-07 | P-06 | Approval granted | < 1 hour |
| P-09 | End User | "Request Access Restore" clicked | Immediate |
| P-09 | Help Desk | Rollback ticket created | Immediate |
| P-11 | P-04 | New recommendation generated | < 1 min (WebSocket) |
| P-11 | P-15 | SoD violation detected | < 1 min (WebSocket) |
| P-14 | P-07 | License change executed | Within 1 business day |
| P-15 | D365 FO | Role assignment change | < 15 min |
| P-18 | End User | "Request Access Restore" clicked | Immediate (auto-grant) |

### 10.3 Manual Triggers

| Process | Actor | Action | Interface |
|---------|-------|--------|-----------|
| P-03 | D365 Admin | Run on-demand analysis | Web app "Run Analysis" button |
| P-09 | D365 Admin | Manual rollback | Web app or D365 FO console |
| P-12 | D365 Admin / Manager | Review recommendation | Web app Recommendations page |
| P-13 | D365 Admin / Security Officer | Generate on-demand report | Web app Reports section |
| P-16 | D365 Admin / License Manager | Change configuration | Web app Admin settings |
| P-18 | Help Desk | Grant manual elevation | Help desk system |

### 10.4 System-Automatic Triggers

| Process | Triggering Condition | Response |
|---------|---------------------|----------|
| P-02 | P-01 ingestion batch completes | Start normalization |
| P-04 | P-03 algorithm execution completes | Start recommendation generation |
| P-05 | New/updated algorithm deployed | Enter observation mode |
| P-08 | P-07 license change applied | Activate monitoring |
| P-10 | OData 429 response received | Apply exponential backoff |
| P-17 | SLA timeout exceeded | Escalate to next tier |
| P-20 | 3+ rollbacks for algorithm + pattern | Trip circuit breaker |
| P-21 | P-09 rollback completed | Capture and classify rollback data |

### 10.5 Cascade Triggers (Process-to-Process)

| Source Process | Triggers | Condition |
|---------------|----------|-----------|
| P-01 | P-02, P-10 | Data batch arrives; OData call made |
| P-02 | P-03 | Normalized data ready |
| P-03 | P-04, P-15 | Algorithm results ready |
| P-04 | P-05 | New recommendations generated |
| P-05 | P-06 | Observation period complete + accuracy met |
| P-06 | P-07 | Approval granted |
| P-07 | P-08, P-14 | License change applied |
| P-09 | P-17, P-18, P-21 | Rollback initiated |
| P-21 | P-20 | Rollback count incremented |
| P-20 | P-05 | Algorithm disabled; must re-enter observation |

---

## 11. Safeguard & Control Point Map

### 11.1 Pre-Execution Gates

| Gate # | Gate Name | Location | Threshold | Action on Failure |
|--------|-----------|----------|-----------|------------------|
| **1** | OData Capacity | P-01 / P-10 | Extraction < 10% of D365 FO API capacity | Throttle extraction, switch to off-peak |
| **2** | Data Quality | P-02 | Validation errors < 0.1% | Pause algorithm execution, alert admin |

### 11.2 In-Execution Controls

| Gate # | Gate Name | Location | Threshold | Action on Failure |
|--------|-----------|----------|-----------|------------------|
| **3** | Algorithm Confidence | P-03 / P-04 | Confidence > 0.70 for auto-approval | Route to manual review |
| **4** | Observation Accuracy | P-05 | True positive rate >= 95% | Block activation, extend observation |

### 11.3 Post-Execution Safeguards

| Gate # | Gate Name | Location | Threshold | Action on Failure |
|--------|-----------|----------|-----------|------------------|
| **5** | Period-End Freeze | P-06 / P-07 / P-19 | Not in freeze window | Block all optimization changes |
| **6** | Approval Authority | P-06 | Approver has correct RBAC role | Reject approval attempt |

### 11.4 Emergency Controls

| Gate # | Gate Name | Location | Threshold | Action on Failure |
|--------|-----------|----------|-----------|------------------|
| **7** | Circuit Breaker | P-07 / P-20 | < 3 rollbacks per algorithm + pattern in 90 days | Auto-disable algorithm for pattern |
| **8** | Post-Implementation Monitoring | P-08 | Monitoring confirmed active | Block change completion status |

### 11.5 Safeguard Chain Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ SAFEGUARD CHAIN: 8 GATES ON THE PIPELINE                             │
└──────────────────────────────────────────────────────────────────────┘

 DATA IN ──► [Gate 1: OData < 10%] ──► [Gate 2: Errors < 0.1%]
                                                 │
                                                 ▼
            ANALYSIS ──► [Gate 3: Confidence > 0.70]
                                                 │
                                                 ▼
          OBSERVATION ──► [Gate 4: Accuracy >= 95%]
                                                 │
                                                 ▼
            APPROVAL ──► [Gate 5: No Freeze] ──► [Gate 6: Authority OK]
                                                 │
                                                 ▼
        IMPLEMENTATION ──► [Gate 7: Circuit Breaker < 3 rollbacks]
                                                 │
                                                 ▼
          MONITORING ──► [Gate 8: Monitoring Active]
                                                 │
                                                 ▼
                                          CHANGE COMPLETE

 ┌──────────────────────────────────────────────────────────────────┐
 │ ANY gate failure = pipeline STOPS at that point.                  │
 │ Restores and rollbacks BYPASS gates 5 and 7 (never blocked).    │
 └──────────────────────────────────────────────────────────────────┘
```

---

## 12. Actor-Process RACI Matrix

**Legend**: **R** = Responsible (does the work), **A** = Accountable (owns the outcome), **C** = Consulted (provides input), **I** = Informed (notified of outcome)

| Process | Azure AI Agent | D365 FO System | D365 Admin | License Mgr | Security Officer | Help Desk | IT Mgmt | Line Manager | End User | CFO/Finance | Auditor |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **P-01** Data Ingestion | R/A | C | I | | | | | | | | |
| **P-02** Normalization | R/A | | I | | | | | | | | |
| **P-03** Algorithm Exec | R/A | | C | C | | | | | | | |
| **P-04** Recommendation Gen | R/A | | I | C | | | | | | | |
| **P-05** Observation Mode | R | A | I | A | | | | | | | |
| **P-06** Approval Workflow | | | R | A | C | | I | R | I | | |
| **P-07** License Change | R | | A | I | | | | | I | | |
| **P-08** Post-Impl Monitor | R/A | | I | I | | | | | | | |
| **P-09** Rollback/Restore | | | R | A | | R | I | I | R | | |
| **P-10** OData Throttling | R/A | C | I | | | | | | | | |
| **P-11** Dashboard Render | R | | | | | | | | | | |
| **P-12** Recommendation Review | | | R | C | R | | | R | R | | |
| **P-13** Report Generation | R | | C | I | C | | I | I | | I | C |
| **P-14** Notification | R | | I | I | | I | | I | I | | |
| **P-15** SoD Detection | R | | I | I | A | | I | | | | C |
| **P-16** Config Management | | | R | A | C | | I | | | | |
| **P-17** Escalation | R | | R | R | | R | A | | | | |
| **P-18** Temp Elevation | R | | R | I | | R | I | I | R | | |
| **P-19** Period-End Safeguard | R | | C | A | | | A (override) | C | | | |
| **P-20** Circuit Breaker | R/A | | I | R | | | I | | | | |
| **P-21** Feedback Loop | R | | I | A | | | I | | | | |

---

## 13. Process Dependencies & Data Flow

### 13.1 Dependency Graph

```
P-01 (Ingest) ──► P-02 (Normalize) ──► P-03 (Algorithms) ──► P-04 (Recommend)
     │                                        │                      │
     └── P-10 (Throttle)                      └── P-15 (SoD)        │
                                                                      ▼
                                              P-05 (Observe) ◄── P-04
                                                   │
                                                   ▼
                                              P-06 (Approve) ◄── P-19 (Freeze Check)
                                                   │
                                                   ▼
                                              P-07 (Execute) ──► P-08 (Monitor)
                                                   │               │
                                                   ├── P-14 (Notify)
                                                   │
                                                   ▼
                                              P-09 (Rollback) ──► P-21 (Feedback)
                                                   │                    │
                                                   ├── P-17 (Escalate)  └── P-20 (Breaker)
                                                   │                         │
                                                   └── P-18 (Elevate)       └──► P-05 (re-observe)

Cross-Cutting: P-11, P-12, P-13 interact with all phases via APIs
Configuration: P-16 feeds parameters to P-03, P-04, P-05, P-15, P-19
```

### 13.2 Key Data Objects Flowing Between Processes

| Data Object | Produced By | Consumed By | Description |
|------------|------------|------------|-------------|
| Raw Ingested Data | P-01 | P-02 | Unprocessed data from 4 sources |
| Normalized Data | P-02 | P-03, P-15 | Validated, enriched, aggregated data |
| Role License Compositions | P-03 (Alg 1.1) | P-03 (Algs 1.3, 1.4, 2.2-2.6) | Cached role-to-license mappings |
| Algorithm Results | P-03 | P-04 | Per-user/role optimization findings |
| SoD Violations | P-15 | P-11, P-13, P-06 | Detected conflict records |
| Recommendations | P-04 | P-05, P-06, P-11, P-12 | Prioritized recommendation list |
| Observation Report | P-05 | P-06 | Accuracy metrics and validation data |
| Approval Decision | P-06 | P-07 | Approved/rejected status |
| Change Record | P-07 | P-08, P-09, P-14 | License change details + rollback snapshot |
| Rollback Record | P-09 | P-21 | Rollback details with category |
| Confidence Adjustment | P-21 | P-03, P-04 | Updated algorithm confidence scores |
| Circuit Breaker State | P-20 | P-07 | Algorithm pattern enable/disable status |
| Freeze State | P-19 | P-06, P-07 | Active/inactive freeze status |
| Configuration | P-16 | P-03, P-04, P-05, P-15, P-19 | Algorithm parameters, pricing, schedules |

### 13.3 Critical Path Analysis

The **longest sequential chain** from data to confirmed value:

```
P-01 → P-02 → P-03 → P-04 → P-05 (30+ days) → P-06 → P-07 → P-08
                                    ▲
                              Bottleneck: Observation mode minimum 30 days
```

**Critical path duration**: 30-60 days (dominated by observation mode)

**Optimization opportunities**:
- Algorithms that have already passed observation can skip P-05 for subsequent runs
- Multiple algorithms can be in observation simultaneously
- On-demand analysis (P-03) bypasses scheduling delays

---

## 14. Error Handling & Recovery Flows

### 14.1 Data Ingestion Failures

| Failure Mode | Detection | Recovery Action | SLA |
|-------------|-----------|----------------|-----|
| OData endpoint unreachable | Connection timeout | Retry 3x with backoff → alert D365 Admin → use cached data | 30 min |
| 429 Too Many Requests | HTTP status code | Exponential backoff (P-10) → switch to off-peak | Automatic |
| Schema change in D365 FO | Validation errors spike | Pause ingestion → alert admin → update schema mapping | 4 hours |
| App Insights stream interruption | No events received for > 30 min | Alert admin → check Event Hub → failover to batch query | 1 hour |
| Data Lake Export failure | Export job error | Fallback to OData extraction → alert admin | 2 hours |

### 14.2 Algorithm Execution Failures

| Failure Mode | Detection | Recovery Action | SLA |
|-------------|-----------|----------------|-----|
| Single algorithm timeout | Execution exceeds expected time (2x normal) | Kill algorithm → log → continue pipeline with partial results | Automatic |
| Algorithm exception | Runtime error | Log stack trace → skip algorithm → alert License Manager | Automatic |
| Data staleness (> 24 hours) | Timestamp check | Flag all results as "stale" → run with warning → alert admin | 1 hour |
| Dependency failure | Prerequisite algorithm failed | Skip dependent algorithms → log → alert | Automatic |
| Memory exhaustion | Resource monitoring | Scale up compute → retry → alert if persistent | 30 min |

### 14.3 Implementation Failures

| Failure Mode | Detection | Recovery Action | SLA |
|-------------|-----------|----------------|-----|
| D365 FO license change API failure | API error response | Retry 3x → mark as "execution failed" → alert D365 Admin | 1 hour |
| User account deleted/disabled | User not found | Close recommendation → log as "user removed" | Automatic |
| Concurrent modification conflict | Version mismatch | Re-analyze user → generate new recommendation | 30 min |
| Rollback snapshot not found | Missing snapshot data | Escalate to D365 Admin → manual restore from D365 FO records | 2 hours |

### 14.4 Cascading Failure Protection

| Scenario | Safeguard | Response |
|----------|-----------|----------|
| Multiple algorithm failures in single run | Pipeline continues with partial results | Alert License Manager; do not generate recommendations from failed algorithms |
| Data quality degradation (> 0.1% errors) | Gate 2 blocks algorithm execution | Pause all analysis; investigate data source |
| High rollback rate (> 10% in a month) | Red threshold metric | Pause ALL active algorithms; full review required |
| Period-end + high volume of issues | Period-end freeze (P-19) | All changes blocked; restores continue |
| Circuit breaker tripped on multiple algorithms | Per-pattern disable | Only affected patterns disabled; other patterns continue |

---

## 15. Appendix

### 15.1 Process ID Reference Table

| ID | Process | Phase | Type | Primary Trigger |
|----|---------|-------|------|-----------------|
| P-01 | Data Ingestion & Sync | 1 | Core | Scheduled + Event |
| P-02 | Data Normalization & Validation | 1 | Core | Automatic |
| P-03 | Algorithm Execution Pipeline | 2 | Core | Scheduled + On-Demand |
| P-04 | Recommendation Generation | 2 | Core | Automatic |
| P-05 | Observation Mode (Shadow Mode) | 3 | Validation | Automatic |
| P-06 | Approval Workflow | 3 | Validation | Event |
| P-07 | License Change Execution | 4 | Core | Event |
| P-08 | Post-Implementation Monitoring | 5 | Monitoring | Automatic |
| P-09 | Rollback & Fast-Restore | 5 | Recovery | Event + Manual |
| P-10 | OData Throttling Management | 1 | Supporting | Automatic |
| P-11 | Dashboard Rendering & Refresh | Web App | Cross-Cutting | Event |
| P-12 | Recommendation Review & Action | Web App | Cross-Cutting | Manual |
| P-13 | Report Generation & Distribution | Web App | Cross-Cutting | Scheduled + Manual |
| P-14 | User Notification & Communication | 4 | Supporting | Event |
| P-15 | SoD Violation Detection & Workflow | 2 | Compliance | Scheduled + Event |
| P-16 | Configuration Management | 4 | Supporting | Manual |
| P-17 | Escalation Management | 5 | Recovery | Automatic |
| P-18 | Temporary License Elevation | 5 | Recovery | Event + Manual |
| P-19 | Period-End Safeguard | 3 | Validation | Scheduled |
| P-20 | Circuit Breaker & Auto-Disable | 5 | Safety | Automatic |
| P-21 | Rollback Tracking & Feedback Loop | 5 | Analytics | Automatic |

### 15.2 Document Cross-Reference Index

| Section in This Document | References Documents |
|-------------------------|---------------------|
| Phase 1: Data Acquisition (Sec 4) | 01, 02, 03, 04, 13 |
| Phase 2: Analysis (Sec 5) | 05, 06, 07, 08, 09, 10, 11, 12, 13, 15 |
| Phase 3: Validation (Sec 6) | 05, 14, 16 |
| Phase 4: Implementation (Sec 7) | 05, 06, 13, 14, 15, 16 |
| Phase 5: Monitoring (Sec 8) | 13, 16 |
| Web App (Sec 9) | 14 |
| Trigger Matrix (Sec 10) | 06, 07, 13, 14, 16 |
| Safeguards (Sec 11) | 13, 15, 16 |
| RACI (Sec 12) | All (05, 13, 14, 16 primarily) |
| Dependencies (Sec 13) | All |
| Error Handling (Sec 14) | 13, 16 |

### 15.3 Glossary

| Term | Definition |
|------|-----------|
| **Algorithm** | A defined analysis routine that processes D365 FO data to produce optimization or security recommendations |
| **Circuit Breaker** | Automatic safety mechanism that disables an algorithm pattern after 3+ rollbacks in 90 days |
| **Confidence Score** | Numeric value (0.0-1.0) indicating the reliability of a recommendation; HIGH > 0.80, MEDIUM 0.60-0.80, LOW < 0.60 |
| **Delta Sync** | Incremental data synchronization that retrieves only changed records since last sync |
| **Effective License Cost** | The customer's actual license cost (negotiated EA/CSP rate if configured, otherwise Microsoft list price) |
| **Freeze Window** | Calendar period during which all optimization changes are blocked (month-end, quarter-end, year-end, audit) |
| **Observation Mode** | Mandatory validation phase where algorithms generate recommendations without executing them (minimum 30 days) |
| **OData** | Open Data Protocol used for D365 FO API data extraction |
| **RACI** | Responsibility matrix: Responsible, Accountable, Consulted, Informed |
| **Rollback** | Reversal of a license optimization change, restoring user to pre-change state |
| **SoD** | Separation of Duties — internal control preventing one person from controlling all phases of a transaction |
| **Temporary Elevation** | Time-limited restoration of a user's previous license (max 30 days) while investigation occurs |

---

## Document Status

| Item | Status |
|------|--------|
| Purpose & Reading Guide | Complete |
| Process Inventory (22 processes) | Complete |
| Agent Lifecycle Diagram | Complete |
| Phase 1: Data Acquisition (P-01, P-02, P-10) | Complete |
| Phase 2: Analysis & Recommendation (P-03, P-04, P-15) | Complete |
| Phase 3: Validation & Approval (P-05, P-06, P-19) | Complete |
| Phase 4: Implementation & Communication (P-07, P-14, P-16) | Complete |
| Phase 5: Monitoring & Improvement (P-08, P-09, P-17, P-18, P-20, P-21) | Complete |
| Web Application Processes (P-11, P-12, P-13) | Complete |
| Trigger Matrix (5 tables) | Complete |
| Safeguard & Control Point Map (8 gates) | Complete |
| RACI Matrix (21 x 11 actors) | Complete |
| Process Dependencies & Data Flow | Complete |
| Error Handling & Recovery Flows | Complete |
| Appendix (reference, cross-ref, glossary) | Complete |

---

**Dependencies**:
- All 16 prior requirements documents (01-16)
- No new requirements introduced — this document synthesizes existing specifications

**Next Steps**:
1. Review process flow with development team for technical feasibility
2. Validate trigger schedules with D365 FO system administrators
3. Confirm RACI assignments with organizational stakeholders
4. Use this document as the integration test blueprint during Phase 1 development

---

**End of Agent Process Flow Document**
