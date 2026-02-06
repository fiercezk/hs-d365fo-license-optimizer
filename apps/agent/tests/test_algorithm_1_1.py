"""Tests for Algorithm 1.1: Role License Composition Analyzer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until
src/algorithms/algorithm_1_1_role_composition_analyzer.py is implemented.

Specification: Requirements/06-Algorithms-Decision-Logic.md, lines 30-104.

Algorithm 1.1 analyzes security configuration data to determine, for each role,
how many menu items require each license type. It produces a composition
breakdown with counts and percentages, and identifies the highest-cost license
type in each role.

Key behaviors:
  - Count menu items per license type for a given role
  - Calculate percentages of each license type
  - Handle combined licenses (Finance + SCM counted in both)
  - Identify the highest license type (by priority/cost)
  - Handle edge cases: empty roles, roles with no menu items
  - Batch processing: analyze multiple roles at once with aggregation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.algorithms.algorithm_1_1_role_composition_analyzer import (
    RoleComposition,
    analyze_role_composition,
    analyze_roles_batch,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_security_config() -> pd.DataFrame:
    """Load the security configuration sample CSV.

    Returns:
        DataFrame with columns: securityrole, AOTName, AccessLevel,
        LicenseType, Priority, Entitled, NotEntitled, securitytype.
    """
    return pd.read_csv(FIXTURES_DIR / "security_config_sample.csv")


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON.

    Returns:
        Parsed pricing config with license costs and savings rules.
    """
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_security_config(
    rows: list[tuple[str, str, str, str, int]],
) -> pd.DataFrame:
    """Build a synthetic security configuration DataFrame.

    Args:
        rows: List of (securityrole, AOTName, AccessLevel, LicenseType, Priority)
            tuples.

    Returns:
        DataFrame matching the security_config_sample.csv schema.
    """
    records: list[dict[str, str | int | bool]] = []
    for role, aot, access, license_type, priority in rows:
        records.append(
            {
                "securityrole": role,
                "AOTName": aot,
                "AccessLevel": access,
                "LicenseType": license_type,
                "Priority": priority,
                "Entitled": 1,
                "NotEntitled": 0,
                "securitytype": "MenuItemDisplay",
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Test: Mixed License Role (80% Team Members, 20% Finance)
# ---------------------------------------------------------------------------


class TestMixedLicenseComposition:
    """Test scenario: Role with 80% Team Members items, 20% Finance items.

    A role named 'MixedRole' has 10 menu items:
    - 8 items requiring Team Members license ($60)
    - 2 items requiring Finance license ($180)

    The algorithm should:
    1. Report total_items = 10
    2. Report Team Members: count=8, percentage=80.0%
    3. Report Finance: count=2, percentage=20.0%
    4. Report all other license types as count=0, percentage=0.0%
    5. Identify highest_license = 'Finance' (highest priority at 180)
    """

    def test_mixed_role_composition(self) -> None:
        """Role with 80/20 split between Team Members and Finance."""
        # -- Arrange --
        rows: list[tuple[str, str, str, str, int]] = [
            ("MixedRole", f"ReadForm_{i}", "Read", "Team Members", 60) for i in range(8)
        ]
        rows.extend(
            [
                ("MixedRole", "GeneralJournalEntry", "Write", "Finance", 180),
                ("MixedRole", "BankReconciliation", "Write", "Finance", 180),
            ]
        )
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="MixedRole",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.role_name == "MixedRole"
        assert result.total_items == 10

        # Team Members composition
        tm_comp = result.license_composition["Team Members"]
        assert tm_comp.count == 8
        assert abs(tm_comp.percentage - 80.0) < 0.01

        # Finance composition
        fin_comp = result.license_composition["Finance"]
        assert fin_comp.count == 2
        assert abs(fin_comp.percentage - 20.0) < 0.01

        # Other license types should be zero
        for license_type in ["Commerce", "SCM", "Operations - Activity"]:
            if license_type in result.license_composition:
                assert result.license_composition[license_type].count == 0

        # Highest license should be Finance (priority 180 > 60)
        assert result.highest_license == "Finance"


# ---------------------------------------------------------------------------
# Test: Role with Multiple License Types (Show Breakdown)
# ---------------------------------------------------------------------------


class TestMultipleLicenseBreakdown:
    """Test scenario: Role spanning Finance, SCM, and Team Members.

    A role named 'CrossFunctionalRole' has 20 menu items:
    - 10 items requiring Team Members ($60, priority 60)
    - 6 items requiring Finance ($180, priority 180)
    - 4 items requiring SCM ($180, priority 180)

    The algorithm should show the full percentage breakdown and identify
    either Finance or SCM as the highest license (both priority 180;
    Finance should win by having more items, or alphabetical -- the spec
    says 'highest license type', meaning the most expensive).
    """

    def test_multiple_license_breakdown(self) -> None:
        """Role with Finance, SCM, and Team Members should show full breakdown."""
        # -- Arrange --
        rows: list[tuple[str, str, str, str, int]] = [
            ("CrossFunctionalRole", f"ReadForm_{i}", "Read", "Team Members", 60)
            for i in range(10)
        ]
        rows.extend(
            [
                ("CrossFunctionalRole", f"FinanceForm_{i}", "Write", "Finance", 180)
                for i in range(6)
            ]
        )
        rows.extend(
            [
                ("CrossFunctionalRole", f"SCMForm_{i}", "Write", "SCM", 180)
                for i in range(4)
            ]
        )
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="CrossFunctionalRole",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.role_name == "CrossFunctionalRole"
        assert result.total_items == 20

        # Team Members: 10/20 = 50%
        tm_comp = result.license_composition["Team Members"]
        assert tm_comp.count == 10
        assert abs(tm_comp.percentage - 50.0) < 0.01

        # Finance: 6/20 = 30%
        fin_comp = result.license_composition["Finance"]
        assert fin_comp.count == 6
        assert abs(fin_comp.percentage - 30.0) < 0.01

        # SCM: 4/20 = 20%
        scm_comp = result.license_composition["SCM"]
        assert scm_comp.count == 4
        assert abs(scm_comp.percentage - 20.0) < 0.01

        # Highest license should be Finance or SCM (both priority 180)
        # Since Finance has more items, it is the dominant high-priority license.
        # The spec says highest license type -- either is valid at priority 180.
        assert result.highest_license in ("Finance", "SCM")


# ---------------------------------------------------------------------------
# Test: Homogeneous Role (Single License Type)
# ---------------------------------------------------------------------------


class TestHomogeneousRole:
    """Test scenario: Role where all menu items require the same license.

    A role named 'PureFinanceRole' has 5 menu items, all requiring Finance.
    The composition should be 100% Finance.
    """

    def test_single_license_type_role(self) -> None:
        """Role with all Finance items should show 100% Finance composition."""
        # -- Arrange --
        rows: list[tuple[str, str, str, str, int]] = [
            ("PureFinanceRole", f"FinanceForm_{i}", "Write", "Finance", 180)
            for i in range(5)
        ]
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="PureFinanceRole",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.role_name == "PureFinanceRole"
        assert result.total_items == 5

        fin_comp = result.license_composition["Finance"]
        assert fin_comp.count == 5
        assert abs(fin_comp.percentage - 100.0) < 0.01

        # All other types should be zero
        for license_type in ["Team Members", "Commerce", "SCM", "Operations - Activity"]:
            if license_type in result.license_composition:
                assert result.license_composition[license_type].count == 0

        assert result.highest_license == "Finance"


# ---------------------------------------------------------------------------
# Test: Role with No Menu Items (Edge Case)
# ---------------------------------------------------------------------------


class TestRoleWithNoMenuItems:
    """Test scenario: Role that has zero menu items.

    The algorithm should handle this gracefully:
    - total_items = 0
    - All license type counts = 0
    - All percentages = 0.0
    - highest_license = 'None' or similar sentinel value
    """

    def test_empty_role_returns_zero_composition(self) -> None:
        """Role with no menu items should return all-zero composition."""
        # -- Arrange --
        # Create a security config with other roles but NOT 'EmptyRole'
        rows: list[tuple[str, str, str, str, int]] = [
            ("OtherRole", "SomeForm", "Read", "Team Members", 60),
        ]
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="EmptyRole",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.role_name == "EmptyRole"
        assert result.total_items == 0

        # All counts should be zero
        for license_type, comp in result.license_composition.items():
            assert comp.count == 0, (
                f"Expected count=0 for {license_type} in empty role, "
                f"got {comp.count}"
            )
            assert abs(comp.percentage - 0.0) < 0.01, (
                f"Expected percentage=0.0 for {license_type} in empty role, "
                f"got {comp.percentage}"
            )

        # Highest license should indicate no license needed
        assert result.highest_license == "None"


# ---------------------------------------------------------------------------
# Test: Batch Analysis -- Multiple Roles with Aggregation
# ---------------------------------------------------------------------------


class TestBatchAnalysisMultipleRoles:
    """Test scenario: Analyze multiple roles in a single batch call.

    Three roles analyzed simultaneously:
    - 'Accountant': Finance-heavy (from fixture data)
    - 'Purchasing manager': SCM-heavy (from fixture data)
    - 'Sales manager': Operations items (from fixture data)

    The batch function should return a list of RoleComposition results,
    one per role, and an optional aggregate summary.
    """

    def test_batch_analysis_returns_all_roles(self) -> None:
        """Batch analysis should return one composition per role."""
        # -- Arrange --
        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()
        role_names: list[str] = ["Accountant", "Purchasing manager", "Sales manager"]

        # -- Act --
        results: list[RoleComposition] = analyze_roles_batch(
            security_config=security_config,
            role_names=role_names,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) == 3, (
            f"Expected 3 role compositions, got {len(results)}"
        )

        result_names: set[str] = {r.role_name for r in results}
        assert result_names == set(role_names), (
            f"Expected roles {set(role_names)}, got {result_names}"
        )

        # Verify Accountant role from fixture
        accountant_result: RoleComposition | None = None
        for r in results:
            if r.role_name == "Accountant":
                accountant_result = r
                break
        assert accountant_result is not None

        # Accountant has 5 items in fixture: 2 Finance, 3 Team Members
        assert accountant_result.total_items == 5
        assert accountant_result.license_composition["Finance"].count == 2
        assert accountant_result.license_composition["Team Members"].count == 3
        assert accountant_result.highest_license == "Finance"

    def test_batch_analysis_with_nonexistent_role(self) -> None:
        """Batch should handle nonexistent roles gracefully (zero items)."""
        # -- Arrange --
        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()
        role_names: list[str] = ["Accountant", "NonexistentRole"]

        # -- Act --
        results: list[RoleComposition] = analyze_roles_batch(
            security_config=security_config,
            role_names=role_names,
            pricing_config=pricing,
        )

        # -- Assert --
        assert len(results) == 2

        nonexistent: RoleComposition | None = None
        for r in results:
            if r.role_name == "NonexistentRole":
                nonexistent = r
                break
        assert nonexistent is not None
        assert nonexistent.total_items == 0
        assert nonexistent.highest_license == "None"


# ---------------------------------------------------------------------------
# Test: Combined License Handling (Finance + SCM)
# ---------------------------------------------------------------------------


class TestCombinedLicenseHandling:
    """Test scenario: Menu item with combined 'Finance + SCM' license type.

    Per the pseudocode specification (lines 76-81), when a license type
    contains both 'Finance' AND 'SCM', the item should be counted in
    BOTH the Finance and SCM buckets.

    Setup:
    - 5 menu items total
    - 2 items with 'Finance' license
    - 1 item with 'SCM' license
    - 2 items with combined 'Finance + SCM' license

    Expected counts:
    - Finance: 2 + 2 = 4
    - SCM: 1 + 2 = 3
    - Total items: 5

    Note: Because combined items are double-counted, the sum of individual
    license counts may exceed total_items. Percentages are still calculated
    relative to total_items (the denominator is the actual item count).
    """

    def test_combined_finance_scm_double_counted(self) -> None:
        """Combined Finance+SCM items should be counted in both buckets."""
        # -- Arrange --
        rows: list[tuple[str, str, str, str, int]] = [
            ("DualRole", "FinanceForm_1", "Write", "Finance", 180),
            ("DualRole", "FinanceForm_2", "Write", "Finance", 180),
            ("DualRole", "SCMForm_1", "Write", "SCM", 180),
            ("DualRole", "CombinedForm_1", "Write", "Finance + SCM", 180),
            ("DualRole", "CombinedForm_2", "Write", "Finance + SCM", 180),
        ]
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="DualRole",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.role_name == "DualRole"
        assert result.total_items == 5

        # Finance: 2 direct + 2 combined = 4
        fin_comp = result.license_composition["Finance"]
        assert fin_comp.count == 4, (
            f"Expected Finance count=4 (2 direct + 2 combined), got {fin_comp.count}"
        )
        assert abs(fin_comp.percentage - 80.0) < 0.01  # 4/5 = 80%

        # SCM: 1 direct + 2 combined = 3
        scm_comp = result.license_composition["SCM"]
        assert scm_comp.count == 3, (
            f"Expected SCM count=3 (1 direct + 2 combined), got {scm_comp.count}"
        )
        assert abs(scm_comp.percentage - 60.0) < 0.01  # 3/5 = 60%

        # Highest should be Finance or SCM (both 180 priority)
        assert result.highest_license in ("Finance", "SCM")


# ---------------------------------------------------------------------------
# Test: Operations - Activity License Type
# ---------------------------------------------------------------------------


class TestOperationsActivityLicenseType:
    """Test scenario: Role with Operations - Activity items.

    Validates that the 'Operations - Activity' license type (priority 30)
    is correctly tracked in the composition, separate from 'Operations'
    (priority 90).
    """

    def test_operations_activity_tracked_separately(self) -> None:
        """Operations - Activity should be a separate category from Operations."""
        # -- Arrange --
        rows: list[tuple[str, str, str, str, int]] = [
            ("OpsRole", "Form_1", "Read", "Team Members", 60),
            ("OpsRole", "Form_2", "Read", "Team Members", 60),
            ("OpsRole", "Form_3", "Write", "Operations - Activity", 30),
            ("OpsRole", "Form_4", "Write", "Operations", 90),
        ]
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="OpsRole",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_items == 4

        tm_comp = result.license_composition["Team Members"]
        assert tm_comp.count == 2
        assert abs(tm_comp.percentage - 50.0) < 0.01

        ops_activity_comp = result.license_composition["Operations - Activity"]
        assert ops_activity_comp.count == 1
        assert abs(ops_activity_comp.percentage - 25.0) < 0.01

        # Operations (not Activity) is tracked separately
        # We check if the composition has an Operations entry
        ops_comp = result.license_composition.get("Operations")
        assert ops_comp is not None
        assert ops_comp.count == 1
        assert abs(ops_comp.percentage - 25.0) < 0.01

        # Highest license should be Operations (priority 90 > 60 > 30)
        assert result.highest_license == "Operations"


# ---------------------------------------------------------------------------
# Test: Algorithm ID and Metadata
# ---------------------------------------------------------------------------


class TestAlgorithmMetadata:
    """Test scenario: Verify algorithm_id and structural metadata.

    Every RoleComposition result should carry the algorithm_id '1.1'
    and contain a valid license_composition dict.
    """

    def test_algorithm_id_is_1_1(self) -> None:
        """RoleComposition.algorithm_id should be '1.1'."""
        # -- Arrange --
        rows: list[tuple[str, str, str, str, int]] = [
            ("MetaRole", "Form_1", "Read", "Team Members", 60),
        ]
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="MetaRole",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.algorithm_id == "1.1"

    def test_composition_contains_standard_license_types(self) -> None:
        """The composition should contain entries for standard license types."""
        # -- Arrange --
        rows: list[tuple[str, str, str, str, int]] = [
            ("StdRole", "Form_1", "Read", "Team Members", 60),
        ]
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="StdRole",
            pricing_config=pricing,
        )

        # -- Assert --
        expected_keys: set[str] = {
            "Commerce",
            "Finance",
            "SCM",
            "Operations - Activity",
            "Team Members",
        }
        actual_keys: set[str] = set(result.license_composition.keys())
        # Standard keys should all be present (may also have 'None' or 'Operations')
        assert expected_keys.issubset(actual_keys), (
            f"Missing standard license types: {expected_keys - actual_keys}"
        )


# ---------------------------------------------------------------------------
# Test: Real Fixture Data (security_config_sample.csv)
# ---------------------------------------------------------------------------


class TestRealFixtureData:
    """Test scenario: Verify against the checked-in security_config_sample.csv.

    The fixture has these roles and items:
    - Accountant: GeneralJournalEntry(Finance), CustomerList(TM),
      VendorList(TM), BankReconciliation(Finance), ACCOUNTANT_BR(TM)
    - Purchasing manager: PurchaseOrder(SCM), VendorList(TM), InventoryOnHand(TM)
    - Sales manager: SalesOrder(Operations), CustomerList(TM)
    - Warehouse worker: WHSMobileApp(SCM), InventoryOnHand(TM)
    """

    def test_accountant_role_from_fixture(self) -> None:
        """Accountant role from fixture should have 2 Finance, 3 Team Members."""
        # -- Arrange --
        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="Accountant",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_items == 5
        assert result.license_composition["Finance"].count == 2
        assert result.license_composition["Team Members"].count == 3
        assert abs(result.license_composition["Finance"].percentage - 40.0) < 0.01
        assert abs(result.license_composition["Team Members"].percentage - 60.0) < 0.01
        assert result.highest_license == "Finance"

    def test_purchasing_manager_from_fixture(self) -> None:
        """Purchasing manager should have 1 SCM, 2 Team Members."""
        # -- Arrange --
        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="Purchasing manager",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_items == 3
        assert result.license_composition["SCM"].count == 1
        assert result.license_composition["Team Members"].count == 2
        assert result.highest_license == "SCM"

    def test_warehouse_worker_from_fixture(self) -> None:
        """Warehouse worker should have 1 SCM, 1 Team Members."""
        # -- Arrange --
        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="Warehouse worker",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_items == 2
        assert result.license_composition["SCM"].count == 1
        assert result.license_composition["Team Members"].count == 1
        assert abs(result.license_composition["SCM"].percentage - 50.0) < 0.01
        assert abs(result.license_composition["Team Members"].percentage - 50.0) < 0.01
        assert result.highest_license == "SCM"


# ---------------------------------------------------------------------------
# Test: All Roles Discovery (No role_names filter)
# ---------------------------------------------------------------------------


class TestAllRolesDiscovery:
    """Test scenario: Batch analysis with no specific role filter.

    When role_names is None, the algorithm should discover and analyze
    ALL unique roles in the security configuration data.
    """

    def test_discover_all_roles_in_fixture(self) -> None:
        """Passing role_names=None should analyze all roles in config."""
        # -- Arrange --
        security_config: pd.DataFrame = _load_security_config()
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        results: list[RoleComposition] = analyze_roles_batch(
            security_config=security_config,
            role_names=None,
            pricing_config=pricing,
        )

        # -- Assert --
        # The fixture has 4 unique roles
        assert len(results) == 4, (
            f"Expected 4 roles from fixture, got {len(results)}"
        )
        result_names: set[str] = {r.role_name for r in results}
        expected_roles: set[str] = {
            "Accountant",
            "Purchasing manager",
            "Sales manager",
            "Warehouse worker",
        }
        assert result_names == expected_roles


# ---------------------------------------------------------------------------
# Test: Commerce License Type
# ---------------------------------------------------------------------------


class TestCommerceLicenseType:
    """Test scenario: Role containing Commerce license items.

    Ensures Commerce ($180) is properly tracked and identified as
    highest license when present.
    """

    def test_commerce_highest_license(self) -> None:
        """Role with Commerce items should identify Commerce as highest."""
        # -- Arrange --
        rows: list[tuple[str, str, str, str, int]] = [
            ("RetailRole", "POSForm_1", "Write", "Commerce", 180),
            ("RetailRole", "POSForm_2", "Write", "Commerce", 180),
            ("RetailRole", "ReadForm_1", "Read", "Team Members", 60),
        ]
        security_config: pd.DataFrame = _build_security_config(rows)
        pricing: dict[str, Any] = _load_pricing()

        # -- Act --
        result: RoleComposition = analyze_role_composition(
            security_config=security_config,
            role_name="RetailRole",
            pricing_config=pricing,
        )

        # -- Assert --
        assert result.total_items == 3
        assert result.license_composition["Commerce"].count == 2
        assert abs(result.license_composition["Commerce"].percentage - 66.67) < 0.1
        assert result.highest_license == "Commerce"
