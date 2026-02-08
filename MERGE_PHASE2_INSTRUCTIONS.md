# Phase 2 Algorithm Merge Instructions

**Status:** Ready to merge - all consolidation branches exist
**Date:** 2026-02-07

---

## PR Creation (Manual - GitHub CLI not available)

Create 4 PRs via GitHub web interface:

### PR 1: Cost Optimization (19 algorithms)

**Base:** `main`
**Head:** `group-cost-optimization-v2`
**Title:** `feat: Cost Optimization algorithms (19 algorithms)`

**Body:**
```
## Algorithms

New algorithms (8):
- 1.1 Role License Composition Analyzer
- 1.2 User Segment Analyzer
- 1.3 Role Splitting Recommender
- 1.4 Component Removal Recommender
- 2.1 Permission vs. Usage Analyzer
- 2.3 Role Segmentation by Usage
- 2.4 Multi-Role Optimization
- 2.6 Cross-Role License Optimization

Plus 11 Phase 1 algorithms (base)

## Testing
All tests passing, quality gates green.
```

**URL:** https://github.com/fiercezk/hs-d365fo-license-optimizer/compare/main...group-cost-optimization-v2

---

### PR 2: Security & Compliance (17 algorithms)

**Base:** `main`
**Head:** `group-security-compliance`
**Title:** `feat: Security & Compliance algorithms (17 algorithms)`

**Body:**
```
## Algorithms

New algorithms (4):
- 3.5 Orphaned Account Detector
- 3.6 Emergency Account Monitor
- 3.7 Service Account Analyzer
- 3.8 Access Review Automation

Plus 11 Phase 1 algorithms + 3.9 Entra Sync + 5.4 Contractor Tracker (base)

## Testing
All tests passing, quality gates green.
```

**URL:** https://github.com/fiercezk/hs-d365fo-license-optimizer/compare/main...group-security-compliance

---

### PR 3: Analytics & Role Management (18 algorithms)

**Base:** `main`
**Head:** `group-analytics-role-mgmt`
**Title:** `feat: Analytics & Role Management algorithms (18 algorithms)`

**Body:**
```
## Algorithms

New algorithms (7):
- 4.2 License Attach Optimizer
- 5.3 Time-Based Access Analyzer
- 6.1 Stale Role Detector
- 6.3 Duplicate Role Consolidator
- 7.1 License Utilization Trend Analyzer
- 7.2 Cost Allocation Engine
- 7.4 ROI Calculator

Plus 11 Phase 1 algorithms (base)

## Testing
All tests passing, quality gates green.
```

**URL:** https://github.com/fiercezk/hs-d365fo-license-optimizer/compare/main...group-analytics-role-mgmt

---

### PR 4: Phase 2 Additional (15 algorithms)

**Base:** `main`
**Head:** `feature/algo-6-2`
**Title:** `feat: Phase 2 algorithms (15 algorithms)`

**Body:**
```
## Algorithms

Phase 2 algorithms (4):
- 3.9 Entra-D365 Sync Validator
- 5.4 Contractor Access Tracker
- 6.2 Permission Explosion Detector
- 6.4 Role Hierarchy Optimizer

Plus 11 Phase 1 algorithms (base)

## Testing
250/250 tests passing
Mypy: 0 errors
Ruff: 0 issues
```

**URL:** https://github.com/fiercezk/hs-d365fo-license-optimizer/compare/main...feature/algo-6-2

---

## Merge Order

1. Merge PR 4 first (feature/algo-6-2) - cleanest, already validated
2. Merge PR 1 (Cost Optimization)
3. Merge PR 2 (Security & Compliance)
4. Merge PR 3 (Analytics & Role Management)

## Post-Merge Validation

```bash
git checkout main
git pull origin main

# Verify all 34 algorithms present
find apps/agent/src/algorithms -name "algorithm_*.py" | wc -l
# Expected: 34

# Run full test suite
cd apps/agent
pytest tests/
# Expected: ~600-800 tests passing

# Quality gates
mypy src/
ruff check src/ tests/

# Tag release
git tag v1.0.0-complete
git push origin v1.0.0-complete
```

---

**Next Step:** Create these 4 PRs via GitHub web interface, then merge sequentially.
