"""
示例数据生成脚本
用于演示JockeyAI系统的各项功能
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import random
from pathlib import Path

def generate_food_log_data(days=30):
    """生成饮食日志示例数据"""
    data = []
    start_date = datetime.now() - timedelta(days=days)
    
    # 食物列表
    foods = [
        "米饭", "面条", "面包", "鸡蛋", "牛奶", "鸡肉", "鱼肉", "牛肉", "猪肉",
        "青菜", "胡萝卜", "土豆", "番茄", "苹果", "香蕉", "橙子", "葡萄",
        "酸奶", "奶酪", "豆腐", "豆浆", "粥", "汤", "沙拉", "三明治"
    ]
    
    # 单位列表
    units = ["碗", "份", "个", "杯", "克", "毫升", "片", "块"]
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # 每天3-5餐
        meals = random.randint(3, 5)
        for meal in range(meals):
            # 随机时间
            hour = random.choice([7, 8, 12, 13, 18, 19, 21])
            minute = random.randint(0, 59)
            meal_time = time(hour, minute)
            
            # 随机食物
            food = random.choice(foods)
            quantity = random.randint(1, 3)
            unit = random.choice(units)
            
            # 营养成分（估算）
            calories = random.randint(50, 500)
            protein = random.uniform(2, 25)
            carbs = random.uniform(10, 60)
            fat = random.uniform(1, 20)
            
            # 备注
            notes = random.choice(["", "很好吃", "营养丰富", "下次再吃", "不太喜欢"])
            
            data.append({
                'date': current_date.date(),
                'time': meal_time,
                'food_name': food,
                'quantity': quantity,
                'unit': unit,
                'calories': calories,
                'protein': round(protein, 1),
                'carbs': round(carbs, 1),
                'fat': round(fat, 1),
                'notes': notes
            })
    
    return pd.DataFrame(data)

def generate_sleep_log_data(days=30):
    """生成睡眠日志示例数据"""
    data = []
    start_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # 随机就寝时间 (22:00 - 01:00)
        bedtime_hour = random.choice([22, 23, 0, 1])
        bedtime_minute = random.randint(0, 59)
        bedtime = time(bedtime_hour, bedtime_minute)
        
        # 随机起床时间 (06:00 - 09:00)
        wake_hour = random.randint(6, 9)
        wake_minute = random.randint(0, 59)
        wake_time = time(wake_hour, wake_minute)
        
        # 计算睡眠时长
        if bedtime_hour > wake_hour:  # 跨夜
            sleep_hours = (24 - bedtime_hour) + wake_hour + (wake_minute - bedtime_minute) / 60
        else:
            sleep_hours = (wake_hour - bedtime_hour) + (wake_minute - bedtime_minute) / 60
        
        # 睡眠质量 (1-10)
        sleep_quality = random.randint(5, 10)
        
        # 深度睡眠和REM睡眠
        deep_sleep = random.uniform(1, 3)
        rem_sleep = random.uniform(1, 2)
        
        # 备注
        notes = random.choice(["", "睡得很好", "有点失眠", "做了好梦", "太累了"])
        
        data.append({
            'date': current_date.date(),
            'bedtime': bedtime,
            'wake_time': wake_time,
            'sleep_duration': round(sleep_hours, 1),
            'sleep_quality': sleep_quality,
            'deep_sleep': round(deep_sleep, 1),
            'rem_sleep': round(rem_sleep, 1),
            'notes': notes
        })
    
    return pd.DataFrame(data)

def generate_training_log_data(days=30):
    """生成训练日志示例数据"""
    data = []
    start_date = datetime.now() - timedelta(days=days)
    
    # 训练类型
    training_types = [
        "跑步", "骑行", "游泳", "力量训练", "瑜伽", "拉伸", "有氧运动",
        "马术训练", "平衡训练", "核心训练", "柔韧性训练"
    ]
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # 每天0-2次训练
        training_sessions = random.randint(0, 2)
        
        for session in range(training_sessions):
            training_type = random.choice(training_types)
            
            # 训练时长 (30-120分钟)
            duration = random.randint(30, 120)
            
            # 训练强度 (1-10)
            intensity = random.randint(4, 9)
            
            # 距离 (根据训练类型)
            if training_type in ["跑步", "骑行"]:
                distance = random.uniform(3, 20)
            elif training_type == "游泳":
                distance = random.uniform(0.5, 3)
            else:
                distance = None
            
            # 消耗卡路里
            calories_burned = int(duration * intensity * random.uniform(0.8, 1.2))
            
            # 心率数据
            heart_rate_avg = random.randint(120, 180)
            heart_rate_max = heart_rate_avg + random.randint(10, 30)
            
            # 备注
            notes = random.choice(["", "感觉很好", "有点累", "进步明显", "需要调整"])
            
            data.append({
                'date': current_date.date(),
                'training_type': training_type,
                'duration': duration,
                'intensity': intensity,
                'distance': round(distance, 1) if distance else None,
                'calories_burned': calories_burned,
                'heart_rate_avg': heart_rate_avg,
                'heart_rate_max': heart_rate_max,
                'notes': notes
            })
    
    return pd.DataFrame(data)

def generate_weight_log_data(days=30):
    """生成体重日志示例数据"""
    data = []
    start_date = datetime.now() - timedelta(days=days)
    
    # 初始体重 (60-80kg)
    base_weight = random.uniform(60, 80)
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # 体重变化 (每天±0.5kg)
        weight_change = random.uniform(-0.5, 0.5)
        weight = base_weight + weight_change
        base_weight = weight  # 更新基准体重
        
        # 体脂率 (10-25%)
        body_fat = random.uniform(10, 25)
        
        # 肌肉量 (体重的一部分)
        muscle_mass = weight * random.uniform(0.3, 0.5)
        
        # 水分百分比 (50-70%)
        water_percentage = random.uniform(50, 70)
        
        # 备注
        notes = random.choice(["", "体重稳定", "需要控制", "感觉良好", "注意饮食"])
        
        data.append({
            'date': current_date.date(),
            'weight': round(weight, 1),
            'body_fat': round(body_fat, 1),
            'muscle_mass': round(muscle_mass, 1),
            'water_percentage': round(water_percentage, 1),
            'notes': notes
        })
    
    return pd.DataFrame(data)

def create_sample_files():
    """创建示例数据文件"""
    # 创建data目录
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 生成示例数据
    print("正在生成示例数据...")
    
    # 饮食日志
    food_df = generate_food_log_data(30)
    food_df.to_csv(data_dir / "sample_food_log.csv", index=False, encoding='utf-8-sig')
    print(f"✅ 饮食日志数据已生成: {len(food_df)} 条记录")
    
    # 睡眠日志
    sleep_df = generate_sleep_log_data(30)
    sleep_df.to_csv(data_dir / "sample_sleep_log.csv", index=False, encoding='utf-8-sig')
    print(f"✅ 睡眠日志数据已生成: {len(sleep_df)} 条记录")
    
    # 训练日志
    training_df = generate_training_log_data(30)
    training_df.to_csv(data_dir / "sample_training_log.csv", index=False, encoding='utf-8-sig')
    print(f"✅ 训练日志数据已生成: {len(training_df)} 条记录")
    
    # 体重日志
    weight_df = generate_weight_log_data(30)
    weight_df.to_csv(data_dir / "sample_weight_log.csv", index=False, encoding='utf-8-sig')
    print(f"✅ 体重日志数据已生成: {len(weight_df)} 条记录")
    
    print("\n🎉 所有示例数据已生成完成！")
    print("文件位置: data/")
    print("\n数据概览:")
    print(f"  饮食日志: {len(food_df)} 条记录")
    print(f"  睡眠日志: {len(sleep_df)} 条记录")
    print(f"  训练日志: {len(training_df)} 条记录")
    print(f"  体重日志: {len(weight_df)} 条记录")

def create_sample_images():
    """创建示例图片数据（模拟OCR测试）"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        
        # 创建示例图片目录
        images_dir = Path("data/sample_images")
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建示例表格图片
        def create_table_image(filename, title, data_rows):
            # 创建图片
            img_width, img_height = 800, 600
            img = Image.new('RGB', (img_width, img_height), color='white')
            draw = ImageDraw.Draw(img)
            
            # 尝试使用系统字体
            try:
                font = ImageFont.truetype("arial.ttf", 16)
                title_font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
            
            # 绘制标题
            draw.text((50, 30), title, fill='black', font=title_font)
            
            # 绘制表格
            y_start = 80
            row_height = 40
            
            for i, row in enumerate(data_rows):
                y = y_start + i * row_height
                draw.text((50, y), row, fill='black', font=font)
            
            # 保存图片
            img.save(images_dir / filename)
            print(f"✅ 示例图片已生成: {filename}")
        
        # 创建饮食日志示例图片
        food_data = [
            "日期        时间    食物名称    数量  单位  卡路里  蛋白质  碳水化合物  脂肪",
            "2024-01-01  08:00   米饭       1    碗   200    4.0    45.0       0.5",
            "2024-01-01  12:00   鸡肉       1    份   250    25.0   0.0        15.0",
            "2024-01-01  18:00   青菜       1    份   50     3.0    8.0        0.5",
            "2024-01-02  08:00   牛奶       1    杯   120    8.0    12.0       5.0",
            "2024-01-02  12:00   面条       1    碗   300    10.0   55.0       2.0"
        ]
        create_table_image("sample_food_log.png", "饮食日志示例", food_data)
        
        # 创建睡眠日志示例图片
        sleep_data = [
            "日期        就寝时间  起床时间  睡眠时长  睡眠质量  深度睡眠  REM睡眠",
            "2024-01-01  23:00    07:00    8.0      8        2.5     1.5",
            "2024-01-02  22:30    06:30    7.5      7        2.0     1.8",
            "2024-01-03  00:00    08:00    8.0      9        2.8     1.2",
            "2024-01-04  23:30    07:30    8.0      8        2.3     1.6",
            "2024-01-05  22:00    06:00    8.0      6        1.8     2.0"
        ]
        create_table_image("sample_sleep_log.png", "睡眠日志示例", sleep_data)
        
        # 创建训练日志示例图片
        training_data = [
            "日期        训练类型  时长  强度  距离  消耗卡路里  平均心率  最大心率",
            "2024-01-01  跑步     45    7    5.0   350        150      175",
            "2024-01-02  力量训练 60    8    0.0   400        140      160",
            "2024-01-03  骑行     90    6    20.0  500        135      155",
            "2024-01-04  游泳     30    8    1.0   250        145      165",
            "2024-01-05  瑜伽     45    5    0.0   200        120      140"
        ]
        create_table_image("sample_training_log.png", "训练日志示例", training_data)
        
        print(f"\n📸 示例图片已生成到: {images_dir}")
        
    except ImportError:
        print("⚠️  PIL库未安装，跳过示例图片生成")
        print("   如需生成示例图片，请安装: pip install pillow")

if __name__ == "__main__":
    print("🏇 JockeyAI 示例数据生成器")
    print("=" * 50)
    
    # 生成CSV数据
    create_sample_files()
    
    # 生成示例图片
    create_sample_images()
    
    print("\n" + "=" * 50)
    print("🎯 使用说明:")
    print("1. 启动应用: streamlit run app.py")
    print("2. 在'文件上传'页面测试OCR功能")
    print("3. 在'数据可视化'页面查看图表")
    print("4. 在'系统设置'页面导出数据")
    print("\n🚀 开始体验JockeyAI的强大功能吧！")
