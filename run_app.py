#!/usr/bin/env python3
"""
骑师营养AI应用启动脚本
"""

import subprocess
import sys
import os

def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖包安装完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False
    return True

def run_app():
    """运行应用"""
    print("正在启动骑师营养AI应用...")
    try:
        # 设置环境变量
        os.environ["STREAMLIT_SERVER_PORT"] = "8501"
        os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
        
        # 启动Streamlit应用
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")

def main():
    """主函数"""
    print("🏇 骑师营养AI - 启动脚本")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return
    
    # 安装依赖
    if not install_requirements():
        return
    
    # 运行应用
    run_app()

if __name__ == "__main__":
    main()
