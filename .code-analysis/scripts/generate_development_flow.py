#!/usr/bin/env python3
"""
Generate PR Impact Grid Visualization
Focused visual showing risk score, file changes, and actionable insights
"""

import json
import os
import sys
import base64
from io import BytesIO
from pathlib import Path
import subprocess
from datetime import datetime
import re

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import numpy as np
    from matplotlib.gridspec import GridSpec
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Constants
OUTPUT_DIR_RELATIVE = '.code-analysis/outputs'
OUTPUT_DIR_PARENT = '../.code-analysis/outputs'
OUTPUT_DIR_GRANDPARENT = '../../.code-analysis/outputs'


def save_image_with_base64(fig, base_filename, title="Development Flow"):
    """Save image as PNG and create base64 + markdown files"""
    # Find the output directory dynamically
    output_dir = None
    for check_dir in [OUTPUT_DIR_RELATIVE, OUTPUT_DIR_PARENT, OUTPUT_DIR_GRANDPARENT]:
        if Path(check_dir).exists() or Path(check_dir).parent.exists():
            output_dir = Path(check_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            break
    
    if not output_dir:
        output_dir = Path(OUTPUT_DIR_RELATIVE)
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


def calculate_risk_score():
    """Calculate overall PR risk score based on multiple factors"""
    try:
        # Get diff stats
        diff_stats = load_diff_stats()
        if not diff_stats:
            return 1, "Low", "#2ECC71"  # Green for no changes
        
        # Calculate base risk factors
        total_files = len(diff_stats)
        total_lines = sum(f['total'] for f in diff_stats)
        
        # File type risk weights
        high_risk_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.cs'}
        # Remove unused medium_risk_extensions variable
        
        risk_score = 0
        
        # File count factor (0-3 points)
        if total_files > 10:
            risk_score += 3
        elif total_files > 5:
            risk_score += 2
        elif total_files > 2:
            risk_score += 1
        
        # Lines changed factor (0-3 points)
        if total_lines > 500:
            risk_score += 3
        elif total_lines > 200:
            risk_score += 2
        elif total_lines > 50:
            risk_score += 1
        
        # File type risk factor (0-2 points)
        high_risk_files = sum(1 for f in diff_stats 
                             if any(f['file'].endswith(ext) for ext in high_risk_extensions))
        if high_risk_files > 5:
            risk_score += 2
        elif high_risk_files > 2:
            risk_score += 1
        
        # Deletion ratio factor (0-2 points) - high deletions = higher risk
        total_deletions = sum(f.get('deletions', 0) for f in diff_stats)
        if total_lines > 0:
            deletion_ratio = total_deletions / total_lines
            if deletion_ratio > 0.4:
                risk_score += 2
            elif deletion_ratio > 0.2:
                risk_score += 1
        
        # Convert to 1-10 scale and categorize
        risk_score = min(10, max(1, risk_score))
        
        if risk_score >= 7:
            return risk_score, "High", "#E74C3C"  # Red
        elif risk_score >= 4:
            return risk_score, "Medium", "#F39C12"  # Orange
        else:
            return risk_score, "Low", "#2ECC71"  # Green
            
    except Exception as e:
        print(f"Error calculating risk score: {e}")
        return 3, "Medium", "#F39C12"


def estimate_review_time():
    """Estimate review time based on change complexity"""
    try:
        diff_stats = load_diff_stats()
        if not diff_stats:
            return "5 min", "#2ECC71"
        
        total_files = len(diff_stats)
        total_lines = sum(f['total'] for f in diff_stats)
        
        # Base time calculation
        minutes = 5  # Base review time
        
        # Add time per file (2 min per file)
        minutes += total_files * 2
        
        # Add time per 50 lines (5 min per 50 lines)
        minutes += (total_lines // 50) * 5
        
        # Complexity multipliers for certain file types
        complex_files = sum(1 for f in diff_stats 
                           if any(f['file'].endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx']))
        if complex_files > 3:
            minutes = int(minutes * 1.5)
        
        # Format time estimate
        if minutes < 60:
            time_str = f"{minutes} min"
            color = "#2ECC71" if minutes < 30 else "#F39C12"
        else:
            hours = minutes // 60
            remaining_mins = minutes % 60
            if remaining_mins > 0:
                time_str = f"{hours}h {remaining_mins}m"
            else:
                time_str = f"{hours}h"
            color = "#E74C3C" if hours > 2 else "#F39C12"
        
        return time_str, color
        
    except Exception as e:
        print(f"Error estimating review time: {e}")
        return "15 min", "#F39C12"


def analyze_change_intent():
    """Analyze git commits to determine actual development intent"""
    try:
        # Get recent commit messages
        cmd = ["git", "log", "--oneline", "--format=%s", "-10"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return ["Code changes", "General updates", "Maintenance"]
        
        messages = result.stdout.strip().split('\n')
        
        # Intent patterns with more specific, actionable descriptions
        intent_patterns = {
            'simplify': {
                'keywords': ['simplify', 'clean', 'refactor', 'reduce', 'streamline'],
                'intent': 'Simplifying codebase'
            },
            'secure': {
                'keywords': ['security', 'auth', 'login', 'validate', 'sanitize', 'escape'],
                'intent': 'Enhancing security'
            },
            'performance': {
                'keywords': ['optimize', 'performance', 'speed', 'cache', 'efficient'],
                'intent': 'Improving performance'
            },
            'error_handling': {
                'keywords': ['error', 'exception', 'handle', 'catch', 'try'],
                'intent': 'Adding error handling'
            },
            'ui_ux': {
                'keywords': ['ui', 'ux', 'interface', 'design', 'style', 'layout'],
                'intent': 'Improving user experience'
            },
            'feature': {
                'keywords': ['add', 'new', 'feature', 'implement', 'create'],
                'intent': 'Adding new functionality'
            },
            'fix': {
                'keywords': ['fix', 'bug', 'issue', 'resolve', 'correct'],
                'intent': 'Fixing bugs'
            },
            'remove': {
                'keywords': ['remove', 'delete', 'legacy', 'deprecated', 'unused'],
                'intent': 'Removing legacy code'
            },
            'test': {
                'keywords': ['test', 'spec', 'coverage', 'unit'],
                'intent': 'Improving test coverage'
            },
            'docs': {
                'keywords': ['doc', 'readme', 'comment', 'documentation'],
                'intent': 'Updating documentation'
            }
        }
        
        # Analyze messages for intents
        detected_intents = []
        for message in messages:
            message_lower = message.lower()
            for pattern_name, pattern_data in intent_patterns.items():
                if any(keyword in message_lower for keyword in pattern_data['keywords']):
                    intent = pattern_data['intent']
                    if intent not in detected_intents:
                        detected_intents.append(intent)
                    break
        
        # Return top 3 most relevant intents
        if not detected_intents:
            return ["Code improvements", "General updates", "Maintenance"]
        
        return detected_intents[:3]
        
    except Exception as e:
        print(f"Error analyzing change intent: {e}")
        return ["Code changes", "Updates", "Development"]


def load_diff_stats():
    """Load and parse git diff statistics"""
    possible_paths = [
        Path(OUTPUT_DIR_RELATIVE + '/diff_stats.txt'),
        Path('../outputs/diff_stats.txt'),
        Path('outputs/diff_stats.txt'),
    ]
    
    diff_file = None
    for path in possible_paths:
        if path.exists():
            diff_file = path
            break
    
    if not diff_file:
        # Try to generate diff stats automatically
        print("Diff stats file not found, attempting to generate...")
        try:
            output_dir = Path(OUTPUT_DIR_RELATIVE)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate diff stats by comparing to main/master branch
            for base_branch in ['origin/main', 'origin/master', 'main', 'master']:
                try:
                    result = subprocess.run(
                        ['git', 'diff', '--numstat', base_branch],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        diff_file = output_dir / 'diff_stats.txt'
                        with open(diff_file, 'w') as f:
                            f.write(result.stdout)
                        print(f"Generated diff stats using {base_branch}")
                        break
                except subprocess.SubprocessError:
                    continue
        except Exception as e:
            print(f"Could not generate diff stats: {e}")
    
    if not diff_file or not diff_file.exists():
        print("No diff stats available")
        return []
    
    file_changes = []
    try:
        with open(diff_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split('\t')
                
                if len(parts) >= 3:
                    try:
                        additions = int(parts[0]) if parts[0] != '-' else 0
                        deletions = int(parts[1]) if parts[1] != '-' else 0
                        filename = parts[2]
                        
                        file_changes.append({
                            'file': filename,
                            'additions': additions,
                            'deletions': deletions,
                            'total': additions + deletions,
                            'file_type': Path(filename).suffix or 'unknown',
                            'directory': str(Path(filename).parent)
                        })
                    except (ValueError, IndexError):
                        # Skip malformed lines
                        continue
                elif len(parts) == 1 and parts[0]:
                    # Handle malformed lines with just filename
                    filename = parts[0]
                    file_changes.append({
                        'file': filename,
                        'additions': 0,
                        'deletions': 0,
                        'total': 1,  # Give it a minimal value
                        'file_type': Path(filename).suffix or 'unknown',
                        'directory': str(Path(filename).parent)
                    })
        print(f"Loaded {len(file_changes)} file changes from diff stats")
    except Exception as e:
        print(f"Error reading diff stats: {e}")
        return []
    
    return file_changes


def create_file_heatmap_data(diff_stats):
    """Create file heatmap data with sizing and coloring"""
    if not diff_stats:
        return []
    
    # Sort by total changes and take top 10 for clarity
    top_files = sorted(diff_stats, key=lambda x: x['total'], reverse=True)[:10]
    
    heatmap_data = []
    for i, file_data in enumerate(top_files):
        additions = file_data['additions']
        deletions = file_data['deletions']
        total = file_data['total']
        
        # Determine color based on change type
        if deletions > additions * 1.5:
            color = '#E74C3C'  # Deep red for heavy deletions
            change_type = 'deletions'
        elif additions > deletions * 1.5:
            color = '#27AE60'  # Deep green for heavy additions  
            change_type = 'additions'
        else:
            color = '#F1C40F'  # Yellow for balanced changes
            change_type = 'balanced'
        
        # Size based on total changes (normalized)
        max_changes = max(f['total'] for f in top_files)
        size_ratio = total / max_changes if max_changes > 0 else 0.1
        
        # Opacity based on complexity (file type and path depth)
        complexity = 0.5
        if file_data['file_type'] in ['.py', '.js', '.ts', '.tsx', '.jsx']:
            complexity += 0.3
        if '/' in file_data['file']:
            complexity += 0.2
        complexity = min(1.0, complexity)
        
        heatmap_data.append({
            'file': Path(file_data['file']).name,  # Just filename for display
            'full_path': file_data['file'],
            'size_ratio': size_ratio,
            'color': color,
            'opacity': complexity,
            'total': total,
            'additions': additions,
            'deletions': deletions,
            'change_type': change_type
        })
    
    return heatmap_data


def generate_impact_grid():
    """Generate focused PR impact grid visualization"""
    if not MATPLOTLIB_AVAILABLE:
        return create_placeholder()
    
    # Gather all data
    risk_score, risk_level, risk_color = calculate_risk_score()
    review_time, time_color = estimate_review_time()
    change_intents = analyze_change_intent()
    diff_stats = load_diff_stats()
    heatmap_data = create_file_heatmap_data(diff_stats)
    
    # Create the grid layout (2x2 main grid with bottom panel)
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 2, height_ratios=[1, 1, 0.8], hspace=0.3, wspace=0.2)
    
    # === TOP LEFT: RISK SCORE ===
    ax_risk = fig.add_subplot(gs[0, 0])
    
    # Big risk score circle
    circle = patches.Circle((0.5, 0.5), 0.35, facecolor=risk_color, alpha=0.8, edgecolor='white', linewidth=4)
    ax_risk.add_patch(circle)
    
    # Risk score number
    ax_risk.text(0.5, 0.6, str(risk_score), ha='center', va='center', 
                fontsize=48, fontweight='bold', color='white')
    
    # Risk level text
    ax_risk.text(0.5, 0.35, risk_level, ha='center', va='center', 
                fontsize=16, fontweight='bold', color='white')
    
    ax_risk.set_xlim(0, 1)
    ax_risk.set_ylim(0, 1)
    ax_risk.set_title('Risk Score', fontsize=14, fontweight='bold', pad=20)
    ax_risk.axis('off')
    
    # === TOP RIGHT: REVIEW TIME ESTIMATE ===
    ax_time = fig.add_subplot(gs[0, 1])
    
    # Time estimate box
    rect = patches.Rectangle((0.1, 0.3), 0.8, 0.4, facecolor=time_color, alpha=0.8, edgecolor='white', linewidth=3)
    ax_time.add_patch(rect)
    
    # Time text
    ax_time.text(0.5, 0.5, review_time, ha='center', va='center', 
                fontsize=24, fontweight='bold', color='white')
    
    ax_time.set_xlim(0, 1)
    ax_time.set_ylim(0, 1)
    ax_time.set_title('Est. Review Time', fontsize=14, fontweight='bold', pad=20)
    ax_time.axis('off')
    
    # === MIDDLE: FILE HEATMAP ===
    ax_heatmap = fig.add_subplot(gs[1, :])
    
    if heatmap_data:
        # Create grid layout for files (max 10 files, 2 rows of 5)
        max_files = min(10, len(heatmap_data))
        cols = 5
        
        for i, file_data in enumerate(heatmap_data[:max_files]):
            row = i // cols
            col = i % cols
            
            # Position calculation
            x = col / cols + 0.1
            y = 0.7 - (row * 0.4)  # Two rows
            
            # Rectangle size based on changes
            width = 0.15 * file_data['size_ratio']
            height = 0.25 * file_data['size_ratio']
            
            # Draw file rectangle
            rect = patches.Rectangle((x, y), width, height, 
                                   facecolor=file_data['color'], 
                                   alpha=file_data['opacity'],
                                   edgecolor='white', linewidth=2)
            ax_heatmap.add_patch(rect)
            
            # Add filename (only show if it's a top file)
            if i < 5:  # Only label top 5 files
                ax_heatmap.text(x + width/2, y - 0.05, file_data['file'][:15], 
                              ha='center', va='top', fontsize=8, fontweight='bold')
            
            # Add change count
            ax_heatmap.text(x + width/2, y + height/2, f"{file_data['total']}", 
                          ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
        # Add legend
        legend_y = 0.05
        ax_heatmap.text(0.1, legend_y, '● Heavy Deletions', color='#E74C3C', fontsize=10, fontweight='bold')
        ax_heatmap.text(0.3, legend_y, '● Heavy Additions', color='#27AE60', fontsize=10, fontweight='bold')
        ax_heatmap.text(0.5, legend_y, '● Balanced Changes', color='#F1C40F', fontsize=10, fontweight='bold')
        ax_heatmap.text(0.7, legend_y, 'Size = Lines Changed', fontsize=10, style='italic')
    else:
        ax_heatmap.text(0.5, 0.5, 'No file changes detected', ha='center', va='center', 
                       fontsize=14, color='#7F8C8D')
    
    ax_heatmap.set_xlim(0, 1)
    ax_heatmap.set_ylim(0, 1)
    ax_heatmap.set_title('File Change Heatmap', fontsize=14, fontweight='bold', pad=20)
    ax_heatmap.axis('off')
    
    # === BOTTOM: CHANGE INTENT SUMMARY ===
    ax_summary = fig.add_subplot(gs[2, :])
    
    # Display change intents as tags
    if change_intents:
        intent_colors = ['#3498DB', '#E74C3C', '#2ECC71']
        for i, intent in enumerate(change_intents):
            x = 0.1 + (i * 0.28)
            color = intent_colors[i % len(intent_colors)]
            
            # Intent tag
            rect = patches.Rectangle((x, 0.4), 0.25, 0.3, facecolor=color, alpha=0.8, 
                                   edgecolor='white', linewidth=2, 
                                   transform=ax_summary.transAxes)
            ax_summary.add_patch(rect)
            
            # Intent text
            ax_summary.text(x + 0.125, 0.55, intent, ha='center', va='center', 
                          fontsize=11, fontweight='bold', color='white',
                          transform=ax_summary.transAxes)
    
    # Summary stats
    total_files = len(diff_stats) if diff_stats else 0
    total_lines = sum(f['total'] for f in diff_stats) if diff_stats else 0
    
    summary_text = f"PR Impact: {total_files} files changed • {total_lines} lines modified"
    ax_summary.text(0.5, 0.15, summary_text, ha='center', va='center', 
                   fontsize=12, fontweight='bold', color='#2C3E50',
                   transform=ax_summary.transAxes)
    
    ax_summary.set_title('Development Intent', fontsize=14, fontweight='bold', pad=20)
    ax_summary.axis('off')
    
    # Overall title
    fig.suptitle('PR Impact Analysis', fontsize=18, fontweight='bold', y=0.95)
    
    plt.tight_layout()
    
    # Save with base64 encoding for PR embedding
    save_image_with_base64(fig, 'development_flow', 'PR Impact Grid')
    plt.close()
    
    return True


def create_no_data_visual():
    """Create minimal visual when no data available"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.text(0.5, 0.5, 'No Change Data Available', 
           ha='center', va='center', fontsize=16, fontweight='bold', color='#7F8C8D')
    ax.text(0.5, 0.3, 'Unable to analyze PR impact', 
           ha='center', va='center', fontsize=12, color='#95A5A6')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save with base64 encoding for PR embedding
    save_image_with_base64(fig, 'development_flow', 'PR Impact Grid')
    plt.close()
    
    return True


def create_placeholder():
    """Create text placeholder when matplotlib unavailable"""
    output_dir = None
    for check_dir in [OUTPUT_DIR_RELATIVE, '../outputs', 'outputs']:
        if Path(check_dir).exists() or Path(check_dir).parent.exists():
            output_dir = Path(check_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            break
    
    if not output_dir:
        output_dir = Path(OUTPUT_DIR_RELATIVE)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'development_flow_placeholder.md'
    
    with open(output_file, 'w') as f:
        f.write("# PR Impact Analysis\n\n")
        f.write("Visual impact grid generation requires matplotlib.\n\n")
        f.write("Install with: `pip install matplotlib numpy`\n")
    
    print("Created PR impact analysis placeholder")
    return False


def main():
    """Main execution function"""
    print("Generating PR impact grid...")
    
    # Ensure output directory exists
    for check_dir in [OUTPUT_DIR_RELATIVE, '../outputs', 'outputs']:
        try:
            Path(check_dir).mkdir(parents=True, exist_ok=True)
            break
        except OSError:
            continue
    
    try:
        success = generate_impact_grid()
        if success:
            print("PR impact grid generation complete!")
        return success
    except Exception as e:
        print(f"Error generating PR impact grid: {e}")
        return create_placeholder()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
