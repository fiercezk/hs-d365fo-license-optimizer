"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  TrendingDown,
  BarChart3,
  Eye,
  Users,
  GitBranch,
  Shield,
  AlertTriangle,
  Activity,
  FileCheck,
  Wand2,
  CheckCircle,
  Settings,
} from "lucide-react";

/**
 * Main sidebar navigation.
 *
 * Navigation structure per Requirements/14-Web-Application-Requirements.md:
 *   Dashboard
 *   License Optimization
 *   Security & Compliance
 *   New User Wizard
 *   Recommendations
 *   Reports
 *   Administration
 */

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  children?: NavItem[];
}

const navigation: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "License Optimization",
    href: "/algorithms",
    icon: TrendingDown,
    children: [
      { label: "Overview", href: "/algorithms", icon: BarChart3 },
      { label: "Read-Only Users", href: "/algorithms/readonly", icon: Eye },
      {
        label: "License Minority",
        href: "/algorithms/minority",
        icon: Users,
      },
      {
        label: "Cross-Role Optimization",
        href: "/algorithms/cross-role",
        icon: GitBranch,
      },
    ],
  },
  {
    label: "Security & Compliance",
    href: "/algorithms/security",
    icon: Shield,
    children: [
      {
        label: "SoD Violations",
        href: "/algorithms/security/sod",
        icon: AlertTriangle,
      },
      {
        label: "Anomalous Activity",
        href: "/algorithms/security/anomalies",
        icon: Activity,
      },
      {
        label: "Compliance Reports",
        href: "/algorithms/security/compliance",
        icon: FileCheck,
      },
    ],
  },
  {
    label: "New User Wizard",
    href: "/wizard",
    icon: Wand2,
  },
  {
    label: "Recommendations",
    href: "/recommendations",
    icon: CheckCircle,
  },
  {
    label: "Administration",
    href: "/admin",
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-white">
      {/* Logo / Brand */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white text-sm font-bold">
            LA
          </div>
          <div>
            <div className="text-sm font-semibold text-gray-900">
              License Agent
            </div>
            <div className="text-xs text-gray-500">D365 FO Optimizer</div>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4">
        <ul className="space-y-1">
          {navigation.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  pathname === item.href || pathname.startsWith(item.href + "/")
                    ? "bg-brand-50 text-brand-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {item.label}
              </Link>

              {/* Submenu */}
              {item.children && (
                <ul className="ml-6 mt-1 space-y-1">
                  {item.children.map((child) => (
                    <li key={child.href}>
                      <Link
                        href={child.href}
                        className={cn(
                          "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs transition-colors",
                          pathname === child.href
                            ? "text-brand-700 font-medium"
                            : "text-gray-500 hover:text-gray-900",
                        )}
                      >
                        {child.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </nav>

      {/* Agent Health Footer */}
      <div className="border-t p-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <div className="h-2 w-2 rounded-full bg-green-400" />
          Agent Healthy
        </div>
      </div>
    </aside>
  );
}
