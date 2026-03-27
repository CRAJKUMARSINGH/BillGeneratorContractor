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
    
    def _calculate_liquidated_damages(self, work_order_amount: float, actual_progress: float, delay_days: int) -> int:
        """
        Calculate liquidated damages based on PWD formula with quarterly distribution
        
        Formula: LD = Penalty Rate × Unexecuted Work
        Where: 
            - Work is distributed quarterly: 12.5%, 25%, 25%, 37.5%
            - Required Progress calculated based on elapsed time and quarterly distribution
            - Unexecuted Work = Required Progress - Actual Progress
            - Penalty Rate varies by quarter (progressive rates)
        
        Args:
            work_order_amount: Total work order amount in rupees
            actual_progress: Actual amount of work completed in rupees
            delay_days: Number of days delayed (not used in quarterly method, kept for compatibility)
            
        Returns:
            Liquidated damages amount in whole rupees (rounded)
        """
        try:
            # Get project dates from title_data
            scheduled_str = self.title_data.get('St. date of completion :', '')
            actual_str = self.title_data.get('Date of actual completion of work :', '')
            start_str = self.title_data.get('Date of written order to commence work :', 
                                           self.title_data.get('St. date of Start :', ''))
            
            if not scheduled_str or not actual_str or not start_str:
                return 0
            
            # Parse dates
            from datetime import datetime
            date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
            
            start_date = None
            scheduled_date = None
            actual_date = None
            
            for fmt in date_formats:
                try:
                    if not start_date:
                        start_date = datetime.strptime(str(start_str).strip(), fmt)
                    if not scheduled_date:
                        scheduled_date = datetime.strptime(str(scheduled_str).strip(), fmt)
                    if not actual_date:
                        actual_date = datetime.strptime(str(actual_str).strip(), fmt)
                    if start_date and scheduled_date and actual_date:
                        break
                except:
                    continue
            
            if not (start_date and scheduled_date and actual_date):
                return 0
            
            # Calculate total project duration and elapsed days
            total_duration = (scheduled_date - start_date).days
            elapsed_days = (actual_date - start_date).days
            
            if total_duration <= 0 or elapsed_days <= total_duration:
                return 0  # No delay
            
            # Define quarterly distribution (PWD formula)
            q1_percent = 0.125  # 12.5%
            q2_percent = 0.25   # 25%
            q3_percent = 0.25   # 25%
            q4_percent = 0.375  # 37.5%
            
            # Calculate quarter boundaries
            q1_end = int(total_duration * 0.25)
            q2_end = int(total_duration * 0.50)
            q3_end = int(total_duration * 0.75)
            q4_end = total_duration
            
            # Calculate quarter lengths
            q1_length = q1_end
            q2_length = q2_end - q1_end
            q3_length = q3_end - q2_end
            q4_length = q4_end - q3_end
            
            # Calculate work distribution
            q1_work = work_order_amount * q1_percent
            q2_work = work_order_amount * q2_percent
            q3_work = work_order_amount * q3_percent
            q4_work = work_order_amount * q4_percent
            
            # Calculate daily progress rates for each quarter
            q1_daily = q1_work / q1_length if q1_length > 0 else 0
            q2_daily = q2_work / q2_length if q2_length > 0 else 0
            q3_daily = q3_work / q3_length if q3_length > 0 else 0
            q4_daily = q4_work / q4_length if q4_length > 0 else 0
            
            # Calculate required progress based on elapsed days
            required_progress = 0
            
            if elapsed_days <= q1_end:
                # In Q1
                required_progress = elapsed_days * q1_daily
                penalty_rate = 0.025  # 2.5% for Q1
            elif elapsed_days <= q2_end:
                # In Q2
                days_in_q2 = elapsed_days - q1_end
                required_progress = q1_work + (days_in_q2 * q2_daily)
                penalty_rate = 0.05  # 5% for Q2
            elif elapsed_days <= q3_end:
                # In Q3
                days_in_q3 = elapsed_days - q2_end
                required_progress = q1_work + q2_work + (days_in_q3 * q3_daily)
                penalty_rate = 0.075  # 7.5% for Q3
            else:
                # In Q4 or beyond
                days_in_q4 = min(elapsed_days - q3_end, q4_length)
                required_progress = q1_work + q2_work + q3_work + (days_in_q4 * q4_daily)
                penalty_rate = 0.10  # 10% for Q4
            
            # Calculate unexecuted work
            unexecuted_work = max(0, required_progress - actual_progress)
            
            # Special case: If work is 100% complete but delayed
            # Presume entire delay occurred in Q4 (final quarter)
            # LD = (Q4 Daily Progress Rate × Delay Days) × Q4 Penalty Rate (10%)
            if unexecuted_work <= 0 and elapsed_days > total_duration:
                # Work is complete but delayed beyond scheduled completion
                delay_beyond_completion = elapsed_days - total_duration
                
                # Use Q4 daily rate and Q4 penalty rate (presume delay in Q4)
                unexecuted_work = q4_daily * delay_beyond_completion
                penalty_rate = 0.10  # Q4 penalty rate (10%)
            elif unexecuted_work <= 0:
                # Work complete and on time - no LD
                return 0
            
            # Calculate liquidated damages
            ld_amount = penalty_rate * unexecuted_work
            
            # Return as whole rupees (rounded)
            return int(round(ld_amount))
            
        except Exception as e:
            print(f"Error calculating liquidated damages: {e}")
            return 0
    
    def get_template(self, template_name: str):
        """Cache loaded templates"""
        if template_name not in self._template_cache:
            self._template_cache[template_name] = self.jinja_env.get_template(template_name)
        return self._template_cache[template_name]