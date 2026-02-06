"""Tests for Algorithm 2.2: Read-Only User Detector.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until src/algorithms/algorithm_2_2_readonly_detector.py
is implemented.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 523-654.

Algorithm 2.2 analyzes user activity data over a configurable period (default 90 days)
to identify users whose read-operation percentage exceeds a threshold (default 95%).
Candidates are evaluated for license downgrade based on:
  - Read vs write operation ratio
  - Whether write operations target Team Members-eligible forms
  - Current license type (already-optimal users are skipped)
  - Confidence scoring from write-operation count and self-service pattern detection

Each test loads:
  - A JSON scenario fixture (user profile, activity summary, expected recommendation)
  - CSV data files (security_config_sample.csv, user_activity_log_sample.csv)
  - Pricing configuration for savings validation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_2_2_readonly_detector import detect_readonly_users
from src.models.output_schemas import (
    LicenseRecommendation,
    RecommendationAction,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

# Tolerance for floating-point comparisons on confidence scores
CONFIDENCE_TOLERANCE: float = 0.05

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
        Parsed JSON as a dictionary containing user info, activity summary,
        and expected recommendation fields.
    """
    path = FIXTURES_DIR / filename
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_security_config() -> pd.DataFrame:
    """Load the security configuration sample CSV.

    Returns:
        DataFrame with columns: securityrole, AOTName, AccessLevel,
        LicenseType, Priority, Entitled, NotEntitled, securitytype.
    """
    return pd.read_csv(FIXTURES_DIR / "security_config_sample.csv")


