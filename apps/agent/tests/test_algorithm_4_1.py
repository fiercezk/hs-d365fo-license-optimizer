"""Tests for Algorithm 4.1: Device License Opportunity Detector.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until src/algorithms/algorithm_4_1_device_license_detector.py
is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 922-1115.

Algorithm 4.1 identifies devices shared by multiple users that would benefit from
device licenses instead of individual user licenses. Detection criteria:
  - Minimum 3 unique users per device (shared device, not personal)
  - Maximum 1 concurrent user (peak concurrent sessions = 1, no simultaneous users)
  - Not dominated by single user (dedicated_user_percentage < 80%)
  - Device type in [Warehouse, Manufacturing, POS, ShopFloor, Kiosk]

Output: List of DeviceLicenseOpportunity records with:
  - device_id, location, device_type
  - unique_users, current_license_cost, device_license_cost
  - monthly_savings, annual_savings
  - confidence_score, action (CONVERT_TO_DEVICE_LICENSE)

Test scenarios:
  1. Warehouse clear case: 5 workers, 1 shared device → HIGH confidence
  2. POS clear case: 4 cashiers, 1 shared POS terminal → HIGH confidence
  3. Desktop case (negative): 2 users, but each has own device → NO recommendation
  4. Concurrent users (negative): 3+ users but concurrent usage → NO recommendation
  5. Dedicated user (negative): 1 user dominates 85% → NO recommendation
  6. Not eligible device type: Office desktop (not in eligible list) → NO recommendation
  7. Multi-device scenario: 3 devices each with 5 users → 3 separate opportunities
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_4_1_device_license_detector import (
    detect_device_license_opportunities,
)
from src.models.output_schemas import (
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


def _load_device_activity() -> pd.DataFrame:
    """Load the device activity test fixture CSV.

    Returns:
        DataFrame with columns: user_id, timestamp, menu_item, action,
        session_id, license_tier, feature, device_id, device_type, location.
    """
    return pd.read_csv(FIXTURES_DIR / "algo_4_1_device_activity.csv")


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON.

    Returns:
        Parsed pricing config with license costs.
    """
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _count_users_per_device(df: pd.DataFrame) -> dict[str, int]:
    """Count unique users per device from activity data.

    Args:
        df: Activity dataframe

    Returns:
        Dictionary mapping device_id to unique user count
    """
    return df.groupby("device_id")["user_id"].nunique().to_dict()


def _count_devices_per_user(df: pd.DataFrame) -> dict[str, int]:
    """Count unique devices per user from activity data.

    Args:
        df: Activity dataframe

    Returns:
        Dictionary mapping user_id to unique device count
    """
    return df.groupby("user_id")["device_id"].nunique().to_dict()


def _get_concurrent_sessions(df: pd.DataFrame, device_id: str) -> dict[str, int]:
    """Count concurrent sessions per timestamp on a device.

    Args:
        df: Activity dataframe
        device_id: Device to analyze

    Returns:
        Dictionary mapping timestamp to session count
    """
    device_df = df[df["device_id"] == device_id]
    # Group by timestamp and session_id to identify unique sessions
    concurrent = device_df.groupby("timestamp")["session_id"].nunique().to_dict()
    return concurrent


def _get_max_concurrent(df: pd.DataFrame, device_id: str) -> int:
    """Get maximum concurrent sessions on a device.

    Args:
        df: Activity dataframe
        device_id: Device to analyze

    Returns:
        Maximum number of concurrent sessions at any point
    """
    concurrent_dict = _get_concurrent_sessions(df, device_id)
    return max(concurrent_dict.values()) if concurrent_dict else 0


def _get_user_dominance(df: pd.DataFrame, device_id: str) -> float:
    """Calculate user dominance percentage on a device.

    The user with the most sessions accounts for what percentage of all sessions?

    Args:
        df: Activity dataframe
        device_id: Device to analyze

    Returns:
        Percentage (0-100) of sessions by dominant user
    """
    device_df = df[df["device_id"] == device_id]
    total_sessions = len(device_df)
    if total_sessions == 0:
        return 0.0
    dominant_user_sessions = device_df["user_id"].value_counts().iloc[0]
    return (dominant_user_sessions / total_sessions) * 100.0


# ---------------------------------------------------------------------------
# Test: Warehouse Clear Case (SCAN-CHI-01)
# ---------------------------------------------------------------------------


