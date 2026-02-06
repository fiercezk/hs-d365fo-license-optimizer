"""Shared pricing utility for D365 FO License Agent.

Canonical implementation of license price lookup, consolidating the four
divergent _get_license_price() implementations from algorithms 2.2, 2.5,
4.1, and 4.3 into a single function with deterministic three-tier fallback.

Addresses Council code review finding H-1: identical inputs must produce
identical results regardless of which algorithm invokes the lookup.

Fallback tiers (from Algorithm 4.3, the most robust of the four):
  1. Exact case-sensitive key match
  2. Normalized key match (lowercase, spaces/hyphens to underscores)
  3. Case-insensitive iteration over all config keys

Usage:
    from src.utils.pricing import get_license_price

    price = get_license_price(pricing_config, "Finance")  # -> 180.0
    price = get_license_price(pricing_config, "Team Members")  # -> 60.0
"""

from __future__ import annotations

import re
from typing import Any


def _normalize_key(name: str) -> str:
    """Normalize a license name to lowercase with single underscores.

    Converts spaces, hyphens, and other separators to underscores,
    collapses consecutive underscores, strips whitespace, and lowercases
    the result for comparison.

    Args:
        name: Raw license name (e.g., "Team Members", "Operations - Activity").

    Returns:
        Normalized key (e.g., "team_members", "operations_activity").
    """
    result: str = name.strip().lower().replace(" ", "_").replace("-", "_")
    # Collapse consecutive underscores: "operations___activity" -> "operations_activity"
    result = re.sub(r"_+", "_", result)
    # Strip leading/trailing underscores
    result = result.strip("_")
    return result


def get_license_price(pricing_config: dict[str, Any], license_name: str) -> float:
    """Retrieve the monthly price for a license type from pricing config.

    Implements a three-tier fallback strategy to handle the various naming
    conventions across D365 FO data sources and configuration files:

      Tier 1 - Exact match: Try ``pricing_config["licenses"][license_name]``
      Tier 2 - Normalized match: Normalize both the input and each config key
               to lowercase with underscores, then compare.
      Tier 3 - Case-insensitive iteration: Iterate all config keys and compare
               lowercased versions (without underscore normalization).

    Args:
        pricing_config: Parsed pricing.json dictionary. Must contain a
            ``licenses`` key mapping license identifiers to objects with
            a ``pricePerUserPerMonth`` field.
        license_name: License type name as it appears in activity data,
            security config, or pricing config (e.g., "Finance", "SCM",
            "Team Members", "team_members", "Operations - Activity").

    Returns:
        Monthly price in USD as a float.

    Raises:
        KeyError: If the license type cannot be resolved through any
            of the three fallback tiers. The error message includes the
            input name and available config keys for debugging.
    """
    licenses: dict[str, Any] = pricing_config.get("licenses", {})
    cleaned_name: str = license_name.strip()

    if not cleaned_name:
        raise KeyError(f"License name '{license_name}' is empty or whitespace-only")

    # Tier 1: Exact case-sensitive match
    if cleaned_name in licenses:
        return float(licenses[cleaned_name]["pricePerUserPerMonth"])

    # Tier 2: Normalized match (lowercase + underscore)
    normalized_input: str = _normalize_key(cleaned_name)
    for config_key, config_data in licenses.items():
        if _normalize_key(config_key) == normalized_input:
            return float(config_data["pricePerUserPerMonth"])

    # Tier 3: Case-insensitive iteration (no underscore normalization)
    lower_input: str = cleaned_name.lower()
    for config_key, config_data in licenses.items():
        if config_key.lower() == lower_input:
            return float(config_data["pricePerUserPerMonth"])

    # No match found across all three tiers
    raise KeyError(
        f"License '{license_name}' not found in pricing config. "
        f"Available: {list(licenses.keys())}"
    )
