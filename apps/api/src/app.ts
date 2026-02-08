/**
 * D365 FO License Agent - Express Application
 * Exports the app for use by server and tests.
 */
import express from 'express';
import cors from 'cors';
import { errorHandler, notFoundHandler } from './middleware/error-handler';
import { getDb } from './db/connection';
import dashboardRoutes from './routes/dashboard';
import recommendationsRoutes from './routes/recommendations';
import algorithmsRoutes from './routes/algorithms';
import usersRoutes from './routes/users';
import securityRoutes from './routes/security';
import wizardRoutes from './routes/wizard';
import agentRoutes from './routes/agent';
import explanationsRoutes from './routes/explanations';

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Request logging (skip in test)
if (process.env.NODE_ENV !== 'test') {
  app.use((req, _res, next) => {
    console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
    next();
  });
}

// Health check endpoint
app.get('/api/v1/health', (req, res) => {
  const db = getDb();
  const userCount = db.prepare('SELECT COUNT(*) as count FROM users').get() as any;

  res.json({
    success: true,
    data: {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: {
        connected: true,
        users: userCount.count,
      },
    },
  });
});

// API Routes
app.use('/api/v1/dashboard', dashboardRoutes);
app.use('/api/v1/recommendations', recommendationsRoutes);
app.use('/api/v1/algorithms', algorithmsRoutes);
app.use('/api/v1/analyze', algorithmsRoutes);
app.use('/api/v1/users', usersRoutes);
app.use('/api/v1/security', securityRoutes);
app.use('/api/v1/wizard', wizardRoutes);
app.use('/api/v1/agent', agentRoutes);
app.use('/api/v1/explanations', explanationsRoutes);

// Error handling
app.use(notFoundHandler);
app.use(errorHandler);

export default app;
