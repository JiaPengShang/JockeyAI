# AI-Driven OCR and Visualization System - MVP Todo

## Project Overview
Develop a Streamlit-based web application for trainee jockeys to digitize handwritten/scanned forms and visualize training data with OCR integration (TesseractOCR + PaddleOCR) and Material3 design.

## MVP Implementation Plan (8 files max)

### Core Files to Create:
1. **app.py** - Main Streamlit application with Material3 styling
2. **ocr_processor.py** - OCR integration (TesseractOCR + PaddleOCR)
3. **data_processor.py** - Data structure handling and CSV/JSON export
4. **visualizer.py** - Chart generation and interactive visualization
5. **exception_handler.py** - 3-level exception handling system
6. **config.py** - Configuration and settings management
7. **utils.py** - Utility functions and helpers
8. **requirements.txt** - Dependencies (already exists, will update)

### Key Features (MVP):
- File upload interface (PDF/images)
- OCR processing with dual engine support
- Structured data output (CSV/JSON)
- Interactive visualizations (charts for diet, training, sleep)
- Material3 design implementation
- Error handling and recovery
- Progress tracking and status display

### Simplified Implementation Strategy:
- Focus on core OCR + visualization functionality
- Use mock data for initial testing if needed
- Implement basic Material3 styling with CSS
- Prioritize working functionality over perfect accuracy
- Include essential error handling without over-engineering

### Data Structure:
- Extracted fields: name, date, diet_content, training_load, sleep_data
- Output formats: CSV and JSON
- Metadata tracking: filename, upload_time, processing_status

### Visualization Types:
- Diet: Pie charts (nutrition distribution), Bar charts (daily calories)
- Training: Line charts (intensity trends), Heatmaps (frequency)
- Sleep: Bar charts (duration), Line charts (quality trends)

This MVP will demonstrate the core concept while maintaining simplicity for higher success rate.