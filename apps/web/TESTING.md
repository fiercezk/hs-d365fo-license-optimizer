# Local Testing Guide

This guide covers how to run and test the D365 FO License Agent locally without deploying to Azure.

---

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Web app dependencies
cd apps/web
bun install

# Mock API server dependencies
npm install express cors
```

### 2. Start Mock API Server

```bash
# From apps/web directory
node mock-api-server.js
```

Expected output:
```
============================================================
  D365 FO License Agent - Mock API Server
============================================================
  Status: Running on http://localhost:3001
  Endpoints: 11 endpoints available
```

### 3. Configure Web App

```bash
# Create .env.local file
cp .env.local.example .env.local

# Edit .env.local to point to mock server
# NEXT_PUBLIC_API_URL=http://localhost:3001
```

### 4. Start Web App

```bash
# In apps/web directory (separate terminal)
bun dev
```

### 5. Test Dashboard

Open browser: **http://localhost:3000**

You should see:
- ✅ Executive Dashboard with metrics
- ✅ Cost Trend Chart (12-month data)
- ✅ Top 5 Optimization Opportunities
- ✅ Security Alerts panel
- ✅ No "Failed to Load" errors

---

## Test Scenarios

### Scenario 1: View Dashboard Metrics

**Steps:**
1. Navigate to `http://localhost:3000`
2. Observe metrics cards

**Expected Results:**
- Total License Cost: $180,000
- Monthly Savings: $12,500
- YTD Savings: $75,000
- Users Analyzed: 1,234
- Pending Recommendations: 156

### Scenario 2: View Cost Trend

**Steps:**
1. Scroll to "License Cost Trend" chart
2. Hover over data points

**Expected Results:**
- 12 months of data displayed
- Three lines: Actual Cost (blue), Forecast (gray dotted), Target (green)
- Tooltip shows values when hovering
- Summary stats below chart (current month, savings, average)

### Scenario 3: View Recommendations

**Steps:**
1. Click "Algorithms" in sidebar
2. View recommendations list

**Expected Results:**
- 3 sample recommendations displayed
- Filters work (type, priority, status)
- Click row to view details

### Scenario 4: Approve Recommendation

**Steps:**
1. Navigate to Algorithms page
2. Click first recommendation (John Doe)
3. Click "Approve" button
4. Check browser console for API call

**Expected Results:**
- Browser console shows: `POST /api/v1/recommendations/REC-001/approve`
- Mock server logs: `Approved recommendation REC-001`
- Success message displayed

### Scenario 5: New User License Wizard

**Steps:**
1. Click "Wizard" in sidebar
2. Select menu items: PurchTable, VendTable
3. Click "Next"
4. Review recommendations

**Expected Results:**
- 2 license recommendations displayed
- Option 1: Team Members ($60/month) - Recommended
- Option 2: Operations Activity ($90/month)
- SoD conflicts: None

---

## API Endpoints Available

The mock server provides these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/metrics` | Dashboard summary metrics |
| GET | `/api/v1/algorithms/5.1/trend` | Cost trend data (12 months) |
| GET | `/api/v1/recommendations` | List recommendations (supports filters) |
| GET | `/api/v1/recommendations/:userId` | User-specific recommendations |
| POST | `/api/v1/recommendations/:id/approve` | Approve recommendation |
| POST | `/api/v1/recommendations/:id/reject` | Reject recommendation |
| POST | `/api/v1/recommendations/:id/rollback` | Rollback implemented change |
| POST | `/api/v1/analyze` | Trigger analysis |
| POST | `/api/v1/suggest-license` | New user license wizard |
| GET | `/api/v1/agent/health` | Agent health status |
| GET | `/api/v1/security/alerts` | Security alerts |

---

## Troubleshooting

### Issue: Dashboard shows "Failed to Load Dashboard"

**Solution:**
1. Check mock API server is running: `curl http://localhost:3001/api/v1/dashboard/metrics`
2. Check `.env.local` has correct URL: `NEXT_PUBLIC_API_URL=http://localhost:3001`
3. Restart web app: `bun dev`

### Issue: Chart not rendering

**Solution:**
1. Check browser console for errors
2. Verify Recharts installed: `bun install recharts`
3. Check API returns data: `curl http://localhost:3001/api/v1/algorithms/5.1/trend?months=12`

### Issue: CORS errors in browser console

**Solution:**
Mock server has CORS enabled. If issue persists:
1. Restart mock server
2. Clear browser cache
3. Use browser DevTools > Network tab to inspect preflight OPTIONS requests

---

## What's Missing for Production

**⚠️ The mock server is for LOCAL TESTING ONLY. For production deployment, you need:**

1. **Azure Functions API Backend** (TypeScript)
   - Real API implementation calling Python algorithms
   - Authentication (Azure AD)
   - Rate limiting, input validation
   - Error handling, logging

2. **Database Schema** (Azure SQL)
   - Tables: Recommendations, Users, AuditLog, AlgorithmConfig
   - Migrations for schema versioning
   - Seed data for initial setup

3. **Azure Deployment**
   - Deploy infrastructure (Bicep templates)
   - Configure environment variables
   - Set up CI/CD pipeline

4. **Chat Interface** (mentioned by user, not yet built)
   - React chat component
   - WebSocket connection
   - AI agent integration (Azure OpenAI)

See `docs/Admin-Guide.md` for full deployment instructions.

---

## Next Steps

After validating local testing works:

1. **Implement Azure Functions API** (8-10 hours)
   - Create `apps/api/` directory
   - Implement TypeScript endpoints
   - Wire to Python algorithms via subprocess or HTTP

2. **Create Database Schema** (2-3 hours)
   - SQL migration scripts
   - Seed data
   - Entity models (Prisma or TypeORM)

3. **Build Chat Interface** (4-6 hours)
   - Chat component (React)
   - WebSocket server (Azure Functions)
   - Azure OpenAI integration

4. **Deploy to Azure** (2-4 hours)
   - Run Bicep deployment
   - Configure secrets in Key Vault
   - Deploy functions + web app

**Estimated Total: 16-23 hours for full production-ready system**

---

**Questions?** Check `docs/User-Manual.md` for user guide or `docs/Admin-Guide.md` for deployment.
