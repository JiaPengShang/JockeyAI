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
        """分析一餐的营养成分"""
        total_nutrition = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0
        }
        
        analyzed_foods = []
        
        for food in foods_data:
            # 获取食物分类
            classification = self.food_classifier.classify_food(food["name"])
            
            # 获取营养信息
            nutrition = self.food_classifier.get_nutrition_info(
                food["name"], 
                food.get("quantity", 100)
            )
            
            # 添加到总营养
            for key in total_nutrition:
                total_nutrition[key] += nutrition.get(key, 0)
            
            # 保存分析结果
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
    
    def compare_with_targets(self, nutrition_data, target_type="体重管理"):
        """与目标营养进行比较"""
        targets = self.nutrition_targets.get(target_type, self.nutrition_targets["体重管理"])
        
        comparison = {}
        for nutrient, target_info in targets.items():
            if nutrient in nutrition_data:
                actual = nutrition_data[nutrient]
                target = target_info["目标"]
                unit = target_info["单位"]
                
                percentage = (actual / target) * 100 if target > 0 else 0
                
                comparison[nutrient] = {
                    "actual": actual,
                    "target": target,
                    "unit": unit,
                    "percentage": percentage,
                    "status": "正常" if 80 <= percentage <= 120 else "不足" if percentage < 80 else "过量"
                }
        
        return comparison
    
    def generate_recommendations(self, analysis_result, target_type="体重管理"):
        """生成营养建议"""
        comparison = self.compare_with_targets(analysis_result["total_nutrition"], target_type)
        
        recommendations = []
        
        # 分析每个营养素
        for nutrient, data in comparison.items():
            if data["status"] == "不足":
                recommendations.append(f"建议增加{nutrient}的摄入，当前摄入{data['actual']:.1f}{data['unit']}，目标{data['target']}{data['unit']}")
            elif data["status"] == "过量":
                recommendations.append(f"建议减少{nutrient}的摄入，当前摄入{data['actual']:.1f}{data['unit']}，目标{data['target']}{data['unit']}")
        
        # 骑师特殊建议
        jockey_recommendations = [
            "骑师需要保持轻量级，建议控制总卡路里摄入",
            "蛋白质摄入对肌肉维护很重要，建议适量增加",
            "比赛前避免高脂肪食物，以免影响表现",
            "保持充足的水分摄入，特别是在比赛期间",
            "建议分餐进食，避免一次性大量进食"
        ]
        
        return {
            "nutrition_comparison": comparison,
            "general_recommendations": recommendations,
            "jockey_specific_recommendations": jockey_recommendations
        }
    
    def analyze_trends(self, daily_records, days=7):
        """分析营养趋势"""
        if len(daily_records) < 2:
            return {"message": "数据不足，无法分析趋势"}
        
        # 计算每日营养摄入
        daily_nutrition = []
        for record in daily_records[-days:]:
            total = {"date": record["date"]}
            for food in record["foods"]:
                nutrition = food["nutrition"]
                for key in ["calories", "protein", "carbs", "fat", "fiber"]:
                    total[key] = total.get(key, 0) + nutrition.get(key, 0)
            daily_nutrition.append(total)
        
        # 计算趋势
        trends = {}
        for nutrient in ["calories", "protein", "carbs", "fat", "fiber"]:
            values = [day[nutrient] for day in daily_nutrition]
            if len(values) > 1:
                # 简单线性回归计算趋势
                x = np.arange(len(values))
                slope = np.polyfit(x, values, 1)[0]
                
                if slope > 0:
                    trend = "上升"
                elif slope < 0:
                    trend = "下降"
                else:
                    trend = "稳定"
                
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
        """计算BMI和体重管理建议"""
        height_m = height / 100  # 转换为米
        bmi = weight / (height_m ** 2)
        
        # BMI分类
        if bmi < 18.5:
            bmi_category = "体重不足"
            recommendation = "建议适当增加体重，但要注意保持健康"
        elif bmi < 24:
            bmi_category = "正常体重"
            recommendation = "保持当前体重，继续健康饮食"
        elif bmi < 28:
            bmi_category = "超重"
            recommendation = "建议适当减重，控制卡路里摄入"
        else:
            bmi_category = "肥胖"
            recommendation = "建议减重，咨询专业营养师"
        
        # 骑师特殊建议
        jockey_weight_recommendations = [
            "骑师需要保持轻量级，建议BMI控制在18.5-22之间",
            "避免快速减重，以免影响健康和表现",
            "通过合理饮食和运动控制体重",
            "定期监测体重变化"
        ]
        
        return {
            "bmi": round(bmi, 1),
            "bmi_category": bmi_category,
            "recommendation": recommendation,
            "jockey_recommendations": jockey_weight_recommendations
        }
