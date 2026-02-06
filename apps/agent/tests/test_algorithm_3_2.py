"""Tests for Algorithm 3.2: Anomalous Role Change Detector.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until src/algorithms/algorithm_3_2_anomalous_role_change_detector.py
is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, Algorithm 3.2.

Algorithm 3.2 detects suspicious or unauthorized role assignment changes that could
indicate security breaches or insider threats. It analyzes:
  - Time-based anomalies (after-hours, weekend assignments)
  - Approver anomalies (unusual approvers, service accounts)
  - Role privilege level (high-privilege roles assigned to new users)
  - Rapid successive changes (3+ roles within 1 hour)
  - Missing approval workflows
  - Service account usage patterns

Each role change is scored on a 0-100 anomaly scale, with risk levels:
  - CRITICAL: >= 90 (immediate investigation)
  - HIGH: >= 70 (within 24 hours)
  - MEDIUM: >= 50 (within 7 days)
  - LOW: < 50 (informational)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.algorithms.algorithm_3_2_anomalous_role_change_detector import (
    detect_anomalous_role_changes,
)
from src.models.output_schemas import (
    LicenseRecommendation,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

# Tolerance for floating-point comparisons on anomaly scores
ANOMALY_TOLERANCE: float = 2.0

# Tolerance for risk level thresholds
RISK_LEVEL_TOLERANCE: float = 1.0


# ---------------------------------------------------------------------------
# Test Data Builders
# ---------------------------------------------------------------------------


def _create_role_change(
    user_id: str,
    user_name: str,
    role_name: str,
    action: str,
    timestamp: datetime,
    changed_by: str,
    has_approval: bool = True,
    is_service_account: bool = False,
    role_privilege_level: str = "MEDIUM",
) -> dict[str, Any]:
    """Create a role change record for testing.

    Args:
        user_id: User identifier
        user_name: User display name
        role_name: Role being assigned/removed
        action: "ASSIGNED" or "REMOVED"
        timestamp: When the change occurred (UTC)
        changed_by: Admin/Service account that made the change
        has_approval: Whether approval workflow exists
        is_service_account: Whether the changer is a service account
        role_privilege_level: "HIGH", "MEDIUM", or "LOW"

    Returns:
        Role change record dictionary.
    """
    return {
        "change_id": f"CHG_{user_id}_{timestamp.timestamp()}",
        "user_affected": user_id,
        "user_name": user_name,
        "role_changed": role_name,
        "action": action,
        "changed_by": changed_by,
        "timestamp": timestamp.isoformat(),
        "has_approval_workflow": has_approval,
        "is_service_account_changer": is_service_account,
        "role_privilege_level": role_privilege_level,
    }


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON.

    Returns:
        Parsed pricing config with license costs and savings rules.
    """
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Test: After-Hours High-Privilege Assignment (CRITICAL)
# ---------------------------------------------------------------------------


