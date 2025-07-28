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


def create_placeholder_graph(output_file, message, graph_type="Dependency Analysis", file_info=None):
    """Create a simple placeholder graph when analysis fails"""
    try:
        _, ax = plt.subplots(1, 1, figsize=(12, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
        # Create a simple diagram
        rect = patches.Rectangle((1, 2), 8, 6, linewidth=2, edgecolor='#cccccc', facecolor='#f8f9fa')
        ax.add_patch(rect)
        
        # Add icon-like elements for files
        for i, x_pos in enumerate([2.5, 4.5, 6.5, 7.5]):
            if i < 4:  # Show up to 4 file icons
                file_rect = patches.Rectangle((x_pos-0.2, 5.5), 0.4, 0.8, 
                                            linewidth=1, edgecolor='#6c757d', facecolor='#e9ecef')
                ax.add_patch(file_rect)
        
        # Add main message
        ax.text(5, 7, message, ha='center', va='center', fontsize=12, 
                fontweight='bold', wrap=True, color='#495057')
        
        # Add file info if provided
        if file_info:
            ax.text(5, 6, file_info, ha='center', va='center', fontsize=10, 
                    style='italic', color='#6c757d', wrap=True)
        else:
            ax.text(5, 6, 'No dependency analysis available', ha='center', va='center', 
                    fontsize=10, style='italic', color='#6c757d')
        
        # Add helpful message
        ax.text(5, 4.5, 'Dependencies will show here when available', ha='center', va='center', 
                fontsize=9, color='#6c757d')
        ax.text(5, 3.8, 'This may be normal for simple projects', ha='center', va='center', 
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


def create_manual_dependency_graph(analyze_paths, output_file, branch_name):
    """Create a manual dependency graph by analyzing import statements"""
    try:
        import networkx as nx
        print("Creating manual dependency graph using file analysis...")
        
        # Collect all files and their imports
        file_imports = {}
        all_files = []
        
        for analyze_path in analyze_paths:
            path_obj = Path(analyze_path)
            js_ts_files = list(path_obj.glob('**/*.js')) + list(path_obj.glob('**/*.ts')) + \
                         list(path_obj.glob('**/*.jsx')) + list(path_obj.glob('**/*.tsx'))
            
            for file_path in js_ts_files:
                # Skip very large files or node_modules
                if 'node_modules' in str(file_path) or file_path.stat().st_size > 100000:
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract import statements (simple regex)
                    import re
                    imports = re.findall(r'import.*from\s+[\'"]([^\'\"]+)[\'"]', content)
                    imports += re.findall(r'require\([\'"]([^\'\"]+)[\'"]\)', content)
                    
                    file_name = file_path.name
                    file_imports[file_name] = imports
                    all_files.append(file_name)
                    
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue
        
        if not file_imports:
            return False
            
        # Create NetworkX graph
        G = nx.DiGraph()
        
        # Add nodes
        for file_name in all_files[:20]:  # Limit to prevent overcrowding
            G.add_node(file_name)
        
        # Add edges based on imports
        for file_name, imports in file_imports.items():
            if file_name in G.nodes():
                for imp in imports:
                    # Try to match import to actual files
                    for target_file in all_files:
                        if imp in target_file or target_file.replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '') in imp:
                            if target_file in G.nodes():
                                G.add_edge(file_name, target_file)
        
        # Create matplotlib visualization
        plt.figure(figsize=(12, 8))
        
        if len(G.nodes()) > 0:
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                 node_size=1000, alpha=0.8)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                 arrows=True, arrowsize=20, alpha=0.6)
            
            # Draw labels
            labels = {node: node.replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '')[:10] 
                     for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8)
            
            plt.title(f'Dependency Graph - {branch_name}\n({len(all_files)} files analyzed)', 
                     fontsize=14, fontweight='bold')
        else:
            plt.text(0.5, 0.5, f'No Dependencies Found\n{len(all_files)} files analyzed', 
                    ha='center', va='center', transform=plt.gca().transAxes, fontsize=12)
            plt.title(f'Dependency Analysis - {branch_name}', fontsize=14, fontweight='bold')
        
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"Created manual dependency graph: {output_file}")
        return True
        
    except ImportError:
        print("NetworkX not available for manual dependency graph")
        return False
    except Exception as e:
        print(f"Error creating manual dependency graph: {e}")
        return False


