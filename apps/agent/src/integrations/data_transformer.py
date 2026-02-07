"""Data Transformation Layer for algorithm input preparation.

Transforms raw data from OData and App Insights into the formats
expected by the 34 algorithm implementations.

Responsibilities:
  - Convert OData JSON to pandas DataFrames
  - Convert App Insights KQL results to typed records
  - Build lookup indices (reverse index for Algorithm 4.7)
  - Aggregate user-level metrics from raw events
  - Validate data quality and completeness

This layer sits between the integration clients and the algorithms:
  OData Client -> DataTransformer -> Algorithm
  AppInsights Client -> DataTransformer -> Algorithm

See Requirements/06-Algorithms-Decision-Logic.md for input requirements.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from ..models.input_schemas import (
    SecurityConfigRecord,
    UserActivityRecord,
    UserRoleAssignment,
)

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms raw integration data into algorithm-ready formats.

    Provides:
      - DataFrame builders for pandas-based algorithms
      - Reverse index builders for set-covering algorithms
      - Data quality validation and completeness scoring
      - Caching of expensive transformations

    Example:
        transformer = DataTransformer()

        # Build security config DataFrame from OData records
        security_df = transformer.security_config_to_dataframe(records)

        # Build reverse index for Algorithm 4.7
        menu_to_roles = transformer.build_menu_item_reverse_index(records)

        # Validate data quality
        quality = transformer.assess_data_quality(security_df, activity_df)
    """

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    # ========================================================================
    # Security Configuration Transformations
    # ========================================================================

    def security_config_to_dataframe(
        self,
        records: list[SecurityConfigRecord],
    ) -> pd.DataFrame:
        """Convert SecurityConfigRecord list to pandas DataFrame.

        The resulting DataFrame is the primary input for algorithms that
        analyze security role structure (1.1, 1.3, 1.4, 2.5, 2.6, etc.)

        Args:
            records: List of SecurityConfigRecord from OData client.

        Returns:
            DataFrame with columns: security_role, aot_name, access_level,
            license_type, priority, entitled, not_entitled, security_type.
        """
        if not records:
            logger.warning("No security config records to transform")
            return pd.DataFrame()

        data = [
            {
                "security_role": r.security_role,
                "aot_name": r.aot_name,
                "access_level": r.access_level.value,
                "license_type": r.license_type.value,
                "priority": r.priority,
                "entitled": r.entitled,
                "not_entitled": r.not_entitled,
                "security_type": r.security_type.value,
            }
            for r in records
        ]

        df = pd.DataFrame(data)
        logger.info(
            "Transformed %d security config records to DataFrame (%d roles, %d menu items)",
            len(df),
            df["security_role"].nunique(),
            df["aot_name"].nunique(),
        )
        return df

    def build_menu_item_reverse_index(
        self,
        records: list[SecurityConfigRecord],
    ) -> dict[str, list[dict[str, Any]]]:
        """Build reverse index: menu_item -> [roles that grant access].

        Used by Algorithm 4.7 (New User License Recommendation) for the
        greedy set-covering approximation. Given required menu items,
        find the minimum set of roles that covers all items.

        Args:
            records: List of SecurityConfigRecord.

        Returns:
            Dict mapping AOT name to list of dicts with role, license, priority info.

        Example:
            {
                "LedgerJournalTable": [
                    {"role": "Accountant", "license": "Finance", "priority": 180},
                    {"role": "Financial Controller", "license": "Finance", "priority": 180},
                ],
                "CustTable": [
                    {"role": "AR Clerk", "license": "Finance", "priority": 180},
                    {"role": "Accountant", "license": "Team Members", "priority": 60},
                ],
            }
        """
        index: dict[str, list[dict[str, Any]]] = {}

        for record in records:
            if record.aot_name not in index:
                index[record.aot_name] = []

            index[record.aot_name].append(
                {
                    "role": record.security_role,
                    "license": record.license_type.value,
                    "priority": record.priority,
                    "access_level": record.access_level.value,
                    "entitled": record.entitled,
                }
            )

        logger.info(
            "Built reverse index: %d menu items, %d total role mappings",
            len(index),
            sum(len(v) for v in index.values()),
        )

        self._cache["menu_item_reverse_index"] = index
        return index

    # ========================================================================
    # User-Role Assignment Transformations
    # ========================================================================

    def user_roles_to_dataframe(
        self,
        assignments: list[UserRoleAssignment],
    ) -> pd.DataFrame:
        """Convert UserRoleAssignment list to pandas DataFrame.

        Args:
            assignments: List of UserRoleAssignment from OData client.

        Returns:
            DataFrame with user-role mapping data.
        """
        if not assignments:
            logger.warning("No user-role assignments to transform")
            return pd.DataFrame()

        data = [
            {
                "user_id": a.user_id,
                "user_name": a.user_name,
                "email": a.email,
                "company": a.company,
                "department": a.department,
                "role_id": a.role_id,
                "role_name": a.role_name,
                "assigned_date": a.assigned_date,
                "status": a.status,
            }
            for a in assignments
        ]

        df = pd.DataFrame(data)
        logger.info(
            "Transformed %d user-role assignments (%d unique users, %d unique roles)",
            len(df),
            df["user_id"].nunique(),
            df["role_name"].nunique(),
        )
        return df

    def build_user_role_map(
        self,
        assignments: list[UserRoleAssignment],
    ) -> dict[str, list[str]]:
        """Build user -> roles mapping.

        Args:
            assignments: List of UserRoleAssignment.

        Returns:
            Dict mapping user_id to list of role names.
        """
        user_roles: dict[str, list[str]] = {}
        for a in assignments:
            if a.user_id not in user_roles:
                user_roles[a.user_id] = []
            user_roles[a.user_id].append(a.role_name)

        logger.info("Built user-role map: %d users", len(user_roles))
        return user_roles

    # ========================================================================
    # Activity Telemetry Transformations
    # ========================================================================

    def activity_to_dataframe(
        self,
        records: list[UserActivityRecord],
    ) -> pd.DataFrame:
        """Convert UserActivityRecord list to pandas DataFrame.

        The resulting DataFrame is used by algorithms that analyze user
        behavior patterns (2.2, 2.5, 3.2, 5.3, etc.)

        Args:
            records: List of UserActivityRecord from App Insights client.

        Returns:
            DataFrame with activity data including timestamp, action type, etc.
        """
        if not records:
            logger.warning("No activity records to transform")
            return pd.DataFrame()

        data = [
            {
                "user_id": r.user_id,
                "timestamp": r.timestamp,
                "menu_item": r.menu_item,
                "action": r.action.value,
                "session_id": r.session_id,
                "license_tier": r.license_tier.value,
                "feature": r.feature,
                "is_write": r.action.value in ("Write", "Create", "Update", "Delete"),
            }
            for r in records
        ]

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        logger.info(
            "Transformed %d activity records (span: %s to %s)",
            len(df),
            df["timestamp"].min() if len(df) > 0 else "N/A",
            df["timestamp"].max() if len(df) > 0 else "N/A",
        )
        return df

    # ========================================================================
    # Data Quality Assessment
    # ========================================================================

    def assess_data_quality(
        self,
        security_config_df: pd.DataFrame | None = None,
        user_roles_df: pd.DataFrame | None = None,
        activity_df: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        """Assess data quality and completeness for algorithm execution.

        Returns a quality score (0.0-1.0) and detailed breakdown of
        issues. Low quality scores reduce algorithm confidence.

        Args:
            security_config_df: Security configuration DataFrame.
            user_roles_df: User-role assignment DataFrame.
            activity_df: Activity telemetry DataFrame.

        Returns:
            Dict with overall score, component scores, and issues list.
        """
        issues: list[str] = []
        scores: dict[str, float] = {}

        # Security config quality
        if security_config_df is not None and not security_config_df.empty:
            null_pct = security_config_df.isnull().sum().sum() / security_config_df.size
            scores["security_config"] = 1.0 - null_pct
            if security_config_df.shape[0] < 1000:
                issues.append(
                    f"Security config has only {security_config_df.shape[0]} records "
                    f"(expected ~700K for typical D365 FO)"
                )
                scores["security_config"] *= 0.5
        else:
            scores["security_config"] = 0.0
            issues.append("Security configuration data is missing")

        # User-role quality
        if user_roles_df is not None and not user_roles_df.empty:
            null_pct = user_roles_df.isnull().sum().sum() / user_roles_df.size
            scores["user_roles"] = 1.0 - null_pct
            orphan_users = user_roles_df[user_roles_df["role_name"].isna()]
            if len(orphan_users) > 0:
                issues.append(f"{len(orphan_users)} users have no role assignment")
        else:
            scores["user_roles"] = 0.0
            issues.append("User-role assignment data is missing")

        # Activity quality
        if activity_df is not None and not activity_df.empty:
            scores["activity"] = 1.0
            # Check for reasonable date range
            date_span = (activity_df["timestamp"].max() - activity_df["timestamp"].min()).days
            if date_span < 30:
                issues.append(
                    f"Activity data spans only {date_span} days (recommend 90+)"
                )
                scores["activity"] *= 0.7
        else:
            scores["activity"] = 0.0
            issues.append("Activity telemetry data is missing")

        # Overall score (weighted)
        weights = {"security_config": 0.3, "user_roles": 0.3, "activity": 0.4}
        overall = sum(scores.get(k, 0) * w for k, w in weights.items())

        quality_report = {
            "overall_score": round(overall, 3),
            "component_scores": scores,
            "issues": issues,
            "assessed_at": datetime.utcnow().isoformat(),
            "recommendation": (
                "HIGH quality - safe for production recommendations"
                if overall >= 0.8
                else (
                    "MEDIUM quality - recommendations should be manually reviewed"
                    if overall >= 0.5
                    else "LOW quality - data insufficient for reliable recommendations"
                )
            ),
        }

        logger.info(
            "Data quality assessment: %.1f%% (%d issues)",
            overall * 100,
            len(issues),
        )
        return quality_report
