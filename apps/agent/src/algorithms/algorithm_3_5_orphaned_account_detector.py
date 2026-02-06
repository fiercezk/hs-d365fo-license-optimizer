"""Algorithm 3.5: Orphaned Account Detector.

Identifies user accounts with no active manager, inactive status, missing
department, inactive manager, or extended inactivity. Orphaned accounts pose
security risks and incur unnecessary license costs.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 634-747

The algorithm checks five orphan indicators:
1. No valid manager assigned (HIGH risk)
2. User status is Inactive (MEDIUM risk)
3. No valid department (HIGH risk)
4. Manager is inactive (HIGH risk)
5. No activity in 180+ days (MEDIUM risk)

Output: List of OrphanedAccountResult with orphan type, reasons, risk level,
and remediation recommendation. Results sorted by risk level (HIGH first).

Author: D365 FO License Agent
Created: 2026-02-06
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OrphanType(str, Enum):
    """Classification of orphan account types.

    See Requirements/07 Algorithm 3.5 output structure:
    Orphan Type: [No Manager/Inactive/No Dept/Inactive Manager/Multiple]
    """

    NO_MANAGER = "NO_MANAGER"
    INACTIVE = "INACTIVE"
    NO_DEPARTMENT = "NO_DEPARTMENT"
    INACTIVE_MANAGER = "INACTIVE_MANAGER"
    MULTIPLE = "MULTIPLE"


# ---------------------------------------------------------------------------
# Input Model
# ---------------------------------------------------------------------------


class UserDirectoryRecord(BaseModel):
    """User directory record for orphaned account analysis.

    Combines data from UserDirectory, UserRoleAssignments, UserActivityData,
    and OrganizationHierarchy into a single denormalized record for efficient
    batch processing.

    See Requirements/07 Algorithm 3.5 input data.
    """

    user_id: str = Field(description="Unique user identifier (e.g., 'USR-001')")
    user_name: str = Field(description="User display name")
    email: str = Field(description="User email address")
    status: str = Field(description="User account status ('Active' or 'Inactive')")
    manager_id: Optional[str] = Field(
        default=None, description="Manager user ID (None if no manager assigned)"
    )
    manager_status: Optional[str] = Field(
        default=None,
        description="Manager account status ('Active', 'Inactive', or None)",
    )
    department: Optional[str] = Field(
        default=None, description="Department name (None if unassigned)"
    )
    department_exists: bool = Field(description="Whether the department is valid/exists in the org")
    current_license: str = Field(description="Current license type (e.g., 'Finance', 'SCM')")
    current_license_cost_monthly: float = Field(description="Monthly license cost in USD", ge=0)
    roles: List[str] = Field(
        description="List of assigned security role names",
        default_factory=list,
    )
    role_count: int = Field(description="Number of roles assigned", ge=0)
    days_since_last_activity: int = Field(
        description="Days since the user last performed any system activity",
        ge=0,
    )


# ---------------------------------------------------------------------------
# Output Model
# ---------------------------------------------------------------------------


class OrphanedAccountResult(BaseModel):
    """Result record for a detected orphaned account.

    Contains all orphan indicators, risk assessment, and remediation guidance.
    See Requirements/07 Algorithm 3.5 output structure.
    """

    user_id: str = Field(description="User identifier")
    user_name: str = Field(description="User display name")
    status: str = Field(description="User account status")
    manager_id: Optional[str] = Field(default=None, description="Manager ID (None if missing)")
    department: Optional[str] = Field(default=None, description="Department name (None if missing)")
    days_since_last_activity: int = Field(description="Days since last activity", ge=0)
    role_count: int = Field(description="Number of roles assigned", ge=0)
    license_cost_per_month: float = Field(description="Monthly license cost in USD", ge=0)
    orphan_type: OrphanType = Field(description="Classification of the orphan condition")
    orphan_reasons: List[str] = Field(description="All detected orphan indicators")
    risk_level: str = Field(description="Risk level: HIGH or MEDIUM")
    recommendation: str = Field(description="Remediation recommendation")
    is_orphaned: bool = Field(
        default=True, description="Always True for results (non-orphaned filtered out)"
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INACTIVITY_THRESHOLD_DAYS: int = 180
"""Days of inactivity before flagging as orphaned (per spec)."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _collect_orphan_reasons(user: UserDirectoryRecord) -> List[str]:
    """Evaluate all five orphan indicators for a single user.

    Checks are ordered to match the spec pseudocode (Requirements/07 lines 678-707):
    1. No valid manager (manager_id is None)
    2. User status is Inactive
    3. No valid department (department is None or department_exists is False)
    4. Manager is inactive (manager_id present but manager_status is Inactive)
    5. No activity in 180+ days

    Args:
        user: User directory record to evaluate.

    Returns:
        List of orphan reason strings. Empty if user is not orphaned.
    """
    reasons: List[str] = []

    # Check 1: No manager assigned
    if user.manager_id is None:
        reasons.append("No valid manager")

    # Check 2: Inactive status
    if user.status == "Inactive":
        reasons.append("User status is Inactive")

    # Check 3: No department or department deleted
    if user.department is None or not user.department_exists:
        reasons.append("No valid department")

    # Check 4: Manager is inactive (only when manager_id is present)
    if user.manager_id is not None and user.manager_status == "Inactive":
        reasons.append("Manager is inactive")

    # Check 5: No activity in 180+ days
    if user.days_since_last_activity > INACTIVITY_THRESHOLD_DAYS:
        reasons.append(f"No activity in {user.days_since_last_activity} days")

    return reasons


