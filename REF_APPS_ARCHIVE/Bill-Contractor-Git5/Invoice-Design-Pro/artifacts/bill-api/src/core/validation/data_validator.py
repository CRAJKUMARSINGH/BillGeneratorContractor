#!/usr/bin/env python3
"""
Comprehensive Data Validation Module
Validates BSR codes, rates, quantities, and other work order data
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class ValidationLevel(Enum):
    ERROR = "error"      # Critical issues that must be fixed
    WARNING = "warning"  # Issues that should be reviewed
    INFO = "info"        # Informational messages


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    level: ValidationLevel
    field: str
    message: str
    original_value: Any
    suggested_value: Any = None
    confidence: float = 0.0


@dataclass
class ValidationReport:
    """Complete validation report for a dataset"""
    total_items: int
    valid_items: int
    errors: List[ValidationResult]
    warnings: List[ValidationResult]
    info: List[ValidationResult]
    overall_score: float
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        return {
            'total_items': self.total_items,
            'valid_items': self.valid_items,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'info_count': len(self.info),
            'overall_score': self.overall_score,
            'success_rate': (self.valid_items / self.total_items * 100) if self.total_items > 0 else 0
        }


class BSRCodeValidator:
    """Validates BSR codes against PWD schedule"""
    
    def __init__(self, schedule_data_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.bsr_schedule = self._load_bsr_schedule(schedule_data_path)
        
        # Common BSR code patterns
        self.bsr_patterns = {
            'earthwork': r'^0[1-9]\.\d{2}(\.\d+)?$',
            'concrete': r'^1[0-9]\.\d{2}(\.\d+)?$',
            'brickwork': r'^2[0-9]\.\d{2}(\.\d+)?$',
            'plastering': r'^3[0-9]\.\d{2}(\.\d+)?$',
            'flooring': r'^4[0-9]\.\d{2}(\.\d+)?$',
            'roofing': r'^5[0-9]\.\d{2}(\.\d+)?$',
            'painting': r'^6[0-9]\.\d{2}(\.\d+)?$',
            'electrical': r'^7[0-9]\.\d{2}(\.\d+)?$',
            'plumbing': r'^8[0-9]\.\d{2}(\.\d+)?$',
            'general': r'^9[0-9]\.\d{2}(\.\d+)?$'
        }
    
    def _load_bsr_schedule(self, schedule_data_path: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Load BSR schedule data"""
        if schedule_data_path and Path(schedule_data_path).exists():
            try:
                with open(schedule_data_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading BSR schedule: {e}")
        
        # Default minimal schedule
        return {
            '18.13': {'description': 'Cement concrete 1:4:8', 'unit': 'm3', 'typical_rate': 3500},
            '27.01': {'description': 'Brick masonry', 'unit': 'm3', 'typical_rate': 4500},
            '15.03': {'description': 'Plastering', 'unit': 'm2', 'typical_rate': 120},
            '12.10': {'description': 'Earthwork', 'unit': 'm3', 'typical_rate': 800}
        }
    
    def validate_bsr_code(self, bsr_code: str) -> ValidationResult:
        """Validate a single BSR code"""
        bsr_code = str(bsr_code).strip()
        
        # Check format
        if not re.match(r'^\d{2}\.\d{2}(\.\d+)?$', bsr_code):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field='bsr_code',
                message=f'Invalid BSR code format: {bsr_code}. Expected format: XX.XX or XX.XX.X',
                original_value=bsr_code,
                suggested_value=self._suggest_bsr_correction(bsr_code)
            )
        
        # Check if in schedule
        if bsr_code in self.bsr_schedule:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                field='bsr_code',
                message=f'BSR code {bsr_code} found in schedule',
                original_value=bsr_code,
                confidence=1.0
            )
        
        # Check pattern matching
        category = self._get_bsr_category(bsr_code)
        if category:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                field='bsr_code',
                message=f'BSR code {bsr_code} matches {category} pattern but not in schedule',
                original_value=bsr_code,
                confidence=0.7
            )
        
        return ValidationResult(
            is_valid=False,
            level=ValidationLevel.ERROR,
            field='bsr_code',
            message=f'Unknown BSR code: {bsr_code}',
            original_value=bsr_code,
            confidence=0.0
        )
    
    def _suggest_bsr_correction(self, bsr_code: str) -> Optional[str]:
        """Suggest correction for invalid BSR code"""
        # Remove extra characters
        cleaned = re.sub(r'[^\d.]', '', bsr_code)
        
        # Add missing digits
        if re.match(r'^\d\.\d{2}$', cleaned):
            cleaned = f"0{cleaned}"
        elif re.match(r'^\d{2}\.\d$', cleaned):
            cleaned = f"{cleaned}0"
        
        if re.match(r'^\d{2}\.\d{2}(\.\d+)?$', cleaned):
            return cleaned
        
        return None
    
    def _get_bsr_category(self, bsr_code: str) -> Optional[str]:
        """Get BSR code category"""
        for category, pattern in self.bsr_patterns.items():
            if re.match(pattern, bsr_code):
                return category
        return None


