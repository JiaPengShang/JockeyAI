#!/usr/bin/env python3
"""
Jockey Nutrition AI System Test Script
"""

import sys
import os
import json
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Test configuration module"""
    print("🔧 Testing configuration module...")
    try:
        from config import OPENAI_API_KEY, FOOD_CATEGORIES, NUTRITION_TARGETS
        print(f"✅ API key configuration: {'Set' if OPENAI_API_KEY else 'Not set'}")
        print(f"✅ Food categories count: {len(FOOD_CATEGORIES)}")
        print(f"✅ Nutrition target types: {len(NUTRITION_TARGETS)}")
        return True
    except Exception as e:
        print(f"❌ Configuration module test failed: {e}")
        return False

def test_food_classifier():
    """Test food classifier"""
    print("\n🍎 Testing food classifier...")
    try:
        from food_classifier import FoodClassifier
        
        classifier = FoodClassifier()
        
        # Test food classification
        test_foods = ["chicken", "rice", "apple", "milk"]
        results = classifier.classify_multiple_foods(test_foods)
        
        print("Food classification results:")
        for result in results:
            print(f"  {result['food_name']} -> {result['category']} (confidence: {result['confidence']:.2f})")
        
        # Test nutrition information
        nutrition = classifier.get_nutrition_info("chicken", 100)
        print(f"Chicken nutrition info: {nutrition}")
        
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
        
        # Test food analysis
        test_foods = [
            {"name": "chicken", "quantity": 150},
            {"name": "rice", "quantity": 200},
            {"name": "apple", "quantity": 100}
        ]
        
        analysis = analyzer.analyze_meal(test_foods)
        print(f"Nutrition analysis results:")
        print(f"  Total calories: {analysis['total_nutrition']['calories']:.1f} kcal")
        print(f"  Protein: {analysis['total_nutrition']['protein']:.1f} g")
        print(f"  Carbohydrates: {analysis['total_nutrition']['carbs']:.1f} g")
        print(f"  Fat: {analysis['total_nutrition']['fat']:.1f} g")
        
        # Test recommendation generation
        recommendations = analyzer.generate_recommendations(analysis)
        print(f"Generated recommendations count: {len(recommendations['general_recommendations'])}")
        
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
        
        # Test data
        nutrition_data = {
            "calories": 1200,
            "protein": 80,
            "carbs": 150,
            "fat": 40,
            "fiber": 25
        }
        
        foods_data = [
            {"category": "Protein"},
            {"category": "Carbohydrates"},
            {"category": "Vitamins"},
            {"category": "Protein"}
        ]
        
        # Create charts
        pie_chart = visualizer.create_nutrition_pie_chart(nutrition_data)
        category_chart = visualizer.create_food_category_chart(foods_data)
        
        print("✅ Pie chart created successfully")
        print("✅ Category chart created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Visualization module test failed: {e}")
        return False

def test_ocr_processor():
    """Test OCR processor"""
    print("\n📷 Testing OCR processor...")
    try:
        from ocr_processor import OCRProcessor
        
        processor = OCRProcessor()
        print("✅ OCR processor initialized successfully")
        
        # Note: Actual OCR testing requires image files
        print("⚠️  OCR testing requires actual image files")
        
        return True
    except Exception as e:
        print(f"❌ OCR processor test failed: {e}")
        return False

def test_integration():
    """Test integration functionality"""
    print("\n🔗 Testing integration functionality...")
    try:
        from food_classifier import FoodClassifier
        from nutrition_analyzer import NutritionAnalyzer
        from visualization import NutritionVisualizer
        
        # Simulate complete analysis workflow
        classifier = FoodClassifier()
        analyzer = NutritionAnalyzer()
        visualizer = NutritionVisualizer()
        
        # Test foods
        test_foods = [
            {"name": "chicken breast", "quantity": 150},
            {"name": "brown rice", "quantity": 200},
            {"name": "broccoli", "quantity": 100}
        ]
        
        # Analysis
        analysis = analyzer.analyze_meal(test_foods)
        
        # Generate charts
        pie_chart = visualizer.create_nutrition_pie_chart(analysis["total_nutrition"])
        category_chart = visualizer.create_food_category_chart(analysis["foods"])
        
        print("✅ Integration test successful")
        print(f"  Analyzed foods count: {len(analysis['foods'])}")
        print(f"  Total calories: {analysis['total_nutrition']['calories']:.1f} kcal")
        
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🏇 Jockey Nutrition AI - System Test")
    print("=" * 50)
    
    tests = [
        ("Configuration Module", test_config),
        ("Food Classifier", test_food_classifier),
        ("Nutrition Analyzer", test_nutrition_analyzer),
        ("Visualization Module", test_visualization),
        ("OCR Processor", test_ocr_processor),
        ("Integration Functionality", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! System ready.")
        print("\nStart application:")
        print("  streamlit run app.py")
    else:
        print("⚠️  Some tests failed, please check related modules.")

if __name__ == "__main__":
    main()
