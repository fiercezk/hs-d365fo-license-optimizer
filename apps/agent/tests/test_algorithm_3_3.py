"""Tests for Algorithm 3.3: Privilege Creep Detector (TDD).

Algorithm 3.3 detects users who have gradually accumulated excessive roles/
privileges over time without removal, creating security risks and unnecessary
license costs.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 400-548

Test scenarios based on algo_3_3 fixtures:
1. Active user (no creep) - should return no_change
2. Completely inactive user (>180 days) - HIGH severity
3. Contractor between projects - MEDIUM with contractor warning
4. Leave of absence user - MEDIUM with LOA warning
5. Recently inactive (90-180 days) - MEDIUM severity
6. Seasonal worker - MEDIUM with seasonal warning
7. Inactive Team Members license - MEDIUM for low-cost
"""

import json
from pathlib import Path

import pytest

from src.algorithms.algorithm_3_3_privilege_creep_detector import (
    detect_privilege_creep,
)
from src.models.output_schemas import RecommendationAction, ConfidenceLevel


@pytest.fixture
def fixtures_dir() -> Path:
    """Get path to algo_3_3 test fixtures directory."""
    return Path(__file__).parent / "fixtures" / "algo_3_3"


@pytest.fixture
def active_user_scenario(fixtures_dir: Path) -> dict:
    """Load active user scenario fixture."""
    with open(fixtures_dir / "test_scenario_active_user.json") as f:
        return json.load(f)


@pytest.fixture
def completely_inactive_scenario(fixtures_dir: Path) -> dict:
    """Load completely inactive user scenario fixture."""
    with open(fixtures_dir / "test_scenario_completely_inactive.json") as f:
        return json.load(f)


@pytest.fixture
def contractor_between_projects_scenario(fixtures_dir: Path) -> dict:
    """Load contractor between projects scenario fixture."""
    with open(fixtures_dir / "test_scenario_contractor_between_projects.json") as f:
        return json.load(f)


@pytest.fixture
def loa_user_scenario(fixtures_dir: Path) -> dict:
    """Load leave of absence user scenario fixture."""
    with open(fixtures_dir / "test_scenario_loa_user.json") as f:
        return json.load(f)


@pytest.fixture
def recently_inactive_scenario(fixtures_dir: Path) -> dict:
    """Load recently inactive user scenario fixture."""
    with open(fixtures_dir / "test_scenario_recently_inactive.json") as f:
        return json.load(f)


@pytest.fixture
def seasonal_worker_scenario(fixtures_dir: Path) -> dict:
    """Load seasonal worker scenario fixture."""
    with open(fixtures_dir / "test_scenario_seasonal_worker.json") as f:
        return json.load(f)


@pytest.fixture
def team_members_inactive_scenario(fixtures_dir: Path) -> dict:
    """Load Team Members inactive scenario fixture."""
    with open(fixtures_dir / "test_scenario_team_members_inactive.json") as f:
        return json.load(f)


class TestActiveUserNoCreep:
    """Test case: Active user with regular usage - should NOT be flagged."""

    def test_active_user_returns_no_change(self, active_user_scenario: dict) -> None:
        """Active user with usage in last 90 days should return no_change."""
        scenario = active_user_scenario
        user = scenario["user"]
        activity_summary = scenario["activity_summary"]
        expected = scenario["expected_recommendation"]

        # Build minimal input data
        recommendation = detect_privilege_creep(
            user_id=user["user_id"],
            user_name=user["name"],
            user_email=user["email"],
            current_license=user["current_license"],
            current_license_cost_monthly=user["current_license_cost_monthly"],
            days_since_last_login=user["last_login_days_ago"],
            operation_count_90d=user["operation_count_90d"],
            is_contractor=user.get("is_contractor", False),
            leave_of_absence=user.get("leave_of_absence", False),
            seasonal_profile=user.get("seasonal_profile"),
            analysis_period_days=activity_summary["analysis_period_days"],
        )

        # Assertions
        assert recommendation is not None
        assert recommendation.action == RecommendationAction(expected["action"])
        assert recommendation.confidence_score == expected["confidence_score"]
        assert recommendation.current_license == expected["from_license"]
        assert recommendation.recommended_license is expected["to_license"]
        assert recommendation.savings is None  # no_change means no savings


