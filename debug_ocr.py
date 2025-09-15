#!/usr/bin/env python3
import os
import fitz
from PIL import Image
import io
from ocr_processor import OCRProcessor

def debug_pdf_ocr(pdf_path: str, page_num: int = 0):
    """调试PDF特定页面的OCR结果"""
    print(f"调试PDF: {pdf_path}, 页面: {page_num + 1}")
    
    # 渲染PDF页面
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    zoom = 200 / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()
    
    # OCR处理
    ocr = OCRProcessor()
    raw_text = ocr.extract_text_from_image(img, language="zh")
    
    print("=" * 50)
    print("原始OCR文本:")
    print("=" * 50)
    print(raw_text)
    print("=" * 50)
    
    return raw_text

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        page_num = int(sys.argv[1]) if len(sys.argv) > 2 else 0
        debug_pdf_ocr("JockeyDiaries230725.pdf", page_num)
    else:
        print("用法: python debug_ocr.py [页面号]")
        print("示例: python debug_ocr.py 0  # 查看第1页")
