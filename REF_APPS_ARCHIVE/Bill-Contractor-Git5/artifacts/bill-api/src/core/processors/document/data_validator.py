"""
Data Validator
Validates extracted data against business rules
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ValidationError:
    """Represents a validation error"""
    field: str
    message: str
    severity: str = "error"  # "error", "warning"


@dataclass
class ValidationWarning:
    """Represents a validation warning"""
    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    fields_requiring_review: List[str] = field(default_factory=list)
    
    def add_error(self, field: str, message: str, severity: str = "error"):
        """Add validation error"""
        self.errors.append(ValidationError(field=field, message=message, severity=severity))
        self.is_valid = False
    
    def add_warning(self, field: str, message: str):
        """Add validation warning"""
        self.warnings.append(ValidationWarning(field=field, message=message))
    
    def flag_for_review(self, field: str):
        """Flag field for manual review"""
        if field not in self.fields_requiring_review:
            self.fields_requiring_review.append(field)


class DataValidator:
    """Validates extracted data against business rules"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        """
        Initialize data validator
        
        Args:
            confidence_threshold: Minimum confidence score (0-1) for automatic acceptance
        """
        self.confidence_threshold = confidence_threshold
    
    def validate_work_order(self, work_order_data) -> ValidationResult:
        """
        Validate work order data completeness and correctness
        
        Args:
            work_order_data: WorkOrderData object with items
        
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)
        
        if not work_order_data or not hasattr(work_order_data, 'items'):
            result.add_error("work_order", "Work order data is missing or invalid")
            return result
        
        items = work_order_data.items if hasattr(work_order_data, 'items') else work_order_data
        
        if not items:
            result.add_error("work_order", "No items found in work order")
            return result
        
        # Validate each item
        for idx, item in enumerate(items):
            item_key = f"item_{idx}"
            
            # Check required fields
            if not item.item_number:
                result.add_error(f"{item_key}.item_number", "Item number is missing")
            
            if not item.description:
                result.add_error(f"{item_key}.description", "Item description is missing")
            
            if not item.unit:
                result.add_warning(f"{item_key}.unit", "Unit is missing (will default to 'nos')")
            
            # Check confidence scores
            if item.confidence_score < self.confidence_threshold:
                result.flag_for_review(f"{item_key}")
                result.add_warning(
                    f"{item_key}",
                    f"Low confidence ({item.confidence_score:.0%}) - please review"
                )
        
        return result
    
    def validate_bill_quantities(self, bill_quantities_data, work_order_data) -> ValidationResult:
        """
        Validate quantities reference valid work order items
        
        Args:
            bill_quantities_data: BillQuantitiesData object
            work_order_data: WorkOrderData object for validation
        
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)
        
        # Get valid item numbers from work order
        if hasattr(work_order_data, 'items'):
            valid_items = {item.item_number for item in work_order_data.items}
        else:
            valid_items = {item.item_number for item in work_order_data}
        
        # Get quantities
        if hasattr(bill_quantities_data, 'quantities'):
            quantities = bill_quantities_data.quantities
        else:
            quantities = bill_quantities_data
        
        if not quantities:
            result.add_warning("bill_quantities", "No quantities found in bill quantities page")
            return result
        
        # Validate each quantity
        for item_number, quantity_data in quantities.items():
            # Extract quantity and confidence
            if isinstance(quantity_data, tuple):
                quantity, confidence = quantity_data
            elif hasattr(quantity_data, 'quantity'):
                quantity = quantity_data.quantity
                confidence = quantity_data.confidence_score
            else:
                quantity = quantity_data
                confidence = 1.0
            
            # Verify item number exists in work order
            if item_number not in valid_items:
                result.add_error(
                    f"quantity.{item_number}",
                    f"Item number '{item_number}' not found in work order"
                )
            
            # Verify quantity is positive
            if quantity <= 0:
                result.add_error(
                    f"quantity.{item_number}",
                    f"Quantity must be positive (got {quantity})"
                )
            
            # Check confidence
            if confidence < self.confidence_threshold:
                result.flag_for_review(f"quantity.{item_number}")
                result.add_warning(
                    f"quantity.{item_number}",
                    f"Low confidence ({confidence:.0%}) - please verify quantity {quantity}"
                )
        
        return result
    
    def validate_extra_items(self, extra_items_data) -> ValidationResult:
        """
        Validate extra items have all required fields
        
        Args:
            extra_items_data: ExtraItemsData object
        
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)
        
        # Get items
        if hasattr(extra_items_data, 'items'):
            items = extra_items_data.items
        else:
            items = extra_items_data
        
        if not items:
            # No extra items is valid (optional)
            return result
        
        # Validate each extra item
        for idx, item in enumerate(items):
            item_key = f"extra_item_{idx}"
            
            # Check required fields
            if not item.description:
                result.add_error(f"{item_key}.description", "Description is missing")
            
            if not item.quantity or item.quantity <= 0:
                result.add_error(
                    f"{item_key}.quantity",
                    f"Quantity must be positive (got {item.quantity})"
                )
            
            if not item.rate or item.rate <= 0:
                result.add_error(
                    f"{item_key}.rate",
                    f"Rate must be positive (got {item.rate})"
                )
            
            if not item.unit:
                result.add_warning(f"{item_key}.unit", "Unit is missing (will default to 'nos')")
            
            # Check confidence scores
            if hasattr(item, 'confidence_scores'):
                for field_name, confidence in item.confidence_scores.items():
                    if confidence < self.confidence_threshold:
                        result.flag_for_review(f"{item_key}.{field_name}")
                        result.add_warning(
                            f"{item_key}.{field_name}",
                            f"Low confidence ({confidence:.0%}) - please review"
                        )
        
        return result
    
    def check_confidence_thresholds(self, data: any) -> List[str]:
        """
        Identify fields below confidence threshold
        
        Args:
            data: Data object with confidence scores
        
        Returns:
            List of field names requiring review
        """
        low_confidence_fields = []
        
        # Check if data has items
        if hasattr(data, 'items'):
            items = data.items
            for idx, item in enumerate(items):
                if hasattr(item, 'confidence_score'):
                    if item.confidence_score < self.confidence_threshold:
                        low_confidence_fields.append(f"item_{idx}")
                
                if hasattr(item, 'confidence_scores'):
                    for field_name, confidence in item.confidence_scores.items():
                        if confidence < self.confidence_threshold:
                            low_confidence_fields.append(f"item_{idx}.{field_name}")
        
        # Check if data has quantities
        if hasattr(data, 'quantities'):
            for item_number, quantity_data in data.quantities.items():
                if isinstance(quantity_data, tuple):
                    _, confidence = quantity_data
                    if confidence < self.confidence_threshold:
                        low_confidence_fields.append(f"quantity.{item_number}")
                elif hasattr(quantity_data, 'confidence_score'):
                    if quantity_data.confidence_score < self.confidence_threshold:
                        low_confidence_fields.append(f"quantity.{item_number}")
        
        return low_confidence_fields
    
    def validate_all(self, work_order_data, bill_quantities_data, extra_items_data) -> ValidationResult:
        """
        Validate all extracted data
        
        Args:
            work_order_data: WorkOrderData object
            bill_quantities_data: BillQuantitiesData object
            extra_items_data: ExtraItemsData object
        
        Returns:
            Combined ValidationResult
        """
        combined_result = ValidationResult(is_valid=True)
        
        # Validate work order
        wo_result = self.validate_work_order(work_order_data)
        combined_result.errors.extend(wo_result.errors)
        combined_result.warnings.extend(wo_result.warnings)
        combined_result.fields_requiring_review.extend(wo_result.fields_requiring_review)
        
        # Validate bill quantities
        bq_result = self.validate_bill_quantities(bill_quantities_data, work_order_data)
        combined_result.errors.extend(bq_result.errors)
        combined_result.warnings.extend(bq_result.warnings)
        combined_result.fields_requiring_review.extend(bq_result.fields_requiring_review)
        
        # Validate extra items
        ei_result = self.validate_extra_items(extra_items_data)
        combined_result.errors.extend(ei_result.errors)
        combined_result.warnings.extend(ei_result.warnings)
        combined_result.fields_requiring_review.extend(ei_result.fields_requiring_review)
        
        # Set overall validity
        combined_result.is_valid = (
            wo_result.is_valid and 
            bq_result.is_valid and 
            ei_result.is_valid
        )
        
        return combined_result
