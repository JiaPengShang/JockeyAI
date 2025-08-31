"""
Data processing module for structured data handling and export
"""
import pandas as pd
import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

from config import data_config
from exception_handler import exception_handler, ExceptionLevel

class DataProcessor:
    """Handle structured data processing and export functionality"""
    
    def __init__(self):
        self.data_store = []
        self.metadata_store = []
    
    def add_data_entry(self, structured_data: Dict, metadata: Dict) -> bool:
        """Add new data entry with metadata"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in structured_data:
                structured_data['timestamp'] = datetime.now().isoformat()
            
            # Validate data structure
            validated_data = self._validate_data_structure(structured_data)
            
            # Store data and metadata
            self.data_store.append(validated_data)
            self.metadata_store.append({
                'entry_id': len(self.data_store),
                'processing_time': datetime.now().isoformat(),
                **metadata
            })
            
            return True
            
        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_2,
                e,
                context={'data_validation_failed': True}
            )
            return False
    
    def _validate_data_structure(self, data: Dict) -> Dict:
        """Validate and clean data structure"""
        required_fields = ['name', 'date', 'diet_content', 'training_load', 'sleep_data', 'confidence_score']
        
        validated_data = {}
        for field in required_fields:
            validated_data[field] = data.get(field, '')
        
        # Add raw text if available
        validated_data['raw_text'] = data.get('raw_text', '')
        validated_data['timestamp'] = data.get('timestamp', datetime.now().isoformat())
        
        # Clean and format specific fields
        validated_data['confidence_score'] = float(validated_data['confidence_score']) if validated_data['confidence_score'] else 0.0
        
        # Ensure diet_content is a list
        if isinstance(validated_data['diet_content'], str):
            validated_data['diet_content'] = [validated_data['diet_content']] if validated_data['diet_content'] else []
        
        return validated_data
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """Export data to CSV format"""
        try:
            if not self.data_store:
                raise ValueError("No data available for export")
            
            # Prepare data for CSV export
            csv_data = []
            for entry in self.data_store:
                csv_row = entry.copy()
                # Convert list fields to string for CSV
                csv_row['diet_content'] = '; '.join(csv_row['diet_content']) if isinstance(csv_row['diet_content'], list) else csv_row['diet_content']
                csv_data.append(csv_row)
            
            # Create DataFrame
            df = pd.DataFrame(csv_data)
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ocr_data_export_{timestamp}.csv"
            
            filepath = os.path.join(data_config.output_dir, filename)
            
            # Export to CSV
            df.to_csv(filepath, index=False, encoding=data_config.csv_encoding)
            
            return filepath
            
        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_3,
                e,
                context={'export_format': 'CSV', 'raw_data': self.data_store}
            )
            return ""
    
    def export_to_json(self, filename: Optional[str] = None) -> str:
        """Export data to JSON format"""
        try:
            if not self.data_store:
                raise ValueError("No data available for export")
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ocr_data_export_{timestamp}.json"
            
            filepath = os.path.join(data_config.output_dir, filename)
            
            # Prepare export data with metadata
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_entries': len(self.data_store),
                    'format_version': '1.0'
                },
                'data': self.data_store,
                'metadata': self.metadata_store
            }
            
            # Export to JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=data_config.json_indent, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_3,
                e,
                context={'export_format': 'JSON', 'raw_data': self.data_store}
            )
            return ""
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of stored data"""
        if not self.data_store:
            return {'total_entries': 0, 'message': 'No data available'}
        
        summary = {
            'total_entries': len(self.data_store),
            'avg_confidence': sum(entry.get('confidence_score', 0) for entry in self.data_store) / len(self.data_store),
            'date_range': self._get_date_range(),
            'unique_names': len(set(entry.get('name', '') for entry in self.data_store if entry.get('name'))),
            'entries_with_diet': sum(1 for entry in self.data_store if entry.get('diet_content')),
            'entries_with_training': sum(1 for entry in self.data_store if entry.get('training_load')),
            'entries_with_sleep': sum(1 for entry in self.data_store if entry.get('sleep_data'))
        }
        
        return summary
    
    def _get_date_range(self) -> Dict[str, str]:
        """Get date range from stored data"""
        dates = []
        for entry in self.data_store:
            if entry.get('date'):
                dates.append(entry['date'])
            elif entry.get('timestamp'):
                dates.append(entry['timestamp'][:10])  # Extract date part
        
        if dates:
            return {
                'earliest': min(dates),
                'latest': max(dates)
            }
        return {'earliest': '', 'latest': ''}
    
    def get_dataframe(self) -> pd.DataFrame:
        """Get data as pandas DataFrame for visualization"""
        if not self.data_store:
            return pd.DataFrame()
        
        # Prepare data for DataFrame
        df_data = []
        for entry in self.data_store:
            df_row = entry.copy()
            # Convert list to string for DataFrame
            if isinstance(df_row.get('diet_content'), list):
                df_row['diet_content'] = '; '.join(df_row['diet_content'])
            df_data.append(df_row)
        
        return pd.DataFrame(df_data)
    
    def clear_data(self):
        """Clear all stored data"""
        self.data_store.clear()
        self.metadata_store.clear()
    
    def load_from_json(self, filepath: str) -> bool:
        """Load data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'data' in data:
                self.data_store = data['data']
            if 'metadata' in data:
                self.metadata_store = data['metadata']
            
            return True
            
        except Exception as e:
            exception_handler.handle_exception(
                ExceptionLevel.LEVEL_1,
                e,
                context={'operation': 'load_data'}
            )
            return False

# Global data processor instance
data_processor = DataProcessor()