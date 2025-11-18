#!/usr/bin/env python3
"""
Generate PR Code Change Heat Map Visualization
Creates a visual heat map showing all files changed in the PR with color coding based on change intensity
"""

import json
import os
import sys
from io import BytesIO
from pathlib import Path
import subprocess
import math

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available, cannot generate heat map")

# Constants
OUTPUT_DIR = Path(__file__).parent.parent / 'outputs'


def load_diff_stats():
    """Load diff stats from available sources"""
    possible_paths = [
        OUTPUT_DIR / 'diff_stats.txt',
        Path('outputs/diff_stats.txt'),
        Path('.code-analysis/outputs/diff_stats.txt'),
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
        with open(diff_file, 'r', encoding='utf-8-sig') as f:
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
                        continue
                elif len(parts) == 1 and parts[0]:
                    # Handle malformed lines with just filename
                    filename = parts[0]
                    file_changes.append({
                        'file': filename,
                        'additions': 0,
                        'deletions': 0,
                        'total': 1,
                        'file_type': Path(filename).suffix or 'unknown',
                        'directory': str(Path(filename).parent)
                    })
        print(f"Loaded {len(file_changes)} file changes from diff stats")
    except Exception as e:
        print(f"Error reading diff stats: {e}")
        return []
    
    return file_changes


def calculate_grid_dimensions(num_files):
    """Calculate optimal grid dimensions for the heat map"""
    if num_files == 0:
        return 1, 1
    
    # Try to make roughly square grid
    cols = math.ceil(math.sqrt(num_files))
    rows = math.ceil(num_files / cols)
    
    return rows, cols


def get_change_color(additions, deletions, max_changes):
    """Get color based on additions and deletions"""
    total = additions + deletions
    
    if total == 0:
        return '#ECEFF1'  # Light gray for no changes
    
    # Normalize to 0-1 scale
    intensity = min(1.0, total / max_changes) if max_changes > 0 else 0.1
    
    # Determine color based on change type
    if deletions > additions * 1.5:
        # More deletions - red tones
        base_color = np.array([231, 76, 60]) / 255.0  # Red
    elif additions > deletions * 1.5:
        # More additions - green tones
        base_color = np.array([39, 174, 96]) / 255.0  # Green
    else:
        # Balanced - blue tones
        base_color = np.array([52, 152, 219]) / 255.0  # Blue
    
    # Mix with white based on intensity (lighter = less intense)
    white = np.array([1.0, 1.0, 1.0])
    color = base_color * intensity + white * (1 - intensity)
    
    return color


def truncate_filename(filename, max_length=20):
    """Truncate filename for display"""
    if len(filename) <= max_length:
        return filename
    
    # Try to keep extension
    name = Path(filename).stem
    ext = Path(filename).suffix
    
    if len(ext) > 5:
        ext = ''
    
    max_name_length = max_length - len(ext) - 3  # Account for '...' and extension
    if max_name_length < 3:
        return filename[:max_length-3] + '...'
    
    return name[:max_name_length] + '...' + ext


def generate_code_change_heatmap(file_changes):
    """Generate the heat map visualization"""
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib not available, cannot generate heat map")
        return None
    
    if not file_changes:
        print("No file changes to visualize")
        return None
    
    num_files = len(file_changes)
    rows, cols = calculate_grid_dimensions(num_files)
    
    # Calculate max changes for normalization
    max_changes = max(f['total'] for f in file_changes) if file_changes else 1
    
    # Create figure with appropriate size
    cell_size = 1.5
    fig_width = max(12, cols * cell_size)
    fig_height = max(8, rows * cell_size + 2)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Title
    ax.text(0.5, 0.98, f'PR Code Change Heat Map ({num_files} files)', 
            transform=ax.transAxes, ha='center', va='top',
            fontsize=18, fontweight='bold', color='#2C3E50')
    
    # Add legend
    legend_y = 0.93
    ax.text(0.1, legend_y, '● More Additions', transform=ax.transAxes,
            ha='left', va='center', fontsize=10, color='#27AE60')
    ax.text(0.3, legend_y, '● More Deletions', transform=ax.transAxes,
            ha='left', va='center', fontsize=10, color='#E74C3C')
    ax.text(0.5, legend_y, '● Balanced Changes', transform=ax.transAxes,
            ha='left', va='center', fontsize=10, color='#3498DB')
    ax.text(0.7, legend_y, f'Max Changes: {max_changes} lines', transform=ax.transAxes,
            ha='left', va='center', fontsize=10, color='#2C3E50', fontstyle='italic')
    
    # Draw grid cells
    for idx, file_data in enumerate(file_changes):
        row = idx // cols
        col = idx % cols
        
        additions = file_data['additions']
        deletions = file_data['deletions']
        total = file_data['total']
        filename = file_data['file']
        
        # Get color for this cell
        color = get_change_color(additions, deletions, max_changes)
        
        # Draw cell rectangle
        x = col
        y = rows - row - 1  # Flip y-axis so first file is top-left
        
        rect = patches.Rectangle((x, y), 1, 1, 
                                facecolor=color, 
                                edgecolor='#BDC3C7', 
                                linewidth=1)
        ax.add_patch(rect)
        
        # Add filename (truncated)
        display_name = truncate_filename(Path(filename).name, max_length=15)
        ax.text(x + 0.5, y + 0.7, display_name, 
               ha='center', va='center',
               fontsize=8, fontweight='bold', color='#2C3E50',
               wrap=True)
        
        # Add change statistics
        change_text = f'+{additions} -{deletions}'
        ax.text(x + 0.5, y + 0.3, change_text,
               ha='center', va='center',
               fontsize=7, color='#34495E')
    
    # Set axis limits and remove ticks
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Adjust layout to prevent clipping
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.02, left=0.02, right=0.98)
    
    return fig


