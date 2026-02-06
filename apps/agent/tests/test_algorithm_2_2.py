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


# ---------------------------------------------------------------------------
# Helpers: programmatic DataFrame construction for precise test control
# ---------------------------------------------------------------------------


def _build_activity_df(
    user_id: str,
    read_count: int,
    write_items: list[tuple[str, int, str, str]],
    read_license_tier: str = "Team Members",
    read_menu_item: str = "CustomerList",
    read_feature: str = "Accounts Receivable",
) -> pd.DataFrame:
    """Build a synthetic activity DataFrame for a single user.

    This helper constructs a precisely controlled activity log that avoids
    reliance on CSV fixtures when exact operation counts matter (boundary
    tests, threshold tests, etc.).

    Args:
        user_id: The user identifier.
        read_count: Number of read operations to generate.
        write_items: List of (menu_item, count, license_tier, feature) tuples
            for write operations.
        read_license_tier: License tier for read operations.
        read_menu_item: Menu item for read operations.
        read_feature: Feature name for read operations.

    Returns:
        DataFrame with columns matching the user_activity_log_sample.csv schema.
    """
    rows: list[dict[str, str]] = []

    # Generate read operations
    for i in range(read_count):
        rows.append(
            {
                "user_id": user_id,
                "timestamp": f"2026-01-15 09:{i // 60:02d}:{i % 60:02d}",
                "menu_item": read_menu_item,
                "action": "Read",
                "session_id": f"sess-synth-{i:04d}",
                "license_tier": read_license_tier,
                "feature": read_feature,
            }
        )

    # Generate write operations
    write_idx: int = read_count
    for menu_item, count, tier, feature in write_items:
        for j in range(count):
            rows.append(
                {
                    "user_id": user_id,
                    "timestamp": f"2026-01-16 10:{(write_idx + j) // 60:02d}:"
                    f"{(write_idx + j) % 60:02d}",
                    "menu_item": menu_item,
                    "action": "Write",
                    "session_id": f"sess-synth-w-{write_idx + j:04d}",
                    "license_tier": tier,
                    "feature": feature,
                }
            )
        write_idx += count

    return pd.DataFrame(rows)


def _build_multi_user_activity_df(
    users: list[tuple[str, int, list[tuple[str, int, str, str]], str]],
) -> pd.DataFrame:
    """Build activity data for multiple users.

    Args:
        users: List of (user_id, read_count, write_items, read_license_tier)
            tuples.  write_items follows the same format as _build_activity_df.

    Returns:
        Combined DataFrame for all users.
    """
    frames: list[pd.DataFrame] = []
    for user_id, read_count, write_items, read_tier in users:
        frames.append(
            _build_activity_df(
                user_id=user_id,
                read_count=read_count,
                write_items=write_items,
                read_license_tier=read_tier,
            )
        )
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Test: Boundary Threshold -- Exactly 95% reads
# ---------------------------------------------------------------------------


