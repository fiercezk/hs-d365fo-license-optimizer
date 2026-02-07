"""Tests for Algorithm 5.4: Contractor Access Tracker (TDD).

TDD RED phase -- these tests define the expected behavior for the
Contractor Access Tracker algorithm.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md
(Algorithm 5.4: Contractor Access Tracker).
Requirements/08-Algorithm-Review-Summary.md: "Extern compliance", Low complexity.

Algorithm 5.4 monitors contractor/external user access to ensure compliance
with contract terms and organizational security policies:
  - Detect contractors with access beyond their contract end date
  - Flag inactive contractors still consuming licenses (zombie accounts)
  - Identify contractors with excessive privileges (high-privilege roles)
  - Track contractors approaching contract expiry for proactive review
  - Calculate cost impact of contractor license waste
  - Generate compliance findings with severity levels

Key behaviors:
  - Expired contract + active access = CRITICAL finding (immediate revocation)
  - Expired contract + no activity = HIGH finding (license waste + compliance risk)
  - Active contract + no activity (>30 days) = MEDIUM finding (zombie account)
  - Active contract + high-privilege role = MEDIUM finding (review needed)
  - Contract expiring within 30 days = LOW finding (proactive notification)
  - Active contract + normal usage = no finding (compliant)
  - Empty input = empty results
  - Results sorted by severity then cost impact
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.algorithms.algorithm_5_4_contractor_access_tracker import (
    ContractorAccessReport,
    FindingSeverity,
    track_contractor_access,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_contractor_records(
    contractors: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic contractor DataFrame.

    Args:
        contractors: List of dicts with keys:
            user_id, user_name, email, user_type, contract_start,
            contract_end, department, roles, license_type,
            license_cost_monthly.
    """
    records: list[dict[str, Any]] = []
    for c in contractors:
        records.append(
            {
                "user_id": c.get("user_id", "CTR-001"),
                "user_name": c.get("user_name", "Test Contractor"),
                "email": c.get("email", "contractor@external.com"),
                "user_type": c.get("user_type", "Contractor"),
                "contract_start": c.get("contract_start", "2025-01-01"),
                "contract_end": c.get("contract_end", "2026-06-30"),
                "department": c.get("department", "IT"),
                "roles": c.get("roles", "Accountant"),
                "is_high_privilege": c.get("is_high_privilege", False),
                "license_type": c.get("license_type", "Finance"),
                "license_cost_monthly": c.get("license_cost_monthly", 180.0),
                "status": c.get("status", "Active"),
            }
        )
    return pd.DataFrame(records)


def _build_activity_data(
    rows: list[tuple[str, str, str, str]],
) -> pd.DataFrame:
    """Build synthetic activity DataFrame.

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
                "session_id": f"sess-{i:04d}",
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Expired Contract with Active Access -> CRITICAL
# ---------------------------------------------------------------------------


class TestExpiredContractActiveAccess:
    """Test scenario: Contractor with expired contract still has access.

    This is the highest-severity finding -- a contractor whose contract
    has ended but still has active system access. Immediate revocation needed.
    """

    def test_expired_contract_is_critical(self) -> None:
        """Contractor with expired contract = CRITICAL finding."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-001",
                    "user_name": "Expired Contractor",
                    "contract_end": "2025-12-31",  # Expired
                    "status": "Active",
                }
            ]
        )
        # Recent activity after contract end
        activity = _build_activity_data(
            [("CTR-001", "2026-01-15 10:00:00", "GeneralJournal", "Write")]
        )

        result: ContractorAccessReport = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert finding.user_id == "CTR-001"
        assert finding.severity == FindingSeverity.CRITICAL
        assert finding.finding_type == "EXPIRED_CONTRACT_ACTIVE_ACCESS"

    def test_expired_contract_includes_days_overdue(self) -> None:
        """CRITICAL finding should include how many days past expiry."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-002",
                    "contract_end": "2025-11-01",  # ~3 months expired
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data([("CTR-002", "2026-01-20 10:00:00", "FormA", "Read")])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert finding.days_overdue is not None
        assert finding.days_overdue > 0

    def test_expired_contract_includes_cost_impact(self) -> None:
        """CRITICAL finding should quantify wasted license cost."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-003",
                    "contract_end": "2025-10-01",  # 4 months expired
                    "license_cost_monthly": 180.0,
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data([("CTR-003", "2026-01-15 10:00:00", "FormA", "Read")])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert finding.monthly_cost_impact > 0
        assert finding.monthly_cost_impact == 180.0


