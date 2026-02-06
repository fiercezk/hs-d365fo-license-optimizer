"""Tests for Algorithm 3.6: Emergency Account Monitor.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_3_6_emergency_account_monitor.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 751-916
(Algorithm 3.6: Emergency Account Monitor).

Algorithm 3.6 monitors emergency/break-glass accounts for inappropriate usage,
ensures proper audit trails, and detects potential abuse:
  - Identify usage of pre-defined emergency accounts
  - Detect sessions without proper approval
  - Flag sessions exceeding approved duration
  - Detect activities outside approved scope
  - Identify high-risk actions without authorization
  - Flag usage outside authorized time windows
  - Support configurable emergency account lists
  - Generate severity-graded alerts (CRITICAL/HIGH/MEDIUM/LOW)

Key behaviors:
  - Emergency accounts used WITHOUT approval = CRITICAL alert
  - Activities outside approved scope = CRITICAL alert
  - High-risk actions (payments, journal posting) without auth = CRITICAL
  - Session duration > 2x expected = HIGH alert
  - Access outside authorized time window = MEDIUM alert
  - Justification mismatch (outage claim but read-only activity) = MEDIUM
  - Normal approved emergency usage = no alert (LOW/no detection)
  - Empty activity data = zero alerts, no errors
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import pytest

from src.algorithms.algorithm_3_6_emergency_account_monitor import (
    EmergencyAccountAlert,
    EmergencyAccountAnalysis,
    EmergencyAccountConfig,
    monitor_emergency_accounts,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MONETARY_TOLERANCE: float = 0.01

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_emergency_account_config(
    accounts: list[dict[str, Any]],
) -> list[EmergencyAccountConfig]:
    """Build emergency account configuration list.

    Args:
        accounts: List of dicts with keys:
            account_id, account_name, account_type (break-glass/emergency),
            authorized_approvers, max_session_hours.
    """
    configs = []
    for acct in accounts:
        configs.append(
            EmergencyAccountConfig(
                account_id=acct.get("account_id", "EMRG-001"),
                account_name=acct.get("account_name", "Emergency Admin"),
                account_type=acct.get("account_type", "break-glass"),
                authorized_approvers=acct.get(
                    "authorized_approvers", ["MGR-001", "MGR-002"]
                ),
                max_session_hours=acct.get("max_session_hours", 4),
            )
        )
    return configs


def _build_activity_df(
    rows: list[tuple[str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic emergency account activity DataFrame.

    Args:
        rows: List of (account_id, timestamp, menu_item, action) tuples.
            Timestamp format: 'YYYY-MM-DD HH:MM:SS'.
    """
    records: list[dict[str, str]] = []
    for i, (acct_id, ts, menu_item, action) in enumerate(rows):
        records.append(
            {
                "user_id": acct_id,
                "timestamp": ts,
                "menu_item": menu_item,
                "action": action,
                "session_id": f"emrg-sess-{i:04d}",
            }
        )
    return pd.DataFrame(records)


