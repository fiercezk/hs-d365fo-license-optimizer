"""Algorithm 3.2: Anomalous Role Change Detector.

Detects suspicious or unauthorized role assignment changes that could indicate
security breaches or insider threats.

Business Value:
  - Security: Detect compromised accounts (attackers adding roles)
  - Insider Threat: Identify privilege escalation before damage
  - Compliance: Maintain audit trail for all changes
  - Operational: Catch accidental role assignments

Input Data Required:
  - AuditLogs: Role assignment changes (who, when, what)
  - UserRoleAssignments: Current state
  - UserActivityData: Post-change behavior (optional)
  - BaselineData: Normal change patterns (optional)

Output Structure:
  - Change ID: Unique identifier
  - User Affected: Name/ID
  - Role Changed: Role name
  - Action: Assigned/Removed
  - Changed By: Admin/Service Account
  - Timestamp: DateTime
  - Anomaly Score: 0-100
  - Anomaly Reasons: List of detected anomalies
  - Risk Level: Critical/High/Medium/Low
  - Recommendation: Action

Risk Level Calculation:
  - >= 90: CRITICAL (Immediate investigation required)
  - >= 70: HIGH (Investigation within 24 hours)
  - >= 50: MEDIUM (Investigation within 7 days)
  - < 50: LOW (Informational)

See Requirements/07-Advanced-Algorithms-Expansion.md, Algorithm 3.2.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd


def detect_anomalous_role_changes(
    role_changes: pd.DataFrame,
    time_window_days: int = 7,
    user_profiles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Detect anomalous role assignment changes.

    Args:
        role_changes: DataFrame with columns:
          - change_id: Unique change identifier
          - user_affected: User ID
          - user_name: User display name
          - role_changed: Role name
          - action: "ASSIGNED" or "REMOVED"
          - changed_by: Admin/Service account that made the change
          - timestamp: ISO format datetime string
          - has_approval_workflow: Boolean
          - is_service_account_changer: Boolean
          - role_privilege_level: "HIGH", "MEDIUM", or "LOW"
        time_window_days: Look back period (default 7 days)
        user_profiles: Optional list of user profile dicts with:
          - user_id: User identifier
          - created_date: ISO format datetime string

    Returns:
        List of anomaly dictionaries with:
          - change_id: Change identifier
          - user_affected: User ID
          - user_name: User display name
          - role_changed: Role name
          - action: ASSIGNED or REMOVED
          - changed_by: Admin who made the change
          - timestamp: When the change occurred
          - anomaly_score: 0-100 score
          - anomaly_reasons: List of detected anomalies
          - risk_level: CRITICAL, HIGH, MEDIUM, or LOW
          - recommendation: Action to take

        Filtered to include only anomalies with anomaly_score >= 50 (MEDIUM+).
        Sorted by anomaly_score descending.
    """
    anomalies: list[dict[str, Any]] = []

    # Build user profile lookup if provided
    user_profile_lookup: dict[str, dict[str, Any]] = {}
    if user_profiles:
        for profile in user_profiles:
            user_profile_lookup[profile["user_id"]] = profile

    # Baseline patterns (common approvers, service account usage)
    # In a real implementation, these would come from historical data
    common_approvers: dict[str, set[str]] = {}  # role_name -> set of common approvers
    service_account_usage_frequency: dict[str, int] = {}  # service_account -> usage_count

    # Pre-convert timestamps to datetime ONCE (avoids O(N^2) pd.to_datetime in loop)
    role_changes = role_changes.copy()
    role_changes["_parsed_timestamp"] = pd.to_datetime(role_changes["timestamp"])

    # Process each role change
    for _, change in role_changes.iterrows():
        anomaly_score: int = 0
        anomaly_reasons: list[str] = []

        # Extract fields
        change_id: str = change["change_id"]
        user_affected: str = change["user_affected"]
        user_name: str = change["user_name"]
        role_changed: str = change["role_changed"]
        action: str = change["action"]
        changed_by: str = change["changed_by"]
        timestamp_str: str = change["timestamp"]
        has_approval: bool = change["has_approval_workflow"]
        is_service_account: bool = change["is_service_account_changer"]
        role_privilege: str = change["role_privilege_level"]

        # Parse timestamp
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = timestamp_str
        except (ValueError, TypeError):
            # Invalid timestamp, skip this change
            continue

        # Skip role removals (de-escalation is not a threat)
        # Only score ASSIGNMENTS for security risk
        if action != "ASSIGNED":
            continue

        # Check 1: Time-based anomaly
        # Lines 304-315 in pseudocode
        hour = timestamp.hour
        day_of_week = timestamp.weekday()  # 0=Monday, 5=Saturday, 6=Sunday

        time_anomaly_score = 0

        if hour < 6 or hour > 18:  # Outside 6 AM - 6 PM
            time_anomaly_score += 30
            anomaly_reasons.append(f"After-hours change at {hour}:00 UTC")

        if day_of_week in [5, 6]:  # Saturday or Sunday
            time_anomaly_score += 20
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            anomaly_reasons.append(f"Weekend change ({day_names[day_of_week]})")

        # Amplify time-based anomalies for high-privilege roles
        # After-hours + high-privilege is inherently more suspicious
        if time_anomaly_score > 0 and role_privilege == "HIGH":
            # Double the time-based score for high-privilege roles
            time_anomaly_score = time_anomaly_score * 2
            anomaly_reasons.append("High-privilege role assigned outside normal hours")

        anomaly_score += time_anomaly_score

        # Check 2: Approver anomaly
        # Lines 317-321 in pseudocode
        if is_service_account:
            # Will handle in Check 6
            pass
        elif changed_by not in common_approvers.get(role_changed, set()):
            # Unusual approver (not in common approvers list)
            # For baseline data, consider it anomalous if not a standard admin
            if not _is_standard_admin(changed_by):
                anomaly_score += 25
                anomaly_reasons.append(f"Changed by unusual approver: {changed_by}")

        # Check 3: Role privilege level for new users
        # Lines 323-332 in pseudocode
        if role_privilege == "HIGH" and action == "ASSIGNED":
            user_age_days = _get_user_age_days(user_affected, user_profile_lookup)
            if user_age_days is not None and user_age_days < 30:
                anomaly_score += 70  # Very high severity: new user + high privilege
                anomaly_reasons.append(
                    f"High-privilege role assigned to new user ({user_age_days} days old)"
                )

        # Check 4: Rapid successive changes
        # Lines 334-342 in pseudocode
        # Count other changes for same user within 1 hour
        one_hour_ago = timestamp - timedelta(hours=1)
        recent_changes = role_changes[
            (role_changes["user_affected"] == user_affected)
            & (role_changes["_parsed_timestamp"] >= one_hour_ago)
            & (role_changes["_parsed_timestamp"] <= timestamp)
        ]
        rapid_change_count = len(recent_changes)

        if rapid_change_count >= 3:  # 3+ changes in 1 hour is suspicious
            anomaly_score += 70  # Privilege escalation pattern is very serious
            anomaly_reasons.append(
                f"Rapid role changes: {rapid_change_count} changes within 1 hour"
            )

        # Check 5: Missing approval for high-privilege roles
        # Lines 344-351 in pseudocode
        if role_privilege == "HIGH" and not has_approval:
            anomaly_score += 60  # Compliance risk: no approval trail
            anomaly_reasons.append("High-privilege role assigned without approval")

        # Check 6: Service account usage
        # Lines 353-360 in pseudocode
        if is_service_account:
            # Service account usage frequency would come from historical baseline
            # For now, any service account making a role change is highly anomalous
            # unless explicitly in common baseline (which is empty by default)
            usage_freq = service_account_usage_frequency.get(changed_by, 0)
            # Most service accounts never make role changes, so treat as anomalous by default
            # Only skip if usage_freq is very high (> 50), which would be unusual
            if usage_freq <= 5:  # Default or very rare
                anomaly_score += 70  # Very high severity: service account making role change
                anomaly_reasons.append(
                    f"Changed by service account (unusual pattern): {changed_by}"
                )

        # Calculate risk level based on score
        # Lines 391-396 in pseudocode
        if anomaly_score >= 90:
            risk_level = "CRITICAL"
        elif anomaly_score >= 70:
            risk_level = "HIGH"
        elif anomaly_score >= 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Only include anomalies with score >= 50 (MEDIUM+)
        if anomaly_score >= 50:
            anomalies.append(
                {
                    "change_id": change_id,
                    "user_affected": user_affected,
                    "user_name": user_name,
                    "role_changed": role_changed,
                    "action": action,
                    "changed_by": changed_by,
                    "timestamp": timestamp_str,
                    "anomaly_score": anomaly_score,
                    "anomaly_reasons": anomaly_reasons,
                    "risk_level": risk_level,
                    "recommendation": _generate_recommendation(
                        user_affected, role_changed, risk_level, anomaly_reasons
                    ),
                }
            )

    # Sort by anomaly score (descending)
    anomalies.sort(key=lambda x: x["anomaly_score"], reverse=True)

    return anomalies


