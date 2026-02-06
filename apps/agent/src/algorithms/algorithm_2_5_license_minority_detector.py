"""Algorithm 2.5: License Minority Detection & Optimization.

Detects users who hold multiple licenses but have highly skewed usage patterns.
When one license is used significantly less than others (below configurable
threshold, default 15%), identifies this as a "minority" license and recommends
optimization through downgrade or role modification.

See Requirements/09-License-Minority-Detection-Algorithm.md for full specification.

The algorithm:
1. Identifies users with multiple licenses
2. Calculates usage distribution across licenses
3. Flags licenses below minority threshold
4. Analyzes read-only patterns for conversion opportunities
5. Generates recommendations with confidence scores and savings estimates
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

# Write-type actions per D365 FO telemetry schema
_WRITE_ACTIONS: frozenset[str] = frozenset({"Write", "Update", "Create", "Delete"})


def _get_license_price(pricing_config: dict[str, Any], license_type: str) -> float:
    """Retrieve the monthly price for a given license type.

    Args:
        pricing_config: Parsed pricing.json dictionary.
        license_type: License type name (e.g., "scm", "finance", normalized).

    Returns:
        Monthly price in USD.

    Raises:
        KeyError: If license type not found in pricing config.
    """
    # Try exact match first (with capitalization)
    license_normalized = license_type.strip()

    # Look for matching license in config (case-insensitive key matching)
    for key, config in pricing_config["licenses"].items():
        if key.lower().replace(" ", "_").replace("-", "_") == license_normalized.lower().replace(
            " ", "_"
        ).replace("-", "_"):
            return float(config["pricePerUserPerMonth"])

    # If no match found, raise error
    raise KeyError(f"License type '{license_type}' not found in pricing config")


def _get_form_to_license_mapping(
    user_activity: pd.DataFrame,
) -> dict[str, str]:
    """Create a mapping from menu_item (form) to LicenseType.

    Uses the license_tier directly from activity data, which indicates
    the actual license required for that form access.

    Args:
        user_activity: User activity DataFrame with license_tier column.

    Returns:
        Dictionary mapping menu_item (form) to LicenseType.
    """
    mapping = {}
    for _, row in user_activity.iterrows():
        form = str(row["menu_item"]).strip()
        license_type = str(row["license_tier"]).strip()
        if form and license_type:
            # Store the license type for this form
            # If form appears with multiple licenses, use the most recent
            mapping[form] = license_type
    return mapping


def _normalize_license_name(license_name: str) -> str:
    """Normalize license name for consistent comparison.

    Args:
        license_name: Raw license name from data.

    Returns:
        Normalized license name.
    """
    return license_name.lower().strip().replace(" ", "_").replace("-", "_")


def _calculate_usage_by_license(
    user_activity: pd.DataFrame,
    form_to_license: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Calculate usage statistics grouped by license type.

    Args:
        user_activity: User's activity records.
        form_to_license: Mapping from form to license type.

    Returns:
        Dictionary with structure:
        {
            "license_type": {
                "form_count": int,
                "access_count": int,
                "percentage": float,
                "forms": [list of unique forms for this license]
            }
        }
    """
    usage_by_license: dict[str, dict[str, Any]] = {}

    # Map each activity to its license
    for _, activity in user_activity.iterrows():
        menu_item = str(activity["menu_item"]).strip()
        license_type = form_to_license.get(menu_item)

        if not license_type:
            continue

        license_norm = _normalize_license_name(license_type)
        if license_norm not in usage_by_license:
            usage_by_license[license_norm] = {
                "form_count": 0,
                "access_count": 0,
                "forms": set(),
                "read_count": 0,
                "write_count": 0,
            }

        # Add form to set (for unique count)
        usage_by_license[license_norm]["forms"].add(menu_item)
        # Increment access count
        usage_by_license[license_norm]["access_count"] += 1
        # Track read vs write
        action = str(activity.get("action", "")).strip()
        if action in _WRITE_ACTIONS:
            usage_by_license[license_norm]["write_count"] += 1
        else:
            usage_by_license[license_norm]["read_count"] += 1

    # Convert form sets to lists and calculate percentages
    total_accesses = sum(stats["access_count"] for stats in usage_by_license.values())

    for license_type, stats in usage_by_license.items():
        stats["form_count"] = len(stats["forms"])
        stats["forms"] = sorted(list(stats["forms"]))
        if total_accesses > 0:
            stats["percentage"] = (stats["access_count"] / total_accesses) * 100
        else:
            stats["percentage"] = 0.0

    return usage_by_license


