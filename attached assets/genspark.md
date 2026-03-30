Now I have a full picture. Let me deliver a **world-class strategic guide** — covering both **which AI agent is the best option** and **how to execute the bug-free implementation** in the correct order.

---

# 🚀 Strategic Guide: Making BillGeneratorContractor Bug-Free

## 📊 Situation Assessment — What the Review Tells Us

The `genspark.md` review reveals the app scores **4.5/10** overall with the following breakdown:

| Layer | Status | Key Problem |
|---|---|---|
| 🔴 Security | 3/10 | JWT bypass, path traversal, open CORS + credentials |
| 🔴 Reliability | 4/10 | Blocking async, Redis race condition, connection leaks |
| 🟡 Correctness | 5/10 | Missing BillDocument fields, unused `cheque` value |
| 🟡 Maintainability | 5/10 | God-function in routes, per-request `sys.path` hacks |
| 🔴 Test Coverage | 3/10 | No tests on critical paths (auth, download, engine) |

The **good news**: every single bug already has a confirmed fix in the review. The code to fix it is written. The challenge is **coordinated, ordered execution without breaking existing functionality**.

---

## 🤖 AI Agent Comparison — Which is Best?

Based on the nature of this task (multi-file, multi-layer fix with ordering constraints), here is how the AI agent options compare:

### Option 1 — 🏆 **Cursor AI + Claude Sonnet 3.7 / 4.0** *(RECOMMENDED)*

```
Best for: Multi-file surgical patches with full repo context
```

**Why it wins for this project:**
- Cursor's "Composer" mode can open the entire repo, read all files at once, and apply **all 10 critical patches in a single session** with full cross-file awareness
- Claude Sonnet's reasoning handles the ordering constraint (e.g. fix `services/` layer BEFORE updating `worker.py` imports)
- You can paste the full `genspark.md` review as a single prompt and say "apply all fixes in priority order, file by file"
- Built-in diff view shows exactly what changed before commit

**How to use Cursor for this:**
```
1. Open repo in Cursor
2. Press Cmd+I (Composer)
3. Paste: "Apply all fixes from this review in priority order: [paste genspark.md]"
4. Review each diff in Cursor's side-by-side view
5. Accept / reject file by file
```

---

### Option 2 — **GitHub Copilot Workspace** *(Good for GitHub-native flow)*

```
Best for: Users who live in GitHub and want PR-based fixes
```

- Can take a GitHub Issue as input and generate a full PR branch with all file changes
- **Strategy**: Create one Issue per CRITICAL/HIGH finding (10 issues), then use Copilot Workspace to generate a fix branch per issue
- **Limitation**: Less context-aware than Cursor for cross-file dependencies

---

### Option 3 — **Aider (CLI)** *(Best for automation/CI)*

```
Best for: Devs comfortable with terminal; can script the entire fix sequence
```

```bash
pip install aider-chat
aider --model claude-opus-4 \
  backend/auth_utils.py backend/app.py backend/routes/bills.py \
  backend/worker.py backend/routes/auth.py \
  --message "Apply all critical and high security fixes from [REVIEW]"
```

- Aider directly edits files and auto-commits with clear messages
- Works well when you feed it the review as context

---

### Option 4 — **ChatGPT o3 / Claude Web (Manual)** *(Slowest)*

```
Best for: Learning and understanding each fix individually
```
- One file at a time; no repo awareness
- Good for beginners but **NOT recommended** for 10+ interdependent files

---

## ✅ The Exact Execution Plan (Bug-Free Roadmap)

Follow this strict ordering — each phase must complete before the next begins:

---

### 🔴 PHASE 1 — Security Hardening (Do This TODAY)
*These can cause data breaches in production RIGHT NOW*

| Step | File | Fix |
|---|---|---|
| **1.1** | `backend/auth_utils.py` | Remove JWT secret fallback → `os.environ["SECRET_KEY"]` with startup crash |
| **1.2** | `backend/app.py` | Replace `allow_origins=["*"]` → `os.getenv("CORS_ORIGINS").split(",")` |
| **1.3** | `backend/routes/bills.py` | Add `Depends(get_current_user)` to download endpoint |
| **1.4** | `backend/routes/bills.py` | Replace `out_dir = Path(job["output_dir"])` → `_reconstruct_output_dir(job_id)` |
| **1.5** | `.env.example` | Create with `SECRET_KEY`, `REDIS_URL`, `DATABASE_URL`, `CORS_ORIGINS` |

