"""Tests for Algorithm 7.1: License Utilization Trend Analyzer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_7_1_license_utilization_trend.py is implemented.

Specification: Requirements/08-Algorithm-Review-Summary.md
(Algorithm 7.1: License Utilization Trend Analyzer, Phase 2, Low complexity).

Algorithm 7.1 analyzes license utilization trends over time, providing visibility
into how efficiently licenses are being used across the organization:
  - Track active users vs. total licensed users over time (utilization rate)
  - Detect under-utilized license pools (e.g., 200 licenses purchased, 120 active)
  - Identify license types with declining utilization trends
  - Identify license types with growing utilization approaching capacity
  - Generate utilization reports per license type
  - Calculate waste (unused licenses * cost)
  - Detect sudden utilization drops (potential for license reduction)
  - Support configurable analysis window (default 6 months)

Key behaviors:
  - Utilization rate = active_users / total_licensed_users * 100
  - Under-utilized: utilization < 70% (configurable)
  - Near-capacity: utilization > 90% (configurable)
  - Declining trend: utilization dropping consistently over 3+ months
  - Growing trend: utilization increasing consistently over 3+ months
  - Waste calculation: (total - active) * price_per_license
  - Empty input: zero results, no errors

Note: This algorithm differs from Algorithm 5.1 (License Cost Trend Analysis)
which focuses on cost and user count trends. Algorithm 7.1 focuses specifically
on utilization efficiency (ratio of active to total licensed users).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_7_1_license_utilization_trend import (
    LicenseUtilization,
    LicenseUtilizationAnalysis,
    analyze_license_utilization,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"
PERCENTAGE_TOLERANCE: float = 0.1
MONETARY_TOLERANCE: float = 0.01

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON."""
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_license_inventory(
    records: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic license inventory DataFrame.

    Args:
        records: List of dicts with keys:
            month (YYYY-MM), license_type, total_licenses, active_users.
    """
    rows: list[dict[str, Any]] = []
    for rec in records:
        rows.append(
            {
                "month": rec["month"],
                "license_type": rec["license_type"],
                "total_licenses": rec["total_licenses"],
                "active_users": rec["active_users"],
            }
        )
    return pd.DataFrame(rows)


def _build_monthly_series(
    license_type: str,
    total_licenses: int,
    active_users_by_month: list[tuple[str, int]],
) -> list[dict[str, Any]]:
    """Build a monthly series for a single license type.

    Args:
        license_type: License type name.
        total_licenses: Total purchased licenses (constant).
        active_users_by_month: List of (month, active_users) tuples.
    """
    return [
        {
            "month": month,
            "license_type": license_type,
            "total_licenses": total_licenses,
            "active_users": active,
        }
        for month, active in active_users_by_month
    ]


# ---------------------------------------------------------------------------
# Test: Under-Utilized License Pool
# ---------------------------------------------------------------------------


class TestUnderUtilizedLicensePool:
    """Test scenario: License pool with <70% utilization.

    200 Finance licenses purchased, only 120 active = 60% utilization.
    """

    def test_under_utilized_detected(self) -> None:
        """License pool below 70% utilization should be flagged."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series(
                "Finance",
                200,
                [
                    ("2025-08", 125),
                    ("2025-09", 122),
                    ("2025-10", 120),
                    ("2025-11", 118),
                    ("2025-12", 120),
                    ("2026-01", 120),
                ],
            )
        )
        pricing = _load_pricing()

        # -- Act --
        result: LicenseUtilizationAnalysis = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.utilizations) >= 1
        finance = next(
            (u for u in result.utilizations if u.license_type == "Finance"),
            None,
        )
        assert finance is not None
        assert finance.current_utilization_percent < 70.0
        assert finance.status == "UNDER_UTILIZED"

    def test_waste_amount_calculated(self) -> None:
        """Waste should equal (total - active) * price."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series(
                "Finance",
                200,
                [("2026-01", 120)],
            )
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        finance = next(
            (u for u in result.utilizations if u.license_type == "Finance"),
            None,
        )
        assert finance is not None
        # 80 unused * $180/month = $14,400/month
        expected_waste = (200 - 120) * 180.0
        assert abs(finance.monthly_waste - expected_waste) < MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test: Near-Capacity License Pool
# ---------------------------------------------------------------------------


class TestNearCapacityLicensePool:
    """Test scenario: License pool approaching capacity (>90% utilization).

    100 SCM licenses, 95 active = 95% utilization.
    """

    def test_near_capacity_detected(self) -> None:
        """License pool above 90% utilization should be flagged."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series(
                "SCM",
                100,
                [
                    ("2025-08", 88),
                    ("2025-09", 90),
                    ("2025-10", 92),
                    ("2025-11", 93),
                    ("2025-12", 94),
                    ("2026-01", 95),
                ],
            )
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        scm = next(
            (u for u in result.utilizations if u.license_type == "SCM"), None
        )
        assert scm is not None
        assert scm.current_utilization_percent > 90.0
        assert scm.status == "NEAR_CAPACITY"


