import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from config import NUTRITION_TARGETS
from food_classifier import FoodClassifier

class NutritionAnalyzer:
    def __init__(self):
        self.food_classifier = FoodClassifier()
        self.nutrition_targets = NUTRITION_TARGETS
    
    def analyze_meal(self, foods_data):
        """Analyze nutrition content of a meal"""
        total_nutrition = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0
        }
        
        analyzed_foods = []
        
        for food in foods_data:
            # Get food classification
            classification = self.food_classifier.classify_food(food["name"])
            
            # Get nutrition information
            nutrition = self.food_classifier.get_nutrition_info(
                food["name"], 
                food.get("quantity", 100)
            )
            
            # Add to total nutrition
            for key in total_nutrition:
                total_nutrition[key] += nutrition.get(key, 0)
            
            # Save analysis results
            analyzed_food = {
                "name": food["name"],
                "quantity": food.get("quantity", 100),
                "category": classification["category"],
                "confidence": classification["confidence"],
                "nutrition": nutrition
            }
            analyzed_foods.append(analyzed_food)
        
        return {
            "foods": analyzed_foods,
            "total_nutrition": total_nutrition
        }
    
    def compare_with_targets(self, nutrition_data, target_type="Weight Management"):
        """Compare with target nutrition"""
        targets = self.nutrition_targets.get(target_type, self.nutrition_targets["Weight Management"])
        
        comparison = {}
        for nutrient, target_info in targets.items():
            if nutrient in nutrition_data:
                actual = nutrition_data[nutrient]
                target = target_info["target"]
                unit = target_info["unit"]
                
                percentage = (actual / target) * 100 if target > 0 else 0
                
                comparison[nutrient] = {
                    "actual": actual,
                    "target": target,
                    "unit": unit,
                    "percentage": percentage,
                    "status": "Normal" if 80 <= percentage <= 120 else "Insufficient" if percentage < 80 else "Excessive"
                }
        
        return comparison
    
    def generate_recommendations(self, analysis_result, target_type="Weight Management"):
        """Generate nutrition recommendations"""
        comparison = self.compare_with_targets(analysis_result["total_nutrition"], target_type)
        
        recommendations = []
        
        # Analyze each nutrient
        for nutrient, data in comparison.items():
            if data["status"] == "Insufficient":
                recommendations.append(f"Recommend increasing {nutrient} intake, current intake {data['actual']:.1f}{data['unit']}, target {data['target']}{data['unit']}")
            elif data["status"] == "Excessive":
                recommendations.append(f"Recommend reducing {nutrient} intake, current intake {data['actual']:.1f}{data['unit']}, target {data['target']}{data['unit']}")
        
        # Jockey-specific recommendations
        jockey_recommendations = [
            "Jockeys need to maintain lightweight, recommend controlling total calorie intake",
            "Protein intake is important for muscle maintenance, recommend moderate increase",
            "Avoid high-fat foods before races to prevent performance impact",
            "Maintain adequate water intake, especially during race periods",
            "Recommend eating in smaller portions, avoid large meals at once"
        ]
        
        return {
            "nutrition_comparison": comparison,
            "general_recommendations": recommendations,
            "jockey_specific_recommendations": jockey_recommendations
        }
    
    def analyze_trends(self, daily_records, days=7):
        """Analyze nutrition trends"""
        if len(daily_records) < 2:
            return {"message": "Insufficient data to analyze trends"}
        
        # Calculate daily nutrition intake
        daily_nutrition = []
        for record in daily_records[-days:]:
            total = {"date": record["date"]}
            for food in record["foods"]:
                nutrition = food["nutrition"]
                for key in ["calories", "protein", "carbs", "fat", "fiber"]:
                    total[key] = total.get(key, 0) + nutrition.get(key, 0)
            daily_nutrition.append(total)
        
        # Calculate trends
        trends = {}
        for nutrient in ["calories", "protein", "carbs", "fat", "fiber"]:
            values = [day[nutrient] for day in daily_nutrition]
            if len(values) > 1:
                # Simple linear regression to calculate trend
                x = np.arange(len(values))
                slope = np.polyfit(x, values, 1)[0]
                
                if slope > 0:
                    trend = "Increasing"
                elif slope < 0:
                    trend = "Decreasing"
                else:
                    trend = "Stable"
                
                trends[nutrient] = {
                    "trend": trend,
                    "slope": slope,
                    "average": np.mean(values),
                    "variance": np.var(values)
                }
        
        return {
            "daily_nutrition": daily_nutrition,
            "trends": trends
        }
    
    def calculate_bmi_recommendations(self, weight, height, activity_level="moderate"):
        """Calculate BMI and weight management recommendations"""
        height_m = height / 100  # Convert to meters
        bmi = weight / (height_m ** 2)
        
        # BMI classification
        if bmi < 18.5:
            bmi_category = "Underweight"
            recommendation = "Recommend appropriate weight gain, but maintain health"
        elif bmi < 24:
            bmi_category = "Normal Weight"
            recommendation = "Maintain current weight, continue healthy diet"
        elif bmi < 28:
            bmi_category = "Overweight"
            recommendation = "Recommend appropriate weight loss, control calorie intake"
        else:
            bmi_category = "Obese"
            recommendation = "Recommend weight loss, consult professional nutritionist"
        
        # Jockey-specific recommendations
        jockey_weight_recommendations = [
            "Jockeys need to maintain lightweight, recommend BMI control between 18.5-22",
            "Avoid rapid weight loss to prevent health and performance impact",
            "Control weight through proper diet and exercise",
            "Regularly monitor weight changes"
        ]
        
        return {
            "bmi": round(bmi, 1),
            "bmi_category": bmi_category,
            "recommendation": recommendation,
            "jockey_recommendations": jockey_weight_recommendations
        }
