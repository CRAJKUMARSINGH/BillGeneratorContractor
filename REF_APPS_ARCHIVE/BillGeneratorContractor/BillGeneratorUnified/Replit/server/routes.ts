import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import multer from "multer";
import * as xlsx from "xlsx";

const upload = multer({ storage: multer.memoryStorage() });

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  app.get(api.bills.list.path, async (req, res) => {
    const billsList = await storage.getBills();
    res.json(billsList);
  });

  app.get(api.bills.get.path, async (req, res) => {
    const bill = await storage.getBill(Number(req.params.id));
    if (!bill) {
      return res.status(404).json({ message: "Bill not found" });
    }
    res.json(bill);
  });

  app.post(api.bills.process.path, upload.single("file"), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ message: "No file uploaded" });
      }

      const workbook = xlsx.read(req.file.buffer, { type: "buffer" });
      
      // Basic extraction
      const titleData: Record<string, any> = {};
      let firstPageItems: any[] = [];
      let deviationItems: any[] = [];
      let extraItems: any[] = [];

      // Try to read "Title" sheet
      if (workbook.Sheets["Title"]) {
        const titleRows = xlsx.utils.sheet_to_json(workbook.Sheets["Title"], { header: 1 });
        titleRows.forEach((row: any) => {
          if (Array.isArray(row) && row.length >= 2) {
            titleData[row[0]] = row[1];
          }
        });
      }

      // Read "Work Order" and "Bill Quantity" to create items
      const woSheet = workbook.Sheets["Work Order"] || workbook.Sheets[workbook.SheetNames[0]];
      const billSheet = workbook.Sheets["Bill Quantity"] || (workbook.SheetNames.length > 1 ? workbook.Sheets[workbook.SheetNames[1]] : woSheet);
      
      if (woSheet && billSheet) {
        const woData = xlsx.utils.sheet_to_json(woSheet) as any[];
        const billData = xlsx.utils.sheet_to_json(billSheet) as any[];

        firstPageItems = woData.map((row: any, i: number) => {
          const billRow = billData.find((b: any) => 
            (b["Item No."] && b["Item No."] === row["Item No."]) || 
            (b["Item"] && b["Item"] === row["Item"]) ||
            (b["Description"] && b["Description"] === row["Description"])
          ) || {};
          
          return {
            itemNo: String(row["Item No."] || row["Item"] || (i + 1)),
            description: String(row["Description"] || ""),
            unit: String(row["Unit"] || ""),
            qtyWo: Number(row["Quantity"] || 0),
            rate: Number(row["Rate"] || 0),
            amtWo: Number(row["Amount"] || (Number(row["Quantity"] || 0) * Number(row["Rate"] || 0))),
            qtyBillSince: Number(billRow["Quantity Since"] || 0),
            qtyBillUpto: Number(billRow["Quantity Upto"] || billRow["Quantity"] || 0),
            amtBillSince: Number(billRow["Amount Since"] || 0),
            amtBillUpto: Number(billRow["Amount Upto"] || billRow["Amount"] || 0),
            excessQty: 0,
            excessAmt: 0,
            savingQty: 0,
            savingAmt: 0,
            remarks: String(row["Remarks"] || billRow["Remarks"] || "")
          };
        });
        
        // Calculate Deviations
        deviationItems = firstPageItems.map((item) => {
          const excessQty = Math.max(0, (item.qtyBillUpto || 0) - (item.qtyWo || 0));
          const savingQty = Math.max(0, (item.qtyWo || 0) - (item.qtyBillUpto || 0));
          const rate = item.rate || 0;
          return {
            ...item,
            excessQty,
            excessAmt: excessQty * rate,
            savingQty,
            savingAmt: savingQty * rate
          };
        });
      }

      const extraSheet = workbook.Sheets["Extra Items"];
      if (extraSheet) {
        const exData = xlsx.utils.sheet_to_json(extraSheet) as any[];
        extraItems = exData.map((row: any, i: number) => ({
          itemNo: String(row["Item No."] || row["Item"] || `E-${i + 1}`),
          description: String(row["Description"] || ""),
          unit: String(row["Unit"] || ""),
          qtyWo: 0,
          rate: Number(row["Rate"] || 0),
          amtWo: 0,
          qtyBillSince: 0,
          qtyBillUpto: Number(row["Quantity"] || 0),
          amtBillSince: 0,
          amtBillUpto: Number(row["Amount"] || 0),
          remarks: String(row["Remarks"] || "")
        }));
      }

      const totals = {
        totalWoAmount: firstPageItems.reduce((acc, it) => acc + (it.amtWo || 0), 0),
        totalBillAmount: firstPageItems.reduce((acc, it) => acc + (it.amtBillUpto || 0), 0),
      };

      const result = {
        titleData,
        firstPageItems,
        deviationItems,
        extraItems,
        totals
      };

      res.status(200).json(result);
    } catch (err: any) {
      console.error(err);
      res.status(500).json({ message: err.message || "Failed to process Excel file" });
    }
  });

  app.post(api.bills.save.path, async (req, res) => {
    try {
      const input = api.bills.save.input.parse(req.body);
      const bill = await storage.createBill(input);
      res.status(201).json(bill);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({
          message: err.errors[0].message,
          field: err.errors[0].path.join('.'),
        });
      }
      throw err;
    }
  });

  return httpServer;
}