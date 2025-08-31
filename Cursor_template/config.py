"""
JockeyAI 系统配置文件
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

# 项目根目录
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_PATH = DATA_DIR / "jockey_ai.db"

# 创建必要的目录
for dir_path in [DATA_DIR, UPLOADS_DIR, PROCESSED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# OCR配置
class OCRConfig(BaseModel):
    """OCR配置类"""
    # Tesseract配置
    tesseract_cmd: str = "tesseract"
    tesseract_lang: str = "chi_sim+eng"
    tesseract_config: str = "--oem 3 --psm 6"
    
    # PaddleOCR配置
    paddle_use_gpu: bool = False
    paddle_use_angle_cls: bool = True
    paddle_det_db_thresh: float = 0.3
    paddle_det_db_box_thresh: float = 0.6
    
    # 混合OCR策略
    primary_ocr: str = "paddle"  # "paddle" 或 "tesseract"
    fallback_ocr: str = "tesseract"
    confidence_threshold: float = 0.7

# 数据结构定义
class DataField(BaseModel):
    """数据字段定义"""
    name: str
    type: str  # "text", "number", "date", "time"
    required: bool = False
    validation_pattern: Optional[str] = None
    description: str = ""

class DataSchema(BaseModel):
    """数据模式定义"""
    name: str
    fields: List[DataField]
    description: str = ""

# 预定义的数据模式
FOOD_LOG_SCHEMA = DataSchema(
    name="food_log",
    description="饮食日志数据结构",
    fields=[
        DataField(name="date", type="date", required=True, description="日期"),
        DataField(name="time", type="time", required=True, description="时间"),
        DataField(name="food_name", type="text", required=True, description="食物名称"),
        DataField(name="quantity", type="text", description="数量"),
        DataField(name="unit", type="text", description="单位"),
        DataField(name="calories", type="number", description="卡路里"),
        DataField(name="protein", type="number", description="蛋白质(g)"),
        DataField(name="carbs", type="number", description="碳水化合物(g)"),
        DataField(name="fat", type="number", description="脂肪(g)"),
        DataField(name="notes", type="text", description="备注"),
    ]
)

SLEEP_LOG_SCHEMA = DataSchema(
    name="sleep_log",
    description="睡眠日志数据结构",
    fields=[
        DataField(name="date", type="date", required=True, description="日期"),
        DataField(name="bedtime", type="time", description="就寝时间"),
        DataField(name="wake_time", type="time", description="起床时间"),
        DataField(name="sleep_duration", type="number", description="睡眠时长(小时)"),
        DataField(name="sleep_quality", type="number", description="睡眠质量(1-10)"),
        DataField(name="deep_sleep", type="number", description="深度睡眠时长"),
        DataField(name="rem_sleep", type="number", description="REM睡眠时长"),
        DataField(name="notes", type="text", description="备注"),
    ]
)

TRAINING_LOG_SCHEMA = DataSchema(
    name="training_log",
    description="训练日志数据结构",
    fields=[
        DataField(name="date", type="date", required=True, description="日期"),
        DataField(name="training_type", type="text", required=True, description="训练类型"),
        DataField(name="duration", type="number", description="训练时长(分钟)"),
        DataField(name="intensity", type="number", description="训练强度(1-10)"),
        DataField(name="distance", type="number", description="距离(km)"),
        DataField(name="calories_burned", type="number", description="消耗卡路里"),
        DataField(name="heart_rate_avg", type="number", description="平均心率"),
        DataField(name="heart_rate_max", type="number", description="最大心率"),
        DataField(name="notes", type="text", description="备注"),
    ]
)

WEIGHT_LOG_SCHEMA = DataSchema(
    name="weight_log",
    description="体重日志数据结构",
    fields=[
        DataField(name="date", type="date", required=True, description="日期"),
        DataField(name="weight", type="number", required=True, description="体重(kg)"),
        DataField(name="body_fat", type="number", description="体脂率(%)"),
        DataField(name="muscle_mass", type="number", description="肌肉量(kg)"),
        DataField(name="water_percentage", type="number", description="水分百分比(%)"),
        DataField(name="notes", type="text", description="备注"),
    ]
)

# 数据模式映射
DATA_SCHEMAS = {
    "food_log": FOOD_LOG_SCHEMA,
    "sleep_log": SLEEP_LOG_SCHEMA,
    "training_log": TRAINING_LOG_SCHEMA,
    "weight_log": WEIGHT_LOG_SCHEMA,
}

# 可视化配置
class VisualizationConfig(BaseModel):
    """可视化配置类"""
    # 图表类型配置
    chart_types = {
        "line": "折线图",
        "bar": "柱状图",
        "scatter": "散点图",
        "pie": "饼图",
        "heatmap": "热力图",
        "box": "箱线图",
        "histogram": "直方图",
        "area": "面积图",
    }
    
    # 默认图表配置
    default_charts = {
        "food_log": ["line", "bar", "pie"],
        "sleep_log": ["line", "scatter", "box"],
        "training_log": ["line", "bar", "scatter"],
        "weight_log": ["line", "scatter"],
    }
    
    # 颜色主题
    color_theme = {
        "primary": "#1976D2",
        "secondary": "#424242",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
    }

# 系统配置
class SystemConfig(BaseModel):
    """系统配置类"""
    app_name: str = "JockeyAI"
    app_version: str = "1.0.0"
    debug: bool = False
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    supported_formats: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
    session_timeout: int = 3600  # 1小时

# 实例化配置
ocr_config = OCRConfig()
viz_config = VisualizationConfig()
sys_config = SystemConfig()

# 环境变量配置
def load_env_config():
    """加载环境变量配置"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 更新OCR配置
    if os.getenv("TESSERACT_CMD"):
        ocr_config.tesseract_cmd = os.getenv("TESSERACT_CMD")
    if os.getenv("TESSERACT_LANG"):
        ocr_config.tesseract_lang = os.getenv("TESSERACT_LANG")
    if os.getenv("PADDLE_USE_GPU"):
        ocr_config.paddle_use_gpu = os.getenv("PADDLE_USE_GPU").lower() == "true"
    
    # 更新系统配置
    if os.getenv("DEBUG"):
        sys_config.debug = os.getenv("DEBUG").lower() == "true"

# 加载环境配置
load_env_config()
