"""
Quality Gate system for PR analysis.

This module implements a quality gate that runs before cognitive scoring
to catch fundamental code quality issues and provide early feedback.
Enhanced with AI-powered code review capabilities.
"""

import ast
import re
import os
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from .ai_client_factory import AIClientFactory
from .copilot_instruction_parser import CopilotInstructionParser


# Constants for repeated strings
CATEGORY_CODE_QUALITY = "Code Quality"
CATEGORY_SECURITY = "Security"
CATEGORY_COMPLEXITY = "Complexity"
CATEGORY_DOCUMENTATION = "Documentation"
CATEGORY_TYPE_SAFETY = "Type Safety"

SUGGESTION_BREAK_FUNCTIONS = "Consider breaking into smaller functions"
SUGGESTION_USE_ENV_VARS = "Use environment variables or secure vault for secrets"
SUGGESTION_USE_PARAMETERIZED = "Use parameterized queries or safe alternatives"


class QualityLevel(Enum):
    """Quality issue severity levels."""
    BLOCKING = "blocking"  # Red flag - must fix
    WARNING = "warning"   # Quality penalty
    ADVISORY = "advisory"  # Suggestion only


@dataclass
class QualityIssue:
    """Represents a single quality issue."""
    level: QualityLevel
    category: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class QualityGateResult:
    """Result of quality gate analysis."""
    passed: bool
    quality_score: int  # 0-100, higher is better
    blocking_issues: List[QualityIssue]
    warning_issues: List[QualityIssue]
    advisory_issues: List[QualityIssue]
    summary: str
    quality_penalty: int  # Penalty to add to cognitive score


