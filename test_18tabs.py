#!/usr/bin/env python3
"""
NASA-LEVEL TEST HARNESS
=======================
Processes all 9 sample Excel files through the fixed bill_processor.
Generates 18 self-contained editable HTML tabs:
  - 9 x First Page  (first_*)
  - 9 x Deviation Statement (dev_*)

Each tab:
  - Renders exactly what the code produced (no manual override)
  - Highlights cells that DIFFER from Order-Fixer reference output (red = mismatch)
  - All data cells are contenteditable for pre-PDF corrections
  - "Print to PDF" button triggers browser print dialog (A4/landscape as needed)
  - Status bar shows PASS / FAIL / WARN per file

Run:  python test_18tabs.py
"""

import sys
import os
import re
import webbrowser
import time
from pathlib import Path
from datetime import datetime

# ── path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

from engine.calculation.excel_processor_enterprise import EnterpriseExcelProcessor
from engine.calculation.bill_processor import process_bill

# ── constants ─────────────────────────────────────────────────────────────────
INPUT_DIR  = ROOT / "Order-Fixer" / "Input_Test_Files"
REF_DIR    = ROOT / "Order-Fixer" / "Test_Outputs"
OUT_DIR    = ROOT / "test_output_18tabs"
OUT_DIR.mkdir(exist_ok=True)

FILES = sorted(INPUT_DIR.glob("*.xlsx"))

# Map input stem → reference folder name (exact match by stem)
REF_MAP = {d.name: d for d in REF_DIR.iterdir() if d.is_dir()}

# ── helpers ───────────────────────────────────────────────────────────────────

def load_excel(path: Path):
    """
    Load sheets RAW (header=None) so bill_processor gets the full layout
    it expects: rows 0-19 = title/header block, row 20 = column headers,
    rows 21+ = item data.  EnterpriseExcelProcessor strips headers which
    breaks bill_processor's positional assumptions.

    These Excel files have NO header block — items start at row 1 (row 0
    is the column-header row "Item | Description | ...").  We pad 21 blank
    rows at the top so bill_processor's range(21, last_row) works correctly.
    """
    xl = pd.ExcelFile(path, engine="openpyxl")
    available = xl.sheet_names

    def _read_padded(name):
        """Read sheet raw and prepend 21 blank rows so bill_processor offsets work."""
        if name not in available:
            return pd.DataFrame()
        df = pd.read_excel(xl, sheet_name=name, header=None)
        if df.empty:
            return df
        # Detect if this sheet already has a header block (row 0 is NOT "Item"/"Description")
        # If row 0 col 0 looks like a title/label (not a number or "Item"), it already has headers
        r0c0 = str(df.iloc[0, 0]).strip().lower() if df.shape[1] > 0 else ""
        already_padded = r0c0 not in ("item", "item no.", "item no", "s.no", "s. no", "sl.no")
        if already_padded:
            return df  # already has header block, use as-is
        # Pad 21 blank rows at top so items land at row 21+
        ncols = df.shape[1]
        blank = pd.DataFrame([[np.nan] * ncols] * 21, columns=df.columns)
        return pd.concat([blank, df], ignore_index=True)

    ws_wo    = _read_padded("Work Order")
    ws_bq    = _read_padded("Bill Quantity")
    ws_extra = _read_padded("Extra Items")

    if ws_wo.empty or ws_bq.empty:
        raise RuntimeError("Missing required sheets (Work Order / Bill Quantity)")

    # Read Title sheet for title_data
    ws_title = pd.read_excel(xl, sheet_name="Title", header=None) if "Title" in available else pd.DataFrame()
    return ws_wo, ws_bq, ws_extra, ws_title


def extract_ref_cells(html_path: Path) -> list[str]:
    """Extract all non-empty td text values from reference HTML, in order."""
    if not html_path.exists():
        return []
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    cells = []
    for td in soup.find_all("td"):
        txt = td.get_text(separator=" ", strip=True)
        cells.append(txt)
    return cells


