"""
AST-based code complexity analysis for cognitive scoring.

This module provides precise complexity measurement using Abstract Syntax Trees
for supported languages, with fallback to heuristic analysis for unsupported languages.
"""

import ast
import hashlib
import json
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union


class ComplexityMetrics:
    """Container for complexity metrics from AST analysis."""
    
    def __init__(self):
        self.cyclomatic_complexity = 0
        self.nesting_depth = 0
        self.function_count = 0
        self.function_length_penalty = 0
        self.control_structures = 0
        self.file_size_penalty = 0
        self.total_score = 0
        
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for serialization."""
        return {
            'cyclomatic_complexity': self.cyclomatic_complexity,
            'nesting_depth': self.nesting_depth,
            'function_count': self.function_count,
            'function_length_penalty': self.function_length_penalty,
            'control_structures': self.control_structures,
            'file_size_penalty': self.file_size_penalty,
            'total_score': self.total_score
        }


class ASTAnalyzer(ABC):
    """Abstract base class for language-specific AST analyzers."""
    
    @abstractmethod
    def analyze(self, code: str, file_path: str) -> ComplexityMetrics:
        """Analyze code and return complexity metrics."""
        pass
    
    @abstractmethod
    def supports_language(self, file_extension: str) -> bool:
        """Check if this analyzer supports the given file extension."""
        pass


class PythonASTAnalyzer(ASTAnalyzer):
    """AST-based complexity analyzer for Python code."""
    
    def supports_language(self, file_extension: str) -> bool:
        """Check if this analyzer supports Python files."""
        return file_extension.lower() in ['.py', '.pyx', '.pyi']
    
    def analyze(self, code: str, file_path: str) -> ComplexityMetrics:
        """Analyze Python code using AST parsing."""
        metrics = ComplexityMetrics()
        
        try:
            tree = ast.parse(code)
            self._analyze_ast(tree, metrics)
        except SyntaxError:
            # Fall back to heuristic analysis for invalid Python
            return self._fallback_analysis(code, file_path)
        
        return metrics
    
    def _analyze_ast(self, tree: ast.AST, metrics: ComplexityMetrics) -> None:
        """Walk AST and calculate complexity metrics."""
        
        for node in ast.walk(tree):
            # Count control structures for cyclomatic complexity
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                metrics.cyclomatic_complexity += 1
                metrics.control_structures += 1
            
            # Count function definitions and analyze their complexity
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics.function_count += 1
                func_metrics = self._analyze_function(node)
                metrics.function_length_penalty += func_metrics.function_length_penalty
                metrics.nesting_depth = max(metrics.nesting_depth, func_metrics.nesting_depth)
            
            # Count exception handlers
            if isinstance(node, ast.ExceptHandler):
                metrics.cyclomatic_complexity += 1
            
            # Count comprehensions as control structures
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                metrics.control_structures += 1
        
        # Calculate total score
        metrics.total_score = (
            metrics.cyclomatic_complexity +
            metrics.nesting_depth +
            metrics.function_length_penalty +
            metrics.file_size_penalty
        )
    
    def _analyze_function(self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> ComplexityMetrics:
        """Analyze a specific function for complexity metrics."""
        func_metrics = ComplexityMetrics()
        
        # Calculate function length penalty
        if hasattr(func_node, 'end_lineno') and hasattr(func_node, 'lineno'):
            line_count = func_node.end_lineno - func_node.lineno
            if line_count > 50:
                func_metrics.function_length_penalty = 3
            elif line_count > 20:
                func_metrics.function_length_penalty = 1
        
        # Calculate nesting depth within function
        func_metrics.nesting_depth = self._calculate_nesting_depth(func_node)
        
        return func_metrics
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in a node."""
        max_depth = 0
        
        def visit_node(node: ast.AST, current_depth: int = 0) -> int:
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            # Nodes that increase nesting depth
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                current_depth += 1
            
            # Recursively visit child nodes
            for child in ast.iter_child_nodes(node):
                visit_node(child, current_depth)
            
            return max_depth
        
        return visit_node(node)
    
    def _fallback_analysis(self, code: str, _file_path: str) -> ComplexityMetrics:
        """Fallback to heuristic analysis when AST parsing fails."""
        metrics = ComplexityMetrics()
        lines = code.split('\n')
        
        # Count control structures using text patterns
        control_keywords = ['if ', 'for ', 'while ', 'try:', 'except:', 'with ']
        for line in lines:
            line_lower = line.lower().strip()
            for keyword in control_keywords:
                if keyword in line_lower:
                    metrics.control_structures += 1
                    break
        
        # Estimate nesting depth by indentation
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent // 4)  # Assume 4-space indentation
        
        metrics.nesting_depth = max_indent
        metrics.cyclomatic_complexity = metrics.control_structures
        
        # File size penalty
        if len(lines) > 100:
            metrics.file_size_penalty = 5
        elif len(lines) > 50:
            metrics.file_size_penalty = 2
        
        metrics.total_score = (
            metrics.cyclomatic_complexity +
            metrics.nesting_depth +
            metrics.file_size_penalty
        )
        
        return metrics


