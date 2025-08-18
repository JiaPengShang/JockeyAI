#!/usr/bin/env python3
"""
骑师营养AI系统测试脚本
"""

import sys
import os
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """测试配置模块"""
    print("🔧 测试配置模块...")
    try:
        from config import OPENAI_API_KEY, FOOD_CATEGORIES, NUTRITION_TARGETS
        print(f"✅ API密钥配置: {'已设置' if OPENAI_API_KEY else '未设置'}")
        print(f"✅ 食物分类数量: {len(FOOD_CATEGORIES)}")
        print(f"✅ 营养目标类型: {len(NUTRITION_TARGETS)}")
        return True
    except Exception as e:
        print(f"❌ 配置模块测试失败: {e}")
        return False

def test_food_classifier():
    """测试食物分类器"""
    print("\n🍎 测试食物分类器...")
    try:
        from food_classifier import FoodClassifier
        
        classifier = FoodClassifier()
        
        # 测试食物分类
        test_foods = ["鸡肉", "米饭", "苹果", "牛奶"]
        results = classifier.classify_multiple_foods(test_foods)
        
        print("食物分类结果:")
        for result in results:
            print(f"  {result['food_name']} -> {result['category']} (置信度: {result['confidence']:.2f})")
        
        # 测试营养信息
        nutrition = classifier.get_nutrition_info("鸡肉", 100)
        print(f"鸡肉营养信息: {nutrition}")
        
        return True
    except Exception as e:
        print(f"❌ 食物分类器测试失败: {e}")
        return False

def test_nutrition_analyzer():
    """测试营养分析器"""
    print("\n📊 测试营养分析器...")
    try:
        from nutrition_analyzer import NutritionAnalyzer
        
        analyzer = NutritionAnalyzer()
        
        # 测试食物分析
        test_foods = [
            {"name": "鸡肉", "quantity": 150},
            {"name": "米饭", "quantity": 200},
            {"name": "苹果", "quantity": 100}
        ]
        
        analysis = analyzer.analyze_meal(test_foods)
        print(f"营养分析结果:")
        print(f"  总卡路里: {analysis['total_nutrition']['calories']:.1f} kcal")
        print(f"  蛋白质: {analysis['total_nutrition']['protein']:.1f} g")
        print(f"  碳水化合物: {analysis['total_nutrition']['carbs']:.1f} g")
        print(f"  脂肪: {analysis['total_nutrition']['fat']:.1f} g")
        
        # 测试建议生成
        recommendations = analyzer.generate_recommendations(analysis)
        print(f"生成建议数量: {len(recommendations['general_recommendations'])}")
        
        return True
    except Exception as e:
        print(f"❌ 营养分析器测试失败: {e}")
        return False

def test_visualization():
    """测试可视化模块"""
    print("\n📈 测试可视化模块...")
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
        
        print("✅ 饼图创建成功")
        print("✅ 分类图创建成功")
        
        return True
    except Exception as e:
        print(f"❌ 可视化模块测试失败: {e}")
        return False

def test_ocr_processor():
    """测试OCR处理器"""
    print("\n📷 测试OCR处理器...")
    try:
        from ocr_processor import OCRProcessor
        
        processor = OCRProcessor()
        print("✅ OCR处理器初始化成功")
        
        # 注意：实际OCR测试需要图片文件
        print("⚠️  OCR测试需要实际图片文件")
        
        return True
    except Exception as e:
        print(f"❌ OCR处理器测试失败: {e}")
        return False

def test_integration():
    """测试集成功能"""
    print("\n🔗 测试集成功能...")
    try:
        from food_classifier import FoodClassifier
        from nutrition_analyzer import NutritionAnalyzer
        from visualization import NutritionVisualizer
        
        # 模拟完整的分析流程
        classifier = FoodClassifier()
        analyzer = NutritionAnalyzer()
        visualizer = NutritionVisualizer()
        
        # 测试食物
        test_foods = [
            {"name": "鸡胸肉", "quantity": 150},
            {"name": "糙米饭", "quantity": 200},
            {"name": "西兰花", "quantity": 100}
        ]
        
        # 分析
        analysis = analyzer.analyze_meal(test_foods)
        
        # 生成图表
        pie_chart = visualizer.create_nutrition_pie_chart(analysis["total_nutrition"])
        category_chart = visualizer.create_food_category_chart(analysis["foods"])
        
        print("✅ 集成测试成功")
        print(f"  分析食物数量: {len(analysis['foods'])}")
        print(f"  总卡路里: {analysis['total_nutrition']['calories']:.1f} kcal")
        
        return True
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🏇 骑师营养AI - 系统测试")
    print("=" * 50)
    
    tests = [
        ("配置模块", test_config),
        ("食物分类器", test_food_classifier),
        ("营养分析器", test_nutrition_analyzer),
        ("可视化模块", test_visualization),
        ("OCR处理器", test_ocr_processor),
        ("集成功能", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}测试通过")
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统准备就绪。")
        print("\n启动应用:")
        print("  streamlit run app.py")
    else:
        print("⚠️  部分测试失败，请检查相关模块。")

if __name__ == "__main__":
    main()
