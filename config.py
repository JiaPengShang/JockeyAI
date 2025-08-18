import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API Configuration
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
