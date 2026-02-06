"""Tests for Algorithm 5.2: Security Risk Scoring (TDD).

Algorithm 5.2 aggregates security findings per user and calculates
a weighted risk score (0-100). Security findings include:
- SoD violations
- Privilege creep
- Anomalous account changes
- Orphaned account status

Risk severity weights:
- CRITICAL: 25 points
- HIGH: 10 points
- MEDIUM: 5 points
- LOW: 2 points

See Requirements/07-Advanced-Algorithms-Expansion.md for full specification.
"""

from src.algorithms.algorithm_5_2_security_risk_scorer import (
    calculate_user_security_risk,
    SecurityFinding,
)


class TestSecurityRiskScoringBasic:
    """Test basic risk scoring functionality."""

    def test_no_security_findings_zero_risk(self):
        """User with no security findings should score 0 (no risk)."""
        user_id = "user_001"
        findings: list[SecurityFinding] = []

        result = calculate_user_security_risk(user_id, findings)

        assert result.user_id == user_id
        assert result.risk_score == 0
        assert result.risk_category == "LOW_RISK"
        assert result.contributing_factors == []

    def test_single_critical_violation(self):
        """Single CRITICAL SoD violation scores 25 points (HIGH_RISK)."""
        user_id = "user_002"
        findings = [
            SecurityFinding(
                finding_type="SoD_VIOLATION",
                severity="CRITICAL",
                description="Conflicting roles: Accounts Payable Clerk + Accounts Payable Manager",
            )
        ]

        result = calculate_user_security_risk(user_id, findings)

        assert result.user_id == user_id
        assert result.risk_score == 25
        assert result.risk_category == "HIGH_RISK"
        assert len(result.contributing_factors) == 1

    def test_single_high_violation(self):
        """Single HIGH severity violation scores 10 points (MEDIUM_RISK)."""
        user_id = "user_003"
        findings = [
            SecurityFinding(
                finding_type="PRIVILEGE_CREEP",
                severity="HIGH",
                description="User assigned to 12 roles (75th percentile is 4 roles)",
            )
        ]

        result = calculate_user_security_risk(user_id, findings)

        assert result.user_id == user_id
        assert result.risk_score == 10
        assert result.risk_category == "MEDIUM_RISK"

    def test_single_medium_violation(self):
        """Single MEDIUM severity violation scores 5 points (LOW_RISK)."""
        user_id = "user_004"
        findings = [
            SecurityFinding(
                finding_type="ANOMALOUS_CHANGE",
                severity="MEDIUM",
                description="Role changed 3 times in 1 week (unusual pattern)",
            )
        ]

        result = calculate_user_security_risk(user_id, findings)

        assert result.user_id == user_id
        assert result.risk_score == 5
        assert result.risk_category == "LOW_RISK"

    def test_single_low_violation(self):
        """Single LOW severity violation scores 2 points."""
        user_id = "user_005"
        findings = [
            SecurityFinding(
                finding_type="ORPHANED_ACCOUNT",
                severity="LOW",
                description="Account last active 90 days ago",
            )
        ]

        result = calculate_user_security_risk(user_id, findings)

        assert result.user_id == user_id
        assert result.risk_score == 2
        assert result.risk_category == "LOW_RISK"


