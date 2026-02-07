/**
 * D365 FO License Agent - API Type Definitions
 *
 * These types mirror the Python Pydantic models in apps/agent/src/models/
 * and define the API contract between the Next.js frontend and Azure Functions backend.
 *
 * See Requirements/13-Azure-Foundry-Agent-Architecture.md for full API specification.
 */

// ============================================================================
// Enums
// ============================================================================

export type LicenseType =
  | "Team Members"
  | "Operations - Activity"
  | "Operations"
  | "SCM"
  | "Finance"
  | "Commerce"
  | "Device License";

export type RecommendationAction =
  | "downgrade"
  | "upgrade"
  | "no_change"
  | "add_license"
  | "remove_license"
  | "review_required";

export type ConfidenceLevel = "high" | "medium" | "low" | "insufficient_data";

export type SeverityLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type RecommendationStatus =
  | "PENDING"
  | "APPROVED"
  | "REJECTED"
  | "IMPLEMENTED";

export type RecommendationType =
  | "LICENSE_DOWNGRADE"
  | "LICENSE_UPGRADE"
  | "ROLE_REMOVAL"
  | "SOD_VIOLATION"
  | "SECURITY_ALERT"
  | "COST_OPTIMIZATION";

export type ReportType =
  | "license-optimization"
  | "security-compliance"
  | "user-activity"
  | "trend-analysis";

export type AnalysisScope = "USER" | "ROLE" | "ORGANIZATION";

// ============================================================================
// Recommendation Models (GET /api/v1/recommendations)
// ============================================================================

export interface RecommendationOption {
  optionId: string;
  type: string;
  description: string;
  impact: string;
  feasibility: "HIGH" | "MEDIUM" | "LOW";
  implementationEffort: "LOW" | "MEDIUM" | "HIGH";
}

export interface Recommendation {
  id: string;
  type: RecommendationType;
  algorithm: string;
  userId: string;
  userName: string;
  priority: SeverityLevel;
  confidence: number;
  currentLicense: LicenseType;
  recommendedLicense: LicenseType | null;
  currentCost: number;
  recommendedCost: number;
  monthlySavings: number;
  annualSavings: number;
  readPercentage?: number;
  writeOperations?: number;
  options: RecommendationOption[];
  status: RecommendationStatus;
  createdAt: string;
  expiresAt: string;
}

export interface RecommendationsResponse {
  recommendations: Recommendation[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
  };
}

// ============================================================================
// Analysis Models (POST /api/v1/analyze)
// ============================================================================

export interface AnalyzeRequest {
  scope: AnalysisScope;
  userId?: string;
  algorithms: string[];
  includeDetails: boolean;
}

export interface AnalyzeResponse {
  analysisId: string;
  status: "IN_PROGRESS" | "COMPLETED" | "FAILED";
  estimatedCompletion: string;
  resultsUrl: string;
}

// ============================================================================
// New User License Wizard (POST /api/v1/suggest-license)
// ============================================================================

export interface SuggestLicenseRequest {
  requiredMenuItems: string[];
  includeSODCheck: boolean;
}

export interface SodConflict {
  ruleId: string;
  roleA: string;
  roleB: string;
  severity: SeverityLevel;
  description: string;
}

export interface LicenseSuggestion {
  rank: number;
  roles: string[];
  roleCount: number;
  licenseRequired: LicenseType;
  monthlyCost: number;
  menuItemCoverage: string;
  sodConflicts: SodConflict[];
  confidence: ConfidenceLevel;
  note: string;
}

export interface SuggestLicenseResponse {
  recommendations: LicenseSuggestion[];
  inputMenuItems: number;
  generatedAt: string;
}

// ============================================================================
// Agent Health (GET /api/v1/agent/health)
// ============================================================================

export interface AgentHealth {
  status: "healthy" | "degraded" | "unhealthy";
  lastExecution: string | null;
  executionTimeMs: number | null;
  algorithmsAvailable: number;
  nextScheduledRun: string | null;
  version: string;
  uptime: number;
}

// ============================================================================
// Dashboard Summary Models
// ============================================================================

export interface DashboardMetrics {
  totalLicenseCost: number;
  monthlySavings: number;
  ytdSavings: number;
  usersOptimized: number;
  pendingRecommendations: number;
  activeAlerts: number;
  complianceScore: number;
}

export interface TopOpportunity {
  algorithm: string;
  name: string;
  userCount: number;
  monthlySavings: number;
  annualSavings: number;
}

export interface SecurityAlert {
  id: string;
  type: string;
  severity: SeverityLevel;
  description: string;
  userId: string;
  detectedAt: string;
}

// ============================================================================
// Report Models (GET /api/v1/reports/{reportType})
// ============================================================================

export interface ReportRequest {
  reportType: ReportType;
  startDate: string;
  endDate: string;
  department?: string;
  format: "json" | "pdf" | "csv";
}

export interface ReportMetadata {
  reportId: string;
  reportType: ReportType;
  generatedAt: string;
  periodStart: string;
  periodEnd: string;
  recordCount: number;
}

// ============================================================================
// WebSocket Event Types
// ============================================================================

export interface AnalysisProgressEvent {
  eventType: "analysis.progress";
  analysisId: string;
  timestamp: string;
  data: {
    algorithm: string;
    progress: number;
    status: "RUNNING" | "COMPLETED" | "FAILED";
    usersProcessed: number;
    totalUsers: number;
    estimatedCompletion: string;
  };
}

export interface RecommendationGeneratedEvent {
  eventType: "recommendation.generated";
  timestamp: string;
  data: {
    recommendationId: string;
    userId: string;
    type: RecommendationType;
    savings: number;
  };
}

export interface AlertTriggeredEvent {
  eventType: "alert.triggered";
  timestamp: string;
  data: {
    alertId: string;
    severity: SeverityLevel;
    type: string;
    userId: string;
    description: string;
  };
}

export type WebSocketEvent =
  | AnalysisProgressEvent
  | RecommendationGeneratedEvent
  | AlertTriggeredEvent;
