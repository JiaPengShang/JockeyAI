"""
Utility functions and helpers for the OCR system
"""
import os
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st
from PIL import Image
import io

def get_file_size_mb(file_content: bytes) -> float:
    """Get file size in MB"""
    return len(file_content) / (1024 * 1024)

def validate_file_format(filename: str, supported_formats: List[str]) -> bool:
    """Validate if file format is supported"""
    file_ext = f".{filename.split('.')[-1].lower()}"
    return file_ext in supported_formats

def create_download_link(file_path: str, link_text: str) -> str:
    """Create download link for files"""
    if not os.path.exists(file_path):
        return ""
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    b64_content = base64.b64encode(file_content).decode()
    filename = os.path.basename(file_path)
    
    href = f'<a href="data:application/octet-stream;base64,{b64_content}" download="{filename}">{link_text}</a>'
    return href

def format_confidence_score(score: float) -> str:
    """Format confidence score for display"""
    if score >= 0.9:
        return f"🟢 {score:.1%} (Excellent)"
    elif score >= 0.75:
        return f"🟡 {score:.1%} (Good)"
    elif score >= 0.5:
        return f"🟠 {score:.1%} (Fair)"
    else:
        return f"🔴 {score:.1%} (Poor)"

def get_material3_css() -> str:
    """Get Material3 CSS styling"""
    return """
    <style>
    /* Material3 Design System CSS */
    .main {
        padding-top: 2rem;
    }
    
    .stApp {
        background-color: #FFFBFE;
    }
    
    /* Material3 Color Tokens */
    :root {
        --md-sys-color-primary: #6750A4;
        --md-sys-color-on-primary: #FFFFFF;
        --md-sys-color-primary-container: #EADDFF;
        --md-sys-color-on-primary-container: #21005D;
        --md-sys-color-secondary: #625B71;
        --md-sys-color-on-secondary: #FFFFFF;
        --md-sys-color-secondary-container: #E8DEF8;
        --md-sys-color-on-secondary-container: #1D192B;
        --md-sys-color-tertiary: #7D5260;
        --md-sys-color-on-tertiary: #FFFFFF;
        --md-sys-color-error: #BA1A1A;
        --md-sys-color-on-error: #FFFFFF;
        --md-sys-color-surface: #FFFBFE;
        --md-sys-color-on-surface: #1C1B1F;
        --md-sys-color-outline: #79747E;
    }
    
    /* Typography Scale */
    .display-large {
        font-size: 57px;
        font-weight: 400;
        line-height: 64px;
        letter-spacing: -0.25px;
    }
    
    .display-medium {
        font-size: 45px;
        font-weight: 400;
        line-height: 52px;
        letter-spacing: 0px;
    }
    
    .headline-large {
        font-size: 32px;
        font-weight: 400;
        line-height: 40px;
        letter-spacing: 0px;
    }
    
    .headline-medium {
        font-size: 28px;
        font-weight: 400;
        line-height: 36px;
        letter-spacing: 0px;
    }
    
    .title-large {
        font-size: 22px;
        font-weight: 400;
        line-height: 28px;
        letter-spacing: 0px;
    }
    
    .body-large {
        font-size: 16px;
        font-weight: 400;
        line-height: 24px;
        letter-spacing: 0.5px;
    }
    
    .body-medium {
        font-size: 14px;
        font-weight: 400;
        line-height: 20px;
        letter-spacing: 0.25px;
    }
    
    /* Material3 Components */
    .material-card {
        background-color: var(--md-sys-color-surface);
        border-radius: 12px;
        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.3), 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
        padding: 16px;
        margin: 8px 0;
    }
    
    .material-button {
        background-color: var(--md-sys-color-primary);
        color: var(--md-sys-color-on-primary);
        border: none;
        border-radius: 20px;
        padding: 10px 24px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .material-button:hover {
        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.3), 0px 2px 6px 2px rgba(0, 0, 0, 0.15);
    }
    
    .material-fab {
        background-color: var(--md-sys-color-primary-container);
        color: var(--md-sys-color-on-primary-container);
        border: none;
        border-radius: 16px;
        width: 56px;
        height: 56px;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0px 3px 5px rgba(0, 0, 0, 0.2), 0px 6px 10px rgba(0, 0, 0, 0.14);
        transition: all 0.2s ease;
    }
    
    .material-fab:hover {
        box-shadow: 0px 5px 5px rgba(0, 0, 0, 0.2), 0px 8px 10px 1px rgba(0, 0, 0, 0.14);
    }
    
    /* Status indicators */
    .status-success {
        color: var(--md-sys-color-primary);
        background-color: var(--md-sys-color-primary-container);
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .status-warning {
        color: #8C4A00;
        background-color: #FFEDCC;
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .status-error {
        color: var(--md-sys-color-on-error);
        background-color: var(--md-sys-color-error);
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
    }
    
    /* Streamlit component overrides */
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 1px solid var(--md-sys-color-outline);
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid var(--md-sys-color-outline);
    }
    
    .stFileUploader > div {
        border-radius: 12px;
        border: 2px dashed var(--md-sys-color-outline);
        background-color: var(--md-sys-color-surface);
    }
    
    /* Progress indicators */
    .stProgress > div > div {
        background-color: var(--md-sys-color-primary);
        border-radius: 4px;
    }
    
    /* Metrics styling */
    .metric-card {
        background: linear-gradient(135deg, var(--md-sys-color-primary-container) 0%, var(--md-sys-color-secondary-container) 100%);
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 600;
        color: var(--md-sys-color-on-primary-container);
        margin: 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: var(--md-sys-color-on-secondary-container);
        margin: 4px 0 0 0;
        font-weight: 500;
    }
    
    /* Animation classes */
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .slide-up {
        animation: slideUp 0.3s ease-out;
    }
    
    @keyframes slideUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    </style>
    """

def display_material_card(title: str, content: str, icon: str = "📋"):
    """Display content in Material3 styled card"""
    st.markdown(f"""
    <div class="material-card fade-in">
        <h3 style="color: var(--md-sys-color-on-surface); margin-top: 0;">
            {icon} {title}
        </h3>
        <div style="color: var(--md-sys-color-on-surface-variant);">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_metric_card(value: str, label: str, icon: str = "📊"):
    """Display metric in Material3 styled card"""
    st.markdown(f"""
    <div class="metric-card slide-up">
        <div style="font-size: 24px; margin-bottom: 8px;">{icon}</div>
        <p class="metric-value">{value}</p>
        <p class="metric-label">{label}</p>
    </div>
    """, unsafe_allow_html=True)

def show_processing_status(message: str, progress: Optional[float] = None):
    """Show processing status with Material3 styling"""
    with st.container():
        st.markdown(f"""
        <div class="material-card">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 20px;">⚙️</div>
                <div>
                    <div style="font-weight: 500; color: var(--md-sys-color-on-surface);">
                        {message}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if progress is not None:
            st.progress(progress)

def create_image_preview(image_content: bytes, max_width: int = 300) -> str:
    """Create image preview with base64 encoding"""
    try:
        # Open and resize image
        image = Image.open(io.BytesIO(image_content))
        
        # Calculate new dimensions maintaining aspect ratio
        width, height = image.size
        if width > max_width:
            ratio = max_width / width
            new_width = max_width
            new_height = int(height * ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f'<img src="data:image/png;base64,{img_str}" style="border-radius: 8px; box-shadow: 0px 2px 8px rgba(0,0,0,0.1);">'
    
    except Exception:
        return '<div style="color: var(--md-sys-color-error);">Unable to preview image</div>'

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def get_timestamp() -> str:
    """Get formatted timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")