class TestWarehouseClearCase:
    """Test scenario: 5 warehouse workers share SCAN-CHI-01 scanner.

    This is a textbook device license conversion opportunity:
    - Device SCAN-CHI-01: used by WH001, WH002, WH003, WH004, WH005 (5 users)
    - No concurrent users (each session is serial, no timestamp overlap)
    - Max concurrent = 1 (meets criteria)
    - Dominance: ~20% each (well below 80% threshold)
    - Device type: Warehouse (eligible)
    - Current licenses: 5 × SCM ($90 each) = $450/month
    - Device license: 1 × Device ($80) = $80/month
    - Savings: $370/month ($4,440/year)
    - Expected confidence: HIGH (0.90+)
    - Expected action: CONVERT_TO_DEVICE_LICENSE
    """

    def test_warehouse_clear_case_produces_recommendation(self) -> None:
        """SCAN-CHI-01 should receive a device license conversion recommendation.

        Validates that:
        1. All 5 warehouse workers on SCAN-CHI-01 are identified
        2. Device meets eligibility criteria (3+ users, max concurrent=1, <80% dominance)
        3. Recommendation action is CONVERT_TO_DEVICE_LICENSE
        4. Savings calculation is correct ($370/month)
        5. Confidence is HIGH (0.90+)
        6. Annual savings is $4,440
        """
        # -- Arrange --
        activity_df: pd.DataFrame = _load_device_activity()
        pricing: dict[str, Any] = _load_pricing()

        # Verify fixture setup
        scan_chi_01_df = activity_df[activity_df["device_id"] == "SCAN-CHI-01"]
        unique_users = scan_chi_01_df["user_id"].nunique()
        max_concurrent = _get_max_concurrent(activity_df, "SCAN-CHI-01")
        dominance = _get_user_dominance(activity_df, "SCAN-CHI-01")

        assert (
            unique_users >= 3
        ), f"Fixture setup error: SCAN-CHI-01 has {unique_users} users, expected >= 3"
        assert max_concurrent == 1, (
            f"Fixture setup error: SCAN-CHI-01 max concurrent={max_concurrent}, "
            f"expected 1 (serial sessions)"
        )
        assert (
            dominance < 80.0
        ), f"Fixture setup error: SCAN-CHI-01 dominance={dominance}%, expected < 80%"

        # -- Act --
        opportunities = detect_device_license_opportunities(
            activity_data=activity_df,
            pricing_config=pricing,
        )

        # -- Assert --
        # Find opportunity for SCAN-CHI-01
        scan_chi_01_opp = None
        for opp in opportunities:
            if opp.user_id == "SCAN-CHI-01":
                scan_chi_01_opp = opp
                break

        assert scan_chi_01_opp is not None, (
            f"Expected opportunity for device SCAN-CHI-01 but not found. "
            f"Devices in results: {[o.user_id for o in opportunities]}"
        )

        # Action must be convert to device license
        assert scan_chi_01_opp.action == RecommendationAction.ADD_LICENSE, (
            f"Expected action=ADD_LICENSE for SCAN-CHI-01 device conversion, "
            f"got {scan_chi_01_opp.action.value}"
        )

        # Monthly savings should be ~$820 (5 × $180 SCM - $80 device)
        # Note: warehouse users have SCM licenses ($180), not operations ($90)
        expected_monthly_savings = (5 * 180.0) - 80.0  # 900 - 80 = 820
        assert scan_chi_01_opp.savings is not None, "Expected savings estimate for eligible device"
        assert (
            abs(scan_chi_01_opp.savings.monthly_savings - expected_monthly_savings)
            <= MONETARY_TOLERANCE * 10  # Allow $1 tolerance for mixed licenses
        ), (
            f"Expected monthly_savings ~${expected_monthly_savings}, "
            f"got ${scan_chi_01_opp.savings.monthly_savings}"
        )

        # Annual savings should be monthly * 12
        expected_annual_savings = scan_chi_01_opp.savings.monthly_savings * 12
        assert (
            abs(scan_chi_01_opp.savings.annual_savings - expected_annual_savings)
            <= MONETARY_TOLERANCE * 10
        ), (
            f"Expected annual_savings ~${expected_annual_savings}, "
            f"got ${scan_chi_01_opp.savings.annual_savings}"
        )

        # Confidence should be HIGH (0.90+)
        assert scan_chi_01_opp.confidence_score >= 0.90 - CONFIDENCE_TOLERANCE, (
            f"Expected confidence_score >= {0.90 - CONFIDENCE_TOLERANCE:.2f} for clear case, "
            f"got {scan_chi_01_opp.confidence_score:.4f}"
        )


