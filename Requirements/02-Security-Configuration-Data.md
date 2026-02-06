# Security Configuration Data - Live from D365 FO

**Last Updated**: 2026-02-05
**Data Source**: D365 FO Security Configuration (Live)
**Nature**: Dynamic/Live data
**Access Method**: To Be Determined (TBD)
**Priority**: High

---

## ⚠️ Important Note

**This data is LIVE and DYNAMIC** from D365 FO. The sample file `FinalAnalysisData.csv` (704,661 records) represents the structure and content, but actual data will be fetched live from D365 FO in real-time.

**Technical implementation will be designed in a later phase.**

---

## 📊 Overview

Security configuration data provides the **complete mapping of security roles to security objects** (menu items, entities, actions) and their associated license types.

```
Security Roles → Security Objects → License Types → Entitlement Status
```

**Sample Reference**: `FinalAnalysisData.csv` (static export representing the live data structure)

---

## 🎯 Purpose & Capabilities

### **What This Data Provides**

| Capability | Description | Business Use |
|------------|-------------|--------------|
| **Role-to-License Mapping** | Which license each role requires | Calculate license costs |
| **Security Object Inventory** | All menu items, entities, actions | Security analysis |
| **Entitlement Status** | Whether access is licensed or not | Compliance gap detection |
| **Access Level Detail** | Read vs. Write requirements | License optimization |
| **Role Comparison** | Compare roles across licenses | Consolidation opportunities |

---

## 🗂️ Data Content (Based on Sample)

### **Key Fields Available** (from FinalAnalysisData.csv sample)

| Field | Description | Sample Values |
|-------|-------------|---------------|
| **AccessLevel** | Type of access permission | `Write`, `Read`, `Delete`, `Update` |
| **AOTName** | Menu item / entity name | `ACCOUNTANT_BR`, `ASSETBUDGET`, `CustomerList` |
| **securityrole** | Security role name | `Accountant`, `Purchasing manager`, `CFO` |
| **LicenseType** | License type required | `Commerce`, `Finance`, `Team Members` |
| **Entitled** | Whether access is covered | `1` = Yes, `0` = No |
| **NotEntitiled** | Whether access is NOT covered | `1` = Compliance risk |
| **securitytype** | Type of security object | `MenuItemDisplay`, `MenuItemAction`, `DataEntity` |
| **Priority** | License priority level | `60` (Commerce), `20` (Team Members) |

**Note**: Actual field names and exact structure will be determined during implementation phase.

---

## 💡 Key Insights from Sample Data

### **1. License Types Identified**

From the sample (FinalAnalysisData.csv):

| Priority | License Type | LicenseRecId | Description |
|----------|-------------|--------------|-------------|
| 60 | Commerce | 1 | Full user license |
| 20 | Team Members | 11 | Limited user license |
| 5 | None | 6 | No license required |

**Inference**: Data likely contains multiple license types (Finance, SCM, Commerce, Team Members, etc.)

---

### **2. Security Object Types**

| Type | Purpose | Example |
|------|---------|---------|
| **MenuItemDisplay** | UI elements/forms | `ACCOUNTANT_BR` |
| **MenuItemAction** | Operational actions | `DMFRUNTARGETASYNC` |
| **MenuItemOutput** | Reports | `RETAILSALESBYHOUR` |
| **DataEntity** | OData/API entities | `PROJPROJECTV2ENTITY` |
| **DataEntityMethod** | Entity methods | `GETWORKEREMPLOYEDLEGALENTITIES` |

**Insight**: Comprehensive coverage of UI, API, and operational access.

---

### **3. Role Diversity**

**100+ unique roles** identified across:

- **Finance**: Accountant, CFO, Budget manager, Accounts payable/receivable
- **Operations**: Purchasing manager, Warehouse manager, Sales manager
- **Technical**: IT manager, Data management admin
- **HR**: HR manager, Recruiter, Payroll admin
- **Executive**: CEO, CFO

---

### **4. Entitlement Status Codes**

| Entitled | NotEntitiled | Meaning |
|----------|-------------|---------|
| 1 | 0 | Access IS covered by license ✅ |
| 0 | 1 | Access NOT covered by license ⚠️ (Compliance risk) |
| - | - | Not applicable |

**Use Case**: Identify security gaps where users have access but license doesn't cover it.

---

## 🔍 Sample Analysis Scenarios

### **Scenario 1: Calculate License Requirement per Role**

**Question**: What license does the "Accountant" role require?

**Data Needed**:
- All security objects for "Accountant" role
- License type for each object
- Highest license type wins

**Logic**:
```
For each role:
  1. Get all security objects assigned to role
  2. Identify highest license type across all objects
  3. That becomes the role's required license
```

