"""
Configuration and settings management for OCR and visualization system
"""
import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class OCRConfig:
    """OCR engine configuration"""
    # Tesseract configuration
    tesseract_cmd: str = "tesseract"
    tesseract_config: str = "--oem 3 --psm 6"
    
    # PaddleOCR configuration
    paddle_use_angle_cls: bool = True
    paddle_use_gpu: bool = False
    
    # Engine activation settings (for ablation studies)
    enable_tesseract: bool = True
    enable_paddle: bool = True
    
    # Processing settings
    target_accuracy: float = 0.85
    enable_preprocessing: bool = True
    combine_results: bool = True
    
    # Ablation study settings
    ablation_mode: bool = False
    selected_engines: List[str] = None
    
    def __post_init__(self):
        if self.selected_engines is None:
            self.selected_engines = []
    
    def get_active_engines(self) -> List[str]:
        """Get list of currently active OCR engines"""
        active_engines = []
        if self.enable_tesseract:
            active_engines.append("tesseract")
        if self.enable_paddle:
            active_engines.append("paddle")
        return active_engines
    
    def set_ablation_engines(self, engines: List[str]):
        """Set engines for ablation study"""
        self.ablation_mode = True
        self.selected_engines = engines
        # Disable engines not in ablation study
        self.enable_tesseract = "tesseract" in engines
        self.enable_paddle = "paddle" in engines

@dataclass
class DataConfig:
    """Data processing configuration"""
    supported_formats: List[str] = None
    output_dir: str = "outputs"
    csv_encoding: str = "utf-8"
    json_indent: int = 2
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff']

@dataclass
class UIConfig:
    """UI and Material3 configuration"""
    primary_color: str = "#6750A4"
    secondary_color: str = "#625B71"
    surface_color: str = "#FFFBFE"
    error_color: str = "#BA1A1A"
    success_color: str = "#006E1C"
    warning_color: str = "#8C4A00"
    
    # Material3 typography
    display_large: str = "57px"
    display_medium: str = "45px"
    headline_large: str = "32px"
    headline_medium: str = "28px"
    title_large: str = "22px"
    body_large: str = "16px"
    body_medium: str = "14px"

# Global configuration instances
ocr_config = OCRConfig()
data_config = DataConfig()
ui_config = UIConfig()

# Create output directory if it doesn't exist
os.makedirs(data_config.output_dir, exist_ok=True)