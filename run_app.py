#!/usr/bin/env python3
"""
Jockey Nutrition AI - launcher script
"""

import subprocess
import sys
import os

def install_requirements():
    """Install Python dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def run_app():
    """Run the app"""
    print("Starting Jockey Nutrition AI app...")
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
        print("\nApp stopped")
    except Exception as e:
        print(f"❌ Failed to start app: {e}")

def main():
    """Main entry"""
    print("🏇 Jockey Nutrition AI - Launcher")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return
    
    # Install dependencies
    if not install_requirements():
        return
    
    # Run app
    run_app()

if __name__ == "__main__":
    main()
