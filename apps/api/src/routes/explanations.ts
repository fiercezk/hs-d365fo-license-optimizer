/**
 * Explanations API Routes
 * Endpoint: get cached AI explanation (stub)
 */
import { Router, Request, Response, NextFunction } from 'express';
import { getDb } from '../db/connection';

const router = Router();

/**
 * GET /api/v1/explanations/:entityType/:entityId
 * Returns cached AI explanation for an entity, or null if not generated yet.
 * This is a stub - production will call Claude API for generation.
 */
router.get('/:entityType/:entityId', (req: Request, res: Response, next: NextFunction) => {
  try {
    const { entityType, entityId } = req.params;
    const db = getDb();

    // Check cache
    const cached = db
      .prepare(
        'SELECT explanation, model_used, tokens_used, generated_at FROM ai_explanations WHERE entity_type = ? AND entity_id = ?'
      )
      .get(entityType, entityId) as any;

    if (cached) {
      res.json({
        success: true,
        data: {
          entityType,
          entityId,
          explanation: cached.explanation,
          modelUsed: cached.model_used,
          tokensUsed: cached.tokens_used,
          generatedAt: cached.generated_at,
        },
      });
    } else {
      // No explanation cached yet - return null
      res.json({
        success: true,
        data: {
          entityType,
          entityId,
          explanation: null,
          modelUsed: null,
          tokensUsed: null,
          generatedAt: null,
        },
      });
    }
  } catch (err) {
    next(err);
  }
});

export default router;