def _assess_confidence(
    usage_by_license: dict[str, dict[str, Any]],
    minority_licenses: list[dict[str, Any]],
) -> float:
    """Calculate confidence score for minority detection.

    Factors:
    - How skewed is dominant license? (40 points max)
    - How low is minority usage? (40 points max)
    - How many minority licenses? (20 points max)

    Args:
        usage_by_license: Usage statistics by license.
        minority_licenses: List of detected minority licenses.

    Returns:
        Confidence score from 0.0 to 1.0.
    """
    confidence_score = 0.0

    if not minority_licenses or not usage_by_license:
        return 0.0

    # Factor 1: Dominance of top license
    percentages = [stats["percentage"] for stats in usage_by_license.values()]
    dominant_percentage = max(percentages) if percentages else 0.0

    if dominant_percentage >= 85:
        confidence_score += 0.40
    elif dominant_percentage >= 70:
        confidence_score += 0.20

    # Factor 2: How low is minority usage?
    minority_percentages = [m["percentage"] for m in minority_licenses]
    lowest_minority = min(minority_percentages) if minority_percentages else 100.0

    if lowest_minority <= 5:
        confidence_score += 0.40
    elif lowest_minority <= 10:
        confidence_score += 0.20

    # Factor 3: Single minority vs multiple
    if len(minority_licenses) == 1:
        confidence_score += 0.20

    return min(1.0, confidence_score)


def _determine_confidence_level(score: float) -> ConfidenceLevel:
    """Convert confidence score to confidence level category.

    Args:
        score: Confidence score (0.0-1.0).

    Returns:
        ConfidenceLevel enum value.
    """
    if score >= 0.90:
        return ConfidenceLevel.HIGH
    elif score >= 0.70:
        return ConfidenceLevel.MEDIUM
    elif score >= 0.50:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.INSUFFICIENT_DATA


def _generate_recommendation_reason(
    user_id: str,
    usage_by_license: dict[str, dict[str, Any]],
    minority_licenses: list[dict[str, Any]],
) -> RecommendationReason:
    """Generate structured recommendation rationale.

    Args:
        user_id: User identifier.
        usage_by_license: Usage statistics by license.
        minority_licenses: List of minority licenses.

    Returns:
        RecommendationReason with primary and supporting factors.
    """
    primary_factor = ""
    supporting_factors = []
    risk_factors = []

    if minority_licenses:
        minority_names = ", ".join(m["license"] for m in minority_licenses)
        total_minority_pct = sum(m["percentage"] for m in minority_licenses)
        primary_factor = (
            f"User has {len(minority_licenses)} minority license(s) ({minority_names}) "
            f"with combined {total_minority_pct:.1f}% usage"
        )

        # Supporting factors
        if len(usage_by_license) >= 3:
            supporting_factors.append(f"User holds {len(usage_by_license)} total licenses")

        # Read-only pattern
        for minority in minority_licenses:
            if minority["read_count"] > 0 and minority["write_count"] == 0:
                supporting_factors.append(
                    f"{minority['license']} usage is read-only " f"({minority['read_count']} reads)"
                )
            elif minority["read_count"] > 0 and minority["write_count"] > 0:
                read_pct = (
                    minority["read_count"] / (minority["read_count"] + minority["write_count"])
                ) * 100
                if read_pct >= 90:
                    supporting_factors.append(f"{minority['license']} is {read_pct:.0f}% read-only")

        # Risk factors
        risk_factors.append("Confirm with user that minority license access is still required")
        risk_factors.append("Consider form-level analysis before removing license entirely")

    return RecommendationReason(
        primary_factor=primary_factor or "Multiple licenses detected",
        supporting_factors=supporting_factors,
        risk_factors=risk_factors,
    )


