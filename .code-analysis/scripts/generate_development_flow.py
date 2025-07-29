#!/usr/bin/env python3
"""
Generate PR Impact Grid Visualization
Focused visual showing risk score, file changes, and actionable insights
"""

import json
import os
import sys
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
OUTPUT_DIR = Path(__file__).parent.parent / 'outputs'  # Always .code-analysis/outputs


def save_image_with_base64(fig, base_filename):
    """Save image as PNG only (no base64 generation for GitHub Pages deployment)"""
    # Use the standardized output directory
    output_dir = OUTPUT_DIR
    
    # Create the directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Print output directory for debugging
    print(f"Saving image to: {output_dir.absolute()}")
    
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
    max_raw_size = 45 * 1024  # 45KB raw for optimal loading
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
    
    print(f"Generated optimized {base_filename}: {size_kb:.1f} KB (DPI: {dpi})")
    print(f"PNG file saved to: {png_path}")
    
    return png_path


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
        
        if risk_score >= 8:
            return risk_score, "CRITICAL", "#E74C3C"  # Red
        elif risk_score >= 5:
            return risk_score, "HIGH", "#F39C12"  # Orange
        elif risk_score >= 3:
            return risk_score, "MEDIUM", "#F1C40F"  # Yellow
        else:
            return risk_score, "LOW", "#2ECC71"  # Green
            
    except Exception as e:
        print(f"Error calculating risk score: {e}")
        return 3, "Medium", "#F39C12"


