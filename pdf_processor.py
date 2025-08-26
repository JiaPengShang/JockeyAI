import fitz  # PyMuPDF
import base64
import io
from PIL import Image
import numpy as np
from typing import List, Dict, Any
import json
from ocr_processor import OCRProcessor

class PDFProcessor:
    """PDF processor that supports multi-page OCR and food data extraction"""
    
    def __init__(self):
        self.ocr = OCRProcessor()
        
    def extract_pages_from_pdf(self, pdf_file, fast_mode=False) -> List[Dict[str, Any]]:
        """Extract all pages from PDF and render to images"""
        pages_data = []
        
        try:
            # Open PDF
            pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
            total_pages = len(pdf_document)
            
            for page_num in range(total_pages):
                # Get page
                page = pdf_document.load_page(page_num)
                
                # Optimize: dynamic scale factor by page size and mode
                page_rect = page.rect
                page_width = page_rect.width
                page_height = page_rect.height
                
                if fast_mode:
                    # Fast mode: smaller scale
                    if page_width > 600 or page_height > 800:
                        scale_factor = 1.0  # 最小缩放
                    else:
                        scale_factor = 1.2  # 较小缩放
                else:
                    # Standard mode: adjust by size
                    if page_width > 800 or page_height > 1000:
                        scale_factor = 1.5  # 降低缩放因子
                    else:
                        scale_factor = 2.0  # 保持原有缩放因子
                
                mat = fitz.Matrix(scale_factor, scale_factor)
                
                # Render page to image
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL image
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
            raise Exception(f"PDF processing failed: {str(e)}")
    
    def process_pdf_content(self, pdf_file, language="en", progress_callback=None, fast_mode=False) -> Dict[str, Any]:
        """Process PDF: extract text per page and analyze food data"""
        try:
            # Extract all pages
            if progress_callback:
                mode_text = "Fast mode" if fast_mode else "Standard mode"
                progress_callback(f"Extracting PDF pages... ({mode_text})", 0.1)
            pages_data = self.extract_pages_from_pdf(pdf_file, fast_mode=fast_mode)
            
            all_text = []
            all_foods = []
            page_results = []
            total_pages = len(pages_data)
            
            # Process each page
            for i, page_data in enumerate(pages_data):
                page_num = page_data["page_number"]
                image = page_data["image"]
                
                # Update progress
                if progress_callback:
                    progress = 0.1 + (i / total_pages) * 0.8  # 10%-90%
                    progress_callback(f"Processing page {page_num}... ({i+1}/{total_pages})", progress)
                
                # OCR current page
                page_text = self.ocr.extract_text_from_image(image, language=language)
                all_text.append(f"Page {page_num}: {page_text}")
                
                # Analyze food content
                food_analysis = self.ocr.analyze_food_content(page_text, language=language)
                
                # Parse JSON
                food_data = self._parse_food_analysis(food_analysis)
                
                if food_data and "foods" in food_data:
                    # Attach page info to each food
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
            
            # Final steps
            if progress_callback:
                progress_callback("Generating analysis report...", 0.95)
            
            # Aggregate foods
            total_nutrition = self._calculate_total_nutrition(all_foods)
            
            # Count by category
            food_categories = self._categorize_foods(all_foods)
            
            # Generate dietary advice
            dietary_advice = self._generate_dietary_advice(all_foods, total_nutrition)
            
            if progress_callback:
                progress_callback("Processing completed!", 1.0)
            
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
            raise Exception(f"PDF content processing failed: {str(e)}")
    
    def _parse_food_analysis(self, food_analysis: str) -> Dict[str, Any]:
        """Parse food analysis JSON"""
        try:
            # 尝试直接解析JSON
            if isinstance(food_analysis, str):
                # Remove possible code fences
                text = food_analysis.strip()
                if text.startswith("```"):
                    text = text.strip("`")
                
                # Extract JSON substring
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
        """Calculate total nutrition"""
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
        """Count foods by category"""
        categories = {}
        
        for food in foods:
            category = food.get("category", "Other")
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def _generate_dietary_advice(self, foods: List[Dict[str, Any]], total_nutrition: Dict[str, float]) -> str:
        """Generate dietary advice (English)"""
        advice_parts = []
        
        # Overall nutrition analysis
        total_calories = total_nutrition["calories"]
        total_protein = total_nutrition["protein"]
        total_carbs = total_nutrition["carbs"]
        total_fat = total_nutrition["fat"]
        
        advice_parts.append(f"📊 Nutrition Analysis Report")
        advice_parts.append(f"Total Calories: {total_calories:.1f} kcal")
        advice_parts.append(f"Protein: {total_protein:.1f} g")
        advice_parts.append(f"Carbohydrates: {total_carbs:.1f} g")
        advice_parts.append(f"Fat: {total_fat:.1f} g")
        advice_parts.append("")
        
        # Food diversity
        unique_foods = len(set(food.get("name", "") for food in foods))
        advice_parts.append(f"🍽️ Food Diversity: {unique_foods} unique items identified")
        
        # Category distribution
        categories = self._categorize_foods(foods)
        if categories:
            advice_parts.append("📈 Food Category Distribution:")
            for category, count in categories.items():
                advice_parts.append(f"  • {category}: {count} items")
        
        advice_parts.append("")
        
        # Nutrition suggestions
        if total_calories > 0:
            # Protein ratio
            protein_ratio = (total_protein * 4 / total_calories) * 100
            if protein_ratio < 10:
                advice_parts.append("⚠️ Low protein intake. Consider lean meats, fish, legumes, dairy.")
            elif protein_ratio > 35:
                advice_parts.append("⚠️ High protein proportion. Balance with carbs and healthy fats.")
            else:
                advice_parts.append("✅ Protein proportion is reasonable.")
            
            # Fat ratio
            fat_ratio = (total_fat * 9 / total_calories) * 100
            if fat_ratio > 35:
                advice_parts.append("⚠️ High fat intake. Reduce fried and high-fat foods.")
            elif fat_ratio < 15:
                advice_parts.append("⚠️ Low fat intake. Add healthy fats like olive oil, nuts.")
            else:
                advice_parts.append("✅ Fat proportion is reasonable.")
            
            # Carbohydrate ratio
            carbs_ratio = (total_carbs * 4 / total_calories) * 100
            if carbs_ratio > 65:
                advice_parts.append("⚠️ High carbohydrates intake. Increase protein and healthy fats.")
            elif carbs_ratio < 40:
                advice_parts.append("⚠️ Low carbohydrates. Add whole grains and fruits.")
            else:
                advice_parts.append("✅ Carbohydrates proportion is reasonable.")
        
        # Additional tips
        if len(foods) > 0:
            advice_parts.append("")
            advice_parts.append("💡 Personalized Tips:")
            
            # Check vegetables/fruits
            has_vegetables = any("vegetable" in food.get("category", "").lower() or 
                               "vitamin" in food.get("category", "").lower() 
                               for food in foods)
            if not has_vegetables:
                advice_parts.append("  • Add vegetables and fruits to increase vitamins and minerals.")
            
            # Check whole grains
            has_whole_grains = any("grain" in food.get("name", "").lower() or 
                                 "whole" in food.get("name", "").lower() 
                                 for food in foods)
            if not has_whole_grains:
                advice_parts.append("  • Choose whole grains for more dietary fiber.")
            
            # Hydration
            advice_parts.append("  • Stay hydrated. Aim for ~8 cups of water per day.")
        
        return "\n".join(advice_parts)