def generate_dependency_graph(branch_name, output_file, project_structure, changed_files=None):
    """Generate dependency graph for a specific branch, optionally focusing on changed files"""
    print(f"Generating dependency graph for {branch_name}...")
    
    project_dir = project_structure['project_dir']
    source_dirs = project_structure['source_dirs']
    
    # For Next.js projects, prioritize src directory
    analyze_paths = []
    
    # If this is a Next.js project, look for specific patterns
    if project_structure.get('project_type') == 'next.js' or Path('next.config.js').exists():
        print("Detected Next.js project")
        
        # Check for src directory structure
        src_path = Path('sample-project/src') if Path('sample-project/src').exists() else Path('src')
        if src_path.exists():
            print(f"Found src directory: {src_path}")
            analyze_paths.append(str(src_path))
        
        # Also check for pages directory
        pages_path = Path('sample-project/pages') if Path('sample-project/pages').exists() else Path('pages')
        if pages_path.exists():
            print(f"Found pages directory: {pages_path}")
            analyze_paths.append(str(pages_path))
            
        # Check for app directory (App Router)
        app_path = Path('sample-project/src/app') if Path('sample-project/src/app').exists() else Path('src/app')
        if app_path.exists():
            print(f"Found app directory: {app_path}")
            analyze_paths.append(str(app_path))
    
    # If we have changed files, focus analysis on those directories
    if changed_files:
        print(f"Focusing on changed files: {changed_files}")
        changed_dirs = set()
        for file in changed_files:
            dir_path = os.path.dirname(file)
            if dir_path:
                changed_dirs.add(dir_path)
                # Also add parent directories for better context
                parent_dir = os.path.dirname(dir_path)
                if parent_dir:
                    changed_dirs.add(parent_dir)
        
        # Use changed directories if we found any JS/TS files
        if changed_dirs:
            changed_paths = [path for path in changed_dirs if Path(path).exists()]
            if changed_paths:
                analyze_paths.extend(changed_paths)
    
    # Fallback to standard paths if nothing found
    if not analyze_paths:
        analyze_paths = find_analyzable_paths(project_dir, source_dirs)
    
    # Remove duplicates and ensure paths exist
    analyze_paths = list({path for path in analyze_paths if Path(path).exists()})
    
    print(f"Paths to analyze: {analyze_paths}")
    
    if not analyze_paths:
        print("No analyzable paths found")
        create_placeholder_graph(output_file, f"No analyzable paths found in {branch_name}", 
                                file_info="Searched for JS/TS files but none found")
        return False
    
    # Check if madge is available
    madge_available = run_command("madge --version") is not None
    
    if madge_available:
        # Try madge first
        for analyze_path in analyze_paths:
            print(f"Analyzing path with madge: {analyze_path}")
            
            # Check what files are in this path
            path_obj = Path(analyze_path)
            js_ts_files = list(path_obj.glob('**/*.js')) + list(path_obj.glob('**/*.ts')) + \
                         list(path_obj.glob('**/*.jsx')) + list(path_obj.glob('**/*.tsx'))
            print(f"Found {len(js_ts_files)} JS/TS files in {analyze_path}")
            
            if len(js_ts_files) == 0:
                print(f"No JS/TS files in {analyze_path}, skipping")
                continue
                
            # Generate PNG version
            png_file = output_file
            
            # Try simpler commands first for better success rate
            commands_to_try = [
                f"madge {analyze_path} --image {png_file}",
                f"madge {analyze_path} --image {png_file} --extensions js,jsx,ts,tsx",
                f"madge {analyze_path} --image {png_file} --exclude node_modules",
                f"madge {analyze_path} --image {png_file} --layout dot",
                f"madge {analyze_path} --image {png_file} --layout circo --exclude node_modules",
            ]
            
            png_generated = False
            
            for cmd in commands_to_try:
                print(f"Trying: {cmd}")
                run_command(cmd)
                
                # Check if file was generated and has content
                if Path(png_file).exists():
                    file_size = Path(png_file).stat().st_size
                    print(f"PNG file exists, size: {file_size} bytes")
                    
                    if file_size > 1000:  # Reasonable size for a dependency graph
                        print(f"PNG graph generated successfully: {png_file}")
                        png_generated = True
                        break
                    else:
                        print(f"PNG file too small ({file_size} bytes), trying next command")
                        # Remove the small/empty file
                        Path(png_file).unlink()
            
            if png_generated:
                return True
            
            print(f"Failed to generate meaningful graph with madge for {analyze_path}")
    
    # Try manual dependency graph as fallback
    print("Trying manual dependency analysis...")
    if create_manual_dependency_graph(analyze_paths, output_file, branch_name):
        return True
    
    # Create placeholder if all attempts failed
    print("All attempts failed, creating placeholder")
    create_placeholder_graph(output_file, f"Unable to analyze dependencies in {branch_name}",
                            file_info=f"Found {sum(len(list(Path(p).glob('**/*.js'))) + len(list(Path(p).glob('**/*.ts'))) + len(list(Path(p).glob('**/*.jsx'))) + len(list(Path(p).glob('**/*.tsx'))) for p in analyze_paths)} JS/TS files but analysis failed")
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


def check_madge_installation():
    """Check if madge is installed and working"""
    result = run_command("madge --version")
    if result:
        print(f"Madge version: {result}")
        return True
    else:
        print("Madge is not installed or not working")
        return False


def main():
    """Main dependency graph generation logic - Only generate PR branch graph"""
    print("Starting PR dependency graph generation...")
    
    # Check if madge is available
    if not check_madge_installation():
        print("Warning: madge not available, will create placeholder graph")
    
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