# ---------------------------------------------------------------------------
# Test: Expired Contract with No Activity -> HIGH
# ---------------------------------------------------------------------------


class TestExpiredContractNoActivity:
    """Test scenario: Contractor with expired contract and no recent activity.

    Still a compliance risk (account should be deprovisioned) but lower
    severity since they are not actively using the system.
    """

    def test_expired_no_activity_is_high(self) -> None:
        """Expired contractor with no activity = HIGH finding."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-004",
                    "contract_end": "2025-12-31",
                    "status": "Active",
                }
            ]
        )
        # No activity at all
        activity = _build_activity_data([])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert finding.user_id == "CTR-004"
        assert finding.severity == FindingSeverity.HIGH
        assert finding.finding_type == "EXPIRED_CONTRACT_NO_ACTIVITY"


# ---------------------------------------------------------------------------
# Test: Active Contract but Inactive User -> MEDIUM
# ---------------------------------------------------------------------------


class TestActiveContractInactiveUser:
    """Test scenario: Contractor with valid contract but no recent activity.

    Zombie contractor accounts that still consume licenses but show no
    usage in the past 30+ days.
    """

    def test_inactive_contractor_is_medium(self) -> None:
        """Active contract + no activity in 30+ days = MEDIUM finding."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-005",
                    "contract_end": "2026-12-31",  # Still valid
                    "status": "Active",
                }
            ]
        )
        # Activity only 60 days ago -- stale
        activity = _build_activity_data([("CTR-005", "2025-12-01 10:00:00", "FormA", "Read")])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 1),
        )

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert finding.user_id == "CTR-005"
        assert finding.severity == FindingSeverity.MEDIUM
        assert finding.finding_type == "INACTIVE_CONTRACTOR"

    def test_inactive_threshold_configurable(self) -> None:
        """Inactivity threshold should be configurable (default 30 days)."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-006",
                    "contract_end": "2026-12-31",
                    "status": "Active",
                }
            ]
        )
        # Activity 20 days ago
        activity = _build_activity_data([("CTR-006", "2026-01-18 10:00:00", "FormA", "Read")])

        # Default threshold (30 days) -- 20 days is within threshold
        result_default = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 7),
        )
        inactive_findings_default = [
            f for f in result_default.findings if f.finding_type == "INACTIVE_CONTRACTOR"
        ]
        assert len(inactive_findings_default) == 0

        # Stricter threshold (14 days) -- 20 days exceeds threshold
        result_strict = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            inactivity_threshold_days=14,
            reference_date=datetime(2026, 2, 7),
        )
        inactive_findings_strict = [
            f for f in result_strict.findings if f.finding_type == "INACTIVE_CONTRACTOR"
        ]
        assert len(inactive_findings_strict) == 1


# ---------------------------------------------------------------------------
# Test: Contractor with High-Privilege Role -> MEDIUM
# ---------------------------------------------------------------------------


class TestContractorHighPrivilege:
    """Test scenario: Contractor assigned high-privilege roles.

    Contractors should generally have minimal access. High-privilege
    roles on contractor accounts require explicit review.
    """

    def test_high_privilege_contractor_is_medium(self) -> None:
        """Contractor with high-privilege role = MEDIUM finding."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-007",
                    "contract_end": "2026-12-31",
                    "is_high_privilege": True,
                    "roles": "SystemAdmin",
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data(
            [("CTR-007", "2026-02-01 10:00:00", "SystemConfig", "Write")]
        )

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 7),
        )

        high_priv_findings = [
            f for f in result.findings if f.finding_type == "HIGH_PRIVILEGE_CONTRACTOR"
        ]
        assert len(high_priv_findings) >= 1
        assert high_priv_findings[0].severity == FindingSeverity.MEDIUM


# ---------------------------------------------------------------------------
# Test: Contract Expiring Soon -> LOW
# ---------------------------------------------------------------------------


