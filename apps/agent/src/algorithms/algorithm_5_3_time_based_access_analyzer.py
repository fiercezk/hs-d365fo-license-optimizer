"""Algorithm 5.3: Time-Based Access Analyzer.

Detects after-hours and anomalous time-based access patterns in D365 FO
user activity telemetry. Identifies access outside configurable business
hours, weekend access, and high-risk actions performed outside normal
working periods.

Severity hierarchy:
- MEDIUM: Weekday after-hours read operation
- HIGH: Weekday after-hours write operation, or any weekend access
- CRITICAL: High-risk menu item accessed after hours

Configurable parameters:
- business_hours_start: Start of business hours (default 6, i.e. 06:00)
- business_hours_end: End of business hours (default 18, i.e. 18:00)
- high_risk_menu_items: List of menu items considered high-risk

See Requirements/07-Advanced-Algorithms-Expansion.md (Algorithm 5.3).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field


class TimeBasedAccessAlert(BaseModel):
    """Individual security alert for anomalous time-based access.

    Generated when a user accesses the system outside defined business
    hours or on weekends, with severity determined by the nature of the
    access (read vs write) and whether the menu item is high-risk.
    """

    user_id: str = Field(description="User identifier")
    alert_type: str = Field(
        description=(
            "Type of alert: AFTER_HOURS_ACCESS, WEEKEND_ACCESS, "
            "HIGH_RISK_AFTER_HOURS"
        )
    )
    severity: str = Field(
        description="Alert severity: MEDIUM, HIGH, or CRITICAL"
    )
    timestamp: str = Field(
        description="Timestamp of the flagged access event"
    )
    menu_item: str = Field(description="Menu item accessed")
    action: str = Field(description="Action performed (Read/Write/etc.)")
    description: str = Field(
        description="Human-readable description of the alert"
    )


class TimeBasedAccessAnalysis(BaseModel):
    """Complete output from Algorithm 5.3: Time-Based Access Analyzer.

    Aggregates all time-based access alerts with summary statistics
    about the analyzed activity period.
    """

    algorithm_id: str = Field(
        default="5.3", description="Algorithm identifier"
    )
    alerts: list[TimeBasedAccessAlert] = Field(
        default_factory=list,
        description="List of generated security alerts",
    )
    total_operations_analyzed: int = Field(
        default=0,
        description="Total number of operations in the input data",
        ge=0,
    )
    after_hours_operations: int = Field(
        default=0,
        description="Number of operations outside business hours (weekdays)",
        ge=0,
    )
    weekend_operations: int = Field(
        default=0,
        description="Number of operations on weekends",
        ge=0,
    )
    unique_users_after_hours: int = Field(
        default=0,
        description="Count of distinct users with any after-hours or weekend access",
        ge=0,
    )


def analyze_time_based_access(
    user_activity: pd.DataFrame,
    *,
    business_hours_start: int = 6,
    business_hours_end: int = 18,
    high_risk_menu_items: Optional[list[str]] = None,
) -> TimeBasedAccessAnalysis:
    """Analyze user activity for after-hours and weekend access patterns.

    Scans user activity telemetry to detect access events that fall
    outside defined business hours or occur on weekends. High-risk
    menu items accessed after hours are escalated to CRITICAL severity.

    Algorithm 5.3 - Time-Based Access Analyzer.
    See Requirements/07-Advanced-Algorithms-Expansion.md.

    Args:
        user_activity: DataFrame with columns: user_id, timestamp,
            menu_item, action, session_id, license_tier, feature.
        business_hours_start: Hour (0-23) when business hours begin.
            Access at exactly this hour is considered within hours.
            Default: 6 (06:00).
        business_hours_end: Hour (0-23) when business hours end.
            Access at exactly this hour is considered outside hours.
            Default: 18 (18:00).
        high_risk_menu_items: Menu items that trigger CRITICAL alerts
            when accessed after hours. Default: empty list.

    Returns:
        TimeBasedAccessAnalysis with alerts and summary statistics.
    """
    if high_risk_menu_items is None:
        high_risk_menu_items = []

    high_risk_set: set[str] = set(high_risk_menu_items)

    # Handle empty input
    if user_activity.empty:
        return TimeBasedAccessAnalysis()

    # Pre-convert timestamps once (O(N) not O(N^2))
    timestamps = pd.to_datetime(user_activity["timestamp"])
    hours = timestamps.dt.hour
    day_of_week = timestamps.dt.dayofweek  # 0=Monday ... 6=Sunday

    # Identify weekend rows (Saturday=5, Sunday=6)
    is_weekend = day_of_week >= 5

    # Identify after-hours rows on weekdays
    is_after_hours = (~is_weekend) & (
        (hours < business_hours_start) | (hours >= business_hours_end)
    )

    total_ops = len(user_activity)
    after_hours_count = int(is_after_hours.sum())
    weekend_count = int(is_weekend.sum())

    # Build alerts
    alerts: list[TimeBasedAccessAlert] = []

    # Flagged indices: union of weekend and after-hours
    flagged_mask = is_weekend | is_after_hours

    # Collect unique users with any flagged access
    flagged_users: set[str] = set()

    for idx in user_activity.index[flagged_mask]:
        row = user_activity.loc[idx]
        user_id: str = str(row["user_id"])
        menu_item: str = str(row["menu_item"])
        action: str = str(row["action"])
        ts_str: str = str(row["timestamp"])
        on_weekend: bool = bool(is_weekend.loc[idx])

        flagged_users.add(user_id)

        # Determine alert type and severity
        alert_type, severity, description = _classify_alert(
            user_id=user_id,
            menu_item=menu_item,
            action=action,
            ts_str=ts_str,
            on_weekend=on_weekend,
            high_risk_set=high_risk_set,
        )

        alerts.append(
            TimeBasedAccessAlert(
                user_id=user_id,
                alert_type=alert_type,
                severity=severity,
                timestamp=ts_str,
                menu_item=menu_item,
                action=action,
                description=description,
            )
        )

    return TimeBasedAccessAnalysis(
        alerts=alerts,
        total_operations_analyzed=total_ops,
        after_hours_operations=after_hours_count,
        weekend_operations=weekend_count,
        unique_users_after_hours=len(flagged_users),
    )


def _classify_alert(
    *,
    user_id: str,
    menu_item: str,
    action: str,
    ts_str: str,
    on_weekend: bool,
    high_risk_set: set[str],
) -> tuple[str, str, str]:
    """Classify an after-hours access event into alert type and severity.

    Severity hierarchy (highest wins):
    1. CRITICAL - high-risk menu item accessed after hours (any day)
    2. HIGH - weekend access OR weekday after-hours write
    3. MEDIUM - weekday after-hours read

    Args:
        user_id: User identifier.
        menu_item: Menu item accessed.
        action: Action performed (Read/Write/etc.).
        ts_str: Timestamp string for the event.
        on_weekend: Whether the event occurred on a weekend.
        high_risk_set: Set of high-risk menu item names.

    Returns:
        Tuple of (alert_type, severity, description).
    """
    is_write = action.lower() not in ("read",)
    is_high_risk = menu_item in high_risk_set

    # Highest priority: high-risk after hours
    if is_high_risk:
        return (
            "HIGH_RISK_AFTER_HOURS",
            "CRITICAL",
            (
                f"User {user_id} accessed high-risk item '{menu_item}' "
                f"({action}) at {ts_str}"
            ),
        )

    # Weekend access
    if on_weekend:
        return (
            "WEEKEND_ACCESS",
            "HIGH",
            (
                f"User {user_id} accessed '{menu_item}' ({action}) "
                f"on weekend at {ts_str}"
            ),
        )

    # Weekday after-hours
    if is_write:
        return (
            "AFTER_HOURS_ACCESS",
            "HIGH",
            (
                f"User {user_id} performed write operation on "
                f"'{menu_item}' after hours at {ts_str}"
            ),
        )

    # Weekday after-hours read (lowest severity for flagged events)
    return (
        "AFTER_HOURS_ACCESS",
        "MEDIUM",
        (
            f"User {user_id} accessed '{menu_item}' (Read) "
            f"after hours at {ts_str}"
        ),
    )
