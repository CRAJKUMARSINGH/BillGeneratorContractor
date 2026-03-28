#!/usr/bin/env python3
"""
PWD BSR Database Module
Provides query and validation functions for PWD BSR codes
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class BSRItem:
    """PWD BSR Item"""
    code: str
    description: str
    unit: str
    rate_2024: float
    rate_range: Tuple[float, float]
    category: str
    subcategory: str
    
    def is_rate_valid(self, rate: float, tolerance: float = 0.2) -> bool:
        """Check if rate is within acceptable range"""
        min_rate = self.rate_range[0] * (1 - tolerance)
        max_rate = self.rate_range[1] * (1 + tolerance)
        return min_rate <= rate <= max_rate
    
    def rate_confidence(self, rate: float) -> float:
        """Calculate confidence score for rate (0.0-1.0)"""
        if self.rate_range[0] <= rate <= self.rate_range[1]:
            return 1.0
        
        # Calculate distance from range
        if rate < self.rate_range[0]:
            distance = (self.rate_range[0] - rate) / self.rate_range[0]
        else:
            distance = (rate - self.rate_range[1]) / self.rate_range[1]
        
        # Convert distance to confidence (max 50% penalty)
        confidence = max(0.0, 1.0 - min(distance, 0.5))
        return confidence


class PWDDatabase:
    """PWD BSR Database Manager"""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "pwd_bsr_database.json"
        
        self.db_path = db_path
        self.data = {}
        self.items = {}
        self.load()
    
    def load(self):
        """Load database from JSON file"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        with open(self.db_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Flatten items for easy lookup
        self.items = {}
        for category_name, category_items in self.data.get('categories', {}).items():
            for code, item_data in category_items.items():
                self.items[code] = BSRItem(
                    code=code,
                    description=item_data['description'],
                    unit=item_data['unit'],
                    rate_2024=item_data['rate_2024'],
                    rate_range=tuple(item_data['rate_range']),
                    category=item_data['category'],
                    subcategory=item_data['subcategory']
                )
    
    def get(self, code: str) -> Optional[BSRItem]:
        """Get BSR item by code"""
        return self.items.get(code)
    
    def exists(self, code: str) -> bool:
        """Check if BSR code exists"""
        return code in self.items
    
    def validate_code(self, code: str) -> Tuple[bool, str]:
        """Validate BSR code"""
        if not code:
            return False, "Empty BSR code"
        
        if code in self.items:
            return True, "Valid BSR code"
        
        # Check for partial matches
        partial_matches = self.find_partial_matches(code)
        if partial_matches:
            return False, f"BSR code not found. Did you mean: {', '.join(partial_matches[:3])}?"
        
        return False, "BSR code not in database"
    
    def validate_rate(self, code: str, rate: float, tolerance: float = 0.2) -> Tuple[bool, str, float]:
        """
        Validate rate for BSR code
        Returns: (is_valid, message, confidence_score)
        """
        item = self.get(code)
        if not item:
            return False, "BSR code not found", 0.0
        
        if item.is_rate_valid(rate, tolerance):
            confidence = item.rate_confidence(rate)
            return True, f"Rate within acceptable range", confidence
        
        expected = item.rate_2024
        return False, f"Rate {rate} outside range {item.rate_range}. Expected: {expected}", 0.3
    
    def validate_unit(self, code: str, unit: str) -> Tuple[bool, str]:
        """Validate unit for BSR code"""
        item = self.get(code)
        if not item:
            return False, "BSR code not found"
        
        # Normalize units for comparison
        unit_normalized = unit.strip().lower()
        expected_normalized = item.unit.strip().lower()
        
        if unit_normalized == expected_normalized:
            return True, "Unit matches"
        
        # Check common variations
        unit_variations = {
            'p. point': ['point', 'p.point', 'ppoint'],
            'mtr.': ['mtr', 'meter', 'metre', 'm'],
            'each': ['ea', 'nos', 'no', 'number']
        }
        
        for standard, variations in unit_variations.items():
            if expected_normalized == standard.lower():
                if unit_normalized in variations:
                    return True, f"Unit matches (variation of {item.unit})"
        
        return False, f"Unit mismatch: got '{unit}', expected '{item.unit}'"
    
    def find_partial_matches(self, code: str, max_results: int = 5) -> List[str]:
        """Find BSR codes that partially match"""
        matches = []
        
        # Exact prefix match
        for item_code in self.items.keys():
            if item_code.startswith(code):
                matches.append(item_code)
        
        # Partial match
        if not matches:
            for item_code in self.items.keys():
                if code in item_code:
                    matches.append(item_code)
        
        return matches[:max_results]
    
    def search_by_description(self, query: str, max_results: int = 10) -> List[BSRItem]:
        """Search items by description"""
        query_lower = query.lower()
        results = []
        
        for item in self.items.values():
            if query_lower in item.description.lower():
                results.append(item)
        
        return results[:max_results]
    
    def filter_by_category(self, category: str) -> List[BSRItem]:
        """Get all items in a category"""
        return [item for item in self.items.values() if item.category == category]
    
    def filter_by_rate_range(self, min_rate: float, max_rate: float) -> List[BSRItem]:
        """Get items within rate range"""
        return [
            item for item in self.items.values()
            if item.rate_range[0] >= min_rate and item.rate_range[1] <= max_rate
        ]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        categories = {}
        for item in self.items.values():
            if item.category not in categories:
                categories[item.category] = 0
            categories[item.category] += 1
        
        return {
            'total_items': len(self.items),
            'categories': categories,
            'version': self.data.get('version', 'unknown'),
            'last_updated': self.data.get('last_updated', 'unknown')
        }
    
    def validate_item(self, code: str, rate: float, unit: str) -> Dict:
        """
        Comprehensive validation of an item
        Returns validation result with confidence score
        """
        result = {
            'valid': True,
            'confidence': 1.0,
            'errors': [],
            'warnings': []
        }
        
        # Validate code
        code_valid, code_msg = self.validate_code(code)
        if not code_valid:
            result['valid'] = False
            result['confidence'] = 0.0
            result['errors'].append(code_msg)
            return result
        
        # Validate rate
        rate_valid, rate_msg, rate_confidence = self.validate_rate(code, rate)
        if not rate_valid:
            result['valid'] = False
            result['errors'].append(rate_msg)
        result['confidence'] *= rate_confidence
        
        # Validate unit
        unit_valid, unit_msg = self.validate_unit(code, unit)
        if not unit_valid:
            result['warnings'].append(unit_msg)
            result['confidence'] *= 0.9
        
        return result


