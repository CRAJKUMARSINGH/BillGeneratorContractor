import sys
import os
from pathlib import Path

# Add root to sys.path
root = Path(__file__).parent.parent
sys.path.append(str(root))
print(f"Added to path: {root}")

try:
    from ingestion.excel_parser import parse_excel_bill
    print("✅ Successfully imported parse_excel_bill")
    from ingestion.normalizer import normalize_to_unified_model
    print("✅ Successfully imported normalize_to_unified_model")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
