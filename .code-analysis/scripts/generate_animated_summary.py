#!/usr/bin/env python3
"""
Generate Animated Summary for Enhanced PR Visuals
Creates progressive reveal markdown with project-specific insights
"""

import json
import os
import sys
from pathlib import Path


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


def load_change_stats():
    """Load change statistics from diff file"""
    diff_file = '.code-analysis/outputs/diff_stats.txt'
    if not Path(diff_file).exists():
        return 0, 0
    
    return _parse_diff_stats(diff_file)


def _parse_diff_stats(diff_file):
    """Parse diff statistics from file"""
    total_files = 0
    total_changes = 0
    
    with open(diff_file, 'r') as f:
        for line in f:
            file_changes = _parse_diff_line(line.strip())
            if file_changes > 0:
                total_files += 1
                total_changes += file_changes
    
    return total_files, total_changes


def _parse_diff_line(line):
    """Parse a single diff line and return total changes"""
    parts = line.split('\t')
    if len(parts) < 3:
        return 0
    
    added, deleted = parts[0], parts[1]
    try:
        added_int = int(added) if added != '-' else 0
        deleted_int = int(deleted) if deleted != '-' else 0
        return added_int + deleted_int
    except ValueError:
        return 0


def get_project_emoji(project_type):
    """Get text indicator for project type"""
    emoji_map = {
        'nextjs': 'Next.js',
        'react': 'React',
        'vue': 'Vue',
        'angular': 'Angular',
        'vite': 'Vite',
        'svelte': 'Svelte',
        'generic': 'Generic'
    }
    return emoji_map.get(project_type, 'Generic')


def get_complexity_level(total_changes, total_files):
    """Determine complexity level based on changes"""
    if total_changes > 500 or total_files > 15:
        return 'High', '45-60 min'
    elif total_changes > 100 or total_files > 8:
        return 'Medium', '15-30 min'
    else:
        return 'Low', '5-15 min'


def get_complexity_level_text(total_changes, total_files):
    """Determine complexity level for console output (no emojis)"""
    if total_changes > 500 or total_files > 15:
        return 'High', '45-60 min'
    elif total_changes > 100 or total_files > 8:
        return 'Medium', '15-30 min'
    else:
        return 'Low', '5-15 min'


def get_scope_level(total_files):
    """Determine scope level based on number of files"""
    if total_files > 10:
        return 'Broad'
    elif total_files > 5:
        return 'Medium'
    else:
        return 'Focused'


def get_scope_level_text(total_files):
    """Determine scope level for console output (no emojis)"""
    if total_files > 10:
        return 'Broad'
    elif total_files > 5:
        return 'Medium'
    else:
        return 'Focused'


def get_project_specific_insights(project_type):
    """Get insights specific to the detected project type"""
    insights = {
        'nextjs': """
## Next.js Specific Insights

- Check for App Router vs Pages Router changes
- Review any middleware or configuration updates  
- Verify SSR/SSG implications
- Consider impact on build performance
""",
        'react': """
## React Specific Insights

- Review component architecture changes
- Check for hook usage patterns
- Verify prop type consistency
- Consider state management implications
""",
        'vue': """
## Vue Specific Insights

- Review component composition changes
- Check for reactivity patterns
- Verify template syntax consistency
- Consider Vue 3 vs Vue 2 compatibility
""",
        'angular': """
## Angular Specific Insights

- Review module dependency changes
- Check for service injection patterns
- Verify TypeScript compatibility
- Consider change detection impact
""",
        'vite': """
## Vite Specific Insights

- Review build configuration changes
- Check for plugin compatibility
- Verify hot reload functionality
- Consider bundle optimization impact
""",
        'generic': """
## General Project Insights

- Review code organization changes
- Check for dependency updates
- Verify documentation consistency
- Consider testing coverage impact
"""
    }
    
    return insights.get(project_type, insights['generic'])


def generate_animated_summary():
    """Generate the animated summary markdown"""
    print("Generating animated summary...")
    
    # Load project data
    project_structure = load_project_structure()
    project_dir = project_structure['project_dir']
    project_type = project_structure['project_type']
    source_dirs = project_structure.get('source_dirs', [])
    
    # Load change statistics
    total_files, total_changes = load_change_stats()
    
    # Calculate metrics
    project_emoji = get_project_emoji(project_type)
    complexity, review_time = get_complexity_level(total_changes, total_files)
    scope = get_scope_level(total_files)
    source_display = ', '.join(source_dirs) if source_dirs else 'auto-detected'
    
    # Generate the animated summary
    animation_md = f"""# PR Animation Summary

## Change Progression

```
PR Impact Analysis for {project_emoji} {project_type.title()} Project
===============================================================
Files Changed: {total_files}
Total Lines: {total_changes}
Project Structure: {project_dir}
Project Type: {project_type.title()}
```

## Visual Story

> **Step 1:** Analyzing {project_type} codebase changes...
> 
> **Step 2:** Scanning directories: {source_display}
> 
> **Step 3:** Creating visual summaries...
> 
> **Step 4:** Ready for review!

## Quick Stats

- **Complexity:** {complexity}
- **Scope:** {scope}
- **Review Time:** {review_time}
- **Project Structure:** {'Well-organized' if len(source_dirs) > 1 else 'Simple'}

{get_project_specific_insights(project_type)}

## Review Checklist

Based on your {project_type} project, consider reviewing:

- [ ] **Code Quality:** Consistent with project patterns
- [ ] **Architecture:** Follows established structure
- [ ] **Performance:** No significant impact on build/runtime
- [ ] **Testing:** Adequate test coverage for changes
- [ ] **Documentation:** Updated where necessary

---

*Generated automatically • Project: {project_type} • Files: {total_files} • Changes: {total_changes} lines*
"""
    
    # Save the animated summary
    os.makedirs('.code-analysis/outputs', exist_ok=True)
    with open('.code-analysis/outputs/animated_summary.md', 'w', encoding='utf-8') as f:
        f.write(animation_md)
    
    # Save summary data for other scripts
    summary_data = {
        'total_files': total_files,
        'total_changes': total_changes,
        'complexity': complexity,
        'scope': scope,
        'review_time': review_time,
        'project_type': project_type,
        'project_dir': project_dir,
        'source_dirs': source_dirs
    }
    
    with open('.code-analysis/outputs/animated_summary_data.json', 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print("Animated summary generated")
    print(f"Project: {project_type} at {project_dir}")
    print(f"Sources: {source_display}")
    
    # Get text versions for console (no emojis)
    complexity_text, _ = get_complexity_level_text(total_changes, total_files)
    scope_text = get_scope_level_text(total_files)
    print(f"Impact: {complexity_text} complexity, {scope_text} scope")
    
    return True


def main():
    """Main animated summary generation logic"""
    print("Starting animated summary generation...")
    
    success = generate_animated_summary()
    
    print("Animated summary generation complete!")
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