class JavaScriptASTAnalyzer(ASTAnalyzer):
    """Heuristic-based complexity analyzer for JavaScript/TypeScript."""
    
    def supports_language(self, file_extension: str) -> bool:
        """Check if this analyzer supports JavaScript/TypeScript files."""
        return file_extension.lower() in ['.js', '.jsx', '.ts', '.tsx', '.mjs']
    
    def analyze(self, code: str, file_path: str) -> ComplexityMetrics:
        """Analyze JavaScript/TypeScript code using pattern matching."""
        metrics = ComplexityMetrics()
        lines = code.split('\n')
        
        # Control structures
        control_patterns = [
            'if ', 'for ', 'while ', 'switch ', 'catch ', 'try ',
            'function ', '=>', '.then(', '.catch('
        ]
        
        brace_nesting = 0
        max_nesting = 0
        
        for line in lines:
            line_stripped = line.strip().lower()
            
            # Count control structures
            for pattern in control_patterns:
                if pattern in line_stripped:
                    metrics.control_structures += 1
                    break
            
            # Estimate nesting depth using braces
            brace_nesting += line.count('{') - line.count('}')
            max_nesting = max(max_nesting, brace_nesting)
        
        metrics.nesting_depth = max_nesting
        metrics.cyclomatic_complexity = metrics.control_structures
        
        # File size penalty
        if len(lines) > 100:
            metrics.file_size_penalty = 5
        elif len(lines) > 50:
            metrics.file_size_penalty = 2
        
        metrics.total_score = (
            metrics.cyclomatic_complexity +
            metrics.nesting_depth +
            metrics.file_size_penalty
        )
        
        return metrics


class GenericASTAnalyzer(ASTAnalyzer):
    """Generic fallback analyzer for unsupported languages."""
    
    def supports_language(self, file_extension: str) -> bool:
        """This analyzer supports all languages as fallback."""
        return True
    
    def analyze(self, code: str, file_path: str) -> ComplexityMetrics:
        """Generic analysis using basic pattern matching."""
        metrics = ComplexityMetrics()
        lines = code.split('\n')
        
        # Generic control structure patterns
        control_patterns = [
            'if', 'for', 'while', 'switch', 'case', 'try', 'catch',
            'function', 'def', 'class', 'struct', 'enum'
        ]
        
        bracket_nesting = 0
        max_nesting = 0
        
        for line in lines:
            line_stripped = line.strip().lower()
            
            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith(('//','#', '/*', '*')):
                continue
            
            # Count control structures
            for pattern in control_patterns:
                if pattern in line_stripped:
                    metrics.control_structures += 1
                    break
            
            # Estimate nesting using brackets
            bracket_nesting += line.count('{') - line.count('}')
            bracket_nesting += line.count('[') - line.count(']')
            bracket_nesting += line.count('(') - line.count(')')
            max_nesting = max(max_nesting, bracket_nesting)
        
        metrics.nesting_depth = max(max_nesting, 0)
        metrics.cyclomatic_complexity = metrics.control_structures
        
        # File size penalty
        if len(lines) > 100:
            metrics.file_size_penalty = 5
        elif len(lines) > 50:
            metrics.file_size_penalty = 2
        
        metrics.total_score = (
            metrics.cyclomatic_complexity +
            metrics.nesting_depth +
            metrics.file_size_penalty
        )
        
        return metrics


