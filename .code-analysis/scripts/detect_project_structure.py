#!/usr/bin/env python3
"""
Project Structure Detection for Enhanced PR Visuals
Automatically detects project type, source directories, and configuration
"""

import os
import json
import subprocess
from pathlib import Path

# Constants
PACKAGE_JSON = 'package.json'
EXCLUDED_DIRS = ['node_modules', '.git', 'dist', 'build', '.next']
STANDARD_SOURCE_DIRS = ["src", "app", "components", "pages", "lib", "utils", "hooks", "services", "modules", "features"]


def find_package_json_files():
    """Find all package.json files in the repository"""
    try:
        result = subprocess.run(
            ['find', '.', '-name', PACKAGE_JSON, '-not', '-path', './node_modules/*', '-not', '-path', './.git/*'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fallback: manual search
    package_files = []
    for root, dirs, files in os.walk('.'):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        if PACKAGE_JSON in files:
            package_files.append(os.path.join(root, PACKAGE_JSON))
    
    return package_files


def detect_project_directory(package_files):
    """Determine the main project directory"""
    if not package_files:
        return "."
    
    # Prefer root-level package.json
    if f"./{PACKAGE_JSON}" in package_files:
        return "."
    
    # Check for common patterns
    common_patterns = [f"./src/{PACKAGE_JSON}", f"./app/{PACKAGE_JSON}", f"./client/{PACKAGE_JSON}"]
    for pattern in common_patterns:
        if pattern in package_files:
            return os.path.dirname(pattern)
    
    # Use the first package.json found
    return os.path.dirname(package_files[0])


def find_source_directories(project_dir):
    """Find source directories within the project"""
    source_dirs = []
    
    for dir_name in STANDARD_SOURCE_DIRS:
        # Check both in project dir and at root
        for base_path in [project_dir, "."]:
            dir_path = os.path.join(base_path, dir_name)
            if os.path.isdir(dir_path) and dir_path not in source_dirs:
                source_dirs.append(dir_path)
    
    # If no standard directories found, look for JS/TS files
    if not source_dirs:
        source_dirs = _find_dirs_with_js_ts_files(project_dir)
    
    # Fallback to project directory
    if not source_dirs:
        source_dirs = [project_dir]
    
    return source_dirs


def _find_dirs_with_js_ts_files(project_dir):
    """Find directories containing JS/TS files"""
    js_ts_extensions = ('.js', '.ts', '.jsx', '.tsx')
    source_dirs = []
    
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        js_ts_files = [f for f in files if f.endswith(js_ts_extensions)]
        if js_ts_files and root not in source_dirs:
            source_dirs.append(root)
            break
    
    return source_dirs


def _check_config_files(project_dir):
    """Check for framework-specific configuration files"""
    config_checks = {
        'nextjs': ['next.config.js', 'next.config.ts', 'next.config.mjs'],
        'vite': ['vite.config.js', 'vite.config.ts'],
        'angular': ['angular.json'],
        'vue': ['vue.config.js']
    }
    
    for project_type, config_files in config_checks.items():
        for config_file in config_files:
            if os.path.exists(os.path.join(project_dir, config_file)):
                return project_type
    
    return None


def _check_package_dependencies(project_dir):
    """Check package.json dependencies for framework detection"""
    package_json_path = os.path.join(project_dir, PACKAGE_JSON)
    if not os.path.exists(package_json_path):
        return None
    
    try:
        with open(package_json_path, 'r') as f:
            package_data = json.loads(f.read())
            
        all_deps = {}
        all_deps.update(package_data.get('dependencies', {}))
        all_deps.update(package_data.get('devDependencies', {}))
        
        # Check for framework dependencies in order of specificity
        framework_deps = [
            ('nextjs', 'next'),
            ('vue', 'vue'),
            ('vue', '@vue/cli'),
            ('angular', '@angular/core'),
            ('vite', 'vite'),
            ('react', 'react'),
            ('svelte', 'svelte')
        ]
        
        for framework, dep in framework_deps:
            if dep in all_deps:
                return framework
                
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    
    return None


def detect_project_type(project_dir):
    """Detect the project type based on configuration files and dependencies"""
    
    # First check config files (more reliable)
    project_type = _check_config_files(project_dir)
    if project_type:
        return project_type
    
    # Then check package.json dependencies
    project_type = _check_package_dependencies(project_dir)
    if project_type:
        return project_type
    
    return 'generic'


def main():
    """Main detection logic"""
    print("Auto-detecting project structure...")
    
    # Find package.json files
    package_files = find_package_json_files()
    print(f"Found {PACKAGE_JSON} files: {package_files}")
    
    # Detect project directory
    project_dir = detect_project_directory(package_files)
    print(f"Project directory: {project_dir}")
    
    # Find source directories
    source_dirs = find_source_directories(project_dir)
    print(f"Source directories: {source_dirs}")
    
    # Detect project type
    project_type = detect_project_type(project_dir)
    print(f"Detected project type: {project_type}")
    
    # Check if package.json exists
    has_package_json = os.path.exists(os.path.join(project_dir, PACKAGE_JSON))
    
    # Set GitHub Actions outputs
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"project_dir={project_dir}\n")
            f.write(f"source_dirs={' '.join(source_dirs)}\n")
            f.write(f"project_type={project_type}\n")
            f.write(f"has_package_json={str(has_package_json).lower()}\n")
    
    # Also save to JSON for other scripts
    os.makedirs('.code-analysis/outputs', exist_ok=True)
    detection_results = {
        'project_dir': project_dir,
        'source_dirs': source_dirs,
        'project_type': project_type,
        'has_package_json': has_package_json,
        'package_files': package_files
    }
    
    with open('.code-analysis/outputs/project_structure.json', 'w') as f:
        json.dump(detection_results, f, indent=2)
    
    print("Project structure detection complete!")


if __name__ == "__main__":
    main()
