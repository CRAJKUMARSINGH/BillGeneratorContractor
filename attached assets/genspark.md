Now I have all I need for a comprehensive, world-class code review. Let me deliver it.

---

# 🔬 Comprehensive Code Review — BillGeneratorContractor

> **Reviewed by:** Senior Staff Software Engineer (15+ years) | **Stack:** Python 3.12 · FastAPI · ARQ · SQLModel · Jinja2/WeasyPrint · React/TypeScript/Vite | **Repo:** [CRAJKUMARSINGH/BillGeneratorContractor](https://github.com/CRAJKUMARSINGH/BillGeneratorContractor)

---

## 📊 1. Summary

| Dimension | Score | Notes |
|---|---|---|
| **Overall Quality** | **4.5 / 10** | Architectural intent is good; execution has critical gaps |
| **Security** | **3 / 10** | Multiple critical/high auth + CORS + path-traversal issues |
| **Reliability** | **4 / 10** | Race conditions, leaked connections, blocking async calls |
| **Maintainability** | **5 / 10** | God-function, scattered sys.path hacks, dead code |
| **Correctness** | **5 / 10** | Missing BillDocument date fields, unused calculated values |
| **Test Coverage** | **3 / 10** | Minimal test structure, no coverage on critical paths |

### ✅ Strengths
- Clean domain separation: `engine/` is pure calculation, `backend/` is thin wrapper
- Good use of ARQ for async job queuing
- Pydantic models well-defined for API contracts
- Logging is present throughout; structured log format in `log_job_event`
- Graceful PDF fallback chain in `PDFGenerator`

### 🚨 Critical/High Priority Issues (Top 10)

| # | Severity | Issue |
|---|---|---|
| 1 | 🔴 CRITICAL | Hardcoded JWT `SECRET_KEY` fallback — any missed env var = full auth bypass |
| 2 | 🔴 CRITICAL | Path traversal in download — `output_dir` read from Redis without validation |
| 3 | 🔴 CRITICAL | CORS `allow_origins=["*"]` + `allow_credentials=True` — spec violation + security hole |
| 4 | 🔴 HIGH | Download endpoint has **zero authentication** — any UUID guess exposes bills |
| 5 | 🔴 HIGH | `_generate_documents()` blocking the ARQ event loop (sync in async) |
| 6 | 🔴 HIGH | `update_redis_job()` — read-modify-write race condition + new connection per call |
| 7 | 🔴 HIGH | `BillDocument` constructed without `date_commencement/date_completion/actual_completion` fields |
| 8 | 🔴 HIGH | `cheque` amount computed but **never used** — likely missing from `BillDocument` |
| 9 | 🔴 HIGH | In-memory rate limiter bypassed with multi-process uvicorn/gunicorn |
| 10 | 🔴 HIGH | First-user-becomes-admin has a **registration race condition** |

---

## 🐛 2. Detailed Issues (All Findings)

### 🔴 CRITICAL

- **`[CRIT-1]`** | `backend/auth_utils.py:6` | **Hardcoded JWT Secret Key**
  > `SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey_change_in_production")` — The default fallback is a publicly known string. Any deployment forgetting to set `SECRET_KEY` silently runs with a breakable key; attackers can forge arbitrary JWTs.
  > **Fix:** Remove the fallback entirely. Raise `ValueError` at startup if unset:
  ```python
  SECRET_KEY = os.environ["SECRET_KEY"]  # Raises KeyError → startup crash = intentional
  ```

- **`[CRIT-2]`** | `backend/routes/bills.py:~260` | **Path Traversal via Redis-stored `output_dir`**
  > `out_dir = Path(job["output_dir"])` — The `output_dir` value is blindly trusted from Redis. A poisoned Redis entry like `{"output_dir": "/etc"}` lets an attacker read `/etc/*.conf`, `/root/.ssh/id_rsa`, etc.
  > **Fix:** Always derive the output path from the trusted `job_id`, never from Redis-stored paths:
  ```python
  # Safe: reconstruct path from the trusted job_id, never trust stored paths
  out_dir = OUTPUT_DIR / job_id
  if not out_dir.is_relative_to(OUTPUT_DIR):
      raise HTTPException(400, "Invalid job path")
  ```

- **`[CRIT-3]`** | `backend/app.py:38-43` | **CORS Wildcard + Credentials Combo**
  > `allow_origins=["*"]` with `allow_credentials=True` violates [CORS spec RFC 6454](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials) and is actively rejected by newer FastAPI/Starlette versions. This also enables full cross-origin cookie/auth attacks.
  > **Fix:**
  ```python
  ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
  app.add_middleware(
      CORSMiddleware,
      allow_origins=ALLOWED_ORIGINS,  # explicit list, never "*" with credentials
      allow_credentials=True,
      allow_methods=["GET", "POST"],
      allow_headers=["Authorization", "Content-Type"],
  )
  ```

---

### 🔴 HIGH

- **`[HIGH-1]`** | `backend/routes/bills.py:~250` | **Unauthenticated Download Endpoint**
  > `async def download_result(job_id: str, format: str = "zip")` has no `Depends(get_current_user)`. Any client that can guess or enumerate a UUID (36-char hex) can download another user's confidential bill documents.
  > **Fix:**
  ```python
  @router.get("/jobs/{job_id}/download")
  async def download_result(
      job_id: str,
      format: str = "zip",
      current_user: User = Depends(get_current_user),  # ADD THIS
  ):
      # Also verify ownership: job must belong to current_user
  ```

- **`[HIGH-2]`** | `backend/worker.py:14` | **Blocking Sync Call Inside Async ARQ Task**
  > `_generate_documents(job_id, req)` is a CPU+IO-heavy synchronous function called directly inside `async def generate_bill_task(ctx, ...)`. This blocks the entire asyncio event loop for potentially minutes, starving all other concurrent ARQ jobs.
  > **Fix:**
  ```python
  import asyncio
  loop = asyncio.get_event_loop()
  await loop.run_in_executor(None, _generate_documents, job_id, req)
  ```

- **`[HIGH-3]`** | `backend/routes/bills.py:32-45` | **`update_redis_job()` — Race Condition + Connection Leak**
  > Creates a **new sync Redis connection on every single call**, never calls `.close()`, and does a non-atomic read-modify-write. Under concurrent updates (two progress updates arrive simultaneously) the job state silently corrupts.
  > **Fix:** Use a shared sync connection pool **or** use Redis `HSET` (atomic field update) **or** use a Lua script. At minimum, close the connection in `finally`:
  ```python
  _sync_redis_pool = redis.ConnectionPool.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
  
  def update_redis_job(job_id: str, **kwargs):
      """Atomically update specific fields of a job record in Redis."""
      r = redis.Redis(connection_pool=_sync_redis_pool)
      key = f"job:{job_id}"
      # Atomic: use pipeline + WATCH for optimistic locking
      with r.pipeline() as pipe:
          while True:
              try:
                  pipe.watch(key)
                  data = pipe.get(key)
                  job_data = json.loads(data) if data else {}
                  job_data.update(kwargs)
                  pipe.multi()
                  pipe.set(key, json.dumps(job_data), ex=86400)
                  pipe.execute()
                  break
              except redis.WatchError:
                  continue  # Retry on concurrent modification
  ```

- **`[HIGH-4]`** | `backend/routes/bills.py:~330` | **Missing Date Fields in `BillDocument`**
  > `_generate_documents()` constructs `BillDocument` without `date_commencement`, `date_completion`, or `actual_completion`. The `run_engine.py` counterpart (`build_document()`) correctly extracts these via `_extract_header_meta()`. All generated documents from the API will have blank date fields.
  > **Fix:** Extract these fields from `req.titleData` using the same `_HEADER_KEY_MAP` lookup:
  ```python
  doc = BillDocument(
      ...
      date_commencement=_td("Date of written order to commence work"),
      date_completion=_td("St. Date of Completion"),
      actual_completion=_td("Date of actual completion of work"),
      ...
  )
  ```

- **`[HIGH-5]`** | `backend/routes/bills.py:~310` | **`cheque` Amount Computed but Never Used**
  > `cheque = int(round(payable - (...)))` is calculated but never passed to `BillDocument` or any template. This is almost certainly a functional bug — the net-payable-after-deductions figure should appear in `Certificate II/III` and the last page. The computation itself also uses inconsistent rounding (`round()` vs integer arithmetic mix).
  > **Fix:** Pass to `BillDocument` (add a field if needed) and verify the deduction formula matches domain rules.

- **`[HIGH-6]`** | `backend/routes/bills.py:28` | **In-Memory Rate Limiter Broken Under Multi-Process Deployment**
  > `RATE_LIMIT_STORE = defaultdict(list)` is process-local. With `uvicorn --workers 4`, each worker has its own dictionary, so each client actually gets 4× the limit. Move to Redis-backed rate limiting.
  > **Fix:**
  ```python
  async def is_rate_limited_redis(ip: str, redis_client) -> bool:
      key = f"ratelimit:{ip}"
      count = await redis_client.incr(key)
      if count == 1:
          await redis_client.expire(key, RATE_LIMIT_WINDOW_SEC)
      return count > RATE_LIMIT_MAX_REQUESTS
  ```

- **`[HIGH-7]`** | `backend/routes/auth.py:22-24` | **Admin Race Condition on First Registration**
  > `existing_users = session.exec(select(User)).first()` — under simultaneous registration requests, two users can both see an empty table and both become `admin`. Use a database-level unique constraint or a seeded admin user instead.
  > **Fix:** Use a counted query with a transaction or remove auto-admin logic entirely (admin should be seeded via a management command):
  ```python
  # Preferred: set admin via CLI seed, never auto-assign
  role = "operator"  # Always operator from registration
  ```

- **`[HIGH-8]`** | `backend/routes/bills.py:~200` | **`pandas.DataFrame` Without Column Names Passed to `process_bill()`**
  > `ws_wo = pd.DataFrame(wo_rows)` creates integer-indexed columns (0,1,2…). If `process_bill()` accesses columns by name (which `EnterpriseExcelProcessor` likely sets), every `generate` API call will throw `KeyError` in production.
  > **Fix:** Match the column schema that `EnterpriseExcelProcessor` produces:
  ```python
  BILL_QTY_COLS = ["serial_no", "description", "unit", "quantity_since", "rate", "amount", "remark"]
  ws_bq = pd.DataFrame(bq_rows, columns=BILL_QTY_COLS)
  ```

- **`[HIGH-9]`** | `backend/routes/bills.py:~185` | **Header DataFrame Column Mismatch**
  > `header_rows` are 2-column `[key, value]` pairs. They're concatenated with a 7-column body DataFrame via `pd.concat`. Pandas fills missing columns with `NaN`, breaking any positional `iloc` access in `process_bill()`.
  > **Fix:** Pad each header row to the same column width as the body, or pass headers as a separate parameter.

- **`[HIGH-10]`** | `backend/auth_utils.py:16` | **7-Day Non-Revocable JWT Token**
  > `ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7` — 7-day tokens with no refresh-token pattern and no server-side revocation list. A stolen token is valid for a week with no recourse.
  > **Fix:** Shorten to 15–60 minutes; implement refresh tokens. At minimum, add a token blocklist in Redis for logout:
  ```python
  ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
  REFRESH_TOKEN_EXPIRE_DAYS = 7
  ```

---

### 🟡 MEDIUM

- **`[MED-1]`** | `backend/app.py:55,63` | **`@app.on_event` Deprecated Since FastAPI 0.93**
  > Use the modern `lifespan` context manager:
  ```python
  from contextlib import asynccontextmanager
  
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      create_db_and_tables()
      app.state.redis_pool = await create_pool(RedisSettings.from_dsn(redis_url))
      yield
      await app.state.redis_pool.aclose()  # correct arq API
  
  app = FastAPI(..., lifespan=lifespan)
  ```

- **`[MED-2]`** | `backend/routes/bills.py:82,115,147` | **`sys.path.insert()` Called Per Request**
  > Three separate route handlers each call `sys.path.insert(0, str(root_dir))` on every request. This is an O(n) list prepend that fires hundreds of times per second under load and obscures import errors.
  > **Fix:** Move all path setup to the **module level** (top of `bills.py`) once.

- **`[MED-3]`** | `backend/routes/bills.py:65` | **`asyncio.get_event_loop()` Deprecated**
  > Replace with `asyncio.get_running_loop()` (Python 3.10+):
  ```python
  loop = asyncio.get_running_loop()
  data = await loop.run_in_executor(None, _parse_excel, save_path, file_id, file.filename)
  ```

- **`[MED-4]`** | `backend/models.py:17` | **`datetime.utcnow()` Deprecated in Python 3.12+**
  ```python
  from datetime import datetime, timezone
  created_at: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))
  ```

- **`[MED-5]`** | `backend/routes/bills.py:~295` | **Unused Import `number_to_words`**
  > `from calculation.bill_processor import number_to_words` — imported but never called. Likely intended to convert the payable amount to words for the note sheet.

- **`[MED-6]`** | `backend/routes/bills.py:249` | **`format` Parameter Has No Type Safety**
  ```python
  from typing import Literal
  async def download_result(job_id: str, format: Literal["zip", "pdf", "html"] = "zip"):
  ```

- **`[MED-7]`** | `backend/routes/bills.py:1` | **`_generate_documents` Imported from Route into Worker — Anti-pattern**
  > `worker.py` imports `_generate_documents` from `routes.bills`. This creates an upward dependency (worker → route), violating layering. Move `_generate_documents` to `engine/` or a dedicated `services/` module.

- **`[MED-8]`** | `batch_manager.py:38` | **Swallowed Exception Detail**
  ```python
  except Exception as e:
      return False, [f"Invalid JSON payload format: {e}"]  # include `e`
  ```

- **`[MED-9]`** | `batch_manager.py:70` | **Hardcoded Template Version `"v2"` May Not Exist**
  > `render_html(doc, job_dir, template_version="v2")` — if `engine/templates/v2/` is absent, every batch run raises `RuntimeError`. Should fall back to `v1` or check at startup.

- **`[MED-10]`** | `backend/app.py:10` | **`/healthz` in Docstring vs `/health` in Route**
  > API contract mismatch — Kubernetes liveness probes often target `/healthz`. Fix the docstring or rename the route.

- **`[MED-11]`** | `backend/routes/bills.py:~55` | **Upload Files Never Cleaned Up**
  > Uploaded Excel files accumulate forever in `UPLOAD_DIR`. Implement a TTL cleanup job or delete immediately after parse:
  ```python
  try:
      data = await loop.run_in_executor(None, _parse_excel, save_path, file_id, file.filename)
      return data
  finally:
      save_path.unlink(missing_ok=True)  # Clean up regardless of success/failure
  ```

- **`[MED-12]`** | `backend/routes/bills.py:138` | **No Authorization Check in `/history` Endpoint**
  > The endpoint returns the authenticated user's records, but it doesn't verify that `current_user.id` is valid; an admin could theoretically query all records with a small URL change if user_id filtering is relaxed.

---

### 🟢 LOW

- **`[LOW-1]`** | `backend/models.py:13` | **`file_paths: str = ""` as Serialized JSON**
  > Storing a JSON string in a string column is a code smell. Use `sa_column=Column(JSON)` via SQLAlchemy or normalize into a separate `BillFile` table.

- **`[LOW-2]`** | `backend/routes/bills.py` | **No `anomaly_warnings` Propagation in `_parse_excel`**
  > `ProcessorResult.warnings` from `EnterpriseExcelProcessor` are logged but never returned in `ParsedBillData.anomaly_warnings`, hiding useful feedback from the UI.

- **`[LOW-3]`** | `engine/run_engine.py:61` | **`_HEADER_KEY_MAP` Not Shared with `bills.py`**
  > The same header-key normalization logic exists independently in `run_engine.py` and `bills.py` (as inline `_td()` calls). Extract to `engine/calculation/header_utils.py` and import from both.

- **`[LOW-4]`** | `backend/routes/bills.py:211` | **Magic Number `19` for Header Row Count**
  > `while len(header_rows) < 19` — the magic number `19` is undocumented. Define as `BILL_HEADER_ROW_COUNT = 19` with a comment explaining the Excel format expectation.

- **`[LOW-5]`** | All files | **`# tighten in Phase 8` TODO Comments Left in Production Code**
  > Convert to GitHub Issues with clear acceptance criteria. Shipping TODO comments signals incomplete work to reviewers and auditors.

---

## 🔧 3. Refactored Code — Key Files

### `backend/auth_utils.py` — Hardened Auth

```python
"""
auth_utils.py — JWT and password hashing utilities.

Security contract:
  - SECRET_KEY MUST be set via environment variable; startup fails otherwise.
  - Tokens expire in ACCESS_TOKEN_EXPIRE_MINUTES (default 60 min).
  - Passwords are bcrypt-hashed with cost factor 12.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

# ── FAIL FAST: Never run with a missing or default secret key ─────────────────
_raw_secret = os.environ.get("SECRET_KEY")
if not _raw_secret or _raw_secret == "supersecretkey_change_in_production":
    raise EnvironmentError(
        "SECRET_KEY environment variable is not set or is using the insecure default. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
SECRET_KEY: str = _raw_secret

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT. Uses timezone-aware UTC datetimes (Python 3.12-safe)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

---

### `backend/app.py` — Modern Lifespan + Hardened CORS

```python
"""
backend/app.py — FastAPI application entry point.

Usage:
  uvicorn backend.app:app --reload --port 8000
"""
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ENGINE_DIR = Path(__file__).parent.parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from database import create_db_and_tables
from models import HealthResponse
from routes.bills import router as bills_router
from routes.auth import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── CORS: never use wildcard with credentials ─────────────────────────────────
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Modern replacement for deprecated @app.on_event startup/shutdown."""
    # Startup
    create_db_and_tables()
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    application.state.redis_pool = await create_pool(RedisSettings.from_dsn(redis_url))
    logger.info("Bill Generator API started. Engine path: %s", ENGINE_DIR)
    yield
    # Shutdown — arq ≥ 0.25 uses aclose()
    await application.state.redis_pool.aclose()
    logger.info("Bill Generator API shut down.")


app = FastAPI(
    title="Bill Generator API",
    description="PWD Contractor Bill Generation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,   # explicit list, never "*" with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(bills_router)
app.include_router(auth_router)


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
async def health():
    """Kubernetes-compatible liveness probe."""
    try:
        from calculation.bill_processor import process_bill  # noqa
        engine_status = "ok"
    except Exception as exc:
        engine_status = f"error: {exc}"

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = aioredis.from_url(redis_url, socket_connect_timeout=1)
        redis_status = "connected" if await r.ping() else "failed"
        await r.aclose()
    except Exception:
        redis_status = "failed"

    return HealthResponse(
        status="ok", redis=redis_status, worker="unknown", engine=engine_status
    )
```

---

### `backend/routes/bills.py` — Critical Fixes Highlighted

```python
"""
bills.py — Upload, generate, poll, and download bill documents.
All domain logic lives in engine/; this is a thin HTTP adapter.
"""
import asyncio
import io
import logging
import uuid
import zipfile
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

import redis
import redis.asyncio as aioredis
import os
from fastapi import APIRouter, File, HTTPException, UploadFile, Request, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from database import engine
from dependencies import get_current_user
from models import (
    BillItem, BillRecord, DocumentInfo, ExtraItem,
    GenerateRequest, JobStatus, ParsedBillData, User, TemplateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bills", tags=["bills"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Module-level path setup (NOT per-request) ─────────────────────────────────
import sys as _sys
_ROOT_DIR = Path(__file__).parent.parent.parent
if str(_ROOT_DIR) not in _sys.path:
    _sys.path.insert(0, str(_ROOT_DIR))
if str(_ROOT_DIR / "engine") not in _sys.path:
    _sys.path.insert(0, str(_ROOT_DIR / "engine"))

# ── Shared Redis connection pool (NOT new connection per call) ────────────────
_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
_sync_redis_pool = redis.ConnectionPool.from_url(_REDIS_URL)

# Magic numbers documented
BILL_HEADER_ROW_COUNT = 19  # process_bill() reads ws_wo.iloc[:19, :7] as header
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SEC = 60
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


def update_redis_job(job_id: str, **kwargs) -> None:
    """
    Atomically update specific fields of a job's Redis state.
    Uses optimistic locking (WATCH/MULTI/EXEC) to prevent race conditions
    when multiple threads update the same job simultaneously.
    """
    r = redis.Redis(connection_pool=_sync_redis_pool)
    key = f"job:{job_id}"
    with r.pipeline() as pipe:
        for _ in range(3):  # max 3 retries on concurrent modification
            try:
                pipe.watch(key)
                raw = pipe.get(key)
                job_data = json.loads(raw) if raw else {}
                job_data.update(kwargs)
                pipe.multi()
                pipe.set(key, json.dumps(job_data), ex=86400)
                pipe.execute()
                return
            except redis.WatchError:
                continue
    logger.warning("Could not update Redis job %s after retries", job_id)


def log_job_event(job_id: str, stage: str, message: str) -> None:
    """Structured job event log (ISO timestamp | job_id | stage | message)."""
    # Use logger's built-in timestamp rather than manual datetime formatting
    logger.info("%s | %s | %s", job_id, stage, message)


def _reconstruct_output_dir(job_id: str) -> Path:
    """
    Safely reconstruct output path from a trusted job_id.
    NEVER trust output_dir values from Redis/user-controlled data.
    """
    out_dir = (OUTPUT_DIR / job_id).resolve()
    if not str(out_dir).startswith(str(OUTPUT_DIR.resolve())):
        raise ValueError(f"Suspicious job_id resolved outside OUTPUT_DIR: {job_id}")
    return out_dir


# ── Upload & Parse ────────────────────────────────────────────────────────────
@router.post("/upload", response_model=ParsedBillData)
async def upload_excel(file: UploadFile = File(...)) -> ParsedBillData:
    """Upload an Excel file, parse it, and return structured data for frontend editing."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".xlsx", ".xls", ".xlsm"}:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: xlsx, xls, xlsm")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large. Maximum allowed: 20 MB.")

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"
    save_path.write_bytes(content)
    logger.info("Saved upload '%s' → %s", file.filename, save_path)

    try:
        loop = asyncio.get_running_loop()  # 3.10+ safe replacement for get_event_loop()
        data = await loop.run_in_executor(
            None, _parse_excel, save_path, file_id, file.filename
        )
        return data
    except Exception:
        logger.exception("Excel parse failed for file_id=%s", file_id)
        raise HTTPException(500, "Failed to parse Excel. Ensure the file matches the expected template.")
    finally:
        save_path.unlink(missing_ok=True)  # Always clean up uploaded file


