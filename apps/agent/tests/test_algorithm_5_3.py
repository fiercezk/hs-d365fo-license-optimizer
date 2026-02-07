"""Tests for Algorithm 5.3: Time-Based Access Analyzer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_5_3_time_based_access_analyzer.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md
(Algorithm 5.3: Time-Based Access Analyzer, referenced as MVP+, Low complexity).

Algorithm 5.3 detects after-hours and anomalous time-based access patterns:
  - Identify access outside business hours (configurable, default 6:00-18:00)
  - Detect weekend access
  - Flag high-risk actions performed after hours
  - Detect pattern changes (users who suddenly start working after hours)
  - Generate security alerts with severity levels
  - Support configurable business hours and timezone

Key behaviors:
  - Normal business-hours access should not generate alerts
  - After-hours access (before 6:00 or after 18:00) flagged
  - Weekend access flagged with higher severity
  - High-risk menu items (payments, journal posting) after hours = CRITICAL
  - Regular after-hours users who always work late = reduced severity
  - Configurable business_hours_start, business_hours_end, timezone
  - Support for company-specific holiday calendars
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_5_3_time_based_access_analyzer import (
    TimeBasedAccessAnalysis,
    analyze_time_based_access,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON."""
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_activity_with_timestamps(
    rows: list[tuple[str, str, str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic user activity with explicit timestamps.

    Args:
        rows: List of (user_id, timestamp, menu_item, action, license_tier, feature)
            tuples. Timestamp format: 'YYYY-MM-DD HH:MM:SS'.
    """
    records: list[dict[str, str]] = []
    for i, (uid, ts, menu_item, action, tier, feature) in enumerate(rows):
        records.append(
            {
                "user_id": uid,
                "timestamp": ts,
                "menu_item": menu_item,
                "action": action,
                "session_id": f"sess-{i:04d}",
                "license_tier": tier,
                "feature": feature,
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Normal Business Hours -- No Alerts
# ---------------------------------------------------------------------------


class TestNormalBusinessHoursNoAlerts:
    """Test scenario: All activity within 6:00-18:00 on weekdays.

    No alerts should be generated for standard business-hours activity.
    """

    def test_business_hours_no_alerts(self) -> None:
        """Activity during business hours should produce zero alerts."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_A", "2026-01-15 09:30:00", "GeneralJournal", "Write", "Finance", "GL"),
                ("USR_A", "2026-01-15 14:00:00", "BankRecon", "Read", "Finance", "Cash Mgmt"),
                ("USR_B", "2026-01-15 08:00:00", "PurchaseOrder", "Write", "SCM", "Procurement"),
                ("USR_B", "2026-01-15 17:00:00", "VendorList", "Read", "SCM", "AP"),
            ]
        )

        # -- Act --
        result: TimeBasedAccessAnalysis = analyze_time_based_access(
            user_activity=activity,
        )

        # -- Assert --
        assert len(result.alerts) == 0


class TestAfterHoursAccessDetected:
    """Test scenario: Access at 2:00 AM on a weekday.

    After-hours access should generate a security alert.
    """

    def test_late_night_access_flagged(self) -> None:
        """Access at 2:00 AM should produce an after-hours alert."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_LATE", "2026-01-15 02:00:00", "GeneralJournal", "Write", "Finance", "GL"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(user_activity=activity)

        # -- Assert --
        assert len(result.alerts) >= 1
        alert = result.alerts[0]
        assert alert.user_id == "USR_LATE"
        assert "after" in alert.alert_type.lower() or "hours" in alert.alert_type.lower()


class TestEarlyMorningAccessDetected:
    """Test scenario: Access at 4:30 AM -- before business hours start."""

    def test_early_morning_flagged(self) -> None:
        """Access at 4:30 AM should be flagged as after-hours."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_EARLY", "2026-01-15 04:30:00", "CustomerList", "Read", "Finance", "AR"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(user_activity=activity)

        # -- Assert --
        assert len(result.alerts) >= 1
        assert result.alerts[0].user_id == "USR_EARLY"


