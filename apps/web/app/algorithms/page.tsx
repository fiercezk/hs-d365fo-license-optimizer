/**
 * License Optimization Overview (Dashboard 2 per Requirements/14).
 *
 * Shows:
 *   - Filter bar: Department, License Type, Status
 *   - Summary statistics: Total Opportunities, Pending, Approved, Savings
 *   - Recommendations table with pagination
 *   - Bulk action controls
 *
 * Data fetched via useRecommendations() hook.
 * This scaffold uses static layout. Replace with real data binding.
 */

export default function AlgorithmsOverviewPage() {
  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            License Optimization
          </h1>
          <p className="text-sm text-gray-500">
            Review and approve license change recommendations
          </p>
        </div>
        <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          Run Analysis
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 rounded-xl border bg-white p-4 shadow-sm">
        <select className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700">
          <option>All Departments</option>
          <option>Finance</option>
          <option>Operations</option>
          <option>Supply Chain</option>
          <option>Commerce</option>
        </select>
        <select className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700">
          <option>All License Types</option>
          <option>Team Members</option>
          <option>Operations</option>
          <option>Finance</option>
          <option>SCM</option>
          <option>Commerce</option>
        </select>
        <select className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700">
          <option>All Statuses</option>
          <option>Pending</option>
          <option>Approved</option>
          <option>Rejected</option>
          <option>Implemented</option>
        </select>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Opportunities", value: "1,234" },
          { label: "Pending Review", value: "156" },
          { label: "Approved", value: "89" },
          { label: "Savings to Date", value: "$75,000" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl border bg-white p-4 text-center shadow-sm"
          >
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className="mt-1 text-2xl font-semibold text-gray-900">
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Recommendations Table */}
      <div className="rounded-xl border bg-white shadow-sm">
        <div className="border-b p-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">
              Recent Recommendations
            </h3>
            <div className="flex gap-2">
              <button className="rounded-lg border px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50">
                Export Selected
              </button>
              <button className="rounded-lg bg-green-600 px-3 py-1.5 text-xs text-white hover:bg-green-700">
                Approve Selected
              </button>
            </div>
          </div>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              <th className="px-4 py-3">
                <input type="checkbox" className="rounded" />
              </th>
              <th className="px-4 py-3">User</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Current</th>
              <th className="px-4 py-3">Recommended</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Savings</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {/* Placeholder rows - replace with mapped data from useRecommendations() */}
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <input type="checkbox" className="rounded" />
              </td>
              <td className="px-4 py-3 text-sm">
                <div className="font-medium text-gray-900">John Doe</div>
                <div className="text-xs text-gray-500">
                  john.doe@contoso.com
                </div>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">Downgrade</td>
              <td className="px-4 py-3 text-sm text-gray-600">Commerce</td>
              <td className="px-4 py-3 text-sm text-green-600">
                Team Members
              </td>
              <td className="px-4 py-3">
                <span className="inline-flex rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">
                  HIGH (95%)
                </span>
              </td>
              <td className="px-4 py-3 text-sm font-medium text-green-600">
                $120/mo
              </td>
              <td className="px-4 py-3">
                <span className="inline-flex rounded-full bg-yellow-50 px-2 py-0.5 text-xs font-medium text-yellow-700">
                  Pending
                </span>
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <input type="checkbox" className="rounded" />
              </td>
              <td className="px-4 py-3 text-sm">
                <div className="font-medium text-gray-900">Jane Smith</div>
                <div className="text-xs text-gray-500">
                  jane.smith@contoso.com
                </div>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">Downgrade</td>
              <td className="px-4 py-3 text-sm text-gray-600">Finance</td>
              <td className="px-4 py-3 text-sm text-green-600">Operations</td>
              <td className="px-4 py-3">
                <span className="inline-flex rounded-full bg-yellow-50 px-2 py-0.5 text-xs font-medium text-yellow-700">
                  MEDIUM (78%)
                </span>
              </td>
              <td className="px-4 py-3 text-sm font-medium text-green-600">
                $90/mo
              </td>
              <td className="px-4 py-3">
                <span className="inline-flex rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">
                  Approved
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div className="border-t p-4 text-center">
          <button className="text-sm text-brand-600 hover:text-brand-700">
            Load More
          </button>
        </div>
      </div>
    </div>
  );
}
