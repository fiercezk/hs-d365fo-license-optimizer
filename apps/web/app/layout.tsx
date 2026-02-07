import type { Metadata } from "next";
import { Providers } from "./providers";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import "./globals.css";

export const metadata: Metadata = {
  title: "D365 FO License Agent",
  description:
    "AI-powered license optimization and security compliance for Microsoft Dynamics 365 Finance & Operations",
};

/**
 * Root layout with sidebar navigation and header.
 *
 * Layout structure:
 *   +---------+----------------------------------+
 *   | Sidebar | Header                           |
 *   |         +----------------------------------+
 *   |         | Page Content                     |
 *   |         |                                  |
 *   |         |                                  |
 *   +---------+----------------------------------+
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <Providers>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <div className="flex flex-1 flex-col overflow-hidden">
              <Header />
              <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
                {children}
              </main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
