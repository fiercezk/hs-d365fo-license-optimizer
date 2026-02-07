"""Tests for Algorithm 3.7: Service Account Analyzer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_3_7_service_account_analyzer.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md
(Algorithm 3.7: Service Account Analyzer).

Algorithm 3.7 analyzes service account usage patterns and security posture:
  - Identify all service/system accounts in the environment
  - Analyze usage patterns (frequency, time of day, actions performed)
  - Detect service accounts with excessive privileges
  - Flag service accounts with no recent activity (stale)
  - Detect service accounts used interactively (human-like patterns)
  - Identify service accounts without proper ownership/documentation
  - Assess password/credential rotation compliance
  - Generate security governance recommendations
  - Calculate risk scores per service account

Key behaviors:
  - Service account with interactive login patterns = HIGH risk
  - Service account with no owner assigned = HIGH risk
  - Stale service account (no activity 90+ days) = MEDIUM risk
  - Service account with admin-level privileges = HIGH risk
  - Service account with credential age > 90 days = MEDIUM risk
  - Well-governed service account = LOW risk / no alert
  - Empty input = zero findings, no errors
  - Results sorted by risk score descending
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.algorithms.algorithm_3_7_service_account_analyzer import (
    ServiceAccountAnalysis,
    analyze_service_accounts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_service_account_inventory(
    accounts: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic service account inventory DataFrame.

    Args:
        accounts: List of dicts with keys:
            account_id, account_name, account_type (service/system/batch),
            owner_id, owner_name, description, created_date,
            last_credential_rotation, roles, role_count.
    """
    records: list[dict[str, Any]] = []
    for acct in accounts:
        records.append(
            {
                "account_id": acct.get("account_id", "SVC-001"),
                "account_name": acct.get("account_name", "SVC_DataSync"),
                "account_type": acct.get("account_type", "service"),
                "owner_id": acct.get("owner_id", None),
                "owner_name": acct.get("owner_name", None),
                "description": acct.get("description", ""),
                "created_date": acct.get("created_date", "2024-01-01"),
                "last_credential_rotation": acct.get(
                    "last_credential_rotation", "2025-12-01"
                ),
                "roles": acct.get("roles", ["DataReader"]),
                "role_count": acct.get("role_count", 1),
                "is_admin": acct.get("is_admin", False),
            }
        )
    return pd.DataFrame(records)


