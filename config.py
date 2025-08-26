import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 如果没有设置环境变量，使用默认值（需要用户更新）
if not OPENAI_API_KEY:
    OPENAI_API_KEY = "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"

# Food Classification Configuration
FOOD_CATEGORIES = {
    "Protein": ["chicken", "beef", "fish", "eggs", "tofu", "beans", "nuts", "dairy"],
    "Carbohydrates": ["rice", "bread", "noodles", "potatoes", "corn", "oats", "fruits", "vegetables"],
    "Fat": ["olive oil", "avocado", "nuts", "cheese", "butter", "coconut oil"],
    "Vitamins": ["carrots", "spinach", "broccoli", "oranges", "lemons", "tomatoes", "bell peppers"],
    "Minerals": ["milk", "yogurt", "spinach", "nuts", "whole grains", "seafood"],
    "Fiber": ["whole grains", "beans", "vegetables", "fruits", "nuts", "seeds"]
}

# Nutrition Targets Configuration (Jockey Specific)
NUTRITION_TARGETS = {
    "Weight Management": {
        "Calories": {"target": 2000, "unit": "kcal/day"},
        "Protein": {"target": 120, "unit": "g/day"},
        "Carbohydrates": {"target": 200, "unit": "g/day"},
        "Fat": {"target": 60, "unit": "g/day"},
        "Fiber": {"target": 25, "unit": "g/day"}
    },
    "Energy Boost": {
        "Calories": {"target": 2500, "unit": "kcal/day"},
        "Protein": {"target": 150, "unit": "g/day"},
        "Carbohydrates": {"target": 300, "unit": "g/day"},
        "Fat": {"target": 80, "unit": "g/day"},
        "Fiber": {"target": 30, "unit": "g/day"}
    }
}

# Application Configuration
APP_CONFIG = {
    "title": "Jockey Nutrition AI",
    "page_icon": "🏇",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}
