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


def determine_complexity_categories(pr_files, result):
    """Determine complexity categories based on file analysis and scores."""
    
    # Default categories
    categories = {
        'architectural': 'LOW',
        'logical': 'LOW',
        'integration': 'LOW',
        'domain': 'LOW'
    }
    
    if not pr_files:
        return categories
    
    # Analyze files for complexity indicators
    architectural_indicators = 0
    logical_indicators = 0
    integration_indicators = 0
    domain_indicators = 0
    
    for file_data in pr_files:
        content = file_data.get('content', '').lower()
        path = file_data.get('path', '').lower()
        
        # Architectural complexity indicators
        if any(keyword in path for keyword in ['config', 'setup', 'architecture', 'infrastructure']):
            architectural_indicators += 2
        if any(keyword in content for keyword in ['class ', 'interface', 'abstract', 'extends', 'implements']):
            architectural_indicators += 1
            
        # Logical complexity indicators  
        if any(keyword in content for keyword in ['if ', 'for ', 'while ', 'switch', 'case']):
            logical_indicators += 1
        if any(keyword in content for keyword in ['algorithm', 'recursive', 'optimize', 'complex']):
            logical_indicators += 2
            
        # Integration complexity indicators
        if any(keyword in content for keyword in ['import ', 'require(', 'api', 'http', 'request']):
            integration_indicators += 1
        if any(keyword in path for keyword in ['api', 'service', 'client', 'integration']):
            integration_indicators += 2
            
        # Domain complexity indicators
        if any(keyword in path for keyword in ['business', 'domain', 'model', 'entity']):
            domain_indicators += 2
        if any(keyword in content for keyword in ['business', 'domain', 'rule', 'policy']):
            domain_indicators += 1
    
    # Determine levels based on indicators and scores
    total_score = result.total_score if hasattr(result, 'total_score') else 0
    
    # Scale indicators based on score
    if total_score > 50:
        multiplier = 1.5
    elif total_score > 30:
        multiplier = 1.2
    else:
        multiplier = 1.0
    
    # Apply thresholds
    categories['architectural'] = get_complexity_level(architectural_indicators * multiplier, [2, 4])
    categories['logical'] = get_complexity_level(logical_indicators * multiplier, [3, 6])
    categories['integration'] = get_complexity_level(integration_indicators * multiplier, [2, 5])
    categories['domain'] = get_complexity_level(domain_indicators * multiplier, [2, 4])
    
    return categories


def get_complexity_level(score, thresholds):
    """Convert a score to complexity level."""
    # Add CRITICAL level for very high complexity
    if score >= thresholds[1] * 2:  # Double the high threshold for critical
        return 'CRITICAL'
    elif score >= thresholds[1]:
        return 'HIGH'
    elif score >= thresholds[0]:
        return 'MEDIUM'
    else:
        return 'LOW'


def run_cognitive_analysis(file_list, quality_penalty=0):
    """Run cognitive analysis on changed files."""
    if not file_list.strip():
        return {
            'tier': 0,
            'total_score': 1,  # Minimum score of 1 instead of 0
            'reasoning': 'No code changes detected',
            'static_score': 0,
            'impact_score': 0,
            'ai_score': 0,
            'quality_penalty': 0,
            'complexity_categories': {
                'architectural': 'LOW',
                'logical': 'LOW', 
                'integration': 'LOW',
                'domain': 'LOW'
            }
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
        # Provide meaningful default scores even when no files found
        complexity_categories = {
            'architectural': 'LOW',
            'logical': 'LOW', 
            'integration': 'LOW',
            'domain': 'LOW'
        }
        return {
            'tier': 0,
            'total_score': max(5 + quality_penalty, 1),  # Minimum score of 1
            'reasoning': 'No valid code files to analyze - minimal change detected',
            'static_score': 0,
            'impact_score': 0,
            'ai_score': 0,
            'quality_penalty': quality_penalty,
            'complexity_categories': complexity_categories
        }
    
    # Run cognitive analysis
    if COGNITIVE_AVAILABLE:
        result = analyzer.analyze_pr(pr_files, quality_penalty=quality_penalty)
    else:
        result = analyzer.analyze_pr(pr_files)
    
    # Determine complexity categories based on scores and content
    complexity_categories = determine_complexity_categories(pr_files, result)
    
    return {
        'tier': result.tier,
        'total_score': result.total_score,
        'reasoning': result.reasoning,
        'static_score': result.static_score,
        'impact_score': result.impact_score,
        'ai_score': result.ai_score,
        'quality_penalty': quality_penalty,
        'complexity_categories': complexity_categories,
        'ast_metrics': result.ast_metrics if hasattr(result, 'ast_metrics') else None
    }


def main():
    """Main entry point for GitHub Actions."""
    changed_files = os.getenv('CHANGED_FILES', '')
    
    # Load quality penalty from quality gate results in outputs directory
    quality_penalty = 0
    try:
        with open('.code-analysis/outputs/quality-gate-results.json', 'r') as f:
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
