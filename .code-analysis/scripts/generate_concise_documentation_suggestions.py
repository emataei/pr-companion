#!/usr/bin/env python3
"""
Generate Concise Documentation Suggestions
Much shorter and to-the-point format
"""

import os
import sys
import json
from pathlib import Path

def generate_concise_docs():
    """Generate a concise documentation comment"""
    
    # Get changed files from environment
    changed_files_str = os.getenv('CHANGED_FILES', '[]')
    try:
        changed_files = json.loads(changed_files_str)
    except:
        changed_files = []
    
    if not changed_files:
        return "## 📝 Documentation Update Suggestions\n\n✅ **No files changed** - no documentation updates needed.\n\n"
    
    # Simple file categorization
    config_files = [f for f in changed_files if any(f.endswith(ext) for ext in ['.yml', '.yaml', '.json', '.env', '.config'])]
    component_files = [f for f in changed_files if any(f.endswith(ext) for ext in ['.tsx', '.jsx', '.vue', '.component.ts'])]
    api_files = [f for f in changed_files if 'api/' in f or 'routes/' in f]
    
    suggestions = []
    
    # Add suggestions based on file types
    if config_files:
        suggestions.append("📝 `docs/CONFIGURATION.md` - Configuration files modified")
    
    if component_files:
        suggestions.append("📝 `docs/COMPONENTS.md` - UI components updated") 
        
    if api_files:
        suggestions.append("📝 `docs/API.md` - API endpoints changed")
    
    # Build concise output
    content = "## 📝 Documentation Update Suggestions\n\n"
    
    if not suggestions:
        content += "✅ **No documentation updates needed**\n\n"
    else:
        content += f"💡 **{len(suggestions)} documentation updates recommended**\n\n"
        for suggestion in suggestions:
            content += f"{suggestion}\n"
        content += "\n"
    
    # Quick summary
    file_count = len(changed_files)
    content += f"📊 **{file_count} files changed** - Review if documentation needs updates.\n\n"
    
    return content

def main():
    """Main function"""
    try:
        # Ensure output directory exists
        output_dir = Path('.code-analysis/outputs')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate concise documentation suggestions
        content = generate_concise_docs()
        
        # Write to output file
        output_file = output_dir / 'documentation_suggestions.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Concise documentation suggestions written to {output_file}")
        
    except Exception as e:
        print(f"❌ Error generating documentation suggestions: {e}")
        
        # Create fallback
        fallback_content = """## 📝 Documentation Update Suggestions

⚠️ **Unable to analyze changes** - Check if documentation needs updates manually.

"""
        
        output_file = Path('.code-analysis/outputs/documentation_suggestions.md')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fallback_content)

if __name__ == "__main__":
    main()
