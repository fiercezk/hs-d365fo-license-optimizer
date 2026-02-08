import { cn } from "@/lib/utils";

/**
 * Dashboard metric card for key KPIs.
 *
 * Per Requirements/14: Executive dashboard shows 4 key metrics:
 *   Total Cost, Monthly Savings, YTD Savings, Users Optimized
 */
interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  description?: string;
}

export function MetricCard({
  title,
  value,
  change,
  changeType = "neutral",
  description,
}: MetricCardProps) {
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        {change && (
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2 py-1 text-xs font-medium",
              changeType === "positive" &&
                "bg-green-50 text-green-700",
              changeType === "negative" &&
                "bg-red-50 text-red-700",
              changeType === "neutral" &&
                "bg-gray-50 text-gray-700",
            )}
          >
            {change}
          </span>
        )}
      </div>
      <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
      {description && (
        <p className="mt-1 text-sm text-gray-500">{description}</p>
      )}
    </div>
  );
}
