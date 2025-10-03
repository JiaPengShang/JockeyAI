#!/usr/bin/env python3
"""
Jockey Nutrition AI Application Startup Script
"""

import subprocess
import sys
import os

def install_requirements():
    """Install dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def run_app():
    """Run application"""
    print("Starting Jockey Nutrition AI application...")
    try:
        # Set environment variables
        os.environ["STREAMLIT_SERVER_PORT"] = "8501"
        os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
        
        # Start Streamlit application
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\nApplication stopped")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")

def main():
    """Main function"""
    print("🏇 Jockey Nutrition AI - Startup Script")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        return
    
    # Install dependencies
    if not install_requirements():
        return
    
    # Run application
    run_app()

if __name__ == "__main__":
    main()