class TestAfterHoursHighPrivilege:
    """Test scenario: High-privilege role assigned at 2 AM on Saturday.

    This is the CRITICAL severity case from the specification:
    - Role: "Accounts Payable Manager" (HIGH privilege)
    - Time: Saturday 2 AM (after-hours + weekend)
    - Expected anomaly score: ~50-80+ (CRITICAL)
    - Risk level: CRITICAL
    - Reason: After-hours + high-privilege role + weekend

    This should trigger immediate investigation.
    """

    def test_after_hours_high_privilege_weekend(self) -> None:
        """High-privilege role assigned at 2 AM Saturday → CRITICAL alert."""
        # Scenario: Saturday 2 AM (2024-02-10 02:00:00 UTC is a Saturday)
        change_time = datetime(2024, 2, 10, 2, 0, 0)  # 2 AM Saturday

        role_changes = [
            _create_role_change(
                user_id="USR015",
                user_name="Jane Doe",
                role_name="Accounts Payable Manager",
                action="ASSIGNED",
                timestamp=change_time,
                changed_by="ADMIN_01",
                has_approval=True,
                role_privilege_level="HIGH",
            )
        ]

        # Convert to DataFrame
        df_changes = pd.DataFrame(role_changes)

        # Run detector
        results = detect_anomalous_role_changes(
            role_changes=df_changes,
            time_window_days=7,
        )

        # Should have one anomaly
        assert len(results) >= 1, "Should detect at least one anomaly for after-hours high-privilege"

        # Find the result for USR015
        result = None
        for r in results:
            if r.get("user_affected") == "USR015":
                result = r
                break

        assert result is not None, "Should have result for USR015"
        assert result["risk_level"] == "CRITICAL", \
            f"After-hours high-privilege should be CRITICAL, got {result['risk_level']}"
        assert result["anomaly_score"] >= 50, \
            f"Anomaly score should be >= 50, got {result['anomaly_score']}"

        # Check for expected anomaly reasons
        reasons_text = " ".join(result["anomaly_reasons"])
        assert "after-hours" in reasons_text.lower() or "2 am" in reasons_text.lower(), \
            "Should mention after-hours change"
        assert "weekend" in reasons_text.lower() or "saturday" in reasons_text.lower(), \
            "Should mention weekend"
        assert "high-privilege" in reasons_text.lower(), \
            "Should mention high-privilege role"

    def test_after_hours_medium_privilege(self) -> None:
        """Medium-privilege role assigned at 2 AM → HIGH risk (but not CRITICAL)."""
        change_time = datetime(2024, 2, 10, 2, 0, 0)  # 2 AM Saturday

        role_changes = [
            _create_role_change(
                user_id="USR016",
                user_name="John Smith",
                role_name="Sales Manager",
                action="ASSIGNED",
                timestamp=change_time,
                changed_by="ADMIN_01",
                role_privilege_level="MEDIUM",
            )
        ]

        df_changes = pd.DataFrame(role_changes)
        results = detect_anomalous_role_changes(df_changes)

        assert len(results) >= 1
        result = next((r for r in results if r["user_affected"] == "USR016"), None)
        assert result is not None

        # Should be HIGH or MEDIUM (after-hours + weekend, but medium privilege)
        assert result["risk_level"] in ["HIGH", "MEDIUM"], \
            f"Medium-privilege after-hours should be HIGH/MEDIUM, got {result['risk_level']}"


# ---------------------------------------------------------------------------
# Test: Rapid Role Escalation (HIGH)
# ---------------------------------------------------------------------------


class TestRapidRoleEscalation:
    """Test scenario: 3+ high-privilege roles assigned within 1 hour.

    This pattern suggests:
    - Compromised account (attacker adding roles)
    - Privilege escalation attempt
    - Should trigger HIGH severity alert

    Specification: Check 4 from pseudocode, lines 334-342.
    """

    def test_rapid_role_escalation_three_in_one_hour(self) -> None:
        """Assign 3 high-privilege roles within 1 hour → HIGH alert."""
        base_time = datetime(2024, 2, 6, 14, 0, 0)  # 2 PM (normal hours)

        role_changes = [
            _create_role_change(
                user_id="USR017",
                user_name="Alice Cooper",
                role_name="Finance Manager",
                action="ASSIGNED",
                timestamp=base_time,
                changed_by="ADMIN_01",
                role_privilege_level="HIGH",
            ),
            _create_role_change(
                user_id="USR017",
                user_name="Alice Cooper",
                role_name="AP Clerk",
                action="ASSIGNED",
                timestamp=base_time + timedelta(minutes=15),
                changed_by="ADMIN_01",
                role_privilege_level="HIGH",
            ),
            _create_role_change(
                user_id="USR017",
                user_name="Alice Cooper",
                role_name="Purchasing Agent",
                action="ASSIGNED",
                timestamp=base_time + timedelta(minutes=30),
                changed_by="ADMIN_01",
                role_privilege_level="HIGH",
            ),
        ]

        df_changes = pd.DataFrame(role_changes)
        results = detect_anomalous_role_changes(df_changes)

        # Should detect anomalies (at least some of the changes)
        assert len(results) > 0, "Should detect anomalies for rapid escalation"

        # Find results for USR017
        usr017_results = [r for r in results if r["user_affected"] == "USR017"]
        assert len(usr017_results) > 0, "Should have results for USR017"

        # At least one should be HIGH or CRITICAL
        risk_levels = [r["risk_level"] for r in usr017_results]
        assert any(level in ["HIGH", "CRITICAL"] for level in risk_levels), \
            f"Rapid escalation should trigger HIGH+ risk, got {risk_levels}"

        # Check for "rapid" mention in reasons (at least one result should have it)
        all_reasons = []
        for r in usr017_results:
            all_reasons.extend(r.get("anomaly_reasons", []))
        reasons_text = " ".join(all_reasons)
        assert "rapid" in reasons_text.lower() or "escalation" in reasons_text.lower(), \
            f"Should mention rapid/escalation in reasons, got: {all_reasons}"


# ---------------------------------------------------------------------------
# Test: High-Privilege Role to New User (HIGH)
# ---------------------------------------------------------------------------


class TestHighPrivilegeNewUser:
    """Test scenario: High-privilege role assigned to brand new user (< 30 days).

    Risks:
    - Account compromise before full onboarding
    - Overprivileging during setup
    - Should trigger HIGH severity

    Specification: Check 3 from pseudocode, lines 323-332.
    """

    def test_high_privilege_assigned_to_new_user(self) -> None:
        """Assign high-privilege role to user created 5 days ago → HIGH alert."""
        # Use current date to make "5 days ago" realistic
        from datetime import datetime as dt
        now = dt.now()
        change_time = now  # Role assignment happens "now"

        role_changes = [
            _create_role_change(
                user_id="USR018",
                user_name="Bob Wilson",
                role_name="Finance Manager",
                action="ASSIGNED",
                timestamp=change_time,
                changed_by="ADMIN_01",
                role_privilege_level="HIGH",
            )
        ]

        df_changes = pd.DataFrame(role_changes)

        # Simulate user created 5 days ago from now
        user_profile = {
            "user_id": "USR018",
            "created_date": (now - timedelta(days=5)).isoformat(),
        }

        results = detect_anomalous_role_changes(
            role_changes=df_changes,
            user_profiles=[user_profile],
        )

        assert len(results) >= 1, \
            f"Should detect anomaly for new user getting high-privilege role, got {len(results)} results"
        result = next((r for r in results if r["user_affected"] == "USR018"), None)
        assert result is not None, "Should have result for USR018"

        assert result["risk_level"] in ["HIGH", "CRITICAL"], \
            f"New user high-privilege should be HIGH+, got {result['risk_level']}"
        assert result["anomaly_score"] >= 50, \
            f"Anomaly score should be >= 50, got {result['anomaly_score']}"


# ---------------------------------------------------------------------------
# Test: Service Account Usage (HIGH)
# ---------------------------------------------------------------------------


class TestServiceAccountAnomalous:
    """Test scenario: Service account making unusual role assignment.

    Most service accounts never make role changes. If one does, it's unusual.
    Should trigger HIGH severity alert.

    Specification: Check 6 from pseudocode, lines 354-360.
    """

    def test_service_account_role_change_rare_pattern(self) -> None:
        """Service account making rare role change → HIGH alert."""
        change_time = datetime(2024, 2, 6, 14, 0, 0)

        role_changes = [
            _create_role_change(
                user_id="USR019",
                user_name="Service Account Robot",
                role_name="Finance Manager",
                action="ASSIGNED",
                timestamp=change_time,
                changed_by="SA_AUTOMATION",  # Service account name
                is_service_account=True,
                role_privilege_level="HIGH",
            )
        ]

        df_changes = pd.DataFrame(role_changes)

        results = detect_anomalous_role_changes(df_changes)

        assert len(results) >= 1
        result = next((r for r in results if r["user_affected"] == "USR019"), None)
        assert result is not None

        assert result["risk_level"] in ["HIGH", "CRITICAL"], \
            f"Service account change should be HIGH+, got {result['risk_level']}"
        assert result["anomaly_score"] >= 40, \
            "Anomaly score should reflect service account concern"

        # Check for service account mention
        reasons_text = " ".join(result["anomaly_reasons"])
        assert "service account" in reasons_text.lower(), \
            "Should mention service account involvement"


# ---------------------------------------------------------------------------
# Test: Missing Approval (MEDIUM/HIGH)
# ---------------------------------------------------------------------------


class TestMissingApproval:
    """Test scenario: High-privilege role assigned without approval workflow.

    High-privilege roles should require approval. Missing approval is a red flag.
    Should trigger MEDIUM to HIGH severity.

    Specification: Check 5 from pseudocode, lines 344-351.
    """

    def test_high_privilege_no_approval(self) -> None:
        """High-privilege role assigned without approval → MEDIUM/HIGH alert."""
        change_time = datetime(2024, 2, 6, 14, 0, 0)

        role_changes = [
            _create_role_change(
                user_id="USR020",
                user_name="Charlie Brown",
                role_name="Finance Manager",
                action="ASSIGNED",
                timestamp=change_time,
                changed_by="ADMIN_01",
                has_approval=False,  # No approval workflow
                role_privilege_level="HIGH",
            )
        ]

        df_changes = pd.DataFrame(role_changes)
        results = detect_anomalous_role_changes(df_changes)

        assert len(results) >= 1
        result = next((r for r in results if r["user_affected"] == "USR020"), None)
        assert result is not None

        assert result["risk_level"] in ["MEDIUM", "HIGH", "CRITICAL"], \
            f"Missing approval for high-privilege should be MEDIUM+, got {result['risk_level']}"
        assert "approval" in " ".join(result["anomaly_reasons"]).lower(), \
            "Should mention missing approval"