def _classify_orphan_type(reasons: List[str]) -> OrphanType:
    """Classify the orphan type based on detected reasons.

    When multiple structural reasons exist, the type is MULTIPLE.
    Otherwise, a single dominant reason determines the type.

    Args:
        reasons: List of orphan reason strings.

    Returns:
        OrphanType enum value.
    """
    # Map reason prefixes to orphan types
    structural_types: List[OrphanType] = []

    for reason in reasons:
        if reason == "No valid manager":
            structural_types.append(OrphanType.NO_MANAGER)
        elif reason == "User status is Inactive":
            structural_types.append(OrphanType.INACTIVE)
        elif reason == "No valid department":
            structural_types.append(OrphanType.NO_DEPARTMENT)
        elif reason == "Manager is inactive":
            structural_types.append(OrphanType.INACTIVE_MANAGER)
        elif reason.startswith("No activity in"):
            structural_types.append(OrphanType.INACTIVE)

    # Deduplicate while preserving order
    unique_types: List[OrphanType] = []
    seen: set[OrphanType] = set()
    for t in structural_types:
        if t not in seen:
            unique_types.append(t)
            seen.add(t)

    if len(unique_types) > 1:
        return OrphanType.MULTIPLE
    if len(unique_types) == 1:
        return unique_types[0]

    # Fallback (should not happen since reasons is non-empty)
    return OrphanType.MULTIPLE


def _assess_risk_level(
    user: UserDirectoryRecord,
    reasons: List[str],
) -> str:
    """Determine risk level based on user state and orphan indicators.

    Risk assessment logic (derived from spec pseudocode and test scenarios):
    - HIGH risk: Active account with roles AND has a structural orphan indicator
      (no manager, no department, inactive manager). These accounts have active
      access but no organizational oversight.
    - MEDIUM risk: Inactive account, OR account with no roles, OR only
      inactivity-based orphan indicator (still has organizational structure).

    Args:
        user: User directory record.
        reasons: Collected orphan reasons.

    Returns:
        "HIGH" or "MEDIUM" risk level string.
    """
    # Structural indicators that escalate to HIGH when user is active with roles
    has_structural_indicator = any(
        r in ("No valid manager", "No valid department", "Manager is inactive") for r in reasons
    )

    if user.status == "Active" and user.role_count > 0 and has_structural_indicator:
        return "HIGH"

    return "MEDIUM"


