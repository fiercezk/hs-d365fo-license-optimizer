"""
Algorithm 3.4: Toxic Combination Detector

Detects dangerous multi-role combinations that enable fraud beyond basic SoD violations.
Users with all roles in a toxic pattern can control complete business cycles (e.g., full
Procure-to-Pay: create vendors + place POs + approve payments).

See Requirements/07-Advanced-Algorithms-Expansion.md Algorithm 3.4

Author: D365 FO License Agent
Created: 2026-02-06
"""

from typing import Any, Dict, List, Set


def detect_toxic_combinations(
    user_id: str,
    user_name: str,
    user_roles: List[str],
    toxic_rules: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detect toxic role combinations for a single user.

    Algorithm checks if user possesses ALL roles required for any enabled toxic pattern.
    Partial matches do not trigger alerts - user must have complete toxic combination.

    Args:
        user_id: User identifier (e.g., "USR001")
        user_name: User display name (e.g., "Alice Johnson")
        user_roles: List of role names assigned to user
        toxic_rules: List of toxic combination rule dictionaries from config

    Returns:
        List of toxic combination alerts. Each alert contains:
        - user_id: User identifier
        - user_name: User display name
        - rule_id: Toxic rule identifier (e.g., "TOXIC-001")
        - risk_type: Risk category (e.g., "Full Procure-to-Pay Control")
        - risk_description: Detailed fraud scenario explanation
        - matched_roles: List of user's roles that matched the toxic pattern
        - combined_privileges: Dangerous capabilities enabled by combination
        - severity: CRITICAL or HIGH
        - recommendation: Remediation guidance
        - fraud_scenario: Example fraud exploit path
        - regulatory_reference: Compliance frameworks (SOX, COSO)

    Examples:
        >>> toxic_rules = [{
        ...     "rule_id": "TOXIC-001",
        ...     "risk_type": "Full Procure-to-Pay Control",
        ...     "roles": ["Purchasing agent", "Vendor master", "AP clerk"],
        ...     "severity": "CRITICAL",
        ...     "is_enabled": True,
        ...     ...
        ... }]
        >>> user_roles = ["Purchasing agent", "Vendor master", "AP clerk"]
        >>> alerts = detect_toxic_combinations("USR001", "Alice", user_roles, toxic_rules)
        >>> len(alerts)
        1
        >>> alerts[0]["severity"]
        'CRITICAL'

    Notes:
        - Only enabled rules (is_enabled=True) are evaluated
        - User must have ALL roles in toxic pattern (no partial matches)
        - Case-sensitive role name matching
        - Returns empty list if no toxic combinations detected
    """
    alerts: List[Dict[str, Any]] = []

    # Convert user roles to set for efficient subset checking
    user_role_set: Set[str] = set(user_roles)

    # Check each toxic rule
    for rule in toxic_rules:
        # Skip disabled rules
        if not rule.get("is_enabled", True):
            continue

        # Get required roles for this toxic pattern
        required_roles: Set[str] = set(rule["roles"])

        # Check if user has ALL required roles (complete toxic combination)
        if required_roles.issubset(user_role_set):
            # User has toxic combination - create alert
            alert = {
                "user_id": user_id,
                "user_name": user_name,
                "rule_id": rule["rule_id"],
                "risk_type": rule["risk_type"],
                "risk_description": rule["description"],
                "matched_roles": list(required_roles),
                "combined_privileges": rule["combined_privileges"],
                "severity": rule["severity"],
                "recommendation": rule["remediation"],
                "fraud_scenario": rule.get("fraud_scenario", ""),
                "regulatory_reference": rule.get("regulatory_reference", ""),
            }
            alerts.append(alert)

    return alerts


def detect_toxic_combinations_batch(
    users: List[Dict[str, Any]], toxic_rules: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Detect toxic combinations for multiple users in batch.

    Args:
        users: List of user dictionaries with keys: user_id, user_name, roles
        toxic_rules: List of toxic combination rule dictionaries

    Returns:
        List of all toxic combination alerts across all users

    Example:
        >>> users = [
        ...     {"user_id": "USR001", "user_name": "Alice", "roles": ["A", "B", "C"]},
        ...     {"user_id": "USR002", "user_name": "Bob", "roles": ["X", "Y"]},
        ... ]
        >>> toxic_rules = [{"rule_id": "T001", "roles": ["A", "B", "C"], ...}]
        >>> alerts = detect_toxic_combinations_batch(users, toxic_rules)
        >>> len(alerts)
        1
    """
    all_alerts: List[Dict[str, Any]] = []

    for user in users:
        alerts = detect_toxic_combinations(
            user_id=user["user_id"],
            user_name=user["user_name"],
            user_roles=user.get("roles", []),
            toxic_rules=toxic_rules,
        )
        all_alerts.extend(alerts)

    return all_alerts
