/**
 * Wizard API Routes
 * Endpoint: suggest-license (stub for Algorithm 4.7 integration)
 */
import { Router, Request, Response, NextFunction } from 'express';
import { ApiError } from '../middleware/error-handler';

const router = Router();

function createError(statusCode: number, message: string, code: string): ApiError {
  const err = new Error(message) as ApiError;
  err.statusCode = statusCode;
  err.code = code;
  return err;
}

/**
 * POST /api/v1/wizard/suggest-license
 * Stub: Accepts required menu items, returns mock license recommendations.
 * In production this calls the Python Algorithm 4.7 engine.
 */
router.post('/suggest-license', (req: Request, res: Response, next: NextFunction) => {
  try {
    const { requiredMenuItems } = req.body;

    if (!requiredMenuItems || !Array.isArray(requiredMenuItems) || requiredMenuItems.length === 0) {
      throw createError(
        400,
        'requiredMenuItems is required and must be a non-empty array',
        'VALIDATION_ERROR'
      );
    }

    // Stub response mimicking Algorithm 4.7 output
    const recommendations = [
      {
        rank: 1,
        licenseName: 'Team Members',
        monthlyCost: 60,
        roles: ['Team Members Basic'],
        coveragePercentage: 0.85,
        sodConflicts: [],
        explanation: 'Most cost-effective option covering majority of requested menu items.',
      },
      {
        rank: 2,
        licenseName: 'Operations',
        monthlyCost: 90,
        roles: ['Operations User'],
        coveragePercentage: 1.0,
        sodConflicts: [],
        explanation: 'Full coverage of all requested menu items with Operations license.',
      },
      {
        rank: 3,
        licenseName: 'Finance',
        monthlyCost: 180,
        roles: ['Finance User', 'Operations User'],
        coveragePercentage: 1.0,
        sodConflicts: [
          {
            roleA: 'Finance User',
            roleB: 'Operations User',
            rule: 'CR-5',
            severity: 'MEDIUM',
          },
        ],
        explanation: 'Premium license with full coverage but potential SoD conflict.',
      },
    ];

    res.json({
      success: true,
      data: {
        requiredMenuItems,
        recommendations,
        generatedAt: new Date().toISOString(),
        note: 'This is a stub response. Production will use Algorithm 4.7 engine.',
      },
    });
  } catch (err) {
    next(err);
  }
});

export default router;
