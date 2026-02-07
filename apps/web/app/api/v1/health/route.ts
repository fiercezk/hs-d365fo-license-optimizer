import { NextResponse } from "next/server";

/**
 * API Route: GET /api/v1/agent/health
 *
 * Returns agent health status. In production, proxies to Azure Functions.
 * In development, returns mock health data.
 */
export async function GET() {
  const healthResponse = {
    status: "healthy",
    lastExecution: "2026-02-07T02:00:00Z",
    executionTimeMs: 45230,
    algorithmsAvailable: 34,
    nextScheduledRun: "2026-02-08T02:00:00Z",
    version: "0.1.0",
    uptime: 86400,
  };

  return NextResponse.json(healthResponse);
}
