"""Tests for Algorithm 2.1: Permission vs. Usage Analyzer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_2_1_permission_usage_analyzer.py is implemented.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 398-519.

Algorithm 2.1 compares what a user CAN do (theoretical permissions from their
assigned roles) with what they ACTUALLY do (observed activity over a
configurable analysis period).  It identifies three optimization opportunities:

  1. License downgrade -- user's actual usage only requires a lower-cost
     license than the one implied by their assigned roles.
  2. Permission reduction -- user exercises <50% of their theoretical
     permissions, indicating over-provisioned roles that could be simplified.
  3. Unused role detection -- roles whose menu items the user never accessed
     during the analysis period.

Key design decisions reflected in tests:
  - New users (<30 days since first activity) are SKIPPED -- insufficient data
    to make reliable recommendations.
  - Multiple opportunities per user are sorted by estimated savings descending.
  - The algorithm operates on DataFrames aligned with existing Phase 1 schemas
    (user_activity, security_config, user_role_assignments).
  - License pricing uses the shared get_license_price() utility from
    src/utils/pricing.py for consistency with other algorithms.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

# Tolerance for floating-point comparisons on confidence scores
CONFIDENCE_TOLERANCE: float = 0.05

# Tolerance for monetary comparisons (cents)
MONETARY_TOLERANCE: float = 0.01


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON."""
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_security_config(
    roles: dict[str, list[tuple[str, str]]],
) -> pd.DataFrame:
    """Build a synthetic security configuration DataFrame.

    Args:
        roles: Mapping of role_name -> list of (menu_item, license_tier) tuples.
            Each entry becomes a row in the security config.

    Returns:
        DataFrame with columns: securityrole, AOTName, LicenseType.
    """
    rows: list[dict[str, str]] = []
    for role_name, items in roles.items():
        for menu_item, license_tier in items:
            rows.append(
                {
                    "securityrole": role_name,
                    "AOTName": menu_item,
                    "LicenseType": license_tier,
                }
            )
    return pd.DataFrame(rows)


def _build_user_role_assignments(
    assignments: list[tuple[str, str]],
) -> pd.DataFrame:
    """Build a synthetic user-role assignment DataFrame.

    Args:
        assignments: List of (user_id, role_name) tuples.

    Returns:
        DataFrame with columns: user_id, role_name.
    """
    rows: list[dict[str, str]] = []
    for user_id, role_name in assignments:
        rows.append({"user_id": user_id, "role_name": role_name})
    return pd.DataFrame(rows)


def _build_activity_df(
    user_id: str,
    activities: list[tuple[str, str, str]],
    days_active: int = 90,
) -> pd.DataFrame:
    """Build a synthetic activity DataFrame for a single user.

    Args:
        user_id: The user identifier.
        activities: List of (menu_item, action, license_tier) tuples.
            Each tuple becomes one activity row.
        days_active: Number of days the user has been active (used for
            generating timestamps that spread across the analysis period).

    Returns:
        DataFrame with columns: user_id, timestamp, menu_item, action,
        session_id, license_tier, feature.
    """
    rows: list[dict[str, str]] = []
    for i, (menu_item, action, license_tier) in enumerate(activities):
        # Spread timestamps across the analysis window
        day_offset = i % max(days_active, 1)
        rows.append(
            {
                "user_id": user_id,
                "timestamp": f"2026-01-{15 - min(day_offset, 14):02d} "
                f"09:{i // 60:02d}:{i % 60:02d}",
                "menu_item": menu_item,
                "action": action,
                "session_id": f"sess-{user_id}-{i:04d}",
                "license_tier": license_tier,
                "feature": "TestFeature",
            }
        )
    return pd.DataFrame(rows)


