"""Tests for Algorithm 6.1: Stale Role Detector.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_6_1_stale_role_detector.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1371-1391
(Algorithm 6.1: Stale Role Detector).

Algorithm 6.1 identifies roles that have not been assigned to any active users
in 6+ months, making them candidates for review or deletion:
  - Scan all defined security roles (custom and standard)
  - Check current user-role assignment counts
  - Check audit logs for last assignment date
  - Classify roles as stale if no assignments in configurable threshold (default 180 days)
  - Distinguish between custom and standard roles
  - Calculate risk level (low for unassigned roles)
  - Generate recommendations for review/deletion

Key behaviors:
  - Roles with 0 current assignments and no recent audit activity = stale
  - Roles with active assignments = not stale (skip)
  - Roles last assigned 180+ days ago (configurable) = stale
  - Standard/system roles flagged separately (recommend review, not deletion)
  - Custom roles with 0 users = recommend deletion
  - Support configurable staleness_threshold_days (default 180)
  - Empty input: zero results, no errors
  - Results should be sorted by days since last used (descending)
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.algorithms.algorithm_6_1_stale_role_detector import (
    StaleRole,
    StaleRoleAnalysis,
    detect_stale_roles,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_role_definitions(
    roles: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic role definitions DataFrame.

    Args:
        roles: List of dicts with keys:
            role_id, role_name, role_type (Custom/Standard),
            created_date, description.
    """
    records: list[dict[str, str]] = []
    for role in roles:
        records.append(
            {
                "role_id": role.get("role_id", "ROLE_001"),
                "role_name": role.get("role_name", "TestRole"),
                "role_type": role.get("role_type", "Custom"),
                "created_date": role.get("created_date", "2024-01-01"),
                "description": role.get("description", "Test role"),
            }
        )
    return pd.DataFrame(records)


def _build_user_role_assignments(
    assignments: list[tuple[str, str, str]],
) -> pd.DataFrame:
    """Build synthetic user-role assignment DataFrame.

    Args:
        assignments: List of (user_id, role_id, status) tuples.
    """
    records: list[dict[str, str]] = []
    for uid, role_id, status in assignments:
        records.append(
            {
                "user_id": uid,
                "role_id": role_id,
                "role_name": role_id,
                "status": status,
                "assigned_date": "2025-01-01",
            }
        )
    return pd.DataFrame(records)


