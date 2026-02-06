"""Algorithm 4.3: Cross-Application License Analyzer.

Identifies users with roles across Finance and SCM who could benefit from a
combined Finance+SCM license. The combined license costs $210/month vs. $180
for each individual license, saving $150/month when held separately.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1261-1336.

Key Logic:
  1. Find all users with roles in both Finance AND SCM applications
  2. Check if their current license includes separate Finance and SCM
  3. If yes, recommend combining into Finance+SCM ($210)
  4. Calculate savings: (Finance $180 + SCM $180) - ($210) = $150/month
  5. Set confidence based on clarity of application access
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


def analyze_cross_application_licenses(
    user_id: str,
    user_name: str,
    security_config: pd.DataFrame,
    user_roles: pd.DataFrame,
    pricing_config: dict[str, Any],
    current_licenses: list[str] | None = None,
) -> LicenseRecommendation:
    """Analyze a user's cross-application license situation.

    Args:
        user_id: The user identifier (e.g., "U001")
        user_name: The user's display name
        security_config: DataFrame with columns:
            - securityrole: Role name
            - Application: Application (Finance, SCM, Commerce, etc.)
            - LicenseType: License required (Finance, SCM, Commerce, etc.)
        user_roles: DataFrame with columns:
            - user_id: User identifier
            - user_name: User name
            - security_role: Role name
            - assignment_date: Assignment date
        pricing_config: Parsed pricing.json configuration
        current_licenses: Optional list of current license names held by user.
            If provided, used to detect already-optimized scenarios (e.g.,
            user already holds 'Finance+SCM' combined license).

    Returns:
        LicenseRecommendation with action, savings, and confidence.
    """
    # Step 0: Check if user already holds the combined license
    if current_licenses and any(
        "+" in lic or "combined" in lic.lower() for lic in current_licenses
    ):
        return _create_already_optimized_recommendation(
            user_id=user_id,
            user_name=user_name,
            current_licenses=current_licenses,
        )

    # Step 1: Get all roles assigned to this user
    user_role_rows = user_roles[user_roles["user_id"] == user_id]

    if user_role_rows.empty:
        # No roles found for user
        return LicenseRecommendation(
            algorithm_id="4.3",
            recommendation_id=str(uuid.uuid4()),
            generated_at=datetime.now(UTC),
            user_id=user_id,
            user_name=user_name,
            current_license="Unknown",
            current_license_cost_monthly=0.0,
            action=RecommendationAction.NO_CHANGE,
            confidence_score=0.0,
            confidence_level=ConfidenceLevel.INSUFFICIENT_DATA,
            reason=RecommendationReason(
                primary_factor="User has no roles assigned",
                supporting_factors=[],
                risk_factors=[],
                data_quality_notes=["No role data available for analysis"],
            ),
            analysis_period_days=90,
            sample_size=0,
            data_completeness=0.0,
            safe_to_automate=False,
            requires_approval=False,
        )

    # Step 2: Map user roles to their applications
    user_role_names = user_role_rows["security_role"].tolist()
    role_app_map = security_config.drop_duplicates(subset=["securityrole", "Application"])
    role_app_map_dict: dict[str, set[str]] = {}

    for role_name in user_role_names:
        role_rows = role_app_map[role_app_map["securityrole"] == role_name]
        apps = set(role_rows["Application"].unique().tolist())
        role_app_map_dict[role_name] = apps

    # Step 3: Determine which applications user has access to
    user_applications: set[str] = set()
    for apps in role_app_map_dict.values():
        user_applications.update(apps)

    # Step 4: Check if user has access to BOTH Finance AND SCM
    has_finance = "Finance" in user_applications
    has_scm = "SCM" in user_applications

    if not (has_finance and has_scm):
        # User does not have cross-app access (e.g., Finance only or SCM only)
        return _create_no_cross_app_recommendation(
            user_id=user_id,
            user_name=user_name,
            applications=user_applications,
            pricing_config=pricing_config,
        )

    # Step 5: Determine current license cost (assume user holds individual licenses)
    # Get prices from pricing config
    finance_price = get_license_price(pricing_config, "Finance")
    scm_price = get_license_price(pricing_config, "SCM")
    combined_price = _get_combined_price(pricing_config, "Finance", "SCM")

    # Calculate cost of other applications (not Finance/SCM)
    other_app_cost = 0.0
    other_apps = user_applications - {"Finance", "SCM"}
    for app in other_apps:
        other_app_cost += get_license_price(pricing_config, app)

    current_cost = finance_price + scm_price + other_app_cost
    recommended_cost = combined_price + other_app_cost
    savings = current_cost - recommended_cost

    # Step 6: Determine confidence level
    # HIGH: Clear Finance and SCM access (substantive menu items in both)
    # MEDIUM: One application has minimal access (few menu items)
    # Count total security config entries (menu items) per application
    app_menu_item_counts: dict[str, int] = {}
    for role_name in user_role_names:
        role_entries = security_config[security_config["securityrole"] == role_name]
        for _, row in role_entries.iterrows():
            app = row["Application"]
            if app not in app_menu_item_counts:
                app_menu_item_counts[app] = 0
            app_menu_item_counts[app] += 1

    finance_menu_count = app_menu_item_counts.get("Finance", 0)
    scm_menu_count = app_menu_item_counts.get("SCM", 0)

    # Minimal access threshold: 5 or fewer menu items in an application
    minimal_threshold = 5
    has_minimal_access = (
        finance_menu_count <= minimal_threshold or scm_menu_count <= minimal_threshold
    )

    confidence_score = 0.75 if has_minimal_access else 0.95
    confidence = ConfidenceLevel.MEDIUM if has_minimal_access else ConfidenceLevel.HIGH

    # Step 7: Already-optimized detection is handled at Step 0 via current_licenses
    # If we reach this point, user is not already optimized

    # Step 8: Build supporting factors
    supporting_factors = [
        f"User has {finance_menu_count} Finance menu item(s)",
        f"User has {scm_menu_count} SCM menu item(s)",
        f"Combined Finance+SCM license saves ${savings:.0f}/month vs. separate licenses",
    ]

    # Step 9: Check for risk factors (e.g., minimal access in one app)
    risk_factors: list[str] = []
    if finance_menu_count <= minimal_threshold:
        risk_factors.append(
            f"Finance access is limited to {finance_menu_count} menu items - "
            f"consider if truly needed"
        )
    if scm_menu_count <= minimal_threshold:
        risk_factors.append(
            f"SCM access is limited to {scm_menu_count} menu items - " f"consider if truly needed"
        )

    # Step 10: Determine automation safety
    safe_to_automate = confidence == ConfidenceLevel.HIGH and not risk_factors

    # Step 11: Compute tags
    tags = ["cross_app_opportunity"]
    if savings >= 150.0:
        tags.append("high_savings")

    annual_savings = savings * 12

    return LicenseRecommendation(
        algorithm_id="4.3",
        recommendation_id=str(uuid.uuid4()),
        generated_at=datetime.now(UTC),
        user_id=user_id,
        user_name=user_name,
        current_license="Finance + SCM (separate)",
        current_license_cost_monthly=current_cost,
        action=RecommendationAction.REMOVE_LICENSE,
        recommended_license="Finance+SCM (combined)",
        recommended_license_cost_monthly=recommended_cost,
        confidence_score=confidence_score,
        confidence_level=confidence,
        reason=RecommendationReason(
            primary_factor=(
                f"User has roles in both Finance and SCM applications with current "
                f"separate licenses (${finance_price:.2f} + ${scm_price:.2f} = "
                f"${current_cost:.2f}/month)"
            ),
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            data_quality_notes=[],
        ),
        savings=SavingsEstimate(
            monthly_current_cost=current_cost,
            monthly_recommended_cost=recommended_cost,
            monthly_savings=savings,
            annual_savings=annual_savings,
            confidence_adjusted_savings=annual_savings * confidence_score,
        ),
        analysis_period_days=90,
        sample_size=len(user_role_names),
        data_completeness=1.0,
        safe_to_automate=safe_to_automate,
        requires_approval=not safe_to_automate,
        implementation_notes=[
            f"Combine Finance and SCM into single combined license to save ${savings:.2f}/month"
        ],
        tags=tags,
    )


def _create_no_cross_app_recommendation(
    user_id: str,
    user_name: str,
    applications: set[str],
    pricing_config: dict[str, Any],
) -> LicenseRecommendation:
    """Create a NO_CHANGE recommendation for users without cross-app access.

    Args:
        user_id: User identifier
        user_name: User display name
        applications: Set of applications the user has access to
        pricing_config: Pricing configuration

    Returns:
        LicenseRecommendation with NO_CHANGE action.
    """
    app_list = ", ".join(sorted(applications)) if applications else "none"
    current_license = list(applications)[0] if applications else "Unknown"

    return LicenseRecommendation(
        algorithm_id="4.3",
        recommendation_id=str(uuid.uuid4()),
        generated_at=datetime.now(UTC),
        user_id=user_id,
        user_name=user_name,
        current_license=current_license,
        current_license_cost_monthly=0.0,
        action=RecommendationAction.NO_CHANGE,
        confidence_score=0.95,
        confidence_level=ConfidenceLevel.HIGH,
        reason=RecommendationReason(
            primary_factor=(
                f"User has access to only {app_list if applications else 'no'} "
                f"application(s), no cross-application opportunity"
            ),
            supporting_factors=[
                "Cross-application license optimization only applies to Finance+SCM combination"
            ],
            risk_factors=[],
            data_quality_notes=[],
        ),
        savings=SavingsEstimate(
            monthly_current_cost=0.0,
            monthly_recommended_cost=0.0,
            monthly_savings=0.0,
            annual_savings=0.0,
            confidence_adjusted_savings=0.0,
        ),
        analysis_period_days=90,
        sample_size=0,
        data_completeness=1.0,
        safe_to_automate=True,
        requires_approval=False,
        tags=["already_optimal"],
    )


def _get_combined_price(pricing_config: dict[str, Any], app1: str, app2: str) -> float:
    """Get the price for a combined license.

    For Finance+SCM, the current pricing is $210 (less than $180+$180).
    This is a business rule from Requirements/07.

    Args:
        pricing_config: Pricing configuration
        app1: First application (Finance)
        app2: Second application (SCM)

    Returns:
        Combined monthly price
    """
    # For Finance + SCM combination, check if there's a specific combined price
    # Otherwise, calculate as sum of individual prices (no discount)

    # Currently, Microsoft doesn't officially support Finance+SCM bundling at $210
    # But Requirements/07 treats it as $210 for this algorithm
    # This is a simplification for analysis purposes
    if sorted([app1, app2]) == ["Finance", "SCM"]:
        return 210.0  # Combined price from Requirements/07

    # For other combinations, return sum
    price1 = get_license_price(pricing_config, app1)
    price2 = get_license_price(pricing_config, app2)
    return price1 + price2


def _create_already_optimized_recommendation(
    user_id: str,
    user_name: str,
    current_licenses: list[str],
) -> LicenseRecommendation:
    """Create a NO_CHANGE recommendation for users already holding a combined license.

    Args:
        user_id: User identifier
        user_name: User display name
        current_licenses: Current license names (e.g., ['Finance+SCM'])

    Returns:
        LicenseRecommendation with NO_CHANGE action (already optimized).
    """
    license_str = ", ".join(current_licenses)
    return LicenseRecommendation(
        algorithm_id="4.3",
        recommendation_id=str(uuid.uuid4()),
        generated_at=datetime.now(UTC),
        user_id=user_id,
        user_name=user_name,
        current_license=license_str,
        current_license_cost_monthly=210.0,
        action=RecommendationAction.NO_CHANGE,
        confidence_score=0.95,
        confidence_level=ConfidenceLevel.HIGH,
        reason=RecommendationReason(
            primary_factor=(
                f"User already holds the optimal combined {license_str} license "
                f"for their dual-application access"
            ),
            supporting_factors=["Combined license is already the most cost-effective option"],
            risk_factors=[],
            data_quality_notes=[],
        ),
        savings=SavingsEstimate(
            monthly_current_cost=210.0,
            monthly_recommended_cost=210.0,
            monthly_savings=0.0,
            annual_savings=0.0,
            confidence_adjusted_savings=0.0,
        ),
        analysis_period_days=90,
        sample_size=0,
        data_completeness=1.0,
        safe_to_automate=True,
        requires_approval=False,
        tags=["already_optimal"],
    )