def _build_approval_records(
    approvals: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic approval records DataFrame.

    Args:
        approvals: List of dicts with keys:
            account_id, approver_id, approved_at, expected_duration_hours,
            authorized_activities (list), includes_high_risk (bool),
            justification, authorized_time_start, authorized_time_end.
    """
    records: list[dict[str, Any]] = []
    for i, appr in enumerate(approvals):
        records.append(
            {
                "approval_id": f"APPR-{i:04d}",
                "account_id": appr.get("account_id", "EMRG-001"),
                "approver_id": appr.get("approver_id", "MGR-001"),
                "approved_at": appr.get("approved_at", "2026-01-15 08:00:00"),
                "expected_duration_hours": appr.get(
                    "expected_duration_hours", 4
                ),
                "authorized_activities": appr.get(
                    "authorized_activities", []
                ),
                "includes_high_risk": appr.get("includes_high_risk", False),
                "justification": appr.get("justification", "System outage"),
                "authorized_time_start": appr.get(
                    "authorized_time_start", "2026-01-15 08:00:00"
                ),
                "authorized_time_end": appr.get(
                    "authorized_time_end", "2026-01-15 12:00:00"
                ),
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Unapproved Emergency Account Usage (CRITICAL)
# ---------------------------------------------------------------------------


class TestUnapprovedUsageCritical:
    """Test scenario: Emergency account used without any approval record.

    Per the spec, unapproved emergency access is CRITICAL severity
    requiring immediate investigation.
    """

    def test_unapproved_usage_generates_critical_alert(self) -> None:
        """Emergency account activity with no approval = CRITICAL alert."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001", "account_name": "Break-Glass Admin"}]
        )
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 10:00:00", "GeneralJournal", "Write"),
                ("EMRG-001", "2026-01-15 10:15:00", "VendorList", "Read"),
            ]
        )
        approvals = _build_approval_records([])  # No approvals

        # -- Act --
        result: EmergencyAccountAnalysis = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert len(result.alerts) >= 1
        critical_alerts = [
            a for a in result.alerts if a.severity == "CRITICAL"
        ]
        assert len(critical_alerts) >= 1
        assert any(
            "without approval" in a.issue.lower() for a in critical_alerts
        )

    def test_unapproved_usage_recommends_immediate_investigation(self) -> None:
        """Unapproved emergency usage should recommend immediate action."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = _build_activity_df(
            [("EMRG-001", "2026-01-15 10:00:00", "BankRecon", "Write")]
        )
        approvals = _build_approval_records([])

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert len(result.alerts) >= 1
        alert = result.alerts[0]
        assert "immediate" in alert.recommendation.lower() or (
            "investigate" in alert.recommendation.lower()
        )


# ---------------------------------------------------------------------------
# Test: Activities Outside Approved Scope (CRITICAL)
# ---------------------------------------------------------------------------


class TestActivitiesOutsideScope:
    """Test scenario: Emergency session performs actions not in approved scope.

    When an emergency account accesses menu items not listed in the
    authorization, this is CRITICAL because it indicates potential abuse.
    """

    def test_out_of_scope_activities_flagged_critical(self) -> None:
        """Activities outside approved scope should generate CRITICAL alert."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = _build_activity_df(
            [
                # Approved scope is only VendorList
                ("EMRG-001", "2026-01-15 09:00:00", "VendorList", "Read"),
                # This is outside scope:
                ("EMRG-001", "2026-01-15 09:30:00", "BankReconciliation", "Write"),
                ("EMRG-001", "2026-01-15 09:45:00", "GeneralJournalPost", "Write"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "authorized_activities": ["VendorList"],
                    "includes_high_risk": False,
                    "justification": "Vendor data fix",
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert len(result.alerts) >= 1
        scope_alerts = [
            a for a in result.alerts
            if a.severity == "CRITICAL"
            and ("scope" in a.issue.lower() or "outside" in a.issue.lower())
        ]
        assert len(scope_alerts) >= 1

    def test_out_of_scope_reports_count(self) -> None:
        """Alert should report how many out-of-scope activities occurred."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 09:00:00", "VendorList", "Read"),
                ("EMRG-001", "2026-01-15 09:30:00", "BankRecon", "Write"),
                ("EMRG-001", "2026-01-15 09:45:00", "GeneralJournal", "Write"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "authorized_activities": ["VendorList"],
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert len(result.alerts) >= 1
        # The alert should reference the count of out-of-scope activities
        scope_alert = next(
            (a for a in result.alerts if "scope" in a.issue.lower()
             or "outside" in a.issue.lower()),
            None,
        )
        assert scope_alert is not None
        assert scope_alert.out_of_scope_count >= 2


# ---------------------------------------------------------------------------
# Test: High-Risk Actions Without Authorization (CRITICAL)
# ---------------------------------------------------------------------------


class TestHighRiskActionsUnauthorized:
    """Test scenario: High-risk financial actions without explicit high-risk auth.

    Per spec, high-risk actions (VendorPayment, GeneralJournalPost,
    BankReconciliation) without includes_high_risk=True are CRITICAL.
    """

    def test_high_risk_action_without_auth_critical(self) -> None:
        """High-risk action without high-risk authorization = CRITICAL."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 09:00:00", "VendorPayment", "Write"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "authorized_activities": ["VendorPayment"],
                    "includes_high_risk": False,  # Not authorized for high-risk
                    "justification": "Emergency fix",
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        critical_alerts = [
            a for a in result.alerts if a.severity == "CRITICAL"
        ]
        assert len(critical_alerts) >= 1
        assert any(
            "high-risk" in a.issue.lower() or "high_risk" in a.issue.lower()
            for a in critical_alerts
        )

    def test_high_risk_with_auth_not_critical(self) -> None:
        """High-risk action WITH high-risk authorization should not be CRITICAL."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 09:00:00", "VendorPayment", "Write"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "authorized_activities": ["VendorPayment"],
                    "includes_high_risk": True,  # Authorized for high-risk
                    "justification": "Emergency payment required",
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        # Should NOT have CRITICAL high-risk alerts
        high_risk_critical = [
            a for a in result.alerts
            if a.severity == "CRITICAL"
            and ("high-risk" in a.issue.lower()
                 or "high_risk" in a.issue.lower())
        ]
        assert len(high_risk_critical) == 0


# ---------------------------------------------------------------------------
# Test: Session Duration Exceeded (HIGH)
# ---------------------------------------------------------------------------


class TestSessionDurationExceeded:
    """Test scenario: Emergency session exceeds 2x expected duration.

    Per spec, if actualDuration > expectedDuration * 2, severity is HIGH.
    """

    def test_long_session_generates_high_alert(self) -> None:
        """Session > 2x expected duration should generate HIGH alert."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001", "max_session_hours": 4}]
        )
        # Session spanning 10 hours (2.5x the 4-hour expectation)
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 08:00:00", "SystemConfig", "Read"),
                ("EMRG-001", "2026-01-15 18:00:00", "SystemConfig", "Write"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "expected_duration_hours": 4,
                    "authorized_activities": ["SystemConfig"],
                    "justification": "System maintenance",
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        duration_alerts = [
            a for a in result.alerts
            if "duration" in a.issue.lower() or "exceed" in a.issue.lower()
        ]
        assert len(duration_alerts) >= 1
        assert duration_alerts[0].severity in ("HIGH", "CRITICAL")

    def test_normal_duration_no_alert(self) -> None:
        """Session within expected duration should not generate duration alert."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001", "max_session_hours": 4}]
        )
        # Session spanning 2 hours (within 4-hour expectation)
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 08:00:00", "SystemConfig", "Read"),
                ("EMRG-001", "2026-01-15 10:00:00", "SystemConfig", "Write"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "expected_duration_hours": 4,
                    "authorized_activities": ["SystemConfig"],
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        duration_alerts = [
            a for a in result.alerts
            if "duration" in a.issue.lower() or "exceed" in a.issue.lower()
        ]
        assert len(duration_alerts) == 0


# ---------------------------------------------------------------------------
# Test: Access Outside Authorized Time Window (MEDIUM)
# ---------------------------------------------------------------------------


class TestAccessOutsideTimeWindow:
    """Test scenario: Emergency account used outside the authorized time window.

    Per spec, access outside the approved time window is MEDIUM severity.
    """

    def test_outside_time_window_flagged(self) -> None:
        """Activity outside authorized time window should generate alert."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        # Activity at 6 AM, but approval window is 8 AM - 12 PM
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 06:00:00", "SystemConfig", "Read"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "authorized_activities": ["SystemConfig"],
                    "authorized_time_start": "2026-01-15 08:00:00",
                    "authorized_time_end": "2026-01-15 12:00:00",
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        time_alerts = [
            a for a in result.alerts
            if "time" in a.issue.lower() or "window" in a.issue.lower()
        ]
        assert len(time_alerts) >= 1

    def test_within_time_window_no_time_alert(self) -> None:
        """Activity within authorized time window should not generate time alert."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 09:00:00", "SystemConfig", "Read"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "authorized_activities": ["SystemConfig"],
                    "authorized_time_start": "2026-01-15 08:00:00",
                    "authorized_time_end": "2026-01-15 12:00:00",
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        time_alerts = [
            a for a in result.alerts
            if "time" in a.issue.lower() or "window" in a.issue.lower()
        ]
        assert len(time_alerts) == 0


# ---------------------------------------------------------------------------
# Test: Justification Mismatch (MEDIUM)
# ---------------------------------------------------------------------------


class TestJustificationMismatch:
    """Test scenario: Emergency session justification does not match activity.

    Per spec, if justification is 'system outage' but >80% of activities
    are read-only, this is suspicious (MEDIUM severity).
    """

    def test_outage_justification_with_mostly_reads_flagged(self) -> None:
        """System outage claim with >80% read activity = MEDIUM alert."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        # 9 reads, 1 write = 90% read-only
        rows = [
            ("EMRG-001", f"2026-01-15 09:{i:02d}:00", f"Form_{i}", "Read")
            for i in range(9)
        ]
        rows.append(
            ("EMRG-001", "2026-01-15 09:09:00", "Form_W", "Write")
        )
        activity = _build_activity_df(rows)
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "authorized_activities": [f"Form_{i}" for i in range(9)]
                    + ["Form_W"],
                    "justification": "system outage",
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        mismatch_alerts = [
            a for a in result.alerts
            if "justification" in a.issue.lower()
            or "mismatch" in a.issue.lower()
        ]
        assert len(mismatch_alerts) >= 1

    def test_outage_justification_with_writes_no_mismatch(self) -> None:
        """System outage claim with significant write activity = no mismatch."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        # 5 reads, 5 writes = 50% read-only (below 80% threshold)
        rows = [
            ("EMRG-001", f"2026-01-15 09:{i:02d}:00", f"FormR_{i}", "Read")
            for i in range(5)
        ]
        rows.extend(
            [
                ("EMRG-001", f"2026-01-15 09:{i+5:02d}:00", f"FormW_{i}", "Write")
                for i in range(5)
            ]
        )
        activity = _build_activity_df(rows)
        all_forms = [f"FormR_{i}" for i in range(5)] + [
            f"FormW_{i}" for i in range(5)
        ]
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "authorized_activities": all_forms,
                    "justification": "system outage",
                    "includes_high_risk": True,
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        mismatch_alerts = [
            a for a in result.alerts
            if "justification" in a.issue.lower()
            or "mismatch" in a.issue.lower()
        ]
        assert len(mismatch_alerts) == 0


# ---------------------------------------------------------------------------
# Test: Normal Approved Usage (No Alerts)
# ---------------------------------------------------------------------------


class TestNormalApprovedUsage:
    """Test scenario: Properly approved emergency usage within all bounds.

    Normal approved usage should produce no alerts or only LOW severity.
    """

    def test_normal_usage_no_alerts(self) -> None:
        """Properly approved emergency usage should produce zero alerts."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001", "max_session_hours": 4}]
        )
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 09:00:00", "SystemConfig", "Write"),
                ("EMRG-001", "2026-01-15 09:30:00", "SystemConfig", "Read"),
                ("EMRG-001", "2026-01-15 10:00:00", "UserAdmin", "Write"),
            ]
        )
        approvals = _build_approval_records(
            [
                {
                    "account_id": "EMRG-001",
                    "expected_duration_hours": 4,
                    "authorized_activities": [
                        "SystemConfig",
                        "UserAdmin",
                    ],
                    "includes_high_risk": False,
                    "justification": "User provisioning fix",
                    "authorized_time_start": "2026-01-15 08:00:00",
                    "authorized_time_end": "2026-01-15 14:00:00",
                }
            ]
        )

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        # Should have no high-severity alerts
        high_alerts = [
            a for a in result.alerts
            if a.severity in ("CRITICAL", "HIGH", "MEDIUM")
        ]
        assert len(high_alerts) == 0