def _generate_recommendation(
    user: UserDirectoryRecord,
    reasons: List[str],
    orphan_type: OrphanType,
) -> str:
    """Generate remediation recommendation based on orphan indicators.

    Provides actionable guidance matching the spec output structure.

    Args:
        user: User directory record.
        reasons: Collected orphan reasons.
        orphan_type: Classified orphan type.

    Returns:
        Recommendation string with remediation guidance.
    """
    if orphan_type == OrphanType.MULTIPLE:
        has_manager_issue = any(r in ("No valid manager", "Manager is inactive") for r in reasons)
        has_dept_issue = "No valid department" in reasons
        has_inactivity = any(r.startswith("No activity in") for r in reasons)
        has_inactive_status = "User status is Inactive" in reasons

        if has_inactive_status or (not has_manager_issue and not has_dept_issue):
            return "Disable account and remove license"

        parts: List[str] = []
        if has_manager_issue:
            parts.append("assign manager")
        if has_dept_issue:
            parts.append("department")
        if has_inactivity:
            parts.append("and verify account necessity")

        action = ", ".join(parts)
        return f"Immediate review required: {action}"

    if orphan_type == OrphanType.NO_MANAGER:
        return "Assign a valid manager to this account"

    if orphan_type == OrphanType.NO_DEPARTMENT:
        return "Assign user to a valid department"

    if orphan_type == OrphanType.INACTIVE_MANAGER:
        return "Assign a new active manager"

    if orphan_type == OrphanType.INACTIVE:
        if user.status == "Inactive":
            return "Disable account and remove license"
        return "Review account and consider disabling or removing license"

    return "Review account for remediation"


# ---------------------------------------------------------------------------
# Main algorithm entry point
# ---------------------------------------------------------------------------


def detect_orphaned_accounts(
    users: List[UserDirectoryRecord],
    inactivity_threshold_days: int = INACTIVITY_THRESHOLD_DAYS,
) -> List[OrphanedAccountResult]:
    """Algorithm 3.5: Detect orphaned user accounts across a user population.

    Evaluates each user against five orphan indicators and returns only those
    flagged as orphaned, sorted by risk level (HIGH before MEDIUM).

    See Requirements/07-Advanced-Algorithms-Expansion.md, lines 634-747.

    Args:
        users: List of UserDirectoryRecord instances to evaluate.
        inactivity_threshold_days: Days of inactivity threshold (default 180).

    Returns:
        List of OrphanedAccountResult sorted by risk level (HIGH first).
        Only includes users with at least one orphan indicator.
        Returns empty list if no orphaned accounts detected.

    Examples:
        >>> from src.algorithms.algorithm_3_5_orphaned_account_detector import (
        ...     detect_orphaned_accounts, UserDirectoryRecord,
        ... )
        >>> user = UserDirectoryRecord(
        ...     user_id="USR-001", user_name="Test", email="test@co.com",
        ...     status="Active", manager_id=None, manager_status=None,
        ...     department="IT", department_exists=True,
        ...     current_license="Finance", current_license_cost_monthly=180.0,
        ...     roles=["Accountant"], role_count=1, days_since_last_activity=5,
        ... )
        >>> results = detect_orphaned_accounts([user])
        >>> len(results)
        1
        >>> results[0].orphan_type.value
        'NO_MANAGER'
    """
    orphaned: List[OrphanedAccountResult] = []

    for user in users:
        # Collect all orphan reasons for this user
        reasons = _collect_orphan_reasons(user)

        # Skip non-orphaned users
        if not reasons:
            continue

        # Classify orphan type and assess risk
        orphan_type = _classify_orphan_type(reasons)
        risk_level = _assess_risk_level(user, reasons)
        recommendation = _generate_recommendation(user, reasons, orphan_type)

        orphaned.append(
            OrphanedAccountResult(
                user_id=user.user_id,
                user_name=user.user_name,
                status=user.status,
                manager_id=user.manager_id,
                department=user.department,
                days_since_last_activity=user.days_since_last_activity,
                role_count=user.role_count,
                license_cost_per_month=user.current_license_cost_monthly,
                orphan_type=orphan_type,
                orphan_reasons=reasons,
                risk_level=risk_level,
                recommendation=recommendation,
                is_orphaned=True,
            )
        )

    # Sort by risk level: HIGH before MEDIUM
    risk_order = {"HIGH": 0, "MEDIUM": 1}
    orphaned.sort(key=lambda r: risk_order.get(r.risk_level, 2))

    return orphaned
