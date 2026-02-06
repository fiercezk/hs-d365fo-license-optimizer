"""Algorithm 7.1: License Utilization Trend Analyzer.

Analyzes license utilization trends over time, providing visibility into how
efficiently licenses are being used across the organization. Tracks the ratio
of active users to total licensed users per license type, detects
under-utilized and near-capacity pools, identifies declining and growing
trends, and calculates waste from unused licenses.

This algorithm differs from Algorithm 5.1 (License Cost Trend Analysis) which
focuses on aggregate cost and user count trends. Algorithm 7.1 focuses on
**utilization efficiency** -- the ratio of active to total licensed users --
per license type.

See Requirements/08-Algorithm-Review-Summary.md for high-level specification.

Key behaviors:
  - Utilization rate = active_users / total_licensed_users * 100
  - Under-utilized: utilization < 70% (configurable)
  - Near-capacity: utilization > 90% (configurable)
  - Declining trend: utilization dropping consistently over 3+ months
  - Growing trend: utilization increasing consistently over 3+ months
  - Waste calculation: (total - active) * price_per_license
  - Empty input: zero results, no errors
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from ..utils.pricing import get_license_price

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_UNDER_UTILIZED_THRESHOLD: float = 70.0
_DEFAULT_NEAR_CAPACITY_THRESHOLD: float = 90.0
_MIN_TREND_MONTHS: int = 3


# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------


class LicenseUtilization(BaseModel):
    """Utilization analysis for a single license type.

    Captures the current utilization rate, status classification, trend
    direction, waste calculation, and the monthly series used for analysis.
    """

    license_type: str = Field(description="License type name (e.g., 'Finance', 'SCM')")
    total_licenses: int = Field(description="Total purchased licenses", ge=0)
    active_users: int = Field(description="Currently active users", ge=0)
    current_utilization_percent: float = Field(
        description="Current utilization rate (active / total * 100)",
        ge=0.0,
        le=100.0,
    )
    status: str = Field(
        description="Utilization status: UNDER_UTILIZED, HEALTHY, or NEAR_CAPACITY"
    )
    trend: str = Field(
        description="Utilization trend: DECLINING, STABLE, or GROWING"
    )
    monthly_waste: float = Field(
        description="Monthly waste from unused licenses in USD",
        ge=0.0,
    )
    annual_waste: float = Field(
        description="Annual waste from unused licenses in USD",
        ge=0.0,
    )
    months_analyzed: int = Field(
        description="Number of months of data used in analysis",
        ge=0,
    )


class LicenseUtilizationAnalysis(BaseModel):
    """Complete output from Algorithm 7.1: License Utilization Trend Analyzer.

    Aggregates per-license-type utilization analyses and provides overall
    waste totals.
    """

    algorithm_id: str = Field(
        default="7.1",
        description="Algorithm identifier",
    )
    utilizations: list[LicenseUtilization] = Field(
        default_factory=list,
        description="Per-license-type utilization analysis results",
    )
    total_monthly_waste: float = Field(
        default=0.0,
        description="Sum of monthly waste across all license types (USD)",
        ge=0.0,
    )
    total_annual_waste: float = Field(
        default=0.0,
        description="Sum of annual waste across all license types (USD)",
        ge=0.0,
    )


# ---------------------------------------------------------------------------
# Trend Detection
# ---------------------------------------------------------------------------


def _detect_trend(utilization_series: list[float]) -> str:
    """Detect utilization trend from a chronologically ordered series.

    A trend is detected when the utilization rate changes in the same
    direction for 3 or more consecutive months. If fewer than 3 data
    points exist, or the series does not show a consistent direction,
    the trend is classified as STABLE.

    Args:
        utilization_series: Chronologically ordered utilization percentages
            (one per month).

    Returns:
        Trend classification: ``"DECLINING"``, ``"GROWING"``, or ``"STABLE"``.
    """
    if len(utilization_series) < _MIN_TREND_MONTHS:
        return "STABLE"

    # Compute consecutive month-over-month direction changes
    increasing_count: int = 0
    decreasing_count: int = 0

    for i in range(1, len(utilization_series)):
        diff: float = utilization_series[i] - utilization_series[i - 1]
        if diff > 0:
            increasing_count += 1
        elif diff < 0:
            decreasing_count += 1

    # Require a strong majority (>= threshold) of transitions in one direction
    # For 3+ month consistent trend, we need most transitions going same way
    if decreasing_count >= _MIN_TREND_MONTHS and decreasing_count > increasing_count:
        return "DECLINING"
    if increasing_count >= _MIN_TREND_MONTHS and increasing_count > decreasing_count:
        return "GROWING"

    return "STABLE"


# ---------------------------------------------------------------------------
# Status Classification
# ---------------------------------------------------------------------------


def _classify_status(
    utilization_percent: float,
    under_utilized_threshold: float,
    near_capacity_threshold: float,
) -> str:
    """Classify a utilization percentage into a status category.

    Args:
        utilization_percent: Current utilization rate (0-100).
        under_utilized_threshold: Threshold below which pool is under-utilized.
        near_capacity_threshold: Threshold above which pool is near capacity.

    Returns:
        Status string: ``"UNDER_UTILIZED"``, ``"HEALTHY"``, or ``"NEAR_CAPACITY"``.
    """
    if utilization_percent < under_utilized_threshold:
        return "UNDER_UTILIZED"
    if utilization_percent > near_capacity_threshold:
        return "NEAR_CAPACITY"
    return "HEALTHY"


# ---------------------------------------------------------------------------
# Main Algorithm
# ---------------------------------------------------------------------------


def analyze_license_utilization(
    license_inventory: pd.DataFrame,
    pricing_config: dict[str, Any],
    under_utilized_threshold: float = _DEFAULT_UNDER_UTILIZED_THRESHOLD,
    near_capacity_threshold: float = _DEFAULT_NEAR_CAPACITY_THRESHOLD,
) -> LicenseUtilizationAnalysis:
    """Analyze license utilization trends across all license types.

    This is the main Algorithm 7.1 entry point. It processes a license
    inventory DataFrame containing monthly snapshots of total licenses and
    active users per license type, and produces utilization analysis with
    status classification, trend detection, and waste calculation.

    Args:
        license_inventory: DataFrame with columns:
            - ``month`` (str, YYYY-MM): Calendar month.
            - ``license_type`` (str): License type name.
            - ``total_licenses`` (int): Total purchased licenses.
            - ``active_users`` (int): Number of active users.
        pricing_config: Parsed ``pricing.json`` dictionary. Must contain a
            ``licenses`` key mapping license identifiers to objects with a
            ``pricePerUserPerMonth`` field.
        under_utilized_threshold: Utilization percentage below which a pool
            is flagged as UNDER_UTILIZED (default 70.0).
        near_capacity_threshold: Utilization percentage above which a pool
            is flagged as NEAR_CAPACITY (default 90.0).

    Returns:
        LicenseUtilizationAnalysis containing per-license-type utilization
        records and aggregate waste totals.

    See Requirements/08 Algorithm 7.1 for specification.
    """
    # Handle empty input gracefully
    if license_inventory.empty:
        return LicenseUtilizationAnalysis()

    utilizations: list[LicenseUtilization] = []

    # Group by license type and analyze each independently
    for license_type, group_df in license_inventory.groupby("license_type"):
        license_type_str: str = str(license_type)

        # Sort by month chronologically
        sorted_df: pd.DataFrame = group_df.sort_values("month").reset_index(drop=True)

        # Build utilization series for trend detection
        utilization_series: list[float] = []
        for _, row in sorted_df.iterrows():
            total: int = int(row["total_licenses"])
            active: int = int(row["active_users"])
            util_pct: float = (active / total * 100.0) if total > 0 else 0.0
            utilization_series.append(util_pct)

        # Use the most recent month for current state
        latest_row = sorted_df.iloc[-1]
        current_total: int = int(latest_row["total_licenses"])
        current_active: int = int(latest_row["active_users"])
        current_utilization: float = (
            (current_active / current_total * 100.0) if current_total > 0 else 0.0
        )

        # Classify status
        status: str = _classify_status(
            current_utilization,
            under_utilized_threshold,
            near_capacity_threshold,
        )

        # Detect trend
        trend: str = _detect_trend(utilization_series)

        # Calculate waste using shared pricing utility
        unused_licenses: int = current_total - current_active
        try:
            price: float = get_license_price(pricing_config, license_type_str)
        except KeyError:
            # If license type not found in pricing, default to 0 waste
            price = 0.0

        monthly_waste: float = float(unused_licenses) * price
        annual_waste: float = monthly_waste * 12.0

        utilizations.append(
            LicenseUtilization(
                license_type=license_type_str,
                total_licenses=current_total,
                active_users=current_active,
                current_utilization_percent=round(current_utilization, 2),
                status=status,
                trend=trend,
                monthly_waste=monthly_waste,
                annual_waste=annual_waste,
                months_analyzed=len(sorted_df),
            )
        )

    # Compute aggregate waste
    total_monthly_waste: float = sum(u.monthly_waste for u in utilizations)
    total_annual_waste: float = sum(u.annual_waste for u in utilizations)

    return LicenseUtilizationAnalysis(
        utilizations=utilizations,
        total_monthly_waste=total_monthly_waste,
        total_annual_waste=total_annual_waste,
    )
