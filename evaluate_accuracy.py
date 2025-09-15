#!/usr/bin/env python3
"""
Accuracy Evaluation Script for Diary Extractor
Compares the first 10 pages of extracted results against ground truth PDF
"""

import json
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from typing import Dict, List, Any, Tuple
import difflib
from collections import defaultdict
import argparse

class DiaryAccuracyEvaluator:
    def __init__(self, pdf_path: str, json_path: str):
        self.pdf_path = pdf_path
        self.json_path = json_path
        self.ground_truth_pages = []
        self.extracted_results = None
        self.evaluation_results = {}
        
    def load_extracted_results(self, max_pages: int = 10):
        """Load the extracted JSON results (first N pages only)"""
        print("📄 Loading extracted results...")
        with open(self.json_path, 'r', encoding='utf-8') as f:
            full_results = json.load(f)
        
        # Only keep the first N pages for evaluation
        self.extracted_results = {
            "source_pdf": full_results.get("source_pdf", ""),
            "page_count": min(len(full_results['pages']), max_pages),
            "category_summary": full_results.get("category_summary", {}),
            "processing_stats": full_results.get("processing_stats", {}),
            "pages": full_results['pages'][:max_pages]
        }
        print(f"✅ Loaded {len(self.extracted_results['pages'])} pages from JSON (first {max_pages} pages)")
        
    def extract_pdf_pages(self, max_pages: int = 10):
        """Extract first 10 pages from PDF as ground truth"""
        print(f"📖 Extracting first {max_pages} pages from PDF...")
        
        doc = fitz.open(self.pdf_path)
        total_pages = min(len(doc), max_pages)
        
        for page_num in range(total_pages):
            page = doc[page_num]
            # Convert to image for visual comparison
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            self.ground_truth_pages.append({
                'page_number': page_num + 1,
                'image': img,
                'text': page.get_text()
            })
            
        doc.close()
        print(f"✅ Extracted {len(self.ground_truth_pages)} pages from PDF")
        
    def evaluate_page_classification(self):
        """Evaluate page classification accuracy"""
        print("🔍 Evaluating page classification...")
        
        classification_results = {
            'correct': 0,
            'total': 0,
            'details': []
        }
        
        for i, gt_page in enumerate(self.ground_truth_pages):
            if i >= len(self.extracted_results['pages']):
                break
                
            extracted_page = self.extracted_results['pages'][i]
            gt_category = self._classify_page_manually(gt_page['image'])
            extracted_category = extracted_page['category']
            
            is_correct = gt_category == extracted_category
            classification_results['correct'] += is_correct
            classification_results['total'] += 1
            classification_results['details'].append({
                'page': i + 1,
                'ground_truth': gt_category,
                'extracted': extracted_category,
                'correct': is_correct
            })
            
        classification_results['accuracy'] = classification_results['correct'] / classification_results['total']
        return classification_results
        
    def _classify_page_manually(self, img: Image.Image) -> str:
        """Use the same classification logic as diary_extractor.py for accurate ground truth"""
        from ocr_processor import OCRProcessor
        
        # Initialize OCR processor (same as diary_extractor.py)
        ocr = OCRProcessor()
        
        # Use the exact same classification prompt as diary_extractor.py
        base64_img = ocr.encode_pil_image(img)
        prompt = (
            "You are a form classification assistant. Analyze this page image and classify it into one of these categories:\n\n"
            "1. food_diary - Contains a weekly food diary table with Monday-Sunday columns and Breakfast/Snack/Lunch/Dinner/Snack rows\n"
            "2. riding_diary - Contains a weekly riding diary table with Horses ridden/Falls/Trackwork/Gallops/Jumpouts/Trials/Races/Other columns\n"
            "3. sleep_diary_morning - Contains morning sleep diary with Bedtime/WakeUpTime/SleepLatencyMins/SleepQuality/MorningFeeling/NightAwakenings/DifficultyFactors\n"
            "4. sleep_diary_night - Contains night sleep diary with NapTaken/CaffeineMorningDrinks/CaffeineAfternoonDrinks/CaffeineEveningDrinks/ExerciseDuration/MedicationsOrDrugsUsed/DaytimeDrowsiness/OverallMood/PreBedActivities\n\n"
            "Respond with ONLY the category name (food_diary, riding_diary, sleep_diary_morning, sleep_diary_night, or unknown). No explanations."
        )

        try:
            response = ocr._chat_with_image(base64_img, prompt, ocr.primary_vision_model)
        except Exception as e:
            print(f"   ⚠️  Primary model failed: {e}, trying fallback...")
            response = ocr._chat_with_image(base64_img, prompt, ocr.fallback_vision_model)

        text = (response.choices[0].message.content or "").strip().lower()
        for cand in ["food_diary", "riding_diary", "sleep_diary_morning", "sleep_diary_night"]:
            if cand in text:
                return cand
        return "unknown"
    
    def evaluate_content_accuracy(self):
        """Evaluate content extraction accuracy"""
        print("📝 Evaluating content extraction...")
        
        content_results = {
            'food_diary': {'correct': 0, 'total': 0, 'details': []},
            'riding_diary': {'correct': 0, 'total': 0, 'details': []},
            'sleep_diary_morning': {'correct': 0, 'total': 0, 'details': []},
            'sleep_diary_night': {'correct': 0, 'total': 0, 'details': []}
        }
        
        for i, gt_page in enumerate(self.ground_truth_pages):
            if i >= len(self.extracted_results['pages']):
                break
                
            extracted_page = self.extracted_results['pages'][i]
            category = extracted_page['category']
            
            if category in content_results:
                # For now, we'll do a basic evaluation
                # In practice, you'd need to manually compare the content
                accuracy = self._evaluate_page_content(gt_page, extracted_page)
                
                content_results[category]['correct'] += accuracy
                content_results[category]['total'] += 1
                content_results[category]['details'].append({
                    'page': i + 1,
                    'accuracy': accuracy
                })
        
        # Calculate overall accuracy for each category
        for category in content_results:
            if content_results[category]['total'] > 0:
                content_results[category]['accuracy'] = content_results[category]['correct'] / content_results[category]['total']
            else:
                content_results[category]['accuracy'] = 0.0
                
        return content_results
    
    def _evaluate_page_content(self, gt_page: Dict, extracted_page: Dict) -> float:
        """Evaluate content accuracy for a single page using more sophisticated checks"""
        # Check if structured data exists
        if 'structured' not in extracted_page:
            return 0.0
            
        structured_data = extracted_page['structured']
        category = extracted_page['category']
        
        # Add page number to structured data for ground truth comparison
        structured_data['page_number'] = extracted_page.get('page', 1)
        
        # More detailed evaluation based on category
        if category == 'food_diary':
            return self._evaluate_food_diary_content(structured_data)
        elif category == 'riding_diary':
            return self._evaluate_riding_diary_content(structured_data)
        elif category in ['sleep_diary_morning', 'sleep_diary_night']:
            return self._evaluate_sleep_diary_content(structured_data, category)
        else:
            return 0.5  # Unknown category
    
    def _evaluate_food_diary_content(self, data: Dict) -> float:
        """Evaluate food diary content quality by comparing with actual image data"""
        from ocr_processor import OCRProcessor
        
        # Get the page image for this food diary
        page_num = data.get('page_number', 1)
        if page_num <= len(self.ground_truth_pages):
            img = self.ground_truth_pages[page_num - 1]['image']
            
            # Extract food diary data from image using the same method as diary_extractor
            ocr = OCRProcessor()
            base64_img = ocr.encode_pil_image(img)
            
            # Use the same prompt as diary_extractor for food diary extraction
            prompt = (
                "You will perform OCR and structured extraction on a \"MASSEY UNIVERSITY / My Food Diary\" handwritten form.\n\n"
                "Output only a JSON following this structure and rules (no explanations):\n"
                "{\n"
                "  \"name\": \"string|null\",\n"
                "  \"date\": \"string|null\",\n"
                "  \"days\": {\n"
                "    \"monday\":    {\"breakfast\":[], \"snack1\":[], \"lunch\":[], \"snack2\":[], \"dinner\":[], \"snack3\":[]},\n"
                "    \"tuesday\":   {\"breakfast\":[], \"snack1\":[], \"lunch\":[], \"snack2\":[], \"dinner\":[], \"snack3\":[]},\n"
                "    \"wednesday\": {\"breakfast\":[], \"snack1\":[], \"lunch\":[], \"snack2\":[], \"dinner\":[], \"snack3\":[]},\n"
                "    \"thursday\":  {\"breakfast\":[], \"snack1\":[], \"lunch\":[], \"snack2\":[], \"dinner\":[], \"snack3\":[]},\n"
                "    \"friday\":    {\"breakfast\":[], \"snack1\":[], \"lunch\":[], \"snack2\":[], \"dinner\":[], \"snack3\":[]},\n"
                "    \"saturday\":  {\"breakfast\":[], \"snack1\":[], \"lunch\":[], \"snack2\":[], \"dinner\":[], \"snack3\":[]},\n"
                "    \"sunday\":    {\"breakfast\":[], \"snack1\":[], \"lunch\":[], \"snack2\":[], \"dinner\":[], \"snack3\":[]}\n"
                "  },\n"
                "  \"notes\": \"string|null\",\n"
                "  \"uncertain\": []\n"
                "}\n\n"
                "Rules:\n"
                "- Read each cell under \"Breakfast / Snack / Lunch / Snack / Dinner / Snack\" (this table has three Snack columns, map them to snack1, snack2, snack3 respectively).\n"
                "- Keep original spelling but translate ALL Chinese food names to English equivalents.\n"
                "- If unreadable or blank: leave array empty []; if uncertain reading, put the text in the array and record position with candidates in `uncertain`.\n"
                "- Each array element is an object: {\"text\":\"English food name\"}\n"
                "- Output ALL content in English only.\n\n"
                "Now process this image (food diary): return JSON."
            )
            
            try:
                response = ocr._chat_with_image(base64_img, prompt, ocr.primary_vision_model)
            except Exception:
                response = ocr._chat_with_image(base64_img, prompt, ocr.fallback_vision_model)
            
            # Parse the ground truth data
            text = (response.choices[0].message.content or "").strip()
            if text.startswith("```"):
                text = text.strip("`")
            first = text.find("{")
            last = text.rfind("}")
            if first != -1 and last != -1 and last > first:
                text = text[first:last+1]
            
            try:
                ground_truth_data = json.loads(text)
                return self._compare_food_diary_data(ground_truth_data, data)
            except Exception as e:
                print(f"   ⚠️  Failed to parse ground truth for food diary: {e}")
                return 0.5  # Fallback score
        
        return 0.5  # Fallback if no image available
    
    def _compare_food_diary_data(self, ground_truth: Dict, extracted: Dict) -> float:
        """Compare ground truth food diary data with extracted data"""
        score = 0.0
        total_comparisons = 0
        
        print(f"   🔍 Comparing Food Diary Data:")
        
        # Compare name
        if 'name' in ground_truth and 'name' in extracted:
            total_comparisons += 1
            gt_name = ground_truth['name']
            ext_name = extracted['name']
            
            if gt_name == ext_name:
                score += 1
                print(f"     ✅ Name: '{gt_name}' == '{ext_name}' (1.0)")
            elif gt_name and ext_name and gt_name.lower() == ext_name.lower():
                score += 0.8
                print(f"     ⚠️  Name: '{gt_name}' ≈ '{ext_name}' (0.8 - case insensitive)")
            else:
                print(f"     ❌ Name: '{gt_name}' ≠ '{ext_name}' (0.0)")
        
        # Compare days data
        if 'days' in ground_truth and 'days' in extracted:
            valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            meal_types = ['breakfast', 'snack1', 'lunch', 'snack2', 'dinner', 'snack3']
            
            for day in valid_days:
                if day in ground_truth['days'] and day in extracted['days']:
                    gt_day = ground_truth['days'][day]
                    ext_day = extracted['days'][day]
                    
                    print(f"     📅 {day.capitalize()}:")
                    
                    for meal in meal_types:
                        if meal in gt_day and meal in ext_day:
                            total_comparisons += 1
                            meal_score = self._compare_meal_data(gt_day[meal], ext_day[meal], f"       {meal}")
                            score += meal_score
        
        final_score = score / total_comparisons if total_comparisons > 0 else 0.5
        print(f"   📊 Food Diary Score: {final_score:.3f} ({score}/{total_comparisons})")
        return final_score
    
    def _compare_meal_data(self, gt_meal: List, ext_meal: List, meal_name: str = "") -> float:
        """Compare meal data between ground truth and extracted"""
        if not gt_meal and not ext_meal:
            print(f"     {meal_name}: Both empty (1.0)")
            return 1.0  # Both empty
        if not gt_meal or not ext_meal:
            print(f"     {meal_name}: One empty, one not (0.0)")
            return 0.0  # One empty, one not
        
        # Extract text from meal items
        gt_texts = [item.get('text', '') for item in gt_meal if isinstance(item, dict)]
        ext_texts = [item.get('text', '') for item in ext_meal if isinstance(item, dict)]
        
        if not gt_texts and not ext_texts:
            print(f"     {meal_name}: Both empty texts (1.0)")
            return 1.0
        if not gt_texts or not ext_texts:
            print(f"     {meal_name}: One empty text, one not (0.0)")
            return 0.0
        
        # Simple text matching
        matches = 0
        print(f"     {meal_name}: GT={gt_texts} vs EXT={ext_texts}")
        
        for gt_text in gt_texts:
            for ext_text in ext_texts:
                if gt_text.lower() == ext_text.lower():
                    matches += 1
                    print(f"       ✅ Match: '{gt_text}' == '{ext_text}'")
                    break
            else:
                print(f"       ❌ No match for: '{gt_text}'")
        
        score = matches / max(len(gt_texts), len(ext_texts))
        print(f"       📊 {meal_name} Score: {score:.3f} ({matches}/{max(len(gt_texts), len(ext_texts))})")
        return score
    
    def _evaluate_riding_diary_content(self, data: Dict) -> float:
        """Evaluate riding diary content quality by comparing with actual image data"""
        from ocr_processor import OCRProcessor
        
        # Get the page image for this riding diary
        page_num = data.get('page_number', 1)
        if page_num <= len(self.ground_truth_pages):
            img = self.ground_truth_pages[page_num - 1]['image']
            
            # Extract riding diary data from image
            ocr = OCRProcessor()
            base64_img = ocr.encode_pil_image(img)
            
            prompt = (
                "You are a riding diary form extraction assistant. This page is a riding diary table containing numbers, text, and check marks. Please combine OCR results with your own recognition to identify content in the image.\n"
                "Please perform error correction and standardization while considering the original layout (row/column alignment, headers, merged cells, etc.):\n"
                "- Carefully identify the days of the week (Monday/Tuesday/Wednesday/Thursday/Friday/Saturday/Sunday) in the table.\n"
                "- For numeric fields (such as Horses ridden, Falls, etc.), extract actual numbers; use '0' if empty.\n"
                "- For text fields, extract actual content; use null if empty.\n"
                "- Output records for 7 days (Monday..Sunday) in table order, use null if missing.\n"
                "- Output all text content in English. Translate Chinese text to English equivalents.\n"
                "- Output only JSON that must conform to the following pattern:\n\n"
                "{\n"
                "  \"category\": \"riding_diary\",\n"
                "  \"records\": [\n"
                "    { \"Day\": \"Monday|Tuesday|...\", \"Horses ridden\": \"string\", \"Falls\": \"string\", \"Trackwork\": \"string\", \"Gallops\": \"string\", \"Jumpouts\": \"string\", \"Trials\": \"string\", \"Races\": \"string\", \"Other eg. gym/run\": \"string\" }\n"
                "  ]\n"
                "}"
            )
            
            try:
                response = ocr._chat_with_image(base64_img, prompt, ocr.primary_vision_model)
            except Exception:
                response = ocr._chat_with_image(base64_img, prompt, ocr.fallback_vision_model)
            
            # Parse the ground truth data
            text = (response.choices[0].message.content or "").strip()
            if text.startswith("```"):
                text = text.strip("`")
            first = text.find("{")
            last = text.rfind("}")
            if first != -1 and last != -1 and last > first:
                text = text[first:last+1]
            
            try:
                ground_truth_data = json.loads(text)
                return self._compare_riding_diary_data(ground_truth_data, data)
            except Exception as e:
                print(f"   ⚠️  Failed to parse ground truth for riding diary: {e}")
                return 0.5
        
        return 0.5
    
    def _compare_riding_diary_data(self, ground_truth: Dict, extracted: Dict) -> float:
        """Compare ground truth riding diary data with extracted data"""
        if 'records' not in ground_truth or 'records' not in extracted:
            print(f"   ❌ Missing records in ground truth or extracted data")
            return 0.0
        
        gt_records = ground_truth['records']
        ext_records = extracted['records']
        
        if not gt_records or not ext_records:
            print(f"   ❌ Empty records in ground truth or extracted data")
            return 0.0
        
        print(f"   🔍 Comparing Riding Diary Data:")
        
        # Compare each day's data
        score = 0.0
        total_comparisons = 0
        
        for gt_record in gt_records:
            day = gt_record.get('Day', '')
            print(f"     📅 {day}:")
            
            # Find corresponding extracted record
            ext_record = None
            for er in ext_records:
                if er.get('Day', '') == day:
                    ext_record = er
                    break
            
            if ext_record:
                # Compare numeric fields
                numeric_fields = ['Horses ridden', 'Falls', 'Trackwork', 'Gallops', 'Jumpouts', 'Trials', 'Races']
                for field in numeric_fields:
                    total_comparisons += 1
                    gt_val = str(gt_record.get(field, '0'))
                    ext_val = str(ext_record.get(field, '0'))
                    
                    if gt_val == ext_val:
                        score += 1.0
                        print(f"       ✅ {field}: '{gt_val}' == '{ext_val}' (1.0)")
                    elif gt_val.isdigit() and ext_val.isdigit() and abs(int(gt_val) - int(ext_val)) <= 1:
                        score += 0.8  # Close numeric match
                        print(f"       ⚠️  {field}: '{gt_val}' ≈ '{ext_val}' (0.8 - close match)")
                    else:
                        print(f"       ❌ {field}: '{gt_val}' ≠ '{ext_val}' (0.0)")
            else:
                print(f"       ❌ No matching record found for {day}")
        
        final_score = score / total_comparisons if total_comparisons > 0 else 0.5
        print(f"   📊 Riding Diary Score: {final_score:.3f} ({score}/{total_comparisons})")
        return final_score
    
    def _evaluate_sleep_diary_content(self, data: Dict, category: str) -> float:
        """Evaluate sleep diary content quality by comparing with actual image data"""
        from ocr_processor import OCRProcessor
        
        # Get the page image for this sleep diary
        page_num = data.get('page_number', 1)
        if page_num <= len(self.ground_truth_pages):
            img = self.ground_truth_pages[page_num - 1]['image']
            
            # Rotate image if it's a sleep diary (same as diary_extractor)
            rotated_img = img.rotate(-90, expand=True)
            
            # Extract sleep diary data from image
            ocr = OCRProcessor()
            base64_img = ocr.encode_pil_image(rotated_img)
            
            if category == "sleep_diary_morning":
                schema = (
                    "{\n"
                    "  \"category\": \"sleep_diary_morning\",\n"
                    "  \"records\": [\n"
                    "    { \"Day\": \"Monday|Tuesday|...\", \"Bedtime\": \"HH:MM\", \"WakeUpTime\": \"HH:MM\", \"SleepLatencyMins\": \"number|string\", \"SleepQuality\": \"string\", \"MorningFeeling\": \"string\", \"NightAwakenings\": \"string\", \"DifficultyFactors\": \"string\" }\n"
                    "  ]\n"
                    "}"
                )
            else:
                schema = (
                    "{\n"
                    "  \"category\": \"sleep_diary_night\",\n"
                    "  \"records\": [\n"
                    "    { \"Day\": \"Monday|Tuesday|...\", \"NapTaken\": \"string\", \"CaffeineMorningDrinks\": \"string\", \"CaffeineAfternoonDrinks\": \"string\", \"CaffeineEveningDrinks\": \"string\", \"ExerciseDuration\": \"string\", \"MedicationsOrDrugsUsed\": \"string\", \"DaytimeDrowsiness\": \"string\", \"OverallMood\": \"string\", \"PreBedActivities\": \"string\" }\n"
                    "  ],\n"
                    "  \"metadata\": { \"institution\": \"string\", \"name\": \"string\", \"date\": \"YYYY-MM-DD|string\", \"form_title\": \"Sleep Diary: Night\" }\n"
                    "}"
                )
            
            prompt = (
                "You are a sleep diary form extraction assistant. This page is a sleep diary table containing checkboxes (circled/selected options) and handwritten/printed text. Please combine OCR results with your own recognition to identify content in the image. One vertical column represents one week.\n"
                "Please perform error correction and standardization while considering the original layout (row/column alignment, headers, merged cells, etc.):\n"
                "- For circled/solid circles/selected options, treat them as selected and use them as the result value for that field.\n"
                "- If multiple selections appear in the same field, use the most obvious/last selection; if unclear, list multiple values as a string.\n"
                "- Time format: HH:MM; Date format: YYYY-MM-DD (keep original if uncertain).\n"
                "- Output records for 7 days (Monday..Sunday) in table order.\n"
                "- For SleepQuality: carefully read the actual selected option (VG/Good/Average/Bad/VB), do not default to 'Very Good'.\n"
                "- For NightAwakenings: if no awakenings, use '0' instead of empty string.\n"
                "- For ExerciseDuration: if there's a number, use the actual number; if empty or no exercise, use '0' instead of empty string.\n"
                "- For MedicationsOrDrugsUsed: if empty or no medications, use 'No' instead of empty string.\n"
                "- For any field with a slash (/) or empty, use null instead of empty string.\n"
                "- For DaytimeDrowsiness: if empty or no drowsiness, use 'No' instead of empty string.\n"
                "- For OverallMood: if empty or no mood, use 'No' instead of empty string.\n"
                "- For PreBedActivities: if empty or no activities, use 'No' instead of empty string.\n"
                "- For NapTaken: if empty or no nap, use 'No' instead of empty string.\n"
                "- For CaffeineMorningDrinks: if empty or no caffeine, use '0' instead of empty string.\n"
                "- For CaffeineAfternoonDrinks: if empty or no caffeine, use '0' instead of empty string.\n"
                "- For CaffeineEveningDrinks: if empty or no caffeine, use '0' instead of empty string.\n"
                "- Output records for 7 days (Monday..Sunday) in table order, use null if missing.\n"
                "- Output all text content in English. Translate Chinese text to English equivalents.\n"
                "- Output only JSON that must conform to the following pattern:\n\n"
                f"Pattern: \n{schema}\n"
            )
            
            try:
                response = ocr._chat_with_image(base64_img, prompt, ocr.primary_vision_model)
            except Exception:
                response = ocr._chat_with_image(base64_img, prompt, ocr.fallback_vision_model)
            
            # Parse the ground truth data
            text = (response.choices[0].message.content or "").strip()
            if text.startswith("```"):
                text = text.strip("`")
            first = text.find("{")
            last = text.rfind("}")
            if first != -1 and last != -1 and last > first:
                text = text[first:last+1]
            
            try:
                ground_truth_data = json.loads(text)
                return self._compare_sleep_diary_data(ground_truth_data, data, category)
            except Exception as e:
                print(f"   ⚠️  Failed to parse ground truth for sleep diary: {e}")
                return 0.5
        
        return 0.5
    
    def _compare_sleep_diary_data(self, ground_truth: Dict, extracted: Dict, category: str) -> float:
        """Compare ground truth sleep diary data with extracted data"""
        if 'records' not in ground_truth or 'records' not in extracted:
            print(f"   ❌ Missing records in ground truth or extracted data")
            return 0.0
        
        gt_records = ground_truth['records']
        ext_records = extracted['records']
        
        if not gt_records or not ext_records:
            print(f"   ❌ Empty records in ground truth or extracted data")
            return 0.0
        
        print(f"   🔍 Comparing Sleep Diary Data ({category}):")
        
        # Compare each day's data
        score = 0.0
        total_comparisons = 0
        
        for gt_record in gt_records:
            day = gt_record.get('Day', '')
            print(f"     📅 {day}:")
            
            # Find corresponding extracted record
            ext_record = None
            for er in ext_records:
                if er.get('Day', '') == day:
                    ext_record = er
                    break
            
            if ext_record:
                if category == 'sleep_diary_morning':
                    fields = ['Bedtime', 'WakeUpTime', 'SleepLatencyMins', 'SleepQuality', 'MorningFeeling', 'NightAwakenings', 'DifficultyFactors']
                else:  # sleep_diary_night
                    fields = ['NapTaken', 'CaffeineMorningDrinks', 'CaffeineAfternoonDrinks', 'CaffeineEveningDrinks', 'ExerciseDuration', 'MedicationsOrDrugsUsed', 'DaytimeDrowsiness', 'OverallMood', 'PreBedActivities']
                
                for field in fields:
                    total_comparisons += 1
                    gt_val = str(gt_record.get(field, ''))
                    ext_val = str(ext_record.get(field, ''))
                    
                    if gt_val == ext_val:
                        score += 1.0
                        print(f"       ✅ {field}: '{gt_val}' == '{ext_val}' (1.0)")
                    elif gt_val.lower() == ext_val.lower():
                        score += 0.9  # Case insensitive match
                        print(f"       ⚠️  {field}: '{gt_val}' ≈ '{ext_val}' (0.9 - case insensitive)")
                    elif self._is_similar_value(gt_val, ext_val):
                        score += 0.7  # Similar values
                        print(f"       ⚠️  {field}: '{gt_val}' ≈ '{ext_val}' (0.7 - similar)")
                    else:
                        print(f"       ❌ {field}: '{gt_val}' ≠ '{ext_val}' (0.0)")
            else:
                print(f"       ❌ No matching record found for {day}")
        
        final_score = score / total_comparisons if total_comparisons > 0 else 0.5
        print(f"   📊 Sleep Diary Score: {final_score:.3f} ({score}/{total_comparisons})")
        return final_score
    
    def _is_similar_value(self, val1: str, val2: str) -> bool:
        """Check if two values are similar (for sleep diary fields)"""
        if not val1 or not val2:
            return val1 == val2
        
        # Normalize values
        v1 = val1.lower().strip()
        v2 = val2.lower().strip()
        
        # Direct match
        if v1 == v2:
            return True
        
        # Common variations
        variations = {
            'no': ['0', 'none', 'null'],
            'yes': ['1', 'y'],
            'vg': ['very good', 'very_good'],
            'g': ['good'],
            'a': ['average'],
            'b': ['bad'],
            'vb': ['very bad', 'very_bad']
        }
        
        for key, variants in variations.items():
            if (v1 == key and v2 in variants) or (v2 == key and v1 in variants):
                return True
        
        return False
    
    def generate_manual_evaluation_template(self):
        """Generate a template for manual evaluation"""
        print("📋 Generating manual evaluation template...")
        
        template = {
            "evaluation_instructions": {
                "description": "Manual evaluation template for diary extraction accuracy",
                "steps": [
                    "1. Compare each page's classification (food_diary, riding_diary, sleep_diary_morning, sleep_diary_night)",
                    "2. For each page, manually verify the extracted content against the PDF",
                    "3. Rate accuracy on a scale of 0-1 for each page",
                    "4. Note any specific errors or issues"
                ]
            },
            "pages_to_evaluate": []
        }
        
        for i, gt_page in enumerate(self.ground_truth_pages):
            if i >= len(self.extracted_results['pages']):
                break
                
            extracted_page = self.extracted_results['pages'][i]
            
            page_eval = {
                "page_number": i + 1,
                "extracted_category": extracted_page['category'],
                "manual_classification": "TO_BE_FILLED",
                "classification_correct": "TO_BE_FILLED",
                "content_accuracy": "TO_BE_FILLED",
                "notes": "TO_BE_FILLED",
                "extracted_content": extracted_page['structured']
            }
            
            template["pages_to_evaluate"].append(page_eval)
        
        # Save template
        template_path = "manual_evaluation_template.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Manual evaluation template saved to {template_path}")
        return template_path
    
    def run_automatic_evaluation(self, max_pages: int = 10):
        """Run automatic evaluation (limited accuracy)"""
        print("🤖 Running automatic evaluation...")
        
        # Load data
        self.load_extracted_results(max_pages=max_pages)
        self.extract_pdf_pages(max_pages=max_pages)
        
        # Run evaluations
        classification_results = self.evaluate_page_classification()
        content_results = self.evaluate_content_accuracy()
        
        # Compile results
        self.evaluation_results = {
            "summary": {
                "total_pages_evaluated": len(self.ground_truth_pages),
                "overall_classification_accuracy": classification_results['accuracy'],
                "overall_content_accuracy": sum(
                    results['accuracy'] for results in content_results.values()
                ) / len([r for r in content_results.values() if r['total'] > 0])
            },
            "classification_results": classification_results,
            "content_results": content_results,
            "note": "This is an automatic evaluation with limited accuracy. For precise results, use manual evaluation."
        }
        
        return self.evaluation_results
    
    def save_results(self, output_path: str = "evaluation_results.json"):
        """Save evaluation results"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.evaluation_results, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to {output_path}")
    
    def print_summary(self):
        """Print evaluation summary"""
        if not self.evaluation_results:
            print("❌ No evaluation results available. Run evaluation first.")
            return
            
        print("\n" + "="*60)
        print("📊 EVALUATION SUMMARY")
        print("="*60)
        
        summary = self.evaluation_results['summary']
        print(f"📄 Total pages evaluated: {summary['total_pages_evaluated']}")
        print(f"🎯 Classification accuracy: {summary['overall_classification_accuracy']:.2%}")
        print(f"📝 Content accuracy: {summary['overall_content_accuracy']:.2%}")
        
        print("\n📋 Classification Details:")
        for detail in self.evaluation_results['classification_results']['details']:
            status = "✅" if detail['correct'] else "❌"
            print(f"  Page {detail['page']}: {status} GT={detail['ground_truth']}, Extracted={detail['extracted']}")
        
        print("\n📊 Content Accuracy by Category:")
        for category, results in self.evaluation_results['content_results'].items():
            if results['total'] > 0:
                print(f"  {category}: {results['accuracy']:.2%} ({results['correct']}/{results['total']})")

def main():
    parser = argparse.ArgumentParser(description="Evaluate diary extraction accuracy")
    parser.add_argument("--pdf", default="JockeyDiaries230725.pdf", help="Path to PDF file")
    parser.add_argument("--json", default="JockeyDiaries230725.json", help="Path to extracted JSON file")
    parser.add_argument("--output", default="evaluation_results.json", help="Output file for results")
    parser.add_argument("--pages", type=int, default=10, help="Number of pages to evaluate (default: 10)")
    parser.add_argument("--template", action="store_true", help="Generate manual evaluation template")
    parser.add_argument("--no-template", action="store_true", help="Skip generating manual evaluation template")
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.pdf):
        print(f"❌ PDF file not found: {args.pdf}")
        return
        
    if not os.path.exists(args.json):
        print(f"❌ JSON file not found: {args.json}")
        return
    
    # Initialize evaluator
    evaluator = DiaryAccuracyEvaluator(args.pdf, args.json)
    
    if args.template:
        # Generate manual evaluation template
        evaluator.load_extracted_results(max_pages=args.pages)
        evaluator.extract_pdf_pages(max_pages=args.pages)
        template_path = evaluator.generate_manual_evaluation_template()
        print(f"\n📋 Manual evaluation template created: {template_path}")
        print("Please fill in the template with manual evaluations and run the script again.")
    else:
        # Run automatic evaluation
        results = evaluator.run_automatic_evaluation(max_pages=args.pages)
        evaluator.save_results(args.output)
        evaluator.print_summary()
        
        # Generate template for manual evaluation only if not disabled
        if not args.no_template:
            template_path = evaluator.generate_manual_evaluation_template()
            print(f"\n📋 For more accurate results, please use the manual evaluation template: {template_path}")
        else:
            print(f"\n✅ Automatic evaluation completed. Results saved to {args.output}")

if __name__ == "__main__":
    main()
