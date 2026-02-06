"""Algorithm 5.1: License Cost Trend Analysis.

Analyzes historical license usage patterns to identify trends, predict future
demand, detect anomalies, and provide actionable recommendations for license
planning and procurement.

See Requirements/11-License-Trend-Analysis-Algorithm.md for specification.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4
import calendar

import pandas as pd
import numpy as np

from ..models.output_schemas import (
    LicenseTrendAnalysis,
    GrowthRate,
    SeasonalPattern,
    LicenseAnomalyRecord,
    ForecastMonth,
    TrendAnalysisRecommendation,
    ConfidenceLevel,
)

# ============================================================================
# MAIN ALGORITHM
# ============================================================================


def analyze_license_trends(
    monthly_data: list[dict[str, Any]],
    historical_months: int = 12,
    forecast_months: int = 12,
    seasonal_deviation_threshold: float = 10.0,
    anomaly_std_dev_threshold: float = 2.0,
    sudden_change_threshold: float = 20.0,
) -> LicenseTrendAnalysis:
    """Analyze historical license trends and generate forecasts.

    This is the main Algorithm 5.1 entry point. It orchestrates all
    sub-algorithms to produce a comprehensive trend analysis report.

    Args:
        monthly_data: List of monthly records with date, user_count, license_cost.
        historical_months: Number of months to analyze (default 12).
        forecast_months: Number of months to forecast (default 12).
        seasonal_deviation_threshold: Percentage deviation to flag seasonal (default 10%).
        anomaly_std_dev_threshold: Standard deviations for anomaly detection (default 2.0).
        sudden_change_threshold: Percentage change to flag sudden change (default 20%).

    Returns:
        LicenseTrendAnalysis with trends, forecasts, anomalies, and recommendations.

    See Requirements/11: Section "Pseudocode" for algorithm specification.
    """
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(monthly_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(historical_months)

    # Current state (last month in data)
    current_month = df.iloc[-1]
    current_users = int(current_month["user_count"])
    current_cost = float(current_month["license_cost"])

    # Analyze growth trends
    growth_rates = calculate_growth_rates(monthly_data=monthly_data)

    # Detect seasonal patterns (requires 12+ months)
    seasonal_patterns = detect_seasonal_patterns(
        monthly_data=monthly_data,
        historical_months=len(df),
        deviation_threshold=seasonal_deviation_threshold,
    )

    # Detect anomalies
    anomalies = detect_anomalies(
        monthly_data=monthly_data,
        std_dev_threshold=anomaly_std_dev_threshold,
        sudden_change_threshold=sudden_change_threshold,
    )

    # Generate forecast
    forecast = generate_forecast(
        monthly_data=monthly_data,
        growth_rates=growth_rates,
        seasonal_patterns=seasonal_patterns,
        forecast_months=forecast_months,
    )

    # Generate recommendations
    recommendations = generate_recommendations(
        current_users=current_users,
        current_cost=current_cost,
        growth_rates=growth_rates,
        seasonal_patterns=seasonal_patterns,
        forecast=forecast,
    )

    # Calculate confidence score
    confidence_score, confidence_level, confidence_factors = calculate_confidence(
        historical_months=len(df),
        growth_rates=growth_rates,
        anomalies=anomalies,
    )

    # Build output
    analysis = LicenseTrendAnalysis(
        analysis_id=str(uuid4()),
        analysis_period_months=len(df),
        period_start=df.iloc[0]["date"].to_pydatetime(),
        period_end=df.iloc[-1]["date"].to_pydatetime(),
        current_users=current_users,
        current_monthly_cost=current_cost,
        growth_rates=growth_rates,
        seasonal_patterns=seasonal_patterns,
        anomalies=anomalies,
        forecast_months=forecast_months,
        forecast=forecast,
        recommendations=recommendations,
        overall_confidence=confidence_level,
        confidence_score=confidence_score,
        confidence_factors=confidence_factors,
    )

    return analysis


# ============================================================================
# SUB-ALGORITHM: Calculate Growth Rates
# ============================================================================


def calculate_growth_rates(monthly_data: list[dict[str, Any]]) -> GrowthRate:
    """Calculate month-over-month, quarter-over-quarter, and year-over-year growth.

    Args:
        monthly_data: List of monthly records with user_count.

    Returns:
        GrowthRate with growth statistics and trend classification.

    See Requirements/11: CalculateMoMGrowth pseudocode.
    """
    if len(monthly_data) < 2:
        raise ValueError("Need at least 2 months of data for growth calculation")

    df = pd.DataFrame(monthly_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    user_counts = df["user_count"].values

    # Overall growth rate
    start_users = user_counts[0]
    end_users = user_counts[-1]
    overall_growth = ((end_users - start_users) / start_users) * 100

    # Month-over-month growth
    mom_growths = []
    for i in range(1, len(user_counts)):
        growth = ((user_counts[i] - user_counts[i - 1]) / user_counts[i - 1]) * 100
        mom_growths.append(growth)

    mom_average = np.mean(mom_growths)
    mom_min = np.min(mom_growths)
    mom_max = np.max(mom_growths)

    # Quarter-over-quarter growth
    qoq_growths = []
    for i in range(3, len(user_counts)):
        growth = ((user_counts[i] - user_counts[i - 3]) / user_counts[i - 3]) * 100
        qoq_growths.append(growth)

    qoq_average = np.mean(qoq_growths) if qoq_growths else 0

    # Year-over-year growth
    yoy_growths = []
    for i in range(12, len(user_counts)):
        growth = ((user_counts[i] - user_counts[i - 12]) / user_counts[i - 12]) * 100
        yoy_growths.append(growth)

    yoy_average = np.mean(yoy_growths) if yoy_growths else mom_average

    # Determine trend
    if abs(mom_average) < 1.0:
        trend = "STABLE"
    elif mom_average > 0:
        trend = "GROWING"
    else:
        trend = "DECLINING"

    return GrowthRate(
        overall_percent=overall_growth,
        period_months=len(user_counts),
        mom_average=mom_average,
        mom_min=mom_min,
        mom_max=mom_max,
        qoq_average=qoq_average,
        yoy_average=yoy_average,
        trend=trend,
    )


# ============================================================================
# SUB-ALGORITHM: Detect Seasonal Patterns
# ============================================================================


def detect_seasonal_patterns(
    monthly_data: list[dict[str, Any]],
    historical_months: int = 12,
    deviation_threshold: float = 10.0,
) -> list[SeasonalPattern]:
    """Detect recurring seasonal patterns in license usage.

    Requires at least 12 months of data. Groups data by calendar month
    and detects if specific months consistently deviate from average.

    Args:
        monthly_data: List of monthly records.
        historical_months: Months to analyze.
        deviation_threshold: Percentage deviation to flag as seasonal (default 10%).

    Returns:
        List of SeasonalPattern records.

    See Requirements/11: DetectSeasonalPatterns pseudocode.
    """
    if len(monthly_data) < 12:
        return []

    df = pd.DataFrame(monthly_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(historical_months)

    # Extract month and year
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year

    # Calculate overall average
    overall_avg = df["user_count"].mean()

    patterns = []

    # Group by calendar month
    for month_num in range(1, 13):
        month_data = df[df["month"] == month_num]

        if len(month_data) < 2:
            # Need at least 2 occurrences to call it a pattern
            continue

        month_avg = month_data["user_count"].mean()
        deviation = ((month_avg - overall_avg) / overall_avg) * 100

        # Only flag if deviation exceeds threshold
        if abs(deviation) > deviation_threshold:
            pattern = SeasonalPattern(
                month=month_num,
                month_name=calendar.month_name[month_num],
                pattern_type="HIGH" if deviation > 0 else "LOW",
                deviation_percent=deviation,
                avg_user_count=month_avg,
                occurrences=len(month_data),
                years=sorted(month_data["year"].unique().tolist()),
            )
            patterns.append(pattern)

    return patterns


# ============================================================================
# SUB-ALGORITHM: Detect Anomalies
# ============================================================================


def detect_anomalies(
    monthly_data: list[dict[str, Any]],
    std_dev_threshold: float = 2.0,
    sudden_change_threshold: float = 20.0,
) -> list[LicenseAnomalyRecord]:
    """Detect statistical anomalies and sudden changes in license data.

    Uses z-score analysis for outliers and month-over-month percentage
    change detection for sudden shifts.

    Args:
        monthly_data: List of monthly records.
        std_dev_threshold: Standard deviations for outlier detection (default 2.0).
        sudden_change_threshold: Percentage change to flag sudden change (default 20%).

    Returns:
        List of LicenseAnomalyRecord objects.

    See Requirements/11: DetectAnomalies pseudocode.
    """
    df = pd.DataFrame(monthly_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    anomalies = []

    # Statistical anomalies (z-score based)
    user_counts = np.asarray(df["user_count"].values, dtype=float)
    costs = np.asarray(df["license_cost"].values, dtype=float)

    user_mean = float(np.mean(user_counts))
    user_std = float(np.std(user_counts))
    cost_mean = float(np.mean(costs))
    cost_std = float(np.std(costs))

    for idx, row in df.iterrows():
        # User count anomaly
        if user_std > 0:
            user_zscore = (row["user_count"] - user_mean) / user_std
            if abs(user_zscore) >= std_dev_threshold:
                severity = "HIGH" if abs(user_zscore) > 3.0 else "MEDIUM"
                anomaly = LicenseAnomalyRecord(
                    anomaly_type="USER_COUNT_ANOMALY",
                    date=row["date"],
                    value=row["user_count"],
                    expected=user_mean,
                    z_score=user_zscore,
                    severity=severity,
                    description=(
                        f"User count {row['user_count']:.0f} significantly "
                        f"{'higher' if user_zscore > 0 else 'lower'} than "
                        f"expected {user_mean:.0f}"
                    ),
                )
                anomalies.append(anomaly)

        # Cost anomaly
        if cost_std > 0:
            cost_zscore = (row["license_cost"] - cost_mean) / cost_std
            if abs(cost_zscore) >= std_dev_threshold:
                severity = "HIGH" if abs(cost_zscore) > 3.0 else "MEDIUM"
                anomaly = LicenseAnomalyRecord(
                    anomaly_type="COST_ANOMALY",
                    date=row["date"],
                    value=row["license_cost"],
                    expected=cost_mean,
                    z_score=cost_zscore,
                    severity=severity,
                    description=(
                        f"Cost ${row['license_cost']:.0f} significantly "
                        f"{'higher' if cost_zscore > 0 else 'lower'} than "
                        f"expected ${cost_mean:.0f}"
                    ),
                )
                anomalies.append(anomaly)

    # Sudden changes (month-over-month)
    for i in range(1, len(df)):
        prev_row = df.iloc[i - 1]
        curr_row = df.iloc[i]

        user_change = (
            (curr_row["user_count"] - prev_row["user_count"]) / prev_row["user_count"]
        ) * 100

        if abs(user_change) >= sudden_change_threshold:
            severity = "HIGH" if abs(user_change) > 40 else "MEDIUM"
            anomaly = LicenseAnomalyRecord(
                anomaly_type="SUDDEN_USER_CHANGE",
                date=curr_row["date"],
                value=curr_row["user_count"],
                expected=prev_row["user_count"],
                z_score=user_change / 10,  # Approximate z-score
                severity=severity,
                description=(
                    f"Sudden {abs(user_change):.1f}% "
                    f"{'increase' if user_change > 0 else 'decrease'} "
                    f"in user count"
                ),
            )
            anomalies.append(anomaly)

    return anomalies


# ============================================================================
# SUB-ALGORITHM: Generate Forecast
# ============================================================================


def generate_forecast(
    monthly_data: list[dict[str, Any]],
    growth_rates: GrowthRate,
    seasonal_patterns: list[SeasonalPattern],
    forecast_months: int = 12,
) -> list[ForecastMonth]:
    """Generate forward-looking license demand forecast.

    Applies base growth rate and seasonal adjustments to project future
    license needs and costs.

    Args:
        monthly_data: Historical monthly data.
        growth_rates: Calculated growth statistics.
        seasonal_patterns: Detected seasonal patterns.
        forecast_months: Number of months to forecast (default 12).

    Returns:
        List of ForecastMonth records.

    See Requirements/11: GenerateForecast pseudocode.
    """
    df = pd.DataFrame(monthly_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Base month (last historical month)
    base_month = df.iloc[-1]
    base_date = pd.to_datetime(base_month["date"])
    base_users = base_month["user_count"]
    base_cost = base_month["license_cost"]
    cost_per_user = base_cost / base_users if base_users > 0 else 0

    # Growth rate (MoM)
    growth_rate = growth_rates.mom_average / 100

    # Create seasonal adjustment map
    seasonal_map = {}
    for pattern in seasonal_patterns:
        seasonal_map[pattern.month] = pattern.deviation_percent / 100

    forecast = []

    for i in range(1, forecast_months + 1):
        # Calculate forecast date
        forecast_date = base_date + timedelta(days=30 * i)
        forecast_month = forecast_date.month

        # Base forecast: apply growth
        forecast_users = base_users * ((1 + growth_rate) ** i)

        # Apply seasonal adjustment if exists
        seasonal_adj = 0.0
        if forecast_month in seasonal_map:
            seasonal_adj = seasonal_map[forecast_month]
            forecast_users = forecast_users * (1 + seasonal_adj)

        # Round to nearest whole number
        forecast_users = int(round(forecast_users))

        # Calculate cost
        forecast_cost = forecast_users * cost_per_user

        # Growth percentage from base
        growth_from_base = ((forecast_users - base_users) / base_users) * 100

        # Confidence decreases further into future
        base_confidence = 100
        confidence_reduction = (i / forecast_months) * 40
        confidence = max(20, min(100, base_confidence - confidence_reduction))

        # Add seasonal note if applicable
        notes = []
        if forecast_month in seasonal_map and seasonal_adj != 0:
            deviation = seasonal_map[forecast_month] * 100
            notes.append(f"Seasonal {'peak' if deviation > 0 else 'dip'} " f"({deviation:+.1f}%)")

        month_forecast = ForecastMonth(
            month_number=i,
            date=forecast_date.to_pydatetime(),
            month_name=calendar.month_name[forecast_month],
            forecast_users=forecast_users,
            forecast_cost=forecast_cost,
            growth_from_base_percent=growth_from_base,
            confidence=int(confidence),
            seasonal_adjustment_percent=seasonal_adj * 100,
            notes=notes,
        )
        forecast.append(month_forecast)

    return forecast


# ============================================================================
# SUB-ALGORITHM: Generate Recommendations
# ============================================================================


def generate_recommendations(
    current_users: int,
    current_cost: float,
    growth_rates: GrowthRate,
    seasonal_patterns: list[SeasonalPattern],
    forecast: list[ForecastMonth],
) -> list[TrendAnalysisRecommendation]:
    """Generate actionable recommendations based on trends and forecasts.

    Args:
        current_users: Current total user count.
        current_cost: Current monthly cost.
        growth_rates: Growth rate analysis.
        seasonal_patterns: Detected seasonal patterns.
        forecast: Generated forecast.

    Returns:
        List of TrendAnalysisRecommendation objects.

    See Requirements/11: GenerateRecommendations pseudocode.
    """
    recommendations = []

    # 1. Procurement recommendations
    if len(forecast) >= 6:
        growth_6m = forecast[5].forecast_users - current_users
        if growth_6m > 0:
            recommendations.append(
                TrendAnalysisRecommendation(
                    recommendation_type="PROCUREMENT_NEEDED",
                    description=(
                        f"Procure {int(growth_6m)} additional licenses " f"in next 6 months"
                    ),
                    priority="HIGH" if growth_6m > 100 else "MEDIUM",
                    timeline="Next 6 months",
                    estimated_impact=(
                        growth_6m * (current_cost / current_users) if current_users > 0 else 0
                    ),
                    action_items=[
                        "Identify license SKUs needed",
                        "Request quotes from vendor",
                        "Plan procurement timeline",
                    ],
                )
            )

    # 2. Seasonal pattern recommendations
    for pattern in seasonal_patterns:
        if pattern.pattern_type == "HIGH" and pattern.deviation_percent > 15:
            recommendations.append(
                TrendAnalysisRecommendation(
                    recommendation_type="SEASONAL_DEMAND",
                    description=(
                        f"Expect {pattern.deviation_percent:.1f}% increase in "
                        f"{pattern.month_name} - plan temporary license"
                        f" procurement"
                    ),
                    priority="MEDIUM",
                    timeline=f"Before {pattern.month_name}",
                    estimated_impact=(pattern.deviation_percent / 100 * current_cost),
                    action_items=[
                        f"Identify temporary licenses for {pattern.month_name}",
                        "Negotiate temporary pricing",
                    ],
                )
            )

    # 3. Optimization recommendations
    if growth_rates.overall_percent < 0:
        recommendations.append(
            TrendAnalysisRecommendation(
                recommendation_type="DECLINING_TREND",
                description=(
                    f"User count declining {abs(growth_rates.overall_percent):.1f}%. "
                    f"Review license assignments for removal of unused "
                    f"licenses"
                ),
                priority="HIGH",
                timeline="Immediate",
                estimated_impact=abs(growth_rates.overall_percent / 100 * current_cost),
                action_items=[
                    "Audit inactive user accounts",
                    "Identify licenses for removal",
                    "Plan license downgrade schedule",
                ],
            )
        )

    # 4. Budget forecast recommendation
    if len(forecast) == 12:
        total_forecast_cost = sum(m.forecast_cost for m in forecast)
        current_annual = current_cost * 12
        budget_change = total_forecast_cost - current_annual
        budget_change_percent = (budget_change / current_annual * 100) if current_annual > 0 else 0

        recommendations.append(
            TrendAnalysisRecommendation(
                recommendation_type="BUDGET_FORECAST",
                description=(
                    f"Forecasted 12-month license cost: "
                    f"${total_forecast_cost:,.0f} "
                    f"({budget_change_percent:+.1f}% vs. current)"
                ),
                priority="CRITICAL",
                timeline="Next 12 months",
                estimated_impact=budget_change,
                action_items=[
                    f"Budget ${total_forecast_cost / 12:,.0f}/month for licenses",
                    "Communicate forecast to finance team",
                    "Review vendor agreements",
                ],
            )
        )

    return recommendations


# ============================================================================
# HELPER: Calculate Confidence Score
# ============================================================================


def calculate_confidence(
    historical_months: int,
    growth_rates: GrowthRate,
    anomalies: list[LicenseAnomalyRecord],
) -> tuple[float, ConfidenceLevel, dict[str, Any]]:
    """Calculate overall confidence score for analysis.

    Considers:
    - Data quality (more months = higher confidence)
    - Trend stability (consistent trends = higher confidence)
    - Anomalies (fewer anomalies = higher confidence)

    Args:
        historical_months: Number of months analyzed.
        growth_rates: Growth rate analysis.
        anomalies: Detected anomalies.

    Returns:
        Tuple of (confidence_score, confidence_level, confidence_factors).

    See Requirements/11: CalculateConfidence pseudocode.
    """
    score = 100.0
    factors = {}

    # Factor 1: Data quality
    if historical_months >= 24:
        factors["data_quality"] = 0
    elif historical_months >= 12:
        factors["data_quality"] = -10
        score -= 10
    elif historical_months >= 6:
        factors["data_quality"] = -30
        score -= 30
    else:
        factors["data_quality"] = -50
        score -= 50

    # Factor 2: Trend stability (using standard deviation of MoM growth)
    stability = abs(growth_rates.mom_average)
    if stability < 1.0:
        factors["trend_stability"] = 0
    elif stability < 3.0:
        factors["trend_stability"] = -5
        score -= 5
    else:
        factors["trend_stability"] = -15
        score -= 15

    # Factor 3: Anomalies
    anomaly_count = len(anomalies)
    if anomaly_count == 0:
        factors["anomalies"] = 0
    elif anomaly_count <= 2:
        factors["anomalies"] = -5
        score -= 5
    elif anomaly_count <= 5:
        factors["anomalies"] = -15
        score -= 15
    else:
        factors["anomalies"] = -30
        score -= 30

    # Clamp score between 0 and 100
    confidence_score = max(0.0, min(100.0, score)) / 100.0

    # Determine confidence level
    if confidence_score >= 0.80:
        confidence_level = ConfidenceLevel.HIGH
    elif confidence_score >= 0.60:
        confidence_level = ConfidenceLevel.MEDIUM
    elif confidence_score >= 0.50:
        confidence_level = ConfidenceLevel.LOW
    else:
        confidence_level = ConfidenceLevel.INSUFFICIENT_DATA

    return confidence_score, confidence_level, factors
