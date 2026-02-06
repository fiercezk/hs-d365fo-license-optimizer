# User Activity Telemetry Data - Live from Azure App Insights

**Last Updated**: 2026-02-05
**Data Source**: Azure Application Insights (Custom D365 FO Telemetry)
**Nature**: Dynamic/Live data
**Access Method**: X++ Custom Telemetry → Azure Application Insights
**Priority**: Critical ⭐⭐⭐

---

## ⚠️ Important Note

**This data is LIVE and DYNAMIC** from Azure Application Insights. Technical implementation details (continuous export, Stream Analytics, pipelines) will be defined in a later phase. This documentation focuses on **what data is available** and **capabilities it enables**.

---

## 📊 Overview

User activity telemetry provides **real-time, granular tracking** of what users actually do in D365 FO, including **Read vs. Write actions** - a critical capability that Microsoft's native solution lacks.

**Sample Reference**: `UserLogSample.png` (visual representation of the data)

---

## 🎯 Purpose & Capabilities

### **What This Data Provides**

| Capability | Description | Business Value |
|------------|-------------|----------------|
| **Actual Usage Tracking** | What users ACTUALLY do (not theoretical) | Real optimization |
| **Read vs. Write Analysis** | Distinguish view-only from create/modify | ⭐ Critical for licensing! |
| **Session Context** | User workflows, time spent | UX insights |
| **Real-Time Events** | Live streaming of user actions | Immediate analysis |
| **Device/Client Info** | Access patterns by device/type | Security insights |

---

## 🗂️ Expected Data Content

### **Key Data Points** (from UserLogSample.png)

| Field | Description | Example |
|-------|-------------|---------|
| **User ID** | User identifier | `john.doe@contoso.com` |
| **Menu Item / Form** | What user accessed | `GeneralJournalEntry`, `CustomerList` |
| **Action** | Type of operation | `Read`, `Write`, `Delete`, `Create` |
| **Timestamp** | When accessed | `2025-02-05 14:32:15` |
| **Session** | Session identifier | `session-guid-12345` |
| **License Tier** | License for this menu item | `Enterprise`, `Activity`, `Team Members` |
| **Feature** | Module/functional area | `General Ledger`, `Accounts Payable` |

**Note**: Exact field names and structure will be determined during implementation phase.

---

## 💡 Key Insights

### **1. Read vs. Write Tracking** ⭐ CRITICAL

This is the **most important capability** for license optimization:

```
Same Menu Item + Different Action = Different License Requirement

Example: GeneralJournalEntry
├─ GeneralJournalEntry (Read)  → Team Members can do this
└─ GeneralJournalEntry (Write) → Requires Enterprise license
```

**Business Impact**:
- User with 99% Read operations → Could downgrade to Team Members
- Estimated savings: $120 per user per month

---

### **2. Session-Level Analysis**

**Session Context Enables**:
- **Workflow Analysis**: What sequence of menu items do users access?
- **Time Distribution**: How long do users spend in different areas?
- **Anomaly Detection**: Unusual session patterns (security risk)
- **UX Optimization**: Understand user journeys

---

### **3. Real-Time vs. Batch**

**Nature of Data**: Live streaming events

**Benefits**:
- ✅ Immediate analysis possible
- ✅ Real-time alerts for anomalies
- ✅ Live dashboards
- ✅ No waiting for batch exports

**Challenges**:
- High event volume (need to manage scale)
- Complex processing (streaming analytics)
- Cost management (Azure pricing)

---

## 🔍 Sample Analysis Scenarios

### **Scenario 1: Read-Only User Detection**

**Problem**: Identify users who only read data (could use cheaper license)

**Data Needed**:
- User ID
- Action type (Read vs. Write)
- Time period (last 90 days)

**Logic**:
```
For each user, last 90 days:
  1. Count total events
  2. Count Read events
  3. Count Write events
  4. Calculate Read percentage
  5. If Read % > 95% → Flag for downgrade
```

