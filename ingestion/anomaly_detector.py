import os
import json
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# A simple storage mechanism for historical bill features.
# In a real deployed app, this would be a Postgres or Qdrant Vector database.
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "historical_features.json")

def _load_historical_features() -> List[Dict[str, Any]]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def _save_historical_features(features: List[Dict[str, Any]]):
    with open(HISTORY_FILE, "w") as f:
        json.dump(features, f, indent=2)

def extract_features(raw_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Converts a parsed document into a feature vector for anomaly detection.
    """
    if not raw_rows:
        return {"total_amount": 0, "item_count": 0, "avg_rate": 0, "max_quantity": 0}

    total_amount = sum(float(r.get("amount", 0) or 0) for r in raw_rows)
    item_count = len(raw_rows)
    rates = [float(r.get("rate", 0) or 0) for r in raw_rows if r.get("rate")]
    avg_rate = sum(rates) / len(rates) if rates else 0
    
    quantities = [float(r.get("quantity", 0) or 0) for r in raw_rows if r.get("quantity")]
    max_quantity = max(quantities) if quantities else 0
    
    return {
        "total_amount": total_amount,
        "item_count": item_count,
        "avg_rate": avg_rate,
        "max_quantity": max_quantity
    }

def detect_anomalies(current_features: Dict[str, float]) -> List[str]:
    """
    Detects anomalies by comparing the current features against historical Z-scores.
    Only saves to history AFTER checking — prevents anomalous bills from poisoning baseline.
    """
    warnings = []
    historical = _load_historical_features()

    # Need at least 3 prior bills to calculate meaningful standard deviation.
    # Check BEFORE appending so the current bill doesn't skew its own evaluation.
    if len(historical) >= 3:
        df = pd.DataFrame(historical)

        for feature in ["total_amount", "max_quantity", "avg_rate", "item_count"]:
            if feature in df.columns:
                mean = df[feature].mean()
                std = df[feature].std()

                if std > 0:
                    current_val = current_features.get(feature, 0)
                    z_score = abs(current_val - mean) / std

                    if z_score > 2.0:
                        warnings.append(
                            f"Anomaly Detected: {feature.replace('_', ' ').title()} "
                            f"({current_val:.2f}) is outside historical norms "
                            f"(mean={mean:.2f}, z={z_score:.1f})"
                        )

    # Only add to history if no anomalies detected — keeps baseline clean.
    # Anomalous bills are flagged for human review but not used to train future checks.
    if not warnings:
        historical.append(current_features)
        _save_historical_features(historical)

    return warnings