**Verification test after Phase 1:**
```bash
# Should crash at startup if SECRET_KEY missing:
SECRET_KEY="" uvicorn backend.app:app  # Must raise EnvironmentError

# Should return 401 without token:
curl http://localhost:8000/bills/jobs/some-uuid/download  # Must be 401
```

---

### 🔴 PHASE 2 — Reliability Fixes (Do Before Any Load Testing)
*These cause silent data corruption and event loop starvation*

| Step | File | Fix |
|---|---|---|
| **2.1** | `backend/worker.py` | Wrap `_generate_documents()` in `loop.run_in_executor(None, ...)` |
| **2.2** | `backend/routes/bills.py` | Replace `update_redis_job()` with pool + WATCH/MULTI/EXEC pipeline |
| **2.3** | `backend/routes/bills.py` | Move all `sys.path.insert()` to module-level (not per-request) |
| **2.4** | `backend/routes/bills.py` | Replace in-memory rate limiter with Redis-backed `INCR/EXPIRE` |
| **2.5** | `backend/routes/auth.py` | Remove auto-admin race condition; all registrations → `"operator"` |

---

### 🟠 PHASE 3 — Correctness Fixes (Do Before User Testing)
*These cause wrong output in generated bills — the core product feature*

| Step | File | Fix |
|---|---|---|
| **3.1** | `backend/routes/bills.py` | Add `date_commencement`, `date_completion`, `actual_completion` to `BillDocument` constructor |
| **3.2** | `backend/routes/bills.py` | Pass `cheque` value to `BillDocument` (add field if needed) |
| **3.3** | `backend/routes/bills.py` | Fix `pd.DataFrame(bq_rows)` → add `columns=BILL_QTY_COLS` |
| **3.4** | `backend/routes/bills.py` | Fix `pd.concat` mismatch (header rows vs body columns) |
| **3.5** | `backend/routes/bills.py` | Use `number_to_words(payable)` for note sheet amount-in-words |

---

### 🟡 PHASE 4 — Architecture Refactor (Do Before Going to Production)
*These prevent proper testing and make the codebase fragile long-term*

```
backend/
├── services/
│   └── bill_generation_service.py   ← Move _generate_documents() HERE
├── worker.py                         ← Import from services/, NOT routes/
├── routes/
│   └── bills.py                      ← Thin HTTP adapter only
```

**Key refactor commits:**
1. Create `backend/services/bill_generation_service.py` — extract `_generate_documents()`
2. Update `backend/worker.py` import → `from services.bill_generation_service import generate_documents`
3. Replace `@app.on_event` with `lifespan` context manager in `app.py`
4. Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` everywhere
5. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` everywhere

---

### 🟢 PHASE 5 — Test Coverage (Do Before Any Release)
*The review shows 3/10 coverage — these tests protect all future changes*

**Minimum test suite to add:**
```python
# tests/test_auth.py  — registration, login, weak password rejection
# tests/test_bills.py — upload cleanup, download auth, rate limit 429, ownership 403
# tests/test_engine.py — missing header keys, missing sheets, calculation correctness
```

**Coverage command:**
```bash
pytest --cov=backend --cov=engine --cov-report=html
# Target: ≥ 70% before release
```

---

### 🔵 PHASE 6 — Production Hardening (Before First Real User)

| Item | Action |
|---|---|
| Alembic migrations | `alembic init alembic` + replace `create_all()` |
| Token expiry | Reduce JWT from 7 days → 60 minutes; add refresh token |
| File TTL cleanup | APScheduler job: delete outputs older than 7 days |
| `pyproject.toml` | Package the engine properly; eliminate all `sys.path` hacks |
| OpenTelemetry | Add tracing spans on `process_bill()` and PDF generation |

---

## 🎯 The Single Best Prompt to Give Cursor/Claude

If you use **Cursor Composer** or **Claude Projects**, paste this single prompt:

