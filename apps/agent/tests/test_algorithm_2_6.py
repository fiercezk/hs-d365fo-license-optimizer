"""Tests for Algorithm 2.6: Cross-Role License Optimization.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_2_6_cross_role_optimizer.py is implemented.

Specification: Requirements/10-Additional-Algorithms-Exploration.md
(Algorithm 2.6: Cross-Role License Optimization).

Algorithm 2.6 optimizes license assignments by analyzing combinations of roles
across the entire organization to identify systemic optimization opportunities.
Instead of optimizing users individually, it:
  - Finds common role combinations that create high license requirements
  - Analyzes actual license usage per role combination
  - Identifies users who only use a single license type within a multi-license combo
  - Recommends splitting roles, creating variants, or adding approval workflows
  - Calculates organization-wide savings from systemic changes

Key behaviors:
  - Group users by their sorted role combination
  - Skip single-role combinations (not cross-role)
  - Skip combinations with fewer than MIN_USERS_THRESHOLD (default 5)
  - Analyze license usage per user within each combination
  - Generate SPLIT_ROLES recommendations for exclusive-use segments
  - Generate CREATE_ROLE_VARIANTS recommendations when >10% savings possible
  - Generate ADD_APPROVAL_WORKFLOW for high-cost combinations
  - Sort results by potential savings descending
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_2_6_cross_role_optimizer import (
    CrossRoleOptimization,
    CrossRoleOptimizationResult,
    optimize_cross_role_licenses,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

MONETARY_TOLERANCE: float = 0.01

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON."""
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_security_config(
    rows: list[tuple[str, str, str, str, int]],
) -> pd.DataFrame:
    """Build a synthetic security configuration DataFrame."""
    records: list[dict[str, str | int | bool]] = []
    for role, aot, access, license_type, priority in rows:
        records.append(
            {
                "securityrole": role,
                "AOTName": aot,
                "AccessLevel": access,
                "LicenseType": license_type,
                "Priority": priority,
                "Entitled": 1,
                "NotEntitled": 0,
                "securitytype": "MenuItemDisplay",
            }
        )
    return pd.DataFrame(records)


def _build_user_role_assignments(
    assignments: list[tuple[str, str, str]],
) -> pd.DataFrame:
    """Build synthetic user-role assignment DataFrame."""
    records: list[dict[str, str]] = []
    for uid, name, role in assignments:
        records.append(
            {
                "user_id": uid,
                "user_name": name,
                "email": f"{uid.lower()}@example.com",
                "company": "USMF",
                "department": "Finance",
                "role_id": f"ROLE_{role.upper().replace(' ', '_')}",
                "role_name": role,
                "assigned_date": "2025-01-01",
                "status": "Active",
            }
        )
    return pd.DataFrame(records)


