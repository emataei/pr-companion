#!/usr/bin/env python3
"""
Generate Dependency Graphs for Enhanced PR Visuals
Reuses existing dependency graph functionality with enhanced features
"""

import os
import json
import subprocess
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def load_project_structure():
    """Load project structure from detection results"""
    try:
        with open('.code-analysis/outputs/project_structure.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to environment variables
        return {
            'project_dir': os.environ.get('PROJECT_DIR', '.'),
            'source_dirs': os.environ.get('SOURCE_DIRS', '').split(),
            'project_type': os.environ.get('PROJECT_TYPE', 'generic')
        }


def run_command(cmd, cwd=None):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=120)
        if result.returncode != 0:
            print(f"Warning: Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {cmd}")
        return None
    except Exception as e:
        print(f"Error running command {cmd}: {e}")
        return None


def find_analyzable_paths(project_dir, source_dirs):
    """Find the best paths to analyze for dependencies"""
    paths_to_analyze = []
    
    for src_dir in source_dirs:
        src_path = Path(src_dir)
        if src_path.exists() and src_path.is_dir():
            # Check if directory has JS/TS files
            js_files = list(src_path.glob('**/*.js')) + list(src_path.glob('**/*.ts')) + \
                      list(src_path.glob('**/*.jsx')) + list(src_path.glob('**/*.tsx'))
            if js_files:
                paths_to_analyze.append(str(src_path))
                print(f"Found {len(js_files)} JS/TS files in {src_path}")
    
    # If no source dirs found, analyze project directory
    if not paths_to_analyze:
        project_path = Path(project_dir)
        if project_path.exists():
            js_files = list(project_path.glob('*.js')) + list(project_path.glob('*.ts')) + \
                      list(project_path.glob('*.jsx')) + list(project_path.glob('*.tsx'))
            if js_files:
                paths_to_analyze.append(str(project_path))
                print(f"Found {len(js_files)} JS/TS files in project root")
    
    return paths_to_analyze