def _build_activity_df(
    rows: list[tuple[str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic service account activity DataFrame.

    Args:
        rows: List of (account_id, timestamp, menu_item, action) tuples.
    """
    records: list[dict[str, str]] = []
    for i, (acct_id, ts, menu_item, action) in enumerate(rows):
        records.append(
            {
                "user_id": acct_id,
                "timestamp": ts,
                "menu_item": menu_item,
                "action": action,
                "session_id": f"svc-sess-{i:04d}",
                "ip_address": "10.0.0.1",
                "user_agent": "D365-BatchService/1.0",
            }
        )
    return pd.DataFrame(records)


def _build_login_history(
    logins: list[tuple[str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic login history DataFrame.

    Args:
        logins: List of (account_id, timestamp, login_type, ip_address) tuples.
            login_type: 'interactive', 'non-interactive', 'batch'.
    """
    records: list[dict[str, str]] = []
    for i, (acct_id, ts, login_type, ip) in enumerate(logins):
        records.append(
            {
                "account_id": acct_id,
                "timestamp": ts,
                "login_type": login_type,
                "ip_address": ip,
                "session_id": f"login-{i:04d}",
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Interactive Login Pattern Detection (HIGH Risk)
# ---------------------------------------------------------------------------


class TestInteractiveLoginDetection:
    """Test scenario: Service account showing interactive login patterns.

    Service accounts should only authenticate via batch/API calls.
    Interactive logins suggest credential compromise or misuse.
    """

    def test_interactive_login_flagged_high_risk(self) -> None:
        """Service account with interactive logins = HIGH risk finding."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-001",
                    "account_name": "SVC_DataSync",
                    "owner_id": "USR-ADMIN",
                    "owner_name": "Admin User",
                }
            ]
        )
        activity = _build_activity_df(
            [
                ("SVC-001", "2026-01-15 14:00:00", "VendorList", "Read"),
                ("SVC-001", "2026-01-15 14:05:00", "CustomerList", "Read"),
            ]
        )
        logins = _build_login_history(
            [
                ("SVC-001", "2026-01-15 13:55:00", "interactive", "192.168.1.50"),
            ]
        )

        # -- Act --
        result: ServiceAccountAnalysis = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        assert len(result.findings) >= 1
        interactive_findings = [
            f for f in result.findings
            if "interactive" in f.finding_type.lower()
            or "interactive" in f.description.lower()
        ]
        assert len(interactive_findings) >= 1
        assert interactive_findings[0].risk_level in ("HIGH", "CRITICAL")

    def test_non_interactive_login_no_flag(self) -> None:
        """Service account with only batch/API logins should not be flagged."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-001",
                    "owner_id": "USR-ADMIN",
                    "owner_name": "Admin User",
                }
            ]
        )
        activity = _build_activity_df(
            [("SVC-001", "2026-01-15 02:00:00", "DataSync", "Write")]
        )
        logins = _build_login_history(
            [("SVC-001", "2026-01-15 02:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        interactive_findings = [
            f for f in result.findings
            if "interactive" in f.finding_type.lower()
        ]
        assert len(interactive_findings) == 0


# ---------------------------------------------------------------------------
# Test: No Owner Assigned (HIGH Risk)
# ---------------------------------------------------------------------------


class TestNoOwnerAssigned:
    """Test scenario: Service account with no owner/custodian.

    Every service account must have an assigned owner for governance.
    Missing ownership = HIGH risk.
    """

    def test_no_owner_flagged_high_risk(self) -> None:
        """Service account with no owner_id = HIGH risk finding."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-ORPHAN",
                    "account_name": "SVC_Legacy",
                    "owner_id": None,
                    "owner_name": None,
                    "description": "",
                }
            ]
        )
        activity = _build_activity_df(
            [("SVC-ORPHAN", "2026-01-15 03:00:00", "DataExport", "Read")]
        )
        logins = _build_login_history(
            [("SVC-ORPHAN", "2026-01-15 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        owner_findings = [
            f for f in result.findings
            if "owner" in f.finding_type.lower()
            or "ownership" in f.description.lower()
        ]
        assert len(owner_findings) >= 1
        assert owner_findings[0].risk_level in ("HIGH", "CRITICAL")

    def test_with_owner_no_ownership_finding(self) -> None:
        """Service account with valid owner should not flag ownership issue."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-OWNED",
                    "owner_id": "USR-ADMIN",
                    "owner_name": "Admin User",
                }
            ]
        )
        activity = _build_activity_df(
            [("SVC-OWNED", "2026-01-15 03:00:00", "DataSync", "Write")]
        )
        logins = _build_login_history(
            [("SVC-OWNED", "2026-01-15 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        owner_findings = [
            f for f in result.findings
            if "owner" in f.finding_type.lower()
        ]
        assert len(owner_findings) == 0


# ---------------------------------------------------------------------------
# Test: Stale Service Account (MEDIUM Risk)
# ---------------------------------------------------------------------------


class TestStaleServiceAccount:
    """Test scenario: Service account with no activity in 90+ days.

    Stale service accounts pose security risks and should be
    reviewed for decommissioning.
    """

    def test_stale_account_90_days_flagged(self) -> None:
        """Service account inactive 90+ days = MEDIUM risk finding."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-STALE",
                    "owner_id": "USR-ADMIN",
                    "owner_name": "Admin User",
                }
            ]
        )
        # No recent activity
        activity = _build_activity_df([])
        logins = _build_login_history([])

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        stale_findings = [
            f for f in result.findings
            if "stale" in f.finding_type.lower()
            or "inactive" in f.finding_type.lower()
            or "no activity" in f.description.lower()
        ]
        assert len(stale_findings) >= 1
        assert stale_findings[0].risk_level in ("MEDIUM", "HIGH")

    def test_active_account_not_flagged_stale(self) -> None:
        """Service account with recent activity should not be flagged as stale."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [{"account_id": "SVC-ACTIVE", "owner_id": "USR-ADMIN", "owner_name": "Admin"}]
        )
        activity = _build_activity_df(
            [("SVC-ACTIVE", "2026-02-05 03:00:00", "DataSync", "Write")]
        )
        logins = _build_login_history(
            [("SVC-ACTIVE", "2026-02-05 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        stale_findings = [
            f for f in result.findings
            if "stale" in f.finding_type.lower()
            or "inactive" in f.finding_type.lower()
        ]
        assert len(stale_findings) == 0


# ---------------------------------------------------------------------------
# Test: Admin-Level Privileges (HIGH Risk)
# ---------------------------------------------------------------------------


class TestAdminPrivileges:
    """Test scenario: Service account with admin/system administrator privileges.

    Service accounts with excessive privileges pose significant security risks.
    """

    def test_admin_service_account_flagged(self) -> None:
        """Service account with is_admin=True = HIGH risk finding."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-ADMIN",
                    "account_name": "SVC_SystemAdmin",
                    "owner_id": "USR-ADMIN",
                    "owner_name": "Admin User",
                    "is_admin": True,
                    "roles": ["SystemAdministrator", "SecurityAdmin"],
                    "role_count": 2,
                }
            ]
        )
        activity = _build_activity_df(
            [("SVC-ADMIN", "2026-01-15 03:00:00", "SystemConfig", "Write")]
        )
        logins = _build_login_history(
            [("SVC-ADMIN", "2026-01-15 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        priv_findings = [
            f for f in result.findings
            if "privilege" in f.finding_type.lower()
            or "admin" in f.finding_type.lower()
            or "excessive" in f.description.lower()
        ]
        assert len(priv_findings) >= 1
        assert priv_findings[0].risk_level in ("HIGH", "CRITICAL")

    def test_limited_privilege_not_flagged(self) -> None:
        """Service account with limited roles should not flag privilege issue."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-LIMITED",
                    "owner_id": "USR-ADMIN",
                    "owner_name": "Admin User",
                    "is_admin": False,
                    "roles": ["DataReader"],
                    "role_count": 1,
                }
            ]
        )
        activity = _build_activity_df(
            [("SVC-LIMITED", "2026-01-15 03:00:00", "ReportView", "Read")]
        )
        logins = _build_login_history(
            [("SVC-LIMITED", "2026-01-15 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        priv_findings = [
            f for f in result.findings
            if "privilege" in f.finding_type.lower()
            or "admin" in f.finding_type.lower()
        ]
        assert len(priv_findings) == 0


# ---------------------------------------------------------------------------
# Test: Credential Rotation Compliance (MEDIUM Risk)
# ---------------------------------------------------------------------------


class TestCredentialRotation:
    """Test scenario: Service account with credentials older than 90 days.

    Regular credential rotation is required for security compliance.
    """

    def test_old_credentials_flagged(self) -> None:
        """Credentials not rotated in 90+ days = MEDIUM risk finding."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-OLDCRED",
                    "owner_id": "USR-ADMIN",
                    "owner_name": "Admin User",
                    "last_credential_rotation": "2025-06-01",
                }
            ]
        )
        activity = _build_activity_df(
            [("SVC-OLDCRED", "2026-01-15 03:00:00", "DataSync", "Write")]
        )
        logins = _build_login_history(
            [("SVC-OLDCRED", "2026-01-15 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        cred_findings = [
            f for f in result.findings
            if "credential" in f.finding_type.lower()
            or "rotation" in f.finding_type.lower()
            or "password" in f.description.lower()
        ]
        assert len(cred_findings) >= 1
        assert cred_findings[0].risk_level in ("MEDIUM", "HIGH")

    def test_recent_rotation_not_flagged(self) -> None:
        """Credentials rotated recently should not flag rotation issue."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-FRESH",
                    "owner_id": "USR-ADMIN",
                    "owner_name": "Admin User",
                    "last_credential_rotation": "2026-01-20",
                }
            ]
        )
        activity = _build_activity_df(
            [("SVC-FRESH", "2026-02-01 03:00:00", "DataSync", "Write")]
        )
        logins = _build_login_history(
            [("SVC-FRESH", "2026-02-01 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        cred_findings = [
            f for f in result.findings
            if "credential" in f.finding_type.lower()
            or "rotation" in f.finding_type.lower()
        ]
        assert len(cred_findings) == 0


# ---------------------------------------------------------------------------
# Test: Multiple Risk Factors Combined
# ---------------------------------------------------------------------------


class TestMultipleRiskFactors:
    """Test scenario: Service account with multiple governance issues.

    A service account can have overlapping risk factors
    (no owner + stale + admin).
    """

    def test_multiple_findings_for_risky_account(self) -> None:
        """Account with multiple issues should generate multiple findings."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-DANGER",
                    "account_name": "SVC_Legacy_Admin",
                    "owner_id": None,
                    "owner_name": None,
                    "is_admin": True,
                    "roles": ["SystemAdministrator"],
                    "role_count": 1,
                    "last_credential_rotation": "2024-01-01",
                }
            ]
        )
        # No activity = stale
        activity = _build_activity_df([])
        logins = _build_login_history([])

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        # Should have at least 3 findings: no owner, stale, admin privilege
        account_findings = [
            f for f in result.findings if f.account_id == "SVC-DANGER"
        ]
        assert len(account_findings) >= 3

    def test_risk_score_increases_with_multiple_factors(self) -> None:
        """Account with multiple issues should have higher risk score."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-MULTI",
                    "owner_id": None,
                    "owner_name": None,
                    "is_admin": True,
                    "last_credential_rotation": "2024-01-01",
                }
            ]
        )
        activity = _build_activity_df([])
        logins = _build_login_history([])

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        # Risk score should be elevated
        account_summary = next(
            (s for s in result.account_summaries if s.account_id == "SVC-MULTI"),
            None,
        )
        assert account_summary is not None
        assert account_summary.risk_score >= 60


