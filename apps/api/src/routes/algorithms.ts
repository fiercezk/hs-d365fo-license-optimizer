/**
 * Algorithms API Routes
 * Endpoints: list algorithms, algorithm recommendations, trigger analysis
 */
import { Router, Request, Response, NextFunction } from 'express';
import { getDb } from '../db/connection';

const router = Router();

/**
 * Known algorithm metadata (supplements DB data).
 */
const ALGORITHM_CATALOG: Record<string, { name: string; category: string }> = {
  '2.2': { name: 'Read-Only User Detection', category: 'Cost Optimization' },
  '2.5': { name: 'License Minority Detection', category: 'Cost Optimization' },
  '3.1': { name: 'Segregation of Duties Conflicts', category: 'Security' },
  '3.2': { name: 'Anomalous Role Change Detection', category: 'Security' },
  '3.3': { name: 'Privilege Creep Detection', category: 'Security' },
  '3.4': { name: 'Toxic Combination Detection', category: 'Security' },
  '4.1': { name: 'Device License Opportunity', category: 'Cost Optimization' },
  '4.3': { name: 'Cross-Application License Analyzer', category: 'Cost Optimization' },
  '4.7': { name: 'New User License Recommendation', category: 'Role Management' },
  '5.1': { name: 'License Cost Trend Analysis', category: 'Analytics' },
  '5.2': { name: 'Security Risk Scoring', category: 'Analytics' },
};

/**
 * GET /api/v1/algorithms
 * List all algorithms with recommendation counts and last run info.
 */
router.get('/', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();

    // Get recommendation counts per algorithm
    const recCounts = db
      .prepare(
        'SELECT algorithm_id, COUNT(*) as count, SUM(monthly_savings) as totalSavings FROM recommendations GROUP BY algorithm_id'
      )
      .all() as { algorithm_id: string; count: number; totalSavings: number }[];

    // Get last run info per algorithm
    const lastRuns = db
      .prepare(
        `SELECT algorithm_id, algorithm_name, completed_at, status, users_processed, recommendations_generated
         FROM algorithm_runs
         WHERE id IN (
           SELECT id FROM algorithm_runs ar2
           WHERE ar2.algorithm_id = algorithm_runs.algorithm_id
           ORDER BY completed_at DESC LIMIT 1
         )`
      )
      .all() as any[];

    // Build response combining catalog, recommendation counts, and run info
    const recCountMap = new Map(recCounts.map((r) => [r.algorithm_id, r]));
    const runMap = new Map(lastRuns.map((r) => [r.algorithm_id, r]));

    const algorithms = Object.entries(ALGORITHM_CATALOG).map(([id, info]) => {
      const recInfo = recCountMap.get(id);
      const runInfo = runMap.get(id);

      return {
        algorithmId: id,
        name: info.name,
        category: info.category,
        recommendationCount: recInfo?.count || 0,
        totalSavings: recInfo?.totalSavings || 0,
        lastRun: runInfo
          ? {
              completedAt: runInfo.completed_at,
              status: runInfo.status,
              usersProcessed: runInfo.users_processed,
              recommendationsGenerated: runInfo.recommendations_generated,
            }
          : null,
      };
    });

    res.json({
      success: true,
      data: algorithms,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/v1/algorithms/:algorithmId/recommendations
 * List recommendations for a specific algorithm.
 */
router.get('/:algorithmId/recommendations', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const { algorithmId } = req.params;
    const page = Math.max(parseInt(req.query.page as string) || 1, 1);
    const limit = Math.min(Math.max(parseInt(req.query.limit as string) || 50, 1), 200);
    const offset = (page - 1) * limit;

    const countRow = db
      .prepare('SELECT COUNT(*) as total FROM recommendations WHERE algorithm_id = ?')
      .get(algorithmId) as { total: number };

    const rows = db
      .prepare(
        `SELECT r.*, u.display_name
         FROM recommendations r
         LEFT JOIN users u ON r.user_id = u.id
         WHERE r.algorithm_id = ?
         ORDER BY r.monthly_savings DESC
         LIMIT ? OFFSET ?`
      )
      .all(algorithmId, limit, offset);

    const data = rows.map((row: any) => ({
      id: row.id,
      userId: row.user_id,
      userName: row.display_name,
      algorithmId: row.algorithm_id,
      type: row.type,
      priority: row.priority,
      confidence: row.confidence,
      currentLicense: row.current_license,
      recommendedLicense: row.recommended_license,
      monthlySavings: row.monthly_savings,
      annualSavings: row.annual_savings,
      status: row.status,
      createdAt: row.created_at,
    }));

    res.json({
      success: true,
      data,
      meta: {
        total: countRow.total,
        page,
        pageSize: limit,
        pages: Math.ceil(countRow.total / limit),
      },
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/v1/analyze/:algorithmId
 * Trigger algorithm analysis (stub - returns queued status).
 */
router.post('/:algorithmId', (req: Request, res: Response, next: NextFunction) => {
  try {
    const algorithmId = req.params.algorithmId as string;
    const algoInfo = ALGORITHM_CATALOG[algorithmId];

    res.status(202).json({
      success: true,
      data: {
        algorithmId,
        name: algoInfo?.name || `Algorithm ${algorithmId}`,
        status: 'queued',
        message: `Analysis for algorithm ${algorithmId} has been queued. Results will be available once processing completes.`,
        queuedAt: new Date().toISOString(),
      },
    });
  } catch (err) {
    next(err);
  }
});

export default router;