class RateValidator:
    """Validates item rates"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Typical rate ranges by unit (in INR)
        self.rate_ranges = {
            'm3': {'min': 500, 'max': 15000},      # Cubic meter
            'm2': {'min': 50, 'max': 2000},       # Square meter  
            'm': {'min': 20, 'max': 5000},         # Linear meter
            'kg': {'min': 5, 'max': 500},          # Kilogram
            'nos': {'min': 10, 'max': 50000},      # Numbers
            'lot': {'min': 100, 'max': 100000},    # Lot
            'day': {'min': 500, 'max': 10000},     # Day
            'month': {'min': 10000, 'max': 100000} # Month
        }
    
    def validate_rate(self, rate: float, unit: str, bsr_code: Optional[str] = None) -> ValidationResult:
        """Validate a rate"""
        try:
            rate = float(rate)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field='rate',
                message=f'Invalid rate format: {rate}',
                original_value=rate
            )
        
        # Check for negative or zero rates
        if rate <= 0:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field='rate',
                message=f'Rate must be positive: {rate}',
                original_value=rate,
                suggested_value=abs(rate) if rate != 0 else 100
            )
        
        # Check rate range for unit
        unit = unit.lower().strip()
        if unit in self.rate_ranges:
            range_data = self.rate_ranges[unit]
            if rate < range_data['min']:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    field='rate',
                    message=f'Rate {rate} seems too low for unit {unit} (min: {range_data["min"]})',
                    original_value=rate,
                    suggested_value=range_data['min']
                )
            elif rate > range_data['max']:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    field='rate',
                    message=f'Rate {rate} seems too high for unit {unit} (max: {range_data["max"]})',
                    original_value=rate,
                    suggested_value=range_data['max']
                )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            field='rate',
            message=f'Rate {rate} appears valid',
            original_value=rate,
            confidence=0.8
        )


class QuantityValidator:
    """Validates item quantities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Typical quantity ranges by unit
        self.quantity_ranges = {
            'm3': {'min': 0.1, 'max': 10000},
            'm2': {'min': 1.0, 'max': 50000},
            'm': {'min': 1.0, 'max': 10000},
            'kg': {'min': 0.1, 'max': 10000},
            'nos': {'min': 1, 'max': 100000},
            'lot': {'min': 1, 'max': 1000},
            'day': {'min': 1, 'max': 365},
            'month': {'min': 1, 'max': 24}
        }
    
    def validate_quantity(self, quantity: float, unit: str) -> ValidationResult:
        """Validate a quantity"""
        try:
            quantity = float(quantity)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field='quantity',
                message=f'Invalid quantity format: {quantity}',
                original_value=quantity
            )
        
        # Check for negative quantities
        if quantity < 0:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                field='quantity',
                message=f'Quantity cannot be negative: {quantity}',
                original_value=quantity,
                suggested_value=abs(quantity)
            )
        
        # Check quantity range for unit
        unit = unit.lower().strip()
        if unit in self.quantity_ranges:
            range_data = self.quantity_ranges[unit]
            if quantity < range_data['min']:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    field='quantity',
                    message=f'Quantity {quantity} seems too low for unit {unit} (min: {range_data["min"]})',
                    original_value=quantity,
                    suggested_value=range_data['min']
                )
            elif quantity > range_data['max']:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    field='quantity',
                    message=f'Quantity {quantity} seems too high for unit {unit} (max: {range_data["max"]})',
                    original_value=quantity,
                    suggested_value=range_data['max']
                )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            field='quantity',
            message=f'Quantity {quantity} appears valid',
            original_value=quantity,
            confidence=0.9
        )


