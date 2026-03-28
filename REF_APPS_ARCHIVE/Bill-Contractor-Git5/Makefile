## Bill Generator SaaS — Dev Commands

.PHONY: dev build test worker docker lint format typecheck

# ── Dev ──────────────────────────────────────────────────────────────────
dev:
	@echo "Starting frontend + backend in parallel..."
	@echo "Run these in separate terminals:"
	@echo "  make dev-frontend"
	@echo "  make dev-backend"
	@echo "  make worker"

dev-frontend:
	pnpm --filter @workspace/bill-ui run dev

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

# ── Worker ───────────────────────────────────────────────────────────────
worker:
	cd backend && uv run python -m arq worker.WorkerSettings

# ── Build ────────────────────────────────────────────────────────────────
build:
	pnpm run build
	cd backend && uv run python -m py_compile app/main.py

# ── Test ─────────────────────────────────────────────────────────────────
test:
	cd backend && uv run pytest tests/ -v

test-smoke:
	cd backend && uv run python tests/test_pipeline.py

# ── Lint / Format / Typecheck ────────────────────────────────────────────
lint:
	pnpm --filter @workspace/bill-ui run typecheck
	cd backend && uv run ruff check app/

format:
	pnpm exec prettier --write "frontend/src/**/*.{ts,tsx}"
	cd backend && uv run ruff format app/

typecheck:
	pnpm run typecheck

# ── Docker ───────────────────────────────────────────────────────────────
docker:
	docker compose -f docker/docker-compose.yml up --build

docker-down:
	docker compose -f docker/docker-compose.yml down
