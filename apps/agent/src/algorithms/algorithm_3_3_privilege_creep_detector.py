"""Algorithm 3.3: Privilege Creep Detector.

Identifies users who have gradually accumulated excessive roles/privileges
over time without removal, creating security risks and unnecessary license
costs.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 400-548

The algorithm analyzes:
- Total inactivity duration (days since last login)
- User activity level (operations in last 90 days)
- Special user status (contractor, LOA, seasonal)
- License cost impact

Output: Recommendation to remove, review, or maintain license with
confidence scoring based on activity patterns.
"""

from __future__ import annotations

from datetime import UTC, datetime
import uuid

from ..models.output_schemas import (
    ConfidenceLevel,
    LicenseRecommendation,
    RecommendationAction,
    RecommendationReason,
    SavingsEstimate,
)


def detect_privilege_creep(
    user_id: str,
    user_name: str,
    user_email: str,
    current_license: str,
    current_license_cost_monthly: float,
    days_since_last_login: int,
    operation_count_90d: int,
    is_contractor: bool = False,
    leave_of_absence: bool = False,
    seasonal_profile: str | None = None,
    analysis_period_days: int = 90,
) -> LicenseRecommendation:
    """Detect privilege creep (unused license due to inactivity).

    This algorithm is primarily an unused license detector. It flags users
    with zero activity for 90+ days as candidates for license suspension or
    review. Special handling for contractors, LOA users, and seasonal workers.

    Args:
        user_id: Unique user identifier
        user_name: User display name
        user_email: User email address
        current_license: Current license type (e.g., "Finance", "SCM")
        current_license_cost_monthly: Monthly cost of current license (USD)
        days_since_last_login: Days since user last logged in
        operation_count_90d: Number of operations in last 90 days
        is_contractor: Whether user is a contractor (special handling)
        leave_of_absence: Whether user is on LOA (lower confidence)
        seasonal_profile: Seasonal profile name if applicable (e.g., "SEASONAL_YEAR_END")
        analysis_period_days: Number of days analyzed (default 90)

    Returns:
        LicenseRecommendation with action and confidence scoring.
    """
    # Generate unique recommendation ID
    recommendation_id = str(uuid.uuid4())

    # Inactivity threshold detection
    INACTIVE_THRESHOLD_LOW = 90  # 90+ days = flagged
    INACTIVE_THRESHOLD_HIGH = 180  # 180+ days = high confidence

    is_inactive = days_since_last_login >= INACTIVE_THRESHOLD_LOW
    is_highly_inactive = days_since_last_login >= INACTIVE_THRESHOLD_HIGH

    # Case 1: User is ACTIVE (within 90 days) - no action
    if not is_inactive:
        return LicenseRecommendation(
            algorithm_id="3.3",
            recommendation_id=recommendation_id,
            generated_at=datetime.now(UTC),
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            current_license=current_license,
            current_license_cost_monthly=current_license_cost_monthly,
            action=RecommendationAction.NO_CHANGE,
            recommended_license=None,
            recommended_license_cost_monthly=None,
            confidence_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            reason=RecommendationReason(
                primary_factor="User has active usage within the inactivity threshold",
                supporting_factors=[
                    f"Last login: {days_since_last_login} days ago",
                    f"Operations in last 90 days: {operation_count_90d}",
                ],
            ),
            savings=None,
            analysis_period_days=analysis_period_days,
            sample_size=operation_count_90d,
            data_completeness=1.0,
            safe_to_automate=True,
            requires_approval=False,
            implementation_notes=["User maintains active usage pattern"],
            tags=["active_user", "no_action"],
        )

    # Case 2: User is INACTIVE and has SPECIAL STATUS
    # (Contractor, LOA, Seasonal) - requires REVIEW
    if leave_of_absence:
        confidence_score = 0.55
        confidence_level = ConfidenceLevel.LOW
        action = RecommendationAction.REVIEW_REQUIRED
        rationale = (
            f"User is on leave of absence. Inactive for {days_since_last_login} days "
            "but return is expected. Recommend review with HR before license suspension."
        )
        tags = ["inactive", "loa", "requires_review"]
    elif is_contractor:
        confidence_score = 0.70
        confidence_level = ConfidenceLevel.MEDIUM
        action = RecommendationAction.REVIEW_REQUIRED
        rationale = (
            f"Contractor user inactive for {days_since_last_login} days. "
            "May be between project assignments. Recommend review with project "
            "management before license suspension."
        )
        tags = ["inactive", "contractor", "requires_review"]
    elif seasonal_profile:
        confidence_score = 0.55
        confidence_level = ConfidenceLevel.LOW
        action = RecommendationAction.REVIEW_REQUIRED
        rationale = (
            f"User is inactive for {days_since_last_login} days but has a known "
            f"seasonal profile ({seasonal_profile}). Active season may be approaching. "
            "Recommend manual review before license suspension."
        )
        tags = ["inactive", "seasonal", "requires_review"]
    # Case 3: User is HIGHLY INACTIVE (>180 days) - REMOVE LICENSE
    elif is_highly_inactive:
        confidence_score = 0.95
        confidence_level = ConfidenceLevel.HIGH
        action = RecommendationAction.REMOVE_LICENSE
        rationale = (
            f"User has zero activity in the last {days_since_last_login} days. "
            "No logins, no operations. License is completely unused. "
            "Recommend suspension to reclaim for active user."
        )
        tags = ["inactive", "high_severity", "unused_license"]
    # Case 4: User is MODERATELY INACTIVE (90-180 days) - REMOVE LICENSE
    else:
        confidence_score = 0.75
        confidence_level = ConfidenceLevel.MEDIUM
        action = RecommendationAction.REMOVE_LICENSE
        rationale = (
            f"User has zero activity in the last {days_since_last_login} days. "
            "Below 180-day HIGH confidence threshold, but exceeds 90-day inactivity "
            "threshold. Recommend suspension with review."
        )
        tags = ["inactive", "medium_severity", "unused_license"]

    # Calculate savings for inactive users
    monthly_savings = current_license_cost_monthly
    annual_savings = monthly_savings * 12
    confidence_adjusted_savings = annual_savings * confidence_score

    savings = SavingsEstimate(
        monthly_current_cost=current_license_cost_monthly,
        monthly_recommended_cost=0.0,
        monthly_savings=monthly_savings,
        annual_savings=annual_savings,
        confidence_adjusted_savings=confidence_adjusted_savings,
    )

    return LicenseRecommendation(
        algorithm_id="3.3",
        recommendation_id=recommendation_id,
        generated_at=datetime.now(UTC),
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
        current_license=current_license,
        current_license_cost_monthly=current_license_cost_monthly,
        action=action,
        recommended_license=None,
        recommended_license_cost_monthly=None,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        reason=RecommendationReason(
            primary_factor=rationale,
            supporting_factors=[
                f"Days since last login: {days_since_last_login}",
                f"Operations in analysis period: {operation_count_90d}",
            ],
            risk_factors=(["User is contractor - unexpected absence"] if is_contractor else [])
            + (["User is on leave - expected return"] if leave_of_absence else [])
            + (["Seasonal pattern detected - peak season approaching"] if seasonal_profile else []),
        ),
        savings=savings,
        analysis_period_days=analysis_period_days,
        sample_size=operation_count_90d,
        data_completeness=1.0,
        safe_to_automate=(action == RecommendationAction.REMOVE_LICENSE and is_highly_inactive),
        requires_approval=action == RecommendationAction.REVIEW_REQUIRED,
        implementation_notes=(
            [
                "High confidence - automatic removal recommended after verification",
                "Ensure user is not returning from planned absence",
            ]
            if is_highly_inactive
            else []
        )
        + (
            [
                "Contractor status - coordinate with project management before suspension",
                "Verify project end date and account cleanup plan",
            ]
            if is_contractor
            else []
        )
        + (
            [
                "User on LOA - coordinate with HR for return date",
                "Consider suspending license during LOA period for cost savings",
            ]
            if leave_of_absence
            else []
        )
        + (
            [
                f"Seasonal profile: {seasonal_profile}",
                "Verify peak season dates before license suspension",
            ]
            if seasonal_profile
            else []
        ),
        tags=tags,
    )
