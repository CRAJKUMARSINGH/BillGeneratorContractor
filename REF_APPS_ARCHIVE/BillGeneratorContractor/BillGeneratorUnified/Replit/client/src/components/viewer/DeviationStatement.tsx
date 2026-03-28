import React from "react";
import { type ProcessedBill } from "@shared/schema";
import { PrintStyles } from "./PrintStyles";

export function DeviationStatement({ bill }: { bill: ProcessedBill }) {
  return (
    <div className="print-area bg-white rounded-2xl p-8 shadow-sm print:shadow-none print:p-0">
      {/* CRITICAL: Deviation Statement MUST be landscape */}
      <PrintStyles orientation="landscape" />

      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold uppercase underline mb-2 print:text-lg">Deviation Statement</h2>
        <div className="flex justify-between text-sm">
          <span><strong>Work:</strong> {bill.titleData.nameOfWork || "N/A"}</span>
          <span><strong>Agmt:</strong> {bill.titleData.agreementNo || "N/A"}</span>
        </div>
      </div>

      <div className="overflow-x-auto print:overflow-visible">
        <table className="w-full text-xs text-left border-collapse print-table-landscape">
          <thead className="bg-gray-50 print:bg-white text-gray-700">
            <tr>
              <th className="border border-gray-300 p-1" style={{ width: '12mm' }}>Item</th>
              <th className="border border-gray-300 p-1" style={{ width: '80mm' }}>Description</th>
              <th className="border border-gray-300 p-1" style={{ width: '12mm' }}>Unit</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '15mm' }}>Qty WO</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '15mm' }}>Rate</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '20mm' }}>Amt WO</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '15mm' }}>Qty Bill</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '20mm' }}>Amt Bill</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '15mm' }}>Exc Qty</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '18mm' }}>Exc Amt</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '15mm' }}>Sav Qty</th>
              <th className="border border-gray-300 p-1 text-right" style={{ width: '18mm' }}>Sav Amt</th>
              <th className="border border-gray-300 p-1" style={{ width: '12mm' }}>Rmk</th>
            </tr>
          </thead>
          <tbody>
            {bill.deviationItems.map((item, idx) => (
              <tr key={idx} className="print:break-inside-avoid">
                <td className="border border-gray-300 p-1 text-center">{item.itemNo}</td>
                <td className="border border-gray-300 p-1 whitespace-pre-wrap">{item.description}</td>
                <td className="border border-gray-300 p-1 text-center">{item.unit || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.qtyWo || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.rate?.toFixed(2) || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.amtWo?.toFixed(2) || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.qtyBillUpto || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.amtBillUpto?.toFixed(2) || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.excessQty || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.excessAmt?.toFixed(2) || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.savingQty || '-'}</td>
                <td className="border border-gray-300 p-1 text-right">{item.savingAmt?.toFixed(2) || '-'}</td>
                <td className="border border-gray-300 p-1">{item.remarks || ''}</td>
              </tr>
            ))}
          </tbody>
          <tfoot className="font-bold bg-gray-50 print:bg-white">
            <tr>
              <td colSpan={5} className="border border-gray-300 p-1 text-right">TOTAL</td>
              <td className="border border-gray-300 p-1 text-right">{bill.totals.amtWo?.toFixed(2) || '-'}</td>
              <td colSpan={1} className="border border-gray-300 p-1 text-right"></td>
              <td className="border border-gray-300 p-1 text-right">{bill.totals.amtBillUpto?.toFixed(2) || '-'}</td>
              <td colSpan={1} className="border border-gray-300 p-1 text-right"></td>
              <td className="border border-gray-300 p-1 text-right">{bill.totals.excessAmt?.toFixed(2) || '-'}</td>
              <td colSpan={1} className="border border-gray-300 p-1 text-right"></td>
              <td className="border border-gray-300 p-1 text-right">{bill.totals.savingAmt?.toFixed(2) || '-'}</td>
              <td className="border border-gray-300 p-1"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
