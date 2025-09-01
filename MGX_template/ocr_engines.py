"""
Independent OCR engine implementations for hot-swapping and ablation studies
"""
import cv2
import numpy as np
from PIL import Image
import pytesseract
from paddleocr import PaddleOCR
from typing import Dict, List, Tuple, Optional, Union
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from config import ocr_config
from exception_handler import exception_handler, ExceptionLevel


@dataclass
class OCRResult:
    """OCR processing result container"""
    text: str
    confidence: float
    engine: str
    bounding_boxes: List[Tuple[int, int, int, int]] = None
    structured_data: Dict = None


class BaseOCREngine(ABC):
    """Abstract base class for OCR engines"""
    
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        self.is_available = False
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize the OCR engine"""
        pass
    
    @abstractmethod
    def process_image(self, image: np.ndarray) -> Optional[OCRResult]:
        """Process image and return OCR result"""
        pass
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        if not ocr_config.enable_preprocessing:
            return image
            
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)

        # Apply threshold
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh


class TesseractEngine(BaseOCREngine):
    """TesseractOCR engine implementation"""
    
    def __init__(self):
        super().__init__("Tesseract")
    
    def _initialize(self):
        """Initialize Tesseract engine"""
        try:
            pytesseract.get_tesseract_version()
            self.is_available = True
            exception_handler.logger.info("Tesseract engine initialized successfully")
        except Exception as e:
            self.is_available = False
            exception_handler.logger.warning(f"Tesseract initialization failed: {e}")
    
    def process_image(self, image: np.ndarray) -> Optional[OCRResult]:
        """Process image with TesseractOCR"""
        if not self.is_available:
            return None
            
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Extract text and confidence
            text = pytesseract.image_to_string(processed_image, config=ocr_config.tesseract_config)

            # Get confidence scores
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100.0,  # Convert to 0-1 scale
                engine=self.engine_name
            )

        except Exception as e:
            exception_handler.logger.warning(f"Tesseract processing failed: {e}")
            return None


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR engine implementation"""
    
    def __init__(self):
        super().__init__("PaddleOCR")
        self.paddle_ocr = None
    
    def _initialize(self):
        """Initialize PaddleOCR engine"""
        try:
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=ocr_config.paddle_use_angle_cls,
                lang='en',
                device='gpu' if ocr_config.paddle_use_gpu else 'cpu'
            )
            self.is_available = True
            exception_handler.logger.info("PaddleOCR engine initialized successfully")
        except Exception as e:
            self.is_available = False
            exception_handler.logger.warning(f"PaddleOCR initialization failed: {e}")
    
    def process_image(self, image: np.ndarray) -> Optional[OCRResult]:
        """Process image with PaddleOCR"""
        if not self.is_available or not self.paddle_ocr:
            return None
            
        try:
            results = self.paddle_ocr.ocr(image)

            # Robust validation of PaddleOCR results
            if not results:
                exception_handler.logger.warning("PaddleOCR returned None results")
                return None

            # Handle case where results is a list but empty or contains None
            if not isinstance(results, list) or len(results) == 0:
                exception_handler.logger.warning("PaddleOCR returned empty or invalid results")
                return None

            # Get the first page results
            page_results = results[0]
            if not page_results:
                exception_handler.logger.warning("PaddleOCR returned None for page results")
                return None

            # Extract text and confidence with robust validation
            texts = []
            confidences = []

            for line in page_results:
                # Validate line structure
                if not line or len(line) < 2:
                    continue

                # line should be [bbox, (text, confidence)]
                text_info = line[1] if len(line) > 1 else None
                if not text_info or len(text_info) < 2:
                    continue

                # Extract text and confidence safely
                try:
                    text = str(text_info[0]) if text_info[0] is not None else ""
                    confidence = float(text_info[1]) if text_info[1] is not None else 0.0

                    if text.strip():  # Only add non-empty text
                        texts.append(text.strip())
                        confidences.append(confidence)

                except (IndexError, ValueError, TypeError) as e:
                    exception_handler.logger.warning(f"Error parsing PaddleOCR line: {e}")
                    continue

            # Check if we extracted any valid text
            if not texts:
                exception_handler.logger.warning("No valid text extracted from PaddleOCR results")
                return None

            combined_text = '\n'.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return OCRResult(
                text=combined_text,
                confidence=avg_confidence,
                engine=self.engine_name
            )

        except Exception as e:
            exception_handler.logger.warning(f"PaddleOCR processing failed: {e}")
            return None


class OCREngineManager:
    """Manager for OCR engines with hot-swapping capability"""
    
    def __init__(self):
        self.engines = {}
        self.active_engines = []
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize all available OCR engines"""
        # Initialize Tesseract
        if ocr_config.enable_tesseract:
            tesseract_engine = TesseractEngine()
            self.engines["tesseract"] = tesseract_engine
            if tesseract_engine.is_available:
                self.active_engines.append("tesseract")
        
        # Initialize PaddleOCR
        if ocr_config.enable_paddle:
            paddle_engine = PaddleOCREngine()
            self.engines["paddle"] = paddle_engine
            if paddle_engine.is_available:
                self.active_engines.append("paddle")
        
        exception_handler.logger.info(f"OCR Engine Manager initialized with {len(self.active_engines)} active engines: {self.active_engines}")
    
    def get_available_engines(self) -> List[str]:
        """Get list of all available engines"""
        return [name for name, engine in self.engines.items() if engine.is_available]
    
    def get_active_engines(self) -> List[str]:
        """Get list of currently active engines"""
        return self.active_engines.copy()
    
    def set_active_engines(self, engine_names: List[str]):
        """Set which engines are active for processing"""
        available_engines = self.get_available_engines()
        self.active_engines = [name for name in engine_names if name in available_engines]
        exception_handler.logger.info(f"Active engines set to: {self.active_engines}")
    
    def enable_engine(self, engine_name: str) -> bool:
        """Enable a specific engine"""
        if engine_name in self.engines and self.engines[engine_name].is_available:
            if engine_name not in self.active_engines:
                self.active_engines.append(engine_name)
            return True
        return False
    
    def disable_engine(self, engine_name: str) -> bool:
        """Disable a specific engine"""
        if engine_name in self.active_engines:
            self.active_engines.remove(engine_name)
            return True
        return False
    
    def process_image(self, image: np.ndarray) -> List[OCRResult]:
        """Process image with all active engines"""
        results = []
        
        for engine_name in self.active_engines:
            if engine_name in self.engines:
                engine = self.engines[engine_name]
                result = engine.process_image(image)
                if result:
                    results.append(result)
        
        return results
    
    def get_engine_status(self) -> Dict[str, Dict]:
        """Get status of all engines"""
        status = {}
        for name, engine in self.engines.items():
            status[name] = {
                'available': engine.is_available,
                'active': name in self.active_engines,
                'engine_name': engine.engine_name
            }
        return status
    
    def reset_to_default(self):
        """Reset to default engine configuration"""
        self.active_engines = []
        for name, engine in self.engines.items():
            if engine.is_available:
                self.active_engines.append(name)
        exception_handler.logger.info(f"Reset to default engines: {self.active_engines}")


# Global engine manager instance
engine_manager = OCREngineManager()
