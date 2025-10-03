import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from datetime import datetime, timedelta
from PIL import Image
import io
import base64
import os

# Import custom modules
from config import APP_CONFIG, NUTRITION_TARGETS, OPENAI_API_KEY
from ocr_processor import OCRProcessor
from food_classifier import FoodClassifier
from nutrition_analyzer import NutritionAnalyzer
from visualization import NutritionVisualizer
from pdf_processor import PDFProcessor

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
def init_components(api_key: str):
    """Initialize all components based on current API key."""
    # Components requiring OpenAI key are initialized only when key is provided
    ocr = OCRProcessor()
    pdf_proc = PDFProcessor()
    return {
        "ocr": ocr,
        "classifier": FoodClassifier(),
        "analyzer": NutritionAnalyzer(),
        "visualizer": NutritionVisualizer(),
        "pdf_processor": pdf_proc
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
    # Initialize or read API key from session/env
    if "api_key" not in st.session_state:
        st.session_state["api_key"] = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    # Top-of-page API key input (visible and editable)
    st.markdown('<h1 class="main-header">🏇 Jockey Nutrition AI</h1>', unsafe_allow_html=True)
    api_key_input = st.text_input("OpenAI API Key", value=st.session_state["api_key"], help="Takes effect immediately after save; you can modify anytime")
    col_save1, col_save2 = st.columns(2)
    with col_save1:
        if st.button("Save API Key", type="primary"):
            new_key = api_key_input.strip()
            os.environ["OPENAI_API_KEY"] = new_key
            import config as cfg
            cfg.OPENAI_API_KEY = new_key
            st.session_state["api_key"] = new_key
            st.cache_resource.clear()
            st.success("API Key saved. App refreshed.")
            st.rerun()
    with col_save2:
        if st.button("Clear API Key"):
            os.environ["OPENAI_API_KEY"] = ""
            import config as cfg
            cfg.OPENAI_API_KEY = ""
            st.session_state["api_key"] = ""
            st.cache_resource.clear()
            st.warning("API Key cleared")
            st.rerun()

    api_ready = bool(st.session_state.get("api_key") and st.session_state.get("api_key").startswith("sk-"))

    # Initialize components only when API key is ready
    components = None
    if api_ready:
        components = init_components(st.session_state["api_key"])    
    
    # Sidebar
    with st.sidebar:
        st.title("🏇 Jockey Nutrition AI")
        st.markdown("---")
        
        # Function selection
        page = st.selectbox(
            "Select Function",
            ["📄 PDF Analysis", "📷 Image Recognition", "💬 Text Analysis", "⚙️ Settings"]
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
    if page == "📄 PDF Analysis":
        if not api_ready:
            st.warning("Please set a valid OpenAI API Key at the top to use this feature.")
            return
        show_pdf_analysis(components)
    elif page == "📷 Image Recognition":
        if not api_ready:
            st.warning("Please set a valid OpenAI API Key at the top to use this feature.")
            return
        show_image_recognition(components)
    elif page == "💬 Text Analysis":
        if not api_ready:
            st.warning("Please set a valid OpenAI API Key at the top to use this feature.")
            return
        show_text_analysis(components)
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

def show_pdf_analysis(components):
    """PDF analysis page"""
    st.markdown('<h1 class="main-header">📄 PDF Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📋 Feature Description
    Upload a PDF file containing food information, and the system will:
    - 🔍 Recognize text content from all pages in the PDF
    - 🍽️ Extract all food data and categorize them
    - 📊 Generate a pie chart showing food category distribution
    - 💡 Provide personalized dietary advice report
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload PDF File",
        type=['pdf'],
        help="Supports multi-page PDF files containing food information, nutrition labels, etc."
    )
    
    if uploaded_file is not None:
        # Display file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
        st.info(f"📄 File size: {file_size_mb:.1f} MB")
        
        # Performance tips
        if file_size_mb > 10:
            st.warning("⚠️ Large file, processing may take longer, please be patient...")
        elif file_size_mb > 5:
            st.info("💡 Large file, estimated processing time: 2-5 minutes")
        else:
            st.info("💡 Estimated processing time: 30 seconds - 2 minutes")
        
        # Language selection
        language = st.selectbox(
            "Select Recognition Language",
            ["English"],
            index=0
        )
        
        # Processing options
        col1, col2 = st.columns(2)
        with col1:
            processing_mode = st.selectbox(
                "Processing Mode",
                ["Standard Mode", "Fast Mode"],
                index=0,
                help="Fast Mode: Reduces image quality to improve processing speed"
            )
        with col2:
            if file_size_mb > 5:
                st.info("💡 Large files recommended to use Fast Mode")
        
        # Process button
        if st.button("Start PDF Analysis", type="primary"):
            try:
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(message, progress):
                    progress_bar.progress(progress)
                    status_text.text(message)
                
                # Process PDF with progress
                pdf_lang = "en"
                fast_mode = processing_mode == "Fast Mode"
                pdf_result = components["pdf_processor"].process_pdf_content(
                    uploaded_file, 
                    language=pdf_lang,
                    progress_callback=update_progress,
                    fast_mode=fast_mode
                )
                
                # Clear progress bar
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                st.success(f"✅ PDF processing completed! Processed {pdf_result['total_pages']} pages")
                
                # Create tabs for different sections
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📄 Page Content", "🍽️ Food Data", "📊 Nutrition Analysis", "🥧 Category Distribution", "💡 Dietary Advice"
                ])
                
                with tab1:
                        st.subheader("📄 Extracted Text Content")
                        st.text_area(
                            "Text content from all pages",
                            value=pdf_result['all_text'],
                            height=300,
                            disabled=True
                        )
                        
                        # Show page-by-page results
                        st.subheader("📄 Page Details")
                        for page_result in pdf_result['page_results']:
                            with st.expander(f"Page {page_result['page_number']}"):
                                st.text_area(
                                    f"Page {page_result['page_number']} text",
                                    value=page_result['text'],
                                    height=150,
                                    disabled=True
                                )
                
                with tab2:
                    st.subheader("🍽️ Identified Foods")
                    if pdf_result['all_foods']:
                        # Show food count
                        st.success(f"📊 Total identified foods: {len(pdf_result['all_foods'])}")
                        
                        # Create DataFrame for better display
                        foods_df = pd.DataFrame(pdf_result['all_foods'])
                        st.dataframe(foods_df, use_container_width=True)
                        
                        # Show food details
                        st.subheader("🍽️ Food Details")
                        for i, food in enumerate(pdf_result['all_foods'], 1):
                            with st.expander(f"{i}. {food.get('name', 'Unknown Food')}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Category**: {food.get('category', 'Unknown')}")
                                    st.write(f"**Quantity**: {food.get('quantity', 'Unknown')}")
                                with col2:
                                    st.write(f"**Calories**: {food.get('calories', 0)} kcal")
                                    st.write(f"**Protein**: {food.get('protein', 0)} g")
                                    st.write(f"**Carbohydrates**: {food.get('carbs', 0)} g")
                                    st.write(f"**Fat**: {food.get('fat', 0)} g")
                    else:
                        st.warning("⚠️ No food information identified")
                        st.info("💡 This might be because:")
                        st.write("  • No clear food information in the PDF")
                        st.write("  • Text recognition is not accurate")
                        st.write("  • Need to adjust recognition language settings")
                
                with tab3:
                    st.subheader("📊 Nutrition Analysis")
                    total_nutrition = pdf_result['total_nutrition']
                    
                    # Display nutrition metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Calories", f"{total_nutrition['calories']:.1f} kcal")
                    with col2:
                        st.metric("Protein", f"{total_nutrition['protein']:.1f} g")
                    with col3:
                        st.metric("Carbohydrates", f"{total_nutrition['carbs']:.1f} g")
                    with col4:
                        st.metric("Fat", f"{total_nutrition['fat']:.1f} g")
                    
                    # Nutrition breakdown chart
                    if components["visualizer"]:
                        nutrition_data = {
                            "Protein": total_nutrition['protein'] * 4,  # 4 kcal/g
                            "Carbohydrates": total_nutrition['carbs'] * 4,  # 4 kcal/g
                            "Fat": total_nutrition['fat'] * 9  # 9 kcal/g
                        }
                        fig = components["visualizer"].create_nutrition_pie_chart(nutrition_data)
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab4:
                    st.subheader("🥧 Food Category Distribution")
                    food_categories = pdf_result['food_categories']
                    
                    # Show debug info
                    st.info(f"📊 Detected {len(food_categories)} food categories")
                    
                    if food_categories:
                        # Display category counts
                        st.write("📈 Food count by category:")
                        for category, count in food_categories.items():
                            st.write(f"  • {category}: {count} items")
                        
                        # Create pie chart
                        if components["visualizer"]:
                            try:
                                fig = components["visualizer"].create_food_category_pie_chart(food_categories)
                                st.plotly_chart(fig, use_container_width=True)
                                st.success("✅ Pie chart generated successfully!")
                            except Exception as e:
                                st.error(f"❌ Failed to generate pie chart: {str(e)}")
                                # Show raw data
                                st.write("Raw data:", food_categories)
                    else:
                        st.warning("⚠️ No food category data available")
                        st.info("💡 This might be because no food information was identified, please check PDF content")
                
                with tab5:
                    st.subheader("💡 Dietary Advice Report")
                    dietary_advice = pdf_result['dietary_advice']
                    
                    # Display advice in a nice format
                    st.markdown("""
                    <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border-left: 4px solid #007bff;">
                    """, unsafe_allow_html=True)
                    
                    # Split advice into lines and format
                    advice_lines = dietary_advice.split('\n')
                    for line in advice_lines:
                        if line.strip():
                            if line.startswith('📊') or line.startswith('🍽️') or line.startswith('📈') or line.startswith('💡'):
                                st.markdown(f"**{line}**")
                            elif line.startswith('⚠️'):
                                st.markdown(f"<span style='color: #ff6b35;'>{line}</span>", unsafe_allow_html=True)
                            elif line.startswith('✅'):
                                st.markdown(f"<span style='color: #28a745;'>{line}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(line)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Export option
                    st.download_button(
                        label="📥 Download Analysis Report",
                        data=dietary_advice,
                        file_name=f"nutrition_analysis_report_{uploaded_file.name.replace('.pdf', '')}.txt",
                        mime="text/plain"
                    )
            
            except Exception as e:
                st.error(f"❌ PDF processing failed: {str(e)}")
                st.info("💡 Please ensure the PDF file contains clear food information or nutrition labels")

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
    
    # Read current API key status from config
    from config import OPENAI_API_KEY
    api_key_configured = bool(OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"))
    
    if api_key_configured:
        st.success("✅ API key configured via environment variable")
        st.info("API key is securely stored in environment variables. To change, modify the `.env` file or set environment variables.")
    else:
        st.warning("⚠️ API key not configured")
        st.error("Please follow these steps to configure the API key:")
        st.markdown("""
        1. Create a `.env` file in the project root directory
        2. Add the following content: `OPENAI_API_KEY=your-api-key-here`
        3. Restart the application
        
        Or set environment variable:
        ```bash
        export OPENAI_API_KEY="your-api-key-here"
        ```
        """)
    
    # API key validation (for testing only)
    if st.button("Test API Key Connection"):
        if api_key_configured:
            try:
                import openai
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                # Try to call API to validate key
                client.models.list()
                st.success("✅ API key validation successful!")
            except Exception as e:
                error_msg = str(e)
                if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                    st.error("❌ API key is invalid or expired")
                elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                    st.error("❌ API quota exceeded or insufficient account balance")
                else:
                    st.error(f"❌ API key validation failed: {error_msg}")
        else:
            st.error("❌ Please configure API key first")
    
    # Display settings
    st.write("**Display Settings**")
    theme = st.selectbox("Theme", ["Light", "Dark"])
    language = st.selectbox("Language", ["English", "Chinese"])
    
    # Show current status
    st.write("**Current Status**")
    if api_key_configured:
        st.success("✅ API key configured, OCR functionality available")
    else:
        st.warning("⚠️ API key not configured, OCR functionality will not be available")

if __name__ == "__main__":
    main()