**Sample Result**:
```
Role: Accountant
├─ 500 menu items require Team Members
├─ 50 menu items require Commerce
└─ Highest: Commerce
Required License: Commerce (Enterprise)
```

---

### **Scenario 2: Identify Compliance Gaps**

**Question**: Which roles have access that's NOT covered by license?

**Data Needed**:
- Entitled = 0 (Not entitled)
- NotEntitiled = 1

**Logic**:
```
Find all security objects where:
  Entitled = 0 AND NotEntitiled = 1

Group by:
  securityrole, LicenseType
```

**Result**: List of roles and menu items with compliance risks

---

### **Scenario 3: Role Consolidation**

**Question**: Which roles are similar and could be consolidated?

**Data Needed**:
- Security objects for Role A
- Security objects for Role B

**Logic**:
```
For each pair of roles:
  Calculate overlap in security objects
  If overlap > 80% → Flag for consolidation
```

**Result**: List of similar roles that could be merged

---

## 🔗 Integration with Other Data Sources

### **Combines With**:

1. **User-Role Assignments** (Live)
   - Adds: Which users have which roles
   - Enables: Per-user license calculation

2. **User Activity** (Live)
   - Adds: What users actually do
   - Enables: Actual usage vs. theoretical permission analysis

3. **Audit Logs** (Live)
   - Adds: Change history
   - Enables: Track how security configuration evolves

---

## 📋 Expected Data Characteristics

### **Volume** (from sample)
- **Total Records**: 704,661 (sample)
- **Unique Roles**: 100+
- **Unique Menu Items**: Thousands
- **Security Object Types**: 5

### **Freshness**
- **Nature**: Live/Dynamic
- **Update Frequency**: Real-time when security changes are made
- **Lag**: Minimal (seconds to minutes)

### **Complexity**
- **Relationships**: Many-to-many (roles ↔ menu items)
- **Hierarchy**: Role → Duty → Privilege → Menu Item (may not all be exposed)
- **Variations**: By company, legal entity, environment

---

## 💡 Business Value

### **What This Data Enables**

✅ **Calculate theoretical license requirement** for each user based on their roles
✅ **Identify compliance gaps** where access exists but license doesn't cover
✅ **Find consolidation opportunities** by comparing similar roles
✅ **Detect high-license privileges** that drive up costs
✅ **Maintain security configuration baseline** for comparison with actual usage

### **Use Cases**

| Use Case | Description | Impact |
|----------|-------------|--------|
| **License Cost Analysis** | Calculate what licenses should cost | Budget planning |
| **Compliance Monitoring** | Detect unauthorized access | Risk management |
| **Role Optimization** | Consolidate similar roles | Cost reduction |
| **Security Reviews** | Audit access rights | Compliance reporting |

---

## ⚠️ Current Limitations (To Be Addressed)

| Aspect | Current Status | To Be Determined |
|--------|----------------|-----------------|
| **Data Access** | Have sample only | Live access method |
| **Exact Schema** | Based on CSV export | Final schema TBD |
| **Refresh Rate** | Unknown | Update frequency TBD |
| **Data Volume** | ~704K records (sample) | Production volume TBD |
| **Field Names** | From CSV sample | Actual D365 FO fields TBD |

---

## 🚀 Next Steps

### **Phase 1: Requirements** (Current)
- ✅ Document data content and capabilities
- ✅ Identify analysis scenarios
- ✅ Define business value

### **Phase 2: Technical Design** (Future)
- [ ] Determine data access method (API, OData, direct DB?)
- [ ] Finalize exact schema and field names
- [ ] Design integration pattern
- [ ] Define refresh strategy
- [ ] Plan error handling

### **Phase 3: Implementation** (Future)
- [ ] Build data connection
- [ ] Implement ingestion
- [ ] Create queries and views
- [ ] Test and validate

---

## 📝 Key Points to Remember

1. **Data is LIVE**: Not a static export, will be fetched in real-time
2. **Sample Reference**: FinalAnalysisData.csv represents the structure
3. **Access Method TBD**: How we fetch this data will be decided later
4. **Schema May Change**: Exact field names/types to be finalized
5. **Focus on Capabilities**: This doc explains WHAT data provides, not HOW to get it

---

## 📚 Related Documentation

- `00-Index.md` - Overview and index
- `03-User-Role-Assignment-Data.md` - User-to-role mappings
- `04-User-Activity-Telemetry-Data.md` - User action tracking

---

**Document Status**: Content Understanding Complete ✅
**Technical Implementation**: To Be Determined ⏳
**Note**: Access method, exact schema, and integration pattern will be defined in later phase

**End of Security Configuration Data**
