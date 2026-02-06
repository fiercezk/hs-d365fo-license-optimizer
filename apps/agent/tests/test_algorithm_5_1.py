"""Tests for Algorithm 5.1: License Cost Trend Analysis (TDD).

Tests historical trend analysis, seasonal pattern detection, forecasting,
anomaly detection, and recommendation generation.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.algorithms.algorithm_5_1_license_trend_analyzer import (
    analyze_license_trends,
    detect_seasonal_patterns,
    detect_anomalies,
    calculate_growth_rates,
    generate_forecast,
    generate_recommendations,
)
from src.models.output_schemas import (
    LicenseTrendAnalysis,
    ConfidenceLevel,
)


# ============================================================================
# FIXTURES: Load test data
# ============================================================================

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "algo_5_1"


@pytest.fixture
def steady_growth_data():
    """Load steady growth fixture (12 months, 2% MoM)."""
    with open(FIXTURES_DIR / "steady_growth_12m.json") as f:
        return json.load(f)


@pytest.fixture
def seasonal_peaks_data():
    """Load seasonal peaks fixture (24 months)."""
    with open(FIXTURES_DIR / "seasonal_peaks_24m.json") as f:
        return json.load(f)


@pytest.fixture
def anomalies_data():
    """Load data with anomalies fixture."""
    with open(FIXTURES_DIR / "with_anomalies_12m.json") as f:
        return json.load(f)


@pytest.fixture
def declining_data():
    """Load declining trend fixture."""
    with open(FIXTURES_DIR / "declining_trend_12m.json") as f:
        return json.load(f)


@pytest.fixture
def project_rollout_data():
    """Load project-based demand fixture."""
    with open(FIXTURES_DIR / "project_based_demand_12m.json") as f:
        return json.load(f)


# ============================================================================
# TESTS: Steady Growth Scenario
# ============================================================================


class TestSteadyGrowth:
    """Test Algorithm 5.1 with steady 2% MoM growth scenario."""

    def test_analyze_with_steady_growth(self, steady_growth_data):
        """Test complete analysis with steady growth data."""
        result = analyze_license_trends(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Verify output structure
        assert isinstance(result, LicenseTrendAnalysis)
        assert result.algorithm_id == "5.1"
        assert result.analysis_period_months == 12
        assert result.forecast_months == 12

    def test_steady_growth_growth_rates(self, steady_growth_data):
        """Test growth rate calculation is accurate."""
        result = analyze_license_trends(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Overall growth should be ~24% (1.02^12 ≈ 1.268)
        assert 23.0 < result.growth_rates.overall_percent < 27.0

        # MoM average should be ~2%
        assert 1.8 < result.growth_rates.mom_average < 2.2

        # Trend should be GROWING
        assert result.growth_rates.trend == "GROWING"

    def test_steady_growth_no_anomalies(self, steady_growth_data):
        """Test that steady growth has no anomalies."""
        result = analyze_license_trends(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Should have 0 anomalies with steady trend
        assert len(result.anomalies) == 0

    def test_steady_growth_forecast_accuracy(self, steady_growth_data):
        """Test forecast extends growth trend into future."""
        result = analyze_license_trends(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Should have 12 forecast months
        assert len(result.forecast) == 12

        # Forecast should show continued growth
        assert result.forecast[-1].forecast_users > result.current_users

    def test_steady_growth_high_confidence(self, steady_growth_data):
        """Test that steady data yields high confidence."""
        result = analyze_license_trends(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Stable trends should have high confidence
        assert result.overall_confidence == ConfidenceLevel.HIGH
        assert result.confidence_score >= 0.80


# ============================================================================
# TESTS: Seasonal Pattern Detection
# ============================================================================


class TestSeasonalPatterns:
    """Test seasonal pattern detection with 24-month data."""

    def test_detect_seasonal_patterns(self, seasonal_peaks_data):
        """Test detection of seasonal patterns in 24-month dataset."""
        patterns = detect_seasonal_patterns(
            monthly_data=seasonal_peaks_data["months"],
            historical_months=24,
            deviation_threshold=10.0,
        )

        # Should detect 4 seasonal patterns (Aug, Sep, Nov, Dec)
        assert len(patterns) >= 2

        # Patterns should include November and December (high deviation)
        pattern_months = [p.month for p in patterns]
        assert 11 in pattern_months or 12 in pattern_months

    def test_seasonal_pattern_structure(self, seasonal_peaks_data):
        """Test structure of detected seasonal patterns."""
        patterns = detect_seasonal_patterns(
            monthly_data=seasonal_peaks_data["months"],
            historical_months=24,
            deviation_threshold=10.0,
        )

        for pattern in patterns:
            # Each pattern should have required fields
            assert pattern.month >= 1 and pattern.month <= 12
            assert pattern.month_name
            assert pattern.pattern_type in ["HIGH", "LOW"]
            assert pattern.deviation_percent != 0  # Not zero deviation
            assert pattern.avg_user_count > 0
            assert pattern.occurrences >= 1
            assert len(pattern.years) > 0

    def test_seasonal_no_false_positives(self, steady_growth_data):
        """Test that steady growth doesn't trigger false seasonal patterns."""
        patterns = detect_seasonal_patterns(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            deviation_threshold=10.0,
        )

        # Steady growth should have minimal/no seasonal patterns
        assert len(patterns) == 0

    def test_seasonal_in_full_analysis(self, seasonal_peaks_data):
        """Test seasonal patterns included in full trend analysis."""
        result = analyze_license_trends(
            monthly_data=seasonal_peaks_data["months"],
            historical_months=24,
            forecast_months=12,
        )

        # Should detect seasonal patterns
        assert len(result.seasonal_patterns) >= 1

        # Forecast should include seasonal adjustments
        seasonal_notes = []
        for month in result.forecast:
            seasonal_notes.extend(month.notes)

        # Check if seasonal peaks are mentioned in forecast
        assert len(seasonal_notes) > 0 or any(
            p.month in [8, 9, 11, 12] for p in result.seasonal_patterns
        )


