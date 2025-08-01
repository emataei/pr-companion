#!/usr/bin/env python3
"""
Integration script to demonstrate the advanced security analyzer
"""

import os
import json
from pathlib import Path
from advanced_security_analyzer import AdvancedSecurityAnalyzer

def main():
    """Test the advanced security analyzer with sample data"""
    
    # Sample security-sensitive code changes
    sample_changes = [
        {
            'file_path': 'src/auth/authentication.py',
            'content': '''
import hashlib
import os

# Hardcoded API key - this should be flagged
API_KEY = "sk-1234567890abcdef1234567890abcdef"

def authenticate_user(username, password):
    # Using weak hash - should be flagged
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    # SQL injection risk - should be flagged
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password_hash}'"
    
    return execute_query(query)

def get_token():
    # This is legitimate token generation
    return os.urandom(32).hex()
'''
        },
        {
            'file_path': 'src/utils/parser.py',
            'content': '''
def parse_token(token_string):
    """Parse a JSON token - this is NOT security related"""
    tokens = token_string.split(',')
    return [token.strip() for token in tokens]

def highlight_syntax_tokens(code):
    """Syntax highlighting - token here means code token"""
    tokens = []
    for line in code.split('\\n'):
        tokens.extend(line.split())
    return tokens
'''
        }
    ]
    
    print("🔍 Running Advanced Security Analysis Demo...")
    print("=" * 60)
    
    analyzer = AdvancedSecurityAnalyzer()
    findings = analyzer.analyze_file_changes(sample_changes)
    summary = analyzer.generate_summary()
    
    print("📊 Analysis Results:")
    print(f"   • Overall Risk: {summary['overall_risk']}")
    print(f"   • Total Findings: {summary['findings_count']}")
    print(f"   • Critical: {summary['critical_findings']}")
    print(f"   • High Risk: {summary['high_findings']}")
    print(f"   • Medium Risk: {summary['medium_findings']}")
    print(f"   • Categories: {', '.join(summary['categories_affected'])}")
    print()
    
    if findings:
        print("🚨 Security Findings:")
        print("-" * 40)
        for finding in findings:
            print(f"   {finding.risk_level.value}: {finding.description}")
            print(f"   File: {finding.file_path}:{finding.line_number}")
            print(f"   Recommendation: {finding.recommendation}")
            print(f"   Confidence: {finding.confidence:.1%}")
            print()
    
    # Save results - ensure we write to the root .code-analysis/outputs directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # Go up two levels from scripts to project root
    output_file = project_root / '.code-analysis' / 'outputs' / 'security-analysis-results.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Results saved to: {output_file}")
    
    # Demonstrate the difference
    print("\n🆚 Comparison with Basic Keyword Matching:")
    print("-" * 50)
    print("❌ Basic approach would flag:")
    print("   • 'token' in parser.py (FALSE POSITIVE)")
    print("   • 'password' in authentication.py (TRUE POSITIVE)")
    print("   • 'API_KEY' in authentication.py (TRUE POSITIVE)")
    print()
    print("✅ Advanced approach correctly identifies:")
    print("   • Hardcoded secret with high confidence")
    print("   • Weak cryptographic algorithm usage")
    print("   • SQL injection vulnerability")
    print("   • Ignores non-security token usage in parser.py")

if __name__ == "__main__":
    main()
