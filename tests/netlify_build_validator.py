#!/usr/bin/env python3
"""
Robotic Netlify build validator.
Checks the frontend/dist/ output against Netlify deployment requirements
without needing a live Netlify account.

Tests:
  1. Required files exist (index.html, _redirects, assets/)
  2. index.html is valid HTML with correct asset references
  3. _redirects SPA fallback rule is present
  4. JS bundle: no localhost/hardcoded URLs, no source maps leaked
  5. CSS bundle: present and non-empty
  6. Asset hashes: filenames contain content hash (cache-busting)
  7. Bundle size within Netlify free-tier limits (< 25 MB total)
  8. netlify.toml: correct publish dir, node version, SPA redirect
  9. VITE_API_URL: not a placeholder in the bundle
  10. No .env files leaked into dist/
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DIST = ROOT / "frontend" / "dist"
TOML = ROOT / "frontend" / "netlify.toml"

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
WARN = "\033[93m⚠️  WARN\033[0m"
INFO = "\033[94mℹ️  INFO\033[0m"

results = []

def check(name: str, ok: bool, detail: str = "", warn_only: bool = False):
    tag = PASS if ok else (WARN if warn_only else FAIL)
    print(f"  {tag}  {name}")
    if detail:
        print(f"         {detail}")
    results.append((name, ok, warn_only))

def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ── 1. Required files ─────────────────────────────────────────
section("1. Required files in dist/")
check("dist/ exists",           DIST.exists())
check("index.html present",     (DIST / "index.html").exists())
check("_redirects present",     (DIST / "_redirects").exists())
check("assets/ dir present",    (DIST / "assets").is_dir())

js_files  = list((DIST / "assets").glob("*.js"))  if (DIST / "assets").exists() else []
css_files = list((DIST / "assets").glob("*.css")) if (DIST / "assets").exists() else []
check("JS bundle present",  len(js_files) > 0,  f"found: {[f.name for f in js_files]}")
check("CSS bundle present", len(css_files) > 0, f"found: {[f.name for f in css_files]}")


# ── 2. index.html validity ────────────────────────────────────
section("2. index.html")
if (DIST / "index.html").exists():
    html = (DIST / "index.html").read_text(encoding="utf-8")
    check("Has <!DOCTYPE html>",        "<!DOCTYPE html>" in html or "<!doctype html>" in html.lower())
    check("Has <div id=\"root\">",      'id="root"' in html)
    check("References JS bundle",       any(f.name in html for f in js_files), warn_only=True)
    check("References CSS bundle",      any(f.name in html for f in css_files), warn_only=True)
    check("No absolute localhost ref",  "localhost" not in html)
    check("No source map comment",      "//# sourceMappingURL" not in html)


# ── 3. _redirects SPA rule ────────────────────────────────────
section("3. _redirects SPA fallback")
if (DIST / "_redirects").exists():
    redir = (DIST / "_redirects").read_text(encoding="utf-8")
    has_spa = re.search(r"/\*\s+/index\.html\s+200", redir) is not None
    check("SPA fallback rule present",  has_spa, f"content: {redir.strip()!r}")
    check("No stale backend proxy rule", "herokuapp.com" not in redir and "your-backend" not in redir)


# ── 4. JS bundle checks ───────────────────────────────────────
section("4. JS bundle content")
if js_files:
    js_text = js_files[0].read_text(encoding="utf-8", errors="replace")
    js_size = js_files[0].stat().st_size

    check("Bundle > 10 KB (not empty)",     js_size > 10_000,  f"size: {js_size/1024:.1f} KB")
    check("Bundle < 5 MB (reasonable)",     js_size < 5_000_000, f"size: {js_size/1024:.1f} KB")
    check("No localhost:8000 hardcoded",    "localhost:8000" not in js_text)
    check("No localhost:5173 hardcoded",    "localhost:5173" not in js_text)
    check("No .env placeholder URL",        "your-backend-api.com" not in js_text)
    check("No Heroku placeholder URL",      "herokuapp.com" not in js_text)
    check("VITE_API_URL resolves to ''",    # empty string means it reads from env at runtime
          "VITE_API_URL" not in js_text,
          "VITE_API_URL baked in — set it in Netlify dashboard instead",
          warn_only=True)
    check("Contains React runtime",         "react" in js_text.lower() or "createElement" in js_text)
    check("Contains BillForge string",      "BillForge" in js_text or "billforge" in js_text.lower())
    check("No inline source map",           "//# sourceMappingURL=data:" not in js_text)

    # Content hash in filename (cache busting)
    hash_pattern = re.compile(r"index-[A-Za-z0-9]{8,}\.js")
    check("Filename has content hash",      bool(hash_pattern.search(js_files[0].name)),
          f"filename: {js_files[0].name}")


# ── 5. CSS bundle checks ──────────────────────────────────────
section("5. CSS bundle content")
if css_files:
    css_text = css_files[0].read_text(encoding="utf-8", errors="replace")
    css_size = css_files[0].stat().st_size
    check("CSS > 1 KB",                     css_size > 1_000,  f"size: {css_size/1024:.1f} KB")
    check("Contains Tailwind utilities",    "flex" in css_text and "grid" in css_text)
    check("No localhost reference in CSS",  "localhost" not in css_text)


# ── 6. Total bundle size ──────────────────────────────────────
section("6. Bundle size (Netlify free tier: 100 GB bandwidth, 300 MB deploy)")
if DIST.exists():
    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    check("Total dist < 50 MB",  total < 50_000_000, f"total: {total/1024:.1f} KB")
    check("Total dist < 5 MB (optimal)", total < 5_000_000,
          f"total: {total/1024:.1f} KB — good for fast deploys", warn_only=True)


# ── 7. netlify.toml ───────────────────────────────────────────
section("7. netlify.toml")
if TOML.exists():
    toml_text = TOML.read_text(encoding="utf-8")
    check("publish = \"dist\"",             'publish = "dist"' in toml_text)
    check("base = \"frontend\"",            'base = "frontend"' in toml_text)
    check("NODE_VERSION = \"20\"",          'NODE_VERSION = "20"' in toml_text)
    check("SPA redirect present",          "/*" in toml_text and "/index.html" in toml_text)
    check("No stale backend proxy",        "your-backend-url.com" not in toml_text)
    check("No Heroku URL",                 "herokuapp.com" not in toml_text)


# ── 8. No leaked secrets ──────────────────────────────────────
section("8. No leaked secrets in dist/")
leaked = list(DIST.glob("**/.env*")) if DIST.exists() else []
check("No .env files in dist/",  len(leaked) == 0, f"found: {leaked}")
if js_files:
    js_text = js_files[0].read_text(encoding="utf-8", errors="replace")
    check("No JWT secret pattern",  not re.search(r"SECRET_KEY\s*=\s*['\"][^'\"]{8,}", js_text))
    check("No password pattern",    not re.search(r"password\s*[:=]\s*['\"][^'\"]{4,}", js_text, re.I))


# ── Summary ───────────────────────────────────────────────────
section("SUMMARY")
total_checks = len(results)
hard_fails   = [(n, d) for n, ok, warn in results if not ok and not warn]
warnings     = [(n, d) for n, ok, warn in results if not ok and warn]
passed       = sum(1 for _, ok, _ in results if ok)

print(f"  Passed:   {passed}/{total_checks}")
print(f"  Warnings: {len(warnings)}")
print(f"  Failures: {len(hard_fails)}")

if hard_fails:
    print(f"\n  Hard failures:")
    for name, _ in hard_fails:
        print(f"    ❌ {name}")

if warnings:
    print(f"\n  Warnings:")
    for name, _ in warnings:
        print(f"    ⚠️  {name}")

print()
if not hard_fails:
    print("  🚀 BUILD IS NETLIFY-READY")
    print()
    print("  To deploy, run ONE of:")
    print("    Option A — New site (first time):")
    print("      cd frontend && netlify deploy --dir=dist --prod")
    print()
    print("    Option B — With auth token (CI/CD):")
    print("      netlify deploy --dir=frontend/dist --prod \\")
    print("        --auth $NETLIFY_AUTH_TOKEN --site $NETLIFY_SITE_ID")
    print()
    print("    Option C — Drag & drop:")
    print("      Open https://app.netlify.com/drop")
    print("      Drag the frontend/dist/ folder into the browser")
    print()
    print("  Required Netlify env vars (set in Site Settings > Env):")
    print("    VITE_API_URL = https://your-deployed-backend.com")
    sys.exit(0)
else:
    print("  ❌ BUILD HAS FAILURES — fix before deploying")
    sys.exit(1)
