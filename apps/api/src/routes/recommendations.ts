/**
 * Recommendations API Routes
 * Endpoints: list, detail, approve, reject, rollback, bulk-approve
 */
import { Router, Request, Response, NextFunction } from 'express';
import { getDb } from '../db/connection';
import { ApiError } from '../middleware/error-handler';

const router = Router();

/**
 * Helper to create an error with statusCode.
 */
function createError(statusCode: number, message: string, code: string): ApiError {
  const err = new Error(message) as ApiError;
  err.statusCode = statusCode;
  err.code = code;
  return err;
}

/**
 * Helper to map a raw DB recommendation row to camelCase API response.
 */
function mapRecommendation(row: any) {
  return {
    id: row.id,
    userId: row.user_id,
    userName: row.display_name || undefined,
    algorithmRunId: row.algorithm_run_id,
    algorithmId: row.algorithm_id,
    type: row.type,
    priority: row.priority,
    confidence: row.confidence,
    currentLicense: row.current_license,
    recommendedLicense: row.recommended_license,
    currentCost: row.current_cost,
    recommendedCost: row.recommended_cost,
    monthlySavings: row.monthly_savings,
    annualSavings: row.annual_savings,
    status: row.status,
    details: row.details ? JSON.parse(row.details) : null,
    aiExplanation: row.ai_explanation,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    expiresAt: row.expires_at,
  };
}

/**
 * POST /api/v1/recommendations/bulk-approve
 * Bulk approve multiple recommendations.
 * IMPORTANT: This must be defined BEFORE the /:id routes to avoid
 * Express matching "bulk-approve" as an :id parameter.
 */
