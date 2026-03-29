import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import multer from "multer";
import path from "path";
import fs from "fs/promises";
import { exec } from "child_process";
import util from "util";

const execAsync = util.promisify(exec);

// Configure multer for file uploads
const upload = multer({ 
  dest: path.join(process.cwd(), 'uploads/'),
  limits: { fileSize: 10 * 1024 * 1024 } // 10MB limit
});

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {

  // Ensure uploads directory exists
  await fs.mkdir(path.join(process.cwd(), 'uploads/'), { recursive: true });

  app.get(api.jobs.list.path, async (req, res) => {
    const jobs = await storage.getJobs();
    res.json(jobs);
  });

  app.get(api.jobs.get.path, async (req, res) => {
    const job = await storage.getJob(Number(req.params.id));
    if (!job) {
      return res.status(404).json({ message: 'Job not found' });
    }
    res.json(job);
  });

  // Serve the generated Excel files
  app.get('/api/downloads/:filename', async (req, res) => {
    const filename = req.params.filename;
    const filepath = path.join(process.cwd(), 'uploads', filename);
    res.download(filepath);
  });

  app.post(
    api.jobs.process.path,
    upload.fields([{ name: 'image', maxCount: 1 }, { name: 'qtyFile', maxCount: 1 }]),
    async (req, res) => {
      try {
        const files = req.files as { [fieldname: string]: Express.Multer.File[] };
        
        if (!files.image || !files.image[0]) {
          return res.status(400).json({ message: "Image file is required", field: "image" });
        }
        if (!files.qtyFile || !files.qtyFile[0]) {
          return res.status(400).json({ message: "Quantity text file is required", field: "qtyFile" });
        }

        const imageFile = files.image[0];
        const qtyFile = files.qtyFile[0];

        // Create initial job record
        const job = await storage.createJob({
          imageFilename: imageFile.originalname,
          qtyFilename: qtyFile.originalname,
          status: 'processing',
        });

        const excelFilename = `bill_${job.id}_${Date.now()}.xlsx`;
        const excelPath = path.join(process.cwd(), 'uploads', excelFilename);
        
        // Execute python script for processing
        const pythonScriptPath = path.join(process.cwd(), 'server', 'ocr_engine.py');
        const command = `python3 ${pythonScriptPath} "${imageFile.path}" "${qtyFile.path}" "${excelPath}"`;

        try {
          const { stdout, stderr } = await execAsync(command);
          
          // Parse stdout to get JSON result
          const lines = stdout.split('\n');
          const jsonLine = lines.find(l => l.startsWith('{"status":'));
          
          if (!jsonLine) {
            throw new Error("Invalid output from OCR engine.");
          }

          const result = JSON.parse(jsonLine);

          if (result.status === "error") {
            const failedJob = await storage.updateJob(job.id, {
              status: 'error',
              errorMessage: result.message
            });
            // We can return 400 or 200 with error status, let's return 200 with the error job
            // So the frontend can display the strict validation error.
            return res.status(200).json(failedJob);
          }

          const completedJob = await storage.updateJob(job.id, {
            status: 'success',
            resultData: result.data,
            excelUrl: `/api/downloads/${excelFilename}`
          });

          res.status(200).json(completedJob);
        } catch (err: any) {
          console.error("Python Execution Error:", err);
          const failedJob = await storage.updateJob(job.id, {
            status: 'error',
            errorMessage: err.message || "Failed to process image and quantity files."
          });
          res.status(200).json(failedJob);
        }

      } catch (err) {
        if (err instanceof z.ZodError) {
          return res.status(400).json({
            message: err.errors[0].message,
            field: err.errors[0].path.join('.'),
          });
        }
        res.status(500).json({ message: "Internal server error" });
      }
    }
  );

  return httpServer;
}
