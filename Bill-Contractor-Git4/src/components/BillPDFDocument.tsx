import {
  Document, Page, Text, View, StyleSheet, Font,
} from '@react-pdf/renderer';
import type { Bill } from '../types/bill';
import { computeSummary } from '../types/bill';

// Register a clean system font stack
Font.registerHyphenationCallback((word) => [word]);

const C = {
  black:   '#0f0f0f',
  dark:    '#1a1a2e',
  mid:     '#374151',
  light:   '#6b7280',
  border:  '#d1d5db',
  bg:      '#f9fafb',
  accent:  '#4f46e5',
  white:   '#ffffff',
};

const s = StyleSheet.create({
  page: {
    fontFamily: 'Helvetica',
    fontSize: 9,
    color: C.black,
    paddingTop: 36,
    paddingBottom: 48,
    paddingHorizontal: 40,
    backgroundColor: C.white,
  },
  // ── Header ──
  headerBox: {
    borderBottom: `2px solid ${C.accent}`,
    paddingBottom: 10,
    marginBottom: 14,
  },
  title: {
    fontSize: 16,
    fontFamily: 'Helvetica-Bold',
    color: C.accent,
    textAlign: 'center',
    letterSpacing: 1,
  },
  subtitle: {
    fontSize: 9,
    color: C.light,
    textAlign: 'center',
    marginTop: 2,
  },
  // ── Meta grid ──
  metaGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 0,
    marginBottom: 14,
    border: `1px solid ${C.border}`,
    borderRadius: 4,
    overflow: 'hidden',
  },
  metaCell: {
    width: '50%',
    flexDirection: 'row',
    borderBottom: `1px solid ${C.border}`,
    borderRight: `1px solid ${C.border}`,
  },
  metaCellFull: {
    width: '100%',
    flexDirection: 'row',
    borderBottom: `1px solid ${C.border}`,
  },
  metaLabel: {
    width: 130,
    backgroundColor: C.bg,
    paddingHorizontal: 8,
    paddingVertical: 5,
    fontSize: 8,
    color: C.light,
    fontFamily: 'Helvetica-Bold',
  },
  metaValue: {
    flex: 1,
    paddingHorizontal: 8,
    paddingVertical: 5,
    fontSize: 8.5,
    color: C.black,
  },
  // ── Table ──
  table: {
    border: `1px solid ${C.border}`,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 14,
  },
  tableHead: {
    flexDirection: 'row',
    backgroundColor: C.accent,
  },
  tableRow: {
    flexDirection: 'row',
    borderTop: `1px solid ${C.border}`,
  },
  tableRowAlt: {
    flexDirection: 'row',
    borderTop: `1px solid ${C.border}`,
    backgroundColor: C.bg,
  },
  th: {
    paddingHorizontal: 6,
    paddingVertical: 5,
    fontSize: 7.5,
    fontFamily: 'Helvetica-Bold',
    color: C.white,
    borderRight: `1px solid rgba(255,255,255,0.2)`,
  },
  td: {
    paddingHorizontal: 6,
    paddingVertical: 4,
    fontSize: 8.5,
    color: C.black,
    borderRight: `1px solid ${C.border}`,
  },
  tdRight: {
    paddingHorizontal: 6,
    paddingVertical: 4,
    fontSize: 8.5,
    color: C.black,
    borderRight: `1px solid ${C.border}`,
    textAlign: 'right',
  },
  // ── Summary ──
  summaryBox: {
    alignSelf: 'flex-end',
    width: 260,
    border: `1px solid ${C.border}`,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 24,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderBottom: `1px solid ${C.border}`,
  },
  summaryRowFinal: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
    paddingVertical: 7,
    backgroundColor: C.accent,
  },
  summaryLabel: { fontSize: 8.5, color: C.mid },
  summaryValue: { fontSize: 8.5, color: C.black, fontFamily: 'Helvetica-Bold' },
  summaryLabelFinal: { fontSize: 9.5, color: C.white, fontFamily: 'Helvetica-Bold' },
  summaryValueFinal: { fontSize: 9.5, color: C.white, fontFamily: 'Helvetica-Bold' },
  // ── Signatures ──
  sigRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 40,
    paddingTop: 10,
    borderTop: `1px solid ${C.border}`,
  },
  sigBox: { width: '30%', alignItems: 'center' },
  sigLine: { width: '100%', borderBottom: `1px solid ${C.black}`, marginBottom: 4 },
  sigLabel: { fontSize: 8, color: C.mid, textAlign: 'center' },
  // ── Footer ──
  footer: {
    position: 'absolute',
    bottom: 20,
    left: 40,
    right: 40,
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTop: `1px solid ${C.border}`,
    paddingTop: 6,
  },
  footerText: { fontSize: 7, color: C.light },
  pageNum: { fontSize: 7, color: C.light },
});

