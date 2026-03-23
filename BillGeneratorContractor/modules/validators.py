#!/usr/bin/env python3
"""
Validation Framework - Week 2 Day 1
Comprehensive validation for extracted items
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from modules.pwd_database import PWDDatabase, BSRItem


class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "error"      # Critical - item is invalid
    WARNING = "warning"  # Non-critical - item may be valid
    INFO = "info"        # Informational only


@dataclass
class ValidationMessage:
    """Single validation message"""
    level: ValidationLevel
    field: str
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation"""
    valid: bool
    confidence: float  # 0.0 to 1.0
    messages: List[ValidationMessage]
    
    def add_error(self, field: str, message: str, expected=None, actual=None):
        """Add error message"""
        self.messages.append(ValidationMessage(
            level=ValidationLevel.ERROR,
            field=field,
            message=message,
            expected=expected,
            actual=actual
        ))
        self.valid = False
    
    def add_warning(self, field: str, message: str, expected=None, actual=None):
        """Add warning message"""
        self.messages.append(ValidationMessage(
            level=ValidationLevel.WARNING,
            field=field,
            message=message,
            expected=expected,
            actual=actual
        ))
    
    def add_info(self, field: str, message: str):
        """Add info message"""
        self.messages.append(ValidationMessage(
            level=ValidationLevel.INFO,
            field=field,
            message=message
        ))
    
    @property
    def errors(self) -> List[ValidationMessage]:
        """Get all error messages"""
        return [m for m in self.messages if m.level == ValidationLevel.ERROR]
    
    @property
    def warnings(self) -> List[ValidationMessage]:
        """Get all warning messages"""
        return [m for m in self.messages if m.level == ValidationLevel.WARNING]


class BaseValidator:
    """Base class for all validators"""
    
    def __init__(self, db: Optional[PWDDatabase] = None):
        self.db = db or PWDDatabase()
    
    def validate(self, item: Dict) -> ValidationResult:
        """Validate an item - to be implemented by subclasses"""
        raise NotImplementedError


class BSRCodeValidator(BaseValidator):
    """Validates BSR codes"""
    
    def validate(self, item: Dict) -> ValidationResult:
        """Validate BSR code"""
        result = ValidationResult(valid=True, confidence=1.0, messages=[])
        
        code = item.get('code', '').strip()
        
        if not code:
            result.add_error('code', 'BSR code is empty')
            result.confidence = 0.0
            return result
        
        # Check if code exists in database
        if self.db.exists(code):
            result.add_info('code', f'BSR code {code} found in database')
            result.confidence = 1.0
            return result
        
        # Try partial matching
        partial_matches = self.db.find_partial_matches(code, max_results=5)
        if partial_matches:
            result.add_warning(
                'code',
                f'BSR code {code} not found, but similar codes exist',
                expected=', '.join(partial_matches[:3]),
                actual=code
            )
            result.confidence = 0.6
            return result
        
        # Code not found
        result.add_error(
            'code',
            f'BSR code {code} not found in database',
            actual=code
        )
        result.confidence = 0.0
        
        return result


class RateValidator(BaseValidator):
    """Validates rates against expected ranges"""
    
    def __init__(self, db: Optional[PWDDatabase] = None, tolerance: float = 0.2):
        super().__init__(db)
        self.tolerance = tolerance
    
    def validate(self, item: Dict) -> ValidationResult:
        """Validate rate"""
        result = ValidationResult(valid=True, confidence=1.0, messages=[])
        
        code = item.get('code', '').strip()
        rate = item.get('rate', 0)
        
        if not code:
            result.add_error('rate', 'Cannot validate rate without BSR code')
            result.confidence = 0.0
            return result
        
        # Get expected rate from database
        db_item = self.db.get(code)
        if not db_item:
            result.add_warning('rate', f'Cannot validate rate - BSR code {code} not in database')
            result.confidence = 0.5
            return result
        
        # Check if rate is within acceptable range
        if db_item.is_rate_valid(rate, self.tolerance):
            rate_confidence = db_item.rate_confidence(rate)
            result.add_info('rate', f'Rate Rs. {rate} is within acceptable range')
            result.confidence = rate_confidence
            return result
        
        # Rate is outside range
        result.add_error(
            'rate',
            f'Rate Rs. {rate} is outside acceptable range',
            expected=f'Rs. {db_item.rate_range[0]} - {db_item.rate_range[1]} (2024: Rs. {db_item.rate_2024})',
            actual=f'Rs. {rate}'
        )
        result.confidence = 0.3
        
        return result