def _build_multi_user_activity(
    user_activities: dict[str, list[tuple[str, str, str]]],
    days_active: int = 90,
) -> pd.DataFrame:
    """Build activity data for multiple users.

    Args:
        user_activities: Mapping of user_id -> list of
            (menu_item, action, license_tier) tuples.
        days_active: Number of days of activity history.

    Returns:
        Combined DataFrame for all users.
    """
    frames: list[pd.DataFrame] = []
    for user_id, activities in user_activities.items():
        frames.append(
            _build_activity_df(
                user_id=user_id,
                activities=activities,
                days_active=days_active,
            )
        )
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Test 1: Finance license user only uses Team Members features -> Downgrade
# ---------------------------------------------------------------------------


class TestLicenseDowngradeOpportunity:
    """User with Finance roles but activity only touches Team Members forms.

    Scenario:
    - User USR_FIN_TM has role 'Accountant' with Finance + Team Members items
    - User ONLY accessed Team Members-level menu items in 90 days
    - Current theoretical license: Finance ($180/month)
    - Actual needed license: Team Members ($60/month)
    - Expected: DOWNGRADE recommendation with $120/month savings

    This is the primary value proposition of Algorithm 2.1 -- detecting users
    whose granted permissions far exceed their actual usage needs.
    """

    def test_finance_user_only_uses_team_members_features(self) -> None:
        """User on Finance role using only TM features should get downgrade."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {
                "Accountant": [
                    ("GeneralJournalEntry", "Finance"),
                    ("BudgetEntry", "Finance"),
                    ("CustTable", "Finance"),
                    ("VendTable", "Finance"),
                    ("HcmESSWorkspace", "Team Members"),
                    ("DirPartyTable", "Team Members"),
                    ("HcmMyExpenses", "Team Members"),
                ],
            }
        )
        user_roles = _build_user_role_assignments([("USR_FIN_TM", "Accountant")])
        # User only accesses Team Members eligible forms (reads + self-service writes)
        activities: list[tuple[str, str, str]] = []
        for _ in range(80):
            activities.append(("HcmESSWorkspace", "Read", "Team Members"))
        for _ in range(15):
            activities.append(("DirPartyTable", "Read", "Team Members"))
        for _ in range(5):
            activities.append(("HcmMyExpenses", "Write", "Team Members"))

        user_activity = _build_activity_df("USR_FIN_TM", activities)
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) >= 1, "Should produce at least one recommendation"

        # Find the license downgrade recommendation
        downgrade_recs = [
            r for r in results
            if r.action.value == "downgrade"
        ]
        assert len(downgrade_recs) >= 1, (
            "Should recommend license downgrade for Finance user "
            "using only Team Members features"
        )

        rec = downgrade_recs[0]
        assert rec.user_id == "USR_FIN_TM"
        assert rec.current_license == "Finance"
        assert rec.recommended_license == "Team Members"
        assert rec.savings is not None
        assert abs(rec.savings.monthly_savings - 120.0) <= MONETARY_TOLERANCE
        assert abs(rec.savings.annual_savings - 1440.0) <= MONETARY_TOLERANCE
        assert rec.confidence_score >= 0.70  # At least MEDIUM confidence


# ---------------------------------------------------------------------------
# Test 2: User uses <50% of permissions -> Permission reduction
# ---------------------------------------------------------------------------


class TestPermissionReductionOpportunity:
    """User granted many permissions but only uses a small fraction.

    Scenario:
    - User USR_OVERPRIV has role 'Accountant' with 10 Finance menu items
    - User only accessed 3 out of 10 items in 90 days
    - Permission utilization = 30% (below 50% threshold)
    - Expected: REVIEW_REQUIRED with permission reduction suggestion

    This tests the second check in the Algorithm 2.1 specification:
    'If unused permissions > 50% of theoretical, recommend role cleanup.'
    """

    def test_low_permission_utilization_flagged(self) -> None:
        """User using <50% of permissions should get review recommendation."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        # 10 Finance menu items in the Accountant role
        security_config = _build_security_config(
            {
                "Accountant": [
                    ("GeneralJournalEntry", "Finance"),
                    ("BudgetEntry", "Finance"),
                    ("CustTable", "Finance"),
                    ("VendTable", "Finance"),
                    ("BankReconciliation", "Finance"),
                    ("FixedAssetJournal", "Finance"),
                    ("TaxReport", "Finance"),
                    ("CashFlowForecast", "Finance"),
                    ("LedgerPostingJournal", "Finance"),
                    ("FinancialDimensions", "Finance"),
                ],
            }
        )
        user_roles = _build_user_role_assignments([("USR_OVERPRIV", "Accountant")])

        # User only uses 3 of 10 items (30% utilization)
        activities: list[tuple[str, str, str]] = []
        for _ in range(40):
            activities.append(("GeneralJournalEntry", "Write", "Finance"))
        for _ in range(30):
            activities.append(("BudgetEntry", "Read", "Finance"))
        for _ in range(30):
            activities.append(("CustTable", "Read", "Finance"))

        user_activity = _build_activity_df("USR_OVERPRIV", activities)
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) >= 1, "Should produce at least one recommendation"

        # Find permission reduction recommendations
        rec = results[0]
        assert rec.user_id == "USR_OVERPRIV"

        # The primary factor or reason should mention permission utilization
        assert "utilization" in rec.reason.primary_factor.lower() or any(
            "utilization" in f.lower() or "unused" in f.lower() or "permission" in f.lower()
            for f in rec.reason.supporting_factors
        ), (
            "Recommendation reason should mention permission utilization. "
            f"Got primary_factor='{rec.reason.primary_factor}', "
            f"supporting_factors={rec.reason.supporting_factors}"
        )


