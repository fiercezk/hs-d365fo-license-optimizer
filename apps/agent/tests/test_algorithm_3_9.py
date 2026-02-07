"""Tests for Algorithm 3.9: Entra-D365 License Sync Validator.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_3_9_entra_d365_sync_validator.py is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md
(Algorithm 3.9: Entra-D365 License Sync Validator).

Algorithm 3.9 detects mismatches between tenant-level Entra ID licensing and
D365 FO role-based licensing. Licenses exist at two independent levels
(Entra ID managed by IT/Identity, D365 FO managed by functional admins)
that can drift out of sync.

Mismatch Types:
  - M1 Ghost License: Entra license assigned, no D365 FO roles
  - M2 Compliance Gap: D365 FO roles present, no/wrong Entra license
  - M3 Over-Provisioned: Entra license tier > theoretical D365 requirement
  - M4 Stale Entitlement: D365 FO user disabled, Entra license still active

Key behaviors:
  - M1 Ghost = Entra license present, zero D365 FO roles => MEDIUM severity
  - M2 Compliance Gap = D365 roles present, no Entra license => HIGH severity
  - M2 Under-licensed = Entra tier < theoretical tier => HIGH severity
  - M3 Over-Provisioned = Entra tier > theoretical tier => MEDIUM severity
  - M4 Stale = D365 FO disabled, Entra license active => MEDIUM severity
  - Savings calculated using shared pricing utility
  - Empty input = empty mismatch list
  - Results sorted by severity (HIGH first), then savings descending
  - algorithm_id = "3.9"
"""

from __future__ import annotations

from typing import Any

import pytest

