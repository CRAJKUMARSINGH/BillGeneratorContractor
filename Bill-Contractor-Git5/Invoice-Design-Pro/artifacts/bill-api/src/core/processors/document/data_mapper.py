"""
Data Mapper
Transforms extracted data into Bill Generator format
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class BillItem:
    """Final bill item for bill generator"""
    item_number: str
    description: str
    unit: str
    quantity: float
    rate: Optional[float] = None
    is_extra_item: bool = False
    confidence_score: float = 1.0


@dataclass
class BillGeneratorInput:
    """Complete input for bill generator system"""
    items: List[BillItem]
    work_order_metadata: Dict
    extraction_metadata: Dict
    original_files: List[Path] = field(default_factory=list)


class DataMapper:
    """Transforms extracted data into Bill Generator format"""
    
    def __init__(self):
        """Initialize data mapper"""
        pass
    
    def map_to_bill_format(self, work_order_data, bill_quantities_data, 
                          extra_items_data, metadata: Optional[Dict] = None) -> BillGeneratorInput:
        """
        Transform all extracted data into bill generator format
        
        Args:
            work_order_data: WorkOrderData object
            bill_quantities_data: BillQuantitiesData object
            extra_items_data: ExtraItemsData object
            metadata: Optional metadata dictionary
        
        Returns:
            BillGeneratorInput object
        """
        # Merge work order items with quantities
        bill_items = self.merge_work_order_and_quantities(work_order_data, bill_quantities_data)
        
        # Add extra items
        if extra_items_data:
            extra_bill_items = self._convert_extra_items(extra_items_data)
            bill_items.extend(extra_bill_items)
        
        # Create metadata
        work_order_metadata = self._extract_work_order_metadata(work_order_data)
        extraction_metadata = self._create_extraction_metadata(
            work_order_data, bill_quantities_data, extra_items_data, metadata
        )
        
        # Get original files
        original_files = []
        if metadata and 'original_files' in metadata:
            original_files = metadata['original_files']
        
        return BillGeneratorInput(
            items=bill_items,
            work_order_metadata=work_order_metadata,
            extraction_metadata=extraction_metadata,
            original_files=original_files
        )
    
    def create_excel_compatible_structure(self, bill_generator_input: BillGeneratorInput) -> Dict:
        """
        Create structure matching Excel processor output
        
        Args:
            bill_generator_input: BillGeneratorInput object
        
        Returns:
            Dictionary compatible with existing Bill Generator
        """
        # Convert to format expected by existing bill generator
        excel_format = {
            'items': [],
            'metadata': {
                **bill_generator_input.work_order_metadata,
                **bill_generator_input.extraction_metadata
            }
        }
        
        for item in bill_generator_input.items:
            excel_item = {
                'item_number': item.item_number,
                'description': item.description,
                'unit': item.unit,
                'quantity': item.quantity,
                'rate': item.rate if item.rate else 0.0,
                'is_extra': item.is_extra_item,
                'confidence': item.confidence_score
            }
            excel_format['items'].append(excel_item)
        
        return excel_format
    
    def merge_work_order_and_quantities(self, work_order_data, 
                                       bill_quantities_data) -> List[BillItem]:
        """
        Combine work order items with extracted quantities
        
        Args:
            work_order_data: WorkOrderData object
            bill_quantities_data: BillQuantitiesData object
        
        Returns:
            List of BillItem objects
        """
        bill_items = []
        
        # Get work order items
        if hasattr(work_order_data, 'items'):
            wo_items = work_order_data.items
        else:
            wo_items = work_order_data
        
        # Get quantities dictionary
        if hasattr(bill_quantities_data, 'quantities'):
            quantities = bill_quantities_data.quantities
        else:
            quantities = bill_quantities_data if bill_quantities_data else {}
        
        # Process each work order item
        for wo_item in wo_items:
            item_number = wo_item.item_number
            
            # Check if quantity exists for this item
            if item_number in quantities:
                # Extract quantity and confidence
                quantity_data = quantities[item_number]
                if isinstance(quantity_data, tuple):
                    quantity, confidence = quantity_data
                elif hasattr(quantity_data, 'quantity'):
                    quantity = quantity_data.quantity
                    confidence = quantity_data.confidence_score
                else:
                    quantity = float(quantity_data)
                    confidence = 1.0
            else:
                # Set quantity to 0 for items not in bill quantities
                quantity = 0.0
                confidence = 1.0
            
            # Create bill item
            bill_item = BillItem(
                item_number=item_number,
                description=wo_item.description,
                unit=wo_item.unit or 'nos',
                quantity=quantity,
                rate=None,  # Rate comes from work order or pricing database
                is_extra_item=False,
                confidence_score=min(wo_item.confidence_score, confidence)
            )
            bill_items.append(bill_item)
        
        return bill_items
    
    def _convert_extra_items(self, extra_items_data) -> List[BillItem]:
        """Convert extra items to BillItem format"""
        bill_items = []
        
        # Get extra items
        if hasattr(extra_items_data, 'items'):
            extra_items = extra_items_data.items
        else:
            extra_items = extra_items_data if extra_items_data else []
        
        # Generate item numbers for extra items
        for idx, extra_item in enumerate(extra_items, start=1):
            # Calculate average confidence
            if hasattr(extra_item, 'confidence_scores'):
                avg_confidence = sum(extra_item.confidence_scores.values()) / len(extra_item.confidence_scores)
            else:
                avg_confidence = 0.7
            
            bill_item = BillItem(
                item_number=f"EXTRA-{idx}",
                description=extra_item.description,
                unit=extra_item.unit or 'nos',
                quantity=extra_item.quantity,
                rate=extra_item.rate,
                is_extra_item=True,
                confidence_score=avg_confidence
            )
            bill_items.append(bill_item)
        
        return bill_items
    
    def _extract_work_order_metadata(self, work_order_data) -> Dict:
        """Extract metadata from work order"""
        metadata = {}
        
        if hasattr(work_order_data, 'metadata'):
            wo_metadata = work_order_data.metadata
            metadata['work_order_file'] = getattr(wo_metadata, 'file_name', 'Unknown')
            metadata['work_order_upload_time'] = getattr(wo_metadata, 'upload_timestamp', datetime.now().isoformat())
            metadata['work_order_pages'] = getattr(wo_metadata, 'page_count', 1)
        
        # Count items
        if hasattr(work_order_data, 'items'):
            metadata['total_items'] = len(work_order_data.items)
        
        return metadata
    
    def _create_extraction_metadata(self, work_order_data, bill_quantities_data, 
                                   extra_items_data, additional_metadata: Optional[Dict]) -> Dict:
        """Create extraction metadata"""
        metadata = {
            'extraction_timestamp': datetime.now().isoformat(),
            'extraction_method': 'AI-powered document processing',
            'ocr_engine': 'Tesseract',
            'hwr_engine': 'Google Cloud Vision',
        }
        
        # Calculate statistics
        if hasattr(work_order_data, 'items'):
            wo_items = work_order_data.items
            if wo_items:
                avg_wo_confidence = sum(item.confidence_score for item in wo_items) / len(wo_items)
                metadata['work_order_avg_confidence'] = f"{avg_wo_confidence:.2%}"
        
        if hasattr(bill_quantities_data, 'quantities'):
            quantities = bill_quantities_data.quantities
            metadata['quantities_extracted'] = len(quantities)
        
        if hasattr(extra_items_data, 'items'):
            extra_items = extra_items_data.items
            metadata['extra_items_count'] = len(extra_items) if extra_items else 0
        
        # Add additional metadata
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return metadata