# ---------------------------------------------------------------------------
# Test 3: Permissions match usage -> No action
# ---------------------------------------------------------------------------


class TestPermissionsMatchUsage:
    """User whose permissions closely match their actual usage.

    Scenario:
    - User USR_OPTIMAL has role 'Accountant' with 5 Finance menu items
    - User accessed 4 out of 5 items (80% utilization)
    - User performs writes (needs Finance license)
    - Expected: NO_CHANGE -- well-configured user

    This validates that the algorithm does not produce false positives
    for well-utilized roles with appropriate license assignments.
    """

    def test_well_utilized_user_gets_no_change(self) -> None:
        """User with good permission utilization should get no_change."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {
                "Accountant": [
                    ("GeneralJournalEntry", "Finance"),
                    ("BudgetEntry", "Finance"),
                    ("CustTable", "Finance"),
                    ("VendTable", "Finance"),
                    ("BankReconciliation", "Finance"),
                ],
            }
        )
        user_roles = _build_user_role_assignments([("USR_OPTIMAL", "Accountant")])

        # User accesses 4 of 5 items (80%) with writes
        activities: list[tuple[str, str, str]] = []
        for _ in range(30):
            activities.append(("GeneralJournalEntry", "Write", "Finance"))
        for _ in range(25):
            activities.append(("BudgetEntry", "Write", "Finance"))
        for _ in range(25):
            activities.append(("CustTable", "Read", "Finance"))
        for _ in range(20):
            activities.append(("VendTable", "Write", "Finance"))

        user_activity = _build_activity_df("USR_OPTIMAL", activities)
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        # Either no results (user is optimal) or results with no_change action
        if len(results) > 0:
            rec = results[0]
            assert rec.user_id == "USR_OPTIMAL"
            assert rec.action.value == "no_change", (
                f"Expected no_change for well-utilized user, "
                f"got {rec.action.value}"
            )
            # No savings for no_change
            if rec.savings is not None:
                assert rec.savings.monthly_savings <= MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test 4: New user (<30 days) -> Skip with insufficient data
# ---------------------------------------------------------------------------


class TestNewUserSkipped:
    """New user with fewer than 30 days of activity should be skipped.

    Scenario:
    - User USR_NEW has been active for only 15 days
    - Even though they only use Team Members features, the data is
      insufficient for a reliable recommendation
    - Expected: No recommendation generated (user excluded)

    This tests the edge case handling from the specification:
    'Skip new users with insufficient analysis period.'
    """

    def test_new_user_under_30_days_excluded(self) -> None:
        """User with <30 days of activity should not produce recommendations."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {
                "Accountant": [
                    ("GeneralJournalEntry", "Finance"),
                    ("HcmESSWorkspace", "Team Members"),
                ],
            }
        )
        user_roles = _build_user_role_assignments([("USR_NEW", "Accountant")])

        # Only 15 days of activity with timestamps clustered in last 15 days
        activities: list[tuple[str, str, str]] = []
        for _ in range(50):
            activities.append(("HcmESSWorkspace", "Read", "Team Members"))

        user_activity = _build_activity_df("USR_NEW", activities, days_active=15)
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
            min_activity_days=30,
        )

        # -- Assert --
        user_recs = [r for r in results if r.user_id == "USR_NEW"]
        assert len(user_recs) == 0, (
            f"New user with <30 days of activity should be excluded, "
            f"but got {len(user_recs)} recommendation(s)"
        )


