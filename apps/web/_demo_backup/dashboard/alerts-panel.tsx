import { cn, getSeverityColor } from "@/lib/utils";
import type { SecurityAlert } from "@/types/api";

/**
 * Security alerts panel.
 *
 * Per Requirements/14: Dashboard shows active security alerts
 * with severity indicators and descriptions.
 */
interface AlertsPanelProps {
  alerts: SecurityAlert[];
}

export function AlertsPanel({ alerts }: AlertsPanelProps) {
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          Security Alerts
        </h3>
        <span className="rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700">
          {alerts.length} active
        </span>
      </div>
      <div className="mt-4 space-y-3">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="flex items-start gap-3 rounded-lg border border-gray-100 p-3"
          >
            <span
              className={cn(
                "mt-0.5 h-2 w-2 rounded-full flex-shrink-0",
                alert.severity === "CRITICAL" && "bg-red-500",
                alert.severity === "HIGH" && "bg-orange-500",
                alert.severity === "MEDIUM" && "bg-yellow-500",
                alert.severity === "LOW" && "bg-green-500",
              )}
            />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "text-xs font-medium",
                    getSeverityColor(alert.severity),
                  )}
                >
                  {alert.severity}
                </span>
                <span className="text-xs text-gray-400">{alert.type}</span>
              </div>
              <p className="mt-0.5 text-sm text-gray-700 truncate">
                {alert.description}
              </p>
              <p className="mt-1 text-xs text-gray-400">
                {alert.userId}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
