"""Tests for Algorithm 3.5: Orphaned Account Detector (TDD).

Algorithm 3.5 identifies user accounts with no active manager, inactive status,
missing department, or extended inactivity. Orphaned accounts pose security risks
and incur unnecessary license costs.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 634-747

Test scenarios based on algo_3_5 fixtures:
1. No manager assigned -> Flag as orphaned (HIGH risk)
2. Inactive user status -> Flag as orphaned (MEDIUM risk)
3. No valid department -> Flag as orphaned (HIGH risk)
4. Active account with manager -> No action (not orphaned)
5. Multiple orphan indicators -> All reasons listed, highest severity
6. Inactive manager -> Flag as orphaned (HIGH risk)
7. Long inactivity only (180+ days) -> Flag as orphaned (MEDIUM risk)
8. No roles/license assigned -> Orphaned, minimal cost impact
9. Batch detection across multiple users
10. Sorting by risk level (HIGH before MEDIUM)
"""

import json
from pathlib import Path

import pytest

from src.algorithms.algorithm_3_5_orphaned_account_detector import (
    detect_orphaned_accounts,
    OrphanedAccountResult,
    OrphanType,
    UserDirectoryRecord,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fixtures_dir() -> Path:
    """Get path to algo_3_5 test fixtures directory."""
    return Path(__file__).parent / "fixtures" / "algo_3_5"


@pytest.fixture
def no_manager_scenario(fixtures_dir: Path) -> dict:
    """Load no-manager scenario fixture."""
    with open(fixtures_dir / "test_scenario_no_manager.json") as f:
        return json.load(f)


@pytest.fixture
def inactive_user_scenario(fixtures_dir: Path) -> dict:
    """Load inactive user scenario fixture."""
    with open(fixtures_dir / "test_scenario_inactive_user.json") as f:
        return json.load(f)


@pytest.fixture
def no_department_scenario(fixtures_dir: Path) -> dict:
    """Load no-department scenario fixture."""
    with open(fixtures_dir / "test_scenario_no_department.json") as f:
        return json.load(f)


@pytest.fixture
def active_with_manager_scenario(fixtures_dir: Path) -> dict:
    """Load active-with-manager scenario fixture."""
    with open(fixtures_dir / "test_scenario_active_with_manager.json") as f:
        return json.load(f)


@pytest.fixture
def multiple_indicators_scenario(fixtures_dir: Path) -> dict:
    """Load multiple-indicators scenario fixture."""
    with open(fixtures_dir / "test_scenario_multiple_indicators.json") as f:
        return json.load(f)


@pytest.fixture
def inactive_manager_scenario(fixtures_dir: Path) -> dict:
    """Load inactive-manager scenario fixture."""
    with open(fixtures_dir / "test_scenario_inactive_manager.json") as f:
        return json.load(f)


@pytest.fixture
def long_inactivity_scenario(fixtures_dir: Path) -> dict:
    """Load long-inactivity-only scenario fixture."""
    with open(fixtures_dir / "test_scenario_long_inactivity_only.json") as f:
        return json.load(f)


@pytest.fixture
def no_roles_scenario(fixtures_dir: Path) -> dict:
    """Load no-roles scenario fixture."""
    with open(fixtures_dir / "test_scenario_no_roles_no_license.json") as f:
        return json.load(f)


def _build_user_record(scenario: dict) -> UserDirectoryRecord:
    """Build a UserDirectoryRecord from a test scenario fixture."""
    user = scenario["user"]
    return UserDirectoryRecord(
        user_id=user["user_id"],
        user_name=user["name"],
        email=user["email"],
        status=user["status"],
        manager_id=user["manager_id"],
        manager_status=user["manager_status"],
        department=user["department"],
        department_exists=user["department_exists"],
        current_license=user["current_license"],
        current_license_cost_monthly=user["current_license_cost_monthly"],
        roles=user["roles"],
        role_count=user["role_count"],
        days_since_last_activity=user["days_since_last_activity"],
    )


# ---------------------------------------------------------------------------
# Test Scenario 1: No Manager Assigned
# ---------------------------------------------------------------------------


class TestNoManagerAssigned:
    """Test case: Active user with no manager -> orphaned (HIGH risk)."""

    def test_no_manager_flagged_as_orphaned(
        self, no_manager_scenario: dict
    ) -> None:
        """User with no manager_id should be flagged as orphaned."""
        user = _build_user_record(no_manager_scenario)
        results = detect_orphaned_accounts([user])

        assert len(results) == 1
        result = results[0]
        assert result.is_orphaned is True
        assert "No valid manager" in result.orphan_reasons

    def test_no_manager_risk_level_high(
        self, no_manager_scenario: dict
    ) -> None:
        """Active orphaned account (no manager) should have HIGH risk."""
        user = _build_user_record(no_manager_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.risk_level == "HIGH"

    def test_no_manager_orphan_type(
        self, no_manager_scenario: dict
    ) -> None:
        """Orphan type should be NO_MANAGER when only missing manager."""
        user = _build_user_record(no_manager_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.orphan_type == OrphanType.NO_MANAGER


# ---------------------------------------------------------------------------
# Test Scenario 2: Inactive User Status
# ---------------------------------------------------------------------------


class TestInactiveUserStatus:
    """Test case: User with Inactive status -> orphaned (MEDIUM risk)."""

    def test_inactive_user_flagged(
        self, inactive_user_scenario: dict
    ) -> None:
        """Inactive user should be flagged as orphaned."""
        user = _build_user_record(inactive_user_scenario)
        results = detect_orphaned_accounts([user])

        assert len(results) == 1
        result = results[0]
        assert result.is_orphaned is True
        assert "User status is Inactive" in result.orphan_reasons

    def test_inactive_user_risk_medium(
        self, inactive_user_scenario: dict
    ) -> None:
        """Inactive user should have MEDIUM risk (already disabled)."""
        user = _build_user_record(inactive_user_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.risk_level == "MEDIUM"

    def test_inactive_user_includes_inactivity_reason(
        self, inactive_user_scenario: dict
    ) -> None:
        """Inactive user with 210 days inactivity should also flag inactivity."""
        user = _build_user_record(inactive_user_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        # Should have both inactive status AND inactivity duration reasons
        has_inactivity_reason = any(
            "No activity in" in r for r in result.orphan_reasons
        )
        assert has_inactivity_reason


# ---------------------------------------------------------------------------
# Test Scenario 3: No Valid Department
# ---------------------------------------------------------------------------


class TestNoDepartment:
    """Test case: Active user with no department -> orphaned (HIGH risk)."""

    def test_no_department_flagged(
        self, no_department_scenario: dict
    ) -> None:
        """User with no valid department should be flagged as orphaned."""
        user = _build_user_record(no_department_scenario)
        results = detect_orphaned_accounts([user])

        assert len(results) == 1
        result = results[0]
        assert result.is_orphaned is True
        assert "No valid department" in result.orphan_reasons

    def test_no_department_orphan_type(
        self, no_department_scenario: dict
    ) -> None:
        """Orphan type should be NO_DEPARTMENT when only missing department."""
        user = _build_user_record(no_department_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.orphan_type == OrphanType.NO_DEPARTMENT


# ---------------------------------------------------------------------------
# Test Scenario 4: Active Account With Manager (Healthy - No Action)
# ---------------------------------------------------------------------------


class TestActiveWithManager:
    """Test case: Active user with manager -> NOT orphaned."""

    def test_healthy_user_not_flagged(
        self, active_with_manager_scenario: dict
    ) -> None:
        """Active user with valid manager should not be flagged."""
        user = _build_user_record(active_with_manager_scenario)
        results = detect_orphaned_accounts([user])

        # Healthy users should not appear in results
        assert len(results) == 0

    def test_healthy_user_no_orphan_reasons(
        self, active_with_manager_scenario: dict
    ) -> None:
        """Active user with all fields valid should have zero orphan reasons."""
        user = _build_user_record(active_with_manager_scenario)
        results = detect_orphaned_accounts([user])

        assert len(results) == 0


# ---------------------------------------------------------------------------
# Test Scenario 5: Multiple Orphan Indicators
# ---------------------------------------------------------------------------


class TestMultipleIndicators:
    """Test case: User with multiple orphan indicators -> highest severity."""

    def test_multiple_indicators_all_reasons_listed(
        self, multiple_indicators_scenario: dict
    ) -> None:
        """All orphan reasons should be listed for multi-indicator user."""
        user = _build_user_record(multiple_indicators_scenario)
        results = detect_orphaned_accounts([user])

        assert len(results) == 1
        result = results[0]
        assert len(result.orphan_reasons) >= 3
        assert "No valid manager" in result.orphan_reasons
        assert "No valid department" in result.orphan_reasons
        has_inactivity = any(
            "No activity in" in r for r in result.orphan_reasons
        )
        assert has_inactivity

    def test_multiple_indicators_high_risk(
        self, multiple_indicators_scenario: dict
    ) -> None:
        """Multiple indicators with active status should be HIGH risk."""
        user = _build_user_record(multiple_indicators_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.risk_level == "HIGH"

    def test_multiple_indicators_orphan_type(
        self, multiple_indicators_scenario: dict
    ) -> None:
        """Multiple reasons should classify as MULTIPLE orphan type."""
        user = _build_user_record(multiple_indicators_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.orphan_type == OrphanType.MULTIPLE


# ---------------------------------------------------------------------------
# Test Scenario 6: Inactive Manager
# ---------------------------------------------------------------------------


class TestInactiveManager:
    """Test case: User whose manager is inactive -> orphaned (HIGH risk)."""

    def test_inactive_manager_flagged(
        self, inactive_manager_scenario: dict
    ) -> None:
        """User with inactive manager should be flagged as orphaned."""
        user = _build_user_record(inactive_manager_scenario)
        results = detect_orphaned_accounts([user])

        assert len(results) == 1
        result = results[0]
        assert result.is_orphaned is True
        assert "Manager is inactive" in result.orphan_reasons

    def test_inactive_manager_orphan_type(
        self, inactive_manager_scenario: dict
    ) -> None:
        """Orphan type should be INACTIVE_MANAGER."""
        user = _build_user_record(inactive_manager_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.orphan_type == OrphanType.INACTIVE_MANAGER


# ---------------------------------------------------------------------------
# Test Scenario 7: Long Inactivity Only (180+ Days)
# ---------------------------------------------------------------------------


class TestLongInactivityOnly:
    """Test case: Active user with 200+ days inactivity -> MEDIUM risk."""

    def test_long_inactivity_flagged(
        self, long_inactivity_scenario: dict
    ) -> None:
        """User with 200+ days inactivity should be flagged."""
        user = _build_user_record(long_inactivity_scenario)
        results = detect_orphaned_accounts([user])

        assert len(results) == 1
        result = results[0]
        assert result.is_orphaned is True
        has_inactivity = any(
            "No activity in" in r for r in result.orphan_reasons
        )
        assert has_inactivity

    def test_inactivity_below_threshold_not_flagged(self) -> None:
        """User with activity within 180 days should NOT be flagged for inactivity."""
        user = UserDirectoryRecord(
            user_id="USR-RECENT",
            user_name="Recent User",
            email="recent@contoso.com",
            status="Active",
            manager_id="MGR-OK",
            manager_status="Active",
            department="IT",
            department_exists=True,
            current_license="Finance",
            current_license_cost_monthly=180.0,
            roles=["Analyst"],
            role_count=1,
            days_since_last_activity=90,
        )
        results = detect_orphaned_accounts([user])
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Test Scenario 8: No Roles Assigned
# ---------------------------------------------------------------------------


class TestNoRolesAssigned:
    """Test case: Orphaned account with no roles -> MEDIUM risk."""

    def test_no_roles_orphaned(
        self, no_roles_scenario: dict
    ) -> None:
        """Inactive user with no roles should still be flagged as orphaned."""
        user = _build_user_record(no_roles_scenario)
        results = detect_orphaned_accounts([user])

        assert len(results) == 1
        result = results[0]
        assert result.is_orphaned is True

    def test_no_roles_medium_risk(
        self, no_roles_scenario: dict
    ) -> None:
        """Account with no roles should be MEDIUM risk (limited access)."""
        user = _build_user_record(no_roles_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.risk_level == "MEDIUM"

    def test_no_roles_license_cost_reported(
        self, no_roles_scenario: dict
    ) -> None:
        """License cost should be reported even for zero-role accounts."""
        user = _build_user_record(no_roles_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.license_cost_per_month == 60.00


# ---------------------------------------------------------------------------
# Test Scenario 9: Batch Detection
# ---------------------------------------------------------------------------


class TestBatchDetection:
    """Test case: Process multiple users and only return orphaned ones."""

    def test_batch_returns_only_orphaned(
        self,
        no_manager_scenario: dict,
        active_with_manager_scenario: dict,
        inactive_user_scenario: dict,
    ) -> None:
        """Batch detection should return only orphaned accounts."""
        users = [
            _build_user_record(no_manager_scenario),
            _build_user_record(active_with_manager_scenario),
            _build_user_record(inactive_user_scenario),
        ]
        results = detect_orphaned_accounts(users)

        # Only 2 of 3 users are orphaned
        assert len(results) == 2
        orphan_ids = {r.user_id for r in results}
        assert "USR-ORPHAN-001" in orphan_ids
        assert "USR-ORPHAN-002" in orphan_ids
        assert "USR-HEALTHY-001" not in orphan_ids


# ---------------------------------------------------------------------------
# Test Scenario 10: Sorting by Risk Level
# ---------------------------------------------------------------------------


class TestSortingByRiskLevel:
    """Test case: Results sorted by risk level (HIGH before MEDIUM)."""

    def test_high_risk_sorted_before_medium(
        self,
        no_manager_scenario: dict,
        long_inactivity_scenario: dict,
    ) -> None:
        """HIGH risk accounts should appear before MEDIUM risk accounts."""
        users = [
            _build_user_record(long_inactivity_scenario),  # MEDIUM risk
            _build_user_record(no_manager_scenario),  # HIGH risk
        ]
        results = detect_orphaned_accounts(users)

        assert len(results) == 2
        assert results[0].risk_level == "HIGH"
        assert results[1].risk_level == "MEDIUM"

    def test_sorting_with_multiple_high_risk(
        self,
        no_manager_scenario: dict,
        inactive_manager_scenario: dict,
        long_inactivity_scenario: dict,
    ) -> None:
        """Multiple HIGH risk should come before MEDIUM risk."""
        users = [
            _build_user_record(long_inactivity_scenario),  # MEDIUM
            _build_user_record(no_manager_scenario),  # HIGH
            _build_user_record(inactive_manager_scenario),  # HIGH
        ]
        results = detect_orphaned_accounts(users)

        assert len(results) == 3
        # First two should be HIGH
        assert results[0].risk_level == "HIGH"
        assert results[1].risk_level == "HIGH"
        # Last should be MEDIUM
        assert results[2].risk_level == "MEDIUM"


# ---------------------------------------------------------------------------
# Test: OrphanedAccountResult model validation
# ---------------------------------------------------------------------------


class TestOrphanedAccountResultModel:
    """Test case: Output model structure and fields."""

    def test_result_has_required_fields(
        self, no_manager_scenario: dict
    ) -> None:
        """OrphanedAccountResult should expose all required fields."""
        user = _build_user_record(no_manager_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        # All required fields from the spec
        assert hasattr(result, "user_id")
        assert hasattr(result, "user_name")
        assert hasattr(result, "status")
        assert hasattr(result, "manager_id")
        assert hasattr(result, "department")
        assert hasattr(result, "days_since_last_activity")
        assert hasattr(result, "role_count")
        assert hasattr(result, "license_cost_per_month")
        assert hasattr(result, "orphan_type")
        assert hasattr(result, "orphan_reasons")
        assert hasattr(result, "risk_level")
        assert hasattr(result, "recommendation")
        assert hasattr(result, "is_orphaned")

    def test_result_preserves_user_data(
        self, no_manager_scenario: dict
    ) -> None:
        """Result should preserve original user identification data."""
        user = _build_user_record(no_manager_scenario)
        results = detect_orphaned_accounts([user])

        result = results[0]
        assert result.user_id == "USR-ORPHAN-001"
        assert result.user_name == "Sarah Chen"
        assert result.status == "Active"
        assert result.license_cost_per_month == 180.00


# ---------------------------------------------------------------------------
# Test: Empty input handling
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Test case: Edge cases with empty or minimal input."""

    def test_empty_user_list_returns_empty(self) -> None:
        """Empty user list should return empty results."""
        results = detect_orphaned_accounts([])
        assert results == []
