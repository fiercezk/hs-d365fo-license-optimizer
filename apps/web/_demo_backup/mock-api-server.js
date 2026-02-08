/**
 * Mock API Server for Local Development
 *
 * Provides fake endpoints matching the Azure Functions API contract.
 * Allows testing the Next.js web app without deploying to Azure.
 *
 * Usage:
 *   node mock-api-server.js
 *   Then: NEXT_PUBLIC_API_URL=http://localhost:3001 bun dev
 */

const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});

// ============================================================================
// Dashboard API
// ============================================================================

app.get('/api/v1/dashboard/metrics', (req, res) => {
  res.json({
    totalLicenseCost: 180000,
    monthlySavings: 12500,
    ytdSavings: 75000,
    usersOptimized: 1234,
    pendingRecommendations: 156,
    activeAlerts: 7,
    complianceScore: 94,
  });
});

// ============================================================================
// Cost Trend API (Algorithm 5.1)
// ============================================================================

app.get('/api/v1/algorithms/5.1/trend', (req, res) => {
  const months = parseInt(req.query.months) || 12;

  // Generate sample data for last N months
  const data = [];
  const today = new Date();

  for (let i = months - 1; i >= 0; i--) {
    const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
    const actualCost = 180000 - (i * 1200) + Math.random() * 5000; // Trending down
    const forecastCost = 185000 - (i * 200); // Slower decline without optimization
    const targetCost = 165000; // Goal

    data.push({
      date: date.toISOString().split('T')[0],
      actualCost: Math.round(actualCost),
      forecastCost: Math.round(forecastCost),
      targetCost: targetCost,
    });
  }

  res.json({ data });
});

// ============================================================================
// Recommendations API
// ============================================================================

const sampleRecommendations = [
  {
    id: 'REC-001',
    type: 'LICENSE_DOWNGRADE',
    algorithm: '2.2',
    userId: 'john.doe@contoso.com',
    userName: 'John Doe',
    priority: 'HIGH',
    confidence: 92,
    currentLicense: 'Operations - Activity',
    recommendedLicense: 'Team Members',
    currentCost: 90,
    recommendedCost: 60,
    monthlySavings: 30,
    annualSavings: 360,
    readPercentage: 98.1,
    writeOperations: 23,
    options: [
      {
        optionId: 'OPT-1',
        type: 'DOWNGRADE',
        description: 'Downgrade to Team Members license',
        impact: 'User retains all current access patterns',
        feasibility: 'HIGH',
        implementationEffort: 'LOW',
      },
    ],
    status: 'PENDING',
    createdAt: '2026-02-07T08:00:00Z',
    expiresAt: '2026-03-07T08:00:00Z',
  },
  {
    id: 'REC-002',
    type: 'LICENSE_DOWNGRADE',
    algorithm: '2.5',
    userId: 'jane.smith@contoso.com',
    userName: 'Jane Smith',
    priority: 'MEDIUM',
    confidence: 85,
    currentLicense: 'Finance',
    recommendedLicense: 'Operations - Activity',
    currentCost: 180,
    recommendedCost: 90,
    monthlySavings: 90,
    annualSavings: 1080,
    options: [],
    status: 'PENDING',
    createdAt: '2026-02-07T09:15:00Z',
    expiresAt: '2026-03-07T09:15:00Z',
  },
  {
    id: 'REC-003',
    type: 'SOD_VIOLATION',
    algorithm: '3.1',
    userId: 'mike.wilson@contoso.com',
    userName: 'Mike Wilson',
    priority: 'CRITICAL',
    confidence: 100,
    currentLicense: 'Operations - Activity',
    recommendedLicense: null,
    currentCost: 90,
    recommendedCost: 90,
    monthlySavings: 0,
    annualSavings: 0,
    options: [
      {
        optionId: 'OPT-2',
        type: 'REMOVE_ROLE',
        description: 'Remove "Vendor Master Maintainer" role',
        impact: 'Resolves SOD conflict with AP Clerk role',
        feasibility: 'HIGH',
        implementationEffort: 'LOW',
      },
    ],
    status: 'PENDING',
    createdAt: '2026-02-07T02:34:00Z',
    expiresAt: '2026-02-14T02:34:00Z',
  },
];

app.get('/api/v1/recommendations', (req, res) => {
  const { type, priority, status, limit = 50, offset = 0 } = req.query;

  let filtered = sampleRecommendations;

  if (type) filtered = filtered.filter(r => r.type === type);
  if (priority) filtered = filtered.filter(r => r.priority === priority);
  if (status) filtered = filtered.filter(r => r.status === status);

  const paginated = filtered.slice(offset, offset + parseInt(limit));

  res.json({
    recommendations: paginated,
    pagination: {
      total: filtered.length,
      limit: parseInt(limit),
      offset: parseInt(offset),
    },
  });
});

app.get('/api/v1/recommendations/:userId', (req, res) => {
  const { userId } = req.params;
  const userRecs = sampleRecommendations.filter(r => r.userId === userId);

  res.json({
    recommendations: userRecs,
    pagination: {
      total: userRecs.length,
      limit: 50,
      offset: 0,
    },
  });
});

app.post('/api/v1/recommendations/:id/approve', (req, res) => {
  const { id } = req.params;
  const { comment } = req.body;

  console.log(`Approved recommendation ${id} with comment: ${comment}`);

  res.json({
    success: true,
    message: 'Recommendation approved',
    recommendationId: id,
    status: 'APPROVED',
  });
});