# ---------------------------------------------------------------------------
# Test: Healthy Utilization
# ---------------------------------------------------------------------------


class TestHealthyUtilization:
    """Test scenario: License pool with 70-90% utilization (healthy).

    50 Commerce licenses, 40 active = 80% utilization.
    """

    def test_healthy_utilization_status(self) -> None:
        """Utilization between 70-90% should be HEALTHY."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series(
                "Commerce",
                50,
                [("2026-01", 40)],
            )
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        commerce = next(
            (u for u in result.utilizations if u.license_type == "Commerce"),
            None,
        )
        assert commerce is not None
        assert abs(commerce.current_utilization_percent - 80.0) < PERCENTAGE_TOLERANCE
        assert commerce.status == "HEALTHY"


# ---------------------------------------------------------------------------
# Test: Declining Utilization Trend
# ---------------------------------------------------------------------------


class TestDecliningTrend:
    """Test scenario: Utilization dropping consistently over 3+ months.

    Indicates potential for license reduction.
    """

    def test_declining_trend_detected(self) -> None:
        """Consistently declining utilization should flag DECLINING trend."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series(
                "Finance",
                200,
                [
                    ("2025-08", 180),  # 90%
                    ("2025-09", 170),  # 85%
                    ("2025-10", 155),  # 77.5%
                    ("2025-11", 140),  # 70%
                    ("2025-12", 130),  # 65%
                    ("2026-01", 120),  # 60%
                ],
            )
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        finance = next(
            (u for u in result.utilizations if u.license_type == "Finance"),
            None,
        )
        assert finance is not None
        assert finance.trend == "DECLINING"


# ---------------------------------------------------------------------------
# Test: Growing Utilization Trend
# ---------------------------------------------------------------------------


class TestGrowingTrend:
    """Test scenario: Utilization increasing consistently over 3+ months.

    May need additional license procurement.
    """

    def test_growing_trend_detected(self) -> None:
        """Consistently growing utilization should flag GROWING trend."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series(
                "SCM",
                100,
                [
                    ("2025-08", 60),  # 60%
                    ("2025-09", 68),  # 68%
                    ("2025-10", 75),  # 75%
                    ("2025-11", 82),  # 82%
                    ("2025-12", 88),  # 88%
                    ("2026-01", 93),  # 93%
                ],
            )
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        scm = next(
            (u for u in result.utilizations if u.license_type == "SCM"), None
        )
        assert scm is not None
        assert scm.trend == "GROWING"


# ---------------------------------------------------------------------------
# Test: Stable Utilization Trend
# ---------------------------------------------------------------------------


class TestStableTrend:
    """Test scenario: Utilization relatively stable over time."""

    def test_stable_trend_detected(self) -> None:
        """Flat utilization should flag STABLE trend."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series(
                "Commerce",
                50,
                [
                    ("2025-08", 40),
                    ("2025-09", 39),
                    ("2025-10", 41),
                    ("2025-11", 40),
                    ("2025-12", 40),
                    ("2026-01", 41),
                ],
            )
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        commerce = next(
            (u for u in result.utilizations if u.license_type == "Commerce"),
            None,
        )
        assert commerce is not None
        assert commerce.trend == "STABLE"


# ---------------------------------------------------------------------------
# Test: Multiple License Types
# ---------------------------------------------------------------------------


