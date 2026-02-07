"""Algorithm 7.4: ROI Calculator for Optimization.

Calculates Return on Investment from optimization recommendations generated
by other algorithms, providing business justification for license changes.

Accepts a set of optimization recommendations and computes:
  - Total implementation cost (labor hours * hourly rate)
  - Total savings (monthly, annual, multi-year)
  - ROI metrics: payback period, NPV, ROI percentage
  - Confidence-adjusted savings (discount low-confidence recommendations)
  - Risk tier categorization (safe, moderate, high-risk)
  - Executive summary suitable for business cases

See Requirements/08-Algorithm-Review-Summary.md (Algorithm 7.4, Phase 2, Medium complexity).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input Model
# ---------------------------------------------------------------------------


class OptimizationRecommendationInput(BaseModel):
    """A single optimization recommendation fed into the ROI calculator.

    Typically produced by algorithms such as 2.2 (Read-Only Detector),
    4.2 (License Attach Optimizer), etc.

    Attributes:
        recommendation_id: Unique identifier for the recommendation.
        algorithm_id: Source algorithm (e.g., '2.2').
        user_id: Target user identifier.
        monthly_savings: Estimated monthly savings (USD) before confidence
            adjustment.
        confidence_score: Confidence in the recommendation (0.0-1.0).
        implementation_hours: Estimated labor hours to implement this change.
        risk_tier: Risk classification - one of 'safe', 'moderate', 'high-risk'.
    """

    recommendation_id: str = Field(description="Unique recommendation identifier")
    algorithm_id: str = Field(description="Source algorithm ID (e.g., '2.2')")
    user_id: str = Field(description="Target user identifier")
    monthly_savings: float = Field(description="Estimated monthly savings (USD)", ge=0)
    confidence_score: float = Field(
        description="Confidence in recommendation (0.0-1.0)", ge=0.0, le=1.0
    )
    implementation_hours: float = Field(
        description="Labor hours required to implement this change", ge=0
    )
    risk_tier: str = Field(
        description="Risk classification: 'safe', 'moderate', or 'high-risk'"
    )


# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------


class ROISummary(BaseModel):
    """Compact summary of ROI analysis for quick consumption.

    Attributes:
        total_recommendations: Number of recommendations analyzed.
        total_annual_savings: Raw annual savings (USD).
        confidence_adjusted_annual_savings: Confidence-weighted annual savings (USD).
        total_implementation_cost: Total one-time implementation cost (USD).
        roi_percentage: Return on Investment percentage.
        payback_period_months: Time to recoup implementation cost (months).
    """

    total_recommendations: int = Field(description="Number of recommendations analyzed")
    total_annual_savings: float = Field(description="Raw annual savings (USD)")
    confidence_adjusted_annual_savings: float = Field(
        description="Confidence-weighted annual savings (USD)"
    )
    total_implementation_cost: float = Field(
        description="Total one-time implementation cost (USD)"
    )
    roi_percentage: float = Field(description="ROI percentage")
    payback_period_months: float = Field(
        description="Time to recoup implementation cost (months)"
    )


class ROIAnalysis(BaseModel):
    """Complete ROI analysis output from Algorithm 7.4.

    Aggregates all recommendation savings, computes ROI metrics,
    risk-tier breakdowns, multi-year projections, NPV, and an
    executive summary suitable for business case presentations.

    Attributes:
        algorithm_id: Always '7.4'.
        total_recommendations: Count of input recommendations.
        total_monthly_savings: Raw total monthly savings (USD).
        total_annual_savings: Raw total annual savings (USD).
        confidence_adjusted_annual_savings: Annual savings weighted by confidence.
        total_implementation_cost: Total one-time cost (USD).
        roi_percentage: (annual_savings - cost) / cost * 100.
        payback_period_months: implementation_cost / monthly_savings.
        npv: Net Present Value over the projection horizon.
        year_1_savings: Confidence-adjusted first-year net savings.
        year_3_savings: Cumulative confidence-adjusted savings over 3 years.
        year_5_savings: Cumulative confidence-adjusted savings over 5 years.
        safe_recommendations_count: Count of 'safe' tier recommendations.
        moderate_recommendations_count: Count of 'moderate' tier recommendations.
        high_risk_recommendations_count: Count of 'high-risk' tier recommendations.
        safe_tier_annual_savings: Raw annual savings from 'safe' recommendations.
        executive_summary: Human-readable summary for business cases.
    """

    algorithm_id: str = Field(default="7.4", description="Algorithm identifier")
    total_recommendations: int = Field(
        default=0, description="Number of recommendations analyzed"
    )

    # Raw savings
    total_monthly_savings: float = Field(
        default=0.0, description="Raw total monthly savings (USD)"
    )
    total_annual_savings: float = Field(
        default=0.0, description="Raw total annual savings (USD)"
    )
    confidence_adjusted_annual_savings: float = Field(
        default=0.0, description="Confidence-weighted annual savings (USD)"
    )

    # Implementation cost
    total_implementation_cost: float = Field(
        default=0.0, description="Total one-time implementation cost (USD)"
    )

    # ROI metrics
    roi_percentage: float = Field(default=0.0, description="ROI percentage")
    payback_period_months: float = Field(
        default=0.0, description="Months to recoup implementation cost"
    )
    npv: float = Field(default=0.0, description="Net Present Value (USD)")

    # Multi-year projections (confidence-adjusted, net of implementation cost)
    year_1_savings: float = Field(
        default=0.0, description="Year 1 net savings (USD)"
    )
    year_3_savings: float = Field(
        default=0.0, description="Cumulative 3-year net savings (USD)"
    )
    year_5_savings: float = Field(
        default=0.0, description="Cumulative 5-year net savings (USD)"
    )

    # Risk tier breakdown
    safe_recommendations_count: int = Field(
        default=0, description="Count of 'safe' recommendations"
    )
    moderate_recommendations_count: int = Field(
        default=0, description="Count of 'moderate' recommendations"
    )
    high_risk_recommendations_count: int = Field(
        default=0, description="Count of 'high-risk' recommendations"
    )
    safe_tier_annual_savings: float = Field(
        default=0.0, description="Annual savings from 'safe' recommendations (USD)"
    )

    # Executive summary
    executive_summary: str = Field(
        default="", description="Human-readable summary for business cases"
    )


# ---------------------------------------------------------------------------
# Main Algorithm
# ---------------------------------------------------------------------------


def calculate_roi(
    recommendations: list[OptimizationRecommendationInput],
    hourly_implementation_cost: float = 100.0,
    discount_rate: float = 0.10,
    projection_years: int = 5,
) -> ROIAnalysis:
    """Algorithm 7.4: Calculate ROI for a set of optimization recommendations.

    Computes financial justification metrics for implementing a batch of
    license optimization recommendations. All savings figures are aggregated
    across the full set of recommendations.

    Args:
        recommendations: List of optimization recommendations to evaluate.
        hourly_implementation_cost: Cost per labor hour for implementation (USD).
            Default: $100/hour.
        discount_rate: Annual discount rate for NPV calculation (0.0-1.0).
            Default: 0.10 (10%).
        projection_years: Number of years for multi-year projection.
            Default: 5.

    Returns:
        ROIAnalysis with comprehensive ROI metrics, risk breakdown,
        multi-year projections, and executive summary.

    Example:
        >>> from src.algorithms.algorithm_7_4_roi_calculator import (
        ...     OptimizationRecommendationInput, calculate_roi,
        ... )
        >>> recs = [
        ...     OptimizationRecommendationInput(
        ...         recommendation_id="REC-001",
        ...         algorithm_id="2.2",
        ...         user_id="USR-001",
        ...         monthly_savings=120.0,
        ...         confidence_score=0.95,
        ...         implementation_hours=0.5,
        ...         risk_tier="safe",
        ...     )
        ... ]
        >>> result = calculate_roi(recs, hourly_implementation_cost=100.0)
        >>> result.roi_percentage > 0
        True
    """
    # Handle zero recommendations -- return zeroed-out analysis
    if not recommendations:
        return ROIAnalysis(
            algorithm_id="7.4",
            total_recommendations=0,
            executive_summary="No optimization recommendations provided.",
        )

    # ------------------------------------------------------------------
    # 1. Aggregate raw savings and implementation cost
    # ------------------------------------------------------------------
    total_monthly_savings = sum(r.monthly_savings for r in recommendations)
    total_annual_savings = total_monthly_savings * 12
    total_implementation_cost = sum(
        r.implementation_hours * hourly_implementation_cost for r in recommendations
    )

    # ------------------------------------------------------------------
    # 2. Confidence-adjusted savings
    # ------------------------------------------------------------------
    confidence_adjusted_monthly = sum(
        r.monthly_savings * r.confidence_score for r in recommendations
    )
    confidence_adjusted_annual = confidence_adjusted_monthly * 12

    # ------------------------------------------------------------------
    # 3. ROI percentage: (annual_savings - cost) / cost * 100
    # ------------------------------------------------------------------
    if total_implementation_cost > 0:
        roi_percentage = (
            (confidence_adjusted_annual - total_implementation_cost)
            / total_implementation_cost
            * 100
        )
    else:
        # No cost -- infinite ROI conceptually, but report savings as percentage
        roi_percentage = confidence_adjusted_annual * 100 if confidence_adjusted_annual > 0 else 0.0

    # ------------------------------------------------------------------
    # 4. Payback period (months)
    # ------------------------------------------------------------------
    if confidence_adjusted_monthly > 0:
        payback_period_months = total_implementation_cost / confidence_adjusted_monthly
    else:
        payback_period_months = 0.0

    # ------------------------------------------------------------------
    # 5. NPV calculation over projection_years
    #    NPV = -implementation_cost + sum(annual_cf / (1 + r)^t for t in 1..N)
    # ------------------------------------------------------------------
    npv = -total_implementation_cost
    for year in range(1, projection_years + 1):
        npv += confidence_adjusted_annual / ((1 + discount_rate) ** year)

    # ------------------------------------------------------------------
    # 6. Multi-year projections (confidence-adjusted, net of impl cost)
    # ------------------------------------------------------------------
    year_1_savings = confidence_adjusted_annual - total_implementation_cost
    year_3_savings = confidence_adjusted_annual * 3 - total_implementation_cost
    year_5_savings = confidence_adjusted_annual * 5 - total_implementation_cost

    # ------------------------------------------------------------------
    # 7. Risk tier categorization
    # ------------------------------------------------------------------
    safe_count = 0
    moderate_count = 0
    high_risk_count = 0
    safe_annual_savings = 0.0

    for rec in recommendations:
        tier = rec.risk_tier.lower()
        if tier == "safe":
            safe_count += 1
            safe_annual_savings += rec.monthly_savings * 12
        elif tier == "moderate":
            moderate_count += 1
        elif tier in ("high-risk", "high_risk", "highrisk"):
            high_risk_count += 1

    # ------------------------------------------------------------------
    # 8. Executive summary
    # ------------------------------------------------------------------
    executive_summary = _build_executive_summary(
        total_recommendations=len(recommendations),
        total_annual_savings=total_annual_savings,
        confidence_adjusted_annual=confidence_adjusted_annual,
        total_implementation_cost=total_implementation_cost,
        roi_percentage=roi_percentage,
        payback_period_months=payback_period_months,
        year_5_savings=year_5_savings,
        safe_count=safe_count,
    )

    # ------------------------------------------------------------------
    # 9. Assemble output
    # ------------------------------------------------------------------
    return ROIAnalysis(
        algorithm_id="7.4",
        total_recommendations=len(recommendations),
        total_monthly_savings=total_monthly_savings,
        total_annual_savings=total_annual_savings,
        confidence_adjusted_annual_savings=confidence_adjusted_annual,
        total_implementation_cost=total_implementation_cost,
        roi_percentage=roi_percentage,
        payback_period_months=payback_period_months,
        npv=npv,
        year_1_savings=year_1_savings,
        year_3_savings=year_3_savings,
        year_5_savings=year_5_savings,
        safe_recommendations_count=safe_count,
        moderate_recommendations_count=moderate_count,
        high_risk_recommendations_count=high_risk_count,
        safe_tier_annual_savings=safe_annual_savings,
        executive_summary=executive_summary,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_executive_summary(
    total_recommendations: int,
    total_annual_savings: float,
    confidence_adjusted_annual: float,
    total_implementation_cost: float,
    roi_percentage: float,
    payback_period_months: float,
    year_5_savings: float,
    safe_count: int,
) -> str:
    """Generate an executive summary paragraph for business cases.

    Args:
        total_recommendations: Number of recommendations analyzed.
        total_annual_savings: Raw annual savings (USD).
        confidence_adjusted_annual: Confidence-weighted annual savings (USD).
        total_implementation_cost: One-time implementation cost (USD).
        roi_percentage: ROI percentage.
        payback_period_months: Months to payback.
        year_5_savings: Cumulative 5-year net savings (USD).
        safe_count: Number of safe-tier recommendations.

    Returns:
        Human-readable executive summary string.
    """
    lines = [
        f"Analysis of {total_recommendations} optimization recommendation(s) "
        f"projects annual savings of ${total_annual_savings:,.0f} "
        f"(${confidence_adjusted_annual:,.0f} confidence-adjusted).",
        f"One-time implementation cost: ${total_implementation_cost:,.0f}.",
        f"ROI: {roi_percentage:,.0f}% with a payback period of "
        f"{payback_period_months:.1f} month(s).",
        f"Projected 5-year cumulative net savings: ${year_5_savings:,.0f}.",
    ]
    if safe_count > 0:
        lines.append(
            f"{safe_count} recommendation(s) are classified as safe "
            f"and suitable for immediate implementation."
        )
    return " ".join(lines)
