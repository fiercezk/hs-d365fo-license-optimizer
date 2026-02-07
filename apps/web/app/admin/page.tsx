/**
 * Administration Page (per Requirements/14 FR-Web-5).
 *
 * Provides:
 *   - Agent schedule configuration (daily/weekly/monthly)
 *   - Algorithm parameter tuning (thresholds)
 *   - Agent health monitoring
 *   - System settings
 *
 * This is a scaffold - connect to useAgentHealth() hook for live data.
 */

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Administration</h1>
        <p className="text-sm text-gray-500">
          Configure agent scheduling, algorithm parameters, and system settings
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Agent Health */}
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">Agent Health</h2>
          <div className="mt-4 space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Status</span>
              <span className="inline-flex items-center gap-1 text-sm font-medium text-green-600">
                <span className="h-2 w-2 rounded-full bg-green-400" />
                Healthy
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Last Run</span>
              <span className="text-sm text-gray-900">
                2026-02-07 02:00 UTC
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Next Run</span>
              <span className="text-sm text-gray-900">
                2026-02-08 02:00 UTC
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Algorithms</span>
              <span className="text-sm text-gray-900">34 available</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Last Duration</span>
              <span className="text-sm text-gray-900">45.2s</span>
            </div>
          </div>
        </div>

        {/* Schedule Configuration */}
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">
            Schedule Configuration
          </h2>
          <div className="mt-4 space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">
                Daily Incremental
              </label>
              <div className="mt-1 flex items-center gap-2">
                <input
                  type="time"
                  defaultValue="02:00"
                  className="rounded-lg border px-3 py-1.5 text-sm"
                />
                <span className="text-sm text-gray-500">UTC</span>
                <span className="ml-auto inline-flex rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">
                  Enabled
                </span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">
                Weekly Full Scan
              </label>
              <div className="mt-1 flex items-center gap-2">
                <select className="rounded-lg border px-3 py-1.5 text-sm">
                  <option>Sunday</option>
                  <option>Saturday</option>
                </select>
                <input
                  type="time"
                  defaultValue="02:00"
                  className="rounded-lg border px-3 py-1.5 text-sm"
                />
                <span className="ml-auto inline-flex rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">
                  Enabled
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Algorithm Parameters */}
        <div className="rounded-xl border bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900">
            Algorithm Parameters
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Tune algorithm thresholds. Changes apply to the next scheduled run.
          </p>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                label: "Read-Only Threshold",
                id: "readonly",
                default: "95",
                unit: "%",
                desc: "Algorithm 2.2",
              },
              {
                label: "Inactivity Days",
                id: "inactive",
                default: "90",
                unit: "days",
                desc: "Algorithm 3.5",
              },
              {
                label: "Minority License Threshold",
                id: "minority",
                default: "15",
                unit: "%",
                desc: "Algorithm 2.5",
              },
              {
                label: "Confidence Threshold",
                id: "confidence",
                default: "70",
                unit: "%",
                desc: "All algorithms",
              },
              {
                label: "Analysis Period",
                id: "period",
                default: "90",
                unit: "days",
                desc: "Data window",
              },
              {
                label: "Min Sample Size",
                id: "sample",
                default: "100",
                unit: "ops",
                desc: "Algorithm 2.2",
              },
            ].map((param) => (
              <div key={param.id} className="rounded-lg border p-3">
                <label className="text-sm font-medium text-gray-700">
                  {param.label}
                </label>
                <p className="text-xs text-gray-400">{param.desc}</p>
                <div className="mt-2 flex items-center gap-2">
                  <input
                    type="number"
                    defaultValue={param.default}
                    className="w-24 rounded-lg border px-3 py-1.5 text-sm"
                  />
                  <span className="text-xs text-gray-500">{param.unit}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
              Save Parameters
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