class TestCompletelyInactiveUser:
    """Test case: User with zero activity for >180 days - HIGH severity."""

    def test_completely_inactive_high_severity(self, completely_inactive_scenario: dict) -> None:
        """User inactive >180 days should return remove_license with HIGH confidence."""
        scenario = completely_inactive_scenario
        user = scenario["user"]
        activity_summary = scenario["activity_summary"]
        expected = scenario["expected_recommendation"]

        recommendation = detect_privilege_creep(
            user_id=user["user_id"],
            user_name=user["name"],
            user_email=user["email"],
            current_license=user["current_license"],
            current_license_cost_monthly=user["current_license_cost_monthly"],
            days_since_last_login=user["last_login_days_ago"],
            operation_count_90d=user["operation_count_90d"],
            is_contractor=user.get("is_contractor", False),
            leave_of_absence=user.get("leave_of_absence", False),
            seasonal_profile=user.get("seasonal_profile"),
            analysis_period_days=activity_summary["analysis_period_days"],
        )

        # Assertions
        assert recommendation is not None
        assert recommendation.action == RecommendationAction(expected["action"])
        assert recommendation.confidence_level == ConfidenceLevel(expected["confidence_level"])
        assert recommendation.confidence_score == expected["confidence_score"]
        assert recommendation.current_license == expected["from_license"]
        assert recommendation.recommended_license is None

        # Check savings
        assert recommendation.savings is not None
        assert recommendation.savings.monthly_savings == expected["estimated_monthly_savings"]
        assert recommendation.savings.annual_savings == expected["estimated_annual_savings"]


class TestContractorBetweenProjects:
    """Test case: Contractor inactive but might be between assignments."""

    def test_contractor_between_projects_review_required(
        self, contractor_between_projects_scenario: dict
    ) -> None:
        """Contractor inactive should return review_required with MEDIUM confidence."""
        scenario = contractor_between_projects_scenario
        user = scenario["user"]
        activity_summary = scenario["activity_summary"]
        expected = scenario["expected_recommendation"]

        recommendation = detect_privilege_creep(
            user_id=user["user_id"],
            user_name=user["name"],
            user_email=user["email"],
            current_license=user["current_license"],
            current_license_cost_monthly=user["current_license_cost_monthly"],
            days_since_last_login=user["last_login_days_ago"],
            operation_count_90d=user["operation_count_90d"],
            is_contractor=user.get("is_contractor", False),
            leave_of_absence=user.get("leave_of_absence", False),
            seasonal_profile=user.get("seasonal_profile"),
            analysis_period_days=activity_summary["analysis_period_days"],
        )

        # Assertions
        assert recommendation is not None
        assert recommendation.action == RecommendationAction(expected["action"])
        assert recommendation.confidence_level == ConfidenceLevel(expected["confidence_level"])
        assert recommendation.confidence_score == expected["confidence_score"]

        # Should flag contractor status in tags or notes
        assert "contractor" in " ".join(recommendation.tags).lower()


class TestLeaveOfAbsenceUser:
    """Test case: User on LOA - flagged as inactive but expected to return."""

    def test_loa_user_review_required(self, loa_user_scenario: dict) -> None:
        """User on LOA should return review_required with LOW confidence."""
        scenario = loa_user_scenario
        user = scenario["user"]
        activity_summary = scenario["activity_summary"]
        expected = scenario["expected_recommendation"]

        recommendation = detect_privilege_creep(
            user_id=user["user_id"],
            user_name=user["name"],
            user_email=user["email"],
            current_license=user["current_license"],
            current_license_cost_monthly=user["current_license_cost_monthly"],
            days_since_last_login=user["last_login_days_ago"],
            operation_count_90d=user["operation_count_90d"],
            is_contractor=user.get("is_contractor", False),
            leave_of_absence=user.get("leave_of_absence", False),
            seasonal_profile=user.get("seasonal_profile"),
            analysis_period_days=activity_summary["analysis_period_days"],
        )

        # Assertions
        assert recommendation is not None
        assert recommendation.action == RecommendationAction(expected["action"])
        assert recommendation.confidence_level == ConfidenceLevel(expected["confidence_level"])
        assert recommendation.confidence_score == expected["confidence_score"]

        # Should flag LOA status in tags or notes
        assert "loa" in " ".join(recommendation.tags).lower()


