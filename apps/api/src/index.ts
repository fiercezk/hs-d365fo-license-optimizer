/**
 * D365 FO License Agent - Express API Server
 * Entry point: imports app from app.ts and starts the server.
 */
import app from './app';

const PORT = process.env.PORT || 3001;

app.listen(PORT, () => {
  console.log(`D365 License Agent API running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/api/v1/health`);
});

export default app;
