# D365 FO License Agent - Production Web Architecture

**Version**: 1.0
**Date**: 2026-02-07
**Status**: Architecture Design (Approved for Implementation)
**Author**: Architect Agent + User Review

---

## Table of Contents

1. [Architecture Principles](#1-architecture-principles)
2. [Page Structure and Routing](#2-page-structure-and-routing)
3. [Component Hierarchy](#3-component-hierarchy)
4. [Data Flow Architecture](#4-data-flow-architecture)
5. [Navigation Structure](#5-navigation-structure)
6. [State Management Strategy](#6-state-management-strategy)
7. [SQLite Database Schema](#7-sqlite-database-schema)
8. [Express.js API Endpoints](#8-expressjs-api-endpoints)
9. [Claude AI Agent Integration](#9-claude-ai-agent-integration)
10. [TDD Strategy](#10-tdd-strategy)
11. [Parallel Execution Plan](#11-parallel-execution-plan)
12. [File Tree Reference](#12-file-tree-reference)

---

## 1. Architecture Principles

These principles are immutable. Every implementation decision must trace back to one of them.

### P1: Data is Primary, Chrome is Secondary

The UI exists to surface data, not to look pretty. Every pixel must earn its place
by communicating information. If a visual element does not help the user understand
their license landscape or make a decision, remove it.

### P2: Drill-Down as the Fundamental Navigation Pattern

Every aggregate number is clickable. Every summary row expands. The user should
never hit a dead end. The navigation path is always:
`Overview tile -> Filtered list -> Individual record -> Detail with AI explanation`

### P3: URL is the Source of Truth for View State

Filters, pagination, sort order, selected tab -- all encoded in the URL. A user
should be able to bookmark any view, share it with a colleague, or refresh without
losing state. This also means the browser back button always works correctly.

### P4: Server State via TanStack Query, UI State via URL + React State

There are exactly two kinds of state in this application:
- **Server state** (recommendations, metrics, user data): Managed exclusively
  by TanStack Query. Cached, deduplicated, background-refreshed.
- **UI state** (sidebar open, modal visible, form inputs): React useState or
  URL search parameters. Never persisted to the server unless it represents
  a user action (approve, reject, configure).

### P5: Deterministic Core, AI Explanation Layer

The 34 algorithms produce deterministic outputs. The Claude AI layer generates
human-readable explanations, never makes license decisions. The UI must clearly
separate "what the algorithm determined" from "how Claude explains it."

### P6: Test-Driven Development, No Exceptions

Every component, hook, API route, and utility function has tests written before
implementation. The test describes the contract. The implementation fulfills it.

### P7: Progressive Enhancement

The application works without JavaScript for static content (Next.js SSR).
Interactive features enhance progressively. Error states are always handled
gracefully -- never a blank screen, never an unrecoverable state.

---

## 2. Page Structure and Routing

### Complete Route Map

There are 19 routes organized into 6 sections. Each route maps to a specific
requirements document reference and algorithm set.

```
Route                                   | Section              | Req Doc Ref
-------------------------------------  | -------------------- | -----------
/                                       | Root                 | Redirect to /dashboard
/dashboard                              | Executive            | 14-Dashboard-1
/dashboard/users/[userId]               | User Detail          | 14-FR-Web-2.2

/optimization                           | License Optimization | 14-Dashboard-2
/optimization/readonly                  | Algorithm 2.2        | 06-Algo-2.2
/optimization/minority                  | Algorithm 2.5        | 09-Algo-2.5
/optimization/cross-role                | Algorithm 4.3        | 10-Algo-2.6
/optimization/component-removal         | Algorithm 1.4        | 06-Algo-1.4
/optimization/role-splitting            | Algorithm 1.3        | 06-Algo-1.3
/optimization/device-license            | Algorithm 4.1        | 07-Algo-4.1

/security                               | Security Overview    | 14-Dashboard-3
/security/sod                           | SoD Violations       | 06-Algo-3.1
/security/anomalies                     | Anomalous Activity   | 07-Algo-3.2
/security/privilege-creep               | Privilege Creep      | 07-Algo-3.3
/security/compliance                    | Compliance Reports   | 14-Report-2

/recommendations                        | Recommendations      | 14-FR-Web-2
/recommendations/[id]                   | Recommendation Detail| 14-FR-Web-2.2

/wizard                                 | New User Wizard      | 14-Dashboard-5

/admin                                  | Administration       | 14-FR-Web-5
/admin/algorithms                       | Algorithm Config     | 14-FR-Web-5.2
/admin/scheduling                       | Agent Scheduling     | 14-FR-Web-5.1
```

### Route Details

#### Dashboard (`/dashboard`)

**Purpose**: Executive summary. The single most important page.

**Tiles (clickable, drill-down)**:
- Total License Cost -> `/optimization` (filtered by cost)
- Monthly Savings -> `/recommendations?status=IMPLEMENTED&period=month`
- YTD Savings -> `/recommendations?status=IMPLEMENTED&period=ytd`
- Users Analyzed -> `/dashboard/users` (future: user listing)
- Pending Recommendations -> `/recommendations?status=PENDING`
- Active Alerts -> `/security`
- Compliance Score -> `/security/compliance`

**Charts**:
- Cost Trend (12-month line chart, Algorithm 5.1 data)
- License Distribution (pie/donut chart)

**Lists**:
- Top 5 Optimization Opportunities (click -> algorithm detail page)
- Security Alerts (click -> `/security/sod` or `/security/anomalies`)

**Data sources**: `GET /api/v1/dashboard/metrics`, `GET /api/v1/algorithms/5.1/trend`

---

#### User Detail (`/dashboard/users/[userId]`)

**Purpose**: Complete view of a single user's license situation.

**Sections**:
- User profile (name, email, department, current license, cost)
- Activity summary (read/write ratio, last active, top forms used)
- All recommendations for this user (from any algorithm)
- Role assignments (current roles, license implications)
- AI explanation: Claude-generated narrative of optimization opportunities

**Data sources**: `GET /api/v1/users/:userId`, `GET /api/v1/recommendations?userId=:userId`

---

#### Optimization Overview (`/optimization`)

**Purpose**: License optimization hub. Admin's primary workspace.

**Layout**: Grid of algorithm summary tiles, each showing:
- Algorithm name and ID
- Users affected count
- Estimated monthly savings
- Confidence distribution (HIGH/MEDIUM/LOW counts)
- Status indicator (last run time, health)

Each tile clicks through to its algorithm detail page.

**Filters**: Department, License Type, Date Range (all in URL params)

---

#### Algorithm Detail Pages (`/optimization/readonly`, `/optimization/minority`, etc.)

**Shared layout** (all algorithm detail pages use the same structure):

1. **Header**: Algorithm name, description, last run timestamp
2. **Summary row**: 4 metric cards (users affected, savings, avg confidence, implementation rate)
3. **Filters bar**: Department, license type, confidence level, status
4. **Data table**: Sortable, paginated table of affected users
   - Columns vary by algorithm (see below)
   - Row click -> slide-out detail panel or `/dashboard/users/[userId]`
5. **Distribution chart**: Bar chart showing breakdown by department or license type
6. **Bulk actions**: Select All, Export CSV, Approve Selected

**Algorithm-specific columns**:

| Route           | Extra Columns                                          |
|-----------------|--------------------------------------------------------|
| `/readonly`     | Read %, Write Ops, Days Analyzed, Current License      |
| `/minority`     | Primary License, Minority License, Minority %, Forms   |
| `/cross-role`   | Role Combination, License Impact, Overlap %            |
| `/component-removal` | Component Name, Usage %, Users Affected, License Tier |
| `/role-splitting`    | Original Role, Proposed Roles, Users Migrated, Savings |
| `/device-license`    | Device ID, Users/Device, Current Cost, Device Cost     |

---

#### Security Overview (`/security`)

**Purpose**: Security monitoring and compliance dashboard.

**Tiles**:
- SoD Violations (count, critical count) -> `/security/sod`
- Anomalous Activity (count, last 24h) -> `/security/anomalies`
- Privilege Creep Alerts (count) -> `/security/privilege-creep`
- Compliance Score (%) -> `/security/compliance`

**Lists**:
- Critical Alerts (top 5, real-time)
- Recent Security Events (last 20)

---

#### SoD Violations (`/security/sod`)

**Table columns**: User, Role A, Role B, Conflict Rule, Severity, Detected At, Status
**Filters**: Severity, Category (from 15-Default-SoD-Conflict-Matrix.md, 7 categories)
**Detail panel**: Rule description, mitigation options, AI explanation

---

#### Anomalous Activity (`/security/anomalies`)

**Table columns**: User, Event Type, Timestamp, Severity, Description, Action Taken
**Filters**: Event type, Severity, Date range
**Detail panel**: Full event timeline, AI-generated risk assessment

---

#### Recommendations (`/recommendations`)

**Purpose**: Central workflow for approve/reject/rollback.

**Tabs** (URL-driven): All | Pending | Approved | Implemented | Rejected
**Table columns**: ID, User, Algorithm, Type, Confidence, Savings, Status, Created
**Row actions**: Approve, Reject (with reason), View Detail
**Bulk actions**: Approve Selected, Export Selected, Export All
**Sort**: By savings (default), priority, date, confidence

---

#### Recommendation Detail (`/recommendations/[id]`)

**Purpose**: Full context for a single recommendation.

**Sections**:
- Recommendation summary (type, algorithm, confidence, savings)
- User context (current license, usage patterns, role assignments)
- Algorithm explanation (deterministic output: inputs, thresholds, result)
- AI narrative (Claude-generated plain-English explanation)
- Options (if multiple: e.g., downgrade to Team Members vs. Operations)
- Action buttons: Approve, Reject, Request Review, Rollback (if implemented)
- Audit trail: All status changes with timestamps and actor

---

#### New User Wizard (`/wizard`)

**Purpose**: Two-step wizard for new user license recommendation (Algorithm 4.7).

**Step 1**: Menu item selection
- Typeahead search across all menu items
- Category browse (Finance, SCM, Commerce filters)
- Selected items shown as removable badges
- "Get Recommendations" button (calls `POST /api/v1/suggest-license`)

**Step 2**: Results display
- Top 3 role+license combinations ranked by cost
- Each shows: roles, license type, monthly cost, coverage %, SoD conflicts
- SoD conflict warnings with expandable details
- "Apply Recommendation" action per option
- AI explanation of why each option was selected

---

#### Administration (`/admin`)

**Purpose**: System configuration.

**Sub-pages**:
- `/admin/algorithms`: Enable/disable algorithms, set thresholds (read-only % default 95%, inactivity days default 90, minority threshold default 15%)
- `/admin/scheduling`: Configure agent run schedules (daily/weekly/monthly)
- Agent health display (last run, execution time, error rate)
- License pricing configuration (view/override pricing.json values)

---

## 3. Component Hierarchy

### Design System: Reusable Components

Components are organized in three tiers: primitives, composites, and page-specific.

```
components/
  ui/                          # Tier 1: Primitives (shadcn/ui)
    badge.tsx                  # Status badges (PENDING, APPROVED, etc.)
    button.tsx                 # All button variants
    card.tsx                   # Base card container
    data-table.tsx             # Generic sortable/filterable table
    dialog.tsx                 # Modal dialogs
    dropdown-menu.tsx          # Dropdown menus
    input.tsx                  # Text inputs, search inputs
    select.tsx                 # Select dropdowns
    skeleton.tsx               # Loading skeletons
    tabs.tsx                   # Tab navigation
    tooltip.tsx                # Hover tooltips
    breadcrumb.tsx             # Breadcrumb navigation

  shared/                      # Tier 2: Composites (project-specific reusable)
    metric-tile.tsx            # Clickable dashboard metric (title, value, change, link)
    confidence-badge.tsx       # HIGH/MEDIUM/LOW color-coded badge
    severity-badge.tsx         # CRITICAL/HIGH/MEDIUM/LOW badge
    status-badge.tsx           # PENDING/APPROVED/REJECTED/IMPLEMENTED badge
    license-badge.tsx          # License type colored badge
    savings-display.tsx        # Formatted savings ($X/mo, $X/yr)
    user-avatar.tsx            # User display (name + email + avatar)
    filter-bar.tsx             # Reusable filter bar (department, license, status dropdowns)
    sort-header.tsx            # Sortable table column header
    pagination.tsx             # Table pagination controls
    empty-state.tsx            # "No results" placeholder with icon and message
    error-boundary.tsx         # Error boundary with retry button
    loading-skeleton.tsx       # Content-aware skeleton (table, card, chart variants)
    export-button.tsx          # CSV/PDF export trigger
    bulk-action-bar.tsx        # Select all + bulk approve/reject/export
    slide-panel.tsx            # Right-side slide-out detail panel
    ai-explanation.tsx         # Claude AI explanation display (collapsible, with source indicator)

  charts/                      # Tier 2: Chart components (Recharts wrappers)
    cost-trend-chart.tsx       # 12-month line chart (actual, forecast, target)
    license-distribution.tsx   # Pie/donut chart of license types
    department-bar-chart.tsx   # Horizontal bar chart by department
    confidence-histogram.tsx   # Distribution of confidence scores
    savings-waterfall.tsx      # Waterfall chart of savings by algorithm

  layout/                      # Tier 2: Layout components
    sidebar.tsx                # Main navigation sidebar
    header.tsx                 # Top header with search, notifications, user
    breadcrumbs.tsx            # Dynamic breadcrumb based on route
    page-header.tsx            # Standard page header (title, description, actions)

  features/                    # Tier 3: Page-specific feature components
    dashboard/
      opportunity-list.tsx     # Top 5 optimization opportunities
      alerts-panel.tsx         # Security alerts list
      metrics-grid.tsx         # 4-7 clickable metric tiles

    optimization/
      algorithm-tile.tsx       # Algorithm summary tile for overview grid
      algorithm-detail-layout.tsx  # Shared layout for all algorithm detail pages
      user-recommendation-row.tsx  # Table row for user in algorithm results
      recommendation-detail-panel.tsx  # Slide-out panel for row detail

    security/
      sod-violation-row.tsx    # SoD violation table row
      anomaly-event-row.tsx    # Anomaly event table row
      compliance-scorecard.tsx # Compliance score breakdown
      security-event-timeline.tsx  # Timeline of security events

    recommendations/
      recommendation-card.tsx  # Recommendation summary card
      approval-dialog.tsx      # Approve confirmation with optional comment
      rejection-dialog.tsx     # Reject with required reason
      rollback-dialog.tsx      # Rollback confirmation with speed selection
      recommendation-timeline.tsx  # Audit trail timeline

    wizard/
      menu-item-selector.tsx   # Step 1: searchable menu item picker
      license-result-card.tsx  # Step 2: individual recommendation card
      sod-conflict-warning.tsx # SoD conflict expandable warning

    admin/
      algorithm-config-form.tsx  # Algorithm parameter form
      schedule-config.tsx      # Cron schedule picker
      pricing-editor.tsx       # License pricing override form
      agent-health-card.tsx    # Agent health status display
```

### Component Reuse Matrix

This matrix shows which Tier 2 components are used across pages, proving their
reuse value justifies abstraction.

```
Component             | Dashboard | Optimization | Security | Recommendations | Wizard | Admin
--------------------- | --------- | ------------ | -------- | --------------- | ------ | -----
metric-tile           |     X     |      X       |    X     |                 |        |
confidence-badge      |     X     |      X       |          |       X         |   X    |
severity-badge        |     X     |              |    X     |       X         |   X    |
status-badge          |           |      X       |    X     |       X         |        |
license-badge         |     X     |      X       |          |       X         |   X    |
savings-display       |     X     |      X       |          |       X         |   X    |
user-avatar           |           |      X       |    X     |       X         |        |
filter-bar            |           |      X       |    X     |       X         |        |
data-table            |           |      X       |    X     |       X         |        |
pagination            |           |      X       |    X     |       X         |        |
empty-state           |           |      X       |    X     |       X         |   X    |
loading-skeleton      |     X     |      X       |    X     |       X         |   X    |  X
export-button         |           |      X       |    X     |       X         |   X    |
slide-panel           |           |      X       |    X     |       X         |        |
ai-explanation        |           |      X       |    X     |       X         |   X    |
bulk-action-bar       |           |      X       |          |       X         |        |
```

---

## 4. Data Flow Architecture

### Request Flow

```
Browser URL Change
    |
    v
Next.js Router (App Router)
    |
    v
Page Component (Server Component shell)
    |
    v
Client Component (with "use client")
    |
    +--> TanStack Query hook (useRecommendations, useDashboardMetrics, etc.)
    |       |
    |       v
    |    api-client.ts (typed fetch wrapper)
    |       |
    |       v
    |    Next.js API Route (/app/api/v1/...)
    |       |
    |       v
    |    Express.js Backend (localhost:3001)
    |       |
    |       +--> SQLite (better-sqlite3, synchronous reads)
    |       |
    |       +--> Python Algorithm Engine (subprocess call or HTTP)
    |       |
    |       +--> Claude API (explanation generation, async)
    |       |
    |       v
    |    JSON Response
    |       |
    |       v
    |    TanStack Query Cache (stale-while-revalidate)
    |       |
    |       v
    +--- React renders with cached data
```

### API Proxy Pattern

Next.js API routes act as a thin proxy to the Express.js backend. This provides:
1. Same-origin requests (no CORS issues)
2. Server-side authentication token injection (future)
3. Response transformation if needed
4. Type safety at the boundary

```typescript
// app/api/v1/recommendations/route.ts (Next.js API Route)
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const response = await fetch(
    `${process.env.API_BACKEND_URL}/api/v1/recommendations?${searchParams}`,
    { headers: { /* auth headers */ } }
  );
  return Response.json(await response.json());
}
```

### Cache Strategy

| Data Type             | Stale Time | Refetch Interval | Rationale                         |
|-----------------------|------------|------------------|-----------------------------------|
| Dashboard metrics     | 60s        | 5 minutes        | Summary data, moderate freshness  |
| Cost trend            | 10 min     | None             | Historical, rarely changes        |
| Recommendations list  | 30s        | None             | Workflow data, user expects fresh  |
| User detail           | 60s        | None             | Read-mostly, navigated to often   |
| Algorithm results     | 60s        | None             | Batch-computed, changes on re-run |
| Security alerts       | 10s        | 60s              | Time-sensitive, auto-refresh      |
| Agent health          | 10s        | 60s              | Monitoring, needs freshness       |
| AI explanations       | 30 min     | None             | Expensive to generate, stable     |

### Optimistic Updates

Approve/reject/rollback mutations use optimistic updates for instant UI feedback:

```typescript
// Example: Approve recommendation with optimistic update
useMutation({
  mutationFn: approveRecommendation,
  onMutate: async (id) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['recommendations'] });
    // Snapshot previous value
    const previous = queryClient.getQueryData(['recommendations']);
    // Optimistically update
    queryClient.setQueryData(['recommendations'], (old) => ({
      ...old,
      recommendations: old.recommendations.map(r =>
        r.id === id ? { ...r, status: 'APPROVED' } : r
      )
    }));
    return { previous };
  },
  onError: (err, id, context) => {
    // Rollback on error
    queryClient.setQueryData(['recommendations'], context.previous);
  },
  onSettled: () => {
    // Refetch to ensure consistency
    queryClient.invalidateQueries({ queryKey: ['recommendations'] });
  },
});
```

---

## 5. Navigation Structure

### Sidebar Navigation

The sidebar is the primary navigation mechanism. It is always visible on desktop
(collapsible on mobile). The structure mirrors the route hierarchy.

```
+------------------------------------------+
| [LA] License Agent                       |
|      D365 FO Optimizer                   |
+------------------------------------------+
|                                          |
| > Dashboard                              |  /dashboard
|                                          |
| v License Optimization                   |  /optimization
|     Overview                             |  /optimization
|     Read-Only Users                      |  /optimization/readonly
|     License Minority                     |  /optimization/minority
|     Cross-Role                           |  /optimization/cross-role
|     Component Removal                    |  /optimization/component-removal
|     Role Splitting                       |  /optimization/role-splitting
|     Device License                       |  /optimization/device-license
|                                          |
| v Security & Compliance                  |  /security
|     Overview                             |  /security
|     SoD Violations                       |  /security/sod
|     Anomalous Activity                   |  /security/anomalies
|     Privilege Creep                      |  /security/privilege-creep
|     Compliance Reports                   |  /security/compliance
|                                          |
| > New User Wizard                        |  /wizard
|                                          |
| > Recommendations                        |  /recommendations
|                                          |
| > Administration                         |  /admin
|                                          |
+------------------------------------------+
| [*] Agent Healthy                        |  Status indicator
+------------------------------------------+
```

### Breadcrumb Navigation

Every page displays a breadcrumb trail below the header. Breadcrumbs are
generated dynamically from the URL path segments.

```
Dashboard > License Optimization > Read-Only Users > John Doe
Dashboard > Security > SoD Violations
Dashboard > Recommendations > REC-00142
```

**Implementation**: A `breadcrumbs.tsx` component reads `usePathname()` and maps
path segments to human-readable labels via a lookup table.

```typescript
const BREADCRUMB_LABELS: Record<string, string> = {
  'dashboard': 'Dashboard',
  'optimization': 'License Optimization',
  'readonly': 'Read-Only Users',
  'minority': 'License Minority',
  'cross-role': 'Cross-Role Optimization',
  'component-removal': 'Component Removal',
  'role-splitting': 'Role Splitting',
  'device-license': 'Device License',
  'security': 'Security & Compliance',
  'sod': 'SoD Violations',
  'anomalies': 'Anomalous Activity',
  'privilege-creep': 'Privilege Creep',
  'compliance': 'Compliance Reports',
  'wizard': 'New User Wizard',
  'recommendations': 'Recommendations',
  'admin': 'Administration',
  'algorithms': 'Algorithm Config',
  'scheduling': 'Scheduling',
};
```

### Drill-Down Navigation Paths

Every number on every page is a hyperlink. Here are the primary drill-down paths:

```
Path 1: Cost Overview
  Dashboard (Total Cost tile)
    -> /optimization (algorithm overview grid)
      -> /optimization/readonly (user table)
        -> Slide panel (user detail)
          -> /dashboard/users/[userId] (full user profile)

Path 2: Security Alert
  Dashboard (Alerts panel)
    -> /security/sod (violation table)
      -> Slide panel (violation detail + AI explanation)
        -> /dashboard/users/[userId] (offending user profile)

Path 3: Recommendation Workflow
  Dashboard (Pending count tile)
    -> /recommendations?status=PENDING (filtered list)
      -> /recommendations/[id] (full detail + approve/reject)
        -> /dashboard/users/[userId] (user context)

Path 4: New User Provisioning
  Sidebar (New User Wizard)
    -> /wizard Step 1 (select menu items)
      -> /wizard Step 2 (view recommendations)
        -> Apply action (creates recommendation record)
          -> /recommendations/[id] (track implementation)
```

---

## 6. State Management Strategy

### State Categories

| Category      | Technology        | Examples                                     |
|---------------|-------------------|----------------------------------------------|
| Server state  | TanStack Query    | Recommendations, metrics, users, alerts      |
| URL state     | nuqs or manual    | Filters, sort, pagination, active tab        |
| Form state    | React useState    | Wizard menu selection, search input, dialog  |
| Global UI     | React Context     | Sidebar collapsed, theme (future)            |

### URL State Management

Filters, sort order, pagination, and tabs are stored in URL search parameters.
This enables bookmarking and sharing of any filtered view.

```
/recommendations?status=PENDING&sort=savings&dir=desc&page=2&limit=50
/optimization/readonly?department=Finance&confidence=high&minReadPct=95
/security/sod?severity=CRITICAL&category=financial
```

**Implementation pattern**:

```typescript
// hooks/use-url-state.ts
import { useSearchParams, useRouter, usePathname } from 'next/navigation';

export function useUrlState<T extends Record<string, string>>(defaults: T) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const state = { ...defaults };
  for (const [key, value] of searchParams.entries()) {
    if (key in defaults) {
      state[key as keyof T] = value as T[keyof T];
    }
  }

  const setState = (updates: Partial<T>) => {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (value === undefined || value === defaults[key as keyof T]) {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    }
    router.push(`${pathname}?${params.toString()}`);
  };

  return [state, setState] as const;
}
```

### TanStack Query Key Convention

All query keys follow a hierarchical structure for targeted invalidation.

```typescript
export const queryKeys = {
  // Dashboard
  dashboard: {
    all: ['dashboard'] as const,
    metrics: ['dashboard', 'metrics'] as const,
    costTrend: (months: number) => ['dashboard', 'cost-trend', months] as const,
  },

  // Recommendations
  recommendations: {
    all: ['recommendations'] as const,
    list: (filters: RecommendationFilters) =>
      ['recommendations', 'list', filters] as const,
    detail: (id: string) => ['recommendations', 'detail', id] as const,
    user: (userId: string) => ['recommendations', 'user', userId] as const,
  },

  // Algorithm Results
  algorithms: {
    all: ['algorithms'] as const,
    overview: ['algorithms', 'overview'] as const,
    results: (algorithmId: string, filters: AlgorithmFilters) =>
      ['algorithms', 'results', algorithmId, filters] as const,
  },

  // Users
  users: {
    all: ['users'] as const,
    detail: (userId: string) => ['users', 'detail', userId] as const,
  },

  // Security
  security: {
    all: ['security'] as const,
    alerts: (filters: SecurityFilters) =>
      ['security', 'alerts', filters] as const,
    sod: (filters: SodFilters) => ['security', 'sod', filters] as const,
    anomalies: (filters: AnomalyFilters) =>
      ['security', 'anomalies', filters] as const,
    compliance: ['security', 'compliance'] as const,
  },

  // Agent
  agent: {
    health: ['agent', 'health'] as const,
    config: ['agent', 'config'] as const,
  },

  // AI Explanations (cached separately due to cost)
  explanations: {
    recommendation: (id: string) => ['explanations', 'recommendation', id] as const,
    user: (userId: string) => ['explanations', 'user', userId] as const,
  },
} as const;
```

---

## 7. SQLite Database Schema

SQLite serves as the local development database. The schema is designed for
eventual migration to Azure SQL (compatible SQL subset). Uses `better-sqlite3`
for synchronous operations.

### Entity Relationship Diagram

```
+------------------+     +----------------------+     +------------------+
| users            |     | recommendations      |     | algorithm_runs   |
|------------------|     |----------------------|     |------------------|
| id (PK)          |<-+  | id (PK)              |  +->| id (PK)          |
| email            |  |  | user_id (FK)         |--+  | algorithm_id     |
| display_name     |  +--| algorithm_run_id (FK) |     | started_at       |
| department       |     | type                 |     | completed_at     |
| current_license  |     | priority             |     | status           |
| monthly_cost     |     | confidence           |     | users_processed  |
| is_active        |     | current_license      |     | recs_generated   |
| last_activity    |     | recommended_license  |     | parameters       |
| created_at       |     | monthly_savings      |     +------------------+
| updated_at       |     | annual_savings       |
+------------------+     | status               |     +------------------+
                          | ai_explanation       |     | security_alerts  |
+------------------+      | created_at           |     |------------------|
| user_roles       |      | updated_at           |     | id (PK)          |
|------------------|      | expires_at           |     | type             |
| id (PK)          |      +----------------------+     | severity         |
| user_id (FK)     |                                   | user_id (FK)     |
| role_name        |      +----------------------+     | description      |
| assigned_at      |      | recommendation_audit |     | detected_at      |
| is_active        |      |----------------------|     | resolved_at      |
+------------------+      | id (PK)              |     | status           |
                           | recommendation_id FK |     +------------------+
+------------------+       | action               |
| user_activity    |       | actor                |     +------------------+
|------------------|       | comment              |     | algorithm_config |
| id (PK)          |       | timestamp            |     |------------------|
| user_id (FK)     |       +----------------------+     | id (PK)          |
| menu_item        |                                    | algorithm_id     |
| action_type      |       +----------------------+     | param_name       |
| timestamp        |       | sod_violations       |     | param_value      |
| form_name        |       |----------------------|     | updated_at       |
| license_required |       | id (PK)              |     | updated_by       |
+------------------+       | user_id (FK)         |     +------------------+
                            | role_a               |
+------------------+        | role_b               |     +------------------+
| security_config  |        | conflict_rule        |     | ai_explanations  |
|------------------|        | severity             |     |------------------|
| id (PK)          |        | category             |     | id (PK)          |
| role_name        |        | detected_at          |     | entity_type      |
| menu_item        |        | status               |     | entity_id        |
| security_object  |        +----------------------+     | explanation      |
| license_required |                                     | model_used       |
| entitlement_type |                                     | tokens_used      |
+------------------+                                     | generated_at     |
                                                         +------------------+
```

### SQL DDL

```sql
-- ============================================================
-- Core Tables
-- ============================================================

CREATE TABLE users (
    id TEXT PRIMARY KEY,                           -- email or user principal name
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    department TEXT,
    current_license TEXT NOT NULL,                  -- 'Team Members', 'Finance', etc.
    monthly_cost REAL NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,          -- SQLite boolean
    last_activity_at TEXT,                          -- ISO 8601
    roles_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_license ON users(current_license);
CREATE INDEX idx_users_active ON users(is_active);

-- ============================================================

CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    role_name TEXT NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, role_name)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_name);

-- ============================================================

CREATE TABLE user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    menu_item TEXT NOT NULL,                       -- AOT name
    action_type TEXT NOT NULL CHECK(action_type IN ('read', 'write', 'delete')),
    form_name TEXT,
    license_required TEXT,
    timestamp TEXT NOT NULL,                        -- ISO 8601
    session_id TEXT
);

CREATE INDEX idx_activity_user ON user_activity(user_id);
CREATE INDEX idx_activity_timestamp ON user_activity(timestamp);
CREATE INDEX idx_activity_action ON user_activity(action_type);

-- ============================================================

CREATE TABLE security_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL,
    menu_item TEXT NOT NULL,
    security_object TEXT,
    security_object_type TEXT,                      -- 'MenuItemDisplay', 'MenuItemAction', etc.
    license_required TEXT,
    entitlement_type TEXT,
    UNIQUE(role_name, menu_item, security_object)
);

CREATE INDEX idx_secconfig_role ON security_config(role_name);
CREATE INDEX idx_secconfig_menuitem ON security_config(menu_item);
CREATE INDEX idx_secconfig_license ON security_config(license_required);

-- ============================================================
-- Recommendation Workflow Tables
-- ============================================================

CREATE TABLE algorithm_runs (
    id TEXT PRIMARY KEY,                            -- UUID
    algorithm_id TEXT NOT NULL,                     -- '2.2', '2.5', '3.1', etc.
    algorithm_name TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'RUNNING'
        CHECK(status IN ('RUNNING', 'COMPLETED', 'FAILED')),
    users_processed INTEGER DEFAULT 0,
    recommendations_generated INTEGER DEFAULT 0,
    parameters TEXT                                 -- JSON string of algorithm parameters
);

CREATE INDEX idx_algo_runs_algorithm ON algorithm_runs(algorithm_id);
CREATE INDEX idx_algo_runs_status ON algorithm_runs(status);

-- ============================================================

CREATE TABLE recommendations (
    id TEXT PRIMARY KEY,                            -- 'REC-00001' format
    user_id TEXT NOT NULL REFERENCES users(id),
    algorithm_run_id TEXT REFERENCES algorithm_runs(id),
    algorithm_id TEXT NOT NULL,                     -- '2.2', '2.5', etc.
    type TEXT NOT NULL
        CHECK(type IN ('LICENSE_DOWNGRADE', 'LICENSE_UPGRADE', 'ROLE_REMOVAL',
                        'SOD_VIOLATION', 'SECURITY_ALERT', 'COST_OPTIMIZATION')),
    priority TEXT NOT NULL
        CHECK(priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    current_license TEXT NOT NULL,
    recommended_license TEXT,
    current_cost REAL NOT NULL,
    recommended_cost REAL,
    monthly_savings REAL NOT NULL DEFAULT 0,
    annual_savings REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'IMPLEMENTED', 'ROLLED_BACK')),
    details TEXT,                                   -- JSON: algorithm-specific data
    ai_explanation TEXT,                            -- Claude-generated explanation
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT                                 -- Recommendation validity window
);

CREATE INDEX idx_recs_user ON recommendations(user_id);
CREATE INDEX idx_recs_algorithm ON recommendations(algorithm_id);
CREATE INDEX idx_recs_status ON recommendations(status);
CREATE INDEX idx_recs_priority ON recommendations(priority);
CREATE INDEX idx_recs_savings ON recommendations(monthly_savings DESC);
CREATE INDEX idx_recs_created ON recommendations(created_at DESC);

-- ============================================================

CREATE TABLE recommendation_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT NOT NULL REFERENCES recommendations(id),
    action TEXT NOT NULL
        CHECK(action IN ('CREATED', 'APPROVED', 'REJECTED', 'IMPLEMENTED',
                          'ROLLED_BACK', 'EXPIRED', 'COMMENT')),
    actor TEXT NOT NULL,                            -- user email or 'system'
    comment TEXT,
    previous_status TEXT,
    new_status TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_audit_rec ON recommendation_audit(recommendation_id);
CREATE INDEX idx_audit_timestamp ON recommendation_audit(timestamp DESC);

-- ============================================================
-- Security Tables
-- ============================================================

CREATE TABLE security_alerts (
    id TEXT PRIMARY KEY,                            -- 'ALERT-00001' format
    type TEXT NOT NULL,                             -- 'SOD_VIOLATION', 'ANOMALOUS_ACCESS', etc.
    severity TEXT NOT NULL
        CHECK(severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    user_id TEXT NOT NULL REFERENCES users(id),
    description TEXT NOT NULL,
    details TEXT,                                   -- JSON: event-specific data
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK(status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED'))
);

CREATE INDEX idx_alerts_severity ON security_alerts(severity);
CREATE INDEX idx_alerts_type ON security_alerts(type);
CREATE INDEX idx_alerts_status ON security_alerts(status);
CREATE INDEX idx_alerts_detected ON security_alerts(detected_at DESC);

-- ============================================================

CREATE TABLE sod_violations (
    id TEXT PRIMARY KEY,                            -- 'SOD-00001' format
    user_id TEXT NOT NULL REFERENCES users(id),
    role_a TEXT NOT NULL,
    role_b TEXT NOT NULL,
    conflict_rule TEXT NOT NULL,                    -- Rule ID from SoD matrix
    severity TEXT NOT NULL
        CHECK(severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    category TEXT NOT NULL,                         -- 'financial', 'procurement', etc.
    description TEXT,
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK(status IN ('OPEN', 'MITIGATED', 'ACCEPTED', 'RESOLVED')),
    mitigation_notes TEXT
);

CREATE INDEX idx_sod_user ON sod_violations(user_id);
CREATE INDEX idx_sod_severity ON sod_violations(severity);
CREATE INDEX idx_sod_status ON sod_violations(status);

-- ============================================================
-- Configuration Tables
-- ============================================================

CREATE TABLE algorithm_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm_id TEXT NOT NULL,
    param_name TEXT NOT NULL,
    param_value TEXT NOT NULL,
    param_type TEXT NOT NULL DEFAULT 'string'
        CHECK(param_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_by TEXT NOT NULL DEFAULT 'system',
    UNIQUE(algorithm_id, param_name)
);

CREATE INDEX idx_algoconfig_algo ON algorithm_config(algorithm_id);

-- ============================================================
-- AI Explanation Cache
-- ============================================================

CREATE TABLE ai_explanations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,                      -- 'recommendation', 'user', 'sod_violation'
    entity_id TEXT NOT NULL,
    explanation TEXT NOT NULL,
    model_used TEXT NOT NULL DEFAULT 'claude-sonnet-4-5-20250514',
    tokens_used INTEGER,
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(entity_type, entity_id)
);

CREATE INDEX idx_explanations_entity ON ai_explanations(entity_type, entity_id);

-- ============================================================
-- Seed: Default Algorithm Configuration
-- ============================================================

INSERT INTO algorithm_config (algorithm_id, param_name, param_value, param_type, description) VALUES
    ('2.2', 'read_only_threshold', '0.95', 'number', 'Minimum read percentage to classify as read-only'),
    ('2.2', 'minimum_activity_days', '30', 'number', 'Minimum days of activity data required'),
    ('2.2', 'analysis_window_days', '90', 'number', 'Number of days to analyze'),
    ('2.5', 'minority_threshold', '0.15', 'number', 'Maximum usage percentage to classify as minority'),
    ('2.5', 'minimum_forms_accessed', '3', 'number', 'Minimum forms for meaningful analysis'),
    ('3.1', 'conflict_matrix_version', 'v1.0', 'string', 'SoD conflict matrix version'),
    ('3.2', 'anomaly_window_hours', '24', 'number', 'Time window for anomaly detection'),
    ('3.2', 'after_hours_start', '20', 'number', 'Start of after-hours period (24h format)'),
    ('3.2', 'after_hours_end', '6', 'number', 'End of after-hours period (24h format)'),
    ('3.3', 'creep_threshold_roles', '5', 'number', 'Role count threshold for privilege creep'),
    ('3.3', 'creep_review_months', '12', 'number', 'Months without review to flag'),
    ('4.1', 'min_users_per_device', '3', 'number', 'Minimum users sharing device for recommendation'),
    ('4.3', 'cross_app_overlap_threshold', '0.10', 'number', 'Minimum overlap percentage'),
    ('4.7', 'max_recommendations', '3', 'number', 'Maximum recommendations to return'),
    ('5.1', 'trend_months', '12', 'number', 'Months of trend data to analyze'),
    ('5.2', 'risk_weight_sod', '0.35', 'number', 'Weight for SoD violations in risk score'),
    ('5.2', 'risk_weight_privilege', '0.25', 'number', 'Weight for privilege creep in risk score'),
    ('5.2', 'risk_weight_anomaly', '0.25', 'number', 'Weight for anomalous activity'),
    ('5.2', 'risk_weight_orphaned', '0.15', 'number', 'Weight for orphaned account status');
```

### Seed Data Script

A separate seed script (`scripts/seed-database.ts`) will populate the database
with realistic test data for 100 users, 500 activity records, 50 recommendations,
and 10 security alerts. This enables full UI development without a live backend.

---

## 8. Express.js API Endpoints

### Architecture: apps/api/ Directory

The Express.js API is a standalone server in `apps/api/`. It communicates with
the SQLite database and the Python algorithm engine.

```
apps/api/
  src/
    index.ts                   # Express server entry point
    routes/
      dashboard.ts             # GET /api/v1/dashboard/metrics
      recommendations.ts       # CRUD /api/v1/recommendations
      algorithms.ts            # GET /api/v1/algorithms, POST /api/v1/analyze
      users.ts                 # GET /api/v1/users, GET /api/v1/users/:id
      security.ts              # GET /api/v1/security/alerts, sod, anomalies
      wizard.ts                # POST /api/v1/suggest-license
      agent.ts                 # GET /api/v1/agent/health, config
      explanations.ts          # GET /api/v1/explanations/:entityType/:entityId
    middleware/
      error-handler.ts         # Centralized error handling
      request-logger.ts        # Request/response logging
      validate.ts              # Zod schema validation middleware
    db/
      connection.ts            # better-sqlite3 connection singleton
      schema.sql               # DDL from Section 7
      seed.ts                  # Test data seeder
      migrations/              # Schema version migrations
    services/
      recommendation.service.ts  # Recommendation CRUD + workflow
      algorithm.service.ts       # Algorithm execution orchestration
      user.service.ts            # User queries
      security.service.ts        # Security alert queries
      dashboard.service.ts       # Dashboard metric aggregation
      explanation.service.ts     # Claude API integration
    types/
      index.ts                 # Shared TypeScript types
  package.json
  tsconfig.json
```

### Complete Endpoint List

```
METHOD  ENDPOINT                                       SERVICE              DESCRIPTION
------  ------                                         -------              -----------

-- Dashboard
GET     /api/v1/dashboard/metrics                      dashboard.service    Aggregated dashboard metrics
GET     /api/v1/dashboard/cost-trend?months=12         dashboard.service    Cost trend data (Algorithm 5.1)
GET     /api/v1/dashboard/opportunities?limit=5        dashboard.service    Top N optimization opportunities

-- Recommendations
GET     /api/v1/recommendations                        recommendation       List (filters: status, type, priority,
                                                                            department, sort, page, limit)
GET     /api/v1/recommendations/:id                    recommendation       Single recommendation detail
POST    /api/v1/recommendations/:id/approve            recommendation       Approve (body: { comment? })
POST    /api/v1/recommendations/:id/reject             recommendation       Reject (body: { reason })
POST    /api/v1/recommendations/:id/rollback           recommendation       Rollback (body: { speed })
GET     /api/v1/recommendations/export                 recommendation       Export as CSV (query params = filters)

-- Algorithms
GET     /api/v1/algorithms                             algorithm.service    List all algorithms with status
GET     /api/v1/algorithms/:id/results                 algorithm.service    Algorithm results (filters: dept,
                                                                            license, confidence, page, limit)
POST    /api/v1/analyze                                algorithm.service    Trigger analysis
                                                                            (body: { scope, algorithms[] })
GET     /api/v1/algorithms/:id/summary                 algorithm.service    Algorithm summary metrics

-- Users
GET     /api/v1/users                                  user.service         List users (filters: dept, license,
                                                                            active, search, page, limit)
GET     /api/v1/users/:id                              user.service         User detail (profile + activity +
                                                                            roles + recommendations)
GET     /api/v1/users/:id/activity                     user.service         User activity log (paginated)

-- Security
GET     /api/v1/security/overview                      security.service     Security dashboard metrics
GET     /api/v1/security/alerts                        security.service     Alert list (filters: severity,
                                                                            type, status, page, limit)
GET     /api/v1/security/sod                           security.service     SoD violations (filters: severity,
                                                                            category, status, page, limit)
GET     /api/v1/security/anomalies                     security.service     Anomalous events (filters: type,
                                                                            severity, dateRange, page, limit)
GET     /api/v1/security/compliance                    security.service     Compliance scorecard

-- New User Wizard
POST    /api/v1/suggest-license                        wizard               Menu items -> license recommendations
                                                                            (body: { requiredMenuItems[],
                                                                            includeSODCheck })
GET     /api/v1/menu-items?search=&module=             wizard               Searchable menu item list

-- Agent
GET     /api/v1/agent/health                           agent                Agent health status
GET     /api/v1/agent/config                           agent                All algorithm configurations
PUT     /api/v1/agent/config/:algorithmId              agent                Update algorithm parameters

-- AI Explanations
GET     /api/v1/explanations/:entityType/:entityId     explanation.service  Cached AI explanation
POST    /api/v1/explanations/generate                  explanation.service  Generate new explanation
                                                                            (body: { entityType, entityId, context })
```

### Standard Response Envelope

All API responses follow a consistent envelope:

```typescript
// Success response
{
  "data": { /* payload */ },
  "pagination"?: {
    "total": 1234,
    "page": 1,
    "limit": 50,
    "pages": 25
  },
  "meta"?: {
    "generatedAt": "2026-02-07T12:00:00Z",
    "queryTimeMs": 42
  }
}

// Error response
{
  "error": {
    "code": "RECOMMENDATION_NOT_FOUND",
    "message": "Recommendation REC-99999 does not exist",
    "status": 404
  }
}
```

### Validation Middleware

Every endpoint validates its inputs using Zod schemas, matching the Python
Pydantic models in `apps/agent/src/models/`.

```typescript
// middleware/validate.ts
import { z } from 'zod';
import { Request, Response, NextFunction } from 'express';

export function validate(schema: z.ZodSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse({
      body: req.body,
      query: req.query,
      params: req.params,
    });
    if (!result.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid request',
          details: result.error.flatten(),
          status: 400,
        },
      });
    }
    next();
  };
}
```

---

## 9. Claude AI Agent Integration

### Architecture Decision

The Claude API (Anthropic SDK) generates human-readable explanations for
algorithm results. It never makes license decisions. The deterministic algorithm
output is always the ground truth; the AI layer adds comprehension.

### Integration Points

| Feature                    | Trigger                          | Input                                   | Output                        |
|----------------------------|----------------------------------|-----------------------------------------|-------------------------------|
| Recommendation explanation | On recommendation detail view    | Algorithm output + user context         | 2-3 paragraph narrative       |
| User optimization summary  | On user detail view              | All recommendations for user            | Executive summary paragraph   |
| SoD violation explanation   | On SoD detail expansion          | Conflict rule + roles + user context    | Risk explanation + mitigation |
| Wizard recommendation note  | After wizard generates results   | Selected menu items + recommendations   | Why this combination is optimal |
| Dashboard insight          | On dashboard load (cached)       | Top 5 opportunities + alert summary     | One-sentence insight per item |

### Implementation: explanation.service.ts

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

interface ExplanationRequest {
  entityType: 'recommendation' | 'user' | 'sod_violation' | 'wizard';
  entityId: string;
  context: Record<string, unknown>;
}

export async function generateExplanation(
  request: ExplanationRequest
): Promise<string> {
  // Check cache first
  const cached = db.prepare(
    'SELECT explanation FROM ai_explanations WHERE entity_type = ? AND entity_id = ?'
  ).get(request.entityType, request.entityId);

  if (cached) return cached.explanation;

  // Build prompt based on entity type
  const systemPrompt = buildSystemPrompt(request.entityType);
  const userPrompt = buildUserPrompt(request);

  const response = await client.messages.create({
    model: 'claude-sonnet-4-5-20250514',
    max_tokens: 500,
    system: systemPrompt,
    messages: [{ role: 'user', content: userPrompt }],
  });

  const explanation = response.content[0].type === 'text'
    ? response.content[0].text
    : '';

  // Cache the result
  db.prepare(
    `INSERT OR REPLACE INTO ai_explanations
     (entity_type, entity_id, explanation, model_used, tokens_used, generated_at)
     VALUES (?, ?, ?, ?, ?, datetime('now'))`
  ).run(
    request.entityType,
    request.entityId,
    explanation,
    'claude-sonnet-4-5-20250514',
    response.usage.output_tokens
  );

  return explanation;
}

function buildSystemPrompt(entityType: string): string {
  const base = `You are a license optimization advisor for Microsoft Dynamics 365 Finance & Operations.
You explain algorithm results in clear, non-technical language that a system administrator
or finance manager can understand. Be concise (2-3 paragraphs max). Focus on the business
impact and recommended action. Never make license decisions -- only explain what the
deterministic algorithm determined and why.`;

  const typeSpecific: Record<string, string> = {
    recommendation: `${base}
Explain this license recommendation. Include: what was detected, why it matters,
what the savings would be, and what the admin should verify before approving.`,
    user: `${base}
Summarize this user's license optimization opportunities across all algorithms.
Highlight the most impactful recommendation and any security concerns.`,
    sod_violation: `${base}
Explain this Segregation of Duties violation. Include: what the conflict is,
why it is a risk (fraud, compliance), and how it can be mitigated.`,
    wizard: `${base}
Explain why this role and license combination is recommended for the new user.
Highlight cost efficiency and any SoD considerations.`,
  };

  return typeSpecific[entityType] || base;
}

function buildUserPrompt(request: ExplanationRequest): string {
  return `Here is the algorithm output to explain:\n\n${JSON.stringify(request.context, null, 2)}`;
}
```

### Cost Control

| Control Mechanism         | Implementation                                         |
|---------------------------|--------------------------------------------------------|
| Cache all explanations    | SQLite `ai_explanations` table with UNIQUE constraint  |
| Use Sonnet, not Opus      | Cost-effective for explanation generation               |
| 500 token max per call    | Keeps explanations concise and costs low               |
| Lazy generation           | Only generate when user views detail, never in bulk    |
| Cache TTL: 24 hours       | Expire stale explanations daily (algorithm re-runs)    |

### Estimated Costs

At 100 explanations/day with Sonnet at ~$3/MTok input, ~$15/MTok output:
- Average input: ~800 tokens/request = $0.0024/request
- Average output: ~400 tokens/request = $0.006/request
- Daily cost: 100 * $0.0084 = $0.84/day
- Monthly cost: ~$25/month

---

## 10. TDD Strategy

### Testing Pyramid

```
                    +------------------+
                    |   E2E (Playwright)|   5-10 critical user flows
                    |   ~10 tests      |
                    +------------------+
                   /                    \
          +---------------------------+
          |  Integration (API + DB)    |   Every endpoint, real SQLite
          |  ~50 tests                 |
          +---------------------------+
         /                              \
+--------------------------------------+
|  Unit (Components + Hooks + Utils)    |   Every component, every hook
|  ~150 tests                           |
+--------------------------------------+
```

### Test Tooling

| Layer       | Tool                         | Runner        | Purpose                    |
|-------------|------------------------------|---------------|----------------------------|
| Unit        | Jest + React Testing Library | `jest`        | Components, hooks, utils   |
| Integration | Jest + supertest             | `jest`        | API routes + SQLite        |
| E2E         | Playwright                   | `playwright`  | Full browser user flows    |
| Visual      | Storybook (future)           | `storybook`   | Component visual review    |

### Test Structure

```
apps/web/
  __tests__/
    unit/
      components/
        shared/
          metric-tile.test.tsx
          confidence-badge.test.tsx
          severity-badge.test.tsx
          status-badge.test.tsx
          filter-bar.test.tsx
          data-table.test.tsx
          pagination.test.tsx
          empty-state.test.tsx
          ai-explanation.test.tsx
        layout/
          sidebar.test.tsx
          header.test.tsx
          breadcrumbs.test.tsx
        charts/
          cost-trend-chart.test.tsx
          license-distribution.test.tsx
        features/
          dashboard/
            metrics-grid.test.tsx
            opportunity-list.test.tsx
            alerts-panel.test.tsx
          optimization/
            algorithm-tile.test.tsx
            algorithm-detail-layout.test.tsx
          recommendations/
            recommendation-card.test.tsx
            approval-dialog.test.tsx
            rejection-dialog.test.tsx
          wizard/
            menu-item-selector.test.tsx
            license-result-card.test.tsx
      hooks/
        use-url-state.test.ts
        use-dashboard-metrics.test.ts
        use-recommendations.test.ts
        use-algorithm-results.test.ts
      lib/
        api-client.test.ts
        utils.test.ts
        formatters.test.ts
    integration/
      api/
        dashboard.test.ts
        recommendations.test.ts
        algorithms.test.ts
        users.test.ts
        security.test.ts
        wizard.test.ts
        explanations.test.ts
    e2e/
      dashboard-flow.spec.ts
      recommendation-workflow.spec.ts
      optimization-drilldown.spec.ts
      security-alert-flow.spec.ts
      wizard-flow.spec.ts
      navigation.spec.ts
```

### What to Test (and What Not To)

**Always test**:
- Component renders with expected props
- Component renders loading state
- Component renders error state
- Component renders empty state
- Click handlers fire correct callbacks
- URL state changes when filters are applied
- API client sends correct requests
- API routes return correct response shapes
- API routes handle errors (404, 400, 500)
- Data transformations (formatCurrency, formatPercentage, etc.)
- TanStack Query hooks return correct states

**Never test**:
- Third-party library internals (shadcn/ui component rendering)
- CSS classes or styling (visual regression is for Storybook)
- Implementation details (avoid testing state variables directly)
- Mock API response format (that is the contract, not behavior)

### TDD Workflow Per Component

```
Step 1: Write the test
  - Create test file (e.g., metric-tile.test.tsx)
  - Write 3-5 test cases:
    a) Renders with required props
    b) Renders change indicator when change prop provided
    c) Does not render change indicator when change prop omitted
    d) Renders description when provided
    e) Handles click event (if clickable)
  - Run test, confirm RED (failure)

Step 2: Create the component
  - Write minimum code to pass all tests
  - Run test, confirm GREEN (pass)

Step 3: Refactor
  - Clean up, extract types, add JSDoc
  - Run test, confirm still GREEN
  - Commit: "feat: add MetricTile component with TDD"

Step 4: Integration
  - Import into page component
  - Write page-level test if needed
  - Run full suite
```

### Example Test: MetricTile Component

```typescript
// __tests__/unit/components/shared/metric-tile.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MetricTile } from '@/components/shared/metric-tile';

describe('MetricTile', () => {
  it('renders title and formatted value', () => {
    render(<MetricTile title="Total Cost" value={180000} format="currency" />);
    expect(screen.getByText('Total Cost')).toBeInTheDocument();
    expect(screen.getByText('$180,000')).toBeInTheDocument();
  });

  it('renders positive change indicator', () => {
    render(
      <MetricTile title="Savings" value={12500} format="currency"
                  change={{ value: 15, direction: 'up' }} />
    );
    expect(screen.getByText('+15%')).toBeInTheDocument();
    expect(screen.getByText('+15%')).toHaveClass('text-green-700');
  });

  it('renders description text', () => {
    render(
      <MetricTile title="Users" value={1234} format="number"
                  description="156 with pending recommendations" />
    );
    expect(screen.getByText('156 with pending recommendations')).toBeInTheDocument();
  });

  it('navigates to href on click', async () => {
    const user = userEvent.setup();
    render(
      <MetricTile title="Pending" value={156} format="number"
                  href="/recommendations?status=PENDING" />
    );
    const tile = screen.getByRole('link');
    expect(tile).toHaveAttribute('href', '/recommendations?status=PENDING');
  });

  it('renders loading skeleton when isLoading is true', () => {
    render(<MetricTile title="Cost" value={0} format="currency" isLoading />);
    expect(screen.getByTestId('metric-tile-skeleton')).toBeInTheDocument();
  });
});
```

### Example Test: Recommendations API Route

```typescript
// __tests__/integration/api/recommendations.test.ts
import request from 'supertest';
import { createApp } from '@/api/src/index';
import { seedTestDatabase, resetTestDatabase } from './helpers';

let app: Express.Application;

beforeAll(async () => {
  app = createApp({ dbPath: ':memory:' });
  seedTestDatabase(app.locals.db);
});

afterAll(() => {
  resetTestDatabase(app.locals.db);
});

describe('GET /api/v1/recommendations', () => {
  it('returns paginated recommendations', async () => {
    const res = await request(app)
      .get('/api/v1/recommendations')
      .expect(200);

    expect(res.body.data).toBeInstanceOf(Array);
    expect(res.body.pagination).toHaveProperty('total');
    expect(res.body.pagination).toHaveProperty('page');
    expect(res.body.pagination).toHaveProperty('limit');
  });

  it('filters by status', async () => {
    const res = await request(app)
      .get('/api/v1/recommendations?status=PENDING')
      .expect(200);

    for (const rec of res.body.data) {
      expect(rec.status).toBe('PENDING');
    }
  });

  it('sorts by savings descending by default', async () => {
    const res = await request(app)
      .get('/api/v1/recommendations')
      .expect(200);

    const savings = res.body.data.map((r: any) => r.monthlySavings);
    expect(savings).toEqual([...savings].sort((a: number, b: number) => b - a));
  });

  it('returns 400 for invalid status filter', async () => {
    const res = await request(app)
      .get('/api/v1/recommendations?status=INVALID')
      .expect(400);

    expect(res.body.error.code).toBe('VALIDATION_ERROR');
  });
});

describe('POST /api/v1/recommendations/:id/approve', () => {
  it('transitions status from PENDING to APPROVED', async () => {
    const res = await request(app)
      .post('/api/v1/recommendations/REC-00001/approve')
      .send({ comment: 'Verified with user' })
      .expect(200);

    expect(res.body.data.status).toBe('APPROVED');
  });

  it('creates audit trail entry', async () => {
    // Approve, then check audit
    await request(app)
      .post('/api/v1/recommendations/REC-00002/approve')
      .send({})
      .expect(200);

    const detail = await request(app)
      .get('/api/v1/recommendations/REC-00002')
      .expect(200);

    const auditEntry = detail.body.data.audit.find(
      (a: any) => a.action === 'APPROVED'
    );
    expect(auditEntry).toBeDefined();
    expect(auditEntry.new_status).toBe('APPROVED');
  });

  it('returns 404 for non-existent recommendation', async () => {
    await request(app)
      .post('/api/v1/recommendations/REC-99999/approve')
      .expect(404);
  });

  it('returns 409 when already approved', async () => {
    // Approve first
    await request(app)
      .post('/api/v1/recommendations/REC-00003/approve')
      .expect(200);

    // Try to approve again
    await request(app)
      .post('/api/v1/recommendations/REC-00003/approve')
      .expect(409);
  });
});
```

---

## 11. Parallel Execution Plan

### Dependency Graph

Pages and components are organized into waves. Within each wave, all items
can be built in parallel by separate agents or developers.

```
WAVE 0: Foundation (Sequential - Must Complete First)
  |
  +-> [0.1] Testing infrastructure (Jest, RTL, Playwright setup)
  +-> [0.2] UI primitives (shadcn/ui components: button, card, badge, input, select, tabs, etc.)
  +-> [0.3] Shared components (metric-tile, confidence-badge, severity-badge, etc.)
  +-> [0.4] Layout components (sidebar refactor, header, breadcrumbs, page-header)
  +-> [0.5] Express.js API scaffold (server, routing, middleware, DB connection)
  +-> [0.6] SQLite schema + seed data
  +-> [0.7] Data table component (sortable, filterable, paginated - most reused component)
  +-> [0.8] URL state hook (useUrlState)
  +-> [0.9] API client refactor (new endpoints, response envelope)
  +-> [0.10] TanStack Query hooks (all query keys + hooks)
  |
  v
WAVE 1: Core Pages (Parallel - 4 Tracks)
  |
  +-> Track A: Dashboard
  |     [1.1] Dashboard page (/dashboard)
  |     [1.2] Chart components (cost-trend, license-distribution)
  |     [1.3] Opportunity list + Alerts panel
  |
  +-> Track B: Recommendations Workflow
  |     [1.4] Recommendations list page (/recommendations)
  |     [1.5] Recommendation detail page (/recommendations/[id])
  |     [1.6] Approve/Reject/Rollback dialogs
  |
  +-> Track C: API Endpoints (Backend)
  |     [1.7] Dashboard endpoints + service
  |     [1.8] Recommendations CRUD + workflow endpoints
  |     [1.9] Users endpoints + service
  |     [1.10] Security endpoints + service
  |
  +-> Track D: New User Wizard
  |     [1.11] Wizard page refactor (/wizard)
  |     [1.12] POST /api/v1/suggest-license endpoint
  |     [1.13] GET /api/v1/menu-items endpoint
  |
  v
WAVE 2: Algorithm Detail Pages (Parallel - 3 Tracks)
  |
  +-> Track E: Optimization Pages
  |     [2.1] Optimization overview (/optimization)
  |     [2.2] Algorithm detail layout (shared)
  |     [2.3] Read-Only Users page (/optimization/readonly)
  |     [2.4] License Minority page (/optimization/minority)
  |     [2.5] Cross-Role page (/optimization/cross-role)
  |
  +-> Track F: More Optimization + Device
  |     [2.6] Component Removal page (/optimization/component-removal)
  |     [2.7] Role Splitting page (/optimization/role-splitting)
  |     [2.8] Device License page (/optimization/device-license)
  |
  +-> Track G: Security Pages
  |     [2.9] Security overview (/security)
  |     [2.10] SoD Violations page (/security/sod)
  |     [2.11] Anomalous Activity page (/security/anomalies)
  |     [2.12] Privilege Creep page (/security/privilege-creep)
  |     [2.13] Compliance Reports page (/security/compliance)
  |
  v
WAVE 3: Enhancement (Parallel - 3 Tracks)
  |
  +-> Track H: AI + User Detail
  |     [3.1] Claude AI explanation service
  |     [3.2] AI explanation component
  |     [3.3] User detail page (/dashboard/users/[userId])
  |
  +-> Track I: Administration
  |     [3.4] Admin page (/admin)
  |     [3.5] Algorithm config page (/admin/algorithms)
  |     [3.6] Scheduling page (/admin/scheduling)
  |
  +-> Track J: Polish
  |     [3.7] Search functionality (header search bar)
  |     [3.8] Notification system (alert dropdown)
  |     [3.9] Export CSV/PDF implementation
  |     [3.10] Error boundaries + fallback UI
  |
  v
WAVE 4: E2E Tests + Integration (Sequential)
  |
  +-> [4.1] E2E test: Dashboard flow
  +-> [4.2] E2E test: Recommendation approval flow
  +-> [4.3] E2E test: Optimization drill-down flow
  +-> [4.4] E2E test: Security alert flow
  +-> [4.5] E2E test: Wizard flow
  +-> [4.6] E2E test: Navigation + breadcrumbs
  +-> [4.7] Full integration smoke test
  +-> [4.8] Performance audit (Lighthouse)
```

### Estimated Effort Per Wave

| Wave | Items | Parallel Tracks | Sequential Estimate | Parallel Estimate |
|------|-------|-----------------|---------------------|-------------------|
| 0    | 10    | 1 (sequential)  | 16-20 hours         | 16-20 hours       |
| 1    | 13    | 4               | 24-32 hours         | 8-10 hours        |
| 2    | 13    | 3               | 20-28 hours         | 8-10 hours        |
| 3    | 10    | 3               | 16-24 hours         | 6-8 hours         |
| 4    | 8     | 1 (sequential)  | 8-12 hours          | 8-12 hours        |
| **Total** |  | -              | **84-116 hours**    | **46-60 hours**   |

### Safe Parallelization Rules

1. **Wave boundaries are hard gates.** Do not start Wave N+1 until Wave N is complete.
   Foundation components must exist before page components can import them.

2. **Within a wave, tracks are independent.** Track A (Dashboard) has no dependency
   on Track B (Recommendations). They share only Wave 0 components.

3. **API and UI can parallel within the same wave** because the API contract
   (types in `types/api.ts`) is defined in Wave 0. UI developers code against types;
   API developers implement against types. They converge at integration.

4. **Test files live with implementation.** When building `metric-tile.tsx`,
   the corresponding `metric-tile.test.tsx` is created first (TDD). This means
   testing is not a separate phase -- it is built into every task.

5. **The data-table component (Wave 0.7) is the critical path.** It is used
   by 8+ pages. Any delay here blocks Wave 1 and Wave 2. Prioritize it.

---

## 12. File Tree Reference

Complete file tree for the production web application after all waves are complete.

```
apps/web/
  app/
    (root)
      page.tsx                             # Redirect to /dashboard
      layout.tsx                           # Root layout (sidebar + header + main)
      providers.tsx                        # TanStack Query + future providers
      globals.css                          # Tailwind base + custom tokens
      not-found.tsx                        # Custom 404 page

    dashboard/
      page.tsx                             # Executive dashboard
      loading.tsx                          # Dashboard skeleton
      users/
        [userId]/
          page.tsx                         # User detail page
          loading.tsx                      # User detail skeleton

    optimization/
      page.tsx                             # Optimization overview (tile grid)
      loading.tsx
      layout.tsx                           # Shared layout for optimization section
      readonly/
        page.tsx                           # Algorithm 2.2: Read-Only Users
        loading.tsx
      minority/
        page.tsx                           # Algorithm 2.5: License Minority
        loading.tsx
      cross-role/
        page.tsx                           # Algorithm 4.3: Cross-Role
        loading.tsx
      component-removal/
        page.tsx                           # Algorithm 1.4: Component Removal
        loading.tsx
      role-splitting/
        page.tsx                           # Algorithm 1.3: Role Splitting
        loading.tsx
      device-license/
        page.tsx                           # Algorithm 4.1: Device License
        loading.tsx

    security/
      page.tsx                             # Security overview dashboard
      loading.tsx
      layout.tsx                           # Shared layout for security section
      sod/
        page.tsx                           # SoD Violations
        loading.tsx
      anomalies/
        page.tsx                           # Anomalous Activity
        loading.tsx
      privilege-creep/
        page.tsx                           # Privilege Creep
        loading.tsx
      compliance/
        page.tsx                           # Compliance Reports
        loading.tsx

    recommendations/
      page.tsx                             # Recommendation list with tabs
      loading.tsx
      [id]/
        page.tsx                           # Recommendation detail
        loading.tsx

    wizard/
      page.tsx                             # New User License Wizard

    admin/
      page.tsx                             # Admin overview
      loading.tsx
      algorithms/
        page.tsx                           # Algorithm configuration
      scheduling/
        page.tsx                           # Agent scheduling

    api/
      v1/
        dashboard/
          metrics/route.ts                 # Proxy to Express backend
          cost-trend/route.ts
          opportunities/route.ts
        recommendations/
          route.ts                         # List + create
          [id]/
            route.ts                       # Detail
            approve/route.ts               # Approve action
            reject/route.ts                # Reject action
            rollback/route.ts              # Rollback action
          export/route.ts                  # Export CSV
        algorithms/
          route.ts                         # List algorithms
          [id]/
            results/route.ts               # Algorithm results
            summary/route.ts               # Algorithm summary
        users/
          route.ts                         # List users
          [id]/
            route.ts                       # User detail
            activity/route.ts              # User activity
        security/
          overview/route.ts
          alerts/route.ts
          sod/route.ts
          anomalies/route.ts
          compliance/route.ts
        wizard/
          suggest-license/route.ts
          menu-items/route.ts
        agent/
          health/route.ts
          config/route.ts
        explanations/
          route.ts                         # Generate
          [entityType]/
            [entityId]/route.ts            # Get cached

  components/
    ui/                                    # shadcn/ui primitives
      badge.tsx
      button.tsx
      card.tsx
      data-table.tsx
      dialog.tsx
      dropdown-menu.tsx
      input.tsx
      select.tsx
      skeleton.tsx
      tabs.tsx
      tooltip.tsx

    shared/                                # Project-specific reusable
      metric-tile.tsx
      confidence-badge.tsx
      severity-badge.tsx
      status-badge.tsx
      license-badge.tsx
      savings-display.tsx
      user-avatar.tsx
      filter-bar.tsx
      sort-header.tsx
      pagination.tsx
      empty-state.tsx
      error-boundary.tsx
      loading-skeleton.tsx
      export-button.tsx
      bulk-action-bar.tsx
      slide-panel.tsx
      ai-explanation.tsx

    charts/
      cost-trend-chart.tsx
      license-distribution.tsx
      department-bar-chart.tsx
      confidence-histogram.tsx
      savings-waterfall.tsx

    layout/
      sidebar.tsx
      header.tsx
      breadcrumbs.tsx
      page-header.tsx

    features/
      dashboard/
        metrics-grid.tsx
        opportunity-list.tsx
        alerts-panel.tsx
      optimization/
        algorithm-tile.tsx
        algorithm-detail-layout.tsx
        user-recommendation-row.tsx
        recommendation-detail-panel.tsx
      security/
        sod-violation-row.tsx
        anomaly-event-row.tsx
        compliance-scorecard.tsx
        security-event-timeline.tsx
      recommendations/
        recommendation-card.tsx
        approval-dialog.tsx
        rejection-dialog.tsx
        rollback-dialog.tsx
        recommendation-timeline.tsx
      wizard/
        menu-item-selector.tsx
        license-result-card.tsx
        sod-conflict-warning.tsx
      admin/
        algorithm-config-form.tsx
        schedule-config.tsx
        pricing-editor.tsx
        agent-health-card.tsx

  hooks/
    use-url-state.ts                       # URL search param state management
    use-debounce.ts                        # Input debounce for search
    use-media-query.ts                     # Responsive breakpoint detection

  lib/
    api-client.ts                          # Typed HTTP client
    query-hooks.ts                         # TanStack Query hooks
    query-keys.ts                          # Centralized query key factory
    utils.ts                               # cn() and general utilities
    formatters.ts                          # formatCurrency, formatPercentage, formatDate
    constants.ts                           # License types, colors, labels, thresholds

  types/
    api.ts                                 # API request/response types
    algorithms.ts                          # Algorithm-specific types
    filters.ts                             # Filter parameter types
    navigation.ts                          # Navigation/routing types

  __tests__/
    unit/
      components/
        shared/                            # Tests for all shared components
        layout/                            # Tests for layout components
        charts/                            # Tests for chart components
        features/                          # Tests for feature components
      hooks/                               # Tests for custom hooks
      lib/                                 # Tests for utilities
    integration/
      api/                                 # Tests for API routes
    e2e/                                   # Playwright E2E tests
    helpers/                               # Test utilities, factories, mocks

  public/
    favicon.ico

  .env.local                               # Local environment variables
  .env.local.example                       # Template
  jest.config.ts                           # Jest configuration
  jest.setup.ts                            # Jest setup (RTL, mocks)
  playwright.config.ts                     # Playwright configuration
  next.config.ts                           # Next.js configuration
  tailwind.config.ts                       # Tailwind + custom brand colors
  tsconfig.json                            # TypeScript configuration
  package.json                             # Dependencies
```

```
apps/api/
  src/
    index.ts                               # Express server + middleware
    routes/
      dashboard.ts
      recommendations.ts
      algorithms.ts
      users.ts
      security.ts
      wizard.ts
      agent.ts
      explanations.ts
    middleware/
      error-handler.ts
      request-logger.ts
      validate.ts
    db/
      connection.ts                        # better-sqlite3 singleton
      schema.sql                           # DDL from Section 7
      seed.ts                              # Test data seeder
      migrations/
        001-initial.sql
    services/
      recommendation.service.ts
      algorithm.service.ts
      user.service.ts
      security.service.ts
      dashboard.service.ts
      explanation.service.ts
    types/
      index.ts
  package.json
  tsconfig.json
```

---

## Appendix A: Color System

| Token            | Value       | Usage                                      |
|------------------|-------------|--------------------------------------------|
| `brand-50`       | `#eff6ff`   | Selected state backgrounds                 |
| `brand-600`      | `#2563eb`   | Primary buttons, active nav                |
| `brand-700`      | `#1d4ed8`   | Primary button hover                       |
| `green-600`      | `#16a34a`   | Positive changes, approved status          |
| `green-50`       | `#f0fdf4`   | HIGH confidence background                 |
| `yellow-600`     | `#ca8a04`   | Warning, MEDIUM confidence                 |
| `yellow-50`      | `#fefce8`   | MEDIUM/PENDING background                  |
| `red-600`        | `#dc2626`   | Critical alerts, rejected                  |
| `red-50`         | `#fef2f2`   | LOW confidence, error background           |
| `orange-600`     | `#ea580c`   | SoD conflicts, warnings                    |
| `gray-50`        | `#f9fafb`   | Page background                            |
| `gray-500`       | `#6b7280`   | Secondary text                             |
| `gray-900`       | `#111827`   | Primary text                               |

---

## Appendix B: License Type Display Mapping

| Internal Value       | Display Label     | Badge Color         |
|----------------------|-------------------|---------------------|
| `Team Members`       | Team Members      | `bg-blue-100`       |
| `Operations`         | Operations        | `bg-purple-100`     |
| `Operations - Activity` | Ops Activity   | `bg-purple-50`      |
| `Finance`            | Finance           | `bg-emerald-100`    |
| `SCM`                | SCM               | `bg-amber-100`      |
| `Commerce`           | Commerce          | `bg-rose-100`       |
| `Device License`     | Device            | `bg-gray-100`       |

---

## Appendix C: Algorithm-to-Page Mapping

| Algorithm ID | Algorithm Name                    | Primary Page                     | Secondary Pages         |
|--------------|-----------------------------------|----------------------------------|-------------------------|
| 1.1          | Role License Composition          | /optimization (overview tile)    | -                       |
| 1.3          | Role Splitting Recommender        | /optimization/role-splitting     | /recommendations        |
| 1.4          | Component Removal Recommender     | /optimization/component-removal  | /recommendations        |
| 2.2          | Read-Only User Detector           | /optimization/readonly           | /recommendations        |
| 2.5          | License Minority Detection        | /optimization/minority           | /recommendations        |
| 3.1          | SoD Violation Detector            | /security/sod                    | /security               |
| 3.2          | Anomalous Role Change Detector    | /security/anomalies              | /security               |
| 3.3          | Privilege Creep Detector          | /security/privilege-creep        | /security               |
| 3.4          | Toxic Combination Detector        | /security/sod (combined)         | /security               |
| 4.1          | Device License Opportunity        | /optimization/device-license     | /recommendations        |
| 4.3          | Cross-Application Analyzer        | /optimization/cross-role         | /recommendations        |
| 4.7          | New User License Recommendation   | /wizard                          | /recommendations        |
| 5.1          | License Cost Trend Analysis       | /dashboard (chart)               | -                       |
| 5.2          | Security Risk Scoring             | /security (compliance score)     | /security/compliance    |

---

## Appendix D: Environment Variables

```bash
# apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:3001          # Express.js backend URL
NEXT_PUBLIC_APP_NAME="D365 FO License Agent"       # Display name

# apps/api/.env
PORT=3001                                          # Express.js port
DATABASE_PATH=./data/dev.db                        # SQLite database file
ANTHROPIC_API_KEY=sk-ant-...                       # Claude API key
PYTHON_ENGINE_PATH=../../apps/agent                # Path to Python algorithm engine
LOG_LEVEL=info                                     # Logging level
```

---

**End of Production Architecture Document**
