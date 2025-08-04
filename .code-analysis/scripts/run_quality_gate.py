#!/usr/bin/env python3
"""
Quality Gate Analysis Script for GitHub Actions.

This script analyzes changed files with the Quality Gate system
and outputs results for GitHub Actions workflows.
"""

import sys
import json
import os
from pathlib import Path

# Add .code-analysis to Python path (script is now inside .code-analysis/scripts/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.quality_gate import QualityGate


def analyze_changed_files(file_list):
    """Analyze changed files with quality gate."""
    if not file_list.strip():
        return {
            'passed': True,
            'score': 100,
            'penalty': 0,
            'blocking_issues': 0,
            'summary': 'No code changes detected',
            'issues': {
                'blocking': [],
                'warning': []
            }
        }
    
    # Parse file list (GitHub Actions passes space-separated files)
    changed_files = [f.strip() for f in file_list.split() if f.strip()]
    
    # Filter for code files and read content
    pr_files = []
    
    for file_path in changed_files:
        try:
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine language from extension
            ext = Path(file_path).suffix.lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.jsx': 'javascript',
                '.tsx': 'typescript',
                '.java': 'java',
                '.cs': 'csharp',
                '.go': 'go',
                '.rs': 'rust'
            }
            
            language = language_map.get(ext, 'unknown')
            
            pr_files.append({
                'path': file_path,
                'content': content,
                'language': language
            })
            
        except Exception:
            # Skip files that can't be read
            continue
    
    if not pr_files:
        return {
            'passed': True,
            'score': 100,
            'penalty': 0,
            'blocking_issues': 0,
            'summary': 'No valid code files to analyze',
            'issues': {
                'blocking': [],
                'warning': []
            }
        }

    # Run quality gate analysis with AI enabled
    # Set enable_ai=False to disable AI analysis for faster execution
    enable_ai = os.getenv('QUALITY_GATE_AI_ENABLED', 'true').lower() == 'true'
    
    quality_gate = QualityGate(enable_ai=enable_ai)
    result = quality_gate.analyze_pr(pr_files)
    
    # Get standards information for enhanced reporting
    standards_info = {}
    if enable_ai:
        try:
            standards = quality_gate.copilot_parser.get_standards()
            emphasis_areas = []
            if standards.error_handling_required:
                emphasis_areas.append('Error Handling')
            if standards.type_safety_emphasis:
                emphasis_areas.append('Type Safety')
            if standards.performance_focus:
                emphasis_areas.append('Performance')
            if standards.documentation_required:
                emphasis_areas.append('Documentation')
            if standards.testing_emphasis:
                emphasis_areas.append('Testing')
        
            standards_info = {
                'standards_applied': True,
                'emphasis_areas': emphasis_areas
            }
        except Exception:
            standards_info = {'standards_applied': False}
    else:
        standards_info = {'standards_applied': False}
    
    # Convert to format expected by GitHub Actions
    result_dict = {
        'passed': result.passed,
        'score': result.quality_score,
        'penalty': result.quality_penalty,
        'blocking_issues': len(result.blocking_issues),
        'summary': result.summary,
        'issues': {
            'blocking': [
                {
                    'category': issue.category,
                    'message': issue.message,
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'suggestion': issue.suggestion
                }
                for issue in result.blocking_issues
            ],
            'warning': [
                {
                    'category': issue.category,
                    'message': issue.message,
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'suggestion': issue.suggestion
                }
                for issue in result.warning_issues
            ]
        }
    }
    
    # Add standards information
    result_dict.update(standards_info)
    
    return result_dict


def main():
    """Main entry point for GitHub Actions."""
    try:
        changed_files = os.getenv('CHANGED_FILES', '')
        result = analyze_changed_files(changed_files)
        
        # Set outputs for GitHub Actions
        github_output = os.getenv('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"passed={str(result['passed']).lower()}\n")
                f.write(f"score={result['score']}\n")
                f.write(f"penalty={result['penalty']}\n")
                f.write(f"blocking_issues={result['blocking_issues']}\n")
        
        # Create detailed results file in outputs directory
        os.makedirs('.code-analysis/outputs', exist_ok=True)
        with open('.code-analysis/outputs/quality-gate-results.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        # Exit with error code if quality gate fails
        if not result['passed']:
            sys.exit(1)
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