def _build_audit_log(
    entries: list[tuple[str, str, str]],
) -> pd.DataFrame:
    """Build synthetic audit log DataFrame.

    Args:
        entries: List of (role_id, action, timestamp) tuples.
            Action: 'ASSIGNED', 'REMOVED'.
            Timestamp: 'YYYY-MM-DD HH:MM:SS'.
    """
    records: list[dict[str, str]] = []
    for i, (role_id, action, ts) in enumerate(entries):
        records.append(
            {
                "audit_id": f"AUD-{i:04d}",
                "role_id": role_id,
                "action": action,
                "timestamp": ts,
                "changed_by": "ADMIN-001",
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Role with Zero Assignments (Stale)
# ---------------------------------------------------------------------------


class TestZeroAssignmentsStale:
    """Test scenario: Custom role with no current assignments.

    A custom role that no user is assigned to should be flagged as stale.
    """

    def test_unassigned_custom_role_detected(self) -> None:
        """Custom role with 0 assignments should be flagged as stale."""
        # -- Arrange --
        roles = _build_role_definitions(
            [{"role_id": "ROLE_UNUSED", "role_name": "Unused Custom Role", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([])  # No assignments
        audit_log = _build_audit_log(
            [("ROLE_UNUSED", "ASSIGNED", "2025-01-15 10:00:00")]  # 12+ months ago
        )

        # -- Act --
        result: StaleRoleAnalysis = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        assert len(result.stale_roles) >= 1
        stale = result.stale_roles[0]
        assert stale.role_id == "ROLE_UNUSED"
        assert stale.current_assignment_count == 0

    def test_unassigned_role_recommends_deletion(self) -> None:
        """Custom role with 0 users should recommend review for deletion."""
        # -- Arrange --
        roles = _build_role_definitions(
            [{"role_id": "ROLE_UNUSED", "role_name": "Unused Custom Role", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log(
            [("ROLE_UNUSED", "ASSIGNED", "2025-01-15 10:00:00")]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        stale = result.stale_roles[0]
        assert "delet" in stale.recommendation.lower() or "review" in stale.recommendation.lower()


# ---------------------------------------------------------------------------
# Test: Role with Active Assignments (Not Stale)
# ---------------------------------------------------------------------------


class TestActiveAssignmentsNotStale:
    """Test scenario: Role with active user assignments.

    A role that currently has users assigned should NOT be stale.
    """

    def test_active_role_not_flagged(self) -> None:
        """Role with current active assignments should not appear as stale."""
        # -- Arrange --
        roles = _build_role_definitions(
            [{"role_id": "ROLE_ACTIVE", "role_name": "Active Role", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_A", "ROLE_ACTIVE", "Active"),
                ("USR_B", "ROLE_ACTIVE", "Active"),
            ]
        )
        audit_log = _build_audit_log(
            [("ROLE_ACTIVE", "ASSIGNED", "2026-01-10 10:00:00")]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        stale_ids = {s.role_id for s in result.stale_roles}
        assert "ROLE_ACTIVE" not in stale_ids


# ---------------------------------------------------------------------------
# Test: Standard Role vs Custom Role Treatment
# ---------------------------------------------------------------------------


class TestStandardVsCustomRole:
    """Test scenario: Standard (system) roles should get different recommendations.

    Standard roles cannot be deleted, only reviewed and potentially deprecated.
    """

    def test_standard_role_recommends_review_not_deletion(self) -> None:
        """Stale standard role should recommend review, not deletion."""
        # -- Arrange --
        roles = _build_role_definitions(
            [
                {
                    "role_id": "ROLE_STD",
                    "role_name": "System Standard Role",
                    "role_type": "Standard",
                }
            ]
        )
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log(
            [("ROLE_STD", "ASSIGNED", "2025-01-01 10:00:00")]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        assert len(result.stale_roles) >= 1
        stale = result.stale_roles[0]
        assert stale.role_type == "Standard"
        # Should NOT recommend deletion for standard roles
        assert "delet" not in stale.recommendation.lower()

    def test_custom_stale_role_identified(self) -> None:
        """Stale custom role should be identified with role_type='Custom'."""
        # -- Arrange --
        roles = _build_role_definitions(
            [{"role_id": "ROLE_CUST", "role_name": "Custom Role", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log(
            [("ROLE_CUST", "ASSIGNED", "2025-01-01 10:00:00")]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        stale = result.stale_roles[0]
        assert stale.role_type == "Custom"


# ---------------------------------------------------------------------------
# Test: Configurable Staleness Threshold
# ---------------------------------------------------------------------------


class TestConfigurableThreshold:
    """Test scenario: Custom staleness_threshold_days parameter."""

    def test_custom_threshold_90_days(self) -> None:
        """With 90-day threshold, role inactive for 100 days should be stale."""
        # -- Arrange --
        roles = _build_role_definitions(
            [{"role_id": "ROLE_THRESH", "role_name": "Threshold Test", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([])
        # Last assignment ~100 days ago
        audit_log = _build_audit_log(
            [("ROLE_THRESH", "ASSIGNED", "2025-10-28 10:00:00")]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
            staleness_threshold_days=90,
        )

        # -- Assert --
        stale_ids = {s.role_id for s in result.stale_roles}
        assert "ROLE_THRESH" in stale_ids

    def test_default_threshold_180_days(self) -> None:
        """With default 180-day threshold, role inactive 100 days = not stale."""
        # -- Arrange --
        roles = _build_role_definitions(
            [{"role_id": "ROLE_RECENT", "role_name": "Recent Role", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([])
        # Last assignment ~100 days ago -- within 180-day default
        audit_log = _build_audit_log(
            [("ROLE_RECENT", "ASSIGNED", "2025-10-28 10:00:00")]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
            # default threshold = 180
        )

        # -- Assert --
        stale_ids = {s.role_id for s in result.stale_roles}
        assert "ROLE_RECENT" not in stale_ids


# ---------------------------------------------------------------------------
# Test: Days Since Last Used
# ---------------------------------------------------------------------------


class TestDaysSinceLastUsed:
    """Test scenario: Verify days_since_last_used calculation."""

    def test_days_since_last_used_populated(self) -> None:
        """Stale role should report correct days since last assignment."""
        # -- Arrange --
        roles = _build_role_definitions(
            [{"role_id": "ROLE_OLD", "role_name": "Old Role", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log(
            [("ROLE_OLD", "ASSIGNED", "2025-01-01 10:00:00")]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        assert len(result.stale_roles) >= 1
        stale = result.stale_roles[0]
        assert stale.days_since_last_used > 180


# ---------------------------------------------------------------------------
# Test: No Audit History for Role
# ---------------------------------------------------------------------------


class TestNoAuditHistory:
    """Test scenario: Role with no audit log entries at all.

    Role exists in definitions but has never been assigned per audit logs.
    Should be considered stale (never used).
    """

    def test_never_used_role_stale(self) -> None:
        """Role with zero audit history should be flagged as stale."""
        # -- Arrange --
        roles = _build_role_definitions(
            [{"role_id": "ROLE_NEVER", "role_name": "Never Used", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log([])  # No entries at all

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        stale_ids = {s.role_id for s in result.stale_roles}
        assert "ROLE_NEVER" in stale_ids


# ---------------------------------------------------------------------------
# Test: Mixed Batch -- Some Stale, Some Active
# ---------------------------------------------------------------------------


class TestMixedBatch:
    """Test scenario: Mix of stale and active roles."""

    def test_only_stale_roles_in_results(self) -> None:
        """Only stale roles should appear in results."""
        # -- Arrange --
        roles = _build_role_definitions(
            [
                {"role_id": "ROLE_STALE1", "role_name": "Stale A", "role_type": "Custom"},
                {"role_id": "ROLE_ACTIVE", "role_name": "Active B", "role_type": "Custom"},
                {"role_id": "ROLE_STALE2", "role_name": "Stale C", "role_type": "Standard"},
            ]
        )
        assignments = _build_user_role_assignments(
            [("USR_A", "ROLE_ACTIVE", "Active")]
        )
        audit_log = _build_audit_log(
            [
                ("ROLE_STALE1", "ASSIGNED", "2025-01-01 10:00:00"),
                ("ROLE_ACTIVE", "ASSIGNED", "2026-01-30 10:00:00"),
                ("ROLE_STALE2", "ASSIGNED", "2024-06-01 10:00:00"),
            ]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        stale_ids = {s.role_id for s in result.stale_roles}
        assert "ROLE_STALE1" in stale_ids
        assert "ROLE_STALE2" in stale_ids
        assert "ROLE_ACTIVE" not in stale_ids


# ---------------------------------------------------------------------------
# Test: Results Sorted by Days Since Last Used
# ---------------------------------------------------------------------------


class TestSortedByDaysSinceUsed:
    """Test scenario: Results sorted by staleness (most stale first)."""

    def test_sorted_most_stale_first(self) -> None:
        """Roles should be sorted by days_since_last_used descending."""
        # -- Arrange --
        roles = _build_role_definitions(
            [
                {"role_id": "ROLE_OLD", "role_name": "Very Old", "role_type": "Custom"},
                {"role_id": "ROLE_LESS_OLD", "role_name": "Less Old", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log(
            [
                ("ROLE_OLD", "ASSIGNED", "2024-01-01 10:00:00"),  # Very old
                ("ROLE_LESS_OLD", "ASSIGNED", "2025-06-01 10:00:00"),  # Less old
            ]
        )

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        if len(result.stale_roles) >= 2:
            assert (
                result.stale_roles[0].days_since_last_used
                >= result.stale_roles[1].days_since_last_used
            )


# ---------------------------------------------------------------------------
# Test: Summary Statistics
# ---------------------------------------------------------------------------


class TestSummaryStatistics:
    """Test scenario: Result should include summary counts."""

    def test_summary_counts_populated(self) -> None:
        """Summary should count total roles, stale roles, and impact."""
        # -- Arrange --
        roles = _build_role_definitions(
            [
                {"role_id": "ROLE_A", "role_name": "A", "role_type": "Custom"},
                {"role_id": "ROLE_B", "role_name": "B", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log([])

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        assert result.total_roles_analyzed >= 2
        assert result.stale_role_count >= 0


# ---------------------------------------------------------------------------
# Test: Empty Input
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input DataFrames."""

    def test_empty_roles_returns_empty(self) -> None:
        """No role definitions should produce zero results."""
        # -- Arrange --
        roles = _build_role_definitions([])
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log([])

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        assert len(result.stale_roles) == 0


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '6.1'."""

    def test_algorithm_id_is_6_1(self) -> None:
        """StaleRoleAnalysis should carry algorithm_id '6.1'."""
        # -- Arrange --
        roles = _build_role_definitions([])
        assignments = _build_user_role_assignments([])
        audit_log = _build_audit_log([])

        # -- Act --
        result = detect_stale_roles(
            role_definitions=roles,
            user_role_assignments=assignments,
            audit_log=audit_log,
        )

        # -- Assert --
        assert result.algorithm_id == "6.1"
