# D365 FO License Agent - Production Web App Development Roadmap

**Date:** 2026-02-07
**Status:** Phase 0 Complete (Planning) → Starting Phase 1 (Infrastructure)
**Approach:** TDD-based, sequential with safe parallelization, Architect-guided

---

## EXECUTIVE SUMMARY

**User Requirements:**
- Professional, clean, useful UI with data visibility as priority
- Easy navigation with clickable tiles that drill down into details
- TDD-based development (no code without tests)
- Complete 100% autonomously without user intervention

**Technical Stack:**
- Frontend: Next.js 15 + shadcn/ui + TanStack Query
- Backend: Express.js (TypeScript) + Python algorithms
- Database: SQLite (local) → PostgreSQL (production)
- AI Agent: Claude API (Anthropic SDK)
- Testing: Jest + React Testing Library + Playwright

**Timeline:** 6-8 weeks (13+ development sessions)

---

## PHASE 0: PLANNING & CLEANUP ✅ COMPLETE

**Status:** ✅ Done (Feb 7, 2026)

### Completed Actions

1. ✅ **Phase 2 Algorithm Status:** All 34 algorithms implemented across 21 feature branches
2. ✅ **Merge Instructions:** Created 4 consolidation PRs (awaiting GitHub PR creation)
3. ✅ **Demo Dashboard Cleanup:** Removed demo pages, kept professional foundation
   - Kept: shadcn/ui components, sidebar, header, query hooks, layouts
   - Removed: dashboard page, demo components, mock API server
4. ✅ **Architecture Design:** Architect agent spawned (running in background)
5. ✅ **User Decisions Gathered:**
   - Page priority: Sequential but parallelize when safe
   - AI Agent: Claude API
   - Database: SQLite
   - UI: Professional, data-focused, drill-down navigation

---

## PHASE 1: TDD INFRASTRUCTURE (Session 2 - 1 day)

**Objective:** Establish testing baseline before any page development

### Tasks

1. **Jest + React Testing Library Setup**
   - Install dependencies
   - Configure jest.config.js
   - Create testing utilities (render wrappers, mock providers)
   - Write first test (smoke test for layout)

2. **Playwright E2E Setup**
   - Install playwright
   - Configure playwright.config.ts
   - Create E2E test utilities (auth helpers, page objects)
   - Write first E2E test (navigate to root)

3. **Baseline Tests for Existing Components**
   - Test Sidebar component (navigation links, icons)
   - Test Header component (search, notifications, user menu)
   - Test Layout component (renders children)
   - Test Providers (TanStack Query setup)

4. **CI/CD Test Pipeline**
   - GitHub Actions workflow
   - Run tests on PR
   - Require all tests passing before merge

**Deliverables:**
- 50+ baseline tests passing
- Test coverage: 80%+ on existing components
- Documentation: TESTING_STRATEGY.md

**Estimated Time:** 1 day (8 hours)

---

## PHASE 2: DATABASE & API FOUNDATION (Session 3 - 1 day)

**Objective:** Set up SQLite database and Express.js API before UI development

### Tasks

1. **SQLite Schema Design**
   - Users table
   - Roles table
   - Recommendations table
   - Activity logs table
   - Algorithm results table

2. **Database Seed Data**
   - 100+ sample users
   - 20+ roles
   - 50+ recommendations
   - 1000+ activity records
   - Test data covers all algorithm scenarios

3. **Express.js API Implementation**
   - TypeScript setup
   - Route structure (RESTful)
   - Database connection (better-sqlite3)
   - Error handling middleware
   - CORS configuration

4. **API Endpoints**
   - GET /api/v1/dashboard/metrics
   - GET /api/v1/algorithms/:id/recommendations
   - GET /api/v1/recommendations/:id
   - POST /api/v1/recommendations/:id/approve
   - POST /api/v1/recommendations/:id/reject
   - POST /api/v1/recommendations/:id/rollback
   - GET /api/v1/security/sod-violations
   - GET /api/v1/security/anomalies
   - +20 more endpoints

5. **API Tests**
   - Integration tests for all endpoints
   - Request validation tests
   - Error handling tests