class TestBoundaryThresholdExact95:
    """Test scenario: User with exactly 95.0% read operations.

    The default read_threshold is 0.95 (95%).  A user with exactly 95.0%
    reads sits precisely at the threshold boundary.  Because the algorithm
    uses ``read_percentage < threshold_pct`` for rejection, 95.0% should
    PASS the threshold (it is not less than 95.0%).

    Setup:
    - 200 total operations: 190 reads + 10 writes
    - 190 / 200 = 95.0% exactly
    - All writes to self-service forms (UserProfile)
    - License tier: Finance ($180) -- should downgrade to Team Members ($60)
    """

    def test_boundary_exact_95_percent_reads(self) -> None:
        """User at exactly 95.0% reads should qualify for downgrade."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="BOUNDARY_95",
            read_count=190,
            write_items=[("UserProfile", 10, "Team Members", "Self-Service")],
            read_license_tier="Finance",
            read_menu_item="GeneralJournalEntry",
            read_feature="General Ledger",
        )
        # Add one Finance-tier read to establish highest tier
        activity.loc[0, "license_tier"] = "Finance"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "BOUNDARY_95")
        assert rec is not None, (
            "User at exactly 95.0% reads should be included in results "
            "(95.0% is not less than the 95.0% threshold)"
        )
        assert rec.action == RecommendationAction.DOWNGRADE, (
            f"Expected downgrade for boundary user at 95.0% reads, " f"got {rec.action.value}"
        )
        assert rec.recommended_license == "Team Members"
        assert rec.savings is not None
        assert abs(rec.savings.monthly_savings - 120.0) <= MONETARY_TOLERANCE
        assert abs(rec.savings.annual_savings - 1440.0) <= MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test: Configurable Threshold -- read_threshold=0.90
# ---------------------------------------------------------------------------


class TestConfigurableThresholdLow:
    """Test scenario: Lowered threshold allows a 92% read user to qualify.

    By passing read_threshold=0.90, a user with 92% reads (below the default
    95%) should now qualify as a read-only candidate.

    Setup:
    - 200 total operations: 184 reads + 16 writes
    - 184 / 200 = 92.0%
    - All writes to self-service (TimeEntry)
    - License tier: SCM ($180)
    """

    def test_lowered_threshold_90_percent(self) -> None:
        """User at 92% reads qualifies with read_threshold=0.90."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="THRESHOLD_LOW",
            read_count=184,
            write_items=[("TimeEntry", 16, "Team Members", "Self-Service")],
            read_license_tier="SCM",
            read_menu_item="InventoryOnHand",
            read_feature="Inventory",
        )
        # Ensure highest tier is SCM
        activity.loc[0, "license_tier"] = "SCM"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
            read_threshold=0.90,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "THRESHOLD_LOW")
        assert rec is not None, "User at 92% reads should qualify when read_threshold=0.90"
        assert rec.action == RecommendationAction.DOWNGRADE
        assert rec.recommended_license == "Team Members"


# ---------------------------------------------------------------------------
# Test: Configurable Threshold -- read_threshold=0.98
# ---------------------------------------------------------------------------


class TestConfigurableThresholdHigh:
    """Test scenario: Raised threshold excludes a 96% read user.

    By passing read_threshold=0.98, a user with 96% reads (above the default
    95% but below 98%) should NOT qualify.

    Setup:
    - 200 total operations: 192 reads + 8 writes
    - 192 / 200 = 96.0%
    - License tier: Commerce ($180)
    """

    def test_raised_threshold_98_percent(self) -> None:
        """User at 96% reads does NOT qualify with read_threshold=0.98."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="THRESHOLD_HIGH",
            read_count=192,
            write_items=[("UserProfile", 8, "Team Members", "Self-Service")],
            read_license_tier="Commerce",
            read_menu_item="RetailStore",
            read_feature="Retail",
        )
        activity.loc[0, "license_tier"] = "Commerce"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
            read_threshold=0.98,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "THRESHOLD_HIGH")
        # User should be excluded (96% < 98% threshold) or marked no_change
        if rec is not None:
            assert rec.action == RecommendationAction.NO_CHANGE, (
                f"User at 96% reads should not get downgrade with threshold=98%, "
                f"got {rec.action.value}"
            )
        # If rec is None, that is also acceptable (excluded by threshold filter)


# ---------------------------------------------------------------------------
# Test: Self-Service Write Classification
# ---------------------------------------------------------------------------


class TestSelfServiceWriteClassification:
    """Test scenario: User with writes ONLY to self-service forms.

    Validates that when all write operations target self-service forms
    (UserProfile, TimeEntry, ExpenseReport), the algorithm:
    1. Classifies the user as a downgrade candidate
    2. Applies the +0.15 self-service confidence boost
    3. Produces HIGH confidence level

    Setup:
    - 200 total operations: 195 reads + 5 writes
    - 195 / 200 = 97.5%
    - 5 writes: 2 TimeEntry, 2 ExpenseReport, 1 UserProfile (all self-service)
    - License tier: Finance ($180)
    """

    def test_self_service_writes_get_confidence_boost(self) -> None:
        """All self-service writes should trigger confidence boost and downgrade."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="SELF_SERVICE",
            read_count=195,
            write_items=[
                ("TimeEntry", 2, "Team Members", "Self-Service"),
                ("ExpenseReport", 2, "Team Members", "Self-Service"),
                ("UserProfile", 1, "Team Members", "Self-Service"),
            ],
            read_license_tier="Finance",
            read_menu_item="GeneralJournalEntry",
            read_feature="General Ledger",
        )
        activity.loc[0, "license_tier"] = "Finance"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "SELF_SERVICE")
        assert rec is not None, "Self-service write user should be in results"
        assert rec.action == RecommendationAction.DOWNGRADE
        assert rec.recommended_license == "Team Members"

        # 5 writes (<=10) -> base 0.75, all self-service -> +0.15 = 0.90
        # Confidence level should be HIGH (>= 0.90)
        from src.models.output_schemas import ConfidenceLevel

        assert rec.confidence_score >= 0.90 - CONFIDENCE_TOLERANCE, (
            f"Expected confidence >= 0.85 (0.90 with tolerance) for self-service writes, "
            f"got {rec.confidence_score}"
        )
        assert rec.confidence_level == ConfidenceLevel.HIGH


