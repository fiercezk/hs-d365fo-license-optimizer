# Tech Stack Recommendation - D365 FO License & Security Optimization Agent

**Project**: D365 FO License & Security Optimization Agent
**Component**: Tech Stack Recommendation
**Last Updated**: February 6, 2026
**Status**: Technical Advisory (Informational Only — No Scope Changes)
**Version**: 1.0
**Category**: Technical Design
**Key Factors**: Cost + Performance

---

## Table of Contents

1. [Context](#1-context)
2. [First Principles: Does This Project Need LLM Compute?](#2-first-principles-does-this-project-need-llm-compute)
3. [Recommended Tech Stack](#3-recommended-tech-stack)
4. [Complete Cost Model](#4-complete-cost-model)
5. [Performance Validation Against SLA Targets](#5-performance-validation-against-sla-targets)
6. [Tech Stack Diagram](#6-tech-stack-diagram)
7. [Key Decisions Summary](#7-key-decisions-summary)
8. [Risk Callouts](#8-risk-callouts)

---

## 1. Context

The architecture docs (13, 14) define *what* the system does and its performance targets, but leave specific service selections open for the technical design phase. This document recommends a concrete tech stack optimized for **cost** and **performance**, with clear tier progression from MVP to scale.

### Already Committed (Not Revisited Here)

- Azure cloud platform
- Azure AD / Entra ID for authentication
- X++ custom telemetry → Azure Application Insights
- OData for D365 FO data extraction
- 34 algorithms (11 Phase 1), deterministic logic
- REST API with defined endpoints
- CI/CD via Azure DevOps

### Open Decisions (Addressed Below)

- Compute platform (API + batch processing)
- Database
- Frontend framework + hosting
- AI/Agent framework (do we actually need LLM compute?)
- API management
- Event streaming / messaging
- Orchestration & scheduling
- Caching layer
- Cost model at each scale tier

---

## 2. First Principles: Does This Project Need LLM Compute?

The docs specify "Azure AI Foundry + Azure AI Agent Service" as the agent framework. But let's examine what the algorithms actually do:

| Algorithm | Computation Type | Needs LLM? |
|-----------|-----------------|-------------|
| 2.2 Read-Only User Detector | Threshold comparison (read % > 95%) | No |
| 2.5 License Minority Detection | Set analysis + cost comparison | No |
| 1.4 Component Removal Recommender | Unused privilege identification | No |
| 2.6 Cross-Role License Optimization | Graph analysis + set covering | No |
| 1.3 Role Splitting Recommender | Cluster analysis | No |
| 3.1 SoD Violation Detector | Matrix rule matching | No |
| 4.7 New User License Recommendation | Greedy set-covering approximation | No |
| 4.4 License Trend Analysis | Time-series statistics | No |

**All 11 Phase 1 algorithms are deterministic.** They use thresholds, set operations, and statistical computations — not natural language processing or reasoning.

### Where an LLM *Could* Add Value

| Use Case | Value | Phase |
|----------|-------|-------|
| Natural language recommendation explanations | Medium — more readable than templates | Phase 2 |
| Conversational query interface ("show me users who...") | High — better UX | Phase 2 |
| Anomaly description generation | Low — structured alerts work fine | Phase 2+ |
| Report narrative generation | Medium — polished executive summaries | Phase 2 |

### Decision: Full AI Agent Service from Day 1

Use **Azure AI Foundry + Azure AI Agent Service** as the agent framework, aligning with the "AI Agent" product positioning.

**Architecture approach**:

- **Azure AI Foundry** — model hosting, prompt management, evaluation
- **Azure AI Agent Service** — agent orchestration, tool calling, state management
- **Azure OpenAI Service** — GPT-4o / GPT-4o-mini for recommendation explanations, report narratives, and conversational interface
- **Algorithm execution remains deterministic** — the LLM generates human-readable explanations and handles conversational queries, but never makes license decisions autonomously
- **Agent tools** — each algorithm is registered as a "tool" the agent can invoke, maintaining the deterministic core with AI-powered UX

**Cost implications**: Adds ~$150-400/month depending on volume (GPT-4o-mini for bulk explanations, GPT-4o for complex conversational queries).

**Performance consideration**: LLM calls are async and non-blocking for batch operations. For interactive queries, response time target is <5s including LLM generation.

---

## 3. Recommended Tech Stack

### Layer 1: Frontend + Hosting

| Decision | Recommendation | Why |
|----------|---------------|-----|
| **Framework** | **Next.js 15 (App Router)** | SSR for dashboards, API routes for BFF pattern, React ecosystem |
| **UI Library** | **shadcn/ui + Tailwind CSS** | Free, tree-shakable, smaller bundle than Material-UI (MUI adds ~200KB) |
| **Charts** | **Recharts** (or Tremor for dashboard components) | React-native, lighter than D3.js for standard charts |
| **State** | **TanStack Query (React Query)** | Server-state management, caching, auto-refetch — eliminates need for Redux in most cases |
| **Hosting** | **Azure Static Web Apps (Free tier)** | 100GB bandwidth/month, custom domains, integrated Azure AD auth, global CDN |

**Cost: $0/month** (Free tier handles up to ~100 concurrent users easily)

**Why not Material-UI?** MUI adds ~200KB to bundle size and has a learning curve. shadcn/ui gives you the same components as copy-paste code (not a dependency), fully customizable, and works with Tailwind which is already best-in-class for responsive design. For a dashboard-heavy app, bundle size directly impacts the <3s page load target.

**Why not Angular/Vue?** React has the largest ecosystem for dashboard components, charting libraries, and Azure integration tooling. Next.js provides SSR which is critical for initial dashboard render performance.

### Layer 2: API Backend

| Decision | Recommendation | Why |
|----------|---------------|-----|
| **Runtime** | **Node.js 22 (LTS) + TypeScript** | Fast startup, excellent Azure Functions support, shared language with frontend |
| **Framework** | **Azure Functions (Node.js)** | Serverless, pay-per-execution, built-in Azure AD integration |
| **Plan** | **Flex Consumption** | Scale to zero, no cold start penalty (pre-provisioned instances), pay-per-use |
| **API Layer** | **Azure Functions HTTP triggers** | Maps 1:1 to the defined REST endpoints |

**Alternative considered**: Azure App Service B1 ($55/month) — simpler but always-on cost even when idle.

**Why Functions Flex Consumption over Premium?**

- Flex Consumption: ~$0.20/million executions + compute seconds. At typical Phase 1 volume (50 users, ~10K API calls/month), this costs **<$5/month**
- Premium EP1: $170/month flat — makes sense only at sustained high volume
- Flex Consumption has pre-provisioned instances (eliminates cold starts) without the Premium price tag

**Cost: ~$5-20/month** (scales with usage)

### Layer 3: Batch Processing (Algorithm Execution)

| Decision | Recommendation | Why |
|----------|---------------|-----|
| **Compute** | **Azure Container Apps (Jobs)** | Scale to zero, supports long-running (2hr+ batch), no cluster to manage |
| **Language** | **Python 3.12** | Best ecosystem for data analysis (pandas, numpy), algorithm implementation |
| **Scheduling** | **Azure Container Apps Job triggers** (cron-based) | Built-in cron scheduling, no separate scheduler needed |
| **Orchestration** | **Prefect** or **Azure Durable Functions** | Fan-out/fan-in for parallel algorithm execution |

**Why Container Apps over AKS?**

- AKS: ~$70/month minimum (cluster management fee) + node costs. Requires Kubernetes expertise.
- Container Apps: $0/month when idle. Pay only for actual compute: ~$0.000012/vCPU-second.
- A 2-hour batch job with 4 vCPUs = **~$0.35 per run**. Daily = ~$10/month.

**Why Container Apps over Azure Functions for batch?**

- Functions have a 10-minute timeout (Consumption) or 60-minute (Premium/Flex)
- Full org batch for 10K users targets <2 hours — Functions can't handle this
- Container Apps Jobs have no timeout limit

**Why Python for algorithms, not TypeScript?**

- pandas/numpy are 10-100x faster than JS equivalents for data manipulation
- Algorithm pseudocode in the docs maps naturally to Python
- Data science ecosystem (scipy for statistics, networkx for graph analysis in role optimization)
- The API layer (TypeScript) calls the batch engine via Container Apps Job API — clean separation

**Cost: ~$10-30/month** (depends on frequency and org size)

### Layer 4: Database

| Decision | Recommendation | Why |
|----------|---------------|-----|
| **Primary DB** | **Azure SQL Database (Serverless, General Purpose)** | Auto-pause, auto-scale, T-SQL familiar to D365 FO teams |
| **Tier** | **Serverless (0.5-4 vCores, auto-pause after 1hr)** | Costs $0 when paused, scales up on demand |
| **Storage** | **32GB initial** (auto-grows) | Sufficient for Phase 1 |

**Why Azure SQL Serverless over PostgreSQL Flexible?**

- **D365 FO ecosystem alignment**: D365 FO runs on SQL Server. Same T-SQL dialect, same tooling, same team skills
- **Auto-pause**: PostgreSQL Flexible doesn't auto-pause. Azure SQL Serverless pauses after inactivity = $0 during off-hours
- **Cost comparison at low usage**:
  - Azure SQL Serverless: ~$5-30/month (auto-pause reduces to near-zero during dev/test)
  - PostgreSQL Flexible Burstable B1ms: ~$13/month flat (always on)
- **Built-in**: Row-level security, temporal tables (for audit history), columnstore indexes (for analytics queries)

**Why not Cosmos DB?**

- Data is relational (users → roles → security objects → licenses)
- Cosmos DB minimum: $24/month for 400 RU/s
- No benefit for this workload pattern — the queries are relational joins, not document lookups

**Cost: ~$5-30/month** (auto-pause keeps dev/test near-zero)

### Layer 5: Caching

| Decision | Recommendation | Why |
|----------|---------------|-----|
| **Cache** | **Azure Cache for Redis (Basic C0)** | Dashboard data caching, algorithm result caching |
| **Tier** | **Basic C0** | 250MB, sufficient for Phase 1 dashboard cache |

**Why Redis?**

- Dashboard queries (user lists, recommendation summaries) are read-heavy and repeated
- Cache algorithm results (refreshed daily) to serve dashboards in <100ms
- Reduces database load by 80%+ for dashboard queries

**Alternative**: Skip Redis entirely and use Next.js ISR (Incremental Static Regeneration) + TanStack Query client cache. This is **free** and sufficient if dashboard latency of 1-2s (from DB) is acceptable.

**Recommendation: Skip Redis for Phase 1.** Use Next.js ISR + TanStack Query stale-while-revalidate pattern. Add Redis when dashboard response time needs to drop below 500ms.

**Cost: $0/month** (Phase 1), **~$55/month** (Phase 2 if needed)

### Layer 6: API Management

**Recommendation: Skip Azure API Management for Phase 1.**

| What APIM Provides | Phase 1 Alternative | Cost Saved |
|--------------------|---------------------|------------|
| Rate limiting | `express-rate-limit` middleware (npm) | $0 |
| Auth | Azure AD middleware (built-in to Functions) | $0 |
| API versioning | URL path routing (`/api/v1/...`) | $0 |
| Request logging | Application Insights (already have it) | $0 |
| Developer portal | Swagger/OpenAPI auto-gen | $0 |

APIM Developer tier: $50/month. Standard: $700/month. **Not justified until you have external API consumers or multi-tenant requirements.**

**Cost: $0/month** (Phase 1)

### Layer 7: Event Streaming

**Recommendation: Skip Event Hubs for Phase 1.**

The telemetry data is already in Application Insights. For algorithm execution:

- Query App Insights via **Log Analytics REST API** (Kusto queries) during scheduled batch runs
- App Insights data retention: 90 days default (configurable to 730 days)
- Kusto queries can aggregate millions of events in seconds

For real-time anomaly detection (Algorithm 5.3 — after-hours monitoring):

- Use **App Insights Alerts** (built-in) with custom KQL queries
- Fires an Azure Function when anomaly detected
- No separate streaming infrastructure needed

**Add Event Hubs only if**: Sub-minute anomaly detection latency is required AND App Insights Alerts (5-min evaluation window) is too slow.

**Cost: $0/month** (Phase 1)

### Layer 8: AI Agent Layer

| Decision | Recommendation | Why |
|----------|---------------|-----|
| **Agent Platform** | **Azure AI Foundry + Azure AI Agent Service** | Full agent orchestration with tool calling, state management, evaluation |
| **Primary Model** | **GPT-4o-mini** (bulk operations) | $0.15/1M input, $0.60/1M output — cost-effective for recommendation explanations |
| **Complex Queries** | **GPT-4o** (conversational interface) | Higher quality for interactive user queries |
| **Prompt Management** | **Azure AI Foundry Prompt Flow** | Version-controlled prompts, A/B testing, evaluation metrics |
| **Agent Tools** | Each algorithm registered as a callable tool | Agent invokes deterministic algorithms, then explains results in natural language |

**How the agent works**:

```
User Query → Azure AI Agent Service
                    │
                    ├── Tool Call: algorithm_2_2(user_id) → deterministic result
                    ├── Tool Call: get_user_roles(user_id) → database lookup
                    ├── Tool Call: get_usage_stats(user_id) → App Insights query
                    │
                    └── GPT-4o-mini: Generate natural language explanation
                              │
                              ▼
                    "John Doe has been 99.76% read-only for the past 90 days.
                     His 2 write operations were self-service profile updates.
                     Recommendation: Downgrade from Commerce ($180/mo) to
                     Team Members ($60/mo). Estimated annual savings: $1,440."
```

**Batch mode** (scheduled runs): Agent orchestrates algorithm execution across all users, generates per-user explanations in bulk using GPT-4o-mini. Cost at scale:

- 10K users × ~500 tokens/explanation = 5M tokens/batch
- GPT-4o-mini: ~$3 per full-org batch run
- Daily runs: ~$90/month

**Interactive mode** (dashboard/conversational): User asks questions like "show me users in Finance who could be downgraded." Agent translates to algorithm calls + database queries, returns natural language response.

- GPT-4o: ~$2.50/1M input, $10/1M output
- Estimated: 5K interactive queries/month = ~$50-100/month

**Cost: ~$150-300/month** (batch + interactive combined)

### Layer 9: Infrastructure & DevOps

| Decision | Recommendation | Why |
|----------|---------------|-----|
| **IaC** | **Bicep** (not Terraform) | Native Azure, no state file management, free, simpler for Azure-only deployments |
| **CI/CD** | **Azure DevOps Pipelines** | Free tier: 1 parallel job, 1800 min/month. Sufficient for Phase 1 |
| **Container Registry** | **Azure Container Registry (Basic)** | $5/month, 10GB storage. For Container Apps images |
| **Monitoring** | **Azure Monitor + App Insights** (already committed) | $0 additional |
| **Secrets** | **Azure Key Vault** | ~$0.03/10K operations. Effectively free |

**Why Bicep over Terraform?**

- Zero cost (Terraform Cloud: $0 for <500 resources but adds complexity)
- No state file to manage (Bicep deploys are idempotent via ARM)
- Better Azure-native type safety and IntelliSense
- Simpler syntax for Azure resources
- Team only needs to learn one cloud (Azure), not a meta-tool

**Cost: ~$5/month** (Container Registry only)

---

## 4. Complete Cost Model

### Tier 1: Development / MVP (Phase 1, Weeks 1-7)

| Component | Service | Monthly Cost |
|-----------|---------|-------------|
| Frontend | Azure Static Web Apps (Free) | $0 |
| API Backend | Azure Functions Flex Consumption | $5-10 |
| Batch Engine | Azure Container Apps Jobs | $5-15 |
| Database | Azure SQL Serverless (auto-pause) | $5-15 |
| AI Agent | Azure AI Foundry + OpenAI (GPT-4o-mini) | $50-100 |
| Telemetry | App Insights (existing D365 FO) | $0* |
| Auth | Azure AD (existing M365) | $0 |
| Secrets | Azure Key Vault | ~$0 |
| Container Registry | ACR Basic | $5 |
| CI/CD | Azure DevOps (Free tier) | $0 |
| Monitoring | Azure Monitor (included) | $0 |
| **TOTAL** | | **~$70-145/month** |

*App Insights costs typically absorbed by existing D365 FO subscription. If dedicated workspace, ~$2.76/GB ingested after 5GB free.

### Tier 2: Production (Phase 1 Complete, ~50 users)

| Component | Service | Monthly Cost |
|-----------|---------|-------------|
| Frontend | Azure Static Web Apps (Standard) | $9 |
| API Backend | Azure Functions Flex Consumption | $10-30 |
| Batch Engine | Azure Container Apps Jobs (daily runs) | $15-40 |
| Database | Azure SQL Serverless (2 vCore peak) | $30-75 |
| AI Agent | Azure AI Foundry + OpenAI (batch + interactive) | $150-300 |
| Cache | Next.js ISR + TanStack Query | $0 |
| Monitoring | Azure Monitor + alerts | $10-20 |
| Key Vault + ACR | Standard usage | $10 |
| **TOTAL** | | **~$235-485/month** |

### Tier 3: Scale (Phase 2+, 500+ users, 10K+ D365 FO users analyzed)

| Component | Service | Monthly Cost |
|-----------|---------|-------------|
| Frontend | Azure Static Web Apps (Standard) | $9 |
| API Backend | Azure Functions Flex Consumption | $30-80 |
| Batch Engine | Container Apps (parallel algorithm execution) | $40-100 |
| Database | Azure SQL Serverless (4 vCore peak) | $100-200 |
| AI Agent | Azure AI Foundry + OpenAI (GPT-4o + 4o-mini) | $250-500 |
| Cache | Azure Cache for Redis (Basic C0) | $55 |
| API Management | APIM Consumption tier | $15-50 |
| Event Hubs | Basic (if real-time needed) | $11 |
| Monitoring | Full Azure Monitor suite | $30-50 |
| **TOTAL** | | **~$540-1,055/month** |

### Tier 4: Enterprise (10K+ D365 FO users, multiple orgs)

| Component | Service | Monthly Cost |
|-----------|---------|-------------|
| All Tier 3 components | Scaled up | $750-1,500 |
| Database | Azure SQL Hyperscale | $200-500 |
| AI Agent | Azure OpenAI (Provisioned Throughput) | $400-800 |
| APIM | Standard (multi-tenant) | $700 |
| Premium Functions | For guaranteed latency | $170 |
| **TOTAL** | | **~$2,200-3,700/month** |

---

## 5. Performance Validation Against SLA Targets

| SLA Target | Stack Component | How It Meets Target |
|------------|----------------|-------------------|
| API Response < 2s (p95) | Functions Flex (pre-provisioned) + SQL Serverless | Pre-warmed instances eliminate cold starts; SQL auto-scales on demand |
| Dashboard Load < 5s | Next.js SSR + ISR + TanStack Query cache | Initial SSR render in <2s, subsequent loads from cache in <500ms |
| Page Load < 3s | Static Web Apps CDN + shadcn/ui (small bundle) | Global CDN, ~50KB JS bundle (vs ~250KB with MUI) |
| Batch < 2hr (10K users) | Container Apps (4 vCPU) + Python pandas | Parallel algorithm execution with fan-out; pandas handles 700K security records in seconds |
| Data Freshness < 15min | App Insights Alerts + Functions triggers | KQL alert evaluates every 5 minutes, triggers Function on match |
| 50+ concurrent users | Functions auto-scale + SQL auto-scale | Both scale horizontally on demand |
| 99.5% uptime | Azure SLAs (Functions 99.95%, SQL 99.99%) | Exceeds target individually |
| Export < 1min (10K rows) | Streaming CSV/Excel generation | Server-side generation, no client memory constraints |

---

## 6. Tech Stack Diagram

```
                    ┌──────────────────────────────────┐
                    │         End Users (Browser)        │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │    Azure Static Web Apps (CDN)     │
                    │    Next.js 15 + shadcn/ui          │
                    │    TanStack Query (client cache)   │
                    └──────────────┬───────────────────┘
                                   │ HTTPS
                    ┌──────────────▼───────────────────┐
                    │    Azure Functions (Flex)           │
                    │    TypeScript API Layer             │
                    │    /api/v1/* endpoints              │
                    │    Azure AD auth middleware         │
                    └───┬──────────┬───────────────────┘
                        │          │
              ┌─────────▼──┐  ┌────▼──────────────────────┐
              │ Azure SQL   │  │  Azure AI Agent Service    │
              │ Serverless  │  │  ┌─────────────────────┐  │
              │ (data store)│  │  │ Azure AI Foundry     │  │
              │             │  │  │ GPT-4o / GPT-4o-mini │  │
              └──────▲──────┘  │  │ Prompt Flow          │  │
                     │         │  └──────────┬──────────┘  │
                     │         │             │ tool calls   │
                     │         │  ┌──────────▼──────────┐  │
                     │         │  │ Algorithm Tools      │  │
                     │         │  │ (11 deterministic)   │  │
                     │         │  └──────────────────────┘  │
                     │         └────┬──────────────────────┘
                     │              │
                     │       ┌──────▼──────────────┐
                     └───────│ Container Apps Jobs  │
                             │ Python 3.12          │
                             │ Batch Algorithm      │
                             │ Engine               │
                             └──────┬──────────────┘
                                    │ Kusto REST API
                          ┌─────────▼──────────────┐
                          │  Application Insights    │
                          │  (telemetry data store)  │
                          └─────────▲──────────────┘
                                    │ TrackEvent()
                          ┌─────────┴──────────────┐
                          │  D365 FO (X++ CoC)       │
                          │  FormRun + FormDataSource │
                          │  TelemetryLogger          │
                          └────────────────────────┘
```

---

## 7. Key Decisions Summary

| Layer | Recommendation | Monthly Cost (Phase 1) | Rationale |
|-------|---------------|----------------------|-----------|
| Frontend | Next.js + shadcn/ui on Static Web Apps | $0 | Free tier, fast, small bundle |
| API | Azure Functions Flex Consumption (TS) | $5-10 | Pay-per-use, no cold starts |
| Batch | Azure Container Apps Jobs (Python) | $5-15 | Scale to zero, no timeout limit |
| Database | Azure SQL Serverless | $5-15 | Auto-pause, D365 ecosystem fit |
| AI Agent | Azure AI Foundry + OpenAI (GPT-4o-mini) | $50-100 | Full agent service, tool calling, NL explanations |
| Cache | Next.js ISR + TanStack Query | $0 | Free, sufficient for Phase 1 |
| APIM | Skip for Phase 1 | $0 | Middleware handles auth + rate limiting |
| Events | Skip — query App Insights directly | $0 | Data already there, no separate stream |
| IaC | Bicep | $0 | Azure-native, no state management |
| CI/CD | Azure DevOps Free | $0 | 1800 min/month sufficient |
| **TOTAL** | | **~$70-145/month** | |

**Phase 1 all-in cost: ~$70-145/month.** Azure's serverless/consumption tiers keep infrastructure costs minimal; the AI Agent layer (Azure OpenAI) is the primary cost driver but enables the full "AI Agent" product positioning.

---

## 8. Risk Callouts

| Risk | Severity | Mitigation |
|------|----------|------------|
| Azure SQL Serverless cold start (~10s resume from paused) | Medium | Set auto-pause to 60min (not 5min); first dashboard load after pause is slower |
| Functions Flex is relatively new (GA 2024) | Low | Fallback to Premium EP1 if issues arise; same code, different hosting plan |
| Python + TypeScript = two languages | Medium | Clean separation: TS for API, Python for algorithms. No shared code needed |
| Azure OpenAI token costs scale with user count | Medium | Use GPT-4o-mini for bulk operations (20x cheaper than GPT-4o); implement response caching for repeated explanations; set token budgets per batch run |
| Azure AI Agent Service is evolving rapidly | Medium | Abstract agent interface so underlying service can be swapped; keep algorithm logic independent of agent framework |
| LLM hallucination in recommendations | High | LLM NEVER makes license decisions — only generates explanations from deterministic algorithm outputs. All numbers come from algorithms, not LLM generation. Include confidence scores from algorithms, not LLM |
| Skip APIM = no developer portal | Low | Auto-generate OpenAPI docs from Functions; add APIM when external consumers appear |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-06 | Initial creation — complete tech stack recommendation with 9-layer architecture, 4-tier cost model, and SLA validation | Claude (AI Assistant) |

---

*This analysis is informational only — no changes to project scope or requirements documents.*

---

**End of Tech Stack Recommendation**
