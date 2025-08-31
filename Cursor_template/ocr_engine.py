"""
OCR引擎模块 - 集成Tesseract和PaddleOCR
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging
import re
from datetime import datetime, date, time
import json

# 导入配置
from config import ocr_config, DATA_SCHEMAS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCREngine:
    """OCR引擎类 - 支持Tesseract和PaddleOCR"""
    
    def __init__(self):
        """初始化OCR引擎"""
        self.tesseract_available = self._check_tesseract()
        self.paddle_available = self._check_paddle()
        
        if not self.tesseract_available and not self.paddle_available:
            raise RuntimeError("No OCR engine available. Please install Tesseract or PaddleOCR.")
        
        logger.info(f"OCR Engine initialized - Tesseract: {self.tesseract_available}, PaddleOCR: {self.paddle_available}")
    
    def _check_tesseract(self) -> bool:
        """检查Tesseract是否可用"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            return False
    
    def _check_paddle(self) -> bool:
        """检查PaddleOCR是否可用"""
        try:
            from paddleocr import PaddleOCR
            return True
        except ImportError:
            logger.warning("PaddleOCR not available")
            return False
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 去噪
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 自适应阈值处理
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # 形态学操作
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def extract_text_tesseract(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """使用Tesseract提取文本"""
        try:
            # 预处理图像
            processed_image = self.preprocess_image(image)
            
            # 配置Tesseract
            custom_config = f'--oem 3 --psm 6 -l {ocr_config.tesseract_lang}'
            
            # 提取文本和位置信息
            data = pytesseract.image_to_data(
                processed_image, 
                config=custom_config, 
                output_type=pytesseract.Output.DICT
            )
            
            results = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # 过滤低置信度结果
                    result = {
                        'text': data['text'][i].strip(),
                        'confidence': float(data['conf'][i]) / 100.0,
                        'bbox': (
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        ),
                        'engine': 'tesseract'
                    }
                    if result['text']:
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return []
    
    def extract_text_paddle(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """使用PaddleOCR提取文本"""
        try:
            from paddleocr import PaddleOCR
            
            # 初始化PaddleOCR
            ocr = PaddleOCR(
                use_angle_cls=ocr_config.paddle_use_angle_cls,
                det_db_thresh=ocr_config.paddle_det_db_thresh,
                det_db_box_thresh=ocr_config.paddle_det_db_box_thresh,
                use_gpu=ocr_config.paddle_use_gpu,
                lang='ch'
            )
            
            # 执行OCR
            results = ocr.ocr(image, cls=True)
            
            extracted_results = []
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) >= 2:
                        bbox, (text, confidence) = line
                        if confidence > ocr_config.confidence_threshold:
                            result = {
                                'text': text.strip(),
                                'confidence': float(confidence),
                                'bbox': bbox,
                                'engine': 'paddle'
                            }
                            if result['text']:
                                extracted_results.append(result)
            
            return extracted_results
            
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return []
    
    def extract_text_hybrid(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """混合OCR策略"""
        results = []
        
        # 主要OCR引擎
        if ocr_config.primary_ocr == "paddle" and self.paddle_available:
            results.extend(self.extract_text_paddle(image))
        elif ocr_config.primary_ocr == "tesseract" and self.tesseract_available:
            results.extend(self.extract_text_tesseract(image))
        
        # 如果主要引擎结果不足，使用备用引擎
        if len(results) < 5 and ocr_config.fallback_ocr != ocr_config.primary_ocr:
            if ocr_config.fallback_ocr == "paddle" and self.paddle_available:
                fallback_results = self.extract_text_paddle(image)
            elif ocr_config.fallback_ocr == "tesseract" and self.tesseract_available:
                fallback_results = self.extract_text_tesseract(image)
            else:
                fallback_results = []
            
            # 合并结果，避免重复
            existing_texts = {r['text'] for r in results}
            for result in fallback_results:
                if result['text'] not in existing_texts:
                    results.append(result)
                    existing_texts.add(result['text'])
        
        return results
    
    def extract_text(self, image: np.ndarray, engine: str = "hybrid") -> List[Dict[str, Any]]:
        """提取文本的主接口"""
        if engine == "tesseract":
            return self.extract_text_tesseract(image)
        elif engine == "paddle":
            return self.extract_text_paddle(image)
        elif engine == "hybrid":
            return self.extract_text_hybrid(image)
        else:
            raise ValueError(f"Unsupported OCR engine: {engine}")

class DataExtractor:
    """数据提取器 - 从OCR结果中提取结构化数据"""
    
    def __init__(self):
        """初始化数据提取器"""
        self.date_patterns = [
            r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            r'(\d{1,2})[-/月](\d{1,2})[日]?',
        ]
        
        self.time_patterns = [
            r'(\d{1,2}):(\d{2})(?::(\d{2}))?',
            r'(\d{1,2})时(\d{2})分',
        ]
        
        self.number_patterns = [
            r'(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(kg|g|ml|l|cal|kcal)',
        ]
    
    def extract_date(self, text: str) -> Optional[date]:
        """提取日期"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        if len(year) == 2:
                            year = f"20{year}"
                        return date(int(year), int(month), int(day))
                    elif len(match.groups()) == 2:
                        month, day = match.groups()
                        # 假设当前年份
                        current_year = datetime.now().year
                        return date(current_year, int(month), int(day))
                except ValueError:
                    continue
        return None
    
    def extract_time(self, text: str) -> Optional[time]:
        """提取时间"""
        for pattern in self.time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if ':' in text:
                        hour, minute = int(match.group(1)), int(match.group(2))
                        second = int(match.group(3)) if match.group(3) else 0
                        return time(hour, minute, second)
                    else:
                        hour, minute = int(match.group(1)), int(match.group(2))
                        return time(hour, minute)
                except ValueError:
                    continue
        return None
    
    def extract_number(self, text: str) -> Optional[float]:
        """提取数字"""
        for pattern in self.number_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def extract_structured_data(self, ocr_results: List[Dict[str, Any]], schema_name: str) -> List[Dict[str, Any]]:
        """提取结构化数据"""
        if schema_name not in DATA_SCHEMAS:
            raise ValueError(f"Unknown schema: {schema_name}")
        
        schema = DATA_SCHEMAS[schema_name]
        extracted_data = []
        
        # 按行分组OCR结果
        lines = self._group_by_lines(ocr_results)
        
        for line in lines:
            data_row = {}
            line_text = ' '.join([r['text'] for r in line])
            
            # 提取每个字段
            for field in schema.fields:
                value = None
                
                if field.type == "date":
                    value = self.extract_date(line_text)
                elif field.type == "time":
                    value = self.extract_time(line_text)
                elif field.type == "number":
                    value = self.extract_number(line_text)
                elif field.type == "text":
                    # 对于文本字段，尝试从OCR结果中匹配
                    value = self._extract_text_field(line, field.name)
                
                if value is not None or field.required:
                    data_row[field.name] = value
            
            # 如果至少有一个有效字段，添加到结果中
            if any(v is not None for v in data_row.values()):
                extracted_data.append(data_row)
        
        return extracted_data
    
    def _group_by_lines(self, ocr_results: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """按行分组OCR结果"""
        if not ocr_results:
            return []
        
        # 按y坐标排序
        sorted_results = sorted(ocr_results, key=lambda x: x['bbox'][1])
        
        lines = []
        current_line = []
        last_y = None
        y_threshold = 20  # 同一行的y坐标差异阈值
        
        for result in sorted_results:
            y = result['bbox'][1]
            
            if last_y is None or abs(y - last_y) <= y_threshold:
                current_line.append(result)
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [result]
            
            last_y = y
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _extract_text_field(self, line_results: List[Dict[str, Any]], field_name: str) -> Optional[str]:
        """提取文本字段"""
        # 简单的关键词匹配
        field_keywords = {
            'food_name': ['食物', '食品', '菜', '饭', '餐'],
            'training_type': ['训练', '运动', '跑步', '骑行', '游泳'],
            'notes': ['备注', '说明', '注释'],
        }
        
        keywords = field_keywords.get(field_name, [])
        
        for result in line_results:
            text = result['text'].lower()
            for keyword in keywords:
                if keyword in text:
                    return result['text']
        
        # 如果没有匹配到关键词，返回第一个非空文本
        for result in line_results:
            if result['text'].strip():
                return result['text']
        
        return None

class OCRProcessor:
    """OCR处理器 - 完整的OCR处理流程"""
    
    def __init__(self):
        """初始化OCR处理器"""
        self.ocr_engine = OCREngine()
        self.data_extractor = DataExtractor()
    
    def process_image(self, image_path: str, schema_name: str, engine: str = "hybrid") -> Dict[str, Any]:
        """处理图像并提取结构化数据"""
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot read image: {image_path}")
            
            # OCR文本提取
            ocr_results = self.ocr_engine.extract_text(image, engine)
            
            # 提取结构化数据
            structured_data = self.data_extractor.extract_structured_data(ocr_results, schema_name)
            
            # 计算准确率（如果有ground truth）
            accuracy = self._calculate_accuracy(ocr_results)
            
            return {
                'success': True,
                'ocr_results': ocr_results,
                'structured_data': structured_data,
                'accuracy': accuracy,
                'engine_used': engine,
                'schema': schema_name,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_accuracy(self, ocr_results: List[Dict[str, Any]]) -> float:
        """计算OCR准确率"""
        if not ocr_results:
            return 0.0
        
        total_confidence = sum(r['confidence'] for r in ocr_results)
        return total_confidence / len(ocr_results)
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """保存OCR结果"""
        try:
            # 保存结构化数据为CSV
            if results['success'] and results['structured_data']:
                df = pd.DataFrame(results['structured_data'])
                csv_path = output_path.replace('.json', '.csv')
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # 保存完整结果为JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Results saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise
