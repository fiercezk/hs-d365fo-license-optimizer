"""
Tests for Algorithm 3.4: Toxic Combination Detector

Detects dangerous multi-role combinations that enable fraud beyond basic SoD violations.
See Requirements/07-Advanced-Algorithms-Expansion.md Algorithm 3.4
"""

import json
from pathlib import Path

import pytest

# Test fixtures path
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def toxic_rules():
    """Load toxic combination rules fixture."""
    with open(FIXTURES_DIR / "algo_3_4_toxic_rules.json", "r") as f:
        data = json.load(f)
    return data["rules"]


@pytest.fixture
def user_roles():
    """Load user-role assignments fixture."""
    with open(FIXTURES_DIR / "algo_3_4_user_roles.json", "r") as f:
        data = json.load(f)
    return data["users"]


def test_critical_procure_to_pay_toxic_combination(toxic_rules, user_roles):
    """
    Test Algorithm 3.4 detects CRITICAL toxic combination: Full Procure-to-Pay Control.

    Scenario:
    - User: Alice Johnson (USR001)
    - Roles: Purchasing agent + Vendor master maintenance + Accounts payable clerk
    - Expected: TOXIC-001 alert, CRITICAL severity
    - Risk: Can create vendors, place POs, approve payments (full P2P cycle)
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    # Get Alice Johnson (has all 3 roles for TOXIC-001)
    alice = next(u for u in user_roles if u["user_id"] == "USR001")

    # Run algorithm
    alerts = detect_toxic_combinations(
        user_id=alice["user_id"],
        user_name=alice["user_name"],
        user_roles=alice["roles"],
        toxic_rules=toxic_rules,
    )

    # Assertions
    assert len(alerts) == 1, f"Expected 1 toxic alert for Alice, got {len(alerts)}"

    alert = alerts[0]
    assert alert["user_id"] == "USR001"
    assert alert["user_name"] == "Alice Johnson"
    assert alert["rule_id"] == "TOXIC-001"
    assert alert["risk_type"] == "Full Procure-to-Pay Control"
    assert alert["severity"] == "CRITICAL"
    assert set(alert["matched_roles"]) == {
        "Purchasing agent",
        "Vendor master maintenance",
        "Accounts payable clerk",
    }
    assert "Create/modify vendor records" in alert["combined_privileges"]
    assert alert["recommendation"] is not None


def test_critical_order_to_cash_toxic_combination(toxic_rules, user_roles):
    """
    Test Algorithm 3.4 detects CRITICAL toxic combination: Complete Order-to-Cash Control.

    Scenario:
    - User: Bob Martinez (USR002)
    - Roles: Sales order processor + Customer master maintenance + AR clerk
    - Expected: TOXIC-002 alert, CRITICAL severity
    - Risk: Full revenue cycle control (customer → sales → invoice → cash)
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    bob = next(u for u in user_roles if u["user_id"] == "USR002")

    alerts = detect_toxic_combinations(
        user_id=bob["user_id"],
        user_name=bob["user_name"],
        user_roles=bob["roles"],
        toxic_rules=toxic_rules,
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["rule_id"] == "TOXIC-002"
    assert alert["severity"] == "CRITICAL"
    assert "revenue manipulation" in alert["risk_description"].lower()


def test_partial_match_no_alert(toxic_rules, user_roles):
    """
    Test Algorithm 3.4 does NOT alert on partial role matches.

    Scenario:
    - User: Carol Zhang (USR003)
    - Roles: Purchasing agent + Vendor master maintenance (2 of 3 for TOXIC-001)
    - Expected: NO alerts (partial match doesn't trigger)
    - Rationale: Missing "Accounts payable clerk" - cannot complete P2P cycle
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    carol = next(u for u in user_roles if u["user_id"] == "USR003")

    alerts = detect_toxic_combinations(
        user_id=carol["user_id"],
        user_name=carol["user_name"],
        user_roles=carol["roles"],
        toxic_rules=toxic_rules,
    )

    assert len(alerts) == 0, f"Expected NO alerts for partial match, got {len(alerts)}"


def test_high_severity_gl_control_toxic_combination(toxic_rules, user_roles):
    """
    Test Algorithm 3.4 detects HIGH severity toxic combination: Full GL Control.

    Scenario:
    - User: David Kim (USR004)
    - Roles: GL clerk + GL accountant + GL approver
    - Expected: TOXIC-003 alert, HIGH severity
    - Risk: Can create, post, and approve own journal entries
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    david = next(u for u in user_roles if u["user_id"] == "USR004")

    alerts = detect_toxic_combinations(
        user_id=david["user_id"],
        user_name=david["user_name"],
        user_roles=david["roles"],
        toxic_rules=toxic_rules,
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["rule_id"] == "TOXIC-003"
    assert alert["severity"] == "HIGH"
    assert "ledger" in alert["risk_type"].lower()  # "Full General Ledger Control"


def test_no_toxic_combinations_clean_user(toxic_rules, user_roles):
    """
    Test Algorithm 3.4 returns empty list for users with no toxic combinations.

    Scenario:
    - User: Frank O'Brien (USR006)
    - Roles: System administrator + IT support analyst
    - Expected: NO alerts (roles don't match any toxic pattern)
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    frank = next(u for u in user_roles if u["user_id"] == "USR006")

    alerts = detect_toxic_combinations(
        user_id=frank["user_id"],
        user_name=frank["user_name"],
        user_roles=frank["roles"],
        toxic_rules=toxic_rules,
    )

    assert len(alerts) == 0, "Expected NO alerts for clean user"


def test_user_with_extra_roles_beyond_toxic_combination(toxic_rules, user_roles):
    """
    Test Algorithm 3.4 detects toxic combination even when user has extra roles.

    Scenario:
    - User: Grace Taylor (USR007)
    - Roles: Bank rec clerk + Cash receipts clerk + Treasury analyst + GL clerk
    - Expected: TOXIC-005 alert (first 3 roles match)
    - Note: Extra role (GL clerk) doesn't prevent detection
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    grace = next(u for u in user_roles if u["user_id"] == "USR007")

    alerts = detect_toxic_combinations(
        user_id=grace["user_id"],
        user_name=grace["user_name"],
        user_roles=grace["roles"],
        toxic_rules=toxic_rules,
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["rule_id"] == "TOXIC-005"
    assert alert["severity"] == "HIGH"
    assert "cash" in alert["risk_type"].lower()


def test_multiple_users_batch_detection(toxic_rules, user_roles):
    """
    Test Algorithm 3.4 batch processing for multiple users.

    Scenario:
    - Process all 7 users in fixture
    - Expected:
      - 5 users with toxic combinations (USR001, USR002, USR004, USR005, USR007)
      - 2 users clean (USR003 partial match, USR006 no match)
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    all_alerts = []
    for user in user_roles:
        alerts = detect_toxic_combinations(
            user_id=user["user_id"],
            user_name=user["user_name"],
            user_roles=user["roles"],
            toxic_rules=toxic_rules,
        )
        all_alerts.extend(alerts)

    # Should have exactly 5 toxic alerts total
    assert len(all_alerts) == 5, f"Expected 5 total alerts, got {len(all_alerts)}"

    # Verify alert distribution by severity
    critical_alerts = [a for a in all_alerts if a["severity"] == "CRITICAL"]
    high_alerts = [a for a in all_alerts if a["severity"] == "HIGH"]

    assert len(critical_alerts) == 2  # USR001 (P2P), USR002 (O2C)
    assert len(high_alerts) == 3  # USR004 (GL), USR005 (Inventory), USR007 (Cash)


def test_disabled_rule_not_detected(toxic_rules, user_roles):
    """
    Test Algorithm 3.4 skips disabled rules.

    Scenario:
    - Disable TOXIC-001 rule
    - User: Alice Johnson (has Procure-to-Pay combination)
    - Expected: NO alert (rule is disabled)
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    # Disable TOXIC-001
    disabled_rules = [r for r in toxic_rules if r["rule_id"] != "TOXIC-001"]

    alice = next(u for u in user_roles if u["user_id"] == "USR001")

    alerts = detect_toxic_combinations(
        user_id=alice["user_id"],
        user_name=alice["user_name"],
        user_roles=alice["roles"],
        toxic_rules=disabled_rules,  # Missing TOXIC-001
    )

    assert len(alerts) == 0, "Expected NO alerts when rule is disabled"


def test_empty_user_roles_returns_empty_list(toxic_rules):
    """
    Test Algorithm 3.4 handles users with no roles assigned.

    Scenario:
    - User with empty roles list
    - Expected: NO alerts (no roles to match)
    """
    from src.algorithms.algorithm_3_4_toxic_combination_detector import (
        detect_toxic_combinations,
    )

    alerts = detect_toxic_combinations(
        user_id="USR999",
        user_name="No Roles User",
        user_roles=[],
        toxic_rules=toxic_rules,
    )

    assert len(alerts) == 0, "Expected NO alerts for user with no roles"
