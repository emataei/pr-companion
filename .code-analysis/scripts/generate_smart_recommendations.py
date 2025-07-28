#!/usr/bin/env python3
"""
Generate Smart, Context-Aware PR Recommendations
Minimizes cognitive load by providing tailored suggestions based on PR metadata
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


def analyze_pr_context() -> Dict[str, Any]:
    """Extract PR context from available data sources"""
    context = {
        "change_intent": "UNKNOWN",
        "files_changed": 0,
        "lines_added": 0,
        "lines_deleted": 0,
        "test_coverage_delta": 0,
        "affected_areas": [],
        "pr_author_experience": "mid",  # Default to mid-level
        "previous_pr_patterns": {}
    }
    
    try:
        # Load intent classification results
        intent_file = Path('.code-analysis/outputs/intent-classification-results.json')
        if intent_file.exists():
            with open(intent_file, 'r', encoding='utf-8') as f:
                intent_data = json.load(f)
                context["change_intent"] = intent_data.get("primary_intent", "UNKNOWN").upper()
                context["affected_areas"] = intent_data.get("affected_areas", [])
                
                # Extract file change metrics
                file_changes = intent_data.get("file_changes_summary", {})
                context["files_changed"] = file_changes.get("total_files", 0)
                context["lines_added"] = file_changes.get("total_lines_added", 0)
                context["lines_deleted"] = file_changes.get("total_lines_removed", 0)
    
        # Load diff stats for additional context
        diff_stats_file = Path('.code-analysis/outputs/diff-stats.json')
        if diff_stats_file.exists():
            with open(diff_stats_file, 'r', encoding='utf-8') as f:
                diff_data = json.load(f)
                if isinstance(diff_data, list) and len(diff_data) > 0:
                    context["files_changed"] = len(diff_data)
                    context["lines_added"] = sum(f.get('added', 0) for f in diff_data)
                    context["lines_deleted"] = sum(f.get('removed', 0) for f in diff_data)
    
        # Infer author experience from PR patterns (simplified heuristic)
        if context["files_changed"] > 20 or abs(context["lines_added"] - context["lines_deleted"]) > 1000:
            context["pr_author_experience"] = "senior"
        elif context["files_changed"] < 5 and abs(context["lines_added"] - context["lines_deleted"]) < 100:
            context["pr_author_experience"] = "junior"
            
    except Exception as e:
        print(f"Warning: Could not load PR context: {e}")
    
    return context


def generate_recommendations_by_intent(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate context-aware recommendations based on change intent"""
    recommendations = []
    intent = context["change_intent"]
    files_changed = context["files_changed"]
    lines_net = abs(context["lines_added"] - context["lines_deleted"])
    areas = context["affected_areas"]
    experience = context["pr_author_experience"]
    
    # REFACTOR recommendations
    if intent == "REFACTOR":
        if files_changed > 15:
            recommendations.append({
                "icon": "🔄",
                "title": "Split into Focused PRs",
                "time_estimate": "30 min",
                "priority": "high",
                "description": f"Current PR touches {files_changed} files across {len(areas)} areas",
                "action": f"Suggest: {min(3, len(areas))} PRs by architectural layer",
                "guideline": "Team Guideline: Max 10 files per refactor PR",
                "experience_note": "Consider incremental approach" if experience == "junior" else None
            })
        
        if context["lines_deleted"] > context["lines_added"] * 2:
            recommendations.append({
                "icon": "🧪",
                "title": "Add Characterization Tests",
                "time_estimate": "45 min",
                "priority": "high",
                "description": f"Large code deletion ({context['lines_deleted']} lines) needs safety net",
                "action": "Add tests before refactoring to preserve behavior",
                "guideline": "Use snapshot testing for behavior preservation",
                "experience_note": "Focus on happy path scenarios first" if experience == "junior" else None
            })
        
        if lines_net > 500:
            recommendations.append({
                "icon": "📊",
                "title": "Document Performance Impact",
                "time_estimate": "15 min",
                "priority": "medium",
                "description": "Large refactor may affect response times",
                "action": "Run benchmarks: `npm run perf:api` or equivalent",
                "guideline": "Add results to PR description"
            })
    
    # FEATURE recommendations
    elif intent == "FEATURE":
        if "api" in areas:
            recommendations.append({
                "icon": "🔒",
                "title": "Security & Validation Review",
                "time_estimate": "20 min",
                "priority": "high",
                "description": "New API endpoints need security assessment",
                "action": "Review input validation, authentication, and authorization",
                "guideline": "API Security Checklist: /docs/api-security.md",
                "experience_note": "Focus on OWASP Top 10" if experience == "junior" else None
            })
        
        if files_changed > 8:
            recommendations.append({
                "icon": "📝",
                "title": "Update Documentation",
                "time_estimate": "25 min",
                "priority": "medium",
                "description": f"Feature spans {files_changed} files - documentation needed",
                "action": "Update README, API docs, and user guides",
                "guideline": "Include usage examples and migration notes"
            })
        
        recommendations.append({
            "icon": "🧪",
            "title": "Comprehensive Test Coverage",
            "time_estimate": "60 min",
            "priority": "high",
            "description": "New features require thorough testing",
            "action": "Unit tests, integration tests, and edge cases",
            "guideline": "Target: 80%+ coverage for new code",
            "experience_note": "Start with happy path, then edge cases" if experience == "junior" else None
        })
    
    # BUG_FIX recommendations
    elif intent == "BUG_FIX":
        recommendations.append({
            "icon": "🐛",
            "title": "Add Regression Test",
            "time_estimate": "20 min",
            "priority": "high",
            "description": "Prevent this bug from reoccurring",
            "action": "Write test that fails before fix, passes after",
            "guideline": "Test should match reported issue exactly"
        })
        
        if files_changed > 5:
            recommendations.append({
                "icon": "🔍",
                "title": "Root Cause Analysis",
                "time_estimate": "15 min",
                "priority": "medium",
                "description": f"Bug fix touches {files_changed} files - investigate scope",
                "action": "Document why bug affected multiple files",
                "guideline": "Add findings to PR description"
            })
    
    # DOCS recommendations
    elif intent == "DOCS":
        if context["lines_added"] > 200:
            recommendations.append({
                "icon": "📖",
                "title": "Review for Accuracy",
                "time_estimate": "30 min",
                "priority": "medium",
                "description": "Extensive documentation changes need validation",
                "action": "Verify code examples compile and run",
                "guideline": "Test all commands and code snippets"
            })
    
    # MAINTENANCE recommendations
    elif intent == "MAINTENANCE":
        if "dependencies" in str(areas).lower() or any("package" in str(area).lower() for area in areas):
            recommendations.append({
                "icon": "🔧",
                "title": "Test Dependency Updates",
                "time_estimate": "40 min",
                "priority": "high",
                "description": "Dependency changes need thorough testing",
                "action": "Run full test suite and check for breaking changes",
                "guideline": "Test in staging environment first"
            })
    
    # Universal recommendations based on size
    if files_changed > 20:
        recommendations.append({
            "icon": "⚡",
            "title": "Consider Incremental Approach",
            "time_estimate": "10 min",
            "priority": "medium",
            "description": f"Large PR ({files_changed} files) increases review complexity",
            "action": "Split into smaller, focused PRs if possible",
            "guideline": "Smaller PRs = faster reviews + easier rollbacks"
        })
    
    # Prioritize and limit recommendations
    recommendations.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])
    return recommendations[:5]  # Limit to 5 recommendations