**Sample Result**:
```
User: john.doe@contoso.com
Last 90 days:
├─ Total events: 847
├─ Read operations: 845 (99.76%)
└─ Write operations: 2 (0.24%)

Conclusion: 99.76% read-only
→ Recommendation: Downgrade to Team Members license
→ Estimated savings: $120/month
```

---

### **Scenario 2: Inactive User Detection**

**Problem**: Find users with no activity in 90+ days

**Data Needed**:
- User ID
- Last access timestamp

**Logic**:
```
For each user:
  1. Find most recent access timestamp
  2. Calculate days since last access
  3. If days inactive > 90 → Flag for license removal
```

**Result**: List of inactive users for cleanup

---

### **Scenario 3: Feature Adoption**

**Problem**: Which menu items are actually used? Which are unused?

**Data Needed**:
- Menu item
- User ID
- Count of accesses

**Logic**:
```
For each menu item:
  1. Count distinct users who accessed it
  2. Count total accesses
  3. Rank by usage
```

**Result**:
- Top 10 most used features
- Bottom 10 unused features (cleanup candidates)

---

## 🔗 Integration with Other Data Sources

### **Combines With**:

1. **Security Configuration** (Live)
   - Enriches: Adds LicenseType to each event
   - Enables: Compare theoretical vs. actual requirements

2. **User-Role Assignments** (Live)
   - Adds: User's assigned roles
   - Enables: Per-user actual usage analysis

3. **Audit Logs** (Live)
   - Adds: Context for role changes
   - Enables: Correlate usage with security changes

---

## 💡 Business Value

### **What This Enables**

✅ **License Optimization**:
- Find read-only users (downgrade to Team Members)
- Detect inactive users (remove licenses)
- Right-size licenses based on actual usage

✅ **Security Monitoring**:
- Real-time anomaly detection
- Unusual access patterns
- Session hijacking detection

✅ **Operational Insights**:
- Feature adoption tracking
- User workflow optimization
- Training needs identification

✅ **Compliance Support**:
- Audit-ready activity logs
- User access certifications
- Change history correlation

---

## 📋 Expected Data Characteristics

### **Volume** (estimates)
- **Events per day**: 10,000 - 10,000,000 (varies by org size)
- **Users**: 100 - 50,000
- **Unique menu items**: Thousands

### **Freshness**
- **Nature**: Live/Dynamic streaming
- **Latency**: Seconds to minutes
- **Availability**: Real-time

### **Complexity**
- **High volume**: Need to manage scale
- **Continuous**: Always streaming
- **Multi-dimensional**: User, action, time, session, device

---

## ⚠️ Current Limitations (To Be Addressed)

| Aspect | Current Status | To Be Determined |
|--------|----------------|-----------------|
| **Data Access** | Sample reviewed (UserLogSample.png) | Live access method TBD |
| **Exact Schema** | Based on sample image | Final schema TBD |
| **Retention** | Unknown | How long to keep events? |
| **Processing** | Unknown | Stream processing approach? |
| **Cost** | Unknown | Azure App Insights pricing |

---

## 🔑 Critical Differentiator

### **Your Custom Telemetry vs. Microsoft Native**

| Feature | Microsoft User Security Governance (Preview) | Your Custom Implementation |
|---------|-------------------------------------------|---------------------------|
| Menu item tracking | ✅ Yes | ✅ Yes |
| **Read vs. Write distinction** | ❌ No | ✅ **Yes** ⭐ |
| **Session-level analysis** | ❌ No | ✅ **Yes** |
| **Real-time streaming** | ⚠️ Limited | ✅ **Yes** |
| **Historical trends** | ⚠️ Limited | ✅ **Yes** (full history) |
| **Custom enrichment** | ❌ No | ✅ **Yes** (device, context) |

**Insight**: Your custom telemetry is significantly more powerful for license optimization!

---

## 🔧 Custom Telemetry Instrumentation (X++)

### **Implementation Approach**

Telemetry is being built using **X++ custom instrumentation** within D365 FO, sending events directly to Azure Application Insights.

### **X++ Form Event Handler Approach**

The telemetry system uses standard D365 FO extension patterns to capture user activity:

