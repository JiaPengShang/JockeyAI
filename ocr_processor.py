import base64
import io
import requests
from PIL import Image
import openai
from config import OPENAI_API_KEY

class OCRProcessor:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.primary_vision_model = "gpt-4o-mini"
        self.fallback_vision_model = "gpt-4o"

    def encode_image(self, image_path):
        """将图片编码为base64格式"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def encode_pil_image(self, image):
        """将PIL图片编码为base64格式"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

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

    def extract_text_from_image(self, image, language="zh"):
        """Extract text from image via OpenAI multimodal vision model."""
        try:
            if isinstance(image, str):
                base64_image = self.encode_image(image)
            else:
                base64_image = self.encode_pil_image(image)

            if language.lower() == "en":
                prompt = (
                    "Please recognize all textual content in this image, including food names, nutrition facts, and quantities. "
                    "Answer in English and use the following format strictly:\n\n"
                    "Food Name:\nNutrition Facts:\nQuantity/Weight:\nOther Info:"
                )
            else:
                prompt = (
                    f"请识别这张图片中的所有文字内容，包括食物名称、营养成分、数量等信息。"
                    f"请用{language}回答，并按照以下格式输出：\n\n食物名称：\n营养成分：\n数量/重量：\n其他信息："
                )

            try:
                response = self._chat_with_image(base64_image, prompt, self.primary_vision_model)
            except Exception as e:
                # 当主模型不可用（如404/下线）时，自动切换到备用模型
                response = self._chat_with_image(base64_image, prompt, self.fallback_vision_model)

            return response.choices[0].message.content

        except Exception as e:
            return f"OCR failed: {str(e)}"

    def analyze_food_content(self, text, language: str = "en"):
        """Analyze extracted text and return structured food and nutrition info.

        Always returns English JSON keys. If language='en', content is expected in English.
        """
        try:
            prompt_user = (
                "Analyze the following text and return ONLY a strict JSON object. "
                "Use English labels and numbers where appropriate. Do not include code fences, comments, or extra text.\n\n"
                f"INPUT:\n{text}\n\n"
                "RESPONSE JSON SCHEMA (keys and types must match):\n"
                "{\n"
                "  \"foods\": [\n"
                "    {\n"
                "      \"name\": \"string\",\n"
                "      \"category\": \"Protein|Carbohydrates|Fat|Vitamins|Minerals|Fiber|Other\",\n"
                "      \"quantity\": \"string\",\n"
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
                "}"
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
            return f"Food analysis failed: {str(e)}"
