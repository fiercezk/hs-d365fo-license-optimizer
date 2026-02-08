/**
 * SQLite database connection singleton.
 */
import Database from 'better-sqlite3';
import { join } from 'path';

const DB_PATH = process.env.DB_PATH || join(__dirname, '../../data/license-agent.db');

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('foreign_keys = ON');
    db.pragma('journal_mode = WAL'); // Better concurrency
  }
  return db;
}

export function closeDb(): void {
  if (db) {
    db.close();
    db = null;
  }
}
