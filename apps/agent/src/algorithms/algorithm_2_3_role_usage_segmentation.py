"""Algorithm 2.3: Role Segmentation by Usage Pattern.

Analyzes a mixed-license role (e.g., Finance + SCM) to determine whether
users naturally segment by their actual license-type usage.  For each role
the algorithm produces:

  - Total user count
  - Segmentation breakdown: Finance-Only, SCM-Only, Mixed (with counts and
    percentages)
  - Optimization recommendations:
      Option A - Split into 2+ license-specific roles
      Option B - Create read-only variant for secondary license
  - Savings estimates for each option
  - Recommendation with implementation notes

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 696-829.

Key decision thresholds:
  - Split recommendation: triggered when any single-license segment
    exceeds 20% of the role's user population.
  - Read-only variant: triggered when mixed users only READ from one
    license type (no writes to that type's menu items).
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from ..utils.pricing import get_license_price

# ---------------------------------------------------------------------------
# Pydantic output models
# ---------------------------------------------------------------------------

# Minimum percentage of single-license users required to recommend a split.
_DEFAULT_SPLIT_THRESHOLD_PCT: float = 20.0


class SegmentInfo(BaseModel):
    """Statistics for a single usage segment within a role."""

    count: int = Field(description="Number of users in this segment", ge=0)
    percentage: float = Field(
        description="Percentage of total role users in this segment",
        ge=0.0,
        le=100.0,
    )
    user_ids: list[str] = Field(
        default_factory=list,
        description="User identifiers belonging to this segment",
    )


class OptimizationRecommendation(BaseModel):
    """A single optimization recommendation for a role."""

    option: str = Field(
        description="Short label for the recommendation option "
        "(e.g., 'Split into separate Finance and SCM roles')"
    )
    users_affected: int = Field(
        description="Number of users affected by this recommendation",
        ge=0,
    )
    estimated_savings_per_month: float = Field(
        description="Estimated monthly savings in USD",
        ge=0.0,
    )
    implementation: str = Field(
        description="Implementation guidance for this recommendation",
    )


class RoleUsageSegmentation(BaseModel):
    """Complete output for Algorithm 2.3: Role Segmentation by Usage Pattern.

    See Requirements/06-Algorithms-Decision-Logic.md, lines 696-829.
    """

    algorithm_id: str = Field(
        default="2.3",
        description="Algorithm identifier",
    )
    role_name: str = Field(description="Name of the analyzed role")
    total_users: int = Field(description="Total users assigned to this role", ge=0)
    segmentation: dict[str, SegmentInfo] = Field(
        description="Usage segmentation breakdown keyed by segment name "
        "(e.g., 'finance_only', 'scm_only', 'mixed')"
    )
    recommendations: list[OptimizationRecommendation] = Field(
        default_factory=list,
        description="Optimization recommendations with savings estimates",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_license_types_for_role(
    role_name: str,
    security_config: pd.DataFrame,
) -> dict[str, set[str]]:
    """Map each license type to its set of menu items for the given role.

    Args:
        role_name: The security role name.
        security_config: Security configuration DataFrame with columns
            ``securityrole``, ``AOTName``, ``LicenseType``.

    Returns:
        Dict mapping license type string to set of AOTName strings.
    """
    role_rows = security_config[security_config["securityrole"] == role_name]
    license_to_menu_items: dict[str, set[str]] = {}
    for _, row in role_rows.iterrows():
        license_type: str = str(row["LicenseType"])
        aot_name: str = str(row["AOTName"])
        license_to_menu_items.setdefault(license_type, set()).add(aot_name)
    return license_to_menu_items


def _build_menu_item_to_license(
    license_to_menu_items: dict[str, set[str]],
) -> dict[str, str]:
    """Build reverse index: menu_item -> license_type.

    When a menu item maps to multiple license types, the first encountered
    mapping wins (deterministic because we iterate sorted keys).

    Args:
        license_to_menu_items: Forward mapping from license type to menu items.

    Returns:
        Dict mapping menu item AOTName to its license type.
    """
    reverse: dict[str, str] = {}
    for license_type in sorted(license_to_menu_items.keys()):
        for menu_item in license_to_menu_items[license_type]:
            if menu_item not in reverse:
                reverse[menu_item] = license_type
    return reverse


def _classify_users(
    user_ids: list[str],
    user_activity: pd.DataFrame,
    menu_item_to_license: dict[str, str],
    license_types: list[str],
) -> dict[str, list[str]]:
    """Classify users into license-usage segments.

    For each user, determines which license types they have actually
    accessed based on their activity records. Users are then categorized as:
      - ``<license>_only`` if they accessed only one license type
      - ``mixed`` if they accessed multiple license types

    Args:
        user_ids: List of user identifiers to classify.
        user_activity: Activity DataFrame with ``user_id`` and ``menu_item``.
        menu_item_to_license: Reverse mapping from menu item to license type.
        license_types: Sorted list of distinct license types for the role.

    Returns:
        Dict mapping segment name to list of user IDs in that segment.
    """
    # Pre-build segments dict
    segments: dict[str, list[str]] = {"mixed": []}
    for lt in license_types:
        key = lt.lower().replace(" ", "_") + "_only"
        segments[key] = []

    # Build a lookup from user_id -> set of license types accessed
    if user_activity.empty:
        return segments

    # Vectorized: map menu items to license types, then groupby user
    activity_for_users = user_activity[user_activity["user_id"].isin(user_ids)]
    if activity_for_users.empty:
        return segments

    # Map each activity row's menu_item to its license type
    activity_licenses = activity_for_users["menu_item"].map(menu_item_to_license)

    # Build user -> set of license types
    user_license_sets: dict[str, set[str]] = {}
    for uid, license_type in zip(activity_for_users["user_id"], activity_licenses, strict=False):
        uid_str = str(uid)
        if pd.notna(license_type):
            user_license_sets.setdefault(uid_str, set()).add(str(license_type))

    # Classify each user
    for uid in user_ids:
        accessed = user_license_sets.get(uid, set())
        if len(accessed) == 0:
            # No recognized activity -- skip (not classified)
            continue
        elif len(accessed) == 1:
            lt = next(iter(accessed))
            key = lt.lower().replace(" ", "_") + "_only"
            if key in segments:
                segments[key].append(uid)
        else:
            segments["mixed"].append(uid)

    return segments


def _classify_users_with_actions(
    user_ids: list[str],
    user_activity: pd.DataFrame,
    menu_item_to_license: dict[str, str],
    license_types: list[str],
) -> dict[str, dict[str, set[str]]]:
    """Classify each user's access pattern per license type (read vs write).

    Returns a dict mapping user_id to a dict of license_type -> set of actions.
    For example: {"USR_01": {"Finance": {"Write"}, "SCM": {"Read"}}}

    Args:
        user_ids: List of user identifiers to classify.
        user_activity: Activity DataFrame with ``user_id``, ``menu_item``, ``action``.
        menu_item_to_license: Reverse mapping from menu item to license type.
        license_types: Sorted list of distinct license types.

    Returns:
        Dict mapping user_id to (license_type -> set of action strings).
    """
    result: dict[str, dict[str, set[str]]] = {}

    if user_activity.empty:
        return result

    activity_for_users = user_activity[user_activity["user_id"].isin(user_ids)]
    if activity_for_users.empty:
        return result

    for _, row in activity_for_users.iterrows():
        uid = str(row["user_id"])
        menu_item = str(row["menu_item"])
        action = str(row["action"])
        license_type = menu_item_to_license.get(menu_item)
        if license_type is None:
            continue
        result.setdefault(uid, {}).setdefault(license_type, set()).add(action)

    return result


_WRITE_ACTIONS: frozenset[str] = frozenset({"Write", "Update", "Create", "Delete"})


def _calculate_split_savings(
    segments: dict[str, list[str]],
    license_types: list[str],
    pricing_config: dict[str, Any],
) -> float:
    """Calculate monthly savings from splitting exclusive-license users.

    Users who only access one license type can be moved from the combined
    (most expensive) license to their single required license, saving the
    difference.

    The "combined" cost is the sum of all license type prices because
    D365 FO uses multi-license stacking: a user accessing both Finance
    and SCM features needs both licenses ($180+$180=$360).

    Args:
        segments: Classification of users into segments.
        license_types: Distinct license types for the role.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        Total monthly savings in USD.
    """
    if len(license_types) < 2:
        return 0.0

    # Combined cost = sum of all license prices (multi-license stacking)
    license_prices: dict[str, float] = {}
    for lt in license_types:
        try:
            license_prices[lt] = get_license_price(pricing_config, lt)
        except KeyError:
            license_prices[lt] = 0.0

    combined_cost = sum(license_prices.values())

    total_savings = 0.0
    for lt in license_types:
        key = lt.lower().replace(" ", "_") + "_only"
        exclusive_users = segments.get(key, [])
        if not exclusive_users:
            continue
        single_cost = license_prices.get(lt, 0.0)
        per_user_savings = combined_cost - single_cost
        if per_user_savings > 0:
            total_savings += per_user_savings * len(exclusive_users)

    return total_savings


def _analyze_read_variant_opportunity(
    user_actions: dict[str, dict[str, set[str]]],
    license_types: list[str],
    pricing_config: dict[str, Any],
) -> OptimizationRecommendation | None:
    """Analyze whether a read-only variant could reduce licensing needs.

    For mixed users, check if they only READ from one license type while
    WRITING to another. If so, a read-only variant for the secondary
    license could reduce costs.

    Args:
        user_actions: Per-user, per-license-type action sets.
        license_types: Distinct license types for the role.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        An OptimizationRecommendation if a read-only variant is beneficial,
        otherwise None.
    """
    if len(license_types) < 2:
        return None

    # For each license type, count users who ONLY read from it
    # (but write to at least one other license type)
    best_candidate_type: str | None = None
    best_candidate_users: list[str] = []

    for target_lt in license_types:
        read_only_users: list[str] = []
        for uid, lt_actions in user_actions.items():
            if target_lt not in lt_actions:
                continue
            # Check if user only reads from this license type
            actions_for_target = lt_actions[target_lt]
            has_write = bool(actions_for_target & _WRITE_ACTIONS)
            if has_write:
                continue
            # Check if user writes to at least one OTHER license type
            writes_other = False
            for other_lt, other_actions in lt_actions.items():
                if other_lt == target_lt:
                    continue
                if other_actions & _WRITE_ACTIONS:
                    writes_other = True
                    break
            if writes_other:
                read_only_users.append(uid)

        if len(read_only_users) > len(best_candidate_users):
            best_candidate_type = target_lt
            best_candidate_users = read_only_users

    if not best_candidate_users or best_candidate_type is None:
        return None

    # Calculate potential savings: these users could potentially use a
    # read-only (Team Members) license for the secondary type instead.
    # Savings estimate: price difference between full license and Team Members
    # for each affected user, on the secondary license type.
    try:
        full_price = get_license_price(pricing_config, best_candidate_type)
    except KeyError:
        full_price = 0.0
    try:
        read_price = get_license_price(pricing_config, "Team Members")
    except KeyError:
        read_price = 0.0

    per_user_savings = max(full_price - read_price, 0.0)
    total_savings = per_user_savings * len(best_candidate_users)

    return OptimizationRecommendation(
        option=f"Create read-only variant for {best_candidate_type} portion",
        users_affected=len(best_candidate_users),
        estimated_savings_per_month=total_savings,
        implementation=(
            f"Create {best_candidate_type}-Read role with read-only access to "
            f"{best_candidate_type} menu items. Reassign {len(best_candidate_users)} "
            f"users who only read {best_candidate_type} data."
        ),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_role_usage_segmentation(
    role_name: str,
    user_role_assignments: pd.DataFrame,
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
    split_threshold_pct: float = _DEFAULT_SPLIT_THRESHOLD_PCT,
) -> RoleUsageSegmentation:
    """Algorithm 2.3: Analyze role usage segmentation by license type.

    For a role with mixed license types (e.g., Finance + SCM), determines
    whether users naturally segment into single-license usage patterns and
    generates optimization recommendations when segmentation is detected.

    See Requirements/06-Algorithms-Decision-Logic.md, lines 696-829.

    Args:
        role_name: Name of the security role to analyze.
        user_role_assignments: DataFrame with columns ``user_id``, ``role_name``
            (and optionally ``user_name``, ``email``, etc.).
        user_activity: DataFrame with columns ``user_id``, ``menu_item``,
            ``action``, ``license_tier``, ``feature``.
        security_config: DataFrame with columns ``securityrole``, ``AOTName``,
            ``LicenseType``, ``AccessLevel``.
        pricing_config: Parsed ``pricing.json`` dictionary.
        split_threshold_pct: Minimum percentage of single-license users to
            trigger a split recommendation. Default 20%.

    Returns:
        RoleUsageSegmentation with segmentation breakdown and recommendations.
    """
    # Step 1: Determine which license types the role covers
    license_to_menu_items = _get_license_types_for_role(role_name, security_config)
    license_types: list[str] = sorted(license_to_menu_items.keys())
    menu_item_to_license = _build_menu_item_to_license(license_to_menu_items)

    # Step 2: Get users assigned to this role
    if user_role_assignments.empty or "role_name" not in user_role_assignments.columns:
        user_ids: list[str] = []
    else:
        role_assignments = user_role_assignments[user_role_assignments["role_name"] == role_name]
        user_ids = role_assignments["user_id"].unique().tolist()
    total_users: int = len(user_ids)

    # Handle empty role
    if total_users == 0:
        return RoleUsageSegmentation(
            role_name=role_name,
            total_users=0,
            segmentation={
                lt.lower().replace(" ", "_") + "_only": SegmentInfo(count=0, percentage=0.0)
                for lt in license_types
            }
            | {"mixed": SegmentInfo(count=0, percentage=0.0)},
            recommendations=[],
        )

    # Handle single license type (no segmentation possible)
    if len(license_types) <= 1:
        seg_key = (
            license_types[0].lower().replace(" ", "_") + "_only"
            if license_types
            else "unknown_only"
        )
        return RoleUsageSegmentation(
            role_name=role_name,
            total_users=total_users,
            segmentation={
                seg_key: SegmentInfo(
                    count=total_users,
                    percentage=100.0,
                    user_ids=user_ids,
                ),
                "mixed": SegmentInfo(count=0, percentage=0.0),
            },
            recommendations=[],
        )

    # Step 3: Classify users into segments
    segments = _classify_users(user_ids, user_activity, menu_item_to_license, license_types)

    # Build segmentation info with percentages
    segmentation: dict[str, SegmentInfo] = {}
    for seg_name, seg_users in segments.items():
        count = len(seg_users)
        pct = (count / total_users) * 100.0 if total_users > 0 else 0.0
        segmentation[seg_name] = SegmentInfo(
            count=count,
            percentage=round(pct, 2),
            user_ids=seg_users,
        )

    # Step 4: Generate recommendations
    recommendations: list[OptimizationRecommendation] = []

    # Recommendation A: Split into separate roles
    any_segment_above_threshold = False
    for lt in license_types:
        key = lt.lower().replace(" ", "_") + "_only"
        seg_info = segmentation.get(key)
        if seg_info and seg_info.percentage >= split_threshold_pct:
            any_segment_above_threshold = True
            break

    if any_segment_above_threshold:
        split_savings = _calculate_split_savings(segments, license_types, pricing_config)
        if split_savings > 0:
            total_exclusive = sum(
                len(segments.get(lt.lower().replace(" ", "_") + "_only", []))
                for lt in license_types
            )
            type_labels = " and ".join(license_types)
            recommendations.append(
                OptimizationRecommendation(
                    option=f"Split into separate {type_labels} roles",
                    users_affected=total_exclusive,
                    estimated_savings_per_month=round(split_savings, 2),
                    implementation=(
                        f"Create {role_name}-{license_types[0]} and "
                        f"{role_name}-{license_types[1]}, reassign exclusive users"
                    ),
                )
            )

    # Recommendation B: Read-only variant
    user_actions = _classify_users_with_actions(
        user_ids, user_activity, menu_item_to_license, license_types
    )
    read_variant_rec = _analyze_read_variant_opportunity(
        user_actions, license_types, pricing_config
    )
    if read_variant_rec is not None and read_variant_rec.estimated_savings_per_month > 0:
        recommendations.append(read_variant_rec)

    return RoleUsageSegmentation(
        role_name=role_name,
        total_users=total_users,
        segmentation=segmentation,
        recommendations=recommendations,
    )
