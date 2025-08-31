#!/usr/bin/env python3
"""
JockeyAI 启动脚本
包含系统检查、依赖验证和应用程序启动
"""
import sys
import os
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'opencv-python',
        'pillow',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - 未安装")
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def check_ocr_engines():
    """检查OCR引擎"""
    print("\n🔍 检查OCR引擎...")
    
    # 检查Tesseract
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR: {version}")
    except Exception as e:
        print(f"❌ Tesseract OCR: 未安装或配置错误")
        print(f"   错误信息: {e}")
        print("   安装指南:")
        print("   Windows: 下载并安装 https://github.com/UB-Mannheim/tesseract/wiki")
        print("   macOS: brew install tesseract tesseract-lang")
        print("   Linux: sudo apt install tesseract-ocr tesseract-ocr-chi-sim")
    
    # 检查PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print("✅ PaddleOCR: 可用")
    except ImportError:
        print("❌ PaddleOCR: 未安装")
        print("   安装命令: pip install paddlepaddle paddleocr")
    
    return True

def check_directories():
    """检查并创建必要的目录"""
    directories = [
        "data",
        "data/uploads",
        "data/processed",
        "data/sample_images"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 目录: {directory}")

def generate_sample_data():
    """生成示例数据"""
    print("\n📊 检查示例数据...")
    
    sample_files = [
        "data/sample_food_log.csv",
        "data/sample_sleep_log.csv",
        "data/sample_training_log.csv",
        "data/sample_weight_log.csv"
    ]
    
    missing_files = [f for f in sample_files if not Path(f).exists()]
    
    if missing_files:
        print("⚠️ 缺少示例数据文件")
        response = input("是否生成示例数据? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            try:
                from sample_data import create_sample_files, create_sample_images
                create_sample_files()
                create_sample_images()
                print("✅ 示例数据生成完成")
            except Exception as e:
                print(f"❌ 生成示例数据失败: {e}")
    else:
        print("✅ 示例数据文件已存在")

def check_database():
    """检查数据库"""
    print("\n🗄️ 检查数据库...")
    
    try:
        from database import DatabaseManager
        db_manager = DatabaseManager()
        print("✅ 数据库连接正常")
        
        # 检查数据库统计
        stats = db_manager.get_statistics()
        if stats:
            print(f"   文件数: {stats.get('files', {}).get('total', 0)}")
            print(f"   数据记录: {stats.get('data', {}).get('total_records', 0)}")
        else:
            print("   数据库为空")
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")

def start_application():
    """启动应用程序"""
    print("\n🚀 启动JockeyAI应用程序...")
    
    try:
        # 启动Streamlit应用
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用程序已停止")
    except Exception as e:
        print(f"❌ 启动应用程序失败: {e}")

def main():
    """主函数"""
    print("🏇 JockeyAI 系统检查")
    print("=" * 50)
    
    # 系统检查
    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("OCR引擎", check_ocr_engines),
        ("目录结构", check_directories),
        ("示例数据", generate_sample_data),
        ("数据库", check_database)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n🔍 检查{check_name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("✅ 所有检查通过！")
        start_application()
    else:
        print("❌ 系统检查未通过，请解决上述问题后重试")
        print("\n💡 常见解决方案:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 安装Tesseract OCR")
        print("3. 检查Python版本 (需要3.8+)")
        print("4. 确保有足够的磁盘空间和权限")

if __name__ == "__main__":
    main()
