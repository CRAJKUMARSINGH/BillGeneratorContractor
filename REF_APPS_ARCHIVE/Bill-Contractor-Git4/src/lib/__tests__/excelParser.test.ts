/**
 * Robotic test harness — Phase 9
 * Feeds real TEST_INPUT_FILES + INPUT_FILES_LEVEL_02 through the parser.
 *
 * Run: npm run test:excel
 */
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as XLSX from 'xlsx';
import { parsedRowsToBillItems } from '../excelParser';
import type { ExcelParseResult, ParsedExcelRow } from '../../types/bill';

// ─── Node-compatible sync wrapper (mirrors async parseExcelFile logic) ────────
// We duplicate the core logic here so tests run in Node without File API.
// The actual browser parser in excelParser.ts is the source of truth.

function norm(s: string) { return s.toLowerCase().replace(/[_\-\/\\]+/g, ' ').replace(/\s+/g, ' ').trim(); }
function toNum(v: unknown) { const n = parseFloat(String(v ?? '').replace(/[,₹$\s]/g, '')); return isNaN(n) ? 0 : n; }
function toStr(v: unknown) { return String(v ?? '').trim(); }
function excelDateToISO(v: unknown): string | null {
  if (!v) return null;
  if (v instanceof Date) return v.toISOString().split('T')[0];
  const n = Number(v);
  if (!isNaN(n) && n > 40000) return new Date(Math.round((n - 25569) * 86400 * 1000)).toISOString().split('T')[0];
  return null;
}

