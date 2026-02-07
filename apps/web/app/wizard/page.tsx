"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { LicenseSuggestion } from "@/types/api";

/**
 * New User License Wizard (Dashboard 5 per Requirements/14).
 *
 * Two-step workflow:
 *   Step 1: Select required menu items (search + category browse)
 *   Step 2: View top-3 license recommendations with SoD conflict check
 *
 * Uses POST /api/v1/suggest-license (Algorithm 4.7).
 * This scaffold uses static layout. Replace with useSuggestLicense() mutation.
 */

// Example menu items for scaffold
const EXAMPLE_MENU_ITEMS = [
  { aotName: "LedgerJournalTable", description: "General journal entry", module: "Finance" },
  { aotName: "CustTable", description: "Customer master", module: "Finance" },
  { aotName: "VendInvoiceJour", description: "Vendor invoice journal", module: "Finance" },
  { aotName: "BankReconciliation", description: "Bank reconciliation", module: "Finance" },
  { aotName: "SalesTable", description: "Sales orders", module: "SCM" },
  { aotName: "PurchTable", description: "Purchase orders", module: "SCM" },
  { aotName: "InventJournalTable", description: "Inventory journals", module: "SCM" },
  { aotName: "ProdTable", description: "Production orders", module: "SCM" },
  { aotName: "RetailTransactionTable", description: "Retail transactions", module: "Commerce" },
];

// Placeholder results
const PLACEHOLDER_RESULTS: LicenseSuggestion[] = [
  {
    rank: 1,
    roles: ["Accountant", "AP Clerk"],
    roleCount: 2,
    licenseRequired: "Team Members",
    monthlyCost: 60,
    menuItemCoverage: "100%",
    sodConflicts: [],
    confidence: "high",
    note: "Theoretical - will be validated after 30 days of actual usage",
  },
  {
    rank: 2,
    roles: ["Finance Manager"],
    roleCount: 1,
    licenseRequired: "Finance",
    monthlyCost: 180,
    menuItemCoverage: "100%",
    sodConflicts: [],
    confidence: "high",
    note: "Theoretical - will be validated after 30 days of actual usage",
  },
  {
    rank: 3,
    roles: ["Accountant", "AR Manager"],
    roleCount: 2,
    licenseRequired: "Finance",
    monthlyCost: 180,
    menuItemCoverage: "100%",
    sodConflicts: [
      {
        ruleId: "AP-003",
        roleA: "Accountant",
        roleB: "AR Manager",
        severity: "MEDIUM",
        description: "Potential conflict between journal posting and receivables management",
      },
    ],
    confidence: "medium",
    note: "Theoretical - 1 SoD conflict detected, review recommended",
  },
];

