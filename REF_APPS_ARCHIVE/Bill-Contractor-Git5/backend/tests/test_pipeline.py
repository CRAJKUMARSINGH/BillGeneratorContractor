"""
Smoke test: parse every xlsx in TEST_INPUT_FILES + INPUT_FILES_LEVEL_02
then run the full calculate() pipeline.
Run with: uv run pytest tests/test_pipeline.py -v
Or standalone: uv run python tests/test_pipeline.py
"""
import sys
import uuid
from pathlib import Path

# Ensure backend/app is importable when run standalone
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.engine.parsers.excel import parse_excel
from app.engine.calculator.engine import calculate

TEST_DIRS = [
    ROOT.parent / "TEST_INPUT_FILES",
    ROOT.parent / "INPUT_FILES_LEVEL_02",
]


def collect_files() -> list[Path]:
    files = []
    for d in TEST_DIRS:
        if d.exists():
            for ext in ("*.xlsx", "*.xlsm"):
                files.extend(f for f in sorted(d.glob(ext)) if not f.name.startswith("~$"))
    return files


def run_one(path: Path) -> tuple[bool, str]:
    try:
        doc = parse_excel(path, str(uuid.uuid4()), path.name)
        assert doc.fileId, "fileId missing"
        assert isinstance(doc.billItems, list), "billItems not a list"
        data = calculate(doc)
        assert "grand_total" in data, "grand_total missing from calculate output"
        assert isinstance(data["grand_total"], float), "grand_total not float"
        return True, f"items={len(doc.billItems)} extra={len(doc.extraItems)} total={data['grand_total']:.2f}"
    except Exception as e:
        return False, str(e)


def main():
    files = collect_files()
    if not files:
        print("⚠  No test files found — check TEST_INPUT_FILES / INPUT_FILES_LEVEL_02")
        sys.exit(1)

    passed = failed = 0
    for f in files:
        ok, msg = run_one(f)
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status}  {f.name:<55} {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*70}")
    print(f"Results: {passed}/{passed+failed} PASS")
    if failed:
        sys.exit(1)


# ── pytest-compatible tests ───────────────────────────────────────────────

import pytest

@pytest.mark.parametrize("path", collect_files(), ids=lambda p: p.name)
def test_parse_and_calculate(path: Path):
    ok, msg = run_one(path)
    assert ok, msg


if __name__ == "__main__":
    main()
