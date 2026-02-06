# Default SoD Conflict Matrix

**Project**: D365 FO License & Security Optimization Agent
**Last Updated**: 2026-02-06
**Status**: Requirements Definition
**Version**: 1.0
**Category**: Security & Compliance
**Related Algorithm**: 3.1 (SoD Violation Detector)

---

## Table of Contents

1. [Purpose](#purpose)
2. [How This Matrix Is Used](#how-this-matrix-is-used)
3. [Conflict Categories](#conflict-categories)
   - [Category 1: Accounts Payable](#category-1-accounts-payable-ap-001-through-ap-005)
   - [Category 2: Accounts Receivable](#category-2-accounts-receivable-ar-001-through-ar-004)
   - [Category 3: General Ledger](#category-3-general-ledger-gl-001-through-gl-004)
   - [Category 4: Procurement](#category-4-procurement-pr-001-through-pr-004)
   - [Category 5: Inventory & Warehouse](#category-5-inventory--warehouse-inv-001-through-inv-003)
   - [Category 6: Cash Management](#category-6-cash-management-cm-001-through-cm-003)
   - [Category 7: System Administration](#category-7-system-administration-sa-001-through-sa-004)
4. [Severity Rating Guide](#severity-rating-guide)
5. [Customization Guide](#customization-guide)
6. [Mapping to D365 FO Standard Security Roles](#mapping-to-d365-fo-standard-security-roles)
7. [Sources & References](#sources--references)
8. [Document Status](#document-status)

---

## Purpose

This document provides the **default baseline conflict matrix** for Algorithm 3.1 (SoD Violation Detector), based on SOX Section 404 requirements and Big 4 audit frameworks. The matrix defines industry-standard Separation of Duties (SoD) conflict rules mapped to D365 Finance & Operations standard security roles.

Separation of Duties is a fundamental internal control principle that prevents a single individual from controlling all phases of a transaction. When one user can both initiate and approve, both create and pay, or both record and reconcile, the organization faces elevated fraud risk and regulatory exposure.

This matrix serves as the **out-of-the-box default** that Algorithm 3.1 uses for conflict detection. Organizations should review and customize this matrix to match their specific control environment, risk appetite, and organizational structure. The rules defined here represent the **minimum recommended baseline** for SOX-compliant organizations.

**Total Default Rules**: 27 rules across 7 categories

---

## How This Matrix Is Used

### Loading and Execution

- Algorithm 3.1 loads these rules as the **default conflict detection baseline** on first deployment
- Each rule defines two conflicting duties (expressed as D365 FO security roles) that should not be assigned to the same user
- The algorithm iterates through all user-role assignments and checks every role pair against this matrix
- When a conflict is detected, the algorithm generates a violation record with severity, risk description, and regulatory reference

### Administration

- Administrators can **add** custom conflict rules via the web application to address organization-specific risks
- Administrators can **modify** existing rules (change severity, update descriptions) when compensating controls exist
- Administrators can **disable** rules that do not apply to their organizational structure (e.g., small organizations where some role overlap is unavoidable)
- Administrators can create entirely **custom rules** for non-standard roles or organizational-specific duties
- Severity ratings drive **alert priority** and **reporting urgency** within the dashboard

### Audit Trail

- All rule changes (add, modify, disable, delete) are **audit-logged** for compliance purposes
- The audit log captures: who made the change, when, what was changed, and the justification provided
- Auditors can review the full rule change history to assess the control environment
- Disabled rules remain in the system with a disabled flag and reason for disablement

### Conflict Detection Flow

```
Algorithm 3.1 Startup:
  1. Load default SoD matrix (this document)
  2. Load any custom/modified rules from database
  3. Merge rules (custom overrides default where Rule IDs match)
  4. For each user:
     a. Get all assigned roles
     b. For each role pair, check against merged matrix
     c. If conflict found, generate violation record
     d. Score severity based on rule severity + activity data
  5. Output sorted violation report
```

---

## Conflict Categories

### Category 1: Accounts Payable (AP-001 through AP-005)

Accounts Payable conflicts represent the highest fraud risk area in most organizations. The ability to create vendors, process invoices, and authorize payments must be segregated to prevent fictitious vendor schemes, invoice fraud, and unauthorized disbursements.

| Rule ID | Role A | Role B | Conflict Type | Risk Description | Severity | Regulatory Reference |
|---------|--------|--------|---------------|------------------|----------|---------------------|
| **AP-001** | Accounts payable clerk | Vendor master maintenance | Process vs. Create | A user who can both create vendors and process invoices against those vendors can fabricate fictitious vendors and route payments to themselves. | **Critical** | SOX 404, COSO Principle 10 |
| **AP-002** | Accounts payable clerk | Accounts payable manager | Process vs. Approve | A user who can both enter invoices and approve them for payment bypasses the review control, enabling unauthorized or inflated payments. | **Critical** | SOX 404, COSO Principle 12 |
| **AP-003** | Vendor master maintenance | Payment clerk | Create vs. Pay | A user who can both create vendor records and execute payment runs can establish shell vendors and disburse funds without independent verification. | **Critical** | SOX 404, COSO Principle 10 |
| **AP-004** | Accounts payable clerk | Payment clerk | Record vs. Pay | A user who can both record liabilities and execute payments can manipulate invoice amounts and immediately release funds without segregated review. | **High** | SOX 404, COSO Principle 13 |
| **AP-005** | Purchasing agent | Accounts payable manager | Procure vs. Approve Payment | A user who can both create purchase orders and approve the resulting invoices for payment can authorize procurement and payment without independent oversight. | **High** | SOX 404, COSO Principle 10 |

---

### Category 2: Accounts Receivable (AR-001 through AR-004)

Accounts Receivable conflicts create risk around revenue manipulation, unauthorized credit issuance, and misappropriation of incoming cash. Segregation between customer management, billing, collections, and cash application is essential.

| Rule ID | Role A | Role B | Conflict Type | Risk Description | Severity | Regulatory Reference |
|---------|--------|--------|---------------|------------------|----------|---------------------|
| **AR-001** | Customer master maintenance | Accounts receivable clerk | Create vs. Invoice | A user who can both create customer records and generate invoices can fabricate fictitious sales transactions to manipulate revenue figures. | **Critical** | SOX 404, COSO Principle 10 |
| **AR-002** | Accounts receivable clerk | Collections agent | Invoice vs. Collect | A user who can both generate invoices and process collections can write off receivables or apply payments to conceal misappropriation of customer funds. | **High** | SOX 404, COSO Principle 13 |
| **AR-003** | Customer master maintenance | Collections agent | Create vs. Write-Off | A user who can both maintain customer master data and execute collections activities can modify credit terms, write off balances, or redirect payments. | **High** | SOX 404, COSO Principle 10 |
| **AR-004** | Billing clerk | Accounts receivable clerk | Bill vs. Record | A user who can both generate billing documents and record receivable transactions can manipulate billing amounts and conceal discrepancies in the ledger. | **Medium** | COSO Principle 13, ISACA COBIT DSS05 |

---

### Category 3: General Ledger (GL-001 through GL-004)

General Ledger conflicts pose direct risk to financial statement integrity. The ability to create, post, approve, and reconcile journal entries must be segregated. GL controls are the most scrutinized area during SOX audits.

| Rule ID | Role A | Role B | Conflict Type | Risk Description | Severity | Regulatory Reference |
|---------|--------|--------|---------------|------------------|----------|---------------------|
| **GL-001** | General ledger clerk | Accounting manager | Create vs. Approve | A user who can both create journal entries and approve them can post fraudulent or erroneous entries without independent review, directly impacting financial statements. | **Critical** | SOX 404, COSO Principle 8 |
| **GL-002** | General ledger clerk | Accounting supervisor | Record vs. Post | A user who can both record journal entries and post them to the ledger bypasses the segregation between preparation and authorization of financial transactions. | **Critical** | SOX 404, COSO Principle 10 |
| **GL-003** | Accounting supervisor | Financial controller | Post vs. Close | A user who can both post journal entries and execute period-close procedures can manipulate closing entries and adjust financial results without independent oversight. | **High** | SOX 404, COSO Principle 13 |
| **GL-004** | General ledger clerk | Financial controller | Record vs. Reconcile | A user who can both record transactions and perform reconciliation can conceal errors or fraud by adjusting both the source entries and the reconciliation. | **High** | SOX 404, COSO Principle 16 |

---

### Category 4: Procurement (PR-001 through PR-004)

Procurement conflicts enable purchase fraud, kickback schemes, and unauthorized commitments. Segregation between requesting, ordering, approving, receiving, and vendor management prevents a single individual from controlling the procure-to-pay cycle.

| Rule ID | Role A | Role B | Conflict Type | Risk Description | Severity | Regulatory Reference |
|---------|--------|--------|---------------|------------------|----------|---------------------|
| **PR-001** | Purchasing agent | Purchasing manager | Create PO vs. Approve PO | A user who can both create purchase orders and approve them bypasses authorization controls, enabling unauthorized procurement commitments. | **Critical** | SOX 404, COSO Principle 12 |
| **PR-002** | Requisitioner | Purchasing manager | Request vs. Approve | A user who can both create purchase requisitions and approve purchase orders can self-authorize procurement without independent budget or need verification. | **High** | SOX 404, COSO Principle 10 |
| **PR-003** | Purchasing agent | Receiving clerk | Order vs. Receive | A user who can both place purchase orders and confirm goods receipt can fabricate receiving records for goods never delivered, enabling payment fraud. | **High** | SOX 404, COSO Principle 10 |
| **PR-004** | Purchasing agent | Vendor master maintenance | Order vs. Create Vendor | A user who can both create vendors and issue purchase orders can establish fictitious vendors and route procurement through them for personal benefit. | **Critical** | SOX 404, COSO Principle 10 |

---

### Category 5: Inventory & Warehouse (INV-001 through INV-003)

Inventory conflicts create risk around asset misappropriation, fictitious inventory records, and manipulation of cost of goods sold. Physical custody of inventory must be segregated from record-keeping and counting functions.

| Rule ID | Role A | Role B | Conflict Type | Risk Description | Severity | Regulatory Reference |
|---------|--------|--------|---------------|------------------|----------|---------------------|
| **INV-001** | Warehouse manager | Inventory clerk | Custody vs. Record | A user who has physical custody of inventory and can also adjust inventory records can conceal theft by manipulating quantities in the system. | **Critical** | SOX 404, COSO Principle 11 |
| **INV-002** | Warehouse worker | Inventory clerk | Move vs. Count | A user who can both move inventory within the warehouse and perform inventory counts can manipulate count results to conceal missing or misplaced stock. | **High** | COSO Principle 11, ISACA COBIT DSS05 |
| **INV-003** | Shipping clerk | Receiving clerk | Ship vs. Receive | A user who can both ship and receive goods can divert outbound shipments, record fictitious receipts, or manipulate transfer records between locations. | **Medium** | COSO Principle 10, SOX 404 |

---

### Category 6: Cash Management (CM-001 through CM-003)

Cash Management conflicts represent direct access to liquid assets. The segregation of payment execution, bank reconciliation, and cash management oversight is a fundamental control in every SOX-compliant organization.

| Rule ID | Role A | Role B | Conflict Type | Risk Description | Severity | Regulatory Reference |
|---------|--------|--------|---------------|------------------|----------|---------------------|
| **CM-001** | Payment clerk | Bank reconciliation clerk | Pay vs. Reconcile | A user who can both execute payments and reconcile bank statements can issue unauthorized payments and conceal them during the reconciliation process. | **Critical** | SOX 404, COSO Principle 10 |
| **CM-002** | Treasurer | Payment clerk | Authorize vs. Execute | A user who can both authorize payment parameters (bank accounts, payment methods) and execute payment runs can redirect funds to unauthorized accounts. | **Critical** | SOX 404, COSO Principle 12 |
| **CM-003** | Treasurer | Bank reconciliation clerk | Manage vs. Reconcile | A user who can both manage cash positions and bank relationships and also reconcile bank statements can manipulate cash reporting and conceal discrepancies. | **High** | SOX 404, COSO Principle 16 |

---

### Category 7: System Administration (SA-001 through SA-004)

System Administration conflicts address the risk of unauthorized access provisioning and configuration manipulation. IT controls are a critical component of the SOX control environment, as system-level access can bypass all application-level controls.

| Rule ID | Role A | Role B | Conflict Type | Risk Description | Severity | Regulatory Reference |
|---------|--------|--------|---------------|------------------|----------|---------------------|
| **SA-001** | System administrator | Security administrator | Configure vs. Provision | A user who can both configure system settings and assign security roles can grant themselves elevated access and modify system behavior to conceal unauthorized actions. | **Critical** | SOX 404 (ITGC), ISACA COBIT DSS05 |
| **SA-002** | Security administrator | Accounts payable manager | Provision vs. Operate | A user who can assign security roles and also perform financial operations can grant themselves conflicting access and execute transactions without oversight. | **Critical** | SOX 404 (ITGC), COSO Principle 12 |
| **SA-003** | IT manager | Financial controller | IT Control vs. Business Control | A user with both IT management authority and financial controller duties can manipulate system configurations to bypass financial controls and alter financial data. | **High** | SOX 404 (ITGC), COSO Principle 11 |
| **SA-004** | System administrator | General ledger clerk | Admin vs. Transact | A user who has system administration privileges and also performs financial transactions can modify application behavior, override controls, and manipulate transaction records. | **High** | SOX 404 (ITGC), ISACA COBIT DSS05 |

---

## Conflict Rule Summary

| Category | Rule Count | Critical | High | Medium |
|----------|-----------|----------|------|--------|
| Accounts Payable | 5 | 3 | 2 | 0 |
| Accounts Receivable | 4 | 1 | 2 | 1 |
| General Ledger | 4 | 2 | 2 | 0 |
| Procurement | 4 | 2 | 2 | 0 |
| Inventory & Warehouse | 3 | 1 | 1 | 1 |
| Cash Management | 3 | 2 | 1 | 0 |
| System Administration | 4 | 2 | 2 | 0 |
| **Total** | **27** | **13** | **12** | **2** |

---

## Severity Rating Guide

| Severity | Description | Action Required | SLA |
|----------|------------|-----------------|-----|
| **Critical** | Direct fraud risk or SOX material weakness. The conflict enables a single user to execute and conceal a fraudulent transaction end-to-end. Auditors will flag this as a material finding. | Immediate remediation required. Escalate to CISO and CFO. Remove conflicting role assignment or implement documented compensating control with management sign-off. | **24 hours** |
| **High** | Significant control weakness that would result in an audit finding. The conflict creates elevated risk but may require additional steps to exploit. Auditors will flag this as a significant deficiency. | Remediation within 1 week. Security officer must review and approve any exception. Compensating controls must be documented and tested. | **7 days** |
| **Medium** | Control improvement opportunity. The conflict represents a deviation from best practice but carries lower inherent risk. Auditors may note this as an observation or recommendation. | Remediation within 1 month. Document risk acceptance if exception is granted. Review during next access certification cycle. | **30 days** |

### Severity Scoring Factors

Algorithm 3.1 adjusts the base severity from this matrix using the following factors:

1. **Activity Factor**: If both conflicting roles are actively used (last 90 days), severity increases. If one or both roles are inactive, severity may decrease.
2. **Transaction Volume Factor**: High transaction volume in both roles increases the risk exposure and may escalate severity.
3. **Compensating Control Factor**: Documented compensating controls (e.g., dual-approval workflows, periodic reconciliation reviews) can reduce effective severity.
4. **User Position Factor**: Users in management or privileged positions may have elevated scoring due to broader system access.

---

## Customization Guide

### Adding Custom Conflict Rules

Administrators can create organization-specific conflict rules through the web application. Custom rules follow the same structure as default rules and participate in the same detection pipeline.

**Required fields for a custom rule:**
- **Rule ID**: Auto-generated with prefix `CUSTOM-` (e.g., `CUSTOM-001`)
- **Role A**: Select from D365 FO role list or enter a custom role name
- **Role B**: Select from D365 FO role list or enter a custom role name
- **Conflict Type**: Brief description of the conflicting duties (e.g., "Approve vs. Execute")
- **Risk Description**: One sentence explaining the fraud or control risk
- **Severity**: Critical, High, or Medium
- **Regulatory Reference**: Applicable standard or "Organization Policy"
- **Justification**: Why this rule is needed (mandatory for audit trail)

### Disabling Rules

Not all default rules apply to every organization. Administrators can disable rules with proper documentation:

1. Navigate to the SoD Configuration page in the web application
2. Select the rule to disable
3. Provide a **mandatory justification** (e.g., "Organization has fewer than 50 users; AP clerk and vendor maintenance are performed by the same team with compensating monthly review")
4. Specify the **compensating control** in place, if any
5. Set a **review date** for periodic reassessment (recommended: quarterly)
6. The disabled rule remains visible in the matrix with a `DISABLED` status

**Important**: Disabling a Critical severity rule requires approval from the Security Officer or designated compliance authority. The approval is captured in the audit log.

### Modifying Severity

When compensating controls exist, administrators can reduce the effective severity of a rule:

| Original Severity | Compensating Control Example | Reduced Severity |
|-------------------|------------------------------|------------------|
| **Critical** | Dual-approval workflow enforced at system level for all payments above a threshold | **High** |
| **Critical** | Monthly reconciliation review by independent party with documented sign-off | **High** |
| **High** | Automated monitoring alerts with 24-hour review SLA by compliance team | **Medium** |
| **High** | Quarterly access review with management certification and exception reporting | **Medium** |

**Requirements for severity reduction:**
- The compensating control must be **documented** with a description, owner, and frequency
- The compensating control must be **tested** and verified as operating effectively
- The modification must be **approved** by the Security Officer or compliance authority
- The modification must be **reassessed** at least annually

### Mapping Custom Security Roles

Organizations often create custom security roles in D365 FO that differ from the standard role names used in this matrix. The mapping process ensures conflict detection works with custom roles:

1. **Role Mapping Table**: Administrators maintain a mapping of custom roles to the standard role categories used in this matrix
2. **Duty-Level Mapping**: For more granular control, administrators can map at the duty level (e.g., "Custom AP Processor" maps to the duties of "Accounts payable clerk")
3. **Automatic Detection**: Algorithm 3.1 can suggest mappings based on the privileges and duties contained within custom roles
4. **Inheritance**: If a custom role contains all the privileges of a standard role, it inherits that standard role's conflict rules automatically

**Example mapping:**

| Custom Role Name | Maps To Standard Role | Mapping Basis |
|-----------------|----------------------|---------------|
| AP Team Lead | Accounts payable clerk + Accounts payable manager | Contains duties from both standard roles |
| Finance Analyst (Read-Only) | No mapping needed | Read-only roles do not participate in SoD conflicts |
| Senior Buyer | Purchasing agent | Contains purchasing agent duties |
| Treasury Operations | Treasurer + Payment clerk | Contains duties from both standard roles |

### Version Control and Change History

All modifications to the SoD matrix are version-controlled:

- **Version Number**: Automatically incremented on each change (e.g., 1.0, 1.1, 1.2)
- **Change Log**: Every modification records: timestamp, user, rule affected, change type (add/modify/disable/enable), before/after values, justification
- **Snapshot Export**: Administrators can export a point-in-time snapshot of the complete matrix for audit evidence
- **Rollback**: Previous versions can be restored if a change is made in error
- **Comparison**: Side-by-side comparison of any two versions to review changes over time

### Compensating Controls and Severity Reduction

Compensating controls are alternative controls that mitigate the risk when segregation of duties cannot be fully achieved. The following framework governs how compensating controls interact with the SoD matrix:

**Compensating Control Requirements:**
1. The control must **directly address** the specific risk described in the conflict rule
2. The control must be **documented** with a clear description, owner, frequency, and evidence requirements
3. The control must be **tested** for operating effectiveness (not just design effectiveness)
4. The control must be **reviewed** at least annually by the compliance authority

**Example: AP-001 Compensating Control**

Original conflict: A user who can both create vendors and process invoices (Critical severity).

Compensating control: All new vendor records require independent approval by the AP Manager through a D365 FO workflow before the vendor becomes active. All invoices above $5,000 require secondary approval. Monthly reconciliation of new vendors to invoices is performed by Internal Audit.

Effect: Severity reduced from Critical to High, because the compensating controls prevent immediate exploitation but do not fully eliminate the underlying access conflict.

---

## Mapping to D365 FO Standard Security Roles

The following table maps common D365 FO standard security roles to the SoD conflict categories in which they participate. This mapping helps administrators quickly identify which roles carry SoD implications.

| D365 FO Standard Role | Role Description | SoD Categories | Rules Involved |
|-----------------------|------------------|----------------|----------------|
| **Accounts payable clerk** | Processes vendor invoices, manages AP transactions | AP, CM | AP-001, AP-002, AP-004 |
| **Accounts payable manager** | Approves payments, manages AP department operations | AP, SA | AP-002, AP-005, SA-002 |
| **Vendor master maintenance** | Creates and maintains vendor master records | AP, PR | AP-001, AP-003, PR-004 |
| **Payment clerk** | Executes payment runs and payment processing | AP, CM | AP-003, AP-004, CM-001, CM-002 |
| **Purchasing agent** | Creates purchase orders, manages procurement | AP, PR | AP-005, PR-001, PR-003, PR-004 |
| **Purchasing manager** | Approves purchase orders, manages procurement department | PR | PR-001, PR-002 |
| **Requisitioner** | Creates purchase requisitions for goods and services | PR | PR-002 |
| **Receiving clerk** | Confirms receipt of goods against purchase orders | PR, INV | PR-003, INV-003 |
| **Accounts receivable clerk** | Manages customer invoices and receivable transactions | AR | AR-001, AR-002, AR-004 |
| **Collections agent** | Manages collections, write-offs, and payment follow-up | AR | AR-002, AR-003 |
| **Customer master maintenance** | Creates and maintains customer master records | AR | AR-001, AR-003 |
| **Billing clerk** | Generates billing documents and invoices to customers | AR | AR-004 |
| **General ledger clerk** | Creates journal entries, manages GL transactions | GL, SA | GL-001, GL-002, GL-004, SA-004 |
| **Accounting manager** | Approves journal entries, manages accounting operations | GL | GL-001 |
| **Accounting supervisor** | Posts approved journal entries, supervises GL activities | GL | GL-002, GL-003 |
| **Financial controller** | Performs period close, reconciliation, financial oversight | GL, SA | GL-003, GL-004, SA-003 |
| **Warehouse manager** | Manages warehouse operations and inventory custody | INV | INV-001 |
| **Inventory clerk** | Records inventory adjustments and maintains inventory records | INV | INV-001, INV-002 |
| **Warehouse worker** | Performs physical inventory movements and handling | INV | INV-002 |
| **Shipping clerk** | Manages outbound shipments and delivery documentation | INV | INV-003 |
| **Treasurer** | Manages bank relationships, cash positions, payment authorization | CM | CM-002, CM-003 |
| **Bank reconciliation clerk** | Performs bank statement reconciliation and matching | CM | CM-001, CM-003 |
| **System administrator** | Configures D365 FO system settings and infrastructure | SA | SA-001, SA-004 |
| **Security administrator** | Manages user accounts, security roles, and access provisioning | SA | SA-001, SA-002 |
| **IT manager** | Oversees IT operations and technology governance | SA | SA-003 |

---

## Data Structure for Algorithm 3.1

Each conflict rule is stored and loaded with the following structure, which Algorithm 3.1 consumes directly:

```
SODConflictRule:
  rule_id: string          // Unique identifier (e.g., "AP-001", "CUSTOM-001")
  category: string         // Category name (e.g., "Accounts Payable")
  role_a: string           // D365 FO role name or custom role
  role_b: string           // D365 FO role name or custom role
  conflict_type: string    // Brief conflict description
  risk_description: string // Detailed risk explanation
  severity: enum           // CRITICAL | HIGH | MEDIUM
  regulatory_reference: string  // Applicable standard(s)
  is_default: boolean      // True for rules from this document
  is_enabled: boolean      // True if active, false if disabled
  created_date: datetime   // When the rule was created
  created_by: string       // User who created the rule
  modified_date: datetime  // Last modification date
  modified_by: string      // User who last modified the rule
  compensating_control: string  // Description of compensating control, if any
  effective_severity: enum // Severity after compensating controls applied
  review_date: datetime    // Next scheduled review date
  version: integer         // Rule version number
```

---

## Sources & References

### Regulatory Frameworks

- **SOX Section 404**: Internal Control Assessment requirements. Requires management to assess and report on the effectiveness of internal controls over financial reporting. SoD is a foundational control under Section 404.
- **COSO Internal Control Framework (2013)**: The Committee of Sponsoring Organizations framework defines 17 principles for effective internal control. SoD rules in this matrix reference specific COSO principles:
  - Principle 8: Assesses fraud risk
  - Principle 10: Selects and develops control activities
  - Principle 11: Selects and develops IT general controls
  - Principle 12: Deploys control activities through policies
  - Principle 13: Uses relevant quality information
  - Principle 16: Evaluates and communicates deficiencies

### Industry Frameworks

- **Big 4 Audit Frameworks**: Deloitte, EY, KPMG, and PwC each publish SoD conflict matrices as part of their internal controls advisory practices. The rules in this document align with commonly identified conflicts across all four firms.
- **ISACA COBIT Framework**: Control Objectives for Information and Related Technologies. Provides IT governance guidance, particularly DSS05 (Manage Security Services) for system administration SoD requirements.

### Microsoft Documentation

- **Microsoft D365 FO Security Best Practices**: Microsoft's official documentation on security role design, duty segregation, and privilege assignment in Dynamics 365 Finance & Operations.
- **Microsoft D365 FO Security Architecture**: Role-based security model documentation including roles, duties, privileges, and permissions hierarchy.
- **Microsoft Dynamics 365 Licensing Guide**: Official licensing documentation for understanding role-to-license mappings and access level implications.

### Additional Standards

- **ISO 27001:2022**: Information security management systems. Annex A.5.3 specifically addresses Segregation of Duties.
- **NIST SP 800-53**: Security and privacy controls for information systems. AC-5 (Separation of Duties) provides federal guidance applicable to D365 FO deployments in regulated environments.

---

## Document Status

**Status**: Requirements Definition - Default SoD Conflict Matrix
**Dependencies**:
- `07-Advanced-Algorithms-Expansion.md` - Algorithm 3.1 (SoD Violation Detector) definition
- `14-Web-Application-Requirements.md` - Web application SoD management interface
- `02-Security-Configuration-Data.md` - Security role and duty data source
- `03-User-Role-Assignment-Data.md` - User-role assignment data source

**Related Documents**:
- `05-Functional-Requirements.md` - Core functional requirements
- `06-Algorithms-Decision-Logic.md` - Core algorithm definitions
- `12-Final-Phase1-Selection.md` - Phase 1 algorithm selection
- `13-Azure-Foundry-Agent-Architecture.md` - Agent architecture

**Next Steps**:
1. Review conflict matrix with compliance stakeholders and internal audit
2. Validate D365 FO role names against target environment
3. Map customer-specific custom roles to standard role categories
4. Configure initial compensating controls for known exceptions
5. Implement matrix loading in Algorithm 3.1 data pipeline
6. Build SoD management interface in web application

---

**End of Default SoD Conflict Matrix**
