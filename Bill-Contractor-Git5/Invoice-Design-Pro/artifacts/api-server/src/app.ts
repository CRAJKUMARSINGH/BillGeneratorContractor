import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import { createProxyMiddleware } from "http-proxy-middleware";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors());

// Proxy bill-related API routes to the Python FastAPI backend
const BILL_API_PORT = process.env.BILL_API_PORT ?? "8000";
app.use(
  "/api/bills",
  createProxyMiddleware({
    target: `http://localhost:${BILL_API_PORT}`,
    changeOrigin: true,
    on: {
      error: (err, req, res) => {
        logger.error({ err }, "Bill API proxy error");
        if (!res.headersSent) {
          (res as express.Response).status(502).json({ error: "Bill API unavailable" });
        }
      },
    },
  }),
);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use("/api", router);

export default app;