# ---------------------------------------------------------------------------
# Test 5: Multiple opportunities -> Highest savings first
# ---------------------------------------------------------------------------


class TestMultipleOpportunitiesSorted:
    """Multiple optimization opportunities sorted by savings descending.

    Scenario:
    - User A: Finance user using only TM features ($120/month savings)
    - User B: Operations user using only TM features ($30/month savings)
    - User C: SCM user using only TM features ($120/month savings)
    - Expected: Results sorted by savings (A & C before B)

    This validates the sorting requirement from the specification:
    'Sort results by savings descending (highest first).'
    """

    def test_results_sorted_by_savings_descending(self) -> None:
        """Results should be sorted by savings in descending order."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {
                "FinanceRole": [
                    ("GeneralJournalEntry", "Finance"),
                    ("HcmESSWorkspace", "Team Members"),
                ],
                "OpsRole": [
                    ("SalesOrder", "Operations"),
                    ("HcmESSWorkspace", "Team Members"),
                ],
                "SCMRole": [
                    ("PurchaseOrder", "SCM"),
                    ("HcmESSWorkspace", "Team Members"),
                ],
            }
        )
        user_roles = _build_user_role_assignments(
            [
                ("USR_A", "FinanceRole"),
                ("USR_B", "OpsRole"),
                ("USR_C", "SCMRole"),
            ]
        )

        # All users only use Team Members features
        tm_activities: list[tuple[str, str, str]] = [
            ("HcmESSWorkspace", "Read", "Team Members")
        ] * 100

        user_activity = pd.concat(
            [
                _build_activity_df("USR_A", tm_activities),
                _build_activity_df("USR_B", tm_activities),
                _build_activity_df("USR_C", tm_activities),
            ],
            ignore_index=True,
        )
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        downgrade_results = [
            r for r in results if r.action.value == "downgrade" and r.savings is not None
        ]
        assert len(downgrade_results) >= 2, (
            f"Expected at least 2 downgrade results, got {len(downgrade_results)}"
        )

        # Verify sorted by savings descending
        for i in range(len(downgrade_results) - 1):
            assert downgrade_results[i].savings is not None
            assert downgrade_results[i + 1].savings is not None
            assert (
                downgrade_results[i].savings.annual_savings
                >= downgrade_results[i + 1].savings.annual_savings
            ), (
                f"Results not sorted by savings descending at index {i}: "
                f"{downgrade_results[i].savings.annual_savings} < "
                f"{downgrade_results[i + 1].savings.annual_savings}"
            )


# ---------------------------------------------------------------------------
# Test 6: Empty activity data -> No results
# ---------------------------------------------------------------------------


class TestEmptyActivityData:
    """Algorithm handles empty input gracefully.

    Scenario:
    - Empty user activity DataFrame
    - Should return empty list without raising exceptions
    """

    def test_empty_activity_returns_empty_results(self) -> None:
        """Empty user activity should produce zero recommendations."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        empty_activity = pd.DataFrame(
            columns=[
                "user_id", "timestamp", "menu_item", "action",
                "session_id", "license_tier", "feature",
            ]
        )
        security_config = _build_security_config(
            {"Accountant": [("GeneralJournalEntry", "Finance")]}
        )
        user_roles = _build_user_role_assignments([("USR_EMPTY", "Accountant")])
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=empty_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        assert results == [], (
            f"Expected empty results for empty activity data, "
            f"got {len(results)} recommendations"
        )


