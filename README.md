# 🏇 Jockey Nutrition AI - AI-Driven Food Choice and Weight Management System

## Project Introduction

This is an AI-driven nutrition analysis system specifically designed for jockeys, combining OCR text recognition, machine learning food classification, nutrition analysis, and visualization functions. The system provides a ChatGPT-like interactive interface that supports image and text input, offering personalized nutrition advice for jockeys.

## 🚀 Main Features

### 1. 📷 Image Recognition Analysis
- Use ChatGPT API for OCR text recognition
- Automatically identify nutritional content in food images
- Support multiple image formats (PNG, JPG, JPEG)

### 2. 💬 Smart Text Analysis
- ChatGPT-like conversation interface
- Natural language processing for food information
- Real-time nutrition analysis and recommendations

### 3. 📊 Nutrition Analysis
- Nutritional component pie charts
- Food classification distribution charts
- Nutrition target comparison analysis
- Radar charts showing nutritional balance

### 4. 📈 Trend Analysis
- Nutrition intake trend charts
- Calorie timeline
- BMI change tracking
- Nutrition heat maps

### 5. ⚙️ Personalized Settings
- Custom nutrition goals
- BMI calculation and weight management
- Jockey-specific recommendations

## 🛠️ Technical Architecture

### Core Modules
- **OCR Processor** (`ocr_processor.py`): Use ChatGPT API for text recognition
- **Food Classifier** (`food_classifier.py`): Machine learning model for food classification
- **Nutrition Analyzer** (`nutrition_analyzer.py`): Nutrition calculation and recommendation generation
- **Visualizer** (`visualization.py`): Chart generation and data analysis

### Technology Stack
- **Frontend**: Streamlit (Apple-like minimalist design)
- **AI/ML**: OpenAI GPT-4, Scikit-learn
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib
- **Image Processing**: Pillow

## 📦 Installation and Running

### Prerequisites
```bash
Python 3.8+
Miniconda or Anaconda
```

### 1. Clone the Repository
```bash
git clone <repository-url>
cd JockeyInsight
```

### 2. Create and Activate Conda Environment
```bash
conda create -n jockey_insight python=3.11 -y
conda activate jockey_insight
```

### 3. Install Dependencies
```bash
conda install pandas numpy matplotlib seaborn scikit-learn -y
pip install streamlit==1.28.1 plotly==5.17.0 openai==1.3.7 pillow==10.0.1 requests==2.31.0 python-dotenv==1.0.0 openpyxl==3.1.2 xlrd==2.0.1 plotly-express==0.4.1 streamlit-option-menu==0.3.6 streamlit-aggrid==0.3.4 streamlit-plotly-events==0.0.6
```

### 4. Configure API Key
In `config.py`, set your OpenAI API key:
```python
OPENAI_API_KEY = "your-api-key-here"
```

## 🚀 Daily Usage Commands

### Startup Commands (Copy and Paste)
```bash
cd /Users/shangjiapeng/Desktop/MasseyUniversity/159333_Programming_Project/JockeyInsight
conda activate jockey_insight
streamlit run app.py
```

### Alternative One-Line Startup
```bash
conda activate jockey_insight && streamlit run app.py
```

### Shutdown Commands
```bash
Ctrl + C
```

### Force Shutdown (if Ctrl+C doesn't work)
```bash
pkill -f streamlit
```

### Verify Application Status
```bash
ps aux | grep streamlit
```

### Access URLs
- Local: http://localhost:8501
- Network: http://10.1.41.46:8501

## 🎯 Usage Guide

### Image Recognition
1. Upload a food image
2. Click "Start Recognition"
3. View OCR recognition results and nutrition analysis

### Text Analysis
1. Enter food information in the chat interface
2. System automatically analyzes nutritional content
3. Get personalized recommendations

### Nutrition Analysis
1. View nutritional component distribution
2. Compare with nutrition targets
3. Analyze nutritional balance

## 🏇 Jockey-Specific Features

### Weight Management
- BMI calculation and classification
- Lightweight weight recommendations
- Pre-race nutrition strategies

### Nutrition Goals
- Weight Management Mode: 2000 kcal/day
- Energy Boost Mode: 2500 kcal/day
- Protein Focus: 120-150g/day

### Special Recommendations
- Avoid high-fat foods before races
- Maintain adequate water intake
- Meal distribution strategies

## 📊 Data Visualization

The system provides multiple chart types:
- **Pie Charts**: Nutritional component distribution
- **Bar Charts**: Food classification statistics
- **Radar Charts**: Nutritional balance analysis
- **Trend Charts**: Nutrition intake changes
- **Heat Maps**: Weekly nutrition patterns

## 🔧 Custom Configuration

### Food Classification
Modify `FOOD_CATEGORIES` in `config.py`:
```python
FOOD_CATEGORIES = {
    "Protein": ["chicken", "beef", "fish", ...],
    "Carbohydrates": ["rice", "bread", "noodles", ...],
    # More categories...
}
```

### Nutrition Targets
Modify target values in `NUTRITION_TARGETS`:
```python
NUTRITION_TARGETS = {
    "Weight Management": {
        "Calories": {"target": 2000, "unit": "kcal/day"},
        # More nutrients...
    }
}
```

## 🤖 AI Features Explained

### OCR Recognition
- Uses GPT-4 Vision model
- Supports Chinese and English recognition
- Automatically extracts food and nutrition information

### Food Classification
- Based on TF-IDF vectorization
- Random Forest classifier
- Confidence assessment

### Nutrition Analysis
- Nutritional component database
- Target comparison analysis
- Personalized recommendation generation

## 📈 Performance Optimization

- Model caching mechanism
- Asynchronous processing
- Responsive design
- Memory optimization

## 🔒 Security Considerations

- Secure API key storage
- Data privacy protection
- Input validation
- Error handling

## 🚀 Future Plans

-  Mobile application
-  More food databases
-  Real-time nutrition tracking
-  Social features
-  Professional nutritionist integration

## 📞 Technical Support

For questions or suggestions, please contact the development team.

---

**Note**: This system is for nutritional reference only. Please consult a professional nutritionist for specific dietary advice.

