#!/usr/bin/env python3
"""
Progress Tracking and User Interface Module
Provides real-time progress updates and user-friendly feedback
"""

import os
import sys
import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

try:
    import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


class ProgressStage(Enum):
    """Processing stages"""
    INITIALIZATION = "initialization"
    IMAGE_DISCOVERY = "image_discovery"
    OCR_PROCESSING = "ocr_processing"
    DATA_VALIDATION = "data_validation"
    EXCEL_GENERATION = "excel_generation"
    COMPLETION = "completion"


@dataclass
class ProgressUpdate:
    """Progress update information"""
    stage: ProgressStage
    current: int
    total: int
    message: str
    details: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100


class ProgressTracker:
    """Main progress tracking class"""
    
    def __init__(self, enable_ui: bool = True):
        self.enable_ui = enable_ui
        self.callbacks = []
        self.current_stage = None
        self.start_time = None
        self.stage_times = {}
        
        # Progress data
        self.progress_data = {
            'total_images': 0,
            'processed_images': 0,
            'total_items': 0,
            'valid_items': 0,
            'errors': [],
            'warnings': [],
            'ocr_stats': {}
        }
        
        # Initialize UI components
        self.tqdm_bar = None
        self.streamlit_placeholder = None
    
    def add_callback(self, callback: Callable[[ProgressUpdate], None]):
        """Add progress callback function"""
        self.callbacks.append(callback)
    
    def start_stage(self, stage: ProgressStage, total: int, message: str):
        """Start a new processing stage"""
        self.current_stage = stage
        self.stage_start_time = time.time()
        
        # Initialize progress bar
        if self.enable_ui:
            self._init_progress_bar(total, message)
        
        # Send initial update
        update = ProgressUpdate(stage, 0, total, message)
        self._notify_callbacks(update)
    
    def update_progress(self, current: int, message: Optional[str] = None, details: Optional[str] = None):
        """Update current progress"""
        if self.current_stage is None:
            return
        
        stage = self.current_stage
        total = getattr(self, f'{stage.value}_total', 100)
        
        if message is None:
            message = f"Processing {current}/{total}..."
        
        update = ProgressUpdate(stage, current, total, message, details)
        self._notify_callbacks(update)
        
        # Update UI
        if self.enable_ui:
            self._update_progress_bar(current, message)
    
    def complete_stage(self, message: str):
        """Complete current stage"""
        if self.current_stage is None:
            return
        
        stage = self.current_stage
        end_time = time.time()
        
        if hasattr(self, 'stage_start_time'):
            duration = end_time - self.stage_start_time
            self.stage_times[stage.value] = duration
        
        # Send completion update
        total = getattr(self, f'{stage.value}_total', 100)
        update = ProgressUpdate(stage, total, total, message)
        self._notify_callbacks(update)
        
        # Close progress bar
        if self.enable_ui:
            self._close_progress_bar()
        
        self.current_stage = None
    
    def add_error(self, error: str):
        """Add error message"""
        self.progress_data['errors'].append({
            'message': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_warning(self, warning: str):
        """Add warning message"""
        self.progress_data['warnings'].append({
            'message': warning,
            'timestamp': datetime.now().isoformat()
        })
    
    def update_data(self, **kwargs):
        """Update progress data"""
        for key, value in kwargs.items():
            if key in self.progress_data:
                self.progress_data[key] = value
    
    def _notify_callbacks(self, update: ProgressUpdate):
        """Notify all callback functions"""
        for callback in self.callbacks:
            try:
                callback(update)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def _init_progress_bar(self, total: int, message: str):
        """Initialize progress bar"""
        if TQDM_AVAILABLE and not STREAMLIT_AVAILABLE:
            self.tqdm_bar = tqdm.tqdm(total=total, desc=message)
        elif STREAMLIT_AVAILABLE:
            self.streamlit_placeholder = st.empty()
            st.info(message)
    
    def _update_progress_bar(self, current: int, message: str):
        """Update progress bar"""
        if self.tqdm_bar is not None:
            self.tqdm_bar.update(1)
            self.tqdm_bar.set_description(message)
        elif self.streamlit_placeholder is not None:
            progress = current / getattr(self, f'{self.current_stage.value}_total', 100)
            self.streamlit_placeholder.progress(progress)
            st.info(message)
    
    def _close_progress_bar(self):
        """Close progress bar"""
        if self.tqdm_bar is not None:
            self.tqdm_bar.close()
            self.tqdm_bar = None
        elif self.streamlit_placeholder is not None:
            self.streamlit_placeholder.empty()
            self.streamlit_placeholder = None


class ConsoleProgressDisplay:
    """Console-based progress display"""
    
    def __init__(self):
        self.last_update = None
    
    def __call__(self, update: ProgressUpdate):
        """Display progress update in console"""
        current_time = update.timestamp.strftime("%H:%M:%S")
        percentage = update.percentage
        
        # Create progress bar
        bar_length = 40
        filled_length = int(bar_length * percentage / 100)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        # Format message
        message = f"[{current_time}] {update.stage.value.upper()}: {bar} {percentage:.1f}% - {update.message}"
        
        if update.details:
            message += f"\n    Details: {update.details}"
        
        # Clear previous line and print new
        if self.last_update:
            print('\r' + ' ' * len(self.last_update), end='\r')
        
        print(message)
        self.last_update = message


class StreamlitProgressDisplay:
    """Streamlit-based progress display"""
    
    def __init__(self):
        self.progress_container = st.container()
        self.status_container = st.container()
    
    def __call__(self, update: ProgressUpdate):
        """Display progress update in Streamlit"""
        with self.progress_container:
            st.progress(update.percentage / 100)
            st.info(f"{update.stage.value.title()}: {update.message}")
        
        if update.details:
            with self.status_container:
                st.text(update.details)


class UserInterface:
    """Main user interface coordinator"""
    
    def __init__(self, interface_type: str = "console"):
        self.interface_type = interface_type
        self.progress_tracker = ProgressTracker(enable_ui=True)
        
        # Initialize display based on type
        if interface_type == "console":
            display = ConsoleProgressDisplay()
        elif interface_type == "streamlit" and STREAMLIT_AVAILABLE:
            display = StreamlitProgressDisplay()
        else:
            display = ConsoleProgressDisplay()  # Fallback
        
        self.progress_tracker.add_callback(display)
        
        # Additional callbacks for logging
        self.progress_tracker.add_callback(self._log_progress)
    
    def _log_progress(self, update: ProgressUpdate):
        """Log progress updates"""
        log_message = f"{update.stage.value}: {update.current}/{update.total} - {update.message}"
        
        # Log to file if available
        try:
            log_file = f"logs/progress_{datetime.now().strftime('%Y%m%d')}.log"
            os.makedirs("logs", exist_ok=True)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{update.timestamp.isoformat()} - {log_message}\n")
        except Exception:
            pass  # Silently ignore logging errors
    
    def start_processing(self, total_images: int):
        """Start processing with total image count"""
        self.progress_tracker.progress_data['total_images'] = total_images
        self.progress_tracker.start_stage(
            ProgressStage.IMAGE_DISCOVERY, 
            total_images, 
            "Discovering images..."
        )
    
    def image_discovered(self, image_path: str):
        """Update when an image is discovered"""
        current = self.progress_tracker.progress_data.get('processed_images', 0) + 1
        self.progress_tracker.progress_data['processed_images'] = current
        self.progress_tracker.update_progress(
            current, 
            f"Found image: {os.path.basename(image_path)}"
        )
    
    def start_ocr_processing(self, total_items: int):
        """Start OCR processing stage"""
        self.progress_tracker.start_stage(
            ProgressStage.OCR_PROCESSING,
            total_items,
            "Extracting text with OCR..."
        )
    
    def ocr_item_processed(self, image_path: str, items_found: int):
        """Update when OCR processes an image"""
        current = self.progress_tracker.progress_data.get('processed_images', 0) + 1
        self.progress_tracker.progress_data['processed_images'] = current
        self.progress_tracker.progress_data['total_items'] += items_found
        
        self.progress_tracker.update_progress(
            current,
            f"Processed {os.path.basename(image_path)} - Found {items_found} items"
        )
    
    def start_validation(self, total_items: int):
        """Start validation stage"""
        self.progress_tracker.start_stage(
            ProgressStage.DATA_VALIDATION,
            total_items,
            "Validating extracted data..."
        )
    
    def validation_item_processed(self, is_valid: bool, bsr_code: str):
        """Update when validation processes an item"""
        current = self.progress_tracker.progress_data.get('total_items', 0) + 1
        
        if is_valid:
            self.progress_tracker.progress_data['valid_items'] += 1
            message = f"Validated {bsr_code} ✓"
        else:
            message = f"Validation failed for {bsr_code} ✗"
        
        self.progress_tracker.update_progress(current, message)
    
    def start_excel_generation(self):
        """Start Excel generation stage"""
        self.progress_tracker.start_stage(
            ProgressStage.EXCEL_GENERATION,
            1,
            "Generating Excel file..."
        )
    
    def excel_generated(self, file_path: str):
        """Update when Excel is generated"""
        self.progress_tracker.complete_stage(f"Excel generated: {file_path}")
    
    def processing_complete(self, success: bool, message: str):
        """Mark processing as complete"""
        status = "SUCCESS" if success else "FAILED"
        self.progress_tracker.start_stage(ProgressStage.COMPLETION, 1, f"Processing {status}")
        self.progress_tracker.complete_stage(message)
    
    def add_error(self, error: str):
        """Add error message"""
        self.progress_tracker.add_error(error)
    
    def add_warning(self, warning: str):
        """Add warning message"""
        self.progress_tracker.add_warning(warning)
    
    def get_progress_data(self) -> Dict[str, Any]:
        """Get current progress data"""
        return self.progress_tracker.progress_data.copy()


def create_progress_interface(interface_type: str = "console") -> UserInterface:
    """Factory function to create progress interface"""
    return UserInterface(interface_type)


if __name__ == "__main__":
    # Test the progress tracker
    ui = create_progress_interface("console")
    
    # Simulate processing
    ui.start_processing(5)
    
    for i in range(5):
        time.sleep(0.5)
        ui.image_discovered(f"image_{i+1}.jpg")
    
    ui.start_ocr_processing(5)
    
    for i in range(5):
        time.sleep(0.3)
        ui.ocr_item_processed(f"image_{i+1}.jpg", i+1)
    
    ui.start_validation(15)
    
    for i in range(15):
        time.sleep(0.1)
        ui.validation_item_processed(i % 3 != 0, f"BSR_{i+1}")
    
    ui.start_excel_generation()
    time.sleep(0.5)
    ui.excel_generated("OUTPUT/test.xlsx")
    
    ui.processing_complete(True, "Processing completed successfully")
