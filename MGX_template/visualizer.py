"""
Visualization module for interactive charts and data display
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from config import ui_config
from exception_handler import exception_handler, ExceptionLevel

class Visualizer:
    """Interactive visualization generator with Material3 styling"""
    
    def __init__(self):
        self.color_palette = {
            'primary': ui_config.primary_color,
            'secondary': ui_config.secondary_color,
            'surface': ui_config.surface_color,
            'error': ui_config.error_color,
            'success': ui_config.success_color,
            'warning': ui_config.warning_color
        }
    
    def create_diet_visualizations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create diet-related visualizations"""
        try:
            visualizations = {}
            
            if df.empty:
                return self._create_empty_state_charts("diet")
            
            # Diet content distribution (pie chart)
            if 'diet_content' in df.columns:
                diet_data = self._process_diet_data(df)
                if diet_data:
                    visualizations['diet_distribution'] = self._create_diet_pie_chart(diet_data)
            
            # Daily entries over time (bar chart)
            if 'date' in df.columns or 'timestamp' in df.columns:
                visualizations['diet_timeline'] = self._create_diet_timeline(df)
            
            return visualizations
            
        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_3,
                e,
                context={'chart_type': 'diet', 'raw_data': df.to_dict() if not df.empty else {}}
            )
            return self._create_error_charts("diet")
    
    def create_training_visualizations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create training-related visualizations"""
        try:
            visualizations = {}
            
            if df.empty:
                return self._create_empty_state_charts("training")
            
            # Training load trends (line chart)
            if 'training_load' in df.columns:
                visualizations['training_trends'] = self._create_training_line_chart(df)
            
            # Training frequency heatmap
            if 'date' in df.columns or 'timestamp' in df.columns:
                visualizations['training_heatmap'] = self._create_training_heatmap(df)
            
            return visualizations
            
        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_3,
                e,
                context={'chart_type': 'training', 'raw_data': df.to_dict() if not df.empty else {}}
            )
            return self._create_error_charts("training")
    
    def create_sleep_visualizations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create sleep-related visualizations"""
        try:
            visualizations = {}
            
            if df.empty:
                return self._create_empty_state_charts("sleep")
            
            # Sleep duration bar chart
            if 'sleep_data' in df.columns:
                visualizations['sleep_duration'] = self._create_sleep_bar_chart(df)
            
            # Sleep quality trends
            if 'date' in df.columns or 'timestamp' in df.columns:
                visualizations['sleep_trends'] = self._create_sleep_line_chart(df)
            
            return visualizations
            
        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_3,
                e,
                context={'chart_type': 'sleep', 'raw_data': df.to_dict() if not df.empty else {}}
            )
            return self._create_error_charts("sleep")
    
    def create_overview_dashboard(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create comprehensive overview dashboard"""
        try:
            if df.empty:
                return self._create_empty_state_charts("overview")
            
            dashboard = {}
            
            # Confidence score trends
            if 'confidence_score' in df.columns:
                dashboard['confidence_trends'] = self._create_confidence_chart(df)
            
            # Data completeness radar chart
            dashboard['data_completeness'] = self._create_completeness_radar(df)
            
            # Summary metrics
            dashboard['summary_metrics'] = self._create_summary_metrics(df)
            
            return dashboard
            
        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_3,
                e,
                context={'chart_type': 'overview', 'raw_data': df.to_dict() if not df.empty else {}}
            )
            return self._create_error_charts("overview")
    
    def _process_diet_data(self, df: pd.DataFrame) -> List[Dict]:
        """Process diet content for visualization"""
        diet_items = []
        for _, row in df.iterrows():
            diet_content = row.get('diet_content', '')
            if diet_content:
                # Split diet content and count occurrences
                items = diet_content.split(';') if isinstance(diet_content, str) else diet_content
                for item in items:
                    if item.strip():
                        diet_items.append(item.strip().lower())
        
        # Count occurrences
        from collections import Counter
        diet_counts = Counter(diet_items)
        
        return [{'item': item, 'count': count} for item, count in diet_counts.most_common(10)]
    
    def _create_diet_pie_chart(self, diet_data: List[Dict]) -> go.Figure:
        """Create diet distribution pie chart"""
        if not diet_data:
            return self._create_placeholder_chart("No diet data available")
        
        df_diet = pd.DataFrame(diet_data)
        
        fig = px.pie(
            df_diet, 
            values='count', 
            names='item',
            title="Diet Content Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            font=dict(size=14),
            title_font_size=18,
            showlegend=True,
            height=400
        )
        
        return fig
    
    def _create_diet_timeline(self, df: pd.DataFrame) -> go.Figure:
        """Create diet entries timeline"""
        # Process dates
        df_copy = df.copy()
        if 'date' in df_copy.columns:
            date_col = 'date'
        else:
            date_col = 'timestamp'
            df_copy['date'] = pd.to_datetime(df_copy['timestamp']).dt.date
        
        # Count entries per date
        daily_counts = df_copy.groupby('date').size().reset_index(name='count')
        
        fig = px.bar(
            daily_counts,
            x='date',
            y='count',
            title="Daily Diet Entries",
            color='count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Entries",
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def _create_training_line_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create training load trends line chart"""
        # Extract numeric values from training_load
        df_copy = df.copy()
        df_copy['training_numeric'] = df_copy['training_load'].str.extract('(\d+)').astype(float)
        
        # Use date or timestamp
        if 'date' in df_copy.columns:
            x_col = 'date'
        else:
            df_copy['date'] = pd.to_datetime(df_copy['timestamp']).dt.date
            x_col = 'date'
        
        fig = px.line(
            df_copy.dropna(subset=['training_numeric']),
            x=x_col,
            y='training_numeric',
            title="Training Load Trends",
            markers=True
        )
        
        fig.update_traces(line_color=self.color_palette['primary'])
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Training Load",
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def _create_training_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """Create training frequency heatmap"""
        # Simple frequency heatmap by day of week
        df_copy = df.copy()
        if 'date' not in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['timestamp']).dt.date
        
        df_copy['day_of_week'] = pd.to_datetime(df_copy['date']).dt.day_name()
        df_copy['week'] = pd.to_datetime(df_copy['date']).dt.isocalendar().week
        
        heatmap_data = df_copy.groupby(['week', 'day_of_week']).size().unstack(fill_value=0)
        
        fig = px.imshow(
            heatmap_data.values,
            labels=dict(x="Day of Week", y="Week", color="Training Sessions"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            title="Training Frequency Heatmap",
            color_continuous_scale="Blues"
        )
        
        fig.update_layout(height=400)
        
        return fig
    
    def _create_sleep_bar_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create sleep duration bar chart"""
        # Extract numeric sleep hours
        df_copy = df.copy()
        df_copy['sleep_hours'] = df_copy['sleep_data'].str.extract('(\d+)').astype(float)
        
        if 'date' not in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['timestamp']).dt.date
        
        fig = px.bar(
            df_copy.dropna(subset=['sleep_hours']),
            x='date',
            y='sleep_hours',
            title="Daily Sleep Duration",
            color='sleep_hours',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Sleep Hours",
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def _create_sleep_line_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create sleep quality trends"""
        df_copy = df.copy()
        df_copy['sleep_hours'] = df_copy['sleep_data'].str.extract('(\d+)').astype(float)
        
        if 'date' not in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['timestamp']).dt.date
        
        fig = px.line(
            df_copy.dropna(subset=['sleep_hours']),
            x='date',
            y='sleep_hours',
            title="Sleep Quality Trends",
            markers=True
        )
        
        fig.update_traces(line_color=self.color_palette['success'])
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Sleep Hours",
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def _create_confidence_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create OCR confidence trends chart"""
        if 'date' not in df.columns:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
        
        fig = px.line(
            df,
            x='date',
            y='confidence_score',
            title="OCR Confidence Score Trends",
            markers=True
        )
        
        fig.update_traces(line_color=self.color_palette['warning'])
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Confidence Score",
            yaxis_range=[0, 1],
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def _create_completeness_radar(self, df: pd.DataFrame) -> go.Figure:
        """Create data completeness radar chart"""
        completeness = {
            'Name': (df['name'] != '').sum() / len(df) * 100,
            'Date': (df['date'] != '').sum() / len(df) * 100,
            'Diet': (df['diet_content'] != '').sum() / len(df) * 100,
            'Training': (df['training_load'] != '').sum() / len(df) * 100,
            'Sleep': (df['sleep_data'] != '').sum() / len(df) * 100
        }
        
        categories = list(completeness.keys())
        values = list(completeness.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Data Completeness %',
            line_color=self.color_palette['primary']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Data Completeness Overview",
            height=400
        )
        
        return fig
    
    def _create_summary_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create summary metrics for dashboard"""
        metrics = {
            'total_entries': len(df),
            'avg_confidence': df['confidence_score'].mean() if 'confidence_score' in df.columns else 0,
            'data_completeness': {
                'diet': (df['diet_content'] != '').sum() / len(df) * 100 if len(df) > 0 else 0,
                'training': (df['training_load'] != '').sum() / len(df) * 100 if len(df) > 0 else 0,
                'sleep': (df['sleep_data'] != '').sum() / len(df) * 100 if len(df) > 0 else 0
            },
            'date_range': {
                'start': df['date'].min() if 'date' in df.columns and not df.empty else 'N/A',
                'end': df['date'].max() if 'date' in df.columns and not df.empty else 'N/A'
            }
        }
        
        return metrics
    
    def _create_empty_state_charts(self, chart_type: str) -> Dict[str, Any]:
        """Create empty state visualizations"""
        empty_fig = self._create_placeholder_chart(f"No {chart_type} data available. Upload files to see visualizations.")
        
        return {
            f'{chart_type}_placeholder': empty_fig
        }
    
    def _create_error_charts(self, chart_type: str) -> Dict[str, Any]:
        """Create error state visualizations"""
        error_fig = self._create_placeholder_chart(f"Error generating {chart_type} visualizations. Check data format.")
        
        return {
            f'{chart_type}_error': error_fig
        }
    
    def _create_placeholder_chart(self, message: str) -> go.Figure:
        """Create placeholder chart with message"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16, color=self.color_palette['secondary']),
            showarrow=False
        )
        
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig

# Global visualizer instance
visualizer = Visualizer()