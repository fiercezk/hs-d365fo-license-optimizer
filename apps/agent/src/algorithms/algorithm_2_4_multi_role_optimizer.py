"""Algorithm 2.4: Multi-Role Optimization.

Analyzes users with multiple roles to identify optimization opportunities
through unused role detection, license downgrade based on actual usage,
and cost impact analysis for each optimization option.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 833-959.

Key behaviors:
  - Skip users with only 1 role (not multi-role)
  - Calculate usage percentage per role (accessed items / total items)
  - Identify unused roles (0% usage) for removal
  - Determine required license from actual menu item usage
  - Recommend license downgrade when actual < theoretical license
  - Estimate savings from unused role removal + license downgrade
  - Handle edge cases: single-role user, all roles unused, no activity
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from ..utils.pricing import get_license_price

# ---------------------------------------------------------------------------
# License priority map -- higher value = more expensive / broader license.
# Used to determine "highest" license across roles.
# ---------------------------------------------------------------------------

_LICENSE_PRIORITY: dict[str, int] = {
    "Team Members": 60,
    "Operations - Activity": 30,
    "Operations": 90,
    "SCM": 180,
    "Finance": 180,
    "Commerce": 180,
    "Device License": 80,
}


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class RoleUsage(BaseModel):
    """Usage statistics for a single role assigned to a user."""

    role_name: str = Field(description="Name of the security role")
    total_menu_items: int = Field(description="Total menu items granted by this role", ge=0)
    accessed_menu_items: int = Field(
        description="Number of role menu items the user actually accessed", ge=0
    )
    usage_percentage: float = Field(
        description="Percentage of role menu items accessed (0-100)", ge=0.0, le=100.0
    )
    license_type: str = Field(description="License type required by this role")


class OptimizationRecommendation(BaseModel):
    """A single optimization recommendation for a multi-role user."""

    option: str = Field(description="Short description of the optimization option")
    impact: str = Field(description="Human-readable impact description")
    estimated_savings_per_month: float = Field(
        description="Estimated monthly savings in USD", ge=0.0
    )
    roles_to_remove: list[str] = Field(
        description="Roles recommended for removal", default_factory=list
    )
    recommended_license: str | None = Field(
        description="Recommended license after optimization", default=None
    )


class MultiRoleOptimization(BaseModel):
    """Complete output from Algorithm 2.4: Multi-Role Optimization.

    Contains role usage analysis, unused role detection, license
    downgrade recommendation, and cost impact for each option.
    """

    algorithm_id: str = Field(default="2.4", description="Algorithm identifier")
    user_id: str = Field(description="Target user identifier")
    is_multi_role: bool = Field(description="Whether the user has more than one role assigned")
    role_count: int = Field(description="Number of roles assigned", ge=0)
    assigned_roles: list[str] = Field(
        description="List of assigned role names", default_factory=list
    )
    current_license: str = Field(
        description="Current (theoretical) license based on all assigned roles",
        default="",
    )
    required_license_based_on_usage: str = Field(
        description="License required based on actual menu item usage",
        default="",
    )
    role_usage: list[RoleUsage] = Field(
        description="Per-role usage statistics", default_factory=list
    )
    unused_roles: list[str] = Field(description="Roles with 0% usage", default_factory=list)
    optimization_recommendations: list[OptimizationRecommendation] = Field(
        description="Optimization recommendations with cost impact",
        default_factory=list,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_highest_license(license_types: list[str]) -> str:
    """Return the highest-priority license from a list of license types.

    Uses ``_LICENSE_PRIORITY`` to rank licenses.  When two licenses share the
    same priority (e.g. Finance and SCM both at 180), the first one encountered
    wins -- this is deterministic given a stable input order.

    Args:
        license_types: List of license type strings.

    Returns:
        The license type string with the highest priority.
    """
    if not license_types:
        return "Team Members"

    best: str = license_types[0]
    best_priority: int = _LICENSE_PRIORITY.get(best, 0)

    for lt in license_types[1:]:
        p = _LICENSE_PRIORITY.get(lt, 0)
        if p > best_priority:
            best = lt
            best_priority = p

    return best


# Premium license types that stack (user pays for each separately).
_PREMIUM_LICENSES: frozenset[str] = frozenset({"Finance", "SCM", "Commerce"})


def _get_stacked_license_label(license_types: list[str]) -> str:
    """Build a composite license label for multi-license stacking.

    D365 FO license stacking means a user with roles spanning Finance AND SCM
    must hold both licenses ($180 + $180 = $360/mo).  This function returns a
    combined label like ``"Finance + SCM"`` when multiple premium licenses are
    required, or a single license name when only one is needed.

    Args:
        license_types: Unique license types from the user's roles.

    Returns:
        A composite label (e.g. ``"Finance + SCM"``) or a single license name.
    """
    unique = list(dict.fromkeys(license_types))  # dedupe, preserve order
    premium = sorted(lt for lt in unique if lt in _PREMIUM_LICENSES)

    if len(premium) > 1:
        return " + ".join(premium)

    return _get_highest_license(unique)


def _compute_stacked_cost(
    license_types: list[str],
    pricing_config: dict[str, Any],
) -> float:
    """Compute the total monthly cost for stacked licenses.

    For premium licenses (Finance, SCM, Commerce), each distinct type costs
    separately.  For non-premium, only the highest is charged.

    Args:
        license_types: Unique license type strings.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        Total monthly cost in USD.
    """
    unique = list(dict.fromkeys(license_types))
    premium = [lt for lt in unique if lt in _PREMIUM_LICENSES]
    non_premium = [lt for lt in unique if lt not in _PREMIUM_LICENSES]

    total: float = 0.0

    # Each premium license stacks
    for lt in set(premium):
        total += get_license_price(pricing_config, lt)

    # Non-premium: only charge the highest
    if non_premium and not premium:
        highest = _get_highest_license(non_premium)
        total += get_license_price(pricing_config, highest)

    # If no licenses at all, default to Team Members
    if total == 0.0 and not unique:
        total = get_license_price(pricing_config, "Team Members")

    return total


def _get_role_license_type(
    role_name: str,
    security_config: pd.DataFrame,
) -> str:
    """Determine the license type required by a given role.

    Looks up all security config rows for this role and returns the
    highest-priority license among them.

    Args:
        role_name: Security role name.
        security_config: Security configuration DataFrame with columns
            ``securityrole``, ``LicenseType``, ``Priority``.

    Returns:
        License type string (e.g. "Finance", "SCM").
    """
    role_rows = security_config[security_config["securityrole"] == role_name]
    if role_rows.empty:
        return "Team Members"

    license_types: list[str] = role_rows["LicenseType"].unique().tolist()
    return _get_highest_license(license_types)


def _get_menu_items_for_role(
    role_name: str,
    security_config: pd.DataFrame,
) -> set[str]:
    """Return the set of menu items (AOTName) granted by a role.

    Args:
        role_name: Security role name.
        security_config: Security configuration DataFrame.

    Returns:
        Set of AOTName strings.
    """
    role_rows = security_config[security_config["securityrole"] == role_name]
    return set(role_rows["AOTName"].unique())


def _determine_required_license_from_activity(
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
) -> str:
    """Determine the minimum license needed based on actually accessed menu items.

    Examines the user's activity to find unique menu items accessed, then
    looks up each in security_config to find its license requirement, and
    returns the highest license needed.

    Args:
        user_activity: Activity DataFrame for a single user (columns include
            ``menu_item``).
        security_config: Security configuration DataFrame.

    Returns:
        License type string required based on actual usage.
    """
    if user_activity.empty:
        return "Team Members"

    accessed_items: set[str] = set(user_activity["menu_item"].unique())

    license_types_needed: list[str] = []
    for item in accessed_items:
        item_rows = security_config[security_config["AOTName"] == item]
        if not item_rows.empty:
            item_licenses: list[str] = item_rows["LicenseType"].unique().tolist()
            license_types_needed.extend(item_licenses)

    if not license_types_needed:
        return "Team Members"

    return _get_highest_license(license_types_needed)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def optimize_multi_role_user(
    user_id: str,
    user_role_assignments: pd.DataFrame,
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> MultiRoleOptimization:
    """Analyze a single multi-role user for optimization opportunities.

    Implements Algorithm 2.4 from Requirements/06-Algorithms-Decision-Logic.md.

    Steps:
      1. Check if user has > 1 role; skip if not.
      2. For each role, calculate usage percentage (accessed / total menu items).
      3. Identify unused roles (0% usage).
      4. Determine current (theoretical) license from all roles.
      5. Determine required license from actual activity.
      6. Generate recommendations: remove unused roles, downgrade license.

    Args:
        user_id: Target user identifier.
        user_role_assignments: DataFrame with columns ``user_id``,
            ``role_name``, etc.
        user_activity: DataFrame with columns ``user_id``, ``menu_item``,
            ``action``, ``license_tier``, ``feature``.
        security_config: DataFrame with columns ``securityrole``,
            ``AOTName``, ``LicenseType``, ``Priority``, etc.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        MultiRoleOptimization result with usage analysis and recommendations.
    """
    # Filter to this user's roles
    user_roles_df = user_role_assignments[user_role_assignments["user_id"] == user_id]
    role_names: list[str] = user_roles_df["role_name"].unique().tolist()
    role_count = len(role_names)

    # Single-role users: not multi-role, skip analysis
    if role_count <= 1:
        return MultiRoleOptimization(
            user_id=user_id,
            is_multi_role=False,
            role_count=role_count,
            assigned_roles=role_names,
        )

    # Filter activity to this user (handle empty DataFrame safely)
    if user_activity.empty or "user_id" not in user_activity.columns:
        user_act = pd.DataFrame(columns=user_activity.columns)
    else:
        user_act = user_activity[user_activity["user_id"] == user_id]

    accessed_menu_items_all: set[str] = (
        set(user_act["menu_item"].unique()) if not user_act.empty else set()
    )

    # Analyze usage per role
    role_usage_list: list[RoleUsage] = []
    unused_roles: list[str] = []

    for role in role_names:
        role_menu_items = _get_menu_items_for_role(role, security_config)
        total_items = len(role_menu_items)

        # Count unique accessed items that belong to this role
        accessed_for_role = accessed_menu_items_all & role_menu_items
        accessed_count = len(accessed_for_role)

        # Calculate usage percentage
        if total_items > 0:
            usage_pct = (accessed_count / total_items) * 100.0
        else:
            usage_pct = 0.0

        role_license = _get_role_license_type(role, security_config)

        role_usage_list.append(
            RoleUsage(
                role_name=role,
                total_menu_items=total_items,
                accessed_menu_items=accessed_count,
                usage_percentage=round(usage_pct, 2),
                license_type=role_license,
            )
        )

        if usage_pct == 0.0:
            unused_roles.append(role)

    # Determine current license (stacked across all assigned roles)
    all_role_licenses = [ru.license_type for ru in role_usage_list]
    current_license = _get_stacked_license_label(all_role_licenses)
    current_cost = _compute_stacked_cost(all_role_licenses, pricing_config)

    # Determine required license based on actual usage
    required_license = _determine_required_license_from_activity(user_act, security_config)

    # Generate optimization recommendations
    recommendations: list[OptimizationRecommendation] = []

    # Option 1: Remove unused roles
    if len(unused_roles) > 0:
        # Calculate license after removing unused roles
        active_role_licenses = [
            ru.license_type for ru in role_usage_list if ru.role_name not in unused_roles
        ]
        license_after_removal = (
            _get_stacked_license_label(active_role_licenses)
            if active_role_licenses
            else "Team Members"
        )
        cost_after_removal = (
            _compute_stacked_cost(active_role_licenses, pricing_config)
            if active_role_licenses
            else get_license_price(pricing_config, "Team Members")
        )

        savings_from_removal = max(current_cost - cost_after_removal, 0.0)

        recommendations.append(
            OptimizationRecommendation(
                option=f"Remove {len(unused_roles)} unused role(s)",
                impact=(
                    f"Remove unused roles: {', '.join(unused_roles)}. "
                    f"No access impact -- user does not use these roles."
                ),
                estimated_savings_per_month=round(savings_from_removal, 2),
                roles_to_remove=unused_roles,
                recommended_license=license_after_removal,
            )
        )

    # Option 2: License downgrade based on actual usage
    if required_license != current_license:
        required_cost = get_license_price(pricing_config, required_license)
        downgrade_savings = max(current_cost - required_cost, 0.0)

        if downgrade_savings > 0:
            recommendations.append(
                OptimizationRecommendation(
                    option=(
                        f"Downgrade license from {current_license} "
                        f"to {required_license} based on actual usage"
                    ),
                    impact=(
                        f"User's actual activity only requires "
                        f"{required_license} license "
                        f"(${required_cost:.0f}/mo vs ${current_cost:.0f}/mo)."
                    ),
                    estimated_savings_per_month=round(downgrade_savings, 2),
                    recommended_license=required_license,
                )
            )

    return MultiRoleOptimization(
        user_id=user_id,
        is_multi_role=True,
        role_count=role_count,
        assigned_roles=role_names,
        current_license=current_license,
        required_license_based_on_usage=required_license,
        role_usage=role_usage_list,
        unused_roles=unused_roles,
        optimization_recommendations=recommendations,
    )


def optimize_multi_role_users_batch(
    user_role_assignments: pd.DataFrame,
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> list[MultiRoleOptimization]:
    """Batch-process all multi-role users for optimization opportunities.

    Identifies all users with > 1 role from the assignments DataFrame and
    runs ``optimize_multi_role_user`` for each.

    Args:
        user_role_assignments: Full user-role assignment DataFrame.
        user_activity: Full user activity DataFrame.
        security_config: Security configuration DataFrame.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        List of MultiRoleOptimization results, one per multi-role user.
    """
    # Identify multi-role users (users with > 1 unique role)
    role_counts = (
        user_role_assignments.groupby("user_id")["role_name"]
        .nunique()
        .reset_index(name="role_count")
    )
    multi_role_users = role_counts[role_counts["role_count"] > 1]["user_id"].tolist()

    results: list[MultiRoleOptimization] = []
    for uid in multi_role_users:
        result = optimize_multi_role_user(
            user_id=uid,
            user_role_assignments=user_role_assignments,
            user_activity=user_activity,
            security_config=security_config,
            pricing_config=pricing_config,
        )
        results.append(result)

    return results