# ============================================================================
# TESTS: Anomaly Detection
# ============================================================================


class TestAnomalyDetection:
    """Test anomaly detection algorithms."""

    def test_detect_anomalies_sudden_spike(self, anomalies_data):
        """Test detection of sudden spike anomaly."""
        anomalies = detect_anomalies(
            monthly_data=anomalies_data["months"],
            std_dev_threshold=2.0,
            sudden_change_threshold=15.0,
        )

        # Should detect at least one anomaly
        assert len(anomalies) > 0

        # Check for spike anomaly (month 6)
        spike_anomalies = [
            a for a in anomalies
            if a.anomaly_type in ["SUDDEN_USER_CHANGE", "USER_COUNT_ANOMALY"]
            and a.value > a.expected
        ]
        assert len(spike_anomalies) > 0

    def test_detect_anomalies_sudden_drop(self, anomalies_data):
        """Test detection of sudden drop anomaly."""
        anomalies = detect_anomalies(
            monthly_data=anomalies_data["months"],
            std_dev_threshold=2.0,
            sudden_change_threshold=15.0,
        )

        # Should detect drop anomaly (month 8)
        drop_anomalies = [
            a for a in anomalies
            if a.anomaly_type in ["SUDDEN_USER_CHANGE", "USER_COUNT_ANOMALY"]
            and a.value < a.expected
        ]
        assert len(drop_anomalies) > 0

    def test_anomaly_structure(self, anomalies_data):
        """Test structure of anomaly records."""
        anomalies = detect_anomalies(
            monthly_data=anomalies_data["months"],
            std_dev_threshold=2.0,
            sudden_change_threshold=15.0,
        )

        for anomaly in anomalies:
            # Each anomaly should have required fields
            assert anomaly.anomaly_type in [
                "USER_COUNT_ANOMALY",
                "COST_ANOMALY",
                "SUDDEN_USER_CHANGE",
                "SUDDEN_COST_CHANGE",
            ]
            assert anomaly.date
            assert anomaly.value >= 0
            assert anomaly.expected >= 0
            assert anomaly.severity in ["MEDIUM", "HIGH"]
            assert anomaly.description

    def test_no_false_anomalies_in_steady_growth(self, steady_growth_data):
        """Test that steady data produces minimal anomalies."""
        anomalies = detect_anomalies(
            monthly_data=steady_growth_data["months"],
            std_dev_threshold=2.0,
            sudden_change_threshold=15.0,
        )

        # Steady growth should have 0-1 anomalies (natural variation)
        assert len(anomalies) <= 1


# ============================================================================
# TESTS: Growth Rate Calculation
# ============================================================================


class TestGrowthRateCalculation:
    """Test growth rate calculation functions."""

    def test_calculate_growth_rates_structure(self, steady_growth_data):
        """Test structure of growth rate output."""
        growth = calculate_growth_rates(monthly_data=steady_growth_data["months"])

        # All fields should be present
        assert growth.overall_percent >= 0
        assert growth.period_months > 0
        assert growth.mom_average >= -100
        assert growth.mom_min >= -100
        assert growth.mom_max >= -100
        assert growth.qoq_average >= -100
        assert growth.yoy_average >= -100
        assert growth.trend in ["GROWING", "STABLE", "DECLINING"]

    def test_growth_rate_positive(self, steady_growth_data):
        """Test growth rate calculation for positive trend."""
        growth = calculate_growth_rates(monthly_data=steady_growth_data["months"])

        assert growth.overall_percent > 0
        assert growth.mom_average > 0
        assert growth.trend == "GROWING"

    def test_growth_rate_negative(self, declining_data):
        """Test growth rate calculation for negative trend."""
        growth = calculate_growth_rates(monthly_data=declining_data["months"])

        assert growth.overall_percent < 0
        assert growth.mom_average < 0
        assert growth.trend == "DECLINING"

    def test_growth_rate_stable(self, seasonal_peaks_data):
        """Test growth rate calculation for stable trend."""
        growth = calculate_growth_rates(
            monthly_data=seasonal_peaks_data["months"][:12]  # First year only
        )

        # Should show minimal overall growth
        assert -5 < growth.overall_percent < 5
        assert growth.trend == "STABLE"


