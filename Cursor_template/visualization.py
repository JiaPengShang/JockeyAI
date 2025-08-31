"""
数据可视化模块 - 支持多种图表类型和Material 3设计
"""
import plotly.graph_objects as go
import plotly.express as px
import plotly.subplots as sp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import logging

from config import viz_config, DATA_SCHEMAS

logger = logging.getLogger(__name__)

class DataVisualizer:
    """数据可视化器 - 支持多种图表类型"""
    
    def __init__(self):
        """初始化可视化器"""
        self.color_theme = viz_config.color_theme
        self.chart_types = viz_config.chart_types
    
    def create_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                         title: str = "", color: str = None) -> go.Figure:
        """创建折线图"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='lines+markers',
            name=y_col,
            line=dict(color=color or self.color_theme['primary'], width=3),
            marker=dict(size=8, color=color or self.color_theme['primary'])
        ))
        
        fig.update_layout(
            title=title or f"{y_col} 趋势图",
            xaxis_title=x_col,
            yaxis_title=y_col,
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50),
            hovermode='x unified'
        )
        
        return fig
    
    def create_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                        title: str = "", color: str = None) -> go.Figure:
        """创建柱状图"""
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df[x_col],
            y=df[y_col],
            name=y_col,
            marker_color=color or self.color_theme['primary'],
            opacity=0.8
        ))
        
        fig.update_layout(
            title=title or f"{y_col} 柱状图",
            xaxis_title=x_col,
            yaxis_title=y_col,
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_scatter_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                           title: str = "", color_col: str = None) -> go.Figure:
        """创建散点图"""
        if color_col and color_col in df.columns:
            fig = px.scatter(
                df, x=x_col, y=y_col, color=color_col,
                title=title or f"{x_col} vs {y_col} 散点图",
                color_continuous_scale='viridis'
            )
        else:
            fig = px.scatter(
                df, x=x_col, y=y_col,
                title=title or f"{x_col} vs {y_col} 散点图"
            )
        
        fig.update_layout(
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_pie_chart(self, df: pd.DataFrame, values_col: str, names_col: str,
                        title: str = "") -> go.Figure:
        """创建饼图"""
        fig = go.Figure(data=[go.Pie(
            labels=df[names_col],
            values=df[values_col],
            hole=0.3,
            marker_colors=px.colors.qualitative.Set3
        )])
        
        fig.update_layout(
            title=title or f"{values_col} 分布图",
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_heatmap(self, df: pd.DataFrame, x_col: str, y_col: str, values_col: str,
                      title: str = "") -> go.Figure:
        """创建热力图"""
        pivot_table = df.pivot_table(values=values_col, index=y_col, columns=x_col, aggfunc='mean')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='Viridis'
        ))
        
        fig.update_layout(
            title=title or f"{values_col} 热力图",
            xaxis_title=x_col,
            yaxis_title=y_col,
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_box_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                        title: str = "") -> go.Figure:
        """创建箱线图"""
        fig = px.box(
            df, x=x_col, y=y_col,
            title=title or f"{y_col} 箱线图",
            color_discrete_sequence=[self.color_theme['primary']]
        )
        
        fig.update_layout(
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_histogram(self, df: pd.DataFrame, column: str, title: str = "") -> go.Figure:
        """创建直方图"""
        fig = px.histogram(
            df, x=column,
            title=title or f"{column} 分布直方图",
            nbins=20,
            color_discrete_sequence=[self.color_theme['primary']]
        )
        
        fig.update_layout(
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_area_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                         title: str = "") -> go.Figure:
        """创建面积图"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            fill='tonexty',
            name=y_col,
            line=dict(color=self.color_theme['primary']),
            fillcolor=f'rgba(25, 118, 210, 0.3)'  # 半透明蓝色
        ))
        
        fig.update_layout(
            title=title or f"{y_col} 面积图",
            xaxis_title=x_col,
            yaxis_title=y_col,
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_dashboard(self, df: pd.DataFrame, schema_name: str) -> go.Figure:
        """创建综合仪表板"""
        if schema_name not in DATA_SCHEMAS:
            raise ValueError(f"Unknown schema: {schema_name}")
        
        schema = DATA_SCHEMAS[schema_name]
        default_charts = viz_config.default_charts.get(schema_name, ["line", "bar"])
        
        # 确定子图数量
        n_charts = min(len(default_charts), 4)  # 最多4个图表
        
        if n_charts == 1:
            fig = self._create_single_chart(df, schema, default_charts[0])
        else:
            fig = self._create_multi_chart_dashboard(df, schema, default_charts[:n_charts])
        
        return fig
    
    def _create_single_chart(self, df: pd.DataFrame, schema, chart_type: str) -> go.Figure:
        """创建单个图表"""
        # 找到数值型字段
        numeric_fields = [field.name for field in schema.fields if field.type == "number"]
        date_fields = [field.name for field in schema.fields if field.type == "date"]
        
        if not numeric_fields:
            return self._create_text_summary(df, schema)
        
        y_col = numeric_fields[0]
        x_col = date_fields[0] if date_fields else df.columns[0]
        
        if chart_type == "line":
            return self.create_line_chart(df, x_col, y_col, f"{schema.description} - {y_col}趋势")
        elif chart_type == "bar":
            return self.create_bar_chart(df, x_col, y_col, f"{schema.description} - {y_col}统计")
        elif chart_type == "scatter":
            return self.create_scatter_chart(df, x_col, y_col, f"{schema.description} - {x_col} vs {y_col}")
        elif chart_type == "pie":
            return self.create_pie_chart(df, y_col, x_col, f"{schema.description} - {y_col}分布")
        else:
            return self.create_line_chart(df, x_col, y_col, f"{schema.description} - {y_col}趋势")
    
    def _create_multi_chart_dashboard(self, df: pd.DataFrame, schema, chart_types: List[str]) -> go.Figure:
        """创建多图表仪表板"""
        # 确定子图布局
        n_charts = len(chart_types)
        if n_charts <= 2:
            rows, cols = 1, n_charts
        else:
            rows, cols = 2, 2
        
        fig = sp.make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[f"{schema.description} - {self.chart_types[ct]}" for ct in chart_types],
            specs=[[{"secondary_y": False}] * cols] * rows
        )
        
        # 找到可用的字段
        numeric_fields = [field.name for field in schema.fields if field.type == "number"]
        date_fields = [field.name for field in schema.fields if field.type == "date"]
        text_fields = [field.name for field in schema.fields if field.type == "text"]
        
        for i, chart_type in enumerate(chart_types):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            if chart_type == "line" and numeric_fields and date_fields:
                y_col = numeric_fields[0]
                x_col = date_fields[0]
                fig.add_trace(
                    go.Scatter(x=df[x_col], y=df[y_col], mode='lines+markers', name=y_col),
                    row=row, col=col
                )
            elif chart_type == "bar" and numeric_fields:
                y_col = numeric_fields[0]
                x_col = date_fields[0] if date_fields else df.index
                fig.add_trace(
                    go.Bar(x=df[x_col], y=df[y_col], name=y_col),
                    row=row, col=col
                )
            elif chart_type == "scatter" and len(numeric_fields) >= 2:
                x_col, y_col = numeric_fields[0], numeric_fields[1]
                fig.add_trace(
                    go.Scatter(x=df[x_col], y=df[y_col], mode='markers', name=f"{x_col} vs {y_col}"),
                    row=row, col=col
                )
            elif chart_type == "pie" and numeric_fields and text_fields:
                values_col = numeric_fields[0]
                names_col = text_fields[0]
                fig.add_trace(
                    go.Pie(labels=df[names_col], values=df[values_col]),
                    row=row, col=col
                )
        
        fig.update_layout(
            title=f"{schema.description} 综合仪表板",
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=600,
            showlegend=False
        )
        
        return fig
    
    def _create_text_summary(self, df: pd.DataFrame, schema) -> go.Figure:
        """创建文本摘要图表"""
        fig = go.Figure()
        
        # 创建文本摘要
        summary_text = f"""
        <b>{schema.description}</b><br><br>
        数据行数: {len(df)}<br>
        数据列数: {len(df.columns)}<br>
        时间范围: {df.iloc[0].get('date', 'N/A')} 到 {df.iloc[-1].get('date', 'N/A')}<br>
        数据完整性: {df.notna().sum().sum() / (len(df) * len(df.columns)) * 100:.1f}%
        """
        
        fig.add_annotation(
            text=summary_text,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color=self.color_theme['primary'])
        )
        
        fig.update_layout(
            title=f"{schema.description} 数据摘要",
            template="plotly_white",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_chart(self, df: pd.DataFrame, chart_type: str, x_col: str, y_col: str,
                    title: str = "", **kwargs) -> go.Figure:
        """通用图表创建接口"""
        if chart_type == "line":
            return self.create_line_chart(df, x_col, y_col, title, **kwargs)
        elif chart_type == "bar":
            return self.create_bar_chart(df, x_col, y_col, title, **kwargs)
        elif chart_type == "scatter":
            return self.create_scatter_chart(df, x_col, y_col, title, **kwargs)
        elif chart_type == "pie":
            return self.create_pie_chart(df, y_col, x_col, title)
        elif chart_type == "heatmap":
            return self.create_heatmap(df, x_col, y_col, kwargs.get('values_col', y_col), title)
        elif chart_type == "box":
            return self.create_box_chart(df, x_col, y_col, title)
        elif chart_type == "histogram":
            return self.create_histogram(df, x_col, title)
        elif chart_type == "area":
            return self.create_area_chart(df, x_col, y_col, title)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

class DataAnalyzer:
    """数据分析器 - 提供数据洞察"""
    
    def __init__(self):
        """初始化数据分析器"""
        pass
    
    def analyze_food_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析饮食数据"""
        analysis = {
            'total_records': len(df),
            'date_range': None,
            'avg_calories': None,
            'top_foods': None,
            'nutrition_summary': None,
            'trends': None
        }
        
        if df.empty:
            return analysis
        
        # 日期范围
        if 'date' in df.columns:
            dates = pd.to_datetime(df['date'])
            analysis['date_range'] = {
                'start': dates.min().strftime('%Y-%m-%d'),
                'end': dates.max().strftime('%Y-%m-%d'),
                'days': (dates.max() - dates.min()).days
            }
        
        # 平均卡路里
        if 'calories' in df.columns:
            analysis['avg_calories'] = df['calories'].mean()
        
        # 最常吃的食物
        if 'food_name' in df.columns:
            top_foods = df['food_name'].value_counts().head(5)
            analysis['top_foods'] = top_foods.to_dict()
        
        # 营养摘要
        nutrition_cols = ['protein', 'carbs', 'fat']
        nutrition_data = {}
        for col in nutrition_cols:
            if col in df.columns:
                nutrition_data[col] = {
                    'mean': df[col].mean(),
                    'total': df[col].sum()
                }
        analysis['nutrition_summary'] = nutrition_data
        
        return analysis
    
    def analyze_sleep_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析睡眠数据"""
        analysis = {
            'total_records': len(df),
            'avg_sleep_duration': None,
            'avg_sleep_quality': None,
            'sleep_patterns': None,
            'best_sleep_days': None
        }
        
        if df.empty:
            return analysis
        
        # 平均睡眠时长
        if 'sleep_duration' in df.columns:
            analysis['avg_sleep_duration'] = df['sleep_duration'].mean()
        
        # 平均睡眠质量
        if 'sleep_quality' in df.columns:
            analysis['avg_sleep_quality'] = df['sleep_quality'].mean()
        
        # 睡眠模式
        if 'date' in df.columns and 'sleep_duration' in df.columns:
            sleep_by_date = df.groupby('date')['sleep_duration'].mean()
            analysis['sleep_patterns'] = sleep_by_date.to_dict()
        
        # 最佳睡眠日
        if 'sleep_quality' in df.columns and 'date' in df.columns:
            best_sleep = df.loc[df['sleep_quality'].idxmax()]
            analysis['best_sleep_days'] = {
                'date': str(best_sleep['date']),
                'quality': best_sleep['sleep_quality'],
                'duration': best_sleep.get('sleep_duration', 'N/A')
            }
        
        return analysis
    
    def analyze_training_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析训练数据"""
        analysis = {
            'total_records': len(df),
            'total_duration': None,
            'total_calories_burned': None,
            'avg_intensity': None,
            'training_types': None,
            'performance_trends': None
        }
        
        if df.empty:
            return analysis
        
        # 总训练时长
        if 'duration' in df.columns:
            analysis['total_duration'] = df['duration'].sum()
        
        # 总消耗卡路里
        if 'calories_burned' in df.columns:
            analysis['total_calories_burned'] = df['calories_burned'].sum()
        
        # 平均训练强度
        if 'intensity' in df.columns:
            analysis['avg_intensity'] = df['intensity'].mean()
        
        # 训练类型分布
        if 'training_type' in df.columns:
            training_types = df['training_type'].value_counts()
            analysis['training_types'] = training_types.to_dict()
        
        # 性能趋势
        if 'date' in df.columns and 'duration' in df.columns:
            performance_by_date = df.groupby('date')['duration'].sum()
            analysis['performance_trends'] = performance_by_date.to_dict()
        
        return analysis
    
    def analyze_weight_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析体重数据"""
        analysis = {
            'total_records': len(df),
            'weight_change': None,
            'current_weight': None,
            'weight_trend': None,
            'body_composition': None
        }
        
        if df.empty:
            return analysis
        
        # 体重变化
        if 'weight' in df.columns and 'date' in df.columns:
            df_sorted = df.sort_values('date')
            first_weight = df_sorted['weight'].iloc[0]
            last_weight = df_sorted['weight'].iloc[-1]
            analysis['weight_change'] = last_weight - first_weight
            analysis['current_weight'] = last_weight
        
        # 体重趋势
        if 'weight' in df.columns and 'date' in df.columns:
            weight_trend = df.groupby('date')['weight'].mean()
            analysis['weight_trend'] = weight_trend.to_dict()
        
        # 身体成分
        body_comp = {}
        for col in ['body_fat', 'muscle_mass', 'water_percentage']:
            if col in df.columns:
                body_comp[col] = {
                    'current': df[col].iloc[-1],
                    'avg': df[col].mean(),
                    'min': df[col].min(),
                    'max': df[col].max()
                }
        analysis['body_composition'] = body_comp
        
        return analysis
