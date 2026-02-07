"""Algorithm 1.1: Role License Composition Analyzer.

Analyzes security configuration data to determine, for each role, how many
menu items require each license type. Produces a composition breakdown with
counts and percentages, and identifies the highest-cost license type in
each role.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 30-104.

Key behaviors:
  - Count menu items per license type for a given role
  - Calculate percentages of each license type (relative to total_items)
  - Handle combined licenses (Finance + SCM counted in both buckets)
  - Identify the highest license type (by priority/cost from the data)
  - Handle edge cases: empty roles, roles with no menu items
  - Batch processing: analyze multiple roles at once
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------


class LicenseCompositionEntry(BaseModel):
    """Single license type entry within a role's composition breakdown.

    Attributes:
        count: Number of menu items requiring this license type.
        percentage: Percentage of total menu items (0.0-100.0).
    """

    count: int = Field(default=0, description="Number of menu items for this license type", ge=0)
    percentage: float = Field(
        default=0.0,
        description="Percentage of total menu items (0.0-100.0)",
        ge=0.0,
    )


class RoleComposition(BaseModel):
    """Complete license composition analysis for a single security role.

    Output of Algorithm 1.1: Role License Composition Analyzer.
    See Requirements/06-Algorithms-Decision-Logic.md, lines 30-104.

    Attributes:
        algorithm_id: Always '1.1' for this algorithm.
        role_name: Name of the security role analyzed.
        total_items: Total number of menu items in the role.
        license_composition: Breakdown by license type (count + percentage).
        highest_license: License type with the highest priority/cost,
            or 'None' if the role has zero menu items.
    """

    algorithm_id: str = Field(default="1.1", description="Algorithm identifier")
    role_name: str = Field(description="Security role name")
    total_items: int = Field(description="Total menu items in role", ge=0)
    license_composition: dict[str, LicenseCompositionEntry] = Field(
        description="Composition breakdown by license type"
    )
    highest_license: str = Field(
        description="Highest-cost license type required, or 'None' if empty role"
    )


# ---------------------------------------------------------------------------
# Standard license types that should always appear in the composition
# ---------------------------------------------------------------------------

_STANDARD_LICENSE_TYPES: list[str] = [
    "Commerce",
    "Finance",
    "SCM",
    "Operations - Activity",
    "Team Members",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_role_composition(
    security_config: pd.DataFrame,
    role_name: str,
    pricing_config: dict[str, Any],
) -> RoleComposition:
    """Analyze the license composition of a single security role.

    Implements Algorithm 1.1 from Requirements/06-Algorithms-Decision-Logic.md,
    lines 30-104. Counts menu items per license type, calculates percentage
    breakdown, and identifies the highest-cost license required.

    Combined licenses (e.g., 'Finance + SCM') are double-counted: the item
    is counted in both the Finance and SCM buckets. The total_items field
    reflects the actual number of distinct menu items (not the sum of
    per-bucket counts).

    Args:
        security_config: DataFrame with columns: securityrole, AOTName,
            AccessLevel, LicenseType, Priority, Entitled, NotEntitled,
            securitytype.
        role_name: Name of the security role to analyze.
        pricing_config: Parsed pricing.json dictionary (used for future
            extensibility; priority is read from the security config data).

    Returns:
        RoleComposition with full breakdown and highest license identification.
    """
    # Filter rows for the requested role
    role_mask: pd.Series = security_config["securityrole"] == role_name  # type: ignore[assignment]
    role_data: pd.DataFrame = security_config[role_mask]

    total_items: int = len(role_data)

    # Initialize counts for all standard license types
    license_counts: dict[str, int] = {lt: 0 for lt in _STANDARD_LICENSE_TYPES}

    # Track the highest priority seen and its associated license type
    highest_priority: int = -1
    highest_license: str = "None"

    if total_items > 0:
        # Vectorized: extract license types and priorities
        license_types: pd.Series = role_data["LicenseType"]  # type: ignore[assignment]
        priorities: pd.Series = role_data["Priority"]  # type: ignore[assignment]

        # Process each row for combined license detection and counting
        for license_type, priority in zip(license_types, priorities):
            lt_str: str = str(license_type)
            pri: int = int(priority)

            # Handle combined licenses: "Finance + SCM" -> count in both
            if "Finance" in lt_str and "SCM" in lt_str:
                license_counts["Finance"] = license_counts.get("Finance", 0) + 1
                license_counts["SCM"] = license_counts.get("SCM", 0) + 1
                # Both Finance and SCM share the same priority (180),
                # so track with either
                if pri > highest_priority:
                    highest_priority = pri
                    highest_license = "Finance"
            else:
                license_counts[lt_str] = license_counts.get(lt_str, 0) + 1
                if pri > highest_priority:
                    highest_priority = pri
                    highest_license = lt_str

    # Build composition entries with percentages
    composition: dict[str, LicenseCompositionEntry] = {}
    for lt, count in license_counts.items():
        pct: float = (count / total_items * 100.0) if total_items > 0 else 0.0
        composition[lt] = LicenseCompositionEntry(count=count, percentage=pct)

    return RoleComposition(
        algorithm_id="1.1",
        role_name=role_name,
        total_items=total_items,
        license_composition=composition,
        highest_license=highest_license,
    )


def analyze_roles_batch(
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
    role_names: list[str] | None = None,
) -> list[RoleComposition]:
    """Analyze license composition for multiple roles in batch.

    When role_names is None, discovers and analyzes ALL unique roles present
    in the security configuration data.

    Args:
        security_config: DataFrame with security configuration data.
        pricing_config: Parsed pricing.json dictionary.
        role_names: List of role names to analyze. If None, all unique
            roles in security_config are discovered and analyzed.

    Returns:
        List of RoleComposition results, one per role.
    """
    if role_names is None:
        role_names = sorted(security_config["securityrole"].unique().tolist())

    results: list[RoleComposition] = []
    for name in role_names:
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name=name,
            pricing_config=pricing_config,
        )
        results.append(result)

    return results
