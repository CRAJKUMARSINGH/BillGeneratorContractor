# Target Architecture — SaaS 2026
Branch: consolidation/saas-2026

## Folder Structure (Target)
```
/
├── frontend/               ← React 19 + Vite 7 + TanStack Router
│   ├── src/
│   │   ├── routes/         ← TanStack Router file-based routes
│   │   ├── components/     ← shadcn/ui + custom
│   │   ├── features/       ← upload / editor / preview / export
│   │   ├── lib/            ← api client, store (zustand), utils
│   │   └── styles/
│   └── package.json
│
├── backend/                ← FastAPI (Python 3.11+)
│   ├── app/
│   │   ├── api/            ← routers: bills, jobs, health
│   │   ├── core/           ← config, security, logging
│   │   ├── engine/         ← document workflow engine
│   │   │   ├── parsers/    ← excel, pdf, ocr
│   │   │   ├── calculator/ ← dependency graph, reactive recalc
│   │   │   ├── renderer/   ← jinja2 HTML, weasyprint PDF
│   │   │   └── models.py   ← unified document model (Pydantic v2)
│   │   ├── jobs/           ← ARQ job queue
│   │   └── main.py
│   ├── tests/
│   └── pyproject.toml
│
├── worker/                 ← ARQ worker process
│   └── worker.py
│
├── tests/                  ← integration + e2e tests
│   ├── test_pipeline.py    ← Excel → HTML smoke tests
│   └── fixtures/           ← TEST_INPUT_FILES symlink
│
├── docker/
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   └── docker-compose.yml
│
├── configs/
│   ├── .env.example
│   └── caddy/Caddyfile
│
├── docs/
│   ├── PHASE0_BASELINE.md
│   └── ARCHITECTURE.md
│
└── Makefile
```

## Tech Stack Decisions

### Frontend
| Concern | Choice | Reason |
|---------|--------|--------|
| Framework | React 19 | Already in use, streaming-ready |
| Build | Vite 7 | Already in use |
| Routing | TanStack Router | Type-safe, URL-based (fixes deep link bug) |
| Server state | TanStack Query v5 | Already in use |
| Client state | Zustand v5 | Already in use |
| UI primitives | shadcn/ui + Radix | Already in use |
| Styling | Tailwind v4 | Already in use |
| Animation | Framer Motion | Already in use |

### Backend
| Concern | Choice | Reason |
|---------|--------|--------|
| Framework | FastAPI (latest) | Already in use, async-native |
| Validation | Pydantic v2 | Type-safe, fast |
| Job queue | ARQ (async Redis Queue) | Async-native, simpler than Celery |
| Redis | Redis 7 (via Docker) | Required by ARQ |
| PDF | WeasyPrint | Already in use |
| Excel | pandas + openpyxl | Already in use |
| DB | SQLite (dev) / Postgres (prod) via Drizzle | Lightweight start |

### Infrastructure
| Concern | Choice |
|---------|--------|
| Reverse proxy | Caddy (auto-HTTPS) |
| Containers | Docker + Compose |
| Secrets | .env + python-dotenv |

## Document Workflow States
```
UPLOADED → PARSED → INPUT_EDITED → CALCULATED → FINAL_EDITED → PRINT_READY → EXPORTED
```

## Phase Execution Plan (5 weeks)
| Week | Phases |
|------|--------|
| 1 | Phase 0 ✅, Phase 1 (audit), Phase 2 (architecture scaffold) |
| 2 | Phase 3 (input ingestion), Phase 4 (workflow engine) |
| 3 | Phase 5 (frontend modernization), Phase 6 (calc engine) |
| 4 | Phase 7 (FastAPI scaling + ARQ), Phase 8 (performance) |
| 5 | Phase 9 (robotic tests), Phase 10 (DX), Phase 11 (Docker) |
