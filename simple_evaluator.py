#!/usr/bin/env python3
"""
Simple Evaluation Script for Diary Extractor
Compares extracted results with PDF pages and generates evaluation report
"""

import json
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from typing import Dict, List, Any
import argparse
from datetime import datetime

def load_extracted_results(json_path: str) -> Dict:
    """Load extracted JSON results"""
    print(f"📄 Loading extracted results from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_pdf_pages(pdf_path: str, max_pages: int = 10) -> List[Dict]:
    """Extract first N pages from PDF"""
    print(f"📖 Extracting first {max_pages} pages from {pdf_path}...")
    
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num in range(min(len(doc), max_pages)):
        page = doc[page_num]
        # Convert to image
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        pages.append({
            'page_number': page_num + 1,
            'image': img,
            'text': page.get_text()
        })
        
        # Save page image for manual inspection
        img.save(f"page_{page_num + 1}.png")
        print(f"  ✅ Page {page_num + 1} saved as page_{page_num + 1}.png")
    
    doc.close()
    return pages

def generate_evaluation_template(extracted_results: Dict, pdf_pages: List[Dict]) -> Dict:
    """Generate evaluation template for manual review"""
    print("📋 Generating evaluation template...")
    
    template = {
        "evaluation_instructions": {
            "description": "Manual evaluation of diary extraction accuracy",
            "steps": [
                "1. Open each page_N.png file to see the PDF page",
                "2. Compare with the extracted content below",
                "3. Fill in the evaluation for each page",
                "4. Rate accuracy from 0-100 (0=completely wrong, 100=perfect)",
                "5. Note any specific issues"
            ]
        },
        "pages_to_evaluate": []
    }
    
    for i, pdf_page in enumerate(pdf_pages):
        if i >= len(extracted_results['pages']):
            break
            
        extracted_page = extracted_results['pages'][i]
        
        page_eval = {
            "page_number": i + 1,
            "pdf_image": f"page_{i + 1}.png",
            "extracted_category": extracted_page['category'],
            "manual_classification": "TO_BE_FILLED",
            "classification_correct": "TO_BE_FILLED",
            "content_accuracy_rating": "TO_BE_FILLED",  # 0-100
            "content_accuracy_percentage": "TO_BE_FILLED",  # 0-1
            "specific_issues": "TO_BE_FILLED",
            "comments": "TO_BE_FILLED",
            "extracted_content": extracted_page['structured']
        }
        
        template["pages_to_evaluate"].append(page_eval)
    
    return template

def calculate_metrics_from_template(template: Dict) -> Dict:
    """Calculate metrics from filled template"""
    pages = template["pages_to_evaluate"]
    
    if not pages:
        return {"error": "No pages to evaluate"}
    
    # Filter out unfilled evaluations
    filled_pages = [p for p in pages if p.get("classification_correct") != "TO_BE_FILLED"]
    
    if not filled_pages:
        return {"error": "No evaluations completed yet"}
    
    total_pages = len(filled_pages)
    correct_classifications = sum(1 for p in filled_pages if p.get("classification_correct") == True)
    
    # Calculate content accuracy
    content_ratings = []
    for p in filled_pages:
        rating = p.get("content_accuracy_rating")
        if isinstance(rating, (int, float)) and 0 <= rating <= 100:
            content_ratings.append(rating / 100)  # Convert to 0-1 scale
    
    avg_content_accuracy = sum(content_ratings) / len(content_ratings) if content_ratings else 0
    
    # Category breakdown
    category_stats = {}
    for p in filled_pages:
        category = p["extracted_category"]
        if category not in category_stats:
            category_stats[category] = {
                "count": 0,
                "correct_classifications": 0,
                "content_ratings": []
            }
        
        category_stats[category]["count"] += 1
        if p.get("classification_correct") == True:
            category_stats[category]["correct_classifications"] += 1
        
        rating = p.get("content_accuracy_rating")
        if isinstance(rating, (int, float)) and 0 <= rating <= 100:
            category_stats[category]["content_ratings"].append(rating / 100)
    
    # Calculate category metrics
    for category in category_stats:
        stats = category_stats[category]
        stats["classification_accuracy"] = stats["correct_classifications"] / stats["count"]
        stats["avg_content_accuracy"] = sum(stats["content_ratings"]) / len(stats["content_ratings"]) if stats["content_ratings"] else 0
    
    return {
        "total_pages_evaluated": total_pages,
        "overall_classification_accuracy": correct_classifications / total_pages,
        "overall_content_accuracy": avg_content_accuracy,
        "category_breakdown": category_stats
    }

def print_evaluation_summary(metrics: Dict):
    """Print evaluation summary"""
    if "error" in metrics:
        print(f"❌ {metrics['error']}")
        return
    
    print(f"\n{'='*60}")
    print("📊 EVALUATION SUMMARY")
    print(f"{'='*60}")
    
    print(f"📄 Total pages evaluated: {metrics['total_pages_evaluated']}")
    print(f"🎯 Overall classification accuracy: {metrics['overall_classification_accuracy']:.1%}")
    print(f"📝 Overall content accuracy: {metrics['overall_content_accuracy']:.1%}")
    
    print(f"\n📊 Category-wise breakdown:")
    for category, stats in metrics['category_breakdown'].items():
        print(f"  {category}:")
        print(f"    Pages: {stats['count']}")
        print(f"    Classification accuracy: {stats['classification_accuracy']:.1%}")
        print(f"    Content accuracy: {stats['avg_content_accuracy']:.1%}")

def main():
    parser = argparse.ArgumentParser(description="Evaluate diary extraction accuracy")
    parser.add_argument("--pdf", default="JockeyDiaries230725.pdf", help="Path to PDF file")
    parser.add_argument("--json", default="JockeyDiaries230725.json", help="Path to extracted JSON file")
    parser.add_argument("--output", default="evaluation_template.json", help="Output file for evaluation template")
    parser.add_argument("--pages", type=int, default=10, help="Number of pages to evaluate")
    parser.add_argument("--calculate", action="store_true", help="Calculate metrics from filled template")
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.pdf):
        print(f"❌ PDF file not found: {args.pdf}")
        return
        
    if not os.path.exists(args.json):
        print(f"❌ JSON file not found: {args.json}")
        return
    
    if args.calculate:
        # Calculate metrics from filled template
        print(f"📊 Calculating metrics from {args.output}...")
        with open(args.output, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        metrics = calculate_metrics_from_template(template)
        print_evaluation_summary(metrics)
        
        # Save metrics
        metrics_file = args.output.replace('.json', '_metrics.json')
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"💾 Metrics saved to {metrics_file}")
        
    else:
        # Generate evaluation template
        print("🚀 Generating evaluation template...")
        
        # Load data
        extracted_results = load_extracted_results(args.json)
        pdf_pages = extract_pdf_pages(args.pdf, args.pages)
        
        # Generate template
        template = generate_evaluation_template(extracted_results, pdf_pages)
        
        # Save template
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Evaluation template saved to {args.output}")
        print(f"📁 Page images saved as page_1.png, page_2.png, etc.")
        print(f"\n📋 Next steps:")
        print(f"1. Open each page_N.png file to see the PDF pages")
        print(f"2. Fill in the evaluation in {args.output}")
        print(f"3. Run: python3 simple_evaluator.py --calculate --output {args.output}")

if __name__ == "__main__":
    main()
