"""
Cognitive Complexity Analyzer for Pull Request Review Automation

This module implements a multi-dimensional scoring system to automatically
determine appropriate review tiers and automation levels for pull requests.

For detailed scoring documentation, see: docs/cognitive_scoring.md

The analyzer combines AST-based static code analysis, impact assessment, and AI-powered
complexity evaluation to assign cognitive scores and review tiers.
"""

import ast
import re
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
from .ai_client_factory import AIClientFactory
from .ast_analyzer import ast_analyzer

@dataclass
class CognitiveScore:
    static_score: int
    impact_score: int
    ai_score: int
    total_score: int
    tier: int
    reasoning: str
    quality_penalty: int = 0
    ast_metrics: Optional[Dict] = None  # Detailed AST analysis breakdown

# Scoring Constants
class ScoringThresholds:
    """Constants for cognitive complexity scoring thresholds"""
    
    # Score Caps
    STATIC_SCORE_MAX = 40
    IMPACT_SCORE_MAX = 30  
    AI_SCORE_MAX = 30
    STATIC_SCORE_PER_FILE_MAX = 40
    
    # Tier Thresholds
    TIER_0_THRESHOLD = 35  # Auto-merge
    TIER_1_THRESHOLD = 65  # Standard review
    # Tier 2 = anything above TIER_1_THRESHOLD (Expert review)
    
    # Static Scoring
    CONTROL_STRUCTURE_POINTS = 1
    FUNCTION_LENGTH_LARGE_PENALTY = 3  # >50 lines
    FUNCTION_LENGTH_MEDIUM_PENALTY = 1  # >20 lines
    FUNCTION_LENGTH_LARGE_THRESHOLD = 50
    FUNCTION_LENGTH_MEDIUM_THRESHOLD = 20
    
    # Impact Scoring
    IMPORTS_PER_POINT = 5  # 1 point per 5 imports
    IMPORTS_MAX_POINTS = 5
    DATABASE_API_POINTS = 3
    
    # AI Scoring (Heuristic fallback)
    COMPLEX_PATTERN_POINTS = 5
    BUSINESS_LOGIC_POINTS = 3
    DATA_STRUCTURE_POINTS = 2
    
    # Generic Language Analysis
    BRACKETS_PER_POINT = 3  # 1 point per 3 brackets
    LARGE_FILE_THRESHOLD = 100
    LARGE_FILE_PENALTY = 5
    MEDIUM_FILE_THRESHOLD = 50
    MEDIUM_FILE_PENALTY = 2

