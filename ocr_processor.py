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
        
        # 验证API密钥
        self._validate_api_key()
    
    def _validate_api_key(self):
        """验证OpenAI API密钥是否有效"""
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            raise ValueError("OpenAI API密钥未设置。请在config.py中设置有效的API密钥。")
        
        try:
            # 尝试调用一个简单的API来验证密钥
            self.client.models.list()
        except Exception as e:
            if "invalid_api_key" in str(e).lower() or "401" in str(e):
                raise ValueError("OpenAI API密钥无效或已过期。请检查您的API密钥设置。")
            elif "quota" in str(e).lower() or "billing" in str(e).lower():
                raise ValueError("OpenAI账户配额已用完或余额不足。请检查您的账户状态。")
            else:
                raise e

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
                    "Please carefully read and extract ALL text content from this image. "
                    "Focus on identifying food names, nutrition facts, ingredients, quantities, and any nutritional information. "
                    "Be thorough and accurate in your transcription. "
                    "Answer in English and use the following format:\n\n"
                    "Food Names:\nNutrition Facts:\nIngredients:\nQuantities/Weights:\nOther Information:"
                )
            else:
                prompt = (
                    f"请仔细阅读并提取这张图片中的所有文字内容。"
                    f"重点关注食物名称、营养成分、配料、数量等营养信息。"
                    f"请全面准确地转录所有文字内容。"
                    f"请用{language}回答，并按照以下格式输出：\n\n"
                    f"食物名称：\n营养成分：\n配料：\n数量/重量：\n其他信息："
                )

            try:
                response = self._chat_with_image(base64_image, prompt, self.primary_vision_model)
            except Exception as e:
                # 当主模型不可用（如404/下线）时，自动切换到备用模型
                response = self._chat_with_image(base64_image, prompt, self.fallback_vision_model)

            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                return "OCR失败：API密钥无效或已过期。请检查您的OpenAI API密钥设置。"
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return "OCR失败：API配额已用完或账户余额不足。请检查您的OpenAI账户状态。"
            else:
                return f"OCR失败：{error_msg}"

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
                return "食物分析失败：API密钥无效或已过期。请检查您的OpenAI API密钥设置。"
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return "食物分析失败：API配额已用完或账户余额不足。请检查您的OpenAI账户状态。"
            else:
                return f"食物分析失败：{error_msg}"
