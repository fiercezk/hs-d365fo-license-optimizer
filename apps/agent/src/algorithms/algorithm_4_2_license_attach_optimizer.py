"""Algorithm 4.2: License Attach Optimizer.

Optimizes license assignments using attach licenses (base + attach) vs.
multiple full licenses. Users with multiple license types can save 10-25%
or more by using an attach model instead of stacking full licenses.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1119-1258
(Algorithm 4.2: License Attach Optimizer).

Key logic:
  1. Identify users with multiple full license types via role-to-license mapping
  2. For each multi-license user, try every combination of base + attach
  3. Check attach license availability per license type
  4. Select the combination with lowest total cost (optimal base license)
  5. Calculate savings per user and aggregate totals
  6. Skip users with only 1 license type (no attach opportunity)
  7. Sort results by monthly savings descending

Attach pricing (from Requirements/07 sample table):
  - Finance: $180 full, no attach variant (base only)
  - SCM: $180 full, $30 attach
  - Commerce: $180 full, $30 attach
  - Operations: $90 full, no attach variant
  - Team Members: $60 full, no attach variant
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from ..utils.pricing import get_license_price


# ---------------------------------------------------------------------------
# Attach pricing lookup
# ---------------------------------------------------------------------------

# License types that have attach variants and their monthly attach price.
# From Requirements/07, Algorithm 4.2 sample licensing table:
#   SCM attach: $30, Commerce attach: $30.
# Finance, Operations, Team Members do NOT have attach variants.
_ATTACH_PRICES: dict[str, float] = {
    "SCM": 30.0,
    "Commerce": 30.0,
}


def _has_attach_variant(license_type: str) -> bool:
    """Check whether a license type has an attach variant available.

    Args:
        license_type: Normalized license type name (e.g., "SCM", "Commerce").

    Returns:
        True if an attach variant exists for this license type.
    """
    return license_type in _ATTACH_PRICES


def _get_attach_price(license_type: str) -> float:
    """Get the monthly attach price for a license type.

    Args:
        license_type: Normalized license type name with a known attach variant.

    Returns:
        Monthly attach price in USD.

    Raises:
        KeyError: If the license type has no attach variant.
    """
    if license_type not in _ATTACH_PRICES:
        raise KeyError(
            f"License type '{license_type}' has no attach variant. "
            f"Attach-eligible types: {list(_ATTACH_PRICES.keys())}"
        )
    return _ATTACH_PRICES[license_type]


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class AttachOptimization(BaseModel):
    """Single user's attach license optimization result.

    Represents the analysis of one user who holds multiple license types,
    showing the optimal base+attach configuration and resulting savings.
    """

    user_id: str = Field(description="User identifier")
    user_name: str | None = Field(default=None, description="User display name")
    current_licenses: list[str] = Field(
        description="Current full license types held by the user"
    )
    current_cost_per_month: float = Field(
        description="Sum of current full license costs per month (USD)", ge=0
    )
    optimized_base_license: str | None = Field(
        default=None,
        description="Recommended base license in attach model",
    )
    optimized_attach_licenses: list[str] = Field(
        default_factory=list,
        description="Recommended attach licenses in attach model",
    )
    optimized_cost_per_month: float = Field(
        description="Total cost under optimized attach model (USD)", ge=0
    )
    monthly_savings: float = Field(
        description="Monthly savings from switching to attach model (USD)", ge=0
    )
    savings_percentage: float = Field(
        description="Savings as percentage of current cost", ge=0
    )
    feasibility: str = Field(
        description="FEASIBLE if attach model possible, NOT_FEASIBLE otherwise"
    )
    recommendation: str = Field(
        default="Switch to base+attach model",
        description="Human-readable recommendation text",
    )


class AttachOptimizationResult(BaseModel):
    """Aggregate result from the License Attach Optimizer (Algorithm 4.2).

    Contains per-user optimizations and summary statistics.
    """

    algorithm_id: str = Field(default="4.2", description="Algorithm identifier")
    optimizations: list[AttachOptimization] = Field(
        default_factory=list,
        description="Per-user attach optimization results (sorted by savings desc)",
    )
    total_monthly_savings: float = Field(
        default=0.0,
        description="Sum of monthly savings across all feasible optimizations (USD)",
        ge=0,
    )
    total_annual_savings: float = Field(
        default=0.0,
        description="Total annual savings (monthly * 12) (USD)",
        ge=0,
    )
    total_users_analyzed: int = Field(
        default=0,
        description="Total number of users evaluated (including single-license users)",
        ge=0,
    )
    feasible_optimizations_count: int = Field(
        default=0,
        description="Number of users with feasible attach optimizations",
        ge=0,
    )


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------


def _resolve_user_license_types(
    user_id: str,
    user_role_assignments: pd.DataFrame,
    security_config: pd.DataFrame,
) -> list[str]:
    """Determine the distinct license types required by a user's roles.

    Joins user-role assignments with the security configuration to map
    each role to its required license type, then deduplicates.

    Args:
        user_id: Target user identifier.
        user_role_assignments: DataFrame with at least ``user_id`` and
            ``role_name`` columns.
        security_config: DataFrame with at least ``securityrole`` and
            ``LicenseType`` columns.

    Returns:
        Sorted list of unique license type strings (e.g., ["Finance", "SCM"]).
    """
    user_roles = user_role_assignments.loc[
        user_role_assignments["user_id"] == user_id, "role_name"
    ]
    if user_roles.empty:
        return []

    role_names: set[str] = set(user_roles.tolist())

    # Map roles to license types via security config
    role_license_rows = security_config[
        security_config["securityrole"].isin(role_names)
    ]
    if role_license_rows.empty:
        return []

    license_types: list[str] = sorted(
        role_license_rows["LicenseType"].unique().tolist()
    )
    return license_types


def _find_optimal_attach_combo(
    license_types: list[str],
    pricing_config: dict[str, Any],
) -> tuple[str | None, list[str], float, bool]:
    """Try every base+attach combination and return the cheapest feasible one.

    For each license type as the candidate base, the remaining types are
    checked for attach availability. If all remaining types have attach
    variants, the combo is feasible and its total cost is computed. The
    cheapest feasible combo wins.

    Args:
        license_types: List of distinct license types the user requires.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        Tuple of (base_license, attach_licenses, total_cost, is_feasible).
        If no feasible combo exists, returns (None, [], 0.0, False).
    """
    best_base: str | None = None
    best_attaches: list[str] = []
    best_cost: float = float("inf")
    any_feasible: bool = False

    for candidate_base in license_types:
        try:
            base_cost = get_license_price(pricing_config, candidate_base)
        except KeyError:
            continue

        attach_cost = 0.0
        feasible = True
        attach_list: list[str] = []

        for other in license_types:
            if other == candidate_base:
                continue
            if _has_attach_variant(other):
                attach_cost += _get_attach_price(other)
                attach_list.append(other)
            else:
                feasible = False
                break

        if feasible:
            total = base_cost + attach_cost
            any_feasible = True
            if total < best_cost:
                best_cost = total
                best_base = candidate_base
                best_attaches = attach_list

    if not any_feasible:
        return None, [], 0.0, False

    return best_base, best_attaches, best_cost, True


def optimize_license_attach(
    user_role_assignments: pd.DataFrame,
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> AttachOptimizationResult:
    """Algorithm 4.2: License Attach Optimizer.

    Analyzes users with multiple license types and determines whether
    switching from stacked full licenses to a base+attach model yields
    cost savings.

    See Requirements/07-Advanced-Algorithms-Expansion.md, Algorithm 4.2
    for the full specification and pseudocode.

    Args:
        user_role_assignments: DataFrame with columns including ``user_id``,
            ``user_name``, and ``role_name``.
        user_activity: DataFrame with user activity telemetry (used for
            future enhancements; currently licensing is determined from
            role assignments and security config).
        security_config: DataFrame with columns including ``securityrole``
            and ``LicenseType``.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        AttachOptimizationResult with per-user optimizations sorted by
        monthly savings (descending) and aggregate statistics.
    """
    optimizations: list[AttachOptimization] = []

    # Handle empty input gracefully
    if user_role_assignments.empty:
        return AttachOptimizationResult(
            algorithm_id="4.2",
            optimizations=[],
            total_monthly_savings=0.0,
            total_annual_savings=0.0,
            total_users_analyzed=0,
            feasible_optimizations_count=0,
        )

    # Get all unique users
    unique_users: list[str] = user_role_assignments["user_id"].unique().tolist()
    total_users = len(unique_users)

    # Build a user_id -> user_name lookup
    user_name_map: dict[str, str | None] = {}
    if "user_name" in user_role_assignments.columns:
        for uid in unique_users:
            names = user_role_assignments.loc[
                user_role_assignments["user_id"] == uid, "user_name"
            ]
            user_name_map[uid] = str(names.iloc[0]) if not names.empty else None

    for user_id in unique_users:
        # Step 1: Resolve the user's license types from their roles
        license_types = _resolve_user_license_types(
            user_id, user_role_assignments, security_config
        )

        # Step 2: Skip users with 0 or 1 license type (no attach opportunity)
        if len(license_types) <= 1:
            continue

        # Step 3: Calculate current cost (sum of full license prices)
        current_cost = 0.0
        for lt in license_types:
            try:
                current_cost += get_license_price(pricing_config, lt)
            except KeyError:
                pass

        # Step 4: Find optimal base+attach combination
        base_license, attach_licenses, optimized_cost, is_feasible = (
            _find_optimal_attach_combo(license_types, pricing_config)
        )

        if is_feasible and base_license is not None:
            monthly_savings = current_cost - optimized_cost
            savings_pct = (
                (monthly_savings / current_cost) * 100.0
                if current_cost > 0
                else 0.0
            )

            if monthly_savings > 0:
                optimizations.append(
                    AttachOptimization(
                        user_id=user_id,
                        user_name=user_name_map.get(user_id),
                        current_licenses=license_types,
                        current_cost_per_month=current_cost,
                        optimized_base_license=base_license,
                        optimized_attach_licenses=attach_licenses,
                        optimized_cost_per_month=optimized_cost,
                        monthly_savings=monthly_savings,
                        savings_percentage=savings_pct,
                        feasibility="FEASIBLE",
                        recommendation="Switch to base+attach model",
                    )
                )
        else:
            # Not feasible -- record but with zero savings
            optimizations.append(
                AttachOptimization(
                    user_id=user_id,
                    user_name=user_name_map.get(user_id),
                    current_licenses=license_types,
                    current_cost_per_month=current_cost,
                    optimized_base_license=None,
                    optimized_attach_licenses=[],
                    optimized_cost_per_month=current_cost,
                    monthly_savings=0.0,
                    savings_percentage=0.0,
                    feasibility="NOT_FEASIBLE",
                    recommendation="No attach variant available for all secondary licenses",
                )
            )

    # Sort by monthly savings descending (spec requirement)
    optimizations.sort(key=lambda o: o.monthly_savings, reverse=True)

    # Aggregate statistics
    feasible_opts = [o for o in optimizations if o.feasibility == "FEASIBLE"]
    total_monthly_savings = sum(o.monthly_savings for o in feasible_opts)

    return AttachOptimizationResult(
        algorithm_id="4.2",
        optimizations=optimizations,
        total_monthly_savings=total_monthly_savings,
        total_annual_savings=total_monthly_savings * 12.0,
        total_users_analyzed=total_users,
        feasible_optimizations_count=len(feasible_opts),
    )
