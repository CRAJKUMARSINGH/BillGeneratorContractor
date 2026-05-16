from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "01_inputs",
    "02_reference_unif_outputs",
    "03_consolidated_outputs",
    "04_ocr_and_quantity_text",
    "05_reports",
    "scripts",
    "docs",
]

REQUIRED_FILES = [
    "README.md",
    "docs/HOW_TO_USE.md",
    "docs/PROVENANCE.md",
    "docs/CHANGELOG.md",
]


def main() -> None:
    errors = []
    for d in REQUIRED_DIRS:
        if not (ROOT / d).is_dir():
            errors.append(f"Missing directory: {d}")
    for f in REQUIRED_FILES:
        if not (ROOT / f).is_file():
            errors.append(f"Missing file: {f}")

    if errors:
        print("SAMPLE_PACK verification FAILED")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)

    print("SAMPLE_PACK verification PASSED")


if __name__ == "__main__":
    main()