- **`FormRun.init()` hooks**: Capture form open events (Read actions) via event handler extensions on form initialization
- **`FormDataSource.write()` hooks**: Capture create/update operations (Write actions) when data is saved through form data sources
- **`FormDataSource.delete()` hooks**: Capture delete operations when records are removed
- **`FormRun.close()` hooks**: Capture session duration by recording form close events

### **App Insights SDK Integration**

Integration uses the `Microsoft.ApplicationInsights` X++ reference to submit telemetry:
- X++ classes reference the Application Insights SDK via .NET interop
- TelemetryClient is initialized with the App Insights instrumentation key
- Events are submitted asynchronously to avoid blocking user operations
- Connection string is stored in D365 FO system parameters (configurable per environment)

### **Expected Event Schema**

```json
{
  "userId": "john.doe@contoso.com",
  "formName": "GeneralJournalEntry",
  "action": "Read|Write|Create|Delete",
  "timestamp": "2026-02-05T14:32:15.000Z",
  "sessionId": "session-guid-12345",
  "menuItemName": "GeneralJournal",
  "licenseTier": "Finance",
  "duration": 45000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `userId` | string | User's AAD email/UPN |
| `formName` | string | D365 FO form name (e.g., `GeneralJournalEntry`) |
| `action` | enum | `Read`, `Write`, `Create`, `Delete` |
| `timestamp` | datetime | UTC timestamp of the event |
| `sessionId` | string | D365 FO session identifier |
| `menuItemName` | string | Menu item that launched the form |
| `licenseTier` | string | License tier required for this menu item |
| `duration` | int | Time spent on form in milliseconds (on close events) |

### **Performance Impact Assessment**

| Metric | Target | Notes |
|--------|--------|-------|
| **Overhead per event** | < 5ms | Async telemetry submission, non-blocking |
| **Sampling rate** | Configurable (default 100%) | Can reduce to 50%/25% for high-volume environments |
| **Memory footprint** | Negligible | TelemetryClient singleton, buffered batch submission |
| **Network impact** | Minimal | Events batched and compressed before transmission |
| **User experience** | Zero perceptible impact | All telemetry operations are fire-and-forget async |

### **Maintenance Strategy**

- Event handlers use **standard D365 FO extension patterns** (no overlayering)
- Extensions survive D365 FO platform updates and version upgrades
- No modifications to base Microsoft code — all functionality via `[ExtensionOf]` and event subscriptions
- Telemetry configuration (instrumentation key, sampling rate) managed via D365 FO parameters form

### **Current Status**

> **Status**: In development. POC will use test telemetry data for algorithm validation.
> Initial telemetry handlers are being developed and will be deployed to a sandbox environment for validation before production rollout.

---

## 📝 Key Points

1. **Data is LIVE**: Real-time streaming from Azure App Insights
2. **Read/Write Tracking**: ⭐ Most important capability for licensing
3. **Access Method**: X++ Custom Telemetry → Azure Application Insights (in development)
4. **Focus on Capabilities**: This doc explains WHAT we can do with the data
5. **Sample Reference**: UserLogSample.png shows the data structure

---

## 🚀 Next Steps

### **Phase 1: Requirements** (Current) ✅
- Document data content and capabilities
- Define analysis scenarios
- Identify business value

### **Phase 2: Technical Design** (Future) ⏳
- [ ] Determine access method (continuous export, stream processing?)
- [ ] Finalize exact schema
- [ ] Design processing architecture
- [ ] Plan cost optimization
- [ ] Define retention policy

### **Phase 3: Implementation** (Future) ⏳
- [ ] Set up data ingestion
- [ ] Implement stream processing
- [ ] Create aggregations
- [ ] Build dashboards

---

## 📚 Related Documentation

- `00-Index.md` - Overview and index
- `02-Security-Configuration-Data.md` - License types and entitlements
- `03-User-Role-Assignment-Data.md` - User-to-role mappings

---

**Document Status**: Content Understanding Complete ✅
**Technical Implementation**: To Be Determined ⏳
**Note**: Access method, processing architecture, and cost optimization will be defined in later phase

**End of User Activity Telemetry Data**
