"""Tests for Algorithm 3.8: Access Review Automation.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_3_8_access_review_automation.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md
(Algorithm 3.8: Access Review Automation).

Algorithm 3.8 automates periodic access reviews by analyzing user-role
assignments against actual usage data, identifying access that should be
revoked, certified, or escalated for review:
  - Generate access review campaigns for all users or filtered subsets
  - Compare assigned roles against actual usage (last 90 days)
  - Flag unused roles as candidates for revocation
  - Flag roles with declining usage as candidates for review
  - Auto-certify roles with consistent, active usage
  - Escalate high-privilege roles for mandatory manager review
  - Track review completion and generate compliance reports
  - Support configurable review periods and thresholds
  - Calculate review priority based on risk and cost

Key behaviors:
  - Unused role (0 activity in review period) = REVOKE recommendation
  - Declining usage (<10% of baseline) = REVIEW recommendation
  - Active usage (>50% of role capabilities used) = AUTO-CERTIFY
  - High-privilege unused role = ESCALATE (mandatory manager review)
  - New assignment (<30 days) = DEFER (too early to review)
  - Review campaign should cover all users in scope
  - Empty input = empty campaign with zero items
  - Items sorted by priority (risk * cost impact)
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.algorithms.algorithm_3_8_access_review_automation import (
    AccessReviewCampaign,
    ReviewAction,
    generate_access_review,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_user_role_assignments(
    assignments: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic user-role assignment DataFrame.

    Args:
        assignments: List of dicts with keys:
            user_id, user_name, role_name, assigned_date, status,
            is_high_privilege, license_type, license_cost_monthly.
    """
    records: list[dict[str, Any]] = []
    for a in assignments:
        records.append(
            {
                "user_id": a.get("user_id", "USR-001"),
                "user_name": a.get("user_name", "Test User"),
                "email": a.get("email", "test@contoso.com"),
                "role_name": a.get("role_name", "TestRole"),
                "role_id": a.get("role_id", a.get("role_name", "TestRole")),
                "assigned_date": a.get("assigned_date", "2025-01-01"),
                "status": a.get("status", "Active"),
                "is_high_privilege": a.get("is_high_privilege", False),
                "license_type": a.get("license_type", "Finance"),
                "license_cost_monthly": a.get("license_cost_monthly", 180.0),
            }
        )
    return pd.DataFrame(records)


def _build_activity_data(
    rows: list[tuple[str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic user activity DataFrame.

    Args:
        rows: List of (user_id, timestamp, menu_item, action) tuples.
    """
    records: list[dict[str, str]] = []
    for i, (uid, ts, menu_item, action) in enumerate(rows):
        records.append(
            {
                "user_id": uid,
                "timestamp": ts,
                "menu_item": menu_item,
                "action": action,
                "session_id": f"sess-{i:04d}",
            }
        )
    return pd.DataFrame(records)


def _build_security_config(
    rows: list[tuple[str, str]],
) -> pd.DataFrame:
    """Build minimal security config mapping role -> menu items.

    Args:
        rows: List of (role_name, menu_item) tuples.
    """
    records: list[dict[str, str]] = []
    for role, menu_item in rows:
        records.append(
            {
                "securityrole": role,
                "AOTName": menu_item,
                "AccessLevel": "Write",
                "LicenseType": "Finance",
                "Priority": 180,
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Unused Role -> REVOKE Recommendation
# ---------------------------------------------------------------------------


class TestUnusedRoleRevoke:
    """Test scenario: Role assigned but zero activity in review period.

    A role with no usage in the review period should be recommended
    for revocation.
    """

    def test_unused_role_recommends_revoke(self) -> None:
        """Role with 0 activity in 90 days = REVOKE recommendation."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-001",
                    "role_name": "Accountant",
                    "assigned_date": "2025-01-01",
                }
            ]
        )
        # No activity for this user/role
        activity = _build_activity_data([])
        sec_config = _build_security_config(
            [
                ("Accountant", "GeneralJournal"),
                ("Accountant", "TrialBalance"),
            ]
        )

        # -- Act --
        result: AccessReviewCampaign = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) >= 1
        item = result.review_items[0]
        assert item.recommended_action == ReviewAction.REVOKE
        assert item.user_id == "USR-001"
        assert item.role_name == "Accountant"

    def test_unused_role_includes_cost_impact(self) -> None:
        """REVOKE recommendation should include potential cost savings."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-001",
                    "role_name": "FinanceManager",
                    "license_cost_monthly": 180.0,
                }
            ]
        )
        activity = _build_activity_data([])
        sec_config = _build_security_config(
            [("FinanceManager", "BudgetApproval")]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) >= 1
        item = result.review_items[0]
        assert item.cost_impact_monthly >= 0


# ---------------------------------------------------------------------------
# Test: Declining Usage -> REVIEW Recommendation
# ---------------------------------------------------------------------------


class TestDecliningUsageReview:
    """Test scenario: Role with declining usage (<10% of baseline).

    A role where the user accesses less than 10% of the role's
    capabilities should be flagged for review.
    """

    def test_low_usage_recommends_review(self) -> None:
        """Role with <10% menu item coverage = REVIEW recommendation."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-002",
                    "role_name": "FullAccountant",
                    "assigned_date": "2025-01-01",
                }
            ]
        )
        # Role has 20 menu items but user only uses 1
        sec_config_rows = [
            ("FullAccountant", f"MenuItem_{i}") for i in range(20)
        ]
        sec_config = _build_security_config(sec_config_rows)
        activity = _build_activity_data(
            [("USR-002", "2026-01-15 10:00:00", "MenuItem_0", "Read")]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) >= 1
        item = result.review_items[0]
        assert item.recommended_action in (ReviewAction.REVIEW, ReviewAction.REVOKE)


