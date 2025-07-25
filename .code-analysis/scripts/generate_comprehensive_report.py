#!/usr/bin/env python3
"""
Generate Comprehensive Report for Enhanced PR Visuals
Combines all analysis results into a single markdown report
"""

import json
import os
import sys
from pathlib import Path


def load_json_file(file_path, default=None):
    """Load JSON file with fallback to default"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default or {}


def load_markdown_file(file_path, default=""):
    """Load markdown file with fallback to default"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return default


def categorize_changed_files():
    """Categorize changed files by type"""
    diff_file = '.code-analysis/outputs/diff_stats.txt'
    if not Path(diff_file).exists():
        return {}
    
    categories = {
        'Source Code': [],
        'Configuration': [],
        'Documentation': [],
        'Tests': [],
        'Other': []
    }
    
    with open(diff_file, 'r') as f:
        for line in f.readlines()[:30]:  # Show first 30 files
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                added, deleted, file_path = parts
                
                # Categorize file
                category = _determine_file_category(file_path)
                categories[category].append((file_path, added, deleted))
    
    return categories


def _determine_file_category(file_path):
    """Determine the category of a file based on its path and extension"""
    path_lower = file_path.lower()
    
    if any(ext in path_lower for ext in ['.js', '.ts', '.jsx', '.tsx', '.vue', '.svelte']):
        return 'Source Code'
    elif any(ext in path_lower for ext in ['.json', '.yml', '.yaml', '.config', '.env']):
        return 'Configuration'
    elif any(ext in path_lower for ext in ['.md', '.txt', '.rst', '.doc']):
        return 'Documentation'
    elif any(term in path_lower for term in ['test', 'spec', '__tests__']):
        return 'Tests'
    else:
        return 'Other'


def format_file_change(file_path, added, deleted):
    """Format a file change entry"""
    if added != '-' and deleted != '-':
        return f"- `{file_path}` (+{added}/-{deleted})"
    else:
        return f"- `{file_path}` (binary or renamed)"


# Constants
SECTION_SEPARATOR = "---\n\n"


def _add_project_structure_section(report_parts, project_structure):
    """Add project structure analysis section"""
    project_dir = project_structure.get('project_dir', '.')
    project_type = project_structure.get('project_type', 'generic')
    source_dirs = project_structure.get('source_dirs', [])
    
    report_parts.append("## 🏗️ Project Structure Analysis\n")
    report_parts.append("**Detected Configuration:**\n")
    report_parts.append(f"- **Project Type:** {project_type.title()}\n")
    report_parts.append(f"- **Root Directory:** `{project_dir}`\n")
    
    if source_dirs:
        source_list = ', '.join([f'`{d}`' for d in source_dirs])
        report_parts.append(f"- **Source Directories:** {source_list}\n")
    else:
        report_parts.append("- **Source Directories:** Auto-detected\n")
    
    report_parts.append(f"\n{SECTION_SEPARATOR}")


def _add_dependency_analysis_section(report_parts, dependency_results):
    """Add dependency analysis section"""
    report_parts.append("## 🗺️ Dependency Analysis\n\n")
    
    if dependency_results.get('base_graph_generated') or dependency_results.get('pr_graph_generated'):
        report_parts.append("### Base Branch Dependencies\n")
        report_parts.append("![Base Dependencies](dependency_graph_base.png)\n\n")
        
        report_parts.append("### PR Branch Dependencies\n")
        report_parts.append("![PR Dependencies](dependency_graph_pr.png)\n\n")
        
        report_parts.append("> **Note:** Dependency graphs show module relationships within the detected source directories.\n")
    else:
        report_parts.append("*Dependency analysis not available for this project type.*\n\n")
    
    report_parts.append(SECTION_SEPARATOR)


def _add_change_heatmap_section(report_parts, change_stats):
    """Add change heatmap section"""
    report_parts.append("## 🔥 Change Heatmap\n\n")
    report_parts.append("![Change Heatmap](change_heatmap.png)\n\n")
    
    if change_stats:
        total_files = change_stats.get('total_files', 0)
        total_changes = change_stats.get('total_changes', 0)
        total_additions = change_stats.get('total_additions', 0)
        total_deletions = change_stats.get('total_deletions', 0)
        
        report_parts.append(f"**Summary:** {total_files} files changed, ")
        report_parts.append(f"{total_changes} total lines (+{total_additions}/-{total_deletions})\n\n")
    
    report_parts.append(SECTION_SEPARATOR)


def _add_files_analysis_section(report_parts):
    """Add files analysis section"""
    report_parts.append("## 🔍 Files Analysis\n\n")
    
    categorized_files = categorize_changed_files()
    if any(categorized_files.values()):
        report_parts.append("### Changed Files by Category:\n\n")
        
        for category, files in categorized_files.items():
            if files:
                report_parts.append(f"**{category}:**\n")
                for file_path, added, deleted in files:
                    report_parts.append(format_file_change(file_path, added, deleted) + "\n")
                report_parts.append("\n")
    else:
        report_parts.append("*No file changes detected or analysis failed.*\n\n")
    
    report_parts.append(SECTION_SEPARATOR)


