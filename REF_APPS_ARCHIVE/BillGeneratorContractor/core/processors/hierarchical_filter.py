"""
Hierarchical Zero Quantity Filtering Module

Filters out items in a hierarchical structure where all descendants have zero quantities.
"""

from functools import lru_cache
from typing import List, Dict, Any
import pandas as pd
import re


class HierarchicalItem:
    """
    Represents an item in a hierarchical structure
    """
    def __init__(self, code: str, description: str, quantity: float, unit: str = "", rate: float = 0.0):
        self.code = code
        self.description = description
        self.quantity = quantity
        self.unit = unit
        self.rate = rate
        self.children: List[HierarchicalItem] = []


def should_populate_item(item: HierarchicalItem) -> bool:
    """
    Determine if an item should be populated based on descendant quantities
    
    Args:
        item: The item to evaluate
        
    Returns:
        bool: True if item should be populated, False otherwise
    """
    # If item itself has quantity > 0, always populate
    if item.quantity > 0:
        return True
    
    # Check if any descendant has quantity > 0
    if has_any_nonzero_descendant(item):
        return True
    
    # All descendants are zero, don't populate
    return False


def has_any_nonzero_descendant(item: HierarchicalItem) -> bool:
    """
    Recursively check if any descendant has non-zero quantity
    
    Args:
        item: The item to check
        
    Returns:
        bool: True if any descendant has non-zero quantity, False otherwise
    """
    for child in item.children:
        if child.quantity > 0:
            return True
        if has_any_nonzero_descendant(child):
            return True
    return False


def filter_zero_hierarchy(items: List[HierarchicalItem]) -> List[HierarchicalItem]:
    """
    Filter out items where all descendants have zero quantities
    
    Args:
        items: List of hierarchical items to filter
        
    Returns:
        List[HierarchicalItem]: Filtered list of items
    """
    filtered_items = []
    
    for item in items:
        if should_populate_item(item):
            # Recursively filter children
            filtered_children = filter_zero_hierarchy(item.children)
            item.children = filtered_children
            filtered_items.append(item)
        # Else: Don't add item to filtered list (effectively removing it)
    
    return filtered_items


def parse_item_code_level(code: str) -> int:
    """
    Determine the hierarchical level of an item based on its code
    E.g., "1.0" -> level 1, "1.1" -> level 2, "1.1.1" -> level 3
    
    Args:
        code: Item code string
        
    Returns:
        int: Hierarchical level (0 for root level items)
    """
    if not code or pd.isna(code):
        return 0
    
    # Count the number of dots to determine level
    return code.count('.')


def build_hierarchy_from_list(items: List[HierarchicalItem]) -> List[HierarchicalItem]:
    """
    Build hierarchical tree structure from flat list of items
    
    Args:
        items: Flat list of hierarchical items
        
    Returns:
        List[HierarchicalItem]: Root level items with children properly assigned
    """
    if not items:
        return []
    
    # Sort items by code to ensure proper ordering
    sorted_items = sorted(items, key=lambda x: x.code if x.code else "")
    
    # Create a map of code to item for quick lookup
    item_map = {item.code: item for item in sorted_items}
    
    # Root items (level 0)
    root_items = []
    
    # Assign children to parents
    for item in sorted_items:
        if not item.code or pd.isna(item.code):
            continue
            
        # Find parent by removing last part of code
        code_parts = item.code.split('.')
        if len(code_parts) > 1:
            # This is a child item, find its parent
            parent_code = '.'.join(code_parts[:-1])
            if parent_code in item_map:
                item_map[parent_code].children.append(item)
        else:
            # This is a root item
            root_items.append(item)
    
    return root_items


