"""
Main Streamlit application for an AI-driven OCR and visualization system
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import custom modules
from config import ocr_config, data_config, ui_config
from ocr_processor import ocr_processor
from data_processor import data_processor
from visualizer import visualizer
from exception_handler import exception_handler
from ocr_engines import engine_manager
from ocr_config_manager import config_manager
from utils import (
    get_material3_css, validate_file_format, get_file_size_mb,
    display_material_card, display_metric_card, show_processing_status,
    create_image_preview, format_confidence_score, create_download_link
)

# Page configuration
st.set_page_config(
    page_title="AI OCR & Visualization System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Material3 styling
st.markdown(get_material3_css(), unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Initialize session state
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = []
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 class="headline-large" style="color: var(--md-sys-color-primary); margin: 0;">
            🔍 AI-Driven OCR & Visualization System
        </h1>
        <p class="body-large" style="color: var(--md-sys-color-on-surface-variant); margin-top: 8px;">
            Transform handwritten forms into structured data and interactive visualizations
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 📋 Navigation")
        page = st.selectbox(
            "Select Page",
            ["🏠 Home", "📤 Upload & Process", "📊 Visualizations", "📈 Dashboard", "⚙️ Settings"],
            key="navigation"
        )
        
        # System status
        st.markdown("### 📊 System Status")
        
        # OCR engines status
        engine_status = engine_manager.get_engine_status()
        
        st.markdown("**OCR Engines:**")
        for engine_name, status in engine_status.items():
            status_icon = "🟢" if status['available'] else "🔴"
            active_icon = "✅" if status['active'] else "❌"
            st.markdown(f"- {status['engine_name']}: {status_icon} Available {active_icon} Active")
        
        st.markdown(f"""
        **Data Entries:** {len(st.session_state.processed_data)}
        
        **Target Accuracy:** ≥{ocr_config.target_accuracy:.0%}
        """)
        
        # Exception summary
        exc_summary = exception_handler.get_exception_summary()
        if any(exc_summary.values()):
            st.markdown("### ⚠️ Exception Summary")
            for level, count in exc_summary.items():
                if count > 0:
                    st.markdown(f"- {level}: {count}")
    
    # Main content based on selected page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📤 Upload & Process":
        show_upload_page()
    elif page == "📊 Visualizations":
        show_visualizations_page()
    elif page == "📈 Dashboard":
        show_dashboard_page()
    elif page == "⚙️ Settings":
        show_settings_page()

def show_home_page():
    """Display home page with system overview"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        display_material_card(
            "Welcome to AI OCR System",
            """
            This system helps trainee jockeys digitize handwritten forms and visualize training data.
            
            **Key Features:**
            - 🔍 Hot-swappable OCR engines (TesseractOCR + PaddleOCR)
            - 🔬 Ablation study support for research
            - 📊 Interactive data visualizations
            - 📋 Structured data export (CSV/JSON)
            - 🎨 Material3 design interface
            - ⚡ Real-time processing with error recovery
            
            **Getting Started:**
            1. Configure OCR engines for your experiment
            2. Upload your handwritten forms or scanned documents
            3. Let the AI extract structured data
            4. Explore interactive visualizations
            5. Export data for further analysis
            """,
            "🏠"
        )
        
        # OCR Engine Configuration Section
        st.markdown("### 🔧 OCR Engine Configuration")
        
        # Get current engine status
        engine_status = engine_manager.get_engine_status()
        available_engines = engine_manager.get_available_engines()
        active_engines = engine_manager.get_active_engines()
        
        # Engine selection for ablation studies
        st.markdown("**Select OCR Engines for Processing:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Tesseract configuration
            if "tesseract" in engine_status:
                tesseract_enabled = st.checkbox(
                    "🔍 TesseractOCR",
                    value="tesseract" in active_engines,
                    disabled=not engine_status["tesseract"]["available"],
                    help="Enable TesseractOCR engine for text extraction"
                )
                
                if tesseract_enabled and "tesseract" not in active_engines:
                    engine_manager.enable_engine("tesseract")
                elif not tesseract_enabled and "tesseract" in active_engines:
                    engine_manager.disable_engine("tesseract")
        
        with col2:
            # PaddleOCR configuration
            if "paddle" in engine_status:
                paddle_enabled = st.checkbox(
                    "🚀 PaddleOCR",
                    value="paddle" in active_engines,
                    disabled=not engine_status["paddle"]["available"],
                    help="Enable PaddleOCR engine for text extraction"
                )
                
                if paddle_enabled and "paddle" not in active_engines:
                    engine_manager.enable_engine("paddle")
                elif not paddle_enabled and "paddle" in active_engines:
                    engine_manager.disable_engine("paddle")
        
        # Ablation study presets
        st.markdown("**🔬 Ablation Study Presets:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧪 Tesseract Only", help="Run ablation study with only TesseractOCR"):
                engine_manager.set_active_engines(["tesseract"])
                st.success("✅ Set to TesseractOCR only")
                st.rerun()
        
        with col2:
            if st.button("🧪 PaddleOCR Only", help="Run ablation study with only PaddleOCR"):
                engine_manager.set_active_engines(["paddle"])
                st.success("✅ Set to PaddleOCR only")
                st.rerun()
        
        with col3:
            if st.button("🧪 Both Engines", help="Run with both OCR engines"):
                engine_manager.set_active_engines(["tesseract", "paddle"])
                st.success("✅ Set to both engines")
                st.rerun()
        
        # Current configuration display
        st.markdown("**📊 Current Configuration:**")
        current_active = engine_manager.get_active_engines()
        if current_active:
            st.info(f"Active engines: {', '.join(current_active)}")
        else:
            st.warning("⚠️ No engines are currently active!")
        
        # Reset button
        if st.button("🔄 Reset to Default"):
            engine_manager.reset_to_default()
            st.success("✅ Reset to default configuration")
            st.rerun()
        
        # Experiment Configuration Management
        st.markdown("### 🧪 Experiment Configuration Management")
        
        # Preset configurations
        st.markdown("**📋 Preset Configurations:**")
        preset_configs = config_manager.get_preset_configs()
        
        col1, col2 = st.columns(2)
        
        with col1:
            for preset_id, preset in list(preset_configs.items())[:2]:
                if st.button(f"📋 {preset['name']}", key=f"preset_{preset_id}"):
                    engine_manager.set_active_engines(preset['active_engines'])
                    ocr_config.enable_preprocessing = preset['enable_preprocessing']
                    ocr_config.combine_results = preset['combine_results']
                    st.success(f"✅ Loaded {preset['name']}")
                    st.rerun()
        
        with col2:
            for preset_id, preset in list(preset_configs.items())[2:]:
                if st.button(f"📋 {preset['name']}", key=f"preset_{preset_id}"):
                    engine_manager.set_active_engines(preset['active_engines'])
                    ocr_config.enable_preprocessing = preset['enable_preprocessing']
                    ocr_config.combine_results = preset['combine_results']
                    st.success(f"✅ Loaded {preset['name']}")
                    st.rerun()
        
        # Save current configuration
        st.markdown("**💾 Save Current Configuration:**")
        col1, col2 = st.columns(2)
        
        with col1:
            experiment_name = st.text_input("Experiment Name", placeholder="e.g., Tesseract Only Test")
        
        with col2:
            experiment_desc = st.text_input("Description", placeholder="Brief description of the experiment")
        
        if st.button("💾 Save Configuration") and experiment_name:
            exp_id = config_manager.save_current_config(experiment_name, experiment_desc)
            st.success(f"✅ Configuration saved as experiment: {exp_id}")
        
        # Load saved experiments
        st.markdown("**📂 Saved Experiments:**")
        saved_experiments = config_manager.list_experiments()
        
        if saved_experiments:
            for exp in saved_experiments:
                with st.expander(f"📁 {exp['name']} ({exp['id']})"):
                    st.markdown(f"**Description:** {exp['description']}")
                    st.markdown(f"**Engines:** {', '.join(exp['active_engines'])}")
                    st.markdown(f"**Created:** {exp['created_at']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📂 Load", key=f"load_{exp['id']}"):
                            if config_manager.load_experiment(exp['id']):
                                st.success("✅ Experiment loaded successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to load experiment")
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{exp['id']}"):
                            if config_manager.delete_experiment(exp['id']):
                                st.success("✅ Experiment deleted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete experiment")
        else:
            st.info("📂 No saved experiments yet. Save your first configuration above!")
    
    with col2:
        # Quick stats
        if st.session_state.processed_data:
            df = pd.DataFrame(st.session_state.processed_data)
            
            display_metric_card(
                str(len(st.session_state.processed_data)),
                "Total Entries",
                "📝"
            )
            
            avg_confidence = df['confidence_score'].mean() if 'confidence_score' in df.columns else 0
            display_metric_card(
                f"{avg_confidence:.1%}",
                "Avg Confidence",
                "🎯"
            )
            
            completeness = sum(1 for entry in st.session_state.processed_data 
                             if entry.get('diet_content') or entry.get('training_load') or entry.get('sleep_data'))
            display_metric_card(
                f"{completeness}/{len(st.session_state.processed_data)}",
                "Complete Records",
                "✅"
            )
        else:
            display_material_card(
                "No Data Yet",
                "Upload your first document to get started with OCR processing and visualization.",
                "📁"
            )

def show_upload_page():
    """Display file upload and processing page"""
    
    st.markdown("### 📤 Upload & Process Documents")
    
    # File upload section
    uploaded_files = st.file_uploader(
        "Choose files to process",
        type=['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        accept_multiple_files=True,
        help="Supported formats: PDF, JPG, PNG, BMP, TIFF"
    )
    
    if uploaded_files:
        st.markdown("### 📋 Uploaded Files")
        
        # Display uploaded files
        for i, file in enumerate(uploaded_files):
            with st.expander(f"📄 {file.name} ({get_file_size_mb(file.getvalue()):.1f} MB)"):
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # File info
                    st.markdown(f"""
                    **File Details:**
                    - Name: {file.name}
                    - Size: {get_file_size_mb(file.getvalue()):.1f} MB
                    - Type: {file.type}
                    """)
                    
                    # Process button
                    if st.button(f"🔍 Process File", key=f"process_{i}"):
                        process_file(file)
                
                with col2:
                    # Image preview for image files
                    if file.type.startswith('image/'):
                        st.markdown("**Preview:**")
                        preview_html = create_image_preview(file.getvalue())
                        st.markdown(preview_html, unsafe_allow_html=True)
        
        # Batch process button
        if len(uploaded_files) > 1:
            st.markdown("---")
            if st.button("🚀 Process All Files", type="primary"):
                process_batch_files(uploaded_files)
    
    # Manual data entry section
    st.markdown("### ✏️ Manual Data Entry")
    st.markdown("If OCR fails, you can manually enter data:")
    
    with st.expander("📝 Manual Entry Form"):
        with st.form("manual_entry"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name")
                date = st.date_input("Date")
                diet_content = st.text_area("Diet Content", placeholder="Enter diet information...")
            
            with col2:
                training_load = st.text_input("Training Load", placeholder="e.g., 30 minutes running")
                sleep_data = st.text_input("Sleep Data", placeholder="e.g., 8 hours")
                confidence = st.slider("Data Confidence", 0.0, 1.0, 0.95, 0.05)
            
            if st.form_submit_button("💾 Save Manual Entry"):
                manual_data = {
                    'name': name,
                    'date': str(date),
                    'diet_content': [diet_content] if diet_content else [],
                    'training_load': training_load,
                    'sleep_data': sleep_data,
                    'confidence_score': confidence,
                    'raw_text': f"Manual entry: {name}, {date}",
                    'timestamp': datetime.now().isoformat()
                }
                
                metadata = {
                    'filename': 'manual_entry',
                    'file_size': 0,
                    'processing_method': 'manual'
                }
                
                if data_processor.add_data_entry(manual_data, metadata):
                    st.session_state.processed_data.append(manual_data)
                    st.success("✅ Manual entry saved successfully!")
                    st.rerun()

def process_file(uploaded_file):
    """Process a single uploaded file"""
    try:
        # Validate file
        if not validate_file_format(uploaded_file.name, data_config.supported_formats):
            st.error(f"❌ Unsupported file format: {uploaded_file.name}")
            return
        
        # Check file size
        file_size_mb = get_file_size_mb(uploaded_file.getvalue())
        if file_size_mb > 10:  # 10MB limit
            st.warning(f"⚠️ Large file size ({file_size_mb:.1f} MB). Processing may take longer.")
        
        # Show processing status
        with st.spinner("🔍 Processing file with OCR engines..."):
            show_processing_status("Extracting text from document...", 0.3)
            
            # Process with OCR
            ocr_results = ocr_processor.process_file(uploaded_file.getvalue(), uploaded_file.name)
            
            if not ocr_results:
                st.error("❌ OCR processing failed. Try manual entry or different file format.")
                return
            
            show_processing_status("Structuring extracted data...", 0.7)
            
            # Extract structured data
            structured_data = ocr_processor.extract_structured_data(ocr_results)
            
            # Prepare metadata
            metadata = {
                'filename': uploaded_file.name,
                'file_size': len(uploaded_file.getvalue()),
                'processing_method': 'ocr'
            }
            
            show_processing_status("Saving processed data...", 0.9)
            
            # Save data
            if data_processor.add_data_entry(structured_data, metadata):
                st.session_state.processed_data.append(structured_data)
                st.session_state.processing_history.append({
                    'filename': uploaded_file.name,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': structured_data.get('confidence_score', 0),
                    'status': 'success'
                })
                
                # Display results
                st.success("✅ File processed successfully!")
                
                # Show extracted data
                with st.expander("📋 Extracted Data", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Structured Data:**")
                        st.json({
                            'name': structured_data.get('name', 'N/A'),
                            'date': structured_data.get('date', 'N/A'),
                            'diet_content': structured_data.get('diet_content', []),
                            'training_load': structured_data.get('training_load', 'N/A'),
                            'sleep_data': structured_data.get('sleep_data', 'N/A')
                        })
                    
                    with col2:
                        st.markdown("**Processing Info:**")
                        confidence_display = format_confidence_score(structured_data.get('confidence_score', 0))
                        st.markdown(f"**Confidence:** {confidence_display}")
                        
                        # Show engines used
                        engines_used = structured_data.get('engines_used', [])
                        if engines_used:
                            st.markdown(f"**Engines Used:** {', '.join(engines_used)}")
                        else:
                            st.markdown(f"**Engines Used:** {len(ocr_results)} OCR engine(s)")
                        
                        # Raw text preview
                        raw_text = structured_data.get('raw_text', '')
                        if raw_text:
                            st.text_area("Raw Extracted Text", raw_text[:500] + "..." if len(raw_text) > 500 else raw_text, height=100)
                
                st.rerun()
            
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        st.session_state.processing_history.append({
            'filename': uploaded_file.name,
            'timestamp': datetime.now().isoformat(),
            'confidence': 0,
            'status': 'failed',
            'error': str(e)
        })

def process_batch_files(uploaded_files):
    """Process multiple files in batch"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    successful_files = 0
    total_files = len(uploaded_files)
    
    for i, file in enumerate(uploaded_files):
        progress = (i + 1) / total_files
        progress_bar.progress(progress)
        status_text.text(f"Processing {file.name} ({i+1}/{total_files})")
        
        try:
            # Process file (simplified for batch)
            ocr_results = ocr_processor.process_file(file.getvalue(), file.name)
            
            if ocr_results:
                structured_data = ocr_processor.extract_structured_data(ocr_results)
                metadata = {
                    'filename': file.name,
                    'file_size': len(file.getvalue()),
                    'processing_method': 'batch_ocr'
                }
                
                if data_processor.add_data_entry(structured_data, metadata):
                    st.session_state.processed_data.append(structured_data)
                    successful_files += 1
        
        except Exception as e:
            st.warning(f"⚠️ Failed to process {file.name}: {str(e)}")
    
    progress_bar.progress(1.0)
    status_text.text(f"Batch processing complete: {successful_files}/{total_files} files processed successfully")
    
    if successful_files > 0:
        st.success(f"✅ Successfully processed {successful_files} out of {total_files} files!")
        st.rerun()

def show_visualizations_page():
    """Display visualizations page"""
    
    st.markdown("### 📊 Data Visualizations")
    
    if not st.session_state.processed_data:
        display_material_card(
            "No Data Available",
            "Upload and process documents first to see visualizations.",
            "📊"
        )
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.processed_data)
    
    # Visualization type selector
    viz_type = st.selectbox(
        "Select Visualization Type",
        ["🍽️ Diet Analysis", "🏃 Training Analysis", "😴 Sleep Analysis", "📈 All Categories"]
    )
    
    # Generate visualizations based on selection
    if viz_type == "🍽️ Diet Analysis":
        st.markdown("#### Diet Pattern Analysis")
        diet_viz = visualizer.create_diet_visualizations(df)
        
        for chart_name, chart in diet_viz.items():
            st.plotly_chart(chart, width='stretch')
    
    elif viz_type == "🏃 Training Analysis":
        st.markdown("#### Training Load Analysis")
        training_viz = visualizer.create_training_visualizations(df)
        
        for chart_name, chart in training_viz.items():
            st.plotly_chart(chart, width='stretch')
    
    elif viz_type == "😴 Sleep Analysis":
        st.markdown("#### Sleep Pattern Analysis")
        sleep_viz = visualizer.create_sleep_visualizations(df)
        
        for chart_name, chart in sleep_viz.items():
            st.plotly_chart(chart, width='stretch')
    
    elif viz_type == "📈 All Categories":
        # Show all visualizations in tabs
        tab1, tab2, tab3 = st.tabs(["🍽️ Diet", "🏃 Training", "😴 Sleep"])
        
        with tab1:
            diet_viz = visualizer.create_diet_visualizations(df)
            for chart_name, chart in diet_viz.items():
                st.plotly_chart(chart, width='stretch')
        
        with tab2:
            training_viz = visualizer.create_training_visualizations(df)
            for chart_name, chart in training_viz.items():
                st.plotly_chart(chart, width='stretch')
        
        with tab3:
            sleep_viz = visualizer.create_sleep_visualizations(df)
            for chart_name, chart in sleep_viz.items():
                st.plotly_chart(chart, width='stretch')

def show_dashboard_page():
    """Display comprehensive dashboard"""
    
    st.markdown("### 📈 Comprehensive Dashboard")
    
    if not st.session_state.processed_data:
        display_material_card(
            "No Data Available",
            "Upload and process documents first to see the dashboard.",
            "📈"
        )
        return
    
    df = pd.DataFrame(st.session_state.processed_data)
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_metric_card(
            str(len(st.session_state.processed_data)),
            "Total Entries",
            "📝"
        )
    
    with col2:
        avg_confidence = df['confidence_score'].mean() if 'confidence_score' in df.columns else 0
        display_metric_card(
            f"{avg_confidence:.1%}",
            "Avg Confidence",
            "🎯"
        )
    
    with col3:
        complete_records = sum(1 for entry in st.session_state.processed_data 
                             if entry.get('diet_content') or entry.get('training_load') or entry.get('sleep_data'))
        display_metric_card(
            f"{complete_records}",
            "Complete Records",
            "✅"
        )
    
    with col4:
        unique_dates = len(set(entry.get('date', '') for entry in st.session_state.processed_data if entry.get('date')))
        display_metric_card(
            f"{unique_dates}",
            "Unique Days",
            "📅"
        )
    
    # Dashboard visualizations
    dashboard_viz = visualizer.create_overview_dashboard(df)
    
    # Display charts in organized layout
    col1, col2 = st.columns(2)
    
    with col1:
        if 'confidence_trends' in dashboard_viz:
            st.plotly_chart(dashboard_viz['confidence_trends'], use_container_width=True)
    
    with col2:
        if 'data_completeness' in dashboard_viz:
            st.plotly_chart(dashboard_viz['data_completeness'], use_container_width=True)
    
    # Data export section
    st.markdown("### 💾 Data Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export CSV"):
            csv_path = data_processor.export_to_csv()
            if csv_path:
                download_link = create_download_link(csv_path, "Download CSV")
                st.markdown(download_link, unsafe_allow_html=True)
                st.success("✅ CSV export ready!")
    
    with col2:
        if st.button("📋 Export JSON"):
            json_path = data_processor.export_to_json()
            if json_path:
                download_link = create_download_link(json_path, "Download JSON")
                st.markdown(download_link, unsafe_allow_html=True)
                st.success("✅ JSON export ready!")
    
    with col3:
        if st.button("🗑️ Clear All Data"):
            if st.button("⚠️ Confirm Clear", type="secondary"):
                data_processor.clear_data()
                st.session_state.processed_data.clear()
                st.session_state.processing_history.clear()
                exception_handler.clear_history()
                st.success("✅ All data cleared!")
                st.rerun()

def show_settings_page():
    """Display settings and configuration page"""
    
    st.markdown("### ⚙️ System Settings")
    
    # OCR Configuration
    with st.expander("🔍 OCR Configuration", expanded=True):
        st.markdown("**OCR Engine Settings:**")
        
        # Get current engine status
        engine_status = engine_manager.get_engine_status()
        active_engines = engine_manager.get_active_engines()
        
        target_accuracy = st.slider(
            "Target Accuracy Threshold",
            0.5, 1.0, ocr_config.target_accuracy, 0.05,
            help="Minimum acceptable OCR confidence score"
        )
        
        use_preprocessing = st.checkbox(
            "Enable Image Preprocessing",
            value=ocr_config.enable_preprocessing,
            help="Apply denoising and threshold processing for better OCR results"
        )
        
        combine_results = st.checkbox(
            "Combine Multiple Engine Results",
            value=ocr_config.combine_results,
            help="Combine results from multiple OCR engines when confidence is similar"
        )
        
        st.markdown("**Current Engine Status:**")
        for engine_name, status in engine_status.items():
            status_icon = "✅" if status['available'] else "❌"
            active_icon = "🟢" if status['active'] else "⚪"
            st.markdown(f"- {status['engine_name']}: {status_icon} Available {active_icon} Active")
        
        # Engine configuration
        st.markdown("**Engine Configuration:**")
        col1, col2 = st.columns(2)
        
        with col1:
            if "tesseract" in engine_status:
                tesseract_config = st.text_input(
                    "Tesseract Config",
                    value=ocr_config.tesseract_config,
                    help="Tesseract configuration parameters"
                )
        
        with col2:
            if "paddle" in engine_status:
                paddle_gpu = st.checkbox(
                    "PaddleOCR GPU",
                    value=ocr_config.paddle_use_gpu,
                    help="Use GPU for PaddleOCR processing"
                )
    
    # Data Configuration
    with st.expander("💾 Data Configuration"):
        st.markdown("**Supported File Formats:**")
        st.markdown(", ".join(data_config.supported_formats))
        
        output_format = st.selectbox(
            "Default Export Format",
            ["CSV", "JSON", "Both"],
            index=2
        )
        
        max_file_size = st.number_input(
            "Maximum File Size (MB)",
            min_value=1, max_value=50, value=10
        )
    
    # UI Configuration
    with st.expander("🎨 UI Configuration"):
        st.markdown("**Material3 Color Scheme:**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.color_picker("Primary Color", ui_config.primary_color, disabled=True)
            st.color_picker("Secondary Color", ui_config.secondary_color, disabled=True)
        
        with col2:
            st.color_picker("Success Color", ui_config.success_color, disabled=True)
            st.color_picker("Error Color", ui_config.error_color, disabled=True)
        
        st.info("🎨 Color customization will be available in future updates")
    
    # System Information
    with st.expander("ℹ️ System Information"):
        st.markdown(f"""
        **System Status:**
        - Total Processed Files: {len(st.session_state.processing_history)}
        - Active Data Entries: {len(st.session_state.processed_data)}
        - Exception History: {sum(exception_handler.get_exception_summary().values())}
        
        **Configuration:**
        - Output Directory: `{data_config.output_dir}`
        - Supported Formats: {len(data_config.supported_formats)} types
        - Target OCR Accuracy: {ocr_config.target_accuracy:.0%}
        """)
        
        # Processing history
        if st.session_state.processing_history:
            st.markdown("**Recent Processing History:**")
            history_df = pd.DataFrame(st.session_state.processing_history[-10:])  # Last 10 entries
            st.dataframe(history_df, use_container_width=True)

if __name__ == "__main__":
    main()