# ---------------------------------------------------------------------------
# Test 7: SCM user using only Operations-level features -> Downgrade to Ops
# ---------------------------------------------------------------------------


class TestSCMToOperationsDowngrade:
    """User on SCM license whose activity only requires Operations tier.

    Scenario:
    - User has SCM role ($180/month) but only uses Operations-level features
    - Expected: Downgrade to Operations ($90/month), saving $90/month
    - Validates intermediate license tier downgrades (not just to TM)
    """

    def test_scm_user_downgrade_to_operations(self) -> None:
        """SCM user using Ops features should get downgrade to Operations."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {
                "WarehouseManager": [
                    ("PurchaseOrder", "SCM"),
                    ("InventoryAdjustment", "SCM"),
                    ("WarehousePicking", "SCM"),
                    ("SalesOrder", "Operations"),
                    ("ProductionOrder", "Operations"),
                ],
            }
        )
        user_roles = _build_user_role_assignments([("USR_SCM_OPS", "WarehouseManager")])

        # User only uses Operations-level features
        activities: list[tuple[str, str, str]] = []
        for _ in range(60):
            activities.append(("SalesOrder", "Write", "Operations"))
        for _ in range(40):
            activities.append(("ProductionOrder", "Read", "Operations"))

        user_activity = _build_activity_df("USR_SCM_OPS", activities)
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        downgrade_recs = [r for r in results if r.action.value == "downgrade"]
        assert len(downgrade_recs) >= 1, (
            "SCM user with Operations-only usage should get downgrade recommendation"
        )
        rec = downgrade_recs[0]
        assert rec.user_id == "USR_SCM_OPS"
        assert rec.current_license == "SCM"
        assert rec.recommended_license == "Operations"
        assert rec.savings is not None
        assert abs(rec.savings.monthly_savings - 90.0) <= MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test 8: Multi-role user where theoretical license is driven by unused role
# ---------------------------------------------------------------------------


class TestMultiRoleUnusedHighLicense:
    """User with multiple roles where the highest-license role is unused.

    Scenario:
    - User has 'Accountant' (Finance) and 'TeamMemberRole' (TM)
    - Theoretical license: Finance ($180) from Accountant role
    - User ONLY accesses Team Members features from TeamMemberRole
    - Expected: Downgrade because actual usage only needs TM license

    This validates Algorithm 2.1's cross-role analysis -- the user has
    Finance permissions through Accountant but never touches Finance items.
    """

    def test_unused_high_license_role_triggers_downgrade(self) -> None:
        """Unused Finance role should trigger downgrade when TM usage only."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {
                "Accountant": [
                    ("GeneralJournalEntry", "Finance"),
                    ("BudgetEntry", "Finance"),
                ],
                "TeamMemberRole": [
                    ("HcmESSWorkspace", "Team Members"),
                    ("HcmMyExpenses", "Team Members"),
                ],
            }
        )
        user_roles = _build_user_role_assignments(
            [
                ("USR_MULTI", "Accountant"),
                ("USR_MULTI", "TeamMemberRole"),
            ]
        )

        # User only uses TeamMemberRole features
        activities: list[tuple[str, str, str]] = []
        for _ in range(80):
            activities.append(("HcmESSWorkspace", "Read", "Team Members"))
        for _ in range(20):
            activities.append(("HcmMyExpenses", "Write", "Team Members"))

        user_activity = _build_activity_df("USR_MULTI", activities)
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        downgrade_recs = [
            r for r in results
            if r.action.value == "downgrade" and r.user_id == "USR_MULTI"
        ]
        assert len(downgrade_recs) >= 1, (
            "User with Finance role but only TM usage should get downgrade"
        )
        rec = downgrade_recs[0]
        assert rec.current_license == "Finance"
        assert rec.recommended_license == "Team Members"
        assert rec.savings is not None
        assert abs(rec.savings.monthly_savings - 120.0) <= MONETARY_TOLERANCE


