"""Tests for Algorithm 6.2: Permission Explosion Detector.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_6_2_permission_explosion_detector.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md
(Algorithm 6.2: Permission Explosion Detector).
Category: Role Management.

Algorithm 6.2 detects roles with excessive permissions (permission explosion),
which pose security risks and increase license costs:
  - Analyze each role's menu item count and access level distribution
  - Flag roles with menu item counts exceeding threshold (configurable)
  - Detect roles with disproportionate write/delete permissions
  - Identify roles that grant access across multiple license tiers
  - Calculate the "permission density" (permissions per user assigned)
  - Flag roles that have grown over time (permission creep at role level)
  - Compare role sizes against organizational averages
  - Generate splitting recommendations for oversized roles
  - Calculate license cost impact of permission explosion

Key behaviors:
  - Role with 500+ menu items (configurable) = EXPLOSION_DETECTED (HIGH)
  - Role with >80% write/delete access = EXCESSIVE_WRITE_ACCESS (HIGH)
  - Role spanning 3+ license tiers = CROSS_TIER_EXPLOSION (MEDIUM)
  - Role 3x larger than org average = STATISTICAL_OUTLIER (MEDIUM)
  - Role with <50 menu items = normal, no finding
  - Empty input = zero findings, no errors
  - Results sorted by menu item count descending
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from src.algorithms.algorithm_6_2_permission_explosion_detector import (
    PermissionExplosionFinding,
    PermissionExplosionAnalysis,
    detect_permission_explosions,
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
        roles: List of dicts with keys: role_name, role_type, created_date.
    """
    records: list[dict[str, str]] = []
    for role in roles:
        records.append(
            {
                "role_id": role.get("role_id", role.get("role_name", "ROLE")),
                "role_name": role.get("role_name", "TestRole"),
                "role_type": role.get("role_type", "Custom"),
                "created_date": role.get("created_date", "2024-01-01"),
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
            {"user_id": uid, "role_name": role, "status": "Active"}
        )
    return pd.DataFrame(records)


def _generate_large_role_config(
    role_name: str,
    count: int,
    access_level: str = "Write",
    license_type: str = "Finance",
    priority: int = 180,
) -> list[tuple[str, str, str, str, int]]:
    """Generate many menu item rows for a single role.

    Args:
        role_name: Security role name.
        count: Number of menu items to generate.
        access_level: Access level for all items.
        license_type: License type for all items.
        priority: Priority for all items.

    Returns:
        List of tuples suitable for _build_security_config.
    """
    return [
        (role_name, f"MenuItem_{i:04d}", access_level, license_type, priority)
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# Test: Role with Excessive Menu Items (HIGH)
# ---------------------------------------------------------------------------


class TestExcessiveMenuItems:
    """Test scenario: Role with 500+ menu items (default threshold).

    Roles with too many permissions indicate poor design and security risk.
    """

    def test_large_role_flagged(self) -> None:
        """Role with 500+ menu items = permission explosion finding."""
        # -- Arrange --
        config_rows = _generate_large_role_config("MegaRole", 600)
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "MegaRole", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments(
            [("USR-A", "MegaRole"), ("USR-B", "MegaRole")]
        )

        # -- Act --
        result: PermissionExplosionAnalysis = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        explosion_findings = [
            f for f in result.findings
            if f.role_name == "MegaRole"
            and "explosion" in f.finding_type.lower()
        ]
        assert len(explosion_findings) >= 1
        assert explosion_findings[0].severity in ("HIGH", "CRITICAL")
        assert explosion_findings[0].menu_item_count >= 600

    def test_small_role_not_flagged(self) -> None:
        """Role with <50 menu items should not be flagged."""
        # -- Arrange --
        config_rows = _generate_large_role_config("SmallRole", 30)
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "SmallRole", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "SmallRole")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        explosion_findings = [
            f for f in result.findings
            if f.role_name == "SmallRole"
            and "explosion" in f.finding_type.lower()
        ]
        assert len(explosion_findings) == 0


# ---------------------------------------------------------------------------
# Test: Configurable Threshold
# ---------------------------------------------------------------------------


class TestConfigurableThreshold:
    """Test scenario: Custom menu_item_threshold parameter."""

    def test_lowered_threshold_catches_moderate_roles(self) -> None:
        """With threshold=200, role with 250 items should be flagged."""
        # -- Arrange --
        config_rows = _generate_large_role_config("ModerateRole", 250)
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "ModerateRole", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "ModerateRole")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
            menu_item_threshold=200,
        )

        # -- Assert --
        findings_for_role = [
            f for f in result.findings if f.role_name == "ModerateRole"
        ]
        assert len(findings_for_role) >= 1

    def test_default_threshold_skips_moderate_roles(self) -> None:
        """With default threshold (500), role with 250 items = no finding."""
        # -- Arrange --
        config_rows = _generate_large_role_config("ModerateRole", 250)
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "ModerateRole", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "ModerateRole")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
            # default threshold = 500
        )

        # -- Assert --
        explosion_findings = [
            f for f in result.findings
            if f.role_name == "ModerateRole"
            and "explosion" in f.finding_type.lower()
        ]
        assert len(explosion_findings) == 0


