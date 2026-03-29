import os
import json
import logging
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import portalocker  # Cross-platform file locking

logger = logging.getLogger(__name__)

# Constants
HISTORY_FILE = Path(__file__).parent / "historical_features.json"
MIN_HISTORY_SIZE = 5
Z_SCORE_THRESHOLD = 3.0

def _load_historical_features() -> List[Dict[str, Any]]:
    """Thread-safe and process-safe read of historical features."""
    if not HISTORY_FILE.exists():
        return []
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            # Acquire shared lock for reading
            portalocker.lock(f, portalocker.LOCK_SH)
            try:
                data = json.load(f)
                return data
            finally:
                portalocker.unlock(f)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Could not read history file: {e}")
        return []

def _save_historical_features(features: List[Dict[str, Any]]) -> None:
    """Atomic write with exclusive locking to prevent corruption."""
    parent = HISTORY_FILE.parent
    parent.mkdir(parents=True, exist_ok=True)
    
    # Use a lock file for coordination during the temp-write process
    lock_path = HISTORY_FILE.with_suffix(".lock")
    
    try:
        with open(lock_path, "w") as lock_f:
            portalocker.lock(lock_f, portalocker.LOCK_EX)
            
            # Create a temp file in the same directory for atomic rename
            fd, tmp_path = tempfile.mkstemp(dir=parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(features, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data hits disk
                
                # Atomic replace
                os.replace(tmp_path, HISTORY_FILE)
            except Exception as e:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise e
            finally:
                portalocker.unlock(lock_f)
    except Exception as e:
        logger.error(f"Failed to persist historical features: {e}")

# ── Public API ────────────────────────────────────────────────────────────────

def extract_features(raw_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """Convert a list of parsed bill rows into a numeric feature vector."""
    if not raw_rows:
        return {"total_amount": 0.0, "item_count": 0, "avg_rate": 0.0, "max_quantity": 0.0}

    amounts = []
    rates = []
    quantities = []
    
    for r in raw_rows:
        try:
            amt = float(r.get("amount") or 0)
            rate = float(r.get("rate") or 0)
            qty = float(r.get("quantity") or 0)
            
            amounts.append(amt)
            if rate > 0: rates.append(rate)
            if qty > 0: quantities.append(qty)
        except (ValueError, TypeError):
            continue

    return {
        "total_amount": sum(amounts),
        "item_count": len(raw_rows),
        "avg_rate": sum(rates) / len(rates) if rates else 0.0,
        "max_quantity": max(quantities) if quantities else 0.0
    }

def detect_anomalies(current_features: Dict[str, float]) -> List[str]:
    """
    Detect statistical anomalies in the current document relative to history.
    Uses Z-score analysis for key features.
    """
    history = _load_historical_features()
    if len(history) < MIN_HISTORY_SIZE:
        # Before saving, we just return empty warnings for first few runs
        return []

    df = pd.DataFrame(history)
    warnings = []

    for feature, value in current_features.items():
        if feature not in df.columns:
            continue
            
        mean = df[feature].mean()
        std = df[feature].std()
        
        if std > 0:
            z_score = abs(value - mean) / std
            if z_score > Z_SCORE_THRESHOLD:
                warnings.append(
                    f"Statistical Anomaly: {feature.replace('_', ' ').title()} ({value:,.2f}) "
                    f"deviates {z_score:.1f} sigma from historical mean ({mean:,.2f})"
                )
    
    return warnings

def save_validated_features(features: Dict[str, float]) -> None:
    """Save the features of a valid document to the historical baseline."""
    history = _load_historical_features()
    history.append(features)
    
    # Keep history size manageable (last 100 docs)
    if len(history) > 100:
        history = history[-100:]
        
    _save_historical_features(history)