def format_recommendations(recommendations: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
    """Format recommendations into markdown"""
    if not recommendations:
        return ""
    
    intent = context["change_intent"]
    files = context["files_changed"]
    areas_text = ", ".join(context["affected_areas"][:3]) if context["affected_areas"] else "multiple areas"
    
    content = f"## Smart Recommendations\n"
    content += f"Based on your **{intent}** affecting **{files} files** in {areas_text}:\n\n"
    
    for i, rec in enumerate(recommendations, 1):
        content += f"{i}. {rec['icon']} **{rec['title']}** ({rec['time_estimate']})\n"
        content += f"   - {rec['description']}\n"
        content += f"   - {rec['action']}\n"
        
        if rec.get('guideline'):
            content += f"   - [{rec['guideline']}]\n"
        
        if rec.get('experience_note'):
            content += f"   - 💡 {rec['experience_note']}\n"
        
        content += "\n"
    
    return content


def generate_smart_recommendations():
    """Main function to generate context-aware recommendations"""
    try:
        # Analyze PR context
        context = analyze_pr_context()
        
        # Generate recommendations
        recommendations = generate_recommendations_by_intent(context)
        
        if not recommendations:
            return "## Smart Recommendations\n\n**No specific recommendations** for this change type.\n\n"
        
        # Format output
        content = format_recommendations(recommendations, context)
        
        return content
        
    except Exception as e:
        print(f"Error generating smart recommendations: {e}")
        return "## Smart Recommendations\n\n**Analysis unavailable** - manual review recommended.\n\n"


def main():
    """Main function for CLI usage"""
    try:
        # Ensure output directory exists
        output_dir = Path('.code-analysis/outputs')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate recommendations
        content = generate_smart_recommendations()
        
        # Write to output file
        output_file = output_dir / 'smart_recommendations.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Quiet success - only output if verbose mode or error
        
    except Exception as e:
        print(f"Error in main: {e}")
        
        # Create fallback
        fallback_content = "## Smart Recommendations\n\n**Analysis failed** - review manually.\n\n"
        
        output_file = Path('.code-analysis/outputs/smart_recommendations.md')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fallback_content)


if __name__ == "__main__":
    main()