class TestRecentlyInactiveUser:
    """Test case: User with 90-180 days inactivity - MEDIUM severity."""

    def test_recently_inactive_medium_confidence(self, recently_inactive_scenario: dict) -> None:
        """User inactive 90-180 days should return remove_license with MEDIUM confidence."""
        scenario = recently_inactive_scenario
        user = scenario["user"]
        activity_summary = scenario["activity_summary"]
        expected = scenario["expected_recommendation"]

        recommendation = detect_privilege_creep(
            user_id=user["user_id"],
            user_name=user["name"],
            user_email=user["email"],
            current_license=user["current_license"],
            current_license_cost_monthly=user["current_license_cost_monthly"],
            days_since_last_login=user["last_login_days_ago"],
            operation_count_90d=user["operation_count_90d"],
            is_contractor=user.get("is_contractor", False),
            leave_of_absence=user.get("leave_of_absence", False),
            seasonal_profile=user.get("seasonal_profile"),
            analysis_period_days=activity_summary["analysis_period_days"],
        )

        # Assertions
        assert recommendation is not None
        assert recommendation.action == RecommendationAction(expected["action"])
        assert recommendation.confidence_level == ConfidenceLevel(expected["confidence_level"])
        assert recommendation.confidence_score == expected["confidence_score"]


class TestSeasonalWorker:
    """Test case: Seasonal worker inactive but has known seasonal profile."""

    def test_seasonal_worker_review_required(self, seasonal_worker_scenario: dict) -> None:
        """Seasonal worker should return review_required with LOW confidence."""
        scenario = seasonal_worker_scenario
        user = scenario["user"]
        activity_summary = scenario["activity_summary"]
        expected = scenario["expected_recommendation"]

        recommendation = detect_privilege_creep(
            user_id=user["user_id"],
            user_name=user["name"],
            user_email=user["email"],
            current_license=user["current_license"],
            current_license_cost_monthly=user["current_license_cost_monthly"],
            days_since_last_login=user["last_login_days_ago"],
            operation_count_90d=user["operation_count_90d"],
            is_contractor=user.get("is_contractor", False),
            leave_of_absence=user.get("leave_of_absence", False),
            seasonal_profile=user.get("seasonal_profile"),
            analysis_period_days=activity_summary["analysis_period_days"],
        )

        # Assertions
        assert recommendation is not None
        assert recommendation.action == RecommendationAction(expected["action"])
        assert recommendation.confidence_level == ConfidenceLevel(expected["confidence_level"])
        assert recommendation.confidence_score == expected["confidence_score"]

        # Should flag seasonal status in tags or notes
        assert "seasonal" in " ".join(recommendation.tags).lower()


class TestTeamMembersInactive:
    """Test case: Inactive Team Members license (low cost but still unused)."""

    def test_team_members_inactive_flagged(self, team_members_inactive_scenario: dict) -> None:
        """Inactive Team Members license should still be flagged for removal."""
        scenario = team_members_inactive_scenario
        user = scenario["user"]
        activity_summary = scenario["activity_summary"]
        expected = scenario["expected_recommendation"]

        recommendation = detect_privilege_creep(
            user_id=user["user_id"],
            user_name=user["name"],
            user_email=user["email"],
            current_license=user["current_license"],
            current_license_cost_monthly=user["current_license_cost_monthly"],
            days_since_last_login=user["last_login_days_ago"],
            operation_count_90d=user["operation_count_90d"],
            is_contractor=user.get("is_contractor", False),
            leave_of_absence=user.get("leave_of_absence", False),
            seasonal_profile=user.get("seasonal_profile"),
            analysis_period_days=activity_summary["analysis_period_days"],
        )

        # Assertions
        assert recommendation is not None
        assert recommendation.action == RecommendationAction(expected["action"])
        assert recommendation.confidence_level == ConfidenceLevel(expected["confidence_level"])

        # Check savings (should be lower since Team Members is cheaper)
        assert recommendation.savings is not None
        assert recommendation.savings.monthly_savings == expected["estimated_monthly_savings"]
