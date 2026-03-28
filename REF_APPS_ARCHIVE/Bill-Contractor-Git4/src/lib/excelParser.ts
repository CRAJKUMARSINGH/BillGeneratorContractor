import * as XLSX from 'xlsx';
import type { Bill, BillItem, ExcelParseResult, ParsedExcelRow } from '../types/bill';

// ─── Generic column aliases (fallback for unknown formats) ───────────────────
const COL_ALIASES: Record<string, keyof ParsedExcelRow> = {
  'sno': 'serial_no', 's.no': 'serial_no', 'sr': 'serial_no', 'sr.no': 'serial_no',
  'serial': 'serial_no', 'serial no': 'serial_no', 'serial_no': 'serial_no',
  '#': 'serial_no', 'item': 'serial_no',
  'description': 'description', 'desc': 'description',
  'description of work': 'description', 'particulars': 'description',
  'name': 'description', 'details': 'description',
  'unit': 'unit', 'uom': 'unit', 'units': 'unit',
  'qty since last': 'qty_since_last_bill', 'qty since last bill': 'qty_since_last_bill',
  'quantity since last': 'qty_since_last_bill', 'qty_since_last_bill': 'qty_since_last_bill',
  'since last': 'qty_since_last_bill', 'incremental qty': 'qty_since_last_bill',
  'qty to date': 'qty_to_date', 'quantity to date': 'qty_to_date', 'qty_to_date': 'qty_to_date',
  'cumulative qty': 'qty_to_date', 'total qty': 'qty_to_date',
  'rate': 'rate', 'unit rate': 'rate', 'unit price': 'rate', 'price': 'rate',
  'remarks': 'remarks', 'remark': 'remarks', 'notes': 'remarks',
};

function norm(s: string): string {
  return s.toLowerCase().replace(/[_\-\/\\]+/g, ' ').replace(/\s+/g, ' ').trim();
}
function toNum(v: unknown): number {
  if (v === null || v === undefined || v === '') return 0;
  const n = parseFloat(String(v).replace(/[,₹$\s]/g, ''));
  return isNaN(n) ? 0 : n;
}
function toStr(v: unknown): string {
  return String(v ?? '').trim();
}
function excelDateToISO(v: unknown): string | null {
  if (!v) return null;
  if (v instanceof Date) return v.toISOString().split('T')[0];
  const n = Number(v);
  if (!isNaN(n) && n > 40000) {
    // Excel serial date
    const d = new Date(Math.round((n - 25569) * 86400 * 1000));
    return d.toISOString().split('T')[0];
  }
  const s = String(v).trim();
  if (s.match(/^\d{4}-\d{2}-\d{2}$/)) return s;
  return null;
}

