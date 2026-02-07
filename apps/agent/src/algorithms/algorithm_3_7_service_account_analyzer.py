"""Algorithm 3.7: Service Account Analyzer.

Analyzes service account usage patterns and security posture to identify
governance, credential, and privilege risks.

Detection categories:
- Interactive login patterns (HIGH risk) - credential compromise indicator
- Missing ownership (HIGH risk) - governance gap
- Stale/inactive accounts (MEDIUM risk) - 90+ days no activity
- Admin-level privileges (HIGH risk) - excessive permissions
- Credential rotation overdue (MEDIUM risk) - 90+ days since last rotation

See Requirements/07-Advanced-Algorithms-Expansion.md (Algorithm 3.7).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class ServiceAccountConfig(BaseModel):
    """Configurable thresholds for service account analysis."""

    stale_threshold_days: int = Field(
        default=90,
        description="Days without activity before an account is considered stale",
        ge=1,
    )
    credential_rotation_max_days: int = Field(
        default=90,
        description="Maximum days between credential rotations",
        ge=1,
    )
    reference_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Reference date for staleness/credential age calculations",
    )


# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------


class ServiceAccountFinding(BaseModel):
    """Individual finding for a service account."""

    account_id: str = Field(description="Service account identifier")
    account_name: str = Field(
        default="", description="Service account display name"
    )
    finding_type: str = Field(
        description=(
            "Category of finding: INTERACTIVE_LOGIN, NO_OWNER, "
            "STALE_ACCOUNT, EXCESSIVE_PRIVILEGE, CREDENTIAL_ROTATION"
        )
    )
    risk_level: str = Field(description="Risk level: CRITICAL, HIGH, MEDIUM, LOW")
    risk_score: int = Field(
        description="Numeric risk contribution (0-100)", ge=0
    )
    description: str = Field(description="Human-readable finding description")
    recommendation: str = Field(description="Recommended remediation action")


class ServiceAccountSummary(BaseModel):
    """Aggregated risk summary for a single service account."""

    account_id: str = Field(description="Service account identifier")
    account_name: str = Field(
        default="", description="Service account display name"
    )
    risk_score: int = Field(
        description="Aggregated risk score across all findings", ge=0
    )
    finding_count: int = Field(
        description="Number of findings for this account", ge=0
    )
    highest_risk_level: str = Field(
        default="LOW",
        description="Highest risk level among findings",
    )


class ServiceAccountAnalysis(BaseModel):
    """Complete output from Algorithm 3.7: Service Account Analyzer."""

    algorithm_id: str = Field(default="3.7", description="Algorithm identifier")
    total_accounts_analyzed: int = Field(
        description="Total service accounts evaluated", ge=0
    )
    total_findings: int = Field(description="Total findings generated", ge=0)
    high_risk_count: int = Field(
        description="Count of HIGH/CRITICAL findings", ge=0
    )
    medium_risk_count: int = Field(
        description="Count of MEDIUM findings", ge=0
    )
    low_risk_count: int = Field(
        description="Count of LOW findings", ge=0, default=0
    )
    findings: list[ServiceAccountFinding] = Field(
        default_factory=list, description="All findings sorted by risk"
    )
    account_summaries: list[ServiceAccountSummary] = Field(
        default_factory=list,
        description="Per-account summaries sorted by risk score descending",
    )


# ---------------------------------------------------------------------------
# Risk score weights per finding type
# ---------------------------------------------------------------------------

_RISK_SCORES: dict[str, int] = {
    "INTERACTIVE_LOGIN": 30,
    "NO_OWNER": 25,
    "EXCESSIVE_PRIVILEGE": 25,
    "STALE_ACCOUNT": 15,
    "CREDENTIAL_ROTATION": 10,
}

_RISK_LEVELS: dict[str, str] = {
    "INTERACTIVE_LOGIN": "HIGH",
    "NO_OWNER": "HIGH",
    "EXCESSIVE_PRIVILEGE": "HIGH",
    "STALE_ACCOUNT": "MEDIUM",
    "CREDENTIAL_ROTATION": "MEDIUM",
}

_RISK_LEVEL_ORDER: dict[str, int] = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}


# ---------------------------------------------------------------------------
# Core Analysis Function
# ---------------------------------------------------------------------------


def analyze_service_accounts(
    service_account_inventory: pd.DataFrame,
    user_activity: pd.DataFrame,
    login_history: pd.DataFrame,
    config: ServiceAccountConfig | None = None,
) -> ServiceAccountAnalysis:
    """Analyze service accounts for security and governance risks.

    Evaluates each service account across five risk dimensions:
    1. Interactive login patterns (credential compromise indicator)
    2. Missing ownership (governance gap)
    3. Staleness / inactivity (decommissioning candidate)
    4. Excessive privileges (admin-level access)
    5. Credential rotation compliance (overdue rotation)

    Args:
        service_account_inventory: DataFrame with columns account_id,
            account_name, account_type, owner_id, owner_name, description,
            created_date, last_credential_rotation, roles, role_count, is_admin.
        user_activity: DataFrame with columns user_id, timestamp,
            menu_item, action, session_id, ip_address, user_agent.
        login_history: DataFrame with columns account_id, timestamp,
            login_type, ip_address, session_id.
        config: Optional configuration overrides.

    Returns:
        ServiceAccountAnalysis with findings and account summaries.
    """
    if config is None:
        config = ServiceAccountConfig()

    # Handle empty inventory
    if service_account_inventory.empty:
        return ServiceAccountAnalysis(
            total_accounts_analyzed=0,
            total_findings=0,
            high_risk_count=0,
            medium_risk_count=0,
            low_risk_count=0,
        )

    # Pre-compute activity sets for O(1) lookup
    active_account_ids: set[str] = set()
    if not user_activity.empty:
        active_account_ids = set(user_activity["user_id"].unique())

    # Pre-compute interactive login accounts
    interactive_account_ids: set[str] = set()
    if not login_history.empty:
        interactive_mask = login_history["login_type"] == "interactive"
        if interactive_mask.any():
            interactive_account_ids = set(
                login_history.loc[interactive_mask, "account_id"].unique()
            )

    # Collect all known service account IDs
    inventory_account_ids: set[str] = set(
        service_account_inventory["account_id"].unique()
    )

    # Analyze each service account
    all_findings: list[ServiceAccountFinding] = []
    account_findings_map: dict[str, list[ServiceAccountFinding]] = {}

    for _, row in service_account_inventory.iterrows():
        account_id: str = str(row["account_id"])
        account_name: str = str(row.get("account_name", ""))
        findings = _analyze_single_account(
            account_id=account_id,
            account_name=account_name,
            row=row,
            active_account_ids=active_account_ids,
            interactive_account_ids=interactive_account_ids,
            inventory_account_ids=inventory_account_ids,
            config=config,
        )
        all_findings.extend(findings)
        account_findings_map[account_id] = findings

    # Sort findings by risk score descending
    all_findings.sort(key=lambda f: f.risk_score, reverse=True)

    # Build per-account summaries
    summaries: list[ServiceAccountSummary] = []
    for _, row in service_account_inventory.iterrows():
        account_id = str(row["account_id"])
        account_name = str(row.get("account_name", ""))
        acct_findings = account_findings_map.get(account_id, [])
        total_risk = sum(f.risk_score for f in acct_findings)
        highest_risk = "LOW"
        for f in acct_findings:
            if _RISK_LEVEL_ORDER.get(f.risk_level, 0) > _RISK_LEVEL_ORDER.get(
                highest_risk, 0
            ):
                highest_risk = f.risk_level
        summaries.append(
            ServiceAccountSummary(
                account_id=account_id,
                account_name=account_name,
                risk_score=total_risk,
                finding_count=len(acct_findings),
                highest_risk_level=highest_risk,
            )
        )

    # Sort summaries by risk score descending
    summaries.sort(key=lambda s: s.risk_score, reverse=True)

    # Count by risk level
    high_count = sum(
        1 for f in all_findings if f.risk_level in ("HIGH", "CRITICAL")
    )
    medium_count = sum(1 for f in all_findings if f.risk_level == "MEDIUM")
    low_count = sum(1 for f in all_findings if f.risk_level == "LOW")

    return ServiceAccountAnalysis(
        total_accounts_analyzed=len(service_account_inventory),
        total_findings=len(all_findings),
        high_risk_count=high_count,
        medium_risk_count=medium_count,
        low_risk_count=low_count,
        findings=all_findings,
        account_summaries=summaries,
    )


# ---------------------------------------------------------------------------
# Per-Account Analysis (private)
# ---------------------------------------------------------------------------


def _analyze_single_account(
    account_id: str,
    account_name: str,
    row: pd.Series,  # type: ignore[type-arg]
    active_account_ids: set[str],
    interactive_account_ids: set[str],
    inventory_account_ids: set[str],
    config: ServiceAccountConfig,
) -> list[ServiceAccountFinding]:
    """Run all risk checks for a single service account.

    Args:
        account_id: The service account identifier.
        account_name: The service account display name.
        row: Inventory row with account metadata.
        active_account_ids: Set of account IDs with recent activity.
        interactive_account_ids: Set of account IDs with interactive logins.
        inventory_account_ids: Set of all service account IDs in inventory.
        config: Analysis configuration.

    Returns:
        List of findings for this account.
    """
    findings: list[ServiceAccountFinding] = []

    # Check 1: Interactive login detection
    if account_id in interactive_account_ids:
        findings.append(
            ServiceAccountFinding(
                account_id=account_id,
                account_name=account_name,
                finding_type="INTERACTIVE_LOGIN",
                risk_level=_RISK_LEVELS["INTERACTIVE_LOGIN"],
                risk_score=_RISK_SCORES["INTERACTIVE_LOGIN"],
                description=(
                    f"Service account '{account_name}' ({account_id}) has "
                    f"interactive login sessions detected. Service accounts "
                    f"should only authenticate via batch or API calls. "
                    f"Interactive logins suggest credential compromise or misuse."
                ),
                recommendation=(
                    "Investigate interactive login source immediately. "
                    "Rotate credentials, review access logs, and restrict "
                    "authentication to non-interactive methods only."
                ),
            )
        )

    # Check 2: No owner assigned
    owner_id = row.get("owner_id")
    if owner_id is None or (isinstance(owner_id, str) and owner_id.strip() == ""):
        findings.append(
            ServiceAccountFinding(
                account_id=account_id,
                account_name=account_name,
                finding_type="NO_OWNER",
                risk_level=_RISK_LEVELS["NO_OWNER"],
                risk_score=_RISK_SCORES["NO_OWNER"],
                description=(
                    f"Service account '{account_name}' ({account_id}) has no "
                    f"assigned owner. Every service account must have a "
                    f"designated ownership contact for governance and "
                    f"accountability."
                ),
                recommendation=(
                    "Assign an owner to this service account immediately. "
                    "Establish a governance process requiring ownership "
                    "review during quarterly access reviews."
                ),
            )
        )

    # Check 3: Stale account (no recent activity)
    if account_id not in active_account_ids:
        findings.append(
            ServiceAccountFinding(
                account_id=account_id,
                account_name=account_name,
                finding_type="STALE_ACCOUNT",
                risk_level=_RISK_LEVELS["STALE_ACCOUNT"],
                risk_score=_RISK_SCORES["STALE_ACCOUNT"],
                description=(
                    f"Service account '{account_name}' ({account_id}) has no "
                    f"activity in the analysis period. Stale service accounts "
                    f"pose security risks and should be reviewed for "
                    f"decommissioning."
                ),
                recommendation=(
                    "Review whether this service account is still needed. "
                    "If no longer required, disable and schedule for "
                    "decommissioning. If still needed, document the "
                    "expected usage pattern."
                ),
            )
        )

    # Check 4: Admin-level privileges
    is_admin = row.get("is_admin", False)
    if is_admin:
        roles = row.get("roles", [])
        role_list = ", ".join(roles) if isinstance(roles, list) else str(roles)
        findings.append(
            ServiceAccountFinding(
                account_id=account_id,
                account_name=account_name,
                finding_type="EXCESSIVE_PRIVILEGE",
                risk_level=_RISK_LEVELS["EXCESSIVE_PRIVILEGE"],
                risk_score=_RISK_SCORES["EXCESSIVE_PRIVILEGE"],
                description=(
                    f"Service account '{account_name}' ({account_id}) has "
                    f"admin-level privileges with excessive permissions. "
                    f"Roles: {role_list}. Service accounts should follow "
                    f"least-privilege principle."
                ),
                recommendation=(
                    "Review and reduce privileges to the minimum required "
                    "for the service account's function. Replace admin roles "
                    "with specific duty roles that grant only needed access."
                ),
            )
        )

    # Check 5: Credential rotation compliance
    last_rotation_str = row.get("last_credential_rotation")
    if last_rotation_str is not None:
        try:
            if isinstance(last_rotation_str, str):
                last_rotation = datetime.fromisoformat(last_rotation_str)
            else:
                last_rotation = pd.Timestamp(last_rotation_str).to_pydatetime()

            # Make timezone-aware if naive
            if last_rotation.tzinfo is None:
                last_rotation = last_rotation.replace(tzinfo=timezone.utc)

            ref_date = config.reference_date
            if ref_date.tzinfo is None:
                ref_date = ref_date.replace(tzinfo=timezone.utc)

            days_since_rotation = (ref_date - last_rotation).days

            if days_since_rotation > config.credential_rotation_max_days:
                findings.append(
                    ServiceAccountFinding(
                        account_id=account_id,
                        account_name=account_name,
                        finding_type="CREDENTIAL_ROTATION",
                        risk_level=_RISK_LEVELS["CREDENTIAL_ROTATION"],
                        risk_score=_RISK_SCORES["CREDENTIAL_ROTATION"],
                        description=(
                            f"Service account '{account_name}' ({account_id}) "
                            f"has not rotated credentials in "
                            f"{days_since_rotation} days. Last rotation: "
                            f"{last_rotation_str}. Password/credential "
                            f"rotation policy requires rotation every "
                            f"{config.credential_rotation_max_days} days."
                        ),
                        recommendation=(
                            "Rotate service account credentials immediately. "
                            "Implement automated credential rotation using "
                            "Azure Key Vault or equivalent secret management."
                        ),
                    )
                )
        except (ValueError, TypeError):
            # If date parsing fails, skip this check
            pass

    return findings
