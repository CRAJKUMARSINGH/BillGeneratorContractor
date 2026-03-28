import { pgTable, text, serial, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const extractionJobs = pgTable("extraction_jobs", {
  id: serial("id").primaryKey(),
  imageFilename: text("image_filename").notNull(),
  qtyFilename: text("qty_filename").notNull(),
  status: text("status").notNull(), // 'success', 'error'
  errorMessage: text("error_message"),
  resultData: jsonb("result_data"), // The extracted items array
  excelUrl: text("excel_url"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertJobSchema = createInsertSchema(extractionJobs).omit({ id: true, createdAt: true });

export type ExtractionJob = typeof extractionJobs.$inferSelect;
export type InsertJob = z.infer<typeof insertJobSchema>;

export const parsedItemSchema = z.object({
  code: z.string(),
  description: z.string(),
  unit: z.string(),
  rate: z.number(),
  qty: z.number(),
  amount: z.number(),
});

export type ParsedItem = z.infer<typeof parsedItemSchema>;