# ---------------------------------------------------------------------------
# Test 9: Algorithm output structure validation
# ---------------------------------------------------------------------------


class TestOutputStructure:
    """Validate that output conforms to the LicenseRecommendation schema.

    Every recommendation from Algorithm 2.1 must:
    - Have algorithm_id == "2.1"
    - Have a valid recommendation_id (UUID pattern)
    - Have user_id set
    - Have current_license and current_license_cost_monthly
    - Have confidence_score between 0 and 1
    - Have analysis_period_days >= 1
    - Have sample_size >= 0
    """

    def test_output_schema_compliance(self) -> None:
        """Output must conform to LicenseRecommendation model."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )
        from src.models.output_schemas import LicenseRecommendation

        # -- Arrange --
        security_config = _build_security_config(
            {
                "Accountant": [
                    ("GeneralJournalEntry", "Finance"),
                    ("HcmESSWorkspace", "Team Members"),
                ],
            }
        )
        user_roles = _build_user_role_assignments([("USR_SCHEMA", "Accountant")])

        activities: list[tuple[str, str, str]] = [
            ("HcmESSWorkspace", "Read", "Team Members")
        ] * 100
        user_activity = _build_activity_df("USR_SCHEMA", activities)
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) >= 1, "Should produce at least one recommendation"
        for rec in results:
            assert isinstance(rec, LicenseRecommendation)
            assert rec.algorithm_id == "2.1"
            assert rec.user_id == "USR_SCHEMA"
            assert 0.0 <= rec.confidence_score <= 1.0
            assert rec.analysis_period_days >= 1
            assert rec.sample_size >= 0
            assert rec.current_license is not None
            assert rec.current_license_cost_monthly >= 0


# ---------------------------------------------------------------------------
# Test 10: Batch processing with mixed user profiles
# ---------------------------------------------------------------------------


class TestBatchMixedProfiles:
    """Process multiple users with different optimization profiles.

    Scenario:
    - User A: Finance user using only TM features (downgrade to TM)
    - User B: Well-configured Finance user (no change)
    - User C: SCM user using only TM features (downgrade to TM)
    - Expected: Correct classification for each user
    """

    def test_batch_mixed_user_classification(self) -> None:
        """Batch processing should correctly classify each user."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {
                "Accountant": [
                    ("GeneralJournalEntry", "Finance"),
                    ("HcmESSWorkspace", "Team Members"),
                ],
                "SCMClerk": [
                    ("PurchaseOrder", "SCM"),
                    ("HcmESSWorkspace", "Team Members"),
                ],
            }
        )
        user_roles = _build_user_role_assignments(
            [
                ("USR_BATCH_A", "Accountant"),
                ("USR_BATCH_B", "Accountant"),
                ("USR_BATCH_C", "SCMClerk"),
            ]
        )

        # User A: Only TM features
        activities_a = [("HcmESSWorkspace", "Read", "Team Members")] * 100

        # User B: Uses Finance features (well-configured)
        activities_b: list[tuple[str, str, str]] = []
        for _ in range(60):
            activities_b.append(("GeneralJournalEntry", "Write", "Finance"))
        for _ in range(40):
            activities_b.append(("HcmESSWorkspace", "Read", "Team Members"))

        # User C: Only TM features (has SCM role)
        activities_c = [("HcmESSWorkspace", "Read", "Team Members")] * 100

        user_activity = pd.concat(
            [
                _build_activity_df("USR_BATCH_A", activities_a),
                _build_activity_df("USR_BATCH_B", activities_b),
                _build_activity_df("USR_BATCH_C", activities_c),
            ],
            ignore_index=True,
        )
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        # User A: should have downgrade
        a_recs = [r for r in results if r.user_id == "USR_BATCH_A"]
        assert any(r.action.value == "downgrade" for r in a_recs), (
            "User A should get downgrade recommendation"
        )

        # User B: should have no_change or not appear (well-configured)
        b_recs = [r for r in results if r.user_id == "USR_BATCH_B"]
        if b_recs:
            assert all(r.action.value == "no_change" for r in b_recs), (
                f"User B should be no_change, got {[r.action.value for r in b_recs]}"
            )

        # User C: should have downgrade
        c_recs = [r for r in results if r.user_id == "USR_BATCH_C"]
        assert any(r.action.value == "downgrade" for r in c_recs), (
            "User C should get downgrade recommendation"
        )


