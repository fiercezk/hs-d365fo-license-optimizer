# D365 FO License Agent - Local Development Strategy

**Date:** 2026-02-07
**Purpose:** Answer feasibility questions before cleanup actions

---

## ✅ QUESTION 1: Can we build the entire Web App (Production Ready) and test it locally?

### Short Answer: **YES, ABSOLUTELY** ✅

You can build, develop, and test the entire production-ready web application locally WITHOUT any Azure deployment. Here's how:

---

### Local Development Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LOCAL DEVELOPMENT STACK                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Next.js App     │◄────────│  PostgreSQL      │          │
│  │  (Port 3000)     │         │  (Port 5432)     │          │
│  │                  │         │  OR SQLite       │          │
│  │  - All pages     │         │                  │          │
│  │  - Components    │         │  Local database  │          │
│  │  - API calls     │         │  with test data  │          │
│  └────────┬─────────┘         └──────────────────┘          │
│           │                                                   │
│           │ HTTP                                              │
│           ▼                                                   │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Express.js API  │◄────────│  Ollama (LLM)    │          │
│  │  (Port 3001)     │         │  (Port 11434)    │          │
│  │                  │         │  OR Mock LLM     │          │
│  │  - Algorithm     │         │                  │          │
│  │    endpoints     │         │  Local AI agent  │          │
│  │  - Auth (mock)   │         │  for testing     │          │
│  └────────┬─────────┘         └──────────────────┘          │
│           │                                                   │
│           │ Import                                            │
│           ▼                                                   │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Python Algos    │         │  Jest + RTL      │          │
│  │  (apps/agent)    │         │  Playwright      │          │
│  │                  │         │                  │          │
│  │  - All 34        │         │  Test suites for │          │
│  │    algorithms    │         │  UI components   │          │
│  │  - 600-800 tests │         │                  │          │
│  └──────────────────┘         └──────────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

### What Runs Locally (Production Equivalent)

| Component | Azure Production | Local Development | Equivalent? |
|-----------|------------------|-------------------|-------------|
| **Frontend** | Azure Static Web Apps | Next.js (dev or production build) | ✅ YES - Identical codebase |
| **Backend API** | Azure Functions (TypeScript) | Express.js (TypeScript) | ✅ YES - Same logic, different runtime |
| **Database** | Azure SQL Serverless | PostgreSQL 16 OR SQLite | ✅ YES - Same schema, compatible SQL |
| **AI Agent** | Azure AI Foundry + GPT-4o | Ollama (Llama 3) OR Mock | ⚠️ MOSTLY - Different LLM, same logic |
| **Auth** | Azure AD B2C | Mock authentication | ⚠️ MOCK - Good for testing, not production auth |
| **Telemetry** | Application Insights | Console logs OR local logging | ⚠️ MOCK - No real telemetry, but testable |

**Verdict:** 100% of application logic can be developed and tested locally. Only difference: local substitutes for Azure services (Postgres vs. Azure SQL, Ollama vs. Azure AI).

---

### Local Setup Requirements

#### Prerequisites

```bash
# Required installations
- Node.js 18+ (for Next.js)
- Bun or npm (package manager)
- Python 3.11+ (for algorithm engine)
- PostgreSQL 16 OR SQLite (database)
- Ollama (optional, for local LLM)
```

#### Setup Steps

**1. Database Setup (PostgreSQL)**

```bash
# Install PostgreSQL
brew install postgresql@16  # macOS
# OR: apt-get install postgresql-16  # Linux
# OR: Download installer for Windows

# Start PostgreSQL
brew services start postgresql@16

# Create database
createdb d365_license_agent

# Load schema
psql d365_license_agent < apps/agent/schema.sql

# Seed test data
psql d365_license_agent < apps/agent/seed_data.sql
```

**Alternative: SQLite (simpler)**

```bash
# No installation needed, SQLite comes with Python
# Create database
sqlite3 apps/agent/data/local.db < apps/agent/schema.sql

# Seed test data
sqlite3 apps/agent/data/local.db < apps/agent/seed_data.sql
```