# ---------------------------------------------------------------------------
# Test: Well-Governed Service Account (No/LOW Findings)
# ---------------------------------------------------------------------------


class TestWellGovernedAccount:
    """Test scenario: Properly managed service account.

    A service account with owner, recent creds, limited privileges,
    and batch-only logins should produce no significant findings.
    """

    def test_healthy_account_no_high_findings(self) -> None:
        """Well-governed service account should have no HIGH/CRITICAL findings."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-GOOD",
                    "account_name": "SVC_DailyImport",
                    "owner_id": "USR-OWNER",
                    "owner_name": "Team Lead",
                    "description": "Nightly data import service account",
                    "is_admin": False,
                    "roles": ["DataImporter"],
                    "role_count": 1,
                    "last_credential_rotation": "2026-01-15",
                }
            ]
        )
        activity = _build_activity_df(
            [
                ("SVC-GOOD", "2026-02-01 02:00:00", "DataImport", "Write"),
                ("SVC-GOOD", "2026-02-02 02:00:00", "DataImport", "Write"),
                ("SVC-GOOD", "2026-02-03 02:00:00", "DataImport", "Write"),
            ]
        )
        logins = _build_login_history(
            [
                ("SVC-GOOD", "2026-02-01 02:00:00", "non-interactive", "10.0.0.1"),
                ("SVC-GOOD", "2026-02-02 02:00:00", "non-interactive", "10.0.0.1"),
                ("SVC-GOOD", "2026-02-03 02:00:00", "non-interactive", "10.0.0.1"),
            ]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        high_findings = [
            f for f in result.findings
            if f.risk_level in ("HIGH", "CRITICAL")
            and f.account_id == "SVC-GOOD"
        ]
        assert len(high_findings) == 0


# ---------------------------------------------------------------------------
# Test: Batch Processing Multiple Accounts
# ---------------------------------------------------------------------------


class TestBatchProcessing:
    """Test scenario: Analyze multiple service accounts simultaneously."""

    def test_multiple_accounts_processed(self) -> None:
        """All service accounts in inventory should be analyzed."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {"account_id": "SVC-A", "owner_id": "USR-1", "owner_name": "Owner 1"},
                {"account_id": "SVC-B", "owner_id": None, "owner_name": None},
                {"account_id": "SVC-C", "owner_id": "USR-2", "owner_name": "Owner 2"},
            ]
        )
        activity = _build_activity_df(
            [
                ("SVC-A", "2026-02-01 03:00:00", "DataSync", "Write"),
                ("SVC-C", "2026-02-01 03:00:00", "DataSync", "Write"),
            ]
        )
        logins = _build_login_history(
            [
                ("SVC-A", "2026-02-01 03:00:00", "non-interactive", "10.0.0.1"),
                ("SVC-C", "2026-02-01 03:00:00", "non-interactive", "10.0.0.1"),
            ]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        assert result.total_accounts_analyzed == 3
        # SVC-B should have findings (no owner + stale)
        svc_b_findings = [
            f for f in result.findings if f.account_id == "SVC-B"
        ]
        assert len(svc_b_findings) >= 1

    def test_findings_only_for_relevant_accounts(self) -> None:
        """Findings should reference only accounts in the inventory."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [{"account_id": "SVC-ONLY", "owner_id": "USR-1", "owner_name": "Owner"}]
        )
        # Activity from non-service account (should be ignored)
        activity = _build_activity_df(
            [
                ("SVC-ONLY", "2026-02-01 03:00:00", "DataSync", "Write"),
                ("USR-REGULAR", "2026-02-01 03:00:00", "SalesOrder", "Write"),
            ]
        )
        logins = _build_login_history(
            [("SVC-ONLY", "2026-02-01 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        for finding in result.findings:
            assert finding.account_id == "SVC-ONLY"


# ---------------------------------------------------------------------------
# Test: Results Sorted by Risk Score Descending
# ---------------------------------------------------------------------------


class TestResultsSorted:
    """Test scenario: Findings should be sorted by risk score descending."""

    def test_highest_risk_first(self) -> None:
        """Findings should be sorted from highest to lowest risk."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {
                    "account_id": "SVC-LOW",
                    "owner_id": "USR-1",
                    "owner_name": "Owner",
                    "is_admin": False,
                    "last_credential_rotation": "2025-11-01",
                },
                {
                    "account_id": "SVC-HIGH",
                    "owner_id": None,
                    "owner_name": None,
                    "is_admin": True,
                    "last_credential_rotation": "2024-01-01",
                },
            ]
        )
        activity = _build_activity_df(
            [("SVC-LOW", "2026-02-01 03:00:00", "DataSync", "Write")]
        )
        logins = _build_login_history(
            [("SVC-LOW", "2026-02-01 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        if len(result.account_summaries) >= 2:
            assert (
                result.account_summaries[0].risk_score
                >= result.account_summaries[1].risk_score
            )


# ---------------------------------------------------------------------------
# Test: Empty Input Handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty inventory and activity data."""

    def test_empty_inventory_no_findings(self) -> None:
        """Empty service account inventory should produce zero findings."""
        # -- Arrange --
        inventory = _build_service_account_inventory([])
        activity = _build_activity_df([])
        logins = _build_login_history([])

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        assert len(result.findings) == 0
        assert result.total_accounts_analyzed == 0

    def test_empty_activity_still_analyzes_governance(self) -> None:
        """Empty activity should still check ownership and credentials."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [{"account_id": "SVC-NOACT", "owner_id": None, "owner_name": None}]
        )
        activity = _build_activity_df([])
        logins = _build_login_history([])

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        # Should find ownership issue even without activity data
        assert len(result.findings) >= 1


# ---------------------------------------------------------------------------
# Test: Summary Statistics
# ---------------------------------------------------------------------------


class TestSummaryStatistics:
    """Test scenario: Result should include summary counts."""

    def test_summary_counts_populated(self) -> None:
        """Summary should count total accounts and findings by risk level."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [
                {"account_id": "SVC-A", "owner_id": "USR-1", "owner_name": "Owner"},
                {"account_id": "SVC-B", "owner_id": None, "owner_name": None},
            ]
        )
        activity = _build_activity_df(
            [("SVC-A", "2026-02-01 03:00:00", "DataSync", "Write")]
        )
        logins = _build_login_history(
            [("SVC-A", "2026-02-01 03:00:00", "non-interactive", "10.0.0.1")]
        )

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        assert result.total_accounts_analyzed == 2
        assert result.total_findings >= 0
        assert hasattr(result, "high_risk_count")
        assert hasattr(result, "medium_risk_count")


# ---------------------------------------------------------------------------
# Test: Finding Output Model Structure
# ---------------------------------------------------------------------------


class TestFindingModelStructure:
    """Test scenario: Verify finding output model has required fields."""

    def test_finding_has_required_fields(self) -> None:
        """ServiceAccountFinding should have all required fields."""
        # -- Arrange --
        inventory = _build_service_account_inventory(
            [{"account_id": "SVC-MODEL", "owner_id": None, "owner_name": None}]
        )
        activity = _build_activity_df([])
        logins = _build_login_history([])

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert hasattr(finding, "account_id")
        assert hasattr(finding, "finding_type")
        assert hasattr(finding, "risk_level")
        assert hasattr(finding, "description")
        assert hasattr(finding, "recommendation")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '3.7'."""

    def test_algorithm_id_is_3_7(self) -> None:
        """ServiceAccountAnalysis should carry algorithm_id '3.7'."""
        # -- Arrange --
        inventory = _build_service_account_inventory([])
        activity = _build_activity_df([])
        logins = _build_login_history([])

        # -- Act --
        result = analyze_service_accounts(
            service_account_inventory=inventory,
            user_activity=activity,
            login_history=logins,
        )

        # -- Assert --
        assert result.algorithm_id == "3.7"