def save_heatmap_image(fig, filename='code_change_heatmap'):
    """Save the heat map image"""
    if fig is None:
        return None
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save PNG file
    png_path = OUTPUT_DIR / f"{filename}.png"
    
    # Use high DPI for better quality
    fig.savefig(
        png_path,
        dpi=100,
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none',
        pad_inches=0.2
    )
    
    size_kb = png_path.stat().st_size / 1024
    print(f"Generated heat map: {size_kb:.1f} KB")
    print(f"Saved to: {png_path}")
    
    plt.close(fig)
    
    return png_path


def generate_heatmap_metadata(file_changes):
    """Generate metadata about the heat map"""
    if not file_changes:
        return {}
    
    total_additions = sum(f['additions'] for f in file_changes)
    total_deletions = sum(f['deletions'] for f in file_changes)
    total_changes = sum(f['total'] for f in file_changes)
    
    # Calculate file type distribution
    file_types = {}
    for f in file_changes:
        ft = f['file_type']
        if ft not in file_types:
            file_types[ft] = 0
        file_types[ft] += 1
    
    # Find most changed file
    most_changed = max(file_changes, key=lambda x: x['total']) if file_changes else None
    
    metadata = {
        'total_files': len(file_changes),
        'total_additions': total_additions,
        'total_deletions': total_deletions,
        'total_changes': total_changes,
        'file_types': file_types,
        'most_changed_file': {
            'file': most_changed['file'],
            'changes': most_changed['total'],
            'additions': most_changed['additions'],
            'deletions': most_changed['deletions']
        } if most_changed else None
    }
    
    return metadata


def main():
    """Main function"""
    try:
        print("Starting PR Code Change Heat Map generation...")
        
        # Load file changes
        file_changes = load_diff_stats()
        
        if not file_changes:
            print("No file changes found, creating placeholder")
            # Create a minimal metadata file so the workflow doesn't fail
            metadata = {
                'total_files': 0,
                'total_additions': 0,
                'total_deletions': 0,
                'total_changes': 0,
                'error': 'No file changes detected'
            }
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_DIR / 'heatmap_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            return 0
        
        # Sort by total changes (most changed first)
        file_changes.sort(key=lambda x: x['total'], reverse=True)
        
        # Limit to top 50 files for readability
        if len(file_changes) > 50:
            print(f"Limiting to top 50 files (out of {len(file_changes)})")
            file_changes = file_changes[:50]
        
        # Generate heat map
        fig = generate_code_change_heatmap(file_changes)
        
        if fig:
            # Save heat map image
            save_heatmap_image(fig)
            
            # Generate and save metadata
            metadata = generate_heatmap_metadata(file_changes)
            metadata_path = OUTPUT_DIR / 'heatmap_metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Saved metadata to: {metadata_path}")
            
            print("Heat map generation completed successfully")
            return 0
        else:
            print("Failed to generate heat map")
            return 1
            
    except Exception as e:
        print(f"Error generating heat map: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
