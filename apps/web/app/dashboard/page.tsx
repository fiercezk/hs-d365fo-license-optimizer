import { MetricCard } from "@/components/dashboard/metric-card";
import { OpportunityList } from "@/components/dashboard/opportunity-list";
import { AlertsPanel } from "@/components/dashboard/alerts-panel";
import type { TopOpportunity, SecurityAlert } from "@/types/api";

/**
 * Executive Dashboard (Dashboard 1 per Requirements/14).
 *
 * Shows:
 *   - Key metrics: Total Cost, Monthly Savings, YTD Savings, Users Optimized
 *   - Top 5 Optimization Opportunities
 *   - Security Alerts
 *   - Cost Trend Chart (placeholder for Recharts integration)
 *
 * Data fetched via TanStack Query hooks (useDashboardMetrics).
 * This scaffold uses static placeholder data. Replace with real API calls.
 */

// Placeholder data for scaffold demonstration
const PLACEHOLDER_OPPORTUNITIES: TopOpportunity[] = [
  {
    algorithm: "2.2",
    name: "Read-Only Users",
    userCount: 234,
    monthlySavings: 28080,
    annualSavings: 336960,
  },
  {
    algorithm: "2.5",
    name: "License Minority Detection",
    userCount: 89,
    monthlySavings: 15000,
    annualSavings: 180000,
  },
  {
    algorithm: "3.5",
    name: "Orphaned Accounts",
    userCount: 12,
    monthlySavings: 2160,
    annualSavings: 25920,
  },
  {
    algorithm: "1.4",
    name: "Component Removal",
    userCount: 45,
    monthlySavings: 8100,
    annualSavings: 97200,
  },
  {
    algorithm: "1.3",
    name: "Role Splitting",
    userCount: 3,
    monthlySavings: 25000,
    annualSavings: 300000,
  },
];

const PLACEHOLDER_ALERTS: SecurityAlert[] = [
  {
    id: "ALERT-001",
    type: "SOD_VIOLATION",
    severity: "CRITICAL",
    description: "john.doe@contoso.com has conflicting roles: AP Clerk + Vendor Master",
    userId: "john.doe@contoso.com",
    detectedAt: "2026-02-07T02:34:00Z",
  },
  {
    id: "ALERT-002",
    type: "ANOMALOUS_ACCESS",
    severity: "HIGH",
    description: "jane.smith@contoso.com accessed 3 critical forms at 2 AM Saturday",
    userId: "jane.smith@contoso.com",
    detectedAt: "2026-02-07T02:00:00Z",
  },
  {
    id: "ALERT-003",
    type: "PRIVILEGE_CREEP",
    severity: "MEDIUM",
    description: "mike.wilson@contoso.com accumulated 12 roles over 18 months without review",
    userId: "mike.wilson@contoso.com",
    detectedAt: "2026-02-06T14:15:00Z",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Executive Dashboard
        </h1>
        <p className="text-sm text-gray-500">
          License optimization and security compliance overview
        </p>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total License Cost"
          value="$180,000"
          change="-3.2%"
          changeType="positive"
          description="Monthly across all users"
        />
        <MetricCard
          title="Monthly Savings"
          value="$12,500"
          change="+15%"
          changeType="positive"
          description="From implemented recommendations"
        />
        <MetricCard
          title="YTD Savings"
          value="$75,000"
          change="+22%"
          changeType="positive"
          description="Cumulative 2026 savings"
        />
        <MetricCard
          title="Users Analyzed"
          value="1,234"
          description="156 with pending recommendations"
        />
      </div>

      {/* Cost Trend Chart Placeholder */}
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">
          License Cost Trend (Last 12 Months)
        </h3>
        <div className="mt-4 flex h-64 items-center justify-center rounded-lg bg-gray-50 text-gray-400">
          {/* Replace with Recharts LineChart component */}
          <p className="text-sm">
            Recharts LineChart: License cost over time (actual vs. forecast).
            Connect to Algorithm 5.1 trend analysis data.
          </p>
        </div>
      </div>

      {/* Two-Column: Opportunities + Alerts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <OpportunityList opportunities={PLACEHOLDER_OPPORTUNITIES} />
        <AlertsPanel alerts={PLACEHOLDER_ALERTS} />
      </div>
    </div>
  );
}
