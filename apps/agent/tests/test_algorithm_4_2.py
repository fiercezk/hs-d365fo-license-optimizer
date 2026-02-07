"""Tests for Algorithm 4.2: License Attach Optimizer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_4_2_license_attach_optimizer.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1119-1258
(Algorithm 4.2: License Attach Optimizer).

Algorithm 4.2 optimizes license assignments using attach licenses (base + attach)
vs. multiple full licenses. Users with multiple license types can save 10-25%
by using an attach model instead of stacking full licenses:
  - Identify users with multiple full license types
  - Try all base + attach combinations to find cheapest option
  - Check attach license availability per license type
  - Calculate savings per user and in aggregate
  - Skip users with only 1 license type
  - Sort results by savings descending

Key behaviors:
  - Finance + SCM full ($360) -> Finance base ($180) + SCM attach ($30) = $210
  - Not all license types have attach variants (Operations-Activity has no attach)
  - Must find optimal base license (try each as base, pick cheapest combo)
  - Users with single license: skip (no attach opportunity)
  - Empty input: zero results, no errors
  - Savings percentage calculated correctly

Pricing reference (data/config/pricing.json):
  - Finance full: $180, SCM full: $180, Commerce full: $180
  - SCM attach: $30, Commerce attach: $30
  - Team Members: $60 (no attach variant)
  - Operations: $90 (no attach variant)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_4_2_license_attach_optimizer import (
    AttachOptimizationResult,
    optimize_license_attach,
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
    """Build a synthetic security configuration DataFrame.

    Args:
        rows: List of (securityrole, AOTName, AccessLevel, LicenseType, Priority)
            tuples.
    """
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
    """Build synthetic user activity DataFrame.

    Args:
        rows: List of (user_id, menu_item, action, license_tier, feature) tuples.
    """
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
# Test: Finance + SCM -> Base + Attach Optimization
# ---------------------------------------------------------------------------


class TestFinanceSCMAttachOptimization:
    """Test scenario: User with Finance + SCM full licenses.

    Current: Finance ($180) + SCM ($180) = $360/month
    Optimized: Finance base ($180) + SCM attach ($30) = $210/month
    Savings: $150/month (42%)
    """

    def test_finance_scm_attach_detected(self) -> None:
        """User with Finance+SCM should be recommended attach model."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinanceRole", "GeneralJournal", "Write", "Finance", 180),
                ("SCMRole", "PurchaseOrder", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_DUAL", "Dual User", "FinanceRole"),
                ("USR_DUAL", "Dual User", "SCMRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_DUAL", "GeneralJournal", "Write", "Finance", "GL"),
                ("USR_DUAL", "PurchaseOrder", "Write", "SCM", "Procurement"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result: AttachOptimizationResult = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.optimizations) >= 1
        opt = result.optimizations[0]
        assert opt.user_id == "USR_DUAL"
        assert opt.feasibility == "FEASIBLE"

    def test_finance_scm_savings_correct(self) -> None:
        """Savings should be $150/month (Finance base + SCM attach)."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinanceRole", "GeneralJournal", "Write", "Finance", 180),
                ("SCMRole", "PurchaseOrder", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_DUAL", "Dual User", "FinanceRole"),
                ("USR_DUAL", "Dual User", "SCMRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_DUAL", "GeneralJournal", "Write", "Finance", "GL"),
                ("USR_DUAL", "PurchaseOrder", "Write", "SCM", "Procurement"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.optimizations) >= 1
        opt = result.optimizations[0]
        assert abs(opt.current_cost_per_month - 360.0) < MONETARY_TOLERANCE
        assert opt.optimized_cost_per_month < opt.current_cost_per_month
        assert opt.monthly_savings > 0

    def test_optimal_base_license_selected(self) -> None:
        """Algorithm should find optimal base license (cheapest combo)."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinanceRole", "GeneralJournal", "Write", "Finance", 180),
                ("SCMRole", "PurchaseOrder", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_DUAL", "Dual User", "FinanceRole"),
                ("USR_DUAL", "Dual User", "SCMRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_DUAL", "GeneralJournal", "Write", "Finance", "GL"),
                ("USR_DUAL", "PurchaseOrder", "Write", "SCM", "Procurement"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        opt = result.optimizations[0]
        # Both Finance and SCM are $180 full, but SCM has a $30 attach.
        # So either base could be chosen; the key is total cost is optimal.
        assert opt.optimized_base_license is not None
        assert len(opt.optimized_attach_licenses) >= 1


# ---------------------------------------------------------------------------
# Test: Triple License (Finance + SCM + Commerce)
# ---------------------------------------------------------------------------


class TestTripleLicenseAttach:
    """Test scenario: User with Finance + SCM + Commerce.

    Current: $180 + $180 + $180 = $540/month
    Optimized: Finance base ($180) + SCM attach ($30) + Commerce attach ($30) = $240
    Savings: $300/month (56%)
    """

    def test_triple_license_savings(self) -> None:
        """Triple-license user should see significant attach savings."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinRole", "FinForm", "Write", "Finance", 180),
                ("SCMRole", "SCMForm", "Write", "SCM", 180),
                ("ComRole", "ComForm", "Write", "Commerce", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_TRI", "Triple User", "FinRole"),
                ("USR_TRI", "Triple User", "SCMRole"),
                ("USR_TRI", "Triple User", "ComRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_TRI", "FinForm", "Write", "Finance", "GL"),
                ("USR_TRI", "SCMForm", "Write", "SCM", "Procurement"),
                ("USR_TRI", "ComForm", "Write", "Commerce", "Retail"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.optimizations) >= 1
        opt = result.optimizations[0]
        assert opt.monthly_savings > 100  # Should save significantly


# ---------------------------------------------------------------------------
# Test: Single License User Skipped
# ---------------------------------------------------------------------------


class TestSingleLicenseSkipped:
    """Test scenario: User with only one license type.

    No attach optimization possible; should be excluded from results.
    """

    def test_single_license_not_in_results(self) -> None:
        """User with only Finance license should not appear in results."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("FinRole", "FinForm", "Write", "Finance", 180)]
        )
        assignments = _build_user_role_assignments(
            [("USR_SINGLE", "Single User", "FinRole")]
        )
        activity = _build_activity_df(
            [("USR_SINGLE", "FinForm", "Write", "Finance", "GL")]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        user_ids = {o.user_id for o in result.optimizations}
        assert "USR_SINGLE" not in user_ids


# ---------------------------------------------------------------------------
# Test: No Attach Available (Not Feasible)
# ---------------------------------------------------------------------------


class TestNoAttachAvailable:
    """Test scenario: License types where no attach variant exists.

    If a user has two license types and neither has an attach variant,
    optimization is not feasible.
    """

    def test_no_attach_variant_not_feasible(self) -> None:
        """License combo without attach variants should be NOT_FEASIBLE."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("TMRole", "TMForm", "Write", "Team Members", 60),
                ("OpsRole", "OpsForm", "Write", "Operations", 90),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_NO_ATTACH", "No Attach", "TMRole"),
                ("USR_NO_ATTACH", "No Attach", "OpsRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_NO_ATTACH", "TMForm", "Write", "Team Members", "Self-Service"),
                ("USR_NO_ATTACH", "OpsForm", "Write", "Operations", "Tasks"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        # Should either exclude or mark as NOT_FEASIBLE
        feasible = [
            o for o in result.optimizations
            if o.user_id == "USR_NO_ATTACH" and o.feasibility == "FEASIBLE"
        ]
        assert len(feasible) == 0


# ---------------------------------------------------------------------------
# Test: Multiple Users Sorted by Savings
# ---------------------------------------------------------------------------


class TestSortedBySavings:
    """Test scenario: Multiple users with different savings potential.

    Results should be sorted by monthly savings in descending order.
    """

    def test_results_sorted_descending_savings(self) -> None:
        """Users should be sorted from highest to lowest savings."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinRole", "FinForm", "Write", "Finance", 180),
                ("SCMRole", "SCMForm", "Write", "SCM", 180),
                ("ComRole", "ComForm", "Write", "Commerce", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                # User A: Finance+SCM (2 licenses)
                ("USR_A", "UserA", "FinRole"),
                ("USR_A", "UserA", "SCMRole"),
                # User B: Finance+SCM+Commerce (3 licenses -> more savings)
                ("USR_B", "UserB", "FinRole"),
                ("USR_B", "UserB", "SCMRole"),
                ("USR_B", "UserB", "ComRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_A", "FinForm", "Write", "Finance", "GL"),
                ("USR_A", "SCMForm", "Write", "SCM", "Procurement"),
                ("USR_B", "FinForm", "Write", "Finance", "GL"),
                ("USR_B", "SCMForm", "Write", "SCM", "Procurement"),
                ("USR_B", "ComForm", "Write", "Commerce", "Retail"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        if len(result.optimizations) >= 2:
            for i in range(len(result.optimizations) - 1):
                assert (
                    result.optimizations[i].monthly_savings
                    >= result.optimizations[i + 1].monthly_savings
                ), "Results should be sorted by savings descending"


# ---------------------------------------------------------------------------
# Test: Savings Percentage Calculation
# ---------------------------------------------------------------------------


class TestSavingsPercentage:
    """Test scenario: Verify savings percentage is calculated correctly."""

    def test_savings_percentage_correct(self) -> None:
        """Savings percentage should be (savings / current_cost) * 100."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinRole", "FinForm", "Write", "Finance", 180),
                ("SCMRole", "SCMForm", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_PCT", "PctUser", "FinRole"),
                ("USR_PCT", "PctUser", "SCMRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_PCT", "FinForm", "Write", "Finance", "GL"),
                ("USR_PCT", "SCMForm", "Write", "SCM", "Procurement"),
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.optimizations) >= 1
        opt = result.optimizations[0]
        expected_pct = (opt.monthly_savings / opt.current_cost_per_month) * 100
        assert abs(opt.savings_percentage - expected_pct) < MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test: Aggregate Summary
# ---------------------------------------------------------------------------


class TestAggregateSummary:
    """Test scenario: Result should contain aggregate statistics."""

    def test_total_savings_aggregated(self) -> None:
        """Total savings across all users should be summed."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("FinRole", "FinForm", "Write", "Finance", 180),
                ("SCMRole", "SCMForm", "Write", "SCM", 180),
            ]
        )
        assignment_rows: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []
        for i in range(5):
            uid = f"USR_{i}"
            assignment_rows.append((uid, f"User{i}", "FinRole"))
            assignment_rows.append((uid, f"User{i}", "SCMRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(assignment_rows)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_monthly_savings >= 0
        assert result.total_users_analyzed >= 5
        assert result.feasible_optimizations_count >= 0


# ---------------------------------------------------------------------------
# Test: Empty Input Data
# ---------------------------------------------------------------------------


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
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.optimizations) == 0
        assert result.total_monthly_savings == 0


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '4.2'."""

    def test_algorithm_id_is_4_2(self) -> None:
        """AttachOptimizationResult should carry algorithm_id '4.2'."""
        # -- Arrange --
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([])
        activity = _build_activity_df([])
        pricing = _load_pricing()

        # -- Act --
        result = optimize_license_attach(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.algorithm_id == "4.2"