# Global database instance
_db_instance = None

def get_database() -> PWDDatabase:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = PWDDatabase()
    return _db_instance


# Convenience functions
def validate_bsr_code(code: str) -> bool:
    """Quick validation of BSR code"""
    db = get_database()
    return db.exists(code)


def get_bsr_item(code: str) -> Optional[BSRItem]:
    """Quick lookup of BSR item"""
    db = get_database()
    return db.get(code)


def validate_item(code: str, rate: float, unit: str) -> Dict:
    """Quick validation of complete item"""
    db = get_database()
    return db.validate_item(code, rate, unit)


if __name__ == '__main__':
    # Test the database
    db = PWDDatabase()
    
    print("PWD BSR Database")
    print("=" * 60)
    
    stats = db.get_statistics()
    print(f"Version: {stats['version']}")
    print(f"Last Updated: {stats['last_updated']}")
    print(f"Total Items: {stats['total_items']}")
    print(f"\nCategories:")
    for cat, count in stats['categories'].items():
        print(f"  {cat}: {count} items")
    
    print("\n" + "=" * 60)
    print("Testing validation...")
    
    # Test valid item
    result = db.validate_item("1.1.2", 601, "P. point")
    print(f"\nTest 1 - Valid item:")
    print(f"  Code: 1.1.2, Rate: 601, Unit: P. point")
    print(f"  Valid: {result['valid']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    
    # Test invalid rate
    result = db.validate_item("1.1.2", 1000, "P. point")
    print(f"\nTest 2 - Invalid rate:")
    print(f"  Code: 1.1.2, Rate: 1000, Unit: P. point")
    print(f"  Valid: {result['valid']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Errors: {result['errors']}")
    
    # Test invalid code
    result = db.validate_item("99.99", 100, "Each")
    print(f"\nTest 3 - Invalid code:")
    print(f"  Code: 99.99, Rate: 100, Unit: Each")
    print(f"  Valid: {result['valid']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Errors: {result['errors']}")
    
    print("\n" + "=" * 60)
    print("Week 1 Day 1: Database foundation complete!")