class ASTComplexityAnalyzer:
    """Main AST-based complexity analyzer with caching and multi-language support."""
    
    def __init__(self):
        self.analyzers = [
            PythonASTAnalyzer(),
            JavaScriptASTAnalyzer(),
            GenericASTAnalyzer()  # Always last as fallback
        ]
        self.cache_enabled = True
    
    def analyze_file(self, file_path: str) -> ComplexityMetrics:
        """Analyze a single file and return complexity metrics."""
        if not os.path.exists(file_path):
            return ComplexityMetrics()
        
        # Check cache first
        if self.cache_enabled:
            cached_result = self._get_cached_result(file_path)
            if cached_result:
                return cached_result
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except (UnicodeDecodeError, IOError):
            return ComplexityMetrics()
        
        # Find appropriate analyzer
        file_extension = os.path.splitext(file_path)[1]
        analyzer = self._get_analyzer(file_extension)
        
        # Analyze code
        metrics = analyzer.analyze(code, file_path)
        
        # Cache result
        if self.cache_enabled:
            self._cache_result(file_path, code, metrics)
        
        return metrics
    
    def analyze_files(self, file_paths: List[str]) -> Dict[str, ComplexityMetrics]:
        """Analyze multiple files and return aggregated metrics."""
        results = {}
        
        for file_path in file_paths:
            results[file_path] = self.analyze_file(file_path)
        
        return results
    
    def get_aggregated_score(self, file_paths: List[str]) -> int:
        """Get aggregated complexity score for multiple files."""
        total_score = 0
        file_results = self.analyze_files(file_paths)
        
        for metrics in file_results.values():
            total_score += metrics.total_score
        
        # Cap at maximum static score
        return min(total_score, 40)
    
    def _get_analyzer(self, file_extension: str) -> ASTAnalyzer:
        """Get the appropriate analyzer for a file extension."""
        for analyzer in self.analyzers:
            if analyzer.supports_language(file_extension):
                return analyzer
        
        # Should never reach here since GenericASTAnalyzer supports all
        return self.analyzers[-1]
    
    @lru_cache(maxsize=100)
    def _get_cached_result(self, file_path: str) -> Optional[ComplexityMetrics]:
        """Get cached analysis result if available and valid."""
        cache_key = self._get_cache_key(file_path)
        cache_file = f"/tmp/ast_cache_{cache_key}.json"
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid (file not modified)
            if cached_data.get('file_hash') == self._get_file_hash(file_path):
                metrics = ComplexityMetrics()
                metrics.__dict__.update(cached_data['metrics'])
                return metrics
        except (json.JSONDecodeError, KeyError, IOError):
            pass
        
        return None
    
    def _cache_result(self, file_path: str, _code: str, metrics: ComplexityMetrics) -> None:
        """Cache analysis result for future use."""
        cache_key = self._get_cache_key(file_path)
        cache_file = f"/tmp/ast_cache_{cache_key}.json"
        
        cache_data = {
            'file_hash': self._get_file_hash(file_path),
            'metrics': metrics.to_dict()
        }
        
        try:
            os.makedirs("/tmp", exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except IOError:
            pass  # Caching is optional
    
    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key for a file."""
        return hashlib.md5(file_path.encode()).hexdigest()
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of file content for cache validation."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except IOError:
            return ""


# Global instance for use in cognitive analysis
ast_analyzer = ASTComplexityAnalyzer()
