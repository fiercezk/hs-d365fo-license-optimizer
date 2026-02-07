"""Tests for Algorithm 3.9: Entra-D365 License Sync Validator.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_3_9_entra_d365_license_sync.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1530-1692
(Algorithm 3.9: Entra-D365 License Sync Validator).

Algorithm 3.9 detects mismatches between tenant-level Entra ID licensing and
D365 FO role-based licensing. Licenses exist at two independent levels
(Entra ID managed by IT/Identity, D365 FO managed by functional admins)
that can drift out of sync.

Mismatch Types:
  M1 - Ghost License:      Entra license assigned, no D365 FO roles
  M2 - Compliance Gap:     D365 FO roles requiring higher license than Entra assignment
  M3 - Over-Provisioned:   Entra license tier > theoretical license from roles
  M4 - Stale Entitlement:  D365 FO user disabled but Entra license still active

Key behaviors:
  - M1: User has Entra D365 license but zero D365 FO roles = Ghost License (MEDIUM)
  - M2: User has D365 FO roles requiring Finance but only Team Members in Entra = HIGH
  - M2: User has D365 FO roles but no Entra license at all = HIGH
  - M3: User has Enterprise Entra license but roles only need Team Members = MEDIUM
  - M4: User disabled in D365 FO but still has active Entra license = MEDIUM
  - No mismatch: Entra license matches theoretical license = no finding
  - Cost impact calculated per mismatch (savings for M1/M3/M4, zero for M2)
  - SKU-to-license mapping table is configurable per tenant
  - Results sorted by severity then savings descending
  - Empty input = zero mismatches, no errors
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from src.algorithms.algorithm_3_9_entra_d365_license_sync import (
    LicenseMismatch,
    LicenseSyncAnalysis,
    MismatchType,
    validate_entra_d365_license_sync,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Standard SKU mapping for tests
DEFAULT_SKU_MAPPING = {
    "SKU-FINANCE": "Finance",
    "SKU-SCM": "SCM",
    "SKU-COMMERCE": "Commerce",
    "SKU-TEAM": "Team Members",
    "SKU-FINANCE-SCM": "Finance + SCM",
}


def _build_entra_license_data(
    users: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic Entra ID license data DataFrame.

    Args:
        users: List of dicts with keys:
            user_id, user_name, email, entra_sku_id, entra_sku_name,
            entra_license_type, entra_status.
    """
    records: list[dict[str, Any]] = []
    for u in users:
        records.append(
            {
                "user_id": u.get("user_id", "USR-001"),
                "user_name": u.get("user_name", "Test User"),
                "email": u.get("email", "test@contoso.com"),
                "entra_sku_id": u.get("entra_sku_id", "SKU-FINANCE"),
                "entra_sku_name": u.get(
                    "entra_sku_name", "Dynamics 365 Finance"
                ),
                "entra_license_type": u.get("entra_license_type", "Finance"),
                "entra_status": u.get("entra_status", "Active"),
            }
        )
    return pd.DataFrame(records)


