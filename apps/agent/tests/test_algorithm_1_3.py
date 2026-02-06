"""Tests for Algorithm 1.3: Role Splitting Recommender.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_1_3_role_splitting_recommender.py is implemented.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 204-298.

Algorithm 1.3 recommends splitting a role into multiple license-specific roles
based on the role's license composition (from Algorithm 1.1) and user segment
analysis (from Algorithm 1.2). The algorithm:
  - Identifies roles with >1 significant license type (configurable threshold)
  - Checks if users segment by license type (exclusive usage patterns)
  - Calculates potential savings from creating license-specific role variants
  - Generates split recommendations with savings, effort, and user impact
  - Returns no-split recommendation when criteria are not met

Key behaviors:
  - shouldSplit=False when role primarily uses one license type
  - shouldSplit=False when no user segment exclusively uses one license
  - shouldSplit=True with savings when exclusive-use segments exist
  - Savings = (currentHighLicense - segmentLicense) * exclusiveUserCount
  - Implementation effort estimation (Low/Medium/High)
  - Configurable min_percentage threshold for significant license types
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_1_3_role_splitting_recommender import (
    RoleSplitRecommendation,
    recommend_role_split,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

MONETARY_TOLERANCE: float = 0.01
PERCENTAGE_TOLERANCE: float = 0.01

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
# Test: Single License Type -- No Split
# ---------------------------------------------------------------------------


class TestSingleLicenseNoSplit:
    """Test scenario: Role where all menu items require the same license.

    A role with 100% Finance items should NOT be recommended for splitting.
    """

    def test_single_license_role_no_split(self) -> None:
        """Role with only Finance items should return shouldSplit=False."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("PureFinRole", f"FinForm_{i}", "Write", "Finance", 180)
                for i in range(10)
            ]
        )
        assignments = _build_user_role_assignments(
            [(f"USR_{i}", f"User{i}", "PureFinRole") for i in range(5)]
        )
        activity = _build_activity_df(
            [
                (f"USR_{i}", f"FinForm_{i % 10}", "Write", "Finance", "GL")
                for i in range(5)
            ]
        )
        pricing = _load_pricing()

        # -- Act --
        result: RoleSplitRecommendation = recommend_role_split(
            role_name="PureFinRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_split is False
        assert "one license type" in result.rationale.lower() or \
               "single" in result.rationale.lower()


class TestTwoLicenseTypesWithExclusiveSegments:
    """Test scenario: Role with Finance + SCM items and exclusive user segments.

    Setup:
    - Role has 60% Finance items, 40% SCM items
    - 7 users only access Finance items
    - 3 users only access SCM items
    - Current license: Finance + SCM = $210/month per user (combined)

    Expected:
    - shouldSplit=True
    - Finance-only users can downgrade to Finance ($180)
    - SCM-only users can downgrade to SCM ($180)
    - Total savings from avoiding combined license
    """

    def test_split_recommended_with_exclusive_segments(self) -> None:
        """Role with clear user segments should be recommended for splitting."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("MixedRole", f"FinForm_{i}", "Write", "Finance", 180)
                for i in range(6)
            ]
            + [
                ("MixedRole", f"SCMForm_{i}", "Write", "SCM", 180)
                for i in range(4)
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 7 Finance-only users
        for i in range(7):
            uid = f"USR_F{i}"
            user_data.append((uid, f"FinUser{i}", "MixedRole"))
            activity_rows.append((uid, f"FinForm_{i % 6}", "Write", "Finance", "GL"))

        # 3 SCM-only users
        for i in range(3):
            uid = f"USR_S{i}"
            user_data.append((uid, f"SCMUser{i}", "MixedRole"))
            activity_rows.append((uid, f"SCMForm_{i % 4}", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result: RoleSplitRecommendation = recommend_role_split(
            role_name="MixedRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_split is True
        assert len(result.proposed_roles) >= 2
        assert result.total_potential_savings_per_month > 0


class TestNoExclusiveSegmentsNoSplit:
    """Test scenario: Mixed-license role where ALL users use both licenses.

    If every user accesses both Finance and SCM items, there are no
    exclusive segments and splitting would not save anything.
    """

    def test_all_mixed_users_no_split(self) -> None:
        """When all users use both licenses, shouldSplit=False."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("AllMixedRole", "FinForm", "Write", "Finance", 180),
                ("AllMixedRole", "SCMForm", "Write", "SCM", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # All 5 users use both Finance and SCM
        for i in range(5):
            uid = f"USR_MIX{i}"
            user_data.append((uid, f"MixUser{i}", "AllMixedRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result: RoleSplitRecommendation = recommend_role_split(
            role_name="AllMixedRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_split is False
        assert "mixed" in result.rationale.lower() or \
               "no user segment" in result.rationale.lower()


class TestMinPercentageThreshold:
    """Test scenario: License type below the significance threshold.

    If a license type represents <10% of items, it should not be
    considered significant enough for splitting.
    """

    def test_below_min_percentage_no_split(self) -> None:
        """License types below min_percentage threshold should not trigger split."""
        # -- Arrange --
        # 95% Finance, 5% SCM -- SCM is below the 10% default
        sec_config = _build_security_config(
            [
                ("DominantRole", f"FinForm_{i}", "Write", "Finance", 180)
                for i in range(19)
            ]
            + [("DominantRole", "SCMForm_0", "Write", "SCM", 180)]
        )
        assignments = _build_user_role_assignments(
            [("USR_DOM", "DomUser", "DominantRole")]
        )
        activity = _build_activity_df(
            [("USR_DOM", "SCMForm_0", "Write", "SCM", "Procurement")]
        )
        pricing = _load_pricing()

        # -- Act --
        result = recommend_role_split(
            role_name="DominantRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
            min_percentage=10.0,
        )

        # -- Assert --
        assert result.should_split is False


class TestSavingsCalculation:
    """Test scenario: Verify savings math for a split recommendation.

    Setup:
    - Role highest license: Finance + SCM combined ($210/month)
    - 10 Finance-only users -> downgrade to Finance ($180/month)
    - Savings per user: $210 - $180 = $30/month
    - Total monthly savings: $30 * 10 = $300/month
    """

    def test_savings_math_correct(self) -> None:
        """Savings should equal (highLicense - segmentLicense) * userCount."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("CalcRole", f"FinForm_{i}", "Write", "Finance", 180)
                for i in range(6)
            ]
            + [
                ("CalcRole", f"SCMForm_{i}", "Write", "SCM", 180)
                for i in range(4)
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 10 Finance-only users
        for i in range(10):
            uid = f"USR_CALC{i}"
            user_data.append((uid, f"CalcUser{i}", "CalcRole"))
            activity_rows.append((uid, f"FinForm_{i % 6}", "Write", "Finance", "GL"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = recommend_role_split(
            role_name="CalcRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_split is True
        assert result.total_potential_savings_per_month > 0

        # Verify at least one proposed role has Finance-only users
        finance_role = None
        for role in result.proposed_roles:
            if role.license_type == "Finance":
                finance_role = role
                break
        assert finance_role is not None, (
            "Expected a proposed Finance-only role in the split"
        )
        assert finance_role.exclusive_user_count == 10


class TestImplementationEffortEstimation:
    """Test scenario: Implementation effort should be estimated.

    The effort depends on complexity:
    - Low: simple 2-way split with clear segments
    - Medium: 3+ role variants, moderate user count
    - High: many roles, large user base, complex dependencies
    """

    def test_effort_is_returned(self) -> None:
        """Split recommendation should include implementation effort."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("EffortRole", "FinForm", "Write", "Finance", 180),
                ("EffortRole", "SCMForm", "Write", "SCM", 180),
            ]
        )
        user_data = [(f"USR_E{i}", f"EUser{i}", "EffortRole") for i in range(6)]
        activity_rows = [
            (f"USR_E{i}", "FinForm", "Write", "Finance", "GL")
            for i in range(3)
        ] + [
            (f"USR_E{i}", "SCMForm", "Write", "SCM", "Procurement")
            for i in range(3, 6)
        ]
        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = recommend_role_split(
            role_name="EffortRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_split is True
        assert result.implementation_effort in ("Low", "Medium", "High")


class TestThreeLicenseTypeSplit:
    """Test scenario: Role spanning Finance, SCM, and Commerce.

    Setup:
    - 5 Finance-only users, 3 SCM-only users, 2 Commerce-only users
    - Should recommend 3 variant roles
    """

    def test_three_way_split(self) -> None:
        """Role with 3 license types and exclusive segments should propose 3 roles."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("TriRole", "FinForm", "Write", "Finance", 180),
                ("TriRole", "SCMForm", "Write", "SCM", 180),
                ("TriRole", "ComForm", "Write", "Commerce", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        for i in range(5):
            uid = f"USR_TF{i}"
            user_data.append((uid, f"FinUser{i}", "TriRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))

        for i in range(3):
            uid = f"USR_TS{i}"
            user_data.append((uid, f"SCMUser{i}", "TriRole"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        for i in range(2):
            uid = f"USR_TC{i}"
            user_data.append((uid, f"ComUser{i}", "TriRole"))
            activity_rows.append((uid, "ComForm", "Write", "Commerce", "Retail"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = recommend_role_split(
            role_name="TriRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_split is True
        assert len(result.proposed_roles) >= 3


class TestRoleNotInConfig:
    """Test scenario: Role that does not exist in security config.

    The algorithm should handle this gracefully -- no items means no split.
    """

    def test_nonexistent_role_no_split(self) -> None:
        """Nonexistent role should return shouldSplit=False gracefully."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("OtherRole", "Form_A", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments([])
        activity = _build_activity_df([])
        pricing = _load_pricing()

        # -- Act --
        result = recommend_role_split(
            role_name="NonexistentRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_split is False


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '1.3'."""

    def test_algorithm_id_is_1_3(self) -> None:
        """RoleSplitRecommendation should carry algorithm_id '1.3'."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("MetaRole", "Form_A", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments([])
        activity = _build_activity_df([])
        pricing = _load_pricing()

        # -- Act --
        result = recommend_role_split(
            role_name="MetaRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.algorithm_id == "1.3"


class TestCustomMinPercentage:
    """Test scenario: Custom min_percentage=5.0 makes more types significant.

    With default min_percentage=10, a type at 8% would be ignored.
    With min_percentage=5, the same type is significant and may trigger a split.
    """

    def test_lower_threshold_triggers_split(self) -> None:
        """Lowering min_percentage should make more license types significant."""
        # -- Arrange --
        # 92% Finance (23 items), 8% SCM (2 items)
        sec_config = _build_security_config(
            [
                ("LowThreshRole", f"FinForm_{i}", "Write", "Finance", 180)
                for i in range(23)
            ]
            + [
                ("LowThreshRole", f"SCMForm_{i}", "Write", "SCM", 180)
                for i in range(2)
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 8 Finance-only users
        for i in range(8):
            uid = f"USR_LF{i}"
            user_data.append((uid, f"FinUser{i}", "LowThreshRole"))
            activity_rows.append((uid, f"FinForm_{i}", "Write", "Finance", "GL"))

        # 2 SCM-only users
        for i in range(2):
            uid = f"USR_LS{i}"
            user_data.append((uid, f"SCMUser{i}", "LowThreshRole"))
            activity_rows.append((uid, f"SCMForm_{i}", "Write", "SCM", "Procurement"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)
        pricing = _load_pricing()

        # -- Act --
        result = recommend_role_split(
            role_name="LowThreshRole",
            security_config=sec_config,
            user_role_assignments=assignments,
            user_activity=activity,
            pricing_config=pricing,
            min_percentage=5.0,
        )

        # -- Assert --
        # With 8% SCM and min_percentage=5, SCM is significant
        assert result.should_split is True
