"""Output schemas for D365 FO License Agent algorithm recommendations.

These Pydantic models define the structure of algorithm outputs:
- License change recommendations
- Confidence scores
- Estimated savings
- Rationale explanations

Consumed by: TypeScript API layer, Web UI, reporting.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class RecommendationAction(str, Enum):
    """Types of license recommendation actions."""

    DOWNGRADE = "downgrade"  # Reduce license tier
    UPGRADE = "upgrade"  # Increase license tier (rare, but possible for compliance)
    NO_CHANGE = "no_change"  # Current license is optimal
    ADD_LICENSE = "add_license"  # Multi-license stacking scenario
    REMOVE_LICENSE = "remove_license"  # Remove redundant license
    REVIEW_REQUIRED = "review_required"  # Edge case requiring human judgment


class ConfidenceLevel(str, Enum):
    """Confidence level categories for recommendations."""

    HIGH = "high"  # ≥ 0.90 confidence
    MEDIUM = "medium"  # 0.70-0.89 confidence
    LOW = "low"  # 0.50-0.69 confidence
    INSUFFICIENT_DATA = "insufficient_data"  # < 0.50 or not enough data


class RecommendationReason(BaseModel):
    """Structured explanation for a recommendation.

    Provides human-readable and machine-parseable rationale.
    """

    primary_factor: str = Field(
        description="Main reason for recommendation (e.g., '99.76% read-only operations')"
    )
    supporting_factors: list[str] = Field(
        description="Additional supporting evidence",
        default_factory=list,
    )
    risk_factors: list[str] = Field(
        description="Potential risks or edge cases to consider",
        default_factory=list,
    )
    data_quality_notes: list[str] = Field(
        description="Data completeness or quality concerns",
        default_factory=list,
    )


class SavingsEstimate(BaseModel):
    """Financial savings calculation for a recommendation."""

    monthly_current_cost: float = Field(description="Current license cost per month (USD)", ge=0)
    monthly_recommended_cost: float = Field(
        description="Recommended license cost per month (USD)", ge=0
    )
    monthly_savings: float = Field(description="Monthly savings (USD)", ge=0)
    annual_savings: float = Field(description="Annual savings (USD)", ge=0)
    confidence_adjusted_savings: float = Field(
        description="Annual savings adjusted by confidence score", ge=0
    )

    @field_validator("annual_savings")
    @classmethod
    def validate_annual_savings(cls, v: float, info: ValidationInfo) -> float:
        """Ensure annual savings = monthly savings * 12."""
        if "monthly_savings" in info.data:
            expected = info.data["monthly_savings"] * 12
            if abs(v - expected) > 0.01:  # Allow for floating point precision
                raise ValueError(f"Annual savings {v} doesn't match monthly * 12 ({expected:.2f})")
        return v


class LicenseRecommendation(BaseModel):
    """Complete license recommendation output from an algorithm.

    This is the primary output contract for all license optimization algorithms.
    """

    # Identification
    algorithm_id: str = Field(
        description="Algorithm that generated this recommendation (e.g., '2.2', '2.5')"
    )
    recommendation_id: str = Field(
        description="Unique recommendation identifier (UUID)", pattern=r"^[a-f0-9\-]{36}$"
    )
    generated_at: datetime = Field(
        description="When recommendation was generated (UTC)", default_factory=datetime.utcnow
    )

    # User context
    user_id: str = Field(description="Target user identifier")
    user_name: str | None = Field(default=None, description="User display name")
    user_email: str | None = Field(default=None, description="User email")

    # Current state
    current_license: str = Field(description="Current license type")
    current_license_cost_monthly: float = Field(description="Current monthly cost (USD)", ge=0)

    # Recommendation
    action: RecommendationAction = Field(description="Recommended action")
    recommended_license: str | None = Field(
        default=None, description="Recommended license type (if action != no_change)"
    )
    recommended_license_cost_monthly: float | None = Field(
        default=None, description="Recommended monthly cost (USD)"
    )

    # Confidence and rationale
    confidence_score: float = Field(
        description="Confidence in recommendation (0.0-1.0)", ge=0.0, le=1.0
    )
    confidence_level: ConfidenceLevel = Field(description="Confidence category")
    reason: RecommendationReason = Field(description="Structured explanation")

    # Savings
    savings: SavingsEstimate | None = Field(
        default=None, description="Financial impact (null if action=no_change)"
    )

    # Analysis metadata
    analysis_period_days: int = Field(description="Number of days of data analyzed", ge=1, le=3650)
    sample_size: int = Field(description="Number of operations analyzed", ge=0)
    data_completeness: float = Field(
        description="Data completeness score (0.0-1.0)", ge=0.0, le=1.0
    )

    # Implementation guidance
    safe_to_automate: bool = Field(description="Whether this recommendation can be auto-approved")
    requires_approval: bool = Field(description="Whether this requires manager/admin approval")
    implementation_notes: list[str] = Field(
        description="Implementation guidance and caveats",
        default_factory=list,
    )

    # Tags for filtering/categorization
    tags: list[str] = Field(
        description="Tags for filtering (e.g., ['high_savings', 'seasonal', 'edge_case'])",
        default_factory=list,
    )

    @property
    def already_optimized(self) -> bool:
        """Whether the current license state is already optimal.

        Derived from action: NO_CHANGE means already optimized.
        Used by Algorithm 4.3 (cross-application analysis) and others.
        """
        return self.action == RecommendationAction.NO_CHANGE

    @property
    def confidence(self) -> ConfidenceLevel:
        """Alias for confidence_level for backward-compatible test access."""
        return self.confidence_level

    @property
    def timestamp(self) -> datetime:
        """Alias for generated_at for backward-compatible test access."""
        return self.generated_at

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: ConfidenceLevel, info: ValidationInfo) -> ConfidenceLevel:
        """Ensure confidence_level matches confidence_score."""
        if "confidence_score" not in info.data:
            return v

        score = info.data["confidence_score"]
        expected = (
            ConfidenceLevel.HIGH
            if score >= 0.90
            else (
                ConfidenceLevel.MEDIUM
                if score >= 0.70
                else ConfidenceLevel.LOW if score >= 0.50 else ConfidenceLevel.INSUFFICIENT_DATA
            )
        )

        if v != expected:
            raise ValueError(
                f"Confidence level {v} doesn't match score {score:.2f} (expected {expected})"
            )
        return v


class AlgorithmMetrics(BaseModel):
    """Performance and accuracy metrics for an algorithm run.

    Used for monitoring, debugging, and algorithm improvement.
    """

    algorithm_id: str
    execution_time_ms: float = Field(description="Algorithm execution time (milliseconds)", ge=0)
    records_processed: int = Field(description="Number of records processed", ge=0)
    memory_usage_mb: float | None = Field(default=None, description="Peak memory usage (MB)")
    cache_hit_rate: float | None = Field(
        default=None, description="Cache hit rate (0.0-1.0)", ge=0.0, le=1.0
    )
    errors_encountered: list[str] = Field(
        description="Non-fatal errors during execution",
        default_factory=list,
    )
    warnings: list[str] = Field(
        description="Warnings about data quality or edge cases",
        default_factory=list,
    )


class BatchRecommendationResult(BaseModel):
    """Output for batch processing of multiple users.

    Used when running algorithms across entire user population.
    """

    batch_id: str = Field(description="Batch identifier (UUID)")
    algorithm_id: str = Field(description="Algorithm used")
    started_at: datetime = Field(description="Batch start time (UTC)")
    completed_at: datetime = Field(description="Batch completion time (UTC)")

    total_users_analyzed: int = Field(description="Total users in batch", ge=0)
    recommendations_generated: int = Field(description="Number of actionable recommendations", ge=0)

    recommendations: list[LicenseRecommendation] = Field(
        description="All recommendations from batch"
    )

    # Aggregate statistics
    total_potential_savings_annual: float = Field(
        description="Sum of all savings estimates (USD)", ge=0
    )
    high_confidence_count: int = Field(
        description="Number of high-confidence recommendations", ge=0
    )
    medium_confidence_count: int = Field(
        description="Number of medium-confidence recommendations", ge=0
    )
    low_confidence_count: int = Field(description="Number of low-confidence recommendations", ge=0)

    metrics: AlgorithmMetrics = Field(description="Batch execution metrics")


class ValidationResult(BaseModel):
    """Result of validating a recommendation against business rules.

    Used for pre-deployment validation and safety checks.
    """

    recommendation_id: str = Field(description="Recommendation being validated")
    is_valid: bool = Field(description="Whether recommendation passes validation")
    validation_errors: list[str] = Field(
        description="Validation errors (empty if valid)",
        default_factory=list,
    )
    validation_warnings: list[str] = Field(
        description="Non-blocking warnings",
        default_factory=list,
    )
    validated_at: datetime = Field(
        description="When validation was performed (UTC)", default_factory=datetime.utcnow
    )
    validated_by: str = Field(description="Validation rule set version")


class SeverityLevel(str, Enum):
    """SoD violation severity levels per Requirements/15."""

    CRITICAL = "CRITICAL"  # Direct fraud risk or SOX material weakness
    HIGH = "HIGH"  # Significant control weakness, audit finding
    MEDIUM = "MEDIUM"  # Control improvement opportunity
    LOW = "LOW"  # Minor control gap


class SODViolation(BaseModel):
    """Segregation of Duties violation detected by Algorithm 3.1.

    Represents a detected SoD conflict where a user has been assigned
    two roles that conflict according to the SoD conflict matrix.

    See Requirements/15-Default-SoD-Conflict-Matrix.md and
    Requirements/07-Advanced-Algorithms-Expansion.md (Algorithm 3.1).
    """

    # Identification
    violation_id: str = Field(
        description="Unique violation identifier (UUID)",
        default_factory=lambda: str(uuid4()),
    )
    rule_id: str = Field(
        description=("SoD conflict rule ID " "(e.g., 'AP-001', 'GL-001', 'CUSTOM-001')")
    )
    detected_at: datetime = Field(
        description="When violation was detected (UTC)",
        default_factory=datetime.utcnow,
    )

    # User and roles
    user_id: str = Field(description="User identifier with conflicting roles")
    user_name: str | None = Field(default=None, description="User display name")
    user_email: str | None = Field(default=None, description="User email")

    # Conflicting roles
    role_a: str = Field(description="First conflicting role name")
    role_b: str = Field(description="Second conflicting role name")
    conflict_type: str = Field(
        description=("Type of conflict " "(e.g., 'Process vs. Create', 'Pay vs. Reconcile')")
    )

    # Severity and risk
    severity: SeverityLevel = Field(description="Severity level (CRITICAL/HIGH/MEDIUM/LOW)")
    risk_description: str = Field(description="Detailed explanation of fraud/compliance risk")
    regulatory_reference: str = Field(
        description=("Applicable regulatory " "standard(s) " "(e.g., 'SOX 404, COSO Principle 10')")
    )

    # Remediation guidance
    recommendation: str | None = Field(
        default=None,
        description=(
            "Recommended remediation action "
            "(e.g., 'Remove one role' or 'Add compensating control')"
        ),
    )
    sla_hours: int | None = Field(
        default=None,
        description=(
            "SLA for remediation in hours " "(24 for CRITICAL, 168 for HIGH, 720 for MEDIUM)"
        ),
    )


# ============================================================================
# Algorithm 5.1: License Cost Trend Analysis Schemas
# ============================================================================


class GrowthRate(BaseModel):
    """Growth rate statistics for license trends.

    Contains overall growth, MoM/QoQ/YoY averages, and trend classification.
    See Algorithm 5.1 calculate_growth_rates() for computation details.
    """

    overall_percent: float = Field(description="Overall growth rate for the period (%)")
    period_months: int = Field(description="Number of months in the analysis period", ge=1)
    mom_average: float = Field(description="Average month-over-month growth rate (%)")
    mom_min: float = Field(description="Minimum month-over-month growth rate (%)")
    mom_max: float = Field(description="Maximum month-over-month growth rate (%)")
    qoq_average: float = Field(description="Average quarter-over-quarter growth rate (%)")
    yoy_average: float = Field(description="Average year-over-year growth rate (%)")
    trend: str = Field(description="Trend classification: GROWING, STABLE, or DECLINING")


class SeasonalPattern(BaseModel):
    """Detected seasonal pattern in license usage.

    Represents a month that consistently deviates from the baseline average
    across multiple years of data.
    """

    month: int = Field(description="Month number (1-12)", ge=1, le=12)
    month_name: str = Field(description="Month name (e.g., 'January')")
    pattern_type: str = Field(description="Pattern type: HIGH or LOW")
    deviation_percent: float = Field(description="Deviation from baseline (%)")
    avg_user_count: float = Field(description="Average user count for this month", ge=0)
    occurrences: int = Field(description="Number of times this pattern was observed", ge=1)
    years: list[int] = Field(description="Years in which the pattern was observed")


class LicenseAnomalyRecord(BaseModel):
    """Detected anomaly in license usage.

    Represents a statistically significant deviation in user count or cost,
    detected via z-score analysis or sudden month-over-month change.
    """

    anomaly_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique anomaly ID")
    anomaly_type: str = Field(
        description=(
            "Type of anomaly: USER_COUNT_ANOMALY, COST_ANOMALY, "
            "SUDDEN_USER_CHANGE, SUDDEN_COST_CHANGE"
        )
    )
    date: datetime = Field(description="Date of anomaly")
    value: float = Field(description="Actual observed value", ge=0)
    expected: float = Field(description="Expected value based on trend/average", ge=0)
    z_score: float = Field(description="Z-score or approximate z-score of the deviation")
    severity: str = Field(description="Anomaly severity: MEDIUM or HIGH")
    description: str = Field(description="Human-readable anomaly description")


class ForecastMonth(BaseModel):
    """Forecasted license demand for a specific month.

    Generated by the forecast sub-algorithm with growth rate projection
    and optional seasonal adjustment.
    """

    month_number: int = Field(description="Forecast month ordinal (1-N)", ge=1)
    date: datetime = Field(description="Forecast date")
    month_name: str = Field(description="Month name (e.g., 'January')")
    forecast_users: int = Field(description="Forecasted user count", ge=0)
    forecast_cost: float = Field(description="Forecasted monthly cost (USD)", ge=0)
    growth_from_base_percent: float = Field(description="Growth percentage from base month")
    confidence: int = Field(description="Confidence score (0-100)", ge=0, le=100)
    seasonal_adjustment_percent: float = Field(
        default=0.0, description="Seasonal adjustment applied (%)"
    )
    notes: list[str] = Field(default_factory=list, description="Notes about this forecast month")


class TrendAnalysisRecommendation(BaseModel):
    """Actionable recommendation from trend analysis.

    Generated by the recommendations sub-algorithm based on growth trends,
    seasonal patterns, and forecast data.
    """

    recommendation_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique recommendation ID"
    )
    recommendation_type: str = Field(
        description=(
            "Type of recommendation: PROCUREMENT_NEEDED, SEASONAL_DEMAND, "
            "DECLINING_TREND, BUDGET_FORECAST"
        )
    )
    description: str = Field(description="Recommendation text")
    priority: str = Field(description="Priority level: LOW, MEDIUM, HIGH, CRITICAL")
    timeline: str | None = Field(default=None, description="Recommended timeline for action")
    estimated_impact: float | None = Field(
        default=None, description="Estimated financial impact (USD)"
    )
    action_items: list[str] = Field(
        default_factory=list, description="Specific action items to implement recommendation"
    )


class LicenseTrendAnalysis(BaseModel):
    """Complete output from Algorithm 5.1: License Cost Trend Analysis.

    Aggregates growth analysis, seasonal patterns, anomaly detection,
    forecasting, and actionable recommendations into a single report.
    """

    # Algorithm identification
    algorithm_id: str = Field(default="5.1", description="Algorithm identifier")

    # Analysis metadata
    analysis_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique analysis ID")
    analysis_date: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis execution timestamp"
    )
    analysis_period_months: int = Field(description="Number of months analyzed", ge=1)
    period_start: datetime = Field(description="Start of the analysis period")
    period_end: datetime = Field(description="End of the analysis period")

    # Current state
    current_users: int = Field(description="Current total user count", ge=0)
    current_monthly_cost: float = Field(description="Current monthly license cost (USD)", ge=0)

    # Growth analysis
    growth_rates: GrowthRate | None = Field(default=None, description="Growth rate statistics")

    # Seasonal patterns
    seasonal_patterns: list[SeasonalPattern] = Field(
        default_factory=list, description="Detected seasonal patterns"
    )

    # Anomalies
    anomalies: list[LicenseAnomalyRecord] = Field(
        default_factory=list, description="Detected anomalies"
    )

    # Forecast
    forecast_months: int = Field(default=12, description="Number of months forecasted")
    forecast: list[ForecastMonth] = Field(default_factory=list, description="Forecast data")

    # Recommendations
    recommendations: list[TrendAnalysisRecommendation] = Field(
        default_factory=list, description="Actionable recommendations"
    )

    # Confidence
    overall_confidence: ConfidenceLevel = Field(description="Overall analysis confidence")
    confidence_score: float = Field(
        description="Numeric confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
    confidence_factors: dict[str, Any] = Field(
        default_factory=dict, description="Factors affecting confidence with their impact"
    )
