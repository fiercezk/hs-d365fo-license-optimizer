"""Algorithm 2.1: Permission vs. Usage Analyzer.

Compares what a user CAN do (theoretical permissions from assigned roles)
with what they ACTUALLY do (observed activity over a configurable analysis
period).  Identifies three types of optimization opportunities:

  1. License downgrade -- user's actual usage only requires a lower-cost
     license than the one implied by their assigned roles.
  2. Permission reduction -- user exercises <50% of their theoretical
     permissions, indicating over-provisioned roles that could be simplified.
  3. Unused role detection -- roles whose menu items the user never accessed
     during the analysis period.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 398-519.

Key design decisions:
  - New users (<30 days since first activity) are SKIPPED -- insufficient data.
  - Multiple opportunities per user are sorted by estimated savings descending.
  - Operates on DataFrames aligned with existing Phase 1 schemas.
  - License pricing uses shared get_license_price() from src/utils/pricing.py.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from ..models.output_schemas import (
    ConfidenceLevel,
    LicenseRecommendation,
    RecommendationAction,
    RecommendationReason,
    SavingsEstimate,
)
from ..utils.pricing import get_license_price

# License tier priority: higher value = more expensive license.
# Used to determine the "theoretical license" (highest tier across assigned
# roles) and the "actual needed license" (highest tier actually used).
_LICENSE_TIER_PRIORITY: dict[str, int] = {
    "Team Members": 1,
    "Operations - Activity": 2,
    "Operations": 3,
    "Device License": 4,
    "SCM": 5,
    "Finance": 5,
    "Commerce": 5,
}

# Threshold: users using fewer than this fraction of their theoretical
# permissions are flagged for permission reduction review.
_PERMISSION_UTILIZATION_THRESHOLD: float = 0.50


def _get_tier_priority(tier: str) -> int:
    """Return the priority for a license tier string.

    Falls back to 0 for unknown tiers so the algorithm degrades
    gracefully when encountering unexpected data.

    Args:
        tier: License tier name (e.g., "Finance", "Team Members").

    Returns:
        Integer priority.  Higher means more expensive.
    """
    return _LICENSE_TIER_PRIORITY.get(tier, 0)


def _highest_tier(tiers: set[str]) -> str:
    """Return the license tier with the highest priority from a set.

    Args:
        tiers: Set of license tier names.

    Returns:
        The tier name with the highest priority.  Returns "Team Members"
        if the set is empty.
    """
    if not tiers:
        return "Team Members"
    return max(tiers, key=_get_tier_priority)


def _determine_confidence_level(score: float) -> ConfidenceLevel:
    """Convert a numeric confidence score to a ConfidenceLevel enum.

    Args:
        score: Confidence score between 0.0 and 1.0.

    Returns:
        ConfidenceLevel enum value matching the score bracket.
    """
    if score >= 0.90:
        return ConfidenceLevel.HIGH
    elif score >= 0.70:
        return ConfidenceLevel.MEDIUM
    elif score >= 0.50:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.INSUFFICIENT_DATA


def _compute_tags(
    action: RecommendationAction,
    annual_savings: float,
    confidence_level: ConfidenceLevel,
    permission_utilization: float | None = None,
) -> list[str]:
    """Compute categorization tags for a recommendation.

    Args:
        action: The recommended action.
        annual_savings: Estimated annual savings in USD.
        confidence_level: Confidence level of the recommendation.
        permission_utilization: Optional utilization percentage (0-100).

    Returns:
        List of string tags for filtering and categorization.
    """
    tags: list[str] = []

    if action == RecommendationAction.DOWNGRADE:
        tags.append("license_downgrade")
    elif action == RecommendationAction.NO_CHANGE:
        tags.append("already_optimal")
    elif action == RecommendationAction.REVIEW_REQUIRED:
        tags.append("permission_reduction")

    if annual_savings >= 1000.0:
        tags.append("high_savings")
    elif annual_savings > 0.0:
        tags.append("moderate_savings")

    if confidence_level == ConfidenceLevel.HIGH:
        tags.append("high_confidence")
    elif confidence_level == ConfidenceLevel.LOW:
        tags.append("low_confidence")

    if permission_utilization is not None and permission_utilization < 50.0:
        tags.append("low_utilization")

    return tags


def analyze_permission_usage(
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    user_role_assignments: pd.DataFrame,
    pricing_config: dict[str, Any],
    min_activity_days: int = 0,
    analysis_period_days: int = 90,
) -> list[LicenseRecommendation]:
    """Analyze permission vs. usage for all users and generate recommendations.

    For each user present in both ``user_role_assignments`` and
    ``user_activity``, this function:

    1. Determines the **theoretical license** -- the most expensive license
       tier required by the union of all menu items across the user's
       assigned roles (from ``security_config``).
    2. Determines the **actual needed license** -- the most expensive
       license tier observed in the user's real activity data.
    3. Calculates **permission utilization** -- fraction of theoretical
       menu items actually accessed.
    4. Emits a ``LicenseRecommendation`` with one of:
       - ``downgrade`` if actual usage requires a cheaper license.
       - ``review_required`` if permission utilization is below 50%.
       - ``no_change`` if the user is well-configured.

    New users whose activity spans fewer than ``min_activity_days`` are
    excluded entirely (insufficient data for reliable recommendations).

    Args:
        user_activity: DataFrame with columns: user_id, timestamp,
            menu_item, action, session_id, license_tier, feature.
        security_config: DataFrame with columns: securityrole, AOTName,
            LicenseType.
        user_role_assignments: DataFrame with columns: user_id, role_name.
        pricing_config: Parsed pricing.json dictionary.
        min_activity_days: Minimum days of activity history required.
            Users with fewer days are skipped.  Default 30.
        analysis_period_days: Reported analysis period.  Default 90.

    Returns:
        List of LicenseRecommendation objects sorted by annual savings
        descending (highest savings first).
    """
    recommendations: list[LicenseRecommendation] = []

    # --- Guard: empty activity data ---
    if user_activity.empty:
        return recommendations

    # --- Guard: empty role assignments ---
    if user_role_assignments.empty:
        return recommendations

    # --- Pre-compute: role -> set of (menu_item, license_tier) ---
    # Vectorized build of the lookup table from security_config.
    role_permissions: dict[str, list[tuple[str, str]]] = {}
    if not security_config.empty:
        for row in security_config.itertuples(index=False):
            role = str(row.securityrole)
            menu_item = str(row.AOTName)
            license_tier = str(row.LicenseType)
            role_permissions.setdefault(role, []).append((menu_item, license_tier))

    # --- Pre-compute: user -> set of assigned roles ---
    user_roles_map: dict[str, set[str]] = {}
    for row in user_role_assignments.itertuples(index=False):
        uid = str(row.user_id)
        role = str(row.role_name)
        user_roles_map.setdefault(uid, set()).add(role)

    # --- Process each user with activity data ---
    for raw_user_id, user_group in user_activity.groupby("user_id", sort=False):
        user_id = str(raw_user_id)

        # Skip users without role assignments
        if user_id not in user_roles_map:
            continue

        # --- Check minimum activity days ---
        timestamps = pd.to_datetime(user_group["timestamp"])
        if timestamps.empty:
            continue
        activity_span_days = (timestamps.max() - timestamps.min()).days
        if activity_span_days < min_activity_days:
            continue

        # --- Theoretical permissions from assigned roles ---
        assigned_roles = user_roles_map[user_id]
        theoretical_items: set[str] = set()
        theoretical_tiers: set[str] = set()
        for role in assigned_roles:
            for menu_item, license_tier in role_permissions.get(role, []):
                theoretical_items.add(menu_item)
                theoretical_tiers.add(license_tier)

        if not theoretical_items:
            continue

        theoretical_license = _highest_tier(theoretical_tiers)

        # --- Actual usage from activity data ---
        actual_items_used: set[str] = set(user_group["menu_item"].dropna().unique().tolist())
        actual_tiers_used: set[str] = set(user_group["license_tier"].dropna().unique().tolist())
        actual_needed_license = _highest_tier(actual_tiers_used)

        # --- Permission utilization ---
        total_theoretical = len(theoretical_items)
        used_count = len(actual_items_used & theoretical_items)
        permission_utilization = (
            (used_count / total_theoretical) * 100.0 if total_theoretical > 0 else 100.0
        )

        # --- Determine action ---
        theoretical_priority = _get_tier_priority(theoretical_license)
        actual_priority = _get_tier_priority(actual_needed_license)

        try:
            current_cost = get_license_price(pricing_config, theoretical_license)
            recommended_cost: float
        except KeyError:
            continue

        action: RecommendationAction
        recommended_license: str
        monthly_savings: float

        if actual_priority < theoretical_priority:
            # Opportunity: user's activity requires a cheaper license
            action = RecommendationAction.DOWNGRADE
            recommended_license = actual_needed_license
            try:
                recommended_cost = get_license_price(pricing_config, recommended_license)
            except KeyError:
                recommended_cost = current_cost
            monthly_savings = max(current_cost - recommended_cost, 0.0)
        elif permission_utilization < _PERMISSION_UTILIZATION_THRESHOLD * 100.0:
            # Over-provisioned: too many unused permissions
            action = RecommendationAction.REVIEW_REQUIRED
            recommended_license = theoretical_license
            recommended_cost = current_cost
            monthly_savings = 0.0
        else:
            # Well-configured user
            action = RecommendationAction.NO_CHANGE
            recommended_license = theoretical_license
            recommended_cost = current_cost
            monthly_savings = 0.0

        annual_savings = monthly_savings * 12.0

        # --- Confidence scoring ---
        # Base confidence from permission utilization and activity volume
        sample_size = len(user_group)
        if action == RecommendationAction.DOWNGRADE:
            # High confidence when utilization is very low relative to tier
            if permission_utilization < 30.0:
                confidence_score = 0.90
            elif permission_utilization < 50.0:
                confidence_score = 0.80
            else:
                confidence_score = 0.70
            # Boost for large sample sizes
            if sample_size >= 100:
                confidence_score = min(confidence_score + 0.05, 1.0)
        elif action == RecommendationAction.REVIEW_REQUIRED:
            confidence_score = 0.70
            if sample_size >= 100:
                confidence_score = min(confidence_score + 0.05, 1.0)
        else:
            confidence_score = 0.85

        confidence_level = _determine_confidence_level(confidence_score)
        confidence_adjusted = annual_savings * confidence_score

        # --- Build reason ---
        utilization_pct = round(permission_utilization, 0)
        primary_factor: str
        supporting_factors: list[str] = []
        risk_factors: list[str] = []

        if action == RecommendationAction.DOWNGRADE:
            primary_factor = (
                f"Actual usage requires {actual_needed_license} license, "
                f"but user holds {theoretical_license} license"
            )
            supporting_factors.append(
                f"Permission utilization: {utilization_pct:.0f}% "
                f"({used_count} of {total_theoretical} menu items used)"
            )
            supporting_factors.append(
                f"Activity analyzed: {sample_size} operations over " f"{activity_span_days} days"
            )
            if monthly_savings > 0:
                supporting_factors.append(
                    f"Potential savings: ${monthly_savings:.2f}/month "
                    f"(${annual_savings:.2f}/year)"
                )
        elif action == RecommendationAction.REVIEW_REQUIRED:
            primary_factor = (
                f"Low permission utilization: {utilization_pct:.0f}% "
                f"({used_count} of {total_theoretical} menu items used)"
            )
            # Identify unused roles
            unused_roles = []
            for role in assigned_roles:
                role_items = {mi for mi, _ in role_permissions.get(role, [])}
                if role_items and not (role_items & actual_items_used):
                    unused_roles.append(role)
            if unused_roles:
                supporting_factors.append(f"Unused roles: {', '.join(sorted(unused_roles))}")
            supporting_factors.append(
                f"Activity analyzed: {sample_size} operations over " f"{activity_span_days} days"
            )
            risk_factors.append(
                "Review with user before removing roles -- "
                "some permissions may be needed infrequently"
            )
        else:
            primary_factor = (
                f"User is well-configured with {utilization_pct:.0f}% " f"permission utilization"
            )
            supporting_factors.append(f"{used_count} of {total_theoretical} menu items used")

        reason = RecommendationReason(
            primary_factor=primary_factor,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            data_quality_notes=[],
        )

        # --- Savings estimate ---
        savings: SavingsEstimate | None = None
        if action == RecommendationAction.DOWNGRADE and monthly_savings > 0:
            savings = SavingsEstimate(
                monthly_current_cost=current_cost,
                monthly_recommended_cost=recommended_cost,
                monthly_savings=monthly_savings,
                annual_savings=annual_savings,
                confidence_adjusted_savings=round(confidence_adjusted, 2),
            )

        # --- Automation safety ---
        safe_to_automate = (
            action == RecommendationAction.DOWNGRADE and confidence_level == ConfidenceLevel.HIGH
        )

        # --- Build recommendation ---
        rec = LicenseRecommendation(
            algorithm_id="2.1",
            recommendation_id=str(uuid.uuid4()),
            generated_at=datetime.now(UTC),
            user_id=user_id,
            current_license=theoretical_license,
            current_license_cost_monthly=current_cost,
            action=action,
            recommended_license=recommended_license,
            recommended_license_cost_monthly=recommended_cost,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            reason=reason,
            savings=savings,
            analysis_period_days=analysis_period_days,
            sample_size=sample_size,
            data_completeness=1.0,
            safe_to_automate=safe_to_automate,
            requires_approval=not safe_to_automate,
            implementation_notes=[],
            tags=_compute_tags(action, annual_savings, confidence_level, permission_utilization),
        )

        recommendations.append(rec)

    # --- Sort by savings descending ---
    recommendations.sort(
        key=lambda r: r.savings.annual_savings if r.savings else 0.0,
        reverse=True,
    )

    return recommendations