class DescriptionValidator:
    """Validates item descriptions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_description(self, description: str) -> ValidationResult:
        """Validate item description"""
        description = str(description).strip()
        
        # Check for empty description
        if not description:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                field='description',
                message='Description is empty',
                original_value=description,
                suggested_value='Item description'
            )
        
        # Check for too short description
        if len(description) < 3:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                field='description',
                message=f'Description too short: {description}',
                original_value=description
            )
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'^[0-9\.]+$',  # Only numbers
            r'^[a-zA-Z]{1,2}$',  # Only 1-2 letters
            r'[^\w\s\-\.\,\(\)]'  # Special characters
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, description):
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    field='description',
                    message=f'Suspicious description pattern: {description}',
                    original_value=description
                )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            field='description',
            message=f'Description appears valid: {description[:50]}...',
            original_value=description,
            confidence=0.8
        )


class DataValidator:
    """Main data validation orchestrator"""
    
    def __init__(self, bsr_schedule_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.bsr_validator = BSRCodeValidator(bsr_schedule_path)
        self.rate_validator = RateValidator()
        self.quantity_validator = QuantityValidator()
        self.description_validator = DescriptionValidator()
    
    def validate_item(self, item: Dict[str, Any]) -> List[ValidationResult]:
        """Validate a single work order item"""
        results = []
        
        # Validate BSR code
        if 'bsr_code' in item:
            results.append(self.bsr_validator.validate_bsr_code(item['bsr_code']))
        
        # Validate description
        if 'description' in item:
            results.append(self.description_validator.validate_description(item['description']))
        
        # Validate rate
        if 'rate' in item:
            unit = item.get('unit', 'm')
            bsr_code = item.get('bsr_code')
            results.append(self.rate_validator.validate_rate(item['rate'], unit, bsr_code))
        
        # Validate quantity
        if 'quantity' in item:
            unit = item.get('unit', 'm')
            results.append(self.quantity_validator.validate_quantity(item['quantity'], unit))
        
        # Validate unit
        if 'unit' in item:
            results.append(self._validate_unit(item['unit']))
        
        return results
    
    def _validate_unit(self, unit: str) -> ValidationResult:
        """Validate unit"""
        valid_units = {'m', 'm2', 'm3', 'm³', 'kg', 'nos', 'lot', 'day', 'month'}
        unit = str(unit).strip().lower()
        
        # Normalize m³ to m3
        if unit == 'm³':
            unit = 'm3'
        
        if unit not in valid_units:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                field='unit',
                message=f'Unknown unit: {unit}',
                original_value=unit,
                suggested_value='m'  # Default to meter
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            field='unit',
            message=f'Unit {unit} is valid',
            original_value=unit,
            confidence=1.0
        )
    
    def validate_dataset(self, items: List[Dict[str, Any]]) -> ValidationReport:
        """Validate complete dataset"""
        all_results = []
        valid_items = 0
        
        for i, item in enumerate(items):
            item_results = self.validate_item(item)
            all_results.extend(item_results)
            
            # Check if item has any errors
            has_errors = any(r.level == ValidationLevel.ERROR for r in item_results)
            if not has_errors:
                valid_items += 1
        
        # Categorize results
        errors = [r for r in all_results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in all_results if r.level == ValidationLevel.WARNING]
        info = [r for r in all_results if r.level == ValidationLevel.INFO]
        
        # Calculate overall score
        total_issues = len(errors) * 10 + len(warnings) * 3 + len(info) * 1
        max_possible_score = len(items) * 10
        overall_score = max(0, 100 - (total_issues / max_possible_score * 100))
        
        return ValidationReport(
            total_items=len(items),
            valid_items=valid_items,
            errors=errors,
            warnings=warnings,
            info=info,
            overall_score=overall_score
        )
    
    def suggest_corrections(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest corrections for invalid data"""
        corrected_items = []
        
        for item in items:
            corrected_item = item.copy()
            results = self.validate_item(item)
            
            for result in results:
                if result.suggested_value is not None and result.level in [ValidationLevel.ERROR, ValidationLevel.WARNING]:
                    corrected_item[result.field] = result.suggested_value
            
            corrected_items.append(corrected_item)
        
        return corrected_items


def create_validator(bsr_schedule_path: Optional[str] = None) -> DataValidator:
    """Factory function to create data validator"""
    return DataValidator(bsr_schedule_path)


if __name__ == "__main__":
    # Test the validator
    logging.basicConfig(level=logging.INFO)
    
    validator = create_validator()
    
    # Test items
    test_items = [
        {
            'bsr_code': '18.13',
            'description': 'Cement concrete 1:4:8',
            'unit': 'm3',
            'quantity': 10.5,
            'rate': 3500.00
        },
        {
            'bsr_code': '99.99',  # Invalid BSR
            'description': 'Invalid item',
            'unit': 'xyz',  # Invalid unit
            'quantity': -5,  # Invalid quantity
            'rate': 0  # Invalid rate
        }
    ]
    
    report = validator.validate_dataset(test_items)
    print(f"Validation Report: {report.get_summary()}")
    
    # Test corrections
    corrected = validator.suggest_corrections(test_items)
    print(f"Corrected items: {corrected}")
