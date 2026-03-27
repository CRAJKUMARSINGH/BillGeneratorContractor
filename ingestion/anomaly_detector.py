"""
Anomaly Detector — statistical Z-score based outlier detection.

Fixes applied (KIMI review):
- Race condition: file writes are now atomic (write-to-temp + rename).
- Baseline poisoning: features are saved ONLY after passing validation.
- save_validated_features() is a separate explicit call so callers control
  when clean data enters the training set.
- Z-score threshold and min-history size are named constants.
"""
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

HISTORY_FILE      = Path(__file__).parent / "historical_features.json"
MIN_HISTORY_SIZE  = 3      # need at least this many prior bills for Z-score
Z_SCORE_THRESHOLD = 2.0    # standard deviations before flagging


# ── I/O helpers ───────────────────────────────────────────────────────────────

def _load_historical_features() -> List[Dict[str, Any]]:
    """Read history file; returns empty list on any error."""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read history file: %s", exc)
        return []


def _save_historical_features(features: List[Dict[str, Any]]) -> None:
    """
    Atomic write: write to a temp file in the same directory, then rename.
    Prevents partial writes from corrupting the history on crash.
    """
    parent = HISTORY_FILE.parent
    try:
        fd, tmp_path = tempfile.mkstemp(dir=parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(features, f, indent=2)
        except Exception:
            os.unlink(tmp_path)
            raise
        # Atomic rename (same filesystem guaranteed because same dir)
        os.replace(tmp_path, HISTORY_FILE)
    except OSError as exc:
        logger.error("Failed to persist history features: %s", exc)


# ── Public API ────────────────────────────────────────────────────────────────

def extract_features(raw_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """Convert a list of parsed bill rows into a numeric feature vector."""
    if not raw_rows:
        return {"total_amount": 0.0, "item_count": 0, "avg_rate": 0.0, "max_quantity": 0.0}

    amounts    = [float(r.get("amount",   0) or 0) for r in raw_rows]
    rates      = [float(r.get("rate",     0) or 0) for r in raw_rows if r.get("rate")]
    quantities = [float(r.get("quantity", 0) or 0) for r in raw_rows if r.get("quantity")]

    return {
        "total_amount": sum(amounts),
        "item_count":   len(raw_rows),
        "avg_rate":     sum(rates) / len(rates) if rates else 0.0,
        "max_quantity": max(quantities) if quantities else 0.0,
    }


def detect_anomalies(current_features: Dict[str, float]) -> List[str]:
    """
    Compare current bill features against historical Z-scores.

    IMPORTANT: does NOT save features — call save_validated_features()
    explicitly after the bill passes all checks.  This prevents anomalous
    bills from poisoning the training baseline.
    """
    warnings: List[str] = []
    historical = _load_historical_features()

    if len(historical) < MIN_HISTORY_SIZE:
        # Not enough history for meaningful statistics — skip silently.
        return warnings

    df = pd.DataFrame(historical)

    for feature in ("total_amount", "max_quantity", "avg_rate", "item_count"):
        if feature not in df.columns:
            continue

        mean = df[feature].mean()
        std  = df[feature].std()

        if std <= 0:
            continue  # No variation — Z-score undefined

        current_val = current_features.get(feature, 0)
        z_score     = abs(current_val - mean) / std

        if z_score > Z_SCORE_THRESHOLD:
            warnings.append(
                f"Anomaly Detected: {feature.replace('_', ' ').title()} "
                f"({current_val:,.2f}) deviates {z_score:.1f}σ from "
                f"historical mean ({mean:,.2f})"
            )

    return warnings


def save_validated_features(features: Dict[str, float]) -> None:
    """
    Persist features to the training history.
    Call this ONLY after detect_anomalies() returns no warnings.
    """
    historical = _load_historical_features()
    historical.append(features)
    _save_historical_features(historical)
