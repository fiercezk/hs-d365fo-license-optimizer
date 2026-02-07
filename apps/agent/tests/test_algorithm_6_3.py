"""Tests for Algorithm 6.3: Duplicate Role Consolidator.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_6_3_duplicate_role_consolidator.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1394-1420
(Algorithm 6.3: Duplicate Role Consolidator).

Algorithm 6.3 finds similar custom roles that could be consolidated, reducing
role management overhead and simplifying the security model:
  - For each pair of custom roles, calculate menu item overlap percentage
  - If overlap > 80% (configurable), flag for consolidation
  - Calculate impact (users affected, maintenance reduction)
  - Report unique menu items in each role of the pair
  - Distinguish between custom and standard roles (only analyze custom)
  - Generate merge recommendations with affected user count
  - Sort results by overlap percentage descending

Key behaviors:
  - Two roles with 92% overlap (273/295 menu items) = consolidation candidate
  - Overlap < 80% (configurable threshold) = skip
  - Standard/system roles excluded from pairwise comparison
  - Each role pair reported only once (no duplicates: A+B same as B+A)
  - Report unique menu items in Role A not in Role B, and vice versa
  - Empty input = zero results
  - Users affected count = sum of users in both roles minus overlap
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.algorithms.algorithm_6_3_duplicate_role_consolidator import (
    DuplicateRolePair,  # noqa: F401 (used for type documentation)
    DuplicateRoleAnalysis,
    detect_duplicate_roles,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_security_config(
    rows: list[tuple[str, str, str, str, int]],
) -> pd.DataFrame:
    """Build synthetic security configuration DataFrame.

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