class TestSecurityRiskScoringAggregation:
    """Test aggregation of multiple findings."""

    def test_mixed_severity_violations(self):
        """Multiple violations aggregate correctly."""
        user_id = "user_006"
        findings = [
            SecurityFinding(
                finding_type="SoD_VIOLATION",
                severity="CRITICAL",
                description="Conflicting roles: Approve + Create",
            ),
            SecurityFinding(
                finding_type="PRIVILEGE_CREEP",
                severity="HIGH",
                description="12 roles assigned (unusual)",
            ),
            SecurityFinding(
                finding_type="ORPHANED_ACCOUNT",
                severity="MEDIUM",
                description="Status: Inactive in AD, still has roles in D365",
            ),
        ]

        result = calculate_user_security_risk(user_id, findings)

        # Expected: 25 + 10 + 5 = 40
        assert result.user_id == user_id
        assert result.risk_score == 40
        assert result.risk_category == "HIGH_RISK"
        assert len(result.contributing_factors) == 3

    def test_example_from_specification(self):
        """Test example from task specification.

        1 CRITICAL SoD + 2 HIGH privilege creep + 1 MEDIUM orphaned = 50 points
        """
        user_id = "user_007"
        findings = [
            SecurityFinding(
                finding_type="SoD_VIOLATION",
                severity="CRITICAL",
                description="Conflict 1: Roles A + B",
            ),
            SecurityFinding(
                finding_type="PRIVILEGE_CREEP",
                severity="HIGH",
                description="Finding 1: Excessive roles",
            ),
            SecurityFinding(
                finding_type="PRIVILEGE_CREEP",
                severity="HIGH",
                description="Finding 2: Cross-module access",
            ),
            SecurityFinding(
                finding_type="ORPHANED_ACCOUNT",
                severity="MEDIUM",
                description="Account status inconsistency",
            ),
        ]

        result = calculate_user_security_risk(user_id, findings)

        # (1×25) + (2×10) + (1×5) = 50
        assert result.risk_score == 50
        assert result.risk_category == "HIGH_RISK"
        assert len(result.contributing_factors) == 4


class TestSecurityRiskCategoryBoundaries:
    """Test risk category thresholds."""

    def test_low_risk_boundary_zero(self):
        """Risk score 0-14 is LOW_RISK."""
        user_id = "user_008"

        # Score 0
        result = calculate_user_security_risk(user_id, [])
        assert result.risk_category == "LOW_RISK"

        # Score 2 (single LOW)
        findings = [SecurityFinding(finding_type="TEST", severity="LOW", description="test")]
        result = calculate_user_security_risk(user_id, findings)
        assert result.risk_category == "LOW_RISK"

    def test_medium_risk_boundary(self):
        """Risk score 10-24 is MEDIUM_RISK."""
        user_id = "user_009"

        # Score 15 (3×5)
        findings = [
            SecurityFinding(finding_type="A", severity="MEDIUM", description="1"),
            SecurityFinding(finding_type="B", severity="MEDIUM", description="2"),
            SecurityFinding(finding_type="C", severity="MEDIUM", description="3"),
        ]
        result = calculate_user_security_risk(user_id, findings)
        assert result.risk_category == "MEDIUM_RISK"

        # Score 24 (2×10 + 2×2)
        findings = [
            SecurityFinding(finding_type="A", severity="HIGH", description="1"),
            SecurityFinding(finding_type="B", severity="HIGH", description="2"),
            SecurityFinding(finding_type="C", severity="LOW", description="3"),
            SecurityFinding(finding_type="D", severity="LOW", description="4"),
        ]
        result = calculate_user_security_risk(user_id, findings)
        assert result.risk_score == 24
        assert result.risk_category == "MEDIUM_RISK"

    def test_high_risk_boundary(self):
        """Risk score 35-74 is HIGH_RISK."""
        user_id = "user_010"

        # Score 35 (1×25 + 1×10)
        findings = [
            SecurityFinding(finding_type="A", severity="CRITICAL", description="1"),
            SecurityFinding(finding_type="B", severity="HIGH", description="2"),
        ]
        result = calculate_user_security_risk(user_id, findings)
        assert result.risk_category == "HIGH_RISK"

    def test_critical_risk_boundary(self):
        """Risk score 75+ is CRITICAL_RISK."""
        user_id = "user_011"

        # Score 75 (3×25)
        findings = [
            SecurityFinding(finding_type="A", severity="CRITICAL", description="1"),
            SecurityFinding(finding_type="B", severity="CRITICAL", description="2"),
            SecurityFinding(finding_type="C", severity="CRITICAL", description="3"),
        ]
        result = calculate_user_security_risk(user_id, findings)
        assert result.risk_category == "CRITICAL_RISK"


class TestSecurityRiskEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_maximum_possible_score(self):
        """Very high number of critical violations."""
        user_id = "user_012"
        findings = [
            SecurityFinding(
                finding_type=f"FINDING_{i}",
                severity="CRITICAL",
                description=f"Violation {i}",
            )
            for i in range(10)
        ]

        result = calculate_user_security_risk(user_id, findings)

        # 10 × 25 = 250
        assert result.risk_score == 250
        # Score capped at 100 for risk_category calculation
        assert result.risk_category == "CRITICAL_RISK"

    def test_contributing_factors_listed(self):
        """Each finding contributes to the factors list."""
        user_id = "user_013"
        findings = [
            SecurityFinding(
                finding_type="SoD_VIOLATION",
                severity="CRITICAL",
                description="Desc 1",
            ),
            SecurityFinding(
                finding_type="PRIVILEGE_CREEP",
                severity="HIGH",
                description="Desc 2",
            ),
        ]

        result = calculate_user_security_risk(user_id, findings)

        # Each finding is a contributing factor
        assert len(result.contributing_factors) == 2
        assert "SoD_VIOLATION" in str(result.contributing_factors)
        assert "PRIVILEGE_CREEP" in str(result.contributing_factors)

    def test_risk_score_never_negative(self):
        """Risk score is always >= 0."""
        user_id = "user_014"
        findings = []

        result = calculate_user_security_risk(user_id, findings)

        assert result.risk_score >= 0

    def test_severity_case_insensitive(self):
        """Severity levels are case-insensitive."""
        user_id = "user_015"
        findings = [
            SecurityFinding(finding_type="TEST1", severity="critical", description="lowercase"),
            SecurityFinding(finding_type="TEST2", severity="CRITICAL", description="uppercase"),
            SecurityFinding(finding_type="TEST3", severity="Critical", description="mixed case"),
        ]

        result = calculate_user_security_risk(user_id, findings)

        # All should score 25 each = 75
        assert result.risk_score == 75


class TestSecurityRiskRecommendations:
    """Test that risk results include actionable recommendations."""

    def test_critical_risk_recommendation(self):
        """CRITICAL_RISK results include immediate action recommendation."""
        user_id = "user_016"
        findings = [
            SecurityFinding(
                finding_type="SoD_VIOLATION",
                severity="CRITICAL",
                description="Conflict 1",
            ),
            SecurityFinding(
                finding_type="SoD_VIOLATION",
                severity="CRITICAL",
                description="Conflict 2",
            ),
            SecurityFinding(
                finding_type="SoD_VIOLATION",
                severity="CRITICAL",
                description="Conflict 3",
            ),
        ]

        result = calculate_user_security_risk(user_id, findings)

        # Score should be 75 (3×25) = CRITICAL_RISK
        assert result.risk_score == 75
        assert result.risk_category == "CRITICAL_RISK"
        assert result.recommendation is not None
        assert (
            "immediate" in result.recommendation.lower()
            or "urgent" in result.recommendation.lower()
        )

    def test_high_risk_recommendation(self):
        """HIGH_RISK results include prompt action recommendation."""
        user_id = "user_017"
        findings = [
            SecurityFinding(
                finding_type="PRIVILEGE_CREEP",
                severity="HIGH",
                description="Too many roles",
            ),
            SecurityFinding(
                finding_type="PRIVILEGE_CREEP",
                severity="HIGH",
                description="Cross-module",
            ),
        ]

        result = calculate_user_security_risk(user_id, findings)

        assert result.recommendation is not None

    def test_low_risk_no_urgent_recommendation(self):
        """LOW_RISK may have monitoring recommendation but not urgent."""
        user_id = "user_018"
        findings = [
            SecurityFinding(
                finding_type="ORPHANED_ACCOUNT",
                severity="LOW",
                description="Old account",
            )
        ]

        result = calculate_user_security_risk(user_id, findings)

        # May have recommendation, but should not be "immediate" or "urgent"
        if result.recommendation:
            assert "immediate" not in result.recommendation.lower()
            assert "urgent" not in result.recommendation.lower()
