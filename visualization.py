import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from config import FOOD_CATEGORIES

class NutritionVisualizer:
    def __init__(self):
        self.colors = {
            "蛋白质": "#FF6B6B",
            "碳水化合物": "#4ECDC4", 
            "脂肪": "#45B7D1",
            "维生素": "#96CEB4",
            "矿物质": "#FFEAA7",
            "纤维": "#DDA0DD"
        }
    
    def create_nutrition_pie_chart(self, nutrition_data):
        """创建营养成分饼图"""
        labels = list(nutrition_data.keys())
        values = list(nutrition_data.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        )])
        
        fig.update_layout(
            title="营养成分分布",
            showlegend=True,
            height=400
        )
        
        return fig
    
    def create_food_category_chart(self, foods_data):
        """创建食物分类图表"""
        # 统计各分类的食物数量
        category_counts = {}
        for food in foods_data:
            category = food.get("category", "其他")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        fig = px.bar(
            x=list(category_counts.keys()),
            y=list(category_counts.values()),
            color=list(category_counts.keys()),
            color_discrete_map=self.colors,
            title="食物分类分布"
        )
        
        fig.update_layout(
            xaxis_title="食物分类",
            yaxis_title="数量",
            height=400
        )
        
        return fig
    
    def create_nutrition_comparison_chart(self, actual_data, target_data):
        """创建营养目标对比图"""
        nutrients = list(actual_data.keys())
        actual_values = list(actual_data.values())
        target_values = [target_data.get(nutrient, 0) for nutrient in nutrients]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name="实际摄入",
            x=nutrients,
            y=actual_values,
            marker_color='#FF6B6B'
        ))
        
        fig.add_trace(go.Bar(
            name="目标摄入",
            x=nutrients,
            y=target_values,
            marker_color='#4ECDC4'
        ))
        
        fig.update_layout(
            title="营养摄入 vs 目标",
            barmode='group',
            xaxis_title="营养素",
            yaxis_title="数量",
            height=400
        )
        
        return fig
    
    def create_trend_chart(self, daily_records, nutrient="calories"):
        """创建营养趋势图"""
        dates = [record["date"] for record in daily_records]
        values = [record[nutrient] for record in daily_records]
        
        fig = px.line(
            x=dates,
            y=values,
            title=f"{nutrient}摄入趋势"
        )
        
        fig.update_layout(
            xaxis_title="日期",
            yaxis_title=f"{nutrient}摄入量",
            height=400
        )
        
        return fig
    
    def create_radar_chart(self, nutrition_data, target_data):
        """创建营养雷达图"""
        nutrients = list(nutrition_data.keys())
        actual_values = list(nutrition_data.values())
        target_values = [target_data.get(nutrient, 0) for nutrient in nutrients]
        
        # 计算百分比
        percentages = []
        for i, nutrient in enumerate(nutrients):
            if target_values[i] > 0:
                percentage = (actual_values[i] / target_values[i]) * 100
            else:
                percentage = 0
            percentages.append(min(percentage, 200))  # 限制最大值
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=percentages,
            theta=nutrients,
            fill='toself',
            name='实际摄入百分比',
            line_color='#FF6B6B'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=[100] * len(nutrients),
            theta=nutrients,
            fill='toself',
            name='目标线',
            line_color='#4ECDC4'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 200]
                )),
            showlegend=True,
            title="营养摄入雷达图",
            height=500
        )
        
        return fig
    
    def create_calorie_timeline(self, daily_records):
        """创建卡路里时间线图"""
        dates = [record["date"] for record in daily_records]
        calories = [record["calories"] for record in daily_records]
        
        fig = px.scatter(
            x=dates,
            y=calories,
            size=calories,
            color=calories,
            title="每日卡路里摄入时间线"
        )
        
        fig.update_layout(
            xaxis_title="日期",
            yaxis_title="卡路里",
            height=400
        )
        
        return fig
    
    def create_nutrition_heatmap(self, weekly_data):
        """创建营养热力图"""
        # 准备数据
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        nutrients = ["calories", "protein", "carbs", "fat", "fiber"]
        
        # 创建数据矩阵
        data_matrix = []
        for nutrient in nutrients:
            row = []
            for day in days:
                # 查找对应日期的数据
                day_data = next((d for d in weekly_data if d["day"] == day), None)
                if day_data:
                    row.append(day_data.get(nutrient, 0))
                else:
                    row.append(0)
            data_matrix.append(row)
        
        fig = px.imshow(
            data_matrix,
            x=days,
            y=nutrients,
            color_continuous_scale='Viridis',
            title="每周营养摄入热力图"
        )
        
        fig.update_layout(height=400)
        
        return fig
    
    def create_bmi_chart(self, weight_history, height):
        """创建BMI变化图"""
        bmi_values = []
        dates = []
        
        for record in weight_history:
            weight = record["weight"]
            date = record["date"]
            height_m = height / 100
            bmi = weight / (height_m ** 2)
            bmi_values.append(bmi)
            dates.append(date)
        
        fig = px.line(
            x=dates,
            y=bmi_values,
            title="BMI变化趋势"
        )
        
        # 添加BMI分类线
        fig.add_hline(y=18.5, line_dash="dash", line_color="red", annotation_text="体重不足")
        fig.add_hline(y=24, line_dash="dash", line_color="green", annotation_text="正常体重")
        fig.add_hline(y=28, line_dash="dash", line_color="orange", annotation_text="超重")
        
        fig.update_layout(
            xaxis_title="日期",
            yaxis_title="BMI",
            height=400
        )
        
        return fig
    
    def create_comprehensive_dashboard(self, analysis_result):
        """创建综合仪表板"""
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("营养成分分布", "食物分类", "营养目标对比", "趋势分析"),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 营养成分饼图
        nutrition_data = analysis_result.get("total_nutrition", {})
        if nutrition_data:
            fig.add_trace(
                go.Pie(labels=list(nutrition_data.keys()), values=list(nutrition_data.values())),
                row=1, col=1
            )
        
        # 食物分类柱状图
        foods_data = analysis_result.get("foods", [])
        if foods_data:
            category_counts = {}
            for food in foods_data:
                category = food.get("category", "其他")
                category_counts[category] = category_counts.get(category, 0) + 1
            
            fig.add_trace(
                go.Bar(x=list(category_counts.keys()), y=list(category_counts.values())),
                row=1, col=2
            )
        
        fig.update_layout(height=800, title_text="营养分析综合仪表板")
        
        return fig
