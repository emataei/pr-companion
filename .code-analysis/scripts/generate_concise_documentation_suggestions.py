#!/usr/bin/env python3
"""
Generate AI-Enhanced Documentation Suggestions
Analyzes actual code changes using AI to provide precise, actionable documentation recommendations
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path

# Add .code-analysis to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scoring.ai_client_factory import AIClientFactory
    AI_CLIENT_AVAILABLE = True
except ImportError:
    AI_CLIENT_AVAILABLE = False

def analyze_api_changes(diff_content):
    """Analyze for new public APIs or interfaces"""
    suggestions = []
    
    # Look for new exports (interfaces, functions, classes, constants)
    if re.search(r'\+.*export.*(?:interface|class|function|const|enum).*\{', diff_content, re.MULTILINE):
        api_matches = re.findall(r'\+.*export.*(?:interface|class|function|const|enum)\s+(\w+)', diff_content)
        if api_matches:
            unique_apis = list(set(api_matches[:5]))  # Limit to top 5
            suggestions.append(f"`docs/API.md` - New public APIs added: {', '.join(unique_apis)}")
    
    # Look for new component props (React/Vue)
    prop_changes = re.findall(r'\+\s*(\w+)\??\s*:\s*[^;,}]+', diff_content)
    react_props = [p for p in prop_changes if not p.startswith('_') and len(p) > 2]
    if react_props and any('Props' in diff_content or 'Component' in diff_content or '.tsx' in diff_content):
        unique_props = list(set(react_props[:3]))
        suggestions.append(f"`docs/COMPONENTS.md` - New component props: {', '.join(unique_props)}")
    
    # Look for new HTTP endpoints/routes
    endpoint_matches = re.findall(r'\+.*["\']/(api|v\d+)/([^"\']+)["\']', diff_content)
    if endpoint_matches:
        endpoints = [f"/{match[0]}/{match[1]}" for match in endpoint_matches[:3]]
        suggestions.append(f"`docs/API.md` - New endpoints: {', '.join(endpoints)}")
    
    return suggestions

def analyze_config_changes(diff_content):
    """Analyze for meaningful configuration changes"""
    suggestions = []
    
    # Look for environment variables
    env_vars = re.findall(r'\+.*(?:process\.env\.|getenv\(.*?)["\']([A-Z_][A-Z0-9_]*)["\']', diff_content)
    if env_vars:
        unique_vars = list(set(env_vars[:4]))
        suggestions.append(f"`docs/SETUP.md` - New environment variables: {', '.join(unique_vars)}")
    
    # Look for configuration object changes
    config_changes = re.findall(r'\+\s*["\']?(\w+)["\']?\s*:\s*["\']?([^,\n}]+)["\']?', diff_content)
    significant_config = [c for c in config_changes if not c[0].startswith('_') and len(c[1]) > 2 and c[0] not in ['name', 'version']]
    if significant_config and len(significant_config) >= 2:
        config_keys = [c[0] for c in significant_config[:3]]
        suggestions.append(f"`docs/CONFIGURATION.md` - New config options: {', '.join(config_keys)}")
    
    # Look for Docker/deployment configuration
    if re.search(r'\+.*(?:FROM|RUN|COPY|ENV).*', diff_content, re.IGNORECASE):
        suggestions.append("`docs/DEPLOYMENT.md` - Docker configuration changes detected")
    
    return suggestions

def analyze_breaking_changes(diff_content):
    """Analyze for breaking changes"""
    suggestions = []
    
    # Look for removed public exports
    if re.search(r'^-.*export.*(?:function|class|const|interface)', diff_content, re.MULTILINE):
        removed_items = re.findall(r'^-.*export.*(?:function|class|const|interface)\s+(\w+)', diff_content, re.MULTILINE)
        if removed_items:
            suggestions.append(f"`docs/BREAKING_CHANGES.md` - Removed public APIs: {', '.join(set(removed_items[:3]))}")
    
    # Look for changed function signatures
    if re.search(r'^-.*function.*\([^)]*\).*\n\+.*function.*\([^)]*\)', diff_content, re.MULTILINE):
        suggestions.append("`docs/BREAKING_CHANGES.md` - Function signature changes detected")
    
    # Look for removed component props
    if re.search(r'^-\s*\w+\??\s*:', diff_content, re.MULTILINE) and ('Props' in diff_content or '.tsx' in diff_content):
        suggestions.append("`docs/BREAKING_CHANGES.md` - Component prop changes detected")
    
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

class AIDocumentationAnalyzer:
    def __init__(self):
        self.ai_client = None
        self.model_name = None
        
        # Initialize AI client if available
        if AI_CLIENT_AVAILABLE:
            try:
                AIClientFactory.validate_config()
                self.ai_client = AIClientFactory.create_client()
                self.model_name = AIClientFactory.get_model_name()
            except Exception as e:
                print(f"Warning: AI client initialization failed: {e}")
                self.ai_client = None
    
    def get_changed_files(self):
        """Get list of changed files"""
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
        
        return changed_files
    
    def get_diff_content(self):
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
    
    def generate_ai_suggestions(self, changed_files, diff_content):
        """Generate AI-powered documentation suggestions with detailed analysis"""
        if not self.ai_client:
            return None
        
        # Limit diff content to avoid token limits
        truncated_diff = diff_content[:4000]  # Keep reasonable size for AI analysis
        file_list = ', '.join(changed_files[:15]) + ("..." if len(changed_files) > 15 else "")
        
        prompt = f"""
        You are a technical documentation specialist. Analyze these code changes and provide precise, actionable documentation recommendations.
        
        **Files changed ({len(changed_files)}):** {file_list}
        
        **Code changes:**
        ```diff
        {truncated_diff}
        ```
        
        **Task:** Generate specific documentation update recommendations based on the actual changes shown. Format your response as:
        
        ## Documentation Update Suggestions
        
        **[NUMBER] documentation updates recommended**
        
        For each recommendation, provide:
        • **File to update:** `docs/[specific-file].md`
        • **Why needed:** Brief explanation of what changed that requires documentation
        • **Specific content:** What should be documented (APIs, configs, breaking changes, etc.)
        • **Priority:** High/Medium/Low based on user impact
        
        **Analysis Guidelines:**
        • Focus on user-facing changes (new APIs, configuration options, breaking changes)
        • Ignore internal implementation details unless they affect usage
        • Be specific about what needs documenting, not just "update docs"
        • Consider different user types (developers, administrators, end-users)
        • Suggest new documentation files if needed for significant features
        
        **If no documentation needed:** Explain why (internal changes, test-only, etc.)
        
        Keep recommendations precise and actionable - each should tell someone exactly what to document and why.
        """
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert technical documentation specialist who helps teams maintain accurate, helpful documentation by analyzing code changes and recommending specific updates."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.ai_client.complete(
                messages=messages,
                model=self.model_name,
                temperature=0.2,  # Lower temperature for more consistent analysis
                max_tokens=1500   # Allow for detailed recommendations
            )
            
            ai_content = response.choices[0].message.content
            
            # Add metadata footer
            file_count = len(changed_files)
            code_files = [f for f in changed_files if any(f.endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs'])]
            
            ai_content += f"\n\n---\n*AI-analyzed {file_count} files ({len(code_files)} code files) for documentation impact*\n"
            
            return ai_content
            
        except Exception as e:
            print(f"AI analysis failed: {str(e)}")
            return None
    
    def generate_rule_based_suggestions(self, changed_files, diff_content):
        """Fallback rule-based analysis"""
        suggestions = analyze_diff_content(diff_content)
        
        content = "## Documentation Update Suggestions\n\n"
        
        if not suggestions:
            code_files = [f for f in changed_files if any(f.endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.cpp', '.c'])]
            if code_files:
                content += "**No documentation updates needed** - Changes appear to be internal implementation details.\n\n"
            else:
                content += "**No documentation updates needed** - Only non-code files modified.\n\n"
        else:
            content += f"**{len(suggestions)} documentation updates recommended**\n\n"
            for suggestion in suggestions:
                content += f"• {suggestion}\n"
            content += "\n"
        
        # Contextual summary
        file_count = len(changed_files)
        code_files = [f for f in changed_files if any(f.endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs'])]
        
        if code_files:
            content += f"**{file_count} files changed** ({len(code_files)} code files) - Analyzed diff content for documentation impact.\n\n"
        else:
            content += f"**{file_count} files changed** (config/docs only) - No API documentation impact expected.\n\n"
        
        return content
    
    def analyze(self):
        """Main analysis method"""
        changed_files = self.get_changed_files()
        
        if not changed_files:
            return "## Documentation Update Suggestions\n\n**No documentation updates needed** - No file changes detected.\n\n"
        
        diff_content = self.get_diff_content()
        
        # Try AI analysis first, fallback to rule-based
        if self.ai_client and diff_content:
            ai_result = self.generate_ai_suggestions(changed_files, diff_content)
            if ai_result:
                return ai_result
            else:
                print("AI analysis failed, falling back to rule-based")
        else:
            print("Using rule-based analysis (AI not available)")
        
        return self.generate_rule_based_suggestions(changed_files, diff_content)

def main():
    """Main function"""
    try:
        # Ensure output directory exists
        output_dir = Path(__file__).parent.parent / 'outputs'  # .code-analysis/outputs
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create analyzer and run analysis
        analyzer = AIDocumentationAnalyzer()
        content = analyzer.analyze()
        
        # Write to output file
        output_file = output_dir / 'documentation_suggestions.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"AI-enhanced documentation suggestions written to {output_file}")
        
    except Exception as e:
        print(f"Error generating documentation suggestions: {e}")
        
        # Create fallback content
        fallback_content = """## Documentation Update Suggestions

**Unable to analyze changes** - Check if documentation needs updates manually.

*AI analysis failed - using manual review recommended*

"""
        
        output_file = Path(__file__).parent.parent / 'outputs' / 'documentation_suggestions.md'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fallback_content)

if __name__ == "__main__":
    main()
