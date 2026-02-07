"""Algorithm 5.4: Contractor Access Tracker.

Monitors contractor/external user access to ensure compliance with contract
terms and organizational security policies. Detects expired access, zombie
accounts, and excessive privileges for external users.

Business Value:
  - Compliance: Ensure contractor access is revoked when contracts end
  - Cost Savings: Identify wasted licenses on inactive/expired contractors
  - Security: Flag contractors with excessive privileges
  - Proactive: Notify of upcoming contract expirations for review

Finding Types:
  - EXPIRED_CONTRACT_ACTIVE_ACCESS (CRITICAL): Access beyond contract end + recent usage
  - EXPIRED_CONTRACT_NO_ACTIVITY (HIGH): Access beyond contract end, no recent usage
  - INACTIVE_CONTRACTOR (MEDIUM): Valid contract but no usage in N days
  - HIGH_PRIVILEGE_CONTRACTOR (MEDIUM): Contractor with high-privilege roles
  - CONTRACT_EXPIRING_SOON (LOW): Contract ending within N days

See Requirements/07-Advanced-Algorithms-Expansion.md, Algorithm 5.4.
See Requirements/08-Algorithm-Review-Summary.md.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

import pandas as pd
from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    """Severity levels for contractor access findings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Severity ordering for sorting (lower number = higher severity)
_SEVERITY_ORDER: dict[FindingSeverity, int] = {
    FindingSeverity.CRITICAL: 0,
    FindingSeverity.HIGH: 1,
    FindingSeverity.MEDIUM: 2,
    FindingSeverity.LOW: 3,
}


class ContractorAccessFinding(BaseModel):
    """Individual finding from contractor access analysis."""

    user_id: str = Field(description="Contractor user identifier")
    user_name: str = Field(description="Contractor display name")
    finding_type: str = Field(
        description="Type of finding: EXPIRED_CONTRACT_ACTIVE_ACCESS, "
        "EXPIRED_CONTRACT_NO_ACTIVITY, INACTIVE_CONTRACTOR, "
        "HIGH_PRIVILEGE_CONTRACTOR, CONTRACT_EXPIRING_SOON"
    )
    severity: FindingSeverity = Field(description="Finding severity level")
    description: str = Field(description="Human-readable finding description")
    recommendation: str = Field(description="Recommended remediation action")
    monthly_cost_impact: float = Field(
        description="Monthly license cost at risk (USD)", ge=0
    )
    contract_end: str = Field(description="Contract end date (ISO 8601)")
    days_overdue: int | None = Field(
        default=None,
        description="Days past contract end (for expired findings)",
    )
    days_until_expiry: int | None = Field(
        default=None,
        description="Days until contract expires (for expiring-soon findings)",
    )


class ContractorAccessReport(BaseModel):
    """Complete output from Algorithm 5.4: Contractor Access Tracker."""

    algorithm_id: str = Field(default="5.4", description="Algorithm identifier")
    total_contractors_analyzed: int = Field(
        description="Number of contractors analyzed", ge=0
    )
    total_findings: int = Field(
        description="Total number of findings", ge=0
    )
    findings: list[ContractorAccessFinding] = Field(
        description="List of contractor access findings",
        default_factory=list,
    )
    critical_count: int = Field(
        default=0, description="Number of CRITICAL findings", ge=0
    )
    high_count: int = Field(
        default=0, description="Number of HIGH findings", ge=0
    )
    medium_count: int = Field(
        default=0, description="Number of MEDIUM findings", ge=0
    )
    low_count: int = Field(
        default=0, description="Number of LOW findings", ge=0
    )
    total_monthly_cost_impact: float = Field(
        default=0.0,
        description="Total monthly cost impact across all findings (USD)",
        ge=0,
    )


