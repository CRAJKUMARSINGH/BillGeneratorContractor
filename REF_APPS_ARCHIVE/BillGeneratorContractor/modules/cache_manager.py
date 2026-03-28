"""
Week 8: Cache Manager Module
Implements caching for extraction results to improve performance.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import time


@dataclass
class CacheEntry:
    """Cache entry for extraction result"""
    image_hash: str
    image_path: str
    items: List[Dict]
    confidence: float
    extractor_used: str
    timestamp: float
    hit_count: int = 0
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


class CacheManager:
    """Manages caching of extraction results"""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24, max_entries: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "extraction_cache.json"
        self.ttl_seconds = ttl_hours * 3600 if ttl_hours > 0 else 0
        self.max_entries = max_entries
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = {'hits': 0, 'misses': 0, 'saves': 0, 'evictions': 0}
        self._load_cache()
    
    def _compute_image_hash(self, image_path: str) -> str:
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return hashlib.md5(str(image_path).encode()).hexdigest()


    def _load_cache(self):
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for image_hash, entry_data in data.items():
                self.cache[image_hash] = CacheEntry.from_dict(entry_data)
        except:
            self.cache = {}
    
    def _save_cache(self):
        try:
            cache_data = {h: e.to_dict() for h, e in self.cache.items()}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except:
            pass
    
    def get(self, image_path: str) -> Optional[CacheEntry]:
        image_hash = self._compute_image_hash(image_path)
        if image_hash in self.cache:
            entry = self.cache[image_hash]
            if self.ttl_seconds > 0:
                age = time.time() - entry.timestamp
                if age > self.ttl_seconds:
                    del self.cache[image_hash]
                    self.stats['misses'] += 1
                    return None
            entry.hit_count += 1
            self.stats['hits'] += 1
            return entry
        self.stats['misses'] += 1
        return None
    
    def put(self, image_path: str, items: List[Dict], confidence: float, extractor_used: str):
        image_hash = self._compute_image_hash(image_path)
        entry = CacheEntry(
            image_hash=image_hash,
            image_path=str(image_path),
            items=items,
            confidence=confidence,
            extractor_used=extractor_used,
            timestamp=time.time(),
            hit_count=0
        )
        self.cache[image_hash] = entry
        self.stats['saves'] += 1
        if self.stats['saves'] % 10 == 0:
            self._save_cache()
    
    def get_stats(self) -> Dict:
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        return {
            'entries': len(self.cache),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'saves': self.stats['saves'],
            'evictions': self.stats['evictions']
        }
    
    def cleanup(self):
        self._save_cache()
