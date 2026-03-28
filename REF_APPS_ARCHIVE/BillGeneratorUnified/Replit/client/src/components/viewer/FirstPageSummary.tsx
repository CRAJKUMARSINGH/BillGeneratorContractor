import React from "react";
import { type ProcessedBill } from "@shared/schema";
import { PrintStyles } from "./PrintStyles";

export function FirstPageSummary({ bill }: { bill: ProcessedBill }) {
  return (
    <div className="print-area bg-white rounded-2xl p-8 shadow-sm print:shadow-none print:p-0">
      <PrintStyles orientation="portrait" />
      
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold uppercase underline mb-2 print:text-lg">First Page Summary</h2>
        <div className="text-sm space-y-1">
          <p><strong>Name of Work:</strong> {bill.titleData.nameOfWork || "N/A"}</p>
          <p><strong>Agreement No:</strong> {bill.titleData.agreementNo || "N/A"}</p>
          <p><strong>Contractor:</strong> {bill.titleData.contractorName || "N/A"}</p>
        </div>
      </div>

      <div className="overflow-x-auto print:overflow-visible">
        <table className="w-full text-sm text-left border-collapse print-table-portrait">
          <thead className="bg-gray-50 print:bg-white text-gray-700">
            <tr>
              <th className="border border-gray-300 p-2" style={{ width: '8mm' }}>S.No.</th>
              <th className="border border-gray-300 p-2" style={{ width: '70mm' }}>Description</th>
              <th className="border border-gray-300 p-2" style={{ width: '12mm' }}>Unit</th>
              <th className="border border-gray-300 p-2 text-right" style={{ width: '15mm' }}>Qty Since</th>
              <th className="border border-gray-300 p-2 text-right" style={{ width: '15mm' }}>Qty Upto</th>
              <th className="border border-gray-300 p-2 text-right" style={{ width: '18mm' }}>Rate</th>
              <th className="border border-gray-300 p-2 text-right" style={{ width: '20mm' }}>Amt Since</th>
              <th className="border border-gray-300 p-2 text-right" style={{ width: '20mm' }}>Amt Upto</th>
              <th className="border border-gray-300 p-2" style={{ width: '12mm' }}>Remarks</th>
            </tr>
          </thead>
          <tbody>
            {bill.firstPageItems.map((item, idx) => (
              <tr key={idx} className={item.isParent ? "font-bold bg-gray-50 print:bg-white" : ""}>
                <td className="border border-gray-300 p-2 text-center">{item.itemNo}</td>
                <td className="border border-gray-300 p-2 whitespace-pre-wrap">{item.description}</td>
                <td className="border border-gray-300 p-2 text-center">{item.unit || '-'}</td>
                <td className="border border-gray-300 p-2 text-right">{item.qtyBillSince || '-'}</td>
                <td className="border border-gray-300 p-2 text-right">{item.qtyBillUpto || '-'}</td>
                <td className="border border-gray-300 p-2 text-right">{item.rate ? item.rate.toFixed(2) : '-'}</td>
                <td className="border border-gray-300 p-2 text-right">{item.amtBillSince ? item.amtBillSince.toFixed(2) : '-'}</td>
                <td className="border border-gray-300 p-2 text-right">{item.amtBillUpto ? item.amtBillUpto.toFixed(2) : '-'}</td>
                <td className="border border-gray-300 p-2">{item.remarks || ''}</td>
              </tr>
            ))}
          </tbody>
          <tfoot className="font-bold bg-gray-50 print:bg-white">
            <tr>
              <td colSpan={6} className="border border-gray-300 p-2 text-right">TOTAL</td>
              <td className="border border-gray-300 p-2 text-right">{bill.totals.amtBillSince?.toFixed(2) || '-'}</td>
              <td className="border border-gray-300 p-2 text-right">{bill.totals.amtBillUpto?.toFixed(2) || '-'}</td>
              <td className="border border-gray-300 p-2"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
