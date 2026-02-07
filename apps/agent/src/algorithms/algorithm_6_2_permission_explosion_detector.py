"""Algorithm 6.2: Permission Explosion Detector.

Detects roles with excessive permissions (permission explosion), which pose
security risks and increase license costs. Analyzes each role's menu item
count, access level distribution, license tier spread, and statistical
deviation from organizational averages.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md (Algorithm 6.2)
Category: Role Management

Detection types:
  - EXPLOSION_DETECTED (HIGH): Role exceeds menu item threshold (default 500)
  - EXCESSIVE_WRITE_ACCESS (HIGH): Role with >80% write/delete permissions
  - CROSS_TIER_EXPLOSION (MEDIUM): Role spans 3+ license tiers
  - STATISTICAL_OUTLIER (MEDIUM): Role 3x larger than organizational average

Results are sorted by menu item count descending so the most critical
roles appear first.
"""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, Field


class PermissionExplosionFinding(BaseModel):
    """Individual finding from the Permission Explosion Detector.

    Each finding represents a specific type of permission explosion
    detected for a security role.
    """

    role_name: str = Field(description="Security role name")
    finding_type: str = Field(
        description=(
            "Type of finding: EXPLOSION_DETECTED, EXCESSIVE_WRITE_ACCESS, "
            "CROSS_TIER_EXPLOSION, STATISTICAL_OUTLIER"
        )
    )
    severity: str = Field(description="Finding severity: CRITICAL, HIGH, MEDIUM, LOW")
    menu_item_count: int = Field(
        description="Number of menu items assigned to the role",
        ge=0,
    )
    users_affected: int = Field(
        description="Number of users currently assigned this role",
        ge=0,
    )
    description: str = Field(description="Human-readable description of the finding")
    recommendation: str = Field(description="Actionable recommendation for remediation")


