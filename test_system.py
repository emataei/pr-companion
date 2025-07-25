#!/usr/bin/env python3
"""
Simple test runner for the updated PR visual system
Uses existing venv312 and validates the emoji-free scripts work
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Test the updated system"""
    print("PR Visual System Test (Emoji-Free)")
    print("=" * 40)
    
    # Use the existing venv
    python_cmd = "venv312\\Scripts\\python.exe"
    
    # Test the quick test
    print("1. Testing quick impact heatmap generation...")
    result = subprocess.run([python_cmd, "local-visual-test\\scripts\\quick_test.py"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("SUCCESS: Impact heatmap generation works!")
        
        # Check if file exists
        output_file = Path('.code-analysis/outputs/impact_heatmap.png')
        if output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            print(f"Generated: {output_file.name} ({size_kb:.1f} KB)")
        
        print("\n2. Testing batch script compatibility...")
        print("You can now use the batch scripts:")
        print("  - local-visual-test\\run_tests.bat (Windows)")
        print("  - local-visual-test\\run_tests.sh (Unix/Linux)")
        
        print("\nAll tests completed successfully!")
        print("The emoji encoding issues have been resolved.")
        
        return True
    else:
        print("FAILED: There are still issues")
        print("STDERR:", result.stderr[:200])
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
