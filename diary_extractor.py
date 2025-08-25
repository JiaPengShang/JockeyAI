import os
import json
from typing import List, Dict, Any
import fitz  # PyMuPDF
from PIL import Image
import io

from ocr_processor import OCRProcessor


class DiaryExtractor:
    def __init__(self, dpi: int = 200, language: str = "zh"):
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

    def _llm_clean_and_structure(self, raw_text: str) -> Dict[str, Any]:
        prompt = (
            "你是一名数据清洗与信息抽取助手。请对下列日记OCR文本进行纠错、去噪、实体标准化，\n"
            "抽取结构化字段并仅以JSON对象输出，不要包含多余文字或代码块。\n\n"
            "要求：\n"
            "- 修正常见OCR错误（断词、标点、错别字）。\n"
            "- 识别日期、时间、餐次（如早餐/午餐/晚餐/加餐）、食品与数量、单位、补充备注。\n"
            "- 对无法确定的数值给出null并保留原文本到notes。\n"
            "- 仅输出一个JSON对象，键必须符合下述模式。\n\n"
            "JSON模式：\n"
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
            f"待处理文本：\n{raw_text}"
        )

        # 复用 OCRProcessor 中的 OpenAI 客户端
        client = self.ocr.client
        model = self.ocr.primary_vision_model
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是严谨的数据工程助手，只输出合法的JSON。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
            )
        except Exception:
            response = client.chat.completions.create(
                model=self.ocr.fallback_vision_model,
                messages=[
                    {"role": "system", "content": "你是严谨的数据工程助手，只输出合法的JSON。"},
                    {"role": "user", "content": prompt},
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
            raw = self.ocr.extract_text_from_image(img, language=self.language)
            structured = self._llm_clean_and_structure(raw)
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


def export_diary_to_json(pdf_path: str, output_json_path: str, dpi: int = 200, language: str = "zh") -> str:
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
    parser.add_argument("--lang", default="zh", help="OCR/LLM language, default zh")
    args = parser.parse_args()

    pdf_path = args.pdf
    out_path = args.out or os.path.splitext(pdf_path)[0] + ".json"

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    export_diary_to_json(pdf_path, out_path, dpi=args.dpi, language=args.lang)
    print(out_path)


