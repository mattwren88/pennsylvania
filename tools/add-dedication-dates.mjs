#!/usr/bin/env node
/*
 * Adds dedication month/day to data/markers.json.
 *
 * markers.json was merged from the PHMC CSV export AND the live PHMC map
 * service — neither is a superset of the other — so this AUGMENTS the file in
 * place rather than rebuilding it from the CSV. Records the CSV doesn't cover
 * keep every field they already had and simply go without a `d`.
 *
 * Adds:  d: "MM-DD"   (only where the CSV gives a full date whose year agrees)
 *
 * Idempotent: re-running produces a byte-identical file.
 *
 *   node tools/add-dedication-dates.mjs
 */
import {readFileSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const JSON_PATH = join(root, 'data/markers.json');
const CSV_PATH = join(root, 'data/phmc-historical-markers.csv');

/* Minimal RFC-4180 reader: quoted fields, "" escapes, newlines inside quotes. */
function parseCsv(text) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else quoted = false;
      } else field += ch;
      continue;
    }
    if (ch === '"') quoted = true;
    else if (ch === ',') { row.push(field); field = ''; }
    else if (ch === '\r') { /* ignore, \n closes the row */ }
    else if (ch === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else field += ch;
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  return rows;
}

const csvRows = parseCsv(readFileSync(CSV_PATH, 'utf8'));
const header = csvRows.shift().map(h => h.trim());
const col = name => {
  const i = header.indexOf(name);
  if (i < 0) throw new Error(`CSV is missing the "${name}" column. Found: ${header.join(', ')}`);
  return i;
};
const iId = col('Historical Marker Number'), iDate = col('Date Dedicated');

/* id -> {mmdd, year}; a marker id appearing twice with conflicting dates is dropped. */
const dates = new Map(), conflicts = new Set();
let csvDated = 0, placeholder = 0;
for (const r of csvRows) {
  const id = (r[iId] || '').trim();
  const raw = (r[iDate] || '').trim();
  if (!id || !raw) continue;
  const m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(raw);
  if (!m) continue;
  const [, mo, da, yr] = m;
  const month = +mo, day = +da;
  if (month < 1 || month > 12 || day < 1 || day > 31) continue;
  /* 165 markers carry 01/01 — a stand-in for "year known, day unknown", not a
     mass New Year's Day dedication. Treat those as year-only. (First-of-month
     dates are also over-represented and probably part-placeholder, but not
     lopsidedly enough to throw away real dedications.) */
  if (month === 1 && day === 1) { placeholder++; continue; }
  csvDated++;
  const rec = {mmdd: String(month).padStart(2, '0') + '-' + String(day).padStart(2, '0'), year: +yr};
  const prev = dates.get(id);
  if (prev && (prev.mmdd !== rec.mmdd || prev.year !== rec.year)) conflicts.add(id);
  else dates.set(id, rec);
}
for (const id of conflicts) dates.delete(id);

const markers = JSON.parse(readFileSync(JSON_PATH, 'utf8'));
const before = markers.length;
let matched = 0, yearMismatch = 0, noId = 0, unmatched = 0;

for (const mk of markers) {
  delete mk.d;                                    // keeps the run idempotent
  if (!mk.id) { noId++; continue; }
  const rec = dates.get(mk.id);
  if (!rec) { unmatched++; continue; }
  /* The year already in markers.json is the trusted value; a disagreement means
     we matched the wrong thing, so leave that record alone. */
  if (mk.y != null && mk.y !== rec.year) { yearMismatch++; continue; }
  mk.d = rec.mmdd;
  matched++;
}

if (markers.length !== before) throw new Error('record count changed — aborting');
writeFileSync(JSON_PATH, JSON.stringify(markers) + '\n');

const pct = n => ((n / before) * 100).toFixed(1) + '%';
console.log(`markers.json      ${before} records (unchanged)`);
console.log(`CSV full dates    ${csvDated}${conflicts.size ? `  (${conflicts.size} id conflicts dropped)` : ''}`);
console.log(`01/01 placeholder ${placeholder} treated as year-only`);
console.log(`dated             ${matched}  ${pct(matched)}`);
console.log(`no CSV match      ${unmatched}`);
console.log(`year disagreed    ${yearMismatch}`);
console.log(`no id on record   ${noId}`);
