"""Algorithm 4.7: New User License Recommendation Engine.

Recommends optimal license for new users based on required menu items,
before they have usage history. Implements the menu-items-first approach
(Interpretation B) as specified in Requirements/07-Advanced-Algorithms-Expansion.md.

The algorithm:
1. Builds a reverse-index: menu_item → [roles that provide it]
2. Uses greedy set-covering approximation to find minimum role combinations
3. Determines license type for each role combination
4. Cross-validates with SoD conflicts (Algorithm 3.1)
5. Returns top-3 recommendations sorted by cost, then role count

Key inputs:
- SecurityConfigurationData: Role → Menu Item → License mapping
- RequiredMenuItems: List of menu items the new user needs access to
- LicensePricingTable: Current license costs

Output: Top-3 license recommendations with roles, cost, coverage %, SoD status
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field

import pandas as pd

from ..models.input_schemas import SecurityConfigRecord


@dataclass
class LicenseRecommendationOption:
    """Single recommendation option from Algorithm 4.7.

    Represents one viable role+license combination to cover the requested
    menu items.
    """

    recommended_roles: list[str]
    role_count: int
    license_required: str
    monthly_cost: float
    menu_item_coverage: float  # 0.0 to 1.0
    sod_conflicts: int  # Count of SoD conflicts in this role set
    confidence: str  # HIGH, MEDIUM, LOW
    warnings: list[str] = field(default_factory=list)
    uncovered_items: list[str] = field(default_factory=list)


class NewUserLicenseRecommender:
    """Main recommender class for Algorithm 4.7.

    Builds reverse-index of security configuration and provides license
    recommendations based on requested menu items.
    """

    def __init__(
        self,
        security_config: list[SecurityConfigRecord],
        pricing_config: dict[str, Any],
    ):
        """Initialize the recommender with security config and pricing.

        Args:
            security_config: List of SecurityConfigRecord objects from D365 FO
            pricing_config: Dictionary loaded from data/config/pricing.json
        """
        self.security_config = security_config
        self.pricing_config = pricing_config

        # Convert to DataFrame for easier operations
        self.config_df = self._convert_to_dataframe(security_config)

        # Build reverse index: menu_item → [roles that provide it]
        self.reverse_index: dict[str, list[str]] = self._build_reverse_index()

        # Build role → license mapping
        self.role_license_map: dict[str, str] = self._build_role_license_map()

        # License priority mapping for determining "highest" license
        self.license_priority_map: dict[str, int] = self._build_license_priority_map()

    def _convert_to_dataframe(self, config: list[SecurityConfigRecord]) -> pd.DataFrame:
        """Convert security config records to DataFrame.

        Args:
            config: List of SecurityConfigRecord

        Returns:
            DataFrame with columns: security_role, aot_name, license_type, etc.
        """
        data = []
        for record in config:
            data.append(
                {
                    "security_role": record.security_role,
                    "aot_name": record.aot_name,
                    "access_level": record.access_level.value,
                    "license_type": record.license_type.value,
                    "priority": record.priority,
                    "entitled": record.entitled,
                    "not_entitled": record.not_entitled,
                    "security_type": record.security_type.value,
                }
            )
        return pd.DataFrame(data)

    def _build_reverse_index(self) -> dict[str, list[str]]:
        """Build reverse index: menu_item → [roles that provide it].

        Specification line 1720-1725: "REVERSE_INDEX: MenuItemA → [Role1, Role2, Role5]"

        Returns:
            Dictionary mapping menu_item name to list of role names that provide it
        """
        reverse_index: dict[str, list[str]] = {}

        # Group by AOT name (menu item) and collect unique roles
        for menu_item, group in self.config_df.groupby("aot_name"):
            roles = group["security_role"].unique().tolist()
            reverse_index[str(menu_item)] = roles

        return reverse_index

    def _build_role_license_map(self) -> dict[str, str]:
        """Build mapping: role → highest license required by that role.

        When a role appears in multiple licenses, take the highest-priority one.

        Returns:
            Dictionary mapping role name to license type
        """
        role_license: dict[str, str] = {}

        # For each role, find the highest-priority license it appears in
        for role, group in self.config_df.groupby("security_role"):
            # Sort by priority descending, take first (highest priority = most expensive)
            highest_license_row = group.sort_values("priority", ascending=False).iloc[0]
            role_license[str(role)] = str(highest_license_row["license_type"])

        return role_license

    def _build_license_priority_map(self) -> dict[str, int]:
        """Build priority mapping for license types (used to determine "highest").

        Returns:
            Dictionary mapping license name to priority (higher = more expensive)
        """
        # Default priorities based on pricing
        default_priorities = {
            "Team Members": 60,
            "Operations - Activity": 30,
            "Operations": 90,
            "SCM": 180,
            "Finance": 180,
            "Commerce": 180,
            "Device License": 80,
        }

        # Try to use pricing config if available
        priority_map = {}
        for license_key, license_info in self.pricing_config.get("licenses", {}).items():
            license_name = license_info.get("name", license_key)
            priority = int(license_info.get("priority", 0))
            if priority == 0:
                # Fall back to default
                priority = default_priorities.get(license_name, 0)
            priority_map[license_name] = priority

        # Ensure all standard licenses are present
        for license_name, priority in default_priorities.items():
            if license_name not in priority_map:
                priority_map[license_name] = priority

        return priority_map

    def _get_license_cost(self, license_type: str) -> float:
        """Get monthly cost for a license type.

        Args:
            license_type: License name (e.g., "Operations", "Finance")

        Returns:
            Monthly cost in USD

        Raises:
            KeyError: If license not found in pricing config
        """
        for license_key, license_info in self.pricing_config.get("licenses", {}).items():
            if license_info.get("name") == license_type:
                return float(license_info.get("pricePerUserPerMonth", 0))

        # Fallback: use some default costs
        defaults = {
            "Team Members": 60.0,
            "Operations - Activity": 30.0,
            "Operations": 90.0,
            "SCM": 180.0,
            "Finance": 180.0,
            "Commerce": 180.0,
            "Device License": 80.0,
        }
        return float(defaults.get(license_type, 0.0))

    def _greedy_set_cover(
        self,
        candidate_roles: dict[str, list[str]],
        max_results: int = 10,
    ) -> list[list[str]]:
        """Greedy set-covering approximation to find minimum role combinations.

        Specification line 1811-1852: GreedySetCover function

        Args:
            candidate_roles: Dict mapping menu_item → [roles that provide it]
            max_results: Maximum number of alternative solutions to generate

        Returns:
            List of role combinations, each as a list of role names
        """
        # All menu items that need to be covered
        uncovered = set(candidate_roles.keys())
        selected_roles: list[str] = []
        all_solutions: list[list[str]] = []

        # Main greedy loop: repeatedly pick the role that covers the most items
        iteration = 0
        max_iterations = 100  # Safety limit
        while uncovered and iteration < max_iterations:
            iteration += 1
            best_role: str | None = None
            best_coverage_count = 0
            best_covers: set[str] = set()
            best_role_cost = float("inf")

            # Get all candidate roles (from all uncovered items)
            all_candidate_roles = set()
            for roles_for_item in candidate_roles.values():
                all_candidate_roles.update(roles_for_item)

            # Find role that covers the most uncovered items (tie-break by cost)
            for role in all_candidate_roles:
                if role in selected_roles:
                    continue  # Already selected

                covers: set[str] = set()
                for menu_item, roles_list in candidate_roles.items():
                    if menu_item in uncovered and role in roles_list:
                        covers.add(menu_item)

                # Prefer role with more coverage, tie-break by lower cost
                role_cost = self._get_license_cost(self.role_license_map.get(role, "Team Members"))

                if len(covers) > best_coverage_count or (
                    len(covers) == best_coverage_count and role_cost < best_role_cost
                ):
                    best_coverage_count = len(covers)
                    best_role = role
                    best_covers = covers
                    best_role_cost = role_cost

            if best_role is None:
                break

            selected_roles.append(best_role)
            uncovered -= best_covers

        # First solution: greedy result
        if selected_roles:
            all_solutions.append(selected_roles)

        # Generate alternative solutions by trying different starting roles
        # (limited to bound computation)
        all_candidate_roles = set()
        for roles_list in candidate_roles.values():
            all_candidate_roles.update(roles_list)

        for attempt in range(1, min(max_results - 1, len(all_candidate_roles))):
            alt_uncovered = set(candidate_roles.keys())
            alt_selected: list[str] = []
            attempted_count = 0

            # Try greedy but starting from a different role
            while alt_uncovered and attempted_count < max_iterations:
                attempted_count += 1
                best_role_alt: str | None = None
                best_coverage_alt: float = 0.0
                best_covers_alt: set[str] = set()

                for role in all_candidate_roles:
                    if role in alt_selected:
                        continue  # Already selected

                    covers_alt: set[str] = set()
                    for menu_item, roles_list in candidate_roles.items():
                        if menu_item in alt_uncovered and role in roles_list:
                            covers_alt.add(menu_item)

                    coverage_score = len(covers_alt) - (0.1 * attempt)  # Penalize variants
                    if coverage_score > best_coverage_alt:
                        best_coverage_alt = coverage_score
                        best_role_alt = role
                        best_covers_alt = covers_alt

                if best_role_alt is None:
                    break

                alt_selected.append(best_role_alt)
                alt_uncovered -= best_covers_alt

            if alt_selected and alt_selected not in all_solutions:
                all_solutions.append(alt_selected)

            if len(all_solutions) >= max_results:
                break

        return all_solutions

    def get_recommendations(
        self,
        required_menu_items: list[str],
    ) -> list[LicenseRecommendationOption]:
        """Get top-3 license recommendations for a new user.

        Specification line 1758-1809

        Args:
            required_menu_items: List of menu item names the user needs

        Returns:
            List of up to 3 LicenseRecommendationOption objects, sorted by cost
        """
        if not required_menu_items:
            return []

        # Step 1: Build candidate roles for each menu item
        candidate_roles: dict[str, list[str]] = {}
        uncovered_items: list[str] = []

        for menu_item in required_menu_items:
            roles_with_item = self.reverse_index.get(menu_item, [])
            if not roles_with_item:
                uncovered_items.append(menu_item)
            else:
                candidate_roles[menu_item] = roles_with_item

        # If no roles cover any menu items, return empty
        if not candidate_roles:
            return []

        # Step 2: Find minimum role combinations using greedy set-covering
        optimal_role_sets = self._greedy_set_cover(candidate_roles, max_results=10)

        # Step 3: For each role set, calculate license and cost
        recommendations: list[LicenseRecommendationOption] = []

        for role_set in optimal_role_sets:
            # Determine highest license required by this role set
            highest_license = self._determine_highest_license(role_set)
            cost = self._get_license_cost(highest_license)

            # Calculate coverage percentage
            covered_items = set()
            for role in role_set:
                for menu_item, roles_list in candidate_roles.items():
                    if role in roles_list:
                        covered_items.add(menu_item)

            coverage_pct = len(covered_items) / len(required_menu_items)

            # Check SoD conflicts
            sod_conflict_count = self._check_sod_conflicts(role_set)

            # Determine confidence based on SoD status
            confidence = "HIGH" if sod_conflict_count == 0 else "MEDIUM"

            # Identify uncovered items for this recommendation
            uncovered_in_rec = [item for item in required_menu_items if item not in covered_items]

            warnings = []
            if uncovered_items:
                warnings.append(f"Menu items not found in any role: {', '.join(uncovered_items)}")
            if uncovered_in_rec:
                warnings.append(f"This recommendation doesn't cover: {', '.join(uncovered_in_rec)}")

            rec = LicenseRecommendationOption(
                recommended_roles=role_set,
                role_count=len(role_set),
                license_required=highest_license,
                monthly_cost=cost,
                menu_item_coverage=coverage_pct,
                sod_conflicts=sod_conflict_count,
                confidence=confidence,
                warnings=warnings,
                uncovered_items=uncovered_in_rec,
            )
            recommendations.append(rec)

        # Step 4: Sort by cost (ascending), then role count (ascending)
        recommendations.sort(key=lambda r: (r.monthly_cost, r.role_count))

        # Return top 3
        return recommendations[:3]

    def _determine_highest_license(self, role_set: list[str]) -> str:
        """Determine the highest-priority license required by a role set.

        When roles require different licenses, take the highest-priority one
        (most expensive, most capable).

        Args:
            role_set: List of role names

        Returns:
            License type name (e.g., "Finance")
        """
        if not role_set:
            return "Team Members"

        # Get licenses required by each role
        licenses = [self.role_license_map.get(role, "Team Members") for role in role_set]

        # Find the highest-priority license
        highest_license = licenses[0]
        highest_priority = self.license_priority_map.get(highest_license, 0)

        for license_type in licenses[1:]:
            priority = self.license_priority_map.get(license_type, 0)
            if priority > highest_priority:
                highest_license = license_type
                highest_priority = priority

        return highest_license

    def _check_sod_conflicts(self, role_set: list[str]) -> int:
        """Check for SoD conflicts in a role combination.

        For Phase 1 MVP, uses a minimal SoD matrix.
        Full matrix is in Requirements/15-Default-SoD-Conflict-Matrix.md

        Args:
            role_set: List of role names

        Returns:
            Count of SoD conflicts found
        """
        # Minimal SoD rules for Phase 1
        sod_rules = [
            # AP-002: AP Clerk + AP Manager (enter and approve)
            {
                "role_pair": {"Accounts payable clerk", "Accounts payable manager"},
                "severity": "CRITICAL",
            },
            # GL-001: GL Clerk + Accounting Manager (create and approve)
            {
                "role_pair": {"General ledger clerk", "Accounting manager"},
                "severity": "CRITICAL",
            },
        ]

        conflict_count = 0
        role_set_lower = {r.lower() for r in role_set}

        for rule in sod_rules:
            rule_pair_lower = {r.lower() for r in rule["role_pair"]}
            if rule_pair_lower.issubset(role_set_lower):
                conflict_count += 1

        return conflict_count


def suggest_license_for_new_user(
    recommender: NewUserLicenseRecommender,
    required_menu_items: list[str],
) -> list[LicenseRecommendationOption]:
    """Convenience function to get license recommendations.

    Args:
        recommender: Initialized NewUserLicenseRecommender instance
        required_menu_items: List of menu items the user needs

    Returns:
        List of up to 3 license recommendation options
    """
    return recommender.get_recommendations(required_menu_items)
