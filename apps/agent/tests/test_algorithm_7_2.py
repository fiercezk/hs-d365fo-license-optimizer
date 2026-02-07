"""Tests for Algorithm 7.2: Cost Allocation Engine.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_7_2_cost_allocation_engine.py is implemented.

Specification: Requirements/08-Algorithm-Review-Summary.md
(Algorithm 7.2: Cost Allocation Engine, Phase 2, Medium complexity).
Additional context: Requirements/03-User-Role-Assignment-Data.md (Cost Allocation use case).

Algorithm 7.2 allocates license costs across departments, cost centers, or
business units for accurate financial reporting and chargebacks:
  - Map each user to their department/cost center
  - Determine each user's license cost (from pricing config)
  - Aggregate costs per department
  - Handle users with multiple departments (split proportionally)
  - Handle users with no department (allocate to 'Unassigned')
  - Calculate per-department totals, percentages, and per-user averages
  - Generate cost allocation report sorted by total cost descending
  - Support configurable allocation method (headcount, usage-based, hybrid)

Key behaviors:
  - Simple case: User in dept A with Finance license -> $180 to dept A
  - Multi-dept user: Split cost proportionally (e.g., 60% Dept A, 40% Dept B)
  - No department: Allocate to 'Unassigned' bucket
  - All license types supported (Finance, SCM, Commerce, TM, Ops, Device)
  - Percentages across all departments should sum to 100%
  - Empty input: zero allocations, no errors
  - Support month-over-month cost allocation comparison
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_7_2_cost_allocation_engine import (
    CostAllocation,
    CostAllocationAnalysis,
    allocate_license_costs,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"
MONETARY_TOLERANCE: float = 0.01
PERCENTAGE_TOLERANCE: float = 0.1

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON."""
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_user_license_assignments(
    rows: list[tuple[str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic user-license-department DataFrame.

    Args:
        rows: List of (user_id, user_name, department, license_type) tuples.
    """
    records: list[dict[str, str]] = []
    for uid, name, dept, license_type in rows:
        records.append(
            {
                "user_id": uid,
                "user_name": name,
                "department": dept,
                "license_type": license_type,
                "status": "Active",
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Simple Single-Department Allocation
# ---------------------------------------------------------------------------


class TestSimpleSingleDepartment:
    """Test scenario: All users belong to one department.

    3 users in Finance dept with Finance licenses = $540/month to Finance dept.
    """

    def test_single_department_total_correct(self) -> None:
        """All costs should be allocated to the single department."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_A", "Alice", "Finance", "Finance"),
                ("USR_B", "Bob", "Finance", "Finance"),
                ("USR_C", "Charlie", "Finance", "Finance"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result: CostAllocationAnalysis = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.allocations) >= 1
        finance_dept = next(
            (a for a in result.allocations if a.department == "Finance"),
            None,
        )
        assert finance_dept is not None
        expected_cost = 3 * 180.0
        assert abs(finance_dept.total_monthly_cost - expected_cost) < MONETARY_TOLERANCE
        assert finance_dept.user_count == 3


# ---------------------------------------------------------------------------
# Test: Multiple Departments
# ---------------------------------------------------------------------------


class TestMultipleDepartments:
    """Test scenario: Users across multiple departments.

    Finance dept: 2 users @ $180 = $360
    IT dept: 1 user @ $60 (Team Members)
    """

    def test_multiple_departments_allocated(self) -> None:
        """Costs should be allocated per department."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_A", "Alice", "Finance", "Finance"),
                ("USR_B", "Bob", "Finance", "SCM"),
                ("USR_C", "Charlie", "IT", "Team Members"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        dept_names = {a.department for a in result.allocations}
        assert "Finance" in dept_names
        assert "IT" in dept_names

    def test_department_percentage_calculation(self) -> None:
        """Each department's percentage should be cost / total * 100."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_A", "Alice", "Finance", "Finance"),
                ("USR_B", "Bob", "IT", "Finance"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        for alloc in result.allocations:
            expected_pct = (alloc.total_monthly_cost / result.total_monthly_cost) * 100
            assert abs(alloc.cost_percentage - expected_pct) < PERCENTAGE_TOLERANCE


# ---------------------------------------------------------------------------
# Test: Percentages Sum to 100%
# ---------------------------------------------------------------------------


class TestPercentagesSumTo100:
    """Test scenario: All department percentages must sum to 100%."""

    def test_percentages_sum(self) -> None:
        """Cost percentages across all departments should sum to 100%."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_A", "Alice", "Finance", "Finance"),
                ("USR_B", "Bob", "IT", "Team Members"),
                ("USR_C", "Charlie", "Operations", "SCM"),
                ("USR_D", "Diana", "HR", "Team Members"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        total_pct = sum(a.cost_percentage for a in result.allocations)
        assert abs(total_pct - 100.0) < PERCENTAGE_TOLERANCE


# ---------------------------------------------------------------------------
# Test: No Department Assigned (Unassigned Bucket)
# ---------------------------------------------------------------------------


class TestNoDepartmentUnassigned:
    """Test scenario: User with no department.

    Should be allocated to 'Unassigned' bucket.
    """

    def test_no_department_goes_to_unassigned(self) -> None:
        """User without department should appear in 'Unassigned'."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_A", "Alice", "Finance", "Finance"),
                ("USR_NONE", "NoDepart", "", "SCM"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        unassigned = next(
            (a for a in result.allocations if a.department == "Unassigned"),
            None,
        )
        assert unassigned is not None
        assert unassigned.user_count >= 1

    def test_null_department_goes_to_unassigned(self) -> None:
        """User with null/NaN department should go to 'Unassigned'."""
        # -- Arrange --
        df = pd.DataFrame(
            [
                {
                    "user_id": "USR_NULL",
                    "user_name": "NullDept",
                    "department": None,
                    "license_type": "Finance",
                    "status": "Active",
                }
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=df,
            pricing_config=pricing,
        )

        # -- Assert --
        unassigned = next(
            (a for a in result.allocations if a.department == "Unassigned"),
            None,
        )
        assert unassigned is not None


# ---------------------------------------------------------------------------
# Test: Per-User Average Cost
# ---------------------------------------------------------------------------


class TestPerUserAverageCost:
    """Test scenario: Average cost per user per department."""

    def test_average_cost_per_user(self) -> None:
        """Average cost = total_cost / user_count."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_A", "Alice", "Finance", "Finance"),    # $180
                ("USR_B", "Bob", "Finance", "Team Members"),  # $60
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        finance_dept = next(
            (a for a in result.allocations if a.department == "Finance"),
            None,
        )
        assert finance_dept is not None
        expected_avg = (180.0 + 60.0) / 2
        assert abs(finance_dept.average_cost_per_user - expected_avg) < MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test: License Type Breakdown Per Department
# ---------------------------------------------------------------------------


class TestLicenseBreakdownPerDept:
    """Test scenario: Breakdown of license types within a department."""

    def test_license_type_breakdown(self) -> None:
        """Each department should show count/cost per license type."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_A", "Alice", "Finance", "Finance"),
                ("USR_B", "Bob", "Finance", "Finance"),
                ("USR_C", "Charlie", "Finance", "Team Members"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        finance_dept = next(
            (a for a in result.allocations if a.department == "Finance"),
            None,
        )
        assert finance_dept is not None
        assert finance_dept.license_breakdown is not None
        assert len(finance_dept.license_breakdown) >= 2


# ---------------------------------------------------------------------------
# Test: All License Types Supported
# ---------------------------------------------------------------------------


class TestAllLicenseTypesSupported:
    """Test scenario: Various license types are correctly priced."""

    def test_different_license_types_priced(self) -> None:
        """Finance, SCM, Commerce, Team Members should have correct prices."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_FIN", "FinUser", "Dept_A", "Finance"),       # $180
                ("USR_SCM", "SCMUser", "Dept_B", "SCM"),           # $180
                ("USR_COM", "ComUser", "Dept_C", "Commerce"),       # $180
                ("USR_TM", "TMUser", "Dept_D", "Team Members"),     # $60
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        total = sum(a.total_monthly_cost for a in result.allocations)
        expected = 180.0 + 180.0 + 180.0 + 60.0
        assert abs(total - expected) < MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test: Sorted by Total Cost Descending
# ---------------------------------------------------------------------------


class TestSortedByTotalCost:
    """Test scenario: Results sorted by total cost (highest first)."""

    def test_highest_cost_department_first(self) -> None:
        """Department with highest cost should appear first."""
        # -- Arrange --
        rows = []
        # Big dept: 10 Finance users
        for i in range(10):
            rows.append((f"USR_BIG_{i}", f"BigUser{i}", "BigDept", "Finance"))
        # Small dept: 1 TM user
        rows.append(("USR_SMALL", "SmallUser", "SmallDept", "Team Members"))

        users = _build_user_license_assignments(rows)
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        if len(result.allocations) >= 2:
            assert (
                result.allocations[0].total_monthly_cost
                >= result.allocations[1].total_monthly_cost
            )


# ---------------------------------------------------------------------------
# Test: Total Cost Aggregation
# ---------------------------------------------------------------------------


class TestTotalCostAggregation:
    """Test scenario: Result should include total cost across all departments."""

    def test_total_monthly_cost(self) -> None:
        """total_monthly_cost should sum all department costs."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [
                ("USR_A", "Alice", "Dept_A", "Finance"),
                ("USR_B", "Bob", "Dept_B", "SCM"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        dept_sum = sum(a.total_monthly_cost for a in result.allocations)
        assert abs(result.total_monthly_cost - dept_sum) < MONETARY_TOLERANCE

    def test_total_annual_cost(self) -> None:
        """total_annual_cost should be total_monthly * 12."""
        # -- Arrange --
        users = _build_user_license_assignments(
            [("USR_A", "Alice", "Dept_A", "Finance")]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        expected_annual = result.total_monthly_cost * 12
        assert abs(result.total_annual_cost - expected_annual) < MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test: Empty Input
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input DataFrame."""

    def test_empty_data_returns_empty(self) -> None:
        """Empty input should produce zero allocations without errors."""
        # -- Arrange --
        users = pd.DataFrame(
            columns=[
                "user_id", "user_name", "department",
                "license_type", "status",
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.allocations) == 0
        assert result.total_monthly_cost == 0


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '7.2'."""

    def test_algorithm_id_is_7_2(self) -> None:
        """CostAllocationAnalysis should carry algorithm_id '7.2'."""
        # -- Arrange --
        users = pd.DataFrame(
            columns=[
                "user_id", "user_name", "department",
                "license_type", "status",
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = allocate_license_costs(
            user_license_assignments=users,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.algorithm_id == "7.2"