**Deliverables:**
- SQLite database with schema + seed data
- Express.js API with 30+ endpoints
- 100+ API integration tests passing
- Documentation: API_REFERENCE.md

**Estimated Time:** 1 day (8 hours)

---

## PHASE 3: CORE PAGES - DASHBOARD (Session 4 - 2 days)

**Objective:** Rebuild dashboard with TDD, clickable tiles, drill-down

### Tasks

1. **Dashboard Page (TDD)**
   - Write tests first: renders 6 metric tiles, tiles are clickable, clicking navigates
   - Implement: Dashboard page component
   - Metric tiles: Total Cost, Monthly Savings, YTD Savings, Users Analyzed, Pending Recommendations, Active Alerts
   - Each tile clickable → drills down to detail view

2. **Dashboard Components (TDD)**
   - MetricCard component (clickable, shows trend, onClick handler)
   - TopOpportunities component (list of top 5 recommendations)
   - SecurityAlerts component (list of top 3 alerts)
   - CostTrendChart component (Recharts LineChart, professional styling)

3. **Dashboard API Integration**
   - useDashboardMetrics hook
   - useCostTrend hook
   - useTopOpportunities hook
   - useSecurityAlerts hook

4. **Dashboard Navigation**
   - Metric tile → Detail page (e.g., "Users Analyzed" → User List)
   - Opportunity card → Algorithm detail page
   - Alert card → Security detail page

**Deliverables:**
- Dashboard page with 6 clickable metric tiles
- 50+ component tests
- 5+ E2E tests (navigate dashboard, click tiles, drill down)
- Professional UI matching user requirements

**Estimated Time:** 2 days (16 hours)

---

## PHASE 4: ALGORITHM DETAIL PAGES (Sessions 5-8 - 8 days)

**Objective:** Build all algorithm detail pages with TDD

### Parallelization Strategy

**Group A (Sessions 5-6):** Cost Optimization (can build in parallel)
- /algorithms/readonly (Algorithm 2.2)
- /algorithms/minority (Algorithm 2.5)
- /algorithms/cross-role (Algorithm 4.3)

**Group B (Sessions 7-8):** Security & Compliance (can build in parallel)
- /security/sod (Algorithm 3.1)
- /security/anomalies (Algorithm 3.2)
- /security/compliance (Reports)

### Page Structure (Template - Reuse Across All)

Each algorithm detail page follows this structure:

1. **Header Section**
   - Algorithm name + description
   - Key metrics (users affected, potential savings, confidence)
   - Time period selector (30/60/90 days)

2. **Recommendations Table**
   - Sortable, filterable, paginated
   - Columns: User, Current License, Recommended License, Savings, Confidence, Action
   - Click row → Drill down to recommendation detail

3. **Visualization**
   - Bar chart: Savings by department
   - Pie chart: Recommendations by confidence level
   - Trend chart: Historical savings opportunity

4. **Bulk Actions**
   - Select multiple recommendations
   - Approve selected
   - Reject selected
   - Export to CSV

### TDD Workflow (Per Page)

1. Write tests (2 hours):
   - Page renders with data
   - Table sorts/filters correctly
   - Charts display correctly
   - Bulk actions work
   - Drill-down navigation works

2. Implement (4 hours):
   - Page component
   - Table component (reusable)
   - Chart components (reusable)
   - Bulk action handlers

3. E2E tests (1 hour):
   - Navigate to page
   - Interact with table
   - Click through to detail
   - Approve recommendation

4. Refactor (1 hour):
   - Extract reusable components
   - Optimize performance
   - Improve accessibility

**Total per page:** 8 hours

### Tasks - Group A (Parallel Execution)

**Readonly Page (/algorithms/readonly)**
- Algorithm 2.2: Read-Only User Detector
- Shows users eligible for Team Members downgrade
- Potential savings: $30/user/month

**Minority Page (/algorithms/minority)**
- Algorithm 2.5: License Minority Detection
- Shows users using <5 menu items
- Form-to-license mapping visualization

**Cross-Role Page (/algorithms/cross-role)**
- Algorithm 4.3: Cross-Application License Analyzer
- Shows users with multiple app licenses who could consolidate
- Cross-app usage patterns

### Tasks - Group B (Parallel Execution)

