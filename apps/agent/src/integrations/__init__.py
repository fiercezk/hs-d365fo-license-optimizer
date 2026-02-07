"""Data integration connectors for D365 FO License Agent.

This module provides typed clients for the four core data sources:
1. D365 FO OData API (Security Configuration, User-Role Assignments)
2. Azure Application Insights (User Activity Telemetry)
3. Microsoft Graph API (Entra ID License Data - optional)

See Requirements/13-Azure-Foundry-Agent-Architecture.md for data flow architecture.
"""

from .odata_client import D365ODataClient
from .app_insights_client import AppInsightsClient
from .data_transformer import DataTransformer

__all__ = [
    "D365ODataClient",
    "AppInsightsClient",
    "DataTransformer",
]
