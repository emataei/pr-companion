#!/usr/bin/env python3
"""
Fallback documentation suggestions generator - minimal version that always works
"""

import os
import json
from pathlib import Path

def main():
    """Generate minimal documentation suggestions"""
    print("Generating documentation suggestions (fallback mode)...")
    
    # Create outputs directory
    outputs_dir = Path(__file__).parent.parent / 'outputs'
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # Basic markdown content
    markdown_content = """## 📝 Documentation Update Suggestions

*Based on the changes in this PR, here are recommended documentation updates:*

### 💡 General Recommendations

**`README.md`** (✅ Check if exists)
- **Reason:** Standard documentation practices
- **Action:** Ensure README is up to date with any new features or changes

### 📊 Project Documentation Status

- **Analysis Method:** 📋 Rule-Based (Fallback)
- **Status:** ✅ Documentation suggestions generated successfully

### 💡 Tips

- Well-documented PRs are easier to review and maintain
- Consider updating documentation alongside code changes
- Check if any new features need documentation

---

*💡 This is a fallback analysis when full documentation analysis is not available.*
"""
    
    # Save markdown report
    report_path = outputs_dir / 'documentation_suggestions.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    # Save minimal JSON data
    results = {
        'project_info': {
            'project_type': 'unknown',
            'has_docs_folder': False,
            'readme_exists': Path('README.md').exists()
        },
        'file_categories': {},
        'suggestions': {
            'critical_updates': [],
            'recommended_updates': [],
            'new_documentation': [],
            'general_improvements': []
        },
        'changed_files': [],
        'total_files_changed': 0,
        'ai_powered': False,
        'fallback_mode': True
    }
    
    json_path = outputs_dir / 'documentation_analysis.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Documentation suggestions saved to: {report_path}")
    print(f"📊 Analysis data saved to: {json_path}")
    print("📋 Used fallback mode due to missing dependencies")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
