"""Algorithm 1.4: Component Removal Recommender.

Identifies low-usage, high-license menu items in a role and recommends
their removal to reduce the role's overall license requirement.

The algorithm examines each menu item assigned to a role via the security
configuration, filters for high-license types (Commerce, Finance, SCM),
and calculates what percentage of users assigned to that role actually
accessed each item in the analysis period.  Items below a configurable
usage threshold (default 5%) are flagged as removal candidates.

Candidates are sorted by impact (Low first) so the safest removals are
presented first.  Critical menu items (e.g., Posting, FinancialClosing)
are always flagged for manual review regardless of usage level.

See Requirements/06-Algorithms-Decision-Logic.md, lines 302-382.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# License types that justify component removal (high-cost tiers).
HIGH_LICENSE_TYPES: frozenset[str] = frozenset({"Commerce", "Finance", "SCM"})

# Menu items considered critical business operations that require manual
# review before removal, even when usage is below the threshold.
# These represent year-end, financial close, and posting functions whose
# absence could have material compliance or operational impact.
CRITICAL_MENU_ITEMS: frozenset[str] = frozenset(
    {
        "Posting",
        "FinancialClosing",
        "YearEndClose",
        "ConsolidateOnline",
        "LedgerAllocation",
        "BankReconcileToLedger",
        "InventClose",
        "CostSheetCalculation",
    }
)

# Impact thresholds for affected user count categorization.
_IMPACT_MEDIUM_THRESHOLD: int = 3
_IMPACT_HIGH_THRESHOLD: int = 10

# Impact sort order for deterministic sorting.
_IMPACT_ORDER: dict[str, int] = {"Low": 0, "Medium": 1, "High": 2}


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class ComponentRemovalCandidate(BaseModel):
    """A single menu item recommended for removal from a role.

    Represents a low-usage, high-license component that can potentially be
    removed to reduce the role's license requirement.

    See Requirements/06 Algorithm 1.4 output specification.
    """

    menu_item: str = Field(description="Menu item AOT name")
    license_type: str = Field(
        description="License type required by this menu item (Commerce/Finance/SCM)"
    )
    users_affected: int = Field(
        description="Number of users who accessed this item in the analysis period",
        ge=0,
    )
    total_users: int = Field(
        description="Total number of users assigned to the role",
        ge=0,
    )
    usage_percentage: float = Field(
        description="Percentage of users who used this item (0.0-100.0)",
        ge=0.0,
        le=100.0,
    )
    impact: str = Field(
        description="Removal impact level: Low, Medium, or High"
    )
    requires_review: bool = Field(
        description="Whether this item requires manual review before removal"
    )
    recommendation: str = Field(
        description="Human-readable recommendation text"
    )


class ComponentRemovalResult(BaseModel):
    """Complete output from Algorithm 1.4: Component Removal Recommender.

    Aggregates all removal candidates for a role with a summary verdict.

    See Requirements/06 Algorithm 1.4 output specification.
    """

    role_name: str = Field(description="The security role that was analyzed")
    should_remove: bool = Field(
        description="Whether any components are recommended for removal"
    )
    components_to_remove: list[ComponentRemovalCandidate] = Field(
        description="List of removal candidates, sorted by impact (Low first)",
        default_factory=list,
    )
    expected_outcome: str = Field(
        description="Human-readable description of the expected outcome",
        default="",
    )


# ---------------------------------------------------------------------------
# Impact assessment
# ---------------------------------------------------------------------------


def _assess_removal_impact(
    menu_item: str,
    users_affected: int,
) -> tuple[str, bool]:
    """Assess the impact of removing a menu item from a role.

    Impact is determined by two factors:
      1. Whether the item is a critical business operation (always High)
      2. The number of affected users:
         - 0-2 users:  Low
         - 3-9 users:  Medium
         - 10+ users:  High

    Args:
        menu_item: The AOT name of the menu item.
        users_affected: Number of users who accessed this item.

    Returns:
        Tuple of (impact_level, requires_review).
        Critical items always return ("High", True).
    """
    is_critical: bool = menu_item in CRITICAL_MENU_ITEMS

    if is_critical:
        return "High", True

    if users_affected >= _IMPACT_HIGH_THRESHOLD:
        return "High", False
    elif users_affected >= _IMPACT_MEDIUM_THRESHOLD:
        return "Medium", False
    else:
        return "Low", False


# ---------------------------------------------------------------------------
# Main algorithm
# ---------------------------------------------------------------------------


def recommend_component_removal(
    role_name: str,
    security_config: pd.DataFrame,
    user_roles: pd.DataFrame,
    user_activity: pd.DataFrame,
    pricing_config: dict[str, Any],
    usage_threshold: float = 5.0,
) -> ComponentRemovalResult:
    """Recommend low-usage, high-license menu items for removal from a role.

    Implements Algorithm 1.4 from Requirements/06-Algorithms-Decision-Logic.md.

    The algorithm:
      1. Retrieves all users assigned to the specified role.
      2. Identifies high-license menu items (Commerce, Finance, SCM) in the
         role's security configuration.
      3. For each high-license item, calculates the percentage of role users
         who accessed it in the analysis period.
      4. Items with usage below ``usage_threshold`` are flagged as removal
         candidates.
      5. Each candidate receives an impact assessment (Low/Medium/High).
      6. Candidates are sorted by impact (Low first) for safest-first ordering.

    Args:
        role_name: The security role to analyze.
        security_config: DataFrame with columns ``securityrole``, ``AOTName``,
            ``LicenseType``, etc. Maps roles to menu items and license types.
        user_roles: DataFrame with columns ``user_id``, ``role_name``.
            Maps users to their assigned roles.
        user_activity: DataFrame with columns ``user_id``, ``menu_item``,
            ``action``, etc. Records of user activity in the analysis period.
        pricing_config: Parsed pricing.json dictionary. Currently used for
            future extensibility (savings estimation). Must contain a
            ``licenses`` key.
        usage_threshold: Maximum usage percentage (0.0-100.0) below which
            an item is considered a removal candidate. Default 5.0 (5%).

    Returns:
        ComponentRemovalResult with removal candidates sorted by impact.
    """
    # Step 1: Get all users assigned to this role
    role_users: pd.DataFrame = user_roles[user_roles["role_name"] == role_name]
    user_ids: list[str] = role_users["user_id"].unique().tolist()
    total_users: int = len(user_ids)

    # Handle empty role gracefully
    if total_users == 0:
        return ComponentRemovalResult(
            role_name=role_name,
            should_remove=False,
            components_to_remove=[],
            expected_outcome="No users assigned to this role.",
        )

    # Step 2: Get the role's menu items from security config
    role_config: pd.DataFrame = security_config[
        security_config["securityrole"] == role_name
    ]

    # Deduplicate menu items (a role may reference the same AOT name
    # multiple times with different access levels).
    menu_items: pd.DataFrame = (
        role_config[["AOTName", "LicenseType"]]
        .drop_duplicates(subset=["AOTName"])
    )

    # Step 3: Filter for high-license types only
    high_license_items: pd.DataFrame = menu_items[
        menu_items["LicenseType"].isin(HIGH_LICENSE_TYPES)
    ]

    if high_license_items.empty:
        return ComponentRemovalResult(
            role_name=role_name,
            should_remove=False,
            components_to_remove=[],
            expected_outcome="No high-license menu items in this role.",
        )

    # Step 4: Pre-compute per-user menu item access from activity data.
    # Filter activity to only users in this role for efficiency.
    role_activity: pd.DataFrame = user_activity[
        user_activity["user_id"].isin(user_ids)
    ]

    # Build a set of (user_id, menu_item) pairs for O(1) lookup.
    if not role_activity.empty:
        user_menu_pairs: set[tuple[str, str]] = set(
            zip(
                role_activity["user_id"].astype(str),
                role_activity["menu_item"].astype(str),
            )
        )
    else:
        user_menu_pairs = set()

    # Step 5: Evaluate each high-license item
    removal_candidates: list[ComponentRemovalCandidate] = []

    for _, row in high_license_items.iterrows():
        aot_name: str = str(row["AOTName"])
        license_type: str = str(row["LicenseType"])

        # Count how many role users accessed this item
        users_who_used: int = sum(
            1 for uid in user_ids if (uid, aot_name) in user_menu_pairs
        )

        # Calculate usage percentage
        usage_pct: float = (users_who_used / total_users) * 100.0

        # Check if below threshold
        if usage_pct >= usage_threshold:
            continue

        # Assess impact
        impact, requires_review = _assess_removal_impact(aot_name, users_who_used)

        recommendation_text: str
        if requires_review:
            recommendation_text = (
                f"REVIEW REQUIRED - Critical item '{aot_name}' has low usage "
                f"({usage_pct:.1f}%) but requires manual review before removal."
            )
        else:
            recommendation_text = (
                f"REMOVE - Low usage ({usage_pct:.1f}%), "
                f"high license requirement ({license_type})"
            )

        removal_candidates.append(
            ComponentRemovalCandidate(
                menu_item=aot_name,
                license_type=license_type,
                users_affected=users_who_used,
                total_users=total_users,
                usage_percentage=round(usage_pct, 2),
                impact=impact,
                requires_review=requires_review,
                recommendation=recommendation_text,
            )
        )

    # Step 6: Sort by impact (Low first, then Medium, then High)
    removal_candidates.sort(key=lambda c: _IMPACT_ORDER.get(c.impact, 99))

    # Build expected outcome
    count: int = len(removal_candidates)
    if count > 0:
        expected_outcome = (
            f"Remove {count} low-usage, high-license menu items "
            f"to reduce overall license requirement."
        )
    else:
        expected_outcome = "No low-usage, high-license menu items found for removal."

    return ComponentRemovalResult(
        role_name=role_name,
        should_remove=count > 0,
        components_to_remove=removal_candidates,
        expected_outcome=expected_outcome,
    )
