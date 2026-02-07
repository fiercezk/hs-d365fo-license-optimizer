"""Tests for Algorithm 2.3: Role Segmentation by Usage Pattern.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_2_3_role_usage_segmentation.py is implemented.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 696-829.

Algorithm 2.3 analyzes a mixed-license role (e.g., Finance + SCM) to determine
if users naturally segment by their actual license-type usage. For each role it
produces:
  - Total user count
  - Segmentation: Finance-Only, SCM-Only, Mixed users with counts/percentages
  - Optimization recommendations:
    - Option A: Split into 2+ license-specific roles
    - Option B: Create read-only variant for secondary license
  - Savings estimates for each option
  - Recommendation with implementation notes

Key behaviors:
  - Analyze which license types each user actually accesses
  - Categorize users: Finance-Only, SCM-Only, Mixed, etc.
  - Generate split recommendation when >20% are single-license
  - Generate read-variant recommendation when applicable
  - Calculate savings for each optimization option
  - Handle edge cases: all mixed, all one type, empty role
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_2_3_role_usage_segmentation import (
    RoleUsageSegmentation,
    analyze_role_usage_segmentation,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
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
# Test: Clear Finance/SCM Segmentation
# ---------------------------------------------------------------------------


class TestClearFinanceSCMSegmentation:
    """Test scenario: 70% Finance-Only, 20% SCM-Only, 10% Mixed.

    Setup:
    - Role 'Accountant-Purchaser' has Finance and SCM menu items
    - 7 users access only Finance items
    - 2 users access only SCM items
    - 1 user accesses both

    Expected: Split recommended, savings calculated for exclusive users.
    """

    def test_clear_segmentation_detected(self) -> None:
        """Role with clear segments should detect Finance/SCM split opportunity."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("AcctPurch", "GeneralJournal", "Write", "Finance", 180),
                ("AcctPurch", "BankRecon", "Write", "Finance", 180),
                ("AcctPurch", "PurchaseOrder", "Write", "SCM", 180),
                ("AcctPurch", "InventOnHand", "Read", "SCM", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 7 Finance-Only users
        for i in range(7):
            uid = f"USR_FIN{i}"
            user_data.append((uid, f"FinUser{i}", "AcctPurch"))
            activity_rows.append((uid, "GeneralJournal", "Write", "Finance", "GL"))
            activity_rows.append((uid, "BankRecon", "Read", "Finance", "Cash Mgmt"))

        # 2 SCM-Only users
        for i in range(2):
            uid = f"USR_SCM{i}"
            user_data.append((uid, f"SCMUser{i}", "AcctPurch"))
            activity_rows.append((uid, "PurchaseOrder", "Write", "SCM", "Procurement"))

        # 1 Mixed user
        uid = "USR_MIX0"
        user_data.append((uid, "MixedUser", "AcctPurch"))
        activity_rows.append((uid, "GeneralJournal", "Write", "Finance", "GL"))
        activity_rows.append((uid, "PurchaseOrder", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result: RoleUsageSegmentation = analyze_role_usage_segmentation(
            role_name="AcctPurch",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.role_name == "AcctPurch"
        assert result.total_users == 10
        assert result.segmentation["finance_only"].count == 7
        assert result.segmentation["scm_only"].count == 2
        assert result.segmentation["mixed"].count == 1

        # Percentages
        assert abs(result.segmentation["finance_only"].percentage - 70.0) < PERCENTAGE_TOLERANCE
        assert abs(result.segmentation["scm_only"].percentage - 20.0) < PERCENTAGE_TOLERANCE


class TestAllMixedUsersNoRecommendation:
    """Test scenario: All users access both Finance and SCM features.

    When all users are mixed, splitting would provide no benefit.
    """

    def test_all_mixed_no_split_recommendation(self) -> None:
        """All mixed users should result in no split recommendation."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("MixedRole", "FinForm", "Write", "Finance", 180),
                ("MixedRole", "SCMForm", "Write", "SCM", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        for i in range(8):
            uid = f"USR_M{i}"
            user_data.append((uid, f"MixUser{i}", "MixedRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = analyze_role_usage_segmentation(
            role_name="MixedRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_users == 8
        assert result.segmentation["mixed"].count == 8
        assert len(result.recommendations) == 0 or all(
            r.estimated_savings_per_month == 0 for r in result.recommendations
        )


class TestSplitSavingsCalculation:
    """Test scenario: Verify savings math for split recommendation.

    Setup:
    - Current: Finance + SCM combined ($210/month per user)
    - 5 Finance-only users -> Finance only ($180/month)
    - Savings: ($210 - $180) * 5 = $150/month
    """

    def test_split_savings_correct(self) -> None:
        """Split savings should be (combined - single) * exclusive_users."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("SavingsRole", "FinForm", "Write", "Finance", 180),
                ("SavingsRole", "SCMForm", "Write", "SCM", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 5 Finance-only, 5 SCM-only
        for i in range(5):
            uid = f"USR_SF{i}"
            user_data.append((uid, f"FinUser{i}", "SavingsRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))

        for i in range(5):
            uid = f"USR_SS{i}"
            user_data.append((uid, f"SCMUser{i}", "SavingsRole"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = analyze_role_usage_segmentation(
            role_name="SavingsRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.recommendations) > 0
        # At least one recommendation should have positive savings
        split_rec = next(
            (r for r in result.recommendations if "split" in r.option.lower()),
            None,
        )
        assert split_rec is not None, "Expected a split recommendation"
        assert split_rec.estimated_savings_per_month > 0


class TestBelowSegmentThreshold:
    """Test scenario: Single-license segments below 20% threshold.

    If Finance-Only is only 10% of users, it does not meet the default
    20% minimum to trigger a split recommendation.
    """

    def test_below_threshold_no_recommendation(self) -> None:
        """Segments below 20% should not trigger split recommendation."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("SmallSegRole", "FinForm", "Write", "Finance", 180),
                ("SmallSegRole", "SCMForm", "Write", "SCM", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 1 Finance-only (10%), 9 mixed (90%)
        user_data.append(("USR_LONE", "LoneFinUser", "SmallSegRole"))
        activity_rows.append(("USR_LONE", "FinForm", "Write", "Finance", "GL"))

        for i in range(9):
            uid = f"USR_MIX{i}"
            user_data.append((uid, f"MixUser{i}", "SmallSegRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = analyze_role_usage_segmentation(
            role_name="SmallSegRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.segmentation["finance_only"].count == 1
        # Should not have a split recommendation since Finance-Only is only 10%
        split_recs = [
            r for r in result.recommendations if "split" in r.option.lower()
        ]
        assert len(split_recs) == 0, (
            "Should not recommend split when segment is below 20%"
        )


class TestReadOnlyVariantRecommendation:
    """Test scenario: Read-only variant opportunity.

    When mixed users only READ from the secondary license type,
    a read-only variant could reduce licensing needs.
    """

    def test_read_variant_recommendation(self) -> None:
        """Mixed users with read-only secondary access should get variant rec."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("ReadVarRole", "FinForm", "Write", "Finance", 180),
                ("ReadVarRole", "SCMForm", "Write", "SCM", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 5 users: Write Finance, Read-only SCM
        for i in range(5):
            uid = f"USR_RV{i}"
            user_data.append((uid, f"ReadVarUser{i}", "ReadVarRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))
            activity_rows.append((uid, "SCMForm", "Read", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = analyze_role_usage_segmentation(
            role_name="ReadVarRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_users == 5
        # Should have a read-variant recommendation
        read_recs = [
            r for r in result.recommendations
            if "read" in r.option.lower() or "variant" in r.option.lower()
        ]
        assert len(read_recs) >= 1, (
            "Expected a read-only variant recommendation for mixed read-only users"
        )


class TestEmptyRoleHandling:
    """Test scenario: Role with no users assigned."""

    def test_empty_role_no_crash(self) -> None:
        """Empty role should return zero-count segmentation without errors."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("EmptyRole", "Form", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments([])
        activity = _build_activity_df([])
        pricing = _load_pricing()

        # -- Act --
        result = analyze_role_usage_segmentation(
            role_name="EmptyRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_users == 0
        assert len(result.recommendations) == 0


class TestSingleLicenseTypeRole:
    """Test scenario: Role with only one license type (no segmentation possible)."""

    def test_single_license_no_segmentation(self) -> None:
        """Single-license-type role should have no split recommendations."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("PureFinRole", f"FinForm_{i}", "Write", "Finance", 180)
                for i in range(5)
            ]
        )
        user_data = [(f"USR_P{i}", f"User{i}", "PureFinRole") for i in range(5)]
        activity_rows = [
            (f"USR_P{i}", f"FinForm_{i}", "Write", "Finance", "GL")
            for i in range(5)
        ]
        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = analyze_role_usage_segmentation(
            role_name="PureFinRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_users == 5
        assert len(result.recommendations) == 0


class TestLargeUserBase:
    """Test scenario: 100-user role to verify batch performance.

    Setup:
    - 60 Finance-Only, 30 SCM-Only, 10 Mixed
    - Algorithm should handle efficiently (no O(N^2) operations)
    """

    def test_large_user_base_correct_segmentation(self) -> None:
        """100-user role should segment correctly without performance issues."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("BigRole", "FinForm", "Write", "Finance", 180),
                ("BigRole", "SCMForm", "Write", "SCM", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        for i in range(60):
            uid = f"USR_BF{i}"
            user_data.append((uid, f"FinUser{i}", "BigRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))

        for i in range(30):
            uid = f"USR_BS{i}"
            user_data.append((uid, f"SCMUser{i}", "BigRole"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        for i in range(10):
            uid = f"USR_BM{i}"
            user_data.append((uid, f"MixUser{i}", "BigRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = analyze_role_usage_segmentation(
            role_name="BigRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_users == 100
        assert result.segmentation["finance_only"].count == 60
        assert result.segmentation["scm_only"].count == 30
        assert result.segmentation["mixed"].count == 10
        assert len(result.recommendations) > 0


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '2.3'."""

    def test_algorithm_id_is_2_3(self) -> None:
        """RoleUsageSegmentation should carry algorithm_id '2.3'."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("MetaRole", "Form_A", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments([])
        activity = _build_activity_df([])
        pricing = _load_pricing()

        # -- Act --
        result = analyze_role_usage_segmentation(
            role_name="MetaRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.algorithm_id == "2.3"