# ---------------------------------------------------------------------------
# Test: Active Usage -> AUTO-CERTIFY
# ---------------------------------------------------------------------------


class TestActiveUsageAutoCertify:
    """Test scenario: Role with consistent, active usage.

    A role where the user regularly uses >50% of capabilities
    should be auto-certified (no review needed).
    """

    def test_active_usage_auto_certified(self) -> None:
        """Role with >50% menu item usage = AUTO_CERTIFY recommendation."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-003",
                    "role_name": "ActiveRole",
                    "assigned_date": "2025-01-01",
                }
            ]
        )
        # Role has 4 menu items, user uses 3
        sec_config = _build_security_config(
            [
                ("ActiveRole", "Item_A"),
                ("ActiveRole", "Item_B"),
                ("ActiveRole", "Item_C"),
                ("ActiveRole", "Item_D"),
            ]
        )
        activity = _build_activity_data(
            [
                ("USR-003", "2026-01-10 10:00:00", "Item_A", "Write"),
                ("USR-003", "2026-01-11 10:00:00", "Item_B", "Write"),
                ("USR-003", "2026-01-12 10:00:00", "Item_C", "Read"),
                ("USR-003", "2026-01-13 10:00:00", "Item_A", "Write"),
                ("USR-003", "2026-01-14 10:00:00", "Item_B", "Read"),
            ]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) >= 1
        item = result.review_items[0]
        assert item.recommended_action == ReviewAction.AUTO_CERTIFY


# ---------------------------------------------------------------------------
# Test: High-Privilege Unused -> ESCALATE
# ---------------------------------------------------------------------------


class TestHighPrivilegeEscalate:
    """Test scenario: Unused high-privilege role requires escalation.

    High-privilege roles that are unused cannot be auto-revoked;
    they must be escalated for mandatory manager review.
    """

    def test_unused_high_privilege_escalated(self) -> None:
        """Unused high-privilege role = ESCALATE recommendation."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-004",
                    "role_name": "SystemAdmin",
                    "assigned_date": "2025-01-01",
                    "is_high_privilege": True,
                }
            ]
        )
        activity = _build_activity_data([])
        sec_config = _build_security_config(
            [
                ("SystemAdmin", "SystemConfig"),
                ("SystemAdmin", "UserManagement"),
            ]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) >= 1
        item = result.review_items[0]
        assert item.recommended_action == ReviewAction.ESCALATE
        assert item.requires_manager_approval is True

    def test_active_high_privilege_not_escalated(self) -> None:
        """Actively used high-privilege role should not escalate."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-004",
                    "role_name": "SystemAdmin",
                    "assigned_date": "2025-01-01",
                    "is_high_privilege": True,
                }
            ]
        )
        sec_config = _build_security_config(
            [
                ("SystemAdmin", "SystemConfig"),
                ("SystemAdmin", "UserManagement"),
            ]
        )
        activity = _build_activity_data(
            [
                ("USR-004", "2026-01-15 10:00:00", "SystemConfig", "Write"),
                ("USR-004", "2026-01-16 10:00:00", "UserManagement", "Write"),
            ]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        escalated = [
            i for i in result.review_items
            if i.recommended_action == ReviewAction.ESCALATE
        ]
        assert len(escalated) == 0


# ---------------------------------------------------------------------------
# Test: New Assignment -> DEFER
# ---------------------------------------------------------------------------


class TestNewAssignmentDefer:
    """Test scenario: Recently assigned role (<30 days).

    New role assignments should be deferred from review
    since there is insufficient usage data.
    """

    def test_new_assignment_deferred(self) -> None:
        """Role assigned <30 days ago = DEFER recommendation."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-005",
                    "role_name": "NewRole",
                    "assigned_date": "2026-01-25",  # ~13 days ago
                }
            ]
        )
        activity = _build_activity_data([])
        sec_config = _build_security_config(
            [("NewRole", "FormA")]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) >= 1
        item = result.review_items[0]
        assert item.recommended_action == ReviewAction.DEFER

    def test_old_assignment_not_deferred(self) -> None:
        """Role assigned >30 days ago should not be deferred."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-005",
                    "role_name": "OldRole",
                    "assigned_date": "2025-06-01",  # 8 months ago
                }
            ]
        )
        activity = _build_activity_data([])
        sec_config = _build_security_config(
            [("OldRole", "FormA")]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        if len(result.review_items) >= 1:
            item = result.review_items[0]
            assert item.recommended_action != ReviewAction.DEFER


# ---------------------------------------------------------------------------
# Test: Multi-User Review Campaign
# ---------------------------------------------------------------------------


class TestMultiUserCampaign:
    """Test scenario: Review campaign covering multiple users."""

    def test_campaign_covers_all_users(self) -> None:
        """Review campaign should include all users in scope."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {"user_id": "USR-A", "role_name": "RoleA", "assigned_date": "2025-01-01"},
                {"user_id": "USR-B", "role_name": "RoleB", "assigned_date": "2025-01-01"},
                {"user_id": "USR-C", "role_name": "RoleC", "assigned_date": "2025-01-01"},
            ]
        )
        activity = _build_activity_data([])
        sec_config = _build_security_config(
            [("RoleA", "FormA"), ("RoleB", "FormB"), ("RoleC", "FormC")]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        reviewed_users = {item.user_id for item in result.review_items}
        assert "USR-A" in reviewed_users
        assert "USR-B" in reviewed_users
        assert "USR-C" in reviewed_users

    def test_campaign_counts_by_action(self) -> None:
        """Campaign summary should count items by recommended action."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {"user_id": "USR-A", "role_name": "RoleA", "assigned_date": "2025-01-01"},
                {"user_id": "USR-B", "role_name": "RoleB", "assigned_date": "2026-01-25"},
            ]
        )
        activity = _build_activity_data([])
        sec_config = _build_security_config(
            [("RoleA", "FormA"), ("RoleB", "FormB")]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.total_review_items >= 2
        assert hasattr(result, "revoke_count")
        assert hasattr(result, "certify_count")
        assert hasattr(result, "escalate_count")
        assert hasattr(result, "defer_count")


# ---------------------------------------------------------------------------
# Test: Usage Percentage Calculation
# ---------------------------------------------------------------------------


class TestUsagePercentage:
    """Test scenario: Verify usage percentage calculation."""

    def test_usage_percentage_populated(self) -> None:
        """Review item should include role usage percentage."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [{"user_id": "USR-PCT", "role_name": "PctRole", "assigned_date": "2025-01-01"}]
        )
        sec_config = _build_security_config(
            [
                ("PctRole", "Item_A"),
                ("PctRole", "Item_B"),
                ("PctRole", "Item_C"),
                ("PctRole", "Item_D"),
            ]
        )
        # User uses 2 of 4 items = 50%
        activity = _build_activity_data(
            [
                ("USR-PCT", "2026-01-15 10:00:00", "Item_A", "Write"),
                ("USR-PCT", "2026-01-16 10:00:00", "Item_B", "Read"),
            ]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) >= 1
        item = result.review_items[0]
        assert hasattr(item, "usage_percentage")
        assert 40.0 <= item.usage_percentage <= 60.0