def detect_license_minority_users(
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    pricing_config: dict[str, Any],
    minority_threshold: float = 15.0,
    analysis_period_days: int = 90,
) -> list[LicenseRecommendation]:
    """Detect users with minority licenses and generate recommendations.

    Args:
        user_activity: User activity records with columns:
                      user_id, timestamp, menu_item, action, session_id,
                      license_tier, feature
        security_config: Security configuration with columns:
                        securityrole, AOTName, AccessLevel, LicenseType, etc.
        pricing_config: Pricing configuration dictionary.
        minority_threshold: Usage percentage below which license is "minority" (default 15).
        analysis_period_days: Number of days to analyze (default 90).

    Returns:
        List of LicenseRecommendation objects for users with minority licenses.
    """
    results: list[LicenseRecommendation] = []

    if user_activity.empty:
        return results

    # Build form-to-license mapping from activity data
    form_to_license = _get_form_to_license_mapping(user_activity)

    # Process each unique user
    for user_id in user_activity["user_id"].unique():
        user_data = user_activity[user_activity["user_id"] == user_id].copy()

        if user_data.empty:
            continue

        # Calculate usage by license
        usage_by_license = _calculate_usage_by_license(user_data, form_to_license)

        # Skip single-license users
        if len(usage_by_license) < 2:
            continue

        # Identify minority licenses
        minority_licenses: list[dict[str, Any]] = []
        for license_type, stats in usage_by_license.items():
            if stats["percentage"] < minority_threshold:
                minority_licenses.append(
                    {
                        "license": license_type,
                        "percentage": stats["percentage"],
                        "form_count": stats["form_count"],
                        "access_count": stats["access_count"],
                        "read_count": stats["read_count"],
                        "write_count": stats["write_count"],
                    }
                )

        # Skip if no minorities detected
        if not minority_licenses:
            continue

        # Find dominant (highest percentage) license
        dominant_license = max(
            usage_by_license.items(),
            key=lambda x: x[1]["percentage"],
        )[0]

        # Calculate current and recommended costs
        try:
            current_cost = sum(
                _get_license_price(pricing_config, lic) for lic in usage_by_license.keys()
            )
        except KeyError:
            # Skip if pricing data incomplete
            continue

        # Recommended: remove minority licenses
        recommended_cost = current_cost - sum(
            _get_license_price(pricing_config, m["license"]) for m in minority_licenses
        )

        monthly_savings = current_cost - recommended_cost
        annual_savings = monthly_savings * 12

        # Assess confidence
        confidence_score = _assess_confidence(usage_by_license, minority_licenses)
        confidence_level = _determine_confidence_level(confidence_score)

        # Generate recommendation reason
        reason = _generate_recommendation_reason(user_id, usage_by_license, minority_licenses)

        # Determine action
        if monthly_savings > 100 and len(minority_licenses) <= 1:
            action = RecommendationAction.REVIEW_REQUIRED
        elif monthly_savings > 50:
            action = RecommendationAction.REVIEW_REQUIRED
        else:
            action = RecommendationAction.NO_CHANGE

        # Build recommendation
        recommendation = LicenseRecommendation(
            algorithm_id="2.5",
            recommendation_id=str(uuid.uuid4()),
            generated_at=datetime.now(UTC),
            user_id=user_id,
            user_name=None,
            user_email=None,
            current_license=dominant_license,
            current_license_cost_monthly=current_cost,
            action=action,
            recommended_license=dominant_license if monthly_savings > 0 else None,
            recommended_license_cost_monthly=recommended_cost if monthly_savings > 0 else None,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            reason=reason,
            savings=(
                SavingsEstimate(
                    monthly_current_cost=current_cost,
                    monthly_recommended_cost=recommended_cost,
                    monthly_savings=monthly_savings,
                    annual_savings=annual_savings,
                    confidence_adjusted_savings=annual_savings * confidence_score,
                )
                if monthly_savings > 0
                else None
            ),
            analysis_period_days=analysis_period_days,
            sample_size=len(user_data),
            data_completeness=1.0,
            safe_to_automate=(confidence_level == ConfidenceLevel.HIGH and monthly_savings > 100),
            requires_approval=True,
        )

        results.append(recommendation)

    # Sort by potential savings (descending)
    results.sort(
        key=lambda r: (r.savings.annual_savings if r.savings else 0.0),
        reverse=True,
    )

    return results