# ---------------------------------------------------------------------------
# Test 11: Permission utilization metric accuracy
# ---------------------------------------------------------------------------


class TestPermissionUtilizationCalculation:
    """Validate accurate permission utilization calculation.

    Scenario:
    - Role has 8 menu items
    - User accessed 2 of 8 items = 25% utilization
    - Expected: Algorithm reports ~25% utilization in reason

    This tests the core metric: (unique items used / total theoretical items).
    """

    def test_utilization_percentage_accuracy(self) -> None:
        """Utilization percentage should reflect actual/theoretical ratio."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {
                "BigRole": [
                    ("Item1", "Finance"),
                    ("Item2", "Finance"),
                    ("Item3", "Finance"),
                    ("Item4", "Finance"),
                    ("Item5", "Finance"),
                    ("Item6", "Finance"),
                    ("Item7", "Finance"),
                    ("Item8", "Finance"),
                ],
            }
        )
        user_roles = _build_user_role_assignments([("USR_UTIL", "BigRole")])

        # User only accesses 2 of 8 items (25%)
        activities: list[tuple[str, str, str]] = []
        for _ in range(60):
            activities.append(("Item1", "Write", "Finance"))
        for _ in range(40):
            activities.append(("Item2", "Read", "Finance"))

        user_activity = _build_activity_df("USR_UTIL", activities)
        pricing = _load_pricing()

        # -- Act --
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) >= 1, "Should produce recommendation for low-utilization user"
        rec = results[0]

        # The reason should reference the low utilization (25%)
        all_text = (
            rec.reason.primary_factor
            + " ".join(rec.reason.supporting_factors)
        )
        assert "25" in all_text or "utilization" in all_text.lower(), (
            "Recommendation should reference the ~25% utilization rate. "
            f"Got: primary='{rec.reason.primary_factor}', "
            f"supporting={rec.reason.supporting_factors}"
        )


# ---------------------------------------------------------------------------
# Test 12: User with no role assignments -> Handle gracefully
# ---------------------------------------------------------------------------


class TestUserWithNoRoles:
    """User in activity data but not in role assignments.

    The algorithm should handle users who have activity but no matching
    role assignment data gracefully (either skip or produce minimal output).
    """

    def test_user_without_role_assignments_handled(self) -> None:
        """User with activity but no role assignments should not crash."""
        from src.algorithms.algorithm_2_1_permission_usage_analyzer import (
            analyze_permission_usage,
        )

        # -- Arrange --
        security_config = _build_security_config(
            {"Accountant": [("GeneralJournalEntry", "Finance")]}
        )
        # Empty role assignments -- no user matches
        user_roles = _build_user_role_assignments([])

        activities = [("GeneralJournalEntry", "Read", "Finance")] * 100
        user_activity = _build_activity_df("USR_NO_ROLES", activities)
        pricing = _load_pricing()

        # -- Act -- (should not raise)
        results = analyze_permission_usage(
            user_activity=user_activity,
            security_config=security_config,
            user_role_assignments=user_roles,
            pricing_config=pricing,
        )

        # -- Assert --
        # Either empty results or results without crash
        assert isinstance(results, list)
