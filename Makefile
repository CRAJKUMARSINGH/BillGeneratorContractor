# Bill Generator — SaaS Build Tool
# Phase 10 DevEx

.PHONY: dev test worker clean help

help:
	@echo "Available commands:"
	@echo "  make dev    - Start backend (8000) and frontend (5173)"
	@echo "  make test   - Run the full robotic ingestion audit"
	@echo "  make worker - Start the ARQ async job worker"
	@echo "  make clean  - Purge legacy multi-repo folders"

dev:
	@echo "Starting development environment..."
	powershell -Command "Start-Process cmd -ArgumentList '/c cd backend && uvicorn app:app --reload --port 8000'; Start-Process cmd -ArgumentList '/c cd frontend && npm run dev'"

test:
	@echo "Running robotic audit..."
	python -m pytest tests/test_robotic_harness.py -v -s

worker:
	@echo "Starting ARQ worker..."
	cd worker && arq worker.WorkerSettings

clean:
	@echo "Purging legacy artifacts..."
	powershell -Command "Remove-Item -Recurse -Force Bill-Contractor-Git4, Bill-Contractor-Git5, BillGeneratorContractor, BillGeneratorHistorical, BillGeneratorUnified"