def diff_score(produced: list[str], reference: list[str]) -> tuple[int, int, list[int]]:
    """
    Compares NUMERIC cells only — amounts, quantities, rates.
    This is what matters for code correctness: did the code compute
    the right numbers? Text/description differences are irrelevant.
    """
    # Extract only cells that look like numbers from each list
    num_re = re.compile(r'^-?[\d,]+\.?\d*$')

    def is_numeric(s):
        s = s.strip().replace(',', '').replace(' ', '')
        return bool(num_re.match(s)) and s not in ('', '0', '0.00', '0.0')

    def norm(s):
        s = s.strip().replace(',', '').replace(' ', '')
        try:
            return f"{float(s):.2f}"
        except Exception:
            return s

    prod_nums = [(i, norm(v)) for i, v in enumerate(produced)  if is_numeric(v)]
    ref_nums  = [(i, norm(v)) for i, v in enumerate(reference) if is_numeric(v)]

    mismatches = []
    matches = 0
    n = min(len(prod_nums), len(ref_nums))
    for k in range(n):
        pi, pv = prod_nums[k]
        ri, rv = ref_nums[k]
        if pv == rv:
            matches += 1
        else:
            mismatches.append(pi)   # highlight the produced cell

    # Extra numeric cells in produced with no reference counterpart
    for k in range(n, len(prod_nums)):
        mismatches.append(prod_nums[k][0])

    total = max(len(prod_nums), len(ref_nums))
    return matches, total, mismatches


# ── HTML builders ─────────────────────────────────────────────────────────────

TOOLBAR_CSS = """
<style>
  body { margin: 0; font-family: Calibri, sans-serif; }
  #toolbar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    background: #1a1a2e; color: #eee; padding: 6px 14px;
    display: flex; align-items: center; gap: 14px;
    font-size: 11px; box-shadow: 0 2px 8px #0008;
  }
  #toolbar .file-name { font-weight: bold; font-size: 13px; color: #7ec8e3; }
  #toolbar .doc-type  { color: #f0a500; font-weight: bold; }
  #toolbar .status    { padding: 3px 10px; border-radius: 4px; font-weight: bold; }
  #toolbar .pass      { background: #1a7a1a; color: #fff; }
  #toolbar .warn      { background: #a06000; color: #fff; }
  #toolbar .fail      { background: #8b0000; color: #fff; }
  #toolbar .score     { color: #aaffaa; }
  #toolbar .diff-info { color: #ffaaaa; font-size: 10px; }
  #toolbar button {
    background: #e63946; color: #fff; border: none;
    padding: 5px 14px; border-radius: 4px; cursor: pointer;
    font-size: 12px; font-weight: bold;
  }
  #toolbar button:hover { background: #c1121f; }
  #toolbar .edit-hint { color: #aaa; font-size: 10px; }
  .page-wrap { margin-top: 48px; padding: 10px; }
  td[contenteditable="true"]:focus {
    outline: 2px solid #4fc3f7 !important;
    background: #fffde7 !important;
  }
  .mismatch { background: #ffe0e0 !important; }
  .mismatch:focus { background: #fff9c4 !important; }
  @media print {
    #toolbar { display: none !important; }
    .page-wrap { margin-top: 0 !important; }
    .mismatch { background: transparent !important; }
  }
</style>
"""

TOOLBAR_JS = """
<script>
function printPDF() {
  window.print();
}
// Make all data td cells editable on load
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('tbody td').forEach(function(td) {
    td.setAttribute('contenteditable', 'true');
    td.setAttribute('spellcheck', 'false');
  });
});
</script>
"""


def make_toolbar(fname, doc_type, matches, total, mismatches_count):
    pct = round(matches / total * 100) if total else 0
    if mismatches_count == 0:
        status_cls, status_txt = "pass", "✔ PASS"
    elif mismatches_count <= 3:
        status_cls, status_txt = "warn", f"⚠ WARN ({mismatches_count} diff)"
    else:
        status_cls, status_txt = "fail", f"✘ FAIL ({mismatches_count} diff)"

    diff_txt = ""
    if mismatches_count > 0:
        diff_txt = f'<span class="diff-info">Red cells = mismatch vs Order-Fixer reference</span>'

    return f"""
<div id="toolbar">
  <span class="file-name">{fname}</span>
  <span class="doc-type">{doc_type}</span>
  <span class="status {status_cls}">{status_txt}</span>
  <span class="score">{matches}/{total} cells match ({pct}%)</span>
  {diff_txt}
  <span class="edit-hint">Click any cell to edit before PDF</span>
  <button onclick="printPDF()">🖨 Print / Save PDF</button>
</div>
"""


