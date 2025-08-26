import base64
import io
import os
import shutil
import subprocess
import tempfile
import requests
from PIL import Image
import fitz  # PyMuPDF
import openai
from config import OPENAI_API_KEY

class OCRProcessor:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.primary_vision_model = "gpt-4o-mini"
        self.fallback_vision_model = "gpt-4o"
        # OCRmyPDF availability
        self.ocrmypdf_path = shutil.which("ocrmypdf")
        self.ocrmypdf_available = self.ocrmypdf_path is not None
        
        # Validate API key
        self._validate_api_key()
    
    def _validate_api_key(self):
        """Validate that OpenAI API key is usable"""
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            raise ValueError("OpenAI API key not set. Please set a valid key in config.py.")
        
        try:
            # Try a simple call to validate key
            self.client.models.list()
        except Exception as e:
            if "invalid_api_key" in str(e).lower() or "401" in str(e):
                raise ValueError("OpenAI API key is invalid or expired. Please check your key.")
            elif "quota" in str(e).lower() or "billing" in str(e).lower():
                raise ValueError("OpenAI account quota exceeded or billing issue. Please check your account.")
            else:
                raise e

    def encode_image(self, image_path):
        """Encode image file to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def encode_pil_image(self, image):
        """Encode PIL image to base64"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def _map_language_to_tesseract(self, language: str) -> str:
        """Map general language code to Tesseract language code."""
        if not language:
            return "eng"
        lang = language.lower().replace("_", "-")
        if lang in ("zh", "zh-cn", "zh-hans", "zh-simplified", "zh-hans-cn"):
            return "chi_sim"
        if lang in ("zh-tw", "zh-hant", "zh-traditional"):
            return "chi_tra"
        if lang.startswith("en"):
            return "eng"
        # 透传其他可能已是 tesseract 的语言码（如 deu, fra 等）
        return lang

    def _chat_with_image(self, base64_image: str, prompt_text: str, model: str):
        return self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                    ],
                }
            ],
            max_tokens=1000,
        )

    def extract_text_from_image(self, image, language="en", prefer_ocrmypdf: bool = False):
        """Extract text from an image.

        - If prefer_ocrmypdf=True and ocrmypdf exists, use ocrmypdf; otherwise use OpenAI vision.
        """
        # Prefer ocrmypdf (optional)
        if prefer_ocrmypdf and self.ocrmypdf_available:
            try:
                with tempfile.TemporaryDirectory() as td:
                    # Save input image to a temp file if needed
                    if isinstance(image, str) and os.path.exists(image):
                        input_img_path = image
                        cleanup_input = False
                    else:
                        input_img_fd, input_img_path = tempfile.mkstemp(suffix=".png", dir=td)
                        os.close(input_img_fd)
                        if isinstance(image, Image.Image):
                            image.save(input_img_path, format="PNG")
                        else:
                            # Assume binary or BytesIO
                            if hasattr(image, "read"):
                                data = image.read()
                            else:
                                data = image
                            with open(input_img_path, "wb") as f:
                                f.write(data)
                        cleanup_input = True

                    # Use ocrmypdf to create searchable PDF
                    output_pdf_path = os.path.join(td, "output.pdf")
                    tesseract_lang = self._map_language_to_tesseract(language)
                    cmd = [self.ocrmypdf_path or "ocrmypdf", "-l", tesseract_lang, input_img_path, output_pdf_path]
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    # Extract text from output PDF
                    with fitz.open(output_pdf_path) as doc:
                        texts = [page.get_text() for page in doc]
                    return "\n".join(texts).strip()
            except Exception:
                # Fallback to OpenAI
                pass

        # OpenAI vision fallback
        try:
            if isinstance(image, str):
                base64_image = self.encode_image(image)
            else:
                base64_image = self.encode_pil_image(image)

            if language.lower() == "en":
                prompt = (
                    "Please carefully read and extract ALL text content from this image. "
                    "Focus on identifying food names, nutrition facts, ingredients, quantities, and any nutritional information. "
                    "Be thorough and accurate in your transcription. "
                    "Answer in English and use the following format:\n\n"
                    "Food Names:\nNutrition Facts:\nIngredients:\nQuantities/Weights:\nOther Information:"
                )
            else:
                prompt = (
                    "Please carefully read and extract ALL text content from this image. "
                    "Focus on food names, nutrition facts, ingredients, quantities, and any nutritional information. "
                    "Be thorough and accurate in your transcription. "
                    "Answer in English and use the following format:\n\n"
                    "Food Names:\nNutrition Facts:\nIngredients:\nQuantities/Weights:\nOther Information:"
                )

            try:
                response = self._chat_with_image(base64_image, prompt, self.primary_vision_model)
            except Exception:
                response = self._chat_with_image(base64_image, prompt, self.fallback_vision_model)

            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                return "OCR failed: API key invalid or expired."
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return "OCR failed: quota exceeded or billing issue."
            else:
                return f"OCR failed: {error_msg}"

    def extract_text_from_pdf(self, pdf_input, language: str = "en", prefer_ocrmypdf: bool = True) -> str:
        """Extract text from a PDF.

        - Prefer ocrmypdf + text layer; fallback to render to images + OpenAI.
        - pdf_input can be filepath, bytes, BytesIO, or any object with read().
        """
        # Prepare temp input PDF path
        temp_dir = tempfile.TemporaryDirectory()
        input_pdf_path = None
        try:
            if isinstance(pdf_input, str) and os.path.exists(pdf_input):
                input_pdf_path = pdf_input
            else:
                data = None
                if isinstance(pdf_input, (bytes, bytearray)):
                    data = bytes(pdf_input)
                elif hasattr(pdf_input, "read"):
                    data = pdf_input.read()
                if not data:
                    raise ValueError("Invalid PDF input.")
                input_pdf_path = os.path.join(temp_dir.name, "input.pdf")
                with open(input_pdf_path, "wb") as f:
                    f.write(data)

            # Prefer ocrmypdf
            if prefer_ocrmypdf and self.ocrmypdf_available:
                try:
                    output_pdf_path = os.path.join(temp_dir.name, "output.pdf")
                    tesseract_lang = self._map_language_to_tesseract(language)
                    cmd = [self.ocrmypdf_path or "ocrmypdf", "-l", tesseract_lang, input_pdf_path, output_pdf_path]
                    # On Windows, same invocation; requires Tesseract and Ghostscript installed
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    # Extract text directly from output PDF
                    with fitz.open(output_pdf_path) as doc:
                        texts = [page.get_text() for page in doc]
                    return "\n".join(texts).strip()
                except Exception:
                    # Fallback to OpenAI
                    pass

            # Fallback: render each page to image and use OpenAI vision
            return self._extract_text_from_pdf_via_openai(input_pdf_path, language)
        finally:
            try:
                temp_dir.cleanup()
            except Exception:
                pass

    def _extract_text_from_pdf_via_openai(self, pdf_path: str, language: str) -> str:
        """Fallback: render PDF pages to images and call OpenAI vision OCR."""
        texts = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                # Render page to image
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                page_text = self.extract_text_from_image(image, language=language, prefer_ocrmypdf=False)
                texts.append(page_text)
        return "\n".join(texts).strip()

    def analyze_food_content(self, text, language: str = "en"):
        """Analyze extracted text and return structured food and nutrition info.

        Always returns English JSON keys. If language='en', content is expected in English.
        """
        try:
            prompt_user = (
                "Analyze the following text and extract ALL food items and nutritional information. "
                "Return ONLY a valid JSON object. Use English labels and numbers where appropriate. "
                "Do not include code fences, comments, or extra text.\n\n"
                f"INPUT TEXT:\n{text}\n\n"
                "RESPONSE JSON SCHEMA (keys and types must match exactly):\n"
                "{\n"
                "  \"foods\": [\n"
                "    {\n"
                "      \"name\": \"string (food name)\",\n"
                "      \"category\": \"Protein|Carbohydrates|Fat|Vitamins|Minerals|Fiber|Other\",\n"
                "      \"quantity\": \"string (amount/weight)\",\n"
                "      \"calories\": number,\n"
                "      \"protein\": number,\n"
                "      \"carbs\": number,\n"
                "      \"fat\": number\n"
                "    }\n"
                "  ],\n"
                "  \"total_calories\": number,\n"
                "  \"total_protein\": number,\n"
                "  \"total_carbs\": number,\n"
                "  \"total_fat\": number\n"
                "}\n\n"
                "IMPORTANT: Extract ALL food items mentioned in the text. If no specific nutritional values are given, estimate reasonable values based on typical food composition."
            )

            try:
                response = self.client.chat.completions.create(
                    model=self.primary_vision_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a nutrition analyst. Identify foods, quantities, and macronutrients. "
                                "Respond with JSON only."
                            ),
                        },
                        {"role": "user", "content": prompt_user},
                    ],
                    max_tokens=1000,
                )
            except Exception:
                response = self.client.chat.completions.create(
                    model=self.fallback_vision_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a nutrition analyst. Identify foods, quantities, and macronutrients. "
                                "Respond with JSON only."
                            ),
                        },
                        {"role": "user", "content": prompt_user},
                    ],
                    max_tokens=1000,
                )

            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                return "Food analysis failed: API key invalid or expired."
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return "Food analysis failed: quota exceeded or billing issue."
            else:
                return f"Food analysis failed: {error_msg}"