from src.algorithms.algorithm_3_9_entra_d365_sync_validator import (
    EntraD365SyncReport,
    MismatchRecord,
    MismatchType,
    validate_entra_d365_sync,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# License tier priority (higher = more expensive/capable)
LICENSE_TIER_PRIORITY: dict[str, int] = {
    "Team Members": 60,
    "Operations": 90,
    "Finance": 180,
    "SCM": 180,
    "Commerce": 180,
}

DEFAULT_SKU_MAP: dict[str, str] = {
    "guid-finance": "Finance",
    "guid-scm": "SCM",
    "guid-commerce": "Commerce",
    "guid-team-members": "Team Members",
    "guid-operations": "Operations",
}

DEFAULT_PRICING: dict[str, Any] = {
    "licenses": {
        "team_members": {
            "name": "Team Members",
            "pricePerUserPerMonth": 60.00,
        },
        "operations": {
            "name": "Operations",
            "pricePerUserPerMonth": 90.00,
        },
        "finance": {
            "name": "Finance",
            "pricePerUserPerMonth": 180.00,
        },
        "scm": {
            "name": "SCM",
            "pricePerUserPerMonth": 180.00,
        },
        "commerce": {
            "name": "Commerce",
            "pricePerUserPerMonth": 180.00,
        },
    }
}


def _build_entra_licenses(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build synthetic Entra license records.

    Args:
        records: List of dicts with keys:
            user_id, user_name, email, sku_id, sku_name, license_type.
    """
    result: list[dict[str, Any]] = []
    for r in records:
        result.append(
            {
                "user_id": r.get("user_id", "USR-001"),
                "user_name": r.get("user_name", "Test User"),
                "email": r.get("email", "test@contoso.com"),
                "sku_id": r.get("sku_id", "guid-finance"),
                "sku_name": r.get("sku_name", "Dynamics 365 Finance"),
                "license_type": r.get("license_type", "Finance"),
                "account_enabled": r.get("account_enabled", True),
            }
        )
    return result


def _build_d365_users(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build synthetic D365 FO user records with role assignments.

    Args:
        records: List of dicts with keys:
            user_id, user_name, email, roles, status,
            theoretical_license, d365_status.
    """
    result: list[dict[str, Any]] = []
    for r in records:
        result.append(
            {
                "user_id": r.get("user_id", "USR-001"),
                "user_name": r.get("user_name", "Test User"),
                "email": r.get("email", "test@contoso.com"),
                "roles": r.get("roles", []),
                "d365_status": r.get("d365_status", "Active"),
                "theoretical_license": r.get("theoretical_license", "Finance"),
            }
        )
    return result


# ---------------------------------------------------------------------------
# Test: M1 Ghost License -- Entra license but no D365 FO roles
# ---------------------------------------------------------------------------


class TestM1GhostLicense:
    """Test scenario: User has Entra D365 license but no D365 FO roles.

    This represents wasted spend -- the user is paying for a license
    they are not using in D365 FO.
    """

    def test_ghost_license_detected(self) -> None:
        """Entra license + zero D365 roles = M1_GHOST_LICENSE mismatch."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-GHOST",
                    "license_type": "Finance",
                    "sku_id": "guid-finance",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-GHOST",
                    "roles": [],
                    "theoretical_license": None,
                    "d365_status": "Active",
                }
            ]
        )

        result: EntraD365SyncReport = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        ghost = [m for m in result.mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE]
        assert len(ghost) >= 1
        assert ghost[0].user_id == "USR-GHOST"
        assert ghost[0].severity == "MEDIUM"

    def test_ghost_license_savings_calculated(self) -> None:
        """M1 Ghost License savings = full license cost (user pays for nothing)."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-GHOST",
                    "license_type": "Finance",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-GHOST",
                    "roles": [],
                    "theoretical_license": None,
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        ghost = [m for m in result.mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE]
        assert len(ghost) >= 1
        assert ghost[0].monthly_cost_impact == pytest.approx(180.0, abs=0.01)

    def test_ghost_license_recommendation(self) -> None:
        """M1 should recommend removing Entra license or assigning roles."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-GHOST",
                    "license_type": "Team Members",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-GHOST",
                    "roles": [],
                    "theoretical_license": None,
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        ghost = [m for m in result.mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE]
        assert len(ghost) >= 1
        assert ghost[0].recommendation is not None
        assert len(ghost[0].recommendation) > 0


# ---------------------------------------------------------------------------
# Test: M2 Compliance Gap -- D365 roles but no/wrong Entra license
# ---------------------------------------------------------------------------


class TestM2ComplianceGap:
    """Test scenario: User has D365 FO roles but no or wrong Entra license.

    This is a compliance risk -- the user is using D365 FO without proper
    licensing at the Entra level.
    """

    def test_missing_entra_license_detected(self) -> None:
        """D365 roles + no Entra license = M2_COMPLIANCE_GAP."""
        entra = _build_entra_licenses([])
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-GAP",
                    "roles": ["Accountant", "FinanceManager"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        gaps = [m for m in result.mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP]
        assert len(gaps) >= 1
        assert gaps[0].user_id == "USR-GAP"
        assert gaps[0].severity == "HIGH"

    def test_under_licensed_detected(self) -> None:
        """Entra tier < theoretical tier = M2_COMPLIANCE_GAP."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-UNDER",
                    "license_type": "Team Members",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-UNDER",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        gaps = [m for m in result.mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP]
        assert len(gaps) >= 1
        assert gaps[0].user_id == "USR-UNDER"
        assert gaps[0].severity == "HIGH"

    def test_compliance_gap_zero_savings(self) -> None:
        """M2 Compliance Gap has zero savings (it is a compliance issue, not cost)."""
        entra = _build_entra_licenses([])
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-GAP",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        gaps = [m for m in result.mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP]
        assert len(gaps) >= 1
        assert gaps[0].monthly_cost_impact == pytest.approx(0.0, abs=0.01)

    def test_matching_license_no_compliance_gap(self) -> None:
        """Entra license matching theoretical tier should NOT produce M2."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-OK",
                    "license_type": "Finance",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-OK",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        gaps = [
            m
            for m in result.mismatches
            if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP
            and m.user_id == "USR-OK"
        ]
        assert len(gaps) == 0


# ---------------------------------------------------------------------------
# Test: M3 Over-Provisioned -- Entra tier > theoretical D365 requirement
# ---------------------------------------------------------------------------


class TestM3OverProvisioned:
    """Test scenario: Entra license tier exceeds actual D365 FO need.

    User has an enterprise Entra license (Finance, $180/mo) but only
    needs Team Members ($60/mo) based on their D365 FO roles.
    """

    def test_over_provisioned_detected(self) -> None:
        """Entra Finance + D365 only needs Team Members = M3_OVER_PROVISIONED."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-OVER",
                    "license_type": "Finance",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-OVER",
                    "roles": ["BasicReader"],
                    "theoretical_license": "Team Members",
                    "d365_status": "Active",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        over = [
            m
            for m in result.mismatches
            if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED
        ]
        assert len(over) >= 1
        assert over[0].user_id == "USR-OVER"
        assert over[0].severity == "MEDIUM"

    def test_over_provisioned_savings(self) -> None:
        """M3 savings = difference between Entra tier cost and theoretical cost."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-OVER",
                    "license_type": "Finance",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-OVER",
                    "roles": ["BasicReader"],
                    "theoretical_license": "Team Members",
                    "d365_status": "Active",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        over = [
            m
            for m in result.mismatches
            if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED
        ]
        assert len(over) >= 1
        # Finance ($180) - Team Members ($60) = $120
        assert over[0].monthly_cost_impact == pytest.approx(120.0, abs=0.01)

    def test_same_tier_not_over_provisioned(self) -> None:
        """Same Entra tier and theoretical tier should NOT produce M3."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-MATCH",
                    "license_type": "Finance",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-MATCH",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        over = [
            m
            for m in result.mismatches
            if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED
            and m.user_id == "USR-MATCH"
        ]
        assert len(over) == 0


# ---------------------------------------------------------------------------
# Test: M4 Stale Entitlement -- Disabled D365 FO user with active Entra license
# ---------------------------------------------------------------------------


class TestM4StaleEntitlement:
    """Test scenario: D365 FO user is disabled but Entra license is still active.

    The user cannot log into D365 FO, yet the organization is still paying
    for the Entra license.
    """

    def test_stale_entitlement_detected(self) -> None:
        """Disabled D365 user + active Entra license = M4_STALE_ENTITLEMENT."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-STALE",
                    "license_type": "Finance",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-STALE",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Disabled",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        stale = [
            m
            for m in result.mismatches
            if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT
        ]
        assert len(stale) >= 1
        assert stale[0].user_id == "USR-STALE"
        assert stale[0].severity == "MEDIUM"

    def test_stale_entitlement_savings(self) -> None:
        """M4 savings = full Entra license cost (user is disabled)."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-STALE",
                    "license_type": "SCM",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-STALE",
                    "roles": [],
                    "theoretical_license": None,
                    "d365_status": "Disabled",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        stale = [
            m
            for m in result.mismatches
            if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT
        ]
        assert len(stale) >= 1
        assert stale[0].monthly_cost_impact == pytest.approx(180.0, abs=0.01)

    def test_active_user_not_stale(self) -> None:
        """Active D365 user should NOT produce M4_STALE_ENTITLEMENT."""
        entra = _build_entra_licenses(
            [
                {
                    "user_id": "USR-ACTIVE",
                    "license_type": "Finance",
                }
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-ACTIVE",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                    "d365_status": "Active",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        stale = [
            m
            for m in result.mismatches
            if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT
            and m.user_id == "USR-ACTIVE"
        ]
        assert len(stale) == 0


# ---------------------------------------------------------------------------
# Test: Multi-User Scenario
# ---------------------------------------------------------------------------


class TestMultiUserSync:
    """Test scenario: Multiple users with mixed mismatch types."""

    def test_multi_user_all_mismatch_types(self) -> None:
        """Process multiple users with different mismatch types."""
        entra = _build_entra_licenses(
            [
                # M1: Ghost (has Entra, no D365 roles)
                {"user_id": "USR-A", "license_type": "Finance"},
                # M3: Over-provisioned (Finance but needs Team Members)
                {"user_id": "USR-B", "license_type": "Finance"},
                # M4: Stale (disabled in D365)
                {"user_id": "USR-C", "license_type": "SCM"},
                # OK: Properly synced
                {"user_id": "USR-D", "license_type": "Finance"},
            ]
        )
        d365 = _build_d365_users(
            [
                {"user_id": "USR-A", "roles": [], "theoretical_license": None},
                {
                    "user_id": "USR-B",
                    "roles": ["BasicReader"],
                    "theoretical_license": "Team Members",
                },
                {
                    "user_id": "USR-C",
                    "roles": ["SCMPlanner"],
                    "theoretical_license": "SCM",
                    "d365_status": "Disabled",
                },
                {
                    "user_id": "USR-D",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                },
                # M2: Compliance gap (has D365 roles, no Entra license)
                {
                    "user_id": "USR-E",
                    "roles": ["Buyer"],
                    "theoretical_license": "SCM",
                },
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        types_found = {m.mismatch_type for m in result.mismatches}
        assert MismatchType.M1_GHOST_LICENSE in types_found
        assert MismatchType.M2_COMPLIANCE_GAP in types_found
        assert MismatchType.M3_OVER_PROVISIONED in types_found
        assert MismatchType.M4_STALE_ENTITLEMENT in types_found

    def test_total_savings_aggregated(self) -> None:
        """Report should aggregate total potential savings."""
        entra = _build_entra_licenses(
            [
                {"user_id": "USR-A", "license_type": "Finance"},
                {"user_id": "USR-B", "license_type": "Finance"},
            ]
        )
        d365 = _build_d365_users(
            [
                {"user_id": "USR-A", "roles": [], "theoretical_license": None},
                {
                    "user_id": "USR-B",
                    "roles": ["BasicReader"],
                    "theoretical_license": "Team Members",
                },
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        # USR-A Ghost: $180 savings, USR-B Over-provisioned: $120 savings
        assert result.total_monthly_savings == pytest.approx(300.0, abs=0.01)
        assert result.total_annual_savings == pytest.approx(3600.0, abs=0.01)


# ---------------------------------------------------------------------------
# Test: Sorting -- HIGH severity first, then savings descending
# ---------------------------------------------------------------------------


class TestSorting:
    """Test scenario: Mismatches sorted by severity then savings."""

    def test_high_severity_before_medium(self) -> None:
        """HIGH severity mismatches should come before MEDIUM severity."""
        entra = _build_entra_licenses(
            [
                # M1 Ghost (MEDIUM)
                {"user_id": "USR-GHOST", "license_type": "Finance"},
            ]
        )
        d365 = _build_d365_users(
            [
                {"user_id": "USR-GHOST", "roles": [], "theoretical_license": None},
                # M2 Compliance Gap (HIGH)
                {
                    "user_id": "USR-GAP",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                },
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        if len(result.mismatches) >= 2:
            # HIGH severity items should come first
            first = result.mismatches[0]
            assert first.severity == "HIGH"


# ---------------------------------------------------------------------------
# Test: Empty Input Handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test scenario: Empty input data."""

    def test_empty_entra_and_d365(self) -> None:
        """No users at all should produce empty report."""
        result = validate_entra_d365_sync(
            entra_licenses=[],
            d365_users=[],
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        assert len(result.mismatches) == 0
        assert result.total_monthly_savings == pytest.approx(0.0, abs=0.01)
        assert result.total_annual_savings == pytest.approx(0.0, abs=0.01)

    def test_empty_entra_with_d365_users(self) -> None:
        """D365 users with no Entra licenses = compliance gaps."""
        entra = _build_entra_licenses([])
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-001",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        gaps = [m for m in result.mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP]
        assert len(gaps) >= 1

    def test_entra_only_no_d365(self) -> None:
        """Entra licenses with no D365 users = ghost licenses."""
        entra = _build_entra_licenses(
            [
                {"user_id": "USR-001", "license_type": "Finance"},
            ]
        )
        d365 = _build_d365_users([])

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        ghost = [m for m in result.mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE]
        assert len(ghost) >= 1


# ---------------------------------------------------------------------------
# Test: Report Model Structure
# ---------------------------------------------------------------------------


class TestReportModelStructure:
    """Test scenario: Verify report and mismatch have required fields."""

    def test_mismatch_has_required_fields(self) -> None:
        """MismatchRecord should have all spec-required fields."""
        entra = _build_entra_licenses(
            [{"user_id": "USR-FIELD", "license_type": "Finance"}]
        )
        d365 = _build_d365_users(
            [{"user_id": "USR-FIELD", "roles": [], "theoretical_license": None}]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        assert len(result.mismatches) >= 1
        item = result.mismatches[0]
        assert hasattr(item, "user_id")
        assert hasattr(item, "user_name")
        assert hasattr(item, "mismatch_type")
        assert hasattr(item, "entra_license")
        assert hasattr(item, "d365_theoretical_license")
        assert hasattr(item, "d365_roles")
        assert hasattr(item, "d365_status")
        assert hasattr(item, "severity")
        assert hasattr(item, "monthly_cost_impact")
        assert hasattr(item, "recommendation")

    def test_report_has_summary_fields(self) -> None:
        """EntraD365SyncReport should have summary aggregation fields."""
        result = validate_entra_d365_sync(
            entra_licenses=[],
            d365_users=[],
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        assert hasattr(result, "algorithm_id")
        assert hasattr(result, "mismatches")
        assert hasattr(result, "total_monthly_savings")
        assert hasattr(result, "total_annual_savings")
        assert hasattr(result, "ghost_count")
        assert hasattr(result, "compliance_gap_count")
        assert hasattr(result, "over_provisioned_count")
        assert hasattr(result, "stale_count")
        assert hasattr(result, "total_users_analyzed")


# ---------------------------------------------------------------------------
# Test: Algorithm Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id is '3.9'."""

    def test_algorithm_id_is_3_9(self) -> None:
        """EntraD365SyncReport should carry algorithm_id '3.9'."""
        result = validate_entra_d365_sync(
            entra_licenses=[],
            d365_users=[],
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        assert result.algorithm_id == "3.9"


# ---------------------------------------------------------------------------
# Test: Counts by Mismatch Type
# ---------------------------------------------------------------------------


class TestMismatchCounts:
    """Test scenario: Verify mismatch counts in report summary."""

    def test_counts_reflect_mismatches(self) -> None:
        """Report summary counts should match actual mismatch list."""
        entra = _build_entra_licenses(
            [
                {"user_id": "USR-A", "license_type": "Finance"},
                {"user_id": "USR-B", "license_type": "SCM"},
            ]
        )
        d365 = _build_d365_users(
            [
                # USR-A: ghost (no roles)
                {"user_id": "USR-A", "roles": [], "theoretical_license": None},
                # USR-B: stale (disabled)
                {
                    "user_id": "USR-B",
                    "roles": [],
                    "theoretical_license": None,
                    "d365_status": "Disabled",
                },
                # USR-C: compliance gap (has D365 roles, no Entra)
                {
                    "user_id": "USR-C",
                    "roles": ["Buyer"],
                    "theoretical_license": "SCM",
                },
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        ghost_actual = len(
            [m for m in result.mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE]
        )
        gap_actual = len(
            [m for m in result.mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP]
        )
        over_actual = len(
            [m for m in result.mismatches if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED]
        )
        stale_actual = len(
            [m for m in result.mismatches if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT]
        )

        assert result.ghost_count == ghost_actual
        assert result.compliance_gap_count == gap_actual
        assert result.over_provisioned_count == over_actual
        assert result.stale_count == stale_actual


# ---------------------------------------------------------------------------
# Test: D365 Users without roles not flagged as M2
# ---------------------------------------------------------------------------


class TestNoRolesNoComplianceGap:
    """Users with no D365 roles and no Entra license = no mismatch."""

    def test_no_roles_no_entra_no_mismatch(self) -> None:
        """User with no roles and no Entra license is not a mismatch."""
        entra = _build_entra_licenses([])
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-EMPTY",
                    "roles": [],
                    "theoretical_license": None,
                }
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        user_mismatches = [m for m in result.mismatches if m.user_id == "USR-EMPTY"]
        assert len(user_mismatches) == 0


# ---------------------------------------------------------------------------
# Test: Perfectly Synced Users -- No Mismatches
# ---------------------------------------------------------------------------


class TestPerfectSync:
    """Test scenario: All users perfectly synced between Entra and D365."""

    def test_all_synced_no_mismatches(self) -> None:
        """All users match: no mismatches produced."""
        entra = _build_entra_licenses(
            [
                {"user_id": "USR-1", "license_type": "Finance"},
                {"user_id": "USR-2", "license_type": "Team Members"},
            ]
        )
        d365 = _build_d365_users(
            [
                {
                    "user_id": "USR-1",
                    "roles": ["Accountant"],
                    "theoretical_license": "Finance",
                },
                {
                    "user_id": "USR-2",
                    "roles": ["BasicReader"],
                    "theoretical_license": "Team Members",
                },
            ]
        )

        result = validate_entra_d365_sync(
            entra_licenses=entra,
            d365_users=d365,
            sku_mapping=DEFAULT_SKU_MAP,
            pricing_config=DEFAULT_PRICING,
        )

        assert len(result.mismatches) == 0
        assert result.total_monthly_savings == pytest.approx(0.0, abs=0.01)