router.post('/bulk-approve', (req: Request, res: Response, next: NextFunction) => {
  try {
    const { ids, comment } = req.body;

    if (!ids || !Array.isArray(ids) || ids.length === 0) {
      throw createError(400, 'ids array is required and must not be empty', 'VALIDATION_ERROR');
    }

    const db = getDb();
    const now = new Date().toISOString();

    const updateStmt = db.prepare(
      "UPDATE recommendations SET status = 'APPROVED', updated_at = ? WHERE id = ? AND status = 'PENDING'"
    );

    const auditStmt = db.prepare(
      `INSERT INTO recommendation_audit (recommendation_id, action, actor, comment, previous_status, new_status, timestamp)
       VALUES (?, 'APPROVED', 'system', ?, 'PENDING', 'APPROVED', ?)`
    );

    let approved = 0;
    const transaction = db.transaction(() => {
      for (const id of ids) {
        const result = updateStmt.run(now, id);
        if (result.changes > 0) {
          auditStmt.run(id, comment || null, now);
          approved++;
        }
      }
    });

    transaction();

    res.json({
      success: true,
      data: {
        approved,
        total: ids.length,
      },
    });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/v1/recommendations
 * List recommendations with filters: status, priority, type, page, limit, sort.
 */
router.get('/', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const {
      status,
      priority,
      type,
      department,
      algorithmId,
      page: pageStr,
      limit: limitStr,
      sort,
    } = req.query;

    const page = Math.max(parseInt(pageStr as string) || 1, 1);
    const limit = Math.min(Math.max(parseInt(limitStr as string) || 50, 1), 200);
    const offset = (page - 1) * limit;

    // Build dynamic WHERE clause
    const conditions: string[] = [];
    const params: any[] = [];

    if (status) {
      conditions.push('r.status = ?');
      params.push(status);
    }
    if (priority) {
      conditions.push('r.priority = ?');
      params.push(priority);
    }
    if (type) {
      conditions.push('r.type = ?');
      params.push(type);
    }
    if (department) {
      conditions.push('u.department = ?');
      params.push(department);
    }
    if (algorithmId) {
      conditions.push('r.algorithm_id = ?');
      params.push(algorithmId);
    }

    const whereClause = conditions.length > 0 ? 'WHERE ' + conditions.join(' AND ') : '';

    // Sort
    let orderClause = 'ORDER BY r.monthly_savings DESC';
    if (sort === 'date') orderClause = 'ORDER BY r.created_at DESC';
    if (sort === 'confidence') orderClause = 'ORDER BY r.confidence DESC';
    if (sort === 'priority') {
      orderClause = `ORDER BY CASE r.priority
        WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3 WHEN 'LOW' THEN 4 END`;
    }

    // Count total
    const countRow = db
      .prepare(
        `SELECT COUNT(*) as total FROM recommendations r LEFT JOIN users u ON r.user_id = u.id ${whereClause}`
      )
      .get(...params) as { total: number };

    // Fetch page
    const rows = db
      .prepare(
        `SELECT r.*, u.display_name
         FROM recommendations r
         LEFT JOIN users u ON r.user_id = u.id
         ${whereClause}
         ${orderClause}
         LIMIT ? OFFSET ?`
      )
      .all(...params, limit, offset);

    res.json({
      success: true,
      data: rows.map(mapRecommendation),
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
 * GET /api/v1/recommendations/:id
 * Single recommendation detail.
 */
router.get('/:id', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const row = db
      .prepare(
        `SELECT r.*, u.display_name
         FROM recommendations r
         LEFT JOIN users u ON r.user_id = u.id
         WHERE r.id = ?`
      )
      .get(req.params.id);

    if (!row) {
      throw createError(404, `Recommendation ${req.params.id} not found`, 'NOT_FOUND');
    }

    // Get audit trail
    const audit = db
      .prepare(
        'SELECT * FROM recommendation_audit WHERE recommendation_id = ? ORDER BY timestamp DESC'
      )
      .all(req.params.id);

    const data = mapRecommendation(row);
    (data as any).auditTrail = audit.map((a: any) => ({
      action: a.action,
      actor: a.actor,
      comment: a.comment,
      previousStatus: a.previous_status,
      newStatus: a.new_status,
      timestamp: a.timestamp,
    }));

    res.json({
      success: true,
      data,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/v1/recommendations/:id/approve
 * Approve a recommendation.
 */
router.post('/:id/approve', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const { comment } = req.body;
    const now = new Date().toISOString();

    const row = db.prepare('SELECT * FROM recommendations WHERE id = ?').get(req.params.id) as any;
    if (!row) {
      throw createError(404, `Recommendation ${req.params.id} not found`, 'NOT_FOUND');
    }

    const previousStatus = row.status;

    db.prepare("UPDATE recommendations SET status = 'APPROVED', updated_at = ? WHERE id = ?").run(
      now,
      req.params.id
    );

    db.prepare(
      `INSERT INTO recommendation_audit (recommendation_id, action, actor, comment, previous_status, new_status, timestamp)
       VALUES (?, 'APPROVED', 'system', ?, ?, 'APPROVED', ?)`
    ).run(req.params.id, comment || null, previousStatus, now);

    const updated = db.prepare('SELECT * FROM recommendations WHERE id = ?').get(req.params.id);

    res.json({
      success: true,
      data: mapRecommendation(updated),
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/v1/recommendations/:id/reject
 * Reject a recommendation (requires reason).
 */
router.post('/:id/reject', (req: Request, res: Response, next: NextFunction) => {
  try {
    const { reason } = req.body;
    if (!reason) {
      throw createError(400, 'Rejection reason is required', 'VALIDATION_ERROR');
    }

    const db = getDb();
    const now = new Date().toISOString();

    const row = db.prepare('SELECT * FROM recommendations WHERE id = ?').get(req.params.id) as any;
    if (!row) {
      throw createError(404, `Recommendation ${req.params.id} not found`, 'NOT_FOUND');
    }

    const previousStatus = row.status;

    db.prepare("UPDATE recommendations SET status = 'REJECTED', updated_at = ? WHERE id = ?").run(
      now,
      req.params.id
    );

    db.prepare(
      `INSERT INTO recommendation_audit (recommendation_id, action, actor, comment, previous_status, new_status, timestamp)
       VALUES (?, 'REJECTED', 'system', ?, ?, 'REJECTED', ?)`
    ).run(req.params.id, reason, previousStatus, now);

    const updated = db.prepare('SELECT * FROM recommendations WHERE id = ?').get(req.params.id);

    res.json({
      success: true,
      data: mapRecommendation(updated),
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/v1/recommendations/:id/rollback
 * Rollback an approved/implemented recommendation.
 */
router.post('/:id/rollback', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const { reason } = req.body;
    const now = new Date().toISOString();

    const row = db.prepare('SELECT * FROM recommendations WHERE id = ?').get(req.params.id) as any;
    if (!row) {
      throw createError(404, `Recommendation ${req.params.id} not found`, 'NOT_FOUND');
    }

    const previousStatus = row.status;

    db.prepare(
      "UPDATE recommendations SET status = 'ROLLED_BACK', updated_at = ? WHERE id = ?"
    ).run(now, req.params.id);

    db.prepare(
      `INSERT INTO recommendation_audit (recommendation_id, action, actor, comment, previous_status, new_status, timestamp)
       VALUES (?, 'ROLLED_BACK', 'system', ?, ?, 'ROLLED_BACK', ?)`
    ).run(req.params.id, reason || null, previousStatus, now);

    const updated = db.prepare('SELECT * FROM recommendations WHERE id = ?').get(req.params.id);

    res.json({
      success: true,
      data: mapRecommendation(updated),
    });
  } catch (err) {
    next(err);
  }
});

export default router;