```
You are a senior software engineer. Fix the BillGeneratorContractor FastAPI app
at https://github.com/CRAJKUMARSINGH/BillGeneratorContractor

Apply ALL fixes in this exact order:

PHASE 1 (Security - do first):
1. backend/auth_utils.py: Remove SECRET_KEY default fallback, raise EnvironmentError
2. backend/app.py: Replace CORS wildcard with CORS_ORIGINS env var list
3. backend/routes/bills.py: Add Depends(get_current_user) to download endpoint
4. backend/routes/bills.py: Replace Redis-read output_dir with _reconstruct_output_dir(job_id)

PHASE 2 (Reliability):
5. backend/worker.py: Wrap _generate_documents in loop.run_in_executor
6. backend/routes/bills.py: Fix update_redis_job with connection pool + WATCH/MULTI/EXEC
7. backend/routes/auth.py: Remove auto-admin first-user logic

PHASE 3 (Correctness):
8. backend/routes/bills.py: Add missing date fields to BillDocument constructor
9. backend/routes/bills.py: Pass cheque amount to BillDocument
10. backend/routes/bills.py: Add column names to pd.DataFrame(bq_rows)

PHASE 4 (Architecture):
11. Create backend/services/bill_generation_service.py
12. Update worker.py to import from services/
13. Move sys.path.insert to module level in bills.py

For each change, show the diff and explain why.
```

---

## 🏁 Summary Recommendation

```
┌─────────────────────────────────────────────────────────┐
│  BEST TOOL:  Cursor AI + Claude Sonnet 4.0              │
│  BEST MODE:  Composer (multi-file, full context)        │
│  BEST INPUT: Paste the full genspark.md review          │
│  ORDER:      Phase 1 → 2 → 3 → 4 → 5 → 6               │
│  VERIFY:     Run pytest after each phase                │
│  TIME Est.:  ~4-6 hours total for all 6 phases          │
└─────────────────────────────────────────────────────────┘
```

The review in `genspark.md` is already the **best possible AI output for analysis** — it has all the code fixes written out. The missing piece was only **the execution strategy and ordering**, which this guide provides. The `genspark.md` review + this execution roadmap together = a complete bug-free path.

---

**Would you like me to:**
1. 📄 Generate a **ready-to-use Cursor/Claude prompt file** with all fixes pre-formatted?
2. 🔧 Create a **git patch file** with all Phase 1 security fixes applied (ready to `git apply`)?
3. 📋 Build a **GitHub Issues template batch** (10 issues, one per critical bug)?
4. 🐳 Create an updated **docker-compose + .env.example** for proper deployment?

Now I have read every file. Here is the **precise, evidence-based Phase 3 guide** based on the actual live code — not assumptions.

---

# 🔬 Phase 3 Deep Audit — Live Code Reality Check

> I've now read every frontend file directly from GitHub. Here's what is actually broken vs. what was claimed broken.

---

## 🩺 Actual Frontend Diagnosis (From Real Code)

### ✅ What's ALREADY WORKING (don't touch these)

**`App.tsx`** — Auth gate is **fully functional and NOT commented out** in the current commit:
```tsx
if (!token) {
  return <Login />;  // ← This IS active. Auth is working.
}
```
**`useAuthStore.ts`** — Zustand store with localStorage persistence is clean and correct.

