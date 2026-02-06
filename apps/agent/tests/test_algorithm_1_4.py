"""Tests for Algorithm 1.4: Component Removal Recommender.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_1_4_component_removal.py is implemented.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 302-382.

Algorithm 1.4 analyzes a role's menu items to identify low-usage, high-license
components that can be removed to reduce the role's overall license requirement.
For each role, the algorithm:
  - Identifies menu items requiring Commerce, Finance, or SCM licenses
  - Calculates usage percentage across all users assigned to the role
  - Recommends removal of items with < 5% usage (configurable threshold)
  - Assesses removal impact (Low/Medium/High) based on affected user count
  - Flags critical menu items for manual review instead of auto-removal
  - Sorts candidates by impact (low impact first for safest removal)

Test scenarios cover:
  1. High-license item with <5% usage -> Recommend removal
  2. High-license item with >5% usage -> No action (actively used)
  3. Low-license item with <5% usage -> Skip (no license savings from removal)
  4. Critical menu item with low usage -> Flag for manual review
  5. Multiple removal candidates -> Sorted by impact (low first)
  6. Empty role (no users) -> Graceful handling
  7. All items actively used -> No removal candidates
  8. Configurable usage threshold
  9. Mixed license tiers -> Only high-license items considered
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.algorithms.algorithm_1_4_component_removal import (
    ComponentRemovalCandidate,
    ComponentRemovalResult,
    recommend_component_removal,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

# High-license types that the algorithm considers for removal
HIGH_LICENSE_TYPES: frozenset[str] = frozenset({"Commerce", "Finance", "SCM"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON.

    Returns:
        Parsed pricing config with license costs and savings rules.
    """
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_security_config(
    role_name: str,
    items: list[tuple[str, str, str]],
) -> pd.DataFrame:
    """Build a security configuration DataFrame for a role.

    Args:
        role_name: The security role name.
        items: List of (aot_name, license_type, access_level) tuples.

    Returns:
        DataFrame matching the security_config schema with columns:
        securityrole, AOTName, AccessLevel, LicenseType, Priority,
        Entitled, NotEntitled, securitytype.
    """
    priority_map: dict[str, int] = {
        "Team Members": 60,
        "Operations": 90,
        "SCM": 180,
        "Finance": 180,
        "Commerce": 180,
    }
    rows: list[dict[str, Any]] = []
    for aot_name, license_type, access_level in items:
        rows.append(
            {
                "securityrole": role_name,
                "AOTName": aot_name,
                "AccessLevel": access_level,
                "LicenseType": license_type,
                "Priority": priority_map.get(license_type, 60),
                "Entitled": 1,
                "NotEntitled": 0,
                "securitytype": "MenuItemDisplay",
            }
        )
    return pd.DataFrame(rows)


def _build_user_roles(
    role_name: str,
    user_ids: list[str],
) -> pd.DataFrame:
    """Build a user-role assignment DataFrame.

    Args:
        role_name: The security role name.
        user_ids: List of user identifiers assigned to the role.

    Returns:
        DataFrame with columns: user_id, role_name.
    """
    rows: list[dict[str, str]] = []
    for uid in user_ids:
        rows.append({"user_id": uid, "role_name": role_name})
    return pd.DataFrame(rows)