def _build_activity_df(
    rows: list[tuple[str, str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic user activity DataFrame."""
    records: list[dict[str, str]] = []
    for i, (uid, menu_item, action, tier, feature) in enumerate(rows):
        records.append(
            {
                "user_id": uid,
                "timestamp": f"2026-01-15 09:{i // 60:02d}:{i % 60:02d}",
                "menu_item": menu_item,
                "action": action,
                "session_id": f"sess-{i:04d}",
                "license_tier": tier,
                "feature": feature,
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Classic Finance+SCM Combination with Segments
# ---------------------------------------------------------------------------


class TestFinanceSCMCombinationWithSegments:
    """Test scenario: Accountant + Purchasing Clerk (50 users).

    Setup:
    - 35 users only use Finance features (70%)
    - 10 users only use SCM features (20%)
    - 5 users use both (10%)
    - Current: All need Finance+SCM combined ($210/month)
    - Optimization: Split into Finance-only and SCM-only roles
    """

    def test_finance_scm_split_detected(self) -> None:
        """Classic Finance+SCM combo should detect optimization opportunity."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("Accountant", "GeneralJournal", "Write", "Finance", 180),
                ("Accountant", "BankRecon", "Write", "Finance", 180),
                ("PurchClerk", "PurchaseOrder", "Write", "SCM", 180),
                ("PurchClerk", "VendorList", "Read", "SCM", 180),
            ]
        )

        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 35 Finance-only users
        for i in range(35):
            uid = f"USR_F{i:02d}"
            assignment_rows.append((uid, f"FinUser{i}", "Accountant"))
            assignment_rows.append((uid, f"FinUser{i}", "PurchClerk"))
            activity_rows.append((uid, "GeneralJournal", "Write", "Finance", "GL"))

        # 10 SCM-only users
        for i in range(10):
            uid = f"USR_S{i:02d}"
            assignment_rows.append((uid, f"SCMUser{i}", "Accountant"))
            assignment_rows.append((uid, f"SCMUser{i}", "PurchClerk"))
            activity_rows.append((uid, "PurchaseOrder", "Write", "SCM", "Procurement"))

        # 5 Mixed users
        for i in range(5):
            uid = f"USR_M{i:02d}"
            assignment_rows.append((uid, f"MixUser{i}", "Accountant"))
            assignment_rows.append((uid, f"MixUser{i}", "PurchClerk"))
            activity_rows.append((uid, "GeneralJournal", "Write", "Finance", "GL"))
            activity_rows.append((uid, "PurchaseOrder", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        results: list[CrossRoleOptimization] = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) >= 1

        # Find the Accountant+PurchClerk combination result
        combo_result = None
        for r in results:
            role_set = set(r.role_combination)
            if role_set == {"Accountant", "PurchClerk"}:
                combo_result = r
                break

        assert combo_result is not None, (
            "Expected to find Accountant+PurchClerk combination in results"
        )
        assert combo_result.user_count == 50
        assert combo_result.has_optimization_opportunity is True
        assert len(combo_result.optimization_options) > 0


class TestSingleRoleCombinationsSkipped:
    """Test scenario: Users with only 1 role should be skipped."""

    def test_single_role_users_excluded(self) -> None:
        """Single-role combinations should not appear in results."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("OnlyRole", "Form", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments(
            [(f"USR_{i}", f"User{i}", "OnlyRole") for i in range(10)]
        )
        activity = _build_activity_df(
            [(f"USR_{i}", "Form", "Read", "Finance", "GL") for i in range(10)]
        )
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        # No single-role combinations should appear
        for r in results:
            assert len(r.role_combination) >= 2, (
                "Single-role combinations should be excluded"
            )


class TestBelowMinUsersThresholdSkipped:
    """Test scenario: Role combination with fewer than 5 users (default).

    Combinations with only 3 users are not worth optimizing.
    """

    def test_small_combinations_excluded(self) -> None:
        """Combinations below min_users_threshold should not appear."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RoleA", "FormA", "Write", "Finance", 180),
                ("RoleB", "FormB", "Write", "SCM", 180),
            ]
        )
        # Only 3 users with this combination (below default threshold of 5)
        assignments = _build_user_role_assignments(
            [
                (f"USR_{i}", f"User{i}", "RoleA")
                for i in range(3)
            ]
            + [
                (f"USR_{i}", f"User{i}", "RoleB")
                for i in range(3)
            ]
        )
        activity = _build_activity_df(
            [(f"USR_{i}", "FormA", "Read", "Finance", "GL") for i in range(3)]
        )
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) == 0, (
            "Combinations with < 5 users should be excluded"
        )


