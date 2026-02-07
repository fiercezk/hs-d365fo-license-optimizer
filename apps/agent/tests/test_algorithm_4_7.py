"""Tests for Algorithm 4.7: New User License Recommendation Engine (TDD).

Specification: Requirements/07-Advanced-Algorithms-Expansion.md Algorithm 4.7

Test scenarios cover:
- Simple case: single menu item → single role → single license
- Multiple menu items → single optimal role
- Multiple menu items → multiple roles required
- Menu item not found in any role (edge case)
- SoD conflict detection with recommendations
- Multiple recommendation alternatives (lowest cost, fewest roles)
- Edge case: no coverage possible with provided roles
- High confidence (no SoD conflicts) vs medium confidence (with conflicts)
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.algorithms.algorithm_4_7_new_user_license_recommender import (
    NewUserLicenseRecommender,
    suggest_license_for_new_user,
)
from src.models.input_schemas import SecurityConfigRecord


@pytest.fixture
def security_config_data() -> list[SecurityConfigRecord]:
    """Load security configuration from CSV fixture.

    Returns: List of SecurityConfigRecord objects representing role → menu item mappings.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "algo_4_7_security_config.csv"
    df = pd.read_csv(fixture_path)
    records = []
    for _, row in df.iterrows():
        records.append(
            SecurityConfigRecord(
                security_role=row["security_role"],
                aot_name=row["aot_name"],
                access_level=row["access_level"],
                license_type=row["license_type"],
                priority=int(row["priority"]),
                entitled=bool(row["entitled"]),
                not_entitled=bool(row["not_entitled"]),
                security_type=row["security_type"],
            )
        )
    return records


@pytest.fixture
def pricing_config() -> dict:
    """Load pricing configuration from pricing.json.

    Returns: Dictionary with license pricing data.
    """
    # Use absolute path to find pricing.json
    config_path = Path(__file__).parent.parent.parent.parent / "data" / "config" / "pricing.json"
    with open(config_path, "r") as f:
        return json.load(f)


@pytest.fixture
def sod_matrix() -> dict:
    """Load SoD conflict matrix.

    For Phase 1 MVP, we use a minimal SoD matrix.
    Full matrix is in Requirements/15-Default-SoD-Conflict-Matrix.md

    Returns: Dictionary with SoD conflict rules.
    """
    # Minimal SoD matrix for testing
    return {
        "rules": [
            {
                "id": "AP-002",
                "severity": "CRITICAL",
                "role_pair": ["Accounts payable clerk", "Accounts payable manager"],
                "description": "AP Clerk cannot also be AP Manager (enter and approve)",
            },
            {
                "id": "GL-001",
                "severity": "CRITICAL",
                "role_pair": ["General ledger clerk", "Accounting manager"],
                "description": "GL Clerk cannot also approve own entries",
            },
        ]
    }