class TestContractExpiringSoon:
    """Test scenario: Contractor contract expiring within 30 days.

    Proactive notification to review whether contract will be renewed
    or access should be revoked at expiry.
    """

    def test_expiring_soon_is_low(self) -> None:
        """Contract expiring within 30 days = LOW finding."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-008",
                    "contract_end": "2026-02-28",  # ~21 days from reference
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data([("CTR-008", "2026-02-05 10:00:00", "FormA", "Write")])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 7),
        )

        expiring_findings = [
            f for f in result.findings if f.finding_type == "CONTRACT_EXPIRING_SOON"
        ]
        assert len(expiring_findings) >= 1
        assert expiring_findings[0].severity == FindingSeverity.LOW
        assert expiring_findings[0].days_until_expiry is not None
        assert expiring_findings[0].days_until_expiry <= 30

    def test_expiry_window_configurable(self) -> None:
        """Expiry warning window should be configurable (default 30 days)."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-009",
                    "contract_end": "2026-04-01",  # ~53 days out
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data([("CTR-009", "2026-02-05 10:00:00", "FormA", "Read")])

        # Default window (30 days) -- 53 days out, no finding
        result_default = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 7),
        )
        expiring_default = [
            f for f in result_default.findings if f.finding_type == "CONTRACT_EXPIRING_SOON"
        ]
        assert len(expiring_default) == 0

        # Wider window (60 days) -- 53 days out, should trigger
        result_wide = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            expiry_warning_days=60,
            reference_date=datetime(2026, 2, 7),
        )
        expiring_wide = [
            f for f in result_wide.findings if f.finding_type == "CONTRACT_EXPIRING_SOON"
        ]
        assert len(expiring_wide) == 1


# ---------------------------------------------------------------------------
# Test: Compliant Contractor -> No Finding
# ---------------------------------------------------------------------------


class TestCompliantContractor:
    """Test scenario: Contractor with valid contract and active usage.

    No findings should be generated for compliant contractors.
    """

    def test_active_compliant_no_findings(self) -> None:
        """Active contractor with valid contract = no findings."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-010",
                    "contract_end": "2027-01-01",  # Far future
                    "is_high_privilege": False,
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data(
            [
                ("CTR-010", "2026-02-01 10:00:00", "FormA", "Write"),
                ("CTR-010", "2026-02-05 10:00:00", "FormB", "Read"),
            ]
        )

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 7),
        )

        assert len(result.findings) == 0


# ---------------------------------------------------------------------------
# Test: Empty Input Handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input data."""

    def test_empty_contractors_returns_empty(self) -> None:
        """No contractor records should produce empty report."""
        contractors = _build_contractor_records([])
        activity = _build_activity_data([])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert len(result.findings) == 0
        assert result.total_contractors_analyzed == 0
        assert result.total_findings == 0

    def test_no_activity_data(self) -> None:
        """Contractors with no activity data should still be analyzed."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-011",
                    "contract_end": "2025-12-31",  # Expired
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data([])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert result.total_contractors_analyzed == 1
        assert len(result.findings) >= 1


# ---------------------------------------------------------------------------
# Test: Multiple Contractors
# ---------------------------------------------------------------------------


class TestMultipleContractors:
    """Test scenario: Multiple contractors with mixed compliance states."""

    def test_multiple_contractors_all_analyzed(self) -> None:
        """All contractors should be analyzed."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-A",
                    "contract_end": "2025-12-31",  # Expired
                    "status": "Active",
                },
                {
                    "user_id": "CTR-B",
                    "contract_end": "2027-01-01",  # Valid
                    "is_high_privilege": True,
                    "status": "Active",
                },
                {
                    "user_id": "CTR-C",
                    "contract_end": "2027-01-01",  # Valid, compliant
                    "is_high_privilege": False,
                    "status": "Active",
                },
            ]
        )
        activity = _build_activity_data(
            [
                ("CTR-A", "2026-01-15 10:00:00", "FormA", "Read"),
                ("CTR-B", "2026-02-01 10:00:00", "AdminPanel", "Write"),
                ("CTR-C", "2026-02-05 10:00:00", "FormC", "Read"),
            ]
        )

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 7),
        )

        assert result.total_contractors_analyzed == 3
        # CTR-A: expired + active = CRITICAL
        # CTR-B: high-privilege = MEDIUM
        # CTR-C: compliant = no finding
        assert result.total_findings >= 2

        user_ids_with_findings = {f.user_id for f in result.findings}
        assert "CTR-A" in user_ids_with_findings
        assert "CTR-B" in user_ids_with_findings
        assert "CTR-C" not in user_ids_with_findings


# ---------------------------------------------------------------------------
# Test: Severity Sorting
# ---------------------------------------------------------------------------


