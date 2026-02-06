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


def analyze_cross_application_licenses(
    user_id: str,
    user_name: str,
    security_config: pd.DataFrame,
    user_roles: pd.DataFrame,
    pricing_config: dict[str, Any],
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

    Returns:
        LicenseRecommendation with action, savings, and confidence.
    """
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
    role_app_map = security_config.drop_duplicates(
        subset=["securityrole", "Application"]
    )
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
    finance_price = _get_license_price(pricing_config, "Finance")
    scm_price = _get_license_price(pricing_config, "SCM")
    combined_price = _get_combined_price(pricing_config, "Finance", "SCM")

    current_cost = finance_price + scm_price
    recommended_cost = combined_price
    savings = current_cost - recommended_cost

    # Step 6: Determine confidence level
    # HIGH: Clear Finance and SCM access (substantive in both)
    # MEDIUM: One application has minimal access
    app_access_counts = {}
    for role_name in user_role_names:
        role_rows_for_role = role_app_map[role_app_map["securityrole"] == role_name]
        for _, row in role_rows_for_role.iterrows():
            app = row["Application"]
            if app not in app_access_counts:
                app_access_counts[app] = 0
            app_access_counts[app] += 1

    finance_role_count = app_access_counts.get("Finance", 0)
    scm_role_count = app_access_counts.get("SCM", 0)

    # If either app has only 1 role (minimal access), set confidence to MEDIUM
    confidence_score = (
        0.75 if (finance_role_count == 1 or scm_role_count == 1) else 0.95
    )
    confidence = (
        ConfidenceLevel.MEDIUM
        if (finance_role_count == 1 or scm_role_count == 1)
        else ConfidenceLevel.HIGH
    )

    # Step 7: Check if user already has the combined license
    # For now, assume if we have cross-app access and separate costs, not optimized
    # (In a real system, we'd check the license_assignments table)
    already_optimized = False

    # Step 8: Build supporting factors
    supporting_factors = [
        f"User has {finance_role_count} Finance role(s)",
        f"User has {scm_role_count} SCM role(s)",
        f"Combined Finance+SCM license saves $150/month vs. separate licenses",
    ]

    # Step 9: Check for risk factors (e.g., minimal access in one app)
    risk_factors: list[str] = []
    if finance_role_count == 1:
        risk_factors.append("Finance access is limited to 1 role - consider if truly needed")
    if scm_role_count == 1:
        risk_factors.append("SCM access is limited to 1 role - consider if truly needed")

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
        analysis_period_days=90,
        sample_size=0,
        data_completeness=1.0,
        safe_to_automate=True,
        requires_approval=False,
        tags=["already_optimal"],
    )


def _get_license_price(pricing_config: dict[str, Any], license_name: str) -> float:
    """Get the monthly price for a license from the pricing configuration.

    Args:
        pricing_config: Pricing configuration dictionary
        license_name: License name (Finance, SCM, Commerce, etc.)

    Returns:
        Monthly price in USD

    Raises:
        KeyError: If license not found in config
    """
    licenses = pricing_config.get("licenses", {})

    # Try exact case-sensitive match first
    if license_name in licenses:
        return float(licenses[license_name].get("pricePerUserPerMonth", 0))

    # Try lowercase with underscores
    license_key_lower = license_name.lower().replace(" ", "_").replace("+", "_")
    if license_key_lower in licenses:
        return float(licenses[license_key_lower].get("pricePerUserPerMonth", 0))

    # Try matching by case-insensitive key lookup
    for key, config in licenses.items():
        if key.lower().replace(" ", "_") == license_key_lower:
            return float(config.get("pricePerUserPerMonth", 0))

    raise KeyError(
        f"License '{license_name}' not found in pricing config. Available: {list(licenses.keys())}"
    )


def _get_combined_price(
    pricing_config: dict[str, Any], app1: str, app2: str
) -> float:
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
    price1 = _get_license_price(pricing_config, app1)
    price2 = _get_license_price(pricing_config, app2)
    return price1 + price2