def test_simple_single_menu_item_single_role(security_config_data, pricing_config):
    """Test scenario: Admin specifies single menu item → single role covers it.

    This is the obvious case where one role provides exactly the menu item needed.
    Expected: HIGH confidence, single role, low license cost.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    # New user needs only to view the ledger
    required_menu_items = ["LedgerInquiry"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    # Should get recommendations
    assert len(recommendations) > 0
    assert len(recommendations) <= 3  # Top 3

    # First recommendation should be the cheapest viable option
    first_rec = recommendations[0]
    assert first_rec.menu_item_coverage == 1.0  # 100% coverage
    assert first_rec.confidence == "HIGH"  # No SoD conflicts
    # Either GL Clerk (Operations) or Accountant (Finance) can provide LedgerInquiry
    # Should pick GL Clerk which is cheaper
    assert first_rec.license_required == "Operations"  # $90/month
    assert first_rec.monthly_cost == 90.0


def test_multiple_menu_items_single_role_covers_all(security_config_data, pricing_config):
    """Test scenario: Multiple menu items, one role covers all.

    Admin specifies menu items that a single role provides.
    Expected: HIGH confidence, minimal role set, optimal cost.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    # Accountant role covers all these menu items
    required_menu_items = ["GeneralJournalEntry", "LedgerInquiry", "TrialBalance"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    assert len(recommendations) > 0
    first_rec = recommendations[0]
    assert first_rec.menu_item_coverage == 1.0
    assert first_rec.confidence == "HIGH"
    # GL Clerk also provides all these items and is cheaper, so should be selected
    assert first_rec.license_required == "Operations"  # $90/month (GL Clerk)
    assert first_rec.monthly_cost == 90.0
    assert first_rec.sod_conflicts == 0


def test_multiple_menu_items_multiple_roles_required(security_config_data, pricing_config):
    """Test scenario: Multiple menu items requiring multiple roles.

    Admin specifies menu items from different modules, greedy set-covering
    must find minimum role combination.
    Expected: Multiple roles, higher license cost, full coverage.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    # Menu items from different processes
    required_menu_items = [
        "InventoryInquiry",
        "PurchaseOrderEntry",
        "InvoiceEntry",
    ]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    assert len(recommendations) > 0
    # Should require multiple roles since no single role covers all 3 items
    first_rec = recommendations[0]
    assert first_rec.menu_item_coverage >= 0.66  # At least 2 of 3
    # Highest priority license should be SCM or Finance since inventory items
    assert first_rec.license_required in ["SCM", "Finance", "Operations"]


def test_menu_item_not_found_edge_case(security_config_data, pricing_config):
    """Test edge case: Requested menu item not found in any role.

    Expected: Partial coverage warning, HIGH confidence on what CAN be covered.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    # Include both valid and invalid menu items
    required_menu_items = ["GeneralJournalEntry", "NonExistentMenuItemXYZ"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    # Should still get recommendations for valid items
    assert len(recommendations) > 0
    first_rec = recommendations[0]
    # Coverage should be less than 100% due to non-existent item
    assert first_rec.menu_item_coverage < 1.0
    # Should have warning about uncovered items
    assert len(first_rec.warnings) > 0


def test_recommendation_sorted_by_cost_then_roles(security_config_data, pricing_config):
    """Test that recommendations are sorted correctly.

    Specification pseudocode line 1804: Sort by cost ASC, then roleCount ASC
    Expected: First recommendation = lowest cost, second = fewest roles, etc.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    required_menu_items = ["GeneralJournalEntry", "InvoiceEntry", "CustomerInquiry"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    # Verify sorting property: cost should be non-decreasing
    costs = [rec.monthly_cost for rec in recommendations]
    for i in range(len(costs) - 1):
        assert costs[i] <= costs[i + 1], "Recommendations not sorted by cost"


def test_sod_conflict_detection_in_recommendations(security_config_data, pricing_config):
    """Test that SoD conflicts are detected and flagged in recommendations.

    Expected: Recommendations with SoD conflicts show MEDIUM confidence,
    clean recommendations show HIGH confidence.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    # Menu items that might require conflicting roles
    required_menu_items = ["GeneralJournalEntry", "LedgerInquiry"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    assert len(recommendations) > 0

    # At least one recommendation should be HIGH confidence (no SoD conflicts)
    high_confidence_exists = any(rec.confidence == "HIGH" for rec in recommendations)
    assert high_confidence_exists, "No HIGH confidence recommendations found"


def test_top_3_recommendations_returned(security_config_data, pricing_config):
    """Test that algorithm returns top 3 recommendations (or fewer if N/A).

    Specification line 1807: Return top 3
    Expected: Max 3 recommendations, sorted by cost.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    required_menu_items = [
        "GeneralJournalEntry",
        "InvoiceEntry",
        "CustomerInquiry",
        "LedgerInquiry",
    ]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    # Should return AT MOST 3 recommendations
    assert len(recommendations) <= 3
    assert len(recommendations) > 0


def test_output_structure_contains_required_fields(security_config_data, pricing_config):
    """Test that recommendation output has all required fields.

    Expected fields:
    - recommended_roles
    - role_count
    - license_required
    - monthly_cost
    - menu_item_coverage
    - sod_conflicts
    - confidence
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    required_menu_items = ["GeneralJournalEntry"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    assert len(recommendations) > 0
    rec = recommendations[0]

    # Verify all required fields exist
    assert hasattr(rec, "recommended_roles")
    assert hasattr(rec, "role_count")
    assert hasattr(rec, "license_required")
    assert hasattr(rec, "monthly_cost")
    assert hasattr(rec, "menu_item_coverage")
    assert hasattr(rec, "sod_conflicts")
    assert hasattr(rec, "confidence")

    # Verify types and ranges
    assert isinstance(rec.recommended_roles, list)
    assert len(rec.recommended_roles) > 0
    assert isinstance(rec.role_count, int)
    assert rec.role_count > 0
    assert isinstance(rec.license_required, str)
    assert isinstance(rec.monthly_cost, float)
    assert rec.monthly_cost > 0
    assert isinstance(rec.menu_item_coverage, float)
    assert 0.0 <= rec.menu_item_coverage <= 1.0
    assert isinstance(rec.sod_conflicts, int)
    assert rec.sod_conflicts >= 0
    assert rec.confidence in ["HIGH", "MEDIUM", "LOW"]


def test_no_menu_items_requested_edge_case(security_config_data, pricing_config):
    """Test edge case: Empty menu items list.

    Expected: Handle gracefully, return no recommendations or error.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    required_menu_items = []

    # Should either return empty or raise appropriate error
    try:
        recommendations = suggest_license_for_new_user(
            recommender=recommender,
            required_menu_items=required_menu_items,
        )
        # If it doesn't error, should be empty
        assert len(recommendations) == 0
    except ValueError:
        # Acceptable to raise an error for empty input
        pass


def test_warehouse_worker_low_cost_recommendation(security_config_data, pricing_config):
    """Test real-world scenario: Warehouse worker needs limited menu items.

    Expected: Team Members license ($60), low cost recommendation.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    # Warehouse worker needs these operations
    required_menu_items = ["InventoryReceiving", "PickListMaintenance"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    assert len(recommendations) > 0
    first_rec = recommendations[0]
    assert first_rec.license_required == "Team Members"
    assert first_rec.monthly_cost == 60.0
    assert first_rec.menu_item_coverage >= 0.5


def test_accountant_vs_ar_clerk_recommendation_options(security_config_data, pricing_config):
    """Test scenario with multiple viable role options.

    Menu items can be covered by different role combinations at different costs.
    Expected: Multiple recommendations with different costs/role counts.
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    # Menu items available in both GL Clerk (90) and Accountant (180)
    required_menu_items = ["GeneralJournalEntry", "LedgerInquiry"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    assert len(recommendations) > 0
    # First should be cheaper option
    assert recommendations[0].monthly_cost <= 180.0

    # If multiple recommendations, verify they have different characteristics
    if len(recommendations) > 1:
        # Later recommendations might have higher costs or different role counts
        assert recommendations[1].monthly_cost >= recommendations[0].monthly_cost


def test_confidence_score_consistency(security_config_data, pricing_config):
    """Test that confidence scoring is consistent with SoD status.

    HIGH confidence: sod_conflicts == 0
    MEDIUM confidence: sod_conflicts > 0
    """
    recommender = NewUserLicenseRecommender(security_config_data, pricing_config)

    required_menu_items = ["GeneralJournalEntry"]

    recommendations = suggest_license_for_new_user(
        recommender=recommender,
        required_menu_items=required_menu_items,
    )

    for rec in recommendations:
        if rec.sod_conflicts == 0:
            assert rec.confidence == "HIGH"
        elif rec.sod_conflicts > 0:
            assert rec.confidence == "MEDIUM"