class PermissionExplosionAnalysis(BaseModel):
    """Complete output from Algorithm 6.2: Permission Explosion Detector.

    Aggregates all findings across analyzed roles with summary statistics.
    """

    algorithm_id: str = Field(
        default="6.2",
        description="Algorithm identifier",
    )
    findings: list[PermissionExplosionFinding] = Field(
        default_factory=list,
        description="List of permission explosion findings, sorted by menu item count desc",
    )
    total_roles_analyzed: int = Field(
        default=0,
        description="Total number of roles analyzed",
    )
    average_menu_item_count: float = Field(
        default=0.0,
        description="Average menu item count across all analyzed roles",
    )
    total_findings: int = Field(
        default=0,
        description="Total number of findings detected",
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MENU_ITEM_THRESHOLD: int = 500
_WRITE_ACCESS_THRESHOLD: float = 0.80
_CROSS_TIER_MIN_TIERS: int = 3
_STATISTICAL_OUTLIER_MULTIPLIER: float = 3.0
_WRITE_DELETE_ACCESS_LEVELS: frozenset[str] = frozenset({"Write", "Delete", "Create", "Update"})


def detect_permission_explosions(
    security_config: pd.DataFrame,
    role_definitions: pd.DataFrame,
    user_role_assignments: pd.DataFrame,
    menu_item_threshold: int = _DEFAULT_MENU_ITEM_THRESHOLD,
) -> PermissionExplosionAnalysis:
    """Detect roles with excessive permissions (permission explosion).

    Analyzes security configuration data to identify roles that have grown
    too large, have disproportionate write access, span multiple license
    tiers, or are statistical outliers compared to organizational averages.

    Args:
        security_config: DataFrame with columns: securityrole, AOTName,
            AccessLevel, LicenseType, Priority, Entitled, NotEntitled,
            securitytype.
        role_definitions: DataFrame with columns: role_id, role_name,
            role_type, created_date.
        user_role_assignments: DataFrame with columns: user_id, role_name,
            status.
        menu_item_threshold: Minimum menu item count to trigger
            EXPLOSION_DETECTED finding (default 500).

    Returns:
        PermissionExplosionAnalysis with findings sorted by menu item
        count descending.
    """
    # Handle empty input gracefully
    if security_config.empty:
        return PermissionExplosionAnalysis(
            algorithm_id="6.2",
            findings=[],
            total_roles_analyzed=0,
            average_menu_item_count=0.0,
            total_findings=0,
        )

    # Pre-compute per-role statistics in a single pass over security_config
    role_stats: dict[str, _RoleStats] = _compute_role_stats(security_config)
    total_roles: int = len(role_stats)

    # Compute organizational total menu item count (for leave-one-out average)
    total_menu_items: int = sum(rs.menu_item_count for rs in role_stats.values())
    if total_roles > 0:
        avg_menu_items: float = total_menu_items / total_roles
    else:
        avg_menu_items = 0.0

    # Pre-compute user counts per role from assignments
    user_counts: dict[str, int] = _compute_user_counts(user_role_assignments)

    # Detect all finding types
    findings: list[PermissionExplosionFinding] = []

    for role_name, stats in role_stats.items():
        users: int = user_counts.get(role_name, 0)

        # Check 1: Menu item explosion (HIGH)
        if stats.menu_item_count >= menu_item_threshold:
            findings.append(_build_explosion_finding(role_name, stats, users, menu_item_threshold))

        # Check 2: Excessive write/delete access (HIGH)
        if stats.menu_item_count > 0 and stats.write_ratio > _WRITE_ACCESS_THRESHOLD:
            findings.append(_build_write_access_finding(role_name, stats, users))

        # Check 3: Cross-tier explosion (MEDIUM)
        if len(stats.license_tiers) >= _CROSS_TIER_MIN_TIERS:
            findings.append(_build_cross_tier_finding(role_name, stats, users))

        # Check 4: Statistical outlier (MEDIUM)
        # Use leave-one-out average to prevent large outliers from inflating
        # the org average and hiding themselves.
        if total_roles > 1:
            other_total: int = total_menu_items - stats.menu_item_count
            other_avg: float = other_total / (total_roles - 1)
        else:
            other_avg = 0.0

        if other_avg > 0 and stats.menu_item_count >= other_avg * _STATISTICAL_OUTLIER_MULTIPLIER:
            findings.append(_build_outlier_finding(role_name, stats, users, other_avg))

    # Sort findings by menu_item_count descending (largest first)
    findings.sort(key=lambda f: f.menu_item_count, reverse=True)

    return PermissionExplosionAnalysis(
        algorithm_id="6.2",
        findings=findings,
        total_roles_analyzed=total_roles,
        average_menu_item_count=round(avg_menu_items, 2),
        total_findings=len(findings),
    )


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


class _RoleStats:
    """Aggregated statistics for a single role (internal, not exported)."""

    __slots__ = (
        "menu_item_count",
        "write_delete_count",
        "read_count",
        "license_tiers",
    )

    def __init__(self) -> None:
        self.menu_item_count: int = 0
        self.write_delete_count: int = 0
        self.read_count: int = 0
        self.license_tiers: set[str] = set()

    @property
    def write_ratio(self) -> float:
        """Proportion of write/delete/create/update permissions."""
        if self.menu_item_count == 0:
            return 0.0
        return self.write_delete_count / self.menu_item_count


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compute_role_stats(security_config: pd.DataFrame) -> dict[str, _RoleStats]:
    """Compute per-role statistics in a single pass over security config.

    O(N) where N is the number of rows in security_config.

    Args:
        security_config: Security configuration DataFrame.

    Returns:
        Dictionary mapping role name to aggregated statistics.
    """
    stats: dict[str, _RoleStats] = {}

    # Use vectorized column access then iterate once
    roles = security_config["securityrole"].values
    access_levels = security_config["AccessLevel"].values
    license_types = security_config["LicenseType"].values

    for i in range(len(roles)):
        role: str = str(roles[i])
        access: str = str(access_levels[i])
        license_type: str = str(license_types[i])

        if role not in stats:
            stats[role] = _RoleStats()

        rs = stats[role]
        rs.menu_item_count += 1
        rs.license_tiers.add(license_type)

        if access in _WRITE_DELETE_ACCESS_LEVELS:
            rs.write_delete_count += 1
        else:
            rs.read_count += 1

    return stats


def _compute_user_counts(user_role_assignments: pd.DataFrame) -> dict[str, int]:
    """Compute number of active users per role.

    O(N) where N is the number of assignment rows.

    Args:
        user_role_assignments: User-role assignment DataFrame.

    Returns:
        Dictionary mapping role name to active user count.
    """
    if user_role_assignments.empty:
        return {}

    # Filter to active assignments only
    active = user_role_assignments
    if "status" in user_role_assignments.columns:
        active = user_role_assignments[user_role_assignments["status"] == "Active"]

    if active.empty:
        return {}

    raw_counts: dict[str, int] = {
        str(k): int(v)
        for k, v in active.groupby("role_name")["user_id"].nunique().to_dict().items()
    }
    return raw_counts


def _build_explosion_finding(
    role_name: str,
    stats: _RoleStats,
    users_affected: int,
    threshold: int,
) -> PermissionExplosionFinding:
    """Build EXPLOSION_DETECTED finding for an oversized role.

    Args:
        role_name: Security role name.
        stats: Aggregated role statistics.
        users_affected: Number of users assigned this role.
        threshold: Menu item threshold that was exceeded.

    Returns:
        PermissionExplosionFinding with splitting recommendation.
    """
    return PermissionExplosionFinding(
        role_name=role_name,
        finding_type="EXPLOSION_DETECTED",
        severity="HIGH",
        menu_item_count=stats.menu_item_count,
        users_affected=users_affected,
        description=(
            f"Role '{role_name}' has {stats.menu_item_count} menu items, "
            f"exceeding the threshold of {threshold}. "
            f"This level of permission concentration poses a security risk "
            f"and affects {users_affected} user(s)."
        ),
        recommendation=(
            f"Split role '{role_name}' into smaller, purpose-specific roles. "
            f"Consider separating by functional area or license tier to reduce "
            f"permission surface and improve security posture."
        ),
    )


def _build_write_access_finding(
    role_name: str,
    stats: _RoleStats,
    users_affected: int,
) -> PermissionExplosionFinding:
    """Build EXCESSIVE_WRITE_ACCESS finding.

    Args:
        role_name: Security role name.
        stats: Aggregated role statistics.
        users_affected: Number of users assigned this role.

    Returns:
        PermissionExplosionFinding for write access excess.
    """
    write_pct: float = round(stats.write_ratio * 100, 1)
    return PermissionExplosionFinding(
        role_name=role_name,
        finding_type="EXCESSIVE_WRITE_ACCESS",
        severity="HIGH",
        menu_item_count=stats.menu_item_count,
        users_affected=users_affected,
        description=(
            f"Role '{role_name}' has {write_pct}% write/delete/create/update "
            f"permissions ({stats.write_delete_count} of {stats.menu_item_count} "
            f"menu items). This disproportionate write access increases "
            f"security risk for {users_affected} user(s)."
        ),
        recommendation=(
            f"Review write permissions for role '{role_name}'. "
            f"Consider creating a read-only variant for users who only need "
            f"view access, and split write permissions into separate roles "
            f"with tighter access controls."
        ),
    )


def _build_cross_tier_finding(
    role_name: str,
    stats: _RoleStats,
    users_affected: int,
) -> PermissionExplosionFinding:
    """Build CROSS_TIER_EXPLOSION finding.

    Args:
        role_name: Security role name.
        stats: Aggregated role statistics.
        users_affected: Number of users assigned this role.

    Returns:
        PermissionExplosionFinding for cross-tier explosion.
    """
    tiers_str: str = ", ".join(sorted(stats.license_tiers))
    return PermissionExplosionFinding(
        role_name=role_name,
        finding_type="CROSS_TIER_EXPLOSION",
        severity="MEDIUM",
        menu_item_count=stats.menu_item_count,
        users_affected=users_affected,
        description=(
            f"Role '{role_name}' spans {len(stats.license_tiers)} license "
            f"tiers ({tiers_str}). Cross-tier roles force users into higher "
            f"license tiers and indicate poor role design."
        ),
        recommendation=(
            f"Split role '{role_name}' into separate roles per license tier. "
            f"This allows users to be assigned only the tier-specific roles "
            f"they need, reducing license costs."
        ),
    )


def _build_outlier_finding(
    role_name: str,
    stats: _RoleStats,
    users_affected: int,
    org_average: float,
) -> PermissionExplosionFinding:
    """Build STATISTICAL_OUTLIER finding.

    Args:
        role_name: Security role name.
        stats: Aggregated role statistics.
        users_affected: Number of users assigned this role.
        org_average: Organizational average menu item count.

    Returns:
        PermissionExplosionFinding for statistical outlier.
    """
    multiplier: float = round(stats.menu_item_count / org_average, 1)
    return PermissionExplosionFinding(
        role_name=role_name,
        finding_type="STATISTICAL_OUTLIER",
        severity="MEDIUM",
        menu_item_count=stats.menu_item_count,
        users_affected=users_affected,
        description=(
            f"Role '{role_name}' has {stats.menu_item_count} menu items, "
            f"which is {multiplier}x the organizational average of "
            f"{round(org_average, 1)}. This role is a statistical outlier "
            f"and warrants review."
        ),
        recommendation=(
            f"Investigate why role '{role_name}' is significantly larger "
            f"than average. Consider splitting into smaller purpose-specific "
            f"roles or removing unused permissions."
        ),
    )
