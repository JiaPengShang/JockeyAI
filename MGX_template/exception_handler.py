"""
3-level exception handling system for OCR and visualization pipeline
"""
import logging
import traceback
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import streamlit as st

class ExceptionLevel(Enum):
    """Exception severity levels"""
    LEVEL_1 = "File Upload Failure"
    LEVEL_2 = "OCR Processing Failure" 
    LEVEL_3 = "Visualization Generation Failure"

@dataclass
class ExceptionInfo:
    """Exception information container"""
    level: ExceptionLevel
    message: str
    details: str
    recovery_action: str
    timestamp: str

class ExceptionHandler:
    """Centralized exception handling with recovery mechanisms"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.exception_history = []
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('OCR_System')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def handle_exception(self, 
                        level: ExceptionLevel, 
                        exception: Exception, 
                        context: Optional[Dict[str, Any]] = None) -> ExceptionInfo:
        """Handle exceptions based on level with appropriate recovery"""
        
        import datetime
        
        exc_info = ExceptionInfo(
            level=level,
            message=str(exception),
            details=traceback.format_exc(),
            recovery_action=self._get_recovery_action(level),
            timestamp=datetime.datetime.now().isoformat()
        )
        
        self.exception_history.append(exc_info)
        self.logger.error(f"{level.value}: {exc_info.message}")
        
        # Display user-friendly error in Streamlit
        self._display_error_ui(exc_info, context)
        
        return exc_info
    
    def _get_recovery_action(self, level: ExceptionLevel) -> str:
        """Get recovery action based on exception level"""
        recovery_actions = {
            ExceptionLevel.LEVEL_1: "Please check file format and try uploading again. Supported formats: PDF, JPG, PNG, BMP, TIFF",
            ExceptionLevel.LEVEL_2: "OCR processing failed. Try with a clearer image or different file format. You can also try manual data entry.",
            ExceptionLevel.LEVEL_3: "Visualization generation failed. Check data format or try with different chart type. Raw data is still available for download."
        }
        return recovery_actions.get(level, "Please try again or contact support.")
    
    def _display_error_ui(self, exc_info: ExceptionInfo, context: Optional[Dict[str, Any]] = None):
        """Display user-friendly error message in Streamlit UI"""
        
        if exc_info.level == ExceptionLevel.LEVEL_1:
            st.error(f"📁 {exc_info.level.value}")
            st.warning(exc_info.recovery_action)
            
        elif exc_info.level == ExceptionLevel.LEVEL_2:
            st.error(f"🔍 {exc_info.level.value}")
            st.warning(exc_info.recovery_action)
            if context and context.get('show_manual_entry'):
                st.info("💡 You can manually enter data using the form below as an alternative.")
                
        elif exc_info.level == ExceptionLevel.LEVEL_3:
            st.error(f"📊 {exc_info.level.value}")
            st.warning(exc_info.recovery_action)
            if context and context.get('raw_data'):
                st.info("📋 Raw extracted data is available for download below.")
    
    def get_exception_summary(self) -> Dict[str, int]:
        """Get summary of exceptions by level"""
        summary = {level.value: 0 for level in ExceptionLevel}
        for exc in self.exception_history:
            summary[exc.level.value] += 1
        return summary
    
    def clear_history(self):
        """Clear exception history"""
        self.exception_history.clear()

# Global exception handler instance
exception_handler = ExceptionHandler()