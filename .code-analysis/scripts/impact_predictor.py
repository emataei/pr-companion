#!/usr/bin/env python3
"""
Smart Change Impact Prediction
Analyzes code changes and predicts their downstream effects and potential issues.
"""

import os
import sys
import json
import re
import ast
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess

# Add .code-analysis to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scoring.ai_client_factory import AIClientFactory
    AI_CLIENT_AVAILABLE = True
except ImportError:
    AI_CLIENT_AVAILABLE = False

class ImpactSeverity(Enum):
    """Impact severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ImpactCategory(Enum):
    """Categories of impact"""
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPATIBILITY = "compatibility"
    USER_EXPERIENCE = "user_experience"
    DATA_INTEGRITY = "data_integrity"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    EXTERNAL_DEPENDENCIES = "external_dependencies"

@dataclass
class ImpactPrediction:
    """A predicted impact from a change"""
    category: ImpactCategory
    severity: ImpactSeverity
    description: str
    confidence: float
    affected_components: List[str]
    recommended_actions: List[str]
    risk_factors: List[str]
    mitigation_strategies: List[str]

@dataclass
class TestRecommendation:
    """Recommendation for specific tests to run"""
    test_type: str  # 'unit', 'integration', 'e2e', 'performance', 'security'
    priority: str   # 'high', 'medium', 'low'
    description: str
    specific_tests: List[str]
    reasoning: str

@dataclass
class ChangeImpactAnalysis:
    """Complete impact analysis for a set of changes"""
    impacts: List[ImpactPrediction]
    test_recommendations: List[TestRecommendation]
    overall_risk_score: float
    deployment_readiness: str
    monitoring_suggestions: List[str]
    rollback_considerations: List[str]
    summary: str

@dataclass
class CodeElement:
    """Represents a code element (function, class, etc.) and its metadata"""
    name: str
    type: str  # 'function', 'class', 'variable', 'import'
    file_path: str
    line_number: int
    dependencies: Set[str]
    is_public_api: bool
    complexity_score: float
    usage_frequency: int  # How often this element is used

class ImpactPredictor:
    """Predicts the impact of code changes using AI and static analysis"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.ai_client = None
        self.model_name = None
        
        if AI_CLIENT_AVAILABLE:
            try:
                AIClientFactory.validate_config()
                self.ai_client = AIClientFactory.create_client()
                self.model_name = AIClientFactory.get_model_name()
            except Exception as e:
                print(f"Warning: AI client not available: {e}")
    
    def analyze_change_impact(self, file_changes: List[Dict], 
                            pr_context: Optional[Dict] = None) -> ChangeImpactAnalysis:
        """Analyze the potential impact of code changes"""
        
        # Extract code elements from changes
        code_elements = self._extract_code_elements(file_changes)
        
        # Analyze dependencies and usage patterns
        dependency_analysis = self._analyze_dependencies(code_elements)
        
        # Generate AI-powered impact predictions
        if self.ai_client:
            ai_impacts = self._get_ai_impact_predictions(file_changes, code_elements, pr_context)
        else:
            ai_impacts = []
        
        # Add rule-based impact analysis
        rule_based_impacts = self._get_rule_based_impacts(file_changes, code_elements)
        
        # Combine all impact predictions
        all_impacts = ai_impacts + rule_based_impacts
        
        # Generate test recommendations
        test_recommendations = self._generate_test_recommendations(
            file_changes, code_elements, all_impacts
        )
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(all_impacts)
        
        # Generate monitoring and deployment suggestions
        monitoring_suggestions = self._generate_monitoring_suggestions(all_impacts, code_elements)
        rollback_considerations = self._generate_rollback_considerations(all_impacts, file_changes)
        
        # Determine deployment readiness
        deployment_readiness = self._assess_deployment_readiness(risk_score, all_impacts)
        
        # Generate summary
        summary = self._generate_impact_summary(all_impacts, risk_score)
        
        return ChangeImpactAnalysis(
            impacts=all_impacts,
            test_recommendations=test_recommendations,
            overall_risk_score=risk_score,
            deployment_readiness=deployment_readiness,
            monitoring_suggestions=monitoring_suggestions,
            rollback_considerations=rollback_considerations,
            summary=summary
        )
    
    def _extract_code_elements(self, file_changes: List[Dict]) -> List[CodeElement]:
        """Extract code elements from changed files"""
        elements = []
        
        for change in file_changes:
            file_path = change.get('file_path', '')
            
            if file_path.endswith('.py'):
                elements.extend(self._extract_python_elements(change))
            elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
                elements.extend(self._extract_typescript_elements(change))
        
        return elements
    
    def _extract_python_elements(self, file_change: Dict) -> List[CodeElement]:
        """Extract Python code elements from a file change"""
        elements = []
        
        try:
            # Get the current content of the file
            file_path = self.repo_path / file_change['file_path']
            if not file_path.exists():
                return elements
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    elements.append(CodeElement(
                        name=node.name,
                        type='function',
                        file_path=str(file_path),
                        line_number=node.lineno,
                        dependencies=self._extract_function_dependencies(node),
                        is_public_api=not node.name.startswith('_'),
                        complexity_score=self._calculate_function_complexity(node),
                        usage_frequency=0  # Would need cross-reference analysis
                    ))
                elif isinstance(node, ast.ClassDef):
                    elements.append(CodeElement(
                        name=node.name,
                        type='class',
                        file_path=str(file_path),
                        line_number=node.lineno,
                        dependencies=set(),
                        is_public_api=not node.name.startswith('_'),
                        complexity_score=len(node.body),
                        usage_frequency=0
                    ))
        
        except Exception as e:
            print(f"Error extracting Python elements from {file_change['file_path']}: {e}")
        
        return elements
    
    def _extract_typescript_elements(self, file_change: Dict) -> List[CodeElement]:
        """Extract TypeScript/JavaScript elements from a file change"""
        elements = []
        
        try:
            file_path = self.repo_path / file_change['file_path']
            if not file_path.exists():
                return elements
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex-based extraction (could be enhanced with proper AST parsing)
            
            # Extract function declarations
            function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\('
            for match in re.finditer(function_pattern, content):
                line_number = content[:match.start()].count('\n') + 1
                elements.append(CodeElement(
                    name=match.group(1),
                    type='function',
                    file_path=str(file_path),
                    line_number=line_number,
                    dependencies=set(),
                    is_public_api='export' in match.group(0),
                    complexity_score=1.0,
                    usage_frequency=0
                ))
            
            # Extract class declarations
            class_pattern = r'(?:export\s+)?class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                line_number = content[:match.start()].count('\n') + 1
                elements.append(CodeElement(
                    name=match.group(1),
                    type='class',
                    file_path=str(file_path),
                    line_number=line_number,
                    dependencies=set(),
                    is_public_api='export' in match.group(0),
                    complexity_score=1.0,
                    usage_frequency=0
                ))
            
            # Extract React components
            component_pattern = r'(?:export\s+)?const\s+(\w+)\s*[=:]\s*(?:\([^)]*\)\s*=>\s*{|\([^)]*\)\s*=>\s*\()'
            for match in re.finditer(component_pattern, content):
                line_number = content[:match.start()].count('\n') + 1
                elements.append(CodeElement(
                    name=match.group(1),
                    type='component',
                    file_path=str(file_path),
                    line_number=line_number,
                    dependencies=set(),
                    is_public_api='export' in match.group(0),
                    complexity_score=1.0,
                    usage_frequency=0
                ))
        
        except Exception as e:
            print(f"Error extracting TypeScript elements from {file_change['file_path']}: {e}")
        
        return elements
    
    def _extract_function_dependencies(self, node: ast.FunctionDef) -> Set[str]:
        """Extract dependencies of a Python function"""
        dependencies = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name):
                        dependencies.add(child.func.value.id)
        
        return dependencies
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> float:
        """Calculate McCabe complexity for a function"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _analyze_dependencies(self, code_elements: List[CodeElement]) -> Dict:
        """Analyze dependency relationships between code elements"""
        
        # Build dependency graph
        dependency_graph = {}
        for element in code_elements:
            dependency_graph[element.name] = list(element.dependencies)
        
        # Find high-impact elements (many dependents)
        dependents = {}
        for element_name, deps in dependency_graph.items():
            for dep in deps:
                if dep not in dependents:
                    dependents[dep] = []
                dependents[dep].append(element_name)
        
        return {
            'dependency_graph': dependency_graph,
            'high_impact_elements': {k: v for k, v in dependents.items() if len(v) > 2},
            'total_elements': len(code_elements),
            'public_api_elements': len([e for e in code_elements if e.is_public_api])
        }
    
    def _get_ai_impact_predictions(self, file_changes: List[Dict], 
                                  code_elements: List[CodeElement],
                                  pr_context: Optional[Dict]) -> List[ImpactPrediction]:
        """Get AI-powered impact predictions"""
        
        # Prepare context for AI
        context = self._prepare_impact_analysis_context(file_changes, code_elements, pr_context)
        
        # Get AI analysis
        ai_response = self._get_ai_impact_analysis(context)
        
        # Parse response into impact predictions
        return self._parse_ai_impact_response(ai_response)
    
    def _prepare_impact_analysis_context(self, file_changes: List[Dict], 
                                       code_elements: List[CodeElement],
                                       pr_context: Optional[Dict]) -> str:
        """Prepare context for AI impact analysis"""
        
        context_parts = []
        
        # Add PR context if available
        if pr_context:
            context_parts.append(f"PR Title: {pr_context.get('title', '')}")
            context_parts.append(f"PR Description: {pr_context.get('description', '')}")
        
        # Add file changes summary
        context_parts.append("\nFile Changes:")
        for change in file_changes[:10]:  # Limit to first 10 files
            context_parts.append(
                f"  {change.get('change_type', 'modified')}: {change.get('file_path', '')} "
                f"(+{change.get('lines_added', 0)}/-{change.get('lines_removed', 0)})"
            )
        
        # Add code elements information
        if code_elements:
            context_parts.append(f"\nCode Elements Modified ({len(code_elements)} total):")
            public_elements = [e for e in code_elements if e.is_public_api]
            if public_elements:
                context_parts.append("  Public API elements:")
                for element in public_elements[:5]:
                    context_parts.append(f"    {element.type}: {element.name}")
        
        # Add key file patterns
        file_patterns = self._analyze_file_patterns(file_changes)
        if file_patterns:
            context_parts.append(f"\nAffected Areas: {', '.join(file_patterns)}")
        
        return '\n'.join(context_parts)
    
    def _analyze_file_patterns(self, file_changes: List[Dict]) -> List[str]:
        """Analyze file patterns to determine affected areas"""
        patterns = set()
        
        for change in file_changes:
            file_path = change.get('file_path', '').lower()
            
            if any(pattern in file_path for pattern in ['/api/', '/routes/', 'api.', 'route.']):
                patterns.add('API')
            if any(pattern in file_path for pattern in ['.tsx', '.jsx', 'component']):
                patterns.add('UI Components')
            if any(pattern in file_path for pattern in ['/auth', 'auth.', 'login', 'permission']):
                patterns.add('Authentication')
            if any(pattern in file_path for pattern in ['/db', '/database', '/migration', '.sql']):
                patterns.add('Database')
            if any(pattern in file_path for pattern in ['/test', '.test.', '.spec.']):
                patterns.add('Tests')
            if any(pattern in file_path for pattern in ['/config', '.env', 'dockerfile']):
                patterns.add('Configuration')
        
        return list(patterns)
    
    def _get_ai_impact_analysis(self, context: str) -> str:
        """Get AI analysis of potential impacts"""
        
        system_prompt = """You are an expert software architect analyzing code changes to predict their potential impacts. 

