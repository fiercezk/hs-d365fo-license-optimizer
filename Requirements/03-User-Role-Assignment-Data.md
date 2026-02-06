# User-Role Assignment Data - Live from D365 FO

**Last Updated**: 2026-02-05
**Data Source**: D365 FO User-Role Assignments (Live)
**Nature**: Dynamic/Live data
**Access Method**: To Be Determined (TBD)
**Priority**: High

---

## ⚠️ Important Note

**This data is LIVE and DYNAMIC** from D365 FO. Technical implementation details (OData, APIs, sync strategies) will be defined in a later phase. This documentation focuses on **what data is available** and **capabilities it enables**.

---

## 📊 Overview

User-role assignment data provides the **critical link** between users and security roles, enabling per-user license analysis.

```
Users ← UserRole → SecurityRoles → SecurityConfiguration → LicenseType
```

---

## 🎯 Purpose & Capabilities

### **What This Data Provides**

| Capability | Description | Business Use |
|------------|-------------|--------------|
| **User-to-Role Mapping** | Which users have which roles | Calculate license per user |
| **User Details** | Name, email, department, manager | Reporting & notifications |
| **Role Assignment History** | When roles were assigned/removed | Audit trail |
| **License Assignment** | Current license per user | Compare vs. requirement |
| **Organizational Context** | Department, company, etc. | Workflow approvals |

---

## 🗂️ Expected Data Content

### **Key Entities** (based on D365 FO data model)

**Users**:
- User ID (unique identifier)
- User name
- Email address
- Company/Legal entity
- Department (optional)
- Manager (optional)
- Status (Active/Inactive)

**Security Roles**:
- Role ID
- Role name
- Description
- License type (derived from SecurityConfiguration)

**User-Role Assignments**:
- User ID
- Role ID
- Assigned date/time
- Assigned by (who made the assignment)
- Valid from/to dates
- Current status (Active/Inactive)

**Note**: Exact field names and structure will be determined during implementation phase.

---

## 💡 Key Capabilities Enabled

### **1. Calculate License Requirement Per User**

**Question**: What license does John Doe require based on his roles?

**Data Needed**:
- John Doe's assigned roles
- License type for each role (from SecurityConfiguration)
- Highest license wins

**Logic**:
```
For each user:
  1. Get all assigned roles
  2. Get license type for each role
  3. Select highest license type
  4. That's the user's required license
```

**Sample Result**:
```
User: john.doe@contoso.com
Roles: Accountant, Budget Clerk
├─ Accountant → Commerce license
└─ Budget Clerk → Team Members license
Required License: Commerce (highest)
```

---

### **2. Identify Users with Too Many Roles**

**Question**: Which users have excessive role assignments?

**Data Needed**:
- Count of roles per user
- Threshold (e.g., > 5 roles)

**Logic**:
```
Find users where:
  Role count > threshold

Group by:
  User, list of roles
```

**Result**: List of users for role cleanup

---

### **3. Track Role Assignment Changes**

**Question**: Who gained/lost roles in the last 7 days?

**Data Needed**:
- Assignment date/time
- Change type (Assigned/Removed)

**Logic**:
```
Filter: Last 7 days
Group by: User, Role, Action
```

**Result**: Recent role changes for audit

---

## 🔗 Integration with Other Data Sources

### **Combines With**:

1. **Security Configuration** (Live)
   - Provides: License type for each role
   - Enables: Calculate user's required license

2. **User Activity** (Live)
   - Provides: What user actually does
   - Enables: Compare required vs. actual usage

3. **Audit Logs** (Live)
   - Provides: Change history
   - Enables: Track why roles were assigned/changed

---

## 💡 Business Value

### **What This Enables**

✅ **Per-user license calculation** (not just per-role)
✅ **Identify over-licensed users** (too many high-license roles)
✅ **Track role explosion** (users with 10+ roles)
✅ **Maintain audit trail** (who assigned what to whom)
✅ **Department-level analysis** (license cost by department)
✅ **Manager notifications** (approval workflows)

