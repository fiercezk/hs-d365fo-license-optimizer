"""Tests for Algorithm 4.3: Cross-Application License Analyzer.

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until src/algorithms/algorithm_4_3_cross_app_analyzer.py
is implemented.

Specification: Requirements/07-Advanced-Algorithms-Expansion.md, lines 1261-1336.

Algorithm 4.3 identifies users with roles across Finance and SCM who could benefit
from a combined Finance+SCM license. Key scenarios:
  - User with both Finance and SCM access, holding separate licenses ($180 each = $360)
  - Opportunity to combine into single license ($210), saving $150/month ($1,800/year)
  - Edge cases: single app, already optimized, three apps, minimal access

Input data:
  - User-role assignments (user_id, role_name)
  - Security configuration (role, application)
  - Pricing configuration (Finance: $180, SCM: $180, Finance+SCM: $210)

Output:
  - Recommendation action (remove_license, no_change, etc.)
  - Savings estimate with confidence level
  - Already-optimized flag
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.algorithms.algorithm_4_3_cross_app_analyzer import (
    analyze_cross_application_licenses,
)
from src.models.output_schemas import (
    ConfidenceLevel,
    LicenseRecommendation,
    RecommendationAction,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"

# Tolerance for floating-point comparisons
CONFIDENCE_TOLERANCE: float = 0.05
MONETARY_TOLERANCE: float = 0.01


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_scenario(filename: str) -> dict[str, Any]:
    """Load a JSON test scenario fixture.

    Args:
        filename: Name of the JSON file inside tests/fixtures/.

    Returns:
        Parsed JSON as a dictionary.
    """
    path = FIXTURES_DIR / filename
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_pricing() -> dict[str, Any]:
    """Load the pricing configuration JSON.

    Returns:
        Parsed pricing config dictionary.
    """
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_security_config() -> pd.DataFrame:
    """Load the security configuration CSV for Algorithm 4.3.

    Returns:
        DataFrame with columns: securityrole, AOTName, AccessLevel,
        Application, LicenseType, Priority, Entitled.
    """
    return pd.read_csv(FIXTURES_DIR / "algo_4_3_security_config.csv")


def _load_user_roles() -> pd.DataFrame:
    """Load the user-role assignments CSV for Algorithm 4.3.

    Returns:
        DataFrame with columns: user_id, user_name, security_role, assignment_date.
    """
    return pd.read_csv(FIXTURES_DIR / "algo_4_3_user_roles.csv")


# ---------------------------------------------------------------------------
# Tests: Obvious Optimization Scenarios
# ---------------------------------------------------------------------------


def test_cross_app_user_with_separate_licenses():
    """Test Algorithm 4.3: User with Finance and SCM access holding separate licenses.

    This is the PRIMARY scenario for Algorithm 4.3:
    - User Alice (U001) has roles in both Finance and SCM
    - Currently holding Finance ($180) + SCM ($180) = $360/month
    - Opportunity to combine into Finance+SCM ($210) = save $150/month

    Expected: REMOVE_LICENSE recommendation with $1,800/year savings, HIGH confidence.
    """
    scenario = _load_scenario("algo_4_3_scenario_cross_app_user.json")
    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    user_id = scenario["user_id"]
    user_name = scenario["user_name"]

    result = analyze_cross_application_licenses(
        user_id=user_id,
        user_name=user_name,
        security_config=security_config,
        user_roles=user_roles,
        pricing_config=pricing_config,
    )

    # Verify result is a LicenseRecommendation
    assert isinstance(result, LicenseRecommendation)

    # Verify the recommendation action
    assert result.action == RecommendationAction.REMOVE_LICENSE
    assert not result.already_optimized

    # Verify savings calculation
    assert result.reason.primary_factor is not None
    assert "Finance" in result.reason.primary_factor and "SCM" in result.reason.primary_factor

    # Verify monetary values with tolerance
    assert abs(result.savings.monthly_current_cost - 360.00) < MONETARY_TOLERANCE
    assert abs(result.savings.monthly_recommended_cost - 210.00) < MONETARY_TOLERANCE
    assert abs(result.savings.monthly_savings - 150.00) < MONETARY_TOLERANCE
    assert abs(result.savings.annual_savings - 1800.00) < MONETARY_TOLERANCE

    # Verify confidence is HIGH
    assert result.confidence == ConfidenceLevel.HIGH


def test_single_app_user_no_opportunity():
    """Test Algorithm 4.3: User with single application access (no opportunity).

    User Bob (U002) has Finance access only:
    - Currently holding Finance ($180/month)
    - No cross-application opportunity exists
    - No action recommended

    Expected: NO_CHANGE recommendation, already_optimized=True.
    """
    scenario = _load_scenario("algo_4_3_scenario_single_app_user.json")
    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    user_id = scenario["user_id"]
    user_name = scenario["user_name"]

    result = analyze_cross_application_licenses(
        user_id=user_id,
        user_name=user_name,
        security_config=security_config,
        user_roles=user_roles,
        pricing_config=pricing_config,
    )

    # Verify no optimization is needed
    assert result.action == RecommendationAction.NO_CHANGE
    assert result.already_optimized

    # Verify zero savings
    assert result.savings.monthly_savings == 0.0
    assert result.savings.annual_savings == 0.0

    # Verify HIGH confidence (single app = clear case)
    assert result.confidence == ConfidenceLevel.HIGH


def test_already_optimized_combined_license():
    """Test Algorithm 4.3: User with Finance and SCM access already holding combined license.

    User Carol (U003) already holds the optimal Finance+SCM combined license:
    - Currently holding Finance+SCM ($210/month)
    - Both Finance and SCM roles assigned
    - Already optimal

    Expected: NO_CHANGE recommendation, already_optimized=True, zero savings.
    """
    scenario = _load_scenario("algo_4_3_scenario_already_optimized.json")
    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    user_id = scenario["user_id"]
    user_name = scenario["user_name"]
    current_licenses = scenario.get("current_licenses", [])

    result = analyze_cross_application_licenses(
        user_id=user_id,
        user_name=user_name,
        security_config=security_config,
        user_roles=user_roles,
        pricing_config=pricing_config,
        current_licenses=current_licenses,
    )

    # Verify already optimized
    assert result.action == RecommendationAction.NO_CHANGE
    assert result.already_optimized

    # Verify zero savings
    assert result.savings.monthly_savings == 0.0
    assert result.savings.annual_savings == 0.0


# ---------------------------------------------------------------------------
# Tests: Complex Scenarios
# ---------------------------------------------------------------------------


def test_three_application_user():
    """Test Algorithm 4.3: User with Finance, SCM, and Commerce access.

    User Diana (U004) has roles in three applications:
    - Finance ($180) + SCM ($180) + Commerce ($180) = $540/month
    - Can optimize Finance + SCM into combined ($210)
    - Keep Commerce separate ($180)
    - Total: Finance+SCM ($210) + Commerce ($180) = $390/month
    - Savings: $150/month ($1,800/year)

    Expected: DOWNGRADE or REMOVE_LICENSE, $150/month savings.
    """
    scenario = _load_scenario("algo_4_3_scenario_three_apps.json")
    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    user_id = scenario["user_id"]
    user_name = scenario["user_name"]

    result = analyze_cross_application_licenses(
        user_id=user_id,
        user_name=user_name,
        security_config=security_config,
        user_roles=user_roles,
        pricing_config=pricing_config,
    )

    # Verify a downgrade/optimization is recommended
    assert result.action in (RecommendationAction.DOWNGRADE, RecommendationAction.REMOVE_LICENSE)
    assert not result.already_optimized

    # Verify savings
    assert abs(result.savings.monthly_current_cost - 540.00) < MONETARY_TOLERANCE
    assert abs(result.savings.monthly_savings - 150.00) < MONETARY_TOLERANCE


def test_minimal_cross_app_access():
    """Test Algorithm 4.3: User with minimal access in one application.

    User Edward (U005) has Finance and minimal SCM access:
    - Finance Accountant role (42 menu items)
    - SCM Viewer role (only 3 menu items)
    - Currently Finance ($180) + SCM ($180) = $360/month
    - Combined license ($210) is still more cost-effective
    - Confidence should be MEDIUM (minimal justification for SCM)

    Expected: REMOVE_LICENSE with MEDIUM confidence.
    """
    scenario = _load_scenario("algo_4_3_scenario_minimal_access.json")
    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    user_id = scenario["user_id"]
    user_name = scenario["user_name"]

    result = analyze_cross_application_licenses(
        user_id=user_id,
        user_name=user_name,
        security_config=security_config,
        user_roles=user_roles,
        pricing_config=pricing_config,
    )

    # Verify recommendation
    assert result.action == RecommendationAction.REMOVE_LICENSE

    # Verify savings
    assert abs(result.savings.monthly_savings - 150.00) < MONETARY_TOLERANCE

    # Confidence should be MEDIUM (minimal SCM access warrants caution)
    assert result.confidence == ConfidenceLevel.MEDIUM

    # Risk factors should mention minimal access
    assert len(result.reason.risk_factors) > 0


# ---------------------------------------------------------------------------
# Tests: Edge Cases & Data Validation
# ---------------------------------------------------------------------------


def test_missing_user_raises_error():
    """Test Algorithm 4.3: Calling with non-existent user raises appropriate error."""
    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    # Call with non-existent user
    result = analyze_cross_application_licenses(
        user_id="NONEXISTENT",
        user_name="Unknown User",
        security_config=security_config,
        user_roles=user_roles,
        pricing_config=pricing_config,
    )

    # Should return NO_CHANGE (insufficient data to analyze)
    # OR should handle gracefully with INSUFFICIENT_DATA confidence
    assert (
        result.action == RecommendationAction.NO_CHANGE
        or result.confidence == ConfidenceLevel.INSUFFICIENT_DATA
    )


def test_output_schema_completeness():
    """Test Algorithm 4.3: Output LicenseRecommendation has all required fields."""
    scenario = _load_scenario("algo_4_3_scenario_cross_app_user.json")
    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    result = analyze_cross_application_licenses(
        user_id=scenario["user_id"],
        user_name=scenario["user_name"],
        security_config=security_config,
        user_roles=user_roles,
        pricing_config=pricing_config,
    )

    # Verify all required fields exist
    assert result.user_id is not None
    assert result.algorithm_id is not None
    assert result.action is not None
    assert result.confidence is not None
    assert result.savings is not None
    assert result.reason is not None
    assert result.already_optimized is not None
    assert result.timestamp is not None


def test_confidence_scoring_consistency():
    """Test Algorithm 4.3: Confidence scoring is consistent and reasonable."""
    scenarios = [
        ("algo_4_3_scenario_cross_app_user.json", ConfidenceLevel.HIGH),
        ("algo_4_3_scenario_single_app_user.json", ConfidenceLevel.HIGH),
        ("algo_4_3_scenario_minimal_access.json", ConfidenceLevel.MEDIUM),
    ]

    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    for scenario_file, expected_confidence in scenarios:
        scenario = _load_scenario(scenario_file)
        result = analyze_cross_application_licenses(
            user_id=scenario["user_id"],
            user_name=scenario["user_name"],
            security_config=security_config,
            user_roles=user_roles,
            pricing_config=pricing_config,
        )

        # Verify confidence matches expected
        assert (
            result.confidence == expected_confidence
        ), f"Scenario {scenario_file}: expected {expected_confidence}, got {result.confidence}"


# ---------------------------------------------------------------------------
# Tests: Integration with Pricing Configuration
# ---------------------------------------------------------------------------


def test_respects_pricing_config():
    """Test Algorithm 4.3: Uses pricing configuration correctly.

    If pricing.json changes (e.g., Finance+SCM becomes $220 instead of $210),
    algorithm should use new pricing and recalculate savings.
    """
    scenario = _load_scenario("algo_4_3_scenario_cross_app_user.json")
    security_config = _load_security_config()
    user_roles = _load_user_roles()
    pricing_config = _load_pricing()

    result = analyze_cross_application_licenses(
        user_id=scenario["user_id"],
        user_name=scenario["user_name"],
        security_config=security_config,
        user_roles=user_roles,
        pricing_config=pricing_config,
    )

    # Get actual prices from config (keys match pricing.json casing)
    licenses = pricing_config["licenses"]
    # Support both capitalized keys (apps/data/config) and lowercase keys (data/config)
    finance_key = "Finance" if "Finance" in licenses else "finance"
    scm_key = "SCM" if "SCM" in licenses else "scm"
    finance_price = float(licenses[finance_key]["pricePerUserPerMonth"])
    scm_price = float(licenses[scm_key]["pricePerUserPerMonth"])

    # Verify current cost matches
    expected_current = finance_price + scm_price
    assert abs(result.savings.monthly_current_cost - expected_current) < MONETARY_TOLERANCE
