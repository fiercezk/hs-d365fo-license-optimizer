AI-powered license optimization agent for Microsoft Dynamics 365 Finance & Operations. Analyzes security configuration, user activity telemetry, and role assignments to detect over-licensed users and security risks. Target: 15-25% annual license cost savings.

---

# Project Structure

```
D365FOLicenseAgent-v1/
├── Requirements/              # 18 specification docs (3000+ pages)
│   ├── 00-Index.md           # Start here for overview
│   ├── 06-Algorithms-Decision-Logic.md
│   ├── 07-Advanced-Algorithms.md
│   └── 18-Tech-Stack-Recommendation.md
│
├── apps/agent/               # Python algorithm engine (PRIMARY WORKSPACE)
│   ├── src/
│   │   ├── algorithms/      # Algorithm implementations (2.2, 2.5, 3.1, etc.)
│   │   ├── models/          # Pydantic schemas (input_schemas.py, output_schemas.py)
│   │   └── services/        # Data access layer (future: OData, App Insights)
│   ├── tests/
│   │   ├── fixtures/        # Test data (CSV/JSON) matching D365 FO structure
│   │   └── test_*.py        # Pytest test modules
│   └── pyproject.toml       # Dependencies: pandas, numpy, pydantic, pytest
│
├── data/config/
│   └── pricing.json         # License pricing (customer-overridable)
│
└── README.md                # Quick start guide
```

---

# Development Approach: Test-Driven Development (TDD)

**ALL code changes MUST follow TDD workflow:**

1. **Write test FIRST** - Define expected behavior in pytest before implementation
2. **Implement SECOND** - Write minimum code to pass the test
3. **Refactor THIRD** - Clean up while keeping tests green

**DO NOT:**
- Write implementation code before tests exist
- Skip tests for "simple" functions (no exceptions)
- Commit code with failing tests

**Example TDD workflow:**
```bash
# 1. Write test first
vim tests/test_algorithm_2_2.py

# 2. Run test (expect failure)
pytest tests/test_algorithm_2_2.py::test_readonly_user_downgrade -v

# 3. Implement algorithm
vim src/algorithms/algorithm_2_2_readonly_detector.py

# 4. Run test until passing
pytest tests/test_algorithm_2_2.py::test_readonly_user_downgrade -v

# 5. Refactor if needed, verify tests still pass
```

---

# Code Style

**Line Length:** 100 characters (configured in pyproject.toml)

**Formatter:** Black (auto-formats on save)
```bash
black src/ tests/
```

**Linter:** Ruff (replaces flake8, isort, pylint)
```bash
ruff check src/ tests/
ruff check --fix src/ tests/  # Auto-fix safe issues
```

**Type Hints:** MANDATORY for all function signatures
```python
# CORRECT
def calculate_savings(current_cost: float, recommended_cost: float) -> float:
    return current_cost - recommended_cost

# INCORRECT - DO NOT COMMIT
def calculate_savings(current_cost, recommended_cost):
    return current_cost - recommended_cost
```

**Docstrings:** Required for public functions, classes, modules
- Use Google-style docstrings
- Include examples for complex logic
- Reference requirement doc sections (e.g., "See Requirements/06 Algorithm 2.2")

**Pydantic Models:** Use for ALL data contracts (input/output)
- Prefer `Field(description=...)` over comments
- Add validators for business rules
- Use Enums for fixed value sets

---

# Key Commands

**Run single test** (PREFERRED for performance):
```bash
pytest tests/test_algorithm_2_2.py::test_readonly_user_downgrade -v
```

**Run test file:**
```bash
pytest tests/test_algorithm_2_2.py -v
```

**Run all tests** (only when necessary):
```bash
pytest
```

**Type checking** (MUST run after code changes):
```bash
mypy src/
```

**Format code:**
```bash
black src/ tests/
```

**Lint:**
```bash
ruff check src/ tests/
```

**Install dependencies:**
```bash
pip install -e ".[dev]"
```

---

# Workflow

**After making code changes:**
1. Run affected tests: `pytest tests/test_<module>.py -v`
2. Type check: `mypy src/`
3. Format: `black src/ tests/`
4. Lint: `ruff check src/ tests/`

