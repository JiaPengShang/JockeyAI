"""
JockeyAI - 主要Streamlit应用程序
集成OCR、数据可视化和Material 3设计
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import time
from pathlib import Path
import json

# 导入自定义模块
from config import sys_config, DATA_SCHEMAS, viz_config
from ocr_engine import OCRProcessor
from visualization import DataVisualizer, DataAnalyzer
from database import DatabaseManager

# 页面配置
st.set_page_config(
    page_title="JockeyAI - 智能数据数字化系统",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Material 3 主题CSS
def load_material3_css():
    """加载Material 3主题CSS"""
    css = """
    <style>
    /* Material 3 主题变量 */
    :root {
        --md-sys-color-primary: #1976D2;
        --md-sys-color-primary-container: #D1E4FF;
        --md-sys-color-on-primary: #FFFFFF;
        --md-sys-color-on-primary-container: #001D36;
        --md-sys-color-secondary: #535F70;
        --md-sys-color-secondary-container: #D7E3F7;
        --md-sys-color-on-secondary: #FFFFFF;
        --md-sys-color-on-secondary-container: #101C2B;
        --md-sys-color-surface: #FDFCFF;
        --md-sys-color-surface-container: #E7E0EC;
        --md-sys-color-surface-container-high: #F3EDF7;
        --md-sys-color-surface-container-highest: #ECE6F0;
        --md-sys-color-on-surface: #1A1C1E;
        --md-sys-color-on-surface-variant: #43474E;
        --md-sys-color-outline: #73777F;
        --md-sys-color-outline-variant: #C3C7CF;
        --md-sys-color-error: #BA1A1A;
        --md-sys-color-error-container: #FFDAD6;
        --md-sys-color-on-error: #FFFFFF;
        --md-sys-color-on-error-container: #410002;
        --md-sys-color-success: #4CAF50;
        --md-sys-color-warning: #FF9800;
        --md-sys-color-info: #2196F3;
    }

    /* 全局样式 */
    .main {
        background-color: var(--md-sys-color-surface);
        color: var(--md-sys-color-on-surface);
    }

    /* 标题样式 */
    h1, h2, h3 {
        color: var(--md-sys-color-on-surface);
        font-weight: 500;
    }

    /* 卡片样式 */
    .stCard {
        background-color: var(--md-sys-color-surface-container);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        transition: box-shadow 0.3s ease;
    }

    .stCard:hover {
        box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
    }

    /* 按钮样式 */
    .stButton > button {
        background-color: var(--md-sys-color-primary);
        color: var(--md-sys-color-on-primary);
        border: none;
        border-radius: 20px;
        padding: 8px 24px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: var(--md-sys-color-primary-container);
        color: var(--md-sys-color-on-primary-container);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    /* 侧边栏样式 */
    .css-1d391kg {
        background-color: var(--md-sys-color-surface-container-high);
    }

    /* 文件上传样式 */
    .stFileUploader {
        border: 2px dashed var(--md-sys-color-outline-variant);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        background-color: var(--md-sys-color-surface-container-high);
    }

    /* 进度条样式 */
    .stProgress > div > div {
        background-color: var(--md-sys-color-primary);
    }

    /* 指标卡片样式 */
    .metric-card {
        background: linear-gradient(135deg, var(--md-sys-color-primary-container), var(--md-sys-color-secondary-container));
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        color: var(--md-sys-color-on-primary-container);
        margin: 8px 0;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 8px 0;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }

    /* 状态指示器 */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-success { background-color: var(--md-sys-color-success); }
    .status-warning { background-color: var(--md-sys-color-warning); }
    .status-error { background-color: var(--md-sys-color-error); }
    .status-info { background-color: var(--md-sys-color-info); }

    /* 响应式设计 */
    @media (max-width: 768px) {
        .metric-value {
            font-size: 1.5rem;
        }
        
        .stCard {
            padding: 12px;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# 初始化组件
@st.cache_resource
def init_components():
    """初始化系统组件"""
    return {
        'ocr_processor': OCRProcessor(),
        'visualizer': DataVisualizer(),
        'analyzer': DataAnalyzer(),
        'db_manager': DatabaseManager()
    }

# 侧边栏
def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("🏇 JockeyAI")
    st.sidebar.markdown("---")
    
    # 导航菜单
    page = st.sidebar.selectbox(
        "导航菜单",
        ["📊 仪表板", "📁 文件上传", "🔍 OCR处理", "📈 数据可视化", "⚙️ 系统设置"]
    )
    
    st.sidebar.markdown("---")
    
    # 数据模式选择
    st.sidebar.subheader("📋 数据模式")
    schema_name = st.sidebar.selectbox(
        "选择数据类型",
        list(DATA_SCHEMAS.keys()),
        format_func=lambda x: DATA_SCHEMAS[x].description
    )
    
    st.sidebar.markdown("---")
    
    # 系统状态
    st.sidebar.subheader("🔧 系统状态")
    components = init_components()
    
    # OCR引擎状态
    ocr_status = "✅ 可用" if components['ocr_processor'].ocr_engine.tesseract_available or components['ocr_processor'].ocr_engine.paddle_available else "❌ 不可用"
    st.sidebar.markdown(f"OCR引擎: {ocr_status}")
    
    # 数据库状态
    try:
        stats = components['db_manager'].get_statistics()
        db_status = "✅ 正常" if stats else "⚠️ 无数据"
    except:
        db_status = "❌ 错误"
    st.sidebar.markdown(f"数据库: {db_status}")
    
    return page, schema_name, components

# 仪表板页面
def render_dashboard(components):
    """渲染仪表板页面"""
    st.title("📊 JockeyAI 仪表板")
    st.markdown("欢迎使用JockeyAI智能数据数字化系统")
    
    # 获取统计数据
    try:
        stats = components['db_manager'].get_statistics()
        
        # 创建指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats.get('files', {}).get('total', 0)}</div>
                <div class="metric-label">总文件数</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats.get('data', {}).get('total_records', 0)}</div>
                <div class="metric-label">数据记录数</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_confidence = stats.get('ocr', {}).get('avg_confidence', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_confidence:.1%}</div>
                <div class="metric-label">OCR准确率</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            processed_files = stats.get('files', {}).get('by_status', {}).get('processed', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{processed_files}</div>
                <div class="metric-label">已处理文件</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 最近活动
        st.subheader("📈 最近活动")
        recent_files = components['db_manager'].get_file_records(limit=5)
        
        if recent_files:
            for file_record in recent_files:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{file_record['filename']}**")
                        st.caption(f"类型: {file_record['schema_name']}")
                    with col2:
                        status_color = {
                            'uploaded': 'info',
                            'processing': 'warning',
                            'processed': 'success',
                            'error': 'error'
                        }.get(file_record['status'], 'info')
                        st.markdown(f'<span class="status-indicator status-{status_color}"></span>{file_record["status"]}', unsafe_allow_html=True)
                    with col3:
                        st.caption(file_record['upload_time'])
        
        # 数据分布图表
        st.subheader("📊 数据分布")
        col1, col2 = st.columns(2)
        
        with col1:
            if stats.get('files', {}).get('by_schema'):
                schema_data = pd.DataFrame([
                    {'schema': k, 'count': v} 
                    for k, v in stats['files']['by_schema'].items()
                ])
                fig = px.pie(schema_data, values='count', names='schema', title='数据类型分布')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if stats.get('files', {}).get('by_status'):
                status_data = pd.DataFrame([
                    {'status': k, 'count': v} 
                    for k, v in stats['files']['by_status'].items()
                ])
                fig = px.bar(status_data, x='status', y='count', title='文件处理状态')
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"获取统计数据时出错: {e}")

# 文件上传页面
def render_file_upload(components, schema_name):
    """渲染文件上传页面"""
    st.title("📁 文件上传")
    st.markdown("上传手写或打印的表格文件进行OCR处理")
    
    # 文件上传区域
    uploaded_files = st.file_uploader(
        "选择文件",
        type=['png', 'jpg', 'jpeg', 'pdf', 'tiff', 'bmp'],
        accept_multiple_files=True,
        help="支持图片和PDF格式，最大50MB"
    )
    
    if uploaded_files:
        st.markdown("---")
        
        # 处理选项
        col1, col2 = st.columns(2)
        with col1:
            ocr_engine = st.selectbox(
                "OCR引擎",
                ["hybrid", "paddle", "tesseract"],
                help="选择OCR识别引擎"
            )
        
        with col2:
            auto_process = st.checkbox(
                "自动处理",
                value=True,
                help="上传后自动开始OCR处理"
            )
        
        # 文件列表
        st.subheader("📋 上传文件列表")
        for i, uploaded_file in enumerate(uploaded_files):
            with st.expander(f"文件 {i+1}: {uploaded_file.name}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**文件名:** {uploaded_file.name}")
                    st.write(f"**大小:** {uploaded_file.size / 1024:.1f} KB")
                    st.write(f"**类型:** {uploaded_file.type}")
                
                with col2:
                    if st.button(f"处理", key=f"process_{i}"):
                        process_file(uploaded_file, schema_name, ocr_engine, components)
                
                with col3:
                    if st.button(f"删除", key=f"delete_{i}"):
                        st.warning("删除功能待实现")
        
        # 批量处理
        if auto_process and st.button("🚀 开始批量处理"):
            with st.spinner("正在处理文件..."):
                for uploaded_file in uploaded_files:
                    process_file(uploaded_file, schema_name, ocr_engine, components)

def process_file(uploaded_file, schema_name, ocr_engine, components):
    """处理单个文件"""
    try:
        # 保存上传文件
        file_path = Path("data/uploads") / uploaded_file.name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 保存文件记录
        file_id = components['db_manager'].save_file_record(
            uploaded_file.name,
            str(file_path),
            uploaded_file.type,
            schema_name,
            uploaded_file.size
        )
        
        # 更新状态
        components['db_manager'].update_file_status(file_id, "processing")
        
        # OCR处理
        start_time = time.time()
        results = components['ocr_processor'].process_image(
            str(file_path), 
            schema_name, 
            ocr_engine
        )
        processing_time = time.time() - start_time
        
        if results['success']:
            # 保存OCR结果
            components['db_manager'].save_ocr_results(file_id, results['ocr_results'])
            
            # 保存结构化数据
            if results['structured_data']:
                components['db_manager'].save_structured_data(
                    file_id, 
                    schema_name, 
                    results['structured_data']
                )
            
            # 更新状态
            components['db_manager'].update_file_status(
                file_id, 
                "processed", 
                results['accuracy'], 
                processing_time
            )
            
            st.success(f"文件 {uploaded_file.name} 处理成功！")
            st.json(results['structured_data'])
            
        else:
            components['db_manager'].update_file_status(file_id, "error")
            st.error(f"文件 {uploaded_file.name} 处理失败: {results['error']}")
            
    except Exception as e:
        st.error(f"处理文件时出错: {e}")

# OCR处理页面
def render_ocr_processing(components):
    """渲染OCR处理页面"""
    st.title("🔍 OCR处理")
    st.markdown("查看和管理OCR处理结果")
    
    # 文件列表
    file_records = components['db_manager'].get_file_records()
    
    if not file_records:
        st.info("暂无文件记录")
        return
    
    # 筛选选项
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "状态筛选",
            ["全部"] + list(set(record['status'] for record in file_records))
        )
    
    with col2:
        schema_filter = st.selectbox(
            "数据类型筛选",
            ["全部"] + list(set(record['schema_name'] for record in file_records))
        )
    
    # 筛选文件
    filtered_records = file_records
    if status_filter != "全部":
        filtered_records = [r for r in filtered_records if r['status'] == status_filter]
    if schema_filter != "全部":
        filtered_records = [r for r in filtered_records if r['schema_name'] == schema_filter]
    
    # 显示文件列表
    for record in filtered_records:
        with st.expander(f"{record['filename']} ({record['status']})"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**文件名:** {record['filename']}")
                st.write(f"**数据类型:** {record['schema_name']}")
                st.write(f"**上传时间:** {record['upload_time']}")
                
                if record['ocr_accuracy']:
                    st.write(f"**OCR准确率:** {record['ocr_accuracy']:.1%}")
                if record['processing_time']:
                    st.write(f"**处理时间:** {record['processing_time']:.2f}秒")
            
            with col2:
                if record['status'] == 'processed':
                    if st.button("查看数据", key=f"view_{record['id']}"):
                        show_processed_data(record['id'], components)
            
            with col3:
                if st.button("删除", key=f"delete_{record['id']}"):
                    components['db_manager'].delete_file_record(record['id'])
                    st.rerun()

def show_processed_data(file_id, components):
    """显示处理后的数据"""
    df = components['db_manager'].get_structured_data(file_id=file_id)
    
    if not df.empty:
        st.subheader("📊 结构化数据")
        st.dataframe(df)
        
        # 数据统计
        st.subheader("📈 数据统计")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**记录数:** {len(df)}")
            st.write(f"**列数:** {len(df.columns)}")
        
        with col2:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                st.write(f"**数值列:** {len(numeric_cols)}")
                st.write(f"**文本列:** {len(df.columns) - len(numeric_cols)}")

# 数据可视化页面
def render_visualization(components, schema_name):
    """渲染数据可视化页面"""
    st.title("📈 数据可视化")
    st.markdown(f"可视化 {DATA_SCHEMAS[schema_name].description}")
    
    # 获取数据
    df = components['db_manager'].get_structured_data(schema_name)
    
    if df.empty:
        st.info(f"暂无 {DATA_SCHEMAS[schema_name].description} 数据")
        return
    
    # 数据筛选
    st.subheader("🔍 数据筛选")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 日期范围筛选
        date_columns = [col for col in df.columns if 'date' in col.lower()]
        if date_columns:
            date_col = st.selectbox("选择日期列", date_columns)
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                date_range = st.date_input(
                    "选择日期范围",
                    value=(df[date_col].min(), df[date_col].max()),
                    min_value=df[date_col].min(),
                    max_value=df[date_col].max()
                )
                if len(date_range) == 2:
                    df = df[(df[date_col].dt.date >= date_range[0]) & 
                           (df[date_col].dt.date <= date_range[1])]
    
    with col2:
        # 数值列筛选
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_columns:
            y_column = st.selectbox("选择Y轴列", numeric_columns)
    
    with col3:
        # 图表类型选择
        chart_type = st.selectbox(
            "选择图表类型",
            list(viz_config.chart_types.keys()),
            format_func=lambda x: viz_config.chart_types[x]
        )
    
    # 创建图表
    if not df.empty:
        st.subheader("📊 图表展示")
        
        try:
            if chart_type == "dashboard":
                fig = components['visualizer'].create_dashboard(df, schema_name)
            else:
                x_col = date_columns[0] if date_columns else df.columns[0]
                y_col = y_column if 'y_column' in locals() else numeric_columns[0] if numeric_columns else df.columns[1]
                
                fig = components['visualizer'].create_chart(
                    df, chart_type, x_col, y_col,
                    title=f"{DATA_SCHEMAS[schema_name].description} - {chart_type}"
                )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 图表控制
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 下载图表"):
                    # 图表下载功能
                    st.info("图表下载功能待实现")
            
            with col2:
                if st.button("🔄 刷新数据"):
                    st.rerun()
                    
        except Exception as e:
            st.error(f"创建图表时出错: {e}")
    
    # 数据分析
    st.subheader("📋 数据分析")
    if schema_name == "food_log":
        analysis = components['analyzer'].analyze_food_data(df)
    elif schema_name == "sleep_log":
        analysis = components['analyzer'].analyze_sleep_data(df)
    elif schema_name == "training_log":
        analysis = components['analyzer'].analyze_training_data(df)
    elif schema_name == "weight_log":
        analysis = components['analyzer'].analyze_weight_data(df)
    else:
        analysis = {}
    
    if analysis:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**基本统计**")
            for key, value in analysis.items():
                if isinstance(value, (int, float)):
                    st.write(f"{key}: {value}")
        
        with col2:
            st.write("**详细分析**")
            # 显示更详细的分析结果
            if 'date_range' in analysis and analysis['date_range']:
                st.write(f"数据时间范围: {analysis['date_range']['start']} 到 {analysis['date_range']['end']}")

# 系统设置页面
def render_settings(components):
    """渲染系统设置页面"""
    st.title("⚙️ 系统设置")
    st.markdown("配置系统参数和查看系统信息")
    
    # 系统信息
    st.subheader("ℹ️ 系统信息")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**应用名称:** {sys_config.app_name}")
        st.write(f"**版本:** {sys_config.app_version}")
        st.write(f"**调试模式:** {'开启' if sys_config.debug else '关闭'}")
    
    with col2:
        st.write(f"**最大文件大小:** {sys_config.max_file_size / 1024 / 1024:.0f} MB")
        st.write(f"**支持格式:** {', '.join(sys_config.supported_formats)}")
        st.write(f"**会话超时:** {sys_config.session_timeout / 3600:.1f} 小时")
    
    st.markdown("---")
    
    # OCR设置
    st.subheader("🔍 OCR设置")
    from config import ocr_config
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Tesseract配置**")
        st.write(f"命令: {ocr_config.tesseract_cmd}")
        st.write(f"语言: {ocr_config.tesseract_lang}")
        st.write(f"配置: {ocr_config.tesseract_config}")
    
    with col2:
        st.write("**PaddleOCR配置**")
        st.write(f"使用GPU: {'是' if ocr_config.paddle_use_gpu else '否'}")
        st.write(f"角度分类: {'是' if ocr_config.paddle_use_angle_cls else '否'}")
        st.write(f"检测阈值: {ocr_config.paddle_det_db_thresh}")
    
    st.markdown("---")
    
    # 数据管理
    st.subheader("🗄️ 数据管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 导出所有数据"):
            try:
                for schema_name in DATA_SCHEMAS.keys():
                    output_path = components['db_manager'].export_data(schema_name, 'csv')
                    st.success(f"数据已导出到: {output_path}")
            except Exception as e:
                st.error(f"导出数据时出错: {e}")
    
    with col2:
        if st.button("🧹 清理旧数据"):
            try:
                components['db_manager'].cleanup_old_data(30)
                st.success("旧数据清理完成")
            except Exception as e:
                st.error(f"清理数据时出错: {e}")
    
    # 系统维护
    st.subheader("🔧 系统维护")
    
    if st.button("🔄 重新初始化数据库"):
        try:
            components['db_manager'].init_database()
            st.success("数据库重新初始化完成")
        except Exception as e:
            st.error(f"数据库初始化失败: {e}")

# 主函数
def main():
    """主函数"""
    # 加载Material 3 CSS
    load_material3_css()
    
    # 渲染侧边栏
    page, schema_name, components = render_sidebar()
    
    # 根据页面选择渲染内容
    if page == "📊 仪表板":
        render_dashboard(components)
    elif page == "📁 文件上传":
        render_file_upload(components, schema_name)
    elif page == "🔍 OCR处理":
        render_ocr_processing(components)
    elif page == "📈 数据可视化":
        render_visualization(components, schema_name)
    elif page == "⚙️ 系统设置":
        render_settings(components)

if __name__ == "__main__":
    main()
