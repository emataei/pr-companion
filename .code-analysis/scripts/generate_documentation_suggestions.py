#!/usr/bin/env python3
"""
Generate documentation suggestions based on PR changes using Azure AI Foundry
"""

import os
import sys
import json
from pathlib import Path
import re
from collections import defaultdict
import subprocess

# Try to import git, but don't fail if it's not available
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("Warning: GitPython not available. Using fallback git commands.")

# Add the parent directory to the path to access shared modules
sys.path.append(str(Path(__file__).parent.parent / 'scoring'))

try:
    from ai_client_factory import AIClientFactory
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: AI client not available. Using rule-based analysis only.")

def load_changed_files():
    """Load the changed files from git diff"""
    try:
        if GIT_AVAILABLE:
            # Use GitPython if available
            repo = git.Repo('.')
            
            # Get base branch from environment or default to main
            base_branch = os.getenv('GITHUB_BASE_REF', 'main')
            head_branch = os.getenv('GITHUB_HEAD_REF', 'HEAD')
            
            # Get the diff
            try:
                base_commit = repo.commit(f'origin/{base_branch}')
                head_commit = repo.commit(head_branch)
                diff = base_commit.diff(head_commit)
                
                changed_files = []
                for item in diff:
                    if item.a_path:
                        changed_files.append(item.a_path)
                    if item.b_path and item.b_path not in changed_files:
                        changed_files.append(item.b_path)
                
                return changed_files
            except Exception:
                # Fall back to subprocess if branch names are problematic
                return load_changed_files_subprocess()
        else:
            # Use subprocess as fallback
            return load_changed_files_subprocess()
            
    except Exception as e:
        print(f"Warning: Could not load changed files from git: {e}")
        return []