# ---------------------------------------------------------------------------
# Test: Non-Self-Service Write Rejection
# ---------------------------------------------------------------------------


class TestNonSelfServiceWriteRejection:
    """Test scenario: User with 96% reads but writes to PurchaseOrder.

    Even though the user exceeds the 95% read threshold, writes to
    non-self-service forms (PurchaseOrder) indicate genuine transactional
    need.  The algorithm should NOT recommend a downgrade.

    Setup:
    - 200 total operations: 192 reads + 8 writes
    - 192 / 200 = 96.0%
    - 8 writes to PurchaseOrder (NOT Team Members-eligible)
    - License tier: SCM ($180)
    - Expected: no_change (non-self-service writes block downgrade)
    """

    def test_non_self_service_writes_block_downgrade(self) -> None:
        """Writes to PurchaseOrder should prevent downgrade despite high read%."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="NON_SS_WRITE",
            read_count=192,
            write_items=[("PurchaseOrder", 8, "SCM", "Procurement")],
            read_license_tier="SCM",
            read_menu_item="VendorList",
            read_feature="Accounts Payable",
        )
        activity.loc[0, "license_tier"] = "SCM"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "NON_SS_WRITE")
        assert rec is not None, (
            "User above threshold should appear in results even with " "non-self-service writes"
        )
        assert rec.action == RecommendationAction.NO_CHANGE, (
            f"Expected no_change for user with PurchaseOrder writes, " f"got {rec.action.value}"
        )
        # Savings should be None (no downgrade) or zero
        if rec.savings is not None:
            assert abs(rec.savings.annual_savings) <= MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test: Empty Activity Data
# ---------------------------------------------------------------------------


class TestEmptyActivityData:
    """Test scenario: Empty DataFrame with no activity records.

    The algorithm must handle an empty input gracefully and return
    an empty results list without raising exceptions.
    """

    def test_empty_activity_returns_empty_results(self) -> None:
        """Empty user activity should produce zero recommendations."""
        # -- Arrange --
        empty_df: pd.DataFrame = pd.DataFrame(
            columns=[
                "user_id",
                "timestamp",
                "menu_item",
                "action",
                "session_id",
                "license_tier",
                "feature",
            ]
        )
        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=empty_df,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        assert results == [], (
            f"Expected empty results for empty activity data, "
            f"got {len(results)} recommendations"
        )


# ---------------------------------------------------------------------------
# Test: Insufficient Sample Size
# ---------------------------------------------------------------------------


class TestInsufficientSampleSize:
    """Test scenario: User with fewer operations than min_sample_size.

    The algorithm requires min_sample_size (default 100) operations to
    produce a recommendation.  A user with only 50 operations should be
    skipped entirely, regardless of their read percentage.

    Setup:
    - 50 total operations: 49 reads + 1 write
    - 49 / 50 = 98.0% reads (would qualify on threshold alone)
    - But 50 < 100 (min_sample_size) -> excluded
    """

    def test_insufficient_sample_excluded(self) -> None:
        """User with 50 operations should be excluded (below min_sample_size)."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="SMALL_SAMPLE",
            read_count=49,
            write_items=[("UserProfile", 1, "Team Members", "Self-Service")],
            read_license_tier="Finance",
            read_menu_item="GeneralJournalEntry",
            read_feature="General Ledger",
        )
        activity.loc[0, "license_tier"] = "Finance"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
            # Default min_sample_size=100, so 50 ops < 100
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "SMALL_SAMPLE")
        assert rec is None, "User with 50 operations should be excluded when min_sample_size=100"


# ---------------------------------------------------------------------------
# Test: Batch Processing -- 10+ Users
# ---------------------------------------------------------------------------