class QualityGate:
    """
    Quality gate analyzer that checks fundamental code quality.
    
    This runs before cognitive scoring to catch basic quality issues
    and provide early feedback to developers. Enhanced with AI-powered analysis.
    """
    
    def __init__(self, enable_ai: bool = True):
        """Initialize Quality Gate with optional AI capabilities."""
        self.enable_ai = enable_ai
        self.ai_client = None
        
        # Initialize Copilot instruction parser for project standards
        self.copilot_parser = CopilotInstructionParser()
        
        # Initialize AI client if enabled
        if self.enable_ai:
            try:
                AIClientFactory.validate_config()
                self.ai_client = AIClientFactory.create_client()
            except Exception as e:
                print(f"AI client initialization failed: {e}. AI analysis disabled.")
                self.enable_ai = False
        
        self.security_patterns = {
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ],
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'query\s*\(\s*["\'].*\+.*["\']'
            ],
            'unsafe_eval': [
                r'\beval\s*\(',
                r'\bexec\s*\('
            ]
        }
        
        self.code_smell_patterns = {
            'unused_imports': r'^import\s+\w+(?:\s+as\s+\w+)?$',
            'todo_fixme': r'#\s*(TODO|FIXME|HACK|XXX)',
            'print_debug': r'\bprint\s*\(',
            'console_log': r'\bconsole\.(log|debug|info)\s*\('
        }
    
    def analyze_pr(self, pr_files: List[Dict]) -> QualityGateResult:
        """
        Main entry point for quality gate analysis.
        
        Args:
            pr_files: List of file dictionaries with 'path', 'content', 'language'
            
        Returns:
            QualityGateResult with analysis results
        """
        blocking_issues = []
        warning_issues = []
        advisory_issues = []
        
        for file_info in pr_files:
            file_path = file_info['path']
            content = file_info['content']
            language = file_info.get('language', 'unknown')
            
            # Security checks
            security_issues = self._check_security(file_path, content)
            blocking_issues.extend([i for i in security_issues if i.level == QualityLevel.BLOCKING])
            warning_issues.extend([i for i in security_issues if i.level == QualityLevel.WARNING])
            
            # Code smell checks
            smell_issues = self._check_code_smells(file_path, content, language)
            blocking_issues.extend([i for i in smell_issues if i.level == QualityLevel.BLOCKING])
            warning_issues.extend([i for i in smell_issues if i.level == QualityLevel.WARNING])
            advisory_issues.extend([i for i in smell_issues if i.level == QualityLevel.ADVISORY])
            
            # Function complexity checks
            complexity_issues = self._check_function_complexity(file_path, content, language)
            warning_issues.extend(complexity_issues)
            
            # Documentation checks
            doc_issues = self._check_documentation(file_path, content, language)
            advisory_issues.extend(doc_issues)
        
        # AI-powered quality analysis (if enabled)
        if self.enable_ai and self.ai_client:
            ai_issues = self._ai_quality_analysis(pr_files)
            blocking_issues.extend([i for i in ai_issues if i.level == QualityLevel.BLOCKING])
            warning_issues.extend([i for i in ai_issues if i.level == QualityLevel.WARNING])
            advisory_issues.extend([i for i in ai_issues if i.level == QualityLevel.ADVISORY])
        
        # Calculate overall quality score and determine if gate passes
        quality_score = self._calculate_quality_score(blocking_issues, warning_issues, advisory_issues)
        # Quality gate passes if there are no blocking issues (warnings and advisory are not blocking)
        passed = len(blocking_issues) == 0
        quality_penalty = self._calculate_quality_penalty(blocking_issues, warning_issues)
        
        summary = self._generate_summary(passed, quality_score, blocking_issues, warning_issues)
        
        return QualityGateResult(
            passed=passed,
            quality_score=quality_score,
            blocking_issues=blocking_issues,
            warning_issues=warning_issues,
            advisory_issues=advisory_issues,
            summary=summary,
            quality_penalty=quality_penalty
        )
    
    def _check_security(self, file_path: str, content: str) -> List[QualityIssue]:
        """Check for security vulnerabilities."""
        issues = []
        
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_no = content[:match.start()].count('\n') + 1
                    
                    if category == 'hardcoded_secrets':
                        issues.append(QualityIssue(
                            level=QualityLevel.BLOCKING,
                            category=CATEGORY_SECURITY,
                            message="Potential hardcoded secret detected",
                            file_path=file_path,
                            line_number=line_no,
                            suggestion=SUGGESTION_USE_ENV_VARS
                        ))
                    elif category in ['sql_injection', 'unsafe_eval']:
                        issues.append(QualityIssue(
                            level=QualityLevel.BLOCKING,
                            category=CATEGORY_SECURITY,
                            message=f"Potential {category.replace('_', ' ')} vulnerability",
                            file_path=file_path,
                            line_number=line_no,
                            suggestion=SUGGESTION_USE_PARAMETERIZED
                        ))
        
        return issues
    
    def _check_code_smells(self, file_path: str, content: str, language: str) -> List[QualityIssue]:
        """Check for code smells."""
        issues = []
        
        # Check TODO/FIXME comments for ticket references
        todo_matches = re.finditer(self.code_smell_patterns['todo_fixme'], content, re.IGNORECASE)
        for match in todo_matches:
            line_no = content[:match.start()].count('\n') + 1
            line_content = content.split('\n')[line_no - 1]
            
            # Check if TODO has a ticket reference (JIRA, GitHub issue, etc.)
            if not re.search(r'(JIRA-\d+|#\d+|TICKET-\d+)', line_content, re.IGNORECASE):
                issues.append(QualityIssue(
                    level=QualityLevel.WARNING,
                    category=CATEGORY_CODE_QUALITY,
                    message="TODO/FIXME comment without ticket reference",
                    file_path=file_path,
                    line_number=line_no,
                    suggestion="Add ticket reference or remove comment if resolved"
                ))
        
        # Debug print statements
        if language == 'python':
            print_matches = re.finditer(self.code_smell_patterns['print_debug'], content)
            for match in print_matches:
                line_no = content[:match.start()].count('\n') + 1
                issues.append(QualityIssue(
                    level=QualityLevel.WARNING,
                    category=CATEGORY_CODE_QUALITY,
                    message="Debug print statement found",
                    file_path=file_path,
                    line_number=line_no,
                    suggestion="Remove debug prints or use proper logging"
                ))
        
        elif language in ['javascript', 'typescript']:
            console_matches = re.finditer(self.code_smell_patterns['console_log'], content)
            for match in console_matches:
                line_no = content[:match.start()].count('\n') + 1
                issues.append(QualityIssue(
                    level=QualityLevel.WARNING,
                    category=CATEGORY_CODE_QUALITY,
                    message="Console log statement found",
                    file_path=file_path,
                    line_number=line_no,
                    suggestion="Remove console logs or use proper logging"
                ))
        
        return issues
    
    def _check_function_complexity(self, file_path: str, content: str, language: str) -> List[QualityIssue]:
        """Check for overly complex functions."""
        issues = []
        
        if language == 'python':
            issues.extend(self._check_python_functions(file_path, content))
        else:
            issues.extend(self._check_generic_functions(file_path, content))
        
        return issues
    
    def _check_python_functions(self, file_path: str, content: str) -> List[QualityIssue]:
        """Check Python-specific function complexity."""
        issues = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    issues.extend(self._check_single_python_function(file_path, node))
        
        except SyntaxError:
            # File has syntax errors, will be caught by other tools
            pass
        
        return issues
    
    def _check_single_python_function(self, file_path: str, node: ast.FunctionDef) -> List[QualityIssue]:
        """Check a single Python function for issues."""
        issues = []
        
        # Calculate function length
        func_lines = node.end_lineno - node.lineno + 1
        
        if func_lines > 100:
            issues.append(QualityIssue(
                level=QualityLevel.WARNING,
                category=CATEGORY_COMPLEXITY,
                message=f"Function '{node.name}' is too long ({func_lines} lines)",
                file_path=file_path,
                line_number=node.lineno,
                suggestion=SUGGESTION_BREAK_FUNCTIONS
            ))
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            issues.append(QualityIssue(
                level=QualityLevel.ADVISORY,
                category=CATEGORY_DOCUMENTATION,
                message=f"Function '{node.name}' missing docstring",
                file_path=file_path,
                line_number=node.lineno,
                suggestion="Add docstring describing function purpose and parameters"
            ))
        
        return issues
    
    def _check_generic_functions(self, file_path: str, content: str) -> List[QualityIssue]:
        """Check function complexity for non-Python languages."""
        issues = []
        lines = content.split('\n')
        in_function = False
        func_start = 0
        func_name = "unknown"
        
        for i, line in enumerate(lines):
            # Simple heuristic for function detection
            func_match = re.match(r'\s*(function|def|func|fn)\s+(\w+)', line)
            if func_match:
                if in_function and i - func_start > 100:
                    issues.append(QualityIssue(
                        level=QualityLevel.WARNING,
                        category=CATEGORY_COMPLEXITY,
                        message=f"Function '{func_name}' is too long ({i - func_start} lines)",
                        file_path=file_path,
                        line_number=func_start + 1,
                        suggestion=SUGGESTION_BREAK_FUNCTIONS
                    ))
                
                in_function = True
                func_start = i
                func_name = func_match.group(2)
            elif in_function and re.match(r'^(def|function|func|fn|\s*class|\s*})', line):
                if i - func_start > 100:
                    issues.append(QualityIssue(
                        level=QualityLevel.WARNING,
                        category=CATEGORY_COMPLEXITY,
                        message=f"Function '{func_name}' is too long ({i - func_start} lines)",
                        file_path=file_path,
                        line_number=func_start + 1,
                        suggestion=SUGGESTION_BREAK_FUNCTIONS
                    ))
                in_function = False
        
        return issues
    
    def _check_documentation(self, file_path: str, content: str, language: str) -> List[QualityIssue]:
        """Check for documentation quality."""
        issues = []
        
        # Check for type hints in Python
        if language == 'python':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function has type hints
                        has_return_annotation = node.returns is not None
                        has_arg_annotations = any(arg.annotation for arg in node.args.args)
                        
                        if not has_return_annotation and not has_arg_annotations:
                            issues.append(QualityIssue(
                                level=QualityLevel.ADVISORY,
                                category=CATEGORY_TYPE_SAFETY,
                                message=f"Function '{node.name}' missing type hints",
                                file_path=file_path,
                                line_number=node.lineno,
                                suggestion="Add type hints for better code clarity"
                            ))
            except SyntaxError:
                pass
        
        return issues
    
    def _calculate_quality_score(self, blocking: List[QualityIssue], 
                                warning: List[QualityIssue], 
                                advisory: List[QualityIssue]) -> int:
        """Calculate overall quality score (0-100)."""
        base_score = 100
        
        # Heavy penalty for blocking issues (these should block the PR)
        base_score -= len(blocking) * 50
        
        # Moderate penalty for warnings (up to 5 points each, capped at 40 total)
        warning_penalty = min(len(warning) * 5, 40)
        base_score -= warning_penalty
        
        # Light penalty for advisory (up to 1 point each, capped at 10 total)
        advisory_penalty = min(len(advisory) * 1, 10)
        base_score -= advisory_penalty
        
        return max(0, min(100, base_score))
    
    def _calculate_quality_penalty(self, blocking: List[QualityIssue], 
                                 warning: List[QualityIssue]) -> int:
        """Calculate penalty to add to cognitive score."""
        penalty = 0
        
        # Add penalty for quality issues that make code harder to review
        penalty += len(blocking) * 20  # Blocking issues add significant cognitive load
        penalty += len(warning) * 5   # Warnings add moderate cognitive load
        
        return min(penalty, 40)  # Cap penalty to avoid overwhelming cognitive score
    
    def _ai_quality_analysis(self, pr_files: List[Dict]) -> List[QualityIssue]:
        """
        Use AI to analyze code changes for quality issues.
        
        AI evaluates:
        - Code quality and best practices adherence
        - Security vulnerabilities that regex patterns might miss
        - Maintainability issues
        - Performance concerns
        - Anti-patterns and code smells
        
        Returns: List of QualityIssue objects
        """
        if not self.ai_client:
            return []
            
        try:
            # Get project-specific coding standards from Copilot instructions
            standards = self.copilot_parser.get_standards()
            
            # Prepare code for AI analysis
            combined_changes = self._prepare_code_for_ai(pr_files)
            
            # Build context-aware prompt with project standards
            standards_context = self._build_standards_context(standards)
            
            prompt = f"""
You are an expert code reviewer analyzing a pull request for quality issues. 

{standards_context}

Review the following code changes and identify any quality, security, maintainability, or performance issues.

For each issue found, provide:
1. Severity level: "blocking" (critical security/functionality issues), "warning" (quality concerns), or "advisory" (suggestions)
2. Category: "Security", "Code Quality", "Performance", "Maintainability", or "Best Practices"
3. Description: Clear description of the issue
4. File path and approximate line number (if applicable)
5. Suggestion for improvement

Code changes:
{combined_changes}

Respond in this JSON format:
{{
  "issues": [
    {{
      "severity": "blocking|warning|advisory",
      "category": "Security|Code Quality|Performance|Maintainability|Best Practices",
      "message": "Description of the issue",
      "file_path": "path/to/file.py",
      "line_number": 42,
      "suggestion": "How to fix this issue"
    }}
  ]
}}

Focus on issues that static analysis might miss, such as:
- Business logic flaws
- Complex security vulnerabilities
- Architecture concerns
- Context-dependent anti-patterns
- Maintainability red flags
"""
            
            # Make AI request
            from azure.ai.inference.models import UserMessage
            messages = [UserMessage(prompt)]
            model_name = AIClientFactory.get_model_name()
            
            response = self.ai_client.complete(
                messages=messages,
                model=model_name,
                max_tokens=1500,
                temperature=0.1
            )
            
            # Parse AI response and convert to QualityIssue objects
            return self._parse_ai_response(response.choices[0].message.content)
            
        except Exception as e:
            print(f"AI quality analysis failed: {e}")
            return []
    
    def _prepare_code_for_ai(self, pr_files: List[Dict]) -> str:
        """Prepare code changes for AI analysis with context."""
        changes = []
        total_length = 0
        max_length = 8000  # Limit for API constraints
        
        for file_info in pr_files:
            file_path = file_info['path']
            content = file_info['content']
            language = file_info.get('language', 'unknown')
            
            # Add file header with context
            file_section = f"\n--- File: {file_path} (Language: {language}) ---\n{content}\n"
            
            if total_length + len(file_section) > max_length:
                break
                
            changes.append(file_section)
            total_length += len(file_section)
        
        return "\n".join(changes)
    
    def _parse_ai_response(self, response_content: str) -> List[QualityIssue]:
        """Parse AI response and convert to QualityIssue objects."""
        issues = []
        
        try:
            import json
            
            # Try to extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                data = json.loads(json_str)
                
                for issue_data in data.get('issues', []):
                    # Map severity to QualityLevel
                    severity_map = {
                        'blocking': QualityLevel.BLOCKING,
                        'warning': QualityLevel.WARNING,
                        'advisory': QualityLevel.ADVISORY
                    }
                    
                    level = severity_map.get(issue_data.get('severity', 'warning'), QualityLevel.WARNING)
                    
                    issue = QualityIssue(
                        level=level,
                        category=issue_data.get('category', 'AI Review'),
                        message=f"AI: {issue_data.get('message', 'Quality issue detected')}",
                        file_path=issue_data.get('file_path', 'unknown'),
                        line_number=issue_data.get('line_number'),
                        suggestion=issue_data.get('suggestion')
                    )
                    
                    issues.append(issue)
                    
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            # Fallback: create a general advisory issue
            issues.append(QualityIssue(
                level=QualityLevel.ADVISORY,
                category="AI Review",
                message="AI analysis completed but response format was unclear",
                file_path="general",
                suggestion="Consider manual review of the changes"
            ))
        
        return issues
    
    def _build_standards_context(self, standards) -> str:
        """Build context from project's Copilot instructions for AI analysis."""
        context_parts = []
        
        if standards.key_principles:
            context_parts.append(f"Project Coding Standards:\n{standards.key_principles}")
        
        if standards.preferred_patterns:
            patterns = "\n".join([f"- {pattern}" for pattern in standards.preferred_patterns[:5]])
            context_parts.append(f"Preferred Patterns:\n{patterns}")
        
        if standards.discouraged_patterns:
            patterns = "\n".join([f"- {pattern}" for pattern in standards.discouraged_patterns[:5]])
            context_parts.append(f"Discouraged Patterns:\n{patterns}")
        
        if standards.code_organization:
            org = "\n".join([f"- {item}" for item in standards.code_organization[:5]])
            context_parts.append(f"Code Organization Requirements:\n{org}")
        
        # Add emphasis flags as context
        emphasis_items = []
        if standards.error_handling_required:
            emphasis_items.append("- Proper error handling is required")
        if standards.type_safety_emphasis:
            emphasis_items.append("- Type safety is emphasized")
        if standards.performance_focus:
            emphasis_items.append("- Performance considerations are important")
        if standards.documentation_required:
            emphasis_items.append("- Code documentation is required")
        if standards.testing_emphasis:
            emphasis_items.append("- Testing coverage is emphasized")
        
        if emphasis_items:
            context_parts.append("Project Emphasis:\n" + "\n".join(emphasis_items))
        
        if context_parts:
            return "Consider the following project-specific standards when reviewing:\n\n" + "\n\n".join(context_parts) + "\n"
        else:
            return "Apply general coding best practices when reviewing.\n"
    
    def _generate_summary(self, passed: bool, quality_score: int,
                         blocking: List[QualityIssue], 
                         warning: List[QualityIssue]) -> str:
        """Generate human-readable summary."""
        if not passed:
            return f"Quality gate FAILED (Score: {quality_score}/100) - {len(blocking)} blocking issues must be fixed"
        elif quality_score < 80:
            return f"Quality gate passed with warnings (Score: {quality_score}/100) - {len(warning)} issues to address"
        else:
            return f"Quality gate passed (Score: {quality_score}/100) - Good code quality"
