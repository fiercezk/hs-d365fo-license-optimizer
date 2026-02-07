"""Algorithm 2.6: Cross-Role License Optimization.

Optimizes license assignments by analyzing combinations of roles across the
entire organization to identify systemic optimization opportunities. Instead
of optimizing users individually, this algorithm finds common role
combinations that create high license requirements and recommends structural
changes (role splitting, variants, approval workflows) to reduce costs.

Specification: Requirements/10-Additional-Algorithms-Exploration.md
(Algorithm 2.6: Cross-Role License Optimization).

Key Logic:
  1. Group users by their sorted role combination
  2. Skip single-role combinations (not cross-role)
  3. Skip combinations with fewer than MIN_USERS_THRESHOLD (default 5)
  4. For each qualifying combination, determine required license types per role
  5. Skip combinations where all roles require the same license (no cross-license
     optimization possible)
  6. Analyze actual usage per user to classify into usage pattern segments
  7. Generate SPLIT_ROLES options for exclusive single-license segments (>=3 users)
  8. Generate CREATE_ROLE_VARIANTS when variant savings exceed 10% of current cost
  9. Generate ADD_APPROVAL_WORKFLOW for high-cost, large combinations
 10. Sort results by potential_savings descending

Performance: O(U + C*A) where U = user-role rows, C = qualifying combinations,
A = average activity rows per combination. Uses vectorized groupby for user
grouping; avoids iterrows() in hot paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from ..utils.pricing import get_license_price

# ---------------------------------------------------------------------------
# Constants / defaults
# ---------------------------------------------------------------------------

_DEFAULT_MIN_USERS_THRESHOLD: int = 5
_MIN_SINGLE_LICENSE_USERS: int = 3
_MIN_SAVINGS_PERCENTAGE: float = 0.10  # 10%
_HIGH_COST_THRESHOLD: float = 500.0
_HIGH_COUNT_THRESHOLD: int = 10

# License priority map (higher number = more expensive license).
# Used to determine the "highest" license when multiple types are present.
_LICENSE_PRIORITY: dict[str, int] = {
    "Team Members": 60,
    "Operations - Activity": 30,
    "Operations": 90,
    "SCM": 180,
    "Finance": 180,
    "Commerce": 180,
}


# ---------------------------------------------------------------------------
# Output data models
# ---------------------------------------------------------------------------


@dataclass
class OptimizationOption:
    """A single optimization option for a role combination.

    Attributes:
        option_type: Type of optimization (SPLIT_ROLES, CREATE_ROLE_VARIANTS,
            ADD_APPROVAL_WORKFLOW).
        description: Human-readable description of the optimization.
        affected_users: Number of users affected by this option.
        total_savings: Total monthly savings (USD) if option is implemented.
        savings_percentage: Savings as a percentage of current combination cost.
        feasibility: Implementation feasibility (HIGH, MEDIUM, LOW).
        recommended_license: For SPLIT_ROLES, the target license type.
        users: List of user IDs affected.
    """

    option_type: str
    description: str
    affected_users: int = 0
    total_savings: float = 0.0
    savings_percentage: float = 0.0
    feasibility: str = "MEDIUM"
    recommended_license: str | None = None
    users: list[str] = field(default_factory=list)


@dataclass
class UsagePatterns:
    """Breakdown of license usage within a role combination.

    Attributes:
        uses_all_licenses: User IDs that access features from ALL license types.
        uses_single_license: Mapping of license type to user IDs that
            exclusively use that license.
        uses_multiple_licenses: User IDs that use more than one but not all
            license types.
    """

    uses_all_licenses: list[str] = field(default_factory=list)
    uses_single_license: dict[str, list[str]] = field(default_factory=dict)
    uses_multiple_licenses: list[str] = field(default_factory=list)


@dataclass
class CrossRoleOptimization:
    """Analysis result for a single role combination.

    Attributes:
        algorithm_id: Always ``"2.6"``.
        role_combination: Sorted list of role names in this combination.
        user_count: Number of users with this exact role combination.
        users: List of user IDs with this combination.
        required_licenses: Set of distinct license types required by the roles.
        current_cost_per_user: Monthly license cost per user (highest license).
        current_total_cost: Total monthly cost for all users in this combination.
        has_optimization_opportunity: Whether any optimization options exist.
        optimization_options: List of possible optimization strategies.
        potential_savings: Best possible monthly savings across all options.
        usage_patterns: Breakdown of how users actually use their licenses.
    """

    algorithm_id: str = "2.6"
    role_combination: list[str] = field(default_factory=list)
    user_count: int = 0
    users: list[str] = field(default_factory=list)
    required_licenses: list[str] = field(default_factory=list)
    current_cost_per_user: float = 0.0
    current_total_cost: float = 0.0
    has_optimization_opportunity: bool = False
    optimization_options: list[OptimizationOption] = field(default_factory=list)
    potential_savings: float = 0.0
    usage_patterns: UsagePatterns | None = None


# CrossRoleOptimizationResult is an alias kept for backward compatibility
# with test imports.
CrossRoleOptimizationResult = CrossRoleOptimization


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_highest_license_cost(
    license_types: set[str],
    pricing_config: dict[str, Any],
) -> float:
    """Return the highest monthly price among the given license types.

    Falls back to the priority map for ordering when prices are equal,
    but the returned value is always the actual price from config.

    Args:
        license_types: Set of license type names (e.g. {"Finance", "SCM"}).
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        The highest monthly price (float).
    """
    if not license_types:
        return 0.0
    prices: list[float] = []
    for lt in license_types:
        try:
            prices.append(get_license_price(pricing_config, lt))
        except KeyError:
            prices.append(float(_LICENSE_PRIORITY.get(lt, 0)))
    return max(prices) if prices else 0.0


def _sum_license_costs(
    license_types: set[str],
    pricing_config: dict[str, Any],
) -> float:
    """Return the sum of monthly prices for all given license types.

    This models the D365 FO multi-license stacking rule: if a user's roles
    require multiple distinct license types, the user must hold all of them.

    Args:
        license_types: Set of license type names.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        Sum of monthly prices (float).
    """
    total = 0.0
    for lt in license_types:
        try:
            total += get_license_price(pricing_config, lt)
        except KeyError:
            total += float(_LICENSE_PRIORITY.get(lt, 0))
    return total


def _determine_role_license(
    role_name: str,
    security_config: pd.DataFrame,
) -> str:
    """Determine the highest-priority license type required by a role.

    Looks up all menu items for the role in security_config and returns the
    license type with the highest priority value.

    Args:
        role_name: Security role name.
        security_config: DataFrame with ``securityrole``, ``LicenseType``,
            ``Priority`` columns.

    Returns:
        License type string (e.g. ``"Finance"``).  Returns ``"Team Members"``
        if the role has no entries in the security config.
    """
    role_rows = security_config[security_config["securityrole"] == role_name]
    if role_rows.empty:
        return "Team Members"
    # Pick the license with the highest priority
    max_idx = role_rows["Priority"].idxmax()
    return str(role_rows.loc[max_idx, "LicenseType"])


def _get_licenses_used_by_user(
    user_id: str,
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    role_names: list[str],
) -> set[str]:
    """Determine which license types a user actually exercises.

    Cross-references the user's accessed menu items (from activity data) with
    the security config to find which license tiers those items belong to,
    filtered to only menu items associated with the user's assigned roles.

    Args:
        user_id: User identifier.
        user_activity: Activity DataFrame with ``user_id``, ``menu_item``,
            ``license_tier`` columns.
        security_config: Security config DataFrame.
        role_names: List of roles assigned to this user.

    Returns:
        Set of license type strings the user actually uses.
    """
    user_rows = user_activity[user_activity["user_id"] == user_id]
    if user_rows.empty:
        return set()

    # Build a mapping: menu_item -> license_type from the security config,
    # scoped to the user's assigned roles.
    role_menu_license: dict[str, str] = {}
    for role in role_names:
        role_entries = security_config[security_config["securityrole"] == role]
        for _, row in role_entries.iterrows():
            aot = str(row["AOTName"])
            lt = str(row["LicenseType"])
            # Keep the higher-priority license if a menu item appears in
            # multiple roles.
            if aot not in role_menu_license:
                role_menu_license[aot] = lt

    # Also consider the license_tier column from activity data directly.
    licenses_used: set[str] = set()
    accessed_items = user_rows["menu_item"].unique()
    for item in accessed_items:
        if item in role_menu_license:
            licenses_used.add(role_menu_license[item])
        else:
            # Fall back to the license_tier recorded in the activity
            tier_rows = user_rows[user_rows["menu_item"] == item]
            if not tier_rows.empty:
                licenses_used.add(str(tier_rows.iloc[0]["license_tier"]))

    return licenses_used


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def optimize_cross_role_licenses(
    user_role_assignments: pd.DataFrame,
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
    min_users_threshold: int = _DEFAULT_MIN_USERS_THRESHOLD,
) -> list[CrossRoleOptimization]:
    """Analyze cross-role license optimization opportunities.

    Groups all users by their sorted role combination, then for each
    qualifying combination (multi-role, above user threshold) analyzes
    actual license usage to recommend structural changes.

    See Requirements/10-Additional-Algorithms-Exploration.md, Algorithm 2.6.

    Args:
        user_role_assignments: DataFrame with columns ``user_id``,
            ``role_name``, plus optional ``user_name``, ``email``, etc.
        user_activity: DataFrame with columns ``user_id``, ``menu_item``,
            ``license_tier``, ``action``, etc.
        security_config: DataFrame with columns ``securityrole``,
            ``AOTName``, ``LicenseType``, ``Priority``, etc.
        pricing_config: Parsed pricing.json dictionary.
        min_users_threshold: Minimum users in a combination to analyze
            (default 5).

    Returns:
        List of :class:`CrossRoleOptimization` results sorted by
        ``potential_savings`` descending (highest savings first).
    """
    # Guard: empty input
    if user_role_assignments.empty:
        return []

    # ------------------------------------------------------------------
    # Step 1: Group users by sorted role combination
    # ------------------------------------------------------------------
    # Build a mapping: user_id -> sorted tuple of role names
    user_roles_grouped: dict[str, list[str]] = {}
    for _, row in user_role_assignments.iterrows():
        uid = str(row["user_id"])
        role = str(row["role_name"])
        user_roles_grouped.setdefault(uid, []).append(role)

    # Create combination key -> list of user IDs
    combo_users: dict[tuple[str, ...], list[str]] = {}
    for uid, roles in user_roles_grouped.items():
        key = tuple(sorted(set(roles)))
        combo_users.setdefault(key, []).append(uid)

    # ------------------------------------------------------------------
    # Step 2: Analyze each qualifying combination
    # ------------------------------------------------------------------
    results: list[CrossRoleOptimization] = []

    for role_tuple, user_ids in combo_users.items():
        # Skip single-role combinations
        if len(role_tuple) < 2:
            continue

        # Skip below user threshold
        if len(user_ids) < min_users_threshold:
            continue

        analysis = _analyze_role_combination(
            role_names=list(role_tuple),
            user_ids=user_ids,
            user_activity=user_activity,
            security_config=security_config,
            pricing_config=pricing_config,
        )
        results.append(analysis)

    # ------------------------------------------------------------------
    # Step 3: Sort by potential savings descending
    # ------------------------------------------------------------------
    results.sort(key=lambda r: r.potential_savings, reverse=True)

    return results


def _analyze_role_combination(
    role_names: list[str],
    user_ids: list[str],
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> CrossRoleOptimization:
    """Analyze a single role combination for optimization opportunities.

    Implements the AnalyzeRoleCombination sub-algorithm from the spec.

    Args:
        role_names: Sorted list of role names in this combination.
        user_ids: User IDs that share this combination.
        user_activity: Full activity DataFrame.
        security_config: Full security config DataFrame.
        pricing_config: Pricing configuration.

    Returns:
        A fully populated :class:`CrossRoleOptimization` instance.
    """
    result = CrossRoleOptimization(
        role_combination=role_names,
        user_count=len(user_ids),
        users=user_ids,
    )

    # Determine required license per role
    role_licenses: dict[str, str] = {}
    for role in role_names:
        role_licenses[role] = _determine_role_license(role, security_config)

    unique_licenses = set(role_licenses.values())
    result.required_licenses = sorted(unique_licenses)

    # Calculate current cost per user (sum of all required license types)
    cost_per_user = _sum_license_costs(unique_licenses, pricing_config)
    result.current_cost_per_user = cost_per_user
    result.current_total_cost = cost_per_user * len(user_ids)

    # If all roles require the same license, no cross-license optimization
    if len(unique_licenses) <= 1:
        result.has_optimization_opportunity = False
        result.usage_patterns = UsagePatterns()
        return result

    # ------------------------------------------------------------------
    # Analyze usage patterns
    # ------------------------------------------------------------------
    usage = UsagePatterns()

    for uid in user_ids:
        licenses_used = _get_licenses_used_by_user(uid, user_activity, security_config, role_names)

        if len(licenses_used) == 0:
            # No activity - treat as unknown; conservatively bucket as
            # single-license if there is a dominant role, else skip.
            continue
        elif licenses_used == unique_licenses:
            usage.uses_all_licenses.append(uid)
        elif len(licenses_used) == 1:
            lic = next(iter(licenses_used))
            usage.uses_single_license.setdefault(lic, []).append(uid)
        else:
            usage.uses_multiple_licenses.append(uid)

    result.usage_patterns = usage

    # ------------------------------------------------------------------
    # Opportunity 1: SPLIT_ROLES for exclusive single-license segments
    # ------------------------------------------------------------------
    options: list[OptimizationOption] = []

    for lic_type, lic_users in usage.uses_single_license.items():
        if len(lic_users) >= _MIN_SINGLE_LICENSE_USERS:
            try:
                lic_cost = get_license_price(pricing_config, lic_type)
            except KeyError:
                lic_cost = float(_LICENSE_PRIORITY.get(lic_type, 0))

            savings_per_user = cost_per_user - lic_cost
            total_savings = savings_per_user * len(lic_users)
            savings_pct = (
                (total_savings / result.current_total_cost * 100)
                if result.current_total_cost > 0
                else 0.0
            )

            options.append(
                OptimizationOption(
                    option_type="SPLIT_ROLES",
                    description=(
                        f"Create separate {lic_type}-only role variant "
                        f"for {len(lic_users)} users"
                    ),
                    affected_users=len(lic_users),
                    total_savings=total_savings,
                    savings_percentage=savings_pct,
                    feasibility="HIGH",
                    recommended_license=lic_type,
                    users=lic_users,
                )
            )

    # ------------------------------------------------------------------
    # Opportunity 2: CREATE_ROLE_VARIANTS (when >10% total savings)
    # ------------------------------------------------------------------
    variant_savings = 0.0
    for uid in user_ids:
        licenses_used = _get_licenses_used_by_user(uid, user_activity, security_config, role_names)
        if 0 < len(licenses_used) < len(unique_licenses):
            # User could use a lower-cost variant
            highest_used_cost = _get_highest_license_cost(licenses_used, pricing_config)
            variant_savings += cost_per_user - highest_used_cost

    if (
        variant_savings > 0
        and result.current_total_cost > 0
        and variant_savings > result.current_total_cost * _MIN_SAVINGS_PERCENTAGE
    ):
        savings_pct = variant_savings / result.current_total_cost * 100
        options.append(
            OptimizationOption(
                option_type="CREATE_ROLE_VARIANTS",
                description=(
                    "Create license-specific variants for roles: " + ", ".join(role_names)
                ),
                affected_users=len(user_ids),
                total_savings=variant_savings,
                savings_percentage=savings_pct,
                feasibility="MEDIUM",
            )
        )

    # ------------------------------------------------------------------
    # Opportunity 3: ADD_APPROVAL_WORKFLOW for high-cost combos
    # ------------------------------------------------------------------
    if result.current_total_cost > _HIGH_COST_THRESHOLD and len(user_ids) > _HIGH_COUNT_THRESHOLD:
        options.append(
            OptimizationOption(
                option_type="ADD_APPROVAL_WORKFLOW",
                description=("Require manager approval for " + " + ".join(role_names)),
                affected_users=len(user_ids),
                total_savings=0.0,
                savings_percentage=0.0,
                feasibility="LOW",
            )
        )

    result.optimization_options = options

    # Determine if there is an optimization opportunity
    result.has_optimization_opportunity = any(o.total_savings > 0 for o in options)

    # Best potential savings
    savings_values = [o.total_savings for o in options if o.total_savings > 0]
    result.potential_savings = max(savings_values) if savings_values else 0.0

    return result