// ─── DOMAIN-SPECIFIC: Parse the known 4-sheet contractor bill format ──────────
// Sheets: Title (metadata), Work Order (agreement qty), Bill Quantity (current qty), Extra Items
function parseDomainFormat(wb: XLSX.WorkBook): {
  header: Partial<Bill>;
  rows: ParsedExcelRow[];
  confidence: number;
} | null {
  const hasTitle = wb.SheetNames.includes('Title');
  const hasBillQty = wb.SheetNames.includes('Bill Quantity');
  const hasWorkOrder = wb.SheetNames.includes('Work Order');

  if (!hasBillQty) return null;

  // ── 1. Extract header from Title sheet ──────────────────────────────────────
  const header: Partial<Bill> = {};
  if (hasTitle) {
    const ws = wb.Sheets['Title'];
    const rows: unknown[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });

    const TITLE_MAP: Record<string, keyof Bill> = {
      'name of contractor or supplier':  'contractor_name',
      'name of contractor':              'contractor_name',
      'contractor':                      'contractor_name',
      'name of work':                    'work_name',
      'serial no. of this bill':         'serial_number',
      'serial no of this bill':          'serial_number',
      'cash book voucher no. and date':  'voucher_number',
      'cash book voucher no':            'voucher_number',
      'reference to work order or agreement': 'work_order_reference',
      'agreement no.':                   'agreement_number',
      'agreement no':                    'agreement_number',
      'tender premium %':                'tender_premium_percentage',
      'tender premium':                  'tender_premium_percentage',
      'amount paid vide last bill':      'last_bill_deduction',
      'date of written order to commence work': 'commencement_date',
      'st. date of start':               'scheduled_start_date',
      'st. date of completion':          'scheduled_completion_date',
      'date of actual completion of work': 'actual_completion_date',
      'date of measurement':             'measurement_date',
    };

    for (const row of rows) {
      if (!row[0]) continue;
      const label = norm(toStr(row[0]).replace(/\s*:\s*$/, '').replace(/\s*;-\s*$/, ''));
      const val = row[1];
      if (!val && val !== 0) continue;

      const mapped = TITLE_MAP[label];
      if (!mapped) continue;

      if (mapped === 'tender_premium_percentage' || mapped === 'last_bill_deduction') {
        (header as Record<string, unknown>)[mapped] = toNum(val);
      } else if (['commencement_date', 'scheduled_start_date', 'scheduled_completion_date',
                  'actual_completion_date', 'measurement_date'].includes(mapped)) {
        (header as Record<string, unknown>)[mapped] = excelDateToISO(val);
      } else {
        (header as Record<string, unknown>)[mapped] = toStr(val);
      }
    }
  }

  // ── 2. Parse Bill Quantity sheet (current bill quantities) ──────────────────
  const billQtyRows = parseItemSheet(wb.Sheets['Bill Quantity']);

  // ── 3. Parse Work Order sheet (agreement quantities) for qty_since_last_bill ─
  const workOrderRows = hasWorkOrder ? parseItemSheet(wb.Sheets['Work Order']) : [];

  // Build a lookup: description → work order qty
  const woQtyMap = new Map<string, number>();
  for (const r of workOrderRows) {
    woQtyMap.set(r.description, r.qty_to_date);
  }

  // ── 4. Merge: qty_since_last_bill = bill_qty - work_order_qty (if positive) ─
  const rows: ParsedExcelRow[] = billQtyRows.map((r) => {
    const woQty = woQtyMap.get(r.description) ?? 0;
    const qtySinceLast = Math.max(0, r.qty_to_date - woQty);
    return { ...r, qty_since_last_bill: qtySinceLast };
  });

  // ── 5. Also parse Extra Items sheet if present ──────────────────────────────
  if (wb.SheetNames.includes('Extra Items')) {
    const extraRows = parseItemSheet(wb.Sheets['Extra Items']);
    rows.push(...extraRows);
  }

  const confidence = rows.length > 0
    ? 0.5
      + (Object.keys(header).length >= 3 ? 0.2 : 0)
      + (rows.some(r => r.rate > 0) ? 0.15 : 0)
      + (rows.some(r => r.qty_to_date > 0) ? 0.15 : 0)
    : 0;

  return { header, rows, confidence };
}

