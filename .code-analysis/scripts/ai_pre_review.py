#!/usr/bin/env python3
"""
AI Pre-Review Bot for GitHub Actions.

This script generates comprehensive PR analysis including:
- Plain-English summary of changes
- Impact analysis and risk assessment
- Suggested review tier and reasoning
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import re

# Add .code-analysis to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scoring.ai_client_factory import AIClientFactory
    AI_CLIENT_AVAILABLE = True
except ImportError:
    AI_CLIENT_AVAILABLE = False

# Constants
MANUAL_REVIEW_REQUIRED = "Manual review required"
AI_ANALYSIS_NOT_AVAILABLE = "AI analysis not available - missing configuration"

# File categorization patterns
FILE_PATTERNS = {
    'ui': ['.tsx', '.jsx', '.vue', '.svelte', '.css', '.scss', '.less'],
    'api': ['/api/', '/routes/', '/controllers/', '/handlers/'],
    'database': ['/migrations/', '/models/', '/schemas/', '.sql'],
    'config': ['.config.', '.env', 'dockerfile', 'docker-compose', '.yml', '.yaml', '.json'],
    'test': ['.test.', '.spec.', '__tests__/', '/tests/'],
    'documentation': ['.md', '.txt', '.rst', 'README', 'CHANGELOG']
}

# Risk assessment patterns
RISK_PATTERNS = {
    'high': [
        'auth', 'security', 'password', 'token', 'credential',
        'payment', 'billing', 'transaction', 'money',
        'permission', 'role', 'admin', 'user_management',
        'migration', 'schema', 'database', 'sql'
    ],
    'medium': [
        'api', 'endpoint', 'route', 'controller',
        'config', 'environment', 'setting',
        'validation', 'sanitization', 'input'
    ]
}

class AIPreReviewBot:
    def __init__(self):
        self.repo = os.environ.get('GITHUB_REPOSITORY')
        self.pr_number = os.environ.get('PR_NUMBER')
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
        
    def get_pr_diff(self) -> str:
        """Get the full diff of the PR"""
        try:
            result = subprocess.run(
                ['git', 'diff', 'origin/main...HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""
    
    def get_changed_files(self) -> List[str]:
        """Get list of changed files"""
        changed_files = os.environ.get('CHANGED_FILES', '')
        return [f.strip() for f in changed_files.split() if f.strip()]
    
    def _categorize_file(self, file: str) -> str:
        """Categorize a single file by type"""
        file_lower = file.lower()
        
        for category, patterns in FILE_PATTERNS.items():
            if any(pattern in file_lower for pattern in patterns):
                return category
        
        return 'other'
    
    def load_quality_gate_results(self) -> Optional[Dict]:
        """Load quality gate results from code quality analysis"""
        possible_paths = [
            './quality-results/quality-gate-results.json',
            './.code-analysis/outputs/quality-gate-results.json',
            './quality-gate-results.json'
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading quality gate results from {path}: {e}")
                    continue
        
        print("No quality gate results found")
        return None
    
    def analyze_file_types(self, files: List[str]) -> Dict[str, List[str]]:
        """Categorize files by type"""
        categories = {category: [] for category in FILE_PATTERNS.keys()}
        categories['other'] = []
        
        for file in files:
            category = self._categorize_file(file)
            categories[category].append(file)
        
        return categories
    
    def _assess_file_risk(self, file: str) -> Tuple[int, List[str]]:
        """Assess risk for a single file"""
        file_lower = file.lower()
        risk_factors = []
        risk_score = 0
        
        for pattern in RISK_PATTERNS['high']:
            if pattern in file_lower:
                risk_score += 3
                risk_factors.append(f"High-risk file: {file} (contains '{pattern}')")
                break
        else:
            for pattern in RISK_PATTERNS['medium']:
                if pattern in file_lower:
                    risk_score += 1
                    risk_factors.append(f"Medium-risk file: {file} (contains '{pattern}')")
                    break
        
        return risk_score, risk_factors
    
    def _assess_diff_risk(self, diff: str) -> Tuple[int, List[str]]:
        """Assess risk based on diff content"""
        diff_lower = diff.lower()
        risk_factors = []
        risk_score = 0
        
        for pattern in RISK_PATTERNS['high']:
            if pattern in diff_lower:
                risk_score += 2
                risk_factors.append(f"High-risk code change detected: '{pattern}'")
        
        return risk_score, risk_factors
    
    def assess_risk_level(self, files: List[str], diff: str) -> Tuple[str, List[str]]:
        """Assess risk level based on files and changes"""
        total_risk_score = 0
        all_risk_factors = []
        
        # Assess file risks
        for file in files:
            file_score, file_factors = self._assess_file_risk(file)
            total_risk_score += file_score
            all_risk_factors.extend(file_factors)
        
        # Assess diff risks
        diff_score, diff_factors = self._assess_diff_risk(diff)
        total_risk_score += diff_score
        all_risk_factors.extend(diff_factors)
        
        # Determine overall risk level
        if total_risk_score >= 5:
            return "HIGH", all_risk_factors
        elif total_risk_score >= 2:
            return "MEDIUM", all_risk_factors
        else:
            return "LOW", all_risk_factors
    
    def _adjust_risk_with_cognitive_analysis(self, risk_level: str, risk_factors: List[str]) -> str:
        """Adjust risk level based on cognitive complexity analysis results"""
        try:
            # Try to load cognitive analysis results
            cognitive_path = Path('.code-analysis/outputs/cognitive-analysis-results.json')
            if not cognitive_path.exists():
                cognitive_path = Path('cognitive-analysis-results.json')
            
            if cognitive_path.exists():
                with open(cognitive_path, 'r') as f:
                    cognitive_results = json.load(f)
                
                cognitive_tier = cognitive_results.get('tier', 1)
                cognitive_score = cognitive_results.get('total_score', 50)
                
                # If cognitive analysis shows very low complexity (tier 0, score < 25)
                # and current risk is HIGH only due to keyword matching (not actual complex changes),
                # downgrade to MEDIUM to avoid contradiction
                if (cognitive_tier == 0 and cognitive_score < 25 and 
                    risk_level == "HIGH"):
                    
                    # Check if HIGH risk is mainly from keyword detection, not structural complexity
                    keyword_based_risks = [f for f in risk_factors if 'High-risk code change detected' in f]
                    structural_risks = [f for f in risk_factors if 'High-risk file' in f and 'database' not in f.lower()]
                    
                    # If most risks are keyword-based and cognitive says it's simple, downgrade
                    if len(keyword_based_risks) > len(structural_risks):
                        print("Adjusting risk from HIGH to MEDIUM based on cognitive complexity analysis")
                        print(f"Cognitive tier: {cognitive_tier}, score: {cognitive_score}")
                        return "MEDIUM"
                
        except Exception as e:
            print(f"Could not load cognitive analysis for risk adjustment: {e}")
        
        return risk_level

    def generate_ai_summary(self, diff: str, files: List[str], quality_results: Optional[Dict] = None) -> Dict[str, str]:
        """Generate AI-powered summary of changes"""
        if not self.ai_client:
            return {
                "summary": AI_ANALYSIS_NOT_AVAILABLE,
                "business_impact": "Unable to assess without AI analysis",
                "technical_changes": "Review diff manually",
                "potential_issues": MANUAL_REVIEW_REQUIRED
            }
        
        # Create a focused prompt for better analysis
        file_list = ', '.join(files[:10]) + ("..." if len(files) > 10 else "")
        
        # Include quality gate results if available
        quality_context = ""
        if quality_results:
            quality_context = f"""
        
        Code Quality Analysis Results:
        {json.dumps(quality_results, indent=2)[:1000]}
        
        """
        
        prompt = f"""
        Analyze this code change and provide a comprehensive review summary.
        
        Files changed ({len(files)}): {file_list}
        {quality_context}
        Code diff:
        {diff[:3000]}  # Truncate very long diffs
        
        Please provide a structured analysis with:
        
        1. **Plain-English Summary**: What this change does in simple terms (format as bulleted list of key points):
           • Point 1: Brief description
           • Point 2: Brief description  
           • Point 3: Brief description
        2. **Business Impact**: How does this affect users, features, or business logic?
        3. **Technical Changes**: What are the key implementation details?
        4. **Risk Assessment**: What potential issues or concerns should reviewers watch for?
        """ + ("5. **Quality Gate Results**: Based on the code quality analysis results above, highlight any critical findings or issues that need attention." if quality_results else "") + """
        
        For the summary section, ALWAYS use bullet points (•) to make it easy to scan and understand quickly. Each bullet should be concise and focused on one key change or improvement.
        """
        
        try:
            # Use the existing AI client pattern
            messages = [
                {"role": "system", "content": "You are an expert code reviewer. Provide clear, actionable analysis that helps human reviewers understand the change quickly."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.ai_client.complete(
                messages=messages,
                model=self.model_name,
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # Parse the response into structured sections
            sections = self._parse_ai_response(content)
            
            return sections
                
        except Exception as e:
            return {
                "summary": f"AI analysis error: {str(e)}",
                "business_impact": MANUAL_REVIEW_REQUIRED,
                "technical_changes": MANUAL_REVIEW_REQUIRED,
                "potential_issues": MANUAL_REVIEW_REQUIRED
            }
    
    def _parse_ai_response(self, content: str) -> Dict[str, str]:
        """Parse AI response into structured sections"""
        sections = {
            "summary": "",
            "business_impact": "",
            "technical_changes": "",
            "potential_issues": ""
        }
        
        # Section header patterns
        section_patterns = {
            'summary': ['plain-english summary', 'summary'],
            'business_impact': ['business impact'],
            'technical_changes': ['technical changes'],
            'potential_issues': ['risk assessment', 'potential issues']
        }
        
        current_section = None
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            new_section = self._identify_section(line, section_patterns)
            if new_section:
                current_section = new_section
                continue
            
            # Add content to current section
            if current_section and line:
                self._add_to_section(sections, current_section, line)
        
        # Fallback if parsing fails
        if not any(sections.values()):
            return self._create_fallback_sections(content)
        
        return sections
    
    def _identify_section(self, line: str, patterns: Dict[str, List[str]]) -> Optional[str]:
        """Identify which section a line belongs to"""
        line_lower = line.lower()
        for section, keywords in patterns.items():
            if any(keyword in line_lower for keyword in keywords):
                return section
        return None
    
    def _add_to_section(self, sections: Dict[str, str], section: str, line: str):
        """Add cleaned line to the appropriate section"""
        # Remove markdown formatting and bullet points
        clean_line = line.replace('**', '').replace('*', '').replace('-', '').strip()
        if clean_line:
            if sections[section]:
                sections[section] += f" {clean_line}"
            else:
                sections[section] = clean_line
    
    def _create_fallback_sections(self, content: str) -> Dict[str, str]:
        """Create fallback sections when parsing fails"""
        return {
            "summary": content[:300] + "..." if len(content) > 300 else content,
            "business_impact": "See summary above",
            "technical_changes": "See summary above",
            "potential_issues": "Manual review recommended"
        }
    
    def run_analysis(self) -> Dict:
        """Run the complete AI pre-review analysis"""
        
        # Get changed files and diff
        files = self.get_changed_files()
        diff = self.get_pr_diff()
        
        # Load quality gate results from code quality analysis
        quality_results = self.load_quality_gate_results()
        
        if not files:
            return {
                "summary": "No changes to analyze",
                "risk_level": "NONE",
                "file_categories": {},
                "risk_factors": [],
                "quality_gate": quality_results,
                "ai_analysis": {
                    "summary": "No changes to analyze",
                    "business_impact": "None",
                    "technical_changes": "None",
                    "potential_issues": "None"
                }
            }
        
        # Analyze file types
        categories = self.analyze_file_types(files)
        
        # Assess risk level
        risk_level, risk_factors = self.assess_risk_level(files, diff)
        
        # Adjust risk level based on cognitive complexity (if available)
        risk_level = self._adjust_risk_with_cognitive_analysis(risk_level, risk_factors)
        
        # Generate AI summary
        ai_analysis = self.generate_ai_summary(diff, files, quality_results)
        
        return {
            "summary": ai_analysis["summary"],
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "file_categories": categories,
            "file_count": len(files),
            "quality_gate": quality_results,
            "ai_analysis": ai_analysis
        }

def main():
    """Main entry point"""
    bot = AIPreReviewBot()
    results = bot.run_analysis()
    
    # Save results for the GitHub Action
    with open('ai-pre-review-results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"AI Pre-Review analysis complete. Risk: {results['risk_level']}")
    print(f"Files analyzed: {results['file_count']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