# ---------------------------------------------------------------------------
# Test: Multiple Emergency Accounts
# ---------------------------------------------------------------------------


class TestMultipleEmergencyAccounts:
    """Test scenario: Monitor multiple emergency accounts simultaneously.

    System should track and alert for each account independently.
    """

    def test_multiple_accounts_independent_alerts(self) -> None:
        """Each emergency account should be assessed independently."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [
                {"account_id": "EMRG-001", "account_name": "Break-Glass 1"},
                {"account_id": "EMRG-002", "account_name": "Break-Glass 2"},
            ]
        )
        activity = _build_activity_df(
            [
                # EMRG-001: unapproved usage
                ("EMRG-001", "2026-01-15 10:00:00", "FormA", "Write"),
                # EMRG-002: no activity (should be fine)
            ]
        )
        approvals = _build_approval_records([])  # No approvals for either

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        # Only EMRG-001 should have alerts (it has activity without approval)
        emrg1_alerts = [
            a for a in result.alerts if a.account_id == "EMRG-001"
        ]
        emrg2_alerts = [
            a for a in result.alerts if a.account_id == "EMRG-002"
        ]
        assert len(emrg1_alerts) >= 1
        assert len(emrg2_alerts) == 0


# ---------------------------------------------------------------------------
# Test: Empty Activity Data
# ---------------------------------------------------------------------------


class TestEmptyActivityData:
    """Test scenario: No emergency account activity in the monitoring period."""

    def test_no_activity_no_alerts(self) -> None:
        """No emergency account activity should produce zero alerts."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = pd.DataFrame(
            columns=["user_id", "timestamp", "menu_item", "action", "session_id"]
        )
        approvals = _build_approval_records([])

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert len(result.alerts) == 0

    def test_empty_config_no_alerts(self) -> None:
        """Empty emergency account config should produce zero alerts."""
        # -- Arrange --
        config: list[EmergencyAccountConfig] = []
        activity = _build_activity_df(
            [("USR_REGULAR", "2026-01-15 10:00:00", "FormA", "Read")]
        )
        approvals = _build_approval_records([])

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert len(result.alerts) == 0