def _load_user_activity() -> pd.DataFrame:
    """Load the user activity log sample CSV.

    Returns:
        DataFrame with columns: user_id, timestamp, menu_item, action,
        session_id, license_tier, feature.
    """
    return pd.read_csv(FIXTURES_DIR / "user_activity_log_sample.csv")


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON.

    Returns:
        Parsed pricing config with license costs and savings rules.
    """
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _find_recommendation_for_user(
    results: list[LicenseRecommendation],
    user_id: str,
) -> LicenseRecommendation | None:
    """Find the recommendation for a specific user in the results list.

    Args:
        results: List of LicenseRecommendation objects from detect_readonly_users.
        user_id: The user_id to search for.

    Returns:
        The matching LicenseRecommendation, or None if the user was not
        included in the results (expected for no-change / already-optimized).
    """
    for rec in results:
        if rec.user_id == user_id:
            return rec
    return None


# ---------------------------------------------------------------------------
# Test: Obvious Optimization (USR001)
# ---------------------------------------------------------------------------


class TestObviousOptimization:
    """Test scenario: USR001 with 99.76% read operations on a Commerce license.

    This user is a textbook downgrade candidate:
    - 847 read operations out of 849 total (99.76% read-only)
    - Only 2 write operations, both to self-service forms (UserProfile, TimeEntry)
    - All accessed forms are Team Members-eligible
    - Current license: Commerce ($180/month)
    - Expected: downgrade to Team Members ($60/month), saving $120/month ($1440/year)

    The algorithm should produce a HIGH confidence recommendation because:
    - Write count <= 2 (HIGH confidence per pseudocode)
    - All writes are self-service (additional HIGH confidence factor)
    - Read percentage (99.76%) far exceeds the 95% threshold
    """

    def test_obvious_optimization(self) -> None:
        """USR001 should receive a downgrade recommendation to Team Members.

        Validates the complete recommendation output:
        1. Action is 'downgrade' (not no_change or review_required)
        2. Target license is Team Members
        3. Confidence score meets or exceeds expected threshold (within tolerance)
        4. Savings calculation matches expected annual savings
        5. Algorithm correctly identifies current Commerce license
        """
        # -- Arrange --
        scenario: dict[str, Any] = _load_scenario("test_scenario_obvious_optimization.json")
        security_config: pd.DataFrame = _load_security_config()
        user_activity: pd.DataFrame = _load_user_activity()
        pricing: dict[str, Any] = _load_pricing()

        expected: dict[str, Any] = scenario["expected_recommendation"]
        user_info: dict[str, Any] = scenario["user"]

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=user_activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        recommendation: LicenseRecommendation | None = _find_recommendation_for_user(
            results, user_info["user_id"]
        )
        assert recommendation is not None, (
            f"Expected a recommendation for user {user_info['user_id']} "
            f"but detect_readonly_users returned no result for this user. "
            f"Returned user_ids: {[r.user_id for r in results]}"
        )

        # Action must be downgrade
        assert recommendation.action == RecommendationAction.DOWNGRADE, (
            f"Expected action='downgrade' for user {user_info['user_id']} "
            f"with {scenario['activity_summary']['read_percentage']}% read ops, "
            f"got action='{recommendation.action.value}'"
        )

        # Target license must be Team Members
        assert recommendation.recommended_license == expected["to_license"], (
            f"Expected recommended_license='{expected['to_license']}', "
            f"got '{recommendation.recommended_license}'"
        )

        # Confidence score must meet threshold (within tolerance)
        assert (
            recommendation.confidence_score >= expected["confidence_score"] - CONFIDENCE_TOLERANCE
        ), (
            f"Expected confidence_score >= {expected['confidence_score'] - CONFIDENCE_TOLERANCE:.2f} "
            f"(threshold {expected['confidence_score']} with {CONFIDENCE_TOLERANCE} tolerance), "
            f"got {recommendation.confidence_score:.4f}"
        )

        # Savings must be populated for a downgrade action
        assert (
            recommendation.savings is not None
        ), "Savings estimate must not be None for a downgrade recommendation"

        # Annual savings must match expected value
        assert (
            abs(recommendation.savings.annual_savings - expected["estimated_annual_savings"])
            <= MONETARY_TOLERANCE
        ), (
            f"Expected annual_savings={expected['estimated_annual_savings']}, "
            f"got {recommendation.savings.annual_savings}"
        )

        # Monthly savings sanity check
        assert (
            abs(recommendation.savings.monthly_savings - expected["estimated_monthly_savings"])
            <= MONETARY_TOLERANCE
        ), (
            f"Expected monthly_savings={expected['estimated_monthly_savings']}, "
            f"got {recommendation.savings.monthly_savings}"
        )

        # Current license must be correctly identified
        assert recommendation.current_license == user_info["current_license"], (
            f"Expected current_license='{user_info['current_license']}', "
            f"got '{recommendation.current_license}'"
        )


# ---------------------------------------------------------------------------
# Test: Edge Case No Change (USR002)
# ---------------------------------------------------------------------------


class TestEdgeCaseNoChange:
    """Test scenario: USR002 with 50/50 read-write split on an SCM license.

    This user should NOT be flagged for downgrade:
    - 250 read operations, 250 write operations (50% read)
    - Heavy transactional writes: PurchaseOrder (200), VendorInvoice (30),
      InventoryAdjustment (15) -- none are Team Members-eligible
    - Read percentage (50%) is well below the 95% threshold
    - Current license: SCM ($180/month)
    - Expected: no_change -- user genuinely needs full SCM access

    The algorithm should either:
    a) Not include USR002 in results at all (read% < threshold), or
    b) Include USR002 with action=no_change

    Either is acceptable because the user does not meet the read-only threshold.
    """

    def test_edge_case_no_change(self) -> None:
        """USR002 should NOT receive a downgrade recommendation.

        Validates that the algorithm correctly rejects users whose read
        percentage falls below the configurable threshold (default 95%).
        A 50/50 split user with heavy transactional writes must retain
        their current license.
        """
        # -- Arrange --
        scenario: dict[str, Any] = _load_scenario("test_scenario_edge_case.json")
        security_config: pd.DataFrame = _load_security_config()
        user_activity: pd.DataFrame = _load_user_activity()
        pricing: dict[str, Any] = _load_pricing()

        expected: dict[str, Any] = scenario["expected_recommendation"]
        user_info: dict[str, Any] = scenario["user"]

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=user_activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        recommendation: LicenseRecommendation | None = _find_recommendation_for_user(
            results, user_info["user_id"]
        )

        # Option A: user not in results (read% below threshold, correctly filtered)
        # Option B: user in results with action=no_change
        if recommendation is None:
            # Acceptable: algorithm correctly skipped user below threshold.
            # Verify that the user's read percentage is indeed below the default
            # 95% threshold per the fixture data.
            assert scenario["activity_summary"]["read_percentage"] < 95.0, (
                f"User {user_info['user_id']} was excluded from results but has "
                f"read_percentage={scenario['activity_summary']['read_percentage']}% "
                f"which is above the 95% threshold -- this user should have been analyzed."
            )
        else:
            # If included, action must be no_change
            assert recommendation.action == RecommendationAction.NO_CHANGE, (
                f"Expected action='no_change' for user {user_info['user_id']} "
                f"with {scenario['activity_summary']['read_percentage']}% read ops, "
                f"got action='{recommendation.action.value}'"
            )

            # Confidence score should still meet a reasonable threshold
            assert (
                recommendation.confidence_score
                >= expected["confidence_score"] - CONFIDENCE_TOLERANCE
            ), (
                f"Expected confidence_score >= {expected['confidence_score'] - CONFIDENCE_TOLERANCE:.2f}, "
                f"got {recommendation.confidence_score:.4f}"
            )

            # Savings must be zero for no_change
            if recommendation.savings is not None:
                assert abs(recommendation.savings.annual_savings) <= MONETARY_TOLERANCE, (
                    f"Expected zero annual_savings for no_change action, "
                    f"got {recommendation.savings.annual_savings}"
                )
                assert abs(recommendation.savings.monthly_savings) <= MONETARY_TOLERANCE, (
                    f"Expected zero monthly_savings for no_change action, "
                    f"got {recommendation.savings.monthly_savings}"
                )


# ---------------------------------------------------------------------------
# Test: Already Optimized (USR005)
# ---------------------------------------------------------------------------


class TestAlreadyOptimized:
    """Test scenario: USR005 already on Team Members license with 98.44% reads.

    This user is already on the lowest-cost applicable license:
    - 315 read operations, 5 write operations (98.44% read-only)
    - All 5 writes are to self-service forms (TimeEntry, ExpenseReport, UserProfile)
    - Current license: Team Members ($60/month) -- already the cheapest
    - Expected: no_change -- no further downgrade possible

    Even though the user meets the read-only threshold, the algorithm should
    recognize that Team Members IS the recommended license and therefore
    report no savings opportunity. This validates the "already optimal" path
    in the algorithm logic.
    """

    def test_already_optimized(self) -> None:
        """USR005 should receive no_change -- already on Team Members license.

        Validates that the algorithm:
        1. Recognizes users already on the optimal license
        2. Does not recommend downgrading Team Members further
        3. Reports zero savings for already-optimized users
        4. Still calculates a confidence score for the no-change decision
        """
        # -- Arrange --
        scenario: dict[str, Any] = _load_scenario("test_scenario_already_optimized.json")
        security_config: pd.DataFrame = _load_security_config()
        user_activity: pd.DataFrame = _load_user_activity()
        pricing: dict[str, Any] = _load_pricing()

        expected: dict[str, Any] = scenario["expected_recommendation"]
        user_info: dict[str, Any] = scenario["user"]

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=user_activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        recommendation: LicenseRecommendation | None = _find_recommendation_for_user(
            results, user_info["user_id"]
        )

        # The algorithm may either:
        # A) Skip already-optimized users entirely (not in results), or
        # B) Include them with action=no_change
        if recommendation is None:
            # Acceptable: algorithm detected that Team Members is already optimal
            # and did not generate a redundant recommendation.
            # Verify the user is indeed on Team Members per fixture.
            assert user_info["current_license"] == "Team Members", (
                f"User {user_info['user_id']} was excluded from results but is on "
                f"'{user_info['current_license']}' -- only Team Members users should be "
                f"excluded for the already-optimized reason."
            )
        else:
            # If included, the action must be no_change (cannot downgrade below
            # Team Members in the D365 FO license hierarchy).
            assert recommendation.action == RecommendationAction.NO_CHANGE, (
                f"Expected action='no_change' for user {user_info['user_id']} "
                f"already on Team Members license, "
                f"got action='{recommendation.action.value}'"
            )

            # Current license reported correctly
            assert recommendation.current_license == user_info["current_license"], (
                f"Expected current_license='{user_info['current_license']}', "
                f"got '{recommendation.current_license}'"
            )

            # Confidence score should be reasonable
            assert (
                recommendation.confidence_score
                >= expected["confidence_score"] - CONFIDENCE_TOLERANCE
            ), (
                f"Expected confidence_score >= {expected['confidence_score'] - CONFIDENCE_TOLERANCE:.2f}, "
                f"got {recommendation.confidence_score:.4f}"
            )

            # Savings must be zero -- no downgrade possible
            if recommendation.savings is not None:
                assert abs(recommendation.savings.annual_savings) <= MONETARY_TOLERANCE, (
                    f"Expected zero annual_savings for already-optimized user, "
                    f"got {recommendation.savings.annual_savings}"
                )
                assert abs(recommendation.savings.monthly_savings) <= MONETARY_TOLERANCE, (
                    f"Expected zero monthly_savings for already-optimized user, "
                    f"got {recommendation.savings.monthly_savings}"
                )

            # Recommended license should be None or same as current (no change)
            if recommendation.recommended_license is not None:
                assert recommendation.recommended_license == user_info["current_license"], (
                    f"Expected recommended_license to be None or '{user_info['current_license']}' "
                    f"for no_change action, got '{recommendation.recommended_license}'"
                )
