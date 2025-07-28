#!/usr/bin/env python3
"""
Generate Context-Aware Documentation Suggestions
Analyzes actual diff content to provide meaningful suggestions
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path

def get_diff_context():
    """Get detailed diff information for context-aware analysis"""
    try:
        # Get the actual diff content
        result = subprocess.run(['git', 'diff', '--unified=3', 'HEAD~1', 'HEAD'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            return result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return ""

def analyze_api_changes(diff_content):
    """Analyze for new public APIs or interfaces"""
    suggestions = []
    if re.search(r'\+.*(?:export|public).*(?:interface|class|function|const).*\{', diff_content, re.MULTILINE):
        api_matches = re.findall(r'\+.*(?:export|public).*(?:interface|class|function|const)\s+(\w+)', diff_content)
        if api_matches:
            suggestions.append(f"`docs/API.md` - New public APIs added: {', '.join(set(api_matches[:3]))}")
    return suggestions

def analyze_config_changes(diff_content):
    """Analyze for meaningful configuration changes"""
    suggestions = []
    config_changes = re.findall(r'\+\s*["\']?(\w+)["\']?\s*:\s*["\']?([^,\n}]+)["\']?', diff_content)
    significant_config = [c for c in config_changes if not c[0].startswith('_') and len(c[1]) > 2]
    if significant_config and len(significant_config) >= 2:
        config_keys = [c[0] for c in significant_config[:3]]
        suggestions.append(f"`docs/CONFIGURATION.md` - New config options: {', '.join(config_keys)}")
    return suggestions

def analyze_breaking_changes(diff_content):
    """Analyze for breaking changes"""
    suggestions = []
    if re.search(r'^-.*(?:export|public).*(?:function|class|const)', diff_content, re.MULTILINE):
        suggestions.append("`docs/BREAKING_CHANGES.md` - Removed public APIs detected")
    return suggestions

def analyze_diff_content(diff_content):
    """Analyze diff content for meaningful changes that require documentation"""
    if not diff_content:
        return []
    
    suggestions = []
    
    # Combine all analysis functions
    suggestions.extend(analyze_api_changes(diff_content))
    suggestions.extend(analyze_config_changes(diff_content))
    suggestions.extend(analyze_breaking_changes(diff_content))
    
    # Database/Schema changes
    if re.search(r'\+.*(?:CREATE TABLE|ALTER TABLE|ADD COLUMN|DROP COLUMN)', diff_content, re.IGNORECASE):
        suggestions.append("`docs/DATABASE.md` - Database schema changes detected")
    
    # Environment variable changes
    env_vars = re.findall(r'\+.*(?:process\.env\.|getenv\(|ENV\[)["\'](\w+)["\']', diff_content)
    if env_vars:
        suggestions.append(f"`docs/SETUP.md` - New environment variables: {', '.join(set(env_vars[:3]))}")
    
    # New dependencies
    if '"dependencies"' in diff_content or '"devDependencies"' in diff_content:
        new_deps = re.findall(r'\+\s*"([^"]+)":\s*"[^"]+"', diff_content)
        if new_deps:
            suggestions.append(f"`docs/DEPENDENCIES.md` - New dependencies: {', '.join(new_deps[:3])}")
    
    return suggestions

def generate_concise_docs():
    """Generate context-aware documentation suggestions"""
    
    # Get changed files for basic info
    changed_files_str = os.getenv('CHANGED_FILES', '')
    if not changed_files_str:
        changed_files_str = os.getenv('GITHUB_CHANGED_FILES', '')
    
    changed_files = []
    if changed_files_str:
        try:
            changed_files = json.loads(changed_files_str)
        except (json.JSONDecodeError, TypeError):
            changed_files = changed_files_str.split()
    
    # Fallback to git diff for file list
    if not changed_files:
        try:
            result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode == 0:
                changed_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    
    if not changed_files:
        return "## Documentation Update Suggestions\n\n**No documentation updates needed** - No file changes detected.\n\n"
    
    # Get diff content for context analysis
    diff_content = get_diff_context()
    
    # Analyze diff for meaningful changes
    suggestions = analyze_diff_content(diff_content)
    
    # Build output
    content = "## Documentation Update Suggestions\n\n"
    
    if not suggestions:
        # Only show this if there are actual code files (not just docs/config touched)
        code_files = [f for f in changed_files if any(f.endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.cpp', '.c'])]
        if code_files:
            content += "**No documentation updates needed** - Changes appear to be internal implementation details.\n\n"
        else:
            content += "**No documentation updates needed** - Only non-code files modified.\n\n"
    else:
        content += f"**{len(suggestions)} documentation updates recommended**\n\n"
        for suggestion in suggestions:
            content += f"- {suggestion}\n"
        content += "\n"
    
    # Contextual summary
    file_count = len(changed_files)
    code_files = [f for f in changed_files if any(f.endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs'])]
    
    if code_files:
        content += f"**{file_count} files changed** ({len(code_files)} code files) - Analyzed diff content for documentation impact.\n\n"
    else:
        content += f"**{file_count} files changed** (config/docs only) - No API documentation impact expected.\n\n"
    
    return content

def main():
    """Main function"""
    try:
        # Ensure output directory exists
        output_dir = Path(__file__).parent.parent / 'outputs'  # .code-analysis/outputs
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate concise documentation suggestions
        content = generate_concise_docs()
        
        # Write to output file
        output_file = output_dir / 'documentation_suggestions.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Concise documentation suggestions written to {output_file}")
        
    except Exception as e:
        print(f"Error generating documentation suggestions: {e}")
        
        # Create fallback content
        fallback_content = """## Documentation Update Suggestions

**Unable to analyze changes** - Check if documentation needs updates manually.

"""
        
        output_file = Path(__file__).parent.parent / 'outputs' / 'documentation_suggestions.md'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fallback_content)

if __name__ == "__main__":
    main()
