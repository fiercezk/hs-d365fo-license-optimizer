-- ============================================================
-- D365 FO License Agent - Database Schema
-- SQLite Database for Local Development
-- Source: PRODUCTION_ARCHITECTURE.md Section 7
-- ============================================================

-- ============================================================
-- Core Tables
-- ============================================================

CREATE TABLE users (
    id TEXT PRIMARY KEY,                           -- email or user principal name
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    department TEXT,
    current_license TEXT NOT NULL,                  -- 'Team Members', 'Finance', etc.
    monthly_cost REAL NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,          -- SQLite boolean
    last_activity_at TEXT,                          -- ISO 8601
    roles_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_license ON users(current_license);
CREATE INDEX idx_users_active ON users(is_active);

-- ============================================================

CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    role_name TEXT NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, role_name)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_name);

-- ============================================================

CREATE TABLE user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    menu_item TEXT NOT NULL,                       -- AOT name
    action_type TEXT NOT NULL CHECK(action_type IN ('read', 'write', 'delete')),
    form_name TEXT,
    license_required TEXT,
    timestamp TEXT NOT NULL,                        -- ISO 8601
    session_id TEXT
);

CREATE INDEX idx_activity_user ON user_activity(user_id);
CREATE INDEX idx_activity_timestamp ON user_activity(timestamp);
CREATE INDEX idx_activity_action ON user_activity(action_type);

-- ============================================================

CREATE TABLE security_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL,
    menu_item TEXT NOT NULL,
    security_object TEXT,
    security_object_type TEXT,                      -- 'MenuItemDisplay', 'MenuItemAction', etc.
    license_required TEXT,
    entitlement_type TEXT,
    UNIQUE(role_name, menu_item, security_object)
);

CREATE INDEX idx_secconfig_role ON security_config(role_name);
CREATE INDEX idx_secconfig_menuitem ON security_config(menu_item);
CREATE INDEX idx_secconfig_license ON security_config(license_required);

-- ============================================================
-- Recommendation Workflow Tables
-- ============================================================

CREATE TABLE algorithm_runs (
    id TEXT PRIMARY KEY,                            -- UUID
    algorithm_id TEXT NOT NULL,                     -- '2.2', '2.5', '3.1', etc.
    algorithm_name TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'RUNNING'
        CHECK(status IN ('RUNNING', 'COMPLETED', 'FAILED')),
    users_processed INTEGER DEFAULT 0,
    recommendations_generated INTEGER DEFAULT 0,
    parameters TEXT                                 -- JSON string of algorithm parameters
);

CREATE INDEX idx_algo_runs_algorithm ON algorithm_runs(algorithm_id);
CREATE INDEX idx_algo_runs_status ON algorithm_runs(status);

-- ============================================================

CREATE TABLE recommendations (
    id TEXT PRIMARY KEY,                            -- 'REC-00001' format
    user_id TEXT NOT NULL REFERENCES users(id),
    algorithm_run_id TEXT REFERENCES algorithm_runs(id),
    algorithm_id TEXT NOT NULL,                     -- '2.2', '2.5', etc.
    type TEXT NOT NULL
        CHECK(type IN ('LICENSE_DOWNGRADE', 'LICENSE_UPGRADE', 'ROLE_REMOVAL',
                        'SOD_VIOLATION', 'SECURITY_ALERT', 'COST_OPTIMIZATION')),
    priority TEXT NOT NULL
        CHECK(priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    current_license TEXT NOT NULL,
    recommended_license TEXT,
    current_cost REAL NOT NULL,
    recommended_cost REAL,
    monthly_savings REAL NOT NULL DEFAULT 0,
    annual_savings REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'IMPLEMENTED', 'ROLLED_BACK')),
    details TEXT,                                   -- JSON: algorithm-specific data
    ai_explanation TEXT,                            -- Claude-generated explanation
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT                                 -- Recommendation validity window
);

CREATE INDEX idx_recs_user ON recommendations(user_id);
CREATE INDEX idx_recs_algorithm ON recommendations(algorithm_id);
CREATE INDEX idx_recs_status ON recommendations(status);
CREATE INDEX idx_recs_priority ON recommendations(priority);
CREATE INDEX idx_recs_savings ON recommendations(monthly_savings DESC);
CREATE INDEX idx_recs_created ON recommendations(created_at DESC);

-- ============================================================

CREATE TABLE recommendation_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT NOT NULL REFERENCES recommendations(id),
    action TEXT NOT NULL
        CHECK(action IN ('CREATED', 'APPROVED', 'REJECTED', 'IMPLEMENTED',
                          'ROLLED_BACK', 'EXPIRED', 'COMMENT')),
    actor TEXT NOT NULL,                            -- user email or 'system'
    comment TEXT,
    previous_status TEXT,
    new_status TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_audit_rec ON recommendation_audit(recommendation_id);
CREATE INDEX idx_audit_timestamp ON recommendation_audit(timestamp DESC);

