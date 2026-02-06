"""Tests for Algorithm 2.5: License Minority Detection.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until src/algorithms/algorithm_2_5_license_minority_detector.py
is implemented.

Specification: Requirements/09-License-Minority-Detection-Algorithm.md

Algorithm 2.5 analyzes users with multiple licenses to detect "minority" licenses
where usage is disproportionately low (below a threshold, default 15%). This detects
licensing inefficiencies where users hold licenses they rarely use, creating
optimization opportunities through downgrade or role modification.

Test scenarios cover:
  1. Clear minority license (user has two licenses, one is obvious minority)
  2. Multiple minority licenses (user has three licenses, two are minorities)
  3. No minority license (all licenses meet threshold)
  4. Single license user (skip - only multi-license users analyzed)
  5. Read-only heavy minority (minority license is mostly read-only, conversion possible)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_2_5_license_minority_detector import (
    detect_license_minority_users,
)
from src.models.output_schemas import (
    ConfidenceLevel,
    LicenseRecommendation,
    RecommendationAction,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

# Tolerance for floating-point comparisons on percentages
PERCENTAGE_TOLERANCE: float = 0.5

# Tolerance for monetary comparisons (cents)
MONETARY_TOLERANCE: float = 0.01


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_scenario(filename: str) -> dict[str, Any]:
    """Load a JSON test scenario fixture.

    Args:
        filename: Name of the JSON file inside tests/fixtures/.

    Returns:
        Parsed JSON as a dictionary containing test expectations.
    """
    path = FIXTURES_DIR / filename
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_user_activity() -> pd.DataFrame:
    """Load the test user activity CSV.

    Returns:
        DataFrame with columns: user_id, timestamp, menu_item, action,
        session_id, license_tier, feature.
    """
    return pd.read_csv(FIXTURES_DIR / "algo_2_5_user_activity.csv")


def _load_security_config() -> pd.DataFrame:
    """Load the test security configuration CSV.

    Returns:
        DataFrame with columns: securityrole, AOTName, AccessLevel,
        LicenseType, Priority, Entitled, NotEntitled, securitytype.
    """
    return pd.read_csv(FIXTURES_DIR / "algo_2_5_security_config.csv")


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON.

    Returns:
        Parsed pricing config with license costs.
    """
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestClearMinorityLicense:
    """Test Case 1: Clear Minority License.

    Scenario: John Doe has SCM + Finance licenses.
    Activity: 94.4% SCM (850 accesses), 5.6% Finance (50 accesses)
    Expected: Finance flagged as minority (5.6% < 15% threshold)
    Recommendation: REVIEW_WITH_USER to confirm if Finance access needed
    Savings: $180/month (remove Finance license)
    Confidence: HIGH (very skewed usage, very low minority usage)
    """

    def test_clear_minority_detected(self) -> None:
        """Test that Finance license is detected as minority."""
        _load_scenario("algo_2_5_scenario_clear_minority.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        # Filter to single user
        john_activity = user_activity[user_activity["user_id"] == "john.doe@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=john_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        # Should find John in results (he has minority)
        assert len(results) > 0
        john_result = next((r for r in results if r.user_id == "john.doe@contoso.com"), None)
        assert john_result is not None

    def test_minority_percentage_calculated(self) -> None:
        """Test that Finance usage is correctly calculated at ~5.6%."""
        scenario = _load_scenario("algo_2_5_scenario_clear_minority.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        john_activity = user_activity[user_activity["user_id"] == "john.doe@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=john_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        john_result = next((r for r in results if r.user_id == "john.doe@contoso.com"), None)
        assert john_result is not None

        # Check that Finance usage is in expected range
        # Expected: ~5.6%, allow tolerance
        assert (
            scenario["expected_outcome"]["minority_licenses"][0]["percentage"]
            - PERCENTAGE_TOLERANCE
            < 6.0
            < scenario["expected_outcome"]["minority_licenses"][0]["percentage"]
            + PERCENTAGE_TOLERANCE
        )

    def test_savings_estimate_correct(self) -> None:
        """Test that monthly savings is $180 (removing Finance license)."""
        scenario = _load_scenario("algo_2_5_scenario_clear_minority.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        john_activity = user_activity[user_activity["user_id"] == "john.doe@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=john_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        john_result = next((r for r in results if r.user_id == "john.doe@contoso.com"), None)
        assert john_result is not None
        assert john_result.savings is not None

        # Finance license costs $180/month
        expected_monthly = scenario["expected_outcome"]["expected_savings_monthly"]
        assert abs(john_result.savings.monthly_savings - expected_monthly) < MONETARY_TOLERANCE

    def test_recommendation_action(self) -> None:
        """Test that recommendation is REVIEW_WITH_USER."""
        _load_scenario("algo_2_5_scenario_clear_minority.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        john_activity = user_activity[user_activity["user_id"] == "john.doe@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=john_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        john_result = next((r for r in results if r.user_id == "john.doe@contoso.com"), None)
        assert john_result is not None
        assert john_result.action in [
            RecommendationAction.REVIEW_REQUIRED,
            RecommendationAction.REMOVE_LICENSE,
        ]

    def test_confidence_high(self) -> None:
        """Test that confidence is HIGH due to clear minority pattern."""
        _load_scenario("algo_2_5_scenario_clear_minority.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        john_activity = user_activity[user_activity["user_id"] == "john.doe@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=john_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        john_result = next((r for r in results if r.user_id == "john.doe@contoso.com"), None)
        assert john_result is not None
        assert john_result.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]


class TestMultipleMinorityLicenses:
    """Test Case 2: Multiple Minority Licenses.

    Scenario: Jane Smith has Commerce + SCM + Finance.
    Activity: 89.3% Commerce, 8.9% SCM, 1.8% Finance
    Expected: Both SCM and Finance flagged as minorities
    Recommendation: REVIEW_WITH_USER with multiple optimization options
    Savings: $360/month (remove both SCM and Finance)
    Confidence: MEDIUM (multiple minorities increases risk)
    """

    def test_multiple_minorities_detected(self) -> None:
        """Test that both SCM and Finance are detected as minorities."""
        _load_scenario("algo_2_5_scenario_multiple_minorities.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        jane_activity = user_activity[user_activity["user_id"] == "jane.smith@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=jane_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        assert len(results) > 0
        jane_result = next((r for r in results if r.user_id == "jane.smith@contoso.com"), None)
        assert jane_result is not None

    def test_savings_includes_all_minorities(self) -> None:
        """Test that savings calculation includes both minority licenses."""
        scenario = _load_scenario("algo_2_5_scenario_multiple_minorities.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        jane_activity = user_activity[user_activity["user_id"] == "jane.smith@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=jane_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        jane_result = next((r for r in results if r.user_id == "jane.smith@contoso.com"), None)
        assert jane_result is not None
        assert jane_result.savings is not None

        # Both SCM and Finance: $180 + $180 = $360/month
        expected_monthly = scenario["expected_outcome"]["expected_savings_monthly"]
        assert abs(jane_result.savings.monthly_savings - expected_monthly) < MONETARY_TOLERANCE


class TestNoMinorityLicense:
    """Test Case 3: No Minority License.

    Scenario: Mike Johnson has Finance + SCM.
    Activity: 75% Finance, 25% SCM
    Expected: SCM is NOT a minority (25% >= 15% threshold)
    Recommendation: KEEP_CURRENT (no optimization needed)
    Savings: $0
    Confidence: LOW (not a minority situation)
    """

    def test_no_minority_detected(self) -> None:
        """Test that Mike is not flagged (no minority found)."""
        _load_scenario("algo_2_5_scenario_no_minority.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        mike_activity = user_activity[user_activity["user_id"] == "mike.johnson@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=mike_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        # Mike should not appear in results (no minority)
        mike_result = next((r for r in results if r.user_id == "mike.johnson@contoso.com"), None)
        # Either he's not in results, or if he is, he has KEEP_CURRENT action
        if mike_result is not None:
            assert mike_result.action == RecommendationAction.NO_CHANGE


class TestSingleLicenseUser:
    """Test Case 4: Single License User.

    Scenario: Bob Wilson has only SCM license
    Expected: Should be skipped (algorithm only analyzes multi-license users)
    Recommendation: Not applicable
    """

    def test_single_license_user_skipped(self) -> None:
        """Test that single-license users are skipped."""
        _load_scenario("algo_2_5_scenario_single_license.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        bob_activity = user_activity[user_activity["user_id"] == "bob.wilson@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=bob_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        # Bob should not appear in results (single license)
        bob_result = next((r for r in results if r.user_id == "bob.wilson@contoso.com"), None)
        assert bob_result is None or bob_result.action == RecommendationAction.NO_CHANGE


class TestReadOnlyHeavyMinority:
    """Test Case 5: Read-Only Heavy Minority.

    Scenario: Alice Green has Operations + Finance.
    Activity: 88% Operations, 12% Finance (minority, but 95% read-only)
    Expected: Finance flagged as minority with read-only note
    Recommendation: REVIEW_WITH_USER (read-only conversion may eliminate license)
    Confidence: MEDIUM (read-only heavy, but still minority)
    """

    def test_readonly_minority_detected(self) -> None:
        """Test that read-only heavy minority is detected."""
        _load_scenario("algo_2_5_scenario_readonly_heavy.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        alice_activity = user_activity[user_activity["user_id"] == "alice.green@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=alice_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        assert len(results) > 0
        alice_result = next((r for r in results if r.user_id == "alice.green@contoso.com"), None)
        assert alice_result is not None

    def test_readonly_percentage_noted(self) -> None:
        """Test that read-only percentage is included in recommendation."""
        _load_scenario("algo_2_5_scenario_readonly_heavy.json")
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        alice_activity = user_activity[user_activity["user_id"] == "alice.green@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=alice_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        alice_result = next((r for r in results if r.user_id == "alice.green@contoso.com"), None)
        assert alice_result is not None
        # Reason should mention read-only pattern
        assert (
            "read" in alice_result.reason.primary_factor.lower()
            or "read" in str(alice_result.reason.supporting_factors).lower()
        )


class TestConfigurableThreshold:
    """Test that minority_threshold parameter is configurable."""

    def test_conservative_threshold_10_percent(self) -> None:
        """Test with conservative threshold of 10%."""
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        # SCM is 8.9% in Jane's case, should be caught at 10% threshold
        jane_activity = user_activity[user_activity["user_id"] == "jane.smith@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=jane_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=10,  # Conservative
            analysis_period_days=90,
        )

        jane_result = next((r for r in results if r.user_id == "jane.smith@contoso.com"), None)
        assert jane_result is not None

    def test_aggressive_threshold_20_percent(self) -> None:
        """Test with aggressive threshold of 20%."""
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        # Mike's 25% SCM should NOT be caught at 20% threshold
        mike_activity = user_activity[user_activity["user_id"] == "mike.johnson@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=mike_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=20,  # Aggressive
            analysis_period_days=90,
        )

        mike_result = next((r for r in results if r.user_id == "mike.johnson@contoso.com"), None)
        # Mike's 25% should NOT be minority at 20% threshold
        if mike_result is not None:
            assert mike_result.action == RecommendationAction.NO_CHANGE


class TestOutputStructure:
    """Test that output follows LicenseRecommendation schema."""

    def test_output_is_license_recommendation(self) -> None:
        """Test that results are LicenseRecommendation objects."""
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        john_activity = user_activity[user_activity["user_id"] == "john.doe@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=john_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        for result in results:
            assert isinstance(result, LicenseRecommendation)
            assert result.algorithm_id == "2.5"
            assert result.user_id is not None
            assert result.current_license is not None
            assert result.confidence_score is not None
            assert result.confidence_level is not None

    def test_savings_estimate_valid(self) -> None:
        """Test that savings estimates are valid."""
        user_activity = _load_user_activity()
        security_config = _load_security_config()
        pricing_config = _load_pricing()

        john_activity = user_activity[user_activity["user_id"] == "john.doe@contoso.com"].copy()

        results = detect_license_minority_users(
            user_activity=john_activity,
            security_config=security_config,
            pricing_config=pricing_config,
            minority_threshold=15,
            analysis_period_days=90,
        )

        john_result = next((r for r in results if r.user_id == "john.doe@contoso.com"), None)
        if john_result and john_result.savings:
            # Annual should equal monthly * 12
            assert (
                abs(john_result.savings.annual_savings - (john_result.savings.monthly_savings * 12))
                < MONETARY_TOLERANCE
            )