**2. Backend API Setup (Express.js)**

```bash
# Already exists as mock-api-server.js
# Enhance to call actual Python algorithms

cd apps/web
npm install express cors dotenv

# Create .env.local
echo "DATABASE_URL=postgresql://localhost:5432/d365_license_agent" > .env.local
# OR for SQLite: DATABASE_URL=sqlite:///apps/agent/data/local.db

# Start API
node mock-api-server.js  # Port 3001
```

**3. Frontend Setup (Next.js)**

```bash
cd apps/web
bun install  # or npm install

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:3001" > .env.local

# Start Next.js
bun run dev  # Port 3000
```

**4. AI Agent Setup (Ollama - Optional)**

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull Llama 3 model
ollama pull llama3

# Ollama runs on port 11434
# API endpoint: http://localhost:11434/api/generate
```

---

### Testing Locally

#### Unit Tests (Algorithm Engine)

```bash
cd apps/agent
pytest tests/                    # Run all 600-800 tests
pytest tests/test_algorithm_2_2.py -v  # Run specific test
```

#### Unit Tests (Web UI - After TDD Setup)

```bash
cd apps/web
npm test                         # Run Jest tests
npm test -- --coverage          # Run with coverage report
```

#### Integration Tests (API + Database)

```bash
# Start all services
postgres &                       # Terminal 1
node apps/web/mock-api-server.js &  # Terminal 2
cd apps/web && bun run dev &    # Terminal 3

# Run integration tests
npm run test:integration
```

#### E2E Tests (Full Stack)

```bash
# Start all services
# ...same as above

# Run Playwright tests
cd apps/web
npx playwright test
npx playwright test --ui  # Interactive mode
```

#### Manual Testing

```bash
# Access web app
open http://localhost:3000

# Test all pages:
# - Dashboard
# - Algorithm detail pages (readonly, minority, etc.)
# - Security pages (SoD violations, anomalies)
# - Recommendations workflow
# - New User License Wizard
```

---

### Production Build Testing (Local)

```bash
# Build production Next.js app
cd apps/web
bun run build

# Test production build locally
bun run start  # Runs production build on port 3000

