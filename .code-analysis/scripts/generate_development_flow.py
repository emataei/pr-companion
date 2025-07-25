#!/usr/bin/env python3
"""
Generate Optimized Development Flow Visualization
Clean, focused visual showing PR development timeline
"""

import json
import os
import sys
import base64
from io import BytesIO
from pathlib import Path
import subprocess
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def save_image_with_base64(fig, base_filename, title="Development Flow"):
    """Save image as PNG and create base64 + markdown files"""
    # Find the output directory dynamically
    output_dir = None
    for check_dir in ['.code-analysis/outputs', '../.code-analysis/outputs', '../../.code-analysis/outputs']:
        if Path(check_dir).exists() or Path(check_dir).parent.exists():
            output_dir = Path(check_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            break
    
    if not output_dir:
        output_dir = Path('.code-analysis/outputs')
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


def classify_commit_purpose(message, files_changed=0):
    """Classify commit purpose based on message and changes"""
    message_lower = message.lower()
    
    # Define purpose patterns (order matters - more specific first)
    purpose_patterns = {
        'setup': {
            'keywords': ['initial', 'setup', 'init', 'scaffold', 'bootstrap', 'create project', 'dependencies', 'config'],
            'color': '#9B59B6',
            'icon': 'SET',
            'label': 'Setup/Config'
        },
        'feature': {
            'keywords': ['add', 'implement', 'create', 'new', 'feature', 'introduce', 'build'],
            'color': '#3498DB', 
            'icon': 'NEW',
            'label': 'Features'
        },
        'fix': {
            'keywords': ['fix', 'bug', 'error', 'issue', 'resolve', 'correct', 'patch'],
            'color': '#E74C3C',
            'icon': 'FIX', 
            'label': 'Bug Fixes'
        },
        'refactor': {
            'keywords': ['refactor', 'cleanup', 'reorganize', 'restructure', 'improve', 'optimize', 'clean'],
            'color': '#F39C12',
            'icon': 'REF',
            'label': 'Refactoring'
        },
        'docs': {
            'keywords': ['doc', 'readme', 'comment', 'documentation', 'guide', 'example'],
            'color': '#2ECC71',
            'icon': 'DOC',
            'label': 'Documentation'
        },
        'test': {
            'keywords': ['test', 'spec', 'unit', 'integration', 'coverage'],
            'color': '#1ABC9C',
            'icon': 'TST',  
            'label': 'Testing'
        },
        'style': {
            'keywords': ['style', 'format', 'lint', 'prettier', 'css', 'ui'],
            'color': '#E67E22',
            'icon': 'STY',
            'label': 'Styling'
        },
        'merge': {
            'keywords': ['merge', 'pull request', 'pr'],
            'color': '#95A5A6',
            'icon': 'MRG',
            'label': 'Merges'
        }
    }
    
    # Check for purpose based on keywords
    for purpose, config in purpose_patterns.items():
        if any(keyword in message_lower for keyword in config['keywords']):
            return purpose, config
    
    # Default to feature if no clear pattern
    return 'feature', purpose_patterns['feature']


def get_commit_timeline():
    """Get commits with purpose classification and impact analysis"""
    try:
        # Get commits with detailed stats
        cmd = ["git", "log", "--oneline", "--format=%h|%s|%ad", "--date=short", "--numstat", "-10"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return []
        
        commits = []
        current_commit = None
        
        for line in result.stdout.strip().split('\n'):
            if '|' in line and not line.startswith('\t'):
                # This is a commit line
                if current_commit:
                    commits.append(current_commit)
                
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    current_commit = {
                        'hash': parts[0][:7],
                        'message': parts[1][:50],
                        'date': parts[2],
                        'files_changed': 0,
                        'lines_added': 0,
                        'lines_deleted': 0
                    }
            elif current_commit and '\t' in line:
                # This is a file change line
                parts = line.split('\t')
                if len(parts) >= 3:
                    try:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        deleted = int(parts[1]) if parts[1] != '-' else 0
                        current_commit['files_changed'] += 1
                        current_commit['lines_added'] += added
                        current_commit['lines_deleted'] += deleted
                    except ValueError:
                        continue
        
        # Add the last commit
        if current_commit:
            commits.append(current_commit)
        
        # Classify each commit's purpose
        for commit in commits:
            purpose, purpose_config = classify_commit_purpose(commit['message'], commit['files_changed'])
            commit['purpose'] = purpose
            commit['purpose_config'] = purpose_config
            
            # Calculate impact
            total_changes = commit['lines_added'] + commit['lines_deleted']
            if total_changes > 100 or commit['files_changed'] > 5:
                commit['impact'] = 'high'
            elif total_changes > 30 or commit['files_changed'] > 2:
                commit['impact'] = 'medium'
            else:
                commit['impact'] = 'low'
        
        return commits[:7]  # Show more commits for better purpose grouping
        
    except Exception as e:
        print(f"Error getting commit timeline: {e}")
        return []


def generate_clean_flow():
    """Generate purpose-focused development flow"""
    if not MATPLOTLIB_AVAILABLE:
        return create_placeholder()
    
    commits = get_commit_timeline()
    if not commits:
        return create_no_data_visual()
    
    # Create larger figure for purpose visualization
    fig, (ax_timeline, ax_groups) = plt.subplots(2, 1, figsize=(16, 10), 
                                                 gridspec_kw={'height_ratios': [2, 1]})
    
    # === TOP: PURPOSE-BASED TIMELINE ===
    
    # Calculate positions
    num_commits = len(commits)
    if num_commits == 1:
        x_positions = [0.5]
    else:
        margin = 0.08
        available_width = 1.0 - (2 * margin)
        spacing = available_width / (num_commits - 1)
        x_positions = [margin + i * spacing for i in range(num_commits)]
    
    # Draw timeline base
    timeline_y = 0.5
    if len(commits) > 1:
        ax_timeline.plot(x_positions, [timeline_y] * len(commits), 
                        color='#BDC3C7', linewidth=6, zorder=1, alpha=0.6)
    
    # Draw commits on timeline
    for i, commit in enumerate(commits):
        x_pos = x_positions[i]
        config = commit['purpose_config']
        
        # Size based on impact
        size_map = {'high': 180, 'medium': 140, 'low': 110}
        size = size_map[commit['impact']]
        
        # Draw commit point
        ax_timeline.scatter(x_pos, timeline_y, s=size, c=config['color'], 
                           zorder=3, edgecolors='white', linewidth=3, alpha=0.9)
        
        # Add purpose icon and hash above
        ax_timeline.text(x_pos, timeline_y + 0.25, f"[{config['icon']}] {commit['hash']}", 
                        ha='center', va='bottom', fontsize=10, 
                        fontweight='bold', color=config['color'])
        
        # Add impact metrics
        total_changes = commit['lines_added'] + commit['lines_deleted']
        metrics_text = f"{commit['files_changed']}f, {total_changes}Δ"
        ax_timeline.text(x_pos, timeline_y - 0.15, metrics_text, 
                        ha='center', va='top', fontsize=9, 
                        color='#34495E', fontweight='bold')
        
        # Add commit message
        message = commit['message'][:30] + '...' if len(commit['message']) > 30 else commit['message']
        ax_timeline.text(x_pos, timeline_y - 0.25, message, 
                        ha='center', va='top', fontsize=8, 
                        color='#7F8C8D', style='italic',
                        bbox={'boxstyle': 'round,pad=0.2', 'facecolor': 'white', 'alpha': 0.9, 'edgecolor': config['color'], 'linewidth': 1})
        
        # Add date
        ax_timeline.text(x_pos, timeline_y - 0.35, commit['date'], 
                        ha='center', va='top', fontsize=7, 
                        color='#95A5A6')
    
    # Timeline styling
    ax_timeline.set_xlim(0, 1)
    ax_timeline.set_ylim(0, 1)
    ax_timeline.set_title('Development Purpose Timeline', fontsize=18, pad=20, fontweight='bold', color='#2C3E50')
    ax_timeline.axis('off')
    
    # === BOTTOM: PURPOSE GROUPS SUMMARY ===
    
    # Group commits by purpose
    purpose_groups = {}
    for commit in commits:
        purpose = commit['purpose']
        if purpose not in purpose_groups:
            purpose_groups[purpose] = {
                'commits': [],
                'config': commit['purpose_config'],
                'total_files': 0,
                'total_changes': 0
            }
        purpose_groups[purpose]['commits'].append(commit)
        purpose_groups[purpose]['total_files'] += commit['files_changed']
        purpose_groups[purpose]['total_changes'] += commit['lines_added'] + commit['lines_deleted']
    
    # Draw purpose groups
    group_positions = list(range(len(purpose_groups)))
    group_x_positions = [i / max(1, len(purpose_groups) - 1) if len(purpose_groups) > 1 else 0.5 for i in group_positions]
    
    for i, (purpose, group_data) in enumerate(purpose_groups.items()):
        x_pos = group_x_positions[i] if len(purpose_groups) > 1 else 0.5
        config = group_data['config']
        count = len(group_data['commits'])
        
        # Draw group circle (size based on commit count)
        circle_size = 100 + (count * 30)
        ax_groups.scatter(x_pos, 0.6, s=circle_size, c=config['color'], 
                         zorder=3, edgecolors='white', linewidth=3, alpha=0.8)
        
        # Add purpose label and count
        ax_groups.text(x_pos, 0.6, f"[{config['icon']}]\n{count}", 
                      ha='center', va='center', fontsize=11, 
                      fontweight='bold', color='white')
        
        # Add purpose name below
        ax_groups.text(x_pos, 0.35, config['label'], 
                      ha='center', va='top', fontsize=10, 
                      fontweight='bold', color=config['color'])
        
        # Add metrics below
        metrics = f"{group_data['total_files']}f, {group_data['total_changes']}Δ"
        ax_groups.text(x_pos, 0.25, metrics, 
                      ha='center', va='top', fontsize=8, 
                      color='#34495E')
    
    # Groups styling
    ax_groups.set_xlim(0, 1)
    ax_groups.set_ylim(0, 1)
    ax_groups.set_title('Purpose Groups Summary', fontsize=14, pad=15, fontweight='bold', color='#2C3E50')
    ax_groups.axis('off')
    
    # Add overall summary
    total_files = sum(c['files_changed'] for c in commits)
    total_added = sum(c['lines_added'] for c in commits)
    total_deleted = sum(c['lines_deleted'] for c in commits)
    
    summary_text = f"PR Development: {len(commits)} commits across {len(purpose_groups)} purposes • {total_files} files • +{total_added}/-{total_deleted} lines"
    fig.suptitle(summary_text, fontsize=13, fontweight='bold', color='#2C3E50', y=0.02)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.95, bottom=0.08)

    # Save with base64 encoding for PR embedding
    save_image_with_base64(fig, 'development_flow', 'Development Timeline')
    plt.close()
    
    return True


def create_ultra_simple_flow(commits):
    """Create minimal text-based flow if image is too large"""
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Just show commit count and latest commit
    latest = commits[0] if commits else {'message': 'No commits', 'hash': ''}
    
    ax.text(0.5, 0.7, f"{len(commits)} Recent Commits", 
           ha='center', va='center', fontsize=16, fontweight='bold')
    ax.text(0.5, 0.3, f"Latest: {latest['message']}", 
           ha='center', va='center', fontsize=12)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save with base64 encoding for PR embedding
    save_image_with_base64(fig, 'development_flow', 'Development Timeline')
    plt.close()
    
    return True


def create_no_data_visual():
    """Create minimal visual when no commit data available"""
    fig, ax = plt.subplots(figsize=(6, 2))
    
    ax.text(0.5, 0.5, 'No Development Data Available', 
           ha='center', va='center', fontsize=14)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save with base64 encoding for PR embedding
    save_image_with_base64(fig, 'development_flow', 'Development Timeline')
    plt.close()
    
    return True


def create_placeholder():
    """Create text placeholder when matplotlib unavailable"""
    output_file = '.code-analysis/outputs/development_flow_placeholder.md'
    
    with open(output_file, 'w') as f:
        f.write("# Development Flow\n\n")
        f.write("Visual flow generation requires matplotlib.\n\n")
        f.write("Install with: `pip install matplotlib numpy`\n")
    
    print("Created development flow placeholder")
    return False


def main():
    """Main execution function"""
    print("Generating optimized development flow...")
    
    # Ensure output directory exists
    Path('.code-analysis/outputs').mkdir(parents=True, exist_ok=True)
    
    try:
        success = generate_clean_flow()
        if success:
            print("Optimized development flow generation complete!")
        return success
    except Exception as e:
        print(f"Error generating development flow: {e}")
        return create_placeholder()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
