# D365 FO License Agent - X++ Instrumentation Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-07
**Target Audience:** D365 FO Developers, X++ Developers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Development Environment Setup](#development-environment-setup)
5. [Telemetry Events Design](#telemetry-events-design)
6. [Implementation Steps](#implementation-steps)
7. [Testing & Validation](#testing--validation)
8. [Deployment](#deployment)
9. [Performance Considerations](#performance-considerations)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

This guide covers the development and deployment of X++ telemetry instrumentation for the D365 FO License Agent. The instrumentation captures user activity events (form opens, actions, operations) and sends them to Azure Application Insights for analysis.

**Purpose:**

- **User Behavior Analysis:** Algorithms 4.1, 4.2, 4.3 analyze read vs. write patterns
- **Device License Detection:** Identify users who access D365 only via mobile devices
- **Security Monitoring:** Detect anomalous access patterns (Algorithm 3.2, 3.6)
- **License Optimization:** Determine if users are read-only, qualify for Team Members, or need full Operations license

**Design Principles:**

- **Minimal Performance Impact:** < 5ms overhead per form open
- **Asynchronous Logging:** Telemetry sent in background, never blocks user workflow
- **Privacy-Aware:** No PII beyond user ID and role names
- **Failure-Safe:** Telemetry failures never crash D365 FO forms or transactions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ D365 Finance & Operations Environment                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ User Workflow (e.g., Open PurchTable form)           │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│                      ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Form EventHandler (formRun.init override)            │  │
│  │  - Captures: userId, formName, timestamp, action     │  │
│  │  - Builds: TelemetryEvent object                     │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│                      ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ LicenseAgentTelemetryEngine (X++ class)              │  │
│  │  - Validates event schema                            │  │
│  │  - Enriches with context (roleNames, deviceType)     │  │
│  │  - Queues for async send                             │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│                      ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ AppInsightsSender (X++ → HTTP POST)                  │  │
│  │  - Batch sends (max 100 events / request)            │  │
│  │  - Retry logic (3 attempts, exponential backoff)     │  │
│  │  - Fallback to local file log on failure             │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │                                      │
└──────────────────────┼──────────────────────────────────────┘
                       │ HTTPS POST
                       │ https://dc.applicationinsights.azure.com/v2/track
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Azure Application Insights                                 │
│  - Stores telemetry events                                 │
│  - Queryable via KQL (Kusto Query Language)                │
│  - Powers Agent algorithms 4.1, 4.2, 4.3, 3.2              │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**

1. **FormEventHandler:** Chain-of-Command extensions on FormRun.init() for all forms
2. **LicenseAgentTelemetryEngine:** Central telemetry engine (validates, enriches, queues)
3. **AppInsightsSender:** HTTP client for Application Insights REST API
4. **TelemetryEvent Data Contract:** Serializable class representing an event
5. **Configuration Table:** Stores App Insights instrumentation key, sampling rate, enabled/disabled flag

---

## Prerequisites

### Development Environment

- **D365 FO Version:** 10.0.38 or later
- **Development VM:** Tier 1 (OneBox) environment with Visual Studio installed
- **Visual Studio Extensions:** Dynamics 365 Finance SCM Tools (latest version)
- **Source Control:** Azure DevOps or GitHub repository for X++ code

### Azure Resources

- **Application Insights:** Instrumentation Key (from Azure Portal)
- **Connectivity:** D365 FO environment must allow outbound HTTPS to `*.applicationinsights.azure.com`

### Permissions

- **D365 FO:** System Administrator role (to deploy code, configure parameters)
- **Azure DevOps:** Contributor access to project (to commit X++ code)

---

## Development Environment Setup

### 1. Create X++ Model

**Steps (Visual Studio on D365 FO Dev VM):**

1. **Dynamics 365 > Model Management > Create model**
   - Model name: `LicenseAgentTelemetry`
   - Model publisher: `YourOrganization`
   - Layer: `ISV` (or `USR` if ISV unavailable)
   - Model description: `Telemetry instrumentation for D365 FO License Agent`

2. **Create new project:**
   - File > New > Project
   - Select **Dynamics 365 Finance Operations Project**
   - Project name: `LicenseAgentTelemetry`
   - Add to model: `LicenseAgentTelemetry`

3. **Add references:**
   - Right-click project > Add reference
   - Add: `ApplicationPlatform`, `ApplicationFoundation`, `ApplicationSuite`

### 2. Create Configuration Table (EDT, Table, Form)

**Extended Data Type (EDT):**

Create `LATelemetryInstrumentationKey` (String, 100 characters):

```xpp
/// <summary>
/// Azure Application Insights Instrumentation Key
/// </summary>
[ExtendedDataType]
class LATelemetryInstrumentationKey extends str
{
    public static LATelemetryInstrumentationKey construct()
    {
        return str::construct();
    }
}
```

**Table: LATelemetryConfig**

```xpp
/// <summary>
/// Configuration table for License Agent Telemetry
/// Stores Azure Application Insights connection info and feature flags
/// </summary>
[DataManagement(DataManagementEnabled = true)]
table LATelemetryConfig
{
    // Primary Key
    Key dataAreaId;

    // Fields
    str InstrumentationKey;     // Azure App Insights instrumentation key
    boolean Enabled;            // Enable/disable telemetry globally
    int SamplingRatePercent;    // Sampling: 1-100% (100 = all events)
    boolean LogFailuresToFile;  // Fallback to file log on HTTP failure
    str AllowedFormPatterns;    // Regex patterns for forms to instrument (e.g., "Purch*,Sales*")

    // Indexes
    index DataAreaIdx
    {
        AllowDuplicates = No;
        dataAreaId;
    }
}
```

**Form: LATelemetryConfigForm**

Create simple form with grid displaying `LATelemetryConfig` table fields. Add to menu item for System Administration > Setup.

---

## Telemetry Events Design

### Event Schema

**Event Type: FormOpened**

Sent when user opens any D365 FO form.

```json
{
  "name": "FormOpened",
  "timestamp": "2026-02-07T10:15:32.123Z",
  "properties": {
    "userId": "john.doe@contoso.com",
    "formName": "PurchTable",
    "moduleName": "ProcurementAndSourcing",
    "roleNames": "Purchasing Agent,Inventory Clerk",
    "deviceType": "Desktop",
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "companyId": "USMF"
  },
  "measurements": {
    "loadTimeMs": 234.5
  }
}
```

**Event Type: FormAction**

Sent when user performs action in a form (save, delete, post, etc.).

```json
{
  "name": "FormAction",
  "timestamp": "2026-02-07T10:16:45.456Z",
  "properties": {
    "userId": "john.doe@contoso.com",
    "formName": "PurchTable",
    "actionName": "Save",
    "actionType": "Write",
    "recordId": "PO-12345",
    "roleNames": "Purchasing Agent",
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "companyId": "USMF"
  },
  "measurements": {
    "durationMs": 89.3
  }
}
```

**Event Type: FormClosed**

Sent when user closes form.

```json
{
  "name": "FormClosed",
  "timestamp": "2026-02-07T10:20:12.789Z",
  "properties": {
    "userId": "john.doe@contoso.com",
    "formName": "PurchTable",
    "sessionDurationSeconds": 280,
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

**Privacy Considerations:**

- **Do NOT capture:** Record field values, customer names, financial amounts, personal data beyond user ID
- **Do capture:** Form name, action type (read/write), timestamp, role names
- **User ID:** Email address (already known to D365 admin, needed for license analysis)

---

## Implementation Steps

### Step 1: Create TelemetryEvent Data Contract

```xpp
/// <summary>
/// Data contract for telemetry events sent to Application Insights
/// </summary>
[DataContract]
class LATelemetryEvent
{
    str eventName;
    utcDateTime timestamp;
    Map properties;     // str -> str
    Map measurements;   // str -> real

    [DataMember('name')]
    public str parmEventName(str _eventName = eventName)
    {
        eventName = _eventName;
        return eventName;
    }

    [DataMember('timestamp')]
    public str parmTimestamp(utcDateTime _timestamp = timestamp)
    {
        timestamp = _timestamp;
        return DateTimeUtil::toStr(_timestamp);
    }

    [DataMember('properties')]
    public Map parmProperties(Map _properties = properties)
    {
        properties = _properties;
        return properties;
    }

    [DataMember('measurements')]
    public Map parmMeasurements(Map _measurements = measurements)
    {
        measurements = _measurements;
        return measurements;
    }

    public void addProperty(str key, str value)
    {
        if (!properties)
        {
            properties = new Map(Types::String, Types::String);
        }
        properties.insert(key, value);
    }

    public void addMeasurement(str key, real value)
    {
        if (!measurements)
        {
            measurements = new Map(Types::String, Types::Real);
        }
        measurements.insert(key, value);
    }

    /// <summary>
    /// Serialize to JSON for Application Insights REST API
    /// </summary>
    public str toJson()
    {
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        sb.Append('{');
        sb.Append(strFmt('"name":"%1",', eventName));
        sb.Append(strFmt('"time":"%1",', DateTimeUtil::toStr(timestamp)));

        // Properties
        sb.Append('"properties":{');
        MapEnumerator propEnum = properties.getEnumerator();
        boolean first = true;
        while (propEnum.moveNext())
        {
            if (!first) sb.Append(',');
            sb.Append(strFmt('"%1":"%2"', propEnum.currentKey(), propEnum.currentValue()));
            first = false;
        }
        sb.Append('},');

        // Measurements
        sb.Append('"measurements":{');
        MapEnumerator measEnum = measurements.getEnumerator();
        first = true;
        while (measEnum.moveNext())
        {
            if (!first) sb.Append(',');
            sb.Append(strFmt('"%1":%2', measEnum.currentKey(), measEnum.currentValue()));
            first = false;
        }
        sb.Append('}');

        sb.Append('}');
        return sb.ToString();
    }
}
```

### Step 2: Create Telemetry Engine

```xpp
/// <summary>
/// Central telemetry engine - validates, enriches, queues events
/// </summary>
class LATelemetryEngine
{
    private LATelemetryConfig config;
    private List eventQueue;
    private int queueMaxSize = 100;

    public void new()
    {
        config = LATelemetryConfig::find();
        eventQueue = new List(Types::Class);
    }

    /// <summary>
    /// Track form opened event
    /// </summary>
    public void trackFormOpened(FormRun _formRun)
    {
        if (!this.isEnabled()) return;

        // Sampling
        if (!this.shouldSample()) return;

        LATelemetryEvent event = new LATelemetryEvent();
        event.parmEventName('FormOpened');
        event.parmTimestamp(DateTimeUtil::utcNow());

        // Properties
        event.addProperty('userId', this.getUserEmail());
        event.addProperty('formName', _formRun.name());
        event.addProperty('moduleName', this.getModuleName(_formRun));
        event.addProperty('roleNames', this.getUserRoles());
        event.addProperty('deviceType', this.getDeviceType());
        event.addProperty('sessionId', sessionId());
        event.addProperty('companyId', curext());

        // Measurements
        event.addMeasurement('loadTimeMs', this.getFormLoadTime(_formRun));

        this.queueEvent(event);
    }

    /// <summary>
    /// Track form action event (save, delete, post)
    /// </summary>
    public void trackFormAction(FormRun _formRun, str _actionName, str _actionType)
    {
        if (!this.isEnabled()) return;
        if (!this.shouldSample()) return;

        LATelemetryEvent event = new LATelemetryEvent();
        event.parmEventName('FormAction');
        event.parmTimestamp(DateTimeUtil::utcNow());

        event.addProperty('userId', this.getUserEmail());
        event.addProperty('formName', _formRun.name());
        event.addProperty('actionName', _actionName);
        event.addProperty('actionType', _actionType); // "Read" or "Write"
        event.addProperty('roleNames', this.getUserRoles());
        event.addProperty('sessionId', sessionId());
        event.addProperty('companyId', curext());

        this.queueEvent(event);
    }

    private boolean isEnabled()
    {
        return config && config.Enabled;
    }

    private boolean shouldSample()
    {
        // Random sampling based on SamplingRatePercent
        int randomPercent = Global::randomInt(1, 100);
        return randomPercent <= config.SamplingRatePercent;
    }

    private str getUserEmail()
    {
        UserInfo userInfo = UserInfo::find();
        return userInfo.networkAlias;  // Typically email in Azure AD-integrated D365
    }

    private str getUserRoles()
    {
        // Query SecurityUserRoleOrganization for current user
        SecurityUserRoleOrganization userRole;
        List roleList = new List(Types::String);

        while select SecurityRole from userRole
            where userRole.User == curUserId()
        {
            roleList.addEnd(userRole.SecurityRole);
        }

        // Join with comma
        return this.joinList(roleList, ',');
    }

    private str getDeviceType()
    {
        // Detect device type from session info
        // Simplified: Check user-agent or form factor
        return 'Desktop';  // TODO: Enhance with actual device detection
    }

    private void queueEvent(LATelemetryEvent _event)
    {
        eventQueue.addEnd(_event);

        // Flush queue if max size reached
        if (eventQueue.elements() >= queueMaxSize)
        {
            this.flushQueue();
        }
    }

    private void flushQueue()
    {
        if (eventQueue.elements() == 0) return;

        // Send events to Application Insights asynchronously
        LATelemetryEventBatch batch = new LATelemetryEventBatch();
        ListEnumerator enum = eventQueue.getEnumerator();

        while (enum.moveNext())
        {
            batch.addEvent(enum.current());
        }

        // Async send
        LATelemetryAsyncSender::send(batch);

        // Clear queue
        eventQueue = new List(Types::Class);
    }
}
```

### Step 3: Create Application Insights HTTP Sender

```xpp
/// <summary>
/// HTTP client for sending telemetry to Azure Application Insights
/// </summary>
class LAAppInsightsSender
{
    private str instrumentationKey;
    private str endpoint = 'https://dc.applicationinsights.azure.com/v2/track';

    public void new(str _instrumentationKey)
    {
        instrumentationKey = _instrumentationKey;
    }

    /// <summary>
    /// Send batch of events to Application Insights
    /// </summary>
    public boolean send(LATelemetryEventBatch _batch)
    {
        System.Net.Http.HttpClient httpClient;
        System.Net.Http.HttpRequestMessage request;
        System.Net.Http.HttpResponseMessage response;
        str jsonBody;
        boolean success = false;
        int retryCount = 0;
        int maxRetries = 3;

        try
        {
            httpClient = new System.Net.Http.HttpClient();

            // Build JSON body
            jsonBody = _batch.toJson();

            // Retry loop
            while (retryCount < maxRetries && !success)
            {
                request = new System.Net.Http.HttpRequestMessage(
                    System.Net.Http.HttpMethod::Post,
                    endpoint
                );

                request.Headers.Add('Content-Type', 'application/json');
                request.Content = new System.Net.Http.StringContent(jsonBody);

                response = httpClient.SendAsync(request).Result;

                if (response.IsSuccessStatusCode)
                {
                    success = true;
                }
                else
                {
                    retryCount++;
                    if (retryCount < maxRetries)
                    {
                        // Exponential backoff: 1s, 2s, 4s
                        sleep(1000 * System.Math::Pow(2, retryCount - 1));
                    }
                }
            }

            if (!success)
            {
                // Log failure
                this.logFailure(jsonBody);
            }
        }
        catch (Exception::CLRError)
        {
            error("Failed to send telemetry to Application Insights");
            this.logFailure(jsonBody);
        }

        return success;
    }

    private void logFailure(str _jsonBody)
    {
        // Fallback: Write to file log
        LATelemetryConfig config = LATelemetryConfig::find();
        if (config.LogFailuresToFile)
        {
            str logPath = @'C:\Temp\LATelemetryFailed.log';
            System.IO.File::AppendAllText(logPath, _jsonBody + '\n');
        }
    }
}
```

### Step 4: Create Chain-of-Command Extension on FormRun

```xpp
/// <summary>
/// Chain-of-Command extension on FormRun.init() to capture form opened events
/// </summary>
[ExtensionOf(formStr(FormRun))]
final class LATelemetryFormRunExtension
{
    public void init()
    {
        next init();

        // Capture form opened event
        LATelemetryEngine engine = new LATelemetryEngine();
        engine.trackFormOpened(this);
    }
}
```

**Note:** This extension applies globally to ALL forms. For performance, consider:
- **Filtering:** Only instrument high-value forms (Purch*, Sales*, Cust*, Vend*)
- **Sampling:** Use 10-20% sampling rate for high-volume environments

### Step 5: Create Batch Job for Queue Flushing

```xpp
/// <summary>
/// Batch job to flush telemetry queue every 5 minutes
/// </summary>
class LATelemetryQueueFlushBatch extends RunBaseBatch
{
    public boolean run()
    {
        LATelemetryEngine engine = new LATelemetryEngine();
        engine.flushQueue();
        return true;
    }

    public static void main(Args _args)
    {
        LATelemetryQueueFlushBatch batch = new LATelemetryQueueFlushBatch();
        if (batch.prompt())
        {
            batch.runOperation();
        }
    }
}
```

**Configure Batch Job:**

1. System Administration > Inquiries > Batch jobs
2. New batch job: `LATelemetryQueueFlush`
3. Recurrence: Every 5 minutes
4. Enable

---

## Testing & Validation

### Unit Testing (SysTest Framework)

```xpp
/// <summary>
/// Unit tests for telemetry engine
/// </summary>
class LATelemetryEngineTest extends SysTestCase
{
    public void testFormOpenedEventCreation()
    {
        // Arrange
        LATelemetryEngine engine = new LATelemetryEngine();
        FormRun mockFormRun = this.createMockFormRun('PurchTable');

        // Act
        engine.trackFormOpened(mockFormRun);

        // Assert
        this.assertEquals(1, engine.queueSize());
        LATelemetryEvent event = engine.peekQueue();
        this.assertEquals('FormOpened', event.parmEventName());
        this.assertEquals('PurchTable', event.getProperty('formName'));
    }

    public void testSamplingRate()
    {
        // Arrange
        LATelemetryConfig::find().SamplingRatePercent = 50;
        LATelemetryEngine engine = new LATelemetryEngine();
        int sampleCount = 0;

        // Act: Send 1000 events
        for (int i = 0; i < 1000; i++)
        {
            if (engine.shouldSample())
            {
                sampleCount++;
            }
        }

        // Assert: ~500 sampled (allow 10% variance)
        this.assertTrue(sampleCount >= 450 && sampleCount <= 550);
    }
}
```

### Integration Testing

**Test Scenario 1: Form Open → Event in App Insights**

1. Configure instrumentation key in LATelemetryConfig table
2. Open D365 FO form: `Procurement and sourcing > Purchase orders > All purchase orders`
3. Wait 30 seconds
4. Query Application Insights:
   ```kusto
   customEvents
   | where timestamp > ago(5m)
   | where name == "FormOpened"
   | where customDimensions.formName == "PurchTable"
   ```

Expected: 1 row returned with your user ID

**Test Scenario 2: Action Tracking (Write Operation)**

1. Open purchase order
2. Modify quantity field
3. Click **Save**
4. Query:
   ```kusto
   customEvents
   | where timestamp > ago(5m)
   | where name == "FormAction"
   | where customDimensions.actionType == "Write"
   ```

Expected: 1 row with actionName = "Save"

---

## Deployment

### Deployment to UAT Environment

1. **Build Model:**
   - Visual Studio > Build > Build Solution
   - Verify 0 errors

2. **Create Deployable Package:**
   - Dynamics 365 > Create deployable package
   - Select model: `LicenseAgentTelemetry`
   - Output: `LicenseAgentTelemetry.zip`

3. **Upload to LCS:**
   - LCS > Asset Library > Software deployable packages
   - Upload `LicenseAgentTelemetry.zip`

4. **Apply to UAT via LCS:**
   - Environment > Maintain > Apply updates
   - Select package: `LicenseAgentTelemetry`
   - Schedule maintenance window (requires environment downtime)

5. **Post-Deployment Configuration:**
   - Login to UAT D365 FO
   - Navigate to: System Administration > Setup > License Agent Telemetry Configuration
   - Enter Application Insights instrumentation key
   - Set Enabled = Yes, SamplingRatePercent = 100 (for testing)
   - Save

6. **Validate:**
   - Open any form
   - Check Application Insights for events within 5 minutes

### Deployment to Production

**Pre-Deployment Checklist:**

- [ ] UAT testing complete (minimum 7 days)
- [ ] Performance testing confirms < 5ms overhead
- [ ] Privacy review approved (no PII beyond user ID)
- [ ] Sampling rate set to 10-20% (not 100%)
- [ ] Fallback logging enabled (LogFailuresToFile = Yes)
- [ ] Rollback plan documented
- [ ] Stakeholder approval obtained

**Deployment Steps:**

Same as UAT, but:
- Schedule during low-usage window (Sunday 2 AM)
- Set SamplingRatePercent = 10 (not 100)
- Monitor Application Insights for 24 hours post-deployment
- If issues detected, disable telemetry: Set Enabled = No

---

## Performance Considerations

### Benchmarking Results (Expected)

| Metric | Target | Acceptable | Unacceptable |
|--------|--------|------------|--------------|
| Form Open Overhead | < 5ms | < 10ms | > 20ms |
| Memory per Event | < 500 bytes | < 1 KB | > 2 KB |
| Queue Size (steady state) | < 100 events | < 500 events | > 1000 events |
| HTTP Send Duration | < 200ms | < 500ms | > 1000ms |

### Optimization Techniques

1. **Sampling:** Use 10-20% in production (vs. 100% in dev/test)
2. **Batching:** Send events in batches of 100 (not individually)
3. **Async Sending:** Use SysOperation framework for background HTTP posts
4. **Form Filtering:** Only instrument high-value forms (skip setup/config forms)
5. **Lazy Initialization:** Don't create LATelemetryEngine if telemetry disabled

**Example: Form Filtering**

```xpp
private boolean shouldInstrumentForm(FormRun _formRun)
{
    str formName = _formRun.name();

    // Exclude low-value forms
    if (formName in ['SysTableBrowser', 'NumberSequenceTableListPage'])
    {
        return false;
    }

    // Include transactional forms
    if (formName like 'Purch*' || formName like 'Sales*' || formName like 'Cust*')
    {
        return true;
    }

    return false;
}
```

---

## Troubleshooting

### Issue: Events Not Appearing in Application Insights

**Diagnostic Steps:**

1. **Check Config:**
   ```xpp
   LATelemetryConfig::find().Enabled == true
   LATelemetryConfig::find().InstrumentationKey != ''
   ```

2. **Check Firewall:**
   - From D365 FO server, test connectivity:
     ```powershell
     Test-NetConnection -ComputerName dc.applicationinsights.azure.com -Port 443
     ```
   - Expected: `TcpTestSucceeded : True`

3. **Check Infolog for Errors:**
   - Open Infolog (System Administration > Inquiries > Infolog)
   - Search for: "Failed to send telemetry"

4. **Check Fallback Log File:**
   - If LogFailuresToFile = Yes, check: `C:\Temp\LATelemetryFailed.log`
   - Review JSON payloads for malformed data

---

**End of X++ Instrumentation Guide**