function fmt(d: string | null) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function money(n: number) { return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`; }

interface Props { bill: Bill }

export default function BillPDFDocument({ bill }: Props) {
  const items = bill.items ?? [];
  const { grand_total, premium_amount, total_with_premium, net_payable } = computeSummary(bill);

  const META_ROWS: { label: string; value: string; full?: boolean }[] = [
    { label: 'Voucher Number',    value: bill.voucher_number || '—' },
    { label: 'Bill Date',         value: fmt(bill.bill_date) },
    { label: 'Serial Number',     value: bill.serial_number || '—' },
    { label: 'Agreement Number',  value: bill.agreement_number || '—' },
    { label: 'Contractor Name',   value: bill.contractor_name || '—', full: true },
    { label: 'Name of Work',      value: bill.work_name || '—', full: true },
    { label: 'Work Order Ref',    value: bill.work_order_reference || '—' },
    { label: 'Previous Bill No.', value: bill.previous_bill_number || '—' },
    { label: 'Previous Bill Date',value: fmt(bill.previous_bill_date) },
    { label: 'Commencement Date', value: fmt(bill.commencement_date) },
    { label: 'Measurement Date',  value: fmt(bill.measurement_date) },
  ];

  const COL_WIDTHS = ['5%', '28%', '6%', '9%', '9%', '9%', '12%', '12%', '10%'];

  return (
    <Document title={`Bill — ${bill.voucher_number || bill.id}`} author="BillForge">
      <Page size="A4" orientation="landscape" style={s.page}>
        {/* Title */}
        <View style={s.headerBox}>
          <Text style={s.title}>CONTRACTOR RUNNING ACCOUNT BILL</Text>
          <Text style={s.subtitle}>Running Account Bill — BillForge</Text>
        </View>

        {/* Meta */}
        <View style={s.metaGrid}>
          {META_ROWS.map((row) => (
            <View key={row.label} style={row.full ? s.metaCellFull : s.metaCell}>
              <Text style={s.metaLabel}>{row.label}</Text>
              <Text style={s.metaValue}>{row.value}</Text>
            </View>
          ))}
        </View>

        {/* Items table */}
        <View style={s.table}>
          <View style={s.tableHead}>
            {['S.No', 'Description of Work', 'Unit', 'Qty Since Last', 'Qty To Date', 'Rate', 'Amt To Date', 'Amt Since Prev', 'Remarks'].map((h, i) => (
              <Text key={h} style={[s.th, { width: COL_WIDTHS[i] }]}>{h}</Text>
            ))}
          </View>
          {items.map((item, idx) => (
            <View key={item.id} style={idx % 2 === 0 ? s.tableRow : s.tableRowAlt}>
              <Text style={[s.td,      { width: COL_WIDTHS[0] }]}>{item.serial_no || String(idx + 1)}</Text>
              <Text style={[s.td,      { width: COL_WIDTHS[1] }]}>{item.description}</Text>
              <Text style={[s.td,      { width: COL_WIDTHS[2] }]}>{item.unit}</Text>
              <Text style={[s.tdRight, { width: COL_WIDTHS[3] }]}>{item.qty_since_last_bill.toFixed(2)}</Text>
              <Text style={[s.tdRight, { width: COL_WIDTHS[4] }]}>{item.qty_to_date.toFixed(2)}</Text>
              <Text style={[s.tdRight, { width: COL_WIDTHS[5] }]}>{money(item.rate)}</Text>
              <Text style={[s.tdRight, { width: COL_WIDTHS[6] }]}>{money(item.amount_to_date)}</Text>
              <Text style={[s.tdRight, { width: COL_WIDTHS[7] }]}>{money(item.amount_since_previous)}</Text>
              <Text style={[s.td,      { width: COL_WIDTHS[8] }]}>{item.remarks}</Text>
            </View>
          ))}
        </View>

        {/* Summary */}
        <View style={s.summaryBox}>
          <View style={s.summaryRow}>
            <Text style={s.summaryLabel}>Grand Total</Text>
            <Text style={s.summaryValue}>{money(grand_total)}</Text>
          </View>
          {bill.tender_premium_percentage > 0 && (
            <>
              <View style={s.summaryRow}>
                <Text style={s.summaryLabel}>Tender Premium ({bill.tender_premium_percentage}%)</Text>
                <Text style={s.summaryValue}>{money(premium_amount)}</Text>
              </View>
              <View style={s.summaryRow}>
                <Text style={s.summaryLabel}>Total with Premium</Text>
                <Text style={s.summaryValue}>{money(total_with_premium)}</Text>
              </View>
            </>
          )}
          {bill.last_bill_deduction > 0 && (
            <View style={s.summaryRow}>
              <Text style={s.summaryLabel}>Less: Previous Bill</Text>
              <Text style={s.summaryValue}>({money(bill.last_bill_deduction)})</Text>
            </View>
          )}
          <View style={s.summaryRowFinal}>
            <Text style={s.summaryLabelFinal}>Net Payable Amount</Text>
            <Text style={s.summaryValueFinal}>{money(net_payable)}</Text>
          </View>
        </View>

        {/* Signatures */}
        <View style={s.sigRow}>
          {['Prepared By', 'Checked By', 'Approved By'].map((label) => (
            <View key={label} style={s.sigBox}>
              <View style={s.sigLine} />
              <Text style={s.sigLabel}>{label}</Text>
            </View>
          ))}
        </View>

        {/* Footer */}
        <View style={s.footer} fixed>
          <Text style={s.footerText}>
            {bill.contractor_name} · {bill.work_name}
          </Text>
          <Text style={s.pageNum} render={({ pageNumber, totalPages }) =>
            `Page ${pageNumber} of ${totalPages}`
          } />
        </View>
      </Page>
    </Document>
  );
}