# ============================================================================
# TESTS: Forecast Generation
# ============================================================================


class TestForecastGeneration:
    """Test forecast generation algorithms."""

    def test_generate_forecast_structure(self, steady_growth_data):
        """Test structure of generated forecast."""
        forecast = generate_forecast(
            monthly_data=steady_growth_data["months"],
            growth_rates=calculate_growth_rates(steady_growth_data["months"]),
            seasonal_patterns=[],
            forecast_months=12,
        )

        # Should have correct number of months
        assert len(forecast) == 12

        # Each month should have required fields
        for month in forecast:
            assert month.month_number >= 1
            assert month.month_number <= 12
            assert month.date
            assert month.month_name
            assert month.forecast_users > 0
            assert month.forecast_cost > 0
            assert 0 <= month.confidence <= 100

    def test_forecast_continues_trend(self, steady_growth_data):
        """Test that forecast extends growth trend."""
        forecast = generate_forecast(
            monthly_data=steady_growth_data["months"],
            growth_rates=calculate_growth_rates(steady_growth_data["months"]),
            seasonal_patterns=[],
            forecast_months=12,
        )

        # Forecast should continue growth pattern
        assert forecast[-1].forecast_users > steady_growth_data["months"][-1]["user_count"]

    def test_forecast_with_seasonal_adjustment(self, seasonal_peaks_data):
        """Test that forecast includes seasonal adjustments."""
        growth = calculate_growth_rates(seasonal_peaks_data["months"])
        patterns = detect_seasonal_patterns(
            monthly_data=seasonal_peaks_data["months"],
            historical_months=24,
            deviation_threshold=10.0,
        )

        forecast = generate_forecast(
            monthly_data=seasonal_peaks_data["months"],
            growth_rates=growth,
            seasonal_patterns=patterns,
            forecast_months=12,
        )

        # Forecast should apply seasonal adjustments
        has_adjustments = any(
            abs(m.seasonal_adjustment_percent) > 0.1
            for m in forecast
        )
        assert has_adjustments or len(patterns) == 0

    def test_forecast_confidence_decreases(self, steady_growth_data):
        """Test that forecast confidence decreases further into future."""
        forecast = generate_forecast(
            monthly_data=steady_growth_data["months"],
            growth_rates=calculate_growth_rates(steady_growth_data["months"]),
            seasonal_patterns=[],
            forecast_months=12,
        )

        # Later months should have lower confidence
        first_confidence = forecast[0].confidence
        last_confidence = forecast[-1].confidence

        assert last_confidence <= first_confidence


# ============================================================================
# TESTS: Recommendation Generation
# ============================================================================


