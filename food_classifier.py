import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pickle
import json
from config import FOOD_CATEGORIES

class FoodClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.categories = list(FOOD_CATEGORIES.keys())
        self.model_trained = False
    
    def prepare_training_data(self):
        """Prepare training data"""
        training_data = []
        training_labels = []
        
        # Add samples for each category
        for category, foods in FOOD_CATEGORIES.items():
            for food in foods:
                training_data.append(food)
                training_labels.append(category)
        
        # Additional samples (English)
        additional_data = {
            "Protein": ["chicken breast", "steak", "salmon", "tuna", "shrimp", "crab", "shellfish", "lean meat", "turkey"],
            "Carbohydrates": ["white rice", "brown rice", "pasta", "steamed bun", "dumpling", "noodles", "porridge", "corn porridge"],
            "Fat": ["peanut oil", "canola oil", "sesame oil", "lard", "mutton fat", "duck fat", "goose fat"],
            "Vitamins": ["apple", "banana", "grape", "strawberry", "blueberry", "kiwi", "mango", "pineapple"],
            "Minerals": ["calcium tablets", "iron tablets", "zinc tablets", "magnesium", "potassium", "sodium", "phosphorus"],
            "Fiber": ["oatmeal", "buckwheat", "quinoa", "millet", "black rice", "purple rice", "job's tears"]
        }
        
        for category, foods in additional_data.items():
            for food in foods:
                training_data.append(food)
                training_labels.append(category)
        
        return training_data, training_labels
    
    def train_model(self):
        """Train classifier"""
        print("Preparing training data...")
        training_data, training_labels = self.prepare_training_data()
        
        print("Vectorizing text...")
        X = self.vectorizer.fit_transform(training_data)
        
        print("Training model...")
        self.classifier.fit(X, training_labels)
        
        # Evaluate
        y_pred = self.classifier.predict(X)
        accuracy = accuracy_score(training_labels, y_pred)
        print(f"Model trained, accuracy: {accuracy:.2f}")
        
        self.model_trained = True
        
        # Save model
        self.save_model()
    
    def classify_food(self, food_name):
        """Classify a single food"""
        if not self.model_trained:
            self.train_model()
        
        # Vectorize input
        X = self.vectorizer.transform([food_name])
        
        # Predict
        prediction = self.classifier.predict(X)[0]
        probabilities = self.classifier.predict_proba(X)[0]
        
        # Confidence
        confidence = max(probabilities)
        
        return {
            "food_name": food_name,
            "category": prediction,
            "confidence": confidence,
            "probabilities": dict(zip(self.categories, probabilities))
        }
    
    def classify_multiple_foods(self, food_list):
        """Classify multiple foods"""
        results = []
        for food in food_list:
            result = self.classify_food(food)
            results.append(result)
        return results
    
    def save_model(self):
        """Save model"""
        model_data = {
            "vectorizer": self.vectorizer,
            "classifier": self.classifier,
            "categories": self.categories
        }
        with open("food_classifier_model.pkl", "wb") as f:
            pickle.dump(model_data, f)
        print("Model saved")
    
    def load_model(self):
        """Load model"""
        try:
            with open("food_classifier_model.pkl", "rb") as f:
                model_data = pickle.load(f)
            
            self.vectorizer = model_data["vectorizer"]
            self.classifier = model_data["classifier"]
            self.categories = model_data["categories"]
            self.model_trained = True
            print("Model loaded")
            return True
        except FileNotFoundError:
            print("Model file not found, retraining...")
            return False
    
    def get_nutrition_info(self, food_name, quantity=100):
        """Get nutrition info (mock database)"""
        nutrition_database = {
            "chicken": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
            "beef": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15, "fiber": 0},
            "fish": {"calories": 120, "protein": 22, "carbs": 0, "fat": 4, "fiber": 0},
            "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0},
            "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4},
            "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7},
            "milk": {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1, "fiber": 0},
            "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4},
            "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6},
            "carrot": {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2, "fiber": 2.8}
        }
        
        # Find best match
        best_match = None
        best_score = 0
        
        for food in nutrition_database.keys():
            if food_name in food or food in food_name:
                score = len(set(food_name) & set(food)) / len(set(food_name) | set(food))
                if score > best_score:
                    best_score = score
                    best_match = food
        
        if best_match and best_score > 0.3:
            nutrition = nutrition_database[best_match].copy()
            # Scale by quantity
            ratio = quantity / 100
            for key in nutrition:
                nutrition[key] = round(nutrition[key] * ratio, 2)
            return nutrition
        else:
            # Default nutrition
            return {
                "calories": 100,
                "protein": 5,
                "carbs": 15,
                "fat": 3,
                "fiber": 2
            }
