import fitz  # PyMuPDF
import base64
import io
from PIL import Image
import numpy as np
from typing import List, Dict, Any
import json
from ocr_processor import OCRProcessor

class PDFProcessor:
    """PDF文件处理器，支持多页面PDF的OCR识别和食物数据提取"""
    
    def __init__(self):
        self.ocr = OCRProcessor()
        
    def extract_pages_from_pdf(self, pdf_file, fast_mode=False) -> List[Dict[str, Any]]:
        """从PDF文件中提取所有页面并转换为图像"""
        pages_data = []
        
        try:
            # 打开PDF文件
            pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
            total_pages = len(pdf_document)
            
            for page_num in range(total_pages):
                # 获取页面
                page = pdf_document.load_page(page_num)
                
                # 优化：根据页面大小和处理模式动态调整缩放因子
                page_rect = page.rect
                page_width = page_rect.width
                page_height = page_rect.height
                
                if fast_mode:
                    # 快速模式：使用较小的缩放因子
                    if page_width > 600 or page_height > 800:
                        scale_factor = 1.0  # 最小缩放
                    else:
                        scale_factor = 1.2  # 较小缩放
                else:
                    # 标准模式：根据页面大小调整
                    if page_width > 800 or page_height > 1000:
                        scale_factor = 1.5  # 降低缩放因子
                    else:
                        scale_factor = 2.0  # 保持原有缩放因子
                
                mat = fitz.Matrix(scale_factor, scale_factor)
                
                # 将页面渲染为图像
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为PIL图像
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                pages_data.append({
                    "page_number": page_num + 1,
                    "image": image,
                    "width": image.width,
                    "height": image.height
                })
            
            pdf_document.close()
            return pages_data
            
        except Exception as e:
            raise Exception(f"PDF处理失败: {str(e)}")
    
    def process_pdf_content(self, pdf_file, language="zh", progress_callback=None, fast_mode=False) -> Dict[str, Any]:
        """处理PDF文件，提取所有页面的内容并分析食物数据"""
        try:
            # 提取所有页面
            if progress_callback:
                mode_text = "快速模式" if fast_mode else "标准模式"
                progress_callback(f"正在提取PDF页面... ({mode_text})", 0.1)
            pages_data = self.extract_pages_from_pdf(pdf_file, fast_mode=fast_mode)
            
            all_text = []
            all_foods = []
            page_results = []
            total_pages = len(pages_data)
            
            # 处理每一页
            for i, page_data in enumerate(pages_data):
                page_num = page_data["page_number"]
                image = page_data["image"]
                
                # 更新进度
                if progress_callback:
                    progress = 0.1 + (i / total_pages) * 0.8  # 10%-90%
                    progress_callback(f"正在处理第 {page_num} 页... ({i+1}/{total_pages})", progress)
                
                # OCR识别当前页面
                page_text = self.ocr.extract_text_from_image(image, language=language)
                all_text.append(f"第{page_num}页: {page_text}")
                
                # 分析食物内容
                food_analysis = self.ocr.analyze_food_content(page_text, language=language)
                
                # 解析JSON结果
                food_data = self._parse_food_analysis(food_analysis)
                
                if food_data and "foods" in food_data:
                    # 为每个食物添加页面信息
                    for food in food_data["foods"]:
                        food["page_number"] = page_num
                        all_foods.append(food)
                
                page_results.append({
                    "page_number": page_num,
                    "text": page_text,
                    "foods": food_data.get("foods", []) if food_data else [],
                    "nutrition_totals": {
                        "calories": food_data.get("total_calories", 0) if food_data else 0,
                        "protein": food_data.get("total_protein", 0) if food_data else 0,
                        "carbs": food_data.get("total_carbs", 0) if food_data else 0,
                        "fat": food_data.get("total_fat", 0) if food_data else 0
                    } if food_data else {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
                })
            
            # 最终处理
            if progress_callback:
                progress_callback("正在生成分析报告...", 0.95)
            
            # 汇总所有食物数据
            total_nutrition = self._calculate_total_nutrition(all_foods)
            
            # 按类别统计食物
            food_categories = self._categorize_foods(all_foods)
            
            # 生成饮食建议
            dietary_advice = self._generate_dietary_advice(all_foods, total_nutrition)
            
            if progress_callback:
                progress_callback("处理完成！", 1.0)
            
            return {
                "total_pages": len(pages_data),
                "all_text": "\n\n".join(all_text),
                "all_foods": all_foods,
                "page_results": page_results,
                "total_nutrition": total_nutrition,
                "food_categories": food_categories,
                "dietary_advice": dietary_advice
            }
            
        except Exception as e:
            raise Exception(f"PDF内容处理失败: {str(e)}")
    
    def _parse_food_analysis(self, food_analysis: str) -> Dict[str, Any]:
        """解析食物分析结果"""
        try:
            # 尝试直接解析JSON
            if isinstance(food_analysis, str):
                # 移除可能的代码块标记
                text = food_analysis.strip()
                if text.startswith("```"):
                    text = text.strip("`")
                
                # 查找JSON部分
                first = text.find('{')
                last = text.rfind('}')
                if first != -1 and last != -1 and last > first:
                    text = text[first:last+1]
                
                return json.loads(text)
            elif isinstance(food_analysis, dict):
                return food_analysis
            else:
                return None
        except Exception:
            return None
    
    def _calculate_total_nutrition(self, foods: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算总营养成分"""
        total = {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0
        }
        
        for food in foods:
            total["calories"] += food.get("calories", 0)
            total["protein"] += food.get("protein", 0)
            total["carbs"] += food.get("carbs", 0)
            total["fat"] += food.get("fat", 0)
        
        return total
    
    def _categorize_foods(self, foods: List[Dict[str, Any]]) -> Dict[str, int]:
        """按类别统计食物数量"""
        categories = {}
        
        for food in foods:
            category = food.get("category", "Other")
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def _generate_dietary_advice(self, foods: List[Dict[str, Any]], total_nutrition: Dict[str, float]) -> str:
        """生成饮食建议"""
        advice_parts = []
        
        # 总体营养分析
        total_calories = total_nutrition["calories"]
        total_protein = total_nutrition["protein"]
        total_carbs = total_nutrition["carbs"]
        total_fat = total_nutrition["fat"]
        
        advice_parts.append(f"📊 营养分析报告")
        advice_parts.append(f"总热量: {total_calories:.1f} kcal")
        advice_parts.append(f"蛋白质: {total_protein:.1f} g")
        advice_parts.append(f"碳水化合物: {total_carbs:.1f} g")
        advice_parts.append(f"脂肪: {total_fat:.1f} g")
        advice_parts.append("")
        
        # 食物多样性分析
        unique_foods = len(set(food.get("name", "") for food in foods))
        advice_parts.append(f"🍽️ 食物多样性: 识别到 {unique_foods} 种不同食物")
        
        # 类别分布分析
        categories = self._categorize_foods(foods)
        if categories:
            advice_parts.append("📈 食物类别分布:")
            for category, count in categories.items():
                advice_parts.append(f"  • {category}: {count} 种")
        
        advice_parts.append("")
        
        # 营养建议
        if total_calories > 0:
            # 蛋白质比例
            protein_ratio = (total_protein * 4 / total_calories) * 100
            if protein_ratio < 10:
                advice_parts.append("⚠️ 蛋白质摄入偏低，建议增加瘦肉、鱼类、豆类等蛋白质来源")
            elif protein_ratio > 35:
                advice_parts.append("⚠️ 蛋白质摄入偏高，注意平衡其他营养素")
            else:
                advice_parts.append("✅ 蛋白质摄入比例合理")
            
            # 脂肪比例
            fat_ratio = (total_fat * 9 / total_calories) * 100
            if fat_ratio > 35:
                advice_parts.append("⚠️ 脂肪摄入偏高，建议减少油炸食品和高脂肪食物")
            elif fat_ratio < 15:
                advice_parts.append("⚠️ 脂肪摄入偏低，可适当增加健康脂肪来源")
            else:
                advice_parts.append("✅ 脂肪摄入比例合理")
            
            # 碳水化合物比例
            carbs_ratio = (total_carbs * 4 / total_calories) * 100
            if carbs_ratio > 65:
                advice_parts.append("⚠️ 碳水化合物摄入偏高，建议增加蛋白质和健康脂肪")
            elif carbs_ratio < 40:
                advice_parts.append("⚠️ 碳水化合物摄入偏低，可适当增加全谷物和水果")
            else:
                advice_parts.append("✅ 碳水化合物摄入比例合理")
        
        # 特殊建议
        if len(foods) > 0:
            advice_parts.append("")
            advice_parts.append("💡 个性化建议:")
            
            # 检查是否有蔬菜水果
            has_vegetables = any("vegetable" in food.get("category", "").lower() or 
                               "vitamin" in food.get("category", "").lower() 
                               for food in foods)
            if not has_vegetables:
                advice_parts.append("  • 建议增加蔬菜和水果摄入，提供丰富的维生素和矿物质")
            
            # 检查是否有全谷物
            has_whole_grains = any("grain" in food.get("name", "").lower() or 
                                 "whole" in food.get("name", "").lower() 
                                 for food in foods)
            if not has_whole_grains:
                advice_parts.append("  • 建议选择全谷物食品，提供更多膳食纤维")
            
            # 检查水分摄入
            advice_parts.append("  • 记得保持充足的水分摄入，建议每天8杯水")
        
        return "\n".join(advice_parts)