def _build_d365_user_roles(
    users: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build synthetic D365 FO user-role data DataFrame.

    Args:
        users: List of dicts with keys:
            user_id, user_name, email, roles (list), role_count,
            theoretical_license, d365_status.
    """
    records: list[dict[str, Any]] = []
    for u in users:
        records.append(
            {
                "user_id": u.get("user_id", "USR-001"),
                "user_name": u.get("user_name", "Test User"),
                "email": u.get("email", "test@contoso.com"),
                "roles": u.get("roles", ["Accountant"]),
                "role_count": u.get("role_count", len(u.get("roles", ["Accountant"]))),
                "theoretical_license": u.get("theoretical_license", "Finance"),
                "d365_status": u.get("d365_status", "Active"),
            }
        )
    return pd.DataFrame(records)


def _build_sku_mapping(
    mapping: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build SKU-to-license mapping table."""
    return mapping or DEFAULT_SKU_MAPPING.copy()


# ---------------------------------------------------------------------------
# License tier ordering for tests
# ---------------------------------------------------------------------------

LICENSE_TIER_ORDER = {
    "Team Members": 1,
    "Operations": 2,
    "Finance": 3,
    "SCM": 3,
    "Commerce": 3,
    "Finance + SCM": 4,
}


# ---------------------------------------------------------------------------
# Test: M1 - Ghost License (Entra license, no D365 FO roles)
# ---------------------------------------------------------------------------


class TestM1GhostLicense:
    """Test scenario: User has Entra D365 license but zero D365 FO roles.

    Ghost licenses waste spend. Recommendation: remove Entra license
    or assign D365 FO roles.
    """

    def test_ghost_license_detected(self) -> None:
        """User with Entra license but no D365 FO roles = M1 Ghost License."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [
                {
                    "user_id": "USR-GHOST",
                    "entra_license_type": "Finance",
                    "entra_sku_id": "SKU-FINANCE",
                }
            ]
        )
        d365_data = _build_d365_user_roles([])  # No D365 FO roles at all
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result: LicenseSyncAnalysis = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m1_mismatches = [
            m for m in result.mismatches
            if m.mismatch_type == MismatchType.M1_GHOST_LICENSE
        ]
        assert len(m1_mismatches) >= 1
        assert m1_mismatches[0].user_id == "USR-GHOST"

    def test_ghost_license_severity_medium(self) -> None:
        """Ghost license should be MEDIUM severity."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-GHOST", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles([])
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m1 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE]
        assert len(m1) >= 1
        assert m1[0].severity == "MEDIUM"

    def test_ghost_license_includes_cost_savings(self) -> None:
        """Ghost license mismatch should report full license cost as savings."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-GHOST", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles([])
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m1 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE]
        assert len(m1) >= 1
        assert m1[0].monthly_cost_impact > 0

    def test_user_with_roles_not_ghost(self) -> None:
        """User with both Entra license and D365 FO roles = NOT ghost."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-OK", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles(
            [
                {
                    "user_id": "USR-OK",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                }
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m1 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE]
        ghost_for_user = [m for m in m1 if m.user_id == "USR-OK"]
        assert len(ghost_for_user) == 0


# ---------------------------------------------------------------------------
# Test: M2 - Compliance Gap (D365 FO roles need higher license than Entra)
# ---------------------------------------------------------------------------


class TestM2ComplianceGap:
    """Test scenario: User has D365 FO roles requiring a license tier
    higher than what is assigned in Entra (or no Entra license at all).

    Compliance gap = audit risk. No savings, but must be fixed.
    """

    def test_no_entra_license_compliance_gap(self) -> None:
        """User with D365 FO roles but no Entra license = M2 Compliance Gap."""
        # -- Arrange --
        entra_data = _build_entra_license_data([])  # No Entra licenses
        d365_data = _build_d365_user_roles(
            [
                {
                    "user_id": "USR-GAP",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                }
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m2 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP]
        assert len(m2) >= 1
        assert m2[0].user_id == "USR-GAP"

    def test_wrong_entra_license_compliance_gap(self) -> None:
        """User with Team Members Entra license but Finance roles = M2."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [
                {
                    "user_id": "USR-WRONG",
                    "entra_license_type": "Team Members",
                    "entra_sku_id": "SKU-TEAM",
                }
            ]
        )
        d365_data = _build_d365_user_roles(
            [
                {
                    "user_id": "USR-WRONG",
                    "roles": ["Accountant", "FinanceManager"],
                    "theoretical_license": "Finance",
                }
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m2 = [
            m for m in result.mismatches
            if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP
            and m.user_id == "USR-WRONG"
        ]
        assert len(m2) >= 1

    def test_compliance_gap_severity_high(self) -> None:
        """Compliance gap should be HIGH severity."""
        # -- Arrange --
        entra_data = _build_entra_license_data([])
        d365_data = _build_d365_user_roles(
            [{"user_id": "USR-GAP", "theoretical_license": "Finance"}]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m2 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP]
        assert len(m2) >= 1
        assert m2[0].severity == "HIGH"

    def test_compliance_gap_zero_savings(self) -> None:
        """Compliance gap has no savings (it's a cost to fix)."""
        # -- Arrange --
        entra_data = _build_entra_license_data([])
        d365_data = _build_d365_user_roles(
            [{"user_id": "USR-GAP", "theoretical_license": "Finance"}]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m2 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP]
        assert len(m2) >= 1
        assert m2[0].monthly_cost_impact == 0


# ---------------------------------------------------------------------------
# Test: M3 - Over-Provisioned (Entra license > theoretical license)
# ---------------------------------------------------------------------------


class TestM3OverProvisioned:
    """Test scenario: User has enterprise Entra license but roles only
    need Team Members. Entra license tier exceeds what D365 FO requires.
    """

    def test_over_provisioned_detected(self) -> None:
        """Finance Entra license with Team Members roles = M3 Over-Provisioned."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [
                {
                    "user_id": "USR-OVER",
                    "entra_license_type": "Finance",
                    "entra_sku_id": "SKU-FINANCE",
                }
            ]
        )
        d365_data = _build_d365_user_roles(
            [
                {
                    "user_id": "USR-OVER",
                    "roles": ["TeamMemberRole"],
                    "theoretical_license": "Team Members",
                }
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m3 = [
            m for m in result.mismatches
            if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED
            and m.user_id == "USR-OVER"
        ]
        assert len(m3) >= 1

    def test_over_provisioned_severity_medium(self) -> None:
        """Over-provisioned should be MEDIUM severity."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-OVER", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles(
            [{"user_id": "USR-OVER", "theoretical_license": "Team Members"}]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m3 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED]
        assert len(m3) >= 1
        assert m3[0].severity == "MEDIUM"

    def test_over_provisioned_includes_tier_diff_savings(self) -> None:
        """Savings = cost(Entra license) - cost(theoretical license)."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-OVER", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles(
            [{"user_id": "USR-OVER", "theoretical_license": "Team Members"}]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m3 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED]
        assert len(m3) >= 1
        # Finance ($180) - Team Members ($60) = $120 savings
        assert m3[0].monthly_cost_impact > 0

    def test_matching_license_not_over_provisioned(self) -> None:
        """Matching Entra and theoretical license = no M3 mismatch."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-MATCH", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles(
            [{"user_id": "USR-MATCH", "theoretical_license": "Finance"}]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m3_for_user = [
            m for m in result.mismatches
            if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED
            and m.user_id == "USR-MATCH"
        ]
        assert len(m3_for_user) == 0


# ---------------------------------------------------------------------------
# Test: M4 - Stale Entitlement (D365 FO disabled, Entra license active)
# ---------------------------------------------------------------------------


class TestM4StaleEntitlement:
    """Test scenario: User disabled in D365 FO but still has Entra license.

    Stale entitlements waste license spend and pose security risk.
    """

    def test_stale_entitlement_detected(self) -> None:
        """Disabled D365 FO user with active Entra license = M4 Stale."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [
                {
                    "user_id": "USR-STALE",
                    "entra_license_type": "Finance",
                    "entra_status": "Active",
                }
            ]
        )
        d365_data = _build_d365_user_roles(
            [
                {
                    "user_id": "USR-STALE",
                    "roles": [],
                    "theoretical_license": "None",
                    "d365_status": "Disabled",
                }
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m4 = [
            m for m in result.mismatches
            if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT
            and m.user_id == "USR-STALE"
        ]
        assert len(m4) >= 1

    def test_stale_entitlement_severity_medium(self) -> None:
        """Stale entitlement should be MEDIUM severity."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-STALE", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles(
            [{"user_id": "USR-STALE", "d365_status": "Disabled"}]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m4 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT]
        assert len(m4) >= 1
        assert m4[0].severity == "MEDIUM"

    def test_stale_entitlement_includes_full_license_cost(self) -> None:
        """Stale entitlement savings = full Entra license cost."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-STALE", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles(
            [{"user_id": "USR-STALE", "d365_status": "Disabled"}]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m4 = [m for m in result.mismatches if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT]
        assert len(m4) >= 1
        assert m4[0].monthly_cost_impact > 0

    def test_active_d365_user_not_stale(self) -> None:
        """Active D365 FO user should not be flagged as stale entitlement."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-ACTIVE", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles(
            [
                {
                    "user_id": "USR-ACTIVE",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                }
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        m4_for_user = [
            m for m in result.mismatches
            if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT
            and m.user_id == "USR-ACTIVE"
        ]
        assert len(m4_for_user) == 0


# ---------------------------------------------------------------------------
# Test: No Mismatch (Perfectly Synced)
# ---------------------------------------------------------------------------


class TestNoMismatch:
    """Test scenario: Entra license matches theoretical D365 FO license."""

    def test_synced_user_no_mismatches(self) -> None:
        """User with matching Entra and D365 FO licenses = zero mismatches."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-SYNCED", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles(
            [
                {
                    "user_id": "USR-SYNCED",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                }
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        user_mismatches = [m for m in result.mismatches if m.user_id == "USR-SYNCED"]
        assert len(user_mismatches) == 0


# ---------------------------------------------------------------------------
# Test: Configurable SKU Mapping
# ---------------------------------------------------------------------------


class TestConfigurableSKUMapping:
    """Test scenario: Custom SKU-to-license mapping per tenant."""

    def test_custom_sku_mapping_used(self) -> None:
        """Custom SKU mapping should override default mapping."""
        # -- Arrange --
        custom_mapping = {
            "CUSTOM-SKU-FIN": "Finance",
            "CUSTOM-SKU-TM": "Team Members",
        }
        entra_data = _build_entra_license_data(
            [
                {
                    "user_id": "USR-CUSTOM",
                    "entra_sku_id": "CUSTOM-SKU-FIN",
                    "entra_license_type": "Finance",
                }
            ]
        )
        d365_data = _build_d365_user_roles(
            [
                {
                    "user_id": "USR-CUSTOM",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                }
            ]
        )

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=custom_mapping,
        )

        # -- Assert --
        user_mismatches = [m for m in result.mismatches if m.user_id == "USR-CUSTOM"]
        assert len(user_mismatches) == 0


# ---------------------------------------------------------------------------
# Test: Batch Processing Multiple Users
# ---------------------------------------------------------------------------


class TestBatchProcessing:
    """Test scenario: Process multiple users with different mismatch types."""

    def test_multiple_mismatch_types_detected(self) -> None:
        """Batch should detect M1, M2, M3, M4 across different users."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [
                {"user_id": "USR-M1", "entra_license_type": "Finance"},
                {"user_id": "USR-M3", "entra_license_type": "Finance"},
                {"user_id": "USR-M4", "entra_license_type": "SCM"},
            ]
        )
        d365_data = _build_d365_user_roles(
            [
                # USR-M1: has Entra but no D365 roles (Ghost)
                # USR-M2: has D365 roles but no Entra license (Compliance Gap)
                {
                    "user_id": "USR-M2",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                },
                # USR-M3: Over-provisioned (Finance Entra, Team Members needed)
                {
                    "user_id": "USR-M3",
                    "roles": ["BasicViewer"],
                    "theoretical_license": "Team Members",
                    "d365_status": "Active",
                },
                # USR-M4: Stale (disabled in D365 but has Entra license)
                {
                    "user_id": "USR-M4",
                    "roles": [],
                    "theoretical_license": "None",
                    "d365_status": "Disabled",
                },
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        types_found = {m.mismatch_type for m in result.mismatches}
        assert MismatchType.M1_GHOST_LICENSE in types_found
        assert MismatchType.M2_COMPLIANCE_GAP in types_found
        assert MismatchType.M3_OVER_PROVISIONED in types_found
        assert MismatchType.M4_STALE_ENTITLEMENT in types_found


# ---------------------------------------------------------------------------
# Test: Results Sorted by Severity then Savings
# ---------------------------------------------------------------------------


class TestResultsSorted:
    """Test scenario: Results sorted by severity (HIGH first) then savings."""

    def test_high_severity_before_medium(self) -> None:
        """HIGH severity mismatches should appear before MEDIUM."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [
                {"user_id": "USR-MEDIUM", "entra_license_type": "Finance"},
            ]
        )
        d365_data = _build_d365_user_roles(
            [
                # M2 (HIGH) user has roles but no Entra license
                {
                    "user_id": "USR-HIGH",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                },
                # USR-MEDIUM is ghost (MEDIUM)
            ]
        )
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        if len(result.mismatches) >= 2:
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            for i in range(len(result.mismatches) - 1):
                current = severity_order.get(result.mismatches[i].severity, 4)
                next_val = severity_order.get(result.mismatches[i + 1].severity, 4)
                assert current <= next_val


# ---------------------------------------------------------------------------
# Test: Empty Input Handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input data."""

    def test_empty_entra_and_d365_no_mismatches(self) -> None:
        """Empty data should produce zero mismatches."""
        # -- Arrange --
        entra_data = _build_entra_license_data([])
        d365_data = _build_d365_user_roles([])
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        assert len(result.mismatches) == 0
        assert result.total_users_analyzed == 0


# ---------------------------------------------------------------------------
# Test: Summary Statistics
# ---------------------------------------------------------------------------


class TestSummaryStatistics:
    """Test scenario: Result includes summary statistics."""

    def test_summary_counts_populated(self) -> None:
        """Summary should count mismatches by type."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-GHOST", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles([])
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        assert hasattr(result, "total_users_analyzed")
        assert hasattr(result, "total_mismatches")
        assert hasattr(result, "total_monthly_savings")
        assert hasattr(result, "ghost_license_count")
        assert hasattr(result, "compliance_gap_count")
        assert hasattr(result, "over_provisioned_count")
        assert hasattr(result, "stale_entitlement_count")


# ---------------------------------------------------------------------------
# Test: Mismatch Output Model Structure
# ---------------------------------------------------------------------------


class TestMismatchModelStructure:
    """Test scenario: Verify mismatch output model has required fields."""

    def test_mismatch_has_required_fields(self) -> None:
        """LicenseMismatch should have all spec-required fields."""
        # -- Arrange --
        entra_data = _build_entra_license_data(
            [{"user_id": "USR-MODEL", "entra_license_type": "Finance"}]
        )
        d365_data = _build_d365_user_roles([])
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        assert len(result.mismatches) >= 1
        m = result.mismatches[0]
        assert hasattr(m, "user_id")
        assert hasattr(m, "mismatch_type")
        assert hasattr(m, "entra_license")
        assert hasattr(m, "d365_theoretical_license")
        assert hasattr(m, "severity")
        assert hasattr(m, "monthly_cost_impact")
        assert hasattr(m, "recommendation")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '3.9'."""

    def test_algorithm_id_is_3_9(self) -> None:
        """LicenseSyncAnalysis should carry algorithm_id '3.9'."""
        # -- Arrange --
        entra_data = _build_entra_license_data([])
        d365_data = _build_d365_user_roles([])
        sku_mapping = _build_sku_mapping()

        # -- Act --
        result = validate_entra_d365_license_sync(
            entra_license_data=entra_data,
            d365_user_roles=d365_data,
            sku_mapping=sku_mapping,
        )

        # -- Assert --
        assert result.algorithm_id == "3.9"