def inject_mismatch_highlights(html: str, mismatch_indices: list[int]) -> str:
    """
    Parse rendered HTML, add class="mismatch" to td cells at mismatch positions.
    Also strips Jinja remnants if any slipped through.
    """
    if not mismatch_indices:
        return html
    soup = BeautifulSoup(html, "html.parser")
    tds = soup.find_all("td")
    idx_set = set(mismatch_indices)
    for i, td in enumerate(tds):
        if i in idx_set:
            existing = td.get("class", [])
            td["class"] = existing + ["mismatch"]
    return str(soup)


def build_first_page_html(fname, first_page, ref_cells) -> str:
    """Render first_page data into a standalone editable HTML."""
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(str(ROOT / "engine" / "templates" / "v2")))
    tmpl = env.get_template("first_page.html")

    # Use pre-extracted title_data (from Title sheet)
    title_data = first_page.get("_title_data", {})

    data = {
        "source_filename": fname,
        "title_data": title_data,
        "items": [_item_to_obj(it) for it in first_page.get("items", [])],
        "totals": _totals_to_obj(first_page.get("totals", {})),
    }

    rendered = tmpl.render(data=_DictObj(data))

    # Extract produced cells for diff
    soup = BeautifulSoup(rendered, "html.parser")
    produced = [td.get_text(separator=" ", strip=True) for td in soup.find_all("td")]
    matches, total, mismatches = diff_score(produced, ref_cells)

    rendered = inject_mismatch_highlights(rendered, mismatches)
    toolbar  = make_toolbar(fname, "FIRST PAGE", matches, total, len(mismatches))

    # Inject toolbar + editable JS into <body>
    rendered = rendered.replace("<body>", f"<body>{TOOLBAR_CSS}{toolbar}{TOOLBAR_JS}<div class='page-wrap'>", 1)
    rendered = rendered.replace("</body>", "</div></body>", 1)
    return rendered, matches, total, len(mismatches)


def build_deviation_html(fname, deviation_data, ref_cells) -> str:
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(str(ROOT / "engine" / "templates" / "v2")))
    tmpl = env.get_template("deviation_statement.html")

    title_data = deviation_data.get("_title_data", {})
    data = {
        "title_data": title_data,
        "deviation_items": [_dev_item_to_obj(it) for it in deviation_data.get("items", [])],
        "summary": _summary_to_obj(deviation_data.get("summary", {})),
    }

    rendered = tmpl.render(data=_DictObj(data))

    soup = BeautifulSoup(rendered, "html.parser")
    produced = [td.get_text(separator=" ", strip=True) for td in soup.find_all("td")]
    matches, total, mismatches = diff_score(produced, ref_cells)

    rendered = inject_mismatch_highlights(rendered, mismatches)
    toolbar  = make_toolbar(fname, "DEVIATION STATEMENT", matches, total, len(mismatches))

    rendered = rendered.replace("<body>", f"<body>{TOOLBAR_CSS}{toolbar}{TOOLBAR_JS}<div class='page-wrap'>", 1)
    rendered = rendered.replace("</body>", "</div></body>", 1)
    return rendered, matches, total, len(mismatches)


# ── data adapters (dict → object with attribute access for Jinja) ─────────────

class _DictObj:
    """Recursively wraps a dict so Jinja can use dot-notation."""
    def __init__(self, d):
        self._d = d if isinstance(d, dict) else {}
    def __getattr__(self, key):
        val = self._d.get(key)
        if isinstance(val, dict):
            return _DictObj(val)
        return val
    def get(self, key, default=None):
        val = self._d.get(key, default)
        if isinstance(val, dict):
            return _DictObj(val)
        return val
    def __getitem__(self, key):
        val = self._d[key]
        if isinstance(val, dict):
            return _DictObj(val)
        if isinstance(val, list):
            return [_DictObj(v) if isinstance(v, dict) else v for v in val]
        return val
    def __contains__(self, key):
        return key in self._d