app.post('/api/v1/recommendations/:id/reject', (req, res) => {
  const { id } = req.params;
  const { reason } = req.body;

  console.log(`Rejected recommendation ${id} with reason: ${reason}`);

  res.json({
    success: true,
    message: 'Recommendation rejected',
    recommendationId: id,
    status: 'REJECTED',
  });
});

app.post('/api/v1/recommendations/:id/rollback', (req, res) => {
  const { id } = req.params;
  const { speed } = req.body;

  console.log(`Rollback recommendation ${id} with speed: ${speed}`);

  res.json({
    success: true,
    message: `Recommendation rolled back (${speed} restore)`,
    recommendationId: id,
    status: 'ROLLED_BACK',
    estimatedCompletionMs: speed === 'fast' ? 5000 : 60000,
  });
});

// ============================================================================
// Analysis API
// ============================================================================

app.post('/api/v1/analyze', (req, res) => {
  const { scope, userId, algorithms } = req.body;

  const analysisId = `ANALYSIS-${Date.now()}`;

  res.json({
    analysisId,
    status: 'IN_PROGRESS',
    estimatedCompletion: new Date(Date.now() + 60000).toISOString(),
    resultsUrl: `/api/v1/analysis/${analysisId}/results`,
  });
});

// ============================================================================
// New User License Wizard API
// ============================================================================

app.post('/api/v1/suggest-license', (req, res) => {
  const { requiredMenuItems, includeSODCheck } = req.body;

  res.json({
    recommendations: [
      {
        rank: 1,
        roles: ['Purchasing Coordinator', 'Vendor Information (read-only)'],
        roleCount: 2,
        licenseRequired: 'Team Members',
        monthlyCost: 60,
        menuItemCoverage: '100%',
        sodConflicts: [],
        confidence: 'high',
        note: 'All requested menu items accessible with Team Members license. No SoD conflicts detected.',
      },
      {
        rank: 2,
        roles: ['Purchasing Agent'],
        roleCount: 1,
        licenseRequired: 'Operations - Activity',
        monthlyCost: 90,
        menuItemCoverage: '100%',
        sodConflicts: [],
        confidence: 'medium',
        note: 'Over-provisioned. Includes write access to vendor master (not required per selections).',
      },
    ],
    inputMenuItems: requiredMenuItems.length,
    generatedAt: new Date().toISOString(),
  });
});

// ============================================================================
// Agent Health API
// ============================================================================

app.get('/api/v1/agent/health', (req, res) => {
  res.json({
    status: 'healthy',
    lastExecution: new Date(Date.now() - 3600000).toISOString(),
    executionTimeMs: 28500,
    algorithmsAvailable: 34,
    nextScheduledRun: new Date(Date.now() + 7200000).toISOString(),
    version: '1.0.0',
    uptime: 86400,
  });
});

// ============================================================================
// Security Alerts API
// ============================================================================

app.get('/api/v1/security/alerts', (req, res) => {
  res.json({
    alerts: [
      {
        id: 'ALERT-001',
        type: 'SOD_VIOLATION',
        severity: 'CRITICAL',
        description: 'john.doe@contoso.com has conflicting roles: AP Clerk + Vendor Master',
        userId: 'john.doe@contoso.com',
        detectedAt: '2026-02-07T02:34:00Z',
      },
      {
        id: 'ALERT-002',
        type: 'ANOMALOUS_ACCESS',
        severity: 'HIGH',
        description: 'jane.smith@contoso.com accessed 3 critical forms at 2 AM Saturday',
        userId: 'jane.smith@contoso.com',
        detectedAt: '2026-02-07T02:00:00Z',
      },
      {
        id: 'ALERT-003',
        type: 'PRIVILEGE_CREEP',
        severity: 'MEDIUM',
        description: 'mike.wilson@contoso.com accumulated 12 roles over 18 months without review',
        userId: 'mike.wilson@contoso.com',
        detectedAt: '2026-02-06T14:15:00Z',
      },
    ],
  });
});

// ============================================================================
// Start Server
// ============================================================================

app.listen(PORT, () => {
  console.log('');
  console.log('='.repeat(60));
  console.log('  D365 FO License Agent - Mock API Server');
  console.log('='.repeat(60));
  console.log(`  Status: Running on http://localhost:${PORT}`);
  console.log(`  Endpoints: 11 endpoints available`);
  console.log('');
  console.log('  Available Endpoints:');
  console.log('  - GET  /api/v1/dashboard/metrics');
  console.log('  - GET  /api/v1/algorithms/5.1/trend');
  console.log('  - GET  /api/v1/recommendations');
  console.log('  - POST /api/v1/recommendations/:id/approve');
  console.log('  - POST /api/v1/recommendations/:id/reject');
  console.log('  - POST /api/v1/analyze');
  console.log('  - POST /api/v1/suggest-license');
  console.log('  - GET  /api/v1/agent/health');
  console.log('  - GET  /api/v1/security/alerts');
  console.log('');
  console.log('  Configure web app:');
  console.log(`  export NEXT_PUBLIC_API_URL=http://localhost:${PORT}`);
  console.log('  cd apps/web && bun dev');
  console.log('='.repeat(60));
  console.log('');
});