class TestMultipleLicenseTypes:
    """Test scenario: Analyze utilization across all license types."""

    def test_all_license_types_analyzed(self) -> None:
        """Each license type should have its own utilization record."""
        # -- Arrange --
        records = _build_monthly_series(
            "Finance", 200, [("2026-01", 150)]
        ) + _build_monthly_series(
            "SCM", 100, [("2026-01", 95)]
        ) + _build_monthly_series(
            "Team Members", 500, [("2026-01", 250)]
        )
        inventory = _build_license_inventory(records)
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        types_analyzed = {u.license_type for u in result.utilizations}
        assert "Finance" in types_analyzed
        assert "SCM" in types_analyzed
        assert "Team Members" in types_analyzed


# ---------------------------------------------------------------------------
# Test: Configurable Thresholds
# ---------------------------------------------------------------------------


class TestConfigurableThresholds:
    """Test scenario: Custom under_utilized and near_capacity thresholds."""

    def test_custom_under_utilized_threshold(self) -> None:
        """Custom threshold 80% should flag 75% utilization."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series("Finance", 100, [("2026-01", 75)])
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
            under_utilized_threshold=80.0,
        )

        # -- Assert --
        finance = next(
            (u for u in result.utilizations if u.license_type == "Finance"),
            None,
        )
        assert finance is not None
        assert finance.status == "UNDER_UTILIZED"

    def test_custom_near_capacity_threshold(self) -> None:
        """Custom capacity threshold 85% should flag 87% utilization."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series("SCM", 100, [("2026-01", 87)])
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
            near_capacity_threshold=85.0,
        )

        # -- Assert --
        scm = next(
            (u for u in result.utilizations if u.license_type == "SCM"), None
        )
        assert scm is not None
        assert scm.status == "NEAR_CAPACITY"


# ---------------------------------------------------------------------------
# Test: Aggregate Waste Summary
# ---------------------------------------------------------------------------


class TestAggregateWasteSummary:
    """Test scenario: Total waste across all license types."""

    def test_total_monthly_waste(self) -> None:
        """Result should sum monthly waste across all license types."""
        # -- Arrange --
        records = _build_monthly_series(
            "Finance", 200, [("2026-01", 120)]
        ) + _build_monthly_series(
            "SCM", 100, [("2026-01", 60)]
        )
        inventory = _build_license_inventory(records)
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        # Finance waste: 80 * 180 = 14400
        # SCM waste: 40 * 180 = 7200
        # Total: 21600
        assert result.total_monthly_waste > 0
        assert result.total_annual_waste > 0


# ---------------------------------------------------------------------------
# Test: Empty Input
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input DataFrame."""

    def test_empty_inventory_returns_empty(self) -> None:
        """Empty inventory should produce zero results without errors."""
        # -- Arrange --
        inventory = pd.DataFrame(
            columns=["month", "license_type", "total_licenses", "active_users"]
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(result.utilizations) == 0
        assert result.total_monthly_waste == 0


# ---------------------------------------------------------------------------
# Test: Utilization Rate Calculation
# ---------------------------------------------------------------------------


class TestUtilizationRateCalculation:
    """Test scenario: Verify utilization percentage is correct."""

    def test_utilization_percentage_correct(self) -> None:
        """Utilization = active_users / total_licenses * 100."""
        # -- Arrange --
        inventory = _build_license_inventory(
            _build_monthly_series("Finance", 200, [("2026-01", 150)])
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        finance = next(
            (u for u in result.utilizations if u.license_type == "Finance"),
            None,
        )
        assert finance is not None
        assert abs(finance.current_utilization_percent - 75.0) < PERCENTAGE_TOLERANCE


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '7.1'."""

    def test_algorithm_id_is_7_1(self) -> None:
        """LicenseUtilizationAnalysis should carry algorithm_id '7.1'."""
        # -- Arrange --
        inventory = pd.DataFrame(
            columns=["month", "license_type", "total_licenses", "active_users"]
        )
        pricing = _load_pricing()

        # -- Act --
        result = analyze_license_utilization(
            license_inventory=inventory,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.algorithm_id == "7.1"
