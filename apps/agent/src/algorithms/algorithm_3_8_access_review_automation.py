"""Algorithm 3.8: Access Review Automation.

Automates periodic access reviews by analyzing user-role assignments against
actual usage data, identifying access that should be revoked, certified,
or escalated for review.

Business Value:
  - Audit: 70% reduction in manual access review effort
  - Compliance: Automated evidence generation for SOX/GDPR access reviews
  - Security: Identify and prioritize unused high-privilege access
  - Cost: Surface unused roles that inflate license requirements

Input Data:
  - user_role_assignments: DataFrame of user-to-role mappings with metadata
  - user_activity: DataFrame of user activity telemetry (menu items accessed)
  - security_config: DataFrame mapping roles to their menu item entitlements

Output:
  - AccessReviewCampaign containing AccessReviewItems sorted by priority

See Requirements/07-Advanced-Algorithms-Expansion.md, Algorithm 3.8.
See Requirements/08-Algorithm-Review-Summary.md for phase placement.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


class ReviewAction(str, Enum):
    """Recommended action for an access review item."""

    REVOKE = "REVOKE"
    REVIEW = "REVIEW"
    AUTO_CERTIFY = "AUTO_CERTIFY"
    ESCALATE = "ESCALATE"
    DEFER = "DEFER"


class AccessReviewItem(BaseModel):
    """Single item in an access review campaign.

    Represents one user-role pair with a recommended review action,
    usage metrics, cost impact, and priority score.
    """

    user_id: str = Field(description="User identifier")
    user_name: str = Field(description="User display name")
    email: str = Field(default="", description="User email address")
    role_name: str = Field(description="Role under review")
    role_id: str = Field(default="", description="Role identifier")
    recommended_action: ReviewAction = Field(description="Recommended review action")
    usage_percentage: float = Field(
        description="Percentage of role menu items used (0.0-100.0)",
        ge=0.0,
        le=100.0,
    )
    cost_impact_monthly: float = Field(
        description="Monthly cost impact if action is taken (USD)",
        ge=0.0,
    )
    priority_score: float = Field(
        description="Review priority (higher = more urgent). Calculated as risk * cost.",
        ge=0.0,
    )
    justification: str = Field(description="Human-readable explanation for recommendation")
    requires_manager_approval: bool = Field(
        default=False,
        description="Whether this item requires mandatory manager sign-off",
    )
    is_high_privilege: bool = Field(
        default=False,
        description="Whether the role is classified as high privilege",
    )
    days_since_assignment: int = Field(
        default=0,
        description="Number of days since the role was assigned",
        ge=0,
    )


class AccessReviewCampaign(BaseModel):
    """Complete access review campaign output from Algorithm 3.8.

    Aggregates all review items with summary counts by action type.
    """

    algorithm_id: str = Field(default="3.8", description="Algorithm identifier")
    review_items: list[AccessReviewItem] = Field(
        default_factory=list,
        description="All review items sorted by priority_score descending",
    )
    total_review_items: int = Field(
        default=0,
        description="Total number of items in the campaign",
    )
    revoke_count: int = Field(default=0, description="Count of REVOKE recommendations")
    review_count: int = Field(default=0, description="Count of REVIEW recommendations")
    certify_count: int = Field(default=0, description="Count of AUTO_CERTIFY recommendations")
    escalate_count: int = Field(default=0, description="Count of ESCALATE recommendations")
    defer_count: int = Field(default=0, description="Count of DEFER recommendations")


# ---------------------------------------------------------------------------
# Thresholds (configurable via function parameters)
# ---------------------------------------------------------------------------

_DEFAULT_REVIEW_PERIOD_DAYS = 90
_DEFAULT_NEW_ASSIGNMENT_DAYS = 30
_DEFAULT_AUTO_CERTIFY_THRESHOLD = 0.50  # >50% usage = auto-certify
_DEFAULT_DECLINING_USAGE_THRESHOLD = 0.10  # <10% usage = review/revoke
_HIGH_PRIVILEGE_RISK_MULTIPLIER = 3.0
_BASE_RISK_UNUSED = 1.0
_BASE_RISK_DECLINING = 0.5
_BASE_RISK_ACTIVE = 0.1


def generate_access_review(
    user_role_assignments: pd.DataFrame,
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    review_period_days: int = _DEFAULT_REVIEW_PERIOD_DAYS,
    new_assignment_days: int = _DEFAULT_NEW_ASSIGNMENT_DAYS,
    auto_certify_threshold: float = _DEFAULT_AUTO_CERTIFY_THRESHOLD,
    declining_usage_threshold: float = _DEFAULT_DECLINING_USAGE_THRESHOLD,
) -> AccessReviewCampaign:
    """Generate an access review campaign for all user-role assignments.

    Analyzes each user-role pair against actual usage telemetry to determine
    the appropriate review action: REVOKE, REVIEW, AUTO_CERTIFY, ESCALATE,
    or DEFER.

    Args:
        user_role_assignments: DataFrame with columns:
            user_id, user_name, email, role_name, role_id, assigned_date,
            status, is_high_privilege, license_type, license_cost_monthly
        user_activity: DataFrame with columns:
            user_id, timestamp, menu_item, action, session_id
        security_config: DataFrame with columns:
            securityrole, AOTName, AccessLevel, LicenseType, Priority
        review_period_days: Number of days to look back for activity (default 90)
        new_assignment_days: Threshold for deferring new assignments (default 30)
        auto_certify_threshold: Usage ratio above which to auto-certify (default 0.50)
        declining_usage_threshold: Usage ratio below which to flag for review (default 0.10)

    Returns:
        AccessReviewCampaign with review items sorted by priority_score descending.
    """
    # Handle empty input
    if user_role_assignments.empty:
        return AccessReviewCampaign(
            algorithm_id="3.8",
            review_items=[],
            total_review_items=0,
        )

    # Pre-compute: build role -> set of menu items from security config
    role_menu_items: dict[str, set[str]] = {}
    if not security_config.empty:
        for role_name, group in security_config.groupby("securityrole"):
            role_menu_items[str(role_name)] = set(group["AOTName"].tolist())

    # Pre-compute: filter activity to review period and build user -> set of menu items
    now = datetime.now(timezone.utc)
    review_cutoff = now - timedelta(days=review_period_days)

    user_menu_items_used: dict[str, set[str]] = {}
    if not user_activity.empty:
        activity_copy = user_activity.copy()
        activity_copy["_parsed_ts"] = pd.to_datetime(activity_copy["timestamp"], utc=True)
        activity_in_period = activity_copy[activity_copy["_parsed_ts"] >= review_cutoff]

        if not activity_in_period.empty:
            for uid, group in activity_in_period.groupby("user_id"):
                user_menu_items_used[str(uid)] = set(group["menu_item"].tolist())

    # Process each user-role assignment
    review_items: list[AccessReviewItem] = []

    for _, row in user_role_assignments.iterrows():
        item = _evaluate_assignment(
            row=row,
            role_menu_items=role_menu_items,
            user_menu_items_used=user_menu_items_used,
            now=now,
            new_assignment_days=new_assignment_days,
            auto_certify_threshold=auto_certify_threshold,
            declining_usage_threshold=declining_usage_threshold,
        )
        review_items.append(item)

    # Sort by priority_score descending (highest priority first)
    review_items.sort(key=lambda x: x.priority_score, reverse=True)

    # Compute summary counts
    revoke_count = sum(1 for i in review_items if i.recommended_action == ReviewAction.REVOKE)
    review_count = sum(1 for i in review_items if i.recommended_action == ReviewAction.REVIEW)
    certify_count = sum(
        1 for i in review_items if i.recommended_action == ReviewAction.AUTO_CERTIFY
    )
    escalate_count = sum(1 for i in review_items if i.recommended_action == ReviewAction.ESCALATE)
    defer_count = sum(1 for i in review_items if i.recommended_action == ReviewAction.DEFER)

    return AccessReviewCampaign(
        algorithm_id="3.8",
        review_items=review_items,
        total_review_items=len(review_items),
        revoke_count=revoke_count,
        review_count=review_count,
        certify_count=certify_count,
        escalate_count=escalate_count,
        defer_count=defer_count,
    )


def _evaluate_assignment(
    row: Any,
    role_menu_items: dict[str, set[str]],
    user_menu_items_used: dict[str, set[str]],
    now: datetime,
    new_assignment_days: int,
    auto_certify_threshold: float,
    declining_usage_threshold: float,
) -> AccessReviewItem:
    """Evaluate a single user-role assignment and determine the review action.

    Decision tree:
      1. If assigned < new_assignment_days ago -> DEFER
      2. If high-privilege AND unused -> ESCALATE
      3. If usage == 0% -> REVOKE
      4. If usage < declining_usage_threshold -> REVIEW (or REVOKE)
      5. If usage >= auto_certify_threshold -> AUTO_CERTIFY
      6. Otherwise -> REVIEW

    Args:
        row: A row from user_role_assignments DataFrame.
        role_menu_items: Mapping of role name to its entitled menu items.
        user_menu_items_used: Mapping of user_id to menu items they accessed.
        now: Current UTC datetime.
        new_assignment_days: Threshold for DEFER.
        auto_certify_threshold: Usage ratio for AUTO_CERTIFY.
        declining_usage_threshold: Usage ratio for REVIEW/REVOKE.

    Returns:
        AccessReviewItem with computed action, usage, cost, and priority.
    """
    user_id: str = str(row["user_id"])
    user_name: str = str(row.get("user_name", ""))
    email: str = str(row.get("email", ""))
    role_name: str = str(row["role_name"])
    role_id: str = str(row.get("role_id", role_name))
    is_high_privilege: bool = bool(row.get("is_high_privilege", False))
    license_cost: float = float(row.get("license_cost_monthly", 0.0))

    # Parse assigned_date
    assigned_date_raw = row.get("assigned_date", "2020-01-01")
    try:
        assigned_date = pd.Timestamp(assigned_date_raw, tz=timezone.utc)
    except Exception:
        assigned_date = pd.Timestamp("2020-01-01", tz=timezone.utc)

    days_since_assignment = max(0, (now - assigned_date).days)

    # Compute usage percentage
    role_items = role_menu_items.get(role_name, set())
    user_items = user_menu_items_used.get(user_id, set())

    if role_items:
        # Intersection: menu items the user actually used that belong to this role
        used_role_items = role_items & user_items
        usage_ratio = len(used_role_items) / len(role_items)
    else:
        # If security config has no menu items for this role, treat as 0% usage
        usage_ratio = 0.0

    usage_percentage = round(usage_ratio * 100.0, 2)

    # Decision logic
    # 1. DEFER: New assignment (< new_assignment_days)
    if days_since_assignment < new_assignment_days:
        return _build_review_item(
            user_id=user_id,
            user_name=user_name,
            email=email,
            role_name=role_name,
            role_id=role_id,
            action=ReviewAction.DEFER,
            usage_percentage=usage_percentage,
            cost_impact=0.0,
            priority_score=0.0,
            justification=(
                f"Role '{role_name}' was assigned {days_since_assignment} days ago "
                f"(< {new_assignment_days}-day threshold). Deferring review until "
                f"sufficient usage data is available."
            ),
            requires_manager_approval=False,
            is_high_privilege=is_high_privilege,
            days_since_assignment=days_since_assignment,
        )

    # 2. ESCALATE: High-privilege + unused (0% usage)
    if is_high_privilege and usage_ratio == 0.0:
        risk_score = _HIGH_PRIVILEGE_RISK_MULTIPLIER * _BASE_RISK_UNUSED
        priority = risk_score * license_cost
        return _build_review_item(
            user_id=user_id,
            user_name=user_name,
            email=email,
            role_name=role_name,
            role_id=role_id,
            action=ReviewAction.ESCALATE,
            usage_percentage=usage_percentage,
            cost_impact=license_cost,
            priority_score=round(priority, 2),
            justification=(
                f"High-privilege role '{role_name}' has 0% usage over the review period. "
                f"Mandatory manager review required before revocation."
            ),
            requires_manager_approval=True,
            is_high_privilege=is_high_privilege,
            days_since_assignment=days_since_assignment,
        )

    # 3. REVOKE: Unused role (0% usage, not high-privilege)
    if usage_ratio == 0.0:
        risk_score = _BASE_RISK_UNUSED
        priority = risk_score * license_cost
        return _build_review_item(
            user_id=user_id,
            user_name=user_name,
            email=email,
            role_name=role_name,
            role_id=role_id,
            action=ReviewAction.REVOKE,
            usage_percentage=usage_percentage,
            cost_impact=license_cost,
            priority_score=round(priority, 2),
            justification=(
                f"Role '{role_name}' has 0% usage over the review period. "
                f"Recommend revocation to reduce license cost."
            ),
            requires_manager_approval=False,
            is_high_privilege=is_high_privilege,
            days_since_assignment=days_since_assignment,
        )

    # 4. REVIEW: Declining usage (< declining_usage_threshold)
    if usage_ratio < declining_usage_threshold:
        risk_score = _BASE_RISK_DECLINING
        if is_high_privilege:
            risk_score *= _HIGH_PRIVILEGE_RISK_MULTIPLIER
        priority = risk_score * license_cost
        return _build_review_item(
            user_id=user_id,
            user_name=user_name,
            email=email,
            role_name=role_name,
            role_id=role_id,
            action=ReviewAction.REVIEW,
            usage_percentage=usage_percentage,
            cost_impact=license_cost,
            priority_score=round(priority, 2),
            justification=(
                f"Role '{role_name}' has only {usage_percentage}% usage "
                f"(below {declining_usage_threshold * 100}% threshold). "
                f"Review whether this role is still needed."
            ),
            requires_manager_approval=is_high_privilege,
            is_high_privilege=is_high_privilege,
            days_since_assignment=days_since_assignment,
        )

    # 5. AUTO_CERTIFY: Active usage (>= auto_certify_threshold)
    if usage_ratio >= auto_certify_threshold:
        risk_score = _BASE_RISK_ACTIVE
        priority = risk_score * license_cost
        return _build_review_item(
            user_id=user_id,
            user_name=user_name,
            email=email,
            role_name=role_name,
            role_id=role_id,
            action=ReviewAction.AUTO_CERTIFY,
            usage_percentage=usage_percentage,
            cost_impact=0.0,
            priority_score=round(priority, 2),
            justification=(
                f"Role '{role_name}' has {usage_percentage}% usage "
                f"(above {auto_certify_threshold * 100}% threshold). "
                f"Active usage confirmed; auto-certifying."
            ),
            requires_manager_approval=False,
            is_high_privilege=is_high_privilege,
            days_since_assignment=days_since_assignment,
        )

    # 6. REVIEW: Usage between declining and auto-certify thresholds
    risk_score = _BASE_RISK_DECLINING
    if is_high_privilege:
        risk_score *= _HIGH_PRIVILEGE_RISK_MULTIPLIER
    priority = risk_score * license_cost
    return _build_review_item(
        user_id=user_id,
        user_name=user_name,
        email=email,
        role_name=role_name,
        role_id=role_id,
        action=ReviewAction.REVIEW,
        usage_percentage=usage_percentage,
        cost_impact=license_cost,
        priority_score=round(priority, 2),
        justification=(
            f"Role '{role_name}' has {usage_percentage}% usage "
            f"(between {declining_usage_threshold * 100}% and "
            f"{auto_certify_threshold * 100}% thresholds). "
            f"Manual review recommended."
        ),
        requires_manager_approval=is_high_privilege,
        is_high_privilege=is_high_privilege,
        days_since_assignment=days_since_assignment,
    )


def _build_review_item(
    user_id: str,
    user_name: str,
    email: str,
    role_name: str,
    role_id: str,
    action: ReviewAction,
    usage_percentage: float,
    cost_impact: float,
    priority_score: float,
    justification: str,
    requires_manager_approval: bool,
    is_high_privilege: bool,
    days_since_assignment: int,
) -> AccessReviewItem:
    """Construct an AccessReviewItem with all fields populated.

    Args:
        user_id: User identifier.
        user_name: User display name.
        email: User email.
        role_name: Role name under review.
        role_id: Role identifier.
        action: Recommended review action.
        usage_percentage: Percentage of role capabilities used (0-100).
        cost_impact: Monthly cost impact if action taken (USD).
        priority_score: Priority score (risk * cost).
        justification: Human-readable explanation.
        requires_manager_approval: Whether manager sign-off is required.
        is_high_privilege: Whether the role is high-privilege.
        days_since_assignment: Days since role was assigned.

    Returns:
        Fully populated AccessReviewItem.
    """
    return AccessReviewItem(
        user_id=user_id,
        user_name=user_name,
        email=email,
        role_name=role_name,
        role_id=role_id,
        recommended_action=action,
        usage_percentage=usage_percentage,
        cost_impact_monthly=cost_impact,
        priority_score=priority_score,
        justification=justification,
        requires_manager_approval=requires_manager_approval,
        is_high_privilege=is_high_privilege,
        days_since_assignment=days_since_assignment,
    )
