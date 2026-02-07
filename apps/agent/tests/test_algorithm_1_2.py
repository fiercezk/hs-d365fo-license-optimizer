"""Tests for Algorithm 1.2: User Segment Analyzer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_1_2_user_segment_analyzer.py is implemented.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 108-200.

Algorithm 1.2 analyzes which users assigned to a given role actually use
which license-type features. For each role it produces:
  - Total user count
  - Segment breakdown: Commerce-Only, Finance-Only, SCM-Only,
    Operations-Only, Team-Members-Only, Mixed-Usage, Inactive
  - Per-segment counts and percentages
  - Detailed per-user breakdown of licenses used

Key behaviors:
  - Categorize each user into exactly one segment based on their activity
  - Inactive users (zero activity in 90 days) go to 'Inactive' segment
  - Users accessing only one license type go to '<LicenseType>-Only'
  - Users accessing multiple license types go to 'Mixed-Usage'
  - Handle edge cases: empty roles, roles with no activity data
  - Respect configurable analysis_days parameter (default 90)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_1_2_user_segment_analyzer import (
    UserSegmentAnalysis,
    analyze_user_segments,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

PERCENTAGE_TOLERANCE: float = 0.01

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_security_config() -> pd.DataFrame:
    """Load the security configuration sample CSV."""
    return pd.read_csv(FIXTURES_DIR / "security_config_sample.csv")


def _load_user_activity() -> pd.DataFrame:
    """Load the user activity log sample CSV."""
    return pd.read_csv(FIXTURES_DIR / "user_activity_log_sample.csv")


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
# Test: Finance-Only Users in a Mixed Role
# ---------------------------------------------------------------------------


class TestFinanceOnlySegment:
    """Test scenario: Role with users who only access Finance features.

    Setup:
    - Role 'AccountingRole' has Finance and SCM menu items
    - User A accesses only Finance items
    - User B accesses only Finance items
    - Both should be in the 'Finance-Only' segment

    Expected:
    - Finance-Only: 2 users, 100% of active users
    - All other segments: 0 users
    """

    def test_finance_only_users_segmented_correctly(self) -> None:
        """Users accessing only Finance features should be in Finance-Only segment."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("AccountingRole", "GeneralJournal", "Write", "Finance", 180),
                ("AccountingRole", "BankRecon", "Write", "Finance", 180),
                ("AccountingRole", "PurchaseOrder", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_A", "Alice", "AccountingRole"),
                ("USR_B", "Bob", "AccountingRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_A", "GeneralJournal", "Write", "Finance", "General Ledger"),
                ("USR_A", "BankRecon", "Read", "Finance", "Cash Management"),
                ("USR_B", "GeneralJournal", "Read", "Finance", "General Ledger"),
            ]
        )

        # -- Act --
        result: UserSegmentAnalysis = analyze_user_segments(
            role_name="AccountingRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.role_name == "AccountingRole"
        assert result.total_users == 2
        assert result.segments["Finance-Only"].count == 2
        assert abs(result.segments["Finance-Only"].percentage - 100.0) < PERCENTAGE_TOLERANCE


class TestSCMOnlySegment:
    """Test scenario: Users who only access SCM features."""

    def test_scm_only_users_segmented_correctly(self) -> None:
        """Users accessing only SCM features should be in SCM-Only segment."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("MixedRole", "GeneralJournal", "Write", "Finance", 180),
                ("MixedRole", "PurchaseOrder", "Write", "SCM", 180),
                ("MixedRole", "InventoryOnHand", "Read", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_C", "Charlie", "MixedRole"),
                ("USR_D", "Diana", "MixedRole"),
                ("USR_E", "Eve", "MixedRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_C", "PurchaseOrder", "Write", "SCM", "Procurement"),
                ("USR_D", "InventoryOnHand", "Read", "SCM", "Inventory"),
                ("USR_E", "PurchaseOrder", "Read", "SCM", "Procurement"),
                ("USR_E", "InventoryOnHand", "Read", "SCM", "Inventory"),
            ]
        )

        # -- Act --
        result = analyze_user_segments(
            role_name="MixedRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.total_users == 3
        assert result.segments["SCM-Only"].count == 3


class TestMixedUsageSegment:
    """Test scenario: Users who access features from multiple license types.

    Setup:
    - User accesses both Finance and SCM menu items
    - Should be classified as 'Mixed-Usage'
    """

    def test_mixed_usage_users_classified(self) -> None:
        """Users accessing Finance AND SCM features should be Mixed-Usage."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("HybridRole", "GeneralJournal", "Write", "Finance", 180),
                ("HybridRole", "PurchaseOrder", "Write", "SCM", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [("USR_MIX", "Mia", "HybridRole")]
        )
        activity = _build_activity_df(
            [
                ("USR_MIX", "GeneralJournal", "Write", "Finance", "General Ledger"),
                ("USR_MIX", "PurchaseOrder", "Write", "SCM", "Procurement"),
            ]
        )

        # -- Act --
        result = analyze_user_segments(
            role_name="HybridRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.total_users == 1
        assert result.segments["Mixed-Usage"].count == 1


class TestInactiveUsersSegment:
    """Test scenario: Users with zero activity in the analysis period.

    Setup:
    - 3 users assigned to role, 1 has no activity data
    - Inactive user should go to 'Inactive' segment
    """

    def test_inactive_user_classified(self) -> None:
        """User with zero activity should be in Inactive segment."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("InactiveTestRole", "Form_A", "Read", "Finance", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_ACTIVE", "Active User", "InactiveTestRole"),
                ("USR_INACTIVE", "Inactive User", "InactiveTestRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_ACTIVE", "Form_A", "Read", "Finance", "General Ledger"),
            ]
        )

        # -- Act --
        result = analyze_user_segments(
            role_name="InactiveTestRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.total_users == 2
        assert result.segments["Inactive"].count == 1
        assert result.segments["Finance-Only"].count == 1


class TestEmptyRoleNoUsers:
    """Test scenario: Role with no assigned users."""

    def test_empty_role_returns_zero_segments(self) -> None:
        """Role with no users should return zero-count segments."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("EmptyRole", "Form_A", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments([])
        activity = _build_activity_df([])

        # -- Act --
        result = analyze_user_segments(
            role_name="EmptyRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.total_users == 0
        for segment in result.segments.values():
            assert segment.count == 0


class TestTeamMembersOnlySegment:
    """Test scenario: Users who only access Team Members-eligible features."""

    def test_team_members_only_segment(self) -> None:
        """Users accessing only Team Members features should be in TM-Only segment."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("MixedRole2", "UserProfile", "Write", "Team Members", 60),
                ("MixedRole2", "TimeEntry", "Write", "Team Members", 60),
                ("MixedRole2", "GeneralJournal", "Write", "Finance", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [("USR_TM", "Team User", "MixedRole2")]
        )
        activity = _build_activity_df(
            [
                ("USR_TM", "UserProfile", "Write", "Team Members", "Self-Service"),
                ("USR_TM", "TimeEntry", "Write", "Team Members", "Self-Service"),
            ]
        )

        # -- Act --
        result = analyze_user_segments(
            role_name="MixedRole2",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.segments["Team-Members-Only"].count == 1


class TestPercentageCalculation:
    """Test scenario: Verify percentage calculations across segments.

    Setup:
    - 10 users: 4 Finance-Only, 3 SCM-Only, 2 Mixed, 1 Inactive
    - Percentages should sum to 100.0%
    """

    def test_segment_percentages_sum_to_100(self) -> None:
        """All segment percentages should sum to 100.0%."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("BigRole", "FinForm", "Write", "Finance", 180),
                ("BigRole", "SCMForm", "Write", "SCM", 180),
            ]
        )

        user_data: list[tuple[str, str, str]] = []
        activity_rows: list[tuple[str, str, str, str, str]] = []

        # 4 Finance-Only users
        for i in range(4):
            uid = f"USR_F{i}"
            user_data.append((uid, f"FinUser{i}", "BigRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))

        # 3 SCM-Only users
        for i in range(3):
            uid = f"USR_S{i}"
            user_data.append((uid, f"SCMUser{i}", "BigRole"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        # 2 Mixed users
        for i in range(2):
            uid = f"USR_M{i}"
            user_data.append((uid, f"MixUser{i}", "BigRole"))
            activity_rows.append((uid, "FinForm", "Write", "Finance", "GL"))
            activity_rows.append((uid, "SCMForm", "Write", "SCM", "Procurement"))

        # 1 Inactive user
        user_data.append(("USR_INACT", "InactiveGuy", "BigRole"))

        assignments = _build_user_role_assignments(user_data)
        activity = _build_activity_df(activity_rows)

        # -- Act --
        result = analyze_user_segments(
            role_name="BigRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.total_users == 10
        assert result.segments["Finance-Only"].count == 4
        assert result.segments["SCM-Only"].count == 3
        assert result.segments["Mixed-Usage"].count == 2
        assert result.segments["Inactive"].count == 1

        total_pct = sum(seg.percentage for seg in result.segments.values())
        assert abs(total_pct - 100.0) < 0.1, (
            f"Segment percentages should sum to 100%, got {total_pct:.2f}%"
        )


class TestDetailedBreakdownPerUser:
    """Test scenario: Verify detailed per-user breakdown is returned."""

    def test_detailed_breakdown_contains_all_users(self) -> None:
        """Detailed breakdown should list every user with their segment."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("DetailRole", "FinForm", "Write", "Finance", 180)]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_D1", "User1", "DetailRole"),
                ("USR_D2", "User2", "DetailRole"),
            ]
        )
        activity = _build_activity_df(
            [
                ("USR_D1", "FinForm", "Read", "Finance", "GL"),
                ("USR_D2", "FinForm", "Write", "Finance", "GL"),
            ]
        )

        # -- Act --
        result = analyze_user_segments(
            role_name="DetailRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        user_ids_in_breakdown = {u.user_id for u in result.detailed_breakdown}
        assert "USR_D1" in user_ids_in_breakdown
        assert "USR_D2" in user_ids_in_breakdown
        assert len(result.detailed_breakdown) == 2


class TestCommerceOnlySegment:
    """Test scenario: Users accessing only Commerce license features."""

    def test_commerce_only_classified(self) -> None:
        """Users accessing only Commerce items should be in Commerce-Only."""
        # -- Arrange --
        sec_config = _build_security_config(
            [
                ("RetailRole", "POSForm", "Write", "Commerce", 180),
                ("RetailRole", "FinForm", "Write", "Finance", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [("USR_COM", "ComUser", "RetailRole")]
        )
        activity = _build_activity_df(
            [("USR_COM", "POSForm", "Write", "Commerce", "Retail")]
        )

        # -- Act --
        result = analyze_user_segments(
            role_name="RetailRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.segments["Commerce-Only"].count == 1


class TestConfigurableAnalysisDays:
    """Test scenario: Custom analysis_days parameter.

    With analysis_days=30, only activity from the last 30 days should count.
    Users with activity older than 30 days should be classified as Inactive.
    """

    def test_custom_analysis_days_parameter(self) -> None:
        """Custom analysis_days should restrict the activity window."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("DaysRole", "Form_A", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments(
            [("USR_OLD", "OldUser", "DaysRole")]
        )
        # Activity from 120 days ago -- outside 30-day window
        old_activity = pd.DataFrame(
            [
                {
                    "user_id": "USR_OLD",
                    "timestamp": "2025-09-01 10:00:00",
                    "menu_item": "Form_A",
                    "action": "Read",
                    "session_id": "sess-old",
                    "license_tier": "Finance",
                    "feature": "GL",
                }
            ]
        )

        # -- Act --
        result = analyze_user_segments(
            role_name="DaysRole",
            user_role_assignments=assignments,
            user_activity=old_activity,
            security_config=sec_config,
            analysis_days=30,
        )

        # -- Assert --
        # With 30-day window, the old activity should not count
        assert result.segments["Inactive"].count == 1


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is correct."""

    def test_algorithm_id_is_1_2(self) -> None:
        """UserSegmentAnalysis should carry algorithm_id '1.2'."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("MetaRole", "Form_A", "Read", "Finance", 180)]
        )
        assignments = _build_user_role_assignments([])
        activity = _build_activity_df([])

        # -- Act --
        result = analyze_user_segments(
            role_name="MetaRole",
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.algorithm_id == "1.2"
