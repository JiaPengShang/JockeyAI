import os
import json
import random
import numpy as np
from typing import List, Dict, Any
import fitz  # PyMuPDF
from PIL import Image
import io
from tqdm import tqdm
import time

from ocr_processor import OCRProcessor


class DiaryExtractor:
    def __init__(self, dpi: int = 200, language: str = "zh", seed: int = 42):
        self.dpi = dpi
        self.language = language
        self.seed = seed
        self.ocr = OCRProcessor()
        
        # Set random seeds for reproducibility
        random.seed(seed)
        np.random.seed(seed)
        
        # Initialize processing statistics
        self.stats = {
            "total_pages": 0,
            "successful_pages": 0,
            "failed_pages": 0,
            "category_counts": {},
            "processing_times": []
        }

    def _render_pdf_pages(self, pdf_path: str) -> List[Image.Image]:
        doc = fitz.open(pdf_path)
        images: List[Image.Image] = []
        zoom = self.dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(img)
        doc.close()
        return images

    # ---------- Page-level category detection ----------
    def _classify_page(self, img: Image.Image) -> str:
        """Use vision model to classify page into one of the predefined categories.

        Returns one of: 'food_diary', 'riding_diary', 'sleep_diary_morning', 'sleep_diary_night', 'unknown'
        """
        base64_img = self.ocr.encode_pil_image(img)
        prompt = (
            "You are a form classification assistant. Analyze this page image and classify it into one of these categories:\n\n"
            "1. food_diary - Contains a weekly food diary table with Monday-Sunday columns and Breakfast/Snack/Lunch/Dinner/Snack rows\n"
            "2. riding_diary - Contains a weekly riding diary table with Horses ridden/Falls/Trackwork/Gallops/Jumpouts/Trials/Races/Other columns\n"
            "3. sleep_diary_morning - Contains morning sleep diary with Bedtime/WakeUpTime/SleepLatencyMins/SleepQuality/MorningFeeling/NightAwakenings/DifficultyFactors\n"
            "4. sleep_diary_night - Contains night sleep diary with NapTaken/CaffeineMorningDrinks/CaffeineAfternoonDrinks/CaffeineEveningDrinks/ExerciseDuration/MedicationsOrDrugsUsed/DaytimeDrowsiness/OverallMood/PreBedActivities\n\n"
            "Respond with ONLY the category name (food_diary, riding_diary, sleep_diary_morning, sleep_diary_night, or unknown). No explanations."
        )

        try:
            response = self.ocr._chat_with_image(base64_img, prompt, self.ocr.primary_vision_model)
        except Exception as e:
            print(f"   ⚠️  Primary model failed: {e}, trying fallback...")
            response = self.ocr._chat_with_image(base64_img, prompt, self.ocr.fallback_vision_model)

        text = (response.choices[0].message.content or "").strip().lower()
        for cand in ["food_diary", "riding_diary", "sleep_diary_morning", "sleep_diary_night"]:
            if cand in text:
                return cand
        return "unknown"



    # ---------- Sleep diary (image-based, circle selection aware) ----------
    def _sleep_diary_structure_from_image(self, img: Image.Image, mode: str) -> Dict[str, Any]:
        """mode in { 'sleep_diary_morning', 'sleep_diary_night' }.
        Use the page image to extract structured JSON. Handle circled options as the value for that field.
        """
        base64_img = self.ocr.encode_pil_image(img)
        if mode == "sleep_diary_morning":
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
            "- For circled/solid circles/selected options, treat them as selected and use them as the result value for that field. For coffee consumption, first identify the number of cups consumed, if the number is not 0, then the circles below represent the time period when these coffees were consumed, otherwise circles represent 0, meaning no coffee was consumed.\n"
            "- If multiple selections appear in the same field, use the most obvious/last selection; if unclear, list multiple values as a string.\n"
            "- Time format: HH:MM; Date format: YYYY-MM-DD (keep original if uncertain).\n"
             "- Output records for 7 days (Monday..Sunday) in table order。\n"
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
            "- For recognition results, the first word in each column is not necessarily the output result. Judge the final output result based on whether there is a nearby circle in this row. If there is a circle, use the word inside the circle as the output result, otherwise use null. If this row has numbers, output the numbers and use the content in the following circle as the unit of the output result\n"
            "- Output records for 7 days (Monday..Sunday) in table order, use null if missing.\n"
            "- Output all text content in English. Translate Chinese text to English equivalents.\n"
            "- Output only JSON that must conform to the following pattern:\n\n"
            f"Pattern: \n{schema}\n"
        )

        try:
            response = self.ocr._chat_with_image(base64_img, prompt, self.ocr.primary_vision_model)
        except Exception:
            response = self.ocr._chat_with_image(base64_img, prompt, self.ocr.fallback_vision_model)

        text = (response.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            text = text[first:last+1]
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {"category": mode, "raw": text}

    # ---------- Riding diary (image-based) ----------
    def _riding_diary_structure_from_image(self, img: Image.Image, mode: str) -> Dict[str, Any]:
        """Extract riding diary data directly from image."""
        base64_img = self.ocr.encode_pil_image(img)
        schema = (
            "{\n"
            "  \"category\": \"riding_diary\",\n"
            "  \"records\": [\n"
            "    { \"Day\": \"Monday|Tuesday|...\", \"Horses ridden\": \"string\", \"Falls\": \"string\", \"Trackwork\": \"string\", \"Gallops\": \"string\", \"Jumpouts\": \"string\", \"Trials\": \"string\", \"Races\": \"string\", \"Other eg. gym/run\": \"string\" }\n"
            "  ]\n"
            "}"
        )

        prompt = (
            "You are a riding diary form extraction assistant. This page is a riding diary table containing numbers, text, and check marks. Please combine OCR results with your own recognition to identify content in the image.\n"
            "Please perform error correction and standardization while considering the original layout (row/column alignment, headers, merged cells, etc.):\n"
            "- Carefully identify the days of the week (Monday/Tuesday/Wednesday/Thursday/Friday/Saturday/Sunday) in the table.\n"
            "- For numeric fields (such as Horses ridden, Falls, etc.), extract actual numbers; use '0' if empty. If this table records riding times or fall counts, output the actual riding times for the corresponding day of the week.\n"
            "- For text fields, extract actual content; use null if empty.\n"
            "- Output records for 7 days (Monday..Sunday) in table order, use null if missing.\n"
            "- Output all text content in English. Translate Chinese text to English equivalents.\n"
            "- Output only JSON that must conform to the following pattern:\n\n"
            f"Pattern: \n{schema}\n"
        )

        try:
            response = self.ocr._chat_with_image(base64_img, prompt, self.ocr.primary_vision_model)
        except Exception:
            response = self.ocr._chat_with_image(base64_img, prompt, self.ocr.fallback_vision_model)

        text = (response.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            text = text[first:last+1]
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {"category": mode, "raw": text}

    # ---------- Food diary (image-based) ----------
    def _food_diary_structure_from_image(self, img: Image.Image, mode: str) -> Dict[str, Any]:
        """Extract food diary data directly from image with English translation."""
        base64_img = self.ocr.encode_pil_image(img)
        schema = (
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
                "- Keep original spelling (e.g., \"Nutri grain\", \"Butter chicken\"), do not correct.\n"
                "- If unreadable or blank: leave array empty []; if uncertain reading, put the text in the array and record position with candidates in `uncertain`.\n"
                "- Each array element is an object: {\"text\":\"original text\",\"conf\":0-1}\n"
                "- uncertain format: [{\"path\":\"days.sunday.dinner[0].text\", \"reason\":\"unclear writing\", \"altCandidates\":[\"option1\", \"option2\"]}]"
            
        )

        prompt = (
            "You will perform OCR and structured extraction on a \"MASSEY UNIVERSITY / My Food Diary\" handwritten form.\n\n"
            "Output only a JSON following this structure and rules (no explanations):\n"
            f"{schema}\n\n"
            "Rules:\n"
            "- Read each cell under \"Breakfast / Snack / Lunch / Snack / Dinner / Snack\" (this table has three Snack columns, map them to snack1, snack2, snack3 respectively).\n"
            "- Keep original spelling but translate ALL Chinese food names to English equivalents (e.g., 香蕉 -> Banana, 黄油鸡 -> Butter chicken).\n"
            "- If unreadable or blank: leave array empty []; if uncertain reading, put the text in the array and record position with candidates in `uncertain`.\n"
            "- Each array element is an object: {\"text\":\"English food name\"}\n"
            "- uncertain format: [{\"path\":\"days.sunday.dinner[0].text\", \"reason\":\"unclear writing\", \"altCandidates\":[\"option1\", \"option2\"]}]\n"
            "- Output ALL content in English only.\n\n"
            "Now process this image (food diary): return JSON."
        )

        try:
            response = self.ocr._chat_with_image(base64_img, prompt, self.ocr.primary_vision_model)
        except Exception:
            response = self.ocr._chat_with_image(base64_img, prompt, self.ocr.fallback_vision_model)

        text = (response.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            text = text[first:last+1]
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {"category": mode, "raw": text}

    

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        start_time = time.time()
        print(f"📄 Starting PDF processing: {os.path.basename(pdf_path)}")
        print(f"🔧 Using seed: {self.seed} (for reproducibility)")
        
        images = self._render_pdf_pages(pdf_path)
        self.stats["total_pages"] = len(images)
        print(f"📖 Found {len(images)} pages")
        
        page_results: List[Dict[str, Any]] = []

        # Use progress bar to show processing progress
        with tqdm(total=len(images), desc="Processing pages", unit="page") as pbar:
            for idx, img in enumerate(images, start=1):
                page_start_time = time.time()
                pbar.set_description(f"Processing page {idx}")
                
                try:
                    # Step 1: classify category on original image
                    print(f"\n🔍 Page {idx}: Identifying page type...")
                    category = self._classify_page(img)
                    print(f"   Classification result: {category}")

                    # If sleep diary, rotate 90 degrees clockwise, then re-classify
                    rotated_img = img
                    if category.startswith("sleep_diary") or category == "unknown":
                        print(f"   Rotating page for re-classification...")
                        rotated_img = img.rotate(-90, expand=True)
                        cat2 = self._classify_page(rotated_img)
                        if cat2 in {"sleep_diary_morning", "sleep_diary_night"}:
                            category = cat2
                            print(f"   Post-rotation classification: {category}")
                        # else keep previous category (could remain unknown)

                    # Step 2: extract structured data according to category
                    print(f"   Extracting structured data...")
                    if category in {"sleep_diary_morning", "sleep_diary_night"}:
                        structured = self._sleep_diary_structure_from_image(rotated_img, category)
                        raw_text = None
                    elif category == "food_diary":
                        # food_diary also needs image-based extraction for better English translation
                        structured = self._food_diary_structure_from_image(img, category)
                        raw_text = None
                    elif category == "riding_diary":
                        # riding_diary also needs image-based extraction like sleep_diary
                        structured = self._riding_diary_structure_from_image(img, category)
                        raw_text = None
                 

                    page_results.append({
                        "page": idx,
                        "category": category,
                        "raw_text": raw_text,
                        "structured": structured
                    })
                    
                    # Update statistics
                    self.stats["successful_pages"] += 1
                    self.stats["category_counts"][category] = self.stats["category_counts"].get(category, 0) + 1
                    
                    page_time = time.time() - page_start_time
                    self.stats["processing_times"].append(page_time)
                    
                    print(f"   ✅ Page {idx} completed (time: {page_time:.2f}s)")
                    
                except Exception as e:
                    print(f"   ❌ Page {idx} failed: {str(e)}")
                    self.stats["failed_pages"] += 1
                    page_results.append({
                        "page": idx,
                        "category": "error",
                        "raw_text": None,
                        "structured": {"error": str(e)}
                    })
                
                pbar.update(1)
                time.sleep(0.1)  # Small delay for clearer progress bar

        # Calculate final statistics
        total_time = time.time() - start_time
        avg_time = sum(self.stats["processing_times"]) / len(self.stats["processing_times"]) if self.stats["processing_times"] else 0
        
        print(f"\n📊 Processing completed! Total time: {total_time:.2f}s")
        print(f"📈 Success: {self.stats['successful_pages']}/{self.stats['total_pages']} pages")
        print(f"📈 Failed: {self.stats['failed_pages']} pages")
        print(f"📈 Average time per page: {avg_time:.2f}s")
        print(f"📈 Page category statistics: {self.stats['category_counts']}")
        
        return {
            "source_pdf": os.path.basename(pdf_path),
            "page_count": len(images),
            "category_summary": self.stats["category_counts"],
            "processing_stats": {
                "total_time": total_time,
                "avg_time_per_page": avg_time,
                "successful_pages": self.stats["successful_pages"],
                "failed_pages": self.stats["failed_pages"],
                "seed_used": self.seed
            },
            "pages": page_results,
        }


def export_diary_to_json(pdf_path: str, output_json_path: str, dpi: int = 200, language: str = "zh", seed: int = 42) -> str:
    extractor = DiaryExtractor(dpi=dpi, language=language, seed=seed)
    result = extractor.extract_from_pdf(pdf_path)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return output_json_path


if __name__ == "__main__":
    import argparse
    import sys
    
    # Default PDF file path
    DEFAULT_PDF = "JockeyDiaries230725.pdf"
    
    parser = argparse.ArgumentParser(description="Extract diary PDF to structured JSON.")
    parser.add_argument("pdf", nargs='?', default=DEFAULT_PDF, 
                       help=f"Path to PDF, default: {DEFAULT_PDF}")
    parser.add_argument("--out", default=None, help="Output JSON path, default same name with .json suffix")
    parser.add_argument("--dpi", type=int, default=200, help="Render DPI for PDF pages")
    parser.add_argument("--lang", default="zh", help="OCR/LLM language, default zh")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility, default 42")
    
    # If no arguments provided, use default values
    if len(sys.argv) == 1:
        print(f"🚀 Running with default parameters...")
        print(f"📄 PDF file: {DEFAULT_PDF}")
        print(f"🔧 Seed: 42")
        print(f"🌐 Language: zh")
        print(f"📐 DPI: 200")
        print("-" * 50)
        
        pdf_path = DEFAULT_PDF
        out_path = os.path.splitext(pdf_path)[0] + ".json"
        dpi = 200
        language = "zh"
        seed = 42
    else:
        args = parser.parse_args()
        pdf_path = args.pdf
        out_path = args.out or os.path.splitext(pdf_path)[0] + ".json"
        dpi = args.dpi
        language = args.lang
        seed = args.seed

    # Check if PDF file exists
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        print(f"💡 Please ensure the file is in the current directory or provide the correct file path")
        sys.exit(1)

    try:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        export_diary_to_json(pdf_path, out_path, dpi=dpi, language=language, seed=seed)
        print(f"✅ Output file: {out_path}")
    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")
        sys.exit(1)


