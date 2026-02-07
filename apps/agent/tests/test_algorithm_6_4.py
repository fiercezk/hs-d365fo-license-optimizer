"""Tests for Algorithm 6.4: Role Hierarchy Optimizer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_6_4_role_hierarchy_optimizer.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md
(Algorithm 6.4: Role Hierarchy Optimizer).
Category: Role Management.

Algorithm 6.4 optimizes role inheritance hierarchies by analyzing the
role structure and recommending improvements:
  - Analyze existing role inheritance relationships (parent-child)
  - Detect deep nesting (>3 levels) causing complexity
  - Identify orphaned branches (inherited roles with no users)
  - Detect circular dependencies in role hierarchy
  - Find common permission subsets that could be extracted into base roles
  - Identify roles with redundant inheritance (child grants same as parent)
  - Calculate hierarchy complexity score
  - Generate flattening and restructuring recommendations
  - Estimate maintenance effort reduction from optimization

Key behaviors:
  - Circular dependency in hierarchy = CRITICAL finding
  - Deep nesting (>3 levels) = HIGH risk (complexity)
  - Redundant inheritance (child re-declares parent permissions) = MEDIUM
  - Orphaned branch (no users assigned) = LOW
  - Common subset (3+ roles share 5+ permissions) = MEDIUM (extract base role)
  - Flat/simple hierarchy = no finding
  - Empty input = zero findings, no errors
  - Results sorted by finding severity then complexity score
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.algorithms.algorithm_6_4_role_hierarchy_optimizer import (
    HierarchyAnalysis,
    optimize_role_hierarchy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_role_hierarchy(
    relationships: list[tuple[str, str]],
) -> pd.DataFrame:
    """Build synthetic role hierarchy DataFrame.

    Args:
        relationships: List of (parent_role, child_role) tuples.
            Represents role inheritance: child inherits from parent.
    """
    records: list[dict[str, str]] = []
    for parent, child in relationships:
        records.append(
            {
                "parent_role": parent,
                "child_role": child,
            }
        )
    return pd.DataFrame(records)


def _build_role_definitions(
    roles: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic role definitions DataFrame.

    Args:
        roles: List of dicts with keys: role_name, role_type.
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


def _build_security_config(
    rows: list[tuple[str, str, str, str, int]],
) -> pd.DataFrame:
    """Build synthetic security configuration DataFrame.

    Args:
        rows: List of (securityrole, AOTName, AccessLevel, LicenseType, Priority)
            tuples.
    """
    records: list[dict[str, str | int]] = []
    for role, aot, access, license_type, priority in rows:
        records.append(
            {
                "securityrole": role,
                "AOTName": aot,
                "AccessLevel": access,
                "LicenseType": license_type,
                "Priority": priority,
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


# ---------------------------------------------------------------------------
# Test: Circular Dependency Detection (CRITICAL)
# ---------------------------------------------------------------------------


class TestCircularDependency:
    """Test scenario: Role hierarchy contains circular inheritance.

    Circular dependencies (A -> B -> C -> A) break the inheritance model
    and must be resolved immediately.
    """

    def test_circular_dependency_detected(self) -> None:
        """A -> B -> C -> A circular chain = CRITICAL finding."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [
                ("RoleA", "RoleB"),
                ("RoleB", "RoleC"),
                ("RoleC", "RoleA"),  # Circular!
            ]
        )
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleA", "role_type": "Custom"},
                {"role_name": "RoleB", "role_type": "Custom"},
                {"role_name": "RoleC", "role_type": "Custom"},
            ]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments(
            [("USR-A", "RoleA")]
        )

        # -- Act --
        result: HierarchyAnalysis = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        circular_findings = [
            f for f in result.findings
            if "circular" in f.finding_type.lower()
            or "cycle" in f.finding_type.lower()
        ]
        assert len(circular_findings) >= 1
        assert circular_findings[0].severity == "CRITICAL"

    def test_self_reference_detected(self) -> None:
        """Role inheriting from itself = circular dependency."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [("RoleSelf", "RoleSelf")]
        )
        role_defs = _build_role_definitions(
            [{"role_name": "RoleSelf", "role_type": "Custom"}]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        circular = [
            f for f in result.findings
            if "circular" in f.finding_type.lower()
            or "self" in f.finding_type.lower()
        ]
        assert len(circular) >= 1


# ---------------------------------------------------------------------------
# Test: Deep Nesting Detection (HIGH)
# ---------------------------------------------------------------------------


class TestDeepNesting:
    """Test scenario: Role hierarchy exceeds 3 levels of nesting.

    Deep nesting makes permissions hard to understand and audit.
    """

    def test_deep_nesting_flagged(self) -> None:
        """Hierarchy with 5 levels of nesting = HIGH risk finding."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [
                ("Level1", "Level2"),
                ("Level2", "Level3"),
                ("Level3", "Level4"),
                ("Level4", "Level5"),
            ]
        )
        role_defs = _build_role_definitions(
            [
                {"role_name": f"Level{i}", "role_type": "Custom"}
                for i in range(1, 6)
            ]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments(
            [("USR-A", "Level5")]
        )

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        nesting_findings = [
            f for f in result.findings
            if "nest" in f.finding_type.lower()
            or "depth" in f.finding_type.lower()
            or "deep" in f.description.lower()
        ]
        assert len(nesting_findings) >= 1
        assert nesting_findings[0].severity in ("HIGH", "CRITICAL")

    def test_shallow_hierarchy_not_flagged(self) -> None:
        """Hierarchy with 2 levels should not flag nesting."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [("Parent", "Child")]
        )
        role_defs = _build_role_definitions(
            [
                {"role_name": "Parent", "role_type": "Custom"},
                {"role_name": "Child", "role_type": "Custom"},
            ]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments(
            [("USR-A", "Child")]
        )

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        nesting_findings = [
            f for f in result.findings
            if "nest" in f.finding_type.lower()
            or "depth" in f.finding_type.lower()
        ]
        assert len(nesting_findings) == 0


# ---------------------------------------------------------------------------
# Test: Redundant Inheritance Detection (MEDIUM)
# ---------------------------------------------------------------------------


class TestRedundantInheritance:
    """Test scenario: Child role re-declares same permissions as parent.

    If child has same menu items as parent through direct assignment
    (not just inheritance), the inheritance is redundant.
    """

    def test_redundant_inheritance_flagged(self) -> None:
        """Child duplicating parent's permissions = redundant inheritance."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [("BaseRole", "DerivedRole")]
        )
        role_defs = _build_role_definitions(
            [
                {"role_name": "BaseRole", "role_type": "Custom"},
                {"role_name": "DerivedRole", "role_type": "Custom"},
            ]
        )
        # Both roles have the same menu items
        sec_config = _build_security_config(
            [
                ("BaseRole", "ItemA", "Write", "Finance", 180),
                ("BaseRole", "ItemB", "Write", "Finance", 180),
                ("DerivedRole", "ItemA", "Write", "Finance", 180),
                ("DerivedRole", "ItemB", "Write", "Finance", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [("USR-A", "DerivedRole")]
        )

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        redundant_findings = [
            f for f in result.findings
            if "redundant" in f.finding_type.lower()
            or "duplicate" in f.finding_type.lower()
        ]
        assert len(redundant_findings) >= 1
        assert redundant_findings[0].severity in ("MEDIUM", "LOW")


# ---------------------------------------------------------------------------
# Test: Orphaned Branch Detection (LOW)
# ---------------------------------------------------------------------------


class TestOrphanedBranch:
    """Test scenario: Branch in hierarchy with no users assigned.

    Orphaned branches add complexity without providing value.
    """

    def test_orphaned_branch_flagged(self) -> None:
        """Hierarchy branch with zero users = orphaned branch finding."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [
                ("Root", "ActiveBranch"),
                ("Root", "OrphanBranch"),
                ("OrphanBranch", "OrphanChild"),
            ]
        )
        role_defs = _build_role_definitions(
            [
                {"role_name": "Root", "role_type": "Custom"},
                {"role_name": "ActiveBranch", "role_type": "Custom"},
                {"role_name": "OrphanBranch", "role_type": "Custom"},
                {"role_name": "OrphanChild", "role_type": "Custom"},
            ]
        )
        sec_config = _build_security_config([])
        # Only ActiveBranch has users
        assignments = _build_user_role_assignments(
            [("USR-A", "ActiveBranch")]
        )

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        orphan_findings = [
            f for f in result.findings
            if "orphan" in f.finding_type.lower()
            or "unused" in f.finding_type.lower()
        ]
        assert len(orphan_findings) >= 1


# ---------------------------------------------------------------------------
# Test: Common Permission Subset Extraction (MEDIUM)
# ---------------------------------------------------------------------------


class TestCommonSubsetExtraction:
    """Test scenario: Multiple roles share a common set of permissions.

    When 3+ roles share 5+ permissions, extract into a base role.
    """

    def test_common_subset_detected(self) -> None:
        """3 roles sharing 5+ permissions = suggest base role extraction."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy([])  # No hierarchy yet
        role_defs = _build_role_definitions(
            [
                {"role_name": "RoleX", "role_type": "Custom"},
                {"role_name": "RoleY", "role_type": "Custom"},
                {"role_name": "RoleZ", "role_type": "Custom"},
            ]
        )
        # All 3 roles share 6 common items
        shared_items = [f"Shared_{i}" for i in range(6)]
        config_rows = []
        for role in ["RoleX", "RoleY", "RoleZ"]:
            for item in shared_items:
                config_rows.append((role, item, "Write", "Finance", 180))
            # Each also has 3 unique items
            for i in range(3):
                config_rows.append((role, f"Unique_{role}_{i}", "Write", "Finance", 180))

        sec_config = _build_security_config(config_rows)
        assignments = _build_user_role_assignments(
            [
                ("USR-A", "RoleX"),
                ("USR-B", "RoleY"),
                ("USR-C", "RoleZ"),
            ]
        )

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        subset_findings = [
            f for f in result.findings
            if "common" in f.finding_type.lower()
            or "subset" in f.finding_type.lower()
            or "base" in f.finding_type.lower()
            or "extract" in f.description.lower()
        ]
        assert len(subset_findings) >= 1


# ---------------------------------------------------------------------------
# Test: Flat/Simple Hierarchy (No Findings)
# ---------------------------------------------------------------------------


class TestFlatHierarchyNoFindings:
    """Test scenario: Simple hierarchy with no issues."""

    def test_simple_hierarchy_no_critical_findings(self) -> None:
        """Simple 2-level hierarchy with users = no CRITICAL/HIGH findings."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [("Base", "Extended")]
        )
        role_defs = _build_role_definitions(
            [
                {"role_name": "Base", "role_type": "Custom"},
                {"role_name": "Extended", "role_type": "Custom"},
            ]
        )
        sec_config = _build_security_config(
            [
                ("Base", "ItemA", "Read", "Finance", 180),
                ("Extended", "ItemA", "Write", "Finance", 180),
                ("Extended", "ItemB", "Write", "Finance", 180),
            ]
        )
        assignments = _build_user_role_assignments(
            [("USR-A", "Base"), ("USR-B", "Extended")]
        )

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        critical_findings = [
            f for f in result.findings if f.severity in ("CRITICAL", "HIGH")
        ]
        assert len(critical_findings) == 0


# ---------------------------------------------------------------------------
# Test: Hierarchy Complexity Score
# ---------------------------------------------------------------------------


class TestComplexityScore:
    """Test scenario: Calculate hierarchy complexity metric."""

    def test_complexity_score_populated(self) -> None:
        """Analysis should include overall hierarchy complexity score."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [
                ("A", "B"),
                ("B", "C"),
                ("B", "D"),
                ("A", "E"),
            ]
        )
        role_defs = _build_role_definitions(
            [{"role_name": r, "role_type": "Custom"} for r in "ABCDE"]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments(
            [("USR-A", "C"), ("USR-B", "D")]
        )

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert hasattr(result, "complexity_score")
        assert result.complexity_score >= 0

    def test_more_complex_hierarchy_higher_score(self) -> None:
        """Deeper/wider hierarchy should have higher complexity score."""
        # -- Arrange --
        simple_hierarchy = _build_role_hierarchy(
            [("P", "C")]
        )
        complex_hierarchy = _build_role_hierarchy(
            [
                ("L1", "L2a"), ("L1", "L2b"),
                ("L2a", "L3a"), ("L2a", "L3b"),
                ("L2b", "L3c"), ("L2b", "L3d"),
                ("L3a", "L4a"),
            ]
        )

        simple_defs = _build_role_definitions(
            [{"role_name": r, "role_type": "Custom"} for r in ["P", "C"]]
        )
        complex_defs = _build_role_definitions(
            [
                {"role_name": r, "role_type": "Custom"}
                for r in ["L1", "L2a", "L2b", "L3a", "L3b", "L3c", "L3d", "L4a"]
            ]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([])

        # -- Act --
        simple_result = optimize_role_hierarchy(
            role_hierarchy=simple_hierarchy,
            role_definitions=simple_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )
        complex_result = optimize_role_hierarchy(
            role_hierarchy=complex_hierarchy,
            role_definitions=complex_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert complex_result.complexity_score > simple_result.complexity_score


# ---------------------------------------------------------------------------
# Test: Flattening Recommendations
# ---------------------------------------------------------------------------


class TestFlatteningRecommendations:
    """Test scenario: Deep hierarchies should recommend flattening."""

    def test_deep_hierarchy_recommends_flattening(self) -> None:
        """Deep hierarchy should include flattening recommendation."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [
                ("L1", "L2"),
                ("L2", "L3"),
                ("L3", "L4"),
                ("L4", "L5"),
            ]
        )
        role_defs = _build_role_definitions(
            [{"role_name": f"L{i}", "role_type": "Custom"} for i in range(1, 6)]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([("USR-A", "L5")])

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        has_flatten_recommendation = any(
            "flatten" in f.recommendation.lower()
            or "simplif" in f.recommendation.lower()
            or "reduc" in f.recommendation.lower()
            for f in result.findings
        )
        assert has_flatten_recommendation


# ---------------------------------------------------------------------------
# Test: Empty Input Handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input data."""

    def test_empty_hierarchy_no_findings(self) -> None:
        """Empty hierarchy should produce zero findings."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy([])
        role_defs = _build_role_definitions([])
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
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
        """Summary should count roles, relationships, and max depth."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [("A", "B"), ("B", "C")]
        )
        role_defs = _build_role_definitions(
            [{"role_name": r, "role_type": "Custom"} for r in "ABC"]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([("USR-A", "C")])

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert result.total_roles_analyzed >= 3
        assert hasattr(result, "max_depth")
        assert hasattr(result, "total_inheritance_relationships")
        assert hasattr(result, "total_findings")


# ---------------------------------------------------------------------------
# Test: Finding Output Model Structure
# ---------------------------------------------------------------------------


class TestFindingModelStructure:
    """Test scenario: Verify finding output model has required fields."""

    def test_finding_has_required_fields(self) -> None:
        """HierarchyFinding should have all spec-required fields."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy(
            [
                ("L1", "L2"),
                ("L2", "L3"),
                ("L3", "L4"),
                ("L4", "L5"),
            ]
        )
        role_defs = _build_role_definitions(
            [{"role_name": f"L{i}", "role_type": "Custom"} for i in range(1, 6)]
        )
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([("USR-A", "L5")])

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert len(result.findings) >= 1
        f = result.findings[0]
        assert hasattr(f, "finding_type")
        assert hasattr(f, "severity")
        assert hasattr(f, "description")
        assert hasattr(f, "recommendation")
        assert hasattr(f, "affected_roles")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '6.4'."""

    def test_algorithm_id_is_6_4(self) -> None:
        """HierarchyAnalysis should carry algorithm_id '6.4'."""
        # -- Arrange --
        hierarchy = _build_role_hierarchy([])
        role_defs = _build_role_definitions([])
        sec_config = _build_security_config([])
        assignments = _build_user_role_assignments([])

        # -- Act --
        result = optimize_role_hierarchy(
            role_hierarchy=hierarchy,
            role_definitions=role_defs,
            security_config=sec_config,
            user_role_assignments=assignments,
        )

        # -- Assert --
        assert result.algorithm_id == "6.4"
