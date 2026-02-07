"""Algorithm 3.9: Entra-D365 License Sync Validator.

Detects mismatches between tenant-level Entra ID licensing and D365 FO
role-based licensing. Licenses exist at two independent levels (Entra ID
managed by IT/Identity, D365 FO managed by functional admins) that can
drift out of sync.

Business Value:
  - Cost Recovery: Detect ghost licenses (Entra license assigned, no D365 FO roles)
  - Compliance: Detect users with D365 FO roles but missing/wrong Entra license
  - Over-Provisioning: Detect users with enterprise Entra license who only need
    Team Members
  - Stale Entitlements: Detect disabled D365 FO users still consuming Entra licenses

Mismatch Types:
  - M1 Ghost License: Entra license present, zero D365 FO roles
  - M2 Compliance Gap: D365 FO roles present, no/wrong Entra license
  - M3 Over-Provisioned: Entra license tier > theoretical D365 requirement
  - M4 Stale Entitlement: D365 FO user disabled, Entra license still active

Input Data Required:
  - EntraLicenseData: Per-user assigned licenses from Microsoft Graph API
  - D365 Users: User records with role assignments and theoretical license
  - SKU Mapping: Entra SKU ID to D365 FO license type
  - Pricing Config: License pricing for savings calculation

See Requirements/07-Advanced-Algorithms-Expansion.md, Algorithm 3.9.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# License tier priority map -- used to compare license levels
# Higher value = more capable / more expensive license
# ---------------------------------------------------------------------------

_LICENSE_TIER_PRIORITY: dict[str, int] = {
    "Team Members": 60,
    "Operations": 90,
    "Finance": 180,
    "SCM": 180,
    "Commerce": 180,
}

_SEVERITY_SORT_ORDER: dict[str, int] = {
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
}


class MismatchType(str, Enum):
    """Types of Entra-D365 license mismatches."""

    M1_GHOST_LICENSE = "M1_GHOST_LICENSE"
    M2_COMPLIANCE_GAP = "M2_COMPLIANCE_GAP"
    M3_OVER_PROVISIONED = "M3_OVER_PROVISIONED"
    M4_STALE_ENTITLEMENT = "M4_STALE_ENTITLEMENT"


@dataclass
class MismatchRecord:
    """A single Entra-D365 license sync mismatch.

    Attributes:
        user_id: User identifier.
        user_name: User display name.
        mismatch_type: One of M1/M2/M3/M4.
        entra_license: Entra SKU license type (or None if absent).
        d365_theoretical_license: Theoretical license from D365 FO roles (or None).
        d365_roles: List of D365 FO role names.
        d365_status: D365 FO user status (Active/Disabled).
        severity: HIGH or MEDIUM.
        monthly_cost_impact: Monthly savings or compliance cost impact (USD).
        recommendation: Remediation action text.
    """

    user_id: str
    user_name: str
    mismatch_type: MismatchType
    entra_license: str | None
    d365_theoretical_license: str | None
    d365_roles: list[str]
    d365_status: str
    severity: str
    monthly_cost_impact: float
    recommendation: str


@dataclass
class EntraD365SyncReport:
    """Complete output from Algorithm 3.9: Entra-D365 License Sync Validator.

    Attributes:
        algorithm_id: Always "3.9".
        mismatches: List of detected mismatches.
        total_monthly_savings: Sum of monthly cost impacts across all mismatches.
        total_annual_savings: total_monthly_savings * 12.
        ghost_count: Count of M1 mismatches.
        compliance_gap_count: Count of M2 mismatches.
        over_provisioned_count: Count of M3 mismatches.
        stale_count: Count of M4 mismatches.
        total_users_analyzed: Number of unique users processed.
    """

    algorithm_id: str = "3.9"
    mismatches: list[MismatchRecord] = field(default_factory=list)
    total_monthly_savings: float = 0.0
    total_annual_savings: float = 0.0
    ghost_count: int = 0
    compliance_gap_count: int = 0
    over_provisioned_count: int = 0
    stale_count: int = 0
    total_users_analyzed: int = 0


def _get_license_price(pricing_config: dict[str, Any], license_name: str) -> float:
    """Retrieve monthly price for a license type from pricing config.

    Uses the shared pricing utility fallback strategy:
      Tier 1 - Exact match
      Tier 2 - Normalized key match (lowercase + underscores)
      Tier 3 - Case-insensitive iteration

    Args:
        pricing_config: Parsed pricing.json dictionary with ``licenses`` key.
        license_name: License type name.

    Returns:
        Monthly price in USD. Returns 0.0 if license not found.
    """
    from ..utils.pricing import get_license_price as _shared_get_price

    try:
        return _shared_get_price(pricing_config, license_name)
    except KeyError:
        return 0.0


def _get_tier_priority(license_name: str | None) -> int:
    """Get the tier priority for a license type.

    Higher value = more capable/expensive license.

    Args:
        license_name: License type name (e.g., "Finance", "Team Members").

    Returns:
        Priority integer. Returns 0 for None or unknown licenses.
    """
    if license_name is None:
        return 0
    return _LICENSE_TIER_PRIORITY.get(license_name, 0)


def validate_entra_d365_sync(
    entra_licenses: list[dict[str, Any]],
    d365_users: list[dict[str, Any]],
    sku_mapping: dict[str, str],
    pricing_config: dict[str, Any],
) -> EntraD365SyncReport:
    """Validate Entra ID and D365 FO license synchronization.

    Compares per-user Entra ID licenses against D365 FO role-based
    theoretical licenses to detect four types of mismatches:

      M1 Ghost License: Entra license present, no D365 FO roles.
      M2 Compliance Gap: D365 FO roles present, no/under Entra license.
      M3 Over-Provisioned: Entra license tier exceeds D365 FO need.
      M4 Stale Entitlement: D365 FO user disabled, Entra license active.

    Args:
        entra_licenses: List of Entra license records. Each dict must have:
            user_id, user_name, email, sku_id, sku_name, license_type,
            account_enabled.
        d365_users: List of D365 FO user records. Each dict must have:
            user_id, user_name, email, roles (list[str]),
            d365_status ("Active"/"Disabled"),
            theoretical_license (str or None).
        sku_mapping: Map of Entra SKU GUID to D365 FO license type name.
        pricing_config: Parsed pricing.json for cost calculations.

    Returns:
        EntraD365SyncReport with all detected mismatches, sorted by
        severity (HIGH first) then monthly_cost_impact descending.
    """
    mismatches: list[MismatchRecord] = []

    # Build lookup maps -- O(N) construction for O(1) access
    entra_map: dict[str, dict[str, Any]] = {}
    for record in entra_licenses:
        entra_map[record["user_id"]] = record

    d365_map: dict[str, dict[str, Any]] = {}
    for record in d365_users:
        d365_map[record["user_id"]] = record

    # Collect all unique user IDs
    all_user_ids: set[str] = set(entra_map.keys()) | set(d365_map.keys())

    # --- Pass 1: Check all Entra-licensed users ---
    for user_id, entra_record in entra_map.items():
        entra_license: str = entra_record["license_type"]
        user_name: str = entra_record.get("user_name", "")
        d365_record = d365_map.get(user_id)

        # Determine D365 status and roles
        d365_status: str = "Active"
        d365_roles: list[str] = []
        theoretical_license: str | None = None

        if d365_record is not None:
            d365_status = d365_record.get("d365_status", "Active")
            d365_roles = d365_record.get("roles", [])
            theoretical_license = d365_record.get("theoretical_license")

        # M4: Stale Entitlement -- D365 FO user disabled but Entra license active
        # Check M4 FIRST because disabled user trumps other checks
        if d365_status == "Disabled":
            entra_cost = _get_license_price(pricing_config, entra_license)
            mismatches.append(
                MismatchRecord(
                    user_id=user_id,
                    user_name=user_name,
                    mismatch_type=MismatchType.M4_STALE_ENTITLEMENT,
                    entra_license=entra_license,
                    d365_theoretical_license=theoretical_license,
                    d365_roles=d365_roles,
                    d365_status=d365_status,
                    severity="MEDIUM",
                    monthly_cost_impact=entra_cost,
                    recommendation=(
                        f"Remove Entra license (user disabled in D365 FO). "
                        f"Saves ${entra_cost:.2f}/month."
                    ),
                )
            )
            continue  # Skip further checks for disabled users

        # M1: Ghost License -- Entra license but no D365 FO roles
        has_no_roles = len(d365_roles) == 0
        if has_no_roles:
            entra_cost = _get_license_price(pricing_config, entra_license)
            mismatches.append(
                MismatchRecord(
                    user_id=user_id,
                    user_name=user_name,
                    mismatch_type=MismatchType.M1_GHOST_LICENSE,
                    entra_license=entra_license,
                    d365_theoretical_license=None,
                    d365_roles=[],
                    d365_status=d365_status,
                    severity="MEDIUM",
                    monthly_cost_impact=entra_cost,
                    recommendation=(
                        f"Remove Entra {entra_license} license or assign D365 FO roles. "
                        f"Saves ${entra_cost:.2f}/month."
                    ),
                )
            )
            continue  # Ghost means no roles, so no M3 possible

        # M3: Over-Provisioned -- Entra license tier > theoretical
        entra_tier = _get_tier_priority(entra_license)
        theoretical_tier = _get_tier_priority(theoretical_license)

        if theoretical_license is not None and entra_tier > theoretical_tier:
            entra_cost = _get_license_price(pricing_config, entra_license)
            theoretical_cost = _get_license_price(pricing_config, theoretical_license)
            tier_diff = entra_cost - theoretical_cost
            mismatches.append(
                MismatchRecord(
                    user_id=user_id,
                    user_name=user_name,
                    mismatch_type=MismatchType.M3_OVER_PROVISIONED,
                    entra_license=entra_license,
                    d365_theoretical_license=theoretical_license,
                    d365_roles=d365_roles,
                    d365_status=d365_status,
                    severity="MEDIUM",
                    monthly_cost_impact=tier_diff,
                    recommendation=(
                        f"Downgrade Entra license from {entra_license} to "
                        f"{theoretical_license}. Saves ${tier_diff:.2f}/month."
                    ),
                )
            )

    # --- Pass 2: Check all D365 FO users with roles for M2 ---
    for user_id, d365_record in d365_map.items():
        d365_roles = d365_record.get("roles", [])
        d365_status = d365_record.get("d365_status", "Active")
        theoretical_license = d365_record.get("theoretical_license")
        user_name = d365_record.get("user_name", "")

        # Skip users without roles (no compliance requirement)
        if not d365_roles:
            continue

        # Skip disabled users (already handled in M4)
        if d365_status == "Disabled":
            continue

        entra_record = entra_map.get(user_id)

        if entra_record is None:
            # M2: Compliance Gap -- has D365 roles but NO Entra license
            mismatches.append(
                MismatchRecord(
                    user_id=user_id,
                    user_name=user_name,
                    mismatch_type=MismatchType.M2_COMPLIANCE_GAP,
                    entra_license=None,
                    d365_theoretical_license=theoretical_license,
                    d365_roles=d365_roles,
                    d365_status=d365_status,
                    severity="HIGH",
                    monthly_cost_impact=0.0,
                    recommendation=(
                        f"Assign Entra license: {theoretical_license}. "
                        f"User has D365 FO roles but no Entra license."
                    ),
                )
            )
        else:
            # Check if Entra tier is LOWER than theoretical (under-licensed)
            entra_license = entra_record["license_type"]
            entra_tier = _get_tier_priority(entra_license)
            theoretical_tier = _get_tier_priority(theoretical_license)

            if theoretical_license is not None and entra_tier < theoretical_tier:
                mismatches.append(
                    MismatchRecord(
                        user_id=user_id,
                        user_name=user_name,
                        mismatch_type=MismatchType.M2_COMPLIANCE_GAP,
                        entra_license=entra_license,
                        d365_theoretical_license=theoretical_license,
                        d365_roles=d365_roles,
                        d365_status=d365_status,
                        severity="HIGH",
                        monthly_cost_impact=0.0,
                        recommendation=(
                            f"Upgrade Entra license from {entra_license} to "
                            f"{theoretical_license}. Current license is insufficient "
                            f"for assigned D365 FO roles."
                        ),
                    )
                )

    # Sort: HIGH severity first, then by monthly_cost_impact descending
    mismatches.sort(
        key=lambda m: (
            _SEVERITY_SORT_ORDER.get(m.severity, 99),
            -m.monthly_cost_impact,
        )
    )

    # Build summary counts
    ghost_count = sum(1 for m in mismatches if m.mismatch_type == MismatchType.M1_GHOST_LICENSE)
    gap_count = sum(1 for m in mismatches if m.mismatch_type == MismatchType.M2_COMPLIANCE_GAP)
    over_count = sum(
        1 for m in mismatches if m.mismatch_type == MismatchType.M3_OVER_PROVISIONED
    )
    stale_count = sum(
        1 for m in mismatches if m.mismatch_type == MismatchType.M4_STALE_ENTITLEMENT
    )
    total_monthly = sum(m.monthly_cost_impact for m in mismatches)

    return EntraD365SyncReport(
        algorithm_id="3.9",
        mismatches=mismatches,
        total_monthly_savings=total_monthly,
        total_annual_savings=total_monthly * 12,
        ghost_count=ghost_count,
        compliance_gap_count=gap_count,
        over_provisioned_count=over_count,
        stale_count=stale_count,
        total_users_analyzed=len(all_user_ids),
    )