def parse_hierarchical_items(df: pd.DataFrame) -> List[HierarchicalItem]:
    """
    Parse hierarchical structure of work order items from DataFrame
    
    Args:
        df: DataFrame containing work order data
        
    Returns:
        List[HierarchicalItem]: List of hierarchical items
    """
    if df is None or df.empty:
        return []
    
    items = []
    
    # Process each row in the DataFrame
    for _, row in df.iterrows():
        # Extract relevant fields
        code = row.get('Item No.', row.get('Item', ''))
        description = row.get('Description', '')
        unit = row.get('Unit', '')
        quantity = 0.0
        rate = 0.0
        
        # Try different column names for quantity
        quantity_cols = ['Quantity', 'Quantity Since', 'Quantity Upto']
        for col in quantity_cols:
            if col in row and pd.notna(row[col]):
                try:
                    quantity = float(row[col])
                    break
                except (ValueError, TypeError):
                    continue
        
        # Try different column names for rate
        rate_cols = ['Rate']
        for col in rate_cols:
            if col in row and pd.notna(row[col]):
                try:
                    rate = float(row[col])
                    break
                except (ValueError, TypeError):
                    continue
        
        # Create hierarchical item
        item = HierarchicalItem(
            code=str(code) if pd.notna(code) else "",
            description=str(description) if pd.notna(description) else "",
            quantity=quantity,
            unit=str(unit) if pd.notna(unit) else "",
            rate=rate
        )
        items.append(item)
    
    # Build hierarchy from flat list
    hierarchical_items = build_hierarchy_from_list(items)
    
    return hierarchical_items


def generate_filtered_summary(filtered_items: List[HierarchicalItem], 
                            filtered_extra_items: List[HierarchicalItem]) -> Dict[str, Any]:
    """
    Generate summary for filtered items
    
    Args:
        filtered_items: List of filtered work order items
        filtered_extra_items: List of filtered extra items
        
    Returns:
        Dict[str, Any]: Summary information
    """
    return {
        'total_filtered_items': len(filtered_items),
        'total_filtered_extra_items': len(filtered_extra_items)
    }


def generate_first_page(work_order_data: Any) -> Dict[str, Any]:
    """
    Generate first page with zero-filtering applied
    
    Args:
        work_order_data: Work order data
        
    Returns:
        Dict[str, Any]: First page data with filtered items
    """
    # Filter work order items
    filtered_items = filter_zero_hierarchy(work_order_data.work_order_items)
    
    # Filter extra items  
    filtered_extra_items = filter_zero_hierarchy(work_order_data.extra_items)
    
    # Generate clean first page
    first_page = {
        'work_order_items': filtered_items,
        'extra_items': filtered_extra_items,
        'summary': generate_filtered_summary(filtered_items, filtered_extra_items)
    }
    
    return first_page


def generate_deviation_sheet(original_items: List[HierarchicalItem], 
                           current_items: List[HierarchicalItem]) -> Dict[str, Any]:
    """
    Generate deviation sheet with zero-filtering
    
    Args:
        original_items: Original items
        current_items: Current items
        
    Returns:
        Dict[str, Any]: Deviation sheet data
    """
    # Filter both original and current items
    filtered_original = filter_zero_hierarchy(original_items)
    filtered_current = filter_zero_hierarchy(current_items)
    
    # Calculate deviations only for populated items
    # Note: This is a placeholder - actual implementation would depend on 
    # how deviations are calculated in your system
    deviations = []  # calculate_deviations(filtered_original, filtered_current)
    
    return {
        'deviations': deviations,
        'summary': {}  # generate_deviation_summary(deviations)
    }


@lru_cache(maxsize=128)
def get_filtered_hierarchy(items_hash: str) -> List[HierarchicalItem]:
    """
    Cache filtered hierarchies to avoid recomputation
    
    Args:
        items_hash: Hash of items to filter
        
    Returns:
        List[HierarchicalItem]: Filtered list of items
    """
    # This is a placeholder - would need actual implementation
    # to decode items_hash and apply filtering
    return []