### **Use Cases**

| Use Case | Description | Impact |
|----------|-------------|--------|
| **License Optimization** | Find users with unnecessary high-cost roles | Cost reduction |
| **Access Reviews** | List all users with sensitive roles | Compliance |
| **Change Management** | Track role assignment changes over time | Audit |
| **Cost Allocation** | Calculate license cost per department | Budgeting |

---

## 📋 Expected Data Characteristics

### **Volume** (estimates)
- **Users**: 100 - 50,000 (varies by org size)
- **Roles**: 50 - 500
- **User-Role Assignments**: 200 - 200,000

### **Freshness**
- **Nature**: Live/Dynamic
- **Update Frequency**: Real-time when changes are made
- **Lag**: Minimal (seconds to minutes)

### **Complexity**
- **Relationships**: Many-to-many (users ↔ roles)
- **Dependencies**: User, Role, Company, Department
- **Time-based**: Valid from/to dates for assignments

---

## ⚠️ Current Limitations (To Be Addressed)

| Aspect | Current Status | To Be Determined |
|--------|----------------|-----------------|
| **Data Access** | Understanding exists | Access method TBD |
| **Exact Schema** | Based on D365 FO model | Final schema TBD |
| **Refresh Rate** | Real-time (theoretical) | Actual sync pattern TBD |
| **History Depth** | Unknown | How much history to keep? |

---

## 🔍 Sample Analysis Queries (Conceptual)

### **Query 1: Users Requiring Enterprise Licenses**

```sql
-- Find all users who need Enterprise licenses
SELECT DISTINCT
    u.User ID,
    u.UserName,
    'Enterprise' as RequiredLicense
FROM User-Role Assignments ua
JOIN SecurityRoles sr ON ua.RoleID = sr.RoleID
JOIN SecurityConfiguration sc ON sr.RoleName = sc.securityrole
WHERE sc.LicenseType IN ('Finance', 'Commerce', 'SCM')
  AND ua.IsActive = 1
```

### **Query 2: Users with Multiple Roles**

```sql
-- Find users with > 5 roles
SELECT
    u.UserID,
    u.UserName,
    COUNT(DISTINCT ua.RoleID) as RoleCount,
    STRING_AGG(sr.RoleName, ', ') as Roles
FROM Users u
JOIN User-Role Assignments ua ON u.UserID = ua.UserID
JOIN SecurityRoles sr ON ua.RoleID = sr.RoleID
WHERE ua.IsActive = 1
GROUP BY u.UserID, u.UserName
HAVING COUNT(DISTINCT ua.RoleID) > 5
ORDER BY RoleCount DESC
```

---

## 🚀 Next Steps

### **Phase 1: Requirements** (Current) ✅
- Document data content and capabilities
- Define analysis scenarios
- Identify business value

### **Phase 2: Technical Design** (Future) ⏳
- [ ] Determine access method (API, OData, direct DB?)
- [ ] Finalize exact schema
- [ ] Design integration pattern
- [ ] Define refresh strategy
- [ ] Plan error handling

### **Phase 3: Implementation** (Future) ⏳
- [ ] Build data connection
- [ ] Implement queries and views
- [ ] Test and validate

---

## 📝 Key Points

1. **Data is LIVE**: Will be fetched in real-time from D365 FO
2. **Access Method TBD**: Technical approach will be decided later
3. **Schema May Vary**: Exact structure to be confirmed during implementation
4. **Focus on Content**: This doc explains WHAT data provides, not HOW to get it

---

## 📚 Related Documentation

- `00-Index.md` - Overview and index
- `02-Security-Configuration-Data.md` - License types and roles
- `04-User-Activity-Telemetry-Data.md` - User action tracking

---

**Document Status**: Content Understanding Complete ✅
**Technical Implementation**: To Be Determined ⏳
**Note**: Access method, exact schema, and integration pattern will be defined in later phase

**End of User-Role Assignment Data**