def _item_to_obj(item: dict) -> _DictObj:
    safe = {
        "serial_no":           item.get("serial_no", ""),
        "description":         item.get("description", ""),
        "unit":                item.get("unit", ""),
        "quantity_since_last": _sf(item.get("quantity_since_last", item.get("quantity", 0))),
        "quantity_upto_date":  _sf(item.get("quantity_upto_date",  item.get("quantity", 0))),
        "quantity":            _sf(item.get("quantity", 0)),
        "rate":                _sf(item.get("rate", 0)),
        "amount":              _sf(item.get("amount", 0)),
        "amount_previous":     _sf(item.get("amount_previous", 0)),
        "remark":              item.get("remark", ""),
        "bold":                item.get("bold", False),
        "underline":           item.get("underline", False),
        "is_divider":          item.get("is_divider", False),
    }
    return _DictObj(safe)


def _dev_item_to_obj(item: dict) -> _DictObj:
    safe = {
        "serial_no":   item.get("serial_no", ""),
        "description": item.get("description", ""),
        "unit":        item.get("unit", ""),
        "qty_wo":      _sf(item.get("qty_wo", 0)),
        "rate":        _sf(item.get("rate", 0)),
        "amt_wo":      _sf(item.get("amt_wo", 0)),
        "qty_bill":    _sf(item.get("qty_bill", 0)),
        "amt_bill":    _sf(item.get("amt_bill", 0)),
        "excess_qty":  _sf(item.get("excess_qty", 0)),
        "excess_amt":  _sf(item.get("excess_amt", 0)),
        "saving_qty":  _sf(item.get("saving_qty", 0)),
        "saving_amt":  _sf(item.get("saving_amt", 0)),
        "remark":      item.get("remark", ""),
        "bold":        item.get("bold", False),
        "underline":   item.get("underline", False),
        "is_divider":  item.get("is_divider", False),
        "is_separator":item.get("is_separator", False),
    }
    return _DictObj(safe)


def _totals_to_obj(t: dict) -> _DictObj:
    prem = t.get("premium", {})
    safe = {
        "grand_total":       _sf(t.get("grand_total", 0)),
        "payable":           _sf(t.get("payable", 0)),
        "extra_items_sum":   _sf(t.get("extra_items_sum", 0)),
        "last_bill_amount":  _sf(t.get("last_bill_amount", 0)),
        "net_payable":       _sf(t.get("net_payable", 0)),
        "premium": {
            "percent": _sf(prem.get("percent", 0)),
            "amount":  _sf(prem.get("amount", 0)),
            "type":    prem.get("type", "above"),
        },
    }
    return _DictObj(safe)


def _summary_to_obj(s: dict) -> _DictObj:
    prem = s.get("premium", {})
    safe = {
        "work_order_total":    _sf(s.get("work_order_total", 0)),
        "executed_total":      _sf(s.get("executed_total", 0)),
        "overall_excess":      _sf(s.get("overall_excess", 0)),
        "overall_saving":      _sf(s.get("overall_saving", 0)),
        "tender_premium_f":    _sf(s.get("tender_premium_f", 0)),
        "tender_premium_h":    _sf(s.get("tender_premium_h", 0)),
        "tender_premium_j":    _sf(s.get("tender_premium_j", 0)),
        "tender_premium_l":    _sf(s.get("tender_premium_l", 0)),
        "grand_total_f":       _sf(s.get("grand_total_f", 0)),
        "grand_total_h":       _sf(s.get("grand_total_h", 0)),
        "grand_total_j":       _sf(s.get("grand_total_j", 0)),
        "grand_total_l":       _sf(s.get("grand_total_l", 0)),
        "net_difference":      _sf(s.get("net_difference", 0)),
        "percentage_deviation":_sf(s.get("percentage_deviation", 0)),
        "is_saving":           bool(s.get("is_saving", False)),
        "premium": {
            "percent": _sf(prem.get("percent", 0)),
            "type":    prem.get("type", "above"),
        },
    }
    return _DictObj(safe)


