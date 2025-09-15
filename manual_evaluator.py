#!/usr/bin/env python3
"""
Manual Evaluation Script for Diary Extractor
Allows manual comparison of extracted results with PDF pages
"""

import json
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from typing import Dict, List, Any
import argparse
from datetime import datetime

class ManualDiaryEvaluator:
    def __init__(self, pdf_path: str, json_path: str):
        self.pdf_path = pdf_path
        self.json_path = json_path
        self.extracted_results = None
        self.evaluation_data = []
        
    def load_data(self):
        """Load PDF and JSON data"""
        print("📄 Loading data...")
        
        # Load extracted results
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.extracted_results = json.load(f)
        
        # Load PDF
        self.doc = fitz.open(self.pdf_path)
        
        print(f"✅ Loaded {len(self.extracted_results['pages'])} extracted pages")
        print(f"✅ Loaded PDF with {len(self.doc)} pages")
        
    def display_page_for_evaluation(self, page_num: int):
        """Display a page for manual evaluation"""
        if page_num >= len(self.extracted_results['pages']):
            print(f"❌ Page {page_num + 1} not found in extracted results")
            return
            
        # Get PDF page
        pdf_page = self.doc[page_num]
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
        pix = pdf_page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Get extracted data
        extracted_page = self.extracted_results['pages'][page_num]
        
        print(f"\n{'='*80}")
        print(f"📄 EVALUATING PAGE {page_num + 1}")
        print(f"{'='*80}")
        
        print(f"📊 Extracted Category: {extracted_page['category']}")
        print(f"📝 Extracted Content:")
        print(json.dumps(extracted_page['structured'], indent=2, ensure_ascii=False))
        
        print(f"\n🔍 PDF Page {page_num + 1} (saved as page_{page_num + 1}.png)")
        
        # Save page image for manual inspection
        img.save(f"page_{page_num + 1}.png")
        
        return {
            'page_number': page_num + 1,
            'extracted_category': extracted_page['category'],
            'extracted_content': extracted_page['structured']
        }
    
    def interactive_evaluation(self, max_pages: int = 10):
        """Interactive evaluation process"""
        print(f"🎯 Starting interactive evaluation for first {max_pages} pages...")
        print("Instructions:")
        print("1. For each page, examine the PDF image and extracted content")
        print("2. Answer the evaluation questions")
        print("3. Results will be saved automatically")
        
        self.evaluation_data = []
        
        for page_num in range(min(max_pages, len(self.extracted_results['pages']))):
            page_info = self.display_page_for_evaluation(page_num)
            
            print(f"\n❓ EVALUATION QUESTIONS FOR PAGE {page_num + 1}:")
            
            # Classification evaluation
            print(f"\n1. What is the correct category for this page?")
            print("   Options: food_diary, riding_diary, sleep_diary_morning, sleep_diary_night, unknown")
            correct_category = input("   Your answer: ").strip()
            
            classification_correct = correct_category == page_info['extracted_category']
            
            # Content evaluation
            print(f"\n2. Rate the content extraction accuracy (0-100):")
            print("   0 = Completely wrong, 50 = Partially correct, 100 = Perfect")
            try:
                content_accuracy = float(input("   Your rating: ").strip())
                content_accuracy = max(0, min(100, content_accuracy)) / 100  # Normalize to 0-1
            except ValueError:
                content_accuracy = 0.5
                print("   Invalid input, using 0.5 as default")
            
            # Specific issues
            print(f"\n3. Any specific issues or comments?")
            comments = input("   Comments: ").strip()
            
            # Compile evaluation
            evaluation = {
                'page_number': page_num + 1,
                'extracted_category': page_info['extracted_category'],
                'correct_category': correct_category,
                'classification_correct': classification_correct,
                'content_accuracy': content_accuracy,
                'comments': comments,
                'extracted_content': page_info['extracted_content']
            }
            
            self.evaluation_data.append(evaluation)
            
            print(f"\n✅ Page {page_num + 1} evaluation completed")
            print(f"   Classification: {'✅ Correct' if classification_correct else '❌ Incorrect'}")
            print(f"   Content accuracy: {content_accuracy:.1%}")
            
            # Ask if user wants to continue
            if page_num < max_pages - 1:
                continue_eval = input(f"\nContinue to next page? (y/n): ").strip().lower()
                if continue_eval != 'y':
                    break
        
        self.doc.close()
        return self.evaluation_data
    
    def calculate_metrics(self):
        """Calculate evaluation metrics"""
        if not self.evaluation_data:
            return None
            
        total_pages = len(self.evaluation_data)
        correct_classifications = sum(1 for eval_data in self.evaluation_data if eval_data['classification_correct'])
        avg_content_accuracy = sum(eval_data['content_accuracy'] for eval_data in self.evaluation_data) / total_pages
        
        # Category-wise breakdown
        category_stats = {}
        for eval_data in self.evaluation_data:
            category = eval_data['extracted_category']
            if category not in category_stats:
                category_stats[category] = {'count': 0, 'correct_class': 0, 'content_accuracy': []}
            
            category_stats[category]['count'] += 1
            if eval_data['classification_correct']:
                category_stats[category]['correct_class'] += 1
            category_stats[category]['content_accuracy'].append(eval_data['content_accuracy'])
        
        # Calculate category metrics
        for category in category_stats:
            stats = category_stats[category]
            stats['classification_accuracy'] = stats['correct_class'] / stats['count']
            stats['avg_content_accuracy'] = sum(stats['content_accuracy']) / len(stats['content_accuracy'])
        
        return {
            'total_pages': total_pages,
            'overall_classification_accuracy': correct_classifications / total_pages,
            'overall_content_accuracy': avg_content_accuracy,
            'category_breakdown': category_stats
        }
    
    def save_results(self, output_path: str = "manual_evaluation_results.json"):
        """Save evaluation results"""
        if not self.evaluation_data:
            print("❌ No evaluation data to save")
            return
            
        metrics = self.calculate_metrics()
        
        results = {
            'evaluation_metadata': {
                'pdf_file': self.pdf_path,
                'json_file': self.json_path,
                'evaluation_date': datetime.now().isoformat(),
                'total_pages_evaluated': len(self.evaluation_data)
            },
            'metrics': metrics,
            'detailed_results': self.evaluation_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to {output_path}")
        return results
    
    def print_summary(self):
        """Print evaluation summary"""
        if not self.evaluation_data:
            print("❌ No evaluation data available")
            return
            
        metrics = self.calculate_metrics()
        
        print(f"\n{'='*60}")
        print("📊 MANUAL EVALUATION SUMMARY")
        print(f"{'='*60}")
        
        print(f"📄 Total pages evaluated: {metrics['total_pages']}")
        print(f"🎯 Overall classification accuracy: {metrics['overall_classification_accuracy']:.1%}")
        print(f"📝 Overall content accuracy: {metrics['overall_content_accuracy']:.1%}")
        
        print(f"\n📊 Category-wise breakdown:")
        for category, stats in metrics['category_breakdown'].items():
            print(f"  {category}:")
            print(f"    Pages: {stats['count']}")
            print(f"    Classification accuracy: {stats['classification_accuracy']:.1%}")
            print(f"    Content accuracy: {stats['avg_content_accuracy']:.1%}")
        
        print(f"\n📋 Detailed results:")
        for eval_data in self.evaluation_data:
            status = "✅" if eval_data['classification_correct'] else "❌"
            print(f"  Page {eval_data['page_number']}: {status} {eval_data['extracted_category']} -> {eval_data['correct_category']} (Content: {eval_data['content_accuracy']:.1%})")
            if eval_data['comments']:
                print(f"    Comments: {eval_data['comments']}")

def main():
    parser = argparse.ArgumentParser(description="Manual evaluation of diary extraction accuracy")
    parser.add_argument("--pdf", default="JockeyDiaries230725.pdf", help="Path to PDF file")
    parser.add_argument("--json", default="JockeyDiaries230725.json", help="Path to extracted JSON file")
    parser.add_argument("--output", default="manual_evaluation_results.json", help="Output file for results")
    parser.add_argument("--pages", type=int, default=10, help="Number of pages to evaluate")
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.pdf):
        print(f"❌ PDF file not found: {args.pdf}")
        return
        
    if not os.path.exists(args.json):
        print(f"❌ JSON file not found: {args.json}")
        return
    
    # Initialize evaluator
    evaluator = ManualDiaryEvaluator(args.pdf, args.json)
    evaluator.load_data()
    
    # Run interactive evaluation
    evaluator.interactive_evaluation(max_pages=args.pages)
    
    # Save and display results
    evaluator.save_results(args.output)
    evaluator.print_summary()

if __name__ == "__main__":
    main()
