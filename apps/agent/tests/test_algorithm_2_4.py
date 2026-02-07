"""Tests for Algorithm 2.4: Multi-Role Optimization.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_2_4_multi_role_optimizer.py is implemented.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 833-959.

Algorithm 2.4 analyzes users with multiple roles to identify optimization
opportunities through:
  - Unused role detection (roles with 0% usage in 90 days)
  - License downgrade based on actual usage vs. theoretical required license
  - Role consolidation when similar roles overlap
  - Cost impact analysis for each optimization option

Key behaviors:
  - Skip users with only 1 role (not multi-role)
  - Calculate usage percentage per role (accessed items / total items)
  - Identify unused roles (0% usage) for removal
  - Determine required license from actual menu item usage
  - Recommend license downgrade when actual < theoretical license
  - Estimate savings from unused role removal + license downgrade
  - Handle edge cases: single-role user, all roles unused, no activity
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_2_4_multi_role_optimizer import (
    MultiRoleOptimization,
    optimize_multi_role_user,
    optimize_multi_role_users_batch,
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
    """Build synthetic user-role assignment DataFrame.

    Args:
        assignments: List of (user_id, user_name, role_name) tuples.
    """
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
# Test: Single Role User -- Skip
# ---------------------------------------------------------------------------


class TestSingleRoleUserSkipped:
    """Test scenario: User with only 1 role assigned.

    Algorithm should return isMultiRole=False for single-role users.
    """

    def test_single_role_not_multi_role(self) -> None:
        """User with 1 role should not be analyzed for multi-role optimization."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("AccountantRole", "FinForm", "Write", "Finance", 180)]
        )
        assignments = _build_user_role_assignments(
            [("USR_SINGLE", "SingleUser", "AccountantRole")]
        )
        activity = _build_activity_df(
            [("USR_SINGLE", "FinForm", "Write", "Finance", "GL")]
        )
        pricing = _load_pricing()

        # -- Act --
        result: MultiRoleOptimization = optimize_multi_role_user(
            user_id="USR_SINGLE",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.is_multi_role is False
        assert len(result.optimization_recommendations) == 0


class TestUnusedRoleDetection:
    """Test scenario: User with 3 roles, 1 completely unused.

    Setup:
    - User has Accountant (Finance), Purchasing Clerk (SCM), Budget Viewer (TM)
    - User accessed Accountant items (95% usage) and Budget Viewer items (90%)
    - User accessed 0 Purchasing Clerk items -> unused role
    - Current license: Finance + SCM = $210/month
    - After removing Purchasing Clerk: Finance only = $180/month
    - Savings: $30/month
    """

    def test_unused_role_identified(self) -> None:
        """Unused role should be detected and recommended for removal."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("Accountant", "GeneralJournal", "Write", "Finance", 180),
                ("Accountant", "BankRecon", "Write", "Finance", 180),
                ("PurchasingClerk", "PurchaseOrder", "Write", "SCM", 180),
                ("PurchasingClerk", "VendorList", "Read", "SCM", 180),
                ("BudgetViewer", "BudgetReport", "Read", "Team Members", 60),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_MULTI", "MultiUser", "Accountant"),
                ("USR_MULTI", "MultiUser", "PurchasingClerk"),
                ("USR_MULTI", "MultiUser", "BudgetViewer"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_MULTI", "GeneralJournal", "Write", "Finance", "GL"),
                ("USR_MULTI", "BankRecon", "Read", "Finance", "Cash Mgmt"),
                ("USR_MULTI", "BudgetReport", "Read", "Team Members", "Budget"),
                # Note: No PurchasingClerk activity
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_multi_role_user(
            user_id="USR_MULTI",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.is_multi_role is True
        assert result.role_count == 3
        assert len(result.unused_roles) >= 1
        assert "PurchasingClerk" in result.unused_roles

        # Should have a remove-unused-roles recommendation
        remove_rec = next(
            (r for r in result.optimization_recommendations
             if "remove" in r.option.lower() or "unused" in r.option.lower()),
            None,
        )
        assert remove_rec is not None, (
            "Expected a recommendation to remove unused roles"
        )


class TestLicenseDowngradeRecommendation:
    """Test scenario: User's actual usage requires lower license than theoretical.

    Setup:
    - User has Accountant (Finance) + Purchasing Clerk (SCM)
    - Theoretical: Finance + SCM = $210/month
    - User only accesses Finance items (no SCM activity)
    - Required based on usage: Finance = $180/month
    - Should recommend license downgrade and role removal
    """

    def test_license_downgrade_from_actual_usage(self) -> None:
        """Usage-based license should be lower than theoretical license."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("Accountant", "GeneralJournal", "Write", "Finance", 180),
                ("PurchasingClerk", "PurchaseOrder", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_DG", "DowngradeUser", "Accountant"),
                ("USR_DG", "DowngradeUser", "PurchasingClerk"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_DG", "GeneralJournal", "Write", "Finance", "GL"),
                # No PurchaseOrder activity
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_multi_role_user(
            user_id="USR_DG",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.is_multi_role is True
        assert result.required_license_based_on_usage != result.current_license
        # Required should be Finance (or lower), not Finance + SCM
        downgrade_rec = next(
            (r for r in result.optimization_recommendations
             if "downgrade" in r.option.lower() or "license" in r.option.lower()),
            None,
        )
        assert downgrade_rec is not None
        assert downgrade_rec.estimated_savings_per_month > 0


class TestAllRolesActivelyUsed:
    """Test scenario: User actively uses all assigned roles.

    When all roles are actively used, there should be no unused role
    removal recommendation. License is correctly matched.
    """

    def test_all_roles_active_no_optimization(self) -> None:
        """User who uses all roles should have minimal optimization."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RoleA", "FormA", "Write", "Finance", 180),
                ("RoleB", "FormB", "Write", "Finance", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_ALL", "ActiveUser", "RoleA"),
                ("USR_ALL", "ActiveUser", "RoleB"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_ALL", "FormA", "Write", "Finance", "GL"),
                ("USR_ALL", "FormB", "Write", "Finance", "GL"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_multi_role_user(
            user_id="USR_ALL",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.is_multi_role is True
        assert len(result.unused_roles) == 0


class TestRoleUsagePercentages:
    """Test scenario: Verify usage percentage calculation per role.

    A role with 10 menu items where user accessed 3 should show 30% usage.
    """

    def test_usage_percentage_calculated(self) -> None:
        """Role usage percentage should be accessed_items / total_items * 100."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("BigRole", f"Form_{i}", "Write", "Finance", 180)
                for i in range(10)
            ]
            + [("SmallRole", "Form_S1", "Read", "Team Members", 60)]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_PCT", "PctUser", "BigRole"),
                ("USR_PCT", "PctUser", "SmallRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_PCT", "Form_0", "Write", "Finance", "GL"),
                ("USR_PCT", "Form_1", "Write", "Finance", "GL"),
                ("USR_PCT", "Form_2", "Write", "Finance", "GL"),
                ("USR_PCT", "Form_S1", "Read", "Team Members", "Self-Service"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_multi_role_user(
            user_id="USR_PCT",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        big_role_usage = next(
            (r for r in result.role_usage if r.role_name == "BigRole"), None
        )
        assert big_role_usage is not None
        assert big_role_usage.total_menu_items == 10
        assert big_role_usage.accessed_menu_items == 3
        assert abs(big_role_usage.usage_percentage - 30.0) < 0.1

        small_role_usage = next(
            (r for r in result.role_usage if r.role_name == "SmallRole"), None
        )
        assert small_role_usage is not None
        assert small_role_usage.accessed_menu_items == 1
        assert abs(small_role_usage.usage_percentage - 100.0) < 0.1


class TestNoActivityData:
    """Test scenario: Multi-role user with zero activity data.

    All roles should show 0% usage. All roles are technically unused
    but the algorithm should handle this gracefully.
    """

    def test_no_activity_all_roles_unused(self) -> None:
        """User with no activity should have all roles flagged as unused."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RoleX", "FormX", "Write", "Finance", 180),
                ("RoleY", "FormY", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_NONE", "NoActivity", "RoleX"),
                ("USR_NONE", "NoActivity", "RoleY"),
            ]
        )
        activity = _build_activity_df([])
        pricing = _load_pricing()

        # -- Act --
        result = optimize_multi_role_user(
            user_id="USR_NONE",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.is_multi_role is True
        assert len(result.unused_roles) == 2


class TestBatchProcessingMultipleUsers:
    """Test scenario: Batch optimization for multiple multi-role users.

    Process 5 users simultaneously and verify each gets correct analysis.
    """

    def test_batch_processing(self) -> None:
        """Batch processing should return one result per multi-role user."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RoleA", "FormA", "Write", "Finance", 180),
                ("RoleB", "FormB", "Write", "SCM", 180),
                ("RoleC", "FormC", "Read", "Team Members", 60),
            ]
        )

        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        for i in range(5):
            uid = f"USR_BATCH{i}"
            assignment_rows.append((uid, f"BatchUser{i}", "RoleA"))
            assignment_rows.append((uid, f"BatchUser{i}", "RoleB"))
            # Only use RoleA items
            activity_rows.append((uid, "FormA", "Write", "Finance", "GL"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        results: list[MultiRoleOptimization] = optimize_multi_role_users_batch(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) == 5
        for result in results:
            assert result.is_multi_role is True
            assert result.role_count == 2


class TestSavingsFromRoleRemoval:
    """Test scenario: Verify savings when removing unused SCM role.

    Current: Finance + SCM license (due to 2 roles)
    After removal: Finance only
    Savings should reflect the license downgrade.
    """

    def test_savings_from_removing_unused_role(self) -> None:
        """Removing unused SCM role should produce measurable savings."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinRole", "FinForm", "Write", "Finance", 180),
                ("SCMRole", "SCMForm", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_SAV", "SavingsUser", "FinRole"),
                ("USR_SAV", "SavingsUser", "SCMRole"),
            ]
        )
        activity = _build_activity_df(
            [("USR_SAV", "FinForm", "Write", "Finance", "GL")]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_multi_role_user(
            user_id="USR_SAV",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.is_multi_role is True
        assert "SCMRole" in result.unused_roles
        # Check there is a recommendation with savings
        total_savings = sum(
            r.estimated_savings_per_month
            for r in result.optimization_recommendations
            if r.estimated_savings_per_month > 0
        )
        assert total_savings > 0, "Expected positive savings from role removal"


class TestFiveRolesThreeUnused:
    """Test scenario: User with 5 roles, 3 completely unused.

    This tests the algorithm with a higher role count and multiple
    unused roles to verify all are detected.
    """

    def test_multiple_unused_roles_detected(self) -> None:
        """All unused roles should be identified for removal."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("R1", "F1", "Write", "Finance", 180),
                ("R2", "F2", "Write", "SCM", 180),
                ("R3", "F3", "Read", "Commerce", 180),
                ("R4", "F4", "Read", "Team Members", 60),
                ("R5", "F5", "Write", "Finance", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_5R", "FiveRoleUser", "R1"),
                ("USR_5R", "FiveRoleUser", "R2"),
                ("USR_5R", "FiveRoleUser", "R3"),
                ("USR_5R", "FiveRoleUser", "R4"),
                ("USR_5R", "FiveRoleUser", "R5"),
            ]
        )
        # Only use R1 and R4
        activity = _build_activity_df(
            [
                ("USR_5R", "F1", "Write", "Finance", "GL"),
                ("USR_5R", "F4", "Read", "Team Members", "Self-Service"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_multi_role_user(
            user_id="USR_5R",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.is_multi_role is True
        assert result.role_count == 5
        assert len(result.unused_roles) == 3
        assert set(result.unused_roles) == {"R2", "R3", "R5"}


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '2.4'."""

    def test_algorithm_id_is_2_4(self) -> None:
        """MultiRoleOptimization should carry algorithm_id '2.4'."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("R1", "F1", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments(
            [("USR_META", "MetaUser", "R1")]
        )
        activity = _build_activity_df([])
        pricing = _load_pricing()

        # -- Act --
        result = optimize_multi_role_user(
            user_id="USR_META",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.algorithm_id == "2.4"
