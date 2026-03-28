import React from "react";
import { type ProcessedBill } from "@shared/schema";
import { PrintStyles } from "./PrintStyles";

export function ExtraItems({ bill }: { bill: ProcessedBill }) {
  if (!bill.extraItems || bill.extraItems.length === 0) {
    return (
      <div className="print-area bg-white rounded-2xl p-12 shadow-sm text-center">
        <h3 className="text-xl font-medium text-gray-500">No Extra Items Found</h3>
        <p className="text-gray-400 mt-2">There are no additional items outside the original work order.</p>
      </div>
    );
  }

  return (
    <div className="print-area bg-white rounded-2xl p-8 shadow-sm print:shadow-none print:p-0">
      <PrintStyles orientation="portrait" />
      
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold uppercase underline mb-2 print:text-lg">Extra Items Statement</h2>
      </div>

      <div className="overflow-x-auto print:overflow-visible">
        <table className="w-full text-sm text-left border-collapse print-table-portrait">
          <thead className="bg-gray-50 print:bg-white text-gray-700">
            <tr>
              <th className="border border-gray-300 p-2" style={{ width: '10mm' }}>S.No.</th>
              <th className="border border-gray-300 p-2" style={{ width: '80mm' }}>Description</th>
              <th className="border border-gray-300 p-2" style={{ width: '15mm' }}>Unit</th>
              <th className="border border-gray-300 p-2 text-right" style={{ width: '20mm' }}>Quantity</th>
              <th className="border border-gray-300 p-2 text-right" style={{ width: '20mm' }}>Rate</th>
              <th className="border border-gray-300 p-2 text-right" style={{ width: '25mm' }}>Amount</th>
              <th className="border border-gray-300 p-2" style={{ width: '20mm' }}>Remarks</th>
            </tr>
          </thead>
          <tbody>
            {bill.extraItems.map((item, idx) => (
              <tr key={idx}>
                <td className="border border-gray-300 p-2 text-center">{item.itemNo}</td>
                <td className="border border-gray-300 p-2 whitespace-pre-wrap">{item.description}</td>
                <td className="border border-gray-300 p-2 text-center">{item.unit || '-'}</td>
                <td className="border border-gray-300 p-2 text-right">{item.qtyBillUpto || '-'}</td>
                <td className="border border-gray-300 p-2 text-right">{item.rate?.toFixed(2) || '-'}</td>
                <td className="border border-gray-300 p-2 text-right">{item.amtBillUpto?.toFixed(2) || '-'}</td>
                <td className="border border-gray-300 p-2">{item.remarks || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
