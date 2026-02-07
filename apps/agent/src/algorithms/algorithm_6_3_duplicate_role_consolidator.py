"""Algorithm 6.3: Duplicate Role Consolidator.

Finds similar custom roles that could be consolidated to reduce role management
overhead and simplify the security model. For example, roles like "Accountant",
"Accountant II", and "Senior Accountant" may share 90%+ menu items and could
be merged into a single role with minor adjustments.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1394-1420
(Algorithm 6.3: Duplicate Role Consolidator).

Algorithm:
  For each pair of custom roles:
    1. Calculate menu item overlap percentage (Jaccard similarity)
    2. If overlap > threshold (default 80%), flag for consolidation
    3. Calculate impact (users affected, unique menu items per role)
    4. Generate merge recommendation

Key behaviours:
  - Only custom roles are compared (standard/system roles excluded)
  - Each role pair is reported exactly once (A+B == B+A)
  - Results are sorted by overlap percentage descending
  - Empty input returns zero results without errors

Author: D365 FO License Agent
Created: 2026-02-06
"""

from __future__ import annotations

from itertools import combinations
from typing import List

import pandas as pd
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class DuplicateRolePair(BaseModel):
    """A pair of custom roles with high menu-item overlap.

    Attributes:
        role_a: Name of the first role in the pair.
        role_b: Name of the second role in the pair.
        overlap_percentage: Jaccard similarity of menu-item sets (0-100).
        shared_menu_items: Menu items present in both roles.
        unique_to_role_a: Menu items only in role_a.
        unique_to_role_b: Menu items only in role_b.
        users_affected: Total distinct users assigned to either role.
        recommendation: Human-readable consolidation recommendation.
    """

    role_a: str = Field(description="First role name in the pair")
    role_b: str = Field(description="Second role name in the pair")
    overlap_percentage: float = Field(
        description="Overlap coefficient percentage (intersection / min size * 100)"
    )
    shared_menu_items: List[str] = Field(
        default_factory=list,
        description="Menu items present in both roles",
    )
    unique_to_role_a: List[str] = Field(
        default_factory=list,
        description="Menu items only in role A",
    )
    unique_to_role_b: List[str] = Field(
        default_factory=list,
        description="Menu items only in role B",
    )
    users_affected: int = Field(
        default=0,
        description="Total distinct users assigned to either role",
    )
    recommendation: str = Field(
        default="",
        description="Human-readable consolidation recommendation",
    )


class DuplicateRoleAnalysis(BaseModel):
    """Top-level result for Algorithm 6.3.

    Attributes:
        algorithm_id: Always '6.3'.
        total_roles_analyzed: Number of custom roles examined.
        duplicate_pair_count: Number of pairs exceeding overlap threshold.
        duplicate_pairs: Detailed pair analysis, sorted by overlap descending.
    """

    algorithm_id: str = Field(default="6.3", description="Algorithm identifier")
    total_roles_analyzed: int = Field(
        default=0,
        description="Number of custom roles examined",
    )
    duplicate_pair_count: int = Field(
        default=0,
        description="Number of pairs exceeding the overlap threshold",
    )
    duplicate_pairs: List[DuplicateRolePair] = Field(
        default_factory=list,
        description="Duplicate role pair details sorted by overlap descending",
    )


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------


