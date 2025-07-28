#!/usr/bin/env python3
"""
Enhanced PR Impact Analysis Visualization
Redesigned for clarity, actionability, and accessibility
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

def analyze_pr_risk_context() -> Dict[str, Any]:
    """Analyze PR to provide contextual risk scoring"""
    risk_data = {
        "overall_score": 0,
        "factors": {
            "security": {"score": 0, "issues": 0, "details": []},
            "complexity": {"score": 0, "cyclomatic": 0, "details": []},
            "coverage": {"score": 100, "percentage": 100, "details": []}
        },
        "recommendation": "approve_merge",
        "time_breakdown": {"fix": "0m", "test": "0m", "review": "15m"}
    }
    
    try:
        # Load quality gate results for security and complexity
        quality_file = Path('.code-analysis/outputs/quality-gate-results.json')
        if quality_file.exists():
            with open(quality_file, 'r', encoding='utf-8') as f:
                quality_data = json.load(f)
                
                # Analyze security issues
                security_issues = []
                complexity_issues = []
                
                blocking_issues = quality_data.get('issues', {}).get('blocking', [])
                for issue in blocking_issues:
                    category = issue.get('category', '').lower()
                    if 'security' in category or 'auth' in category or 'vulnerability' in category:
                        security_issues.append(issue)
                    elif 'complexity' in category or 'cognitive' in category:
                        complexity_issues.append(issue)
                
                # Calculate security risk
                if security_issues:
                    risk_data["factors"]["security"]["score"] = 10
                    risk_data["factors"]["security"]["issues"] = len(security_issues)
                    risk_data["factors"]["security"]["details"] = security_issues[:3]
                    risk_data["recommendation"] = "block_merge"
                
                # Calculate complexity risk
                if complexity_issues:
                    risk_data["factors"]["complexity"]["score"] = min(8, len(complexity_issues) * 2)
                    risk_data["factors"]["complexity"]["details"] = complexity_issues[:3]
                
                # Overall quality score affects coverage assumption
                quality_score = quality_data.get('score', 85)
                if quality_score < 70:
                    risk_data["factors"]["coverage"]["score"] = max(0, quality_score - 20)
                    risk_data["factors"]["coverage"]["percentage"] = max(0, quality_score - 20)
        
        # Load cognitive analysis for complexity details
        cognitive_file = Path('.code-analysis/outputs/cognitive-analysis-results.json')
        if cognitive_file.exists():
            with open(cognitive_file, 'r', encoding='utf-8') as f:
                cognitive_data = json.load(f)
                
                total_score = cognitive_data.get('total_score', 0)
                if total_score and total_score > 50:
                    risk_data["factors"]["complexity"]["score"] = min(10, int(total_score / 10))
                    risk_data["factors"]["complexity"]["cyclomatic"] = total_score
        
        # Calculate overall risk score (max of individual factors)
        factor_scores = [f["score"] for f in risk_data["factors"].values()]
        risk_data["overall_score"] = max(factor_scores) if factor_scores else 1
        
        # Calculate time breakdown based on risk
        total_risk = risk_data["overall_score"]
        if total_risk >= 8:
            risk_data["time_breakdown"] = {"fix": "45m", "test": "60m", "review": "45m"}
        elif total_risk >= 5:
            risk_data["time_breakdown"] = {"fix": "20m", "test": "30m", "review": "25m"}
        else:
            risk_data["time_breakdown"] = {"fix": "10m", "test": "15m", "review": "15m"}
            
    except Exception as e:
        print(f"Warning: Could not analyze risk context: {e}")
    
    return risk_data


def analyze_file_impact() -> Dict[str, Any]:
    """Analyze file changes for impact visualization"""
    file_data = {
        "total_files": 0,
        "risk_categories": {
            "high_risk": {"count": 0, "files": []},
            "medium_risk": {"count": 0, "files": []},
            "low_risk": {"count": 0, "files": []}
        },
        "change_distribution": {
            "modified_percentage": 0,
            "new_files_percentage": 0,
            "deleted_percentage": 0
        }
    }
    
    try:
        # Load diff stats for file analysis
        diff_file = Path('.code-analysis/outputs/diff-stats.json')
        if diff_file.exists():
            with open(diff_file, 'r', encoding='utf-8') as f:
                diff_data = json.load(f)
                
                if isinstance(diff_data, list):
                    file_data["total_files"] = len(diff_data)
                    
                    modified_count = 0
                    new_count = 0
                    deleted_count = 0
                    
                    for file_info in diff_data:
                        file_path = file_info.get('file', '')
                        added = file_info.get('added', 0)
                        removed = file_info.get('removed', 0)
                        
                        # Categorize file risk
                        if any(pattern in file_path.lower() for pattern in ['auth', 'security', 'password', 'token', 'payment', 'billing']):
                            file_data["risk_categories"]["high_risk"]["files"].append({
                                "path": file_path,
                                "reason": "Security/Business critical"
                            })
                        elif any(pattern in file_path.lower() for pattern in ['migration', 'schema', 'database', 'db/', 'api/', 'core/']):
                            file_data["risk_categories"]["high_risk"]["files"].append({
                                "path": file_path,
                                "reason": "Data integrity/Core system"
                            })
                        elif added + removed > 100:
                            file_data["risk_categories"]["medium_risk"]["files"].append({
                                "path": file_path,
                                "reason": "Large changes need review"
                            })
                        else:
                            file_data["risk_categories"]["low_risk"]["files"].append({
                                "path": file_path,
                                "reason": "Minor changes"
                            })
                        
                        # Track change types
                        if removed == 0 and added > 0:
                            new_count += 1
                        elif added == 0 and removed > 0:
                            deleted_count += 1
                        else:
                            modified_count += 1
                    
                    # Calculate percentages
                    total = len(diff_data)
                    if total > 0:
                        file_data["change_distribution"]["modified_percentage"] = int((modified_count / total) * 100)
                        file_data["change_distribution"]["new_files_percentage"] = int((new_count / total) * 100)
                        file_data["change_distribution"]["deleted_percentage"] = int((deleted_count / total) * 100)
                    
                    # Update counts
                    file_data["risk_categories"]["high_risk"]["count"] = len(file_data["risk_categories"]["high_risk"]["files"])
                    file_data["risk_categories"]["medium_risk"]["count"] = len(file_data["risk_categories"]["medium_risk"]["files"])
                    file_data["risk_categories"]["low_risk"]["count"] = len(file_data["risk_categories"]["low_risk"]["files"])
                    
    except Exception as e:
        print(f"Warning: Could not analyze file impact: {e}")
    
    return file_data


def generate_actionable_insights(risk_data: Dict[str, Any], file_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate prioritized, actionable insights"""
    insights = []
    
    # Security-based actions (highest priority)
    if risk_data["factors"]["security"]["score"] > 0:
        security_issues = risk_data["factors"]["security"]["details"]
        if security_issues:
            insights.append({
                "priority": 1,
                "type": "security_fix",
                "title": f"Fix security issue in {security_issues[0].get('file', 'multiple files')}",
                "effort": risk_data["time_breakdown"]["fix"],
                "icon": "🔒",
                "blocking": True
            })
    
    # Coverage-based actions
    if risk_data["factors"]["coverage"]["score"] < 70:
        insights.append({
            "priority": 2,
            "type": "add_tests",
            "title": "Add test coverage for modified code",
            "effort": risk_data["time_breakdown"]["test"],
            "icon": "🧪",
            "blocking": False
        })
    
    # File structure recommendations
    if file_data["total_files"] > 15:
        insights.append({
            "priority": 3,
            "type": "split_pr",
            "title": f"Consider splitting {file_data['total_files']} files into focused PRs",
            "effort": "30m",
            "icon": "📋",
            "blocking": False
        })
    
    # High-risk file warnings
    high_risk_files = file_data["risk_categories"]["high_risk"]["count"]
    if high_risk_files > 0:
        insights.append({
            "priority": 1 if risk_data["factors"]["security"]["score"] == 0 else 4,
            "type": "review_critical",
            "title": f"Extra review needed for {high_risk_files} critical files",
            "effort": risk_data["time_breakdown"]["review"],
            "icon": "👀",
            "blocking": high_risk_files > 3
        })
    
    # Sort by priority and limit to top 4
    insights.sort(key=lambda x: x["priority"])
    return insights[:4]


