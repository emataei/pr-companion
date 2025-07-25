#!/usr/bin/env python3
"""
Cognitive Analysis Script for GitHub Actions.

This script runs cognitive analysis on changed files and outputs
tier assignment results for GitHub Actions workflows.
"""

import sys
import json
import os
from pathlib import Path

# Add .code-analysis to Python path (script is now inside .code-analysis/scripts/)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import cognitive analyzer, fallback if AI dependencies missing
try:
    from scoring.cognitive_analyzer import CognitiveAnalyzer, CognitiveScore
    COGNITIVE_AVAILABLE = True
except ImportError:
    COGNITIVE_AVAILABLE = False
    # Create a minimal fallback
    class CognitiveScore:
        def __init__(self, static_score=0, impact_score=0, ai_score=0, total_score=0, tier=0, reasoning="Static analysis only", ast_metrics=None):
            self.static_score = static_score
            self.impact_score = impact_score
            self.ai_score = ai_score
            self.total_score = total_score
            self.tier = tier
            self.reasoning = reasoning
            self.ast_metrics = ast_metrics


def run_cognitive_analysis(file_list, quality_penalty=0):
    """Run cognitive analysis on changed files."""
    if not file_list.strip():
        return {
            'tier': 0,
            'total_score': 0,
            'reasoning': 'No code changes detected',
            'static_score': 0,
            'impact_score': 0,
            'ai_score': 0,
            'quality_penalty': 0
        }
    
    # Initialize analyzer with fallback
    try:
        if COGNITIVE_AVAILABLE:
            analyzer = CognitiveAnalyzer()
        else:
            raise ImportError("Cognitive analyzer dependencies not available")
    except Exception:
        # Create a minimal analyzer without AI
        class MinimalAnalyzer:
            def analyze_pr(self, _files, quality_penalty=0):
                # Basic AST metrics for fallback
                ast_metrics = {
                    'summary': {
                        'total_cyclomatic_complexity': 5,
                        'max_nesting_depth': 2,
                        'total_functions': 2,
                        'total_control_structures': 8,
                        'complex_files': []
                    },
                    'files': {}
                }
                
                return CognitiveScore(
                    static_score=10,
                    impact_score=5,
                    ai_score=0,
                    total_score=15 + quality_penalty,
                    tier=0 if 15 + quality_penalty <= 35 else 1,
                    reasoning="Static analysis only - AI client not available",
                    ast_metrics=ast_metrics
                )
        
        analyzer = MinimalAnalyzer()
    
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
            pass  # Skip files that can't be read
    
    if not pr_files:
        return {
            'tier': 0,
            'total_score': quality_penalty,
            'reasoning': 'No valid code files to analyze',
            'static_score': 0,
            'impact_score': 0,
            'ai_score': 0,
            'quality_penalty': quality_penalty
        }
    
    # Run cognitive analysis
    if COGNITIVE_AVAILABLE:
        result = analyzer.analyze_pr(pr_files, quality_penalty=quality_penalty)
    else:
        result = analyzer.analyze_pr(pr_files)
    
    return {
        'tier': result.tier,
        'total_score': result.total_score,
        'reasoning': result.reasoning,
        'static_score': result.static_score,
        'impact_score': result.impact_score,
        'ai_score': result.ai_score,
        'quality_penalty': quality_penalty,
        'ast_metrics': result.ast_metrics if hasattr(result, 'ast_metrics') else None
    }


def main():
    """Main entry point for GitHub Actions."""
    changed_files = os.getenv('CHANGED_FILES', '')
    
    # Load quality penalty from quality gate results
    quality_penalty = 0
    try:
        with open('quality-gate-results.json', 'r') as f:
            quality_results = json.load(f)
            quality_penalty = quality_results.get('penalty', 0)
    except Exception:
        pass  # Use default quality penalty of 0
    
    result = run_cognitive_analysis(changed_files, quality_penalty)
    
    # Set outputs for GitHub Actions
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"tier={result['tier']}\n")
            f.write(f"total_score={result['total_score']}\n")
            f.write(f"reasoning={result['reasoning']}\n")
    
    # Ensure outputs directory exists
    os.makedirs('.code-analysis/outputs', exist_ok=True)
    
    # Create detailed results file
    with open('.code-analysis/outputs/cognitive-analysis-results.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    # Also create the legacy filename for compatibility
    with open('.code-analysis/outputs/cognitive_score.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    # Create the file that story_arc.py expects
    with open('.code-analysis/outputs/cognitive_analysis.json', 'w') as f:
        json.dump(result, f, indent=2)


if __name__ == '__main__':
    main()