def detect_duplicate_roles(
    security_config: pd.DataFrame,
    role_definitions: pd.DataFrame,
    user_role_assignments: pd.DataFrame,
    overlap_threshold: float = 80.0,
) -> DuplicateRoleAnalysis:
    """Detect custom roles with high menu-item overlap for consolidation.

    Algorithm 6.3 compares every pair of *custom* roles and calculates the
    Jaccard similarity of their menu-item sets.  Pairs whose overlap exceeds
    ``overlap_threshold`` are flagged with a consolidation recommendation.

    See Requirements/07-Advanced-Algorithms-Expansion.md (Algorithm 6.3).

    Args:
        security_config: DataFrame with at least columns ``securityrole`` and
            ``AOTName`` (menu item identifier).
        role_definitions: DataFrame with columns ``role_name`` and
            ``role_type`` (``'Custom'`` or ``'Standard'``).
        user_role_assignments: DataFrame with columns ``user_id`` and
            ``role_name``.
        overlap_threshold: Minimum Jaccard similarity percentage (0-100) to
            flag a pair.  Default 80.0.

    Returns:
        DuplicateRoleAnalysis with pairs sorted by overlap descending.
    """
    # ------------------------------------------------------------------
    # 1. Identify custom roles
    # ------------------------------------------------------------------
    if role_definitions.empty or security_config.empty:
        return DuplicateRoleAnalysis(
            algorithm_id="6.3",
            total_roles_analyzed=0,
            duplicate_pair_count=0,
            duplicate_pairs=[],
        )

    custom_roles: set[str] = set(
        role_definitions.loc[
            role_definitions["role_type"] == "Custom", "role_name"
        ].tolist()
    )

    if len(custom_roles) < 2:
        return DuplicateRoleAnalysis(
            algorithm_id="6.3",
            total_roles_analyzed=len(custom_roles),
            duplicate_pair_count=0,
            duplicate_pairs=[],
        )

    # ------------------------------------------------------------------
    # 2. Build menu-item sets per custom role  (O(N) single pass)
    # ------------------------------------------------------------------
    role_menu_items: dict[str, set[str]] = {}
    for role_name, group in security_config.groupby("securityrole"):
        if role_name in custom_roles:
            role_menu_items[str(role_name)] = set(group["AOTName"].tolist())

    # Only consider custom roles that actually appear in security config
    analysed_roles = sorted(role_menu_items.keys())
    total_roles_analyzed = len(analysed_roles)

    if total_roles_analyzed < 2:
        return DuplicateRoleAnalysis(
            algorithm_id="6.3",
            total_roles_analyzed=total_roles_analyzed,
            duplicate_pair_count=0,
            duplicate_pairs=[],
        )

    # ------------------------------------------------------------------
    # 3. Build user-count lookup per role  (O(M) single pass)
    # ------------------------------------------------------------------
    role_user_sets: dict[str, set[str]] = {}
    if not user_role_assignments.empty:
        for role_name, group in user_role_assignments.groupby("role_name"):
            role_name_str = str(role_name)
            if role_name_str in role_menu_items:
                role_user_sets[role_name_str] = set(group["user_id"].tolist())

    # ------------------------------------------------------------------
    # 4. Pairwise comparison (only upper triangle, avoiding duplicates)
    # ------------------------------------------------------------------
    pairs: list[DuplicateRolePair] = []

    for role_a, role_b in combinations(analysed_roles, 2):
        items_a = role_menu_items[role_a]
        items_b = role_menu_items[role_b]

        intersection = items_a & items_b
        union = items_a | items_b
        min_size = min(len(items_a), len(items_b))

        if min_size == 0:
            continue

        # Overlap coefficient: intersection / min(|A|, |B|) * 100
        # This measures how much the smaller role is contained in the larger.
        overlap_pct = (len(intersection) / min_size) * 100.0

        if overlap_pct < overlap_threshold:
            continue

        unique_a = sorted(items_a - items_b)
        unique_b = sorted(items_b - items_a)
        shared = sorted(intersection)

        # Users affected = distinct users in either role
        users_a = role_user_sets.get(role_a, set())
        users_b = role_user_sets.get(role_b, set())
        users_affected = len(users_a | users_b)

        # Build recommendation
        recommendation = _build_recommendation(
            role_a=role_a,
            role_b=role_b,
            overlap_pct=overlap_pct,
            shared_count=len(shared),
            union_count=len(union),
            unique_a=unique_a,
            unique_b=unique_b,
            users_affected=users_affected,
        )

        pairs.append(
            DuplicateRolePair(
                role_a=role_a,
                role_b=role_b,
                overlap_percentage=round(overlap_pct, 2),
                shared_menu_items=shared,
                unique_to_role_a=unique_a,
                unique_to_role_b=unique_b,
                users_affected=users_affected,
                recommendation=recommendation,
            )
        )

    # ------------------------------------------------------------------
    # 5. Sort by overlap descending
    # ------------------------------------------------------------------
    pairs.sort(key=lambda p: p.overlap_percentage, reverse=True)

    return DuplicateRoleAnalysis(
        algorithm_id="6.3",
        total_roles_analyzed=total_roles_analyzed,
        duplicate_pair_count=len(pairs),
        duplicate_pairs=pairs,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_recommendation(
    role_a: str,
    role_b: str,
    overlap_pct: float,
    shared_count: int,
    union_count: int,
    unique_a: list[str],
    unique_b: list[str],
    users_affected: int,
) -> str:
    """Generate a human-readable consolidation recommendation.

    Args:
        role_a: First role name.
        role_b: Second role name.
        overlap_pct: Jaccard similarity percentage.
        shared_count: Number of shared menu items.
        union_count: Total distinct menu items across both roles.
        unique_a: Menu items unique to role_a.
        unique_b: Menu items unique to role_b.
        users_affected: Total distinct users in either role.

    Returns:
        Recommendation string describing the consolidation action.
    """
    unique_total = len(unique_a) + len(unique_b)

    if overlap_pct >= 99.9:
        action = (
            f"Merge '{role_a}' and '{role_b}' into a single role. "
            f"The roles are functionally identical ({shared_count}/{union_count} menu items). "
        )
    elif unique_total <= 3:
        action = (
            f"Merge '{role_a}' and '{role_b}' into a single role and add the "
            f"{unique_total} unique menu item(s) to cover both. "
        )
    else:
        action = (
            f"Consolidate '{role_a}' and '{role_b}' "
            f"({overlap_pct:.1f}% overlap, {shared_count}/{union_count} menu items). "
            f"Create one merged role and a supplementary duty for the "
            f"{unique_total} differing menu item(s). "
        )

    if users_affected > 0:
        action += f"{users_affected} user(s) affected; reassignment required. "

    action += "Reduces role count by 1 and simplifies maintenance."

    return action