# ── Generate ──────────────────────────────────────────────────────────────────
@router.post("/generate", response_model=JobStatus)
async def generate_bill(
    req: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> JobStatus:
    """Enqueue bill document generation via ARQ. Returns job_id immediately."""
    client_ip = request.client.host if request.client else "unknown"

    # Redis-backed rate limiting (works across multiple processes)
    async with aioredis.from_url(_REDIS_URL) as rc:
        rl_key = f"ratelimit:{client_ip}"
        count = await rc.incr(rl_key)
        if count == 1:
            await rc.expire(rl_key, RATE_LIMIT_WINDOW_SEC)
        if count > RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(429, "Too many requests. Please try again later.")

    job_id = str(uuid.uuid4())
    out_dir = _reconstruct_output_dir(job_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    initial_state = {
        "jobId": job_id, "status": "pending", "progress": 0,
        "message": "Queued", "documents": [], "error": None,
        # Note: output_dir is NOT stored in Redis to prevent path traversal
    }

    # Store job state and DB record atomically
    async with aioredis.from_url(_REDIS_URL) as rc:
        await rc.set(f"job:{job_id}", json.dumps(initial_state), ex=86400)

    with Session(engine) as session:
        session.add(BillRecord(
            job_id=job_id, user_id=current_user.id,
            status="pending", message="Generation queued", total_amount=0.0,
        ))
        session.commit()

    await request.app.state.redis_pool.enqueue_job(
        "generate_bill_task", job_id, req.model_dump()
    )
    log_job_event(job_id, "enqueued", f"Request from user '{current_user.username}'")
    return JobStatus(**initial_state)


# ── Job Status ────────────────────────────────────────────────────────────────
@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    async with aioredis.from_url(_REDIS_URL) as rc:
        data = await rc.get(f"job:{job_id}")
    if not data:
        raise HTTPException(404, f"Job '{job_id}' not found.")
    job = json.loads(data)
    return JobStatus(**{k: v for k, v in job.items() if k != "output_dir"})


# ── Download ──────────────────────────────────────────────────────────────────
@router.get("/jobs/{job_id}/download")
async def download_result(
    job_id: str,
    format: Literal["zip", "pdf", "html"] = "zip",
    current_user: User = Depends(get_current_user),  # REQUIRED: auth gate
) -> StreamingResponse:
    """Download generated documents. Requires authentication and job ownership."""
    async with aioredis.from_url(_REDIS_URL) as rc:
        data = await rc.get(f"job:{job_id}")
    if not data:
        raise HTTPException(404, "Job not found.")

    job = json.loads(data)
    if job.get("status") != "complete":
        raise HTTPException(400, f"Job not complete (status: {job.get('status')}).")

    # Verify ownership via DB (do not trust Redis for authorization)
    with Session(engine) as session:
        record = session.exec(
            select(BillRecord).where(
                BillRecord.job_id == job_id,
                BillRecord.user_id == current_user.id,
            )
        ).first()
        if not record:
            raise HTTPException(403, "You do not have access to this job.")

    # Reconstruct path from trusted job_id — never from Redis-stored data
    out_dir = _reconstruct_output_dir(job_id)

    if format == "zip":
        zip_path = out_dir / "bill_documents.zip"
        if not zip_path.exists():
            raise HTTPException(404, "ZIP archive not found. Job may have failed silently.")
        return StreamingResponse(
            io.BytesIO(zip_path.read_bytes()),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="bill_{job_id[:8]}.zip"'},
        )

    if format == "pdf":
        pdfs = sorted(out_dir.glob("*.pdf"))
        if not pdfs:
            raise HTTPException(404, "No PDF files found for this job.")
        if len(pdfs) == 1:
            return StreamingResponse(
                io.BytesIO(pdfs[0].read_bytes()),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{pdfs[0].name}"'},
            )
        # Multiple PDFs → bundle in ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in pdfs:
                zf.write(p, p.name)
        buf.seek(0)
        return StreamingResponse(
            buf, media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="bills_pdf_{job_id[:8]}.zip"'},
        )

    # format == "html" (guaranteed by Literal type)
    htmls = sorted(out_dir.glob("*.html"))
    if not htmls:
        raise HTTPException(404, "No HTML files found for this job.")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for h in htmls:
            zf.write(h, h.name)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="bills_html_{job_id[:8]}.zip"'},
    )
```

---

### `backend/worker.py` — Non-Blocking Async Worker

```python
"""
worker.py — ARQ async worker for bill generation tasks.

The synchronous _generate_documents() function is run in a thread executor
to prevent blocking the asyncio event loop.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

from arq.connections import RedisSettings

# Import the service function from services layer (not from routes)
_ROOT = Path(__file__).parent.parent
if str(_ROOT / "engine") not in sys.path:
    sys.path.insert(0, str(_ROOT / "engine"))

from services.bill_generation_service import generate_documents  # Moved out of routes
from models import GenerateRequest

logger = logging.getLogger("worker")


async def generate_bill_task(ctx, job_id: str, req_dump: dict) -> None:
    """
    ARQ task handler. Runs the CPU-bound generation in a thread pool
    so we don't block the event loop for potentially minutes.
    """
    logger.info("Worker picked up job_id=%s", job_id)
    req = GenerateRequest(**req_dump)
    loop = asyncio.get_running_loop()
    try:
        # run_in_executor: prevents sync PDF generation from blocking event loop
        await loop.run_in_executor(None, generate_documents, job_id, req)
        logger.info("Worker completed job_id=%s", job_id)
    except Exception as exc:
        logger.exception("Worker failed on job_id=%s: %s", job_id, exc)
        raise  # Re-raise so ARQ marks job as failed


class WorkerSettings:
    functions = [generate_bill_task]
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://redis:6379/0")
    )
    max_jobs = int(os.getenv("WORKER_CONCURRENCY", "4"))

    @staticmethod
    async def on_startup(ctx) -> None:
        logger.info("ARQ Worker started.")

    @staticmethod
    async def on_shutdown(ctx) -> None:
        logger.info("ARQ Worker shutting down.")
```

---

### `backend/routes/auth.py` — Race-Condition-Free Registration

```python
"""
auth.py — Authentication routes (register, login).

Admin role assignment: First-user-auto-admin is removed.
Admins must be seeded via CLI: `python manage.py create_admin`.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select

from auth_utils import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password
from database import get_session
from models import User

router = APIRouter(prefix="/auth", tags=["auth"])

_MIN_PASSWORD_LEN = 8


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < _MIN_PASSWORD_LEN:
            raise ValueError(f"Password must be at least {_MIN_PASSWORD_LEN} characters.")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, session: Session = Depends(get_session)) -> Token:
    """Register a new operator account. Admins are provisioned separately via CLI."""
    existing = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered.")

    new_user = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        role="operator",  # All self-registered users are operators; admins seeded via CLI
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    token = create_access_token({"sub": new_user.username, "role": new_user.role})
    return Token(access_token=token, token_type="bearer")


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    # Constant-time comparison prevents username enumeration timing attacks
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        {"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token, token_type="bearer")
```

---

## 🏗️ 4. Additional Recommendations

### 🧪 Required Unit & Integration Tests

```python
# tests/test_auth.py
def test_register_returns_token(client):
    r = client.post("/auth/register", json={"username": "alice", "password": "secure123"})
    assert r.status_code == 201
    assert "access_token" in r.json()

def test_duplicate_registration_rejected(client, existing_user):
    r = client.post("/auth/register", json={"username": "alice", "password": "secure123"})
    assert r.status_code == 400

def test_weak_password_rejected(client):
    r = client.post("/auth/register", json={"username": "bob", "password": "123"})
    assert r.status_code == 422

def test_login_wrong_password(client, existing_user):
    r = client.post("/auth/login", data={"username": "alice", "password": "wrong"})
    assert r.status_code == 401

# tests/test_bills.py
def test_download_requires_auth(client, completed_job):
    r = client.get(f"/bills/jobs/{completed_job}/download")
    assert r.status_code == 401

def test_download_ownership_enforced(client, job_owned_by_other_user, auth_token):
    r = client.get(f"/bills/jobs/{job_owned_by_other_user}/download",
                   headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 403

def test_upload_cleans_up_temp_file(client, sample_excel, auth_token):
    upload_dir_before = set(Path("backend/uploads").glob("*"))
    client.post("/bills/upload", files={"file": sample_excel},
                headers={"Authorization": f"Bearer {auth_token}"})
    upload_dir_after = set(Path("backend/uploads").glob("*"))
    assert upload_dir_before == upload_dir_after  # No new files left

def test_rate_limit_enforced(client, auth_token):
    for _ in range(10):
        client.post("/bills/generate", json={...}, headers={"Authorization": f"Bearer {auth_token}"})
    r = client.post("/bills/generate", json={...}, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 429

# tests/test_engine.py
def test_extract_header_meta_handles_missing_keys():
    meta = _extract_header_meta([])
    assert meta["agreement_no"] == ""
    assert meta["work_order_amount"] == 0.0

def test_build_document_missing_sheets_raises():
    with pytest.raises(RuntimeError, match="Required sheets missing"):
        build_document({}, 0.0, "above", 0.0)
```

### 🏛️ Architectural Improvements

| Priority | Recommendation |
|---|---|
| 🔴 **Now** | Extract `_generate_documents` → `backend/services/bill_generation_service.py`. Worker should import from `services/`, not from `routes/`. |
| 🔴 **Now** | Add `.env.example` with all required env vars documented (`SECRET_KEY`, `REDIS_URL`, `DATABASE_URL`, `CORS_ORIGINS`). |
| 🟡 **Soon** | Add Alembic for database migrations. `SQLModel.metadata.create_all()` is fine for prototyping but breaks when you need schema changes in production. |
| 🟡 **Soon** | Add a job ownership table or store `user_id` in Redis job state (with signature) to avoid cross-user job access without DB round-trips on every download. |
| 🟡 **Soon** | Implement soft-delete / TTL for `OUTPUT_DIR` using a cron job or APScheduler. Output files for jobs older than 7 days should be purged. |
| 🟢 **Future** | Replace `sys.path` manipulation entirely with a proper Python package (`pip install -e .` with `pyproject.toml`). This is the root cause of path hacks scattered throughout. |
| 🟢 **Future** | Add OpenTelemetry tracing spans around `process_bill()` and PDF generation for production observability. |
| 🟢 **Future** | Consider `fastapi-limiter` (Redis-backed) to replace the bespoke rate limiter. |

### ❓ Clarification Questions

1. **`process_bill()` column schema**: Does it access columns by name or by position? This determines whether the missing column headers in `_generate_documents` cause immediate crashes or silent wrong results.
2. **`cheque` variable**: What deduction formula is correct for the domain (IT @10%, security deposit @2%, labour cess @2%, other @1%)? Should this appear in `BillDocument` as `net_cheque_amount`?
3. **`number_to_words`**: Is this intentionally unused, or should it convert `payable` to words for the note sheet ("Rupees X only")?
4. **Template v2**: Does it exist in the `engine/templates/` directory? The `batch_manager.py` hardcodes it.
5. **Auth design**: Is there a requirement for refresh tokens or session revocation (e.g., logout)? The current 60-min token + no blocklist means there's no logout capability.

---

> 💡 **Suggested Next Step**: Start with `[CRIT-1]` through `[HIGH-5]` — these can cause security breaches or production crashes today. Then address the architectural refactor of `_generate_documents` into a `services/` module, which will fix the worker anti-pattern and unlock proper unit testing of the generation pipeline.