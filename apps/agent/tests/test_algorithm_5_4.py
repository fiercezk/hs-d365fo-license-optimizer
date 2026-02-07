"""Tests for Algorithm 5.4: Contractor Access Tracker.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_5_4_contractor_access_tracker.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md
(Algorithm 5.4: Contractor Access Tracker).
Category: User Behavior & Analytics.

Algorithm 5.4 tracks contractor/external user access for compliance:
  - Identify all contractor/external users in the environment
  - Track contract expiration dates and flag expired contractors
  - Monitor contractor activity against authorized scope
  - Detect contractors with access beyond their contract period
  - Flag contractors with elevated privileges (should be limited)
  - Detect inactive contractors still consuming licenses
  - Generate compliance reports for external access reviews
  - Calculate license cost for contractor accounts
  - Support configurable contractor identification criteria

Key behaviors:
  - Expired contractor still active = CRITICAL (compliance violation)
  - Contractor with admin/elevated privileges = HIGH risk
  - Contractor inactive 60+ days but license active = MEDIUM risk
  - Contractor accessing outside authorized scope = HIGH risk
  - Active contractor within contract period = no finding
  - Contractor approaching expiration (30 days) = WARNING
  - Empty input = zero findings, no errors
  - Results sorted by severity then contract expiration date
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from src.algorithms.algorithm_5_4_contractor_access_tracker import (
    ContractorFinding,
    ContractorAccessAnalysis,
    track_contractor_access,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_contractor_registry(
    contractors: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic contractor registry DataFrame.

    Args:
        contractors: List of dicts with keys:
            user_id, user_name, email, contractor_company,
            contract_start_date, contract_end_date, status,
            authorized_roles, authorized_menu_items,
            is_elevated_privilege, current_license,
            license_cost_monthly.
    """
    records: list[dict[str, Any]] = []
    for c in contractors:
        records.append(
            {
                "user_id": c.get("user_id", "CNTR-001"),
                "user_name": c.get("user_name", "External Contractor"),
                "email": c.get("email", "contractor@external.com"),
                "contractor_company": c.get("contractor_company", "Acme Consulting"),
                "contract_start_date": c.get("contract_start_date", "2025-01-01"),
                "contract_end_date": c.get("contract_end_date", "2026-12-31"),
                "status": c.get("status", "Active"),
                "authorized_roles": c.get("authorized_roles", ["DataAnalyst"]),
                "authorized_menu_items": c.get(
                    "authorized_menu_items", ["ReportView", "DataExport"]
                ),
                "is_elevated_privilege": c.get("is_elevated_privilege", False),
                "current_license": c.get("current_license", "Team Members"),
                "license_cost_monthly": c.get("license_cost_monthly", 60.0),
            }
        )
    return pd.DataFrame(records)


def _build_user_role_assignments(
    assignments: list[tuple[str, str, str]],
) -> pd.DataFrame:
    """Build synthetic user-role assignment DataFrame.

    Args:
        assignments: List of (user_id, role_name, status) tuples.
    """
    records: list[dict[str, str]] = []
    for uid, role, status in assignments:
        records.append(
            {
                "user_id": uid,
                "role_name": role,
                "status": status,
                "assigned_date": "2025-06-01",
            }
        )
    return pd.DataFrame(records)