Analyze the provided changes and predict potential impacts across these categories:
- PERFORMANCE: Effects on speed, memory usage, or scalability
- SECURITY: Security implications or vulnerabilities  
- COMPATIBILITY: Breaking changes or backward compatibility issues
- USER_EXPERIENCE: Impact on end-user functionality or experience
- DATA_INTEGRITY: Risks to data consistency or corruption
- RELIABILITY: Effects on system stability or error handling
- MAINTAINABILITY: Impact on code quality and future development
- TESTING: Testing requirements or coverage changes
- DEPLOYMENT: Deployment risks or requirements
- EXTERNAL_DEPENDENCIES: Impact on external services or APIs

For each potential impact, provide:
- Category and severity (low/medium/high/critical)
- Description of the impact
- Confidence level (0.0-1.0)
- Affected components
- Recommended actions
- Risk factors
- Mitigation strategies

Return your analysis as a JSON array of impact predictions:
[
  {
    "category": "PERFORMANCE",
    "severity": "medium", 
    "description": "Database query changes may increase response times",
    "confidence": 0.75,
    "affected_components": ["user API", "dashboard"],
    "recommended_actions": ["Load testing", "Query optimization review"],
    "risk_factors": ["High user traffic during peak hours"],
    "mitigation_strategies": ["Database indexing", "Query caching", "Gradual rollout"]
  }
]

