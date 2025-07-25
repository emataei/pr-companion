#!/usr/bin/env python3
"""
GitHub Pages Cleanup Script
Removes old PR visual directories to keep the site manageable
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta

def cleanup_old_pr_visuals(keep_recent_days=30, max_prs_to_keep=50):
    """
    Clean up old PR visual directories
    
    Args:
        keep_recent_days: Keep PRs from the last N days
        max_prs_to_keep: Maximum number of PR directories to keep
    """
    
    gh_pages_pr_dir = Path("gh-pages/pr")
    
    if not gh_pages_pr_dir.exists():
        print("No gh-pages/pr directory found, nothing to clean up")
        return
    
    # Get all PR directories
    pr_dirs = []
    for item in gh_pages_pr_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
            pr_dirs.append({
                'path': item,
                'pr_number': int(item.name),
                'modified_time': item.stat().st_mtime
            })
    
    if not pr_dirs:
        print("No PR directories found")
        return
    
    # Sort by modification time (newest first)
    pr_dirs.sort(key=lambda x: x['modified_time'], reverse=True)
    
    print(f"Found {len(pr_dirs)} PR visual directories")
    
    # Calculate cutoff time
    cutoff_time = (datetime.now() - timedelta(days=keep_recent_days)).timestamp()
    
    # Determine which directories to remove
    dirs_to_remove = []
    
    # Keep recent directories (by time)
    recent_dirs = [pr for pr in pr_dirs if pr['modified_time'] > cutoff_time]
    
    # If we still have too many, keep only the most recent ones
    if len(recent_dirs) > max_prs_to_keep:
        dirs_to_keep = recent_dirs[:max_prs_to_keep]
        dirs_to_remove.extend(recent_dirs[max_prs_to_keep:])
    else:
        dirs_to_keep = recent_dirs
    
    # Add old directories to removal list
    old_dirs = [pr for pr in pr_dirs if pr['modified_time'] <= cutoff_time]
    dirs_to_remove.extend(old_dirs)
    
    # Remove directories
    removed_count = 0
    for pr_dir in dirs_to_remove:
        try:
            print(f"Removing old PR visual directory: pr/{pr_dir['pr_number']}")
            shutil.rmtree(pr_dir['path'])
            removed_count += 1
        except Exception as e:
            print(f"Error removing directory pr/{pr_dir['pr_number']}: {e}")
    
    kept_prs = [pr['pr_number'] for pr in dirs_to_keep]
    print(f"✅ Cleanup complete:")
    print(f"   - Removed: {removed_count} old PR visual directories")
    print(f"   - Kept: {len(kept_prs)} recent directories")
    print(f"   - Kept PRs: {sorted(kept_prs, reverse=True)[:10]}{'...' if len(kept_prs) > 10 else ''}")
    
    # Update the main index with recent PRs (could be enhanced later)
    update_main_index(kept_prs[:10])  # Show top 10 recent PRs

def update_main_index(recent_prs):
    """Update the main index.html with recent PR links"""
    
    if not recent_prs:
        return
    
    # Read the current index
    index_path = "gh-pages/index.html"
    if not os.path.exists(index_path):
        return
    
    with open(index_path, 'r') as f:
        content = f.read()
    
    # Create PR cards HTML
    pr_cards_html = ""
    for pr_num in sorted(recent_prs, reverse=True):
        pr_cards_html += f'''
        <div class="pr-card">
            <div class="pr-number">PR #{pr_num}</div>
            <p>Visual analysis for Pull Request #{pr_num}</p>
            <a href="pr/{pr_num}/" style="color: #0366d6; text-decoration: none;">View Analysis →</a>
        </div>'''
    
    if pr_cards_html:
        # Replace the no-prs div with actual PR cards
        updated_content = content.replace(
            '<div class="no-prs">\n            No PR analysis available yet. PR visuals will appear here once generated.\n        </div>',
            f'<div class="pr-grid">{pr_cards_html}\n        </div>'
        )
        
        with open(index_path, 'w') as f:
            f.write(updated_content)
        
        print(f"📄 Updated main index with {len(recent_prs)} recent PRs")

if __name__ == "__main__":
    import sys
    
    # Allow configuration via environment variables
    keep_days = int(os.environ.get('CLEANUP_KEEP_DAYS', '30'))
    max_prs = int(os.environ.get('CLEANUP_MAX_PRS', '50'))
    
    print(f"Starting GitHub Pages cleanup (keep {keep_days} days, max {max_prs} PRs)")
    cleanup_old_pr_visuals(keep_days, max_prs)
