"""Azure Application Insights Client for User Activity Telemetry.

Queries user activity events from Application Insights using the
Log Analytics REST API (Kusto/KQL queries).

This is the primary data source for understanding what users ACTUALLY do
(read vs write operations), which drives license optimization algorithms
like 2.2 (Read-Only User Detector) and 2.5 (License Minority Detection).

Data Schema (per Requirements/04-User-Activity-Telemetry.md):
  - customEvents table in App Insights
  - Fields: user_id, menu_item, action (Read/Write/Create/Update/Delete),
    license_tier, feature, session_id

Environment Variables Required:
  APP_INSIGHTS_APP_ID:       Application Insights Application ID
  APP_INSIGHTS_API_KEY:      Application Insights API Key (or use managed identity)
  APP_INSIGHTS_WORKSPACE_ID: Log Analytics Workspace ID (alternative auth)

See Requirements/04-User-Activity-Telemetry.md for event schema.
See Requirements/13 for data freshness SLAs (<15 minutes).
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import requests

from ..models.input_schemas import AccessLevel, LicenseType, UserActivityRecord

logger = logging.getLogger(__name__)


@dataclass
class AppInsightsConfig:
    """Configuration for Azure Application Insights connection."""

    app_id: str = field(
        default_factory=lambda: os.environ.get("APP_INSIGHTS_APP_ID", "")
    )
    api_key: str = field(
        default_factory=lambda: os.environ.get("APP_INSIGHTS_API_KEY", "")
    )
    workspace_id: str = field(
        default_factory=lambda: os.environ.get("APP_INSIGHTS_WORKSPACE_ID", "")
    )
    timeout_seconds: int = 120  # KQL queries can take time for large datasets

    @property
    def query_url(self) -> str:
        """App Insights REST API query endpoint."""
        return f"https://api.applicationinsights.io/v1/apps/{self.app_id}/query"

    @property
    def workspace_query_url(self) -> str:
        """Log Analytics REST API query endpoint (alternative)."""
        return (
            f"https://api.loganalytics.io/v1/workspaces/{self.workspace_id}/query"
        )

    def validate(self) -> list[str]:
        """Validate configuration."""
        errors = []
        if not self.app_id and not self.workspace_id:
            errors.append(
                "Either APP_INSIGHTS_APP_ID or APP_INSIGHTS_WORKSPACE_ID is required"
            )
        if not self.api_key:
            errors.append("APP_INSIGHTS_API_KEY is required")
        return errors


class AppInsightsClient:
    """Typed client for querying user activity telemetry from Application Insights.

    Executes KQL (Kusto Query Language) queries against the customEvents table
    to extract user activity data for algorithm processing.

    Example:
        config = AppInsightsConfig()
        client = AppInsightsClient(config)

        # Get activity for a specific user
        activity = client.get_user_activity("john.doe@contoso.com", days=90)

        # Get read/write ratio for all users
        ratios = client.get_user_readwrite_ratios(days=90)
    """

    def __init__(self, config: AppInsightsConfig | None = None) -> None:
        self.config = config or AppInsightsConfig()
        self._session = requests.Session()

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with API key."""
        return {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _execute_query(self, kql: str) -> list[dict[str, Any]]:
        """Execute a KQL query and return results as list of dicts.

        Args:
            kql: Kusto Query Language query string.

        Returns:
            List of row dicts with column names as keys.
        """
        payload = {"query": kql}

        response = self._session.post(
            self.config.query_url,
            headers=self._get_headers(),
            json=payload,
            timeout=self.config.timeout_seconds,
        )

        if response.status_code == 429:
            logger.warning("App Insights query throttled (429)")
            raise RuntimeError("App Insights query rate limited. Retry later.")

        response.raise_for_status()
        data = response.json()

        # Parse tabular response into list of dicts
        results = []
        for table in data.get("tables", []):
            columns = [col["name"] for col in table.get("columns", [])]
            for row in table.get("rows", []):
                results.append(dict(zip(columns, row)))

        return results

    # ========================================================================
    # User Activity Queries
    # ========================================================================

    def get_user_activity(
        self,
        user_id: str,
        days: int = 90,
    ) -> list[UserActivityRecord]:
        """Get all activity events for a specific user.

        Retrieves read/write/create/update/delete events from the
        D365FO_UserActivity custom event table.

        Args:
            user_id: User identifier (email or user ID).
            days: Number of days to look back.

        Returns:
            List of UserActivityRecord instances.
        """
        kql = f"""
        customEvents
        | where name == "D365FO_UserActivity"
        | where timestamp > ago({days}d)
        | where customDimensions["user_id"] == "{user_id}"
        | project
            user_id = tostring(customDimensions["user_id"]),
            timestamp,
            menu_item = tostring(customDimensions["menu_item"]),
            action = tostring(customDimensions["action"]),
            session_id = tostring(customDimensions["session_id"]),
            license_tier = tostring(customDimensions["license_tier"]),
            feature = tostring(customDimensions["feature"])
        | order by timestamp desc
        """

        logger.info("Querying activity for user %s (last %d days)", user_id, days)
        raw_results = self._execute_query(kql)

        records = []
        for raw in raw_results:
            try:
                record = UserActivityRecord(
                    user_id=raw["user_id"],
                    timestamp=raw["timestamp"],
                    menu_item=raw["menu_item"],
                    action=AccessLevel(raw["action"]),
                    session_id=raw["session_id"],
                    license_tier=LicenseType(raw["license_tier"]),
                    feature=raw["feature"],
                )
                records.append(record)
            except (ValueError, KeyError) as e:
                logger.warning("Skipping invalid activity record: %s", e)

        logger.info("Retrieved %d activity records for %s", len(records), user_id)
        return records

    def get_user_readwrite_ratios(
        self,
        days: int = 90,
        min_operations: int = 10,
    ) -> list[dict[str, Any]]:
        """Get read/write ratio for all users.

        This is the primary query for Algorithm 2.2 (Read-Only User Detector).
        Returns aggregated read vs write percentages per user.

        Args:
            days: Analysis period in days.
            min_operations: Minimum total operations to include user.

        Returns:
            List of dicts with user_id, total_ops, read_ops, write_ops,
            read_percentage, write_percentage.
        """
        kql = f"""
        customEvents
        | where name == "D365FO_UserActivity"
        | where timestamp > ago({days}d)
        | extend
            user_id = tostring(customDimensions["user_id"]),
            action = tostring(customDimensions["action"])
        | summarize
            total_ops = count(),
            read_ops = countif(action == "Read"),
            write_ops = countif(action in ("Write", "Create", "Update", "Delete"))
            by user_id
        | where total_ops >= {min_operations}
        | extend
            read_percentage = round(100.0 * read_ops / total_ops, 2),
            write_percentage = round(100.0 * write_ops / total_ops, 2)
        | order by read_percentage desc
        """

        logger.info(
            "Querying read/write ratios for all users (last %d days, min %d ops)",
            days,
            min_operations,
        )
        return self._execute_query(kql)

    def get_user_form_usage(
        self,
        user_id: str,
        days: int = 90,
    ) -> list[dict[str, Any]]:
        """Get form/menu item usage breakdown for a specific user.

        Returns which forms the user accessed and how often, categorized
        by read vs write. Used by multiple algorithms for detailed analysis.

        Args:
            user_id: User identifier.
            days: Analysis period in days.

        Returns:
            List of dicts with menu_item, read_count, write_count, total_count,
            last_accessed, license_tier.
        """
        kql = f"""
        customEvents
        | where name == "D365FO_UserActivity"
        | where timestamp > ago({days}d)
        | where customDimensions["user_id"] == "{user_id}"
        | extend
            menu_item = tostring(customDimensions["menu_item"]),
            action = tostring(customDimensions["action"]),
            license_tier = tostring(customDimensions["license_tier"])
        | summarize
            total_count = count(),
            read_count = countif(action == "Read"),
            write_count = countif(action in ("Write", "Create", "Update", "Delete")),
            last_accessed = max(timestamp),
            license_tier = any(license_tier)
            by menu_item
        | order by total_count desc
        """

        logger.info("Querying form usage for user %s", user_id)
        return self._execute_query(kql)

    def get_after_hours_activity(
        self,
        days: int = 30,
        business_start_hour: int = 7,
        business_end_hour: int = 19,
    ) -> list[dict[str, Any]]:
        """Detect after-hours access patterns.

        Used by Algorithm 5.3 (Time-Based Access Analyzer) to identify
        potentially anomalous after-hours activity.

        Args:
            days: Analysis period.
            business_start_hour: Start of business hours (UTC).
            business_end_hour: End of business hours (UTC).

        Returns:
            List of dicts with user_id, after_hours_count, total_count,
            after_hours_percentage, unique_forms_accessed.
        """
        kql = f"""
        customEvents
        | where name == "D365FO_UserActivity"
        | where timestamp > ago({days}d)
        | extend
            user_id = tostring(customDimensions["user_id"]),
            hour_of_day = hourofday(timestamp),
            menu_item = tostring(customDimensions["menu_item"])
        | summarize
            total_count = count(),
            after_hours_count = countif(
                hour_of_day < {business_start_hour} or
                hour_of_day >= {business_end_hour}
            ),
            unique_forms = dcount(menu_item)
            by user_id
        | extend
            after_hours_pct = round(100.0 * after_hours_count / total_count, 2)
        | where after_hours_count > 0
        | order by after_hours_pct desc
        """

        logger.info("Querying after-hours activity (last %d days)", days)
        return self._execute_query(kql)

    # ========================================================================
    # Health Check
    # ========================================================================

    def health_check(self) -> dict[str, Any]:
        """Test connectivity to Application Insights."""
        import time

        start = time.time()
        try:
            kql = "customEvents | take 1"
            self._execute_query(kql)
            elapsed = time.time() - start
            return {
                "status": "healthy",
                "response_time_ms": round(elapsed * 1000),
                "app_id": self.config.app_id[:8] + "...",
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "status": "unhealthy",
                "response_time_ms": round(elapsed * 1000),
                "error": str(e),
            }