# ---------------------------------------------------------------------------
# Test: Normal Change (No Alert)
# ---------------------------------------------------------------------------


class TestNormalChange:
    """Test scenario: Normal role assignment (no anomalies).

    Normal business hours, low-privilege role, with approval.
    Should NOT trigger an alert (no result returned).
    """

    def test_normal_business_hours_low_privilege(self) -> None:
        """Normal low-privilege role during business hours → no alert."""
        change_time = datetime(2024, 2, 6, 14, 0, 0)  # 2 PM Tuesday

        role_changes = [
            _create_role_change(
                user_id="USR021",
                user_name="David Lee",
                role_name="Sales Clerk",
                action="ASSIGNED",
                timestamp=change_time,
                changed_by="ADMIN_01",
                has_approval=True,
                role_privilege_level="LOW",
            )
        ]

        df_changes = pd.DataFrame(role_changes)
        results = detect_anomalous_role_changes(df_changes)

        # Should have no results (or very low anomaly score < 50)
        usr021_results = [r for r in results if r["user_affected"] == "USR021"]
        if len(usr021_results) > 0:
            # If there is a result, it should be LOW severity
            assert all(r["risk_level"] == "LOW" for r in usr021_results), \
                "Normal change should not trigger HIGH+ alerts"
        # Either no result or LOW severity is acceptable


# ---------------------------------------------------------------------------
# Test: Role Removal (Not Escalation Risk)
# ---------------------------------------------------------------------------


class TestRoleRemoval:
    """Test scenario: Role removal (de-provisioning).

    Removing roles is generally lower risk than adding them.
    De-escalation is not a security concern (inverse of privilege creep).
    """

    def test_role_removal_no_high_risk(self) -> None:
        """Removing high-privilege role → no high-risk alert."""
        change_time = datetime(2024, 2, 6, 14, 0, 0)

        role_changes = [
            _create_role_change(
                user_id="USR022",
                user_name="Eve Martinez",
                role_name="Finance Manager",
                action="REMOVED",  # Removal, not assignment
                timestamp=change_time,
                changed_by="ADMIN_01",
                role_privilege_level="HIGH",
            )
        ]

        df_changes = pd.DataFrame(role_changes)
        results = detect_anomalous_role_changes(df_changes)

        # Removal should not trigger HIGH+ alerts
        usr022_results = [r for r in results if r["user_affected"] == "USR022"]
        if len(usr022_results) > 0:
            # If there is a result, it should be LOW or MEDIUM (not HIGH/CRITICAL)
            assert all(r["risk_level"] in ["LOW", "MEDIUM"] for r in usr022_results), \
                "Role removal should not trigger CRITICAL+ alerts"


# ---------------------------------------------------------------------------
# Test: Combined Anomalies (Highest Severity)
# ---------------------------------------------------------------------------


class TestCombinedAnomalies:
    """Test scenario: Multiple anomalies on same change = CRITICAL.

    When multiple anomaly factors combine:
    - After-hours + high-privilege + weekend + no approval
    Should result in highest possible anomaly score and CRITICAL risk.
    """

    def test_multiple_anomalies_combined(self) -> None:
        """After-hours + high-privilege + weekend + no approval → CRITICAL."""
        # Saturday 2 AM with all red flags
        change_time = datetime(2024, 2, 10, 2, 0, 0)  # 2 AM Saturday

        role_changes = [
            _create_role_change(
                user_id="USR023",
                user_name="Frank Underwood",
                role_name="Accounts Payable Manager",
                action="ASSIGNED",
                timestamp=change_time,
                changed_by="ADMIN_01",
                has_approval=False,  # No approval
                role_privilege_level="HIGH",  # High privilege
            )
        ]

        df_changes = pd.DataFrame(role_changes)
        results = detect_anomalous_role_changes(df_changes)

        assert len(results) >= 1
        result = next((r for r in results if r["user_affected"] == "USR023"), None)
        assert result is not None

        assert result["risk_level"] == "CRITICAL", \
            f"Multiple combined anomalies should be CRITICAL, got {result['risk_level']}"
        assert result["anomaly_score"] >= 70, \
            f"Combined anomalies should have high anomaly score, got {result['anomaly_score']}"

        # Should mention multiple reasons
        reasons = result["anomaly_reasons"]
        assert len(reasons) >= 2, \
            f"Should have multiple anomaly reasons, got {len(reasons)}: {reasons}"