class CognitiveAnalyzer:
    def __init__(self):
        # Initialize AI client if available, but don't fail without it
        try:
            # Validate configuration
            AIClientFactory.validate_config()
            
            # Initialize AI Foundry client
            self.ai_client = AIClientFactory.create_client()
        except Exception:
            # Continue without AI client - AST analysis will still work
            self.ai_client = None
        
        self.file_impact_weights = {
            'migration': 10, 'schema': 10, 'api': 8, 'config': 6,
            'security': 8, 'payment': 9, 'test': 2, 'doc': 1
        }
    
    def _get_model_name(self) -> str:
        """Get the model deployment name"""
        if self.ai_client:
            return AIClientFactory.get_model_name()
        return "unavailable"
    
    def analyze_pr(self, pr_files: List[Dict], quality_penalty: int = 0) -> CognitiveScore:
        """Main entry point for analyzing a PR's cognitive complexity"""
        static_score = self._calculate_static_score(pr_files)
        impact_score = self._calculate_impact_score(pr_files)
        ai_score = self._calculate_ai_score(pr_files)
        
        # Capture detailed AST metrics for PR comments
        ast_metrics = self._collect_ast_metrics(pr_files)
        
        # Add quality penalty to total score
        total_score = static_score + impact_score + ai_score + quality_penalty
        
        # Check for auto-merge eligibility before tier assignment
        if self._is_auto_merge_eligible(pr_files, total_score):
            tier = 0
        else:
            tier = self._assign_tier(total_score)
            
        reasoning = self._generate_reasoning(static_score, impact_score, ai_score, quality_penalty)
        
        return CognitiveScore(
            static_score=static_score,
            impact_score=impact_score,
            ai_score=ai_score,
            total_score=total_score,
            tier=tier,
            reasoning=reasoning,
            quality_penalty=quality_penalty,
            ast_metrics=ast_metrics
        )
    
    def _calculate_static_score(self, pr_files: List[Dict]) -> int:
        """
        Calculate complexity from AST-based static analysis.
        
        Uses AST-based analysis for precise complexity measurement including:
        - Control structures and cyclomatic complexity
        - Nesting depth calculation
        - Function length penalties
        - Language-specific complexity patterns
        
        Returns: 0-40 points (capped)
        """
        total_score = 0
        
        for file_info in pr_files:
            file_path = file_info['path']
            
            # Use AST analyzer for precise complexity measurement
            metrics = ast_analyzer.analyze_file(file_path)
            score = metrics.total_score
            
            # Cap per file to prevent single complex file from dominating
            total_score += min(score, ScoringThresholds.STATIC_SCORE_PER_FILE_MAX)
        
        return min(total_score, ScoringThresholds.STATIC_SCORE_MAX)
    
    def _collect_ast_metrics(self, pr_files: List[Dict]) -> Dict:
        """
        Collect detailed AST metrics for each file for PR comments.
        
        Returns comprehensive breakdown of complexity metrics per file.
        """
        file_metrics = {}
        total_metrics = {
            'total_cyclomatic_complexity': 0,
            'max_nesting_depth': 0,
            'total_functions': 0,
            'total_control_structures': 0,
            'complex_files': []
        }
        
        for file_info in pr_files:
            file_path = file_info['path']
            
            # Get detailed AST metrics
            metrics = ast_analyzer.analyze_file(file_path)
            
            file_data = {
                'path': file_path,
                'language': file_info.get('language', 'unknown'),
                'total_score': metrics.total_score,
                'cyclomatic_complexity': metrics.cyclomatic_complexity,
                'nesting_depth': metrics.nesting_depth,
                'function_count': metrics.function_count,
                'control_structures': metrics.control_structures,
                'function_length_penalty': metrics.function_length_penalty,
                'file_size_penalty': metrics.file_size_penalty
            }
            
            file_metrics[file_path] = file_data
            
            # Update totals
            total_metrics['total_cyclomatic_complexity'] += metrics.cyclomatic_complexity
            total_metrics['max_nesting_depth'] = max(total_metrics['max_nesting_depth'], metrics.nesting_depth)
            total_metrics['total_functions'] += metrics.function_count
            total_metrics['total_control_structures'] += metrics.control_structures
            
            # Flag complex files for special attention
            if metrics.total_score > 15:
                total_metrics['complex_files'].append({
                    'path': file_path,
                    'score': metrics.total_score,
                    'main_issues': self._identify_complexity_issues(metrics)
                })
        
        return {
            'files': file_metrics,
            'summary': total_metrics
        }
    
    def _identify_complexity_issues(self, metrics) -> List[str]:
        """Identify the main complexity issues in a file."""
        issues = []
        
        if metrics.cyclomatic_complexity > 10:
            issues.append(f"High cyclomatic complexity ({metrics.cyclomatic_complexity})")
        
        if metrics.nesting_depth > 4:
            issues.append(f"Deep nesting ({metrics.nesting_depth} levels)")
        
        if metrics.function_length_penalty > 1:
            issues.append("Long functions detected")
        
        if metrics.control_structures > 15:
            issues.append(f"Many control structures ({metrics.control_structures})")
        
        if not issues:
            issues.append("Multiple complexity factors")
        
        return issues
    
    def _calculate_impact_score(self, pr_files: List[Dict]) -> int:
        """
        Calculate impact based on files changed and blast radius.
        
        Scoring breakdown:
        - File type weights: Migration(10), Schema(10), Payment(9), API(8), Security(8), Config(6), Test(2), Doc(1)
        - Dependencies: +1 per 5 imports (max +5)
        - External integrations: +3 for database/API keywords
        
        Returns: 0-30 points (capped)
        """
        impact_score = 0
        
        for file_info in pr_files:
            file_path = file_info['path'].lower()
            
            # File type impact weights
            for pattern, weight in self.file_impact_weights.items():
                if pattern in file_path:
                    impact_score += weight
                    break
            
            # Cross-module dependencies (import counting)
            imports = self._count_imports(file_info['content'])
            dependency_points = min(imports // ScoringThresholds.IMPORTS_PER_POINT, 
                                  ScoringThresholds.IMPORTS_MAX_POINTS)
            impact_score += dependency_points
            
            # Database/API integration changes
            if any(keyword in file_info['content'].lower() 
                   for keyword in ['database', 'db.', 'api.', 'fetch(', 'axios']):
                impact_score += ScoringThresholds.DATABASE_API_POINTS
        
        return min(impact_score, ScoringThresholds.IMPACT_SCORE_MAX)
    
    def _calculate_ai_score(self, pr_files: List[Dict]) -> int:
        """
        Use AI Foundry to assess code comprehension difficulty.
        
        AI evaluates:
        - Comprehension difficulty
        - Business rule complexity  
        - Unusual patterns or anti-patterns
        - Required domain knowledge
        
        Falls back to heuristic scoring if AI unavailable.
        
        Returns: 0-30 points (capped)
        """
        if not self.ai_client:
            return self._heuristic_ai_score(pr_files)
            
        try:
            # Combine changed code for analysis (limit for API constraints)
            combined_code = "\n".join([f['content'] for f in pr_files[:3]])
            
            prompt = f"""
            Analyze this code change for cognitive complexity. Rate 0-30 based on:
            - How difficult is this to understand?
            - Are there complex business rules or algorithms?
            - Does this use unusual patterns or anti-patterns?
            - How much domain knowledge is required?
            
            Code:
            {combined_code[:2000]}  # Truncate for API limits
            
            Respond with just a number 0-30.
            """
            
            # Make AI Foundry request
            from azure.ai.inference.models import UserMessage
            messages = [UserMessage(prompt)]
            model_name = self._get_model_name()
            
            response = self.ai_client.complete(
                messages=messages,
                model=model_name,
                max_tokens=10,
                temperature=0.1
            )
            
            # Extract numeric score from response
            score = int(re.search(r'\d+', response.choices[0].message.content).group())
            return min(max(score, 0), ScoringThresholds.AI_SCORE_MAX)
            
        except Exception as e:
            print(f"AI analysis failed: {e}, falling back to heuristic scoring")
            return self._heuristic_ai_score(pr_files)
    
    def _heuristic_ai_score(self, pr_files: List[Dict]) -> int:
        """
        Fallback heuristic scoring when AI is unavailable.
        
        Pattern-based scoring:
        - Complex patterns (+5): algorithm, recursive, optimization, performance, threading, async, promise, callback
        - Business logic (+3): pricing, payment, billing, discount, tax, inventory, order, subscription  
        - Data structures (+2): nested, recursive, tree, graph, matrix
        
        Returns: 0-30 points (capped)
        """
        score = 0
        
        for file_info in pr_files:
            content = file_info['content'].lower()
            
            # Complex algorithmic patterns that indicate higher cognitive load
            complex_patterns = [
                'algorithm', 'recursive', 'optimization', 'performance',
                'threading', 'async', 'promise', 'callback'
            ]
            if any(pattern in content for pattern in complex_patterns):
                score += ScoringThresholds.COMPLEX_PATTERN_POINTS
            
            # Business logic indicators requiring domain knowledge
            business_patterns = [
                'pricing', 'payment', 'billing', 'discount', 'tax',
                'inventory', 'order', 'subscription'
            ]
            if any(pattern in content for pattern in business_patterns):
                score += ScoringThresholds.BUSINESS_LOGIC_POINTS
                
            # Complex data structure manipulation
            data_structure_patterns = [
                'nested', 'recursive', 'tree', 'graph', 'matrix'
            ]
            if any(pattern in content for pattern in data_structure_patterns):
                score += ScoringThresholds.DATA_STRUCTURE_POINTS
        
        return min(score, ScoringThresholds.AI_SCORE_MAX)
    
    def _is_auto_merge_eligible(self, pr_files: List[Dict], total_score: int) -> bool:
        """
        Check if PR is eligible for auto-merge (Tier 0).
        
        Additional checks beyond just total score to ensure safety:
        - Must be below Tier 0 threshold
        - No high-impact files (migrations, schemas, security)
        - No complex individual files
        - Limited number of files changed
        
        Args:
            pr_files: List of changed files with metadata
            total_score: Combined total score (before tier assignment)
            
        Returns:
            bool: True if eligible for auto-merge, False otherwise
        """
        # Must meet basic threshold requirement
        if total_score > ScoringThresholds.TIER_0_THRESHOLD:
            return False
            
        # Limit number of changed files for auto-merge
        if len(pr_files) > 5:
            return False
            
        # Check for high-impact file types that should never auto-merge
        high_impact_patterns = ['migration', 'schema', 'security', 'payment']
        for file_info in pr_files:
            file_path = file_info['path'].lower()
            if any(pattern in file_path for pattern in high_impact_patterns):
                return False
                
        # Check individual file complexity (prevent one complex file from sneaking through)
        for file_info in pr_files:
            file_path = file_info['path']
            
            # Use AST analyzer for precise complexity measurement
            metrics = ast_analyzer.analyze_file(file_path)
            file_complexity = metrics.total_score
                
            # If any single file is too complex, require human review
            if file_complexity > 15:
                return False
                
        return True
    
    def _assign_tier(self, total_score: int) -> int:
        """
        Assign review tier based on total cognitive score.
        
        Tier 0 (Auto-merge): ≤ 35 points
        - Automated merge on CI success
        - No human review required
        - Simple utility functions, docs, configs
        
        Tier 1 (Standard Review): 36-65 points
        - Standard peer review required  
        - 1-2 reviewers needed
        - Most feature development
        
        Tier 2 (Expert Review): 66+ points
        - Senior/expert review required
        - Domain expertise needed
        - Complex algorithms, critical systems
        
        Args:
            total_score: Combined static + impact + AI + quality penalty score
            
        Returns:
            int: Review tier (0, 1, or 2)
        """
        if total_score <= ScoringThresholds.TIER_0_THRESHOLD:
            return 0
        elif total_score <= ScoringThresholds.TIER_1_THRESHOLD:
            return 1
        else:
            return 2
    
    def _calculate_nesting_depth(self, node) -> int:
        """Calculate maximum nesting depth in AST node - deprecated, use AST analyzer instead"""
        # This method is kept for compatibility but should use AST analyzer
        max_depth = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                depth = 1
                parent = child
                while hasattr(parent, 'parent'):
                    if isinstance(parent.parent, (ast.If, ast.For, ast.While, ast.With)):
                        depth += 1
                    parent = parent.parent
                max_depth = max(max_depth, depth)
        return max_depth
    
    def _count_imports(self, content: str) -> int:
        """Count import statements in code"""
        import_patterns = [
            r'^\s*import\s+',  # Python/JS imports
            r'^\s*from\s+.*\s+import',  # Python from imports
            r'^\s*#include\s+',  # C/C++ includes
            r'^\s*using\s+',  # C# using
            r'^\s*require\s*\(',  # Node.js requires
        ]
        
        count = 0
        for line in content.splitlines():
            for pattern in import_patterns:
                if re.match(pattern, line):
                    count += 1
                    break
        
        return count
    
    def _generate_reasoning(self, static: int, impact: int, ai: int, quality_penalty: int = 0) -> str:
        """Generate human-readable explanation of scoring"""
        reasons = []
        
        if static > 20:
            reasons.append(f"High static complexity ({static}/40)")
        if impact > 15:
            reasons.append(f"Significant impact surface ({impact}/30)")
        if ai > 20:
            reasons.append(f"AI flagged as complex ({ai}/30)")
        if quality_penalty > 0:
            reasons.append(f"Quality penalty applied (+{quality_penalty})")
            
        if not reasons:
            return "Low complexity change, suitable for automated review"
        
        return "Requires human review: " + ", ".join(reasons)
