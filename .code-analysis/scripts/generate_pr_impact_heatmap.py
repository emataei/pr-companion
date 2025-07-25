#!/usr/bin/env python3
"""
Generate Optimized PR Impact Heatmap
Consolidated, clean visualization focused on key insights
Includes base64 encoding for easy PR comment embedding
"""

import json
import os
import sys
import base64
from pathlib import Path
from io import BytesIO

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def load_diff_stats():
    """Load and parse git diff statistics"""
    # Try multiple possible locations for diff_stats.txt
    possible_paths = [
        Path('../outputs/diff_stats.txt'),  # When run from scripts directory
        Path('.code-analysis/outputs/diff_stats.txt'),  # When run from project root
        Path('outputs/diff_stats.txt'),  # When run from .code-analysis directory
    ]
    
    diff_file = None
    for path in possible_paths:
        if path.exists():
            diff_file = path
            break
    
    if not diff_file:
        print(f"No diff stats file found. Searched:")
        for path in possible_paths:
            print(f"  - {path.absolute()}")
        return []
    
    file_changes = []
    with open(diff_file, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                try:
                    added = int(parts[0]) if parts[0] != '-' else 0
                    deleted = int(parts[1]) if parts[1] != '-' else 0
                    file_path = parts[2]
                    
                    if added > 0 or deleted > 0:
                        file_changes.append({
                            'file': file_path,
                            'added': added,
                            'deleted': deleted,
                            'total': added + deleted,
                            'file_type': get_file_type(file_path),
                            'directory': get_directory(file_path)
                        })
                except ValueError:
                    continue
    
    return file_changes


def get_file_type(file_path):
    """Get simplified file type for grouping"""
    ext = Path(file_path).suffix.lower()
    type_map = {
        '.js': 'JavaScript',
        '.ts': 'TypeScript', 
        '.tsx': 'React',
        '.jsx': 'React',
        '.py': 'Python',
        '.md': 'Docs',
        '.json': 'Config',
        '.yml': 'Config',
        '.yaml': 'Config'
    }
    return type_map.get(ext, 'Other')


def get_directory(file_path):
    """Get top-level directory for grouping"""
    parts = Path(file_path).parts
    if len(parts) > 1:
        return parts[0]
    return 'root'


def save_image_with_base64(output_file, plt_figure=None, dpi=100):
    """Save image to file and generate base64 encoded version for PR embedding"""
    
    if plt_figure:
        # First save to check raw file size
        temp_buffer = BytesIO()
        plt_figure.savefig(
            temp_buffer,
            format='png',
            dpi=dpi,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        temp_buffer.seek(0)
        raw_size = len(temp_buffer.getvalue())
        temp_buffer.close()
        
        # If too large, reduce DPI and try again
        max_raw_size = 45 * 1024  # 45KB raw = ~60KB base64 (under 64KB GitHub limit)
        if raw_size > max_raw_size:
            print(f"Image too large ({raw_size/1024:.1f}KB), reducing DPI from {dpi} to 60")
            dpi = 60
            
            # Try again with lower DPI
            temp_buffer = BytesIO()
            plt_figure.savefig(
                temp_buffer,
                format='png',
                dpi=dpi,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )
            temp_buffer.seek(0)
            raw_size = len(temp_buffer.getvalue())
            temp_buffer.close()
            
            # If still too large, reduce further
            if raw_size > max_raw_size:
                print(f"Still too large ({raw_size/1024:.1f}KB), reducing DPI to 40")
                dpi = 40
        
        # Save to file with final DPI
        plt_figure.savefig(
            output_file, 
            dpi=dpi,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        
        # Generate base64 version with same settings
        buffer = BytesIO()
        plt_figure.savefig(
            buffer,
            format='png',
            dpi=dpi,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        buffer.seek(0)
        
        # Encode to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        base64_with_prefix = f"data:image/png;base64,{image_base64}"
        
        # Check final size
        final_size = len(base64_with_prefix)
        github_limit = 64 * 1024  # 64KB
        
        if final_size > github_limit:
            print(f"Warning: Base64 size ({final_size/1024:.1f}KB) exceeds GitHub limit ({github_limit/1024}KB)")
            # Create a placeholder instead
            placeholder_content = "Image too large for GitHub comment display. Available in workflow artifacts."
            base64_file = str(output_file).replace('.png', '_base64.txt')
            with open(base64_file, 'w') as f:
                f.write(placeholder_content)
            
            markdown_file = str(output_file).replace('.png', '_embed.md')
            with open(markdown_file, 'w') as f:
                f.write(f"{placeholder_content}\n")
            
            buffer.close()
            plt.close()
            return 0
        
        # Save base64 version for easy PR embedding
        base64_file = str(output_file).replace('.png', '_base64.txt')
        with open(base64_file, 'w') as f:
            f.write(base64_with_prefix)
        
        # Also save markdown-ready version
        markdown_file = str(output_file).replace('.png', '_embed.md')
        with open(markdown_file, 'w') as f:
            f.write(f"![PR Impact Heatmap](data:image/png;base64,{image_base64})\n")
        
        buffer.close()
        plt.close()
        
        print(f"Generated base64 image: {final_size/1024:.1f}KB (DPI: {dpi})")
        return len(image_base64)
    
    return 0


def get_output_file_path():
    """Get the correct output file path based on current working directory"""
    possible_paths = [
        Path('../outputs/pr_impact_heatmap.png'),  # When run from scripts directory
        Path('.code-analysis/outputs/pr_impact_heatmap.png'),  # When run from project root
        Path('outputs/pr_impact_heatmap.png'),  # When run from .code-analysis directory
    ]
    
    # Use the first path whose parent directory exists or can be created
    for path in possible_paths:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            return str(path)
        except OSError:
            continue
    
    # Fallback
    return '../outputs/pr_impact_heatmap.png'


def generate_optimized_heatmap():
    """Generate clean, focused impact heatmap"""
    if not MATPLOTLIB_AVAILABLE:
        return create_placeholder()
    
    file_changes = load_diff_stats()
    if not file_changes:
        return create_no_changes_visual()
    
    # Focus on top impactful files only (reduce noise)
    df = pd.DataFrame(file_changes)
    
    # Limit to top 15 most changed files to keep it clean
    top_files = df.nlargest(15, 'total')
    
    if len(top_files) == 0:
        return create_no_changes_visual()
    
    # Create clean, minimal heatmap
    plt.style.use('default')
    _, ax = plt.subplots(figsize=(10, 6))  # Smaller size for better embedding
    
    # Prepare data for heatmap - group by file type and directory
    heatmap_data = top_files.pivot_table(
        values='total', 
        index='file_type', 
        columns='directory', 
        aggfunc='sum', 
        fill_value=0
    )
    
    # Use a clean color scheme
    sns.heatmap(
        heatmap_data, 
        annot=True, 
        fmt='d', 
        cmap='YlOrRd',  # Clean color palette
        cbar_kws={'label': 'Lines Changed'},
        ax=ax,
        square=False,
        linewidths=0.5
    )
    
    ax.set_title('PR Impact by File Type & Directory', fontsize=14, pad=20)
    ax.set_xlabel('Directory', fontsize=12)
    ax.set_ylabel('File Type', fontsize=12)
    
    # Optimize for size
    plt.tight_layout()
    
    # Save with base64 encoding for PR embedding
    output_file = get_output_file_path()
    base64_length = save_image_with_base64(output_file, plt.gcf(), dpi=100)
    
    # Check file size
    file_size = Path(output_file).stat().st_size
    print(f"Generated optimized heatmap: {file_size / 1024:.1f} KB")
    print(f"Base64 encoded: {base64_length:,} characters")
    print(f"Files created:")
    print(f"  - {output_file}")
    print(f"  - {output_file.replace('.png', '_base64.txt')}")
    print(f"  - {output_file.replace('.png', '_embed.md')}")
    
    if file_size > 100 * 1024:  # If still > 100KB, create simplified version
        return create_simplified_heatmap(top_files)
    
    return True


def create_simplified_heatmap(df):
    """Create ultra-simplified version if file is still too large"""
    plt.style.use('default')
    _, ax = plt.subplots(figsize=(8, 4))  # Even smaller
    
    # Just show top 10 files as horizontal bar chart
    top_10 = df.nlargest(10, 'total')
    
    colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(top_10)))
    bars = ax.barh(range(len(top_10)), top_10['total'], color=colors)
    
    # Clean labels
    ax.set_yticks(range(len(top_10)))
    ax.set_yticklabels([Path(f).name for f in top_10['file']], fontsize=10)
    ax.set_xlabel('Lines Changed', fontsize=12)
    ax.set_title('Top 10 Changed Files', fontsize=14, pad=15)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                f'{int(width)}', ha='left', va='center', fontsize=9)
    
    plt.tight_layout()
    
    output_file = get_output_file_path()
    base64_length = save_image_with_base64(output_file, plt.gcf(), dpi=80)
    
    file_size = Path(output_file).stat().st_size
    print(f"Generated simplified heatmap: {file_size / 1024:.1f} KB")
    print(f"Base64 encoded: {base64_length:,} characters")
    return True


def create_no_changes_visual():
    """Create minimal visual for no changes"""
    output_file = get_output_file_path()
    
    _, ax = plt.subplots(figsize=(6, 3))
    ax.text(0.5, 0.5, 'No Significant Changes', 
            ha='center', va='center', fontsize=16, 
            transform=ax.transAxes)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    
    base64_length = save_image_with_base64(output_file, plt.gcf(), dpi=80)
    
    print("Created no-changes heatmap")
    print(f"Base64 encoded: {base64_length:,} characters")
    return True


def create_placeholder():
    """Create text placeholder when matplotlib unavailable"""
    output_file = '.code-analysis/outputs/pr_impact_heatmap_placeholder.md'
    
    with open(output_file, 'w') as f:
        f.write("# PR Impact Analysis\n\n")
        f.write("Visual heatmap generation requires matplotlib.\n\n")
        f.write("Install with: `pip install matplotlib seaborn pandas numpy`\n")
    
    print("Created heatmap placeholder")
    return False


def main():
    """Main execution function"""
    print("Generating optimized PR impact heatmap...")
    
    # Ensure output directory exists (try multiple possible locations)
    possible_dirs = [
        Path('../outputs'),
        Path('.code-analysis/outputs'),
        Path('outputs')
    ]
    
    for dir_path in possible_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            break
        except:
            continue
    
    try:
        success = generate_optimized_heatmap()
        if success:
            print("Optimized heatmap generation complete!")
        return success
    except Exception as e:
        print(f"Error generating heatmap: {e}")
        return create_placeholder()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