# ---------------------------------------------------------------------------
# Test: Excessive Write/Delete Access (HIGH)
# ---------------------------------------------------------------------------


class TestExcessiveWriteAccess:
    """Test scenario: Role where >80% of permissions are write/delete.

    Roles granting predominantly write/delete access pose higher
    security risk than read-heavy roles.
    """

    def test_high_write_percentage_flagged(self) -> None:
        """Role with >80% write/delete access = EXCESSIVE_WRITE_ACCESS."""
        # -- Arrange --
        config_rows = []
        # 90 write items, 10 read items = 90% write
        for i in range(90):
            config_rows.append(("WriteHeavy", f"Write_{i}", "Write", "Finance", 180))
        for i in range(10):
            config_rows.append(("WriteHeavy", f"Read_{i}", "Read", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "WriteHeavy", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "WriteHeavy")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        write_findings = [
            f for f in result.findings
            if "write" in f.finding_type.lower()
            or "write" in f.description.lower()
        ]
        assert len(write_findings) >= 1
        assert write_findings[0].severity in ("HIGH", "CRITICAL")

    def test_balanced_access_not_flagged(self) -> None:
        """Role with 50/50 read/write should not flag write excess."""
        # -- Arrange --
        config_rows = []
        for i in range(50):
            config_rows.append(("Balanced", f"Write_{i}", "Write", "Finance", 180))
        for i in range(50):
            config_rows.append(("Balanced", f"Read_{i}", "Read", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "Balanced", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "Balanced")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        write_findings = [
            f for f in result.findings
            if "write" in f.finding_type.lower()
            and f.role_name == "Balanced"
        ]
        assert len(write_findings) == 0


# ---------------------------------------------------------------------------
# Test: Cross-Tier Explosion (MEDIUM)
# ---------------------------------------------------------------------------


class TestCrossTierExplosion:
    """Test scenario: Role granting access across 3+ license tiers.

    A single role spanning multiple license tiers indicates poor
    role design and may force users into higher license tiers.
    """

    def test_cross_tier_role_flagged(self) -> None:
        """Role spanning Finance, SCM, and Commerce = cross-tier finding."""
        # -- Arrange --
        config_rows = [
            ("CrossTier", "FinItem_A", "Write", "Finance", 180),
            ("CrossTier", "FinItem_B", "Write", "Finance", 180),
            ("CrossTier", "SCMItem_A", "Write", "SCM", 180),
            ("CrossTier", "SCMItem_B", "Write", "SCM", 180),
            ("CrossTier", "ComItem_A", "Write", "Commerce", 180),
        ]
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "CrossTier", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "CrossTier")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        tier_findings = [
            f for f in result.findings
            if "tier" in f.finding_type.lower()
            or "cross" in f.finding_type.lower()
        ]
        assert len(tier_findings) >= 1
        assert tier_findings[0].severity in ("MEDIUM", "HIGH")

    def test_single_tier_not_flagged(self) -> None:
        """Role within single license tier should not flag cross-tier."""
        # -- Arrange --
        config_rows = [
            ("SingleTier", f"Item_{i}", "Write", "Finance", 180)
            for i in range(10)
        ]
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "SingleTier", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "SingleTier")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        tier_findings = [
            f for f in result.findings
            if "tier" in f.finding_type.lower()
            or "cross" in f.finding_type.lower()
        ]
        assert len(tier_findings) == 0


# ---------------------------------------------------------------------------
# Test: Statistical Outlier (3x org average)
# ---------------------------------------------------------------------------


class TestStatisticalOutlier:
    """Test scenario: Role 3x larger than organizational average."""

    def test_outlier_role_flagged(self) -> None:
        """Role with 300 items when avg is 50 = statistical outlier."""
        # -- Arrange --
        config_rows = []
        # Normal roles: 50 items each
        for i in range(50):
            config_rows.append(("NormalA", f"ItemA_{i}", "Write", "Finance", 180))
        for i in range(50):
            config_rows.append(("NormalB", f"ItemB_{i}", "Write", "Finance", 180))
        # Outlier role: 300 items (6x average of 50)
        for i in range(300):
            config_rows.append(("Outlier", f"ItemO_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "NormalA", "role_type": "Custom"},
                {"role_name": "NormalB", "role_type": "Custom"},
                {"role_name": "Outlier", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR-A", "NormalA"),
                ("USR-B", "NormalB"),
                ("USR-C", "Outlier"),
            ]
        )

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        outlier_findings = [
            f for f in result.findings
            if f.role_name == "Outlier"
            and ("outlier" in f.finding_type.lower()
                 or "average" in f.description.lower())
        ]
        assert len(outlier_findings) >= 1


# ---------------------------------------------------------------------------
# Test: Splitting Recommendations
# ---------------------------------------------------------------------------


class TestSplittingRecommendations:
    """Test scenario: Oversized roles should include splitting guidance."""

    def test_large_role_has_splitting_recommendation(self) -> None:
        """Exploded role should recommend splitting into smaller roles."""
        # -- Arrange --
        config_rows = _generate_large_role_config("SplitMe", 700)
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "SplitMe", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "SplitMe")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        split_findings = [
            f for f in result.findings
            if f.role_name == "SplitMe"
        ]
        assert len(split_findings) >= 1
        assert "split" in split_findings[0].recommendation.lower() or (
            "separate" in split_findings[0].recommendation.lower()
        )