-- ============================================================
-- Security Tables
-- ============================================================

CREATE TABLE security_alerts (
    id TEXT PRIMARY KEY,                            -- 'ALERT-00001' format
    type TEXT NOT NULL,                             -- 'SOD_VIOLATION', 'ANOMALOUS_ACCESS', etc.
    severity TEXT NOT NULL
        CHECK(severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    user_id TEXT NOT NULL REFERENCES users(id),
    description TEXT NOT NULL,
    details TEXT,                                   -- JSON: event-specific data
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK(status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED'))
);

CREATE INDEX idx_alerts_severity ON security_alerts(severity);
CREATE INDEX idx_alerts_type ON security_alerts(type);
CREATE INDEX idx_alerts_status ON security_alerts(status);
CREATE INDEX idx_alerts_detected ON security_alerts(detected_at DESC);

-- ============================================================

CREATE TABLE sod_violations (
    id TEXT PRIMARY KEY,                            -- 'SOD-00001' format
    user_id TEXT NOT NULL REFERENCES users(id),
    role_a TEXT NOT NULL,
    role_b TEXT NOT NULL,
    conflict_rule TEXT NOT NULL,                    -- Rule ID from SoD matrix
    severity TEXT NOT NULL
        CHECK(severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    category TEXT NOT NULL,                         -- 'financial', 'procurement', etc.
    description TEXT,
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK(status IN ('OPEN', 'MITIGATED', 'ACCEPTED', 'RESOLVED')),
    mitigation_notes TEXT
);

CREATE INDEX idx_sod_user ON sod_violations(user_id);
CREATE INDEX idx_sod_severity ON sod_violations(severity);
CREATE INDEX idx_sod_status ON sod_violations(status);

-- ============================================================
-- Configuration Tables
-- ============================================================

CREATE TABLE algorithm_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm_id TEXT NOT NULL,
    param_name TEXT NOT NULL,
    param_value TEXT NOT NULL,
    param_type TEXT NOT NULL DEFAULT 'string'
        CHECK(param_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_by TEXT NOT NULL DEFAULT 'system',
    UNIQUE(algorithm_id, param_name)
);

CREATE INDEX idx_algoconfig_algo ON algorithm_config(algorithm_id);

-- ============================================================
-- AI Explanation Cache
-- ============================================================

CREATE TABLE ai_explanations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,                      -- 'recommendation', 'user', 'sod_violation'
    entity_id TEXT NOT NULL,
    explanation TEXT NOT NULL,
    model_used TEXT NOT NULL DEFAULT 'claude-sonnet-4-5-20250514',
    tokens_used INTEGER,
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(entity_type, entity_id)
);

CREATE INDEX idx_explanations_entity ON ai_explanations(entity_type, entity_id);

-- ============================================================
-- Seed: Default Algorithm Configuration
-- ============================================================

INSERT INTO algorithm_config (algorithm_id, param_name, param_value, param_type, description) VALUES
    ('2.2', 'read_only_threshold', '0.95', 'number', 'Minimum read percentage to classify as read-only'),
    ('2.2', 'minimum_activity_days', '30', 'number', 'Minimum days of activity data required'),
    ('2.2', 'analysis_window_days', '90', 'number', 'Number of days to analyze'),
    ('2.5', 'minority_threshold', '0.15', 'number', 'Maximum usage percentage to classify as minority'),
    ('2.5', 'minimum_forms_accessed', '3', 'number', 'Minimum forms for meaningful analysis'),
    ('3.1', 'conflict_matrix_version', 'v1.0', 'string', 'SoD conflict matrix version'),
    ('3.2', 'anomaly_window_hours', '24', 'number', 'Time window for anomaly detection'),
    ('3.2', 'after_hours_start', '20', 'number', 'Start of after-hours period (24h format)'),
    ('3.2', 'after_hours_end', '6', 'number', 'End of after-hours period (24h format)'),
    ('3.3', 'creep_threshold_roles', '5', 'number', 'Role count threshold for privilege creep'),
    ('3.3', 'creep_review_months', '12', 'number', 'Months without review to flag'),
    ('4.1', 'min_users_per_device', '3', 'number', 'Minimum users sharing device for recommendation'),
    ('4.3', 'cross_app_overlap_threshold', '0.10', 'number', 'Minimum overlap percentage'),
    ('4.7', 'max_recommendations', '3', 'number', 'Maximum recommendations to return'),
    ('5.1', 'trend_months', '12', 'number', 'Months of trend data to analyze'),
    ('5.2', 'risk_weight_sod', '0.35', 'number', 'Weight for SoD violations in risk score'),
    ('5.2', 'risk_weight_privilege', '0.25', 'number', 'Weight for privilege creep in risk score'),
    ('5.2', 'risk_weight_anomaly', '0.25', 'number', 'Weight for anomalous activity'),
    ('5.2', 'risk_weight_orphaned', '0.15', 'number', 'Weight for orphaned account status');