def track_contractor_access(
    contractor_records: pd.DataFrame,
    user_activity: pd.DataFrame,
    inactivity_threshold_days: int = 30,
    expiry_warning_days: int = 30,
    reference_date: datetime | None = None,
) -> ContractorAccessReport:
    """Track contractor access for compliance and cost optimization.

    Analyzes contractor user records against their activity data and
    contract dates to identify compliance risks and cost waste.

    Args:
        contractor_records: DataFrame with columns:
            - user_id: Contractor user identifier
            - user_name: Display name
            - email: Email address
            - user_type: "Contractor" or similar
            - contract_start: Contract start date (ISO 8601)
            - contract_end: Contract end date (ISO 8601)
            - department: Department
            - roles: Assigned roles (comma-separated or single)
            - is_high_privilege: Whether any role is high-privilege
            - license_type: License type name
            - license_cost_monthly: Monthly license cost
            - status: "Active" or "Inactive"
        user_activity: DataFrame with columns:
            - user_id: User identifier
            - timestamp: Activity timestamp (ISO 8601)
            - menu_item: Menu item accessed
            - action: Action performed (Read/Write/etc.)
        inactivity_threshold_days: Days without activity to flag as inactive
            (default 30).
        expiry_warning_days: Days before contract end to trigger warning
            (default 30).
        reference_date: Date to use as "now" for calculations (default:
            datetime.utcnow()). Primarily for testability.

    Returns:
        ContractorAccessReport with findings sorted by severity then cost.
    """
    if reference_date is None:
        reference_date = datetime.utcnow()

    findings: list[ContractorAccessFinding] = []

    if contractor_records.empty:
        return ContractorAccessReport(
            total_contractors_analyzed=0,
            total_findings=0,
            findings=[],
        )

    # Pre-build activity lookup: user_id -> latest activity timestamp
    latest_activity: dict[str, datetime] = {}
    if not user_activity.empty:
        user_activity = user_activity.copy()
        user_activity["_parsed_ts"] = pd.to_datetime(user_activity["timestamp"])
        for uid, group in user_activity.groupby("user_id"):
            latest_activity[str(uid)] = group["_parsed_ts"].max().to_pydatetime()

    total_analyzed = 0

    for _, row in contractor_records.iterrows():
        user_id: str = str(row["user_id"])
        user_name: str = str(row["user_name"])
        status: str = str(row["status"])
        contract_end_str: str = str(row["contract_end"])
        license_cost: float = float(row["license_cost_monthly"])
        is_high_privilege: bool = bool(row["is_high_privilege"])

        # Skip inactive/disabled contractors (already deprovisioned)
        if status != "Active":
            continue

        total_analyzed += 1

        # Parse contract end date
        try:
            contract_end = datetime.fromisoformat(contract_end_str)
        except (ValueError, TypeError):
            continue

        # Determine if contract is expired
        is_expired = contract_end < reference_date
        days_overdue = (reference_date - contract_end).days if is_expired else 0

        # Determine last activity
        user_last_activity = latest_activity.get(user_id)
        has_recent_activity = False
        if user_last_activity is not None:
            # Ensure timezone-naive comparison
            if user_last_activity.tzinfo is not None:
                user_last_activity = user_last_activity.replace(tzinfo=None)
            days_since_activity = (reference_date - user_last_activity).days
            has_recent_activity = days_since_activity <= inactivity_threshold_days
        else:
            days_since_activity = None

        has_any_activity = user_last_activity is not None

        # --- Finding: EXPIRED_CONTRACT_ACTIVE_ACCESS (CRITICAL) ---
        if is_expired and has_any_activity:
            # Check if activity happened at all (even if not "recent")
            # The key issue is: expired contract + account still active
            findings.append(
                ContractorAccessFinding(
                    user_id=user_id,
                    user_name=user_name,
                    finding_type="EXPIRED_CONTRACT_ACTIVE_ACCESS",
                    severity=FindingSeverity.CRITICAL,
                    description=(
                        f"Contractor {user_name} ({user_id}) has an expired "
                        f"contract (ended {contract_end_str}) but still has "
                        f"active system access. Contract expired {days_overdue} "
                        f"days ago."
                    ),
                    recommendation=(
                        "IMMEDIATE ACTION: Revoke all system access for this "
                        "contractor. Contract has expired and access should "
                        "have been deprovisioned."
                    ),
                    monthly_cost_impact=license_cost,
                    contract_end=contract_end_str,
                    days_overdue=days_overdue,
                )
            )
            continue  # Expired + active is the top finding; skip other checks

        # --- Finding: EXPIRED_CONTRACT_NO_ACTIVITY (HIGH) ---
        if is_expired and not has_any_activity:
            findings.append(
                ContractorAccessFinding(
                    user_id=user_id,
                    user_name=user_name,
                    finding_type="EXPIRED_CONTRACT_NO_ACTIVITY",
                    severity=FindingSeverity.HIGH,
                    description=(
                        f"Contractor {user_name} ({user_id}) has an expired "
                        f"contract (ended {contract_end_str}) and still has an "
                        f"active account. No recent activity detected. "
                        f"Contract expired {days_overdue} days ago."
                    ),
                    recommendation=(
                        "Deprovision contractor account. Contract has expired "
                        "and account is consuming a license unnecessarily."
                    ),
                    monthly_cost_impact=license_cost,
                    contract_end=contract_end_str,
                    days_overdue=days_overdue,
                )
            )
            continue

        # --- Non-expired contract checks ---

        # Days until contract expiry
        days_until_expiry = (contract_end - reference_date).days

        # --- Finding: HIGH_PRIVILEGE_CONTRACTOR (MEDIUM) ---
        if is_high_privilege:
            findings.append(
                ContractorAccessFinding(
                    user_id=user_id,
                    user_name=user_name,
                    finding_type="HIGH_PRIVILEGE_CONTRACTOR",
                    severity=FindingSeverity.MEDIUM,
                    description=(
                        f"Contractor {user_name} ({user_id}) is assigned "
                        f"high-privilege roles. Contractors should generally "
                        f"have minimal access permissions."
                    ),
                    recommendation=(
                        "Review contractor's role assignments. Consider "
                        "downgrading to least-privilege access appropriate "
                        "for their contract scope."
                    ),
                    monthly_cost_impact=license_cost,
                    contract_end=contract_end_str,
                )
            )

        # --- Finding: INACTIVE_CONTRACTOR (MEDIUM) ---
        if not has_recent_activity and not is_expired:
            # Only flag if they have no recent activity
            # (either no activity at all, or activity older than threshold)
            if days_since_activity is None or days_since_activity > inactivity_threshold_days:
                findings.append(
                    ContractorAccessFinding(
                        user_id=user_id,
                        user_name=user_name,
                        finding_type="INACTIVE_CONTRACTOR",
                        severity=FindingSeverity.MEDIUM,
                        description=(
                            f"Contractor {user_name} ({user_id}) has a valid "
                            f"contract (ends {contract_end_str}) but has not "
                            f"accessed the system in over "
                            f"{inactivity_threshold_days} days. "
                            f"License may be wasted."
                        ),
                        recommendation=(
                            "Review whether this contractor still requires "
                            "system access. Consider suspending the account "
                            "to save license costs until access is needed."
                        ),
                        monthly_cost_impact=license_cost,
                        contract_end=contract_end_str,
                    )
                )

        # --- Finding: CONTRACT_EXPIRING_SOON (LOW) ---
        if 0 < days_until_expiry <= expiry_warning_days:
            findings.append(
                ContractorAccessFinding(
                    user_id=user_id,
                    user_name=user_name,
                    finding_type="CONTRACT_EXPIRING_SOON",
                    severity=FindingSeverity.LOW,
                    description=(
                        f"Contractor {user_name} ({user_id}) has a contract "
                        f"expiring in {days_until_expiry} days "
                        f"({contract_end_str}). Plan for contract renewal "
                        f"or access deprovisioning."
                    ),
                    recommendation=(
                        "Confirm with contract manager whether this contractor's "
                        "contract will be renewed. If not, prepare access "
                        "revocation for the contract end date."
                    ),
                    monthly_cost_impact=0.0,  # Not yet a cost issue
                    contract_end=contract_end_str,
                    days_until_expiry=days_until_expiry,
                )
            )

    # Sort findings: by severity (CRITICAL first), then by cost impact descending
    findings.sort(
        key=lambda f: (
            _SEVERITY_ORDER.get(f.severity, 99),
            -f.monthly_cost_impact,
        )
    )

    # Count by severity
    critical_count = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
    high_count = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
    medium_count = sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM)
    low_count = sum(1 for f in findings if f.severity == FindingSeverity.LOW)

    total_monthly_cost = sum(f.monthly_cost_impact for f in findings)

    return ContractorAccessReport(
        total_contractors_analyzed=total_analyzed,
        total_findings=len(findings),
        findings=findings,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        total_monthly_cost_impact=total_monthly_cost,
    )
