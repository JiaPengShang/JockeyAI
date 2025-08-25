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
def init_components():
    """Initialize all components"""
    return {
        "ocr": OCRProcessor(),
        "classifier": FoodClassifier(),
        "analyzer": NutritionAnalyzer(),
        "visualizer": NutritionVisualizer(),
        "pdf_processor": PDFProcessor()
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
            ["📄 PDF Analysis", "📷 Image Recognition", "💬 Text Analysis", "📊 Nutrition Analysis", "📈 Trend Analysis", "⚙️ Settings"]
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
        show_pdf_analysis(components)
    elif page == "📷 Image Recognition":
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

def show_pdf_analysis(components):
    """PDF analysis page"""
    st.markdown('<h1 class="main-header">📄 PDF Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📋 功能说明
    上传包含食物信息的PDF文件，系统将：
    - 🔍 识别PDF中所有页面的文字内容
    - 🍽️ 提取所有食物数据并进行分类
    - 📊 生成食物类别分布饼图
    - 💡 提供个性化饮食建议报告
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "上传PDF文件",
        type=['pdf'],
        help="支持多页面PDF文件，包含食物信息、营养标签等"
    )
    
    if uploaded_file is not None:
        # Display file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"✅ 文件上传成功: {uploaded_file.name}")
        st.info(f"📄 文件大小: {file_size_mb:.1f} MB")
        
        # 性能提示
        if file_size_mb > 10:
            st.warning("⚠️ 文件较大，处理时间可能较长，请耐心等待...")
        elif file_size_mb > 5:
            st.info("💡 文件较大，预计处理时间：2-5分钟")
        else:
            st.info("💡 预计处理时间：30秒-2分钟")
        
        # Language selection
        language = st.selectbox(
            "选择识别语言",
            ["中文", "English"],
            index=0
        )
        
        # 处理选项
        col1, col2 = st.columns(2)
        with col1:
            processing_mode = st.selectbox(
                "处理模式",
                ["标准模式", "快速模式"],
                index=0,
                help="快速模式：降低图像质量以提高处理速度"
            )
        with col2:
            if file_size_mb > 5:
                st.info("💡 大文件建议使用快速模式")
        
        # Process button
        if st.button("开始分析PDF", type="primary"):
            try:
                # 创建进度条
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(message, progress):
                    progress_bar.progress(progress)
                    status_text.text(message)
                
                # Process PDF with progress
                pdf_lang = "zh" if language == "中文" else "en"
                fast_mode = processing_mode == "快速模式"
                pdf_result = components["pdf_processor"].process_pdf_content(
                    uploaded_file, 
                    language=pdf_lang,
                    progress_callback=update_progress,
                    fast_mode=fast_mode
                )
                
                # 清除进度条
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                st.success(f"✅ PDF处理完成！共处理 {pdf_result['total_pages']} 页")
                
                # Create tabs for different sections
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📄 页面内容", "🍽️ 食物数据", "📊 营养分析", "🥧 类别分布", "💡 饮食建议"
                ])
                
                with tab1:
                        st.subheader("📄 提取的文字内容")
                        st.text_area(
                            "所有页面的文字内容",
                            value=pdf_result['all_text'],
                            height=300,
                            disabled=True
                        )
                        
                        # Show page-by-page results
                        st.subheader("📄 分页详情")
                        for page_result in pdf_result['page_results']:
                            with st.expander(f"第 {page_result['page_number']} 页"):
                                st.text_area(
                                    f"第 {page_result['page_number']} 页文字",
                                    value=page_result['text'],
                                    height=150,
                                    disabled=True
                                )
                
                with tab2:
                    st.subheader("🍽️ 识别的食物")
                    if pdf_result['all_foods']:
                        # Show food count
                        st.success(f"📊 共识别到 {len(pdf_result['all_foods'])} 种食物")
                        
                        # Create DataFrame for better display
                        foods_df = pd.DataFrame(pdf_result['all_foods'])
                        st.dataframe(foods_df, use_container_width=True)
                        
                        # 显示食物详情
                        st.subheader("🍽️ 食物详情")
                        for i, food in enumerate(pdf_result['all_foods'], 1):
                            with st.expander(f"{i}. {food.get('name', '未知食物')}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**类别**: {food.get('category', '未知')}")
                                    st.write(f"**数量**: {food.get('quantity', '未知')}")
                                with col2:
                                    st.write(f"**热量**: {food.get('calories', 0)} kcal")
                                    st.write(f"**蛋白质**: {food.get('protein', 0)} g")
                                    st.write(f"**碳水化合物**: {food.get('carbs', 0)} g")
                                    st.write(f"**脂肪**: {food.get('fat', 0)} g")
                    else:
                        st.warning("⚠️ 未识别到任何食物信息")
                        st.info("💡 这可能是因为：")
                        st.write("  • PDF中没有清晰的食物信息")
                        st.write("  • 文字识别不准确")
                        st.write("  • 需要调整识别语言设置")
                
                with tab3:
                    st.subheader("📊 营养分析")
                    total_nutrition = pdf_result['total_nutrition']
                    
                    # Display nutrition metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总热量", f"{total_nutrition['calories']:.1f} kcal")
                    with col2:
                        st.metric("蛋白质", f"{total_nutrition['protein']:.1f} g")
                    with col3:
                        st.metric("碳水化合物", f"{total_nutrition['carbs']:.1f} g")
                    with col4:
                        st.metric("脂肪", f"{total_nutrition['fat']:.1f} g")
                    
                    # Nutrition breakdown chart
                    if components["visualizer"]:
                        nutrition_data = {
                            "蛋白质": total_nutrition['protein'] * 4,  # 4 kcal/g
                            "碳水化合物": total_nutrition['carbs'] * 4,  # 4 kcal/g
                            "脂肪": total_nutrition['fat'] * 9  # 9 kcal/g
                        }
                        fig = components["visualizer"].create_nutrition_pie_chart(nutrition_data)
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab4:
                    st.subheader("🥧 食物类别分布")
                    food_categories = pdf_result['food_categories']
                    
                    # 显示调试信息
                    st.info(f"📊 检测到 {len(food_categories)} 个食物类别")
                    
                    if food_categories:
                        # Display category counts
                        st.write("📈 各类别食物数量:")
                        for category, count in food_categories.items():
                            st.write(f"  • {category}: {count} 种")
                        
                        # Create pie chart
                        if components["visualizer"]:
                            try:
                                fig = components["visualizer"].create_food_category_pie_chart(food_categories)
                                st.plotly_chart(fig, use_container_width=True)
                                st.success("✅ 饼图生成成功！")
                            except Exception as e:
                                st.error(f"❌ 饼图生成失败: {str(e)}")
                                # 显示原始数据
                                st.write("原始数据:", food_categories)
                    else:
                        st.warning("⚠️ 暂无食物类别数据")
                        st.info("💡 这可能是因为没有识别到食物信息，请检查PDF内容")
                
                with tab5:
                    st.subheader("💡 饮食建议报告")
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
                        label="📥 下载分析报告",
                        data=dietary_advice,
                        file_name=f"nutrition_analysis_report_{uploaded_file.name.replace('.pdf', '')}.txt",
                        mime="text/plain"
                    )
            
            except Exception as e:
                st.error(f"❌ PDF处理失败: {str(e)}")
                st.info("💡 请确保PDF文件包含清晰的食物信息或营养标签")

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
    
    # 从配置文件读取当前API密钥
    from config import OPENAI_API_KEY
    current_api_key = OPENAI_API_KEY if OPENAI_API_KEY != "your_openai_api_key_here" else ""
    
    api_key = st.text_input("OpenAI API Key", type="password", 
                           value=current_api_key,
                           help="输入您的OpenAI API密钥以启用OCR功能")
    
    # API密钥验证
    if st.button("验证API密钥"):
        if api_key and api_key.startswith("sk-"):
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                # 尝试调用API验证密钥
                client.models.list()
                st.success("✅ API密钥验证成功！")
                
                # 保存到配置文件
                if st.button("保存API密钥"):
                    try:
                        # 更新配置文件
                        with open('config.py', 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 替换API密钥
                        if 'OPENAI_API_KEY = "your_openai_api_key_here"' in content:
                            content = content.replace('OPENAI_API_KEY = "your_openai_api_key_here"', f'OPENAI_API_KEY = "{api_key}"')
                        elif 'OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")' in content:
                            # 如果使用环境变量，直接设置默认值
                            content = content.replace('if not OPENAI_API_KEY:\n    OPENAI_API_KEY = "your_openai_api_key_here"', 
                                                    f'if not OPENAI_API_KEY:\n    OPENAI_API_KEY = "{api_key}"')
                        
                        with open('config.py', 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        st.success("✅ API密钥已保存到配置文件！")
                        st.info("请重启应用程序以使更改生效。")
                        
                    except Exception as e:
                        st.error(f"保存配置文件时出错：{str(e)}")
                        
            except Exception as e:
                error_msg = str(e)
                if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                    st.error("❌ API密钥无效或已过期")
                elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                    st.error("❌ API配额已用完或账户余额不足")
                else:
                    st.error(f"❌ API密钥验证失败：{error_msg}")
        else:
            st.error("❌ 请输入有效的API密钥（应以'sk-'开头）")
    
    # Display settings
    st.write("**Display Settings**")
    theme = st.selectbox("Theme", ["Light", "Dark"])
    language = st.selectbox("Language", ["English", "Chinese"])
    
    # 显示当前状态
    st.write("**当前状态**")
    if current_api_key and current_api_key.startswith("sk-"):
        st.success("✅ API密钥已配置")
    else:
        st.warning("⚠️ API密钥未配置，OCR功能将不可用")

if __name__ == "__main__":
    main()
