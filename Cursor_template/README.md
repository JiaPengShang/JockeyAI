# JockeyAI - 智能数据数字化系统

🏇 **JockeyAI** 是一个专为见习骑师设计的AI驱动数据数字化与可视化系统，支持手写和打印表格的OCR识别、结构化数据提取和智能可视化分析。

## 🚀 主要特性

### 🔍 智能OCR识别
- **混合OCR引擎**: 集成Tesseract和PaddleOCR，提供高精度文字识别
- **多语言支持**: 支持中文和英文混合识别
- **图像预处理**: 自动优化图像质量，提高识别准确率
- **结构化提取**: 智能提取表格数据，自动分类字段

### 📊 数据可视化
- **多种图表类型**: 折线图、柱状图、散点图、饼图、热力图等
- **Material 3设计**: 现代化的用户界面，符合Google Material Design 3规范
- **交互式图表**: 支持缩放、筛选、导出等功能
- **智能分析**: 自动生成数据洞察和趋势分析

### 🗄️ 数据管理
- **结构化存储**: 支持饮食日志、睡眠记录、训练数据、体重变化等多种数据类型
- **数据库管理**: SQLite数据库，支持数据导入导出
- **文件管理**: 完整的文件上传、处理、删除流程
- **数据安全**: 本地存储，保护用户隐私

## 📋 系统要求

### 基础要求
- Python 3.8+
- Windows 10/11, macOS, Linux

### OCR引擎要求
- **Tesseract OCR**: 需要安装Tesseract 4.0+
- **PaddleOCR**: 自动安装，支持CPU/GPU

### 推荐配置
- 8GB+ RAM
- 4核+ CPU
- 10GB+ 可用磁盘空间

## 🛠️ 安装指南

### 1. 克隆项目
```bash
git clone https://github.com/your-username/JockeyAI.git
cd JockeyAI
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 安装Tesseract OCR

#### Windows
1. 下载并安装 [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
2. 将Tesseract添加到系统PATH
3. 下载中文语言包

#### macOS
```bash
brew install tesseract
brew install tesseract-lang
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-chi-sim
```

### 5. 配置环境变量
创建 `.env` 文件：
```env
# OCR配置
TESSERACT_CMD=tesseract
TESSERACT_LANG=chi_sim+eng
PADDLE_USE_GPU=false

# 系统配置
DEBUG=false
```

## 🚀 快速开始

### 1. 启动应用
```bash
streamlit run app.py
```

### 2. 访问应用
打开浏览器访问: http://localhost:8501

### 3. 上传文件
1. 在侧边栏选择数据类型（饮食日志、睡眠记录等）
2. 点击"文件上传"页面
3. 上传手写或打印的表格图片
4. 选择OCR引擎和处理选项
5. 开始处理

### 4. 查看结果
- 在"OCR处理"页面查看处理状态
- 在"数据可视化"页面查看图表和分析
- 在"仪表板"页面查看系统概览

## 📁 项目结构

```
JockeyAI/
├── app.py                 # 主应用程序
├── config.py             # 配置文件
├── ocr_engine.py         # OCR引擎模块
├── visualization.py      # 数据可视化模块
├── database.py           # 数据库管理模块
├── requirements.txt      # 依赖包列表
├── README.md            # 项目说明
├── data/                # 数据目录
│   ├── uploads/         # 上传文件
│   ├── processed/       # 处理结果
│   └── jockey_ai.db    # 数据库文件
└── doc/                 # 文档目录
    ├── 项目总介绍.md
    └── JokeyDesign.drawio
```

## 📊 支持的数据类型

### 1. 饮食日志 (food_log)
- 日期、时间
- 食物名称、数量、单位
- 营养成分（卡路里、蛋白质、碳水化合物、脂肪）
- 备注信息

### 2. 睡眠记录 (sleep_log)
- 日期、就寝时间、起床时间
- 睡眠时长、睡眠质量
- 深度睡眠、REM睡眠时长
- 备注信息

### 3. 训练记录 (training_log)
- 日期、训练类型
- 训练时长、强度、距离
- 消耗卡路里、心率数据
- 备注信息

### 4. 体重记录 (weight_log)
- 日期、体重
- 体脂率、肌肉量、水分百分比
- 备注信息

## 🎨 Material 3 设计

系统采用Google Material Design 3设计规范：

- **动态颜色**: 自适应主题色彩
- **卡片设计**: 现代化的卡片式布局
- **响应式**: 支持桌面和移动设备
- **无障碍**: 符合无障碍设计标准

## 🔧 配置选项

### OCR配置
```python
# config.py
ocr_config = OCRConfig(
    tesseract_cmd="tesseract",
    tesseract_lang="chi_sim+eng",
    primary_ocr="paddle",
    fallback_ocr="tesseract",
    confidence_threshold=0.7
)
```

### 可视化配置
```python
# config.py
viz_config = VisualizationConfig(
    chart_types={
        "line": "折线图",
        "bar": "柱状图",
        "scatter": "散点图",
        "pie": "饼图"
    }
)
```

## 📈 性能优化

### OCR性能
- 图像预处理优化
- 多引擎并行处理
- 缓存机制

### 可视化性能
- 数据懒加载
- 图表缓存
- 响应式渲染

## 🐛 故障排除

### 常见问题

1. **Tesseract未找到**
   ```
   解决方案: 确保Tesseract已正确安装并添加到PATH
   ```

2. **PaddleOCR安装失败**
   ```
   解决方案: 使用国内镜像源安装
   pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **数据库连接错误**
   ```
   解决方案: 检查data目录权限，确保可写
   ```

4. **内存不足**
   ```
   解决方案: 减少并发处理文件数量，增加系统内存
   ```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目主页: https://github.com/your-username/JockeyAI
- 问题反馈: https://github.com/your-username/JockeyAI/issues
- 邮箱: your-email@example.com

## 🙏 致谢

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/)
- [Material Design 3](https://m3.material.io/)

---

**JockeyAI** - 让数据数字化更智能，让训练管理更高效！🏇
