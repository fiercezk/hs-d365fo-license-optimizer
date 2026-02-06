"""Tests for shared pricing utility: get_license_price().

TDD RED phase -- these tests are written BEFORE the implementation exists.
They will fail with ImportError until src/utils/pricing.py is implemented.

The shared pricing utility consolidates 4 divergent _get_license_price()
implementations (from algorithms 2.2, 2.5, 4.1, 4.3) into a single
canonical function with three-tier fallback logic:

  1. Exact case-sensitive match against pricing config keys
  2. Normalized match (lowercase, underscores) against normalized config keys
  3. Case-insensitive iteration over all config keys

This eliminates the H-1 Council finding where identical inputs produced
different results depending on which algorithm's copy ran.

Pricing config structure (from data/config/pricing.json):
  {
    "licenses": {
      "team_members": { "pricePerUserPerMonth": 60.00, ... },
      "scm": { "pricePerUserPerMonth": 180.00, ... },
      "finance": { "pricePerUserPerMonth": 180.00, ... },
      "commerce": { "pricePerUserPerMonth": 180.00, ... },
      "operations": { "pricePerUserPerMonth": 90.00, ... },
      "operations_activity": { "pricePerUserPerMonth": 30.00, ... },
      "device": { "pricePerDevicePerMonth": 80.00, ... }
    }
  }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.utils.pricing import get_license_price

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRICING_PATH: Path = Path(__file__).parents[2] / "data" / "config" / "pricing.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_pricing() -> dict[str, Any]:
    """Load the real pricing configuration JSON.

    Returns:
        Parsed pricing config with license costs.
    """
    with open(PRICING_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _minimal_pricing_config() -> dict[str, Any]:
    """Create a minimal pricing config for isolated unit tests.

    Returns:
        Pricing config with known values for deterministic testing.
    """
    return {
        "licenses": {
            "team_members": {
                "name": "Team Members",
                "pricePerUserPerMonth": 60.00,
            },
            "operations": {
                "name": "Operations",
                "pricePerUserPerMonth": 90.00,
            },
            "scm": {
                "name": "SCM",
                "pricePerUserPerMonth": 180.00,
            },
            "finance": {
                "name": "Finance",
                "pricePerUserPerMonth": 180.00,
            },
            "commerce": {
                "name": "Commerce",
                "pricePerUserPerMonth": 180.00,
            },
            "operations_activity": {
                "name": "Operations - Activity",
                "pricePerUserPerMonth": 30.00,
            },
        }
    }


# ---------------------------------------------------------------------------
# Tests: Tier 1 - Exact Match
# ---------------------------------------------------------------------------


class TestExactMatch:
    """Tier 1: Exact case-sensitive key match in pricing config."""

    def test_exact_lowercase_key(self) -> None:
        """Exact match with lowercase key 'scm' returns correct price."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "scm") == 180.00

    def test_exact_lowercase_key_finance(self) -> None:
        """Exact match with lowercase key 'finance' returns correct price."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "finance") == 180.00

    def test_exact_lowercase_key_team_members(self) -> None:
        """Exact match with underscore key 'team_members' returns correct price."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "team_members") == 60.00

    def test_exact_lowercase_key_operations(self) -> None:
        """Exact match with 'operations' returns correct price."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "operations") == 90.00


# ---------------------------------------------------------------------------
# Tests: Tier 2 - Normalized Match (lowercase + underscores)
# ---------------------------------------------------------------------------


class TestNormalizedMatch:
    """Tier 2: Match after normalizing to lowercase with underscores."""

    def test_capitalized_name_scm(self) -> None:
        """'SCM' (capitalized) should match config key 'scm'."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "SCM") == 180.00

    def test_capitalized_name_finance(self) -> None:
        """'Finance' (title case) should match config key 'finance'."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "Finance") == 180.00

    def test_capitalized_name_commerce(self) -> None:
        """'Commerce' (title case) should match config key 'commerce'."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "Commerce") == 180.00

    def test_space_separated_name(self) -> None:
        """'Team Members' (with space) should match 'team_members' (underscore)."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "Team Members") == 60.00

    def test_hyphen_separated_name(self) -> None:
        """'Operations - Activity' should match 'operations_activity'."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "Operations - Activity") == 30.00

    def test_mixed_case_with_spaces(self) -> None:
        """'TEAM MEMBERS' (all caps with space) should match 'team_members'."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "TEAM MEMBERS") == 60.00

    def test_leading_trailing_whitespace(self) -> None:
        """Whitespace around name should be stripped before matching."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "  SCM  ") == 180.00

    def test_underscore_input_matches_underscore_key(self) -> None:
        """'operations_activity' (already underscored) should match directly."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "operations_activity") == 30.00


# ---------------------------------------------------------------------------
# Tests: Tier 3 - Case-Insensitive Iteration
# ---------------------------------------------------------------------------


class TestCaseInsensitiveIteration:
    """Tier 3: Fallback to iterating all keys with case-insensitive comparison."""

    def test_partial_case_mismatch(self) -> None:
        """'Scm' (mixed case) should still resolve via iteration."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "Scm") == 180.00

    def test_all_uppercase(self) -> None:
        """'FINANCE' (all caps) should resolve via normalization or iteration."""
        config = _minimal_pricing_config()
        assert get_license_price(config, "FINANCE") == 180.00


