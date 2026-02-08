/**
 * Database initialization script.
 * Creates SQLite database with schema from init.sql
 */
import Database from 'better-sqlite3';
import { readFileSync } from 'fs';
import { join } from 'path';

const DB_PATH = join(__dirname, '../data/license-agent.db');
const SCHEMA_PATH = join(__dirname, 'schema/init.sql');

console.log('🔧 Initializing D365 License Agent database...');
console.log(`📍 Database path: ${DB_PATH}`);

// Create database directory if it doesn't exist
const { mkdirSync } = require('fs');
const { dirname } = require('path');
try {
  mkdirSync(dirname(DB_PATH), { recursive: true });
} catch (err) {
  // Directory already exists
}

// Create/open database
const db = new Database(DB_PATH);

// Enable foreign keys
db.pragma('foreign_keys = ON');

// Read and execute schema
const schema = readFileSync(SCHEMA_PATH, 'utf-8');

console.log('📝 Executing schema...');
db.exec(schema);

console.log('✅ Database initialized successfully!');
console.log('\n📊 Tables created:');

const tables = db.prepare(`
  SELECT name FROM sqlite_master
  WHERE type='table' AND name NOT LIKE 'sqlite_%'
  ORDER BY name
`).all();

tables.forEach((table: any) => {
  const count = db.prepare(`SELECT COUNT(*) as count FROM ${table.name}`).get() as any;
  console.log(`   • ${table.name.padEnd(25)} (${count.count} rows)`);
});

db.close();

console.log('\n✅ Database ready at:', DB_PATH);
console.log('Next: Run `npm run db:seed` to load test data');