Focus on the most likely and impactful scenarios. Be specific about technical risks."""

        try:
            response = self.ai_client.complete(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error getting AI impact analysis: {e}")
            return "[]"
    
    def _parse_ai_impact_response(self, ai_response: str) -> List[ImpactPrediction]:
        """Parse AI response into impact predictions"""
        
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                impact_data = json.loads(json_match.group())
            else:
                return []
            
            impacts = []
            for item in impact_data:
                try:
                    impact = ImpactPrediction(
                        category=ImpactCategory(item.get('category', 'maintainability').lower()),
                        severity=ImpactSeverity(item.get('severity', 'low').lower()),
                        description=item.get('description', ''),
                        confidence=float(item.get('confidence', 0.5)),
                        affected_components=item.get('affected_components', []),
                        recommended_actions=item.get('recommended_actions', []),
                        risk_factors=item.get('risk_factors', []),
                        mitigation_strategies=item.get('mitigation_strategies', [])
                    )
                    impacts.append(impact)
                except (ValueError, KeyError) as e:
                    print(f"Error parsing impact item: {e}")
                    continue
            
            return impacts
            
        except Exception as e:
            print(f"Error parsing AI impact response: {e}")
            return []
    
    def _get_rule_based_impacts(self, file_changes: List[Dict], 
                               code_elements: List[CodeElement]) -> List[ImpactPrediction]:
        """Generate rule-based impact predictions"""
        
        impacts = []
        
        # Check for high-risk file patterns
        for change in file_changes:
            file_path = change.get('file_path', '').lower()
            
            # Database-related changes
            if any(pattern in file_path for pattern in ['/migration', '.sql', '/schema']):
                impacts.append(ImpactPrediction(
                    category=ImpactCategory.DATA_INTEGRITY,
                    severity=ImpactSeverity.HIGH,
                    description="Database schema changes require careful testing",
                    confidence=0.9,
                    affected_components=["database", "data layer"],
                    recommended_actions=["Database migration testing", "Backup verification"],
                    risk_factors=["Data corruption", "Downtime during migration"],
                    mitigation_strategies=["Rollback plan", "Staged deployment", "Data backup"]
                ))
            
            # Authentication changes
            if any(pattern in file_path for pattern in ['/auth', 'login', 'password', 'security']):
                impacts.append(ImpactPrediction(
                    category=ImpactCategory.SECURITY,
                    severity=ImpactSeverity.HIGH,
                    description="Authentication changes require security review",
                    confidence=0.85,
                    affected_components=["authentication", "user management"],
                    recommended_actions=["Security testing", "Penetration testing"],
                    risk_factors=["Unauthorized access", "Authentication bypass"],
                    mitigation_strategies=["Security audit", "Access logging", "Multi-factor authentication"]
                ))
            
            # API changes
            if any(pattern in file_path for pattern in ['/api/', '/routes', 'api.']):
                impacts.append(ImpactPrediction(
                    category=ImpactCategory.COMPATIBILITY,
                    severity=ImpactSeverity.MEDIUM,
                    description="API changes may affect client applications",
                    confidence=0.7,
                    affected_components=["API", "client applications"],
                    recommended_actions=["API contract testing", "Client compatibility check"],
                    risk_factors=["Breaking changes", "Client application failures"],
                    mitigation_strategies=["API versioning", "Backward compatibility", "Client notification"]
                ))
        
        # Check for public API element changes
        public_elements = [e for e in code_elements if e.is_public_api]
        if public_elements:
            impacts.append(ImpactPrediction(
                category=ImpactCategory.COMPATIBILITY,
                severity=ImpactSeverity.MEDIUM,
                description=f"Changes to {len(public_elements)} public API elements",
                confidence=0.8,
                affected_components=[e.name for e in public_elements],
                recommended_actions=["API compatibility testing", "Documentation updates"],
                risk_factors=["Breaking changes for consumers"],
                mitigation_strategies=["Deprecation notices", "Version management"]
            ))
        
        return impacts
    
    def _generate_test_recommendations(self, file_changes: List[Dict], 
                                     code_elements: List[CodeElement],
                                     impacts: List[ImpactPrediction]) -> List[TestRecommendation]:
        """Generate test recommendations based on changes and impacts"""
        
        recommendations = []
        
        # Based on file patterns
        file_patterns = self._analyze_file_patterns(file_changes)
        
        if 'API' in file_patterns:
            recommendations.append(TestRecommendation(
                test_type='integration',
                priority='high',
                description='Test API endpoints for functionality and contracts',
                specific_tests=['API integration tests', 'Contract tests'],
                reasoning='API changes detected that could affect client integrations'
            ))
        
        if 'Authentication' in file_patterns:
            recommendations.append(TestRecommendation(
                test_type='security',
                priority='high', 
                description='Security testing for authentication flows',
                specific_tests=['Authentication flow tests', 'Authorization tests', 'Session management tests'],
                reasoning='Authentication changes require thorough security validation'
            ))
        
        if 'Database' in file_patterns:
            recommendations.append(TestRecommendation(
                test_type='integration',
                priority='high',
                description='Database integration and migration testing',
                specific_tests=['Migration tests', 'Data integrity tests', 'Performance tests'],
                reasoning='Database changes require data integrity validation'
            ))
        
        # Based on impact predictions
        for impact in impacts:
            if impact.category == ImpactCategory.PERFORMANCE and impact.severity in [ImpactSeverity.HIGH, ImpactSeverity.CRITICAL]:
                recommendations.append(TestRecommendation(
                    test_type='performance',
                    priority='high',
                    description='Performance testing for potential bottlenecks',
                    specific_tests=['Load tests', 'Stress tests', 'Performance regression tests'],
                    reasoning=f'High-impact performance changes detected: {impact.description}'
                ))
        
        return recommendations
    
    def _calculate_risk_score(self, impacts: List[ImpactPrediction]) -> float:
        """Calculate overall risk score (0.0 to 1.0)"""
        
        if not impacts:
            return 0.0
        
        severity_weights = {
            ImpactSeverity.LOW: 0.25,
            ImpactSeverity.MEDIUM: 0.5,
            ImpactSeverity.HIGH: 0.75,
            ImpactSeverity.CRITICAL: 1.0
        }
        
        total_risk = 0.0
        total_weight = 0.0
        
        for impact in impacts:
            weight = severity_weights[impact.severity] * impact.confidence
            total_risk += weight
            total_weight += impact.confidence
        
        if total_weight == 0:
            return 0.0
        
        # Normalize to 0-1 scale
        normalized_risk = min(total_risk / len(impacts), 1.0)
        return round(normalized_risk, 2)
    
    def _generate_monitoring_suggestions(self, impacts: List[ImpactPrediction], 
                                       code_elements: List[CodeElement]) -> List[str]:
        """Generate monitoring suggestions based on impacts"""
        
        suggestions = set()
        
        for impact in impacts:
            if impact.category == ImpactCategory.PERFORMANCE:
                suggestions.add("Monitor API response times and database query performance")
                suggestions.add("Set up alerts for increased error rates")
            
            elif impact.category == ImpactCategory.SECURITY:
                suggestions.add("Monitor authentication failure rates")
                suggestions.add("Track unusual access patterns")
            
            elif impact.category == ImpactCategory.RELIABILITY:
                suggestions.add("Monitor application error rates and crash reports")
                suggestions.add("Track system resource usage")
        
        return list(suggestions)
    
    def _generate_rollback_considerations(self, impacts: List[ImpactPrediction], 
                                        file_changes: List[Dict]) -> List[str]:
        """Generate rollback considerations"""
        
        considerations = set()
        
        # Check for database changes
        has_db_changes = any(
            any(pattern in change.get('file_path', '').lower() 
                for pattern in ['/migration', '.sql', '/schema'])
            for change in file_changes
        )
        
        if has_db_changes:
            considerations.add("Database rollback plan required - ensure migration reversibility")
        
        # Check for high-impact changes
        critical_impacts = [i for i in impacts if i.severity == ImpactSeverity.CRITICAL]
        if critical_impacts:
            considerations.add("Critical impact changes - prepare immediate rollback capability")
        
        # Check for API changes
        has_api_changes = any(
            any(pattern in change.get('file_path', '').lower() 
                for pattern in ['/api/', '/routes'])
            for change in file_changes
        )
        
        if has_api_changes:
            considerations.add("API changes - coordinate rollback with client applications")
        
        if not considerations:
            considerations.add("Standard rollback procedures apply")
        
        return list(considerations)
    
    def _assess_deployment_readiness(self, risk_score: float, 
                                   impacts: List[ImpactPrediction]) -> str:
        """Assess deployment readiness based on risk analysis"""
        
        critical_impacts = len([i for i in impacts if i.severity == ImpactSeverity.CRITICAL])
        high_impacts = len([i for i in impacts if i.severity == ImpactSeverity.HIGH])
        
        if critical_impacts > 0:
            return "HOLD - Critical impacts require mitigation before deployment"
        elif risk_score > 0.8 or high_impacts > 2:
            return "CAUTION - High risk deployment, consider staged rollout"
        elif risk_score > 0.5:
            return "READY - Medium risk, standard deployment precautions"
        else:
            return "READY - Low risk deployment"
    
    def _generate_impact_summary(self, impacts: List[ImpactPrediction], 
                               risk_score: float) -> str:
        """Generate a summary of the impact analysis"""
        
        if not impacts:
            return "No significant impacts identified. Standard review and testing recommended."
        
        # Count impacts by severity
        severity_counts = {}
        for impact in impacts:
            severity_counts[impact.severity] = severity_counts.get(impact.severity, 0) + 1
        
        # Build summary
        summary_parts = [f"Overall risk score: {risk_score:.1%}"]
        
        if severity_counts:
            counts_str = ", ".join([
                f"{count} {severity.value}"
                for severity, count in sorted(severity_counts.items(), 
                                            key=lambda x: ['low', 'medium', 'high', 'critical'].index(x[0].value))
            ])
            summary_parts.append(f"Impact distribution: {counts_str}")
        
        # Highlight key concerns
        high_impact_categories = set()
        for impact in impacts:
            if impact.severity in [ImpactSeverity.HIGH, ImpactSeverity.CRITICAL]:
                high_impact_categories.add(impact.category.value)
        
        if high_impact_categories:
            summary_parts.append(f"Key concerns: {', '.join(high_impact_categories)}")
        
        return ". ".join(summary_parts) + "."

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Predict the impact of code changes')
    parser.add_argument('--repo', required=True, help='Repository path')
    parser.add_argument('--changes-file', help='JSON file with file changes')
    parser.add_argument('--pr-title', help='PR title')
    parser.add_argument('--pr-description', help='PR description')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--pr-output', action='store_true',
                       help='Generate output for PR comment integration')
    
    args = parser.parse_args()
    
    # Load file changes
    if args.changes_file and os.path.exists(args.changes_file):
        with open(args.changes_file, 'r') as f:
            file_changes = json.load(f)
    else:
        # Mock file changes for testing
        file_changes = [
            {
                'file_path': 'src/api/users.py',
                'change_type': 'modified',
                'lines_added': 25,
                'lines_removed': 10
            }
        ]
    
    # Prepare PR context
    pr_context = {}
    if args.pr_title:
        pr_context['title'] = args.pr_title
    if args.pr_description:
        pr_context['description'] = args.pr_description
    
    # Analyze impact
    predictor = ImpactPredictor(args.repo)
    analysis = predictor.analyze_change_impact(file_changes, pr_context)
    
    # Convert to dict for JSON serialization
    result = asdict(analysis)
    
    # Convert enums to strings
    for impact in result['impacts']:
        impact['category'] = impact['category'].value if hasattr(impact['category'], 'value') else str(impact['category'])
        impact['severity'] = impact['severity'].value if hasattr(impact['severity'], 'value') else str(impact['severity'])
    
    # Always generate PR integration file if in GitHub Actions
    if args.pr_output or os.getenv('GITHUB_ACTIONS'):
        pr_output_file = 'impact-prediction-results.json'
        with open(pr_output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"PR integration results written to {pr_output_file}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Impact analysis written to {args.output}")
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