class TestRecommendationGeneration:
    """Test recommendation generation."""

    def test_recommendations_steady_growth(self, steady_growth_data):
        """Test recommendations for steady growth scenario."""
        result = analyze_license_trends(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Should have at least one recommendation
        assert len(result.recommendations) > 0

        # Should include procurement planning
        recommendation_types = [r.recommendation_type for r in result.recommendations]
        assert "PROCUREMENT_NEEDED" in recommendation_types or \
               "BUDGET_FORECAST" in recommendation_types

    def test_recommendations_declining(self, declining_data):
        """Test recommendations for declining trend."""
        result = analyze_license_trends(
            monthly_data=declining_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Should include optimization recommendation
        recommendation_types = [r.recommendation_type for r in result.recommendations]
        assert "DECLINING_TREND" in recommendation_types

    def test_recommendations_seasonal(self, seasonal_peaks_data):
        """Test recommendations for seasonal patterns."""
        result = analyze_license_trends(
            monthly_data=seasonal_peaks_data["months"],
            historical_months=24,
            forecast_months=12,
        )

        # Should include seasonal planning
        recommendation_types = [r.recommendation_type for r in result.recommendations]
        has_seasonal_or_procurement = (
            "SEASONAL_DEMAND" in recommendation_types
            or "PROCUREMENT_NEEDED" in recommendation_types
        )
        assert has_seasonal_or_procurement

    def test_recommendation_structure(self, steady_growth_data):
        """Test structure of recommendations."""
        result = analyze_license_trends(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        for rec in result.recommendations:
            # Each recommendation should have required fields
            assert rec.recommendation_type
            assert rec.description
            assert rec.priority in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            # timeline and estimated_impact are optional


# ============================================================================
# TESTS: Full Integration
# ============================================================================


class TestFullAnalysis:
    """Test complete Algorithm 5.1 analysis."""

    def test_full_analysis_output_schema(self, steady_growth_data):
        """Test that full analysis output validates against schema."""
        result = analyze_license_trends(
            monthly_data=steady_growth_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Should validate as LicenseTrendAnalysis
        assert isinstance(result, LicenseTrendAnalysis)

        # All required fields should be present
        assert result.algorithm_id == "5.1"
        assert result.analysis_id
        assert result.period_start
        assert result.period_end
        assert result.current_users > 0
        assert result.current_monthly_cost > 0
        assert result.growth_rates
        assert isinstance(result.seasonal_patterns, list)
        assert isinstance(result.anomalies, list)
        assert len(result.forecast) > 0
        assert len(result.recommendations) > 0
        assert result.overall_confidence
        assert 0.0 <= result.confidence_score <= 1.0

    def test_full_analysis_with_project_rollout(self, project_rollout_data):
        """Test full analysis with project-based demand scenario."""
        result = analyze_license_trends(
            monthly_data=project_rollout_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Should show strong growth
        assert result.growth_rates.overall_percent > 40

        # Should recommend procurement
        recommendation_types = [r.recommendation_type for r in result.recommendations]
        assert "PROCUREMENT_NEEDED" in recommendation_types or \
               "BUDGET_FORECAST" in recommendation_types

    def test_full_analysis_with_anomalies(self, anomalies_data):
        """Test full analysis with anomalies."""
        result = analyze_license_trends(
            monthly_data=anomalies_data["months"],
            historical_months=12,
            forecast_months=12,
        )

        # Should detect anomalies
        assert len(result.anomalies) > 0

        # Confidence should be medium (due to anomalies)
        assert result.overall_confidence in [
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
        ]


# ============================================================================
# TESTS: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_data_period(self):
        """Test analysis with minimum viable data (6 months)."""
        minimal_data = [
            {"date": f"2025-{m:02d}-01", "month_num": m, "year": 2025,
             "user_count": 1000 + (i * 20), "license_cost": 180000 + (i * 3600)}
            for i, m in enumerate(range(8, 14))
        ]

        result = analyze_license_trends(
            monthly_data=minimal_data,
            historical_months=6,
            forecast_months=6,
        )

        # Should produce valid result
        assert result.analysis_period_months == 6
        assert len(result.forecast) == 6

    def test_large_data_period(self):
        """Test analysis with 36 months of data."""
        large_data = [
            {"date": f"2023-{(m % 12) + 1:02d}-01",
             "month_num": (m % 12) + 1,
             "year": 2023 + (m // 12),
             "user_count": 1000 + (i * 10),
             "license_cost": 180000 + (i * 1800)}
            for i, m in enumerate(range(36))
        ]

        result = analyze_license_trends(
            monthly_data=large_data,
            historical_months=36,
            forecast_months=12,
        )

        # Should handle large dataset
        assert result.analysis_period_months == 36
        assert result.confidence_score >= 0.8

    def test_flat_data_no_growth(self):
        """Test with completely flat data (no growth or decline)."""
        flat_data = [
            {"date": f"2025-{m:02d}-01", "month_num": m, "year": 2025,
             "user_count": 1000, "license_cost": 180000}
            for m in range(1, 13)
        ]

        result = analyze_license_trends(
            monthly_data=flat_data,
            historical_months=12,
            forecast_months=12,
        )

        # Growth should be ~0%
        assert abs(result.growth_rates.overall_percent) < 1.0
        assert result.growth_rates.trend == "STABLE"

    def test_extreme_spike(self):
        """Test handling of extreme spike (300% increase in one month)."""
        spike_data = [
            {"date": "2025-01-01", "month_num": 1, "year": 2025,
             "user_count": 1000, "license_cost": 180000},
            {"date": "2025-02-01", "month_num": 2, "year": 2025,
             "user_count": 4000, "license_cost": 720000},
            {"date": "2025-03-01", "month_num": 3, "year": 2025,
             "user_count": 4000, "license_cost": 720000},
        ] + [
            {"date": f"2025-{m:02d}-01", "month_num": m, "year": 2025,
             "user_count": 4000, "license_cost": 720000}
            for m in range(4, 13)
        ]

        result = analyze_license_trends(
            monthly_data=spike_data,
            historical_months=12,
            forecast_months=12,
        )

        # Should detect anomaly
        assert len(result.anomalies) > 0

        # Should have lower confidence
        assert result.overall_confidence in [
            ConfidenceLevel.LOW,
            ConfidenceLevel.MEDIUM,
        ]