**SoD Violations Page (/security/sod)**
- Algorithm 3.1: Segregation of Duties Conflicts
- Shows toxic role combinations
- Conflict matrix visualization
- SOX compliance status

**Anomalies Page (/security/anomalies)**
- Algorithm 3.2: Anomalous Role Change Detection
- Shows suspicious role assignments
- Timeline visualization
- Risk scoring

**Compliance Page (/security/compliance)**
- Compliance reports aggregation
- SOX, GDPR, SOC 2 status
- Historical compliance trends
- Downloadable audit reports

**Deliverables:**
- 6 algorithm detail pages
- 1 reusable RecommendationsTable component
- 3+ reusable Chart components
- 200+ component tests
- 30+ E2E tests

**Estimated Time:** 8 days (64 hours) - parallelizable to 4 days with 2 concurrent streams

---

## PHASE 5: RECOMMENDATION DETAIL & WORKFLOW (Session 9 - 2 days)

**Objective:** Drill-down detail view + approve/reject/rollback workflow

### Tasks

1. **Recommendation Detail Page (TDD)**
   - URL: /recommendations/[id]
   - Shows full recommendation details
   - User profile (roles, activity, license history)
   - Algorithm explanation (Claude AI-generated)
   - Confidence breakdown
   - Historical data visualization

2. **Workflow Actions (TDD)**
   - Approve button → Confirmation dialog → API call → Success toast → Refresh
   - Reject button → Reason form → API call → Success toast → Refresh
   - Rollback button (if applicable) → Confirmation → Fast Restore
   - Comment system (add notes to recommendation)

3. **Approval Workflow State Machine**
   - States: Pending → Approved → Implemented → Rolled Back / Rejected
   - Status indicators
   - State transition history

**Deliverables:**
- Recommendation detail page with full workflow
- 40+ component tests
- 10+ E2E tests (full workflow scenarios)

**Estimated Time:** 2 days (16 hours)

---

## PHASE 6: CLAUDE AI AGENT INTEGRATION (Session 10 - 1 day)

**Objective:** Integrate Claude API for explanation generation

### Tasks

1. **Anthropic SDK Setup**
   - Install @anthropic-ai/sdk
   - Configure API key (env variable)
   - Create AI agent service layer

2. **Explanation Generator**
   - Prompt engineering (context + recommendation → explanation)
   - Response parsing and validation
   - Error handling and fallbacks
   - Caching strategy (cache explanations in DB)

3. **Integration Points**
   - Recommendation detail page (generate explanation on load)
   - Batch explanation generation (background job)
   - Explanation quality scoring

4. **Testing Strategy**
   - Mock Claude API responses in tests
   - Integration tests with real API (rate-limited)
   - Quality validation tests (explanation length, relevance)

**Deliverables:**
- Claude AI agent service integrated
- Explanation generation working on all recommendation pages
- 30+ AI agent tests
- Fallback to static explanations if API fails

**Estimated Time:** 1 day (8 hours)

---

## PHASE 7: REMAINING PAGES (Session 11 - 3 days)

**Objective:** Build all remaining pages

### Tasks

1. **User List Page**
   - /users
   - Table of all users with current licenses
   - Filter by license type, department, role
   - Click user → User detail page

2. **User Detail Page**
   - /users/[id]
   - User profile, roles, activity history
   - License history timeline
   - Recommendations for this user

3. **Recommendations List Page**
   - /recommendations
   - All recommendations with tab filters (All/Pending/Approved/Implemented/Rejected)
   - Search and filter
   - Bulk actions

4. **New User License Wizard**
   - /wizard
   - Multi-step form: Enter menu items → Algorithm finds optimal role + license
   - SoD validation
   - Recommendation + cost estimate

5. **Admin Configuration Page**
   - /admin
   - Algorithm parameters configuration
   - License pricing overrides
   - Threshold adjustments

**Deliverables:**
- 5+ pages
- 100+ component tests
- 20+ E2E tests

**Estimated Time:** 3 days (24 hours)

---

## PHASE 8: POLISH & REFINEMENT (Session 12 - 2 days)

**Objective:** Professional UI polish, performance optimization

### Tasks