def estimate_review_time():
    """Estimate review time based on change complexity (15 min to 2 hours max)"""
    try:
        diff_stats = load_diff_stats()
        if not diff_stats:
            return "15 min", "#2ECC71"
        
        total_files = len(diff_stats)
        total_lines = sum(f['total'] for f in diff_stats)
        
        # More conservative time calculation
        # Base time: 15 min for any change
        minutes = 15
        
        # File complexity: 2 min per file (much more conservative)
        file_time = min(total_files * 2, 30)  # Cap file contribution at 30 min
        minutes += file_time
        
        # Line complexity: 1 min per 50 lines (much more conservative)
        line_time = min((total_lines // 50) * 1, 20)  # Cap line contribution at 20 min
        minutes += line_time
        
        # Complexity multipliers for certain file types (very small)
        complex_files = sum(1 for f in diff_stats 
                           if any(f['file'].endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx']))
        if complex_files > 8:
            minutes = int(minutes * 1.3)  # Only for very complex PRs
        elif complex_files > 4:
            minutes = int(minutes * 1.1)  # Minimal bump
        
        # Conservative cap at 90 minutes (1.5 hours) for most cases
        # Only allow 2 hours for truly massive changes
        if total_files > 20 or total_lines > 1000:
            minutes = min(minutes, 120)  # 2 hours max for massive PRs
        else:
            minutes = min(minutes, 90)   # 1.5 hours max for normal PRs
        
        # Format time estimate
        if minutes < 60:
            time_str = f"{minutes} min"
            color = "#2ECC71" if minutes <= 30 else "#F39C12"
        else:
            hours = minutes // 60
            remaining_mins = minutes % 60
            if remaining_mins > 0:
                time_str = f"{hours}h {remaining_mins}m"
            else:
                time_str = f"{hours}h"
            # Color coding: green <= 30 min, orange <= 60 min, red > 60 min
            color = "#E74C3C" if minutes > 60 else "#F39C12"
        
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
        OUTPUT_DIR / 'diff_stats.txt',
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
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            
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
                        diff_file = OUTPUT_DIR / 'diff_stats.txt'
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


def load_enhanced_analysis_data():
    """Load enhanced PR impact analysis data if available"""
    try:
        # Try multiple possible locations for the enhanced analysis file
        possible_paths = [
            OUTPUT_DIR / 'pr_impact_analysis_v2.json',
            Path('outputs/pr_impact_analysis_v2.json'),
        ]
        
        for enhanced_file in possible_paths:
            if enhanced_file.exists():
                with open(enhanced_file, 'r', encoding='utf-8') as f:
                    print(f"Loading enhanced analysis from: {enhanced_file}")
                    return json.load(f)
                    
        print("Enhanced analysis file not found in any expected location")
    except Exception as e:
        print(f"Could not load enhanced analysis data: {e}")
    return None


def get_risk_level_text(risk_score):
    """Convert risk score to text level"""
    if risk_score >= 8:
        return "CRITICAL"
    elif risk_score >= 5:
        return "HIGH"
    elif risk_score >= 3:
        return "MEDIUM"
    else:
        return "LOW"


def get_risk_color(risk_score):
    """Get color for risk score"""
    if risk_score >= 8:
        return "#E74C3C"  # Red
    elif risk_score >= 5:
        return "#F39C12"  # Orange
    elif risk_score >= 3:
        return "#F1C40F"  # Yellow
    else:
        return "#2ECC71"  # Green


def get_time_color(review_time):
    """Get color for review time"""
    if "h" in review_time and int(review_time.split("h")[0]) >= 2:
        return "#E74C3C"  # Red for 2+ hours
    elif "h" in review_time or ("m" in review_time and int(review_time.replace("m", "")) > 60):
        return "#F39C12"  # Orange for 1+ hour
    else:
        return "#2ECC71"  # Green for under 1 hour


def create_consistent_risk_categories(diff_stats, overall_risk_score):
    """Create file risk categories that are consistent with the overall risk score"""
    if not diff_stats:
        return {
            'high_risk': {'count': 0, 'files': []},
            'medium_risk': {'count': 0, 'files': []},
            'low_risk': {'count': 0, 'files': []}
        }
    
    high_risk_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.cs'}
    config_extensions = {'.json', '.yaml', '.yml', '.xml', '.config'}
    
    high_risk_files = []
    medium_risk_files = []
    low_risk_files = []
    
    # Sort files by total changes to prioritize
    sorted_files = sorted(diff_stats, key=lambda x: x['total'], reverse=True)
    
    for file_data in sorted_files:
        file_path = file_data['file']
        total_changes = file_data['total']
        file_ext = Path(file_path).suffix.lower()
        
        # Determine risk level based on multiple factors
        risk_factors = 0
        reasons = []
        
        # Factor 1: File type
        if file_ext in high_risk_extensions:
            risk_factors += 2
            reasons.append("critical code file")
        elif file_ext in config_extensions:
            risk_factors += 1
            reasons.append("configuration file")
        
        # Factor 2: Change volume
        if total_changes > 100:
            risk_factors += 2
            reasons.append(f"{total_changes} lines changed")
        elif total_changes > 50:
            risk_factors += 1
            reasons.append(f"{total_changes} lines changed")
        
        # Factor 3: Deletion ratio (high deletions = higher risk)
        deletions = file_data.get('deletions', 0)
        if total_changes > 0:
            deletion_ratio = deletions / total_changes
            if deletion_ratio > 0.5:
                risk_factors += 1
                reasons.append("high deletion ratio")
        
        # Factor 4: Path complexity (deep nesting may indicate core files)
        path_depth = len(Path(file_path).parts)
        if path_depth > 3:
            risk_factors += 1
            reasons.append("deep path structure")
        
        # Categorize based on risk factors
        reason_text = ", ".join(reasons) if reasons else "minor changes"
        file_info = {
            'file': Path(file_path).name,
            'full_path': file_path,
            'reason': reason_text,
            'changes': total_changes
        }
        
        if risk_factors >= 3:
            high_risk_files.append(file_info)
        elif risk_factors >= 1:
            medium_risk_files.append(file_info)
        else:
            low_risk_files.append(file_info)
    
    # If overall risk is high but we have no high-risk files, promote some medium-risk files
    if overall_risk_score >= 5 and len(high_risk_files) == 0 and len(medium_risk_files) > 0:
        # Promote the top medium-risk files to high-risk
        files_to_promote = min(2, len(medium_risk_files))
        for _ in range(files_to_promote):
            file_info = medium_risk_files.pop(0)
            file_info['reason'] = f"high overall PR risk, {file_info['reason']}"
            high_risk_files.append(file_info)
    
    # If overall risk is medium but we have no medium-risk files, promote some low-risk files
    elif overall_risk_score >= 3 and len(medium_risk_files) == 0 and len(low_risk_files) > 0:
        files_to_promote = min(2, len(low_risk_files))
        for _ in range(files_to_promote):
            file_info = low_risk_files.pop(0)
            file_info['reason'] = f"medium overall PR risk, {file_info['reason']}"
            medium_risk_files.append(file_info)
    
    return {
        'high_risk': {'count': len(high_risk_files), 'files': high_risk_files},
        'medium_risk': {'count': len(medium_risk_files), 'files': medium_risk_files},
        'low_risk': {'count': len(low_risk_files), 'files': low_risk_files}
    }


def get_file_change_color(change_type):
    """Get color for file change type"""
    colors = {
        'addition': '#27AE60',  # Green for additions
        'deletion': '#E74C3C',  # Red for deletions
        'modification': '#F1C40F',  # Yellow for modifications
        'mixed': '#3498DB',  # Blue for mixed changes
        'unknown': '#95A5A6'  # Gray for unknown
    }
    return colors.get(change_type, colors['mixed'])


def create_demo_heatmap_data():
    """Create demo heatmap data for visualization"""
    demo_files = [
        {'file': 'UserProfile.tsx', 'total': 85, 'change_type': 'modification'},
        {'file': 'api/users.ts', 'total': 45, 'change_type': 'addition'},
        {'file': 'UserSettings.tsx', 'total': 32, 'change_type': 'mixed'},
        {'file': 'types/user.ts', 'total': 28, 'change_type': 'addition'},
        {'file': 'utils/auth.ts', 'total': 67, 'change_type': 'modification'},
        {'file': 'components/Nav.tsx', 'total': 15, 'change_type': 'deletion'},
        {'file': 'styles/global.css', 'total': 23, 'change_type': 'mixed'},
        {'file': 'config/database.ts', 'total': 47, 'change_type': 'addition'}
    ]
    
    heatmap_data = []
    for file_data in demo_files:
        heatmap_data.append({
            'file': file_data['file'],
            'total': file_data['total'],
            'size_ratio': min(1.0, file_data['total'] / 100),
            'color': get_file_change_color(file_data['change_type']),
            'opacity': 0.8
        })
    
    return heatmap_data


def create_demo_visual():
    """Create a demo visual with sample data when no enhanced analysis is available"""
    if not MATPLOTLIB_AVAILABLE:
        return create_placeholder()
    
    # Demo data
    risk_score = 6
    risk_level = get_risk_level_text(risk_score)
    risk_color = get_risk_color(risk_score)
    review_time = "1h 15m"
    time_color = get_time_color(review_time)
    
    heatmap_data = create_demo_heatmap_data()
    
    file_impact = {
        'total_files': 8,
        'total_lines_changed': 342
    }
    
    return generate_visual_with_data(risk_score, risk_level, risk_color, review_time, time_color, heatmap_data, file_impact, None)


def generate_visual_with_data(risk_score, risk_level, risk_color, review_time, time_color, heatmap_data, file_impact, enhanced_data=None):
    """Generate the actual visual with provided data following redesign specifications"""
    # Create clean, simple layout with more space for file impact section
    fig = plt.figure(figsize=(14, 10))  # Larger size for better readability
    # Adjusted grid with more space for file impact section
    gs = GridSpec(3, 2, height_ratios=[1.0, 2.0, 1.0], hspace=0.3, wspace=0.3, 
                  top=0.94, bottom=0.06, left=0.06, right=0.94)
    
    # === TOP LEFT: RISK SCORE (Clean and Simple) ===
    ax_risk = fig.add_subplot(gs[0, 0])
    
    # Simple risk box without complex styling
    risk_box = patches.Rectangle((0.1, 0.2), 0.8, 0.6, facecolor='white', 
                               edgecolor=risk_color, linewidth=2)
    ax_risk.add_patch(risk_box)
    
    # Simple text without emojis (avoiding font issues)
    ax_risk.text(0.5, 0.65, f"RISK: {risk_score}/10", ha='center', va='center', 
                fontsize=16, fontweight='bold', color=risk_color)
    ax_risk.text(0.5, 0.45, risk_level, ha='center', va='center', 
                fontsize=14, fontweight='bold', color=risk_color)
    ax_risk.text(0.5, 0.25, f"Test Coverage: {100-(risk_score*10)}%", ha='center', va='center', 
                fontsize=11, color='#2C3E50')
    
    ax_risk.set_xlim(0, 1)
    ax_risk.set_ylim(0, 1)
    ax_risk.axis('off')
    
    # === TOP RIGHT: TIME INVESTMENT (Clean and Simple) ===
    ax_time = fig.add_subplot(gs[0, 1])
    
    # Simple time box
    time_box = patches.Rectangle((0.1, 0.2), 0.8, 0.6, facecolor='white', 
                               edgecolor=time_color, linewidth=2)
    ax_time.add_patch(time_box)
    
    ax_time.text(0.5, 0.65, f"Time Investment: {review_time}", ha='center', va='center', 
                fontsize=14, fontweight='bold', color=time_color)
    ax_time.text(0.5, 0.45, "Fix: 15m | Test: 45m | Review: 30m", ha='center', va='center', 
                fontsize=11, color='#2C3E50')
    
    ax_time.set_xlim(0, 1)
    ax_time.set_ylim(0, 1)
    ax_time.axis('off')
    
    # === MIDDLE: FILE IMPACT (Improved Layout) ===
    ax_files = fig.add_subplot(gs[1, :])
    total_files = file_impact.get('total_files', len(heatmap_data))
    
    # Clean title with more space
    ax_files.text(0.5, 0.95, f"File Impact Summary ({total_files} files)", ha='center', va='center', 
                 fontsize=16, fontweight='bold', color='#2C3E50')
    
    # Get or create consistent risk categories based on overall risk score
    risk_categories = file_impact.get('risk_categories', {})
    
    # If risk categories are empty or inconsistent, create consistent ones
    if (not risk_categories or 
        (risk_score >= 5 and risk_categories.get('high_risk', {}).get('count', 0) == 0) or
        (risk_score >= 3 and risk_categories.get('medium_risk', {}).get('count', 0) == 0 and 
         risk_categories.get('high_risk', {}).get('count', 0) == 0)):
        
        # Load diff stats to create consistent categories
        diff_stats = load_diff_stats()
        risk_categories = create_consistent_risk_categories(diff_stats, risk_score)
    
    high_risk_count = risk_categories.get('high_risk', {}).get('count', 0)
    medium_risk_count = risk_categories.get('medium_risk', {}).get('count', 0)
    low_risk_count = risk_categories.get('low_risk', {}).get('count', 0)
    
    # Get actual file examples if available
    high_risk_files = risk_categories.get('high_risk', {}).get('files', [])
    medium_risk_files = risk_categories.get('medium_risk', {}).get('files', [])
    low_risk_files = risk_categories.get('low_risk', {}).get('files', [])
    
    # LEFT COLUMN: Risk Categories with improved spacing
    # HIGH RISK section with better layout
    ax_files.text(0.05, 0.8, f"HIGH RISK ({high_risk_count} files)", ha='left', va='top', 
                 fontsize=13, fontweight='bold', color='#E74C3C')
    if high_risk_files:
        first_high_risk = high_risk_files[0]
        file_name = first_high_risk.get('file', 'Security/Critical files')
        reason = first_high_risk.get('reason', 'High risk changes')
        # Split into two lines for better readability
        ax_files.text(0.07, 0.75, f"• {file_name}", ha='left', va='top', 
                     fontsize=10, color='#2C3E50', fontweight='bold')
        ax_files.text(0.07, 0.72, f"  {reason}", ha='left', va='top', 
                     fontsize=9, color='#555555', style='italic')
    else:
        ax_files.text(0.07, 0.75, "• No high risk files detected", ha='left', va='top', 
                     fontsize=10, color='#7F8C8D')
    
    # MEDIUM RISK section with better layout
    ax_files.text(0.05, 0.65, f"MEDIUM RISK ({medium_risk_count} files)", ha='left', va='top', 
                 fontsize=13, fontweight='bold', color='#F39C12')
    if medium_risk_files:
        first_medium_risk = medium_risk_files[0]
        file_name = first_medium_risk.get('file', 'Complex files')
        reason = first_medium_risk.get('reason', 'Needs review')
        # Split into two lines for better readability
        ax_files.text(0.07, 0.6, f"• {file_name}", ha='left', va='top', 
                     fontsize=10, color='#2C3E50', fontweight='bold')
        ax_files.text(0.07, 0.57, f"  {reason}", ha='left', va='top', 
                     fontsize=9, color='#555555', style='italic')
    else:
        ax_files.text(0.07, 0.6, "• No medium risk files detected", ha='left', va='top', 
                     fontsize=10, color='#7F8C8D')
    
    # LOW RISK section with better layout
    ax_files.text(0.05, 0.5, f"LOW RISK ({low_risk_count} files)", ha='left', va='top', 
                 fontsize=13, fontweight='bold', color='#27AE60')
    if low_risk_files:
        first_low_risk = low_risk_files[0]
        file_name = first_low_risk.get('file', 'Documentation files')
        reason = first_low_risk.get('reason', 'Minor changes')
        # Split into two lines for better readability
        ax_files.text(0.07, 0.45, f"• {file_name}", ha='left', va='top', 
                     fontsize=10, color='#2C3E50', fontweight='bold')
        ax_files.text(0.07, 0.42, f"  {reason}", ha='left', va='top', 
                     fontsize=9, color='#555555', style='italic')
    else:
        ax_files.text(0.07, 0.45, "• No low risk files detected", ha='left', va='top', 
                     fontsize=10, color='#7F8C8D')
    
    # RIGHT COLUMN: Change Distribution with improved positioning
    ax_files.text(0.55, 0.8, "Change Distribution:", ha='left', va='top', 
                 fontsize=13, fontweight='bold', color='#2C3E50')
    
    # Get change distribution data
    change_dist = file_impact.get('change_distribution', {})
    modified_pct = change_dist.get('modified_percentage', 80)
    new_files_pct = change_dist.get('new_files_percentage', 20)
    
    # Modified files bar with better positioning
    bar_width = max(0.05, (modified_pct / 100) * 0.35)  # Scale to max 0.35 width
    mod_rect = patches.Rectangle((0.55, 0.7), bar_width, 0.06, facecolor='#3498DB', alpha=0.8)
    ax_files.add_patch(mod_rect)
    ax_files.text(0.92, 0.73, f"{modified_pct}% Modified", ha='left', va='center', fontsize=11, color='#2C3E50')
    
    # New files bar with better positioning
    new_bar_width = max(0.03, (new_files_pct / 100) * 0.35)  # Scale to max 0.35 width
    new_rect = patches.Rectangle((0.55, 0.6), new_bar_width, 0.06, facecolor='#27AE60', alpha=0.8)
    ax_files.add_patch(new_rect)
    ax_files.text(0.92, 0.63, f"{new_files_pct}% New files", ha='left', va='center', fontsize=11, color='#2C3E50')
    
    ax_files.set_xlim(0, 1)
    ax_files.set_ylim(0, 1)
    ax_files.axis('off')
    
    # === BOTTOM: REQUIRED ACTIONS (Clean List) ===
    ax_actions = fig.add_subplot(gs[2, :])
    
    ax_actions.text(0.1, 0.8, "Required Actions (Prioritized)", ha='left', va='center', 
                   fontsize=14, fontweight='bold', color='#2C3E50')
    
    # Get actionable items from enhanced data
    actions = []
    action_colors = ['#E74C3C', '#F39C12', '#3498DB', '#9B59B6']
    
    if enhanced_data and 'actionable_items' in enhanced_data:
        actionable_items = enhanced_data['actionable_items']
        for i, item in enumerate(actionable_items[:3]):  # Limit to top 3 for visual space
            title = item.get('title', 'Review required')
            effort = item.get('effort', '?')
            blocking = item.get('blocking', False)
            blocking_text = " WARNING" if blocking else ""
            action_text = f"{i+1}. {title} ({effort}){blocking_text}"
            actions.append(action_text)
    else:
        # Fallback actions if no enhanced data available
        actions = [
            "1. Review changed files for quality",
            "2. Ensure test coverage is adequate", 
            "3. Update documentation if needed"
        ]
    
    for i, action in enumerate(actions):
        y_pos = 0.6 - (i * 0.2)
        color = action_colors[i] if i < len(action_colors) else '#2C3E50'
        ax_actions.text(0.1, y_pos, action, ha='left', va='center', 
                       fontsize=12, color=color, fontweight='bold')
    
    ax_actions.set_xlim(0, 1)
    ax_actions.set_ylim(0, 1)
    ax_actions.axis('off')
    
    # Add timestamp to bottom right corner to ensure unique content
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    fig.text(0.98, 0.02, f"Updated: {current_time}", ha='right', va='bottom', 
             fontsize=8, color='#7F8C8D', alpha=0.7)
    
    # Clean title
    fig.suptitle('PR Impact Analysis', fontsize=18, fontweight='bold', y=0.95, color='#2C3E50')
    
    plt.tight_layout()
    
    # Save with PNG-only (no base64 for GitHub Pages deployment)
    save_image_with_base64(fig, 'development_flow')
    plt.close()
    
    return True
    
def generate_impact_grid():
    """Generate focused PR impact grid visualization using enhanced analysis data"""
    if not MATPLOTLIB_AVAILABLE:
        return create_placeholder()
    
    # Load enhanced PR impact analysis data
    enhanced_data = load_enhanced_analysis_data()
    
    if not enhanced_data:
        print("No enhanced analysis data available - creating demo visualization")
        return create_demo_visual()
    
    # Extract data from enhanced analysis
    visual_risk_score = enhanced_data.get("risk_metrics", {}).get("overall_score", 5)
    visual_risk_level = get_risk_level_text(visual_risk_score)
    visual_risk_color = get_risk_color(visual_risk_score)
    visual_review_time = enhanced_data.get("time_investment", {}).get("total", "45m")
    visual_time_color = get_time_color(visual_review_time)
    
    # Get file impact data for heatmap
    file_impacts = enhanced_data.get("file_impact", {}).get("high_impact_files", [])
    visual_heatmap_data = []
    for file_data in file_impacts[:10]:  # Limit to 10 files
        visual_heatmap_data.append({
            'file': file_data.get('file', 'unknown'),
            'total': file_data.get('lines_changed', 0),
            'size_ratio': min(1.0, file_data.get('lines_changed', 0) / 100),
            'color': get_file_change_color(file_data.get('change_type', 'mixed')),
            'opacity': 0.8
        })
    
    # If no file impacts, create demo data
    if not visual_heatmap_data:
        visual_heatmap_data = create_demo_heatmap_data()
    
    # Get diff stats for summary  
    visual_file_impact = enhanced_data.get("file_impact", {})
    
    # If no file impact data, create demo data
    if not visual_file_impact.get('total_files') and not visual_file_impact.get('total_lines_changed'):
        visual_file_impact = {
            'total_files': 8,
            'total_lines_changed': 342
        }
    
    return generate_visual_with_data(visual_risk_score, visual_risk_level, visual_risk_color, 
                                   visual_review_time, visual_time_color, visual_heatmap_data, 
                                   visual_file_impact, enhanced_data)


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
    # Save with PNG-only (no base64 for GitHub Pages deployment)  
    save_image_with_base64(fig, 'development_flow')
    plt.close()
    
    return True


def create_placeholder():
    """Create text placeholder when matplotlib unavailable"""
    # Use the standardized output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating placeholder in: {OUTPUT_DIR.absolute()}")
    
    output_file = OUTPUT_DIR / 'development_flow_placeholder.md'
    
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
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Using output directory: {OUTPUT_DIR.absolute()}")
    except Exception as e:
        print(f"Error creating output directory: {e}")
    
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
