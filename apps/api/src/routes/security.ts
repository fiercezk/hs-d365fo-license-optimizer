/**
 * Security API Routes
 * Endpoints: alerts, sod-violations, compliance
 */
import { Router, Request, Response, NextFunction } from 'express';
import { getDb } from '../db/connection';

const router = Router();

/**
 * GET /api/v1/security/alerts
 * Security alerts with filters: severity, type, status, page, limit.
 */
router.get('/alerts', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const { severity, type, status, page: pageStr, limit: limitStr } = req.query;

    const page = Math.max(parseInt(pageStr as string) || 1, 1);
    const limit = Math.min(Math.max(parseInt(limitStr as string) || 50, 1), 200);
    const offset = (page - 1) * limit;

    const conditions: string[] = [];
    const params: any[] = [];

    if (severity) {
      conditions.push('severity = ?');
      params.push(severity);
    }
    if (type) {
      conditions.push('type = ?');
      params.push(type);
    }
    if (status) {
      conditions.push('status = ?');
      params.push(status);
    }

    const whereClause = conditions.length > 0 ? 'WHERE ' + conditions.join(' AND ') : '';

    const countRow = db
      .prepare(`SELECT COUNT(*) as total FROM security_alerts ${whereClause}`)
      .get(...params) as { total: number };

    const rows = db
      .prepare(
        `SELECT id, type, severity, user_id, description, details, detected_at, resolved_at, status
         FROM security_alerts
         ${whereClause}
         ORDER BY
           CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 WHEN 'LOW' THEN 4 END,
           detected_at DESC
         LIMIT ? OFFSET ?`
      )
      .all(...params, limit, offset);

    const data = rows.map((row: any) => ({
      id: row.id,
      type: row.type,
      severity: row.severity,
      userId: row.user_id,
      description: row.description,
      details: row.details ? JSON.parse(row.details) : null,
      detectedAt: row.detected_at,
      resolvedAt: row.resolved_at,
      status: row.status,
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
 * GET /api/v1/security/sod-violations
 * SoD violations with filters: severity, status, category.
 */
router.get('/sod-violations', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const { severity, status, category, page: pageStr, limit: limitStr } = req.query;

    const page = Math.max(parseInt(pageStr as string) || 1, 1);
    const limit = Math.min(Math.max(parseInt(limitStr as string) || 50, 1), 200);
    const offset = (page - 1) * limit;

    const conditions: string[] = [];
    const params: any[] = [];

    if (severity) {
      conditions.push('severity = ?');
      params.push(severity);
    }
    if (status) {
      conditions.push('status = ?');
      params.push(status);
    }
    if (category) {
      conditions.push('category = ?');
      params.push(category);
    }

    const whereClause = conditions.length > 0 ? 'WHERE ' + conditions.join(' AND ') : '';

    const countRow = db
      .prepare(`SELECT COUNT(*) as total FROM sod_violations ${whereClause}`)
      .get(...params) as { total: number };

    const rows = db
      .prepare(
        `SELECT id, user_id, role_a, role_b, conflict_rule, severity, category, description, detected_at, status, mitigation_notes
         FROM sod_violations
         ${whereClause}
         ORDER BY
           CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 WHEN 'LOW' THEN 4 END,
           detected_at DESC
         LIMIT ? OFFSET ?`
      )
      .all(...params, limit, offset);

    const data = rows.map((row: any) => ({
      id: row.id,
      userId: row.user_id,
      roleA: row.role_a,
      roleB: row.role_b,
      conflictRule: row.conflict_rule,
      severity: row.severity,
      category: row.category,
      description: row.description,
      detectedAt: row.detected_at,
      status: row.status,
      mitigationNotes: row.mitigation_notes,
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
 * GET /api/v1/security/compliance
 * Compliance summary with score calculation.
 */
router.get('/compliance', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();

    const totalUsers = db
      .prepare('SELECT COUNT(*) as count FROM users')
      .get() as { count: number };

    const openSodViolations = db
      .prepare("SELECT COUNT(*) as count FROM sod_violations WHERE status = 'OPEN'")
      .get() as { count: number };

    const openAlerts = db
      .prepare("SELECT COUNT(*) as count FROM security_alerts WHERE status = 'OPEN'")
      .get() as { count: number };

    const criticalAlerts = db
      .prepare("SELECT COUNT(*) as count FROM security_alerts WHERE severity = 'CRITICAL' AND status = 'OPEN'")
      .get() as { count: number };

    const mitigatedSod = db
      .prepare("SELECT COUNT(*) as count FROM sod_violations WHERE status IN ('MITIGATED', 'RESOLVED')")
      .get() as { count: number };

    const totalSod = db
      .prepare('SELECT COUNT(*) as count FROM sod_violations')
      .get() as { count: number };

    // Calculate compliance score (0-100)
    // Deduct points for open violations and alerts
    let score = 100;
    // Each open SoD violation: -10 points
    score -= openSodViolations.count * 10;
    // Each open critical alert: -15 points
    score -= criticalAlerts.count * 15;
    // Each open non-critical alert: -5 points
    score -= (openAlerts.count - criticalAlerts.count) * 5;
    // Clamp to 0-100
    score = Math.max(0, Math.min(100, score));

    res.json({
      success: true,
      data: {
        complianceScore: score,
        totalUsers: totalUsers.count,
        sodViolations: {
          open: openSodViolations.count,
          mitigated: mitigatedSod.count,
          total: totalSod.count,
        },
        openAlerts: openAlerts.count,
        criticalAlerts: criticalAlerts.count,
      },
    });
  } catch (err) {
    next(err);
  }
});

export default router;