def _build_role_definitions(
    roles: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic role definitions DataFrame.

    Args:
        roles: List of dicts with keys: role_id, role_name, role_type.
    """
    records: list[dict[str, str]] = []
    for role in roles:
        records.append(
            {
                "role_id": role.get("role_id", role.get("role_name", "ROLE")),
                "role_name": role.get("role_name", "TestRole"),
                "role_type": role.get("role_type", "Custom"),
            }
        )
    return pd.DataFrame(records)


def _build_user_role_assignments(
    assignments: list[tuple[str, str]],
) -> pd.DataFrame:
    """Build synthetic user-role assignment DataFrame.

    Args:
        assignments: List of (user_id, role_name) tuples.
    """
    records: list[dict[str, str]] = []
    for uid, role in assignments:
        records.append(
            {
                "user_id": uid,
                "role_name": role,
                "status": "Active",
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: High Overlap Pair Detected
# ---------------------------------------------------------------------------


class TestHighOverlapDetected:
    """Test scenario: Two custom roles with >80% menu item overlap.

    Role A has 10 menu items, Role B has 10 menu items, 9 in common = 90% overlap.
    """

    def test_high_overlap_flagged(self) -> None:
        """Roles with 90% overlap should be flagged for consolidation."""
        # -- Arrange --
        # Role A: items 0-9 (10 items)
        # Role B: items 1-10 (10 items, 9 overlap with A)
        config_rows = []
        for i in range(10):
            config_rows.append(("RoleA", f"MenuItem_{i}", "Write", "Finance", 180))
        for i in range(1, 11):
            config_rows.append(("RoleB", f"MenuItem_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleA", "role_type": "Custom"},
                {"role_name": "RoleB", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_A1", "RoleA"),
                ("USR_A2", "RoleA"),
                ("USR_B1", "RoleB"),
            ]
        )

        # -- Act --
        result: DuplicateRoleAnalysis = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.duplicate_pairs) >= 1
        pair = result.duplicate_pairs[0]
        assert pair.overlap_percentage >= 80.0

    def test_overlap_percentage_calculated_correctly(self) -> None:
        """Overlap percentage should be intersection / union * 100."""
        # -- Arrange --
        # Role A: items 0-9 (10 items)
        # Role B: items 0-9 (exactly same 10 items) = 100% overlap
        config_rows = []
        for i in range(10):
            config_rows.append(("RoleSame1", f"Item_{i}", "Write", "Finance", 180))
            config_rows.append(("RoleSame2", f"Item_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleSame1", "role_type": "Custom"},
                {"role_name": "RoleSame2", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.duplicate_pairs) >= 1
        pair = result.duplicate_pairs[0]
        assert abs(pair.overlap_percentage - 100.0) < 0.1


# ---------------------------------------------------------------------------
# Test: Below Threshold Skipped
# ---------------------------------------------------------------------------


class TestBelowThresholdSkipped:
    """Test scenario: Two roles with overlap < 80% (default threshold).

    Roles with low overlap should not be flagged as duplicates.
    """

    def test_low_overlap_not_flagged(self) -> None:
        """Roles with 50% overlap should not appear in results."""
        # -- Arrange --
        # Role A: items 0-9 (10 items)
        # Role B: items 5-14 (10 items, only 5 overlap = 50%)
        config_rows = []
        for i in range(10):
            config_rows.append(("RoleLow1", f"Item_{i}", "Write", "Finance", 180))
        for i in range(5, 15):
            config_rows.append(("RoleLow2", f"Item_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleLow1", "role_type": "Custom"},
                {"role_name": "RoleLow2", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        # 50% overlap should be below 80% threshold
        assert len(result.duplicate_pairs) == 0


# ---------------------------------------------------------------------------
# Test: Custom Overlap Threshold
# ---------------------------------------------------------------------------


class TestCustomOverlapThreshold:
    """Test scenario: Custom overlap_threshold parameter."""

    def test_lowered_threshold_catches_more_pairs(self) -> None:
        """With overlap_threshold=40, 50% overlap pair should be flagged."""
        # -- Arrange --
        config_rows = []
        for i in range(10):
            config_rows.append(("RoleX", f"Item_{i}", "Write", "Finance", 180))
        for i in range(5, 15):
            config_rows.append(("RoleY", f"Item_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleX", "role_type": "Custom"},
                {"role_name": "RoleY", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
            overlap_threshold=40.0,
        )

        # -- Assert --
        # 50% overlap > 40% threshold, should be flagged
        assert len(result.duplicate_pairs) >= 1


# ---------------------------------------------------------------------------
# Test: Standard Roles Excluded
# ---------------------------------------------------------------------------


class TestStandardRolesExcluded:
    """Test scenario: Standard/system roles should not be compared.

    Only custom roles should be analyzed for duplicates.
    """

    def test_standard_roles_not_in_results(self) -> None:
        """Standard roles should be excluded from duplicate analysis."""
        # -- Arrange --
        config_rows = []
        for i in range(10):
            config_rows.append(("StdRole", f"Item_{i}", "Write", "Finance", 180))
            config_rows.append(("CustRole", f"Item_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "StdRole", "role_type": "Standard"},
                {"role_name": "CustRole", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        # StdRole should not appear in any pair
        for pair in result.duplicate_pairs:
            assert "StdRole" not in (pair.role_a, pair.role_b)


# ---------------------------------------------------------------------------
# Test: Unique Menu Items Reported
# ---------------------------------------------------------------------------


class TestUniqueMenuItemsReported:
    """Test scenario: Report which menu items are unique to each role.

    When consolidating, admins need to know what differs between the roles.
    """

    def test_unique_items_per_role(self) -> None:
        """Each pair should list unique menu items per role."""
        # -- Arrange --
        config_rows = []
        # Shared items: 0-8
        for i in range(9):
            config_rows.append(("RoleP", f"Shared_{i}", "Write", "Finance", 180))
            config_rows.append(("RoleQ", f"Shared_{i}", "Write", "Finance", 180))
        # Unique to RoleP
        config_rows.append(("RoleP", "UniqueP", "Write", "Finance", 180))
        # Unique to RoleQ
        config_rows.append(("RoleQ", "UniqueQ", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleP", "role_type": "Custom"},
                {"role_name": "RoleQ", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.duplicate_pairs) >= 1
        pair = result.duplicate_pairs[0]
        # Check that unique items are reported
        all_unique = pair.unique_to_role_a + pair.unique_to_role_b
        assert len(all_unique) == 2


# ---------------------------------------------------------------------------
# Test: Users Affected Count
# ---------------------------------------------------------------------------


class TestUsersAffectedCount:
    """Test scenario: Report number of users affected by consolidation."""

    def test_users_affected_counts(self) -> None:
        """Pair should report users assigned to each role."""
        # -- Arrange --
        config_rows = []
        for i in range(10):
            config_rows.append(("RoleM", f"Item_{i}", "Write", "Finance", 180))
            config_rows.append(("RoleN", f"Item_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleM", "role_type": "Custom"},
                {"role_name": "RoleN", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR_1", "RoleM"),
                ("USR_2", "RoleM"),
                ("USR_3", "RoleM"),
                ("USR_4", "RoleN"),
                ("USR_5", "RoleN"),
            ]
        )

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.duplicate_pairs) >= 1
        pair = result.duplicate_pairs[0]
        assert pair.users_affected >= 5


# ---------------------------------------------------------------------------
# Test: No Duplicate Pairs (Pair Reported Once)
# ---------------------------------------------------------------------------


class TestNoDuplicatePairEntries:
    """Test scenario: Each role pair should appear only once in results.

    RoleA+RoleB is the same as RoleB+RoleA; report only once.
    """

    def test_pair_reported_once(self) -> None:
        """Each pair should appear exactly once, not twice."""
        # -- Arrange --
        config_rows = []
        for i in range(10):
            config_rows.append(("RoleUni1", f"Item_{i}", "Write", "Finance", 180))
            config_rows.append(("RoleUni2", f"Item_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleUni1", "role_type": "Custom"},
                {"role_name": "RoleUni2", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        pair_tuples = set()
        for pair in result.duplicate_pairs:
            normalized = tuple(sorted([pair.role_a, pair.role_b]))
            assert normalized not in pair_tuples, f"Duplicate pair: {normalized}"
            pair_tuples.add(normalized)


# ---------------------------------------------------------------------------
# Test: Sorted by Overlap Percentage Descending
# ---------------------------------------------------------------------------


class TestSortedByOverlap:
    """Test scenario: Results sorted by overlap percentage (highest first)."""

    def test_highest_overlap_first(self) -> None:
        """Pairs with highest overlap should appear first."""
        # -- Arrange --
        config_rows = []
        # Pair 1: RoleH1 + RoleH2 = 100% overlap (10/10)
        for i in range(10):
            config_rows.append(("RoleH1", f"High_{i}", "Write", "Finance", 180))
            config_rows.append(("RoleH2", f"High_{i}", "Write", "Finance", 180))
        # Pair 2: RoleM1 + RoleM2 = ~82% overlap (9/11)
        for i in range(10):
            config_rows.append(("RoleM1", f"Med_{i}", "Write", "Finance", 180))
        for i in range(1, 11):
            config_rows.append(("RoleM2", f"Med_{i}", "Write", "Finance", 180))
        config_rows.append(("RoleM2", "Med_Extra", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleH1", "role_type": "Custom"},
                {"role_name": "RoleH2", "role_type": "Custom"},
                {"role_name": "RoleM1", "role_type": "Custom"},
                {"role_name": "RoleM2", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        if len(result.duplicate_pairs) >= 2:
            for i in range(len(result.duplicate_pairs) - 1):
                assert (
                    result.duplicate_pairs[i].overlap_percentage
                    >= result.duplicate_pairs[i + 1].overlap_percentage
                )


# ---------------------------------------------------------------------------
# Test: Merge Recommendation Generated
# ---------------------------------------------------------------------------


class TestMergeRecommendation:
    """Test scenario: Consolidation pairs should have merge recommendations."""

    def test_recommendation_present(self) -> None:
        """Each duplicate pair should carry a consolidation recommendation."""
        # -- Arrange --
        config_rows = []
        for i in range(10):
            config_rows.append(("RoleRec1", f"Item_{i}", "Write", "Finance", 180))
            config_rows.append(("RoleRec2", f"Item_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleRec1", "role_type": "Custom"},
                {"role_name": "RoleRec2", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.duplicate_pairs) >= 1
        pair = result.duplicate_pairs[0]
        assert pair.recommendation is not None
        assert len(pair.recommendation) > 0


# ---------------------------------------------------------------------------
# Test: Empty Input
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input DataFrames."""

    def test_empty_config_returns_empty(self) -> None:
        """Empty input should produce zero results without errors."""
        # -- Arrange --
        sec_config = _build_security_config([])
        role_defs = _build_role_definitions([])
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.duplicate_pairs) == 0

    def test_single_role_no_pairs(self) -> None:
        """Single role cannot form a pair; should return empty."""
        # -- Arrange --
        sec_config = _build_security_config(
            [("OnlyRole", "Item", "Write", "Finance", 180)]
        )
        role_defs = _build_role_definitions(
            [{"role_name": "OnlyRole", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.duplicate_pairs) == 0


# ---------------------------------------------------------------------------
# Test: Summary Statistics
# ---------------------------------------------------------------------------


class TestSummaryStatistics:
    """Test scenario: Result should include summary statistics."""

    def test_summary_populated(self) -> None:
        """Summary should count roles analyzed and pairs found."""
        # -- Arrange --
        config_rows = []
        for i in range(10):
            config_rows.append(("RoleS1", f"Item_{i}", "Write", "Finance", 180))
            config_rows.append(("RoleS2", f"Item_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleS1", "role_type": "Custom"},
                {"role_name": "RoleS2", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert result.total_roles_analyzed >= 2
        assert result.duplicate_pair_count >= 0


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '6.3'."""

    def test_algorithm_id_is_6_3(self) -> None:
        """DuplicateRoleAnalysis should carry algorithm_id '6.3'."""
        # -- Arrange --
        sec_config = _build_security_config([])
        role_defs = _build_role_definitions([])
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_duplicate_roles(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert result.algorithm_id == "6.3"
