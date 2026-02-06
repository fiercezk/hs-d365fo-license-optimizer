"""Algorithm 4.1: Device License Opportunity Detector.

Identifies devices shared by multiple users that would benefit from device
licenses instead of individual user licenses. Analyzes usage patterns to
detect warehouse scanners, POS terminals, and manufacturing floor devices
suitable for conversion to shared device licenses.

Follows the pseudocode specification from Requirements/07-Advanced-Algorithms-
Expansion.md, lines 922-1115.

Key detection criteria:
  - Minimum 3 unique users per device (true shared device, not personal)
  - Maximum 1 concurrent user (peak concurrent = 1, no simultaneous usage)
  - Not dominated by single user (dedicated_user_percentage < 80%)
  - Device type in [Warehouse, Manufacturing, POS, ShopFloor, Kiosk]

Output: List of device license opportunities with:
  - device_id, location, device_type
  - unique_users, current cost vs device license cost
  - monthly/annual savings estimates
  - confidence score and recommendation action
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

# Device types eligible for device license conversion
ELIGIBLE_DEVICE_TYPES: frozenset[str] = frozenset(
    {
        "Warehouse",
        "Manufacturing",
        "POS",
        "ShopFloor",
        "Kiosk",
    }
)

# License type priority for determining a user's current/highest license
_DEFAULT_LICENSE_PRIORITY: dict[str, int] = {
    "Team Members": 60,
    "Operations - Activity": 90,
    "Operations": 90,
    "SCM": 180,
    "Finance": 180,
    "Commerce": 180,
    "Device License": 80,
}


def _get_license_price(pricing_config: dict[str, Any], license_type: str) -> float:
    """Retrieve the monthly price for a given license type.

    Args:
        pricing_config: Parsed pricing.json dictionary.
        license_type: License type name (e.g., "Commerce", "SCM").

    Returns:
        Monthly price in USD.

    Raises:
        KeyError: If license type not found in pricing config.
    """
    licenses_dict: dict[str, Any] = pricing_config.get("licenses", {})
    # Handle both snake_case (from config) and space-case (from data)
    normalized_name = license_type.lower().replace(" ", "_")
    for config_key, config_data in licenses_dict.items():
        if config_key.lower() == normalized_name:
            price_key = "pricePerUserPerMonth"
            if price_key in config_data:
                return float(config_data[price_key])
    # Fallback if not found
    raise KeyError(f"License type '{license_type}' not found in pricing config")


def _get_device_license_price(pricing_config: dict[str, Any]) -> float:
    """Retrieve the device license monthly price.

    Args:
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        Monthly device license price in USD.
    """
    licenses_dict: dict[str, Any] = pricing_config.get("licenses", {})
    for config_key, config_data in licenses_dict.items():
        if config_key.lower() == "device":
            # Device licenses use pricePerDevicePerMonth
            price_key = "pricePerDevicePerMonth"
            if price_key in config_data:
                return float(config_data[price_key])
    # Fallback to $80 if not found
    return 80.0


def _determine_current_license(
    user_activity: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> str:
    """Determine a user's current license from highest-tier activity.

    The user's current license is the most expensive license tier observed
    across all their activity records.

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
    if not unique_tiers:
        return "Operations"  # Fallback

    best_license: str = unique_tiers[0]
    best_priority: int = priority_map.get(best_license, 0)

    for tier in unique_tiers[1:]:
        tier_priority: int = priority_map.get(tier, 0)
        if tier_priority > best_priority:
            best_license = tier
            best_priority = tier_priority

    return best_license


def _analyze_device_usage_pattern(
    device_df: pd.DataFrame,
) -> dict[str, Any]:
    """Analyze usage patterns for a device.

    Calculates:
    - Number of unique users
    - Peak concurrent sessions (using session_id uniqueness per timestamp)
    - Average concurrent sessions
    - Dominant user percentage
    - User rotation level (HIGH/MEDIUM/LOW)

    Args:
        device_df: Activity rows for a single device.

    Returns:
        Dictionary with pattern analysis metrics.
    """
    if len(device_df) == 0:
        return {
            "unique_users": 0,
            "total_sessions": 0,
            "peak_concurrent": 0,
            "avg_concurrent": 0.0,
            "dominant_user_percentage": 0.0,
            "rotation_level": "LOW",
        }

    unique_users = device_df["user_id"].nunique()
    total_operations = len(device_df)

    # Calculate concurrent sessions by timestamp
    # Group by timestamp and count unique session_ids (each session = one user)
    concurrent_by_timestamp = device_df.groupby("timestamp")["session_id"].nunique()
    peak_concurrent = int(concurrent_by_timestamp.max()) if len(concurrent_by_timestamp) > 0 else 0
    avg_concurrent = (
        float(concurrent_by_timestamp.mean()) if len(concurrent_by_timestamp) > 0 else 0.0
    )

    # Calculate dominant user percentage
    user_operation_counts = device_df["user_id"].value_counts()
    dominant_user_ops = int(user_operation_counts.iloc[0]) if len(user_operation_counts) > 0 else 0
    dominant_user_percentage = (
        (dominant_user_ops / total_operations) * 100.0 if total_operations > 0 else 0.0
    )

    # Classify rotation level
    if dominant_user_percentage > 80.0:
        rotation_level = "LOW"
    elif dominant_user_percentage > 50.0:
        rotation_level = "MEDIUM"
    else:
        rotation_level = "HIGH"

    return {
        "unique_users": unique_users,
        "total_sessions": len(device_df.groupby("session_id").size()),  # Count unique sessions
        "peak_concurrent": peak_concurrent,
        "avg_concurrent": avg_concurrent,
        "dominant_user_percentage": dominant_user_percentage,
        "rotation_level": rotation_level,
    }


