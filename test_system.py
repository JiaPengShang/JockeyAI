#!/usr/bin/env python3
"""
Jockey Nutrition AI - system test script
"""

import sys
import os
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Test config module"""
    print("🔧 Testing config module...")
    try:
        from config import OPENAI_API_KEY, FOOD_CATEGORIES, NUTRITION_TARGETS
        print(f"✅ API key configured: {bool(OPENAI_API_KEY)}")
        print(f"✅ Food categories: {len(FOOD_CATEGORIES)}")
        print(f"✅ Nutrition target types: {len(NUTRITION_TARGETS)}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_food_classifier():
    """Test food classifier"""
    print("\n🍎 Testing food classifier...")
    try:
        from food_classifier import FoodClassifier
        
        classifier = FoodClassifier()
        
        # Classification
        test_foods = ["chicken", "rice", "apple", "milk"]
        results = classifier.classify_multiple_foods(test_foods)
        
        print("Classification results:")
        for result in results:
            print(f"  {result['food_name']} -> {result['category']} (置信度: {result['confidence']:.2f})")
        
        # Nutrition info
        nutrition = classifier.get_nutrition_info("chicken", 100)
        print(f"Chicken nutrition: {nutrition}")
        
        return True
    except Exception as e:
        print(f"❌ Food classifier test failed: {e}")
        return False

def test_nutrition_analyzer():
    """Test nutrition analyzer"""
    print("\n📊 Testing nutrition analyzer...")
    try:
        from nutrition_analyzer import NutritionAnalyzer
        
        analyzer = NutritionAnalyzer()
        
        # Analysis
        test_foods = [
            {"name": "chicken", "quantity": 150},
            {"name": "rice", "quantity": 200},
            {"name": "apple", "quantity": 100}
        ]
        
        analysis = analyzer.analyze_meal(test_foods)
        print(f"Analysis results:")
        print(f"  Calories: {analysis['total_nutrition']['calories']:.1f} kcal")
        print(f"  Protein: {analysis['total_nutrition']['protein']:.1f} g")
        print(f"  Carbs: {analysis['total_nutrition']['carbs']:.1f} g")
        print(f"  Fat: {analysis['total_nutrition']['fat']:.1f} g")
        
        # 测试建议生成
        recommendations = analyzer.generate_recommendations(analysis)
        print(f"Recommendations count: {len(recommendations['general_recommendations'])}")
        
        return True
    except Exception as e:
        print(f"❌ Nutrition analyzer test failed: {e}")
        return False

def test_visualization():
    """Test visualization module"""
    print("\n📈 Testing visualization module...")
    try:
        from visualization import NutritionVisualizer
        
        visualizer = NutritionVisualizer()
        
        # 测试数据
        nutrition_data = {
            "calories": 1200,
            "protein": 80,
            "carbs": 150,
            "fat": 40,
            "fiber": 25
        }
        
        foods_data = [
            {"category": "蛋白质"},
            {"category": "碳水化合物"},
            {"category": "维生素"},
            {"category": "蛋白质"}
        ]
        
        # 创建图表
        pie_chart = visualizer.create_nutrition_pie_chart(nutrition_data)
        category_chart = visualizer.create_food_category_chart(foods_data)
        
        print("✅ Pie chart created")
        print("✅ Category chart created")
        
        return True
    except Exception as e:
        print(f"❌ Visualization test failed: {e}")
        return False

def test_ocr_processor():
    """Test OCR processor"""
    print("\n📷 Testing OCR processor...")
    try:
        from ocr_processor import OCRProcessor
        
        processor = OCRProcessor()
        print("✅ OCR processor initialized")
        
        # 注意：实际OCR测试需要图片文件
        print("⚠️ OCR test requires actual image file(s)")
        
        return True
    except Exception as e:
        print(f"❌ OCR processor test failed: {e}")
        return False

def test_integration():
    """Test integration flow"""
    print("\n🔗 Testing integration...")
    try:
        from food_classifier import FoodClassifier
        from nutrition_analyzer import NutritionAnalyzer
        from visualization import NutritionVisualizer
        
        # Simulate full flow
        classifier = FoodClassifier()
        analyzer = NutritionAnalyzer()
        visualizer = NutritionVisualizer()
        
        test_foods = [
            {"name": "chicken breast", "quantity": 150},
            {"name": "brown rice", "quantity": 200},
            {"name": "broccoli", "quantity": 100}
        ]
        
        # 分析
        analysis = analyzer.analyze_meal(test_foods)
        
        # 生成图表
        pie_chart = visualizer.create_nutrition_pie_chart(analysis["total_nutrition"])
        category_chart = visualizer.create_food_category_chart(analysis["foods"])
        
        print("✅ Integration test success")
        print(f"  Foods analyzed: {len(analysis['foods'])}")
        print(f"  Total calories: {analysis['total_nutrition']['calories']:.1f} kcal")
        
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🏇 Jockey Nutrition AI - System Tests")
    print("=" * 50)
    
    tests = [
        ("Config", test_config),
        ("Classifier", test_food_classifier),
        ("Analyzer", test_nutrition_analyzer),
        ("Visualization", test_visualization),
        ("OCR", test_ocr_processor),
        ("Integration", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed. System ready.")
        print("\nRun the app:")
        print("  streamlit run app.py")
    else:
        print("⚠️ Some tests failed. Please check the modules.")

if __name__ == "__main__":
    main()
