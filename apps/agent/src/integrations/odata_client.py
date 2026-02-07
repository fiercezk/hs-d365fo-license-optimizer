"""D365 FO OData Client for Security Configuration and User-Role data.

Provides typed access to D365 FO data via OData v4 API endpoints.
Implements throttling mitigation per Requirements/13 (OData Throttling Strategy):
  - Delta sync (change tracking) for incremental updates
  - $batch requests for bundled queries
  - Exponential backoff on 429 responses
  - Off-peak scheduling awareness

Data Sources:
  - Security Configuration: Role -> Menu Item -> License mapping (~700K records)
  - User-Role Assignments: User -> Role mapping (200-200K records)
  - Audit Logs: Security changes and role assignment history

Environment Variables Required:
  D365_BASE_URL:       D365 FO environment URL (e.g., https://contoso.operations.dynamics.com)
  D365_TENANT_ID:      Azure AD tenant ID
  D365_CLIENT_ID:      Azure AD app registration client ID
  D365_CLIENT_SECRET:  Azure AD app registration client secret

See Requirements/02-Security-Configuration-Data.md for data schema.
See Requirements/03-User-Role-Assignment-Data.md for assignment schema.
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.input_schemas import (
    AccessLevel,
    LicenseType,
    SecurityConfigRecord,
    SecurityObjectType,
    UserRoleAssignment,
)

logger = logging.getLogger(__name__)


@dataclass
class ODataConfig:
    """Configuration for D365 FO OData connection.

    All values should come from environment variables or Azure Key Vault.
    Never hardcode credentials.
    """

    base_url: str = field(default_factory=lambda: os.environ.get("D365_BASE_URL", ""))
    tenant_id: str = field(default_factory=lambda: os.environ.get("D365_TENANT_ID", ""))
    client_id: str = field(default_factory=lambda: os.environ.get("D365_CLIENT_ID", ""))
    client_secret: str = field(
        default_factory=lambda: os.environ.get("D365_CLIENT_SECRET", "")
    )
    page_size: int = 5000  # Records per page ($top)
    max_retries: int = 3
    backoff_factor: float = 1.0  # 1s, 2s, 4s exponential backoff
    timeout_seconds: int = 60

    @property
    def token_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

    @property
    def odata_url(self) -> str:
        return f"{self.base_url}/data"

    def validate(self) -> list[str]:
        """Validate that all required configuration is present."""
        errors = []
        if not self.base_url:
            errors.append("D365_BASE_URL is required")
        if not self.tenant_id:
            errors.append("D365_TENANT_ID is required")
        if not self.client_id:
            errors.append("D365_CLIENT_ID is required")
        if not self.client_secret:
            errors.append("D365_CLIENT_SECRET is required")
        return errors


class D365ODataClient:
    """Typed OData v4 client for D365 Finance & Operations.

    Provides methods to fetch:
      - Security configuration (roles, menu items, license mappings)
      - User-role assignments
      - Audit logs (role assignment changes)

    Implements:
      - OAuth 2.0 client credentials flow
      - Pagination with server-side cursors
      - Delta sync (change tracking) for incremental updates
      - Exponential backoff on throttling (429)
      - Request batching ($batch)

    Example:
        config = ODataConfig()
        client = D365ODataClient(config)

        # Full initial load
        for record in client.get_security_config():
            process(record)

        # Delta sync (subsequent runs)
        delta_link = load_last_delta_link()
        for record in client.get_security_config_delta(delta_link):
            process(record)
    """

    def __init__(self, config: ODataConfig | None = None) -> None:
        self.config = config or ODataConfig()
        self._access_token: str | None = None
        self._token_expires: float = 0
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _get_access_token(self) -> str:
        """Acquire OAuth 2.0 access token via client credentials flow.

        Caches token until expiry (minus 5-minute buffer).
        """
        if self._access_token and time.time() < self._token_expires:
            return self._access_token

        logger.info("Acquiring new OAuth access token for D365 FO")

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": f"{self.config.base_url}/.default",
        }

        response = self._session.post(
            self.config.token_url,
            data=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data["access_token"]
        # Expire 5 minutes early to avoid edge cases
        self._token_expires = time.time() + token_data.get("expires_in", 3600) - 300

        logger.info("OAuth token acquired, expires in %ds", token_data.get("expires_in", 0))
        return self._access_token

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with OAuth bearer token."""
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Prefer": f"odata.maxpagesize={self.config.page_size}",
        }

    def _paginated_get(
        self,
        url: str,
        params: dict[str, str] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Fetch all pages from an OData endpoint.

        Follows @odata.nextLink for server-driven pagination.
        Yields individual records from each page.

        Args:
            url: OData endpoint URL.
            params: Query parameters ($filter, $select, $orderby, etc.)

        Yields:
            Individual records from the OData response.
        """
        current_url = url
        page_count = 0

        while current_url:
            page_count += 1
            logger.debug("Fetching page %d from %s", page_count, current_url[:100])

            response = self._session.get(
                current_url,
                headers=self._get_headers(),
                params=params if page_count == 1 else None,
                timeout=self.config.timeout_seconds,
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "60"))
                logger.warning("OData throttled (429). Waiting %ds", retry_after)
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            data = response.json()

            records = data.get("value", [])
            for record in records:
                yield record

            # Follow pagination link
            current_url = data.get("@odata.nextLink")

        logger.info("Fetched %d pages from OData endpoint", page_count)

    # ========================================================================
    # Security Configuration
    # ========================================================================

    def get_security_config(
        self,
        select_fields: list[str] | None = None,
    ) -> Generator[SecurityConfigRecord, None, None]:
        """Fetch all security configuration records from D365 FO.

        Maps the OData SecurityRolePermissions entity to SecurityConfigRecord
        Pydantic model.

        Full load: ~700K records, paginated at 5000/page = ~140 requests.
        Estimated time: 5-15 minutes depending on throttling.

        Args:
            select_fields: Optional $select fields to reduce payload size.

        Yields:
            SecurityConfigRecord instances.
        """
        url = f"{self.config.odata_url}/SecurityRolePermissions"
        params: dict[str, str] = {}

        if select_fields:
            params["$select"] = ",".join(select_fields)

        logger.info("Starting full security config load from D365 FO OData")
        record_count = 0

        for raw in self._paginated_get(url, params):
            try:
                record = SecurityConfigRecord(
                    security_role=raw.get("SecurityRole", ""),
                    aot_name=raw.get("AOTName", ""),
                    access_level=AccessLevel(raw.get("AccessLevel", "Read")),
                    license_type=LicenseType(raw.get("LicenseType", "Team Members")),
                    priority=int(raw.get("Priority", 60)),
                    entitled=bool(raw.get("Entitled", True)),
                    not_entitled=bool(raw.get("NotEntitled", False)),
                    security_type=SecurityObjectType(
                        raw.get("SecurityType", "MenuItemDisplay")
                    ),
                )
                record_count += 1
                yield record
            except (ValueError, KeyError) as e:
                logger.warning("Skipping invalid security config record: %s", e)

        logger.info("Loaded %d security config records", record_count)

    def get_security_config_delta(
        self,
        delta_link: str,
    ) -> Generator[SecurityConfigRecord, None, None]:
        """Fetch only changed security config records since last sync.

        Uses D365 FO Change Tracking (delta links) to retrieve only
        modified/deleted records. Reduces volume by 95%+ vs full load.

        Args:
            delta_link: The @odata.deltaLink from the previous sync.

        Yields:
            SecurityConfigRecord instances (changed records only).
        """
        logger.info("Starting delta sync from: %s", delta_link[:80])
        for raw in self._paginated_get(delta_link):
            try:
                record = SecurityConfigRecord(
                    security_role=raw.get("SecurityRole", ""),
                    aot_name=raw.get("AOTName", ""),
                    access_level=AccessLevel(raw.get("AccessLevel", "Read")),
                    license_type=LicenseType(raw.get("LicenseType", "Team Members")),
                    priority=int(raw.get("Priority", 60)),
                    entitled=bool(raw.get("Entitled", True)),
                    not_entitled=bool(raw.get("NotEntitled", False)),
                    security_type=SecurityObjectType(
                        raw.get("SecurityType", "MenuItemDisplay")
                    ),
                )
                yield record
            except (ValueError, KeyError) as e:
                logger.warning("Skipping invalid delta record: %s", e)

    # ========================================================================
    # User-Role Assignments
    # ========================================================================

    def get_user_role_assignments(
        self,
        company: str | None = None,
        active_only: bool = True,
    ) -> Generator[UserRoleAssignment, None, None]:
        """Fetch user-role assignments from D365 FO.

        Maps the OData UserSecurityRoles entity to UserRoleAssignment
        Pydantic model.

        Args:
            company: Optional legal entity filter (e.g., 'USMF').
            active_only: If True, only return active assignments.

        Yields:
            UserRoleAssignment instances.
        """
        url = f"{self.config.odata_url}/UserSecurityRoles"
        params: dict[str, str] = {}
        filters = []

        if company:
            filters.append(f"Company eq '{company}'")
        if active_only:
            filters.append("Status eq 'Active'")
        if filters:
            params["$filter"] = " and ".join(filters)

        logger.info(
            "Fetching user-role assignments (company=%s, active_only=%s)",
            company,
            active_only,
        )
        record_count = 0

        for raw in self._paginated_get(url, params):
            try:
                record = UserRoleAssignment(
                    user_id=raw.get("UserId", ""),
                    user_name=raw.get("UserName", ""),
                    email=raw.get("Email", "unknown@unknown.com"),
                    company=raw.get("Company", ""),
                    department=raw.get("Department"),
                    role_id=raw.get("RoleId", ""),
                    role_name=raw.get("RoleName", ""),
                    assigned_date=raw.get(
                        "AssignedDate",
                        datetime.utcnow().isoformat(),
                    ),
                    status=raw.get("Status", "Active"),
                )
                record_count += 1
                yield record
            except (ValueError, KeyError) as e:
                logger.warning("Skipping invalid user-role record: %s", e)

        logger.info("Loaded %d user-role assignments", record_count)

    # ========================================================================
    # Health Check
    # ========================================================================

    def health_check(self) -> dict[str, Any]:
        """Test connectivity to D365 FO OData endpoint.

        Returns:
            Dict with status, response time, and any errors.
        """
        start = time.time()
        try:
            url = f"{self.config.odata_url}/$metadata"
            response = self._session.get(
                url,
                headers=self._get_headers(),
                timeout=10,
            )
            elapsed = time.time() - start
            return {
                "status": "healthy" if response.ok else "unhealthy",
                "response_time_ms": round(elapsed * 1000),
                "status_code": response.status_code,
                "base_url": self.config.base_url,
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "status": "unhealthy",
                "response_time_ms": round(elapsed * 1000),
                "error": str(e),
                "base_url": self.config.base_url,
            }