# ---------------------------------------------------------------------------
# Test: Non-Emergency Account Activity Ignored
# ---------------------------------------------------------------------------


class TestNonEmergencyIgnored:
    """Test scenario: Regular user activity should not trigger alerts.

    Only accounts in the emergency account config should be monitored.
    """

    def test_regular_user_activity_not_flagged(self) -> None:
        """Activity from non-emergency accounts should be ignored."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        # Activity from a regular user, not an emergency account
        activity = _build_activity_df(
            [("USR_REGULAR", "2026-01-15 10:00:00", "FormA", "Write")]
        )
        approvals = _build_approval_records([])

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert len(result.alerts) == 0


# ---------------------------------------------------------------------------
# Test: Summary Statistics
# ---------------------------------------------------------------------------


class TestSummaryStatistics:
    """Test scenario: Result should include summary statistics."""

    def test_summary_includes_session_counts(self) -> None:
        """Summary should count total sessions and flagged sessions."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = _build_activity_df(
            [
                ("EMRG-001", "2026-01-15 09:00:00", "FormA", "Read"),
                ("EMRG-001", "2026-01-15 09:30:00", "FormB", "Write"),
            ]
        )
        approvals = _build_approval_records([])

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert result.total_sessions_analyzed >= 1
        assert result.total_emergency_accounts_monitored >= 1


