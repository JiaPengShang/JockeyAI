"""
数据库模块 - 数据存储和管理
"""
import sqlite3
import pandas as pd
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

from config import DATABASE_PATH, DATA_SCHEMAS

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = None):
        """初始化数据库管理器"""
        self.db_path = db_path or DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建文件记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        schema_name TEXT NOT NULL,
                        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_size INTEGER,
                        status TEXT DEFAULT 'uploaded',
                        ocr_accuracy REAL,
                        processing_time REAL
                    )
                ''')
                
                # 创建OCR结果表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ocr_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id INTEGER,
                        ocr_engine TEXT NOT NULL,
                        confidence REAL,
                        text_content TEXT,
                        bbox TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (file_id) REFERENCES file_records (id)
                    )
                ''')
                
                # 创建结构化数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS structured_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id INTEGER,
                        schema_name TEXT NOT NULL,
                        data_json TEXT NOT NULL,
                        created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (file_id) REFERENCES file_records (id)
                    )
                ''')
                
                # 创建数据统计表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        schema_name TEXT NOT NULL,
                        total_records INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_summary TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def save_file_record(self, filename: str, file_path: str, file_type: str, 
                        schema_name: str, file_size: int = None) -> int:
        """保存文件记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO file_records (filename, file_path, file_type, schema_name, file_size)
                    VALUES (?, ?, ?, ?, ?)
                ''', (filename, file_path, file_type, schema_name, file_size))
                
                file_id = cursor.lastrowid
                conn.commit()
                logger.info(f"File record saved with ID: {file_id}")
                return file_id
                
        except Exception as e:
            logger.error(f"Error saving file record: {e}")
            raise
    
    def save_ocr_results(self, file_id: int, ocr_results: List[Dict[str, Any]]):
        """保存OCR结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for result in ocr_results:
                    cursor.execute('''
                        INSERT INTO ocr_results (file_id, ocr_engine, confidence, text_content, bbox)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        file_id,
                        result.get('engine', 'unknown'),
                        result.get('confidence', 0.0),
                        result.get('text', ''),
                        json.dumps(result.get('bbox', []))
                    ))
                
                conn.commit()
                logger.info(f"OCR results saved for file ID: {file_id}")
                
        except Exception as e:
            logger.error(f"Error saving OCR results: {e}")
            raise
    
    def save_structured_data(self, file_id: int, schema_name: str, 
                           structured_data: List[Dict[str, Any]]):
        """保存结构化数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for data_row in structured_data:
                    cursor.execute('''
                        INSERT INTO structured_data (file_id, schema_name, data_json)
                        VALUES (?, ?, ?)
                    ''', (file_id, schema_name, json.dumps(data_row, default=str)))
                
                conn.commit()
                logger.info(f"Structured data saved for file ID: {file_id}")
                
        except Exception as e:
            logger.error(f"Error saving structured data: {e}")
            raise
    
    def update_file_status(self, file_id: int, status: str, 
                          ocr_accuracy: float = None, processing_time: float = None):
        """更新文件处理状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if ocr_accuracy is not None and processing_time is not None:
                    cursor.execute('''
                        UPDATE file_records 
                        SET status = ?, ocr_accuracy = ?, processing_time = ?
                        WHERE id = ?
                    ''', (status, ocr_accuracy, processing_time, file_id))
                else:
                    cursor.execute('''
                        UPDATE file_records 
                        SET status = ?
                        WHERE id = ?
                    ''', (status, file_id))
                
                conn.commit()
                logger.info(f"File status updated to '{status}' for file ID: {file_id}")
                
        except Exception as e:
            logger.error(f"Error updating file status: {e}")
            raise
    
    def get_file_records(self, schema_name: str = None, status: str = None) -> List[Dict[str, Any]]:
        """获取文件记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM file_records"
                params = []
                
                if schema_name or status:
                    query += " WHERE"
                    if schema_name:
                        query += " schema_name = ?"
                        params.append(schema_name)
                    if status:
                        if schema_name:
                            query += " AND"
                        query += " status = ?"
                        params.append(status)
                
                query += " ORDER BY upload_time DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df.to_dict('records')
                
        except Exception as e:
            logger.error(f"Error getting file records: {e}")
            return []
    
    def get_structured_data(self, schema_name: str = None, file_id: int = None) -> pd.DataFrame:
        """获取结构化数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM structured_data"
                params = []
                
                if schema_name or file_id:
                    query += " WHERE"
                    if schema_name:
                        query += " schema_name = ?"
                        params.append(schema_name)
                    if file_id:
                        if schema_name:
                            query += " AND"
                        query += " file_id = ?"
                        params.append(file_id)
                
                df = pd.read_sql_query(query, conn, params=params)
                
                # 解析JSON数据
                if not df.empty:
                    df['data'] = df['data_json'].apply(json.loads)
                    # 展开数据列
                    expanded_data = pd.json_normalize(df['data'])
                    df = pd.concat([df.drop(['data_json', 'data'], axis=1), expanded_data], axis=1)
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting structured data: {e}")
            return pd.DataFrame()
    
    def get_data_summary(self, schema_name: str) -> Dict[str, Any]:
        """获取数据摘要"""
        try:
            df = self.get_structured_data(schema_name)
            
            if df.empty:
                return {
                    'total_records': 0,
                    'date_range': None,
                    'columns': [],
                    'last_updated': None
                }
            
            summary = {
                'total_records': len(df),
                'columns': list(df.columns),
                'last_updated': df['created_time'].max() if 'created_time' in df.columns else None
            }
            
            # 日期范围
            date_columns = [col for col in df.columns if 'date' in col.lower()]
            if date_columns:
                date_col = date_columns[0]
                try:
                    dates = pd.to_datetime(df[date_col])
                    summary['date_range'] = {
                        'start': dates.min().strftime('%Y-%m-%d'),
                        'end': dates.max().strftime('%Y-%m-%d'),
                        'days': (dates.max() - dates.min()).days
                    }
                except:
                    pass
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
    
    def delete_file_record(self, file_id: int):
        """删除文件记录及相关数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除相关数据
                cursor.execute("DELETE FROM ocr_results WHERE file_id = ?", (file_id,))
                cursor.execute("DELETE FROM structured_data WHERE file_id = ?", (file_id,))
                cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
                
                conn.commit()
                logger.info(f"File record and related data deleted for file ID: {file_id}")
                
        except Exception as e:
            logger.error(f"Error deleting file record: {e}")
            raise
    
    def export_data(self, schema_name: str, format: str = 'csv', 
                   output_path: str = None) -> str:
        """导出数据"""
        try:
            df = self.get_structured_data(schema_name)
            
            if df.empty:
                raise ValueError(f"No data found for schema: {schema_name}")
            
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"data/export_{schema_name}_{timestamp}.{format}"
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'csv':
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif format.lower() == 'excel':
                df.to_excel(output_path, index=False)
            elif format.lower() == 'json':
                df.to_json(output_path, orient='records', force_ascii=False, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Data exported to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # 文件统计
                df_files = pd.read_sql_query("SELECT * FROM file_records", conn)
                stats['files'] = {
                    'total': len(df_files),
                    'by_status': df_files['status'].value_counts().to_dict(),
                    'by_schema': df_files['schema_name'].value_counts().to_dict(),
                    'by_type': df_files['file_type'].value_counts().to_dict()
                }
                
                # 数据统计
                df_data = pd.read_sql_query("SELECT * FROM structured_data", conn)
                stats['data'] = {
                    'total_records': len(df_data),
                    'by_schema': df_data['schema_name'].value_counts().to_dict()
                }
                
                # OCR统计
                df_ocr = pd.read_sql_query("SELECT * FROM ocr_results", conn)
                stats['ocr'] = {
                    'total_results': len(df_ocr),
                    'avg_confidence': df_ocr['confidence'].mean() if not df_ocr.empty else 0,
                    'by_engine': df_ocr['ocr_engine'].value_counts().to_dict()
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除指定天数前的文件记录
                cursor.execute('''
                    DELETE FROM file_records 
                    WHERE upload_time < datetime('now', '-{} days')
                '''.format(days))
                
                # 删除孤立的OCR结果和结构化数据
                cursor.execute('''
                    DELETE FROM ocr_results 
                    WHERE file_id NOT IN (SELECT id FROM file_records)
                ''')
                
                cursor.execute('''
                    DELETE FROM structured_data 
                    WHERE file_id NOT IN (SELECT id FROM file_records)
                ''')
                
                conn.commit()
                logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            raise
