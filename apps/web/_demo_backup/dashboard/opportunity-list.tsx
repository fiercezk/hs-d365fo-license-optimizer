import { formatCurrency } from "@/lib/utils";
import type { TopOpportunity } from "@/types/api";

/**
 * Top optimization opportunities list.
 *
 * Per Requirements/14: Dashboard shows Top 5 Optimization Opportunities
 * with user count and monthly savings for each.
 */
interface OpportunityListProps {
  opportunities: TopOpportunity[];
}

export function OpportunityList({ opportunities }: OpportunityListProps) {
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">
        Top Optimization Opportunities
      </h3>
      <div className="mt-4 space-y-3">
        {opportunities.map((opp, index) => (
          <div
            key={opp.algorithm}
            className="flex items-center justify-between rounded-lg bg-gray-50 p-3"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-xs font-medium text-brand-700">
                {index + 1}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-900">{opp.name}</p>
                <p className="text-xs text-gray-500">
                  {opp.userCount} users affected
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-green-600">
                {formatCurrency(opp.monthlySavings)}/mo
              </p>
              <p className="text-xs text-gray-500">
                {formatCurrency(opp.annualSavings)}/yr
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