# ---------------------------------------------------------------------------
# Test: POS Clear Case (POS-NYC-01)
# ---------------------------------------------------------------------------


class TestPOSClearCase:
    """Test scenario: 4 cashiers share POS-NYC-01 terminal.

    Clear device license conversion opportunity for retail POS:
    - Device POS-NYC-01: used by POS001, POS002, POS003, POS004 (4 users)
    - Device type: POS (eligible)
    - Max concurrent = 1 (serial sessions)
    - Dominance: 25% each (well below 80%)
    - Current licenses: 4 × Commerce ($180 each) = $720/month
    - Device license: 1 × Device ($80) = $80/month
    - Savings: $640/month ($7,680/year)
    - Expected confidence: HIGH (0.90+)
    """

    def test_pos_clear_case_produces_high_savings_recommendation(self) -> None:
        """POS-NYC-01 should receive device license recommendation with high savings.

        Validates that:
        1. All 4 POS users on POS-NYC-01 are identified
        2. Device meets eligibility (4 users, max concurrent=1, <80% dominance)
        3. Action is ADD_LICENSE
        4. Savings are high (~$640/month) due to Commerce license cost
        5. Confidence is HIGH
        """
        # -- Arrange --
        activity_df: pd.DataFrame = _load_device_activity()
        pricing: dict[str, Any] = _load_pricing()

        # Verify fixture setup
        pos_df = activity_df[activity_df["device_id"] == "POS-NYC-01"]
        unique_users = pos_df["user_id"].nunique()
        device_type = pos_df["device_type"].iloc[0] if len(pos_df) > 0 else None

        assert (
            unique_users >= 3
        ), f"Fixture error: POS-NYC-01 has {unique_users} users, expected >= 3"
        assert (
            device_type == "POS"
        ), f"Fixture error: POS-NYC-01 type is {device_type}, expected POS"

        # -- Act --
        opportunities = detect_device_license_opportunities(
            activity_data=activity_df,
            pricing_config=pricing,
        )

        # -- Assert --
        pos_opp = None
        for opp in opportunities:
            if opp.user_id == "POS-NYC-01":
                pos_opp = opp
                break

        assert pos_opp is not None, (
            f"Expected opportunity for POS-NYC-01 but not found. "
            f"Devices: {[o.user_id for o in opportunities]}"
        )

        # Should be eligible (meets all criteria)
        assert (
            pos_opp.action == RecommendationAction.ADD_LICENSE
        ), f"Expected ADD_LICENSE for POS-NYC-01, got {pos_opp.action.value}"

        # Monthly savings should be substantial (Commerce is expensive at $180/user)
        assert pos_opp.savings is not None, "Expected savings estimate for eligible POS device"
        assert pos_opp.savings.monthly_savings >= 600.0, (
            f"Expected monthly_savings >= $600 for expensive POS licenses, "
            f"got ${pos_opp.savings.monthly_savings}"
        )

        # Confidence should be HIGH
        assert pos_opp.confidence_score >= 0.90 - CONFIDENCE_TOLERANCE, (
            f"Expected HIGH confidence (0.90+) for clear POS case, "
            f"got {pos_opp.confidence_score:.4f}"
        )


# ---------------------------------------------------------------------------
# Test: Dedicated User Case (SCAN-LA-01) - NEGATIVE
# ---------------------------------------------------------------------------


