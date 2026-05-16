import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    records = []
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and ".git" not in str(p):
            rel = p.relative_to(ROOT).as_posix()
            records.append(
                {
                    "path": rel,
                    "size": p.stat().st_size,
                    "sha256": sha256(p),
                }
            )

    out = ROOT / "pack_index.json"
    out.write_text(json.dumps({"files": records}, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