def _is_device_license_eligible(
    usage_pattern: dict[str, Any],
    device_type: str,
) -> bool:
    """Check if device meets eligibility criteria for device license conversion.

    Criteria:
    1. Minimum 3 unique users
    2. Maximum 1 concurrent user (peak = 1)
    3. Not dominated by single user (< 80%)
    4. Device type in [Warehouse, Manufacturing, POS, ShopFloor, Kiosk]

    Args:
        usage_pattern: Output from _analyze_device_usage_pattern()
        device_type: Device type string (e.g., "Warehouse")

    Returns:
        True if device meets all eligibility criteria, False otherwise.
    """
    # Criterion 1: At least 3 unique users
    if usage_pattern["unique_users"] < 3:
        return False

    # Criterion 2: Maximum 1 concurrent user
    if usage_pattern["peak_concurrent"] > 1:
        return False

    # Criterion 3: Not dominated by single user
    if usage_pattern["dominant_user_percentage"] > 80.0:
        return False

    # Criterion 4: Device type is eligible
    if device_type not in ELIGIBLE_DEVICE_TYPES:
        return False

    return True


def _calculate_confidence_score(
    unique_users: int,
    dominant_user_percentage: float,
    peak_concurrent: int,
) -> tuple[float, ConfidenceLevel]:
    """Calculate confidence score for device license recommendation.

    Score factors:
    - Number of users (more users = higher confidence in shared device)
    - User dominance (lower = more true sharing)
    - Concurrent usage (lower = safer to convert)

    Args:
        unique_users: Number of unique users on device
        dominant_user_percentage: Percentage of operations by dominant user
        peak_concurrent: Maximum concurrent sessions

    Returns:
        Tuple of (confidence_score, confidence_level)
    """
    # Base score starts at 0.5
    score = 0.5

    # Bonus for number of users (up to +0.25)
    if unique_users >= 5:
        score += 0.25
    elif unique_users >= 4:
        score += 0.20
    elif unique_users >= 3:
        score += 0.15

    # Bonus for even user distribution (up to +0.25)
    if dominant_user_percentage <= 40.0:
        score += 0.25
    elif dominant_user_percentage <= 50.0:
        score += 0.20
    elif dominant_user_percentage <= 60.0:
        score += 0.10

    # Ensure peak concurrent is 1 for eligibility (if we got here, it is)
    if peak_concurrent == 1:
        score += 0.10

    # Cap at 1.0
    score = min(score, 1.0)

    # Determine confidence level
    if score >= 0.90:
        level = ConfidenceLevel.HIGH
    elif score >= 0.70:
        level = ConfidenceLevel.MEDIUM
    elif score >= 0.50:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.INSUFFICIENT_DATA

    return score, level