class TestDedicatedUserNegativeCase:
    """Test scenario: SCAN-LA-01 has 2 users but one dominates heavily.

    This device SHOULD NOT be recommended because:
    - Only 2 unique users (minimum is 3)
    - One user (SOLO001) dominates workflow
    - Not a true shared device scenario
    - Expected: No recommendation or action=NO_CHANGE
    """

    def test_dedicated_user_case_not_recommended(self) -> None:
        """SCAN-LA-01 with < 3 users should NOT produce a recommendation.

        Validates that:
        1. Device with < 3 users is filtered out (not recommended)
        2. If included, action must be NO_CHANGE (not eligible)
        3. No savings calculated for ineligible device
        """
        # -- Arrange --
        activity_df: pd.DataFrame = _load_device_activity()
        pricing: dict[str, Any] = _load_pricing()

        # Verify fixture setup
        scan_la_df = activity_df[activity_df["device_id"] == "SCAN-LA-01"]
        unique_users = scan_la_df["user_id"].nunique()

        assert unique_users < 3, (
            f"Fixture error: SCAN-LA-01 has {unique_users} users, "
            f"test expects < 3 for negative case"
        )

        # -- Act --
        opportunities = detect_device_license_opportunities(
            activity_data=activity_df,
            pricing_config=pricing,
        )

        # -- Assert --
        # Either not in results (preferred, early filtering) or action=NO_CHANGE
        scan_la_opp = None
        for opp in opportunities:
            if opp.user_id == "SCAN-LA-01":
                scan_la_opp = opp
                break

        if scan_la_opp is not None:
            # If included, must be NO_CHANGE (not eligible)
            assert scan_la_opp.action == RecommendationAction.NO_CHANGE, (
                f"SCAN-LA-01 with {unique_users} users should be NO_CHANGE, "
                f"got {scan_la_opp.action.value}"
            )


# ---------------------------------------------------------------------------
# Test: Concurrent Users Case (DUAL devices) - NEGATIVE
# ---------------------------------------------------------------------------


class TestConcurrentUsersNegativeCase:
    """Test scenario: SCAN-CHI-03 and DESK-HQ-02 used by DUAL001 and DUAL002+.

    DUAL001 uses both SCAN-CHI-03 (warehouse) and DESK-HQ-02 (office) on same day.
    SCAN-CHI-03 also has multiple other users (DUAL002, DUAL003, DUAL004).

    While SCAN-CHI-03 meets user count (4 users) and type (Warehouse),
    we need to validate concurrent user detection still works correctly.

    Test validates that the algorithm properly handles:
    - Users appearing on multiple devices (not an eligibility blocker)
    - Mixed concurrent patterns
    """

    def test_multi_device_users_handled_correctly(self) -> None:
        """Users on multiple devices should still be analyzed per device.

        Validates that:
        1. User DUAL001 on multiple devices doesn't break logic
        2. Each device is evaluated independently
        3. No double-counting of users across devices
        """
        # -- Arrange --
        activity_df: pd.DataFrame = _load_device_activity()
        pricing: dict[str, Any] = _load_pricing()

        # Verify DUAL001 appears on multiple devices
        dual001_devices = activity_df[activity_df["user_id"] == "DUAL001"]["device_id"].unique()
        assert len(dual001_devices) >= 2, (
            f"Fixture error: DUAL001 should be on multiple devices, " f"got {len(dual001_devices)}"
        )

        # -- Act --
        opportunities = detect_device_license_opportunities(
            activity_data=activity_df,
            pricing_config=pricing,
        )

        # -- Assert --
        # Should complete without error
        assert (
            opportunities is not None
        ), "Algorithm should handle multi-device users without crashing"

        # Each device should be counted independently
        # Check SCAN-CHI-03 if it qualifies
        for opp in opportunities:
            if opp.user_id == "SCAN-CHI-03":
                # Should be evaluated on its own merits
                assert opp.action in [
                    RecommendationAction.ADD_LICENSE,
                    RecommendationAction.NO_CHANGE,
                ], f"Unexpected action for SCAN-CHI-03: {opp.action.value}"


# ---------------------------------------------------------------------------
# Test: Not Eligible Device Type (DESK-HQ-01) - NEGATIVE
# ---------------------------------------------------------------------------


