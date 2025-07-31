#!/usr/bin/env python3
"""
Advanced Security Code Analysis
Replaces simple keyword scanning with sophisticated pattern detection
and contextual analysis for security-related code changes.
"""

import ast
import re
import json
import sys
from typing import Dict, List, Tuple, Optional, Set, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class SecurityRiskLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"

class SecurityCategory(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CRYPTOGRAPHY = "cryptography"
    INPUT_VALIDATION = "input_validation"
    SECRET_MANAGEMENT = "secret_management"
    SESSION_MANAGEMENT = "session_management"
    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"
    INSECURE_COMMUNICATION = "insecure_communication"

@dataclass
class SecurityFinding:
    category: SecurityCategory
    risk_level: SecurityRiskLevel
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    recommendation: str
    confidence: float
    context: str

class AdvancedSecurityAnalyzer:
    """Advanced security analyzer using AST parsing and contextual analysis"""
    
    def __init__(self):
        self.patterns = self._load_security_patterns()
        self.findings: List[SecurityFinding] = []
    
    def _load_security_patterns(self) -> Dict[str, Any]:
        """Load sophisticated security patterns for analysis"""
        return {
            'hardcoded_secrets': {
                'patterns': [
                    # API keys and tokens with context
                    r'(?:api[_-]?key|token|secret|password)\s*[=:]\s*["\']([a-zA-Z0-9+/=]{20,})["\']',
                    # JWT tokens
                    r'["\']eyJ[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]*["\']',
                    # AWS keys
                    r'(?:AKIA|ASIA)[0-9A-Z]{16}',
                    # Database URLs with credentials
                    r'(?:postgres|mysql|mongodb)://[^:]+:[^@]+@[^/]+',
                ],
                'exclude_contexts': [
                    'test', 'mock', 'example', 'placeholder', 'dummy',
                    'xxx', 'your_key_here', 'sample'
                ]
            },
            'crypto_issues': {
                'weak_algorithms': ['md5', 'sha1', 'des', 'rc4'],
                'deprecated_functions': ['hashlib.md5', 'hashlib.sha1'],
                'insecure_random': ['random.random', 'math.random']
            },
            'injection_risks': {
                'sql_injection': [
                    r'cursor\.execute\s*\(\s*["\'][^"\']*%s[^"\']*["\']',
                    r'\.format\s*\([^)]*\)\s*(?:into|from|where|select)',
                    r'f["\'][^"\']*(?:select|insert|update|delete)[^"\']*{[^}]*}[^"\']*["\']'
                ],
                'command_injection': [
                    r'subprocess\.(?:call|run|Popen)\s*\([^)]*\+',
                    r'os\.system\s*\([^)]*\+',
                    r'eval\s*\([^)]*input'
                ]
            },
            'authentication_patterns': {
                'session_fixation': [
                    r'session_regenerate_id\s*\(\s*false',
                    r'session\.regenerate\s*\(\s*false'
                ],
                'weak_password_checks': [
                    r'len\s*\(\s*password\s*\)\s*[<>=]\s*[1-7]',
                    r'password\s*==\s*["\'][^"\']{1,7}["\']'
                ]
            }
        }
    
    def analyze_file_changes(self, file_changes: List[Dict]) -> List[SecurityFinding]:
        """Analyze file changes for security issues"""
        self.findings.clear()
        
        for change in file_changes:
            file_path = change.get('file_path', '')
            content = change.get('content', '')
            
            if not content:
                continue
            
            # Skip test files unless they contain real security code
            if self._is_test_file(file_path) and not self._has_security_relevance(content):
                continue
            
            # Analyze based on file type
            if file_path.endswith('.py'):
                self._analyze_python_file(file_path, content)
            elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                self._analyze_javascript_file(file_path, content)
            elif file_path.endswith(('.sql', '.migration')):
                self._analyze_sql_file(file_path, content)
            elif file_path.endswith(('.yaml', '.yml', '.json')):
                self._analyze_config_file(file_path, content)
        
        return self.findings
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file"""
        test_indicators = ['test', 'spec', '__test__', '.test.', '.spec.']
        return any(indicator in file_path.lower() for indicator in test_indicators)
    
    def _has_security_relevance(self, content: str) -> bool:
        """Check if test file has actual security relevance"""
        security_keywords = [
            'authentication', 'authorization', 'crypto', 'hash', 'encrypt',
            'jwt', 'oauth', 'security', 'vulnerability', 'exploit'
        ]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in security_keywords)
    
    def _analyze_python_file(self, file_path: str, content: str):
        """Analyze Python file using AST parsing"""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check for hardcoded secrets in assignments
                if isinstance(node, ast.Assign):
                    self._check_python_assignment(file_path, content, node)
                
                # Check for dangerous function calls
                elif isinstance(node, ast.Call):
                    self._check_python_function_call(file_path, content, node)
                
                # Check for weak crypto usage
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._check_python_imports(file_path, content, node)
        
        except SyntaxError:
            # If AST parsing fails, fall back to regex analysis
            self._analyze_with_regex(file_path, content)
    
    def _check_python_assignment(self, file_path: str, content: str, node: ast.Assign):
        """Check Python assignments for security issues"""
        if not node.targets or not isinstance(node.value, ast.Constant):
            return
        
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id.lower()
                value = str(node.value.value)
                
                # Check for potential secrets
                if self._is_secret_variable(var_name) and self._is_likely_real_secret(value):
                    line_no = node.lineno
                    code_snippet = self._get_line_from_content(content, line_no)
                    
                    self.findings.append(SecurityFinding(
                        category=SecurityCategory.SECRET_MANAGEMENT,
                        risk_level=SecurityRiskLevel.HIGH,
                        file_path=file_path,
                        line_number=line_no,
                        code_snippet=code_snippet,
                        description=f"Potential hardcoded secret in variable '{target.id}'",
                        recommendation="Use environment variables or secure secret management",
                        confidence=0.85,
                        context=f"Variable assignment: {var_name}"
                    ))
    
    def _check_python_function_call(self, file_path: str, content: str, node: ast.Call):
        """Check Python function calls for security issues"""
        if isinstance(node.func, ast.Attribute):
            func_name = f"{ast.unparse(node.func.value)}.{node.func.attr}"
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        else:
            return
        
        # Check for dangerous functions
        dangerous_functions = {
            'eval': SecurityRiskLevel.CRITICAL,
            'exec': SecurityRiskLevel.CRITICAL,
            'os.system': SecurityRiskLevel.HIGH,
            'subprocess.call': SecurityRiskLevel.MEDIUM,
        }
        
        if func_name in dangerous_functions:
            # Check if arguments come from user input
            if self._has_user_input_args(node):
                line_no = node.lineno
                code_snippet = self._get_line_from_content(content, line_no)
                
                self.findings.append(SecurityFinding(
                    category=SecurityCategory.INJECTION,
                    risk_level=dangerous_functions[func_name],
                    file_path=file_path,
                    line_number=line_no,
                    code_snippet=code_snippet,
                    description=f"Dangerous function '{func_name}' with potential user input",
                    recommendation="Validate and sanitize all inputs, use safer alternatives",
                    confidence=0.8,
                    context=f"Function call: {func_name}"
                ))
    
    def _check_python_imports(self, file_path: str, content: str, node):
        """Check Python imports for deprecated/insecure modules"""
        if isinstance(node, ast.ImportFrom):
            module = node.module
            if module in ['md5', 'sha'] or (module == 'hashlib' and 
                any(alias.name in ['md5', 'sha1'] for alias in node.names)):
                
                line_no = node.lineno
                code_snippet = self._get_line_from_content(content, line_no)
                
                self.findings.append(SecurityFinding(
                    category=SecurityCategory.CRYPTOGRAPHY,
                    risk_level=SecurityRiskLevel.MEDIUM,
                    file_path=file_path,
                    line_number=line_no,
                    code_snippet=code_snippet,
                    description="Use of weak cryptographic algorithm",
                    recommendation="Use SHA-256 or stronger algorithms",
                    confidence=0.9,
                    context=f"Weak crypto import: {module}"
                ))
    
    def _analyze_javascript_file(self, file_path: str, content: str):
        """Analyze JavaScript/TypeScript files"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_lower = line.lower().strip()
            
            # Check for token usage patterns
            if 'token' in line_lower:
                if self._is_security_relevant_token_usage(line, content):
                    risk_level = self._assess_token_risk(line, file_path)
                    
                    if risk_level != SecurityRiskLevel.NONE:
                        self.findings.append(SecurityFinding(
                            category=SecurityCategory.AUTHENTICATION,
                            risk_level=risk_level,
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip(),
                            description=self._get_token_description(line),
                            recommendation=self._get_token_recommendation(line),
                            confidence=0.7,
                            context="Token usage analysis"
                        ))
            
            # Check for XSS vulnerabilities
            if any(pattern in line_lower for pattern in ['innerhtml', 'dangerouslysetinnerhtml']):
                if not self._is_safe_html_usage(line):
                    self.findings.append(SecurityFinding(
                        category=SecurityCategory.XSS,
                        risk_level=SecurityRiskLevel.HIGH,
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line.strip(),
                        description="Potential XSS vulnerability through innerHTML",
                        recommendation="Use textContent or proper sanitization",
                        confidence=0.8,
                        context="Dynamic HTML content"
                    ))
    
    def _is_security_relevant_token_usage(self, line: str, full_content: str) -> bool:
        """Determine if token usage is security-relevant"""
        line_lower = line.lower()
        
        # Skip obvious non-security contexts
        non_security_contexts = [
            'parse', 'split', 'join', 'replace', 'format',
            'highlight', 'syntax', 'lexer', 'parser'
        ]
        
        if any(context in line_lower for context in non_security_contexts):
            return False
        
        # Look for security-related contexts
        security_contexts = [
            'auth', 'jwt', 'bearer', 'session', 'api', 'access',
            'refresh', 'login', 'signin', 'authenticate'
        ]
        
        # Check surrounding lines for context
        lines = full_content.split('\n')
        current_line_idx = lines.index(line) if line in lines else 0
        
        context_window = []
        for i in range(max(0, current_line_idx - 2), min(len(lines), current_line_idx + 3)):
            context_window.append(lines[i].lower())
        
        context_text = ' '.join(context_window)
        return any(context in context_text for context in security_contexts)
    
    def _assess_token_risk(self, line: str, file_path: str) -> SecurityRiskLevel:
        """Assess the risk level of token usage"""
        line_lower = line.lower()
        
        # High risk patterns
        if any(pattern in line_lower for pattern in [
            'token =', 'token:', 'hardcoded', 'secret', 'bearer '
        ]):
            return SecurityRiskLevel.HIGH
        
        # Medium risk patterns
        if any(pattern in line_lower for pattern in [
            'gettoken', 'settoken', 'savetoken', 'storetoken'
        ]):
            return SecurityRiskLevel.MEDIUM
        
        # Low risk if in configuration or environment files
        if any(ext in file_path.lower() for ext in ['.env', '.config', 'settings']):
            return SecurityRiskLevel.LOW
        
        return SecurityRiskLevel.NONE
    
    def _get_token_description(self, line: str) -> str:
        """Get description for token-related finding"""
        line_lower = line.lower()
        
        if 'token =' in line_lower or 'token:' in line_lower:
            return "Token assignment detected - verify if hardcoded"
        elif 'bearer' in line_lower:
            return "Bearer token usage - ensure proper validation"
        elif any(func in line_lower for func in ['gettoken', 'settoken']):
            return "Token management function - verify secure handling"
        else:
            return "Token usage detected - review for security implications"
    
    def _get_token_recommendation(self, line: str) -> str:
        """Get recommendation for token-related finding"""
        line_lower = line.lower()
        
        if 'token =' in line_lower:
            return "Use environment variables or secure configuration for tokens"
        elif 'bearer' in line_lower:
            return "Ensure token validation and proper error handling"
        else:
            return "Implement secure token storage and transmission practices"
    
    def _analyze_with_regex(self, file_path: str, content: str):
        """Fallback regex analysis when AST parsing fails"""
        lines = content.split('\n')
        
        for category, patterns in self.patterns.items():
            if isinstance(patterns, dict) and 'patterns' in patterns:
                for pattern in patterns['patterns']:
                    for i, line in enumerate(lines, 1):
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            if self._should_exclude_match(match.group(), patterns.get('exclude_contexts', [])):
                                continue
                            
                            self.findings.append(SecurityFinding(
                                category=SecurityCategory.SECRET_MANAGEMENT,
                                risk_level=SecurityRiskLevel.MEDIUM,
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line.strip(),
                                description=f"Potential security issue detected: {category}",
                                recommendation="Review and validate security implementation",
                                confidence=0.6,
                                context=f"Regex match: {pattern}"
                            ))
    
    def _is_secret_variable(self, var_name: str) -> bool:
        """Check if variable name suggests it holds a secret"""
        secret_indicators = [
            'key', 'token', 'secret', 'password', 'pass', 'pwd',
            'auth', 'api_key', 'access_token', 'refresh_token'
        ]
        return any(indicator in var_name for indicator in secret_indicators)
    
    def _is_likely_real_secret(self, value: str) -> bool:
        """Check if value looks like a real secret (not placeholder)"""
        if len(value) < 8:
            return False
        
        placeholders = [
            'your_key_here', 'placeholder', 'example', 'test',
            'dummy', 'mock', 'xxx', 'changeme', 'secret'
        ]
        
        return not any(placeholder in value.lower() for placeholder in placeholders)
    
    def _has_user_input_args(self, node: ast.Call) -> bool:
        """Check if function call has arguments that might come from user input"""
        input_indicators = ['input', 'request', 'form', 'query', 'param']
        
        for arg in node.args:
            if isinstance(arg, ast.Name) and any(indicator in arg.id.lower() for indicator in input_indicators):
                return True
            elif isinstance(arg, ast.Attribute) and any(indicator in ast.unparse(arg).lower() for indicator in input_indicators):
                return True
        
        return False
    
    def _should_exclude_match(self, match_text: str, exclude_contexts: List[str]) -> bool:
        """Check if match should be excluded based on context"""
        match_lower = match_text.lower()
        return any(context in match_lower for context in exclude_contexts)
    
    def _is_safe_html_usage(self, line: str) -> bool:
        """Check if HTML usage is safe (sanitized)"""
        safe_indicators = ['sanitize', 'escape', 'dompurify', 'xss-filters']
        return any(indicator in line.lower() for indicator in safe_indicators)
    
    def _get_line_from_content(self, content: str, line_no: int) -> str:
        """Get specific line from content"""
        lines = content.split('\n')
        if 1 <= line_no <= len(lines):
            return lines[line_no - 1].strip()
        return ""
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of security analysis"""
        if not self.findings:
            return {
                'overall_risk': SecurityRiskLevel.NONE.value,
                'findings_count': 0,
                'critical_findings': 0,
                'high_findings': 0,
                'categories_affected': [],
                'recommendations': ["No significant security issues detected"]
            }
        
        risk_counts = {level: 0 for level in SecurityRiskLevel}
        categories = set()
        
        for finding in self.findings:
            risk_counts[finding.risk_level] += 1
            categories.add(finding.category.value)
        
        # Determine overall risk
        if risk_counts[SecurityRiskLevel.CRITICAL] > 0:
            overall_risk = SecurityRiskLevel.CRITICAL
        elif risk_counts[SecurityRiskLevel.HIGH] > 0:
            overall_risk = SecurityRiskLevel.HIGH
        elif risk_counts[SecurityRiskLevel.MEDIUM] > 0:
            overall_risk = SecurityRiskLevel.MEDIUM
        else:
            overall_risk = SecurityRiskLevel.LOW
        
        return {
            'overall_risk': overall_risk.value,
            'findings_count': len(self.findings),
            'critical_findings': risk_counts[SecurityRiskLevel.CRITICAL],
            'high_findings': risk_counts[SecurityRiskLevel.HIGH],
            'medium_findings': risk_counts[SecurityRiskLevel.MEDIUM],
            'categories_affected': sorted(list(categories)),
            'findings': [
                {
                    'category': f.category.value,
                    'risk_level': f.risk_level.value,
                    'file_path': f.file_path,
                    'line_number': f.line_number,
                    'description': f.description,
                    'recommendation': f.recommendation,
                    'confidence': f.confidence,
                    'context': f.context
                } for f in sorted(self.findings, key=lambda x: (x.risk_level.value, x.file_path))
            ]
        }

def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 2:
        print("Usage: python advanced_security_analyzer.py <changes_file>")
        sys.exit(1)
    
    changes_file = sys.argv[1]
    
    try:
        with open(changes_file, 'r', encoding='utf-8') as f:
            file_changes = json.load(f)
    except Exception as e:
        print(f"Error loading changes file: {e}")
        sys.exit(1)
    
    analyzer = AdvancedSecurityAnalyzer()
    findings = analyzer.analyze_file_changes(file_changes)
    summary = analyzer.generate_summary()
    
    # Output results - ensure we write to the root .code-analysis/outputs directory
    # Get the script directory and navigate to the project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # Go up two levels from scripts to project root
    output_file = project_root / '.code-analysis' / 'outputs' / 'security-analysis-results.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Security analysis complete. Found {len(findings)} findings.")
    print(f"Overall risk level: {summary['overall_risk']}")
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