# Verify:
# - All pages load
# - API calls work
# - Performance is good (Lighthouse > 90)
# - No console errors
```

---

### What CANNOT Be Tested Locally

| Feature | Limitation | Workaround |
|---------|------------|------------|
| **Azure AD B2C Auth** | Requires Azure tenant | Mock authentication with JWT tokens |
| **D365 FO OData Integration** | Requires D365 FO instance | Use seed data (CSV fixtures) |
| **Application Insights Telemetry** | Requires Azure resource | Console logs + local logging library |
| **Azure CDN Performance** | Requires Azure deployment | Test with production build locally |
| **Multi-region Failover** | Requires Azure infrastructure | Not testable locally |

**Verdict:** 95% of functionality testable locally. Only Azure-specific features (AD auth, OData sync, telemetry) require substitutes.

---

## ✅ QUESTION 2: Can the AI Agent logic be built and tested locally?

### Short Answer: **YES, with 4 options** ✅

The AI Agent can be fully developed and tested locally. You have 4 options for LLM integration:

---

### AI Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AI AGENT COMPONENTS                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. EXPLANATION GENERATOR (Core Logic)               │   │
│  │                                                       │   │
│  │  Input:  Algorithm output (recommendation)           │   │
│  │          User context (roles, activity)              │   │
│  │          Historical data (trends)                    │   │
│  │                                                       │   │
│  │  Process: Format prompt with context                 │   │
│  │           Call LLM API                               │   │
│  │           Parse response                             │   │
│  │           Validate explanation quality               │   │
│  │                                                       │   │
│  │  Output: Natural language explanation (200-300 words)│   │
│  └───────────────────┬───────────────────────────────────┘   │
│                      │                                        │
│                      ▼                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  2. LLM PROVIDER (Choose One)                        │   │
│  │                                                       │   │
│  │  Option A: Mock Responses (fastest)                  │   │
│  │  Option B: Ollama + Llama 3 (fully local)           │   │
│  │  Option C: OpenAI API (requires key)                │   │
│  │  Option D: Azure AI Foundry (requires Azure)        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

### Option A: Mock LLM Responses (Recommended for Early Testing)

**Pros:**
- ✅ Zero setup, instant start
- ✅ Deterministic (same input → same output)
- ✅ Fast (no API latency)
- ✅ Works offline

**Cons:**
- ❌ Not testing real LLM integration
- ❌ Fixed responses don't adapt to input

**Implementation:**

```typescript
// apps/web/lib/ai-agent.ts
export function generateExplanation(recommendation: Recommendation): string {
  const mockExplanations = {
    'readonly': `This user has been identified as read-only based on their activity patterns over the past 90 days. They have accessed 12 forms, all of which are eligible for Team Members license ($60/month). Current license: Operations ($90/month). Downgrading would save $30/month ($360/year) without impacting their workflow.`,
    'minority': `This user is a License Minority - they use only 3 menu items, all available in Team Members license. 89% of users in similar roles use Operations license, but this user's activity pattern shows they don't need it. Recommendation: downgrade to Team Members to save $30/month.`,
    'sod': `Segregation of Duties conflict detected. This user has both AP Clerk (create invoices) and Vendor Master (create vendors) roles, creating a fraud risk. They could create fake vendors and pay them. This violates SOX compliance rule #27.`,
  };

  return mockExplanations[recommendation.type] || 'No explanation available.';
}
```

**Testing:**

```bash
# Test AI agent with mock responses
npm test src/lib/ai-agent.test.ts
```

---

### Option B: Ollama + Llama 3 (Fully Local LLM)

**Pros:**
- ✅ Fully local, no cloud dependency
- ✅ No API costs
- ✅ Privacy (data never leaves machine)
- ✅ Real LLM testing (adaptive responses)

**Cons:**
- ⚠️ Requires powerful hardware (16GB+ RAM, GPU recommended)
- ⚠️ Slower than cloud LLMs (5-10 sec per request)
- ⚠️ Quality slightly lower than GPT-4o

**Setup:**

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull Llama 3 model (4.7GB download)
ollama pull llama3

# Test Ollama
ollama run llama3 "Explain why a user should downgrade their license"

# Ollama API runs on http://localhost:11434
```

**Implementation:**

```typescript
// apps/web/lib/ai-agent.ts
export async function generateExplanation(
  recommendation: Recommendation
): Promise<string> {
  const prompt = `You are a license optimization agent. Explain this recommendation:

User: ${recommendation.userId}
Current License: ${recommendation.currentLicense} ($${recommendation.currentCost}/month)
Recommended License: ${recommendation.recommendedLicense} ($${recommendation.recommendedCost}/month)
Savings: $${recommendation.savings}/month
Reason: ${recommendation.algorithmReason}

Generate a 200-word explanation for an IT admin about why this recommendation makes sense.`;

  const response = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'llama3',
      prompt: prompt,
      stream: false,
    }),
  });

  const data = await response.json();
  return data.response;
}
```

**Testing:**

```bash
# Test AI agent with Ollama
npm test src/lib/ai-agent.test.ts

# Test with real LLM call
npm run test:ai-agent -- --runInBand  # Serial execution to avoid rate limits
```

---

### Option C: OpenAI API (Cloud LLM)

**Pros:**
- ✅ High quality (GPT-4o)
- ✅ Fast (cloud-hosted)
- ✅ Easy setup (just API key)
- ✅ Similar to Azure AI (OpenAI backend)

**Cons:**
- ❌ Requires internet connection
- ❌ API costs (~$0.01 per explanation, $10-20/month for testing)
- ❌ Data leaves local machine (privacy concern)

