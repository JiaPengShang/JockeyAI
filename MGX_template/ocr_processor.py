"""
OCR processing module with hot-swappable OCR engines for ablation studies
"""
import cv2
import numpy as np
from PIL import Image
import io
from typing import Dict, List, Tuple, Optional, Union
import re
from dataclasses import dataclass

from config import ocr_config
from exception_handler import exception_handler, ExceptionLevel
from ocr_engines import engine_manager, OCRResult


class OCRProcessor:
    """Hot-swappable OCR processor with ablation study support"""

    def __init__(self):
        self.engine_manager = engine_manager

    def process_file(self, file_content: bytes, filename: str) -> List[OCRResult]:
        """Process uploaded file and extract text using active OCR engines"""
        try:
            # Convert file to images
            images = self._file_to_images(file_content, filename)

            all_results = []
            for i, image in enumerate(images):
                page_results = []

                # Process with all active engines
                engine_results = self.engine_manager.process_image(image)
                if engine_results:
                    page_results.extend(engine_results)

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

    def _combine_results(self, results: List[OCRResult], page_num: int) -> OCRResult:
        """Combine results from multiple OCR engines"""
        if len(results) == 1:
            return results[0]

        if not ocr_config.combine_results:
            # Return the result with highest confidence
            return max(results, key=lambda r: r.confidence)

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
            'confidence_score': 0.0,
            'engines_used': []
        }
        
        all_text = ""
        total_confidence = 0.0
        engines_used = []
        
        for result in ocr_results:
            all_text += result.text + "\n"
            total_confidence += result.confidence
            engines_used.append(result.engine)
        
        structured_data['raw_text'] = all_text
        structured_data['confidence_score'] = total_confidence / len(ocr_results) if ocr_results else 0.0
        structured_data['engines_used'] = list(set(engines_used))  # Remove duplicates
        
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

    def get_engine_status(self) -> Dict[str, Dict]:
        """Get current engine status"""
        return self.engine_manager.get_engine_status()

    def set_active_engines(self, engine_names: List[str]):
        """Set which engines are active for processing"""
        self.engine_manager.set_active_engines(engine_names)

    def enable_engine(self, engine_name: str) -> bool:
        """Enable a specific engine"""
        return self.engine_manager.enable_engine(engine_name)

    def disable_engine(self, engine_name: str) -> bool:
        """Disable a specific engine"""
        return self.engine_manager.disable_engine(engine_name)

    def reset_engines(self):
        """Reset to default engine configuration"""
        self.engine_manager.reset_to_default()


# Global OCR processor instance
ocr_processor = OCRProcessor()