def _is_standard_admin(approver_name: str) -> bool:
    """Check if approver is a standard system admin (known/trusted).

    In production, this would check against a list of approved admins
    from the system administrator role.

    Args:
        approver_name: Admin identifier

    Returns:
        True if standard admin, False otherwise.
    """
    # Standard admin pattern: starts with ADMIN_
    if approver_name.startswith("ADMIN_"):
        return True

    # In production, would check an actual admin list
    return approver_name in {"SYSTEM", "SYSADMIN", "ROOT"}


def _get_user_age_days(
    user_id: str,
    user_profile_lookup: dict[str, dict[str, Any]],
) -> int | None:
    """Calculate user age in days.

    Args:
        user_id: User identifier
        user_profile_lookup: Dictionary of user profiles with created_date

    Returns:
        User age in days, or None if profile not found.
    """
    if user_id not in user_profile_lookup:
        return None

    profile = user_profile_lookup[user_id]
    created_date_str = profile.get("created_date")

    if not created_date_str:
        return None

    try:
        created_date = datetime.fromisoformat(created_date_str)
        # Make created_date timezone-aware if needed
        if created_date.tzinfo is None:
            created_date = created_date.replace(tzinfo=UTC)

        # Use current time with proper timezone handling
        now = datetime.now(UTC)
        # Ensure both are timezone-aware for subtraction
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        age_delta = now - created_date
        age = age_delta.days
        return age
    except (ValueError, TypeError, AttributeError):
        return None


def _generate_recommendation(
    user_id: str,
    role_changed: str,
    risk_level: str,
    anomaly_reasons: list[str],
) -> str:
    """Generate remediation recommendation based on risk level.

    Args:
        user_id: User affected
        role_changed: Role that was changed
        risk_level: CRITICAL, HIGH, MEDIUM, or LOW
        anomaly_reasons: List of detected anomalies

    Returns:
        Recommendation text.
    """
    if risk_level == "CRITICAL":
        return (
            f"IMMEDIATE ACTION REQUIRED: Verify if user {user_id} "
            f"should have {role_changed}. Account may be compromised. "
            f"Revoke access if unauthorized."
        )
    elif risk_level == "HIGH":
        return (
            f"Investigate within 24 hours: User {user_id} received "
            f"{role_changed} under suspicious circumstances. "
            f"Confirm authorization."
        )
    elif risk_level == "MEDIUM":
        return (
            f"Review within 7 days: User {user_id} received {role_changed} "
            f"with some unusual patterns. Routine investigation recommended."
        )
    else:  # LOW
        return f"Informational: Role change for user {user_id}. " f"No immediate action required."