# ---------------------------------------------------------------------------
# Tests: Error Handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Test error cases for missing or invalid license names."""

    def test_missing_license_raises_key_error(self) -> None:
        """Completely unknown license name should raise KeyError."""
        config = _minimal_pricing_config()
        with pytest.raises(KeyError, match="NonexistentLicense"):
            get_license_price(config, "NonexistentLicense")

    def test_empty_string_raises_key_error(self) -> None:
        """Empty string should raise KeyError."""
        config = _minimal_pricing_config()
        with pytest.raises(KeyError):
            get_license_price(config, "")

    def test_whitespace_only_raises_key_error(self) -> None:
        """Whitespace-only string should raise KeyError."""
        config = _minimal_pricing_config()
        with pytest.raises(KeyError):
            get_license_price(config, "   ")

    def test_empty_licenses_dict_raises_key_error(self) -> None:
        """Empty licenses dict should raise KeyError."""
        config: dict[str, Any] = {"licenses": {}}
        with pytest.raises(KeyError):
            get_license_price(config, "SCM")

    def test_missing_licenses_key_raises_key_error(self) -> None:
        """Config without 'licenses' key should raise KeyError."""
        config: dict[str, Any] = {}
        with pytest.raises(KeyError):
            get_license_price(config, "SCM")


# ---------------------------------------------------------------------------
# Tests: Return Type
# ---------------------------------------------------------------------------


class TestReturnType:
    """Verify return value is always a float."""

    def test_returns_float(self) -> None:
        """get_license_price should always return a float."""
        config = _minimal_pricing_config()
        result = get_license_price(config, "scm")
        assert isinstance(result, float)

    def test_returns_float_from_int_config(self) -> None:
        """Even if config has integer value, should return float."""
        config: dict[str, Any] = {
            "licenses": {
                "test_license": {
                    "name": "Test",
                    "pricePerUserPerMonth": 100,  # int, not float
                }
            }
        }
        result = get_license_price(config, "test_license")
        assert isinstance(result, float)
        assert result == 100.0


# ---------------------------------------------------------------------------
# Tests: Real Pricing Config Integration
# ---------------------------------------------------------------------------


class TestRealPricingConfig:
    """Integration tests using the actual pricing.json file.

    These tests validate that the shared utility works correctly with
    the real pricing configuration, matching the exact keys and values
    that the algorithms encounter in production.
    """

    def test_real_config_scm(self) -> None:
        """Real pricing.json: 'SCM' resolves to $180."""
        config = _load_pricing()
        assert get_license_price(config, "SCM") == 180.00

    def test_real_config_finance(self) -> None:
        """Real pricing.json: 'Finance' resolves to $180."""
        config = _load_pricing()
        assert get_license_price(config, "Finance") == 180.00

    def test_real_config_commerce(self) -> None:
        """Real pricing.json: 'Commerce' resolves to $180."""
        config = _load_pricing()
        assert get_license_price(config, "Commerce") == 180.00

    def test_real_config_team_members(self) -> None:
        """Real pricing.json: 'Team Members' resolves to $60."""
        config = _load_pricing()
        assert get_license_price(config, "Team Members") == 60.00

    def test_real_config_operations(self) -> None:
        """Real pricing.json: 'Operations' resolves to $90."""
        config = _load_pricing()
        assert get_license_price(config, "Operations") == 90.00

    def test_real_config_operations_activity(self) -> None:
        """Real pricing.json: 'Operations - Activity' resolves to $30."""
        config = _load_pricing()
        assert get_license_price(config, "Operations - Activity") == 30.00

    def test_real_config_all_licenses_consistent(self) -> None:
        """All license names that algorithms use should resolve to known prices.

        This is the canonical consistency check: every name variant that any
        algorithm has ever passed to _get_license_price() must produce the
        same result through the shared utility.
        """
        config = _load_pricing()

        # Names used across algorithms 2.2, 2.5, 4.1, 4.3
        expected_prices: dict[str, float] = {
            # Exact config keys (lowercase underscore)
            "scm": 180.00,
            "finance": 180.00,
            "commerce": 180.00,
            "team_members": 60.00,
            "operations": 90.00,
            "operations_activity": 30.00,
            # Capitalized variants from activity data
            "SCM": 180.00,
            "Finance": 180.00,
            "Commerce": 180.00,
            "Team Members": 60.00,
            "Operations": 90.00,
            "Operations - Activity": 30.00,
        }

        for name, expected_price in expected_prices.items():
            actual_price = get_license_price(config, name)
            assert actual_price == expected_price, (
                f"License name '{name}' returned ${actual_price}, " f"expected ${expected_price}"
            )
