import { db } from "./db";
import { extractionJobs, type InsertJob, type ExtractionJob } from "@shared/schema";
import { eq, desc } from "drizzle-orm";

export interface IStorage {
  getJobs(): Promise<ExtractionJob[]>;
  getJob(id: number): Promise<ExtractionJob | undefined>;
  createJob(job: InsertJob): Promise<ExtractionJob>;
  updateJob(id: number, updates: Partial<InsertJob>): Promise<ExtractionJob>;
}

export class DatabaseStorage implements IStorage {
  async getJobs(): Promise<ExtractionJob[]> {
    return await db.select().from(extractionJobs).orderBy(desc(extractionJobs.createdAt));
  }

  async getJob(id: number): Promise<ExtractionJob | undefined> {
    const [job] = await db.select().from(extractionJobs).where(eq(extractionJobs.id, id));
    return job;
  }

  async createJob(insertJob: InsertJob): Promise<ExtractionJob> {
    const [job] = await db.insert(extractionJobs).values(insertJob).returning();
    return job;
  }

  async updateJob(id: number, updates: Partial<InsertJob>): Promise<ExtractionJob> {
    const [job] = await db
      .update(extractionJobs)
      .set(updates)
      .where(eq(extractionJobs.id, id))
      .returning();
    return job;
  }
}

export const storage = new DatabaseStorage();