class TestSeveritySorting:
    """Test scenario: Findings sorted by severity then cost impact."""

    def test_findings_sorted_by_severity(self) -> None:
        """CRITICAL findings should appear before MEDIUM findings."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-HI",
                    "contract_end": "2025-12-31",  # Expired = CRITICAL
                    "license_cost_monthly": 60.0,
                    "status": "Active",
                },
                {
                    "user_id": "CTR-MED",
                    "contract_end": "2027-01-01",
                    "is_high_privilege": True,  # High priv = MEDIUM
                    "license_cost_monthly": 180.0,
                    "status": "Active",
                },
            ]
        )
        activity = _build_activity_data(
            [
                ("CTR-HI", "2026-01-15 10:00:00", "FormA", "Read"),
                ("CTR-MED", "2026-02-05 10:00:00", "AdminPanel", "Write"),
            ]
        )

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 7),
        )

        assert len(result.findings) >= 2
        severities = [f.severity for f in result.findings]
        # CRITICAL should come before MEDIUM
        critical_idx = next(i for i, s in enumerate(severities) if s == FindingSeverity.CRITICAL)
        medium_idx = next(i for i, s in enumerate(severities) if s == FindingSeverity.MEDIUM)
        assert critical_idx < medium_idx


# ---------------------------------------------------------------------------
# Test: Report Summary Statistics
# ---------------------------------------------------------------------------


class TestReportSummary:
    """Test scenario: Report includes aggregate statistics."""

    def test_report_has_summary_counts(self) -> None:
        """Report should include counts by severity."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-X",
                    "contract_end": "2025-12-31",
                    "status": "Active",
                },
                {
                    "user_id": "CTR-Y",
                    "contract_end": "2027-01-01",
                    "is_high_privilege": True,
                    "status": "Active",
                },
            ]
        )
        activity = _build_activity_data(
            [
                ("CTR-X", "2026-01-15 10:00:00", "FormA", "Read"),
                ("CTR-Y", "2026-02-05 10:00:00", "Admin", "Write"),
            ]
        )

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
            reference_date=datetime(2026, 2, 7),
        )

        assert hasattr(result, "critical_count")
        assert hasattr(result, "high_count")
        assert hasattr(result, "medium_count")
        assert hasattr(result, "low_count")
        assert result.total_findings == (
            result.critical_count + result.high_count + result.medium_count + result.low_count
        )

    def test_report_has_total_cost_impact(self) -> None:
        """Report should include total monthly cost impact."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-COST",
                    "contract_end": "2025-12-31",
                    "license_cost_monthly": 180.0,
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data([("CTR-COST", "2026-01-15 10:00:00", "FormA", "Read")])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert hasattr(result, "total_monthly_cost_impact")
        assert result.total_monthly_cost_impact >= 0


# ---------------------------------------------------------------------------
# Test: Finding Model Structure
# ---------------------------------------------------------------------------


class TestFindingModelStructure:
    """Test scenario: Verify finding model has required fields."""

    def test_finding_has_required_fields(self) -> None:
        """ContractorAccessFinding should have all required fields."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-MODEL",
                    "contract_end": "2025-12-31",
                    "status": "Active",
                }
            ]
        )
        activity = _build_activity_data([("CTR-MODEL", "2026-01-15 10:00:00", "FormA", "Read")])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert hasattr(finding, "user_id")
        assert hasattr(finding, "user_name")
        assert hasattr(finding, "finding_type")
        assert hasattr(finding, "severity")
        assert hasattr(finding, "description")
        assert hasattr(finding, "recommendation")
        assert hasattr(finding, "monthly_cost_impact")
        assert hasattr(finding, "contract_end")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '5.4'."""

    def test_algorithm_id_is_5_4(self) -> None:
        """ContractorAccessReport should carry algorithm_id '5.4'."""
        contractors = _build_contractor_records([])
        activity = _build_activity_data([])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        assert result.algorithm_id == "5.4"


# ---------------------------------------------------------------------------
# Test: Disabled Contractor Status
# ---------------------------------------------------------------------------


class TestDisabledContractorStatus:
    """Test scenario: Contractors with Inactive status should be skipped."""

    def test_inactive_status_contractor_skipped(self) -> None:
        """Contractor with Inactive status should not generate findings."""
        contractors = _build_contractor_records(
            [
                {
                    "user_id": "CTR-DISABLED",
                    "contract_end": "2025-12-31",  # Expired
                    "status": "Inactive",  # Already disabled
                }
            ]
        )
        activity = _build_activity_data([])

        result = track_contractor_access(
            contractor_records=contractors,
            user_activity=activity,
        )

        # Inactive contractors are already deprovisioned -- no finding
        assert len(result.findings) == 0
