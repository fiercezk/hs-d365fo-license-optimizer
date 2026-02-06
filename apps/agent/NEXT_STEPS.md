# Phase 2 Sequential Development - Next Steps

**Status:** Algorithm 1.4 complete ✅ | Remaining: 3 algorithms (1.1, 2.1, 3.5)
**Approach:** Sequential development (Council recommendation)
**Last Updated:** 2026-02-06

---

## Completed Work

### ✅ Algorithm 1.4 - Component Removal Recommender
- **Status:** 🟢 COMPLETE (ready for PR to main)
- **Branch:** `feature/algo-3-5`
- **Tests:** 12/12 passing
- **Quality:** Mypy clean, Ruff clean, 5/5 completeness checks
- **Commits:** 4 (KeyError fix, completeness script, manifests)
- **Next:** Create PR to main, merge, verify Gate 2

### ✅ Infrastructure Built
- **Completeness Checker:** `scripts/check_algorithm_completeness.py`
- **Manifest Template:** `MANIFEST.template.md`
- **Algorithm 1.4 Manifest:** `MANIFEST.md`
- **Purpose:** Enable parallel development with coordination

---

## Remaining Algorithms (RED-phase complete)

All 3 algorithms have RED-phase TDD complete (tests written, no implementations):

### 1. Algorithm 1.1 - Role License Composition Analyzer
- **Specification:** `Requirements/06-Algorithms-Decision-Logic.md`, lines 112-185
- **Category:** Role Management
- **Test File:** `tests/test_algorithm_1_1.py` (755 lines, 12 test classes)
- **Status:** 🔴 RED (tests exist, implementation missing)
- **Import Error:** `ModuleNotFoundError: No module named 'src.algorithms.algorithm_1_1_role_composition_analyzer'`

**What it does:** Analyzes role composition to identify redundant license requirements. Detects when a role requires multiple high-license components but usage suggests a single component would suffice.

**Priority:** HIGH (foundational for other role algorithms)

