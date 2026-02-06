"""Algorithm 6.1: Stale Role Detector.

Identifies security roles that have not been assigned to any active users
in a configurable time period (default 6 months / 180 days), making them
candidates for review or deletion.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1371-1391
(Algorithm 6.1: Stale Role Detector).

The algorithm:
  1. Scans all defined security roles (custom and standard).
  2. Checks current user-role assignment counts per role.
  3. Checks audit logs for last assignment date per role.
  4. Classifies roles as stale if they have zero active assignments AND
     no audit activity within the staleness threshold.
  5. Distinguishes between custom and standard roles for recommendations:
     - Custom stale roles: recommend review for deletion.
     - Standard stale roles: recommend review only (cannot delete system roles).
  6. Returns results sorted by days_since_last_used descending (most stale first).

Performance: O(R + A + U) where R = roles, A = audit entries, U = assignments.
Uses vectorized pandas groupby operations; avoids iterrows().
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
from pydantic import BaseModel, Field


class StaleRole(BaseModel):
    """A single stale role detected by Algorithm 6.1.

    Represents a security role that has no active user assignments and
    has not been assigned to anyone within the staleness threshold.

    Attributes:
        role_id: Unique role identifier.
        role_name: Human-readable role name.
        role_type: 'Custom' or 'Standard' (system).
        current_assignment_count: Number of currently active assignments (0 for stale).
        days_since_last_used: Days since the role was last assigned per audit logs.
        last_assignment_date: ISO date string of last assignment, or None if never used.
        recommendation: Actionable recommendation text.
        risk_level: Risk assessment ('Low' for unassigned roles).
    """

    role_id: str = Field(description="Unique role identifier")
    role_name: str = Field(description="Human-readable role name")
    role_type: str = Field(description="Role type: 'Custom' or 'Standard'")
    current_assignment_count: int = Field(
        description="Number of currently active assignments", ge=0
    )
    days_since_last_used: int = Field(
        description="Days since the role was last assigned per audit logs", ge=0
    )
    last_assignment_date: str | None = Field(
        default=None,
        description="ISO date string of last assignment, or None if never used",
    )
    recommendation: str = Field(description="Actionable recommendation text")
    risk_level: str = Field(
        default="Low",
        description="Risk level - Low for unassigned roles (no users affected)",
    )


class StaleRoleAnalysis(BaseModel):
    """Complete output from Algorithm 6.1: Stale Role Detector.

    Aggregates all detected stale roles with summary statistics.

    Attributes:
        algorithm_id: Always '6.1'.
        stale_roles: List of detected stale roles, sorted by staleness descending.
        total_roles_analyzed: Total number of roles scanned.
        stale_role_count: Number of roles classified as stale.
    """

    algorithm_id: str = Field(default="6.1", description="Algorithm identifier")
    stale_roles: list[StaleRole] = Field(
        default_factory=list,
        description="Detected stale roles, sorted by days_since_last_used descending",
    )
    total_roles_analyzed: int = Field(
        description="Total number of roles scanned", ge=0
    )
    stale_role_count: int = Field(
        description="Number of roles classified as stale", ge=0
    )


def detect_stale_roles(
    role_definitions: pd.DataFrame,
    user_role_assignments: pd.DataFrame,
    audit_log: pd.DataFrame,
    staleness_threshold_days: int = 180,
) -> StaleRoleAnalysis:
    """Detect security roles that are stale (unused) candidates for cleanup.

    Algorithm 6.1 scans all defined security roles, checks current assignment
    counts and audit history, then flags roles with zero active assignments and
    no recent audit activity as stale.

    See Requirements/07-Advanced-Algorithms-Expansion.md, Algorithm 6.1.

    Args:
        role_definitions: DataFrame with columns:
            role_id, role_name, role_type, created_date, description.
        user_role_assignments: DataFrame with columns:
            user_id, role_id, role_name, status, assigned_date.
        audit_log: DataFrame with columns:
            audit_id, role_id, action, timestamp, changed_by.
        staleness_threshold_days: Number of days without activity to consider
            a role stale. Default 180 (6 months).

    Returns:
        StaleRoleAnalysis with detected stale roles sorted by staleness
        (most stale first) and summary statistics.
    """
    # Handle empty role definitions
    if role_definitions.empty:
        return StaleRoleAnalysis(
            total_roles_analyzed=0,
            stale_role_count=0,
            stale_roles=[],
        )

    total_roles = len(role_definitions)
    now = datetime.now(UTC)

    # Step 1: Count active assignments per role (O(U) via groupby)
    active_assignment_counts: dict[str, int] = {}
    if not user_role_assignments.empty:
        active = user_role_assignments[
            user_role_assignments["status"].str.lower() == "active"
        ]
        if not active.empty:
            counts = active.groupby("role_id").size()
            active_assignment_counts = {
                str(k): int(v) for k, v in counts.items()
            }

    # Step 2: Find last assignment date per role from audit log (O(A) via groupby)
    last_assignment_dates: dict[str, datetime] = {}
    if not audit_log.empty:
        audit_copy = audit_log.copy()
        audit_copy["timestamp"] = pd.to_datetime(audit_copy["timestamp"], utc=True)
        last_dates = audit_copy.groupby("role_id")["timestamp"].max()
        last_assignment_dates = {
            str(role_id): ts.to_pydatetime()
            for role_id, ts in last_dates.items()
        }

    # Step 3: Evaluate each role for staleness (O(R))
    stale_roles: list[StaleRole] = []

    for _, row in role_definitions.iterrows():
        role_id: str = str(row["role_id"])
        role_name: str = str(row["role_name"])
        role_type: str = str(row["role_type"])

        # Check active assignment count
        assignment_count = active_assignment_counts.get(role_id, 0)

        # Roles with active assignments are NOT stale -- skip
        if assignment_count > 0:
            continue

        # Determine days since last used
        last_date = last_assignment_dates.get(role_id)
        if last_date is None:
            # Never used per audit log -- treat as maximally stale
            days_since_last_used = staleness_threshold_days + 1
            last_assignment_str: str | None = None
        else:
            delta = now - last_date
            days_since_last_used = int(delta.days)
            last_assignment_str = last_date.strftime("%Y-%m-%d")

        # Only flag as stale if beyond the threshold
        if days_since_last_used < staleness_threshold_days:
            continue

        # Generate recommendation based on role type
        if role_type == "Standard":
            recommendation = (
                f"Review standard role '{role_name}' -- no active assignments "
                f"in {days_since_last_used} days. Standard roles should be "
                f"reviewed for disabling or retention justification."
            )
        else:
            recommendation = (
                f"Review custom role '{role_name}' for deletion -- no active "
                f"assignments in {days_since_last_used} days. Role has 0 users "
                f"and may be safely removed after verification."
            )

        stale_roles.append(
            StaleRole(
                role_id=role_id,
                role_name=role_name,
                role_type=role_type,
                current_assignment_count=assignment_count,
                days_since_last_used=days_since_last_used,
                last_assignment_date=last_assignment_str,
                recommendation=recommendation,
                risk_level="Low",
            )
        )

    # Step 4: Sort by days_since_last_used descending (most stale first)
    stale_roles.sort(key=lambda r: r.days_since_last_used, reverse=True)

    return StaleRoleAnalysis(
        total_roles_analyzed=total_roles,
        stale_role_count=len(stale_roles),
        stale_roles=stale_roles,
    )
