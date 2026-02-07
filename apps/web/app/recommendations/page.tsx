/**
 * Recommendations Management Page (per Requirements/14 FR-Web-2).
 *
 * Provides:
 *   - Prioritized recommendation list (sort by savings, priority, date)
 *   - Filter by status, type, confidence, department
 *   - Approval/rejection workflow
 *   - Bulk actions
 *   - Export to CSV/PDF/Excel
 *
 * This is a scaffold - connect to useRecommendations() hook for live data.
 */

export default function RecommendationsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Recommendations
          </h1>
          <p className="text-sm text-gray-500">
            Manage license optimization and security recommendations
          </p>
        </div>
        <div className="flex gap-2">
          <button className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">
            Export All
          </button>
          <button className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700">
            Approve Selected
          </button>
        </div>
      </div>

      {/* Status Tabs */}
      <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
        {["All", "Pending", "Approved", "Implemented", "Rejected"].map(
          (tab) => (
            <button
              key={tab}
              className={`rounded-md px-4 py-2 text-sm font-medium ${
                tab === "All"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              {tab}
            </button>
          ),
        )}
      </div>

      {/* Recommendations list placeholder */}
      <div className="rounded-xl border bg-white p-8 text-center shadow-sm">
        <p className="text-gray-500">
          Connect to useRecommendations() hook to display live recommendation
          data from the Azure Functions API.
        </p>
      </div>
    </div>
  );
}
