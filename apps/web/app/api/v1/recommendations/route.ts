import { NextRequest, NextResponse } from "next/server";

/**
 * API Route: GET /api/v1/recommendations
 *
 * Proxies to Azure Functions backend in production.
 * In development, returns mock data for frontend development.
 *
 * Query parameters:
 *   type: LICENSE, SECURITY, COMPLIANCE, ALL
 *   priority: HIGH, MEDIUM, LOW
 *   status: PENDING, APPROVED, REJECTED, IMPLEMENTED
 *   limit: number (default 100)
 *   offset: number (default 0)
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const _type = searchParams.get("type");
  const _priority = searchParams.get("priority");
  const _status = searchParams.get("status");
  const limit = parseInt(searchParams.get("limit") || "100");
  const offset = parseInt(searchParams.get("offset") || "0");

  // Mock data for development - replace with Azure Functions proxy in production
  const mockRecommendations = {
    recommendations: [
      {
        id: "REC-2026-001",
        type: "LICENSE_DOWNGRADE",
        algorithm: "2.2-Read-Only-User-Detector",
        userId: "john.doe@contoso.com",
        userName: "John Doe",
        priority: "HIGH",
        confidence: 95,
        currentLicense: "Commerce",
        recommendedLicense: "Team Members",
        currentCost: 180,
        recommendedCost: 60,
        monthlySavings: 120,
        annualSavings: 1440,
        readPercentage: 99.76,
        writeOperations: 2,
        options: [
          {
            optionId: "OPT-001",
            type: "DOWNGRADE_LICENSE",
            description:
              "Downgrade from Commerce to Team Members license",
            impact: "User will have read-only access to most functions",
            feasibility: "HIGH",
            implementationEffort: "LOW",
          },
        ],
        status: "PENDING",
        createdAt: "2026-02-06T10:30:00Z",
        expiresAt: "2026-03-06T10:30:00Z",
      },
    ],
    pagination: {
      total: 1,
      limit,
      offset,
    },
  };

  return NextResponse.json(mockRecommendations);
}
