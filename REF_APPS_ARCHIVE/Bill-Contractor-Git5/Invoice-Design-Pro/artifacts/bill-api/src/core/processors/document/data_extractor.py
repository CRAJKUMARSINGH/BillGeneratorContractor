"""
Data Extractor
Parses OCR/HWR output into structured fields
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class WorkOrderItem:
    """Represents a single item from work order"""
    item_number: str
    description: str
    unit: str
    confidence_score: float
    page_number: int = 1


@dataclass
class ExtraItem:
    """Additional item not in work order"""
    description: str
    quantity: float
    rate: float
    unit: str
    confidence_scores: Dict[str, float]


class ExtractionRules:
    """Rules for extracting specific patterns"""
    
    # Item number patterns
    ITEM_NUMBER_PATTERNS = [
        r'^\d+(?:\.\d+)*',  # 1, 1.1, 1.2.3
        r'^\w+-\d+',         # A-1, B-5
        r'^\d+[A-Z]?',       # 1A, 2B
    ]
    
    # Unit patterns
    COMMON_UNITS = [
        'sqm', 'sq.m', 'sq m', 'square meter',
        'cum', 'cu.m', 'cu m', 'cubic meter',
        'kg', 'kilogram',
        'nos', 'no', 'number', 'numbers',
        'rmt', 'running meter',
        'mt', 'meter', 'metre',
        'ltr', 'litre', 'liter',
        'each', 'set', 'pair', 'piece'
    ]
    
    # Quantity patterns
    QUANTITY_PATTERN = r'\d+\.?\d*'
    
    # Rate patterns (with currency symbols)
    RATE_PATTERN = r'(?:Rs\.?|₹)?\s*\d+\.?\d*'


class DataExtractor:
    """Extracts structured data from OCR/HWR results"""
    
    def __init__(self):
        """Initialize data extractor"""
        self.rules = ExtractionRules()
    
    def extract_work_order_items(self, ocr_result, page_number: int = 1) -> List[WorkOrderItem]:
        """
        Parse work order text into structured items
        
        Args:
            ocr_result: OCR result object with text and words
            page_number: Page number for multi-page documents
        
        Returns:
            List of WorkOrderItem objects
        """
        items = []
        lines = ocr_result.text.split('\n')
        
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with item number
            item_number = self._extract_item_number(line)
            
            if item_number:
                # Save previous item if exists
                if current_item:
                    items.append(current_item)
                
                # Start new item
                remaining_text = line[len(item_number):].strip()
                
                # Extract unit from end of line
                unit, description = self._extract_unit_and_description(remaining_text)
                
                # Calculate confidence from OCR words
                confidence = self._calculate_line_confidence(line, ocr_result.words)
                
                current_item = WorkOrderItem(
                    item_number=item_number,
                    description=description,
                    unit=unit,
                    confidence_score=confidence,
                    page_number=page_number
                )
            elif current_item:
                # Continuation of description
                current_item.description += ' ' + line
        
        # Add last item
        if current_item:
            items.append(current_item)
        
        return items
    
    def extract_bill_quantities(self, hwr_result, valid_items: List[str]) -> Dict[str, Tuple[float, float]]:
        """
        Parse handwritten quantities and match to item numbers
        
        Args:
            hwr_result: HWR result object with text and lines
            valid_items: List of valid item numbers from work order
        
        Returns:
            Dictionary mapping item_number to (quantity, confidence)
        """
        quantities = {}
        
        # Try to extract item-quantity pairs directly
        if hasattr(hwr_result, 'lines'):
            for line in hwr_result.lines:
                text = line.text.strip()
                
                # Pattern: item number followed by quantity
                match = re.match(r'^(\d+(?:\.\d+)*|\w+-\d+)\s+(\d+\.?\d*)$', text)
                
                if match:
                    item_number = match.group(1)
                    quantity = float(match.group(2))
                    
                    # Only include if item number is valid
                    if item_number in valid_items:
                        quantities[item_number] = (quantity, line.confidence)
        
        # Fallback: parse text line by line
        if not quantities:
            lines = hwr_result.text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract item number
                item_number = self._extract_item_number(line)
                
                if item_number and item_number in valid_items:
                    # Extract quantity (first number after item number)
                    remaining = line[len(item_number):].strip()
                    quantity_match = re.search(self.rules.QUANTITY_PATTERN, remaining)
                    
                    if quantity_match:
                        quantity = float(quantity_match.group())
                        confidence = 0.7  # Default confidence for fallback parsing
                        quantities[item_number] = (quantity, confidence)
        
        return quantities
    
    def extract_extra_items(self, hwr_result) -> List[ExtraItem]:
        """
        Parse handwritten extra items with descriptions, quantities, and rates
        
        Args:
            hwr_result: HWR result object
        
        Returns:
            List of ExtraItem objects
        """
        extra_items = []
        lines = hwr_result.text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to extract: description, quantity, rate, unit
            # Pattern: "Description 10 sqm @ Rs. 500"
            # Or: "Description 10 500 sqm"
            
            # Extract all numbers
            numbers = re.findall(self.rules.QUANTITY_PATTERN, line)
            
            if len(numbers) >= 2:
                # Assume first number is quantity, second is rate
                quantity = float(numbers[0])
                rate = float(numbers[1])
                
                # Extract unit
                unit = self._extract_unit_from_text(line)
                
                # Description is everything before the first number
                first_number_pos = line.find(numbers[0])
                description = line[:first_number_pos].strip()
                
                # Remove common prefixes
                description = re.sub(r'^(extra|additional|new)\s+', '', description, flags=re.IGNORECASE)
                
                if description:
                    extra_item = ExtraItem(
                        description=description,
                        quantity=quantity,
                        rate=rate,
                        unit=unit or 'nos',
                        confidence_scores={
                            'description': 0.7,
                            'quantity': 0.8,
                            'rate': 0.8,
                            'unit': 0.7
                        }
                    )
                    extra_items.append(extra_item)
        
        return extra_items
    
    def apply_extraction_rules(self, raw_data: str, rules: ExtractionRules) -> Dict:
        """
        Apply regex patterns and business rules to extract fields
        
        Args:
            raw_data: Raw text data
            rules: Extraction rules to apply
        
        Returns:
            Dictionary of extracted fields
        """
        extracted = {}
        
        # Extract item numbers
        item_numbers = []
        for pattern in rules.ITEM_NUMBER_PATTERNS:
            matches = re.findall(pattern, raw_data, re.MULTILINE)
            item_numbers.extend(matches)
        extracted['item_numbers'] = list(set(item_numbers))
        
        # Extract quantities
        quantities = re.findall(rules.QUANTITY_PATTERN, raw_data)
        extracted['quantities'] = [float(q) for q in quantities]
        
        # Extract rates
        rates = re.findall(rules.RATE_PATTERN, raw_data)
        extracted['rates'] = [self._parse_rate(r) for r in rates]
        
        # Extract units
        units = []
        for unit in rules.COMMON_UNITS:
            if unit.lower() in raw_data.lower():
                units.append(unit)
        extracted['units'] = list(set(units))
        
        return extracted
    
    def _extract_item_number(self, text: str) -> Optional[str]:
        """Extract item number from beginning of text"""
        for pattern in self.rules.ITEM_NUMBER_PATTERNS:
            match = re.match(pattern, text)
            if match:
                return match.group()
        return None
    
    def _extract_unit_and_description(self, text: str) -> Tuple[str, str]:
        """
        Extract unit and description from text
        
        Returns:
            Tuple of (unit, description)
        """
        text_lower = text.lower()
        
        # Check for units at the end
        for unit in self.rules.COMMON_UNITS:
            if text_lower.endswith(unit):
                description = text[:len(text) - len(unit)].strip()
                return unit, description
            
            # Check with space
            if f' {unit}' in text_lower:
                parts = text_lower.rsplit(unit, 1)
                description = text[:len(parts[0])].strip()
                return unit, description
        
        # No unit found
        return '', text
    
    def _extract_unit_from_text(self, text: str) -> str:
        """Extract unit from anywhere in text"""
        text_lower = text.lower()
        
        for unit in self.rules.COMMON_UNITS:
            if unit in text_lower:
                return unit
        
        return ''
    
    def _calculate_line_confidence(self, line: str, words: List) -> float:
        """Calculate confidence for a line based on OCR words"""
        if not words:
            return 0.5
        
        # Find words that appear in this line
        line_words = [w for w in words if w.text in line]
        
        if not line_words:
            return 0.5
        
        # Average confidence
        return sum(w.confidence for w in line_words) / len(line_words)
    
    def _parse_rate(self, rate_str: str) -> float:
        """Parse rate string to float"""
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[Rs\.₹\s]', '', rate_str)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
