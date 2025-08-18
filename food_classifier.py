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
        """准备训练数据"""
        training_data = []
        training_labels = []
        
        # 为每个分类添加训练数据
        for category, foods in FOOD_CATEGORIES.items():
            for food in foods:
                training_data.append(food)
                training_labels.append(category)
        
        # 添加一些额外的训练数据
        additional_data = {
            "蛋白质": ["鸡胸肉", "牛排", "三文鱼", "金枪鱼", "虾", "蟹", "贝类", "瘦肉", "火鸡肉"],
            "碳水化合物": ["白米饭", "糙米", "意大利面", "馒头", "包子", "饺子", "面条", "粥", "玉米粥"],
            "脂肪": ["花生油", "菜籽油", "芝麻油", "猪油", "羊油", "鸭油", "鹅油"],
            "维生素": ["苹果", "香蕉", "葡萄", "草莓", "蓝莓", "猕猴桃", "芒果", "菠萝"],
            "矿物质": ["钙片", "铁片", "锌片", "镁片", "钾片", "钠片", "磷片"],
            "纤维": ["燕麦片", "荞麦", "藜麦", "小米", "黑米", "紫米", "薏米"]
        }
        
        for category, foods in additional_data.items():
            for food in foods:
                training_data.append(food)
                training_labels.append(category)
        
        return training_data, training_labels
    
    def train_model(self):
        """训练分类模型"""
        print("正在准备训练数据...")
        training_data, training_labels = self.prepare_training_data()
        
        print("正在向量化文本...")
        X = self.vectorizer.fit_transform(training_data)
        
        print("正在训练模型...")
        self.classifier.fit(X, training_labels)
        
        # 评估模型
        y_pred = self.classifier.predict(X)
        accuracy = accuracy_score(training_labels, y_pred)
        print(f"模型训练完成，准确率: {accuracy:.2f}")
        
        self.model_trained = True
        
        # 保存模型
        self.save_model()
    
    def classify_food(self, food_name):
        """分类单个食物"""
        if not self.model_trained:
            self.train_model()
        
        # 向量化输入
        X = self.vectorizer.transform([food_name])
        
        # 预测
        prediction = self.classifier.predict(X)[0]
        probabilities = self.classifier.predict_proba(X)[0]
        
        # 获取置信度
        confidence = max(probabilities)
        
        return {
            "food_name": food_name,
            "category": prediction,
            "confidence": confidence,
            "probabilities": dict(zip(self.categories, probabilities))
        }
    
    def classify_multiple_foods(self, food_list):
        """分类多个食物"""
        results = []
        for food in food_list:
            result = self.classify_food(food)
            results.append(result)
        return results
    
    def save_model(self):
        """保存模型"""
        model_data = {
            "vectorizer": self.vectorizer,
            "classifier": self.classifier,
            "categories": self.categories
        }
        with open("food_classifier_model.pkl", "wb") as f:
            pickle.dump(model_data, f)
        print("模型已保存")
    
    def load_model(self):
        """加载模型"""
        try:
            with open("food_classifier_model.pkl", "rb") as f:
                model_data = pickle.load(f)
            
            self.vectorizer = model_data["vectorizer"]
            self.classifier = model_data["classifier"]
            self.categories = model_data["categories"]
            self.model_trained = True
            print("模型加载成功")
            return True
        except FileNotFoundError:
            print("模型文件不存在，将重新训练")
            return False
    
    def get_nutrition_info(self, food_name, quantity=100):
        """获取食物的营养信息（模拟数据）"""
        nutrition_database = {
            "鸡肉": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
            "牛肉": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15, "fiber": 0},
            "鱼肉": {"calories": 120, "protein": 22, "carbs": 0, "fat": 4, "fiber": 0},
            "鸡蛋": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0},
            "米饭": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4},
            "面包": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7},
            "牛奶": {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1, "fiber": 0},
            "苹果": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4},
            "香蕉": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6},
            "胡萝卜": {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2, "fiber": 2.8}
        }
        
        # 查找最匹配的食物
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
            # 根据数量调整营养值
            ratio = quantity / 100
            for key in nutrition:
                nutrition[key] = round(nutrition[key] * ratio, 2)
            return nutrition
        else:
            # 返回默认营养信息
            return {
                "calories": 100,
                "protein": 5,
                "carbs": 15,
                "fat": 3,
                "fiber": 2
            }