1. **UI Polish**
   - Consistent spacing, typography, colors
   - Professional data visualizations
   - Loading states (skeletons, spinners)
   - Empty states (no data messages)
   - Error states (error boundaries, retry logic)

2. **Navigation Enhancement**
   - Breadcrumbs on all pages
   - Back button navigation
   - Deep linking (share URLs work)
   - Sidebar active state

3. **Performance Optimization**
   - Code splitting (dynamic imports)
   - Image optimization
   - React Query caching tuning
   - Lighthouse score > 90

4. **Accessibility**
   - ARIA labels
   - Keyboard navigation
   - Focus management
   - Screen reader testing

**Deliverables:**
- Professional, polished UI
- Lighthouse score > 90
- WCAG 2.1 AA compliance
- Performance optimizations

**Estimated Time:** 2 days (16 hours)

---

## PHASE 9: E2E TESTING & QA (Session 13 - 2 days)

**Objective:** Comprehensive E2E testing and QA validation

### Tasks

1. **E2E Test Suite Completion**
   - 50+ E2E tests covering all user flows
   - Critical path scenarios (approve recommendation end-to-end)
   - Error scenarios (API failures, auth failures)
   - Cross-browser testing (Chrome, Firefox, Safari)

2. **QA Validation**
   - Spawn QATester agent
   - Test all pages manually
   - Verify drill-down navigation works everywhere
   - Verify data accuracy
   - Verify professional UI standards

3. **Bug Fixes**
   - Fix any issues found by QATester
   - Regression testing
   - Performance profiling

**Deliverables:**
- 50+ E2E tests passing
- QA sign-off
- All critical bugs fixed
- Production build validated

**Estimated Time:** 2 days (16 hours)

---

## PARALLELIZATION OPPORTUNITIES

**Safe to parallelize (no dependencies):**

1. **Phase 4 - Algorithm Pages:**
   - Group A (readonly, minority, cross-role) - 3 parallel streams
   - Group B (SoD, anomalies, compliance) - 3 parallel streams
   - Can reduce 8 days to 4 days with parallel execution

2. **Phase 7 - Remaining Pages:**
   - User List + User Detail - 1 stream
   - Recommendations List - 1 stream
   - Wizard + Admin - 1 stream
   - Can reduce 3 days to 2 days with parallel execution

**NOT safe to parallelize (dependencies):**
- Phase 1 → Phase 2 → Phase 3 (sequential foundation)
- Phase 6 (AI agent) depends on Phase 5 (recommendation detail page)
- Phase 8-9 (polish + QA) depend on all pages complete

**Timeline Optimization:**
- Sequential: 25 days (5 weeks)
- With parallelization: 18 days (3.5 weeks) + buffer = **4-5 weeks total**

---

## SUCCESS CRITERIA

**Definition of Done (100% Complete):**

1. ✅ All 15+ pages implemented with TDD
2. ✅ 200+ unit tests passing (80%+ coverage)
3. ✅ 50+ E2E tests passing
4. ✅ Professional UI meeting user requirements:
   - Clean, data-focused design
   - Easy navigation with breadcrumbs
   - Clickable tiles with drill-down everywhere
5. ✅ Claude AI agent integrated and working
6. ✅ SQLite database with comprehensive seed data
7. ✅ Express.js API with 30+ endpoints
8. ✅ Lighthouse score > 90
9. ✅ WCAG 2.1 AA accessibility compliance
10. ✅ QA validation complete
11. ✅ Production build tested locally
12. ✅ All documentation complete

**User Acceptance:**
- User can navigate entire app without confusion
- Data is clearly visible and actionable
- Drill-down navigation works intuitively
- Professional appearance suitable for enterprise

---

## CURRENT STATUS

**Phase 0:** ✅ Complete
**Phase 1:** ⏳ Starting next session
**Architect Agent:** 🏃 Running in background (designing architecture)

**Next Actions:**
1. Wait for Architect agent to complete (20-30 min)
2. Review architecture document
3. Begin Phase 1 (TDD Infrastructure) in next session

---

**Document Status:** Living Roadmap
**Last Updated:** 2026-02-07 23:30 (Session 1 complete)
**Next Session:** Phase 1 (TDD Infrastructure)
