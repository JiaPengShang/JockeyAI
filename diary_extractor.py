import os
import json
from typing import List, Dict, Any
import fitz  # PyMuPDF
from PIL import Image
import io

from ocr_processor import OCRProcessor


class DiaryExtractor:
    def __init__(self, dpi: int = 200, language: str = "en"):
        self.dpi = dpi
        self.language = language
        self.ocr = OCRProcessor()

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

    def _ensure_landscape(self, image: Image.Image) -> Image.Image:
        """Rotate counterclockwise 90 degrees if the image is portrait (height > width)."""
        try:
            if image.height > image.width:
                return image.rotate(90, expand=True)
            return image
        except Exception:
            return image

    def _llm_clean_and_structure(self, raw_text: str, image: Image.Image) -> Dict[str, Any]:
        """Send both OCR text and the original page image to the model for correction and structuring."""
        prompt_text = (
            "You are a data cleaning and extraction assistant. Clean the OCR text using the page image as reference: fix OCR errors, denoise, standardize entities, and extract structured fields.\n"
            "Output ONLY one JSON object, no extra text or code fences.\n\n"
            "Requirements:\n"
            "- Prefer the OCR text, but verify with the image for numbers, units, and table alignment.\n"
            "- Identify date, time, meal_type (breakfast|lunch|dinner|snack|other), and items with quantity, unit, and notes.\n"
            "- Use null for unknown values and keep ambiguous raw text in notes.\n"
            "- Keys must follow the schema below.\n\n"
            "JSON schema:\n"
            "{\n"
            "  \"entries\": [\n"
            "    {\n"
            "      \"date\": \"YYYY-MM-DD\",\n"
            "      \"time\": \"HH:MM\" | null,\n"
            "      \"meal_type\": \"breakfast|lunch|dinner|snack|other\",\n"
            "      \"items\": [\n"
            "        {\n"
            "          \"name\": \"string\",\n"
            "          \"quantity\": \"string\" | null,\n"
            "          \"unit\": \"string\" | null,\n"
            "          \"notes\": \"string\" | null\n"
            "        }\n"
            "      ],\n"
            "      \"notes\": \"string\" | null\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"OCR_TEXT:\n{raw_text}\n\nUse the attached page image to correct errors."
        )

        # Reuse OpenAI client from OCRProcessor
        client = self.ocr.client
        model = self.ocr.primary_vision_model
        base64_image = self.ocr.encode_pil_image(image)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a rigorous data engineering assistant. Output valid JSON only."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        ],
                    },
                ],
                max_tokens=2000,
            )
        except Exception:
            response = client.chat.completions.create(
                model=self.ocr.fallback_vision_model,
                messages=[
                    {"role": "system", "content": "You are a rigorous data engineering assistant. Output valid JSON only."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        ],
                    },
                ],
                max_tokens=2000,
            )

        text = response.choices[0].message.content or ""
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            text = text[first:last+1]
        try:
            return json.loads(text)
        except Exception:
            return {"entries": [], "raw": raw_text}

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        images = self._render_pdf_pages(pdf_path)
        page_results: List[Dict[str, Any]] = []

        for idx, img in enumerate(images, start=1):
            corrected_img = self._ensure_landscape(img)
            # Prefer ocrmypdf for OCR if available
            raw = self.ocr.extract_text_from_image(corrected_img, language=self.language, prefer_ocrmypdf=True)
            structured = self._llm_clean_and_structure(raw, corrected_img)
            page_results.append({
                "page": idx,
                "raw_text": raw,
                "structured": structured
            })

        # 合并页级结构
        merged_entries: List[Dict[str, Any]] = []
        for r in page_results:
            s = r.get("structured") or {}
            entries = s.get("entries") or []
            if isinstance(entries, list):
                merged_entries.extend(entries)

        return {
            "source_pdf": os.path.basename(pdf_path),
            "page_count": len(images),
            "entries": merged_entries,
            "pages": page_results,
        }


def export_diary_to_json(pdf_path: str, output_json_path: str, dpi: int = 200, language: str = "en") -> str:
    extractor = DiaryExtractor(dpi=dpi, language=language)
    result = extractor.extract_from_pdf(pdf_path)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return output_json_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract diary PDF to structured JSON.")
    parser.add_argument("pdf", help="Path to PDF, e.g., JockeyDiaries230725.pdf")
    parser.add_argument("--out", default=None, help="Output JSON path, default same name with .json suffix")
    parser.add_argument("--dpi", type=int, default=200, help="Render DPI for PDF pages")
    parser.add_argument("--lang", default="en", help="OCR/LLM language, default en")
    args = parser.parse_args()

    pdf_path = args.pdf
    out_path = args.out or os.path.splitext(pdf_path)[0] + ".json"

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    export_diary_to_json(pdf_path, out_path, dpi=args.dpi, language=args.lang)
    print(out_path)


