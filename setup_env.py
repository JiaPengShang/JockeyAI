#!/usr/bin/env python3
"""
Environment Variable Setup Assistant
Helps users safely set up OpenAI API key
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file"""
    env_file = Path('.env')
    
    if env_file.exists():
        print("⚠️  .env file already exists")
        response = input("Do you want to overwrite the existing file? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return False
    
    print("\n🔐 Setting up OpenAI API Key")
    print("Please get your API key from https://platform.openai.com/account/api-keys")
    
    api_key = input("Please enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ API key cannot be empty")
        return False
    
    if not api_key.startswith("sk-"):
        print("❌ API key format is incorrect, should start with 'sk-'")
        return False
    
    # Write to .env file
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        
        print("✅ .env file created successfully!")
        print(f"📁 File location: {env_file.absolute()}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def verify_setup():
    """Verify environment variable setup"""
    print("\n🔍 Verifying environment variable setup...")
    
    # Reload environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Environment variable not set")
        return False
    
    if not api_key.startswith("sk-"):
        print("❌ API key format is incorrect")
        return False
    
    print("✅ Environment variable setup is correct")
    print(f"🔑 API key: {api_key[:10]}...{api_key[-4:]}")
    return True

def main():
    print("🚀 JockeyInsight Environment Variable Setup Assistant")
    print("=" * 50)
    
    # Check if in correct directory
    if not Path('config.py').exists():
        print("❌ Please run this script in the project root directory")
        sys.exit(1)
    
    # Create .env file
    if create_env_file():
        # Verify setup
        if verify_setup():
            print("\n🎉 Setup completed!")
            print("You can now run the application:")
            print("streamlit run app.py")
        else:
            print("\n❌ Setup verification failed, please check .env file")
    else:
        print("\n❌ Setup failed")

if __name__ == "__main__":
    main()
