import sys
from pathlib import Path
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "backend"))

print(f"Path: {sys.path}")
try:
    from engine.models import UnifiedBillDocument
    print("✅ engine.models.UnifiedBillDocument imported")
    from backend.services.ingestion_service import IngestionService
    print("✅ IngestionService imported")
except Exception as e:
    print(f"❌ Error: {e}")
