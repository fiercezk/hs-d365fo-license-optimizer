# Algorithm Implementation Manifest

**Algorithm:** X.Y - [Algorithm Name]
**Branch:** `feature/algo-X-Y`
**Developer:** [Your Name]
**Date Started:** YYYY-MM-DD
**Status:** 🔴 RED | 🟡 GREEN | 🟢 COMPLETE

---

## Scope

### Primary Deliverables
- [ ] Implementation: `src/algorithms/algorithm_X_Y_<name>.py`
- [ ] Tests: `tests/test_algorithm_X_Y.py`
- [ ] Test fixtures: `tests/fixtures/algo_X_Y/` (if needed)
- [ ] Documentation: Inline docstrings + spec reference

### Specification Reference
- Requirements doc: `Requirements/[06|07]-*.md`, lines XXX-YYY
- Algorithm category: [Cost Optimization | Security | Behavior | Role | Analytics]
- Phase: [Phase 1 | Phase 2 | Phase 3]

---

## Dependencies

### Data Models (Input)
List all input schemas from `src/models/input_schemas.py`:
- [ ] `SecurityConfigRecord`
- [ ] `UserActivityRecord`
- [ ] `UserRoleAssignmentRecord`
- [ ] `LicenseAssignmentRecord`
- [ ] [Other input models...]

### Data Models (Output)
List all output schemas from `src/models/output_schemas.py`:
- [ ] `LicenseRecommendation` (standard)
- [ ] [Custom output models if needed]

### Shared Utilities
List any shared utilities from `src/utils/`:
- [ ] `pricing.py::get_license_price()` (if pricing needed)
- [ ] [Other utilities...]

### Algorithm Dependencies
List any other algorithms this algorithm calls or depends on:
- [ ] Algorithm X.Y: [Purpose]
- [ ] [Other algorithms...]

---

## Shared File Changes

### `src/algorithms/__init__.py`
**Action:** ADD (append-only, safe for parallel development)

```python
# Add to imports section:
from .algorithm_X_Y_<name> import (
    [OutputModel],
    [function_name],
)

# Add to __all__ list:
"[OutputModel]",
"[function_name]",
```

### `src/models/input_schemas.py`
**Action:** [NONE | ADD | MODIFY]

If MODIFY or ADD, describe changes:
```python
# Example: New input schema
class NewInputSchema(BaseModel):
    field1: str
    field2: int
```

**Conflict Risk:** [LOW | MEDIUM | HIGH]
**Reason:** [Why this might conflict with parallel work]

### `src/models/output_schemas.py`
**Action:** [NONE | ADD | MODIFY]

If MODIFY or ADD, describe changes:
```python
# Example: Custom output model
class CustomOutputModel(BaseModel):
    field1: str
    field2: int
```

**Conflict Risk:** [LOW | MEDIUM | HIGH]
**Reason:** [Why this might conflict with parallel work]

### `src/utils/`
**Action:** [NONE | ADD | MODIFY]

If MODIFY or ADD, describe changes and conflict risk.

---

## Conflict Detection

### Known Parallel Branches
List other feature branches being developed in parallel:
- `feature/algo-A-B` - [Algorithm A.B Name]
- `feature/algo-C-D` - [Algorithm C.D Name]

### Potential Conflicts
Identify files that might be modified by multiple branches:

| File | This Branch | Other Branch | Conflict Risk | Mitigation |
|------|-------------|--------------|---------------|------------|
| `src/algorithms/__init__.py` | ADD exports | ADD exports | LOW | Append-only, merge sequentially |
| `src/models/input_schemas.py` | NONE | MODIFY | NONE | No conflict |
| Example | ... | ... | MEDIUM | Coordinate with other dev |

### Coordination Notes
- [ ] Reviewed MANIFEST.md files of parallel branches
- [ ] Identified shared model changes, coordinated field naming
- [ ] Scheduled merge order (if conflict risk is MEDIUM/HIGH)

---

## Implementation Checklist

### RED Phase (TDD)
- [ ] Test file created with all scenarios
- [ ] Test fixtures created (if needed)
- [ ] Tests run and fail with expected ModuleNotFoundError

### GREEN Phase (Implementation)
- [ ] Algorithm implementation file created
- [ ] All tests pass (12/12, 15/15, etc.)
- [ ] Algorithm registered in `__init__.py`

### Quality Gates
- [ ] Mypy clean (no type errors)
- [ ] Ruff clean (all linting checks pass)
- [ ] Black formatted (if applicable)

### Completeness Validation
- [ ] Run: `python scripts/check_algorithm_completeness.py X.Y`
- [ ] Result: ✓ ALL CHECKS PASSED (5/5)

---

## Test Summary

| Test Scenario | Status | Notes |
|---------------|--------|-------|
| 1. [Scenario name] | ✓ PASS | [Any notes] |
| 2. [Scenario name] | ✓ PASS | [Any notes] |
| ... | ... | ... |

**Total:** X/X tests passing

---

## Merge Strategy

### Pre-Merge Checklist (Gate 1)
- [ ] All tests pass
- [ ] Mypy clean
- [ ] Ruff clean
- [ ] Completeness script passes (5/5)
- [ ] No conflicts with main branch
- [ ] MANIFEST.md updated with final status

### Post-Merge Validation (Gate 2)
- [ ] Full test suite passes on main: `pytest`
- [ ] Integration with other Phase 2 algorithms tested
- [ ] Regression tests for Phase 1 still pass

### Merge Order
If parallel development: List merge order here based on dependency analysis.

Example:
1. `feature/algo-1-1` (no dependencies)
2. `feature/algo-1-4` (depends on 1.1)
3. This branch

---

## Notes

### Design Decisions
Document any significant design decisions made during implementation:
- [Decision 1]: Why approach A chosen over approach B
- [Decision 2]: Performance optimization rationale

### Known Limitations
List any known limitations or edge cases:
- [Limitation 1]: Description
- [Limitation 2]: Description

### Future Work
List any follow-up tasks or Phase 3 enhancements:
- [Enhancement 1]: Description
- [Enhancement 2]: Description

---

## Sign-off

**Implementation Complete:** [Date]
**Reviewed By:** [Reviewer name]
**Merged to main:** [Date]
**Status:** 🟢 COMPLETE

---

*Template version: 1.0*
*Last updated: 2026-02-06*
