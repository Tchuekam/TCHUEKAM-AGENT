import sqlite3 from 'sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DB_PATH = process.env.DATABASE_PATH || path.join(__dirname, 'leads.db');

// Initialize Database connection
const db = new sqlite3.Database(DB_PATH);

// Helper to run queries using promises
export const query = (sql, params = []) => {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
};

export const run = (sql, params = []) => {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) reject(err);
      else resolve({ id: this.lastID, changes: this.changes });
    });
  });
};

// Initialize schema
export async function initDatabase() {
  await run(`
    CREATE TABLE IF NOT EXISTS leads (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      phone TEXT,
      email TEXT,
      website TEXT,
      source TEXT NOT NULL,
      category TEXT,
      location TEXT,
      rating REAL,
      date_scraped TEXT DEFAULT CURRENT_TIMESTAMP,
      contacted_status TEXT DEFAULT 'pending',
      priority_score INTEGER,
      message_template TEXT
    )
  `);

  // Create individual indices for fast lookup
  await run(`CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone)`);
  await run(`CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)`);
}

/**
 * Sanitizes phone/email strings to ensure uniform comparisons
 */
function cleanValue(val) {
  if (!val) return '';
  return val.trim().toLowerCase();
}

/**
 * Inserts a lead, applying robust multi-channel deduplication and field-merging.
 * If a lead exists with the same phone (non-empty) or email (non-empty), 
 * it updates and merges the existing lead instead of creating a duplicate.
 */
export async function upsertLead(lead) {
  const cleanedPhone = cleanValue(lead.phone);
  const cleanedEmail = cleanValue(lead.email);

  let existing = null;

  // 1. Search by phone
  if (cleanedPhone) {
    const rows = await query('SELECT * FROM leads WHERE phone = ?', [cleanedPhone]);
    if (rows && rows.length > 0) {
      existing = rows[0];
    }
  }

  // 2. Search by email (if not found by phone)
  if (!existing && cleanedEmail) {
    const rows = await query('SELECT * FROM leads WHERE email = ?', [cleanedEmail]);
    if (rows && rows.length > 0) {
      existing = rows[0];
    }
  }

  if (existing) {
    // Merge Strategy: Retain existing fields, overwrite if new data is richer/non-empty
    const mergedName = lead.name || existing.name;
    const mergedPhone = lead.phone || existing.phone;
    const mergedEmail = lead.email || existing.email;
    const mergedWebsite = lead.website || existing.website;
    const mergedCategory = lead.category || existing.category;
    const mergedLocation = lead.location || existing.location;
    const mergedRating = lead.rating !== undefined ? lead.rating : existing.rating;
    const mergedPriority = lead.priority_score !== undefined ? lead.priority_score : existing.priority_score;
    const mergedTemplate = lead.message_template || existing.message_template;
    
    // Retain source if it's already recorded, append new source if different
    let mergedSource = existing.source;
    if (lead.source && !existing.source.includes(lead.source)) {
      mergedSource = `${existing.source}, ${lead.source}`;
    }

    await run(
      `UPDATE leads SET 
        name = ?, phone = ?, email = ?, website = ?, source = ?, 
        category = ?, location = ?, rating = ?, priority_score = ?, message_template = ?
       WHERE id = ?`,
      [
        mergedName, mergedPhone, mergedEmail, mergedWebsite, mergedSource,
        mergedCategory, mergedLocation, mergedRating, mergedPriority, mergedTemplate,
        existing.id
      ]
    );
    return { status: 'merged', id: existing.id };
  } else {
    // Standard insert
    const res = await run(
      `INSERT INTO leads 
        (name, phone, email, website, source, category, location, rating, priority_score, message_template)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        lead.name, lead.phone || '', lead.email || '', lead.website || '',
        lead.source, lead.category || '', lead.location || '', lead.rating || null,
        lead.priority_score || 1, lead.message_template || ''
      ]
    );
    return { status: 'inserted', id: res.id };
  }
}

/**
 * Fetches all leads sorted by priority_score descending (High first)
 */
export async function getAllLeads(filter = {}) {
  let sql = 'SELECT * FROM leads';
  const params = [];
  const clauses = [];

  if (filter.source) {
    clauses.push('source LIKE ?');
    params.push(`%${filter.source}%`);
  }
  if (filter.category) {
    clauses.push('category LIKE ?');
    params.push(`%${filter.category}%`);
  }
  if (filter.location) {
    clauses.push('location LIKE ?');
    params.push(`%${filter.location}%`);
  }
  if (filter.priority) {
    clauses.push('priority_score = ?');
    params.push(parseInt(filter.priority));
  }

  if (clauses.length > 0) {
    sql += ' WHERE ' + clauses.join(' AND ');
  }

  sql += ' ORDER BY priority_score DESC, rating DESC, id DESC';
  return await query(sql, params);
}

/**
 * Returns the exact NEXUS queue format for messaging agent consumption
 */
export async function getNexusQueue() {
  const rows = await query('SELECT name, phone, email, message_template as intro_message_template, source, priority_score FROM leads ORDER BY priority_score DESC');
  return rows;
}

/**
 * Compiles the database contents into a properly-escaped CSV format string
 */
export async function generateLeadsCSV() {
  const leads = await query('SELECT * FROM leads ORDER BY priority_score DESC, id DESC');
  
  const headers = [
    'ID', 'Business Name', 'Phone', 'Email', 'Website', 
    'Source', 'Category', 'Location', 'Rating', 'Date Scraped', 
    'Contacted Status', 'Priority Score', 'Outreach Template'
  ];

  const escapeCSV = (val) => {
    if (val === null || val === undefined) return '';
    const str = String(val);
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const csvRows = [headers.join(',')];

  for (const lead of leads) {
    const row = [
      lead.id,
      escapeCSV(lead.name),
      escapeCSV(lead.phone),
      escapeCSV(lead.email),
      escapeCSV(lead.website),
      escapeCSV(lead.source),
      escapeCSV(lead.category),
      escapeCSV(lead.location),
      lead.rating || '',
      escapeCSV(lead.date_scraped),
      escapeCSV(lead.contacted_status),
      lead.priority_score,
      escapeCSV(lead.message_template)
    ];
    csvRows.push(row.join(','));
  }

  return csvRows.join('\r\n');
}
