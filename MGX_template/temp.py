"""
OCR processing module with TesseractOCR and PaddleOCR integration
"""
import cv2
import numpy as np
from PIL import Image
import pytesseract
from paddleocr import PaddleOCR
import PyPDF2
import io
from typing import Dict, List, Tuple, Optional, Union
import re
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


class OCRProcessor:
    """Dual OCR engine processor with TesseractOCR and PaddleOCR"""

    def __init__(self):
        self.tesseract_available = self._check_tesseract()
        self.paddle_ocr = self._init_paddle_ocr()

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            exception_handler.logger.warning(f"Tesseract not available: {e}")
            return False

    def _init_paddle_ocr(self) -> Optional[PaddleOCR]:
        """Initialize PaddleOCR engine"""
        try:
            return PaddleOCR(
                use_angle_cls=ocr_config.paddle_use_angle_cls,
                use_gpu=ocr_config.paddle_use_gpu,
                lang='en'
            )
        except Exception as e:
            exception_handler.logger.warning(f"PaddleOCR initialization failed: {e}")
            return None

    def process_file(self, file_content: bytes, filename: str) -> List[OCRResult]:
        """Process uploaded file and extract text using both OCR engines"""
        try:
            # Convert file to images
            images = self._file_to_images(file_content, filename)

            all_results = []
            for i, image in enumerate(images):
                page_results = []

                # Process with Tesseract if available
                if self.tesseract_available:
                    tesseract_result = self._process_with_tesseract(image)
                    if tesseract_result:
                        page_results.append(tesseract_result)

                # Process with PaddleOCR if available
                if self.paddle_ocr:
                    paddle_result = self._process_with_paddle(image)
                    if paddle_result:
                        page_results.append(paddle_result)

                # Combine results for this page
                if page_results:
                    combined_result = self._combine_results(page_results, i)
                    all_results.append(combined_result)

            return all_results

        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_2,
                e,
                context={'show_manual_entry': True}
            )
            return []

    def _file_to_images(self, file_content: bytes, filename: str) -> List[np.ndarray]:
        """Convert file content to list of images"""
        file_ext = filename.lower().split('.')[-1]

        if file_ext == 'pdf':
            return self._pdf_to_images(file_content)
        else:
            # Handle image files
            image = Image.open(io.BytesIO(file_content))
            image_array = np.array(image)
            if len(image_array.shape) == 3 and image_array.shape[2] == 4:
                # Convert RGBA to RGB
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
            return [image_array]

    def _pdf_to_images(self, pdf_content: bytes) -> List[np.ndarray]:
        """Convert PDF to list of images (simplified - would need pdf2image for production)"""
        # For MVP, we'll return empty list for PDFs and suggest image upload
        exception_handler.logger.info("PDF processing requires additional setup. Please convert PDF to images.")
        return []

    def _process_with_tesseract(self, image: np.ndarray) -> Optional[OCRResult]:
        """Process image with TesseractOCR"""
        try:
            # Preprocess image
            processed_image = self._preprocess_image(image)

            # Extract text and confidence
            text = pytesseract.image_to_string(processed_image, config=ocr_config.tesseract_config)

            # Get confidence scores
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100.0,  # Convert to 0-1 scale
                engine="Tesseract"
            )

        except Exception as e:
            exception_handler.logger.warning(f"Tesseract processing failed: {e}")
            return None

    def _process_with_paddle(self, image: np.ndarray) -> Optional[OCRResult]:
        """Process image with PaddleOCR"""
        try:
            results = self.paddle_ocr.ocr(image, cls=True)

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
                engine="PaddleOCR"
            )

        except Exception as e:
            exception_handler.logger.warning(f"PaddleOCR processing failed: {e}")
            return None

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
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

    def _combine_results(self, results: List[OCRResult], page_num: int) -> OCRResult:
        """Combine results from multiple OCR engines"""
        if len(results) == 1:
            return results[0]

        # Choose result with higher confidence
        best_result = max(results, key=lambda r: r.confidence)

        # Combine texts if confidences are similar
        if len(results) == 2:
            conf_diff = abs(results[0].confidence - results[1].confidence)
            if conf_diff < 0.1:  # Similar confidence, combine texts
                combined_text = f"{results[0].text}\n---\n{results[1].text}"
                avg_confidence = sum(r.confidence for r in results) / len(results)
                return OCRResult(
                    text=combined_text,
                    confidence=avg_confidence,
                    engine="Combined"
                )

        return best_result

    def extract_structured_data(self, ocr_results: List[OCRResult]) -> Dict:
        """Extract structured data from OCR text"""
        structured_data = {
            'name': '',
            'date': '',
            'diet_content': [],
            'training_load': '',
            'sleep_data': '',
            'raw_text': '',
            'confidence_score': 0.0
        }

        all_text = ""
        total_confidence = 0.0

        for result in ocr_results:
            all_text += result.text + "\n"
            total_confidence += result.confidence

        structured_data['raw_text'] = all_text
        structured_data['confidence_score'] = total_confidence / len(ocr_results) if ocr_results else 0.0

        # Extract specific fields using regex patterns
        structured_data.update(self._extract_fields(all_text))

        return structured_data

    def _extract_fields(self, text: str) -> Dict:
        """Extract specific fields from text using regex patterns"""
        fields = {}

        # Extract name (look for "Name:" or similar patterns)
        name_pattern = r'(?:name|姓名)[:：]\s*([^\n]+)'
        name_match = re.search(name_pattern, text, re.IGNORECASE)
        fields['name'] = name_match.group(1).strip() if name_match else ''

        # Extract date patterns
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        date_match = re.search(date_pattern, text)
        fields['date'] = date_match.group(1) if date_match else ''

        # Extract training load (look for numbers with units)
        training_pattern = r'(?:training|训练|负荷)[:：]?\s*([^\n]+)'
        training_match = re.search(training_pattern, text, re.IGNORECASE)
        fields['training_load'] = training_match.group(1).strip() if training_match else ''

        # Extract sleep data
        sleep_pattern = r'(?:sleep|睡眠)[:：]?\s*([^\n]+)'
        sleep_match = re.search(sleep_pattern, text, re.IGNORECASE)
        fields['sleep_data'] = sleep_match.group(1).strip() if sleep_match else ''

        # Extract diet content (look for food items)
        diet_lines = []
        for line in text.split('\n'):
            if any(keyword in line.lower() for keyword in
                   ['food', 'meal', 'breakfast', 'lunch', 'dinner', '早餐', '午餐', '晚餐']):
                diet_lines.append(line.strip())
        fields['diet_content'] = diet_lines

        return fields


# Global OCR processor instance
ocr_processor = OCRProcessor()