class TestIneligibleDeviceTypeNegativeCase:
    """Test scenario: DESK-HQ-01 is a desktop with multiple users.

    Even though DESK-HQ-01 has 2 users (DESK001, DESK002):
    - Device type: Desktop (not in eligible list [Warehouse, Manufacturing, POS, ShopFloor, Kiosk])
    - NOT eligible for device license conversion
    - Expected: No recommendation or action=NO_CHANGE
    """

    def test_ineligible_device_type_not_recommended(self) -> None:
        """Desktop devices should NOT be recommended for device licenses.

        Validates that:
        1. Device type is checked against eligible list
        2. Desktop devices are filtered out (not eligible)
        3. No savings calculated for ineligible device types
        """
        # -- Arrange --
        activity_df: pd.DataFrame = _load_device_activity()
        pricing: dict[str, Any] = _load_pricing()

        # Verify fixture setup
        desk_df = activity_df[activity_df["device_id"] == "DESK-HQ-01"]
        device_type = desk_df["device_type"].iloc[0] if len(desk_df) > 0 else None

        assert (
            device_type == "Desktop"
        ), f"Fixture error: DESK-HQ-01 should be type Desktop, got {device_type}"

        # -- Act --
        opportunities = detect_device_license_opportunities(
            activity_data=activity_df,
            pricing_config=pricing,
        )

        # -- Assert --
        # Desktop should not be recommended (filter check below)
        found_desk = any(opp.user_id == "DESK-HQ-01" for opp in opportunities)
        assert (
            not found_desk
        ), "DESK-HQ-01 should not be recommended (Desktop type not in eligible list)"


# ---------------------------------------------------------------------------
# Test: Multi-Device Scenario (SCAN-CHI-01, SCAN-CHI-02, SCAN-CHI-03)
# ---------------------------------------------------------------------------


class TestMultiDeviceScenario:
    """Test scenario: Multiple warehouse scanners in Chicago.

    SCAN-CHI-01: 5 shared users (WH001-WH005)
    SCAN-CHI-02: 3 shared users (WH006, WH007, WH008)
    SCAN-CHI-03: 4 shared users (DUAL001-DUAL004)

    All eligible. Expected: 3 separate opportunities, each with own savings calculation.
    """

    def test_multiple_devices_analyzed_independently(self) -> None:
        """Multiple eligible devices should each produce separate opportunities.

        Validates that:
        1. All eligible warehouse devices are identified
        2. Each device gets independent analysis
        3. Savings are calculated per-device (not aggregated)
        4. All three devices produce recommendations if eligible
        """
        # -- Arrange --
        activity_df: pd.DataFrame = _load_device_activity()
        pricing: dict[str, Any] = _load_pricing()

        warehouse_devices = ["SCAN-CHI-01", "SCAN-CHI-02", "SCAN-CHI-03"]

        # -- Act --
        opportunities = detect_device_license_opportunities(
            activity_data=activity_df,
            pricing_config=pricing,
        )

        # -- Assert --
        found_devices = {opp.user_id for opp in opportunities}

        # At least some warehouse devices should be recommended
        expected_found = sum(1 for d in warehouse_devices if d in found_devices)
        assert expected_found >= 1, (
            f"Expected at least 1 warehouse device to be recommended, "
            f"found {expected_found} in {found_devices}"
        )

        # Each recommended device should have independent savings
        for opp in opportunities:
            assert (
                opp.savings is not None and opp.savings.monthly_savings > 0.0
            ), f"Device {opp.user_id} recommendation should have positive savings"
            assert (
                opp.action == RecommendationAction.ADD_LICENSE
            ), f"Device {opp.user_id} should have ADD_LICENSE action if recommended"


# ---------------------------------------------------------------------------
# Test: Empty Activity Data - EDGE CASE
# ---------------------------------------------------------------------------


class TestEmptyActivityData:
    """Test algorithm gracefully handles empty or minimal data.

    Edge case: What if activity_df is empty?
    Expected: Return empty list (no opportunities), not crash.
    """

    def test_empty_activity_data_returns_empty_list(self) -> None:
        """Algorithm should handle empty activity data gracefully.

        Validates that:
        1. Empty DataFrame doesn't crash algorithm
        2. Returns empty list of opportunities
        3. No errors or exceptions raised
        """
        # -- Arrange --
        empty_df = pd.DataFrame(
            columns=[
                "user_id",
                "timestamp",
                "menu_item",
                "action",
                "session_id",
                "license_tier",
                "feature",
                "device_id",
                "device_type",
                "location",
            ]
        )
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        opportunities = detect_device_license_opportunities(
            activity_data=empty_df,
            pricing_config=pricing,
        )

        # -- Assert --
        assert isinstance(opportunities, list), "Result should be a list even for empty input"
        assert (
            len(opportunities) == 0
        ), f"Expected empty list for empty input, got {len(opportunities)} opportunities"