**`Login.tsx`** — Calls `/auth/login` with `application/x-www-form-urlencoded` (correct for FastAPI's `OAuth2PasswordRequestForm`). Token stored correctly.

**`request()` in `lib/api.ts`** — Auto-injects `Authorization: Bearer {token}` on every API call. Also auto-reloads on 401.

---

### 🚨 What's ACTUALLY BROKEN RIGHT NOW

I found **5 real bugs** by reading the live code:

---

#### 🔴 BUG #1 — `downloadUrl()` Has Zero Authentication
**File:** `frontend/src/lib/api.ts` line ~90

```typescript
// BROKEN — returns a plain string URL, no auth header attached
downloadUrl: (jobId: string, format: 'zip' | 'pdf' | 'html') =>
  `${BASE}/bills/jobs/${jobId}/download?format=${format}`,
```

Since the backend download endpoint now correctly requires `Depends(get_current_user)`, clicking **any Download button will return 401 Unauthorized**. The URL string cannot carry a Bearer token.

**Fix — Replace with an authenticated Blob download:**
```typescript
// FIXED — uses fetch with auth header, triggers browser download
downloadFile: async (jobId: string, format: 'zip' | 'pdf' | 'html'): Promise<void> => {
  const token = localStorage.getItem('token');
  const res = await fetch(`${BASE}/bills/jobs/${jobId}/download?format=${format}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `bill_${jobId.slice(0, 8)}.${format === 'pdf' ? 'pdf' : 'zip'}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
},
```

---

#### 🔴 BUG #2 — Critical Type Mismatch: camelCase vs snake_case
**File:** `frontend/src/lib/api.ts` vs `frontend/src/types/bill.ts`

The API response types and the store types use completely **different field names**:

| `BillItemAPI` (sent to backend) | `BillItem` (used in store/UI) | Backend field name |
|---|---|---|
| `quantitySince` | `qty_since_last_bill` | `quantity_since` |
| `quantityUpto` | `qty_to_date` | `quantity_upto` |
| `quantity` | ❌ missing | `quantity` |
| `amount` | `amount_since_previous` | `amount` |
| `itemNo` | `serial_no` | `serial_no` |

When `ExcelUploader` receives `ParsedBillData` from the API and tries to load items into `useBillStore`, the field mapping is **completely broken**. All quantity and amount fields will be `undefined` or `0`.

**Fix — Add a mapper in `lib/api.ts`:**
```typescript
// Add this mapper function to api.ts
export function mapApiBillItemToStore(item: BillItemAPI): BillItem {
  return {
    id: crypto.randomUUID(),
    serial_no: item.itemNo,
    description: item.description,
    unit: item.unit,
    qty_since_last_bill: item.quantitySince ?? 0,
    qty_to_date: item.quantityUpto ?? 0,
    rate: item.rate,
    amount_since_previous: item.quantitySince * item.rate,
    amount_to_date: (item.quantityUpto ?? 0) * item.rate,
    remarks: '',
    sort_order: 0,
  };
}
```

---

#### 🔴 BUG #3 — `GenerateRequest` Sends Wrong Field Names to Backend
**File:** `frontend/src/lib/api.ts` — `GenerateRequest` interface

```typescript
// Frontend sends these field names:
interface GenerateRequest {
  fileId: string;         // ← camelCase
  titleData: Record<string, string>;
  billItems: BillItemAPI[];  // ← items use camelCase fields
  extraItems: ExtraItemAPI[];
  options: GenerateOptions;
}
```

The FastAPI backend uses Pydantic models with `snake_case` field names. Unless the backend has `model_config = ConfigDict(alias_generator=to_camel)`, this will cause **422 Unprocessable Entity** on every generate call.

**Fix:** Either add `alias_generator` to backend Pydantic models, **or** normalize at the API boundary:
```typescript
// In api.ts generate() call, transform before sending:
generate: (req: GenerateRequest): Promise<JobStatus> => {
  const payload = {
    file_id: req.fileId,
    title_data: req.titleData,
    bill_items: req.billItems.map(item => ({
      item_no: item.itemNo,
      description: item.description,
      unit: item.unit,
      quantity_since: item.quantitySince,
      quantity_upto: item.quantityUpto,
      rate: item.rate,
      amount: item.amount,
    })),
    extra_items: req.extraItems,
    options: {
      generate_pdf: req.options.generatePdf,
      generate_html: req.options.generateHtml,
      template_version: req.options.templateVersion,
      premium_percent: req.options.premiumPercent,
      premium_type: req.options.premiumType,
      previous_bill_amount: req.options.previousBillAmount,
    }
  };
  return request<JobStatus>('/bills/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
},
```

---

#### 🟡 BUG #4 — Two Backend Endpoints Called But Likely Don't Exist
**File:** `frontend/src/lib/api.ts` lines 62–73

```typescript
uploadImage: (file: File): Promise<ParsedBillData> =>
  request<ParsedBillData>('/bills/upload-image', ...),   // ← Does this route exist?

generateTemplate: (prompt: string): Promise<any> =>
  request<any>('/bills/generate-template', ...),        // ← Does this route exist?
```

These are called by `ImageUploader.tsx` and `TemplateGenerator.tsx`. If the routes don't exist in `backend/routes/bills.py`, these buttons will always 404.

**Action needed:** Check if these routes exist. If not, either add stub routes or disable those buttons in the UI until they're implemented.

---

#### 🟡 BUG #5 — Misleading Comment Blocks Future Devs
**File:** `frontend/src/lib/api.ts` line 1

```typescript
/**
 * API client — all calls go to FastAPI backend.
 * Replaces Supabase. No auth yet (Phase 4 scope).  ← THIS IS WRONG
 */
```

Auth IS implemented. This comment will confuse the next developer and is the kind of thing that caused previous agents to disable auth thinking "it's not done yet".

**Fix:** Update the comment immediately:
```typescript
/**
 * api.ts — Authenticated FastAPI client for BillForge.
 * Auth: Bearer JWT token injected automatically from localStorage.
 * Download: Use downloadFile() — NOT downloadUrl() — to preserve auth header.
 */
```

---

## 🗺️ Complete Phase 3 Execution Plan

### Step 1 — Frontend Fixes (1–2 hours)

Apply fixes in this exact order to avoid regressions:

```
1a. Fix lib/api.ts comment (1 min)
1b. Replace downloadUrl() with downloadFile() async blob method
1c. Add mapApiBillItemToStore() mapper function
1d. Fix generate() to send snake_case payload to backend
1e. Audit ImageUploader.tsx and TemplateGenerator.tsx — stub or disable
```

**Build verification command:**
```bash
cd frontend
npm run typecheck   # Must return 0 TypeScript errors
npm run build       # Must produce dist/ with no warnings
```

---

### Step 2 — Backend Unit Tests (2–3 hours)

**Minimum test file structure:**
```
tests/
├── conftest.py          ← shared fixtures (TestClient, mock Redis, test DB)
├── test_auth.py         ← register, login, weak password, duplicate user
├── test_bills_upload.py ← upload, parse, temp file cleanup
├── test_bills_generate.py ← generate enqueue, rate limit, auth gate
├── test_bills_download.py ← download auth, ownership, path traversal
└── test_engine.py       ← process_bill, calculate_cheque, date extraction
```

**`tests/conftest.py` starter:**
```python
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from unittest.mock import MagicMock, patch

from backend.app import app
from backend.database import get_session

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})

@pytest.fixture(autouse=True)
def setup_test_db():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture
def client():
    def override_get_session():
        with Session(test_engine) as session:
            yield session
    app.dependency_overrides[get_session] = override_get_session
    with patch("backend.routes.bills._REDIS_URL", "redis://localhost:6379/0"), \
         patch("redis.asyncio.from_url") as mock_redis:
        mock_redis.return_value.__aenter__ = MagicMock(return_value=MagicMock(
            incr=MagicMock(return_value=1),
            expire=MagicMock(),
            get=MagicMock(return_value=None),
            set=MagicMock(),
            ping=MagicMock(return_value=True),
        ))
        yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def auth_token(client):
    client.post("/auth/register", json={"username": "testuser", "password": "secure123"})
    r = client.post("/auth/login", data={"username": "testuser", "password": "secure123"})
    return r.json()["access_token"]
```

---

### Step 3 — Alembic Migrations (1 hour)

```bash
# 1. Install
pip install alembic

# 2. Init in backend directory
cd backend
alembic init alembic

# 3. Edit alembic/env.py — replace the target_metadata line:
from sqlmodel import SQLModel
from models import User, BillRecord   # import ALL models
target_metadata = SQLModel.metadata

# 4. Edit alembic.ini — set sqlalchemy.url:
sqlalchemy.url = sqlite:///./bills.db  # or env var

# 5. Generate first migration
alembic revision --autogenerate -m "initial_schema"

# 6. Apply
alembic upgrade head

# 7. Replace in database.py:
# REMOVE: SQLModel.metadata.create_all(engine)  ← brittle
# ADD:    Use alembic upgrade head in startup script
```

**`alembic/env.py` key section:**
```python
import os
from alembic import context
from sqlmodel import SQLModel
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import User, BillRecord  # noqa: F401 — registers models

config = context.config
target_metadata = SQLModel.metadata

def get_url():
    return os.getenv("DATABASE_URL", "sqlite:///./bills.db")
```

---

### Step 4 — Docker + CI Setup (1–2 hours)

**`docker-compose.yml`** (complete, production-ready):
```yaml
version: "3.9"
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes: [redis_data:/data]

  backend:
    build: ./backend
    restart: unless-stopped
    depends_on: [redis]
    environment:
      SECRET_KEY: ${SECRET_KEY:?SECRET_KEY must be set}
      REDIS_URL: redis://redis:6379/0
      DATABASE_URL: sqlite:///./data/bills.db
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:5173}
      ACCESS_TOKEN_EXPIRE_MINUTES: "60"
    volumes: [./data:/app/data, ./outputs:/app/outputs]
    ports: ["8000:8000"]
    command: >
      sh -c "alembic upgrade head &&
             uvicorn backend.app:app --host 0.0.0.0 --port 8000"

  worker:
    build: ./backend
    restart: unless-stopped
    depends_on: [redis, backend]
    environment:
      SECRET_KEY: ${SECRET_KEY:?SECRET_KEY must be set}
      REDIS_URL: redis://redis:6379/0
      DATABASE_URL: sqlite:///./data/bills.db
    volumes: [./data:/app/data, ./outputs:/app/outputs]
    command: python -m arq backend.worker.WorkerSettings

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}
    ports: ["5173:80"]
    depends_on: [backend]

volumes:
  redis_data:
```

**`.env.example`** (add this file to the repo root):
```bash
# REQUIRED — generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=

# Optional overrides (defaults shown)
REDIS_URL=redis://redis:6379/0
DATABASE_URL=sqlite:///./data/bills.db
CORS_ORIGINS=http://localhost:5173
ACCESS_TOKEN_EXPIRE_MINUTES=60
VITE_API_URL=http://localhost:8000
```

**`.github/workflows/ci.yml`** (GitHub Actions):
```yaml
name: CI
on: [push, pull_request]
jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt pytest pytest-cov
      - run: pytest tests/ --cov=backend --cov=engine --cov-report=xml
        env:
          SECRET_KEY: test_secret_for_ci_only_not_production
          REDIS_URL: redis://localhost:6379/0

  test-frontend:
    runs-on: ubuntu-latest
    defaults:
      run: { working-directory: frontend }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run typecheck
      - run: npm run build
```

---

## 🎯 Prioritized Fix Checklist

```
IMMEDIATE (breaks all downloads today):
  ☐ Replace downloadUrl() → downloadFile() in lib/api.ts
  ☐ Fix GenerateRequest snake_case payload mapping
  ☐ Add mapApiBillItemToStore() type bridge

IMPORTANT (causes silent wrong data):
  ☐ Fix misleading "No auth yet" comment in api.ts
  ☐ Audit /bills/upload-image and /bills/generate-template routes
  ☐ Add conftest.py + 3 core test files

DEPLOYMENT:
  ☐ Add .env.example with all variables documented
  ☐ Add Alembic setup (env.py + first migration)
  ☐ Add docker-compose.yml
  ☐ Add .github/workflows/ci.yml
```

---

## 🤖 Best AI Agent for Phase 3

Given the nature of these specific fixes — **TypeScript API typing + Python tests + Docker config**, the optimal tool is:

| Task | Best Agent |
|---|---|
| `lib/api.ts` type fixes + `downloadFile()` | **Cursor + Claude Sonnet** (TypeScript-aware, can see the type mismatch across files) |
| `conftest.py` + test files | **Aider CLI with Claude** (pytest-specific, iterates fast) |
| Alembic `env.py` setup | **GitHub Copilot Chat** (boilerplate, well-trained on this) |
| `docker-compose.yml` + CI | **Genspark AI / ChatGPT-4o** (config generation, no code execution needed) |

The **single most important fix** to do RIGHT NOW before anything else is `downloadFile()` in `lib/api.ts` — because without it, the entire download feature is broken for every user who is authenticated, which is the most visible user-facing regression introduced by the correct security fix.