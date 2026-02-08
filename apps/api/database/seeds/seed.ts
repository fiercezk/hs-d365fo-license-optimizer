/**
 * Seed database with realistic test data.
 * Creates 100+ users, 50+ recommendations, 1000+ activity records.
 */
import Database from 'better-sqlite3';
import { join } from 'path';

const DB_PATH = join(__dirname, '../../data/license-agent.db');

console.log('🌱 Seeding database with test data...\n');

const db = new Database(DB_PATH);
db.pragma('foreign_keys = ON');

// Helper to generate random date within last N days
const randomDate = (daysAgo: number) => {
  const date = new Date();
  date.setDate(date.getDate() - Math.floor(Math.random() * daysAgo));
  return date.toISOString();
};

// Helper to pick random element from array
const randomPick = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

// ============================================================
// 1. Users (100 users)
// ============================================================
console.log('👥 Creating users...');

const departments = ['Finance', 'Sales', 'IT', 'HR', 'Operations', 'Procurement', 'Manufacturing'];
const licenses = ['Team Members', 'Operations', 'Finance', 'Supply Chain Management', 'Commerce'];
const licenseCosts: Record<string, number> = {
  'Team Members': 60,
  'Operations': 90,
  'Finance': 180,
  'Supply Chain Management': 180,
  'Commerce': 180,
};