class TestWeekendAccessHigherSeverity:
    """Test scenario: Access on Saturday should have higher severity.

    Weekend access is more suspicious than weekday after-hours access.
    """

    def test_weekend_access_flagged(self) -> None:
        """Saturday access should produce a weekend-type alert."""
        # -- Arrange --
        # 2026-01-17 is a Saturday
        activity = _build_activity_with_timestamps(
            [
                ("USR_WKND", "2026-01-17 10:00:00", "GeneralJournal", "Write", "Finance", "GL"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(user_activity=activity)

        # -- Assert --
        assert len(result.alerts) >= 1
        alert = result.alerts[0]
        assert alert.user_id == "USR_WKND"
        assert "weekend" in alert.alert_type.lower() or alert.severity in ("HIGH", "CRITICAL")


class TestHighRiskActionAfterHoursCritical:
    """Test scenario: High-risk financial action performed after hours.

    Payment processing or journal posting at 3:00 AM should be CRITICAL.
    """

    def test_high_risk_after_hours_critical(self) -> None:
        """High-risk action after hours should produce CRITICAL alert."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_RISK", "2026-01-15 03:00:00", "VendorPayment", "Write", "Finance", "AP"),
            ]
        )
        high_risk_items = ["VendorPayment", "GeneralJournalPost", "BankReconciliation"]

        # -- Act --
        result = analyze_time_based_access(
            user_activity=activity,
            high_risk_menu_items=high_risk_items,
        )

        # -- Assert --
        assert len(result.alerts) >= 1
        critical_alerts = [a for a in result.alerts if a.severity == "CRITICAL"]
        assert len(critical_alerts) >= 1, (
            "High-risk action after hours should produce CRITICAL alert"
        )


class TestConfigurableBusinessHours:
    """Test scenario: Custom business hours 8:00-20:00.

    With extended business hours, access at 19:00 should not be flagged.
    """

    def test_custom_business_hours(self) -> None:
        """Access at 19:00 with business_hours_end=20 should not be flagged."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_LATE", "2026-01-15 19:00:00", "CustomerList", "Read", "Finance", "AR"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(
            user_activity=activity,
            business_hours_start=8,
            business_hours_end=20,
        )

        # -- Assert --
        # 19:00 is within 8:00-20:00, so no alerts
        assert len(result.alerts) == 0

    def test_access_outside_custom_hours_flagged(self) -> None:
        """Access at 21:00 with business_hours_end=20 should be flagged."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_LATE", "2026-01-15 21:00:00", "CustomerList", "Read", "Finance", "AR"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(
            user_activity=activity,
            business_hours_start=8,
            business_hours_end=20,
        )

        # -- Assert --
        assert len(result.alerts) >= 1


class TestMultipleUsersMultipleAlerts:
    """Test scenario: 3 users with various after-hours activities.

    Verify that alerts are generated per-user and per-incident.
    """

    def test_multiple_users_multiple_alerts(self) -> None:
        """Each after-hours incident should generate its own alert."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                # User A: 2 AM
                ("USR_A", "2026-01-15 02:00:00", "Form_A", "Read", "Finance", "GL"),
                # User B: Saturday
                ("USR_B", "2026-01-17 10:00:00", "Form_B", "Write", "SCM", "Procurement"),
                # User C: 11 PM
                ("USR_C", "2026-01-15 23:00:00", "Form_C", "Read", "Finance", "AR"),
                # User D: normal hours (no alert)
                ("USR_D", "2026-01-15 10:00:00", "Form_D", "Read", "Finance", "GL"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(user_activity=activity)

        # -- Assert --
        assert len(result.alerts) >= 3

        flagged_users = {a.user_id for a in result.alerts}
        assert "USR_A" in flagged_users
        assert "USR_B" in flagged_users
        assert "USR_C" in flagged_users
        assert "USR_D" not in flagged_users


class TestEmptyActivityData:
    """Test scenario: Empty activity DataFrame."""

    def test_empty_data_no_alerts(self) -> None:
        """Empty input should produce zero alerts without errors."""
        # -- Arrange --
        activity = pd.DataFrame(
            columns=[
                "user_id", "timestamp", "menu_item", "action",
                "session_id", "license_tier", "feature",
            ]
        )

        # -- Act --
        result = analyze_time_based_access(user_activity=activity)

        # -- Assert --
        assert len(result.alerts) == 0


class TestAlertSeverityLevels:
    """Test scenario: Verify severity hierarchy.

    - Weekday after-hours read: MEDIUM
    - Weekday after-hours write: HIGH
    - Weekend access: HIGH
    - High-risk action after hours: CRITICAL
    """

    def test_severity_hierarchy(self) -> None:
        """Different access patterns should produce appropriate severity levels."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                # Weekday after-hours read
                ("USR_MED", "2026-01-15 22:00:00", "CustomerList", "Read", "Finance", "AR"),
                # Weekday after-hours write
                ("USR_HIGH", "2026-01-15 22:00:00", "GeneralJournal", "Write", "Finance", "GL"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(user_activity=activity)

        # -- Assert --
        assert len(result.alerts) >= 2

        med_alert = next((a for a in result.alerts if a.user_id == "USR_MED"), None)
        high_alert = next((a for a in result.alerts if a.user_id == "USR_HIGH"), None)

        assert med_alert is not None
        assert high_alert is not None
        # Write operations after hours should have higher or equal severity
        severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        assert severity_order.get(high_alert.severity, 0) >= severity_order.get(
            med_alert.severity, 0
        ), "Write after-hours should have >= severity than read after-hours"


class TestSummaryStatistics:
    """Test scenario: Result should contain summary statistics.

    - Total operations analyzed
    - After-hours operation count
    - Weekend operation count
    - Unique users with after-hours access
    """

    def test_summary_stats_populated(self) -> None:
        """Summary should contain total, after-hours, and weekend counts."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_A", "2026-01-15 09:00:00", "Form_A", "Read", "Finance", "GL"),
                ("USR_A", "2026-01-15 23:00:00", "Form_B", "Write", "Finance", "GL"),
                ("USR_B", "2026-01-17 12:00:00", "Form_C", "Read", "SCM", "Procurement"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(user_activity=activity)

        # -- Assert --
        assert result.total_operations_analyzed == 3
        assert result.after_hours_operations >= 1
        assert result.weekend_operations >= 1
        assert result.unique_users_after_hours >= 1


class TestBoundaryExactlyAtBusinessHoursStart:
    """Test scenario: Access at exactly 6:00 AM (business hours start).

    Boundary test: access exactly at the start of business hours should
    NOT be flagged as after-hours.
    """

    def test_exact_start_time_not_flagged(self) -> None:
        """Access at exactly 6:00 should be considered within business hours."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_EXACT", "2026-01-15 06:00:00", "Form_A", "Read", "Finance", "GL"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(
            user_activity=activity,
            business_hours_start=6,
            business_hours_end=18,
        )

        # -- Assert --
        assert len(result.alerts) == 0


class TestBoundaryExactlyAtBusinessHoursEnd:
    """Test scenario: Access at exactly 18:00 (business hours end).

    Boundary test: access exactly at the end of business hours.
    Depending on implementation (inclusive vs exclusive), this may or may
    not be flagged. We test for consistent behavior.
    """

    def test_exact_end_time_behavior(self) -> None:
        """Access at 18:00 boundary should be handled consistently."""
        # -- Arrange --
        activity = _build_activity_with_timestamps(
            [
                ("USR_BOUND", "2026-01-15 18:00:00", "Form_A", "Read", "Finance", "GL"),
            ]
        )

        # -- Act --
        result = analyze_time_based_access(
            user_activity=activity,
            business_hours_start=6,
            business_hours_end=18,
        )

        # -- Assert --
        # 18:00 is the end boundary. The algorithm should handle this
        # consistently -- either always flag or never flag.
        # We accept both behaviors but verify no crash.
        assert isinstance(result.alerts, list)


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '5.3'."""

    def test_algorithm_id_is_5_3(self) -> None:
        """TimeBasedAccessAnalysis should carry algorithm_id '5.3'."""
        # -- Arrange --
        activity = _build_activity_with_timestamps([])

        # -- Act --
        result = analyze_time_based_access(user_activity=activity)

        # -- Assert --
        assert result.algorithm_id == "5.3"