def _build_activity_data(
    rows: list[tuple[str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic contractor activity DataFrame.

    Args:
        rows: List of (user_id, timestamp, menu_item, action) tuples.
    """
    records: list[dict[str, str]] = []
    for i, (uid, ts, menu_item, action) in enumerate(rows):
        records.append(
            {
                "user_id": uid,
                "timestamp": ts,
                "menu_item": menu_item,
                "action": action,
                "session_id": f"cntr-sess-{i:04d}",
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Expired Contractor Still Active (CRITICAL)
# ---------------------------------------------------------------------------


class TestExpiredContractorCritical:
    """Test scenario: Contractor whose contract has expired but account
    is still active. This is a compliance violation.
    """

    def test_expired_contractor_detected(self) -> None:
        """Contractor with expired contract but Active status = CRITICAL."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-EXPIRED",
                    "contract_end_date": "2025-12-31",  # Expired
                    "status": "Active",
                }
            ]
        )
        roles = _build_user_role_assignments(
            [("CNTR-EXPIRED", "DataAnalyst", "Active")]
        )
        activity = _build_activity_data(
            [("CNTR-EXPIRED", "2026-02-01 10:00:00", "ReportView", "Read")]
        )

        # -- Act --
        result: ContractorAccessAnalysis = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        expired_findings = [
            f for f in result.findings
            if "expired" in f.finding_type.lower()
            or "contract" in f.finding_type.lower()
        ]
        assert len(expired_findings) >= 1
        assert expired_findings[0].severity == "CRITICAL"
        assert expired_findings[0].user_id == "CNTR-EXPIRED"

    def test_expired_contractor_recommends_immediate_action(self) -> None:
        """Expired contractor should recommend immediate access revocation."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [{"user_id": "CNTR-EXP", "contract_end_date": "2025-06-30", "status": "Active"}]
        )
        roles = _build_user_role_assignments(
            [("CNTR-EXP", "Analyst", "Active")]
        )
        activity = _build_activity_data([])

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        expired = [
            f for f in result.findings
            if "expired" in f.finding_type.lower()
        ]
        assert len(expired) >= 1
        assert "revok" in expired[0].recommendation.lower() or (
            "disabl" in expired[0].recommendation.lower()
        )


# ---------------------------------------------------------------------------
# Test: Contractor with Elevated Privileges (HIGH Risk)
# ---------------------------------------------------------------------------


class TestElevatedPrivilegesHigh:
    """Test scenario: Contractor with admin or elevated privileges.

    Contractors should have minimal access. Elevated privileges = HIGH risk.
    """

    def test_elevated_privilege_flagged(self) -> None:
        """Contractor with is_elevated_privilege=True = HIGH risk finding."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-ADMIN",
                    "is_elevated_privilege": True,
                    "contract_end_date": "2026-12-31",
                    "status": "Active",
                }
            ]
        )
        roles = _build_user_role_assignments(
            [
                ("CNTR-ADMIN", "SystemAdmin", "Active"),
                ("CNTR-ADMIN", "SecurityAdmin", "Active"),
            ]
        )
        activity = _build_activity_data(
            [("CNTR-ADMIN", "2026-01-15 10:00:00", "SystemConfig", "Write")]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        priv_findings = [
            f for f in result.findings
            if "privilege" in f.finding_type.lower()
            or "elevated" in f.finding_type.lower()
        ]
        assert len(priv_findings) >= 1
        assert priv_findings[0].severity in ("HIGH", "CRITICAL")

    def test_limited_privilege_not_flagged(self) -> None:
        """Contractor with standard access should not be flagged for privilege."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-NORMAL",
                    "is_elevated_privilege": False,
                    "contract_end_date": "2026-12-31",
                    "status": "Active",
                }
            ]
        )
        roles = _build_user_role_assignments(
            [("CNTR-NORMAL", "DataAnalyst", "Active")]
        )
        activity = _build_activity_data(
            [("CNTR-NORMAL", "2026-01-15 10:00:00", "ReportView", "Read")]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        priv_findings = [
            f for f in result.findings
            if "privilege" in f.finding_type.lower()
            or "elevated" in f.finding_type.lower()
        ]
        assert len(priv_findings) == 0


# ---------------------------------------------------------------------------
# Test: Inactive Contractor with Active License (MEDIUM)
# ---------------------------------------------------------------------------


class TestInactiveContractorMedium:
    """Test scenario: Contractor inactive 60+ days but license still active.

    Wasted license spend for inactive contractors.
    """

    def test_inactive_contractor_flagged(self) -> None:
        """Contractor with no activity in 60+ days = MEDIUM finding."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-IDLE",
                    "contract_end_date": "2026-12-31",
                    "status": "Active",
                    "license_cost_monthly": 60.0,
                }
            ]
        )
        roles = _build_user_role_assignments(
            [("CNTR-IDLE", "DataAnalyst", "Active")]
        )
        # No activity at all
        activity = _build_activity_data([])

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        inactive_findings = [
            f for f in result.findings
            if "inactive" in f.finding_type.lower()
            or "idle" in f.finding_type.lower()
            or "no activity" in f.description.lower()
        ]
        assert len(inactive_findings) >= 1
        assert inactive_findings[0].severity in ("MEDIUM", "HIGH")

    def test_active_contractor_not_flagged_inactive(self) -> None:
        """Contractor with recent activity should not be flagged as inactive."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-BUSY",
                    "contract_end_date": "2026-12-31",
                    "status": "Active",
                }
            ]
        )
        roles = _build_user_role_assignments(
            [("CNTR-BUSY", "DataAnalyst", "Active")]
        )
        activity = _build_activity_data(
            [
                ("CNTR-BUSY", "2026-02-05 10:00:00", "ReportView", "Read"),
                ("CNTR-BUSY", "2026-02-06 10:00:00", "DataExport", "Write"),
            ]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        inactive_findings = [
            f for f in result.findings
            if "inactive" in f.finding_type.lower()
            or "idle" in f.finding_type.lower()
        ]
        assert len(inactive_findings) == 0


# ---------------------------------------------------------------------------
# Test: Access Outside Authorized Scope (HIGH)
# ---------------------------------------------------------------------------


class TestOutsideAuthorizedScope:
    """Test scenario: Contractor accessing menu items beyond authorized scope.

    Contractors should only access specifically authorized functionality.
    """

    def test_out_of_scope_access_flagged(self) -> None:
        """Contractor accessing unauthorized menu items = HIGH finding."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-SCOPE",
                    "authorized_menu_items": ["ReportView", "DataExport"],
                    "contract_end_date": "2026-12-31",
                    "status": "Active",
                }
            ]
        )
        roles = _build_user_role_assignments(
            [("CNTR-SCOPE", "DataAnalyst", "Active")]
        )
        activity = _build_activity_data(
            [
                ("CNTR-SCOPE", "2026-01-15 10:00:00", "ReportView", "Read"),
                # These are outside authorized scope:
                ("CNTR-SCOPE", "2026-01-15 10:30:00", "VendorPayment", "Write"),
                ("CNTR-SCOPE", "2026-01-15 11:00:00", "GeneralJournal", "Write"),
            ]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        scope_findings = [
            f for f in result.findings
            if "scope" in f.finding_type.lower()
            or "unauthorized" in f.finding_type.lower()
        ]
        assert len(scope_findings) >= 1
        assert scope_findings[0].severity in ("HIGH", "CRITICAL")

    def test_in_scope_access_not_flagged(self) -> None:
        """Contractor accessing only authorized items should not be flagged."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-GOOD",
                    "authorized_menu_items": ["ReportView", "DataExport"],
                    "contract_end_date": "2026-12-31",
                    "status": "Active",
                }
            ]
        )
        roles = _build_user_role_assignments(
            [("CNTR-GOOD", "DataAnalyst", "Active")]
        )
        activity = _build_activity_data(
            [
                ("CNTR-GOOD", "2026-01-15 10:00:00", "ReportView", "Read"),
                ("CNTR-GOOD", "2026-01-15 10:30:00", "DataExport", "Read"),
            ]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        scope_findings = [
            f for f in result.findings
            if "scope" in f.finding_type.lower()
            or "unauthorized" in f.finding_type.lower()
        ]
        assert len(scope_findings) == 0


# ---------------------------------------------------------------------------
# Test: Active Contractor Within Contract (No Finding)
# ---------------------------------------------------------------------------


class TestActiveContractorNoFinding:
    """Test scenario: Well-managed contractor with no issues.

    Active contractor within contract period, using authorized access,
    with limited privileges should generate no significant findings.
    """

    def test_compliant_contractor_no_findings(self) -> None:
        """Compliant contractor should generate no HIGH/CRITICAL findings."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-CLEAN",
                    "contract_end_date": "2026-12-31",
                    "status": "Active",
                    "authorized_menu_items": ["ReportView", "DataExport"],
                    "is_elevated_privilege": False,
                }
            ]
        )
        roles = _build_user_role_assignments(
            [("CNTR-CLEAN", "DataAnalyst", "Active")]
        )
        activity = _build_activity_data(
            [
                ("CNTR-CLEAN", "2026-02-01 10:00:00", "ReportView", "Read"),
                ("CNTR-CLEAN", "2026-02-02 10:00:00", "DataExport", "Read"),
            ]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        high_findings = [
            f for f in result.findings
            if f.severity in ("HIGH", "CRITICAL")
            and f.user_id == "CNTR-CLEAN"
        ]
        assert len(high_findings) == 0


# ---------------------------------------------------------------------------
# Test: Contract Approaching Expiration (WARNING)
# ---------------------------------------------------------------------------


class TestContractApproachingExpiration:
    """Test scenario: Contractor contract expires within 30 days.

    Proactive warning to ensure timely renewal or offboarding.
    """

    def test_expiration_warning_generated(self) -> None:
        """Contract expiring within 30 days = WARNING finding."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {
                    "user_id": "CNTR-EXPIRING",
                    "contract_end_date": "2026-02-28",  # ~21 days from now
                    "status": "Active",
                }
            ]
        )
        roles = _build_user_role_assignments(
            [("CNTR-EXPIRING", "DataAnalyst", "Active")]
        )
        activity = _build_activity_data(
            [("CNTR-EXPIRING", "2026-02-05 10:00:00", "ReportView", "Read")]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        expiring_findings = [
            f for f in result.findings
            if "expir" in f.finding_type.lower()
            or "approaching" in f.description.lower()
        ]
        assert len(expiring_findings) >= 1
        assert expiring_findings[0].severity in ("LOW", "MEDIUM")


# ---------------------------------------------------------------------------
# Test: License Cost Tracking
# ---------------------------------------------------------------------------


class TestLicenseCostTracking:
    """Test scenario: Track license costs for contractor accounts."""

    def test_total_contractor_license_cost(self) -> None:
        """Analysis should report total monthly license cost for contractors."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {"user_id": "CNTR-A", "license_cost_monthly": 60.0, "contract_end_date": "2026-12-31"},
                {"user_id": "CNTR-B", "license_cost_monthly": 180.0, "contract_end_date": "2026-12-31"},
            ]
        )
        roles = _build_user_role_assignments(
            [
                ("CNTR-A", "Viewer", "Active"),
                ("CNTR-B", "Accountant", "Active"),
            ]
        )
        activity = _build_activity_data(
            [
                ("CNTR-A", "2026-02-01 10:00:00", "ReportView", "Read"),
                ("CNTR-B", "2026-02-01 10:00:00", "GeneralJournal", "Write"),
            ]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        assert result.total_contractor_license_cost_monthly >= 240.0


# ---------------------------------------------------------------------------
# Test: Batch Processing Multiple Contractors
# ---------------------------------------------------------------------------


class TestBatchProcessing:
    """Test scenario: Process multiple contractors with different statuses."""

    def test_multiple_contractors_analyzed(self) -> None:
        """All contractors in registry should be analyzed."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [
                {"user_id": "CNTR-1", "contract_end_date": "2025-06-30", "status": "Active"},
                {"user_id": "CNTR-2", "contract_end_date": "2026-12-31", "status": "Active"},
                {"user_id": "CNTR-3", "contract_end_date": "2026-12-31", "status": "Active"},
            ]
        )
        roles = _build_user_role_assignments(
            [
                ("CNTR-1", "Analyst", "Active"),
                ("CNTR-2", "Analyst", "Active"),
                ("CNTR-3", "Analyst", "Active"),
            ]
        )
        activity = _build_activity_data(
            [("CNTR-2", "2026-02-01 10:00:00", "ReportView", "Read")]
        )

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        assert result.total_contractors_analyzed == 3
        # CNTR-1 should have expired finding
        expired = [
            f for f in result.findings
            if f.user_id == "CNTR-1" and "expired" in f.finding_type.lower()
        ]
        assert len(expired) >= 1


# ---------------------------------------------------------------------------
# Test: Empty Input Handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input data."""

    def test_empty_registry_no_findings(self) -> None:
        """Empty contractor registry should produce zero findings."""
        # -- Arrange --
        registry = _build_contractor_registry([])
        roles = _build_user_role_assignments([])
        activity = _build_activity_data([])

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        assert len(result.findings) == 0
        assert result.total_contractors_analyzed == 0


# ---------------------------------------------------------------------------
# Test: Finding Output Model Structure
# ---------------------------------------------------------------------------


class TestFindingModelStructure:
    """Test scenario: Verify finding output model has required fields."""

    def test_finding_has_required_fields(self) -> None:
        """ContractorFinding should have all spec-required fields."""
        # -- Arrange --
        registry = _build_contractor_registry(
            [{"user_id": "CNTR-MODEL", "contract_end_date": "2025-06-30", "status": "Active"}]
        )
        roles = _build_user_role_assignments(
            [("CNTR-MODEL", "Analyst", "Active")]
        )
        activity = _build_activity_data([])

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        assert len(result.findings) >= 1
        f = result.findings[0]
        assert hasattr(f, "user_id")
        assert hasattr(f, "finding_type")
        assert hasattr(f, "severity")
        assert hasattr(f, "description")
        assert hasattr(f, "recommendation")
        assert hasattr(f, "contractor_company")
        assert hasattr(f, "contract_end_date")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '5.4'."""

    def test_algorithm_id_is_5_4(self) -> None:
        """ContractorAccessAnalysis should carry algorithm_id '5.4'."""
        # -- Arrange --
        registry = _build_contractor_registry([])
        roles = _build_user_role_assignments([])
        activity = _build_activity_data([])

        # -- Act --
        result = track_contractor_access(
            contractor_registry=registry,
            user_role_assignments=roles,
            user_activity=activity,
        )

        # -- Assert --
        assert result.algorithm_id == "5.4"
