#!/usr/bin/env python3
"""
Generate Optimized PR Story Arc
Simple, clean visual summary for reviewers
"""

import os
import sys
import json
import base64
from io import BytesIO
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def save_image_with_base64(fig, base_filename, title="PR Summary"):
    """Save image as PNG and create base64 + markdown files"""
    # Use standardized output directory
    output_dir = Path(__file__).parent.parent / 'outputs'  # .code-analysis/outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save PNG file with size optimization
    png_path = output_dir / f"{base_filename}.png"
    
    # First save to check raw file size
    temp_buffer = BytesIO()
    fig.savefig(
        temp_buffer,
        format='png',
        dpi=80,
        bbox_inches='tight',
        facecolor='white'
    )
    temp_buffer.seek(0)
    raw_size = len(temp_buffer.getvalue())
    temp_buffer.close()
    
    dpi = 80
    # If too large, reduce DPI and try again
    max_raw_size = 45 * 1024  # 45KB raw = ~60KB base64 (under 64KB GitHub limit)
    if raw_size > max_raw_size:
        print(f"Image too large ({raw_size/1024:.1f}KB), reducing DPI from {dpi} to 60")
        dpi = 60
        
        # Try again with lower DPI
        temp_buffer = BytesIO()
        fig.savefig(
            temp_buffer,
            format='png',
            dpi=dpi,
            bbox_inches='tight',
            facecolor='white'
        )
        temp_buffer.seek(0)
        raw_size = len(temp_buffer.getvalue())
        temp_buffer.close()
        
        # If still too large, reduce further
        if raw_size > max_raw_size:
            print(f"Still too large ({raw_size/1024:.1f}KB), reducing DPI to 40")
            dpi = 40
    
    # Save PNG file with optimized DPI
    fig.savefig(png_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    
    # Get file size
    size_kb = png_path.stat().st_size / 1024
    
    # Create base64 version
    with open(png_path, "rb") as img_file:
        img_data = img_file.read()
        base64_data = base64.b64encode(img_data).decode('utf-8')
        data_uri = f"data:image/png;base64,{base64_data}"
    
    # Check final base64 size
    final_size = len(data_uri)
    github_limit = 64 * 1024  # 64KB
    
    if final_size > github_limit:
        print(f"Warning: Base64 size ({final_size/1024:.1f}KB) exceeds GitHub limit ({github_limit/1024}KB)")
        # Create a placeholder instead
        placeholder_content = "Image too large for GitHub comment display. Available in workflow artifacts."
        base64_path = output_dir / f"{base_filename}_base64.txt"
        with open(base64_path, 'w') as f:
            f.write(placeholder_content)
        
        markdown_path = output_dir / f"{base_filename}_embed.md"
        with open(markdown_path, 'w') as f:
            f.write(f"{placeholder_content}\n")
        
        return png_path, base64_path, markdown_path
    
    # Save base64 text file
    base64_path = output_dir / f"{base_filename}_base64.txt"
    with open(base64_path, 'w') as f:
        f.write(data_uri)
    
    # Create markdown embedding file
    markdown_path = output_dir / f"{base_filename}_embed.md"
    with open(markdown_path, 'w') as f:
        f.write(f"![{title}]({data_uri})\n")
    
    print(f"Generated optimized {base_filename}: {size_kb:.1f} KB (DPI: {dpi})")
    print(f"Base64 encoded: {len(base64_data):,} characters")
    
    return png_path, base64_path, markdown_path


def load_pr_summary():
    """Load basic PR summary data"""
    # Try to get data from diff stats
    diff_file = Path(__file__).parent.parent / 'outputs' / 'diff_stats.txt'
    if Path(diff_file).exists():
        with open(diff_file, 'r') as f:
            lines = f.readlines()
            
        file_count = len([line for line in lines if line.strip()])
        total_changes = 0
        
        for line in lines:
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                try:
                    added = int(parts[0]) if parts[0] != '-' else 0
                    deleted = int(parts[1]) if parts[1] != '-' else 0
                    total_changes += added + deleted
                except ValueError:
                    continue
        
        return {
            'files_changed': file_count,
            'total_changes': total_changes,
            'has_data': file_count > 0
        }
    
    return {'files_changed': 0, 'total_changes': 0, 'has_data': False}


def generate_simple_summary():
    """Generate a simple, clean PR summary visual"""
    if not MATPLOTLIB_AVAILABLE:
        return create_placeholder()
    
    summary = load_pr_summary()
    
    if not summary['has_data']:
        return create_no_data_summary()
    
    # Create simple summary chart
    fig, ax = plt.subplots(figsize=(8, 3))  # Compact size
    
    # Simple metrics display
    metrics = [
        ('Files Changed', summary['files_changed']),
        ('Total Changes', summary['total_changes'])
    ]
    
    # Clean bar chart
    x_pos = [0, 1]
    values = [summary['files_changed'], min(summary['total_changes'], 1000)]  # Cap display
    colors = ['#3498db', '#e74c3c']
    
    bars = ax.bar(x_pos, values, color=colors, alpha=0.7, width=0.6)
    
    # Add value labels on bars
    for i, (bar, (label, value)) in enumerate(zip(bars, metrics)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.05,
                f'{value}', ha='center', va='bottom', fontweight='bold')
        ax.text(bar.get_x() + bar.get_width()/2., -height*0.1,
                label, ha='center', va='top', fontsize=10)
    
    # Clean up plot
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(0, max(values) * 1.2 if values else 1)
    ax.set_title('PR Summary', fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')  # Remove axes for cleaner look
    
    plt.tight_layout()
    
    # Save with base64 encoding for PR embedding
    save_image_with_base64(fig, 'story_arc', 'PR Summary')
    plt.close()
    
    return True


def create_no_data_summary():
    """Create minimal summary when no data available"""
    fig, ax = plt.subplots(figsize=(6, 2))
    
    ax.text(0.5, 0.5, 'No Changes to Summarize', 
           ha='center', va='center', fontsize=14)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save with base64 encoding for PR embedding
    save_image_with_base64(fig, 'story_arc', 'PR Summary')
    plt.close()
    
    return True


def create_placeholder():
    """Create text placeholder when matplotlib unavailable"""
    output_file = Path(__file__).parent.parent / 'outputs' / 'story_arc_placeholder.md'
    
    with open(output_file, 'w') as f:
        f.write("# PR Story Arc\n\n")
        f.write("Visual summary generation requires matplotlib.\n\n")
        f.write("Install with: `pip install matplotlib numpy`\n")
    
    print("Created story arc placeholder")
    return False


def main():
    """Main execution function"""
    print("Generating optimized PR summary...")
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent.parent / 'outputs'  # .code-analysis/outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        success = generate_simple_summary()
        if success:
            print("Optimized PR summary generation complete!")
        return success
    except Exception as e:
        print(f"Error generating PR summary: {e}")
        return create_placeholder()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
