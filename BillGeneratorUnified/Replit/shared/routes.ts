import { z } from "zod";
import { insertBillSchema, bills, ProcessedBillSchema } from "./schema";

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  internal: z.object({
    message: z.string(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
};

export const api = {
  bills: {
    list: {
      method: 'GET' as const,
      path: '/api/bills' as const,
      responses: {
        200: z.array(z.custom<typeof bills.$inferSelect>()),
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/bills/:id' as const,
      responses: {
        200: z.custom<typeof bills.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    process: {
      method: 'POST' as const,
      path: '/api/bills/process' as const,
      responses: {
        200: ProcessedBillSchema,
        400: errorSchemas.validation,
        500: errorSchemas.internal,
      },
    },
    save: {
      method: 'POST' as const,
      path: '/api/bills' as const,
      input: insertBillSchema,
      responses: {
        201: z.custom<typeof bills.$inferSelect>(),
        400: errorSchemas.validation,
      },
    }
  }
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}
