"""
Advanced export formats for the Stream Bill Generator
This module provides XML and JSON export capabilities.
"""
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
import pandas as pd

def generate_json(data: Dict[str, Any], output_path: str) -> bool:
    """
    Generate JSON export of bill data
    
    Args:
        data (Dict[str, Any]): Bill data
        output_path (str): Path where JSON file should be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        print(f"Error generating JSON: {e}")
        return False

def dict_to_xml(tag: str, d: Dict[str, Any]) -> ET.Element:
    """
    Convert a dictionary to XML element
    
    Args:
        tag (str): Root tag name
        d (Dict[str, Any]): Dictionary to convert
        
    Returns:
        ET.Element: XML element
    """
    elem = ET.Element(tag)
    for key, val in d.items():
        if isinstance(val, dict):
            child = dict_to_xml(key, val)
            elem.append(child)
        elif isinstance(val, list):
            child = ET.Element(key)
            for item in val:
                if isinstance(item, dict):
                    grandchild = dict_to_xml("item", item)
                    child.append(grandchild)
                else:
                    grandchild = ET.Element("item")
                    grandchild.text = str(item)
                    child.append(grandchild)
            elem.append(child)
        else:
            child = ET.Element(key)
            child.text = str(val)
            elem.append(child)
    return elem

def generate_xml(data: Dict[str, Any], output_path: str) -> bool:
    """
    Generate XML export of bill data
    
    Args:
        data (Dict[str, Any]): Bill data
        output_path (str): Path where XML file should be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        root = dict_to_xml("bill", data)
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        return True
    except Exception as e:
        print(f"Error generating XML: {e}")
        return False

def create_bill_dataframe(first_page_data: Dict[str, Any], 
                         deviation_data: Dict[str, Any],
                         extra_items_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a consolidated DataFrame from bill data
    
    Args:
        first_page_data (Dict[str, Any]): First page data
        deviation_data (Dict[str, Any]): Deviation statement data
        extra_items_data (Dict[str, Any]): Extra items data
        
    Returns:
        pd.DataFrame: Consolidated DataFrame
    """
    # Extract items from first page
    items = []
    
    # Add work order items
    for item in first_page_data.get("items", []):
        if not item.get("is_divider", False):
            items.append({
                "type": "work_order",
                "serial_no": item.get("serial_no", ""),
                "description": item.get("description", ""),
                "unit": item.get("unit", ""),
                "quantity": item.get("quantity", 0),
                "rate": item.get("rate", 0),
                "amount": item.get("amount", 0),
                "remark": item.get("remark", "")
            })
    
    # Add extra items
    for item in extra_items_data.get("items", []):
        items.append({
            "type": "extra_item",
            "serial_no": item.get("serial_no", ""),
            "description": item.get("description", ""),
            "unit": item.get("unit", ""),
            "quantity": item.get("quantity", 0),
            "rate": item.get("rate", 0),
            "amount": item.get("amount", 0),
            "remark": item.get("remark", "")
        })
    
    # Add deviation items
    for item in deviation_data.get("items", []):
        items.append({
            "type": "deviation",
            "serial_no": item.get("serial_no", ""),
            "description": item.get("description", ""),
            "unit": item.get("unit", ""),
            "qty_wo": item.get("qty_wo", 0),
            "rate": item.get("rate", 0),
            "amt_wo": item.get("amt_wo", 0),
            "qty_bill": item.get("qty_bill", 0),
            "amt_bill": item.get("amt_bill", 0),
            "excess_qty": item.get("excess_qty", 0),
            "excess_amt": item.get("excess_amt", 0),
            "saving_qty": item.get("saving_qty", 0),
            "saving_amt": item.get("saving_amt", 0),
            "remark": item.get("remark", "")
        })
    
    return pd.DataFrame(items)

def export_to_csv(first_page_data: Dict[str, Any], 
                 deviation_data: Dict[str, Any],
                 extra_items_data: Dict[str, Any],
                 output_path: str) -> bool:
    """
    Export bill data to CSV format
    
    Args:
        first_page_data (Dict[str, Any]): First page data
        deviation_data (Dict[str, Any]): Deviation statement data
        extra_items_data (Dict[str, Any]): Extra items data
        output_path (str): Path where CSV file should be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        df = create_bill_dataframe(first_page_data, deviation_data, extra_items_data)
        df.to_csv(output_path, index=False)
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False

def export_bill_data(first_page_data: Dict[str, Any], 
                    last_page_data: Dict[str, Any],
                    deviation_data: Dict[str, Any],
                    extra_items_data: Dict[str, Any],
                    note_sheet_data: Dict[str, Any],
                    output_dir: str) -> List[str]:
    """
    Export all bill data to multiple formats
    
    Args:
        first_page_data (Dict[str, Any]): First page data
        last_page_data (Dict[str, Any]): Last page data
        deviation_data (Dict[str, Any]): Deviation statement data
        extra_items_data (Dict[str, Any]): Extra items data
        note_sheet_data (Dict[str, Any]): Note sheet data
        output_dir (str): Directory where files should be saved
        
    Returns:
        List[str]: List of generated file paths
    """
    import os
    generated_files = []
    
    # Combine all data into a single structure
    all_data = {
        "first_page": first_page_data,
        "last_page": last_page_data,
        "deviation_statement": deviation_data,
        "extra_items": extra_items_data,
        "note_sheet": note_sheet_data
    }
    
    # Generate JSON
    json_path = os.path.join(output_dir, "bill_data.json")
    if generate_json(all_data, json_path):
        generated_files.append(json_path)
    
    # Generate XML
    xml_path = os.path.join(output_dir, "bill_data.xml")
    if generate_xml(all_data, xml_path):
        generated_files.append(xml_path)
    
    # Generate CSV
    csv_path = os.path.join(output_dir, "bill_data.csv")
    if export_to_csv(first_page_data, deviation_data, extra_items_data, csv_path):
        generated_files.append(csv_path)
    
    return generated_files

if __name__ == "__main__":
    # Example usage
    sample_data = {
        "header": [["Agreement No.", "123/2024"]],
        "items": [
            {"unit": "M", "quantity": "100", "serial_no": "1", "description": "Sample Item", "rate": "50", "amount": "5000", "remark": "Test"}
        ],
        "totals": {
            "grand_total": "5000",
            "premium": {"percent": 0.05, "amount": "250"},
            "payable": "5250"
        }
    }
    
    # Test JSON generation
    success = generate_json(sample_data, "sample_output.json")
    print(f"JSON generation: {'Success' if success else 'Failed'}")
    
    # Test XML generation
    success = generate_xml(sample_data, "sample_output.xml")
    print(f"XML generation: {'Success' if success else 'Failed'}")