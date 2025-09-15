import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from datetime import datetime, timedelta
from PIL import Image
import io
import base64

# Import custom modules
from config import APP_CONFIG, NUTRITION_TARGETS
from ocr_processor import OCRProcessor
from food_classifier import FoodClassifier
from nutrition_analyzer import NutritionAnalyzer
from visualization import NutritionVisualizer

# Helpers
def safe_parse_json(possibly_json_str: str):
    """Parse JSON robustly from a model response that may contain code fences or extra text."""
    if not possibly_json_str:
        return None
    text = possibly_json_str.strip()
    # Remove common code fences
    if text.startswith("```"):
        text = text.strip("`")
    # Trim to first '{' and last '}'
    first = text.find('{')
    last = text.rfind('}')
    if first != -1 and last != -1 and last > first:
        text = text[first:last+1]
    try:
        return json.loads(text)
    except Exception:
        return None

# Page configuration
st.set_page_config(
    page_title=APP_CONFIG["title"],
    page_icon=APP_CONFIG["page_icon"],
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["initial_sidebar_state"]
)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize all components"""
    return {
        "ocr": OCRProcessor(),
        "classifier": FoodClassifier(),
        "analyzer": NutritionAnalyzer(),
        "visualizer": NutritionVisualizer()
    }

# Custom CSS styles
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        text-align: right;
    }
    .ai-message {
        background-color: #e9ecef;
        color: black;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
    }
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize components
    components = init_components()
    
    # Sidebar
    with st.sidebar:
        st.title("🏇 Jockey Nutrition AI")
        st.markdown("---")
        
        # Function selection
        page = st.selectbox(
            "Select Function",
            ["📷 Image Recognition", "💬 Text Analysis", "📊 Nutrition Analysis", "📈 Trend Analysis", "⚙️ Settings"]
        )
        
        st.markdown("---")
        
        # Nutrition goals
        st.subheader("Nutrition Goals")
        target_type = st.selectbox(
            "Select Goal Type",
            ["Weight Management", "Energy Boost"]
        )
        
        st.markdown("---")
        
        # Personal information
        st.subheader("Personal Information")
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=150.0, value=70.0)
        height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0)
        
        # BMI calculation
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        st.metric("BMI", f"{bmi:.1f}")
        
        if bmi < 18.5:
            st.warning("Underweight")
        elif bmi < 24:
            st.success("Normal Weight")
        elif bmi < 28:
            st.warning("Overweight")
        else:
            st.error("Obese")
    
    # Main content area
    if page == "📷 Image Recognition":
        show_image_recognition(components)
    elif page == "💬 Text Analysis":
        show_text_analysis(components)
    elif page == "📊 Nutrition Analysis":
        show_nutrition_analysis(components, target_type)
    elif page == "📈 Trend Analysis":
        show_trend_analysis(components)
    elif page == "⚙️ Settings":
        show_settings()

def show_image_recognition(components):
    """Image recognition page"""
    st.markdown('<h1 class="main-header">📷 Image Recognition Analysis</h1>', unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Food Image",
        type=['png', 'jpg', 'jpeg'],
        help="Supports PNG, JPG, JPEG formats"
    )
    
    if uploaded_file is not None:
        # Display image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        # OCR processing
        if st.button("Start Recognition", type="primary"):
            with st.spinner("Recognizing text in image..."):
                # OCR text recognition (force English output)
                ocr_text = components["ocr"].extract_text_from_image(image, language="en")
                
                # Display OCR results
                st.subheader("Recognition Results")
                st.text_area("Extracted Text", ocr_text, height=200)
                
                # Food analysis
                with st.spinner("Analyzing food content..."):
                    food_analysis = components["ocr"].analyze_food_content(ocr_text)
                    
                    st.subheader("Food Analysis")
                    st.text_area("Analysis Results", food_analysis, height=200)
                    
                    # Try to parse JSON results
                    food_data = safe_parse_json(food_analysis)
                    if food_data and isinstance(food_data, dict) and "foods" in food_data:
                        st.subheader("Identified Foods")
                        for food in food_data["foods"]:
                            st.write(f"• {food.get('name', '')} - {food.get('category', '')}")

                        # Nutrition analysis using analyzer
                        try:
                            nutrition_result = components["analyzer"].analyze_meal(food_data["foods"])
                            if nutrition_result and "total_nutrition" in nutrition_result:
                                totals = nutrition_result["total_nutrition"]
                                st.subheader("Nutrition Analysis")
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Calories", f"{totals.get('calories', 0)} kcal")
                                with col2:
                                    st.metric("Protein", f"{totals.get('protein', 0)} g")
                                with col3:
                                    st.metric("Carbs", f"{totals.get('carbs', 0)} g")
                                with col4:
                                    st.metric("Fat", f"{totals.get('fat', 0)} g")
                        except Exception as e:
                            st.error(f"Nutrition analysis failed: {e}")
                    else:
                        st.warning("Unable to parse food analysis results")

def show_text_analysis(components):
    """Text analysis page"""
    st.markdown('<h1 class="main-header">💬 Text Analysis</h1>', unsafe_allow_html=True)
    
    # Text input
    text_input = st.text_area(
        "Enter food description or meal text",
        height=200,
        placeholder="Example: I ate grilled chicken with rice and vegetables for lunch..."
    )
    
    if st.button("Analyze Text", type="primary"):
        if text_input.strip():
            with st.spinner("Analyzing text..."):
                # Food classification
                food_items = components["classifier"].classify_food(text_input)
                
                if food_items:
                    st.subheader("Detected Food Items")
                    for food in food_items:
                        st.write(f"• {food}")
                    
                    # Nutrition analysis
                    nutrition_data = components["analyzer"].analyze_nutrition(food_items)
                    
                    if nutrition_data:
                        st.subheader("Nutrition Analysis")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Calories", f"{nutrition_data.get('calories', 0)} kcal")
                        with col2:
                            st.metric("Protein", f"{nutrition_data.get('protein', 0)}g")
                        with col3:
                            st.metric("Carbs", f"{nutrition_data.get('carbs', 0)}g")
                        with col4:
                            st.metric("Fat", f"{nutrition_data.get('fat', 0)}g")
                        
                        # Visualization
                        if components["visualizer"]:
                            fig = components["visualizer"].create_nutrition_chart(nutrition_data)
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No food items detected in the text")
        else:
            st.warning("Please enter some text to analyze")

def show_nutrition_analysis(components, target_type):
    """Nutrition analysis page"""
    st.markdown('<h1 class="main-header">📊 Nutrition Analysis</h1>', unsafe_allow_html=True)
    
    # Target nutrition display
    st.subheader(f"Target Nutrition Goals: {target_type}")
    
    targets = NUTRITION_TARGETS.get(target_type, {})
    if targets:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Calories", f"{targets.get('Calories', {}).get('target', 0)} kcal")
        with col2:
            st.metric("Protein", f"{targets.get('Protein', {}).get('target', 0)}g")
        with col3:
            st.metric("Carbs", f"{targets.get('Carbohydrates', {}).get('target', 0)}g")
        with col4:
            st.metric("Fat", f"{targets.get('Fat', {}).get('target', 0)}g")
        with col5:
            st.metric("Fiber", f"{targets.get('Fiber', {}).get('target', 0)}g")
    
    # Sample data visualization
    st.subheader("Sample Nutrition Data")
    
    # Create sample data
    sample_data = {
        'calories': 1850,
        'protein': 95,
        'carbs': 180,
        'fat': 65,
        'fiber': 22
    }
    
    if components["visualizer"]:
        fig = components["visualizer"].create_nutrition_chart(sample_data)
        st.plotly_chart(fig, use_container_width=True)

def show_trend_analysis(components):
    """Trend analysis page"""
    st.markdown('<h1 class="main-header">📈 Trend Analysis</h1>', unsafe_allow_html=True)
    
    # Sample trend data
    st.subheader("Nutrition Trends Over Time")
    
    # Create sample trend data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    calories = np.random.normal(2000, 200, len(dates))
    
    trend_data = pd.DataFrame({
        'Date': dates,
        'Calories': calories,
        'Protein': np.random.normal(120, 15, len(dates)),
        'Carbs': np.random.normal(200, 30, len(dates)),
        'Fat': np.random.normal(60, 10, len(dates))
    })
    
    # Display trend chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_data['Date'], y=trend_data['Calories'], 
                             mode='lines+markers', name='Calories'))
    fig.update_layout(title="Daily Calorie Intake Trend",
                     xaxis_title="Date",
                     yaxis_title="Calories (kcal)")
    
    st.plotly_chart(fig, use_container_width=True)

def show_settings():
    """Settings page"""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    st.subheader("Application Settings")
    
    # API settings
    st.write("**OpenAI API Configuration**")
    api_key = st.text_input("OpenAI API Key (从环境变量读取，允许临时覆盖)", type="password", value="")
    if api_key:
        st.session_state["OPENAI_API_KEY"] = api_key
    
    # Display settings
    st.write("**Display Settings**")
    theme = st.selectbox("Theme", ["Light", "Dark"])
    language = st.selectbox("Language", ["English", "Chinese"])
    
    # Save settings
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")

if __name__ == "__main__":
    main()
