"""
Week 7: Completeness Checker Module

Detects missing items and validates extraction completeness.
Ensures all items from work order images are captured.
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from modules.pwd_database import PWDDatabase
import re


@dataclass
class CompletenessResult:
    """Result of completeness check"""
    is_complete: bool
    total_items: int
    valid_items: int
    invalid_items: int
    missing_fields: List[str]
    unknown_codes: List[str]
    warnings: List[str]
    completeness_score: float  # 0.0 to 1.0
    
    def __str__(self):
        return (
            f"Completeness: {self.completeness_score:.2f} "
            f"({self.valid_items}/{self.total_items} valid)"
        )


class CompletenessChecker:
    """
    Checks completeness of extracted items
    
    Features:
    - Validates all required fields present
    - Checks for unknown BSR codes
    - Estimates expected item count
    - Detects missing items
    - Calculates completeness score
    """
    
    def __init__(self, database: PWDDatabase):
        self.db = database
        
        # Required fields for each item
        self.required_fields = ['code', 'description', 'unit', 'rate']
        
        # Optional but recommended fields
        self.optional_fields = ['quantity', 'amount']
    
    def check_completeness(self, items: List[Dict]) -> CompletenessResult:
        """
        Check completeness of extracted items
        
        Args:
            items: List of extracted items
            
        Returns:
            CompletenessResult with detailed analysis
        """
        if not items:
            return CompletenessResult(
                is_complete=False,
                total_items=0,
                valid_items=0,
                invalid_items=0,
                missing_fields=[],
                unknown_codes=[],
                warnings=["No items extracted"],
                completeness_score=0.0
            )
        
        total_items = len(items)
        valid_items = 0
        invalid_items = 0
        missing_fields = []
        unknown_codes = []
        warnings = []
        
        # Check each item
        for i, item in enumerate(items, 1):
            item_valid = True
            item_warnings = []
            
            # Check required fields
            for field in self.required_fields:
                if not item.get(field):
                    item_valid = False
                    item_warnings.append(f"Item {i}: Missing {field}")
                    if field not in missing_fields:
                        missing_fields.append(field)
            
            # Check BSR code validity
            code = item.get('code', '')
            if code:
                if not self.db.validate_bsr_code(code):
                    # Check if it's a partial match
                    matches = self.db.search_by_code(code)
                    if not matches:
                        unknown_codes.append(code)
                        item_warnings.append(f"Item {i}: Unknown BSR code '{code}'")
                        item_valid = False
            
            # Check rate validity
            if code and item.get('rate'):
                rate = float(item.get('rate', 0))
                if not self.db.validate_rate(code, rate):
                    item_warnings.append(
                        f"Item {i}: Rate {rate} outside expected range for {code}"
                    )
            
            # Check unit validity
            if code and item.get('unit'):
                unit = item.get('unit', '')
                if not self.db.validate_unit(code, unit):
                    item_warnings.append(
                        f"Item {i}: Unit '{unit}' doesn't match expected for {code}"
                    )
            
            if item_valid:
                valid_items += 1
            else:
                invalid_items += 1
                warnings.extend(item_warnings)
        
        # Calculate completeness score
        completeness_score = self._calculate_completeness_score(
            total_items, valid_items, missing_fields, unknown_codes
        )
        
        # Determine if complete
        is_complete = (
            completeness_score >= 0.90 and
            len(unknown_codes) == 0 and
            len(missing_fields) == 0
        )
        
        # Add summary warnings
        if unknown_codes:
            warnings.insert(0, f"Found {len(unknown_codes)} unknown BSR codes")
        if missing_fields:
            warnings.insert(0, f"Missing fields: {', '.join(set(missing_fields))}")
        if invalid_items > 0:
            warnings.insert(0, f"{invalid_items}/{total_items} items have issues")
        
        return CompletenessResult(
            is_complete=is_complete,
            total_items=total_items,
            valid_items=valid_items,
            invalid_items=invalid_items,
            missing_fields=list(set(missing_fields)),
            unknown_codes=list(set(unknown_codes)),
            warnings=warnings[:10],  # Limit to top 10 warnings
            completeness_score=completeness_score
        )
    
    def _calculate_completeness_score(
        self,
        total_items: int,
        valid_items: int,
        missing_fields: List[str],
        unknown_codes: List[str]
    ) -> float:
        """
        Calculate completeness score (0.0 to 1.0)
        
        Factors:
        - Valid items ratio (60% weight)
        - Missing fields penalty (20% weight)
        - Unknown codes penalty (20% weight)
        """
        if total_items == 0:
            return 0.0
        
        # Valid items score (60% weight)
        valid_ratio = valid_items / total_items
        valid_score = valid_ratio * 0.60
        
        # Missing fields penalty (20% weight)
        # Penalize based on number of required fields missing
        missing_penalty = len(missing_fields) / len(self.required_fields)
        missing_score = (1.0 - missing_penalty) * 0.20
        
        # Unknown codes penalty (20% weight)
        # Penalize based on ratio of unknown codes
        unknown_ratio = len(unknown_codes) / total_items
        unknown_score = (1.0 - unknown_ratio) * 0.20
        
        total_score = valid_score + missing_score + unknown_score
        
        return min(1.0, max(0.0, total_score))
    
    def estimate_item_count(self, items: List[Dict]) -> Dict:
        """
        Estimate expected item count based on BSR code patterns
        
        Returns:
            Dictionary with count estimates and analysis
        """
        if not items:
            return {
                'extracted_count': 0,
                'estimated_min': 0,
                'estimated_max': 0,
                'confidence': 'low',
                'analysis': 'No items to analyze'
            }
        
        extracted_count = len(items)
        
        # Analyze BSR code patterns
        codes = [item.get('code', '') for item in items if item.get('code')]
        
        # Check for sequential patterns
        sequential_gaps = self._find_sequential_gaps(codes)
        
        # Estimate based on typical work orders
        # Most work orders have 5-50 items
        estimated_min = max(5, extracted_count - 2)
        estimated_max = min(50, extracted_count + 5)
        
        # Adjust based on gaps
        if sequential_gaps:
            estimated_max += len(sequential_gaps)
        
        # Determine confidence
        if sequential_gaps:
            confidence = 'medium'
            analysis = f"Found {len(sequential_gaps)} potential gaps in sequence"
        elif extracted_count < 5:
            confidence = 'low'
            analysis = "Very few items extracted, may be incomplete"
        elif extracted_count > 30:
            confidence = 'medium'
            analysis = "Large number of items, verify completeness"
        else:
            confidence = 'high'
            analysis = "Item count within typical range"
        
        return {
            'extracted_count': extracted_count,
            'estimated_min': estimated_min,
            'estimated_max': estimated_max,
            'confidence': confidence,
            'analysis': analysis,
            'sequential_gaps': sequential_gaps
        }
    
    def _find_sequential_gaps(self, codes: List[str]) -> List[str]:
        """
        Find gaps in sequential BSR codes
        
        Example: If we have 1.1, 1.2, 1.4, 1.5
        Gap detected: 1.3 is missing
        """
        gaps = []
        
        # Group codes by major number
        code_groups = {}
        for code in codes:
            if not code:
                continue
            
            parts = code.split('.')
            if len(parts) >= 2:
                major = parts[0]
                try:
                    minor = int(parts[1])
                    if major not in code_groups:
                        code_groups[major] = []
                    code_groups[major].append(minor)
                except ValueError:
                    continue
        
        # Check for gaps in each group
        for major, minors in code_groups.items():
            if len(minors) < 2:
                continue
            
            minors.sort()
            for i in range(len(minors) - 1):
                current = minors[i]
                next_val = minors[i + 1]
                
                # If gap > 1, there might be missing items
                if next_val - current > 1:
                    for missing in range(current + 1, next_val):
                        gaps.append(f"{major}.{missing}")
        
        return gaps[:10]  # Limit to 10 gaps
    
    def detect_missing_items(
        self,
        items: List[Dict],
        expected_categories: Optional[List[str]] = None
    ) -> Dict:
        """
        Detect potentially missing items based on patterns
        
        Args:
            items: Extracted items
            expected_categories: Optional list of expected categories
            
        Returns:
            Dictionary with missing item analysis
        """
        if not items:
            return {
                'missing_count': 0,
                'missing_categories': [],
                'suggestions': ['No items to analyze']
            }
        
        # Get categories of extracted items
        extracted_categories = set()
        for item in items:
            code = item.get('code', '')
            if code:
                db_item = self.db.get_item_by_code(code)
                if db_item:
                    extracted_categories.add(db_item.get('category', 'Unknown'))
        
        missing_categories = []
        suggestions = []
        
        # Check against expected categories
        if expected_categories:
            for category in expected_categories:
                if category not in extracted_categories:
                    missing_categories.append(category)
                    suggestions.append(f"No items found for category: {category}")
        
        # Check for common missing items
        common_items = [
            '1.1',  # Excavation
            '1.2',  # Filling
            '2.1',  # Cement concrete
            '10.1', # Wiring
        ]
        
        extracted_codes = [item.get('code', '') for item in items]
        for common_code in common_items:
            if common_code not in extracted_codes:
                db_item = self.db.get_item_by_code(common_code)
                if db_item:
                    suggestions.append(
                        f"Common item not found: {common_code} - "
                        f"{db_item.get('description', 'Unknown')}"
                    )
        
        return {
            'missing_count': len(missing_categories),
            'missing_categories': missing_categories,
            'suggestions': suggestions[:5]  # Top 5 suggestions
        }
    
    def generate_report(self, items: List[Dict]) -> str:
        """
        Generate comprehensive completeness report
        
        Args:
            items: Extracted items
            
        Returns:
            Formatted report string
        """
        result = self.check_completeness(items)
        count_estimate = self.estimate_item_count(items)
        missing_analysis = self.detect_missing_items(items)
        
        report = []
        report.append("="*60)
        report.append("COMPLETENESS REPORT")
        report.append("="*60)
        report.append("")
        
        # Overall status
        status = "✓ COMPLETE" if result.is_complete else "⚠ INCOMPLETE"
        report.append(f"Status: {status}")
        report.append(f"Completeness Score: {result.completeness_score:.2%}")
        report.append("")
        
        # Item counts
        report.append("ITEM COUNTS:")
        report.append(f"  Total Items: {result.total_items}")
        report.append(f"  Valid Items: {result.valid_items}")
        report.append(f"  Invalid Items: {result.invalid_items}")
        report.append("")
        
        # Estimates
        report.append("ESTIMATES:")
        report.append(f"  Extracted: {count_estimate['extracted_count']}")
        report.append(f"  Expected Range: {count_estimate['estimated_min']}-{count_estimate['estimated_max']}")
        report.append(f"  Confidence: {count_estimate['confidence'].upper()}")
        report.append(f"  Analysis: {count_estimate['analysis']}")
        report.append("")
        
        # Issues
        if result.warnings:
            report.append("WARNINGS:")
            for warning in result.warnings:
                report.append(f"  • {warning}")
            report.append("")
        
        # Missing items
        if missing_analysis['suggestions']:
            report.append("SUGGESTIONS:")
            for suggestion in missing_analysis['suggestions']:
                report.append(f"  • {suggestion}")
            report.append("")
        
        report.append("="*60)
        
        return "\n".join(report)


def demo():
    """Demo the completeness checker"""
    from modules.pwd_database import PWDDatabase
    
    db = PWDDatabase()
    checker = CompletenessChecker(db)
    
    # Test with sample items
    test_items = [
        {
            'code': '1.1',
            'description': 'Excavation',
            'unit': 'cum',
            'rate': 150.0,
            'quantity': 10
        },
        {
            'code': '1.2',
            'description': 'Filling',
            'unit': 'cum',
            'rate': 120.0,
            'quantity': 8
        },
        {
            'code': '1.4',  # Gap: 1.3 missing
            'description': 'Some work',
            'unit': 'cum',
            'rate': 200.0,
            'quantity': 5
        },
        {
            'code': 'INVALID',  # Unknown code
            'description': 'Unknown item',
            'unit': 'nos',
            'rate': 100.0
        },
        {
            'code': '2.1',
            'description': 'Cement concrete',
            # Missing unit and rate
            'quantity': 3
        }
    ]
    
    print("Testing Completeness Checker")
    print("="*60)
    
    # Check completeness
    result = checker.check_completeness(test_items)
    print(f"\nCompleteness: {result.completeness_score:.2%}")
    print(f"Valid: {result.valid_items}/{result.total_items}")
    print(f"Complete: {result.is_complete}")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  • {warning}")
    
    # Estimate count
    print("\n" + "="*60)
    count_estimate = checker.estimate_item_count(test_items)
    print(f"Extracted: {count_estimate['extracted_count']}")
    print(f"Expected: {count_estimate['estimated_min']}-{count_estimate['estimated_max']}")
    print(f"Confidence: {count_estimate['confidence']}")
    
    if count_estimate['sequential_gaps']:
        print(f"Gaps found: {', '.join(count_estimate['sequential_gaps'])}")
    
    # Full report
    print("\n" + "="*60)
    print(checker.generate_report(test_items))


if __name__ == '__main__':
    demo()