class TestBatchProcessingMultipleUsers:
    """Test scenario: 12 users processed in a single batch call.

    Validates that the algorithm can handle multiple users simultaneously
    and produces the correct recommendation for each based on their
    individual activity patterns.

    User mix:
    - 4 downgrade candidates (high read%, self-service writes only)
    - 4 no-change users (high read% but non-self-service writes)
    - 2 below-threshold users (should be excluded)
    - 2 already-optimal Team Members users
    """

    def test_batch_12_users_correct_classification(self) -> None:
        """12-user batch should produce correct per-user recommendations."""
        # -- Arrange --
        users: list[tuple[str, int, list[tuple[str, int, str, str]], str]] = []

        # 4 downgrade candidates: 97% reads, self-service writes, Finance tier
        for i in range(4):
            users.append(
                (
                    f"BATCH_DOWN_{i}",
                    194,
                    [("UserProfile", 6, "Team Members", "Self-Service")],
                    "Finance",
                )
            )

        # 4 no-change users: 96% reads, non-self-service writes, SCM tier
        for i in range(4):
            users.append(
                (
                    f"BATCH_KEEP_{i}",
                    192,
                    [("PurchaseOrder", 8, "SCM", "Procurement")],
                    "SCM",
                )
            )

        # 2 below-threshold users: 80% reads (excluded)
        for i in range(2):
            users.append(
                (
                    f"BATCH_LOW_{i}",
                    160,
                    [("PurchaseOrder", 40, "SCM", "Procurement")],
                    "SCM",
                )
            )

        # 2 already-optimal Team Members users: 98% reads
        for i in range(2):
            users.append(
                (
                    f"BATCH_TM_{i}",
                    196,
                    [("TimeEntry", 4, "Team Members", "Self-Service")],
                    "Team Members",
                )
            )

        activity: pd.DataFrame = _build_multi_user_activity_df(users)
        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        # Downgrade candidates must all be present with action=downgrade
        for i in range(4):
            uid: str = f"BATCH_DOWN_{i}"
            rec: LicenseRecommendation | None = _find_recommendation_for_user(results, uid)
            assert rec is not None, f"{uid} should be in results"
            assert (
                rec.action == RecommendationAction.DOWNGRADE
            ), f"{uid} should be downgrade, got {rec.action.value}"

        # No-change users should be in results with no_change
        for i in range(4):
            uid = f"BATCH_KEEP_{i}"
            rec = _find_recommendation_for_user(results, uid)
            assert rec is not None, f"{uid} should be in results (above threshold)"
            assert (
                rec.action == RecommendationAction.NO_CHANGE
            ), f"{uid} should be no_change, got {rec.action.value}"

        # Below-threshold users should be excluded
        for i in range(2):
            uid = f"BATCH_LOW_{i}"
            rec = _find_recommendation_for_user(results, uid)
            assert rec is None, f"{uid} at 80% reads should be excluded (below 95% threshold)"

        # Already-optimal Team Members users: either excluded or no_change
        for i in range(2):
            uid = f"BATCH_TM_{i}"
            rec = _find_recommendation_for_user(results, uid)
            if rec is not None:
                assert rec.action == RecommendationAction.NO_CHANGE, (
                    f"{uid} on Team Members should be no_change, " f"got {rec.action.value}"
                )


# ---------------------------------------------------------------------------
# Test: Operations License User -- Smaller Savings
# ---------------------------------------------------------------------------