**Setup:**

```bash
# Get API key from https://platform.openai.com/api-keys
# Add to .env.local
echo "OPENAI_API_KEY=sk-..." >> apps/web/.env.local

# Install OpenAI SDK
npm install openai
```

**Implementation:**

```typescript
// apps/web/lib/ai-agent.ts
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function generateExplanation(
  recommendation: Recommendation
): Promise<string> {
  const prompt = `...same as Option B...`;

  const completion = await openai.chat.completions.create({
    model: 'gpt-4o-mini',  // Cheaper than gpt-4o
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 300,
    temperature: 0.7,
  });

  return completion.choices[0].message.content;
}
```

---

### Option D: Azure AI Foundry (Production)

**Pros:**
- ✅ Production-ready (Azure infrastructure)
- ✅ Enterprise security (managed identity)
- ✅ Integrated telemetry (App Insights)
- ✅ Multi-model support (GPT-4o, GPT-4o-mini)

**Cons:**
- ❌ Requires Azure subscription
- ❌ Requires deployment (can't run locally)
- ❌ Setup complexity (Foundry project, deployments, keys)

**When to use:** Only after local development/testing complete and ready for production deployment.

---

### Recommended AI Agent Testing Strategy

**Phase 1: Early Development (Weeks 1-2)**
- Use **Option A (Mock)** for UI development
- Focus on page layout, API integration, user flows
- No LLM dependency, fast iteration

**Phase 2: Integration Testing (Weeks 3-4)**
- Switch to **Option B (Ollama)** or **Option C (OpenAI)**
- Test prompt engineering (does LLM generate good explanations?)
- Validate explanation quality
- Test edge cases (missing data, malformed responses)

**Phase 3: Production Deployment (Week 5+)**
- Deploy to **Option D (Azure AI Foundry)**
- Keep Options A-C as fallbacks for local testing
- Use mock in CI/CD tests (deterministic, no API costs)

---

## 📐 COMPLETE LOCAL DEVELOPMENT ARCHITECTURE

### Full Stack Local Setup

```bash
# Directory structure
D365FOLicenseAgent-v1/
├── apps/
│   ├── agent/              # Python algorithm engine
│   │   ├── src/algorithms/ # All 34 algorithms
│   │   ├── tests/          # 600-800 pytest tests
│   │   └── data/           # Local SQLite database
│   │
│   ├── api/                # Express.js API (NEW - replace mock-api-server.js)
│   │   ├── src/
│   │   │   ├── routes/     # API endpoints
│   │   │   ├── services/   # Business logic
│   │   │   ├── db/         # Database connection (Postgres/SQLite)
│   │   │   └── ai/         # AI agent integration (Ollama/OpenAI/Mock)
│   │   ├── tests/          # API integration tests
│   │   └── package.json
│   │
│   └── web/                # Next.js frontend
│       ├── app/            # Pages (with TDD)
│       ├── components/     # UI components (with TDD)
│       ├── lib/            # API client, utilities
│       ├── tests/          # Jest + Playwright tests
│       └── package.json
│
├── data/
│   ├── fixtures/           # Test data (CSV files from D365 FO exports)
│   ├── schema.sql          # Database schema (Postgres/SQLite compatible)
│   └── seed_data.sql       # Sample data for testing
│
└── docker-compose.yml      # Optional: Run entire stack in Docker
```

### Docker Compose (Optional - One-Command Startup)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: d365_license_agent
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
    ports:
      - "5432:5432"
    volumes:
      - ./data/schema.sql:/docker-entrypoint-initdb.d/1-schema.sql
      - ./data/seed_data.sql:/docker-entrypoint-initdb.d/2-seed.sql

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama

  api:
    build: ./apps/api
    ports:
      - "3001:3001"
    environment:
      DATABASE_URL: postgresql://dev:dev123@postgres:5432/d365_license_agent
      OLLAMA_URL: http://ollama:11434
    depends_on:
      - postgres
      - ollama

  web:
    build: ./apps/web
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:3001
    depends_on:
      - api

volumes:
  ollama:
```

**Usage:**

```bash
# Start entire stack
docker-compose up

# Access web app
open http://localhost:3000

# Run tests
docker-compose exec api npm test
docker-compose exec web npm test
```

---

## 🧹 CLEANUP ACTION PLAN

**User requested:**
1. Merge anything not merged to main
2. Scrap the demo dashboard

### Action 1: Merge Phase 2 Algorithms to Main

**Current State:**
- 11 Phase 1 algorithms on main (merged, tested)
- 23 Phase 2 algorithms on 21 feature branches (not merged)

**Strategy:** Hybrid consolidation (4 PRs grouped by category)

**Commands:**

```bash
# Create 4 consolidation branches
# Group 1: Cost Optimization (8 algorithms)
git checkout -b group-cost-optimization
git merge --no-edit origin/feature/algo-1-1
git merge --no-edit origin/feature/algo-1-2
git merge --no-edit origin/feature/algo-1-3
git merge --no-edit origin/feature/algo-2-1
git merge --no-edit origin/feature/algo-2-3
git merge --no-edit origin/feature/algo-2-4
git merge --no-edit origin/feature/algo-2-6
# Fix merge conflicts (if any)
pytest apps/agent/tests/  # Verify all tests pass
git push -u origin group-cost-optimization

# Group 2: Security & Compliance (4 algorithms)
git checkout -b group-security-compliance
git merge --no-edit origin/feature/algo-3-5-orphaned
git merge --no-edit origin/feature/algo-3-6
git merge --no-edit origin/feature/algo-3-7
git merge --no-edit origin/feature/algo-3-8
pytest apps/agent/tests/
git push -u origin group-security-compliance

# Group 3: Analytics & Role Management (7 algorithms)
git checkout -b group-analytics-role-mgmt
git merge --no-edit origin/feature/algo-4-2
git merge --no-edit origin/feature/algo-5-3
git merge --no-edit origin/feature/algo-6-1
git merge --no-edit origin/feature/algo-6-3
git merge --no-edit origin/feature/algo-7-1
git merge --no-edit origin/feature/algo-7-2
git merge --no-edit origin/feature/algo-7-4
pytest apps/agent/tests/
git push -u origin group-analytics-role-mgmt

# Group 4: Current branch (4 Phase 2 algorithms from feature/algo-6-2)
git checkout feature/algo-6-2
git push -u origin feature/algo-6-2

# Create PRs for all 4 groups
gh pr create --base main --head group-cost-optimization \
  --title "feat: Cost Optimization algorithms (8 algorithms)" \
  --body "Algorithms 1.1, 1.2, 1.3, 1.4, 2.1, 2.3, 2.4, 2.6. See IMPLEMENTATION_STATUS.md"

gh pr create --base main --head group-security-compliance \
  --title "feat: Security & Compliance algorithms (4 algorithms)" \
  --body "Algorithms 3.5, 3.6, 3.7, 3.8. See IMPLEMENTATION_STATUS.md"

gh pr create --base main --head group-analytics-role-mgmt \
  --title "feat: Analytics & Role Management algorithms (7 algorithms)" \
  --body "Algorithms 4.2, 5.3, 6.1, 6.3, 7.1, 7.2, 7.4. See IMPLEMENTATION_STATUS.md"

gh pr create --base main --head feature/algo-6-2 \
  --title "feat: Phase 2 algorithms (4 algorithms)" \
  --body "Algorithms 3.9, 5.4, 6.2, 6.4. See IMPLEMENTATION_STATUS.md"
```

**Expected Outcome:**
- 4 PRs created
- After merge: all 34 algorithms on main
- Estimated time: 2-3 weeks (PR reviews + integration testing)

**Rollback Strategy:**
```bash
# If merge causes issues, rollback is easy:
git checkout main
git reset --hard origin/main  # Reset to pre-merge state
```

---

### Action 2: Scrap Demo Dashboard

**Current State:**
- Demo dashboard in `apps/web/` (scaffolded today, Feb 7)
- Components: Dashboard page, CostTrendChart, Sidebar, Header
- Status: Working but not production-ready (0 tests)

**Strategy:** Delete demo, start fresh with TDD approach

**Commands:**

```bash
# Option A: Delete entire web app directory
cd /home/user/projects/work/D365FOLicenseAgent-v1
rm -rf apps/web/

# Option B: Keep useful components, delete demo-specific code
cd apps/web
rm -rf app/dashboard/  # Delete demo dashboard page
rm -f mock-api-server.js  # Delete mock API (will build proper API)
# Keep: components/ (reusable), lib/ (utilities), tailwind.config.ts, etc.
```

**Recommended: Option B (Keep Reusable Components)**

Keep these (production-quality):
- ✅ `components/ui/` (shadcn/ui components - production-ready)
- ✅ `components/layout/sidebar.tsx` (sidebar with icons - working)
- ✅ `components/layout/header.tsx` (header component - working)
- ✅ `lib/query-hooks.ts` (TanStack Query hooks - good architecture)
- ✅ `tailwind.config.ts` (Tailwind config - production-ready)

Delete these (demo-specific):
- ❌ `app/dashboard/page.tsx` (demo dashboard, will rebuild with TDD)
- ❌ `components/dashboard/cost-trend-chart.tsx` (demo chart, will rebuild with TDD)
- ❌ `mock-api-server.js` (demo API, will build proper Express.js API)

**Commands for Option B:**

```bash
cd /home/user/projects/work/D365FOLicenseAgent-v1/apps/web

# Delete demo pages
rm -rf app/dashboard/
rm -rf app/page.tsx  # Root redirect to dashboard

# Delete demo components
rm -rf components/dashboard/

# Delete mock API
rm -f mock-api-server.js

# Keep everything else (components/ui, layout, lib, config)

# Commit deletion
git add .
git commit -m "chore: remove demo dashboard, prepare for production rebuild with TDD"
git push
```

**Rollback Strategy:**
```bash
# If you change your mind, restore from git history
git checkout HEAD~1 -- apps/web/app/dashboard/
git checkout HEAD~1 -- apps/web/components/dashboard/
git checkout HEAD~1 -- apps/web/mock-api-server.js
```

---

## ✅ SUMMARY & RECOMMENDATIONS

### Question Answers

**Q1: Can we build production-ready web app locally?**
- ✅ **YES** - 100% of app logic testable locally
- Use: Next.js (frontend) + Express.js (API) + PostgreSQL/SQLite (DB) + Ollama/OpenAI (AI)
- Only difference from production: Azure services replaced with local equivalents

**Q2: Can AI agent logic be tested locally?**
- ✅ **YES** - 4 options available
- Recommended: Start with Mock (fast), then Ollama (real LLM), deploy Azure AI (production)
- All AI agent logic (prompt engineering, parsing, validation) testable locally

### Recommended Next Steps

**This Week:**
1. ✅ **Answer questions** (this document)
2. ⏳ **Await user approval** for cleanup actions
3. If approved: Execute Action 1 (merge Phase 2, 4 PRs)
4. If approved: Execute Action 2 (scrap demo dashboard)

**Next 2 Weeks:**
5. Set up local development stack (PostgreSQL + Express.js API + Ollama)
6. Establish TDD baseline (Jest + Playwright setup)
7. Start building production web app (TDD approach)
8. Build top 3 priority pages (readonly, minority, sod) with tests

**Timeline to Production-Ready App:**
- Local development complete: 6-8 weeks
- Azure deployment: +2-3 weeks
- **Total: 8-11 weeks**

---

**Document Status:** Ready for User Approval
**Next Action:** User approves/modifies cleanup actions, then execute
**Local Dev Feasibility:** ✅ 100% POSSIBLE