export default function WizardPage() {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [moduleFilter, setModuleFilter] = useState("All");

  const filteredMenuItems = EXAMPLE_MENU_ITEMS.filter((item) => {
    const matchesSearch =
      item.aotName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesModule =
      moduleFilter === "All" || item.module === moduleFilter;
    return matchesSearch && matchesModule;
  });

  const toggleItem = (aotName: string) => {
    setSelectedItems((prev) =>
      prev.includes(aotName)
        ? prev.filter((i) => i !== aotName)
        : [...prev, aotName],
    );
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          New User License Wizard
        </h1>
        <p className="text-sm text-gray-500">
          Find the optimal license and role combination for a new user based on
          required menu items
        </p>
      </div>

      {/* Step 1: Menu Item Selection */}
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">
          Step 1: Select Required Menu Items
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Choose the forms and functions the new user needs access to
        </p>

        {/* Search + Filter */}
        <div className="mt-4 flex gap-3">
          <input
            type="search"
            placeholder="Search menu items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 rounded-lg border border-gray-200 px-4 py-2 text-sm placeholder-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <select
            value={moduleFilter}
            onChange={(e) => setModuleFilter(e.target.value)}
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700"
          >
            <option>All</option>
            <option>Finance</option>
            <option>SCM</option>
            <option>Commerce</option>
          </select>
          {selectedItems.length > 0 && (
            <button
              onClick={() => setSelectedItems([])}
              className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-500 hover:bg-gray-50"
            >
              Clear All
            </button>
          )}
        </div>

        {/* Selected Items Badge */}
        {selectedItems.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {selectedItems.map((item) => (
              <span
                key={item}
                className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700"
              >
                {item}
                <button
                  onClick={() => toggleItem(item)}
                  className="ml-1 text-brand-400 hover:text-brand-600"
                >
                  x
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Menu Item List */}
        <div className="mt-4 max-h-64 space-y-1 overflow-y-auto rounded-lg border">
          {filteredMenuItems.map((item) => (
            <label
              key={item.aotName}
              className={cn(
                "flex cursor-pointer items-center gap-3 px-4 py-2.5 hover:bg-gray-50",
                selectedItems.includes(item.aotName) && "bg-brand-50",
              )}
            >
              <input
                type="checkbox"
                checked={selectedItems.includes(item.aotName)}
                onChange={() => toggleItem(item.aotName)}
                className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              />
              <div className="flex-1">
                <span className="text-sm font-medium text-gray-900">
                  {item.aotName}
                </span>
                <span className="ml-2 text-xs text-gray-500">
                  {item.description}
                </span>
              </div>
              <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {item.module}
              </span>
            </label>
          ))}
        </div>

        {/* Get Recommendations Button */}
        <div className="mt-4">
          <button
            onClick={() => setShowResults(true)}
            disabled={selectedItems.length === 0}
            className={cn(
              "rounded-lg px-6 py-2.5 text-sm font-medium text-white",
              selectedItems.length > 0
                ? "bg-brand-600 hover:bg-brand-700"
                : "bg-gray-300 cursor-not-allowed",
            )}
          >
            Get Recommendations ({selectedItems.length} items selected)
          </button>
        </div>
      </div>

      {/* Step 2: Results */}
      {showResults && (
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">
            Step 2: License Recommendations
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Top 3 role + license combinations ranked by cost efficiency
          </p>

          <div className="mt-4 space-y-4">
            {PLACEHOLDER_RESULTS.map((result) => (
              <div
                key={result.rank}
                className={cn(
                  "rounded-lg border p-4",
                  result.rank === 1 && "border-green-200 bg-green-50",
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold",
                        result.rank === 1
                          ? "bg-green-600 text-white"
                          : "bg-gray-200 text-gray-600",
                      )}
                    >
                      {result.rank}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900">
                        {result.roles.join(", ")}
                      </p>
                      <p className="text-sm text-gray-500">
                        {result.roleCount} role{result.roleCount > 1 ? "s" : ""}{" "}
                        | {result.licenseRequired} | Coverage:{" "}
                        {result.menuItemCoverage}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-gray-900">
                      ${result.monthlyCost}
                      <span className="text-sm font-normal text-gray-500">
                        /mo
                      </span>
                    </p>
                    <span
                      className={cn(
                        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
                        result.confidence === "high" &&
                          "bg-green-100 text-green-700",
                        result.confidence === "medium" &&
                          "bg-yellow-100 text-yellow-700",
                        result.confidence === "low" &&
                          "bg-red-100 text-red-700",
                      )}
                    >
                      {result.confidence.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* SoD Conflicts */}
                {result.sodConflicts.length > 0 && (
                  <div className="mt-3 rounded-lg border border-orange-200 bg-orange-50 p-3">
                    <p className="text-xs font-medium text-orange-700">
                      {result.sodConflicts.length} SoD Conflict(s) Detected
                    </p>
                    {result.sodConflicts.map((conflict) => (
                      <p
                        key={conflict.ruleId}
                        className="mt-1 text-xs text-orange-600"
                      >
                        [{conflict.ruleId}] {conflict.description}
                      </p>
                    ))}
                  </div>
                )}

                <div className="mt-3 flex gap-2">
                  <button className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700">
                    Apply Recommendation
                  </button>
                  <button className="rounded-lg border px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50">
                    Export as PDF
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 rounded-lg bg-blue-50 p-3">
            <p className="text-xs text-blue-700">
              Note: These are theoretical recommendations based on security
              configuration data. Actual license requirements will be validated
              after 30 days of observed usage patterns.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