class TestOperationsLicenseDowngrade:
    """Test scenario: Operations license ($90) user downgrade to Team Members ($60).

    Validates savings calculation for a mid-tier license that produces
    smaller per-user savings than the $180 full licenses.

    Setup:
    - 200 total operations: 198 reads + 2 writes
    - 198 / 200 = 99.0%
    - 2 writes to TimeEntry (self-service)
    - License tier: Operations ($90)
    - Expected: downgrade to Team Members ($60), saving $30/month ($360/year)
    """

    def test_operations_to_team_members_savings(self) -> None:
        """Operations user should save $30/month when downgraded."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="OPS_USER",
            read_count=198,
            write_items=[("TimeEntry", 2, "Team Members", "Self-Service")],
            read_license_tier="Operations",
            read_menu_item="SalesOrder",
            read_feature="Sales",
        )
        # Ensure Operations is the highest tier
        activity.loc[0, "license_tier"] = "Operations"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "OPS_USER")
        assert rec is not None, "Operations user above threshold should be in results"
        assert rec.action == RecommendationAction.DOWNGRADE
        assert rec.current_license == "Operations"
        assert rec.recommended_license == "Team Members"
        assert rec.savings is not None
        assert abs(rec.savings.monthly_savings - 30.0) <= MONETARY_TOLERANCE, (
            f"Expected $30 monthly savings (Operations $90 -> Team Members $60), "
            f"got {rec.savings.monthly_savings}"
        )
        assert (
            abs(rec.savings.annual_savings - 360.0) <= MONETARY_TOLERANCE
        ), f"Expected $360 annual savings, got {rec.savings.annual_savings}"


# ---------------------------------------------------------------------------
# Test: Single Operation Edge Case (with lowered min_sample_size)
# ---------------------------------------------------------------------------


class TestSingleOperationEdgeCase:
    """Test scenario: User with exactly 1 read operation.

    With min_sample_size=1, a user with a single read operation should
    produce a valid recommendation (100% reads, zero writes).

    This tests the extreme boundary of the algorithm's handling of
    minimal data.
    """

    def test_single_read_operation(self) -> None:
        """Single read operation with min_sample_size=1 should produce result."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="SINGLE_OP",
            read_count=1,
            write_items=[],
            read_license_tier="Commerce",
            read_menu_item="RetailStore",
            read_feature="Retail",
        )

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
            min_sample_size=1,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "SINGLE_OP")
        assert rec is not None, "Single-read user with min_sample_size=1 should be in results"
        assert rec.action == RecommendationAction.DOWNGRADE
        assert rec.recommended_license == "Team Members"
        # 100% reads, 0 writes -> confidence = 1.0 (perfect)
        assert abs(rec.confidence_score - 1.0) <= CONFIDENCE_TOLERANCE
        assert rec.sample_size == 1


# ---------------------------------------------------------------------------
# Test: All Reads, Zero Writes -- Perfect Read-Only
# ---------------------------------------------------------------------------


class TestAllReadsZeroWrites:
    """Test scenario: User with 100% read operations (zero writes).

    This is the purest read-only case.  The algorithm should produce:
    - Action: downgrade
    - Confidence: 1.0 (zero writes -> highest possible confidence)
    - Full savings from current tier to Team Members

    Setup:
    - 200 total operations: 200 reads + 0 writes
    - 200 / 200 = 100.0%
    - License tier: Finance ($180)
    """

    def test_pure_readonly_maximum_confidence(self) -> None:
        """100% read user should get confidence 1.0 and full downgrade."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="PURE_READER",
            read_count=200,
            write_items=[],
            read_license_tier="Finance",
            read_menu_item="GeneralJournalEntry",
            read_feature="General Ledger",
        )
        activity.loc[0, "license_tier"] = "Finance"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "PURE_READER")
        assert rec is not None, "100% read user should be in results"
        assert rec.action == RecommendationAction.DOWNGRADE
        assert rec.recommended_license == "Team Members"

        # Zero writes -> confidence = 1.0 exactly
        assert abs(rec.confidence_score - 1.0) <= CONFIDENCE_TOLERANCE, (
            f"Expected confidence ~1.0 for zero-write user, " f"got {rec.confidence_score}"
        )

        from src.models.output_schemas import ConfidenceLevel

        assert rec.confidence_level == ConfidenceLevel.HIGH

        # Savings: Finance $180 -> Team Members $60 = $120/month
        assert rec.savings is not None
        assert abs(rec.savings.monthly_savings - 120.0) <= MONETARY_TOLERANCE
        assert abs(rec.savings.annual_savings - 1440.0) <= MONETARY_TOLERANCE

        # safe_to_automate should be True (downgrade + HIGH confidence)
        assert rec.safe_to_automate is True


# ---------------------------------------------------------------------------
# Test: All Writes -- Heavy Writer
# ---------------------------------------------------------------------------


class TestAllWritesHeavyWriter:
    """Test scenario: User with 0% reads (all write operations).

    This user has zero read operations and 200 write operations.
    Read percentage = 0%, which is far below the 95% threshold.
    The algorithm should exclude this user entirely.

    Setup:
    - 200 total operations: 0 reads + 200 writes
    - 0 / 200 = 0.0% reads
    - License tier: SCM ($180)
    """

    def test_all_writes_excluded(self) -> None:
        """User with 0% reads should be excluded from results."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="HEAVY_WRITER",
            read_count=0,
            write_items=[("PurchaseOrder", 200, "SCM", "Procurement")],
            read_license_tier="SCM",
        )

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "HEAVY_WRITER")
        assert rec is None, "User with 0% reads should be excluded (far below 95% threshold)"


