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

from pydantic import BaseModel, Field, field_validator


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
    def validate_annual_savings(cls, v: float, info) -> float:
        """Ensure annual savings = monthly savings * 12."""
        if "monthly_savings" in info.data:
            expected = info.data["monthly_savings"] * 12
            if abs(v - expected) > 0.01:  # Allow for floating point precision
                raise ValueError(
                    f"Annual savings {v} doesn't match monthly * 12 ({expected:.2f})"
                )
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
    analysis_period_days: int = Field(
        description="Number of days of data analyzed", ge=1, le=3650
    )
    sample_size: int = Field(
        description="Number of operations analyzed", ge=0
    )
    data_completeness: float = Field(
        description="Data completeness score (0.0-1.0)", ge=0.0, le=1.0
    )

    # Implementation guidance
    safe_to_automate: bool = Field(
        description="Whether this recommendation can be auto-approved"
    )
    requires_approval: bool = Field(
        description="Whether this requires manager/admin approval"
    )
    implementation_notes: list[str] = Field(
        description="Implementation guidance and caveats",
        default_factory=list,
    )

    # Tags for filtering/categorization
    tags: list[str] = Field(
        description="Tags for filtering (e.g., ['high_savings', 'seasonal', 'edge_case'])",
        default_factory=list,
    )

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: ConfidenceLevel, info) -> ConfidenceLevel:
        """Ensure confidence_level matches confidence_score."""
        if "confidence_score" not in info.data:
            return v

        score = info.data["confidence_score"]
        expected = (
            ConfidenceLevel.HIGH
            if score >= 0.90
            else ConfidenceLevel.MEDIUM
            if score >= 0.70
            else ConfidenceLevel.LOW
            if score >= 0.50
            else ConfidenceLevel.INSUFFICIENT_DATA
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
    recommendations_generated: int = Field(
        description="Number of actionable recommendations", ge=0
    )

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
    low_confidence_count: int = Field(
        description="Number of low-confidence recommendations", ge=0
    )

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