def _build_user_activity(
    activities: list[tuple[str, str, str]],
) -> pd.DataFrame:
    """Build a user activity DataFrame.

    Args:
        activities: List of (user_id, menu_item, action) tuples representing
            individual activity events over the analysis period.

    Returns:
        DataFrame with columns: user_id, timestamp, menu_item, action,
        session_id, license_tier, feature.
    """
    rows: list[dict[str, str]] = []
    for idx, (user_id, menu_item, action) in enumerate(activities):
        rows.append(
            {
                "user_id": user_id,
                "timestamp": f"2026-01-15 09:{idx // 60:02d}:{idx % 60:02d}",
                "menu_item": menu_item,
                "action": action,
                "session_id": f"sess-{idx:04d}",
                "license_tier": "Finance",
                "feature": "General Ledger",
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Test 1: High-license item with <5% usage -> Recommend removal
# ---------------------------------------------------------------------------


class TestHighLicenseLowUsageRemoval:
    """Test scenario: Finance menu item used by < 5% of role users.

    Setup:
    - Role: 'AccountingClerk' with 100 users
    - Menu item 'AdvancedLedgerEntry' requires Finance license ($180)
    - Only 2 out of 100 users (2%) accessed this menu item in 90 days
    - Expected: Recommend removal (2% < 5% threshold)
    - Impact should be Low (only 2 users affected)
    """

    def test_low_usage_high_license_item_recommended_for_removal(self) -> None:
        """Finance menu item at 2% usage should be a removal candidate."""
        # -- Arrange --
        role_name = "AccountingClerk"
        user_ids = [f"USR{i:03d}" for i in range(100)]

        security_config = _build_security_config(
            role_name,
            [
                ("AdvancedLedgerEntry", "Finance", "Read"),
                ("CustomerList", "Team Members", "Read"),
                ("GeneralJournal", "Finance", "Write"),
            ],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        # Only 2 users accessed AdvancedLedgerEntry; many used GeneralJournal
        activity_events: list[tuple[str, str, str]] = []
        # 2 users accessed the low-usage item
        activity_events.append(("USR000", "AdvancedLedgerEntry", "Read"))
        activity_events.append(("USR001", "AdvancedLedgerEntry", "Read"))
        # 80 users accessed GeneralJournal (high usage)
        for i in range(80):
            activity_events.append((f"USR{i:03d}", "GeneralJournal", "Write"))

        user_activity = _build_user_activity(activity_events)
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is True, (
            "Expected should_remove=True when there is a low-usage high-license item"
        )
        assert len(result.components_to_remove) >= 1, (
            "Expected at least 1 removal candidate"
        )

        # Find the AdvancedLedgerEntry candidate
        candidate = next(
            (c for c in result.components_to_remove if c.menu_item == "AdvancedLedgerEntry"),
            None,
        )
        assert candidate is not None, (
            "AdvancedLedgerEntry should be a removal candidate"
        )
        assert candidate.license_type == "Finance"
        assert candidate.users_affected == 2
        assert candidate.usage_percentage < 5.0
        assert candidate.impact == "Low"


# ---------------------------------------------------------------------------
# Test 2: High-license item with >5% usage -> No action
# ---------------------------------------------------------------------------


class TestHighLicenseHighUsageNoAction:
    """Test scenario: Finance menu item used by > 5% of role users.

    Setup:
    - Role: 'FinanceManager' with 20 users
    - Menu item 'GeneralJournalPosting' requires Finance license ($180)
    - 15 out of 20 users (75%) accessed this menu item in 90 days
    - Expected: NOT a removal candidate (75% >> 5% threshold)
    """

    def test_high_usage_item_not_flagged_for_removal(self) -> None:
        """Finance item at 75% usage should NOT be a removal candidate."""
        # -- Arrange --
        role_name = "FinanceManager"
        user_ids = [f"USR{i:03d}" for i in range(20)]

        security_config = _build_security_config(
            role_name,
            [
                ("GeneralJournalPosting", "Finance", "Write"),
                ("BudgetReport", "Finance", "Read"),
            ],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        # 15 out of 20 users accessed GeneralJournalPosting
        activity_events: list[tuple[str, str, str]] = []
        for i in range(15):
            activity_events.append((f"USR{i:03d}", "GeneralJournalPosting", "Write"))
        # 18 out of 20 accessed BudgetReport
        for i in range(18):
            activity_events.append((f"USR{i:03d}", "BudgetReport", "Read"))

        user_activity = _build_user_activity(activity_events)
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is False, (
            "Expected should_remove=False when all items are above usage threshold"
        )
        assert len(result.components_to_remove) == 0, (
            "Expected 0 removal candidates when all items are actively used"
        )


# ---------------------------------------------------------------------------
# Test 3: Low-license item with <5% usage -> Skip (low impact)
# ---------------------------------------------------------------------------


class TestLowLicenseLowUsageSkipped:
    """Test scenario: Team Members item with <5% usage is skipped.

    Per the algorithm specification, only high-license items (Commerce,
    Finance, SCM) are considered for removal. Low-license items like
    Team Members are skipped because removing them provides no license
    cost savings.

    Setup:
    - Role: 'BasicUser' with 50 users
    - Menu item 'EmployeeDirectory' requires Team Members license ($60)
    - Only 1 out of 50 users (2%) accessed it
    - Expected: NOT a removal candidate (Team Members is not high-license)
    """

    def test_low_license_item_not_considered(self) -> None:
        """Team Members item should not be a removal candidate regardless of usage."""
        # -- Arrange --
        role_name = "BasicUser"
        user_ids = [f"USR{i:03d}" for i in range(50)]

        security_config = _build_security_config(
            role_name,
            [
                ("EmployeeDirectory", "Team Members", "Read"),
                ("TimeEntryForm", "Team Members", "Write"),
            ],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        # Only 1 user accessed EmployeeDirectory
        activity_events: list[tuple[str, str, str]] = [
            ("USR000", "EmployeeDirectory", "Read"),
        ]
        # Many users accessed TimeEntryForm
        for i in range(40):
            activity_events.append((f"USR{i:03d}", "TimeEntryForm", "Write"))

        user_activity = _build_user_activity(activity_events)
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is False, (
            "Expected should_remove=False when only low-license items have low usage"
        )
        assert len(result.components_to_remove) == 0, (
            "Team Members items should not appear as removal candidates"
        )


# ---------------------------------------------------------------------------
# Test 4: Critical menu item -> Flag for manual review
# ---------------------------------------------------------------------------


class TestCriticalMenuItemFlaggedForReview:
    """Test scenario: Critical menu item with low usage flagged for review.

    Certain menu items are considered critical business operations (e.g.,
    'Posting', 'FinancialClosing', 'YearEndClose'). Even with low usage,
    removing these requires manual review rather than automatic removal.

    Setup:
    - Role: 'SeniorAccountant' with 50 users
    - Menu item 'Posting' requires Finance ($180), only 1 user (2%) used it
    - Expected: Removal candidate but impact = 'High' and flagged for review
    """

    def test_critical_item_flagged_for_manual_review(self) -> None:
        """Critical menu item should be flagged with High impact for review."""
        # -- Arrange --
        role_name = "SeniorAccountant"
        user_ids = [f"USR{i:03d}" for i in range(50)]

        security_config = _build_security_config(
            role_name,
            [
                ("Posting", "Finance", "Write"),
                ("TrialBalance", "Finance", "Read"),
            ],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        # Only 1 user accessed 'Posting'
        activity_events: list[tuple[str, str, str]] = [
            ("USR000", "Posting", "Write"),
        ]
        # Many users accessed TrialBalance
        for i in range(40):
            activity_events.append((f"USR{i:03d}", "TrialBalance", "Read"))

        user_activity = _build_user_activity(activity_events)
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is True, (
            "Expected should_remove=True (critical items still count as candidates)"
        )

        candidate = next(
            (c for c in result.components_to_remove if c.menu_item == "Posting"),
            None,
        )
        assert candidate is not None, "Posting should be a removal candidate"
        assert candidate.impact == "High", (
            f"Critical menu item 'Posting' should have impact='High', got '{candidate.impact}'"
        )
        assert candidate.requires_review is True, (
            "Critical menu item must be flagged for manual review"
        )


# ---------------------------------------------------------------------------
# Test 5: Multiple removal candidates -> Sorted by impact (low first)
# ---------------------------------------------------------------------------


class TestMultipleCandidatesSortedByImpact:
    """Test scenario: Multiple low-usage items sorted by impact.

    When multiple menu items qualify for removal, the algorithm must sort
    them by impact (Low first, then Medium, then High) so that the safest
    removals are presented first.

    Setup:
    - Role: 'WarehouseManager' with 100 users
    - 3 removal candidates with different impact levels:
      - 'RareReport' (SCM, 0 users, 0%) -> Low impact
      - 'SpecialTransfer' (SCM, 3 users, 3%) -> Medium impact
      - 'Posting' (Finance, 1 user, 1%) -> High impact (critical item)
    """

    def test_candidates_sorted_low_impact_first(self) -> None:
        """Removal candidates should be sorted by impact ascending."""
        # -- Arrange --
        role_name = "WarehouseManager"
        user_ids = [f"USR{i:03d}" for i in range(100)]

        security_config = _build_security_config(
            role_name,
            [
                ("RareReport", "SCM", "Read"),
                ("SpecialTransfer", "SCM", "Write"),
                ("Posting", "Finance", "Write"),
                ("InventoryOnHand", "SCM", "Read"),
            ],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        # Activity data: RareReport unused, SpecialTransfer used by 3, Posting by 1
        activity_events: list[tuple[str, str, str]] = []
        # SpecialTransfer: 3 users
        for i in range(3):
            activity_events.append((f"USR{i:03d}", "SpecialTransfer", "Write"))
        # Posting: 1 user
        activity_events.append(("USR000", "Posting", "Write"))
        # InventoryOnHand: 80 users (not a candidate)
        for i in range(80):
            activity_events.append((f"USR{i:03d}", "InventoryOnHand", "Read"))

        user_activity = _build_user_activity(activity_events)
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is True
        assert len(result.components_to_remove) >= 3, (
            f"Expected at least 3 removal candidates, got {len(result.components_to_remove)}"
        )

        # Verify sorting: Low impact first, High impact last
        impacts = [c.impact for c in result.components_to_remove]
        impact_order = {"Low": 0, "Medium": 1, "High": 2}
        numeric_impacts = [impact_order[i] for i in impacts]
        assert numeric_impacts == sorted(numeric_impacts), (
            f"Candidates not sorted by impact ascending: {impacts}"
        )


# ---------------------------------------------------------------------------
# Test 6: Empty role (no users assigned) -> Graceful handling
# ---------------------------------------------------------------------------


class TestEmptyRoleNoUsers:
    """Test scenario: Role with no users assigned.

    The algorithm must handle a role with zero users gracefully without
    division-by-zero or other errors.

    Setup:
    - Role: 'EmptyRole' with 0 users
    - Menu items exist in security config but nobody is assigned
    - Expected: should_remove=False, 0 candidates
    """

    def test_empty_role_returns_no_candidates(self) -> None:
        """Role with no users should return empty result."""
        # -- Arrange --
        role_name = "EmptyRole"
        security_config = _build_security_config(
            role_name,
            [
                ("SomeFinanceForm", "Finance", "Write"),
                ("SomeReport", "SCM", "Read"),
            ],
        )
        user_roles = _build_user_roles(role_name, [])  # No users
        user_activity = _build_user_activity([])  # No activity
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is False
        assert len(result.components_to_remove) == 0


# ---------------------------------------------------------------------------
# Test 7: All items actively used -> No removal candidates
# ---------------------------------------------------------------------------


class TestAllItemsActivelyUsed:
    """Test scenario: Every menu item has >5% usage.

    When all high-license items are actively used by a significant portion
    of users, there should be no removal candidates.

    Setup:
    - Role: 'ActiveTeam' with 20 users
    - 2 Finance items, both used by 10+ users (50%+ usage)
    - Expected: should_remove=False
    """

    def test_no_candidates_when_all_items_used(self) -> None:
        """All items above threshold should produce no candidates."""
        # -- Arrange --
        role_name = "ActiveTeam"
        user_ids = [f"USR{i:03d}" for i in range(20)]

        security_config = _build_security_config(
            role_name,
            [
                ("JournalEntry", "Finance", "Write"),
                ("BankReconciliation", "Finance", "Write"),
            ],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        activity_events: list[tuple[str, str, str]] = []
        # 15 users accessed JournalEntry (75%)
        for i in range(15):
            activity_events.append((f"USR{i:03d}", "JournalEntry", "Write"))
        # 10 users accessed BankReconciliation (50%)
        for i in range(10):
            activity_events.append((f"USR{i:03d}", "BankReconciliation", "Write"))

        user_activity = _build_user_activity(activity_events)
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is False
        assert len(result.components_to_remove) == 0


# ---------------------------------------------------------------------------
# Test 8: Configurable usage threshold
# ---------------------------------------------------------------------------


class TestConfigurableUsageThreshold:
    """Test scenario: Custom threshold changes candidate selection.

    With the default 5% threshold, a 3% usage item is a candidate.
    With a 2% threshold, that same item would NOT be a candidate.

    Setup:
    - Role: 'ThresholdTest' with 100 users
    - Menu item used by 3 users (3%)
    - Test A: usage_threshold=5.0 -> item IS a candidate (3% < 5%)
    - Test B: usage_threshold=2.0 -> item is NOT a candidate (3% > 2%)
    """

    def test_default_threshold_includes_3_percent_usage(self) -> None:
        """3% usage item should be a candidate with default 5% threshold."""
        # -- Arrange --
        role_name = "ThresholdTest"
        user_ids = [f"USR{i:03d}" for i in range(100)]
        security_config = _build_security_config(
            role_name,
            [("RareFinanceForm", "Finance", "Read")],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        activity_events: list[tuple[str, str, str]] = []
        for i in range(3):
            activity_events.append((f"USR{i:03d}", "RareFinanceForm", "Read"))

        user_activity = _build_user_activity(activity_events)
        pricing = _load_pricing()

        # -- Act --
        result = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
            usage_threshold=5.0,
        )

        # -- Assert --
        assert result.should_remove is True
        assert len(result.components_to_remove) == 1

    def test_strict_threshold_excludes_3_percent_usage(self) -> None:
        """3% usage item should NOT be a candidate with 2% threshold."""
        # -- Arrange --
        role_name = "ThresholdTest"
        user_ids = [f"USR{i:03d}" for i in range(100)]
        security_config = _build_security_config(
            role_name,
            [("RareFinanceForm", "Finance", "Read")],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        activity_events: list[tuple[str, str, str]] = []
        for i in range(3):
            activity_events.append((f"USR{i:03d}", "RareFinanceForm", "Read"))

        user_activity = _build_user_activity(activity_events)
        pricing = _load_pricing()

        # -- Act --
        result = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
            usage_threshold=2.0,
        )

        # -- Assert --
        assert result.should_remove is False
        assert len(result.components_to_remove) == 0


# ---------------------------------------------------------------------------
# Test 9: Mixed license tiers -> Only high-license items considered
# ---------------------------------------------------------------------------


class TestMixedLicenseTiersFiltering:
    """Test scenario: Role with mixed license tier items.

    Only items requiring Commerce, Finance, or SCM should be evaluated.
    Operations and Team Members items should be completely skipped.

    Setup:
    - Role: 'MixedRole' with 100 users
    - 4 menu items: 1 Finance (low usage), 1 SCM (low usage),
      1 Operations (low usage), 1 Team Members (low usage)
    - ALL have 0% usage
    - Expected: Only Finance and SCM items appear as candidates
    """

    def test_only_high_license_items_in_candidates(self) -> None:
        """Only Commerce/Finance/SCM items should appear as removal candidates."""
        # -- Arrange --
        role_name = "MixedRole"
        user_ids = [f"USR{i:03d}" for i in range(100)]

        security_config = _build_security_config(
            role_name,
            [
                ("FinanceReport", "Finance", "Read"),
                ("WarehouseTransfer", "SCM", "Write"),
                ("BasicOpsForm", "Operations", "Read"),
                ("SelfServiceForm", "Team Members", "Read"),
            ],
        )
        user_roles = _build_user_roles(role_name, user_ids)

        # No one used any of these items
        user_activity = _build_user_activity([])
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is True
        assert len(result.components_to_remove) == 2, (
            f"Expected exactly 2 candidates (Finance + SCM), "
            f"got {len(result.components_to_remove)}"
        )

        candidate_items = {c.menu_item for c in result.components_to_remove}
        assert "FinanceReport" in candidate_items
        assert "WarehouseTransfer" in candidate_items
        assert "BasicOpsForm" not in candidate_items
        assert "SelfServiceForm" not in candidate_items

        # Verify license types are all high-license
        for c in result.components_to_remove:
            assert c.license_type in HIGH_LICENSE_TYPES, (
                f"Unexpected license type '{c.license_type}' in candidates"
            )


# ---------------------------------------------------------------------------
# Test 10: Expected outcome string is populated
# ---------------------------------------------------------------------------


class TestExpectedOutcomeString:
    """Test scenario: Result includes a descriptive expected outcome.

    The output should contain a human-readable expected_outcome string
    describing the number of components recommended for removal.
    """

    def test_expected_outcome_includes_count(self) -> None:
        """Expected outcome should mention the number of components to remove."""
        # -- Arrange --
        role_name = "OutcomeTest"
        user_ids = [f"USR{i:03d}" for i in range(50)]

        security_config = _build_security_config(
            role_name,
            [
                ("UnusedFinanceForm", "Finance", "Read"),
                ("UnusedCommerceForm", "Commerce", "Read"),
            ],
        )
        user_roles = _build_user_roles(role_name, user_ids)
        user_activity = _build_user_activity([])  # No activity at all
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.should_remove is True
        assert result.expected_outcome is not None
        assert len(result.expected_outcome) > 0
        # Should mention the count of items
        assert "2" in result.expected_outcome, (
            f"Expected outcome should mention 2 components: '{result.expected_outcome}'"
        )


# ---------------------------------------------------------------------------
# Test 11: Role name correctly reflected in result
# ---------------------------------------------------------------------------


class TestRoleNameInResult:
    """Test scenario: Result references the analyzed role name."""

    def test_role_name_in_result(self) -> None:
        """Result should include the role that was analyzed."""
        # -- Arrange --
        role_name = "SpecificRoleName"
        user_ids = ["USR001"]

        security_config = _build_security_config(
            role_name,
            [("SomeForm", "Finance", "Read")],
        )
        user_roles = _build_user_roles(role_name, user_ids)
        user_activity = _build_user_activity([])
        pricing = _load_pricing()

        # -- Act --
        result: ComponentRemovalResult = recommend_component_removal(
            role_name=role_name,
            security_config=security_config,
            user_roles=user_roles,
            user_activity=user_activity,
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.role_name == role_name
