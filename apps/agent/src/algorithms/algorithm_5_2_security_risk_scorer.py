"""Algorithm 5.2: Security Risk Scoring.

Aggregates security findings per user and calculates a weighted risk score
(0-100+). Security findings include SoD violations, privilege creep,
anomalous account changes, and orphaned account status.

Risk severity weights:
- CRITICAL: 25 points
- HIGH: 10 points
- MEDIUM: 5 points
- LOW: 2 points

The algorithm categorizes users into risk tiers:
- LOW_RISK: 0-14 points
- MEDIUM_RISK: 15-34 points
- HIGH_RISK: 35-74 points
- CRITICAL_RISK: 75+ points

See Requirements/07-Advanced-Algorithms-Expansion.md for full specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..models.input_schemas import SecurityFinding


class SecurityRiskResult(BaseModel):
    """Result of security risk scoring for a user."""

    user_id: str = Field(description="User identifier")
    risk_score: int = Field(
        description="Aggregated risk score (0+, no upper limit)",
        ge=0,
    )
    risk_category: str = Field(
        description="Risk category (LOW_RISK, MEDIUM_RISK, HIGH_RISK, CRITICAL_RISK)"
    )
    contributing_factors: list[str] = Field(
        description="List of security finding types contributing to score",
        default_factory=list,
    )
    recommendation: str | None = Field(
        default=None,
        description="Actionable recommendation based on risk level",
    )


def calculate_user_security_risk(
    user_id: str,
    findings: list[SecurityFinding],
) -> SecurityRiskResult:
    """Calculate aggregated security risk score for a user.

    Implements weighted risk aggregation where each security finding
    contributes points based on severity:
    - CRITICAL: 25 points
    - HIGH: 10 points
    - MEDIUM: 5 points
    - LOW: 2 points

    Args:
        user_id: Target user identifier
        findings: List of security findings for the user

    Returns:
        SecurityRiskResult with score, category, and recommendation
    """
    # Risk severity weights
    severity_weights: dict[str, int] = {
        "CRITICAL": 25,
        "HIGH": 10,
        "MEDIUM": 5,
        "LOW": 2,
    }

    # Calculate total risk score
    total_score: int = 0
    contributing_factors: list[str] = []

    for finding in findings:
        # Normalize severity to uppercase for lookup
        severity = finding.severity.upper()

        # Get weight, default to 0 if unknown severity
        weight = severity_weights.get(severity, 0)

        total_score += weight
        contributing_factors.append(finding.finding_type)

    # Determine risk category based on score
    if total_score < 10:
        risk_category = "LOW_RISK"
    elif total_score < 25:
        risk_category = "MEDIUM_RISK"
    elif total_score < 75:
        risk_category = "HIGH_RISK"
    else:
        risk_category = "CRITICAL_RISK"

    # Generate recommendation based on risk level
    recommendation = _generate_recommendation(
        risk_category,
        total_score,
        contributing_factors,
    )

    return SecurityRiskResult(
        user_id=user_id,
        risk_score=total_score,
        risk_category=risk_category,
        contributing_factors=contributing_factors,
        recommendation=recommendation,
    )


def _generate_recommendation(
    risk_category: str,
    risk_score: int,
    contributing_factors: list[str],
) -> str:
    """Generate actionable recommendation based on risk assessment.

    Args:
        risk_category: The determined risk category
        risk_score: The calculated risk score
        contributing_factors: List of finding types

    Returns:
        Recommendation string
    """
    if risk_category == "CRITICAL_RISK":
        return (
            f"IMMEDIATE ACTION REQUIRED: User presents critical security risk "
            f"(score: {risk_score}). Primary issues: {', '.join(contributing_factors[:2])}. "
            f"Review and remediate immediately."
        )
    elif risk_category == "HIGH_RISK":
        return (
            f"Prompt remediation needed: User presents high security risk "
            f"(score: {risk_score}). Issues: {', '.join(contributing_factors[:2])}. "
            f"Schedule remediation within 1 week."
        )
    elif risk_category == "MEDIUM_RISK":
        return (
            f"Review and monitor: User presents medium security risk "
            f"(score: {risk_score}). Consider review of: "
            f"{', '.join(contributing_factors[:2])}."
        )
    else:  # LOW_RISK
        return f"Low security risk (score: {risk_score}). Continue routine monitoring."