// ─── Parse a standard item sheet (Item/Description/Unit/Quantity/Rate/Amount) ─
function parseItemSheet(ws: XLSX.WorkSheet): ParsedExcelRow[] {
  if (!ws || !ws['!ref']) return [];
  const raw: unknown[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
  if (raw.length === 0) return [];

  // Find header row
  let headerRow = -1;
  let descCol = -1, unitCol = -1, qtyCol = -1, rateCol = -1, itemCol = -1, remarksCol = -1;

  for (let i = 0; i < Math.min(raw.length, 5); i++) {
    const row = raw[i] as unknown[];
    const normalized = row.map((c) => norm(toStr(c)));
    const dIdx = normalized.findIndex((c) =>
      c === 'description' || c === 'description of work' || c === 'particulars'
    );
    const rIdx = normalized.findIndex((c) => c === 'rate' || c === 'unit rate');
    if (dIdx >= 0 && rIdx >= 0) {
      headerRow = i;
      descCol = dIdx;
      rateCol = rIdx;
      unitCol = normalized.findIndex((c) => c === 'unit' || c === 'uom');
      qtyCol  = normalized.findIndex((c) =>
        c === 'quantity' || c === 'qty' || c === 'qty to date' || c === 'qty_to_date'
      );
      itemCol = normalized.findIndex((c) =>
        c === 'item' || c === 'sno' || c === 's.no' || c === '#'
      );
      remarksCol = normalized.findIndex((c) => c === 'remarks' || c === 'bsr' || c === 'notes');
      break;
    }
  }

  if (headerRow < 0) return [];

  const rows: ParsedExcelRow[] = [];
  let lastParentDesc = '';
  let lastParentItem = '';

  for (let i = headerRow + 1; i < raw.length; i++) {
    const row = raw[i] as unknown[];
    const rawDesc = toStr(row[descCol]);
    const rawItem = itemCol >= 0 ? toStr(row[itemCol]) : '';
    const qty = qtyCol >= 0 ? toNum(row[qtyCol]) : 0;
    const rate = toNum(row[rateCol]);
    const unit = unitCol >= 0 ? toStr(row[unitCol]) : '';

    if (!rawDesc && !rawItem) continue;

    // Parent row (has item number but no unit/qty — it's a category header)
    if (rawItem && !unit && qty === 0 && rate === 0) {
      lastParentDesc = rawDesc || lastParentDesc;
      lastParentItem = rawItem;
      continue;
    }

    // Sub-item row (description may be short, parent provides context)
    const fullDesc = rawDesc
      ? (lastParentDesc && rawDesc.length < 60 && !rawDesc.includes(lastParentDesc.slice(0, 20))
          ? `${lastParentDesc} — ${rawDesc}`
          : rawDesc)
      : lastParentDesc;

    if (!fullDesc) continue;

    rows.push({
      serial_no: rawItem || lastParentItem || String(rows.length + 1),
      description: fullDesc,
      unit,
      qty_since_last_bill: 0, // filled by caller if cross-referencing
      qty_to_date: qty,
      rate,
      remarks: remarksCol >= 0 ? toStr(row[remarksCol]) : '',
    });
  }

  return rows;
}

// ─── Generic fallback parser for unknown formats ──────────────────────────────
function parseGenericFormat(wb: XLSX.WorkBook): {
  header: Partial<Bill>;
  rows: ParsedExcelRow[];
  confidence: number;
} {
  const warnings: string[] = [];
  let bestRows: ParsedExcelRow[] = [];
  let bestScore = -1;

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
      if (colMap.has('description') && colMap.has('rate')) {
        dataStart = r + 1;
        break;
      }
    }

    if (dataStart < 0) { warnings.push(`Sheet "${sheetName}": no headers`); continue; }

    const rows: ParsedExcelRow[] = [];
    for (let r = dataStart; r <= range.e.r; r++) {
      const get = (f: keyof ParsedExcelRow) => {
        const c = colMap.get(f);
        if (c === undefined) return undefined;
        return ws[XLSX.utils.encode_cell({ r, c })]?.v;
      };
      const desc = toStr(get('description'));
      if (!desc) continue;
      rows.push({
        serial_no: toStr(get('serial_no')) || String(rows.length + 1),
        description: desc,
        unit: toStr(get('unit')),
        qty_since_last_bill: toNum(get('qty_since_last_bill')),
        qty_to_date: toNum(get('qty_to_date')),
        rate: toNum(get('rate')),
        remarks: toStr(get('remarks')),
      });
    }

    let score = rows.length > 0 ? 0.3 : 0;
    if (rows.some(r => r.rate > 0)) score += 0.2;
    if (rows.some(r => r.qty_since_last_bill > 0 || r.qty_to_date > 0)) score += 0.2;
    if (score > bestScore) { bestScore = score; bestRows = rows; }
  }

  return { header: {}, rows: bestRows, confidence: Math.max(bestScore, 0) };
}

// ─── Main parse function (browser File API) ───────────────────────────────────
export async function parseExcelFile(file: File): Promise<ExcelParseResult> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { type: 'array', cellDates: true });

  // Try domain-specific parser first
  const domain = parseDomainFormat(wb);
  if (domain && domain.rows.length > 0) {
    return {
      header: domain.header,
      rows: domain.rows,
      confidence: domain.confidence,
      warnings: [],
      raw_sheet_names: wb.SheetNames,
    };
  }

  // Fallback to generic
  const generic = parseGenericFormat(wb);
  return {
    header: generic.header,
    rows: generic.rows,
    confidence: generic.confidence,
    warnings: ['Used generic parser — review all fields'],
    raw_sheet_names: wb.SheetNames,
  };
}

// ─── Convert parse result to BillItems ───────────────────────────────────────
export function parsedRowsToBillItems(rows: ParsedExcelRow[], billId = ''): BillItem[] {
  return rows.map((row, i) => ({
    id: crypto.randomUUID(),
    bill_id: billId,
    serial_no: row.serial_no,
    description: row.description,
    unit: row.unit,
    qty_since_last_bill: row.qty_since_last_bill,
    qty_to_date: row.qty_to_date,
    rate: row.rate,
    amount_since_previous: row.qty_since_last_bill * row.rate,
    amount_to_date: row.qty_to_date * row.rate,
    remarks: row.remarks,
    sort_order: i,
  }));
}