class TestSameLicenseTypeCombination:
    """Test scenario: Both roles require the same license type.

    When all roles in a combination require Finance, there is no
    cross-license optimization opportunity.
    """

    def test_same_license_no_opportunity(self) -> None:
        """All-Finance combination should have no optimization opportunity."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinRoleA", "FinFormA", "Write", "Finance", 180),
                ("FinRoleB", "FinFormB", "Write", "Finance", 180),
            ]
        )
        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        for i in range(10):
            uid = f"USR_{i}"
            assignment_rows.append((uid, f"User{i}", "FinRoleA"))
            assignment_rows.append((uid, f"User{i}", "FinRoleB"))
            activity_rows.append((uid, "FinFormA", "Write", "Finance", "GL"))
            activity_rows.append((uid, "FinFormB", "Write", "Finance", "GL"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        for r in results:
            if set(r.role_combination) == {"FinRoleA", "FinRoleB"}:
                assert r.has_optimization_opportunity is False


class TestSplitRolesOptimizationType:
    """Test scenario: SPLIT_ROLES recommendation type.

    When >=3 users exclusively use a single license type,
    a SPLIT_ROLES optimization should be generated.
    """

    def test_split_roles_recommendation_generated(self) -> None:
        """Exclusive single-license segments should generate SPLIT_ROLES option."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RoleX", "FinForm", "Write", "Finance", 180),
                ("RoleY", "SCMForm", "Write", "SCM", 180),
            ]
        )

        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 5 Finance-only + 5 SCM-only
        for i in range(5):
            uid = f"USR_FO{i}"
            assignment_rows.append((uid, f"FinOnly{i}", "RoleX"))
            assignment_rows.append((uid, f"FinOnly{i}", "RoleY"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))

        for i in range(5):
            uid = f"USR_SO{i}"
            assignment_rows.append((uid, f"SCMOnly{i}", "RoleX"))
            assignment_rows.append((uid, f"SCMOnly{i}", "RoleY"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) >= 1
        combo_result = results[0]
        split_opts = [
            o for o in combo_result.optimization_options
            if o.option_type == "SPLIT_ROLES"
        ]
        assert len(split_opts) >= 1, "Expected SPLIT_ROLES optimization option"


class TestSortedBySavingsDescending:
    """Test scenario: Results should be sorted by potential savings descending.

    Multiple role combinations should appear in order of highest savings first.
    """

    def test_results_sorted_by_savings(self) -> None:
        """Results should be sorted from highest to lowest potential savings."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("SmallRoleA", "SmallFormA", "Write", "Finance", 180),
                ("SmallRoleB", "SmallFormB", "Write", "SCM", 180),
                ("BigRoleA", "BigFormA", "Write", "Finance", 180),
                ("BigRoleB", "BigFormB", "Write", "Commerce", 180),
            ]
        )

        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # Small combo: 6 users
        for i in range(6):
            uid = f"USR_SM{i}"
            assignment_rows.append((uid, f"SmUser{i}", "SmallRoleA"))
            assignment_rows.append((uid, f"SmUser{i}", "SmallRoleB"))
            activity_rows.append((uid, "SmallFormA", "Write", "Finance", "GL"))

        # Big combo: 20 users
        for i in range(20):
            uid = f"USR_BG{i}"
            assignment_rows.append((uid, f"BgUser{i}", "BigRoleA"))
            assignment_rows.append((uid, f"BgUser{i}", "BigRoleB"))
            activity_rows.append((uid, "BigFormA", "Write", "Finance", "GL"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        if len(results) >= 2:
            for i in range(len(results) - 1):
                assert results[i].potential_savings >= results[i + 1].potential_savings, (
                    f"Results not sorted by savings descending: "
                    f"index {i} has {results[i].potential_savings}, "
                    f"index {i+1} has {results[i+1].potential_savings}"
                )


class TestUsagePatternBreakdown:
    """Test scenario: Verify usage pattern analysis per combination.

    The result should break down users into:
    - uses_all_licenses: users who access all license types
    - uses_single_license: keyed by license type
    - uses_multiple_licenses: users who use some but not all
    """

    def test_usage_patterns_populated(self) -> None:
        """Usage pattern breakdown should classify all users."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RA", "FA", "Write", "Finance", 180),
                ("RB", "FB", "Write", "SCM", 180),
            ]
        )

        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 3 Finance-only
        for i in range(3):
            uid = f"USR_PF{i}"
            assignment_rows.append((uid, f"PFinUser{i}", "RA"))
            assignment_rows.append((uid, f"PFinUser{i}", "RB"))
            activity_rows.append((uid, "FA", "Write", "Finance", "GL"))

        # 2 Both-license
        for i in range(2):
            uid = f"USR_PB{i}"
            assignment_rows.append((uid, f"PBothUser{i}", "RA"))
            assignment_rows.append((uid, f"PBothUser{i}", "RB"))
            activity_rows.append((uid, "FA", "Write", "Finance", "GL"))
            activity_rows.append((uid, "FB", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) >= 1
        combo = results[0]
        assert combo.usage_patterns is not None
        assert combo.user_count == 5


class TestCustomMinUsersThreshold:
    """Test scenario: Custom min_users_threshold=3.

    With lowered threshold, smaller combinations should be analyzed.
    """

    def test_custom_threshold_includes_small_combos(self) -> None:
        """Lowered min_users_threshold should include smaller combinations."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RA", "FA", "Write", "Finance", 180),
                ("RB", "FB", "Write", "SCM", 180),
            ]
        )
        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # Only 3 users
        for i in range(3):
            uid = f"USR_{i}"
            assignment_rows.append((uid, f"User{i}", "RA"))
            assignment_rows.append((uid, f"User{i}", "RB"))
            activity_rows.append((uid, "FA", "Write", "Finance", "GL"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
            min_users_threshold=3,
        )

        # -- Assert --
        assert len(results) >= 1, (
            "With min_users_threshold=3, 3-user combo should be included"
        )


class TestEmptyInputData:
    """Test scenario: Empty input DataFrames."""

    def test_empty_data_returns_empty_results(self) -> None:
        """Empty input should produce zero results without errors."""
        # -- Arrange --
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([])
        activity = _build_activity_df([])
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert results == []


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '2.6'."""

    def test_algorithm_id_is_2_6(self) -> None:
        """Results should carry algorithm_id '2.6'."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RA", "FA", "Write", "Finance", 180),
                ("RB", "FB", "Write", "SCM", 180),
            ]
        )
        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []
        for i in range(6):
            uid = f"USR_{i}"
            assignment_rows.append((uid, f"User{i}", "RA"))
            assignment_rows.append((uid, f"User{i}", "RB"))
            activity_rows.append((uid, "FA", "Write", "Finance", "GL"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        results = optimize_cross_role_licenses(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) >= 1
        assert results[0].algorithm_id == "2.6"
