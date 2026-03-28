import { db } from "./db";
import { bills, type Bill, type InsertBill } from "@shared/schema";
import { eq } from "drizzle-orm";

export interface IStorage {
  getBills(): Promise<Bill[]>;
  getBill(id: number): Promise<Bill | undefined>;
  createBill(bill: InsertBill): Promise<Bill>;
}

export class DatabaseStorage implements IStorage {
  async getBills(): Promise<Bill[]> {
    return await db.select().from(bills);
  }

  async getBill(id: number): Promise<Bill | undefined> {
    const [bill] = await db.select().from(bills).where(eq(bills.id, id));
    return bill;
  }

  async createBill(insertBill: InsertBill): Promise<Bill> {
    const [bill] = await db.insert(bills).values(insertBill).returning();
    return bill;
  }
}

export const storage = new DatabaseStorage();