def process_work_order_sheet(df: Any) -> Any:
    """
    Process work order sheet with zero filtering
    
    Args:
        df: DataFrame containing work order data
        
    Returns:
        Any: Clean worksheet data
    """
    # Parse hierarchical structure
    items = parse_hierarchical_items(df)
    
    # Apply zero filtering
    filtered_items = filter_zero_hierarchy(items)
    
    # Generate clean worksheet (placeholder)
    return filtered_items


def generate_reports(work_data: Any) -> Dict[str, Any]:
    """
    Generate all reports with zero filtering applied
    
    Args:
        work_data: Work data
        
    Returns:
        Dict[str, Any]: Reports with zero filtering applied
    """
    reports = {
        'first_page': generate_first_page(work_data),
        'deviation_sheet': generate_deviation_sheet(
            work_data.original_items, 
            work_data.current_items
        ),
        'scrutiny_sheet': {}  # generate_scrutiny_sheet(work_data)
    }
    
    # Apply zero filtering to all reports
    for report_name, report_data in reports.items():
        # In a real implementation, you would apply filtering specific to each report type
        pass
    
    return reports


def hierarchical_items_to_dataframe(items: List[HierarchicalItem]) -> pd.DataFrame:
    """
    Convert HierarchicalItem objects back to DataFrame
    
    Args:
        items: List of HierarchicalItem objects
        
    Returns:
        pd.DataFrame: DataFrame with hierarchical items flattened
    """
    rows = []
    
    def flatten_items(item_list, rows_list):
        """Recursively flatten hierarchical items"""
        for item in item_list:
            rows_list.append({
                'Item No.': item.code,
                'Description': item.description,
                'Unit': item.unit,
                'Quantity': item.quantity,
                'Rate': item.rate
            })
            if item.children:
                flatten_items(item.children, rows_list)
    
    flatten_items(items, rows)
    return pd.DataFrame(rows)


def apply_hierarchical_filtering(work_order_data: pd.DataFrame, bill_quantity_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Apply hierarchical filtering to work order and bill quantity data
    
    Filters out items where all descendants have zero quantities while maintaining
    parent items if any child has non-zero quantity.
    
    Args:
        work_order_data: Work order data from Excel
        bill_quantity_data: Bill quantity data from Excel
        
    Returns:
        Dict[str, Any]: Filtered data as DataFrames
    """
    # If data is empty, return as-is
    if work_order_data.empty and bill_quantity_data.empty:
        return {
            'filtered_work_order_data': work_order_data,
            'filtered_bill_quantity_data': bill_quantity_data
        }
    
    try:
        # Parse to hierarchical structure
        work_order_items = parse_hierarchical_items(work_order_data)
        bill_quantity_items = parse_hierarchical_items(bill_quantity_data)
        
        # Apply filtering
        filtered_work_order_items = filter_zero_hierarchy(work_order_items)
        filtered_bill_quantity_items = filter_zero_hierarchy(bill_quantity_items)
        
        # Convert back to DataFrames
        filtered_work_order_df = hierarchical_items_to_dataframe(filtered_work_order_items)
        filtered_bill_quantity_df = hierarchical_items_to_dataframe(filtered_bill_quantity_items)
        
        # If filtering resulted in empty DataFrames, return original data
        # This prevents issues when all items have zero quantities
        if filtered_work_order_df.empty and not work_order_data.empty:
            filtered_work_order_df = work_order_data
        if filtered_bill_quantity_df.empty and not bill_quantity_data.empty:
            filtered_bill_quantity_df = bill_quantity_data
        
        return {
            'filtered_work_order_data': filtered_work_order_df,
            'filtered_bill_quantity_data': filtered_bill_quantity_df
        }
    except Exception as e:
        # If filtering fails, return original data to maintain compatibility
        print(f"Warning: Hierarchical filtering failed: {e}")
        print("Returning original data without filtering")
        return {
            'filtered_work_order_data': work_order_data,
            'filtered_bill_quantity_data': bill_quantity_data
        }