# ---------------------------------------------------------------------------
# Test: Users Affected Count
# ---------------------------------------------------------------------------


class TestUsersAffectedCount:
    """Test scenario: Report number of users affected by explosion."""

    def test_users_affected_populated(self) -> None:
        """Finding should include count of users assigned to the role."""
        # -- Arrange --
        config_rows = _generate_large_role_config("PopularBig", 600)
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "PopularBig", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments(
            [
                ("USR-A", "PopularBig"),
                ("USR-B", "PopularBig"),
                ("USR-C", "PopularBig"),
                ("USR-D", "PopularBig"),
                ("USR-E", "PopularBig"),
            ]
        )

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        findings = [f for f in result.findings if f.role_name == "PopularBig"]
        assert len(findings) >= 1
        assert findings[0].users_affected >= 5


# ---------------------------------------------------------------------------
# Test: Results Sorted by Menu Item Count Descending
# ---------------------------------------------------------------------------


class TestResultsSorted:
    """Test scenario: Findings sorted by menu item count (largest first)."""

    def test_largest_role_first(self) -> None:
        """Roles with most menu items should appear first."""
        # -- Arrange --
        config_rows = (
            _generate_large_role_config("BigRole", 800)
            + _generate_large_role_config("MedRole", 550)
        )
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [
                {"role_name": "BigRole", "role_type": "Custom"},
                {"role_name": "MedRole", "role_type": "Custom"},
            ]
        )
        assignments = _build_user_role_assignments(
            [("USR-A", "BigRole"), ("USR-B", "MedRole")]
        )

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        explosion_findings = [
            f for f in result.findings if "explosion" in f.finding_type.lower()
        ]
        if len(explosion_findings) >= 2:
            assert (
                explosion_findings[0].menu_item_count
                >= explosion_findings[1].menu_item_count
            )


# ---------------------------------------------------------------------------
# Test: Empty Input Handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input data."""

    def test_empty_config_no_findings(self) -> None:
        """Empty security config should produce zero findings."""
        # -- Arrange --
        sec_config = _build_security_config([])
        role_defs = _build_role_definitions([])
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.findings) == 0
        assert result.total_roles_analyzed == 0


# ---------------------------------------------------------------------------
# Test: Summary Statistics
# ---------------------------------------------------------------------------


class TestSummaryStatistics:
    """Test scenario: Result includes summary statistics."""

    def test_summary_populated(self) -> None:
        """Summary should count roles analyzed and findings detected."""
        # -- Arrange --
        config_rows = _generate_large_role_config("TestRole", 100)
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "TestRole", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "TestRole")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert result.total_roles_analyzed >= 1
        assert hasattr(result, "average_menu_item_count")
        assert hasattr(result, "total_findings")


# ---------------------------------------------------------------------------
# Test: Finding Output Model Structure
# ---------------------------------------------------------------------------


class TestFindingModelStructure:
    """Test scenario: Verify finding output model has required fields."""

    def test_finding_has_required_fields(self) -> None:
        """PermissionExplosionFinding should have all required fields."""
        # -- Arrange --
        config_rows = _generate_large_role_config("ModelRole", 600)
        sec_config = _build_security_config(config_rows)
        role_defs = _build_role_definitions(
            [{"role_name": "ModelRole", "role_type": "Custom"}]
        )
        assignments = _build_user_role_assignments([("USR-A", "ModelRole")])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.findings) >= 1
        f = result.findings[0]
        assert hasattr(f, "role_name")
        assert hasattr(f, "finding_type")
        assert hasattr(f, "severity")
        assert hasattr(f, "menu_item_count")
        assert hasattr(f, "users_affected")
        assert hasattr(f, "description")
        assert hasattr(f, "recommendation")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '6.2'."""

    def test_algorithm_id_is_6_2(self) -> None:
        """PermissionExplosionAnalysis should carry algorithm_id '6.2'."""
        # -- Arrange --
        sec_config = _build_security_config([])
        role_defs = _build_role_definitions([])
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = detect_permission_explosions(
            security_config=sec_config,
            role_definitions=role_defs,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert result.algorithm_id == "6.2"
