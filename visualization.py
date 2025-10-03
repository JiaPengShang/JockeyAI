import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from config import FOOD_CATEGORIES

class NutritionVisualizer:
    def __init__(self):
        self.colors = {
            "Protein": "#FF6B6B",
            "Carbohydrates": "#4ECDC4", 
            "Fat": "#45B7D1",
            "Vitamins": "#96CEB4",
            "Minerals": "#FFEAA7",
            "Fiber": "#DDA0DD"
        }
    
    def create_nutrition_pie_chart(self, nutrition_data):
        """Create nutrition pie chart"""
        labels = list(nutrition_data.keys())
        values = list(nutrition_data.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        )])
        
        fig.update_layout(
            title="Nutrition Distribution",
            showlegend=True,
            height=400
        )
        
        return fig
    
    def create_food_category_chart(self, foods_data):
        """Create food category chart"""
        # Count foods by category
        category_counts = {}
        for food in foods_data:
            category = food.get("category", "Other")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        fig = px.bar(
            x=list(category_counts.keys()),
            y=list(category_counts.values()),
            color=list(category_counts.keys()),
            color_discrete_map=self.colors,
            title="Food Category Distribution"
        )
        
        fig.update_layout(
            xaxis_title="Food Category",
            yaxis_title="Count",
            height=400
        )
        
        return fig
    
    def create_food_category_pie_chart(self, food_categories):
        """Create food category pie chart"""
        if not food_categories:
            # Create empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No food data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(
                title="Food Category Distribution",
                height=400
            )
            return fig
        
        labels = list(food_categories.keys())
        values = list(food_categories.values())
        
        # Assign colors for each category
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFB347', '#98D8C8']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=colors[:len(labels)],
            textinfo='label+percent+value',
            textposition='inside'
        )])
        
        fig.update_layout(
            title="Food Category Distribution Pie Chart",
            showlegend=True,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig
    
    def create_nutrition_comparison_chart(self, actual_data, target_data):
        """Create nutrition target comparison chart"""
        nutrients = list(actual_data.keys())
        actual_values = list(actual_data.values())
        target_values = [target_data.get(nutrient, 0) for nutrient in nutrients]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name="Actual Intake",
            x=nutrients,
            y=actual_values,
            marker_color='#FF6B6B'
        ))
        
        fig.add_trace(go.Bar(
            name="Target Intake",
            x=nutrients,
            y=target_values,
            marker_color='#4ECDC4'
        ))
        
        fig.update_layout(
            title="Nutrition Intake vs Target",
            barmode='group',
            xaxis_title="Nutrients",
            yaxis_title="Amount",
            height=400
        )
        
        return fig
    
    def create_trend_chart(self, daily_records, nutrient="calories"):
        """Create nutrition trend chart"""
        dates = [record["date"] for record in daily_records]
        values = [record[nutrient] for record in daily_records]
        
        fig = px.line(
            x=dates,
            y=values,
            title=f"{nutrient} Intake Trend"
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=f"{nutrient} Intake",
            height=400
        )
        
        return fig
    
    def create_radar_chart(self, nutrition_data, target_data):
        """Create nutrition radar chart"""
        nutrients = list(nutrition_data.keys())
        actual_values = list(nutrition_data.values())
        target_values = [target_data.get(nutrient, 0) for nutrient in nutrients]
        
        # Calculate percentages
        percentages = []
        for i, nutrient in enumerate(nutrients):
            if target_values[i] > 0:
                percentage = (actual_values[i] / target_values[i]) * 100
            else:
                percentage = 0
            percentages.append(min(percentage, 200))  # Limit maximum value
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=percentages,
            theta=nutrients,
            fill='toself',
            name='Actual Intake Percentage',
            line_color='#FF6B6B'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=[100] * len(nutrients),
            theta=nutrients,
            fill='toself',
            name='Target Line',
            line_color='#4ECDC4'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 200]
                )),
            showlegend=True,
            title="Nutrition Intake Radar Chart",
            height=500
        )
        
        return fig
    
    def create_calorie_timeline(self, daily_records):
        """Create calorie timeline chart"""
        dates = [record["date"] for record in daily_records]
        calories = [record["calories"] for record in daily_records]
        
        fig = px.scatter(
            x=dates,
            y=calories,
            size=calories,
            color=calories,
            title="Daily Calorie Intake Timeline"
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Calories",
            height=400
        )
        
        return fig
    
    def create_nutrition_heatmap(self, weekly_data):
        """Create nutrition heatmap"""
        # Prepare data
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        nutrients = ["calories", "protein", "carbs", "fat", "fiber"]
        
        # Create data matrix
        data_matrix = []
        for nutrient in nutrients:
            row = []
            for day in days:
                # Find data for corresponding date
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
            title="Weekly Nutrition Intake Heatmap"
        )
        
        fig.update_layout(height=400)
        
        return fig
    
    def create_bmi_chart(self, weight_history, height):
        """Create BMI change chart"""
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
            title="BMI Change Trend"
        )
        
        # Add BMI classification lines
        fig.add_hline(y=18.5, line_dash="dash", line_color="red", annotation_text="Underweight")
        fig.add_hline(y=24, line_dash="dash", line_color="green", annotation_text="Normal Weight")
        fig.add_hline(y=28, line_dash="dash", line_color="orange", annotation_text="Overweight")
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="BMI",
            height=400
        )
        
        return fig
    
    def create_comprehensive_dashboard(self, analysis_result):
        """Create comprehensive dashboard"""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Nutrition Distribution", "Food Categories", "Nutrition Target Comparison", "Trend Analysis"),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # Nutrition pie chart
        nutrition_data = analysis_result.get("total_nutrition", {})
        if nutrition_data:
            fig.add_trace(
                go.Pie(labels=list(nutrition_data.keys()), values=list(nutrition_data.values())),
                row=1, col=1
            )
        
        # Food category bar chart
        foods_data = analysis_result.get("foods", [])
        if foods_data:
            category_counts = {}
            for food in foods_data:
                category = food.get("category", "Other")
                category_counts[category] = category_counts.get(category, 0) + 1
            
            fig.add_trace(
                go.Bar(x=list(category_counts.keys()), y=list(category_counts.values())),
                row=1, col=2
            )
        
        fig.update_layout(height=800, title_text="Nutrition Analysis Comprehensive Dashboard")
        
        return fig
