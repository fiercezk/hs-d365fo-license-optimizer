"""Algorithm 1.3: Role Splitting Recommender.

Recommends splitting a role into multiple license-specific roles based on the
role's license composition and user segment analysis. Identifies roles with
multiple significant license types and checks whether users segment into
exclusive usage patterns. When exclusive segments exist, splitting the role
can allow users to hold lower-cost licenses instead of the combined highest
license required by the unsplit role.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 204-298.

Key Logic:
  1. Analyze the role's security configuration to determine license composition
  2. Filter to license types exceeding the significance threshold (min_percentage)
  3. Analyze user activity to identify exclusive-use segments per license type
  4. Calculate savings: (highestLicenseCost - segmentLicenseCost) * exclusiveUserCount
  5. Estimate implementation effort based on split complexity
  6. Return split recommendation with proposed roles and savings

Dependencies:
  - Builds on Algorithm 1.1 (Role License Composition) logic inline
  - Builds on Algorithm 1.2 (User Segment Analysis) logic inline
  - Uses shared pricing utility for license cost lookup
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from ..utils.pricing import get_license_price

# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------


class ProposedRole(BaseModel):
    """A proposed license-specific role variant from a split recommendation.

    Represents one segment of a role that would be split by license type,
    along with the users who exclusively use that license type and the
    potential savings from the split.
    """

    license_type: str = Field(
        description="License type for this proposed role variant (e.g., 'Finance', 'SCM')"
    )
    exclusive_user_count: int = Field(
        description="Number of users who exclusively use this license type", ge=0
    )
    menu_item_count: int = Field(
        description="Number of menu items requiring this license type", ge=0
    )
    savings_per_user_per_month: float = Field(
        description="Monthly savings per user from this split (USD)", ge=0
    )
    potential_savings_per_month: float = Field(
        description="Total monthly savings for this segment (USD)", ge=0
    )
    exclusive_users: list[str] = Field(
        description="User IDs who exclusively use this license type",
        default_factory=list,
    )


class RoleSplitRecommendation(BaseModel):
    """Complete output from Algorithm 1.3: Role Splitting Recommender.

    Contains the split recommendation, proposed role variants, savings
    estimates, and implementation effort assessment.
    """

    algorithm_id: str = Field(default="1.3", description="Algorithm identifier")
    role_name: str = Field(description="Name of the role analyzed")
    should_split: bool = Field(
        description="Whether the role should be split into license-specific variants"
    )
    rationale: str = Field(description="Human-readable explanation for the recommendation")
    proposed_roles: list[ProposedRole] = Field(
        description="Proposed license-specific role variants (empty if should_split=False)",
        default_factory=list,
    )
    total_potential_savings_per_month: float = Field(
        description="Total monthly savings across all proposed roles (USD)",
        default=0.0,
        ge=0,
    )
    implementation_effort: str = Field(
        description="Estimated effort to implement the split: Low, Medium, or High",
        default="Low",
    )
    significant_license_types: list[str] = Field(
        description="License types that exceeded the significance threshold",
        default_factory=list,
    )
    total_users_analyzed: int = Field(
        description="Total number of users assigned to this role", default=0, ge=0
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MIN_PERCENTAGE: float = 10.0
"""Default minimum percentage for a license type to be considered significant."""


# ---------------------------------------------------------------------------
# Core Algorithm
# ---------------------------------------------------------------------------


def recommend_role_split(
    role_name: str,
    security_config: pd.DataFrame,
    user_role_assignments: pd.DataFrame,
    user_activity: pd.DataFrame,
    pricing_config: dict[str, Any],
    min_percentage: float = _DEFAULT_MIN_PERCENTAGE,
) -> RoleSplitRecommendation:
    """Algorithm 1.3: Recommend whether a role should be split by license type.

    Analyzes the license composition of a role's menu items and the activity
    patterns of its assigned users to determine whether creating license-specific
    role variants would reduce license costs.

    See Requirements/06-Algorithms-Decision-Logic.md, lines 204-298.

    Args:
        role_name: Name of the security role to analyze.
        security_config: DataFrame with columns:
            - securityrole: Role name
            - AOTName: Menu item AOT name
            - LicenseType: License type required
            - AccessLevel: Access level (Read/Write/etc.)
            - Priority: License priority value
        user_role_assignments: DataFrame with columns:
            - user_id: User identifier
            - role_name: Security role name
        user_activity: DataFrame with columns:
            - user_id: User identifier
            - menu_item: Menu item accessed
            - license_tier: License tier of the activity
        pricing_config: Parsed pricing.json dictionary with license cost data.
        min_percentage: Minimum percentage of menu items a license type must
            represent to be considered significant. Default: 10.0%.

    Returns:
        RoleSplitRecommendation with split decision, proposed roles, and savings.
    """
    # Step 1: Get role's menu items and their license types from security config
    role_items = security_config[security_config["securityrole"] == role_name]

    if role_items.empty:
        return RoleSplitRecommendation(
            role_name=role_name,
            should_split=False,
            rationale=(
                f"Role '{role_name}' not found in security configuration. "
                "No menu items to analyze."
            ),
        )

    # Step 2: Analyze license composition
    license_counts: dict[str, int] = {
        str(k): int(v) for k, v in role_items["LicenseType"].value_counts().to_dict().items()
    }
    total_items: int = len(role_items)

    # Calculate percentages and filter to significant license types
    license_percentages: dict[str, float] = {
        lt: (count / total_items) * 100.0 for lt, count in license_counts.items()
    }
    significant_licenses: list[str] = [
        lt for lt, pct in license_percentages.items() if pct >= min_percentage
    ]

    # If fewer than 2 significant license types, no split needed
    if len(significant_licenses) < 2:
        highest_license = max(license_counts, key=lambda lt: license_counts[lt])
        return RoleSplitRecommendation(
            role_name=role_name,
            should_split=False,
            rationale=(
                f"Role primarily uses one license type ('{highest_license}', "
                f"{license_percentages.get(highest_license, 0.0):.1f}% of menu items). "
                "Splitting is not beneficial."
            ),
            significant_license_types=significant_licenses,
        )

    # Step 3: Get users assigned to this role
    role_users = user_role_assignments[user_role_assignments["role_name"] == role_name]
    user_ids: list[str] = role_users["user_id"].unique().tolist()
    total_users: int = len(user_ids)

    if total_users == 0:
        return RoleSplitRecommendation(
            role_name=role_name,
            should_split=False,
            rationale=(
                f"No users assigned to role '{role_name}'. " "Cannot analyze usage segments."
            ),
            significant_license_types=significant_licenses,
        )

    # Step 4: Analyze user activity to find exclusive segments
    # For each user, determine which license types they access
    user_license_usage: dict[str, set[str]] = {}
    for uid in user_ids:
        user_acts = user_activity[user_activity["user_id"] == uid]
        if user_acts.empty:
            continue

        # Determine license types from activity
        if "license_tier" in user_activity.columns:
            used_types: set[str] = set(user_acts["license_tier"].unique())
        else:
            # Fall back to matching menu items against security config
            used_items = set(user_acts["menu_item"].unique())
            used_types = set()
            for _, row in role_items.iterrows():
                if row["AOTName"] in used_items:
                    used_types.add(str(row["LicenseType"]))

        # Only consider significant license types
        used_significant = used_types & set(significant_licenses)
        if used_significant:
            user_license_usage[uid] = used_significant

    # Step 5: Identify exclusive segments (users using only one license type)
    exclusive_segments: dict[str, list[str]] = {lt: [] for lt in significant_licenses}
    for uid, used_types in user_license_usage.items():
        if len(used_types) == 1:
            license_type = next(iter(used_types))
            if license_type in exclusive_segments:
                exclusive_segments[license_type].append(uid)

    # Step 6: Determine the combined license cost for the unsplit role.
    # When a role spans multiple license types, users must hold stacked
    # licenses covering all types (see pricing.json multiLicenseStacking).
    # The current cost per user is the SUM of all significant license prices.
    combined_license_cost: float = 0.0
    license_prices: dict[str, float] = {}
    for lt in significant_licenses:
        try:
            cost = get_license_price(pricing_config, lt)
            license_prices[lt] = cost
            combined_license_cost += cost
        except KeyError:
            continue

    # Step 7: Build proposed roles for segments with exclusive users
    proposed_roles: list[ProposedRole] = []
    for lt in significant_licenses:
        exclusive_users = exclusive_segments.get(lt, [])
        if len(exclusive_users) == 0:
            continue

        segment_cost = license_prices.get(lt, 0.0)
        if segment_cost == 0.0:
            continue

        savings_per_user = max(0.0, combined_license_cost - segment_cost)
        total_savings = savings_per_user * len(exclusive_users)

        proposed_roles.append(
            ProposedRole(
                license_type=lt,
                exclusive_user_count=len(exclusive_users),
                menu_item_count=license_counts.get(lt, 0),
                savings_per_user_per_month=savings_per_user,
                potential_savings_per_month=total_savings,
                exclusive_users=exclusive_users,
            )
        )

    # Step 8: If no proposed roles with exclusive users, no split
    if not proposed_roles:
        return RoleSplitRecommendation(
            role_name=role_name,
            should_split=False,
            rationale=(
                "No user segment exclusively uses a single license type. "
                "All users have mixed usage patterns."
            ),
            significant_license_types=significant_licenses,
            total_users_analyzed=total_users,
        )

    # Step 9: Calculate total savings and estimate effort
    total_savings_per_month: float = sum(r.potential_savings_per_month for r in proposed_roles)
    effort = _estimate_effort(
        proposed_roles=proposed_roles,
        total_users=total_users,
    )

    return RoleSplitRecommendation(
        role_name=role_name,
        should_split=True,
        rationale=(
            "Role can be split to optimize license costs based on actual " "usage patterns."
        ),
        proposed_roles=proposed_roles,
        total_potential_savings_per_month=total_savings_per_month,
        implementation_effort=effort,
        significant_license_types=significant_licenses,
        total_users_analyzed=total_users,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _estimate_effort(
    proposed_roles: list[ProposedRole],
    total_users: int,
) -> str:
    """Estimate implementation effort for a role split.

    Heuristic based on number of proposed role variants and total user count:
      - Low: 2 variants AND fewer than 50 users
      - High: 4+ variants OR 200+ users
      - Medium: everything else

    Args:
        proposed_roles: List of proposed role variants.
        total_users: Total number of users assigned to the role.

    Returns:
        Effort estimate string: "Low", "Medium", or "High".
    """
    num_variants = len(proposed_roles)

    if num_variants >= 4 or total_users >= 200:
        return "High"
    if num_variants <= 2 and total_users < 50:
        return "Low"
    return "Medium"
