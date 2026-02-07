# D365 FO License Agent - Web Application

Next.js 15 web application for the D365 FO License & Security Optimization Agent.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **UI**: shadcn/ui + Tailwind CSS
- **State**: TanStack Query (React Query) for server-state management
- **Charts**: Recharts (placeholder - add charts to dashboard)
- **Types**: TypeScript strict mode
- **Hosting**: Azure Static Web Apps (Free tier)

## Directory Structure

```
apps/web/
  app/                      # Next.js App Router pages
    layout.tsx              # Root layout (sidebar + header)
    page.tsx                # Root redirect to /dashboard
    providers.tsx           # Client providers (TanStack Query)
    globals.css             # Tailwind base styles
    dashboard/
      page.tsx              # Executive dashboard (Dashboard 1)
    algorithms/
      page.tsx              # License optimization overview (Dashboard 2)
    wizard/
      page.tsx              # New User License Wizard (Dashboard 5)
    recommendations/
      page.tsx              # Recommendation management
    admin/
      page.tsx              # Agent configuration
    api/v1/                 # API route stubs (mock data for dev)
      recommendations/
        route.ts
      health/
        route.ts
  components/
    layout/
      sidebar.tsx           # Main navigation sidebar
      header.tsx            # Top header with search
    dashboard/
      metric-card.tsx       # KPI metric card component
      opportunity-list.tsx  # Top opportunities list
      alerts-panel.tsx      # Security alerts panel
    ui/                     # shadcn/ui components (add as needed)
    algorithms/             # Algorithm-specific components
  lib/
    utils.ts                # Utility functions (cn, formatCurrency, etc.)
    api-client.ts           # Typed API client for Azure Functions backend
    query-hooks.ts          # TanStack Query hooks for data fetching
  types/
    api.ts                  # TypeScript types matching Python Pydantic models
  public/                   # Static assets
```

## Getting Started

### Prerequisites

- Node.js 22+ (LTS)
- bun (preferred) or npm

### Install Dependencies

```bash
cd apps/web
bun install
```

### Development Server

```bash
bun dev
```

Open [http://localhost:3000](http://localhost:3000).

### Build for Production

```bash
bun run build
```

### Type Checking

```bash
bun run type-check
```

## Pages

| Path | Component | Description |
|------|-----------|-------------|
| `/dashboard` | Executive Dashboard | Key metrics, trends, opportunities, alerts |
| `/algorithms` | License Optimization | Recommendation table with filters and bulk actions |
| `/wizard` | New User Wizard | Menu item selection + license recommendation |
| `/recommendations` | Recommendation Management | Approval/rejection workflow |
| `/admin` | Administration | Agent config, scheduling, parameters |

## API Integration

The web app communicates with Azure Functions via typed API client (`lib/api-client.ts`).

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/recommendations` | List recommendations |
| GET | `/api/v1/recommendations/{userId}` | User recommendations |
| POST | `/api/v1/analyze` | Trigger analysis |
| POST | `/api/v1/suggest-license` | New user wizard |
| GET | `/api/v1/agent/health` | Agent health status |
| GET | `/api/v1/reports/{type}` | Generate reports |

### TanStack Query Hooks

All data fetching uses centralized hooks in `lib/query-hooks.ts`:

- `useDashboardMetrics()` - Dashboard KPIs
- `useRecommendations(filters)` - Filtered recommendations
- `useTriggerAnalysis()` - Mutation to start analysis
- `useSuggestLicense()` - Mutation for wizard
- `useAgentHealth()` - Agent status

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Azure Functions backend URL | `http://localhost:7071` |
| `NEXT_PUBLIC_APP_ENV` | Environment name | `development` |

## Deployment

Deployed to Azure Static Web Apps via GitHub Actions or Azure DevOps.

```bash
# Link to Azure Static Web Apps
az staticwebapp create --name d365licagent-dev-swa --resource-group d365licagent-dev-rg
```

## Design System

- **Colors**: Brand blue (#3b82f6), severity-based (red/orange/yellow/green)
- **Typography**: Inter (body), JetBrains Mono (code)
- **Components**: shadcn/ui (copy-paste, not dependency)
- **Layout**: Sidebar navigation + header + content area
