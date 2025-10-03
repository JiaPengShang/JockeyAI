import base64
import io
import requests
from PIL import Image
import openai
import os
import config as cfg

class OCRProcessor:
    def __init__(self):
        # Read latest API key dynamically (supports runtime updates from UI)
        api_key = os.getenv("OPENAI_API_KEY") or getattr(cfg, "OPENAI_API_KEY", "")
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.primary_vision_model = "gpt-4o-mini"
        self.fallback_vision_model = "gpt-4o"
        
        # Validate API key
        self._validate_api_key()
    
    def _validate_api_key(self):
        """Validate if OpenAI API key is valid"""
        current_key = os.getenv("OPENAI_API_KEY") or getattr(cfg, "OPENAI_API_KEY", "")
        if not current_key:
            raise ValueError("OpenAI API key not set. Please set environment variable OPENAI_API_KEY or create .env file.")
        
        try:
            # Try to call a simple API to validate the key
            self.client.models.list()
        except Exception as e:
            if "invalid_api_key" in str(e).lower() or "401" in str(e):
                raise ValueError("OpenAI API key is invalid or expired. Please check your API key settings.")
            elif "quota" in str(e).lower() or "billing" in str(e).lower():
                raise ValueError("OpenAI account quota exceeded or insufficient balance. Please check your account status.")
            else:
                raise e

    def encode_image(self, image_path):
        """Encode image to base64 format"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def encode_pil_image(self, image):
        """Encode PIL image to base64 format"""
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
                    f"Please carefully read and extract ALL text content from this image. "
                    f"Focus on identifying food names, nutrition facts, ingredients, quantities, and any nutritional information. "
                    f"Be thorough and accurate in your transcription. "
                    f"Answer in {language} and use the following format:\n\n"
                    f"Food Names:\nNutrition Facts:\nIngredients:\nQuantities/Weights:\nOther Information:"
                )

            try:
                response = self._chat_with_image(base64_image, prompt, self.primary_vision_model)
            except Exception as e:
                # When primary model is unavailable (e.g., 404/offline), automatically switch to fallback model
                response = self._chat_with_image(base64_image, prompt, self.fallback_vision_model)

            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                return "OCR failed: API key is invalid or expired. Please check your OpenAI API key settings."
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return "OCR failed: API quota exceeded or insufficient account balance. Please check your OpenAI account status."
            else:
                return f"OCR failed: {error_msg}"

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
                return "Food analysis failed: API key is invalid or expired. Please check your OpenAI API key settings."
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return "Food analysis failed: API quota exceeded or insufficient account balance. Please check your OpenAI account status."
            else:
                return f"Food analysis failed: {error_msg}"