class UnitValidator(BaseValidator):
    """Validates units"""
    
    # Common unit variations
    UNIT_VARIATIONS = {
        'p. point': ['point', 'p.point', 'ppoint', 'p point'],
        'mtr.': ['mtr', 'meter', 'metre', 'm', 'mtrs'],
        'each': ['ea', 'nos', 'no', 'number', 'pcs', 'piece'],
        'set': ['sets'],
        'job': ['jobs'],
    }
    
    def normalize_unit(self, unit: str) -> str:
        """Normalize unit to standard form"""
        unit_lower = unit.strip().lower()
        
        for standard, variations in self.UNIT_VARIATIONS.items():
            if unit_lower == standard.lower():
                return standard
            if unit_lower in variations:
                return standard
        
        return unit.strip()
    
    def validate(self, item: Dict) -> ValidationResult:
        """Validate unit"""
        result = ValidationResult(valid=True, confidence=1.0, messages=[])
        
        code = item.get('code', '').strip()
        unit = item.get('unit', '').strip()
        
        if not code:
            result.add_error('unit', 'Cannot validate unit without BSR code')
            result.confidence = 0.0
            return result
        
        if not unit:
            result.add_error('unit', 'Unit is empty')
            result.confidence = 0.0
            return result
        
        # Get expected unit from database
        db_item = self.db.get(code)
        if not db_item:
            result.add_warning('unit', f'Cannot validate unit - BSR code {code} not in database')
            result.confidence = 0.5
            return result
        
        # Normalize both units
        normalized_unit = self.normalize_unit(unit)
        normalized_expected = self.normalize_unit(db_item.unit)
        
        # Check if units match
        if normalized_unit.lower() == normalized_expected.lower():
            result.add_info('unit', f'Unit "{unit}" matches expected unit')
            result.confidence = 1.0
            return result
        
        # Units don't match
        result.add_warning(
            'unit',
            f'Unit mismatch',
            expected=db_item.unit,
            actual=unit
        )
        result.confidence = 0.7
        
        return result


class CompositeValidator(BaseValidator):
    """Combines multiple validators"""
    
    def __init__(self, db: Optional[PWDDatabase] = None):
        super().__init__(db)
        self.code_validator = BSRCodeValidator(db)
        self.rate_validator = RateValidator(db)
        self.unit_validator = UnitValidator(db)
    
    def validate(self, item: Dict) -> ValidationResult:
        """Validate item using all validators"""
        # Validate each aspect
        code_result = self.code_validator.validate(item)
        rate_result = self.rate_validator.validate(item)
        unit_result = self.unit_validator.validate(item)
        
        # Combine results
        combined = ValidationResult(valid=True, confidence=1.0, messages=[])
        
        # Add all messages
        combined.messages.extend(code_result.messages)
        combined.messages.extend(rate_result.messages)
        combined.messages.extend(unit_result.messages)
        
        # Calculate combined confidence (weighted average)
        # Code is most important (50%), rate (30%), unit (20%)
        combined.confidence = (
            code_result.confidence * 0.5 +
            rate_result.confidence * 0.3 +
            unit_result.confidence * 0.2
        )
        
        # Item is valid only if all critical checks pass
        combined.valid = (
            code_result.valid and
            rate_result.valid and
            len(combined.errors) == 0
        )
        
        return combined


def validate_item(item: Dict, db: Optional[PWDDatabase] = None) -> ValidationResult:
    """Convenience function to validate an item"""
    validator = CompositeValidator(db)
    return validator.validate(item)


if __name__ == '__main__':
    # Test the validators
    print("\n" + "="*80)
    print("VALIDATION FRAMEWORK TEST - WEEK 2 DAY 1")
    print("="*80)
    
    # Test items
    test_items = [
        {
            'code': '1.1.2',
            'description': 'Wiring of light point',
            'unit': 'P. point',
            'rate': 601,
            'quantity': 10
        },
        {
            'code': '1.1.2',
            'description': 'Wiring of light point',
            'unit': 'point',  # Variation
            'rate': 601,
            'quantity': 10
        },
        {
            'code': '1.1.2',
            'description': 'Wiring of light point',
            'unit': 'P. point',
            'rate': 1000,  # Invalid rate
            'quantity': 10
        },
        {
            'code': '99.99',  # Invalid code
            'description': 'Unknown item',
            'unit': 'Each',
            'rate': 100,
            'quantity': 1
        },
    ]
    
    for i, item in enumerate(test_items, 1):
        print(f"\nTest {i}: {item['code']} - Rs. {item['rate']} - {item['unit']}")
        print("-" * 80)
        
        result = validate_item(item)
        
        print(f"Valid: {result.valid}")
        print(f"Confidence: {result.confidence:.2f}")
        
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for msg in result.errors:
                print(f"  - {msg.field}: {msg.message}")
                if msg.expected:
                    print(f"    Expected: {msg.expected}")
                if msg.actual:
                    print(f"    Actual: {msg.actual}")
        
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for msg in result.warnings:
                print(f"  - {msg.field}: {msg.message}")
                if msg.expected:
                    print(f"    Expected: {msg.expected}")
                if msg.actual:
                    print(f"    Actual: {msg.actual}")
    
    print("\n" + "="*80)
    print("VALIDATION FRAMEWORK: OPERATIONAL")
    print("="*80 + "\n")
