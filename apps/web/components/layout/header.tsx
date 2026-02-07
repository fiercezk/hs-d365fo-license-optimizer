"use client";

/**
 * Top header bar with search, notifications, and user profile.
 */
export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative">
          <input
            type="search"
            placeholder="Search users, roles, recommendations..."
            className="w-80 rounded-lg border border-gray-200 bg-gray-50 px-4 py-2 text-sm placeholder-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
      </div>

      {/* Right side: notifications + user */}
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100">
          <span className="sr-only">Notifications</span>
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          {/* Notification badge */}
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
        </button>

        {/* User menu */}
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 text-sm font-medium">
            SA
          </div>
          <div className="text-sm">
            <div className="font-medium text-gray-900">System Admin</div>
            <div className="text-xs text-gray-500">admin@contoso.com</div>
          </div>
        </div>
      </div>
    </header>
  );
}
