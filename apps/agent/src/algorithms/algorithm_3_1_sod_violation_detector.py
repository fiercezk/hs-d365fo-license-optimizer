"""Algorithm 3.1: Segregation of Duties (SoD) Violation Detector.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md (Algorithm 3.1)
Reference: Requirements/15-Default-SoD-Conflict-Matrix.md

Purpose:
    Automatically detect users with conflicting role assignments that violate
    internal controls and compliance requirements (SOX 404, ISO 27001, GDPR).

Business Value:
    - Compliance: SOX Section 404 requires SoD for financial processes
    - Risk Reduction: Prevent fraud (e.g., vendor creation + payment approval)
    - Audit Readiness: Automated evidence for auditors
    - Cost Avoidance: Fines for compliance violations

Algorithm Logic:
    1. Load SoD conflict matrix (27 default rules from sod_matrix.json)
    2. For each user, get assigned roles
    3. Check all role pairs against SoD matrix
    4. Flag violations with severity (CRITICAL/HIGH/MEDIUM)
    5. Return list of conflicts per user, sorted by severity
"""

import json
from itertools import combinations
from pathlib import Path
from typing import Any

from ..models.input_schemas import UserRoleAssignment
from ..models.output_schemas import SODViolation, SeverityLevel


class SODMatrixLoader:
    """Loads and manages the SoD conflict matrix from JSON."""

    _instance: "SODMatrixLoader | None" = None
    _matrix_data: list[dict[str, Any]] | None = None

    def __new__(cls) -> "SODMatrixLoader":
        """Singleton pattern to ensure matrix is loaded only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_matrix(self) -> list[dict[str, Any]]:
        """Load SoD conflict rules from sod_matrix.json.

        Returns:
            List of conflict rule dictionaries from the matrix

        Raises:
            FileNotFoundError: If sod_matrix.json does not exist
            json.JSONDecodeError: If JSON is malformed
        """
        if self._matrix_data is not None:
            return self._matrix_data

        # Load from data/config/sod_matrix.json
        matrix_path = Path("data/config/sod_matrix.json")

        if not matrix_path.exists():
            raise FileNotFoundError(f"SoD matrix file not found at {matrix_path.absolute()}")

        with open(matrix_path, "r") as f:
            matrix_json = json.load(f)

        # Extract rules array
        rules_data: list[dict[str, Any]] = matrix_json.get("rules", [])

        if not rules_data:
            raise ValueError("SoD matrix JSON has no 'rules' array")

        # Cache the rules
        self._matrix_data = rules_data

        return rules_data

    def build_lookup_index(
        self, rules: list[dict[str, Any]]
    ) -> dict[tuple[str, str], dict[str, Any]]:
        """Build bidirectional lookup index from rule list.

        Creates a dictionary keyed by (role_a, role_b) and (role_b, role_a)
        to enable fast conflict checking regardless of role order.

        Args:
            rules: List of conflict rules from matrix

        Returns:
            Dictionary indexed by role pairs (both directions)
        """
        index: dict[tuple[str, str], dict[str, Any]] = {}

        for rule in rules:
            # Only index enabled rules
            if not rule.get("is_enabled", True):
                continue

            role_a = rule["role_a"]
            role_b = rule["role_b"]

            # Add both directions to support role pair matching
            # regardless of assignment order
            index[(role_a, role_b)] = rule
            index[(role_b, role_a)] = rule

        return index


def detect_sod_violations(
    user_roles: list[UserRoleAssignment],
) -> list[SODViolation]:
    """Detect SoD violations in user role assignments.

    Main entry point for Algorithm 3.1. Analyzes all user role assignments
    and detects violations against the SoD conflict matrix.

    Args:
        user_roles: List of user-to-role assignments (from D365 FO)

    Returns:
        List of SODViolation objects, sorted by severity (CRITICAL first)
    """
    if not user_roles:
        return []

    # Load conflict matrix
    loader = SODMatrixLoader()
    rules = loader.load_matrix()
    conflict_index = loader.build_lookup_index(rules)

    # Group roles by user
    user_roles_map: dict[str, list[dict[str, Any]]] = {}

    for assignment in user_roles:
        if assignment.user_id not in user_roles_map:
            user_roles_map[assignment.user_id] = []

        user_roles_map[assignment.user_id].append(
            {
                "user_id": assignment.user_id,
                "user_name": assignment.user_name,
                "user_email": assignment.email,
                "role_name": assignment.role_name,
                "role_id": assignment.role_id,
                "status": assignment.status,
            }
        )

    # Check each user for violations
    violations: list[SODViolation] = []

    for user_id, roles in user_roles_map.items():
        # Extract role names for conflict checking
        role_names = [r["role_name"] for r in roles]

        # Get user info (use first role assignment since all share same user info)
        user_name = roles[0]["user_name"]
        user_email = roles[0]["user_email"]

        # Check all combinations of roles for conflicts
        for role_a, role_b in combinations(role_names, 2):
            # Check if this pair conflicts
            conflict_rule = conflict_index.get((role_a, role_b))

            if conflict_rule:
                # Found a conflict - create violation record
                severity = SeverityLevel(conflict_rule["severity"])
                sla = _get_sla_hours(severity)

                violation = SODViolation(
                    rule_id=conflict_rule["rule_id"],
                    user_id=user_id,
                    user_name=user_name,
                    user_email=user_email,
                    role_a=role_a,
                    role_b=role_b,
                    conflict_type=conflict_rule["conflict_type"],
                    severity=severity,
                    risk_description=conflict_rule["risk_description"],
                    regulatory_reference=conflict_rule["regulatory_reference"],
                    sla_hours=sla,
                )

                violations.append(violation)

    # Sort violations by severity (CRITICAL, HIGH, MEDIUM, LOW)
    severity_order = {
        SeverityLevel.CRITICAL: 0,
        SeverityLevel.HIGH: 1,
        SeverityLevel.MEDIUM: 2,
        SeverityLevel.LOW: 3,
    }

    violations.sort(key=lambda v: severity_order[v.severity])

    return violations


def _get_sla_hours(severity: SeverityLevel) -> int:
    """Get SLA hours for a given severity level.

    Based on Requirements/15-Default-SoD-Conflict-Matrix.md
    Severity Rating Guide.

    Args:
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)

    Returns:
        SLA in hours
    """
    sla_map = {
        SeverityLevel.CRITICAL: 24,  # 1 day
        SeverityLevel.HIGH: 168,  # 7 days
        SeverityLevel.MEDIUM: 720,  # 30 days
        SeverityLevel.LOW: 2160,  # 90 days
    }
    return sla_map.get(severity, 720)