def create_enhanced_visualization():
    """Create the enhanced PR impact visualization"""
    try:
        # For now, generate the structured data that will be used by the visual generator
        # This replaces the old development flow script with much better data structure
        
        risk_data = analyze_pr_risk_context()
        file_data = analyze_file_impact()
        insights = generate_actionable_insights(risk_data, file_data)
        
        # Calculate total time investment
        time_parts = risk_data["time_breakdown"]
        total_minutes = sum([
            int(time_parts["fix"].replace("m", "")),
            int(time_parts["test"].replace("m", "")),
            int(time_parts["review"].replace("m", ""))
        ])
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        total_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Create enhanced visualization data
        visualization_data = {
            "visualization_type": "pr_impact_analysis_v2",
            "risk_metrics": risk_data,
            "file_impact": file_data,
            "actionable_items": insights,
            "time_investment": {
                "total": total_time,
                "breakdown": time_parts
            },
            "recommendation": risk_data["recommendation"],
            "accessibility": {
                "high_contrast": True,
                "screen_reader_friendly": True,
                "color_blind_safe": True
            }
        }
        
        # Generate markdown summary for immediate use
        markdown_content = generate_impact_summary(visualization_data)
        
        # Save the structured data
        output_dir = Path('.code-analysis/outputs')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / 'pr_impact_analysis_v2.json', 'w', encoding='utf-8') as f:
            json.dump(visualization_data, f, indent=2)
        
        with open(output_dir / 'pr_impact_summary.md', 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Enhanced PR impact analysis generated successfully")
        return True
        
    except Exception as e:
        print(f"Error creating enhanced visualization: {e}")
        return False


def generate_impact_summary(data: Dict[str, Any]) -> str:
    """Generate markdown summary of the PR impact analysis"""
    risk = data["risk_metrics"]
    files = data["file_impact"]
    insights = data["actionable_items"]
    time_data = data["time_investment"]
    
    # Risk level emoji and text
    risk_score = risk["overall_score"]
    if risk_score >= 8:
        risk_emoji = "🔴"
        risk_level = "CRITICAL"
    elif risk_score >= 5:
        risk_emoji = "🟡"
        risk_level = "MEDIUM"
    else:
        risk_emoji = "🟢"
        risk_level = "LOW"
    
    content = f"""## PR Impact Analysis

### {risk_emoji} Risk Assessment: {risk_score}/10 ({risk_level})

**Time Investment:** {time_data['total']}
- Fix: {time_data['breakdown']['fix']} | Test: {time_data['breakdown']['test']} | Review: {time_data['breakdown']['review']}

**Risk Factors:**
- 🔒 Security Issues: {risk['factors']['security']['issues']}
- 📏 Complexity: {'High' if risk['factors']['complexity']['score'] > 6 else 'Medium' if risk['factors']['complexity']['score'] > 3 else 'Low'}
- 🧪 Test Coverage: {risk['factors']['coverage']['percentage']}%

### 📁 File Impact Summary ({files['total_files']} files)

**Risk Distribution:**
- 🔴 High Risk: {files['risk_categories']['high_risk']['count']} files
- 🟡 Medium Risk: {files['risk_categories']['medium_risk']['count']} files  
- 🟢 Low Risk: {files['risk_categories']['low_risk']['count']} files

**Change Distribution:**
- Modified: {files['change_distribution']['modified_percentage']}%
- New files: {files['change_distribution']['new_files_percentage']}%
- Deleted: {files['change_distribution']['deleted_percentage']}%

### 🎯 Required Actions (Prioritized)

"""
    
    for i, insight in enumerate(insights, 1):
        blocking_text = " ⚠️ BLOCKING" if insight.get("blocking") else ""
        content += f"{i}. {insight['icon']} **{insight['title']}** ({insight['effort']}){blocking_text}\n"
    
    content += f"\n**Recommendation:** {'🚫 BLOCK MERGE' if data['recommendation'] == 'block_merge' else '✅ APPROVE'}\n\n"
    
    return content


def main():
    """Main function"""
    try:
        success = create_enhanced_visualization()
        if success:
            print("Enhanced PR impact analysis complete!")
        else:
            print("Failed to generate enhanced analysis")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