def detect_device_license_opportunities(
    activity_data: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> list[LicenseRecommendation]:
    """Detect devices suitable for device license conversion.

    Analyzes user activity data to identify devices (warehouse scanners, POS
    terminals, manufacturing floor devices) that would benefit from shared
    device licenses instead of individual user licenses.

    Args:
        activity_data: DataFrame with columns: user_id, timestamp, menu_item,
            action, session_id, license_tier, feature, device_id, device_type,
            location.
        pricing_config: Parsed pricing.json dictionary with license costs.

    Returns:
        List of LicenseRecommendation objects for device license opportunities,
        sorted by annual savings in descending order.
    """
    recommendations: list[LicenseRecommendation] = []

    if len(activity_data) == 0:
        return recommendations

    # Get device license price
    device_license_price = _get_device_license_price(pricing_config)

    # Analyze each device
    for device_id, device_df in activity_data.groupby("device_id"):
        device_id_str: str = str(device_id)

        # Get device metadata
        device_type: str = device_df["device_type"].iloc[0]
        location: str = device_df["location"].iloc[0]

        # Analyze usage pattern
        usage_pattern = _analyze_device_usage_pattern(device_df)

        # Check eligibility
        if not _is_device_license_eligible(usage_pattern, device_type):
            continue

        # Get users on this device
        device_users = device_df["user_id"].unique().tolist()

        # Calculate current license cost (highest license tier per user)
        current_cost = 0.0
        for user_id in device_users:
            user_activity = device_df[device_df["user_id"] == user_id]
            current_license = _determine_current_license(user_activity, pricing_config)
            try:
                user_license_cost = _get_license_price(pricing_config, current_license)
                current_cost += user_license_cost
            except KeyError:
                # If license not found, estimate at $90
                current_cost += 90.0

        # Monthly savings = current cost - device license cost
        monthly_savings = current_cost - device_license_price
        annual_savings = monthly_savings * 12.0

        # Calculate confidence
        confidence_score, confidence_level = _calculate_confidence_score(
            unique_users=usage_pattern["unique_users"],
            dominant_user_percentage=usage_pattern["dominant_user_percentage"],
            peak_concurrent=usage_pattern["peak_concurrent"],
        )

        # Build savings estimate
        savings = SavingsEstimate(
            monthly_current_cost=current_cost,
            monthly_recommended_cost=device_license_price,
            monthly_savings=monthly_savings,
            annual_savings=annual_savings,
            confidence_adjusted_savings=round(annual_savings * confidence_score, 2),
        )

        # Build recommendation reason
        primary_factor = (
            f"{usage_pattern['unique_users']} users share {device_id_str} "
            f"({usage_pattern['rotation_level']} rotation, "
            f"{usage_pattern['dominant_user_percentage']:.1f}% dominant user)"
        )
        supporting_factors = [
            f"Location: {location}",
            f"Device type: {device_type}",
            f"Peak concurrent users: {usage_pattern['peak_concurrent']}",
            f"User rotation level: {usage_pattern['rotation_level']}",
        ]
        risk_factors = []
        if usage_pattern["dominant_user_percentage"] > 50.0:
            risk_factors.append("Moderate dominance by single user - verify device sharing intent")

        reason = RecommendationReason(
            primary_factor=primary_factor,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            data_quality_notes=[],
        )

        # Determine automation safety
        safe_to_automate = confidence_level == ConfidenceLevel.HIGH

        rec = LicenseRecommendation(
            algorithm_id="4.1",
            recommendation_id=str(uuid.uuid4()),
            generated_at=datetime.now(UTC),
            user_id=device_id_str,  # For device recommendations, user_id = device_id
            user_name=device_id_str,
            current_license=f"User licenses (${current_cost:.0f}/month)",
            current_license_cost_monthly=current_cost,
            action=RecommendationAction.ADD_LICENSE,  # Add device license
            recommended_license="Device License",
            recommended_license_cost_monthly=device_license_price,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            reason=reason,
            savings=savings,
            analysis_period_days=90,
            sample_size=len(device_df),
            data_completeness=1.0,
            safe_to_automate=safe_to_automate,
            requires_approval=not safe_to_automate,
            implementation_notes=[
                f"Convert {usage_pattern['unique_users']} user licenses to 1 device license",
                f"Device location: {location}",
                f"Estimated ROI: {annual_savings / 100:.1f} months (rough estimate)",
            ],
            tags=_compute_tags(
                unique_users=usage_pattern["unique_users"],
                annual_savings=annual_savings,
                confidence_level=confidence_level,
                device_type=device_type,
            ),
        )

        recommendations.append(rec)

    # Sort by annual savings descending
    recommendations.sort(
        key=lambda r: r.savings.annual_savings if r.savings else 0.0,
        reverse=True,
    )

    return recommendations


def _compute_tags(
    unique_users: int,
    annual_savings: float,
    confidence_level: ConfidenceLevel,
    device_type: str,
) -> list[str]:
    """Compute categorization tags for a device license recommendation.

    Args:
        unique_users: Number of users on device
        annual_savings: Estimated annual savings in USD
        confidence_level: Confidence level of the recommendation
        device_type: Device type (Warehouse, POS, etc.)

    Returns:
        List of string tags for filtering and categorization.
    """
    tags: list[str] = []

    # Device type tags
    tags.append(f"device_type_{device_type.lower()}")

    # User count tags
    if unique_users >= 5:
        tags.append("high_user_count")
    elif unique_users >= 3:
        tags.append("moderate_user_count")

    # Savings tags
    if annual_savings >= 5000.0:
        tags.append("very_high_savings")
    elif annual_savings >= 2000.0:
        tags.append("high_savings")
    elif annual_savings >= 500.0:
        tags.append("moderate_savings")

    # Confidence tags
    if confidence_level == ConfidenceLevel.HIGH:
        tags.append("high_confidence")
    elif confidence_level == ConfidenceLevel.MEDIUM:
        tags.append("medium_confidence")
    elif confidence_level == ConfidenceLevel.LOW:
        tags.append("low_confidence")

    tags.append("device_license_opportunity")

    return tags
