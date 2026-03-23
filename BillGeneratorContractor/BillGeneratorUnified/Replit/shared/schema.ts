import { pgTable, text, serial, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const bills = pgTable("bills", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  data: jsonb("data").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertBillSchema = createInsertSchema(bills).omit({ id: true, createdAt: true });

export type Bill = typeof bills.$inferSelect;
export type InsertBill = z.infer<typeof insertBillSchema>;

export const BillItemSchema = z.object({
  itemNo: z.string(),
  description: z.string(),
  unit: z.string().optional(),
  qtyWo: z.number().optional(),
  rate: z.number().optional(),
  amtWo: z.number().optional(),
  qtyBillSince: z.number().optional(),
  qtyBillUpto: z.number().optional(),
  amtBillSince: z.number().optional(),
  amtBillUpto: z.number().optional(),
  excessQty: z.number().optional(),
  excessAmt: z.number().optional(),
  savingQty: z.number().optional(),
  savingAmt: z.number().optional(),
  remarks: z.string().optional(),
  isParent: z.boolean().optional(),
});

export const ProcessedBillSchema = z.object({
  titleData: z.record(z.string(), z.any()),
  firstPageItems: z.array(BillItemSchema),
  deviationItems: z.array(BillItemSchema),
  extraItems: z.array(BillItemSchema),
  totals: z.record(z.string(), z.any()),
});

export type ProcessedBill = z.infer<typeof ProcessedBillSchema>;
