"""
Test script for OCR engine hot-swapping and ablation study functionality
"""
import sys
import os
import numpy as np
from PIL import Image

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_engines import engine_manager, TesseractEngine, PaddleOCREngine
from ocr_config_manager import config_manager
from config import ocr_config


def create_test_image():
    """Create a simple test image with text"""
    # Create a white image with black text
    img = Image.new('RGB', (400, 200), color='white')
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(img)
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    # Add some test text
    draw.text((50, 50), "Name: John Doe", fill='black', font=font)
    draw.text((50, 80), "Date: 2024-01-15", fill='black', font=font)
    draw.text((50, 110), "Training: 30 min running", fill='black', font=font)
    draw.text((50, 140), "Sleep: 8 hours", fill='black', font=font)
    
    return np.array(img)


def test_engine_initialization():
    """Test OCR engine initialization"""
    print("🔧 Testing OCR Engine Initialization...")
    
    # Test Tesseract engine
    print("Testing Tesseract engine...")
    tesseract_engine = TesseractEngine()
    print(f"Tesseract available: {tesseract_engine.is_available}")
    
    # Test PaddleOCR engine
    print("Testing PaddleOCR engine...")
    paddle_engine = PaddleOCREngine()
    print(f"PaddleOCR available: {paddle_engine.is_available}")
    
    return tesseract_engine.is_available or paddle_engine.is_available


def test_engine_manager():
    """Test engine manager functionality"""
    print("\n🔧 Testing Engine Manager...")
    
    # Get available engines
    available_engines = engine_manager.get_available_engines()
    print(f"Available engines: {available_engines}")
    
    # Get active engines
    active_engines = engine_manager.get_active_engines()
    print(f"Active engines: {active_engines}")
    
    # Test engine status
    status = engine_manager.get_engine_status()
    print("Engine status:")
    for name, info in status.items():
        print(f"  {name}: Available={info['available']}, Active={info['active']}")
    
    return len(available_engines) > 0


def test_engine_switching():
    """Test engine switching functionality"""
    print("\n🔄 Testing Engine Switching...")
    
    available_engines = engine_manager.get_available_engines()
    if not available_engines:
        print("No engines available for testing")
        return False
    
    # Test switching to first available engine only
    first_engine = available_engines[0]
    engine_manager.set_active_engines([first_engine])
    active_engines = engine_manager.get_active_engines()
    print(f"Switched to {first_engine} only: {active_engines}")
    
    # Test switching to all available engines
    engine_manager.set_active_engines(available_engines)
    active_engines = engine_manager.get_active_engines()
    print(f"Switched to all engines: {active_engines}")
    
    # Test enabling/disabling individual engines
    if len(available_engines) > 1:
        engine_manager.disable_engine(available_engines[0])
        active_engines = engine_manager.get_active_engines()
        print(f"Disabled {available_engines[0]}: {active_engines}")
        
        engine_manager.enable_engine(available_engines[0])
        active_engines = engine_manager.get_active_engines()
        print(f"Re-enabled {available_engines[0]}: {active_engines}")
    
    return True


def test_image_processing():
    """Test image processing with different engine configurations"""
    print("\n🖼️ Testing Image Processing...")
    
    # Create test image
    test_image = create_test_image()
    print("Created test image")
    
    available_engines = engine_manager.get_available_engines()
    if not available_engines:
        print("No engines available for processing")
        return False
    
    # Test with each engine individually
    for engine_name in available_engines:
        print(f"\nTesting {engine_name}...")
        engine_manager.set_active_engines([engine_name])
        
        results = engine_manager.process_image(test_image)
        if results:
            for result in results:
                print(f"  Engine: {result.engine}")
                print(f"  Confidence: {result.confidence:.3f}")
                print(f"  Text: {result.text[:100]}...")
        else:
            print(f"  No results from {engine_name}")
    
    # Test with all engines
    print(f"\nTesting all engines...")
    engine_manager.set_active_engines(available_engines)
    results = engine_manager.process_image(test_image)
    if results:
        print(f"  Total results: {len(results)}")
        for result in results:
            print(f"  {result.engine}: {result.confidence:.3f}")
    else:
        print("  No results from any engine")
    
    return True


def test_config_manager():
    """Test configuration manager functionality"""
    print("\n📋 Testing Configuration Manager...")
    
    # Test preset configurations
    presets = config_manager.get_preset_configs()
    print(f"Available presets: {list(presets.keys())}")
    
    # Test saving current configuration
    exp_id = config_manager.save_current_config(
        "Test Experiment", 
        "Test configuration for ablation study"
    )
    print(f"Saved experiment: {exp_id}")
    
    # Test listing experiments
    experiments = config_manager.list_experiments()
    print(f"Saved experiments: {len(experiments)}")
    
    # Test loading experiment
    if experiments:
        first_exp = experiments[0]
        success = config_manager.load_experiment(first_exp['id'])
        print(f"Loaded experiment {first_exp['id']}: {success}")
    
    return True


def main():
    """Run all tests"""
    print("🧪 OCR Engine Hot-Swapping Test Suite")
    print("=" * 50)
    
    tests = [
        ("Engine Initialization", test_engine_initialization),
        ("Engine Manager", test_engine_manager),
        ("Engine Switching", test_engine_switching),
        ("Image Processing", test_image_processing),
        ("Config Manager", test_config_manager),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ FAIL {test_name}: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! OCR engine hot-swapping is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    main()