def _add_generation_details_section(report_parts, project_structure):
    """Add generation details section"""
    project_dir = project_structure.get('project_dir', '.')
    project_type = project_structure.get('project_type', 'generic')
    source_dirs = project_structure.get('source_dirs', [])
    
    report_parts.append("<details>\n")
    report_parts.append("<summary>🤖 How This Analysis Was Generated</summary>\n\n")
    report_parts.append("This PR analysis includes:\n")
    report_parts.append("- **Auto-Detection**: Automatically discovered ")
    report_parts.append(f"{project_type} project structure\n")
    report_parts.append("- **Dependency Graphs**: Visual representation of module relationships before/after changes\n")
    report_parts.append("- **Change Heatmap**: Statistical breakdown of modifications by file, directory, and type\n")
    report_parts.append("- **Animated Summary**: Progressive reveal of PR impact and complexity\n")
    report_parts.append("- **Smart Categorization**: Files organized by type and purpose\n")
    report_parts.append("- **Portable Design**: Works with any repository structure\n\n")
    
    report_parts.append("**Project Detection Results:**\n")
    report_parts.append(f"- Root: `{project_dir}`\n")
    report_parts.append(f"- Type: {project_type}\n")
    
    if source_dirs:
        source_display = ', '.join(source_dirs)
        report_parts.append(f"- Sources: {source_display}\n")
    else:
        report_parts.append("- Sources: auto-detected\n")
    
    report_parts.append("\nGenerated automatically by the Enhanced PR Visuals workflow.\n")
    report_parts.append("</details>\n")


def _save_report_metadata(project_structure, animated_summary, change_stats, dependency_results, report_parts):
    """Save metadata about the generated report"""
    report_metadata = {
        'project_structure': project_structure,
        'has_animated_summary': bool(animated_summary),
        'has_change_stats': bool(change_stats),
        'has_dependency_results': bool(dependency_results),
        'total_sections': len([p for p in report_parts if p.startswith('##')]),
        'generated_files': [
            'comprehensive_pr_report.md',
            'animated_summary.md' if animated_summary else None,
            'change_heatmap.png',
            'dependency_graph_base.png' if dependency_results.get('base_graph_generated') else None,
            'dependency_graph_pr.png' if dependency_results.get('pr_graph_generated') else None
        ]
    }
    
    # Remove None values
    report_metadata['generated_files'] = [f for f in report_metadata['generated_files'] if f]
    
    with open('.code-analysis/outputs/enhanced_visuals_results.json', 'w') as f:
        json.dump(report_metadata, f, indent=2)
    
    return report_metadata


def generate_comprehensive_report():
    """Generate the comprehensive PR report"""
    print("Generating comprehensive report...")
    
    # Load all analysis results
    project_structure = load_json_file('.code-analysis/outputs/project_structure.json')
    animated_summary = load_markdown_file('.code-analysis/outputs/animated_summary.md')
    change_stats = load_json_file('.code-analysis/outputs/change_heatmap_results.json')
    dependency_results = load_json_file('.code-analysis/outputs/dependency_graphs_results.json')
    
    # Start building the report
    report_parts = []
    
    # Add animated summary if available
    if animated_summary:
        report_parts.append(animated_summary)
        report_parts.append(f"\n{SECTION_SEPARATOR}")
    
    # Add all sections
    _add_project_structure_section(report_parts, project_structure)
    _add_dependency_analysis_section(report_parts, dependency_results)
    _add_change_heatmap_section(report_parts, change_stats)
    _add_files_analysis_section(report_parts)
    _add_generation_details_section(report_parts, project_structure)
    
    # Combine all parts and save
    comprehensive_report = ''.join(report_parts)
    
    os.makedirs('.code-analysis/outputs', exist_ok=True)
    with open('.code-analysis/outputs/comprehensive_pr_report.md', 'w', encoding='utf-8') as f:
        f.write(comprehensive_report)
    
    # Save metadata
    report_metadata = _save_report_metadata(
        project_structure, animated_summary, change_stats, dependency_results, report_parts
    )
    
    project_type = project_structure.get('project_type', 'generic')
    project_dir = project_structure.get('project_dir', '.')
    
    print("Comprehensive report generated")
    print(f"Project structure: {project_type} at {project_dir}")
    print(f"Report sections: {report_metadata['total_sections']}")
    print(f"Generated files: {len(report_metadata['generated_files'])}")
    
    return True


def main():
    """Main comprehensive report generation logic"""
    print("Starting comprehensive report generation...")
    
    success = generate_comprehensive_report()
    
    print("Comprehensive report generation complete!")
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
