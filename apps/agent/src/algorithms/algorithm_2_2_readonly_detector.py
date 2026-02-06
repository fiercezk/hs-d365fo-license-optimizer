"""Algorithm 2.2: Read-Only User Detector (Enhanced).

Identifies users who primarily perform read operations and recommends
license downgrades to reduce costs. Follows the pseudocode specification
from Requirements/06-Algorithms-Decision-Logic.md, lines 523-654.

The algorithm examines user activity data over a configurable period,
calculates the read-to-write operation ratio, and produces a license
recommendation with a confidence score when the read percentage exceeds
a configurable threshold (default 95%).

Confidence scoring accounts for:
  - Total write operation count (fewer writes = higher confidence)
  - Whether all writes target self-service forms (UserProfile, TimeEntry,
    ExpenseReport) eligible for Team Members license
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

import pandas as pd

from ..models.output_schemas import (
    ConfidenceLevel,
    LicenseRecommendation,
    RecommendationAction,
    RecommendationReason,
    SavingsEstimate,
)
from ..utils.pricing import get_license_price

# Forms whose write operations are considered self-service and acceptable
# under the Team Members license tier.
SELF_SERVICE_FORMS: frozenset[str] = frozenset(
    {
        "UserProfile",
        "TimeEntry",
        "ExpenseReport",
    }
)

# Priority lookup for license tiers used to determine a user's current
# license from activity data.  Higher priority = more expensive license.
_DEFAULT_LICENSE_PRIORITY: dict[str, int] = {
    "Team Members": 60,
    "Operations - Activity": 30,
    "Operations": 90,
    "SCM": 180,
    "Finance": 180,
    "Commerce": 180,
    "Device License": 80,
}

# Write-type actions per the D365 FO telemetry schema.
_WRITE_ACTIONS: frozenset[str] = frozenset({"Write", "Update", "Create", "Delete"})


def _determine_current_license(
    user_activity: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> str:
    """Determine a user's current license from the highest-tier activity.

    The user's current license is the most expensive license tier observed
    across all their activity records.  This reflects the license they must
    hold to access those features.

    Args:
        user_activity: Activity rows for a single user.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        License type string (e.g., "Commerce", "SCM").
    """
    licenses_config: dict[str, Any] = pricing_config.get("licenses", {})
    priority_map: dict[str, int] = {}
    for name, info in licenses_config.items():
        priority_map[name] = int(info.get("priority", _DEFAULT_LICENSE_PRIORITY.get(name, 0)))

    unique_tiers: list[str] = user_activity["license_tier"].unique().tolist()
    best_license: str = unique_tiers[0]
    best_priority: int = priority_map.get(best_license, 0)

    for tier in unique_tiers[1:]:
        tier_priority: int = priority_map.get(tier, 0)
        if tier_priority > best_priority:
            best_license = tier
            best_priority = tier_priority

    return best_license


def _assess_confidence(
    write_count: int,
    write_menu_items: pd.Series,  # type: ignore[type-arg]
) -> tuple[float, ConfidenceLevel]:
    """Assess confidence for a read-only classification.

    Implements the confidence scoring logic from the specification
    (lines 621-654):
      - writeOpCount == 0  -> 1.00, HIGH
      - writeOpCount <= 2  -> 0.95, HIGH
      - writeOpCount <= 10 -> 0.75, MEDIUM
      - writeOpCount > 10  -> 0.55, LOW

    A +0.15 boost (capped at 1.0) is applied when ALL write operations
    target self-service forms (UserProfile, TimeEntry, ExpenseReport),
    since those forms are eligible under the Team Members license.

    Args:
        write_count: Total number of write operations.
        write_menu_items: Series of menu_item values for write operations.

    Returns:
        Tuple of (confidence_score, confidence_level).
    """
    # Base confidence from write count
    if write_count == 0:
        base_score: float = 1.0
    elif write_count <= 2:
        base_score = 0.95
    elif write_count <= 10:
        base_score = 0.75
    else:
        base_score = 0.55

    # Self-service boost: all writes to eligible forms
    if write_count > 0:
        unique_write_forms: set[str] = set(write_menu_items.unique())
        all_self_service: bool = unique_write_forms.issubset(SELF_SERVICE_FORMS)
        if all_self_service:
            base_score = min(base_score + 0.15, 1.0)

    # Determine confidence level from final score
    if base_score >= 0.90:
        level = ConfidenceLevel.HIGH
    elif base_score >= 0.70:
        level = ConfidenceLevel.MEDIUM
    elif base_score >= 0.50:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.INSUFFICIENT_DATA

    return base_score, level


def _build_recommendation_reason(
    read_ops: int,
    write_ops: int,
    read_percentage: float,
    write_menu_items: list[str],
    all_self_service: bool,
    action: RecommendationAction,
    current_license: str,
) -> RecommendationReason:
    """Build a structured explanation for the recommendation.

    Args:
        read_ops: Number of read operations.
        write_ops: Number of write operations.
        read_percentage: Percentage of read operations.
        write_menu_items: Unique menu items targeted by writes.
        all_self_service: Whether all writes are self-service forms.
        action: The recommended action.
        current_license: The user's current license type.

    Returns:
        Populated RecommendationReason model.
    """
    primary: str = (
        f"{read_percentage:.2f}% read-only operations ({read_ops} reads, {write_ops} writes)"
    )

    supporting: list[str] = []
    risk: list[str] = []

    if write_ops == 0:
        supporting.append("Zero write operations observed in analysis period")
    elif all_self_service:
        supporting.append(
            f"All {write_ops} write operations target self-service forms "
            f"({', '.join(sorted(write_menu_items))})"
        )
    else:
        risk.append(
            f"Write operations include non-self-service forms: "
            f"{', '.join(sorted(set(write_menu_items) - SELF_SERVICE_FORMS))}"
        )

    if action == RecommendationAction.NO_CHANGE and current_license == "Team Members":
        supporting.append("User already on optimal Team Members license")

    return RecommendationReason(
        primary_factor=primary,
        supporting_factors=supporting,
        risk_factors=risk,
        data_quality_notes=[],
    )


def detect_readonly_users(
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
    read_threshold: float = 0.95,
    min_sample_size: int = 100,
) -> list[LicenseRecommendation]:
    """Detect users whose activity is predominantly read-only.

    Analyzes user activity data to identify users whose read-operation
    percentage exceeds ``read_threshold``.  For each qualifying user,
    produces a ``LicenseRecommendation`` indicating whether a downgrade
    to Team Members is appropriate, along with confidence scoring and
    savings estimates.

    Args:
        user_activity: DataFrame with columns ``user_id``, ``timestamp``,
            ``menu_item``, ``action``, ``session_id``, ``license_tier``,
            ``feature``.
        security_config: DataFrame with security role to license mapping.
            Used for form eligibility validation.
        pricing_config: Parsed ``pricing.json`` dictionary with license
            costs under ``licenses.<type>.pricePerUserPerMonth``.
        read_threshold: Minimum read percentage (as a fraction, 0.0-1.0)
            to qualify as a read-only candidate.  Default 0.95 (95%).
        min_sample_size: Minimum number of operations required for a user
            to be considered.  Users with fewer operations are skipped.
            Default 100.

    Returns:
        List of ``LicenseRecommendation`` objects, sorted by annual
        savings in descending order.  Users below the read threshold
        or with insufficient data are excluded.
    """
    recommendations: list[LicenseRecommendation] = []
    threshold_pct: float = read_threshold * 100.0

    grouped = user_activity.groupby("user_id")

    for user_id, group_df in grouped:
        user_id_str: str = str(user_id)
        total_ops: int = len(group_df)

        # Skip users with insufficient data
        if total_ops < min_sample_size:
            continue

        # Count read vs write operations
        is_read: pd.Series = group_df["action"] == "Read"  # type: ignore[assignment]
        read_ops: int = int(is_read.sum())
        write_ops: int = total_ops - read_ops

        # Skip users with zero operations (defensive)
        if total_ops == 0:
            continue

        read_percentage: float = (read_ops / total_ops) * 100.0

        # Check if user meets the read-only threshold
        if read_percentage < threshold_pct:
            continue

        # Determine current license from highest-tier activity
        current_license: str = _determine_current_license(group_df, pricing_config)
        current_cost: float = get_license_price(pricing_config, current_license)

        # Assess confidence based on write operations
        write_df: pd.DataFrame = group_df[~is_read]
        write_menu_items: pd.Series = write_df["menu_item"]  # type: ignore[assignment]

        confidence_score, confidence_level = _assess_confidence(
            write_count=write_ops,
            write_menu_items=write_menu_items,
        )

        # Check if all writes are self-service eligible
        unique_write_forms: set[str] = set(write_menu_items.unique()) if write_ops > 0 else set()
        all_self_service: bool = unique_write_forms.issubset(SELF_SERVICE_FORMS)

        # Determine recommended license
        recommended_license: str
        if current_license == "Team Members":
            # Already on lowest applicable tier -- no downgrade possible
            recommended_license = "Team Members"
            action = RecommendationAction.NO_CHANGE
        elif all_self_service or write_ops == 0:
            # All writes are self-service or no writes at all -> Team Members
            recommended_license = "Team Members"
            action = RecommendationAction.DOWNGRADE
        else:
            # Non-self-service writes exist; cannot safely downgrade
            recommended_license = current_license
            action = RecommendationAction.NO_CHANGE

        # Calculate savings
        recommended_cost: float = get_license_price(pricing_config, recommended_license)
        monthly_savings: float = max(current_cost - recommended_cost, 0.0)
        annual_savings: float = monthly_savings * 12.0
        confidence_adjusted: float = annual_savings * confidence_score

        savings: SavingsEstimate | None = None
        if action == RecommendationAction.DOWNGRADE:
            savings = SavingsEstimate(
                monthly_current_cost=current_cost,
                monthly_recommended_cost=recommended_cost,
                monthly_savings=monthly_savings,
                annual_savings=annual_savings,
                confidence_adjusted_savings=round(confidence_adjusted, 2),
            )

        # Build structured reason
        reason: RecommendationReason = _build_recommendation_reason(
            read_ops=read_ops,
            write_ops=write_ops,
            read_percentage=read_percentage,
            write_menu_items=list(unique_write_forms),
            all_self_service=all_self_service,
            action=action,
            current_license=current_license,
        )

        # Determine automation safety
        safe_to_automate: bool = (
            action == RecommendationAction.DOWNGRADE and confidence_level == ConfidenceLevel.HIGH
        )

        rec = LicenseRecommendation(
            algorithm_id="2.2",
            recommendation_id=str(uuid.uuid4()),
            generated_at=datetime.now(UTC),
            user_id=user_id_str,
            current_license=current_license,
            current_license_cost_monthly=current_cost,
            action=action,
            recommended_license=recommended_license,
            recommended_license_cost_monthly=recommended_cost,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            reason=reason,
            savings=savings,
            analysis_period_days=90,
            sample_size=total_ops,
            data_completeness=1.0,
            safe_to_automate=safe_to_automate,
            requires_approval=not safe_to_automate,
            implementation_notes=[],
            tags=_compute_tags(action, annual_savings, confidence_level),
        )

        recommendations.append(rec)

    # Sort by annual savings descending (highest savings first)
    recommendations.sort(
        key=lambda r: r.savings.annual_savings if r.savings else 0.0,
        reverse=True,
    )

    return recommendations


def _compute_tags(
    action: RecommendationAction,
    annual_savings: float,
    confidence_level: ConfidenceLevel,
) -> list[str]:
    """Compute categorization tags for a recommendation.

    Args:
        action: The recommended action.
        annual_savings: Estimated annual savings in USD.
        confidence_level: Confidence level of the recommendation.

    Returns:
        List of string tags for filtering and categorization.
    """
    tags: list[str] = []

    if action == RecommendationAction.DOWNGRADE:
        tags.append("read_only_candidate")
    elif action == RecommendationAction.NO_CHANGE:
        tags.append("already_optimal")

    if annual_savings >= 1000.0:
        tags.append("high_savings")
    elif annual_savings > 0.0:
        tags.append("moderate_savings")

    if confidence_level == ConfidenceLevel.HIGH:
        tags.append("high_confidence")
    elif confidence_level == ConfidenceLevel.LOW:
        tags.append("low_confidence")

    return tags
