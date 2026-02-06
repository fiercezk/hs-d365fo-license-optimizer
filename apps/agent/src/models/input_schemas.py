"""Input data schemas for D365 FO License Agent algorithms.

These Pydantic models define the structure of data coming FROM:
- D365 FO Security Configuration (OData)
- D365 FO User-Role Assignments (OData)
- Azure Application Insights (User Activity Telemetry)

Based on Requirements docs 02, 03, 04.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class AccessLevel(str, Enum):
    """D365 FO security access levels."""

    READ = "Read"
    WRITE = "Write"
    UPDATE = "Update"
    DELETE = "Delete"
    CREATE = "Create"


class SecurityObjectType(str, Enum):
    """D365 FO security object types."""

    MENU_ITEM_DISPLAY = "MenuItemDisplay"
    MENU_ITEM_ACTION = "MenuItemAction"
    MENU_ITEM_OUTPUT = "MenuItemOutput"
    DATA_ENTITY = "DataEntity"
    DATA_ENTITY_METHOD = "DataEntityMethod"


class LicenseType(str, Enum):
    """D365 FO license types with monthly costs."""

    TEAM_MEMBERS = "Team Members"  # $60/month
    OPERATIONS_ACTIVITY = "Operations - Activity"  # $30/month (add-on)
    OPERATIONS = "Operations"  # $90/month
    SCM = "SCM"  # $180/month
    FINANCE = "Finance"  # $180/month
    COMMERCE = "Commerce"  # $180/month
    DEVICE = "Device License"  # $80/device/month


class SecurityConfigRecord(BaseModel):
    """Single record from D365 FO Security Configuration data.

    Maps security roles → security objects → license requirements.
    Source: Doc 02 (Security Configuration Data)
    """

    security_role: str = Field(description="Security role name (e.g., 'Accountant')")
    aot_name: str = Field(description="Menu item / entity AOT name (e.g., 'GeneralJournalEntry')")
    access_level: AccessLevel = Field(description="Type of access permission")
    license_type: LicenseType = Field(description="License required for this access")
    priority: int = Field(
        description="License priority/cost (60=Team Members, 180=Finance/SCM/Commerce)",
        ge=0,
        le=300,
    )
    entitled: bool = Field(description="Whether access is covered by license (1=Yes, 0=No)")
    not_entitled: bool = Field(
        description="Whether access is NOT covered (1=Compliance risk, 0=OK)"
    )
    security_type: SecurityObjectType = Field(description="Type of security object")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int, info: ValidationInfo) -> int:
        """Validate priority matches typical D365 FO license costs."""
        valid_priorities = {20, 30, 60, 90, 180, 300}
        if v not in valid_priorities:
            raise ValueError(
                f"Priority {v} not a standard D365 FO license cost. "
                f"Expected one of: {valid_priorities}"
            )
        return v


class UserRoleAssignment(BaseModel):
    """User-to-role assignment record from D365 FO.

    Links users to security roles.
    Source: Doc 03 (User-Role Assignment Data)
    """

    user_id: str = Field(description="Unique user identifier (e.g., 'USR001')")
    user_name: str = Field(description="User display name")
    email: str = Field(description="User email address")
    company: str = Field(description="Legal entity / company code (e.g., 'USMF')")
    department: str | None = Field(default=None, description="Department (optional)")
    role_id: str = Field(description="Role identifier (e.g., 'ROLE_ACCT')")
    role_name: str = Field(description="Role display name (e.g., 'Accountant')")
    assigned_date: str = Field(description="When role was assigned (ISO 8601 date)")
    status: Literal["Active", "Inactive"] = Field(description="Assignment status")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError(f"Invalid email address: {v}")
        return v.lower()


class UserActivityRecord(BaseModel):
    """Single user activity event from Azure Application Insights.

    Tracks what users ACTUALLY do (read vs write operations).
    Source: Doc 04 (User Activity Telemetry Data)
    """

    user_id: str = Field(description="User identifier")
    timestamp: datetime = Field(description="When action occurred (UTC)")
    menu_item: str = Field(description="Menu item / form accessed")
    action: AccessLevel = Field(description="Read/Write/Create/Update/Delete operation")
    session_id: str = Field(description="Session identifier for correlation")
    license_tier: LicenseType = Field(description="License required for this action")
    feature: str = Field(description="Module / functional area (e.g., 'General Ledger')")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: datetime | str) -> datetime | str:
        """Parse timestamp from string if needed."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class AlgorithmInputParameters(BaseModel):
    """Common input parameters for all algorithms.

    Defines date ranges, thresholds, confidence levels.
    """

    user_id: str = Field(description="Target user for analysis")
    date_range_start: datetime = Field(description="Analysis period start (UTC)")
    date_range_end: datetime = Field(description="Analysis period end (UTC)")
    read_only_threshold: float = Field(
        default=0.95,
        description="Read percentage threshold for downgrade consideration (default 95%)",
        ge=0.0,
        le=1.0,
    )
    min_sample_size: int = Field(
        default=100,
        description="Minimum operations required for high-confidence recommendation",
        ge=10,
    )
    confidence_threshold: float = Field(
        default=0.70,
        description="Minimum confidence score to return recommendation",
        ge=0.0,
        le=1.0,
    )

    @field_validator("date_range_end")
    @classmethod
    def validate_date_range(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Ensure end date is after start date."""
        if "date_range_start" in info.data and v <= info.data["date_range_start"]:
            raise ValueError("date_range_end must be after date_range_start")
        return v


class TeamMembersEligibleForm(BaseModel):
    """Form eligibility mapping for Team Members license.

    Source: Doc 09 (License Minority Detection)
    CRITICAL: Requires customer validation before production use.
    """

    form_name: str = Field(description="Menu item / form AOT name")
    team_members_eligible: bool = Field(
        description="Whether form is accessible with Team Members license"
    )
    operations_activity_eligible: bool = Field(
        description="Whether form requires Operations Activity add-on"
    )
    validation_status: Literal["validated", "unvalidated", "deprecated"] = Field(
        description="Validation status - MUST be 'validated' for production use"
    )
    validation_date: datetime | None = Field(
        default=None, description="When validation was performed"
    )
    notes: str | None = Field(default=None, description="Validation notes / exceptions")


class SecurityFinding(BaseModel):
    """Individual security finding for Algorithm 5.2 risk scoring.

    Represents a detected security risk (SoD violation, privilege creep, etc.)
    that contributes to the user's overall security risk score.
    """

    finding_type: str = Field(
        description="Type of security finding (SoD_VIOLATION, PRIVILEGE_CREEP, "
        "ANOMALOUS_CHANGE, ORPHANED_ACCOUNT, etc.)"
    )
    severity: str = Field(
        description="Severity level (CRITICAL, HIGH, MEDIUM, LOW) " "- case insensitive"
    )
    description: str = Field(description="Detailed description of the security finding")
