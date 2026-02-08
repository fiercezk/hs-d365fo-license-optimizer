/**
 * Agent API Routes
 * Endpoints: get config, update config
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
 * GET /api/v1/agent/config
 * Returns all algorithm configuration parameters.
 */
router.get('/config', (req: Request, res: Response, next: NextFunction) => {
  try {
    const db = getDb();

    const rows = db
      .prepare(
        'SELECT algorithm_id, param_name, param_value, param_type, description, updated_at, updated_by FROM algorithm_config ORDER BY algorithm_id, param_name'
      )
      .all();

    const data = rows.map((row: any) => ({
      algorithmId: row.algorithm_id,
      paramName: row.param_name,
      paramValue: row.param_value,
      paramType: row.param_type,
      description: row.description,
      updatedAt: row.updated_at,
      updatedBy: row.updated_by,
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
 * POST /api/v1/agent/config
 * Update an algorithm configuration parameter.
 */
router.post('/config', (req: Request, res: Response, next: NextFunction) => {
  try {
    const { algorithmId, paramName, paramValue } = req.body;

    if (!algorithmId || !paramName || paramValue === undefined || paramValue === null) {
      throw createError(
        400,
        'algorithmId, paramName, and paramValue are required',
        'VALIDATION_ERROR'
      );
    }

    const db = getDb();
    const now = new Date().toISOString();

    const result = db
      .prepare(
        `UPDATE algorithm_config
         SET param_value = ?, updated_at = ?, updated_by = 'api'
         WHERE algorithm_id = ? AND param_name = ?`
      )
      .run(String(paramValue), now, algorithmId, paramName);

    if (result.changes === 0) {
      // Insert if not exists
      db.prepare(
        `INSERT INTO algorithm_config (algorithm_id, param_name, param_value, param_type, updated_at, updated_by)
         VALUES (?, ?, ?, 'string', ?, 'api')`
      ).run(algorithmId, paramName, String(paramValue), now);
    }

    res.json({
      success: true,
      data: {
        algorithmId,
        paramName,
        paramValue: String(paramValue),
        updatedAt: now,
      },
    });
  } catch (err) {
    next(err);
  }
});

export default router;