# ---------------------------------------------------------------------------
# Test: Medium Write Count -- Confidence Scoring Tiers
# ---------------------------------------------------------------------------


class TestMediumWriteCountConfidence:
    """Test scenario: User with 7 writes (medium confidence tier).

    Per the confidence specification:
    - writeOpCount <= 10 -> base score 0.75, MEDIUM
    - If all self-service -> +0.15 boost = 0.90, HIGH

    This test validates the medium write count tier without the
    self-service boost (writes to PurchaseOrder).

    Setup:
    - 200 total operations: 193 reads + 7 writes
    - 193 / 200 = 96.5%
    - 7 writes to PurchaseOrder (non-self-service)
    - No downgrade (non-self-service writes), but confidence scoring tested
    """

    def test_medium_write_count_no_boost(self) -> None:
        """7 non-self-service writes should produce no_change with medium confidence."""
        # -- Arrange --
        activity: pd.DataFrame = _build_activity_df(
            user_id="MED_WRITES",
            read_count=193,
            write_items=[("PurchaseOrder", 7, "SCM", "Procurement")],
            read_license_tier="SCM",
            read_menu_item="VendorList",
            read_feature="Accounts Payable",
        )
        activity.loc[0, "license_tier"] = "SCM"

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        rec: LicenseRecommendation | None = _find_recommendation_for_user(results, "MED_WRITES")
        assert rec is not None, "User above threshold should be in results"
        assert rec.action == RecommendationAction.NO_CHANGE, (
            f"Non-self-service writes should block downgrade, " f"got {rec.action.value}"
        )
        # 7 writes -> base 0.75, no self-service boost
        assert abs(rec.confidence_score - 0.75) <= CONFIDENCE_TOLERANCE, (
            f"Expected confidence ~0.75 for 7 non-self-service writes, "
            f"got {rec.confidence_score}"
        )


# ---------------------------------------------------------------------------
# Test: Results Sorted by Savings Descending
# ---------------------------------------------------------------------------


class TestResultsSortedBySavings:
    """Test scenario: Multiple users sorted by annual savings descending.

    The algorithm specification requires results to be sorted by
    annual_savings in descending order so that the highest-value
    optimization opportunities appear first.

    Setup:
    - User A: Commerce ($180 -> $60 = $120/month savings)
    - User B: Operations ($90 -> $60 = $30/month savings)
    Both are clear downgrade candidates (100% reads).
    """

    def test_results_ordered_by_savings_desc(self) -> None:
        """Higher savings user should appear first in results."""
        # -- Arrange --
        users: list[tuple[str, int, list[tuple[str, int, str, str]], str]] = [
            # User B first in input (lower savings)
            ("SORT_OPS", 200, [], "Operations"),
            # User A second in input (higher savings)
            ("SORT_COMMERCE", 200, [], "Commerce"),
        ]
        activity: pd.DataFrame = _build_multi_user_activity_df(users)
        # Ensure correct highest tiers
        ops_mask = activity["user_id"] == "SORT_OPS"
        activity.loc[ops_mask & (activity.index == activity[ops_mask].index[0]), "license_tier"] = (
            "Operations"
        )
        com_mask = activity["user_id"] == "SORT_COMMERCE"
        activity.loc[com_mask & (activity.index == activity[com_mask].index[0]), "license_tier"] = (
            "Commerce"
        )

        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[LicenseRecommendation] = detect_readonly_users(
            user_activity=activity,
            security_config=security_config,
            pricing_config=pricing,
        )

        # -- Assert --
        downgrade_results: list[LicenseRecommendation] = [
            r for r in results if r.action == RecommendationAction.DOWNGRADE
        ]
        assert (
            len(downgrade_results) >= 2
        ), f"Expected at least 2 downgrade results, got {len(downgrade_results)}"

        # First result should have higher savings
        assert downgrade_results[0].savings is not None
        assert downgrade_results[1].savings is not None
        assert (
            downgrade_results[0].savings.annual_savings
            >= downgrade_results[1].savings.annual_savings
        ), (
            f"Results not sorted by savings descending: "
            f"first={downgrade_results[0].savings.annual_savings}, "
            f"second={downgrade_results[1].savings.annual_savings}"
        )
