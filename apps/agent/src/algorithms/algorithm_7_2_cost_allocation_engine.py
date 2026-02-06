"""Algorithm 7.2: Cost Allocation Engine.

Allocates license costs across departments, cost centers, or business units
for accurate financial reporting and chargebacks. Maps each user to their
department/cost center, determines license cost from pricing configuration,
and aggregates costs per department with percentage breakdowns.

Specification: Requirements/08-Algorithm-Review-Summary.md
(Algorithm 7.2: Cost Allocation Engine, Phase 2, Medium complexity).

Key behaviors:
  - Map each user to their department/cost center
  - Determine each user's license cost (from pricing config)
  - Aggregate costs per department
  - Handle users with no department (allocate to 'Unassigned')
  - Calculate per-department totals, percentages, and per-user averages
  - Generate cost allocation report sorted by total cost descending
  - Support license type breakdown per department
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from ..utils.pricing import get_license_price

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNASSIGNED_DEPARTMENT: str = "Unassigned"


# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------


class LicenseBreakdownItem(BaseModel):
    """Breakdown of a single license type within a department.

    Shows the count and cost contribution of one license type
    for a given department allocation.
    """

    license_type: str = Field(description="License type name (e.g., 'Finance', 'Team Members')")
    user_count: int = Field(description="Number of users with this license type", ge=0)
    monthly_cost: float = Field(description="Total monthly cost for this license type (USD)", ge=0)


class CostAllocation(BaseModel):
    """Cost allocation for a single department.

    Contains the total cost, user count, percentage of overall spend,
    average cost per user, and license type breakdown for one department.
    """

    department: str = Field(description="Department or cost center name")
    total_monthly_cost: float = Field(
        description="Total monthly license cost for this department (USD)", ge=0
    )
    user_count: int = Field(description="Number of users in this department", ge=0)
    cost_percentage: float = Field(
        description="Percentage of total organizational cost allocated to this department",
        ge=0,
        le=100,
    )
    average_cost_per_user: float = Field(
        description="Average monthly license cost per user in this department (USD)", ge=0
    )
    license_breakdown: list[LicenseBreakdownItem] = Field(
        description="Breakdown of costs by license type within this department",
        default_factory=list,
    )


class CostAllocationAnalysis(BaseModel):
    """Complete output from Algorithm 7.2: Cost Allocation Engine.

    Aggregates per-department cost allocations with organizational totals.
    Departments are sorted by total_monthly_cost descending (highest first).
    """

    algorithm_id: str = Field(default="7.2", description="Algorithm identifier")
    allocations: list[CostAllocation] = Field(
        description="Per-department cost allocations, sorted by total cost descending",
        default_factory=list,
    )
    total_monthly_cost: float = Field(
        description="Total monthly license cost across all departments (USD)", ge=0, default=0.0
    )
    total_annual_cost: float = Field(
        description="Total annual license cost (monthly * 12) (USD)", ge=0, default=0.0
    )
    total_users: int = Field(
        description="Total number of users across all departments", ge=0, default=0
    )


# ---------------------------------------------------------------------------
# Core Algorithm
# ---------------------------------------------------------------------------


def _normalize_department(value: Any) -> str:
    """Normalize a department value, mapping empty/null to 'Unassigned'.

    Args:
        value: Raw department value from the DataFrame. May be str, None, NaN,
               or empty string.

    Returns:
        Normalized department name string. Empty, None, or NaN values are
        mapped to 'Unassigned'.
    """
    if value is None:
        return UNASSIGNED_DEPARTMENT
    if isinstance(value, float) and pd.isna(value):
        return UNASSIGNED_DEPARTMENT
    dept_str = str(value).strip()
    if not dept_str:
        return UNASSIGNED_DEPARTMENT
    return dept_str


def _build_license_breakdown(
    dept_df: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> list[LicenseBreakdownItem]:
    """Build per-license-type breakdown for a department.

    Groups users by license_type within the department and calculates
    the count and cost for each license type.

    Args:
        dept_df: DataFrame rows for a single department.
        pricing_config: Parsed pricing.json dictionary.

    Returns:
        List of LicenseBreakdownItem sorted by monthly_cost descending.
    """
    breakdown: list[LicenseBreakdownItem] = []

    grouped = dept_df.groupby("license_type")
    for license_type, group_df in grouped:
        license_type_str = str(license_type)
        count = len(group_df)
        try:
            unit_price = get_license_price(pricing_config, license_type_str)
        except KeyError:
            unit_price = 0.0
        monthly_cost = unit_price * count

        breakdown.append(
            LicenseBreakdownItem(
                license_type=license_type_str,
                user_count=count,
                monthly_cost=monthly_cost,
            )
        )

    # Sort by monthly_cost descending
    breakdown.sort(key=lambda item: item.monthly_cost, reverse=True)
    return breakdown


def allocate_license_costs(
    user_license_assignments: pd.DataFrame,
    pricing_config: dict[str, Any],
) -> CostAllocationAnalysis:
    """Allocate license costs across departments for financial reporting.

    Algorithm 7.2: Cost Allocation Engine. Processes a DataFrame of user-license
    assignments, determines per-user license costs from the pricing configuration,
    and aggregates costs by department with percentage breakdowns and license type
    detail.

    See Requirements/08-Algorithm-Review-Summary.md for specification.

    Args:
        user_license_assignments: DataFrame with columns:
            - user_id (str): Unique user identifier
            - user_name (str): User display name
            - department (str | None): Department or cost center
            - license_type (str): License type name (e.g., 'Finance', 'SCM')
            - status (str): Assignment status (e.g., 'Active')
        pricing_config: Parsed pricing.json dictionary with license costs.

    Returns:
        CostAllocationAnalysis with per-department allocations sorted by
        total cost descending, organizational totals, and license breakdowns.
    """
    # Handle empty input
    if len(user_license_assignments) == 0:
        return CostAllocationAnalysis(
            algorithm_id="7.2",
            allocations=[],
            total_monthly_cost=0.0,
            total_annual_cost=0.0,
            total_users=0,
        )

    # Make a working copy to avoid mutating the input
    df = user_license_assignments.copy()

    # Normalize departments: empty/null/NaN -> 'Unassigned'
    df["department"] = df["department"].apply(_normalize_department)

    # Pre-compute per-user license cost in a vectorized-friendly way
    # Build a mapping from (row index) -> price using the shared pricing utility
    user_costs: list[float] = []
    for _, row in df.iterrows():
        license_type_str = str(row["license_type"])
        try:
            price = get_license_price(pricing_config, license_type_str)
        except KeyError:
            price = 0.0
        user_costs.append(price)

    df["user_cost"] = user_costs

    # Calculate organizational total
    total_monthly_cost: float = float(df["user_cost"].sum())

    # Group by department and build allocations
    allocations: list[CostAllocation] = []
    for dept_name, dept_df in df.groupby("department"):
        dept_str = str(dept_name)
        dept_total: float = float(dept_df["user_cost"].sum())
        dept_user_count: int = len(dept_df)

        # Calculate percentage of total
        cost_pct: float = (
            (dept_total / total_monthly_cost) * 100.0 if total_monthly_cost > 0 else 0.0
        )

        # Calculate average cost per user
        avg_cost: float = dept_total / dept_user_count if dept_user_count > 0 else 0.0

        # Build license type breakdown
        breakdown = _build_license_breakdown(dept_df, pricing_config)

        allocations.append(
            CostAllocation(
                department=dept_str,
                total_monthly_cost=dept_total,
                user_count=dept_user_count,
                cost_percentage=cost_pct,
                average_cost_per_user=avg_cost,
                license_breakdown=breakdown,
            )
        )

    # Sort by total cost descending (highest cost department first)
    allocations.sort(key=lambda a: a.total_monthly_cost, reverse=True)

    total_users: int = len(df)
    total_annual: float = total_monthly_cost * 12.0

    return CostAllocationAnalysis(
        algorithm_id="7.2",
        allocations=allocations,
        total_monthly_cost=total_monthly_cost,
        total_annual_cost=total_annual,
        total_users=total_users,
    )