def create_placeholder_graph(output_file, message, graph_type="Dependency Analysis"):
    """Create a simple placeholder graph when analysis fails"""
    try:
        _, ax = plt.subplots(1, 1, figsize=(10, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
        # Create a simple diagram
        rect = patches.Rectangle((1, 3), 8, 4, linewidth=2, edgecolor='#cccccc', facecolor='#f8f9fa')
        ax.add_patch(rect)
        
        # Add icon-like elements
        circle = patches.Circle((2.5, 5.5), 0.3, facecolor='#e9ecef', edgecolor='#6c757d')
        ax.add_patch(circle)
        
        circle2 = patches.Circle((7.5, 5.5), 0.3, facecolor='#e9ecef', edgecolor='#6c757d')
        ax.add_patch(circle2)
        
        # Add connecting line
        ax.plot([3, 7], [5.5, 5.5], color='#6c757d', linestyle='--', alpha=0.5)
        
        ax.text(5, 6.5, message, ha='center', va='center', fontsize=12, 
                fontweight='bold', wrap=True, color='#495057')
        ax.text(5, 4.5, 'No dependency analysis available', ha='center', va='center', 
                fontsize=10, style='italic', color='#6c757d')
        ax.text(5, 3.8, 'This may be normal for non-JS/TS projects', ha='center', va='center', 
                fontsize=8, color='#6c757d')
        
        ax.set_title(f'{graph_type} - {message}', fontsize=14, fontweight='bold', pad=20)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"Created placeholder graph: {output_file}")
        return True
    except Exception as e:
        print(f"Failed to create placeholder: {e}")
        return False


def generate_dependency_graph(branch_name, output_file, project_structure, changed_files=None):
    """Generate dependency graph for a specific branch, optionally focusing on changed files"""
    print(f"Generating dependency graph for {branch_name}...")
    
    project_dir = project_structure['project_dir']
    source_dirs = project_structure['source_dirs']
    
    # If we have changed files, focus analysis on those
    if changed_files:
        print(f"Focusing on changed files: {changed_files}")
        # Try to analyze the directories containing changed files
        changed_dirs = set()
        for file in changed_files:
            dir_path = os.path.dirname(file)
            if dir_path:
                changed_dirs.add(dir_path)
        analyze_paths = list(changed_dirs) if changed_dirs else find_analyzable_paths(project_dir, source_dirs)
    else:
        # Find paths to analyze
        analyze_paths = find_analyzable_paths(project_dir, source_dirs)
    
    if not analyze_paths:
        print("No analyzable JavaScript/TypeScript files found")
        create_placeholder_graph(output_file, f"No JS/TS files found in {branch_name}")
        return False
    
    # Try each path until one works
    for analyze_path in analyze_paths:
        print(f"Analyzing path: {analyze_path}")
        
        # Generate both PNG and SVG versions
        png_file = output_file
        svg_file = output_file.replace('.png', '.svg')
        
        # Generate graph with different madge options
        commands_to_try = [
            f"madge --image {png_file} --layout dot {analyze_path}",
            f"madge --image {svg_file} --layout dot {analyze_path}",
            f"madge --image {png_file} --layout circo {analyze_path}",
            f"madge --image {svg_file} --layout circo {analyze_path}",
            f"madge --image {png_file} {analyze_path}",
            f"madge --image {svg_file} {analyze_path}",
            f"madge --image {png_file} --exclude 'node_modules|\.git|dist|build' {analyze_path}",
            f"madge --image {svg_file} --exclude 'node_modules|\.git|dist|build' {analyze_path}"
        ]
        
        png_generated = False
        svg_generated = False
        
        for cmd in commands_to_try:
            print(f"Trying: {cmd}")
            run_command(cmd)
            
            if png_file in cmd and Path(png_file).exists():
                print(f"PNG graph generated: {png_file}")
                png_generated = True
            elif svg_file in cmd and Path(svg_file).exists():
                print(f"SVG graph generated: {svg_file}")
                svg_generated = True
        
        if png_generated or svg_generated:
            return True
        
        print(f"Failed to generate graph for {analyze_path}")
    
    # Create placeholder if all attempts failed
    create_placeholder_graph(output_file, f"Analysis failed for {branch_name}")
    return False


def get_changed_files():
    """Get list of changed files in the PR"""
    try:
        # Get changed files between base and HEAD
        base_ref = os.environ.get('GITHUB_BASE_REF', 'main')
        changed_files = run_command(f"git diff --name-only origin/{base_ref}...HEAD")
        if changed_files:
            files = [f.strip() for f in changed_files.split('\n') if f.strip()]
            # Filter for JS/TS files
            js_ts_files = [f for f in files if f.endswith(('.js', '.ts', '.jsx', '.tsx'))]
            return js_ts_files
        return []
    except Exception as e:
        print(f"Error getting changed files: {e}")
        return []


def main():
    """Main dependency graph generation logic - Only generate PR branch graph"""
    print("Starting PR dependency graph generation...")
    
    # Load project structure
    project_structure = load_project_structure()
    print(f"Project: {project_structure['project_type']} at {project_structure['project_dir']}")
    print(f"Sources: {project_structure['source_dirs']}")
    
    # Get changed files
    changed_files = get_changed_files()
    print(f"Changed JS/TS files: {changed_files}")
    
    # Get environment variables
    head_ref = os.environ.get('GITHUB_HEAD_REF', 'HEAD')
    
    # Ensure output directory exists
    os.makedirs('.code-analysis/outputs', exist_ok=True)
    
    # Only generate graph for PR branch (current changes)
    print("Generating dependency graph for PR changes...")
    pr_success = generate_dependency_graph(
        head_ref, 
        ".code-analysis/outputs/dependency_graph_pr.png", 
        project_structure,
        changed_files
    )
    
    # Save results
    results = {
        'pr_graph_generated': pr_success,
        'changed_files': changed_files,
        'project_structure': project_structure,
        'analysis_timestamp': run_command("date -u +%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open('.code-analysis/outputs/dependency_graphs_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("PR dependency graph generation complete!")
    return pr_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