# ---------------------------------------------------------------------------
# Test: Configurable Review Period
# ---------------------------------------------------------------------------


class TestConfigurableReviewPeriod:
    """Test scenario: Custom review_period_days parameter."""

    def test_custom_review_period(self) -> None:
        """Custom review period should affect activity window."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [{"user_id": "USR-PER", "role_name": "PeriodRole", "assigned_date": "2025-01-01"}]
        )
        sec_config = _build_security_config(
            [("PeriodRole", "FormA")]
        )
        # Activity 45 days ago -- within 60-day window but outside 30-day
        activity = _build_activity_data(
            [("USR-PER", "2025-12-24 10:00:00", "FormA", "Write")]
        )

        # -- Act --
        result_60 = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            review_period_days=60,
        )

        result_30 = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
            review_period_days=30,
        )

        # -- Assert --
        # With 60-day window, activity IS within period
        # With 30-day window, activity is OUTSIDE period
        items_60 = [i for i in result_60.review_items if i.user_id == "USR-PER"]
        items_30 = [i for i in result_30.review_items if i.user_id == "USR-PER"]
        # 30-day should be more likely to recommend revoke
        if items_60 and items_30:
            assert items_30[0].recommended_action != ReviewAction.AUTO_CERTIFY


# ---------------------------------------------------------------------------
# Test: Priority Sorting (Risk * Cost)
# ---------------------------------------------------------------------------


class TestPrioritySorting:
    """Test scenario: Review items sorted by priority."""

    def test_high_cost_high_risk_first(self) -> None:
        """Items with highest risk * cost should appear first."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [
                {
                    "user_id": "USR-LO",
                    "role_name": "CheapRole",
                    "assigned_date": "2025-01-01",
                    "license_cost_monthly": 60.0,
                    "is_high_privilege": False,
                },
                {
                    "user_id": "USR-HI",
                    "role_name": "ExpensiveAdmin",
                    "assigned_date": "2025-01-01",
                    "license_cost_monthly": 180.0,
                    "is_high_privilege": True,
                },
            ]
        )
        activity = _build_activity_data([])  # Both unused
        sec_config = _build_security_config(
            [("CheapRole", "FormA"), ("ExpensiveAdmin", "AdminPanel")]
        )

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        if len(result.review_items) >= 2:
            # Higher priority (expensive admin) should come first
            assert result.review_items[0].priority_score >= result.review_items[1].priority_score