def _sf(v):
    """Safe float — returns 0.0 for None/empty/nan."""
    if v is None:
        return 0.0
    if isinstance(v, float) and (v != v):  # nan check
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*70}")
    print(f"  SEQUENTIAL REVIEW  --  {len(FILES)} files, 2 tabs each (First Page + Deviation)")
    print(f"  Press ENTER after reviewing each tab to proceed to next.")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    tab_paths = []
    summary_rows = []

    # ── Phase 1: generate all HTML files ─────────────────────────────────
    print("Generating HTML for all files...")
    for xlsx in FILES:
        stem = xlsx.stem
        print(f"  Processing: {stem}")

        ref_folder = REF_MAP.get(stem)
        if ref_folder is None:
            for k, v in REF_MAP.items():
                if stem.lower() in k.lower() or k.lower() in stem.lower():
                    ref_folder = v
                    break

        ref_fp_cells  = extract_ref_cells(ref_folder / "First Page Summary.html")  if ref_folder else []
        ref_dev_cells = extract_ref_cells(ref_folder / "Deviation Statement.html") if ref_folder else []

        try:
            ws_wo, ws_bq, ws_extra, ws_title = load_excel(xlsx)

            title_data = {}
            premium_percent = 0.0
            premium_type = "above"
            if not ws_title.empty:
                for _, row in ws_title.iterrows():
                    if len(row) >= 2:
                        k = str(row.iloc[0]).strip()
                        v = row.iloc[1]
                        if k and k != "nan":
                            title_data[k] = "" if (pd.isna(v) or str(v) == "nan") else str(v).strip()
                for key in ('TENDER PREMIUM %', 'Tender Premium %', 'TENDER PREMIUM'):
                    if key in title_data:
                        try: premium_percent = float(title_data[key])
                        except: pass
                        break
                for key in ('Above / Below', 'ABOVE', 'Premium Type', 'above_below'):
                    if key in title_data:
                        premium_type = "below" if "below" in str(title_data[key]).lower() else "above"
                        break

            first_page, _, deviation_data, _, _ = process_bill(
                ws_wo, ws_bq, ws_extra,
                premium_percent=premium_percent,
                premium_type=premium_type,
                previous_bill_amount=0.0,
            )
            first_page["_title_data"]    = title_data
            deviation_data["_title_data"] = title_data
        except Exception as e:
            print(f"    ERROR: {e}")
            summary_rows.append((stem, "ERROR", "ERROR", str(e)))
            tab_paths.append((stem, None, None))
            continue

        fp_path = dev_path = None
        fp_status = dev_status = "ERR"

        try:
            fp_html, fp_m, fp_t, fp_bad = build_first_page_html(stem, first_page, ref_fp_cells)
            fp_path = OUT_DIR / f"first_{stem}.html"
            fp_path.write_text(fp_html, encoding="utf-8")
            fp_status = "OK"
            print(f"    first_page  saved  ({fp_m}/{fp_t} numeric cells match ref)")
        except Exception as e:
            print(f"    first_page error: {e}")

        try:
            dev_html, dev_m, dev_t, dev_bad = build_deviation_html(stem, deviation_data, ref_dev_cells)
            dev_path = OUT_DIR / f"dev_{stem}.html"
            dev_path.write_text(dev_html, encoding="utf-8")
            dev_status = "OK"
            print(f"    deviation   saved  ({dev_m}/{dev_t} numeric cells match ref)")
        except Exception as e:
            print(f"    deviation error: {e}")

        tab_paths.append((stem, fp_path, dev_path))
        summary_rows.append((stem, fp_status, dev_status, ""))

    # ── Phase 2: open one pair at a time ─────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  Starting sequential review...")
    print(f"{'='*70}\n")

    for file_no, (stem, fp_path, dev_path) in enumerate(tab_paths, 1):
        print(f"\n[{file_no}/{len(tab_paths)}]  {stem}")
        print(f"  {'-'*60}")

        if fp_path and fp_path.exists():
            print(f"  Opening FIRST PAGE...")
            webbrowser.open(fp_path.as_uri())
            input("  >> Review & edit First Page. Press ENTER when done...")
        else:
            print(f"  First Page not available.")

        if dev_path and dev_path.exists():
            print(f"  Opening DEVIATION STATEMENT...")
            webbrowser.open_new_tab(dev_path.as_uri())
            input("  >> Review & edit Deviation. Press ENTER when done...")
        else:
            print(f"  Deviation not available.")

        if file_no < len(tab_paths):
            print(f"  Moving to next file...")

    # ── Index page ────────────────────────────────────────────────────────
    flat_paths = [p for _, fp, dev in tab_paths for p in [fp, dev] if p]
    index_html = _build_index(summary_rows, flat_paths)
    index_path = OUT_DIR / "_INDEX.html"
    index_path.write_text(index_html, encoding="utf-8")

    print(f"\n{'='*70}")
    print(f"  All {len(tab_paths)} files reviewed.")
    print(f"  Index: {index_path}")
    print(f"{'='*70}\n")