const users: string[] = [];
const insertUser = db.prepare(`
  INSERT INTO users (id, email, display_name, department, current_license, monthly_cost, is_active, last_activity_at, roles_count)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

for (let i = 1; i <= 100; i++) {
  const id = `user${i}@contoso.com`;
  const name = `User ${i}`;
  const dept = randomPick(departments);
  const license = randomPick(licenses);
  const cost = licenseCosts[license];
  const isActive = i <= 95 ? 1 : 0; // 95% active
  const lastActivity = isActive ? randomDate(30) : null;
  const rolesCount = Math.floor(Math.random() * 8) + 1;

  insertUser.run(id, id, name, dept, license, cost, isActive, lastActivity, rolesCount);
  users.push(id);
}

console.log(`✅ Created ${users.length} users`);

// ============================================================
// 2. User Roles (200+ roles)
// ============================================================
console.log('🔑 Assigning user roles...');

const roles = [
  'Accounts Payable Clerk',
  'Accounts Receivable Clerk',
  'Vendor Master',
  'Customer Master',
  'General Ledger Accountant',
  'Inventory Manager',
  'Purchasing Agent',
  'Sales Representative',
  'Warehouse Worker',
  'Production Planner',
];

const insertRole = db.prepare(`
  INSERT INTO user_roles (user_id, role_name, assigned_at, is_active)
  VALUES (?, ?, ?, ?)
`);

let roleCount = 0;
for (const userId of users.slice(0, 80)) {
  const numRoles = Math.floor(Math.random() * 5) + 1;
  const userRoles = [];
  while (userRoles.length < numRoles) {
    const role = randomPick(roles);
    if (!userRoles.includes(role)) {
      userRoles.push(role);
      insertRole.run(userId, role, randomDate(365), 1);
      roleCount++;
    }
  }
}

console.log(`✅ Assigned ${roleCount} roles`);

// ============================================================
// 3. User Activity (1000+ records)
// ============================================================
console.log('📊 Generating activity logs...');

const menuItems = [
  'VendInvoice', 'VendTable', 'CustTable', 'SalesTable', 'PurchTable',
  'InventTable', 'LedgerJournal', 'BankAccounts', 'ProjTable', 'WHSWork'
];
const actionTypes = ['read', 'write', 'delete'];
const forms = [
  'VendInvoiceJournal', 'VendEditInvoice', 'CustInvoiceJournal', 'SalesTableListPage',
  'PurchTableListPage', 'InventItemListPage', 'LedgerJournalTable'
];

const insertActivity = db.prepare(`
  INSERT INTO user_activity (user_id, menu_item, action_type, form_name, license_required, timestamp)
  VALUES (?, ?, ?, ?, ?, ?)
`);

for (let i = 0; i < 1200; i++) {
  const userId = randomPick(users.slice(0, 80));
  const menuItem = randomPick(menuItems);
  const actionType = randomPick(actionTypes);
  const formName = randomPick(forms);
  const license = actionType === 'write' ? 'Operations' : randomPick(['Team Members', 'Operations']);
  const timestamp = randomDate(90);

  insertActivity.run(userId, menuItem, actionType, formName, license, timestamp);
}

console.log('✅ Generated 1200 activity records');

// ============================================================
// 4. Security Config (150+ records)
// ============================================================
console.log('🔒 Creating security configuration...');

const insertSecConfig = db.prepare(`
  INSERT INTO security_config (role_name, menu_item, security_object, security_object_type, license_required, entitlement_type)
  VALUES (?, ?, ?, ?, ?, ?)
`);

let secConfigCount = 0;
for (const role of roles) {
  for (const menuItem of menuItems) {
    insertSecConfig.run(role, menuItem, menuItem, 'MenuItemDisplay', randomPick(licenses), 'View');
    secConfigCount++;
  }
}

console.log(`✅ Created ${secConfigCount} security config records`);

// ============================================================
// 5. Algorithm Run + Recommendations (50 recommendations)
// ============================================================
console.log('💡 Creating recommendations...');

const insertAlgoRun = db.prepare(`
  INSERT INTO algorithm_runs (id, algorithm_id, algorithm_name, started_at, completed_at, status, users_processed, recommendations_generated)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

const runId = 'run-001';
insertAlgoRun.run(
  runId, '2.2', 'Read-Only User Detection',
  randomDate(7), randomDate(7), 'COMPLETED',
  100, 50
);

const insertRec = db.prepare(`
  INSERT INTO recommendations (id, user_id, algorithm_run_id, algorithm_id, type, priority, confidence, current_license, recommended_license, current_cost, recommended_cost, monthly_savings, annual_savings, status, details, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

for (let i = 1; i <= 50; i++) {
  const recId = `REC-${String(i).padStart(5, '0')}`;
  const userId = randomPick(users.slice(0, 80));
  const algorithmId = randomPick(['2.2', '2.5', '3.1', '4.3']);
  const type = randomPick(['LICENSE_DOWNGRADE', 'LICENSE_UPGRADE', 'COST_OPTIMIZATION', 'SOD_VIOLATION']);
  const priority = randomPick(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']);
  const confidence = 0.7 + Math.random() * 0.3; // 0.7-1.0
  const currentLicense = 'Operations';
  const recommendedLicense = 'Team Members';
  const currentCost = 90;
  const recommendedCost = 60;
  const monthlySavings = 30;
  const annualSavings = 360;
  const status = randomPick(['PENDING', 'PENDING', 'PENDING', 'APPROVED', 'REJECTED']); // Most pending
  const details = JSON.stringify({ readPercentage: 0.95, writePercentage: 0.05 });
  const createdAt = randomDate(14);

  insertRec.run(
    recId, userId, runId, algorithmId, type, priority, confidence,
    currentLicense, recommendedLicense, currentCost, recommendedCost,
    monthlySavings, annualSavings, status, details, createdAt
  );
}

console.log('✅ Created 50 recommendations');

// ============================================================
// 6. Security Alerts (10 alerts)
// ============================================================
console.log('⚠️  Creating security alerts...');

const insertAlert = db.prepare(`
  INSERT INTO security_alerts (id, type, severity, user_id, description, detected_at, status)
  VALUES (?, ?, ?, ?, ?, ?, ?)
`);

const alertTypes = ['SOD_VIOLATION', 'ANOMALOUS_ACCESS', 'PRIVILEGE_CREEP', 'AFTER_HOURS_ACCESS'];

for (let i = 1; i <= 10; i++) {
  const alertId = `ALERT-${String(i).padStart(5, '0')}`;
  const type = randomPick(alertTypes);
  const severity = randomPick(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']);
  const userId = randomPick(users.slice(0, 50));
  const description = `${type} detected for ${userId}`;
  const detectedAt = randomDate(30);
  const status = i <= 7 ? 'OPEN' : 'RESOLVED';

  insertAlert.run(alertId, type, severity, userId, description, detectedAt, status);
}

console.log('✅ Created 10 security alerts');

// ============================================================
// 7. SoD Violations (5 violations)
// ============================================================
console.log('🚫 Creating SoD violations...');

const insertSod = db.prepare(`
  INSERT INTO sod_violations (id, user_id, role_a, role_b, conflict_rule, severity, category, description, detected_at, status)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

const sodPairs = [
  ['Accounts Payable Clerk', 'Vendor Master', 'financial', 'Can create vendors and process payments'],
  ['Purchasing Agent', 'Accounts Payable Clerk', 'procurement', 'Can create POs and approve payments'],
  ['General Ledger Accountant', 'Accounts Receivable Clerk', 'financial', 'Can post GL and manage AR'],
];

for (let i = 1; i <= 5; i++) {
  const sodId = `SOD-${String(i).padStart(5, '0')}`;
  const userId = randomPick(users.slice(0, 30));
  const [roleA, roleB, category, description] = randomPick(sodPairs);
  const conflictRule = `CR-${i}`;
  const severity = randomPick(['CRITICAL', 'HIGH', 'MEDIUM']);
  const detectedAt = randomDate(60);
  const status = i <= 3 ? 'OPEN' : 'MITIGATED';

  insertSod.run(sodId, userId, roleA, roleB, conflictRule, severity, category, description, detectedAt, status);
}

console.log('✅ Created 5 SoD violations');

// ============================================================
// Summary
// ============================================================
db.close();

console.log('\n📊 Seed Summary:');
console.log('   • 100 users');
console.log('   • 200+ user roles');
console.log('   • 1200 activity records');
console.log('   • 150+ security config records');
console.log('   • 50 recommendations');
console.log('   • 10 security alerts');
console.log('   • 5 SoD violations');
console.log('   • 19 algorithm config defaults');
console.log('\n✅ Database seeded successfully!');
console.log('Next: Run `npm run dev` to start the API server');