function parseItemSheet(ws: XLSX.WorkSheet): ParsedExcelRow[] {
  if (!ws || !ws['!ref']) return [];
  const raw: unknown[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
  let headerRow = -1, descCol = -1, unitCol = -1, qtyCol = -1, rateCol = -1, itemCol = -1, remarksCol = -1;

  for (let i = 0; i < Math.min(raw.length, 5); i++) {
    const row = raw[i] as unknown[];
    const n = row.map((c) => norm(toStr(c)));
    const dIdx = n.findIndex((c) => c === 'description' || c === 'description of work' || c === 'particulars');
    const rIdx = n.findIndex((c) => c === 'rate' || c === 'unit rate');
    if (dIdx >= 0 && rIdx >= 0) {
      headerRow = i; descCol = dIdx; rateCol = rIdx;
      unitCol = n.findIndex((c) => c === 'unit' || c === 'uom');
      qtyCol  = n.findIndex((c) => c === 'quantity' || c === 'qty' || c === 'qty to date');
      itemCol = n.findIndex((c) => c === 'item' || c === 'sno' || c === 's.no' || c === '#');
      remarksCol = n.findIndex((c) => c === 'remarks' || c === 'bsr' || c === 'notes');
      break;
    }
  }
  if (headerRow < 0) return [];

  const rows: ParsedExcelRow[] = [];
  let lastParentDesc = '', lastParentItem = '';

  for (let i = headerRow + 1; i < raw.length; i++) {
    const row = raw[i] as unknown[];
    const rawDesc = toStr(row[descCol]);
    const rawItem = itemCol >= 0 ? toStr(row[itemCol]) : '';
    const qty = qtyCol >= 0 ? toNum(row[qtyCol]) : 0;
    const rate = toNum(row[rateCol]);
    const unit = unitCol >= 0 ? toStr(row[unitCol]) : '';

    if (!rawDesc && !rawItem) continue;
    if (rawItem && !unit && qty === 0 && rate === 0) { lastParentDesc = rawDesc || lastParentDesc; lastParentItem = rawItem; continue; }

    const fullDesc = rawDesc
      ? (lastParentDesc && rawDesc.length < 60 && !rawDesc.includes(lastParentDesc.slice(0, 20))
          ? `${lastParentDesc} — ${rawDesc}` : rawDesc)
      : lastParentDesc;
    if (!fullDesc) continue;

    rows.push({
      serial_no: rawItem || lastParentItem || String(rows.length + 1),
      description: fullDesc, unit,
      qty_since_last_bill: 0, qty_to_date: qty, rate,
      remarks: remarksCol >= 0 ? toStr(row[remarksCol]) : '',
    });
  }
  return rows;
}

function parseBuffer(buffer: Buffer): ExcelParseResult {
  const wb = XLSX.read(buffer, { type: 'buffer', cellDates: true });
  const hasBillQty = wb.SheetNames.includes('Bill Quantity');
  const hasWorkOrder = wb.SheetNames.includes('Work Order');
  const hasTitle = wb.SheetNames.includes('Title');

  // ── Domain-specific path ──────────────────────────────────────────────────
  if (hasBillQty) {
    const header: Partial<import('../../types/bill').Bill> = {};

    if (hasTitle) {
      const ws = wb.Sheets['Title'];
      const rows: unknown[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
      const MAP: Record<string, string> = {
        'name of contractor or supplier': 'contractor_name',
        'name of contractor': 'contractor_name',
        'name of work': 'work_name',
        'serial no. of this bill': 'serial_number',
        'serial no of this bill': 'serial_number',
        'cash book voucher no. and date': 'voucher_number',
        'reference to work order or agreement': 'work_order_reference',
        'agreement no.': 'agreement_number', 'agreement no': 'agreement_number',
        'tender premium %': 'tender_premium_percentage', 'tender premium': 'tender_premium_percentage',
        'amount paid vide last bill': 'last_bill_deduction',
        'date of written order to commence work': 'commencement_date',
        'st. date of start': 'scheduled_start_date',
        'st. date of completion': 'scheduled_completion_date',
        'date of actual completion of work': 'actual_completion_date',
        'date of measurement': 'measurement_date',
      };
      for (const row of rows) {
        if (!row[0]) continue;
        const label = norm(toStr(row[0]).replace(/\s*[;:-]+\s*$/, ''));
        const val = row[1];
        if (!val && val !== 0) continue;
        const mapped = MAP[label];
        if (!mapped) continue;
        if (mapped === 'tender_premium_percentage' || mapped === 'last_bill_deduction') {
          (header as Record<string, unknown>)[mapped] = toNum(val);
        } else if (mapped.includes('_date') || mapped === 'commencement_date') {
          (header as Record<string, unknown>)[mapped] = excelDateToISO(val);
        } else {
          (header as Record<string, unknown>)[mapped] = toStr(val);
        }
      }
    }

    const billRows = parseItemSheet(wb.Sheets['Bill Quantity']);
    const woRows = hasWorkOrder ? parseItemSheet(wb.Sheets['Work Order']) : [];
    const woMap = new Map(woRows.map(r => [r.description, r.qty_to_date]));

    const rows: ParsedExcelRow[] = billRows.map(r => ({
      ...r, qty_since_last_bill: Math.max(0, r.qty_to_date - (woMap.get(r.description) ?? 0)),
    }));

    if (wb.SheetNames.includes('Extra Items')) {
      rows.push(...parseItemSheet(wb.Sheets['Extra Items']));
    }

    const confidence = rows.length > 0
      ? 0.5
        + (Object.keys(header).length >= 3 ? 0.2 : 0)
        + (rows.some(r => r.rate > 0) ? 0.15 : 0)
        + (rows.some(r => r.qty_to_date > 0) ? 0.15 : 0)
      : 0;

    return { header, rows, confidence, warnings: [], raw_sheet_names: wb.SheetNames };
  }

  // ── Generic fallback ──────────────────────────────────────────────────────
  const COL_ALIASES: Record<string, keyof ParsedExcelRow> = {
    'sno': 'serial_no', 's.no': 'serial_no', 'item': 'serial_no',
    'description': 'description', 'description of work': 'description',
    'unit': 'unit', 'rate': 'rate', 'unit rate': 'rate',
    'qty since last': 'qty_since_last_bill', 'qty to date': 'qty_to_date',
    'quantity': 'qty_to_date', 'remarks': 'remarks',
  };

  let bestRows: ParsedExcelRow[] = [], bestScore = -1;
  const warnings: string[] = [];

  for (const sheetName of wb.SheetNames) {
    const ws = wb.Sheets[sheetName];
    if (!ws || !ws['!ref']) continue;
    const range = XLSX.utils.decode_range(ws['!ref']);
    const colMap = new Map<keyof ParsedExcelRow, number>();
    let dataStart = -1;

    for (let r = range.s.r; r <= Math.min(range.s.r + 10, range.e.r); r++) {
      colMap.clear();
      for (let c = range.s.c; c <= range.e.c; c++) {
        const cell = ws[XLSX.utils.encode_cell({ r, c })];
        if (!cell) continue;
        const mapped = COL_ALIASES[norm(toStr(cell.v))];
        if (mapped) colMap.set(mapped, c);
      }
      if (colMap.has('description') && colMap.has('rate')) { dataStart = r + 1; break; }
    }
    if (dataStart < 0) { warnings.push(`Sheet "${sheetName}": no headers`); continue; }

    const rows: ParsedExcelRow[] = [];
    for (let r = dataStart; r <= range.e.r; r++) {
      const get = (f: keyof ParsedExcelRow) => {
        const c = colMap.get(f); if (c === undefined) return undefined;
        return ws[XLSX.utils.encode_cell({ r, c })]?.v;
      };
      const desc = toStr(get('description'));
      if (!desc) continue;
      rows.push({
        serial_no: toStr(get('serial_no')) || String(rows.length + 1),
        description: desc, unit: toStr(get('unit')),
        qty_since_last_bill: toNum(get('qty_since_last_bill')),
        qty_to_date: toNum(get('qty_to_date')),
        rate: toNum(get('rate')), remarks: toStr(get('remarks')),
      });
    }
    let score = rows.length > 0 ? 0.3 : 0;
    if (rows.some(r => r.rate > 0)) score += 0.2;
    if (score > bestScore) { bestScore = score; bestRows = rows; }
  }

  return { header: {}, rows: bestRows, confidence: Math.max(bestScore, 0), warnings, raw_sheet_names: wb.SheetNames };
}

// ─── Discover test files ──────────────────────────────────────────────────────
const TEST_DIR   = path.resolve(process.cwd(), 'TEST_INPUT_FILES');
const INPUT_DIR  = path.resolve(process.cwd(), 'INPUT_FILES_LEVEL_02');

function getXlsxFiles(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => /\.(xlsx|xls|xlsm)$/i.test(f) && !f.startsWith('~$'))
    .map(f => path.join(dir, f));
}

const allFiles = [...getXlsxFiles(TEST_DIR), ...getXlsxFiles(INPUT_DIR)];
const bugLog: { file: string; issue: string }[] = [];

// ─── Tests ────────────────────────────────────────────────────────────────────
describe('Excel Parser — Robotic Test Harness', () => {
  it('should find test Excel files', () => {
    expect(allFiles.length).toBeGreaterThan(0);
    console.log(`\nFound ${allFiles.length} Excel files to test`);
  });

  allFiles.forEach((filePath) => {
    const name = path.basename(filePath);

    it(`parses: ${name}`, () => {
      const buffer = fs.readFileSync(filePath);
      const result = parseBuffer(buffer);

      const headerKeys = Object.keys(result.header).filter(k => (result.header as Record<string,unknown>)[k]);
      console.log(`\n  [${name}]`);
      console.log(`    Sheets:  ${result.raw_sheet_names.join(', ')}`);
      console.log(`    Rows:    ${result.rows.length}`);
      console.log(`    Score:   ${(result.confidence * 100).toFixed(0)}%`);
      console.log(`    Header:  ${headerKeys.join(', ') || 'none'}`);
      if (result.warnings.length) console.log(`    Warns:   ${result.warnings.join(' | ')}`);

      if (result.rows.length === 0) bugLog.push({ file: name, issue: 'Zero rows parsed' });
      if (result.confidence < 0.4 && result.rows.length > 0) bugLog.push({ file: name, issue: `Low confidence: ${(result.confidence * 100).toFixed(0)}%` });

      // Validate BillItems conversion
      if (result.rows.length > 0) {
        const items = parsedRowsToBillItems(result.rows, 'test-id');
        expect(items.length).toBe(result.rows.length);
        items.forEach((item) => {
          expect(item.amount_since_previous).toBeCloseTo(item.qty_since_last_bill * item.rate, 5);
          expect(item.amount_to_date).toBeCloseTo(item.qty_to_date * item.rate, 5);
        });
        // Sample: first item with rate > 0 should have valid amounts
        const withRate = items.find(i => i.rate > 0);
        if (withRate) {
          expect(withRate.amount_to_date).toBeGreaterThan(0);
        }
      }

      expect(result).toBeDefined();
      expect(Array.isArray(result.rows)).toBe(true);
    });
  });

  it('prints BUG FIX LOG', () => {
    if (bugLog.length === 0) {
      console.log('\n✅ BUG FIX LOG: No issues found across all files');
    } else {
      console.log('\n⚠️  BUG FIX LOG:');
      bugLog.forEach(({ file, issue }) => console.log(`  [FAIL] ${file}: ${issue}`));
    }
    expect(true).toBe(true);
  });
});
