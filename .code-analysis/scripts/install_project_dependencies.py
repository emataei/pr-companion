#!/usr/bin/env python3
"""
Install Project Dependencies for Enhanced PR Visuals
Handles npm install based on detected project structure
"""

import os
import subprocess
import sys


def run_command(cmd, cwd=None):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=300)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def install_project_dependencies():
    """Install project dependencies if package.json exists"""
    project_dir = os.environ.get('PROJECT_DIR', '.')
    has_package_json = os.environ.get('HAS_PACKAGE_JSON', 'false').lower() == 'true'
    
    if not has_package_json:
        print("No package.json found, skipping npm install")
        return True
    
    print(f"Installing project dependencies in {project_dir}...")
    
    # Try different npm install strategies
    install_commands = [
        "npm install --ignore-scripts --no-audit --no-fund",
        "npm ci --ignore-scripts --no-audit --no-fund",
        "npm install --only=production --ignore-scripts"
    ]
    
    for cmd in install_commands:
        print(f"Trying: {cmd}")
        success, _, stderr = run_command(cmd, cwd=project_dir)
        
        if success:
            print("Dependencies installed successfully")
            return True
        else:
            print(f"Failed: {stderr}")
    
    print("Could not install dependencies, continuing without them")
    return False


def main():
    """Main installation logic"""
    success = install_project_dependencies()
    
    if not success:
        print("Warning: Could not install project dependencies")
        print("Dependency analysis may be limited")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