def load_changed_files_subprocess():
    """Load changed files using subprocess git commands"""
    try:
        # Get base branch from environment or default to main
        base_branch = os.getenv('GITHUB_BASE_REF', 'main')
        
        # Use git diff to get changed files
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'origin/{base_branch}'],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return changed_files
        else:
            print(f"Git diff command failed: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"Warning: Subprocess git command failed: {e}")
        return []

def analyze_project_structure():
    """Analyze the project structure to understand documentation setup"""
    project_info = {
        'has_docs_folder': False,
        'docs_folder': None,
        'existing_docs': [],
        'project_type': 'unknown',
        'readme_exists': False,
        'package_json_exists': False
    }
    
    # Check for common documentation folders
    for docs_dir in ['docs', 'documentation', 'doc', 'wiki']:
        if Path(docs_dir).exists():
            project_info['has_docs_folder'] = True
            project_info['docs_folder'] = docs_dir
            
            # Find existing documentation files
            docs_path = Path(docs_dir)
            for file in docs_path.rglob('*.md'):
                project_info['existing_docs'].append(str(file))
            break
    
    # Check project type
    if Path('package.json').exists():
        project_info['project_type'] = 'javascript'
        project_info['package_json_exists'] = True
    elif Path('requirements.txt').exists() or Path('setup.py').exists():
        project_info['project_type'] = 'python'
    elif Path('Cargo.toml').exists():
        project_info['project_type'] = 'rust'
    elif Path('go.mod').exists():
        project_info['project_type'] = 'go'
    
    # Check for README
    for readme in ['README.md', 'README.rst', 'README.txt', 'readme.md']:
        if Path(readme).exists():
            project_info['readme_exists'] = True
            break
    
    return project_info

def categorize_changes(changed_files):
    """Categorize the changed files by type and purpose"""
    categories = {
        'api_changes': [],
        'ui_components': [],
        'configuration': [],
        'tests': [],
        'documentation': [],
        'dependencies': [],
        'workflows': [],
        'other': []
    }
    
    for file in changed_files:
        file_lower = file.lower()
        file_path = Path(file)
        
        # API changes
        if any(pattern in file_lower for pattern in ['api/', 'route', 'endpoint', 'controller']):
            categories['api_changes'].append(file)
        
        # UI Components
        elif any(pattern in file_lower for pattern in ['component', 'page', 'layout', '.tsx', '.jsx', '.vue']):
            categories['ui_components'].append(file)
        
        # Configuration
        elif any(pattern in file_lower for pattern in ['config', '.json', '.yml', '.yaml', '.toml', '.env']):
            categories['configuration'].append(file)
        
        # Tests
        elif any(pattern in file_lower for pattern in ['test', 'spec', '__tests__']):
            categories['tests'].append(file)
        
        # Documentation
        elif any(pattern in file_lower for pattern in ['.md', '.rst', '.txt', 'doc']):
            categories['documentation'].append(file)
        
        # Dependencies
        elif file_path.name in ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml']:
            categories['dependencies'].append(file)
        
        # Workflows
        elif '.github' in file:
            categories['workflows'].append(file)
        
        else:
            categories['other'].append(file)
    
    return categories

def generate_documentation_suggestions(project_info, file_categories):
    """Generate specific documentation suggestions based on changes"""
    suggestions = {
        'critical_updates': [],
        'recommended_updates': [],
        'new_documentation': [],
        'general_improvements': []
    }
    
    # Try AI-powered analysis first, fallback to rule-based
    if AI_AVAILABLE:
        ai_suggestions = generate_ai_documentation_suggestions(project_info, file_categories)
        if ai_suggestions:
            return ai_suggestions
    
    # Fallback to rule-based analysis
    return generate_rule_based_suggestions(project_info, file_categories)

def generate_ai_documentation_suggestions(project_info, file_categories):
    """Generate documentation suggestions using Azure AI Foundry"""
    try:
        # Validate AI configuration
        AIClientFactory.validate_config()
        ai_client = AIClientFactory.create_client()
        model_name = AIClientFactory.get_model_name()
        
        # Prepare context for AI
        context = {
            'project_info': project_info,
            'file_categories': file_categories,
            'changed_files': sum(len(files) for files in file_categories.values())
        }
        
        prompt = f"""You are a documentation expert analyzing a pull request. Based on the following changes, suggest specific documentation updates.

Project Context:
- Project Type: {project_info['project_type']}
- Has Documentation Folder: {project_info['has_docs_folder']}
- Documentation Folder: {project_info.get('docs_folder', 'None')}
- README Exists: {project_info['readme_exists']}
- Existing Docs: {len(project_info['existing_docs'])} files

File Changes by Category:
- API Changes: {len(file_categories['api_changes'])} files
- UI Components: {len(file_categories['ui_components'])} files
- Configuration: {len(file_categories['configuration'])} files
- Dependencies: {len(file_categories['dependencies'])} files
- Workflows: {len(file_categories['workflows'])} files
- Tests: {len(file_categories['tests'])} files
- Documentation: {len(file_categories['documentation'])} files

Changed Files:
{json.dumps(file_categories, indent=2)[:2000]}

Analyze these changes and provide documentation suggestions in this JSON format:
{{
  "critical_updates": [
    {{
      "file": "path/to/file.md",
      "reason": "Brief explanation why this is critical",
      "action": "Specific action to take",
      "priority": "high|medium|low",
      "estimated_effort": "low|medium|high"
    }}
  ],
  "recommended_updates": [...],
  "new_documentation": [...],
  "general_improvements": [...]
}}

Focus on:
1. API documentation needs based on endpoint changes
2. Component documentation for UI changes
3. Configuration documentation for setup changes
4. Installation instructions for dependency changes
5. Missing documentation structures

Respond with only valid JSON, no other text."""

        # Make AI request
        from azure.ai.inference.models import UserMessage
        messages = [UserMessage(prompt)]
        
        response = ai_client.complete(
            messages=messages,
            model=model_name,
            max_tokens=2000,
            temperature=0.3
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content.strip()
        
        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            ai_suggestions = json.loads(json_match.group())
            
            # Validate and enrich AI suggestions with file existence checks
            validated_suggestions = validate_ai_suggestions(ai_suggestions, project_info)
            return validated_suggestions
        else:
            print("Warning: Could not parse AI response as JSON, falling back to rule-based analysis")
            return None
            
    except Exception as e:
        print(f"AI documentation analysis failed: {e}, falling back to rule-based analysis")
        return None

def validate_ai_suggestions(ai_suggestions, project_info):
    """Validate and enrich AI suggestions with file existence checks"""
    validated = {
        'critical_updates': [],
        'recommended_updates': [],
        'new_documentation': [],
        'general_improvements': []
    }
    
    for category, suggestions in ai_suggestions.items():
        if category in validated:
            for suggestion in suggestions:
                if isinstance(suggestion, dict) and 'file' in suggestion:
                    # Add file existence check
                    suggestion['exists'] = Path(suggestion['file']).exists()
                    
                    # Add changes field if missing (for compatibility with rule-based format)
                    if 'changes' not in suggestion:
                        suggestion['changes'] = []
                    
                    validated[category].append(suggestion)
    
    return validated

def generate_rule_based_suggestions(project_info, file_categories):
    """Generate documentation suggestions using rule-based logic (fallback)"""
    suggestions = {
        'critical_updates': [],
        'recommended_updates': [],
        'new_documentation': [],
        'general_improvements': []
    }
    
    # API Changes - Critical documentation needs
    if file_categories['api_changes']:
        if project_info['has_docs_folder']:
            api_doc = f"{project_info['docs_folder']}/API.md"
            suggestions['critical_updates'].append({
                'file': api_doc,
                'reason': 'API endpoints have been modified',
                'changes': file_categories['api_changes'],
                'action': 'Update API documentation with new endpoints, parameters, and response formats',
                'exists': Path(api_doc).exists()
            })
        else:
            suggestions['new_documentation'].append({
                'file': 'docs/API.md',
                'reason': 'API changes detected but no API documentation found',
                'changes': file_categories['api_changes'],
                'action': 'Create API documentation describing endpoints, authentication, and usage examples'
            })
    
    # UI Component Changes
    if file_categories['ui_components']:
        if project_info['has_docs_folder']:
            ui_doc = f"{project_info['docs_folder']}/COMPONENTS.md"
            suggestions['recommended_updates'].append({
                'file': ui_doc,
                'reason': 'UI components have been modified',
                'changes': file_categories['ui_components'],
                'action': 'Update component documentation with new props, usage examples, and screenshots',
                'exists': Path(ui_doc).exists()
            })
        
        # Check if README needs updating for major UI changes
        if len(file_categories['ui_components']) > 3:
            suggestions['recommended_updates'].append({
                'file': 'README.md',
                'reason': 'Significant UI changes may affect user experience',
                'changes': file_categories['ui_components'],
                'action': 'Update README with new screenshots, usage instructions, or feature descriptions',
                'exists': project_info['readme_exists']
            })
    
    # Configuration Changes
    if file_categories['configuration']:
        config_doc = f"{project_info['docs_folder']}/CONFIGURATION.md" if project_info['has_docs_folder'] else 'docs/CONFIGURATION.md'
        suggestions['recommended_updates'].append({
            'file': config_doc,
            'reason': 'Configuration files have been modified',
            'changes': file_categories['configuration'],
            'action': 'Document new configuration options, environment variables, and setup requirements',
            'exists': Path(config_doc).exists() if project_info['has_docs_folder'] else False
        })
    
    # Dependency Changes
    if file_categories['dependencies']:
        suggestions['critical_updates'].append({
            'file': 'README.md',
            'reason': 'Dependencies have changed',
            'changes': file_categories['dependencies'],
            'action': 'Update installation instructions, system requirements, and dependency versions',
            'exists': project_info['readme_exists']
        })
    
    # Workflow Changes
    if file_categories['workflows']:
        ci_doc = f"{project_info['docs_folder']}/CI_CD.md" if project_info['has_docs_folder'] else 'docs/CI_CD.md'
        suggestions['recommended_updates'].append({
            'file': ci_doc,
            'reason': 'CI/CD workflows have been modified',
            'changes': file_categories['workflows'],
            'action': 'Update documentation about build processes, deployment, and development workflows',
            'exists': Path(ci_doc).exists() if project_info['has_docs_folder'] else False
        })
    
    # General improvements
    if not project_info['readme_exists']:
        suggestions['critical_updates'].append({
            'file': 'README.md',
            'reason': 'No README found',
            'changes': [],
            'action': 'Create a comprehensive README with project description, installation, and usage instructions',
            'exists': False
        })
    
    if not project_info['has_docs_folder'] and len(file_categories['api_changes'] + file_categories['ui_components']) > 2:
        suggestions['new_documentation'].append({
            'file': 'docs/',
            'reason': 'Significant changes but no documentation structure',
            'changes': [],
            'action': 'Create a docs folder with structured documentation for the project',
            'exists': False
        })
    
    return suggestions

def format_suggestions_markdown(suggestions, project_info, file_categories):
    """Format the suggestions as markdown for the PR comment"""
    
    content = "## 📝 Documentation Update Suggestions\n\n"
    
    # Check if suggestions were generated by AI
    ai_powered = any(
        'priority' in suggestion or 'estimated_effort' in suggestion
        for category in suggestions.values()
        for suggestion in (category if isinstance(category, list) else [])
        if isinstance(suggestion, dict)
    )
    
    if ai_powered and AI_AVAILABLE:
        content += "*AI-powered analysis of your PR changes with smart documentation recommendations:*\n\n"
    else:
        content += "*Based on the changes in this PR, here are recommended documentation updates:*\n\n"
    
    # Critical Updates
    if suggestions['critical_updates']:
        content += "### 🚨 Critical Updates Required\n\n"
        for suggestion in suggestions['critical_updates']:
            status = "✅ Exists" if suggestion.get('exists', False) else "❌ Missing"
            content += f"**`{suggestion['file']}`** ({status})\n"
            content += f"- **Reason:** {suggestion['reason']}\n"
            content += f"- **Action:** {suggestion['action']}\n"
            
            # Add AI-specific fields if available
            if 'priority' in suggestion:
                content += f"- **Priority:** {suggestion['priority'].title()}\n"
            if 'estimated_effort' in suggestion:
                content += f"- **Effort:** {suggestion['estimated_effort'].title()}\n"
            
            if suggestion.get('changes'):
                content += f"- **Related files:** {', '.join(f'`{f}`' for f in suggestion['changes'][:3])}"
                if len(suggestion['changes']) > 3:
                    content += f" *(+{len(suggestion['changes'])-3} more)*"
                content += "\n"
            content += "\n"
    
    # Recommended Updates
    if suggestions['recommended_updates']:
        content += "### 💡 Recommended Updates\n\n"
        for suggestion in suggestions['recommended_updates']:
            status = "✅ Exists" if suggestion.get('exists', False) else "📝 Create"
            content += f"**`{suggestion['file']}`** ({status})\n"
            content += f"- **Reason:** {suggestion['reason']}\n"
            content += f"- **Action:** {suggestion['action']}\n"
            
            # Add AI-specific fields if available
            if 'priority' in suggestion:
                content += f"- **Priority:** {suggestion['priority'].title()}\n"
            if 'estimated_effort' in suggestion:
                content += f"- **Effort:** {suggestion['estimated_effort'].title()}\n"
            
            if suggestion.get('changes'):
                content += f"- **Related files:** {', '.join(f'`{f}`' for f in suggestion['changes'][:3])}"
                if len(suggestion['changes']) > 3:
                    content += f" *(+{len(suggestion['changes'])-3} more)*"
                content += "\n"
            content += "\n"
    
    # New Documentation
    if suggestions['new_documentation']:
        content += "### 📄 New Documentation Needed\n\n"
        for suggestion in suggestions['new_documentation']:
            content += f"**`{suggestion['file']}`**\n"
            content += f"- **Reason:** {suggestion['reason']}\n"
            content += f"- **Action:** {suggestion['action']}\n"
            
            # Add AI-specific fields if available
            if 'priority' in suggestion:
                content += f"- **Priority:** {suggestion['priority'].title()}\n"
            if 'estimated_effort' in suggestion:
                content += f"- **Effort:** {suggestion['estimated_effort'].title()}\n"
            
            if suggestion.get('changes'):
                content += f"- **Related files:** {', '.join(f'`{f}`' for f in suggestion['changes'][:3])}"
                if len(suggestion['changes']) > 3:
                    content += f" *(+{len(suggestion['changes'])-3} more)*"
                content += "\n"
            content += "\n"
    
    # Project Structure Info
    content += "### 📊 Project Documentation Status\n\n"
    content += f"- **Documentation Folder:** {'✅ ' + project_info['docs_folder'] if project_info['has_docs_folder'] else '❌ None'}\n"
    content += f"- **README:** {'✅ Exists' if project_info['readme_exists'] else '❌ Missing'}\n"
    content += f"- **Project Type:** {project_info['project_type'].title()}\n"
    content += f"- **Existing Docs:** {len(project_info['existing_docs'])} files\n"
    content += f"- **Analysis Method:** {'🤖 AI-Powered' if ai_powered and AI_AVAILABLE else '📋 Rule-Based'}\n\n"
    
    if project_info['existing_docs']:
        content += "<details>\n<summary>📚 Existing Documentation Files</summary>\n\n"
        for doc in sorted(project_info['existing_docs'])[:10]:  # Show first 10
            content += f"- `{doc}`\n"
        if len(project_info['existing_docs']) > 10:
            content += f"- *...and {len(project_info['existing_docs'])-10} more*\n"
        content += "\n</details>\n\n"
    
    # Change Summary
    total_changes = sum(len(files) for files in file_categories.values())
    content += "### 📈 Change Summary\n\n"
    content += f"**{total_changes} files changed** across these categories:\n\n"
    
    for category, files in file_categories.items():
        if files:
            emoji = {
                'api_changes': '🔌',
                'ui_components': '🎨',
                'configuration': '⚙️',
                'tests': '🧪',
                'documentation': '📝',
                'dependencies': '📦',
                'workflows': '🔄',
                'other': '📁'
            }.get(category, '📄')
            
            category_name = category.replace('_', ' ').title()
            content += f"- {emoji} **{category_name}:** {len(files)} files\n"
    
    content += "\n---\n\n"
    
    if ai_powered and AI_AVAILABLE:
        content += "*🤖 **AI-Powered Analysis:** These suggestions were generated using Azure AI Foundry to provide contextual, intelligent documentation recommendations based on your specific changes.*\n"
    else:
        content += "*💡 **Tip:** Well-documented PRs are easier to review and maintain! Consider updating documentation alongside code changes.*\n"
    
    return content

def main():
    """Main function to run documentation analysis"""
    print("Generating documentation suggestions...")
    
    # Check AI availability
    if AI_AVAILABLE:
        try:
            AIClientFactory.validate_config()
            print("🤖 AI-powered analysis enabled (Azure AI Foundry)")
        except Exception as e:
            print(f"⚠️ AI configuration issue: {e}")
            print("📋 Falling back to rule-based analysis")
    else:
        print("📋 Using rule-based analysis (AI dependencies not available)")
    
    # Create outputs directory
    outputs_dir = Path(__file__).parent.parent / 'outputs'
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Analyze the changes
        changed_files = load_changed_files()
        project_info = analyze_project_structure()
        file_categories = categorize_changes(changed_files)
        suggestions = generate_documentation_suggestions(project_info, file_categories)
        
        # Generate the markdown report
        markdown_content = format_suggestions_markdown(suggestions, project_info, file_categories)
        
        # Save results
        report_path = outputs_dir / 'documentation_suggestions.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Save JSON data for other scripts
        results = {
            'project_info': project_info,
            'file_categories': file_categories,
            'suggestions': suggestions,
            'changed_files': changed_files,
            'total_files_changed': len(changed_files),
            'ai_powered': AI_AVAILABLE and any(
                'priority' in suggestion or 'estimated_effort' in suggestion
                for category in suggestions.values()
                for suggestion in (category if isinstance(category, list) else [])
                if isinstance(suggestion, dict)
            )
        }
        
        json_path = outputs_dir / 'documentation_analysis.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        analysis_method = "AI-powered" if results['ai_powered'] else "rule-based"
        print(f"✅ Documentation suggestions saved to: {report_path}")
        print(f"📊 Analysis data saved to: {json_path}")
        print(f"🔍 Found {len(changed_files)} changed files")
        print(f"📝 Generated {len(suggestions['critical_updates']) + len(suggestions['recommended_updates']) + len(suggestions['new_documentation'])} documentation suggestions ({analysis_method})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating documentation suggestions: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