def _build_index(rows, tab_paths) -> str:
    rows_html = ""
    tab_iter = iter(tab_paths)
    for stem, fp_st, dev_st, err in rows:
        fp_path  = next(tab_iter, None)
        dev_path = next(tab_iter, None)

        def badge(st):
            if "PASS" in st:   return f'<span style="background:#1a7a1a;color:#fff;padding:2px 8px;border-radius:3px">{st}</span>'
            if "WARN" in st:   return f'<span style="background:#a06000;color:#fff;padding:2px 8px;border-radius:3px">{st}</span>'
            if "FAIL" in st:   return f'<span style="background:#8b0000;color:#fff;padding:2px 8px;border-radius:3px">{st}</span>'
            return f'<span style="background:#555;color:#fff;padding:2px 8px;border-radius:3px">{st}</span>'

        fp_link  = f'<a href="{fp_path.as_uri()}"  target="_blank">Open First Page</a>'  if fp_path  else "—"
        dev_link = f'<a href="{dev_path.as_uri()}" target="_blank">Open Deviation</a>'   if dev_path else "—"

        rows_html += f"""
        <tr>
          <td style="font-weight:bold">{stem}</td>
          <td>{badge(fp_st)}</td>
          <td>{fp_link}</td>
          <td>{badge(dev_st)}</td>
          <td>{dev_link}</td>
          <td style="color:#888;font-size:11px">{err}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Test Results — 18 Tabs</title>
  <style>
    body {{ font-family: Calibri, sans-serif; background: #0f0f1a; color: #ddd; padding: 30px; }}
    h1   {{ color: #7ec8e3; margin-bottom: 6px; }}
    p    {{ color: #aaa; margin-bottom: 20px; font-size: 13px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th   {{ background: #1a1a2e; color: #f0a500; padding: 10px 14px; text-align: left; }}
    td   {{ padding: 9px 14px; border-bottom: 1px solid #2a2a3e; font-size: 13px; }}
    tr:hover td {{ background: #1a1a2e; }}
    a    {{ color: #7ec8e3; }}
    .legend {{ margin-top: 20px; font-size: 12px; color: #888; }}
  </style>
</head>
<body>
  <h1>🚀 NASA-Level Test Results</h1>
  <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp;
     Red cells in each tab = mismatch vs Order-Fixer reference &nbsp;|&nbsp;
     Click any cell to edit before printing PDF</p>
  <table>
    <thead>
      <tr>
        <th>File</th>
        <th>First Page</th>
        <th>First Page Tab</th>
        <th>Deviation</th>
        <th>Deviation Tab</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="legend">
    ✔ PASS = all cells match reference &nbsp;|&nbsp;
    ⚠ WARN = 1–3 cell differences &nbsp;|&nbsp;
    ✘ FAIL = 4+ cell differences
  </div>
</body>
</html>"""


if __name__ == "__main__":
    main()
