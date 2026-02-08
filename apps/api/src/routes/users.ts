/**
 * Users API Routes
 * Endpoints: list, detail, activity, recommendations
 */
import { Router, Request, Response, NextFunction } from 'express';
import { getDb } from '../db/connection';
import { ApiError } from '../middleware/error-handler';

const router = Router();

function createError(statusCode: number, message: string, code: string): ApiError {
  const err = new Error(message) as ApiError;
  err.statusCode = statusCode;
  err.code = code;
  return err;
}

/**
 * GET /api/v1/users
 * List users with filters: department, license, search, page, limit.
 */
router.get('/', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const { department, license, search, page: pageStr, limit: limitStr } = req.query;

    const page = Math.max(parseInt(pageStr as string) || 1, 1);
    const limit = Math.min(Math.max(parseInt(limitStr as string) || 50, 1), 200);
    const offset = (page - 1) * limit;

    const conditions: string[] = [];
    const params: any[] = [];

    if (department) {
      conditions.push('department = ?');
      params.push(department);
    }
    if (license) {
      conditions.push('current_license = ?');
      params.push(license);
    }
    if (search) {
      conditions.push('(display_name LIKE ? OR email LIKE ?)');
      params.push(`%${search}%`, `%${search}%`);
    }

    const whereClause = conditions.length > 0 ? 'WHERE ' + conditions.join(' AND ') : '';

    const countRow = db
      .prepare(`SELECT COUNT(*) as total FROM users ${whereClause}`)
      .get(...params) as { total: number };

    const rows = db
      .prepare(
        `SELECT id, email, display_name, department, current_license, monthly_cost, is_active, last_activity_at, roles_count
         FROM users
         ${whereClause}
         ORDER BY display_name ASC
         LIMIT ? OFFSET ?`
      )
      .all(...params, limit, offset);

    const data = rows.map((row: any) => ({
      id: row.id,
      email: row.email,
      displayName: row.display_name,
      department: row.department,
      currentLicense: row.current_license,
      monthlyCost: row.monthly_cost,
      isActive: row.is_active === 1,
      lastActivityAt: row.last_activity_at,
      rolesCount: row.roles_count,
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
 * GET /api/v1/users/:id
 * User detail with roles.
 */
router.get('/:id', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const row = db.prepare('SELECT * FROM users WHERE id = ?').get(req.params.id) as any;

    if (!row) {
      throw createError(404, `User ${req.params.id} not found`, 'NOT_FOUND');
    }

    const roles = db
      .prepare('SELECT role_name, assigned_at, is_active FROM user_roles WHERE user_id = ?')
      .all(req.params.id)
      .map((r: any) => ({
        roleName: r.role_name,
        assignedAt: r.assigned_at,
        isActive: r.is_active === 1,
      }));

    res.json({
      success: true,
      data: {
        id: row.id,
        email: row.email,
        displayName: row.display_name,
        department: row.department,
        currentLicense: row.current_license,
        monthlyCost: row.monthly_cost,
        isActive: row.is_active === 1,
        lastActivityAt: row.last_activity_at,
        rolesCount: row.roles_count,
        createdAt: row.created_at,
        updatedAt: row.updated_at,
        roles,
      },
    });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/v1/users/:id/activity?days=90
 * User activity history.
 */
router.get('/:id/activity', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();
    const days = Math.min(Math.max(parseInt(req.query.days as string) || 90, 1), 365);

    // Verify user exists
    const user = db.prepare('SELECT id FROM users WHERE id = ?').get(req.params.id);
    if (!user) {
      throw createError(404, `User ${req.params.id} not found`, 'NOT_FOUND');
    }

    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    const activities = db
      .prepare(
        `SELECT menu_item, action_type, form_name, license_required, timestamp
         FROM user_activity
         WHERE user_id = ? AND timestamp >= ?
         ORDER BY timestamp DESC`
      )
      .all(req.params.id, cutoff.toISOString());

    const data = activities.map((a: any) => ({
      menuItem: a.menu_item,
      actionType: a.action_type,
      formName: a.form_name,
      licenseRequired: a.license_required,
      timestamp: a.timestamp,
    }));

    res.json({
      success: true,
      data,
      meta: {
        userId: req.params.id,
        days,
        total: data.length,
      },
    });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/v1/users/:id/recommendations
 * Recommendations for a specific user.
 */
router.get('/:id/recommendations', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();

    // Verify user exists
    const user = db.prepare('SELECT id FROM users WHERE id = ?').get(req.params.id);
    if (!user) {
      throw createError(404, `User ${req.params.id} not found`, 'NOT_FOUND');
    }

    const rows = db
      .prepare(
        `SELECT * FROM recommendations WHERE user_id = ? ORDER BY monthly_savings DESC`
      )
      .all(req.params.id);

    const data = rows.map((row: any) => ({
      id: row.id,
      userId: row.user_id,
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
    });
  } catch (err) {
    next(err);
  }
});

export default router;
