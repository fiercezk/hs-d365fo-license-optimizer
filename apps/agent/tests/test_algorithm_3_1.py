"""Tests for Algorithm 3.1: SoD Violation Detector (TDD).

Specification: Requirements/07-Advanced-Algorithms-Expansion.md (Algorithm 3.1)
Reference: Requirements/15-Default-SoD-Conflict-Matrix.md

Test scenarios cover:
- Critical SoD violations (high fraud risk)
- High severity violations
- Medium severity violations
- No violations / clean user assignments
- Multiple violations per user
- Edge cases: inactive roles, edge date ranges
"""

import json

import pytest

from src.algorithms.algorithm_3_1_sod_violation_detector import detect_sod_violations
from src.models.input_schemas import UserRoleAssignment


@pytest.fixture
def sod_matrix_data():
    """Load the default SoD matrix from JSON.

    Returns: List of conflict rules from apps/agent/data/config/sod_matrix.json
    """
    with open("data/config/sod_matrix.json", "r") as f:
        matrix_json = json.load(f)
    return matrix_json["rules"]


@pytest.fixture
def user_roles_critical_ap_ap002():
    """User with CRITICAL SoD violation: AP-002 (AP Clerk + AP Manager).

    Risk: A user who can both enter invoices and approve them for payment
    bypasses the review control, enabling unauthorized or inflated payments.

    This is the classic "enter and approve" fraud scenario.
    """
    return [
        UserRoleAssignment(
            user_id="USER_CRITICAL_AP002_A",
            user_name="Fraud Test User",
            email="fraud@company.com",
            company="USMF",
            department="Accounts Payable",
            role_id="ROLE_AP_CLERK",
            role_name="Accounts payable clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
        UserRoleAssignment(
            user_id="USER_CRITICAL_AP002_A",
            user_name="Fraud Test User",
            email="fraud@company.com",
            company="USMF",
            department="Accounts Payable",
            role_id="ROLE_AP_MGR",
            role_name="Accounts payable manager",
            assigned_date="2023-01-01",
            status="Active",
        ),
    ]


@pytest.fixture
def user_roles_critical_gl_gl001():
    """User with CRITICAL SoD violation: GL-001 (GL Clerk + Accounting Manager).

    Risk: A user who can both create journal entries and approve them can post
    fraudulent or erroneous entries without independent review, directly impacting
    financial statements.
    """
    return [
        UserRoleAssignment(
            user_id="USER_CRITICAL_GL001_B",
            user_name="Journal Entry Approver",
            email="gl_approver@company.com",
            company="USMF",
            department="General Ledger",
            role_id="ROLE_GL_CLERK",
            role_name="General ledger clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
        UserRoleAssignment(
            user_id="USER_CRITICAL_GL001_B",
            user_name="Journal Entry Approver",
            email="gl_approver@company.com",
            company="USMF",
            department="General Ledger",
            role_id="ROLE_ACCT_MGR",
            role_name="Accounting manager",
            assigned_date="2023-01-01",
            status="Active",
        ),
    ]


@pytest.fixture
def user_roles_critical_ap001():
    """User with CRITICAL SoD violation: AP-001 (AP Clerk + Vendor Master).

    Risk: A user who can both create vendors and process invoices against those
    vendors can fabricate fictitious vendors and route payments to themselves.

    This is the classic "vendor creation and invoice processing" fraud.
    """
    return [
        UserRoleAssignment(
            user_id="USER_CRITICAL_AP001_C",
            user_name="Vendor Fraud User",
            email="vendor_fraud@company.com",
            company="USMF",
            department="Accounts Payable",
            role_id="ROLE_AP_CLERK",
            role_name="Accounts payable clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
        UserRoleAssignment(
            user_id="USER_CRITICAL_AP001_C",
            user_name="Vendor Fraud User",
            email="vendor_fraud@company.com",
            company="USMF",
            department="Accounts Payable",
            role_id="ROLE_VENDOR_MAINT",
            role_name="Vendor master maintenance",
            assigned_date="2023-01-01",
            status="Active",
        ),
    ]


@pytest.fixture
def user_roles_critical_cm001():
    """User with CRITICAL SoD violation: CM-001 (Payment Clerk + Bank Recon).

    Risk: A user who can both execute payments and reconcile bank statements can
    issue unauthorized payments and conceal them during reconciliation.
    """
    return [
        UserRoleAssignment(
            user_id="USER_CRITICAL_CM001_D",
            user_name="Cash Diversion Risk",
            email="cash_risk@company.com",
            company="USMF",
            department="Cash Management",
            role_id="ROLE_PAYMENT_CLERK",
            role_name="Payment clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
        UserRoleAssignment(
            user_id="USER_CRITICAL_CM001_D",
            user_name="Cash Diversion Risk",
            email="cash_risk@company.com",
            company="USMF",
            department="Cash Management",
            role_id="ROLE_BANK_RECON",
            role_name="Bank reconciliation clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
    ]


@pytest.fixture
def user_roles_high_severity():
    """User with HIGH severity violation: AR-002 (AR Clerk + Collections Agent).

    Risk: A user who can both generate invoices and process collections can write
    off receivables or apply payments to conceal misappropriation of customer funds.
    """
    return [
        UserRoleAssignment(
            user_id="USER_HIGH_AR002_E",
            user_name="AR Collections Risk",
            email="ar_collections@company.com",
            company="USMF",
            department="Accounts Receivable",
            role_id="ROLE_AR_CLERK",
            role_name="Accounts receivable clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
        UserRoleAssignment(
            user_id="USER_HIGH_AR002_E",
            user_name="AR Collections Risk",
            email="ar_collections@company.com",
            company="USMF",
            department="Accounts Receivable",
            role_id="ROLE_COLLECTIONS_AGENT",
            role_name="Collections agent",
            assigned_date="2023-01-01",
            status="Active",
        ),
    ]


@pytest.fixture
def user_roles_no_conflict():
    """User with NO SoD conflicts - clean assignment.

    This user has only non-conflicting roles.
    """
    return [
        UserRoleAssignment(
            user_id="USER_CLEAN_001",
            user_name="Clean User",
            email="clean@company.com",
            company="USMF",
            department="General Ledger",
            role_id="ROLE_GL_CLERK",
            role_name="General ledger clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
    ]


@pytest.fixture
def user_roles_multiple_violations():
    """User with MULTIPLE SoD violations in a single assignment.

    This user has 3 roles that create 2 conflicts:
    - AP Clerk + Vendor Master = AP-001 (CRITICAL)
    - AP Clerk + Payment Clerk = AP-004 (HIGH)

    This tests the algorithm's ability to detect all pairs.
    """
    return [
        UserRoleAssignment(
            user_id="USER_MULTIPLE_001",
            user_name="Multiple Violations User",
            email="multi_violations@company.com",
            company="USMF",
            department="Accounts Payable",
            role_id="ROLE_AP_CLERK",
            role_name="Accounts payable clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
        UserRoleAssignment(
            user_id="USER_MULTIPLE_001",
            user_name="Multiple Violations User",
            email="multi_violations@company.com",
            company="USMF",
            department="Accounts Payable",
            role_id="ROLE_VENDOR_MAINT",
            role_name="Vendor master maintenance",
            assigned_date="2023-01-01",
            status="Active",
        ),
        UserRoleAssignment(
            user_id="USER_MULTIPLE_001",
            user_name="Multiple Violations User",
            email="multi_violations@company.com",
            company="USMF",
            department="Accounts Payable",
            role_id="ROLE_PAYMENT_CLERK",
            role_name="Payment clerk",
            assigned_date="2023-01-01",
            status="Active",
        ),
    ]


class TestSODViolationDetection:
    """Test suite for SoD Violation Detector (Algorithm 3.1)."""

    def test_critical_ap002_violation(self, user_roles_critical_ap_ap002):
        """Test detection of CRITICAL AP-002 violation (AP Clerk + AP Manager).

        Expected: Exactly 1 violation detected with CRITICAL severity.
        """
        violations = detect_sod_violations(user_roles_critical_ap_ap002)

        assert len(violations) == 1
        violation = violations[0]

        assert violation.user_id == "USER_CRITICAL_AP002_A"
        assert violation.severity == "CRITICAL"
        assert violation.rule_id == "AP-002"
        assert violation.role_a == "Accounts payable clerk"
        assert violation.role_b == "Accounts payable manager"
        assert "enter invoices" in violation.risk_description.lower()
        assert "approve" in violation.risk_description.lower()

    def test_critical_gl001_violation(self, user_roles_critical_gl_gl001):
        """Test detection of CRITICAL GL-001 violation (GL Clerk + Accounting Manager).

        Expected: Exactly 1 violation detected with CRITICAL severity.
        """
        violations = detect_sod_violations(user_roles_critical_gl_gl001)

        assert len(violations) == 1
        violation = violations[0]

        assert violation.user_id == "USER_CRITICAL_GL001_B"
        assert violation.severity == "CRITICAL"
        assert violation.rule_id == "GL-001"

    def test_critical_ap001_violation(self, user_roles_critical_ap001):
        """Test detection of CRITICAL AP-001 violation (AP Clerk + Vendor Master).

        Expected: Exactly 1 violation detected with CRITICAL severity.
        """
        violations = detect_sod_violations(user_roles_critical_ap001)

        assert len(violations) == 1
        violation = violations[0]

        assert violation.user_id == "USER_CRITICAL_AP001_C"
        assert violation.severity == "CRITICAL"
        assert violation.rule_id == "AP-001"

    def test_critical_cm001_violation(self, user_roles_critical_cm001):
        """Test detection of CRITICAL CM-001 violation (Payment Clerk + Bank Recon).

        Expected: Exactly 1 violation detected with CRITICAL severity.
        """
        violations = detect_sod_violations(user_roles_critical_cm001)

        assert len(violations) == 1
        violation = violations[0]

        assert violation.user_id == "USER_CRITICAL_CM001_D"
        assert violation.severity == "CRITICAL"
        assert violation.rule_id == "CM-001"

    def test_high_severity_violation(self, user_roles_high_severity):
        """Test detection of HIGH severity violation (AR Clerk + Collections Agent).

        Expected: Exactly 1 violation detected with HIGH severity.
        """
        violations = detect_sod_violations(user_roles_high_severity)

        assert len(violations) == 1
        violation = violations[0]

        assert violation.user_id == "USER_HIGH_AR002_E"
        assert violation.severity == "HIGH"
        assert violation.rule_id == "AR-002"

    def test_no_violations_clean_assignment(self, user_roles_no_conflict):
        """Test that users with non-conflicting roles return no violations.

        Expected: Empty list of violations.
        """
        violations = detect_sod_violations(user_roles_no_conflict)

        assert len(violations) == 0

    def test_multiple_violations_same_user(self, user_roles_multiple_violations):
        """Test detection of multiple violations within a single user's role set.

        User has: AP Clerk, Vendor Master, Payment Clerk

        Expected violations:
        - AP-001: AP Clerk + Vendor Master (CRITICAL)
        - AP-004: AP Clerk + Payment Clerk (HIGH)

        Note: Vendor Master + Payment Clerk = AP-003 (CRITICAL) also
        Expected: 3 violations total
        """
        violations = detect_sod_violations(user_roles_multiple_violations)

        assert len(violations) == 3

        # Check all three conflicts are detected
        rule_ids = {v.rule_id for v in violations}
        assert "AP-001" in rule_ids
        assert "AP-003" in rule_ids
        assert "AP-004" in rule_ids

        # Check severities
        critical_violations = [v for v in violations if v.severity == "CRITICAL"]
        high_violations = [v for v in violations if v.severity == "HIGH"]

        assert len(critical_violations) == 2  # AP-001 and AP-003 are CRITICAL
        assert len(high_violations) == 1  # AP-004 is HIGH

    def test_violation_output_structure(self, user_roles_critical_ap_ap002):
        """Test that violation output has required fields.

        Validates that SODViolation object contains all required information
        for reporting and remediation.
        """
        violations = detect_sod_violations(user_roles_critical_ap_ap002)
        violation = violations[0]

        # Verify required fields exist
        assert hasattr(violation, "violation_id")
        assert violation.violation_id is not None
        assert len(violation.violation_id) > 0

        assert hasattr(violation, "user_id")
        assert hasattr(violation, "user_name")
        assert hasattr(violation, "role_a")
        assert hasattr(violation, "role_b")
        assert hasattr(violation, "severity")
        assert hasattr(violation, "rule_id")
        assert hasattr(violation, "risk_description")
        assert hasattr(violation, "conflict_type")
        assert hasattr(violation, "regulatory_reference")

    def test_violation_sorted_by_severity(
        self,
        user_roles_critical_ap_ap002,
        user_roles_high_severity,
    ):
        """Test that violations are returned sorted by severity.

        Mix CRITICAL and HIGH severity violations, verify sorting.
        """
        # Combine multiple user roles
        combined_roles = user_roles_critical_ap_ap002 + user_roles_high_severity
        violations = detect_sod_violations(combined_roles)

        # Should have both violations
        assert len(violations) == 2

        # CRITICAL should come before HIGH
        assert violations[0].severity == "CRITICAL"
        assert violations[1].severity == "HIGH"

    def test_bidirectional_rule_matching(self):
        """Test that conflicts are detected regardless of role assignment order.

        AP-001 can match (AP Clerk, Vendor Master) OR (Vendor Master, AP Clerk).
        This tests that the algorithm handles role pairs in both directions.
        """
        # First order: AP Clerk then Vendor Master
        roles_order_1 = [
            UserRoleAssignment(
                user_id="USER_ORDER_TEST_1",
                user_name="Test User",
                email="test1@company.com",
                company="USMF",
                department="AP",
                role_id="ROLE_AP_CLERK",
                role_name="Accounts payable clerk",
                assigned_date="2023-01-01",
                status="Active",
            ),
            UserRoleAssignment(
                user_id="USER_ORDER_TEST_1",
                user_name="Test User",
                email="test1@company.com",
                company="USMF",
                department="AP",
                role_id="ROLE_VENDOR_MAINT",
                role_name="Vendor master maintenance",
                assigned_date="2023-01-01",
                status="Active",
            ),
        ]

        # Opposite order: Vendor Master then AP Clerk
        roles_order_2 = [
            UserRoleAssignment(
                user_id="USER_ORDER_TEST_2",
                user_name="Test User",
                email="test2@company.com",
                company="USMF",
                department="AP",
                role_id="ROLE_VENDOR_MAINT",
                role_name="Vendor master maintenance",
                assigned_date="2023-01-01",
                status="Active",
            ),
            UserRoleAssignment(
                user_id="USER_ORDER_TEST_2",
                user_name="Test User",
                email="test2@company.com",
                company="USMF",
                department="AP",
                role_id="ROLE_AP_CLERK",
                role_name="Accounts payable clerk",
                assigned_date="2023-01-01",
                status="Active",
            ),
        ]

        violations_1 = detect_sod_violations(roles_order_1)
        violations_2 = detect_sod_violations(roles_order_2)

        # Both should detect the same violation
        assert len(violations_1) == 1
        assert len(violations_2) == 1
        assert violations_1[0].rule_id == violations_2[0].rule_id == "AP-001"

    def test_single_role_no_violations(self):
        """Test that users with only one role generate no violations.

        SoD requires at least 2 roles to have a conflict.
        """
        single_role = [
            UserRoleAssignment(
                user_id="USER_SINGLE_ROLE",
                user_name="Single Role User",
                email="single@company.com",
                company="USMF",
                department="AP",
                role_id="ROLE_AP_CLERK",
                role_name="Accounts payable clerk",
                assigned_date="2023-01-01",
                status="Active",
            ),
        ]

        violations = detect_sod_violations(single_role)

        assert len(violations) == 0

    def test_empty_user_list(self):
        """Test that empty user list returns empty violations list."""
        violations = detect_sod_violations([])

        assert len(violations) == 0
        assert isinstance(violations, list)