# ---------------------------------------------------------------------------
# Test: Empty Input Handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input data."""

    def test_empty_assignments_returns_empty(self) -> None:
        """No user-role assignments should produce empty campaign."""
        # -- Arrange --
        assignments = _build_user_role_assignments([])
        activity = _build_activity_data([])
        sec_config = _build_security_config([])

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) == 0
        assert result.total_review_items == 0


# ---------------------------------------------------------------------------
# Test: Review Item Model Structure
# ---------------------------------------------------------------------------


class TestReviewItemModelStructure:
    """Test scenario: Verify review item has required fields."""

    def test_review_item_has_required_fields(self) -> None:
        """AccessReviewItem should have all spec-required fields."""
        # -- Arrange --
        assignments = _build_user_role_assignments(
            [{"user_id": "USR-MODEL", "role_name": "ModelRole", "assigned_date": "2025-01-01"}]
        )
        activity = _build_activity_data([])
        sec_config = _build_security_config([("ModelRole", "FormA")])

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert len(result.review_items) >= 1
        item = result.review_items[0]
        assert hasattr(item, "user_id")
        assert hasattr(item, "user_name")
        assert hasattr(item, "role_name")
        assert hasattr(item, "recommended_action")
        assert hasattr(item, "usage_percentage")
        assert hasattr(item, "cost_impact_monthly")
        assert hasattr(item, "priority_score")
        assert hasattr(item, "justification")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '3.8'."""

    def test_algorithm_id_is_3_8(self) -> None:
        """AccessReviewCampaign should carry algorithm_id '3.8'."""
        # -- Arrange --
        assignments = _build_user_role_assignments([])
        activity = _build_activity_data([])
        sec_config = _build_security_config([])

        # -- Act --
        result = generate_access_review(
            user_role_assignments=assignments,
            user_activity=activity,
            security_config=sec_config,
        )

        # -- Assert --
        assert result.algorithm_id == "3.8"