# ---------------------------------------------------------------------------
# Test: Alert Output Model Structure
# ---------------------------------------------------------------------------


class TestAlertModelStructure:
    """Test scenario: Verify alert output model has required fields."""

    def test_alert_has_required_fields(self) -> None:
        """EmergencyAccountAlert should have all spec-required fields."""
        # -- Arrange --
        config = _build_emergency_account_config(
            [{"account_id": "EMRG-001"}]
        )
        activity = _build_activity_df(
            [("EMRG-001", "2026-01-15 10:00:00", "FormA", "Write")]
        )
        approvals = _build_approval_records([])

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert len(result.alerts) >= 1
        alert = result.alerts[0]
        assert hasattr(alert, "account_id")
        assert hasattr(alert, "severity")
        assert hasattr(alert, "issue")
        assert hasattr(alert, "recommendation")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '3.6'."""

    def test_algorithm_id_is_3_6(self) -> None:
        """EmergencyAccountAnalysis should carry algorithm_id '3.6'."""
        # -- Arrange --
        config = _build_emergency_account_config([])
        activity = pd.DataFrame(
            columns=["user_id", "timestamp", "menu_item", "action", "session_id"]
        )
        approvals = _build_approval_records([])

        # -- Act --
        result = monitor_emergency_accounts(
            emergency_accounts=config,
            user_activity=activity,
            approval_records=approvals,
        )

        # -- Assert --
        assert result.algorithm_id == "3.6"
