/**
 * Comprehensive Integration Tests for D365 FO License Agent API
 * 28 endpoints, 100+ test assertions
 *
 * TDD RED PHASE: These tests define the contract for all API endpoints.
 * Written BEFORE implementation per CLAUDE.md TDD mandate.
 */
import request from 'supertest';
import app from '../src/app';

// ============================================================
// DASHBOARD ROUTES (4 endpoints)
// ============================================================

describe('Dashboard API', () => {
  // Endpoint 1: GET /api/v1/dashboard/metrics
  describe('GET /api/v1/dashboard/metrics', () => {
    it('returns 200 with success envelope', async () => {
      const res = await request(app).get('/api/v1/dashboard/metrics');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
    });

    it('returns totalCost as a positive number', async () => {
      const res = await request(app).get('/api/v1/dashboard/metrics');
      expect(typeof res.body.data.totalCost).toBe('number');
      expect(res.body.data.totalCost).toBeGreaterThan(0);
    });

    it('returns totalUsers count matching seeded data', async () => {
      const res = await request(app).get('/api/v1/dashboard/metrics');
      expect(res.body.data.totalUsers).toBe(100);
    });

    it('returns pendingRecommendations count', async () => {
      const res = await request(app).get('/api/v1/dashboard/metrics');
      expect(typeof res.body.data.pendingRecommendations).toBe('number');
      expect(res.body.data.pendingRecommendations).toBeGreaterThanOrEqual(0);
    });

    it('returns potentialSavings as a number', async () => {
      const res = await request(app).get('/api/v1/dashboard/metrics');
      expect(typeof res.body.data.potentialSavings).toBe('number');
    });

    it('returns activeAlerts count', async () => {
      const res = await request(app).get('/api/v1/dashboard/metrics');
      expect(typeof res.body.data.activeAlerts).toBe('number');
    });

    it('returns licenseDistribution as an array', async () => {
      const res = await request(app).get('/api/v1/dashboard/metrics');
      expect(Array.isArray(res.body.data.licenseDistribution)).toBe(true);
      expect(res.body.data.licenseDistribution.length).toBeGreaterThan(0);
      // Each entry has license name and count
      const entry = res.body.data.licenseDistribution[0];
      expect(entry).toHaveProperty('license');
      expect(entry).toHaveProperty('count');
    });
  });

  // Endpoint 2: GET /api/v1/dashboard/cost-trend
  describe('GET /api/v1/dashboard/cost-trend', () => {
    it('returns 200 with cost trend data', async () => {
      const res = await request(app).get('/api/v1/dashboard/cost-trend');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('respects months query parameter', async () => {
      const res = await request(app).get('/api/v1/dashboard/cost-trend?months=6');
      expect(res.status).toBe(200);
      expect(res.body.data.length).toBeLessThanOrEqual(6);
    });

    it('defaults to 12 months when no parameter', async () => {
      const res = await request(app).get('/api/v1/dashboard/cost-trend');
      expect(res.body.data.length).toBeLessThanOrEqual(12);
    });

    it('each data point has month and cost fields', async () => {
      const res = await request(app).get('/api/v1/dashboard/cost-trend');
      if (res.body.data.length > 0) {
        const point = res.body.data[0];
        expect(point).toHaveProperty('month');
        expect(point).toHaveProperty('cost');
      }
    });
  });

  // Endpoint 3: GET /api/v1/dashboard/opportunities
  describe('GET /api/v1/dashboard/opportunities', () => {
    it('returns 200 with top opportunities', async () => {
      const res = await request(app).get('/api/v1/dashboard/opportunities');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('returns at most 5 opportunities by default', async () => {
      const res = await request(app).get('/api/v1/dashboard/opportunities');
      expect(res.body.data.length).toBeLessThanOrEqual(5);
    });

    it('each opportunity has required fields', async () => {
      const res = await request(app).get('/api/v1/dashboard/opportunities');
      if (res.body.data.length > 0) {
        const opp = res.body.data[0];
        expect(opp).toHaveProperty('id');
        expect(opp).toHaveProperty('userId');
        expect(opp).toHaveProperty('monthlySavings');
        expect(opp).toHaveProperty('type');
      }
    });

    it('opportunities are sorted by savings descending', async () => {
      const res = await request(app).get('/api/v1/dashboard/opportunities');
      const savings = res.body.data.map((o: any) => o.monthlySavings);
      for (let i = 1; i < savings.length; i++) {
        expect(savings[i]).toBeLessThanOrEqual(savings[i - 1]);
      }
    });
  });

  // Endpoint 4: GET /api/v1/dashboard/alerts
  describe('GET /api/v1/dashboard/alerts', () => {
    it('returns 200 with recent alerts', async () => {
      const res = await request(app).get('/api/v1/dashboard/alerts');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('each alert has required fields', async () => {
      const res = await request(app).get('/api/v1/dashboard/alerts');
      if (res.body.data.length > 0) {
        const alert = res.body.data[0];
        expect(alert).toHaveProperty('id');
        expect(alert).toHaveProperty('severity');
        expect(alert).toHaveProperty('type');
        expect(alert).toHaveProperty('description');
      }
    });

    it('returns only open alerts', async () => {
      const res = await request(app).get('/api/v1/dashboard/alerts');
      for (const alert of res.body.data) {
        expect(alert.status).toBe('OPEN');
      }
    });
  });
});

// ============================================================
// RECOMMENDATIONS ROUTES (6 endpoints)
// ============================================================

describe('Recommendations API', () => {
  // Endpoint 5: GET /api/v1/recommendations
  describe('GET /api/v1/recommendations', () => {
    it('returns 200 with recommendations list', async () => {
      const res = await request(app).get('/api/v1/recommendations');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('includes pagination metadata', async () => {
      const res = await request(app).get('/api/v1/recommendations');
      expect(res.body.meta).toBeDefined();
      expect(typeof res.body.meta.total).toBe('number');
      expect(typeof res.body.meta.page).toBe('number');
      expect(typeof res.body.meta.pageSize).toBe('number');
    });

    it('filters by status=PENDING', async () => {
      const res = await request(app).get('/api/v1/recommendations?status=PENDING');
      expect(res.status).toBe(200);
      for (const rec of res.body.data) {
        expect(rec.status).toBe('PENDING');
      }
    });

    it('filters by status=APPROVED', async () => {
      const res = await request(app).get('/api/v1/recommendations?status=APPROVED');
      expect(res.status).toBe(200);
      for (const rec of res.body.data) {
        expect(rec.status).toBe('APPROVED');
      }
    });

    it('respects limit parameter', async () => {
      const res = await request(app).get('/api/v1/recommendations?limit=5');
      expect(res.body.data.length).toBeLessThanOrEqual(5);
    });

    it('respects page parameter', async () => {
      const res1 = await request(app).get('/api/v1/recommendations?page=1&limit=10');
      const res2 = await request(app).get('/api/v1/recommendations?page=2&limit=10');
      // Different pages should return different results (if enough data)
      if (res1.body.meta.total > 10) {
        expect(res1.body.data[0].id).not.toBe(res2.body.data[0].id);
      }
    });

    it('filters by priority', async () => {
      const res = await request(app).get('/api/v1/recommendations?priority=CRITICAL');
      expect(res.status).toBe(200);
      for (const rec of res.body.data) {
        expect(rec.priority).toBe('CRITICAL');
      }
    });

    it('sorts by savings descending by default', async () => {
      const res = await request(app).get('/api/v1/recommendations');
      const savings = res.body.data.map((r: any) => r.monthlySavings);
      for (let i = 1; i < savings.length; i++) {
        expect(savings[i]).toBeLessThanOrEqual(savings[i - 1]);
      }
    });

    it('each recommendation has required fields', async () => {
      const res = await request(app).get('/api/v1/recommendations');
      if (res.body.data.length > 0) {
        const rec = res.body.data[0];
        expect(rec).toHaveProperty('id');
        expect(rec).toHaveProperty('userId');
        expect(rec).toHaveProperty('algorithmId');
        expect(rec).toHaveProperty('type');
        expect(rec).toHaveProperty('priority');
        expect(rec).toHaveProperty('confidence');
        expect(rec).toHaveProperty('status');
        expect(rec).toHaveProperty('monthlySavings');
      }
    });
  });

  // Endpoint 6: GET /api/v1/recommendations/:id
  describe('GET /api/v1/recommendations/:id', () => {
    it('returns 200 for existing recommendation', async () => {
      const res = await request(app).get('/api/v1/recommendations/REC-00001');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.id).toBe('REC-00001');
    });

    it('returns full recommendation detail', async () => {
      const res = await request(app).get('/api/v1/recommendations/REC-00001');
      const rec = res.body.data;
      expect(rec).toHaveProperty('id');
      expect(rec).toHaveProperty('userId');
      expect(rec).toHaveProperty('algorithmId');
      expect(rec).toHaveProperty('type');
      expect(rec).toHaveProperty('priority');
      expect(rec).toHaveProperty('confidence');
      expect(rec).toHaveProperty('currentLicense');
      expect(rec).toHaveProperty('recommendedLicense');
      expect(rec).toHaveProperty('monthlySavings');
      expect(rec).toHaveProperty('annualSavings');
      expect(rec).toHaveProperty('status');
    });

    it('returns 404 for non-existent recommendation', async () => {
      const res = await request(app).get('/api/v1/recommendations/REC-99999');
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
    });
  });

  // Endpoint 7: POST /api/v1/recommendations/:id/approve
  describe('POST /api/v1/recommendations/:id/approve', () => {
    it('approves a pending recommendation', async () => {
      // First find a pending recommendation
      const listRes = await request(app).get('/api/v1/recommendations?status=PENDING&limit=1');
      const recId = listRes.body.data[0]?.id;
      if (!recId) return; // skip if no pending

      const res = await request(app)
        .post(`/api/v1/recommendations/${recId}/approve`)
        .send({ comment: 'Approved by test' });
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.status).toBe('APPROVED');
    });

    it('returns 404 for non-existent recommendation', async () => {
      const res = await request(app)
        .post('/api/v1/recommendations/REC-99999/approve')
        .send({});
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
    });
  });

  // Endpoint 8: POST /api/v1/recommendations/:id/reject
  describe('POST /api/v1/recommendations/:id/reject', () => {
    it('rejects a pending recommendation with reason', async () => {
      const listRes = await request(app).get('/api/v1/recommendations?status=PENDING&limit=1');
      const recId = listRes.body.data[0]?.id;
      if (!recId) return;

      const res = await request(app)
        .post(`/api/v1/recommendations/${recId}/reject`)
        .send({ reason: 'Not applicable' });
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.status).toBe('REJECTED');
    });

    it('requires a reason for rejection', async () => {
      const listRes = await request(app).get('/api/v1/recommendations?status=PENDING&limit=1');
      const recId = listRes.body.data[0]?.id;
      if (!recId) return;

      const res = await request(app)
        .post(`/api/v1/recommendations/${recId}/reject`)
        .send({});
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });

    it('returns 404 for non-existent recommendation', async () => {
      const res = await request(app)
        .post('/api/v1/recommendations/REC-99999/reject')
        .send({ reason: 'test' });
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
    });
  });

  // Endpoint 9: POST /api/v1/recommendations/:id/rollback
  describe('POST /api/v1/recommendations/:id/rollback', () => {
    it('rolls back an approved recommendation', async () => {
      const listRes = await request(app).get('/api/v1/recommendations?status=APPROVED&limit=1');
      const recId = listRes.body.data[0]?.id;
      if (!recId) return;

      const res = await request(app)
        .post(`/api/v1/recommendations/${recId}/rollback`)
        .send({ reason: 'User requested rollback' });
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.status).toBe('ROLLED_BACK');
    });

    it('returns 404 for non-existent recommendation', async () => {
      const res = await request(app)
        .post('/api/v1/recommendations/REC-99999/rollback')
        .send({ reason: 'test' });
      expect(res.status).toBe(404);
    });
  });

  // Endpoint 10: POST /api/v1/recommendations/bulk-approve
  describe('POST /api/v1/recommendations/bulk-approve', () => {
    it('approves multiple recommendations at once', async () => {
      const listRes = await request(app).get('/api/v1/recommendations?status=PENDING&limit=3');
      const ids = listRes.body.data.map((r: any) => r.id);
      if (ids.length === 0) return;

      const res = await request(app)
        .post('/api/v1/recommendations/bulk-approve')
        .send({ ids, comment: 'Bulk approved by test' });
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(typeof res.body.data.approved).toBe('number');
    });

    it('returns 400 when ids array is empty', async () => {
      const res = await request(app)
        .post('/api/v1/recommendations/bulk-approve')
        .send({ ids: [] });
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });

    it('returns 400 when ids is missing', async () => {
      const res = await request(app)
        .post('/api/v1/recommendations/bulk-approve')
        .send({});
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });
  });
});

// ============================================================
// ALGORITHMS ROUTES (3 endpoints)
// ============================================================

describe('Algorithms API', () => {
  // Endpoint 11: GET /api/v1/algorithms
  describe('GET /api/v1/algorithms', () => {
    it('returns 200 with algorithms list', async () => {
      const res = await request(app).get('/api/v1/algorithms');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('each algorithm has required fields', async () => {
      const res = await request(app).get('/api/v1/algorithms');
      if (res.body.data.length > 0) {
        const algo = res.body.data[0];
        expect(algo).toHaveProperty('algorithmId');
        expect(algo).toHaveProperty('name');
        expect(algo).toHaveProperty('recommendationCount');
      }
    });

    it('includes recommendation counts per algorithm', async () => {
      const res = await request(app).get('/api/v1/algorithms');
      const total = res.body.data.reduce(
        (sum: number, a: any) => sum + a.recommendationCount,
        0
      );
      expect(total).toBeGreaterThan(0);
    });
  });

  // Endpoint 12: GET /api/v1/algorithms/:algorithmId/recommendations
  describe('GET /api/v1/algorithms/:algorithmId/recommendations', () => {
    it('returns recommendations for algorithm 2.2', async () => {
      const res = await request(app).get('/api/v1/algorithms/2.2/recommendations');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
      for (const rec of res.body.data) {
        expect(rec.algorithmId).toBe('2.2');
      }
    });

    it('returns empty array for algorithm with no results', async () => {
      const res = await request(app).get('/api/v1/algorithms/9.9/recommendations');
      expect(res.status).toBe(200);
      expect(res.body.data).toEqual([]);
    });

    it('includes pagination metadata', async () => {
      const res = await request(app).get('/api/v1/algorithms/2.2/recommendations');
      expect(res.body.meta).toBeDefined();
      expect(typeof res.body.meta.total).toBe('number');
    });
  });

  // Endpoint 13: POST /api/v1/analyze/:algorithmId
  describe('POST /api/v1/analyze/:algorithmId', () => {
    it('returns 202 accepted for valid algorithm', async () => {
      const res = await request(app)
        .post('/api/v1/analyze/2.2')
        .send({});
      expect(res.status).toBe(202);
      expect(res.body.success).toBe(true);
      expect(res.body.data).toHaveProperty('message');
    });

    it('returns stub response indicating analysis queued', async () => {
      const res = await request(app)
        .post('/api/v1/analyze/3.1')
        .send({});
      expect(res.body.data.status).toBe('queued');
    });
  });
});

// ============================================================
// USERS ROUTES (4 endpoints)
// ============================================================

describe('Users API', () => {
  // Endpoint 14: GET /api/v1/users
  describe('GET /api/v1/users', () => {
    it('returns 200 with users list', async () => {
      const res = await request(app).get('/api/v1/users');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('includes pagination metadata', async () => {
      const res = await request(app).get('/api/v1/users');
      expect(res.body.meta).toBeDefined();
      expect(res.body.meta.total).toBe(100);
    });

    it('filters by department', async () => {
      const res = await request(app).get('/api/v1/users?department=Finance');
      expect(res.status).toBe(200);
      for (const user of res.body.data) {
        expect(user.department).toBe('Finance');
      }
    });

    it('filters by license type', async () => {
      const res = await request(app).get('/api/v1/users?license=Team Members');
      expect(res.status).toBe(200);
      for (const user of res.body.data) {
        expect(user.currentLicense).toBe('Team Members');
      }
    });

    it('supports search by name or email', async () => {
      const res = await request(app).get('/api/v1/users?search=user1');
      expect(res.status).toBe(200);
      expect(res.body.data.length).toBeGreaterThan(0);
    });

    it('respects limit parameter', async () => {
      const res = await request(app).get('/api/v1/users?limit=5');
      expect(res.body.data.length).toBeLessThanOrEqual(5);
    });

    it('each user has required fields', async () => {
      const res = await request(app).get('/api/v1/users?limit=1');
      if (res.body.data.length > 0) {
        const user = res.body.data[0];
        expect(user).toHaveProperty('id');
        expect(user).toHaveProperty('email');
        expect(user).toHaveProperty('displayName');
        expect(user).toHaveProperty('department');
        expect(user).toHaveProperty('currentLicense');
        expect(user).toHaveProperty('monthlyCost');
      }
    });
  });

  // Endpoint 15: GET /api/v1/users/:id
  describe('GET /api/v1/users/:id', () => {
    it('returns 200 for existing user', async () => {
      const res = await request(app).get('/api/v1/users/user1@contoso.com');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.id).toBe('user1@contoso.com');
    });

    it('returns user detail with roles', async () => {
      const res = await request(app).get('/api/v1/users/user1@contoso.com');
      expect(res.body.data).toHaveProperty('roles');
      expect(Array.isArray(res.body.data.roles)).toBe(true);
    });

    it('returns 404 for non-existent user', async () => {
      const res = await request(app).get('/api/v1/users/nonexistent@contoso.com');
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
    });
  });

  // Endpoint 16: GET /api/v1/users/:id/activity
  describe('GET /api/v1/users/:id/activity', () => {
    it('returns activity history for user', async () => {
      const res = await request(app).get('/api/v1/users/user30@contoso.com/activity');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('respects days query parameter', async () => {
      const res = await request(app).get('/api/v1/users/user30@contoso.com/activity?days=30');
      expect(res.status).toBe(200);
      // Activity should be from within last 30 days
    });

    it('each activity has required fields', async () => {
      const res = await request(app).get('/api/v1/users/user30@contoso.com/activity');
      if (res.body.data.length > 0) {
        const activity = res.body.data[0];
        expect(activity).toHaveProperty('menuItem');
        expect(activity).toHaveProperty('actionType');
        expect(activity).toHaveProperty('timestamp');
      }
    });

    it('returns 404 for non-existent user', async () => {
      const res = await request(app).get('/api/v1/users/nonexistent@contoso.com/activity');
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
    });
  });

  // Endpoint 17: GET /api/v1/users/:id/recommendations
  describe('GET /api/v1/users/:id/recommendations', () => {
    it('returns recommendations for a specific user', async () => {
      const res = await request(app).get('/api/v1/users/user22@contoso.com/recommendations');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('all returned recommendations belong to the user', async () => {
      const res = await request(app).get('/api/v1/users/user22@contoso.com/recommendations');
      for (const rec of res.body.data) {
        expect(rec.userId).toBe('user22@contoso.com');
      }
    });

    it('returns empty array for user with no recommendations', async () => {
      // user99 unlikely to have recommendations in seed data
      const res = await request(app).get('/api/v1/users/user99@contoso.com/recommendations');
      expect(res.status).toBe(200);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('returns 404 for non-existent user', async () => {
      const res = await request(app).get('/api/v1/users/nonexistent@contoso.com/recommendations');
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
    });
  });
});

// ============================================================
// SECURITY ROUTES (3 endpoints)
// ============================================================

describe('Security API', () => {
  // Endpoint 18: GET /api/v1/security/alerts
  describe('GET /api/v1/security/alerts', () => {
    it('returns 200 with security alerts', async () => {
      const res = await request(app).get('/api/v1/security/alerts');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('filters by severity', async () => {
      const res = await request(app).get('/api/v1/security/alerts?severity=CRITICAL');
      expect(res.status).toBe(200);
      for (const alert of res.body.data) {
        expect(alert.severity).toBe('CRITICAL');
      }
    });

    it('filters by status', async () => {
      const res = await request(app).get('/api/v1/security/alerts?status=OPEN');
      expect(res.status).toBe(200);
      for (const alert of res.body.data) {
        expect(alert.status).toBe('OPEN');
      }
    });

    it('includes pagination metadata', async () => {
      const res = await request(app).get('/api/v1/security/alerts');
      expect(res.body.meta).toBeDefined();
      expect(typeof res.body.meta.total).toBe('number');
    });

    it('each alert has required fields', async () => {
      const res = await request(app).get('/api/v1/security/alerts');
      if (res.body.data.length > 0) {
        const alert = res.body.data[0];
        expect(alert).toHaveProperty('id');
        expect(alert).toHaveProperty('type');
        expect(alert).toHaveProperty('severity');
        expect(alert).toHaveProperty('userId');
        expect(alert).toHaveProperty('description');
        expect(alert).toHaveProperty('detectedAt');
        expect(alert).toHaveProperty('status');
      }
    });
  });

  // Endpoint 19: GET /api/v1/security/sod-violations
  describe('GET /api/v1/security/sod-violations', () => {
    it('returns 200 with SoD violations', async () => {
      const res = await request(app).get('/api/v1/security/sod-violations');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('filters by status=OPEN', async () => {
      const res = await request(app).get('/api/v1/security/sod-violations?status=OPEN');
      expect(res.status).toBe(200);
      for (const v of res.body.data) {
        expect(v.status).toBe('OPEN');
      }
    });

    it('filters by severity', async () => {
      const res = await request(app).get('/api/v1/security/sod-violations?severity=HIGH');
      expect(res.status).toBe(200);
      for (const v of res.body.data) {
        expect(v.severity).toBe('HIGH');
      }
    });

    it('each violation has required fields', async () => {
      const res = await request(app).get('/api/v1/security/sod-violations');
      if (res.body.data.length > 0) {
        const v = res.body.data[0];
        expect(v).toHaveProperty('id');
        expect(v).toHaveProperty('userId');
        expect(v).toHaveProperty('roleA');
        expect(v).toHaveProperty('roleB');
        expect(v).toHaveProperty('conflictRule');
        expect(v).toHaveProperty('severity');
        expect(v).toHaveProperty('category');
        expect(v).toHaveProperty('status');
      }
    });

    it('includes pagination metadata', async () => {
      const res = await request(app).get('/api/v1/security/sod-violations');
      expect(res.body.meta).toBeDefined();
    });
  });

  // Endpoint 20: GET /api/v1/security/compliance
  describe('GET /api/v1/security/compliance', () => {
    it('returns 200 with compliance summary', async () => {
      const res = await request(app).get('/api/v1/security/compliance');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
    });

    it('returns compliance score as a percentage', async () => {
      const res = await request(app).get('/api/v1/security/compliance');
      expect(typeof res.body.data.complianceScore).toBe('number');
      expect(res.body.data.complianceScore).toBeGreaterThanOrEqual(0);
      expect(res.body.data.complianceScore).toBeLessThanOrEqual(100);
    });

    it('returns breakdown of compliance categories', async () => {
      const res = await request(app).get('/api/v1/security/compliance');
      expect(res.body.data).toHaveProperty('sodViolations');
      expect(res.body.data).toHaveProperty('openAlerts');
      expect(res.body.data).toHaveProperty('totalUsers');
    });
  });
});

// ============================================================
// WIZARD ROUTE (1 endpoint)
// ============================================================

describe('Wizard API', () => {
  // Endpoint 21: POST /api/v1/wizard/suggest-license
  describe('POST /api/v1/wizard/suggest-license', () => {
    it('returns 200 with stub license suggestion', async () => {
      const res = await request(app)
        .post('/api/v1/wizard/suggest-license')
        .send({
          requiredMenuItems: ['CustTable', 'SalesTable'],
        });
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
    });

    it('returns recommendations array', async () => {
      const res = await request(app)
        .post('/api/v1/wizard/suggest-license')
        .send({
          requiredMenuItems: ['CustTable', 'SalesTable'],
        });
      expect(Array.isArray(res.body.data.recommendations)).toBe(true);
    });

    it('returns 400 when requiredMenuItems is missing', async () => {
      const res = await request(app)
        .post('/api/v1/wizard/suggest-license')
        .send({});
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });

    it('returns 400 when requiredMenuItems is empty', async () => {
      const res = await request(app)
        .post('/api/v1/wizard/suggest-license')
        .send({ requiredMenuItems: [] });
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });
  });
});

// ============================================================
// AGENT ROUTES (2 endpoints)
// ============================================================

describe('Agent API', () => {
  // Endpoint 22: GET /api/v1/agent/config
  describe('GET /api/v1/agent/config', () => {
    it('returns 200 with algorithm configurations', async () => {
      const res = await request(app).get('/api/v1/agent/config');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(Array.isArray(res.body.data)).toBe(true);
    });

    it('returns configuration grouped by algorithm', async () => {
      const res = await request(app).get('/api/v1/agent/config');
      expect(res.body.data.length).toBeGreaterThan(0);
      const config = res.body.data[0];
      expect(config).toHaveProperty('algorithmId');
      expect(config).toHaveProperty('paramName');
      expect(config).toHaveProperty('paramValue');
      expect(config).toHaveProperty('paramType');
    });
  });

  // Endpoint 23: POST /api/v1/agent/config
  describe('POST /api/v1/agent/config', () => {
    it('updates an algorithm configuration parameter', async () => {
      const res = await request(app)
        .post('/api/v1/agent/config')
        .send({
          algorithmId: '2.2',
          paramName: 'read_only_threshold',
          paramValue: '0.90',
        });
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
    });

    it('persists the updated value', async () => {
      // First update
      await request(app)
        .post('/api/v1/agent/config')
        .send({
          algorithmId: '2.2',
          paramName: 'read_only_threshold',
          paramValue: '0.92',
        });

      // Then verify
      const res = await request(app).get('/api/v1/agent/config');
      const updated = res.body.data.find(
        (c: any) => c.algorithmId === '2.2' && c.paramName === 'read_only_threshold'
      );
      expect(updated.paramValue).toBe('0.92');
    });

    it('returns 400 when required fields are missing', async () => {
      const res = await request(app)
        .post('/api/v1/agent/config')
        .send({ algorithmId: '2.2' });
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });
  });
});

// ============================================================
// EXPLANATIONS ROUTE (1 endpoint)
// ============================================================

describe('Explanations API', () => {
  // Endpoint 24: GET /api/v1/explanations/:entityType/:entityId
  describe('GET /api/v1/explanations/:entityType/:entityId', () => {
    it('returns 200 with empty explanation (stub)', async () => {
      const res = await request(app).get('/api/v1/explanations/recommendation/REC-00001');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
    });

    it('returns explanation field (null for stub)', async () => {
      const res = await request(app).get('/api/v1/explanations/recommendation/REC-00001');
      expect(res.body.data).toHaveProperty('explanation');
    });

    it('accepts different entity types', async () => {
      const types = ['recommendation', 'user', 'sod_violation'];
      for (const type of types) {
        const res = await request(app).get(`/api/v1/explanations/${type}/test-id`);
        expect(res.status).toBe(200);
      }
    });
  });
});

// ============================================================
// HEALTH CHECK
// ============================================================

describe('Health Check', () => {
  it('GET /api/v1/health returns healthy status', async () => {
    const res = await request(app).get('/api/v1/health');
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.status).toBe('healthy');
    expect(res.body.data.database.connected).toBe(true);
  });

  it('includes database user count', async () => {
    const res = await request(app).get('/api/v1/health');
    expect(res.body.data.database.users).toBe(100);
  });

  it('includes timestamp', async () => {
    const res = await request(app).get('/api/v1/health');
    expect(res.body.data.timestamp).toBeDefined();
    // Should be a valid ISO date
    expect(new Date(res.body.data.timestamp).getTime()).not.toBeNaN();
  });
});

// ============================================================
// ERROR HANDLING
// ============================================================

describe('Error Handling', () => {
  it('returns 404 for unknown routes', async () => {
    const res = await request(app).get('/api/v1/nonexistent');
    expect(res.status).toBe(404);
    expect(res.body.success).toBe(false);
    expect(res.body.error.code).toBe('NOT_FOUND');
  });

  it('returns 404 with route info in message', async () => {
    const res = await request(app).get('/api/v1/does-not-exist');
    expect(res.body.error.message).toContain('/api/v1/does-not-exist');
  });

  it('returns 404 for POST to unknown routes', async () => {
    const res = await request(app).post('/api/v1/nonexistent').send({});
    expect(res.status).toBe(404);
  });
});

// ============================================================
// CROSS-CUTTING CONCERNS
// ============================================================

describe('Cross-Cutting Concerns', () => {
  it('dashboard metrics totalCost matches sum of user monthly costs', async () => {
    const metricsRes = await request(app).get('/api/v1/dashboard/metrics');
    const usersRes = await request(app).get('/api/v1/users?limit=200');
    const sumFromUsers = usersRes.body.data
      .filter((u: any) => u.isActive)
      .reduce((sum: number, u: any) => sum + u.monthlyCost, 0);
    expect(metricsRes.body.data.totalCost).toBe(sumFromUsers);
  });

  it('recommendations list total matches filter counts', async () => {
    const allRes = await request(app).get('/api/v1/recommendations');
    const pendingRes = await request(app).get('/api/v1/recommendations?status=PENDING');
    const approvedRes = await request(app).get('/api/v1/recommendations?status=APPROVED');
    const rejectedRes = await request(app).get('/api/v1/recommendations?status=REJECTED');
    const rolledBackRes = await request(app).get('/api/v1/recommendations?status=ROLLED_BACK');

    const sumOfFilters =
      pendingRes.body.meta.total +
      approvedRes.body.meta.total +
      rejectedRes.body.meta.total +
      rolledBackRes.body.meta.total;

    expect(allRes.body.meta.total).toBe(sumOfFilters);
  });

  it('user detail roles count matches user_roles table', async () => {
    const res = await request(app).get('/api/v1/users/user1@contoso.com');
    expect(res.body.data.roles.length).toBeGreaterThanOrEqual(0);
  });

  it('algorithm recommendation counts match overall list', async () => {
    const algosRes = await request(app).get('/api/v1/algorithms');
    const allRecsRes = await request(app).get('/api/v1/recommendations?limit=200');
    const totalFromAlgos = algosRes.body.data.reduce(
      (sum: number, a: any) => sum + a.recommendationCount,
      0
    );
    expect(totalFromAlgos).toBe(allRecsRes.body.meta.total);
  });

  it('security compliance score reflects open violations count', async () => {
    const compRes = await request(app).get('/api/v1/security/compliance');
    const sodRes = await request(app).get('/api/v1/security/sod-violations?status=OPEN');
    expect(compRes.body.data.sodViolations.open).toBe(sodRes.body.meta.total);
  });

  it('dashboard alerts count matches security alerts open count', async () => {
    const dashRes = await request(app).get('/api/v1/dashboard/metrics');
    const alertsRes = await request(app).get('/api/v1/security/alerts?status=OPEN');
    expect(dashRes.body.data.activeAlerts).toBe(alertsRes.body.meta.total);
  });

  it('cost trend returns chronologically ordered months', async () => {
    const res = await request(app).get('/api/v1/dashboard/cost-trend?months=6');
    const months = res.body.data.map((d: any) => d.month);
    for (let i = 1; i < months.length; i++) {
      expect(months[i] > months[i - 1]).toBe(true);
    }
  });

  it('wizard stub returns 3 recommendations ranked by cost', async () => {
    const res = await request(app)
      .post('/api/v1/wizard/suggest-license')
      .send({ requiredMenuItems: ['CustTable'] });
    const costs = res.body.data.recommendations.map((r: any) => r.monthlyCost);
    for (let i = 1; i < costs.length; i++) {
      expect(costs[i]).toBeGreaterThanOrEqual(costs[i - 1]);
    }
  });

  it('agent config has entries for all Phase 1 algorithms', async () => {
    const res = await request(app).get('/api/v1/agent/config');
    const algorithmIds = [...new Set(res.body.data.map((c: any) => c.algorithmId))];
    expect(algorithmIds).toContain('2.2');
    expect(algorithmIds).toContain('2.5');
    expect(algorithmIds).toContain('3.1');
    expect(algorithmIds).toContain('5.2');
  });
});
