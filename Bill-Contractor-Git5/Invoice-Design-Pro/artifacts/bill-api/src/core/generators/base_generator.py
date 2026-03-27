"""
Base Generator - Base class for all document generators
"""
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os

class BaseGenerator:
    """Base class for all document generators"""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.title_data = data.get('title_data', {})
        self.work_order_data = data.get('work_order_data', pd.DataFrame())
        self.bill_quantity_data = data.get('bill_quantity_data', pd.DataFrame())
        self.extra_items_data = data.get('extra_items_data', pd.DataFrame())
        
        # Set up Jinja2 environment for templates
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Template cache
        self._template_cache = {}
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        if pd.isna(value) or value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_serial_no(self, value) -> str:
        """Safely convert serial number to string"""
        if pd.isna(value) or value is None:
            return ''
        return str(value)
    
    def _format_unit_or_text(self, value) -> str:
        """Format unit or text value"""
        if pd.isna(value) or value is None:
            return ''
        return str(value)
    
    def _format_number(self, value) -> str:
        """Format number for display"""
        if value == 0:
            return ''
        return f"{value:.2f}"
    
    def _number_to_words(self, num: int) -> str:
        """Convert number to words using Indian numbering system (Lakh, Crore)"""
        ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
        teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
        tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
        
        if num == 0:
            return 'Zero'
        
        def convert_below_hundred(n):
            """Convert numbers below 100 to words"""
            if n == 0:
                return ''
            elif n < 10:
                return ones[n]
            elif n < 20:
                return teens[n - 10]
            else:
                return tens[n // 10] + ('' if n % 10 == 0 else ' ' + ones[n % 10])
        
        def convert_below_thousand(n):
            """Convert numbers below 1000 to words"""
            if n == 0:
                return ''
            elif n < 100:
                return convert_below_hundred(n)
            else:
                hundred_part = ones[n // 100] + ' Hundred'
                remainder = n % 100
                if remainder == 0:
                    return hundred_part
                else:
                    return hundred_part + ' ' + convert_below_hundred(remainder)
        
        # Handle Indian numbering system: Crore, Lakh, Thousand, Hundred
        if num < 0:
            return 'Minus ' + self._number_to_words(-num)
        
        result = []
        
        # Crores (10,000,000)
        if num >= 10000000:
            crore = num // 10000000
            result.append(convert_below_thousand(crore) + ' Crore')
            num = num % 10000000
        
        # Lakhs (100,000)
        if num >= 100000:
            lakh = num // 100000
            result.append(convert_below_hundred(lakh) + ' Lakh')
            num = num % 100000
        
        # Thousands (1,000)
        if num >= 1000:
            thousand = num // 1000
            result.append(convert_below_hundred(thousand) + ' Thousand')
            num = num % 1000
        
        # Hundreds and below
        if num > 0:
            result.append(convert_below_thousand(num))
        
        return ' '.join(result)
    
    def _has_extra_items(self) -> bool:
        """Check if there are extra items to include"""
        if isinstance(self.extra_items_data, pd.DataFrame):
            return not self.extra_items_data.empty
        return False
    
    def _calculate_delay_days(self) -> int:
        """Calculate delay days between scheduled and actual completion dates"""
        try:
            from datetime import datetime
            
            # Get scheduled completion date
            scheduled_str = self.title_data.get('St. date of completion :', '')
            # Get actual completion date
            actual_str = self.title_data.get('Date of actual completion of work :', '')
            
            if not scheduled_str or not actual_str:
                return 0
            
            # Parse dates - try multiple formats
            date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
            
            scheduled_date = None
            actual_date = None
            
            for fmt in date_formats:
                try:
                    scheduled_date = datetime.strptime(str(scheduled_str).strip(), fmt)
                    break
                except:
                    continue
            
            for fmt in date_formats:
                try:
                    actual_date = datetime.strptime(str(actual_str).strip(), fmt)
                    break
                except:
                    continue
            
            if scheduled_date and actual_date:
                delay = (actual_date - scheduled_date).days
                return max(0, delay)  # Return 0 if completed early
            
            return 0
        except Exception as e:
            print(f"Error calculating delay days: {e}")
            return 0
    
    def get_template(self, template_name: str):
        """Cache loaded templates"""
        if template_name not in self._template_cache:
            self._template_cache[template_name] = self.jinja_env.get_template(template_name)
        return self._template_cache[template_name]