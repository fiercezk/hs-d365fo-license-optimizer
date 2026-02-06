# D365 FO License & Security Optimization Agent

**AI-powered license optimization and security analysis for Microsoft Dynamics 365 Finance & Operations.**

Automatically detect over-licensed users, security risks, and optimization opportunities. Estimated savings: **15-25% of annual license costs** (potentially 3-8% additional with Entra ID integration).

---

## 🎯 What This Does

The D365 FO License Agent analyzes your Dynamics 365 Finance & Operations environment to:

1. **License Optimization** - Detect over-licensed users who could use cheaper licenses
2. **Security Analysis** - Find Segregation of Duties (SoD) conflicts and security risks
3. **Usage Patterns** - Identify unused licenses, seasonal patterns, role optimization opportunities
4. **Compliance** - Detect license-entitlement mismatches (compliance gaps)

**Key Innovation**: Tracks **Read vs Write operations** (not available in Microsoft's native tools) to accurately identify Team Members license candidates.

---

## 📊 Phase 1 Capabilities (11 Algorithms)

| Category | Algorithm | Savings Potential | Phase |
|----------|-----------|-------------------|-------|
| **Cost Optimization** | 2.2: Read-Only User Detection | High | 1 |
| | 2.5: License Minority Detection | Medium | 1 |
| | 3.3: Unused License Detection | Medium | 1 |
| | 3.4: Seasonal Pattern Detection | Low-Medium | 1 |
| **Security** | 3.1: Segregation of Duties (SoD) Conflicts | N/A | 1 |
| | 5.2: Security Risk Scoring | N/A | 1 |
| **Behavior Analysis** | 4.3: License Reduction Prediction | Medium | 1 |
| **Role Optimization** | 4.1: Device License Opportunity | N/A | 1 |
| | 4.7: New User License Recommendation | N/A | 1 |
| **Analytics** | 5.1: License Cost Trend Analysis | N/A | 1 |
| **Advanced** | 3.2: Redundant Role Detection | Medium | 1 |

**Phase 2+**: 23 additional algorithms (Enterprise Role Opportunities, License Cost Center Analysis, and more)

See `/Requirements/` for complete specifications.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    D365 Finance & Operations                    │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐  │
│  │ Security     │  │ User-Role      │  │ X++ Telemetry      │  │
│  │ Config       │  │ Assignments    │  │ (Read/Write Track) │  │
│  └──────┬───────┘  └───────┬────────┘  └──────────┬─────────┘  │
└─────────┼──────────────────┼────────────────────────┼───────────┘
          │                  │                        │
          └──────────────────┴──────────────┬─────────┘
                                             │ OData / Telemetry
                                             ▼
               ┌─────────────────────────────────────────────┐
               │        Azure Application Insights           │
               │     (User Activity Telemetry Storage)       │
               └──────────────────┬──────────────────────────┘
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────────┐
      │                D365 FO License Agent                       │
      │  ┌──────────────────┐  ┌───────────────┐  ┌─────────────┐ │
      │  │ Algorithm Engine │◄─┤ Azure AI      │◄─┤ Web App     │ │
      │  │ (Python)         │  │ Agent Service │  │ (Next.js)   │ │
      │  │ • 34 Algorithms  │  │ • GPT-4o      │  │ • Dashboard │ │
      │  │ • Deterministic  │  │ • Explanations│  │ • Workflows │ │
      │  └──────────────────┘  └───────────────┘  └─────────────┘ │
      │           ▲                                                 │
      │           └─────── Azure SQL Database ──────────────────── │
      └────────────────────────────────────────────────────────────┘
```

**Key Design Principle**: Algorithms are **deterministic**. LLM generates explanations only, never makes license decisions.

---

## 🚀 Quick Start (Day 0 Setup)

### Prerequisites

- Python 3.11+ (tested with 3.13)
- Git
- D365 FO environment (for production data)
- Azure subscription (for cloud deployment - not needed for local dev)

### 1. Clone & Setup

```bash
# Initialize git (if starting fresh)
git init
git checkout -b dev

# Create Python virtual environment
cd apps/agent
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Verify Setup

```bash
# Run tests (should show "no tests collected" initially - that's correct)
pytest

# Verify Pydantic models import
python3 -c "from src.models.input_schemas import SecurityConfigRecord; print('✓ Setup OK')"
```

### 3. Test Data

Test fixtures are provided in `tests/fixtures/`:
- `security_config_sample.csv` - Security configuration data
- `user_roles_sample.csv` - User-role assignments
- `user_activity_log_sample.csv` - Activity telemetry
- `test_scenario_*.json` - 3 test scenarios for Algorithm 2.2

### 4. Next Steps

See `/Requirements/18-Tech-Stack-Recommendation.md` for:
- Algorithm implementation guide
- Azure deployment steps
- API and Web App setup

---

## 📂 Repository Structure

```
D365FOLicenseAgent-v1/
├── Requirements/              # 18 requirement documents (3000+ pages)
│   ├── 00-Index.md           # Start here - project overview
│   ├── 02-Security-Configuration-Data.md
│   ├── 03-User-Role-Assignment-Data.md
│   ├── 04-User-Activity-Telemetry-Data.md
│   ├── 06-Algorithms-Decision-Logic.md
│   ├── 07-Advanced-Algorithms.md
│   ├── 08-Algorithm-Review.md
│   ├── 12-Final-Phase1-Selection.md
│   ├── 13-Azure-AI-Agent-Architecture.md
│   ├── 14-Web-Application-Requirements.md
│   ├── 17-Agent-Process-Flow.md
│   └── 18-Tech-Stack-Recommendation.md
│
├── apps/
│   ├── agent/                # Python algorithm engine (START HERE)
│   │   ├── src/
│   │   │   ├── algorithms/  # Algorithm implementations
│   │   │   ├── models/      # Pydantic data contracts
│   │   │   └── services/    # Data access layer
│   │   ├── tests/
│   │   │   └── fixtures/    # Test data (CSV/JSON)
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── api/                  # Azure Functions TypeScript (Phase 1 Week 2)
│   └── web/                  # Next.js 15 Web App (Phase 1 Week 2-3)
│
├── data/
│   └── config/
│       └── pricing.json      # License pricing configuration
│
├── infra/                    # Bicep IaC templates (Phase 1 Week 2)
├── .gitignore
└── README.md                 # This file
```

---

## 🔧 Tech Stack

**Algorithm Engine** (Python 3.12+)
- pandas, numpy, scipy - Data processing
- networkx - Graph algorithms (SoD conflicts)
- pydantic - Type-safe data contracts
- pytest - Testing

**API Layer** (TypeScript)
- Azure Functions Flex Consumption
- Zod - Schema validation

**Web Application** (TypeScript)
- Next.js 15 (App Router)
- shadcn/ui - UI components
- TanStack Query - Data fetching
- Recharts - Visualizations

**Data & Storage**
- Azure SQL Database (Serverless, auto-pause)
- Azure Application Insights (Telemetry)

**AI & Intelligence**
- Azure AI Foundry + Agent Service
- GPT-4o (interactive explanations)
- GPT-4o-mini (bulk processing)

**Infrastructure**
- Bicep (IaC)
- Azure Container Apps Jobs (Batch processing)
- Azure Static Web Apps (Frontend hosting)

See `/Requirements/18-Tech-Stack-Recommendation.md` for complete architecture details.

---

## 💰 Cost Model (Phase 1)

**Monthly Operating Cost Estimate**: $70-145 USD

| Component | Tier | Monthly Cost |
|-----------|------|--------------|
| Azure AI Agent | Pay-per-use (GPT-4o-mini bulk) | $30-80 |
| Azure Functions | Flex Consumption | $5-15 |
| Azure SQL | Serverless (auto-pause) | $15-25 |
| Static Web Apps | Free | $0 |
| Container Apps | Consumption | $5-10 |
| App Insights | Pay-per-GB | $5-15 |
| **Total** | | **~$70-145/mo** |

**ROI**: At 15% savings on a $100K annual license spend, monthly savings = **$1,250**. Break-even in < 1 month.

---

## 📚 Key Documents

Start with these requirement documents in `/Requirements/`:

1. **00-Index.md** - Project overview, data sources, algorithm catalog
2. **05-Functional-Requirements.md** - Business capabilities and workflows
3. **06-Algorithms-Decision-Logic.md** - Core algorithm specifications (Phase 1)
4. **07-Advanced-Algorithms.md** - Advanced algorithms (Phase 2+)
5. **12-Final-Phase1-Selection.md** - Phase 1 algorithm selection rationale
6. **17-Agent-Process-Flow.md** - 22 processes, 5 diagrams, RACI matrix
7. **18-Tech-Stack-Recommendation.md** - Architecture & implementation guide

**Total Documentation**: 18 docs, ~3000 pages

---

## ⚠️ Critical Dependencies (Before Production)

These require validation with customer D365 FO environment:

1. **`TEAM_MEMBERS_ELIGIBLE_FORMS` table** - Validates which forms are accessible with Team Members license. Unvalidated → blocks Algorithm 2.2 production accuracy.

2. **`OPERATIONS_ACTIVITY_ELIGIBLE_FORMS` table** - Similar validation for Operations Activity add-on.

3. **OData entity names** - Requirements docs use placeholder names. Actual D365 FO OData entity names needed for data ingestion.

4. **X++ Telemetry Deployment** - Custom X++ Chain of Command (CoC) extensions must be deployed to D365 FO for read/write tracking. See `/Requirements/X++-Telemetry-Instrumentation-Strategy.md`.

**Mitigation**: Algorithms work with synthetic test data during development. Real data access needed Week 2-3.

---

## 🔐 Security & Compliance

- **Data Residency**: All data processed in customer's Azure region
- **Authentication**: Entra ID (Azure AD) single sign-on
- **Authorization**: Role-based access control (RBAC)
- **Audit Trail**: All recommendations logged, tamper-proof audit log
- **Observation Mode**: Test recommendations in read-only mode before auto-approval
- **Rollback**: Fast-restore procedures for license changes (< 5 minutes)
- **Encryption**: Data encrypted at rest (Azure SQL TDE) and in transit (TLS 1.3)

See `/Requirements/16-Rollback-Fast-Restore-Procedures.md` for SLA and safety protocols.

---

## 📈 Phase Roadmap

### Phase 1 (Weeks 1-8) - MVP
- 11 core algorithms implemented
- Web dashboard with recommendation review
- Manual approval workflow
- Azure deployment (dev + prod)
- **Target**: 15-25% license cost savings*

### Phase 2 (Weeks 9-16) - Automation
- 12 additional algorithms (23 total)
- Auto-approval workflows
- Entra ID license sync (Algorithm 3.9)
- Advanced analytics dashboards
- **Target**: +3-8% savings from Entra sync

### Phase 3 (Weeks 17-24) - Intelligence
- 11 remaining algorithms (34 total)
- Predictive analytics (seasonal forecasting)
- API integrations (ServiceNow, Jira)
- Custom business rules engine

*Pending validation of Team Members form eligibility tables

---

## 🤝 Contributing

This is an internal project. For questions or issues:
1. Check `/Requirements/` documentation first
2. Review algorithm specifications in docs 06-07
3. Check process flows in doc 17
4. Consult tech stack details in doc 18

---

## 📄 License Pricing Reference

Microsoft Dynamics 365 F&O License Types (USD, monthly, per-user):

| License | Cost | Description |
|---------|------|-------------|
| Team Members | $60 | Read-only + self-service writes (time, expenses, profile) |
| Operations Activity | $30 | Add-on to Team Members for activity-based operations |
| Operations | $90 | Full transactional access (single module) |
| Finance | $180 | Full Finance module |
| SCM | $180 | Full Supply Chain Management module |
| Commerce | $180 | Full Commerce (retail/e-commerce) module |
| Device License | $80/device | Shared device (warehouse scanner, POS terminal) |

Source: `data/config/pricing.json` (customer-overridable)

---

## 🎯 Algorithm Spotlight: 2.2 Read-Only User Detection

**The highest-value algorithm** - detects users performing 95%+ read-only operations who could downgrade from $180/month licenses to $60/month Team Members.

**Example**:
- User: John Doe, Finance Accountant
- Current License: Commerce ($180/month)
- Actual Usage: 847 reads, 2 writes (99.76% read-only)
- Recommendation: Downgrade to Team Members ($60/month)
- Savings: $1,440/year
- Confidence: 0.95 (high)

**Why it works**: Microsoft's native tools can't distinguish read vs write operations. This agent captures telemetry at the X++ layer, enabling accurate classification.

See `/Requirements/06-Algorithms-Decision-Logic.md` for complete specification.

---

## 📊 Status

**Current Stage**: ✅ Day 0 Complete - Ready for Algorithm 2.2 implementation

**Completed**:
- ✅ Git repository initialized
- ✅ Python project structure with pyproject.toml
- ✅ Pydantic data models (input + output schemas)
- ✅ Test data fixtures (3 scenarios)
- ✅ License pricing configuration
- ✅ Requirements documentation (18 docs, 3000+ pages)

**Next Steps** (Day 1):
1. Implement Algorithm 2.2 (Read-Only User Detection)
2. Write pytest tests using test fixtures
3. Verify against pseudocode in doc 06
4. First test passing = Milestone 1 complete

**Timeline to First Deployment**: 3 weeks (end-to-end deployed slice)

---

**Last Updated**: 2026-02-06