### 2. Algorithm 2.1 - Permission vs. Usage Analyzer
- **Specification:** `Requirements/06-Algorithms-Decision-Logic.md`, lines 187-256
- **Category:** Cost Optimization
- **Test File:** `tests/test_algorithm_2_1.py` (1021 lines)
- **Status:** 🔴 RED (tests exist, implementation missing)
- **Import Error:** `ModuleNotFoundError` (module doesn't exist)

**What it does:** Compares granted permissions (via roles) to actual usage telemetry to identify over-privileged users who could be downgraded to lower-cost licenses.

**Priority:** MEDIUM (builds on Phase 1 read-only detection)

### 3. Algorithm 3.5 - Orphaned Account Detector
- **Specification:** `Requirements/07-Advanced-Algorithms.md`, lines [TBD]
- **Category:** Security & Compliance
- **Test File:** `tests/test_algorithm_3_5.py` (561 lines, 8 fixture scenarios)
- **Test Fixtures:** `tests/fixtures/algo_3_5/` (8 JSON files)
- **Status:** 🔴 RED (tests exist, implementation missing)
- **Import Error:** `ModuleNotFoundError: No module named 'src.algorithms.algorithm_3_5_orphaned_account_detector'`

**What it does:** Detects orphaned D365 accounts (inactive, no manager, terminated employees) that still hold active licenses. Security risk + cost waste.

**Priority:** MEDIUM (security-critical but lower savings potential)

---

## Sequential Development Workflow

### Recommended Order
Based on dependencies and complexity:

1. **Algorithm 1.1** (Role Composition) - Foundational
2. **Algorithm 2.1** (Permission vs. Usage) - Moderate complexity
3. **Algorithm 3.5** (Orphaned Accounts) - Security-focused

### Workflow for Each Algorithm

#### Step 1: Merge Algorithm 1.4 to main
Before starting the next algorithm, ensure Algorithm 1.4 is merged and stable:

```bash
# After PR approval:
git checkout main
git pull origin main

# Verify Algorithm 1.4 is in main
python scripts/check_algorithm_completeness.py 1.4  # Should show 5/5

# Verify full suite
pytest  # Should show 187 passing (175 Phase 1 + 12 Algorithm 1.4)
```

#### Step 2: Create Feature Branch for Next Algorithm
Example for Algorithm 1.1:

```bash
git checkout main
git pull origin main
git checkout -b feature/algo-1-1

# Copy manifest template
cp MANIFEST.template.md MANIFEST.md

# Edit MANIFEST.md:
# - Update algorithm number to 1.1
# - Fill in specification reference
# - Document dependencies (check test file imports)
# - Review parallel branches (none expected in sequential approach)
```

#### Step 3: GREEN Phase - Implement Algorithm
Tests are already written (RED-phase complete). Now implement:

```bash
# Create implementation file
touch src/algorithms/algorithm_1_1_role_composition_analyzer.py

# Implement algorithm following specification and test expectations
# Refer to test file for expected function signatures and behavior

# Run tests (expect failures initially)
pytest tests/test_algorithm_1_1.py -v
```

**TDD Loop:**
1. Run test → fails with specific error
2. Write minimum code to fix that error
3. Run test again → next error or pass
4. Repeat until all tests pass

**Tips:**
- Read the test file carefully - it shows exact expected behavior
- Look at test helper functions to understand data structures
- Check imports in test file to see what classes/functions to export
- Use Phase 1 algorithms as reference for patterns (e.g., `algorithm_2_2_readonly_detector.py`)

#### Step 4: Quality Gates
After all tests pass:

```bash
# Type check
mypy src/algorithms/algorithm_1_1_*.py

# Lint
ruff check src/algorithms/algorithm_1_1_*.py tests/test_algorithm_1_1.py

# Fix any issues
ruff check --fix src/algorithms/algorithm_1_1_*.py tests/test_algorithm_1_1.py

# Register in __init__.py
# Edit src/algorithms/__init__.py:
# - Add import for algorithm_1_1_* module
# - Add exports to __all__ list

# Run completeness check
python scripts/check_algorithm_completeness.py 1.1

# Expected output: ✓ ALL CHECKS PASSED (5/5)
```

#### Step 5: Update Manifest and Commit

```bash
# Update MANIFEST.md:
# - Mark implementation checklist items as complete
# - Record test summary (X/X passing)
# - Document any design decisions or known limitations
# - Update status to 🟢 COMPLETE

# Commit
git add .
git commit -m "feat: implement Algorithm 1.1 - Role License Composition Analyzer

- Implementation: algorithm_1_1_role_composition_analyzer.py
- Tests: X/X passing
- Quality: mypy clean, ruff clean
- Registered in __init__.py

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"

# Push
git push -u origin feature/algo-1-1
```

#### Step 6: Create PR and Merge

```bash
# Create PR (if gh CLI available)
gh pr create --base main --head feature/algo-1-1 \
  --title "feat: Algorithm 1.1 - Role License Composition Analyzer (Phase 2)" \
  --body "See MANIFEST.md for full details. Gate 1: All checks pass."

# Or manually via GitHub web interface:
# https://github.com/fiercezk/hs-d365fo-license-optimizer/compare/main...feature/algo-1-1
```

**Gate 1 (Pre-Merge):** Verify tests, mypy, ruff, completeness
**Gate 2 (Post-Merge):** Full suite on main, regression tests

#### Step 7: Repeat for Next Algorithm
After Algorithm 1.1 is merged to main:
- Repeat Steps 1-6 for Algorithm 2.1
- Then repeat for Algorithm 3.5

---

## Current Branch Cleanup

### Branch: `feature/algo-3-5`
**Contains:**
- Algorithm 1.4 (COMPLETE)
- Algorithm 1.1 (RED-phase only)
- Algorithm 2.1 (RED-phase only)
- Algorithm 3.5 (RED-phase only)

**After Algorithm 1.4 PR is merged:**

**Option A:** Keep branch, delete RED-phase work
```bash
# Delete RED-phase test files and fixtures for 1.1, 2.1, 3.5
git rm tests/test_algorithm_1_1.py
git rm tests/test_algorithm_2_1.py
git rm tests/test_algorithm_3_5.py
git rm -r tests/fixtures/algo_3_5/
git commit -m "cleanup: remove RED-phase work for sequential development"
git push origin feature/algo-3-5

# Branch becomes: Algorithm 1.4 only (already merged, can delete)
```

**Option B:** Preserve RED-phase work in separate branches
```bash
# Copy RED-phase work to new branches before merging 1.4

# For Algorithm 1.1:
git checkout -b feature/algo-1-1-red
git reset --hard feature/algo-3-5  # Preserve current state
# Delete algorithm 1.4, 2.1, 3.5 test files, keep only 1.1
git push -u origin feature/algo-1-1-red

# For Algorithm 2.1:
git checkout feature/algo-3-5
git checkout -b feature/algo-2-1-red
# Delete algorithm 1.1, 1.4, 3.5 test files, keep only 2.1
git push -u origin feature/algo-2-1-red

# For Algorithm 3.5:
git checkout feature/algo-3-5
git checkout -b feature/algo-3-5-red
# Delete algorithm 1.1, 1.4, 2.1 test files, keep only 3.5
git push -u origin feature/algo-3-5-red
```

**Recommendation:** Option B preserves RED-phase TDD work for review/reference.

---

## Estimation

### Time per Algorithm (Based on Algorithm 1.4)
- **GREEN Phase Implementation:** 2-4 hours (depends on complexity)
- **KeyError/Bug Fixes:** 0.5-1 hour (if tests expose issues)
- **Quality Gates:** 0.5 hour (mypy, ruff, completeness check)
- **Manifest + Commit:** 0.5 hour
- **PR + Review:** 1-2 hours

**Total per algorithm:** 4-8 hours
**Total for 3 algorithms:** 12-24 hours

### Complexity Assessment
| Algorithm | Complexity | Estimated Time | Notes |
|-----------|-----------|----------------|-------|
| 1.1 (Role Composition) | MEDIUM | 5-7 hours | 12 test classes, role graph analysis |
| 2.1 (Permission vs. Usage) | HIGH | 7-9 hours | 1021 lines tests, multi-dimensional analysis |
| 3.5 (Orphaned Accounts) | LOW-MEDIUM | 4-6 hours | 8 scenarios, simpler logic |

**Total: 16-22 hours** for all 3 algorithms.

---

## Automated Testing

### Continuous Validation
After each algorithm merge, run full validation:

```bash
# From apps/agent/
source .venv/bin/activate

# Full suite (should increase by ~12-15 tests per algorithm)
pytest  # Expected: 187 → 199 → 214 → 227 (approx)

# All completeness checks
for algo in 1.4 2.2 2.5 3.1 3.2 3.3 3.4 4.1 4.3 4.7 5.1 5.2 1.1 2.1 3.5; do
    echo "Checking Algorithm $algo..."
    python scripts/check_algorithm_completeness.py $algo || echo "FAILED: $algo"
done

# Type safety
mypy src/

# Linting
ruff check src/ tests/
```

### Regression Protection
Before merging each PR, verify Phase 1 algorithms still pass:

```bash
pytest tests/test_algorithm_2_2.py -v  # Read-Only Detection
pytest tests/test_algorithm_2_5.py -v  # License Minority
pytest tests/test_algorithm_3_1.py -v  # SoD Conflicts
pytest tests/test_algorithm_3_2.py -v  # Anomalous Role Changes
pytest tests/test_algorithm_3_3.py -v  # Privilege Creep
pytest tests/test_algorithm_3_4.py -v  # Toxic Combinations
pytest tests/test_algorithm_4_1.py -v  # Device License
pytest tests/test_algorithm_4_3.py -v  # Cross-App Analyzer
pytest tests/test_algorithm_4_7.py -v  # New User Recommendation
pytest tests/test_algorithm_5_1.py -v  # Cost Trend Analysis
pytest tests/test_algorithm_5_2.py -v  # Security Risk Scoring
```

All should remain passing after each Phase 2 algorithm merge.

---

## Risk Mitigation

### Identified Risks
1. **Test file interpretation:** RED-phase tests may have ambiguous expectations
   - **Mitigation:** Study test fixtures, helper functions, assertion logic carefully

2. **Shared model conflicts:** Multiple algorithms might need same input schema changes
   - **Mitigation:** Check MANIFEST.md "Shared File Changes" section before implementing

3. **Performance issues:** Council found 2 CRITICAL O(N²) bugs in Algorithm 1.4
   - **Mitigation:** Avoid `iterrows()`, pre-compute expensive operations, use vectorized pandas

4. **Import organization:** Algorithm 1.4 had inconsistent absolute/relative imports
   - **Mitigation:** Use relative imports (`from ..models import ...`) in algorithm files

5. **Empty DataFrame bugs:** Algorithm 1.4 had KeyError on empty DataFrames
   - **Mitigation:** Always specify column names when creating empty DataFrames

### Code Review Checklist (Self-Review)
Before committing:
- [ ] No `iterrows()` in hot paths (use vectorized operations)
- [ ] Empty DataFrame constructors have explicit `columns=` parameter
- [ ] Relative imports used (`from ..models import`)
- [ ] Type hints on all function signatures
- [ ] Docstrings reference specification section
- [ ] Tests pass without warnings
- [ ] Mypy clean (no `type: ignore` added)
- [ ] Ruff clean (no auto-fix required)

---

## Resources

### Reference Implementations
- **Algorithm 2.2** (`algorithm_2_2_readonly_detector.py`): Good example of Phase 1 structure
- **Algorithm 1.4** (`algorithm_1_4_component_removal.py`): First Phase 2 algorithm (current branch)

### Specification Docs
- `Requirements/06-Algorithms-Decision-Logic.md`: Core algorithms (1.1-4.7)
- `Requirements/07-Advanced-Algorithms.md`: Advanced algorithms (3.5, 3.9, etc.)
- `Requirements/08-Algorithm-Review-Summary.md`: All 34 algorithms summary

### Utilities
- `src/utils/pricing.py`: Canonical license price lookup (use this, don't hardcode)
- `scripts/check_algorithm_completeness.py`: 5-checkbox validation

### Test Data Patterns
- Study `tests/fixtures/` for existing fixture patterns
- Use helper functions like `_build_user_activity()`, `_build_security_config()`
- Empty data must include column names: `pd.DataFrame(columns=[...])`

---

## Success Criteria

### Phase 2 Complete When:
- [x] Algorithm 1.4 merged to main, Gate 2 passed
- [ ] Algorithm 1.1 merged to main, Gate 2 passed
- [ ] Algorithm 2.1 merged to main, Gate 2 passed
- [ ] Algorithm 3.5 merged to main, Gate 2 passed
- [ ] Full test suite: ~227 tests passing (175 Phase 1 + 52 Phase 2)
- [ ] All 4 algorithms show 5/5 on completeness check
- [ ] No mypy errors across entire `src/` directory
- [ ] No ruff issues across `src/` and `tests/`
- [ ] README.md updated with Phase 2 completion status

### Post-Phase 2
After all 4 algorithms (1.1, 1.4, 2.1, 3.5) are complete:
- Update `README.md` Phase 2 section: 4/23 algorithms complete
- Tag release: `v0.2.0-phase2-milestone1`
- Plan next batch: Select next 3-4 algorithms from remaining 19

---

**Last Updated:** 2026-02-06
**Status:** Ready to proceed with Algorithm 1.1 after Algorithm 1.4 PR merge
