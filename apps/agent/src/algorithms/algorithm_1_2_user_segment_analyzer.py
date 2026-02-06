"""Algorithm 1.2: User Segment Analyzer.

For a given role, analyzes which users actually use which license-type features
and categorizes them into segments: Commerce-Only, Finance-Only, SCM-Only,
Operations-Only, Team-Members-Only, Mixed-Usage, or Inactive.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 108-200.

Input:
  - user_role_assignments: DataFrame with user-role mappings
  - user_activity: DataFrame with user activity telemetry
  - security_config: DataFrame with menu item -> license type mapping
  - role_name: Role to analyze
  - analysis_days: Configurable activity window (default 90)

Output:
  - UserSegmentAnalysis with per-segment counts, percentages,
    and detailed per-user breakdown of licenses used.

Key behaviors:
  - Each user is classified into exactly one segment
  - Inactive users (zero activity within analysis window) -> 'Inactive'
  - Users accessing one license type -> '<LicenseType>-Only'
  - Users accessing multiple license types -> 'Mixed-Usage'
  - Percentages across all segments sum to 100%
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import pandas as pd
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Canonical segment names
# ---------------------------------------------------------------------------

SEGMENT_NAMES: list[str] = [
    "Commerce-Only",
    "Finance-Only",
    "SCM-Only",
    "Operations-Only",
    "Team-Members-Only",
    "Mixed-Usage",
    "Inactive",
]

# Maps license type strings (as they appear in activity / security config data)
# to their corresponding segment name (single-license case).
_LICENSE_TO_SEGMENT: dict[str, str] = {
    "Commerce": "Commerce-Only",
    "Finance": "Finance-Only",
    "SCM": "SCM-Only",
    "Operations": "Operations-Only",
    "Team Members": "Team-Members-Only",
}


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class SegmentStats(BaseModel):
    """Statistics for a single user segment.

    Attributes:
        count: Number of users in this segment.
        percentage: Percentage of total users in this segment (0.0-100.0).
        user_ids: User IDs belonging to this segment.
    """

    count: int = Field(default=0, description="Number of users in segment", ge=0)
    percentage: float = Field(
        default=0.0,
        description="Percentage of total users (0-100)",
        ge=0.0,
        le=100.0,
    )
    user_ids: list[str] = Field(
        default_factory=list,
        description="User IDs in this segment",
    )


class UserSegmentDetail(BaseModel):
    """Detailed per-user breakdown showing which licenses a user accessed.

    Attributes:
        user_id: User identifier.
        user_name: User display name (if available).
        segment: Segment the user was classified into.
        licenses_used: Set of license types the user accessed.
        activity_count: Number of activity records within the analysis window.
    """

    user_id: str = Field(description="User identifier")
    user_name: str | None = Field(default=None, description="User display name")
    segment: str = Field(description="Assigned segment name")
    licenses_used: list[str] = Field(
        default_factory=list,
        description="License types accessed by this user",
    )
    activity_count: int = Field(
        default=0,
        description="Number of activity records in the analysis window",
        ge=0,
    )


class UserSegmentAnalysis(BaseModel):
    """Complete output from Algorithm 1.2: User Segment Analyzer.

    Provides segment breakdown with counts, percentages, and per-user detail
    for all users assigned to the analyzed role.

    See Requirements/06-Algorithms-Decision-Logic.md, lines 108-200.
    """

    algorithm_id: str = Field(
        default="1.2",
        description="Algorithm identifier",
    )
    role_name: str = Field(description="Role that was analyzed")
    total_users: int = Field(description="Total users assigned to the role", ge=0)
    segments: dict[str, SegmentStats] = Field(
        description="Per-segment statistics keyed by segment name",
    )
    detailed_breakdown: list[UserSegmentDetail] = Field(
        default_factory=list,
        description="Per-user classification details",
    )


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------


def _build_menu_item_license_map(security_config: pd.DataFrame) -> dict[str, str]:
    """Build a mapping of menu item AOT name to license type.

    When a menu item appears under multiple license types in the security
    config, the highest-priority (most expensive) license type wins.
    This matches the Algorithm 1.1 behaviour for determining the
    'highest license' a menu item requires.

    Args:
        security_config: DataFrame with at least columns
            ``AOTName``, ``LicenseType``, and ``Priority``.

    Returns:
        Dict mapping AOTName -> LicenseType string.
    """
    menu_license: dict[str, str] = {}
    menu_priority: dict[str, int] = {}

    for _, row in security_config.iterrows():
        aot: str = str(row["AOTName"])
        license_type: str = str(row["LicenseType"])
        priority: int = int(row["Priority"])

        if aot not in menu_license or priority > menu_priority[aot]:
            menu_license[aot] = license_type
            menu_priority[aot] = priority

    return menu_license


def analyze_user_segments(
    role_name: str,
    user_role_assignments: pd.DataFrame,
    user_activity: pd.DataFrame,
    security_config: pd.DataFrame,
    analysis_days: int = 90,
) -> UserSegmentAnalysis:
    """Algorithm 1.2 -- Analyze user segments for a given role.

    For the specified role, determines which license-type features each user
    actually uses and classifies them into one of seven segments:
    Commerce-Only, Finance-Only, SCM-Only, Operations-Only,
    Team-Members-Only, Mixed-Usage, or Inactive.

    See Requirements/06-Algorithms-Decision-Logic.md, lines 108-200.

    Args:
        role_name: The security role to analyze.
        user_role_assignments: DataFrame with columns including
            ``user_id``, ``user_name``, ``role_name``.
        user_activity: DataFrame with columns including
            ``user_id``, ``timestamp``, ``menu_item``, ``license_tier``.
        security_config: DataFrame with columns including
            ``securityrole``, ``AOTName``, ``LicenseType``, ``Priority``.
        analysis_days: Number of days of activity to consider (default 90).

    Returns:
        UserSegmentAnalysis with segment counts, percentages, and
        detailed per-user breakdown.
    """
    # -- Step 1: Get users with this role --
    if user_role_assignments.empty or "role_name" not in user_role_assignments.columns:
        role_users = user_role_assignments.iloc[0:0]  # empty frame
        user_ids: list[str] = []
    else:
        role_users = user_role_assignments[
            user_role_assignments["role_name"] == role_name
        ]
        user_ids = role_users["user_id"].unique().tolist()
    total_users: int = len(user_ids)

    # Build a quick lookup of user_id -> user_name
    user_name_map: dict[str, str | None] = {}
    if "user_name" in role_users.columns and not role_users.empty:
        for _, row in role_users.iterrows():
            user_name_map[str(row["user_id"])] = str(row["user_name"])

    # -- Step 2: Build menu item -> license type map --
    menu_item_licenses: dict[str, str] = _build_menu_item_license_map(
        security_config
    )

    # -- Step 3: Filter activity to analysis window --
    cutoff: datetime = datetime.now(tz=UTC) - timedelta(days=analysis_days)

    if not user_activity.empty:
        activity_df = user_activity.copy()
        activity_df["_ts"] = pd.to_datetime(activity_df["timestamp"], utc=True)
        activity_df = activity_df[activity_df["_ts"] >= cutoff]
    else:
        activity_df = user_activity

    # -- Step 4: Classify each user --
    # Initialize segment buckets
    segment_users: dict[str, list[str]] = {name: [] for name in SEGMENT_NAMES}
    detailed: list[UserSegmentDetail] = []

    for uid in user_ids:
        user_acts = activity_df[activity_df["user_id"] == uid]
        act_count: int = len(user_acts)

        if act_count == 0:
            # Inactive -- no activity within window
            segment_users["Inactive"].append(uid)
            detailed.append(
                UserSegmentDetail(
                    user_id=uid,
                    user_name=user_name_map.get(uid),
                    segment="Inactive",
                    licenses_used=[],
                    activity_count=0,
                )
            )
            continue

        # Determine which license types the user actually accessed
        licenses_used: set[str] = set()
        for _, act in user_acts.iterrows():
            menu_item: str = str(act["menu_item"])
            # Prefer the security-config mapping; fall back to the
            # license_tier column in the activity data itself.
            if menu_item in menu_item_licenses:
                licenses_used.add(menu_item_licenses[menu_item])
            elif "license_tier" in act.index and pd.notna(act["license_tier"]):
                licenses_used.add(str(act["license_tier"]))

        # Classify based on license count
        if len(licenses_used) == 1:
            license_type = next(iter(licenses_used))
            segment_name = _LICENSE_TO_SEGMENT.get(
                license_type, f"{license_type}-Only"
            )
            # Ensure the segment exists in our canonical list
            if segment_name not in segment_users:
                segment_users[segment_name] = []
            segment_users[segment_name].append(uid)
        elif len(licenses_used) > 1:
            segment_name = "Mixed-Usage"
            segment_users["Mixed-Usage"].append(uid)
        else:
            # Edge case: activity exists but no license mapping found
            segment_name = "Inactive"
            segment_users["Inactive"].append(uid)

        detailed.append(
            UserSegmentDetail(
                user_id=uid,
                user_name=user_name_map.get(uid),
                segment=segment_name,
                licenses_used=sorted(licenses_used),
                activity_count=act_count,
            )
        )

    # -- Step 5: Calculate statistics --
    segments: dict[str, SegmentStats] = {}
    for seg_name in SEGMENT_NAMES:
        uid_list = segment_users.get(seg_name, [])
        count = len(uid_list)
        pct = (count / total_users * 100.0) if total_users > 0 else 0.0
        segments[seg_name] = SegmentStats(
            count=count,
            percentage=round(pct, 2),
            user_ids=uid_list,
        )

    return UserSegmentAnalysis(
        algorithm_id="1.2",
        role_name=role_name,
        total_users=total_users,
        segments=segments,
        detailed_breakdown=detailed,
    )