**Performance optimization:**
- Run SINGLE tests during development, not full suite
- Use `pytest -k <pattern>` to filter tests
- Full suite runs in CI/CD only

**Before committing:**
```bash
# Full validation
pytest && mypy src/ && ruff check src/ tests/
```

---

# Environment

**Python Version:** 3.11+ (tested with 3.13)

**Setup:**
```bash
cd apps/agent
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

**Required packages:**
- pandas, numpy - Data processing
- scipy - Statistical functions
- networkx - Graph algorithms (SoD conflict detection)
- pydantic - Type-safe data models
- pytest - Testing framework

**Optional (Phase 2):**
- Azure SDK packages (deployment only)
- Redis client (caching, not needed Phase 1)

---

# Critical Context

**Data Sources** (see Requirements/00-Index.md):
1. Security Configuration (D365 FO) - Role → Menu Item → License mapping
2. User-Role Assignments (D365 FO) - User → Role mapping
3. User Activity Telemetry (Azure App Insights) - Read/Write operation tracking
4. License Assignments (D365 FO Admin) - Current license per user

**Pending Validations:**
- `TEAM_MEMBERS_ELIGIBLE_FORMS` table: Form eligibility for Team Members license (UNVALIDATED - blocks Algorithm 2.2 production use)
- `OPERATIONS_ACTIVITY_ELIGIBLE_FORMS` table: Similar validation needed

**DO NOT assume form eligibility without validation.** Use test fixtures with known eligibility status during development.

**License Pricing** (data/config/pricing.json):
- Team Members: $60/month
- Operations: $90/month
- Finance/SCM/Commerce: $180/month each
- Device License: $80/device/month

Customer can override prices. DO NOT hardcode pricing in algorithms.

**Phase 1 Algorithms** (11 of 34 total):
- 2.2: Read-Only User Detection (highest priority)
- 2.5: License Minority Detection
- 3.1: Segregation of Duties (SoD) Conflicts
- 3.2: Redundant Role Detection
- 3.3: Unused License Detection
- 3.4: Seasonal Pattern Detection
- 4.1: Device License Opportunity
- 4.3: License Reduction Prediction
- 4.7: New User License Recommendation
- 5.1: License Cost Trend Analysis
- 5.2: Security Risk Scoring

**Key Principle:** Algorithms are DETERMINISTIC. LLM (GPT-4o) generates explanations only, never makes license decisions.

---

# Algorithm Implementation Pattern

**Standard algorithm structure:**
```python
# src/algorithms/algorithm_X_Y_<name>.py

from typing import List
from pydantic import BaseModel
from ..models.input_schemas import UserActivityRecord, SecurityConfigRecord
from ..models.output_schemas import LicenseRecommendation

def detect_<behavior>(
    user_id: str,
    activity_log: List[UserActivityRecord],
    security_config: List[SecurityConfigRecord],
    **params
) -> LicenseRecommendation:
    """Algorithm X.Y: <Name>.

    See Requirements/06 (or 07) for specification.

    Args:
        user_id: Target user identifier
        activity_log: User activity telemetry (read/write operations)
        security_config: Security role configuration
        **params: Algorithm-specific parameters

    Returns:
        LicenseRecommendation with action, confidence, savings
    """
    # Implementation following pseudocode in Requirements/
    pass
```

**Test structure:**
```python
# tests/test_algorithm_X_Y.py

import pytest
from src.algorithms.algorithm_X_Y_<name> import detect_<behavior>

def test_obvious_case_scenario():
    """Test Algorithm X.Y with clear optimization opportunity."""
    # Load test fixture
    # Run algorithm
    # Assert expected recommendation
    pass

def test_edge_case_scenario():
    """Test Algorithm X.Y boundary conditions."""
    pass

def test_no_action_needed_scenario():
    """Test Algorithm X.Y when current state is optimal."""
    pass
```

---

# References

- **Requirements:** `/Requirements/` (start with 00-Index.md)
- **Tech Stack:** `/Requirements/18-Tech-Stack-Recommendation.md`
- **Process Flows:** `/Requirements/17-Agent-Process-Flow.md`
- **Test Fixtures:** `apps/agent/tests/fixtures/README.md`

---

**Last Updated:** 2026-02-06 (Day 0 - Development environment ready)
