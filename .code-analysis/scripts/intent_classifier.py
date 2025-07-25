#!/usr/bin/env python3
"""
Intent-based Change Classification
Analyzes git diffs and code changes to determine the intent behind the changes.
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import subprocess

# Add .code-analysis to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scoring.ai_client_factory import AIClientFactory
    AI_CLIENT_AVAILABLE = True
except ImportError:
    AI_CLIENT_AVAILABLE = False

class ChangeIntent(Enum):
    """Enumeration of possible change intents"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    MAINTENANCE = "maintenance"
    STYLE = "style"
    ARCHITECTURE = "architecture"

@dataclass
class IntentClassification:
    """Result of intent classification analysis"""
    primary_intent: ChangeIntent
    confidence: float
    secondary_intents: List[Tuple[ChangeIntent, float]]
    reasoning: str
    affected_areas: List[str]
    business_impact: str
    technical_details: str

@dataclass
class FileChange:
    """Represents a file change with context"""
    file_path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    lines_added: int
    lines_removed: int
    diff_content: str
    file_type: str
    is_test_file: bool

class IntentClassifier:
    """Classifies the intent behind code changes using AI analysis"""
    
    def __init__(self):
        self.ai_client = None
        self.model_name = None
        
        if AI_CLIENT_AVAILABLE:
            try:
                AIClientFactory.validate_config()
                self.ai_client = AIClientFactory.create_client()
                self.model_name = AIClientFactory.get_model_name()
            except Exception as e:
                print(f"Warning: AI client not available: {e}")
    
    def analyze_pr_intent(self, pr_title: str, pr_description: str, 
                         file_changes: List[FileChange]) -> IntentClassification:
        """Analyze the intent of a PR based on title, description, and file changes"""
        
        if not self.ai_client:
            return self._fallback_classification(pr_title, pr_description, file_changes)
        
        # Prepare context for AI analysis
        context = self._prepare_analysis_context(pr_title, pr_description, file_changes)
        
        # Generate AI analysis
        ai_analysis = self._get_ai_intent_analysis(context)
        
        # Parse AI response into structured format
        return self._parse_ai_response(ai_analysis, file_changes)
    
    def _prepare_analysis_context(self, pr_title: str, pr_description: str, 
                                 file_changes: List[FileChange]) -> str:
        """Prepare context string for AI analysis"""
        
        # Summarize file changes
        change_summary = self._summarize_file_changes(file_changes)
        
        # Extract key code snippets
        code_snippets = self._extract_key_code_snippets(file_changes)
        
        context = f"""
PR Analysis Context:

Title: {pr_title}

Description: {pr_description}

File Changes Summary:
{change_summary}

Key Code Changes:
{code_snippets}
        """.strip()
        
        return context
    
    def _summarize_file_changes(self, file_changes: List[FileChange]) -> str:
        """Create a summary of file changes"""
        summary_lines = []
        
        # Group by change type
        by_type = {}
        for change in file_changes:
            if change.change_type not in by_type:
                by_type[change.change_type] = []
            by_type[change.change_type].append(change)
        
        for change_type, changes in by_type.items():
            if change_type == 'added':
                summary_lines.append(f"Added {len(changes)} files:")
                for change in changes[:5]:  # Limit to first 5
                    summary_lines.append(f"  + {change.file_path} ({change.lines_added} lines)")
                if len(changes) > 5:
                    summary_lines.append(f"  ... and {len(changes) - 5} more")
                    
            elif change_type == 'modified':
                summary_lines.append(f"Modified {len(changes)} files:")
                for change in changes[:5]:
                    summary_lines.append(f"  ~ {change.file_path} (+{change.lines_added}/-{change.lines_removed})")
                if len(changes) > 5:
                    summary_lines.append(f"  ... and {len(changes) - 5} more")
                    
            elif change_type == 'deleted':
                summary_lines.append(f"Deleted {len(changes)} files:")
                for change in changes[:5]:
                    summary_lines.append(f"  - {change.file_path}")
                if len(changes) > 5:
                    summary_lines.append(f"  ... and {len(changes) - 5} more")
        
        return '\n'.join(summary_lines)
    
    def _extract_key_code_snippets(self, file_changes: List[FileChange], max_snippets: int = 3) -> str:
        """Extract the most relevant code snippets for analysis"""
        snippets = []
        
        # Prioritize changes by importance
        important_changes = sorted(
            file_changes,
            key=lambda x: (
                len(x.diff_content),  # Larger changes first
                x.lines_added + x.lines_removed,  # More line changes
                not x.is_test_file  # Non-test files first
            ),
            reverse=True
        )
        
        for change in important_changes[:max_snippets]:
            # Extract meaningful diff sections
            diff_lines = change.diff_content.split('\n')
            meaningful_lines = []
            
            for line in diff_lines:
                # Include added/removed lines and context
                if line.startswith(('+', '-', '@@')) or (
                    len(line.strip()) > 0 and 
                    not line.startswith('index') and 
                    not line.startswith('diff --git')
                ):
                    meaningful_lines.append(line)
            
            if meaningful_lines:
                snippet = '\n'.join(meaningful_lines[:20])  # Limit length
                snippets.append(f"\n{change.file_path}:\n{snippet}")
        
        return '\n'.join(snippets)
    
    def _get_ai_intent_analysis(self, context: str) -> str:
        """Get AI analysis of change intent"""
        
        system_prompt = """You are an expert code reviewer analyzing a pull request to determine the intent behind the changes.

Analyze the provided context and classify the changes according to these categories:
- FEATURE: New functionality or capabilities
- BUGFIX: Fixing defects or issues
- REFACTOR: Restructuring code without changing behavior
- PERFORMANCE: Optimizing speed, memory, or efficiency
- SECURITY: Addressing security vulnerabilities or hardening
- DOCUMENTATION: Adding or updating documentation
- TESTING: Adding or improving tests
- CONFIGURATION: Changing settings, build, or deployment config
- DEPENDENCY: Updating dependencies or packages
- MAINTENANCE: General upkeep, cleanup, or tooling
- STYLE: Code formatting or style changes
- ARCHITECTURE: Structural or design pattern changes

Provide your analysis in this JSON format:
{
  "primary_intent": "CATEGORY",
  "confidence": 0.85,
  "secondary_intents": [["CATEGORY", 0.65], ["CATEGORY", 0.45]],
  "reasoning": "Detailed explanation of why you classified it this way",
  "affected_areas": ["ui", "api", "database", "authentication"],
  "business_impact": "How this affects end users or business goals",
  "technical_details": "Technical implementation details and patterns used"
}

Be thorough but concise. Focus on the most significant changes and their implications."""

        try:
            response = self.ai_client.complete(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error getting AI analysis: {e}")
            return self._generate_fallback_response(context)
    
    def _parse_ai_response(self, ai_response: str, file_changes: List[FileChange]) -> IntentClassification:
        """Parse AI response into structured IntentClassification"""
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in AI response")
            
            # Parse primary intent
            primary_intent = ChangeIntent(ai_data.get('primary_intent', 'maintenance').lower())
            
            # Parse secondary intents
            secondary_intents = []
            for intent_data in ai_data.get('secondary_intents', []):
                if len(intent_data) == 2:
                    try:
                        intent = ChangeIntent(intent_data[0].lower())
                        confidence = float(intent_data[1])
                        secondary_intents.append((intent, confidence))
                    except (ValueError, KeyError):
                        continue
            
            return IntentClassification(
                primary_intent=primary_intent,
                confidence=float(ai_data.get('confidence', 0.5)),
                secondary_intents=secondary_intents,
                reasoning=ai_data.get('reasoning', ''),
                affected_areas=ai_data.get('affected_areas', []),
                business_impact=ai_data.get('business_impact', ''),
                technical_details=ai_data.get('technical_details', '')
            )
            
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._fallback_classification("", "", file_changes)
    
    def _fallback_classification(self, pr_title: str, pr_description: str, 
                               file_changes: List[FileChange]) -> IntentClassification:
        """Provide rule-based classification when AI is not available"""
        
        # Simple rule-based classification
        title_lower = pr_title.lower()
        desc_lower = pr_description.lower()
        
        # Check for common patterns in title/description
        if any(word in title_lower for word in ['fix', 'bug', 'issue', 'error', 'broken']):
            primary_intent = ChangeIntent.BUGFIX
            confidence = 0.7
        elif any(word in title_lower for word in ['add', 'new', 'feature', 'implement']):
            primary_intent = ChangeIntent.FEATURE
            confidence = 0.7
        elif any(word in title_lower for word in ['refactor', 'restructure', 'reorganize']):
            primary_intent = ChangeIntent.REFACTOR
            confidence = 0.7
        elif any(word in title_lower for word in ['test', 'testing', 'spec']):
            primary_intent = ChangeIntent.TESTING
            confidence = 0.6
        elif any(word in title_lower for word in ['docs', 'documentation', 'readme']):
            primary_intent = ChangeIntent.DOCUMENTATION
            confidence = 0.8
        else:
            # Analyze file types
            if all(change.is_test_file for change in file_changes):
                primary_intent = ChangeIntent.TESTING
                confidence = 0.6
            elif any('.md' in change.file_path for change in file_changes):
                primary_intent = ChangeIntent.DOCUMENTATION
                confidence = 0.6
            else:
                primary_intent = ChangeIntent.MAINTENANCE
                confidence = 0.4
        
        # Determine affected areas from file paths
        affected_areas = self._determine_affected_areas(file_changes)
        
        return IntentClassification(
            primary_intent=primary_intent,
            confidence=confidence,
            secondary_intents=[],
            reasoning=f"Rule-based classification based on PR title pattern",
            affected_areas=affected_areas,
            business_impact="Analysis requires AI capability for detailed assessment",
            technical_details="File-based analysis indicates changes in " + ", ".join(affected_areas)
        )
    
    def _determine_affected_areas(self, file_changes: List[FileChange]) -> List[str]:
        """Determine which areas of the codebase are affected"""
        areas = set()
        
        for change in file_changes:
            path = change.file_path.lower()
            
            if any(ui_ext in path for ui_ext in ['.tsx', '.jsx', '.vue', '.css', '.scss']):
                areas.add('ui')
            elif '/api/' in path or '/routes/' in path:
                areas.add('api')
            elif '/test' in path or '.test.' in path:
                areas.add('testing')
            elif '/config' in path or '.config.' in path:
                areas.add('configuration')
            elif '/auth' in path or 'auth' in change.file_path:
                areas.add('authentication')
            elif '/db' in path or '/migration' in path:
                areas.add('database')
            elif '.md' in path or 'readme' in path:
                areas.add('documentation')
        
        return list(areas)
    
    def _generate_fallback_response(self, context: str) -> str:
        """Generate a fallback response when AI fails"""
        return json.dumps({
            "primary_intent": "MAINTENANCE",
            "confidence": 0.3,
            "secondary_intents": [],
            "reasoning": "Fallback classification due to AI analysis failure",
            "affected_areas": ["unknown"],
            "business_impact": "Unable to determine without AI analysis",
            "technical_details": "Manual review required for detailed analysis"
        })

def get_file_changes_from_git(repo_path: str, base_ref: str = "HEAD~1", 
                             head_ref: str = "HEAD") -> List[FileChange]:
    """Extract file changes from git diff"""
    
    try:
        # Get list of changed files
        result = subprocess.run(
            ['git', 'diff', '--name-status', f'{base_ref}..{head_ref}'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        file_changes = []
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) < 2:
                continue
                
            status = parts[0]
            file_path = parts[1]
            
            # Get diff for this file
            diff_result = subprocess.run(
                ['git', 'diff', f'{base_ref}..{head_ref}', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            # Count lines added/removed
            lines_added = diff_result.stdout.count('\n+') - diff_result.stdout.count('\n+++')
            lines_removed = diff_result.stdout.count('\n-') - diff_result.stdout.count('\n---')
            
            # Determine change type
            if status.startswith('A'):
                change_type = 'added'
            elif status.startswith('D'):
                change_type = 'deleted'
            elif status.startswith('M'):
                change_type = 'modified'
            elif status.startswith('R'):
                change_type = 'renamed'
            else:
                change_type = 'modified'
            
            # Determine file type and if it's a test
            file_extension = Path(file_path).suffix
            is_test_file = (
                '/test' in file_path.lower() or 
                '.test.' in file_path.lower() or 
                '.spec.' in file_path.lower() or
                '__tests__' in file_path.lower()
            )
            
            file_changes.append(FileChange(
                file_path=file_path,
                change_type=change_type,
                lines_added=max(0, lines_added),
                lines_removed=max(0, lines_removed),
                diff_content=diff_result.stdout,
                file_type=file_extension,
                is_test_file=is_test_file
            ))
        
        return file_changes
        
    except subprocess.CalledProcessError as e:
        print(f"Error getting git changes: {e}")
        return []

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Classify the intent of code changes')
    parser.add_argument('--repo', required=True, help='Repository path')
    parser.add_argument('--title', default='', help='PR title')
    parser.add_argument('--description', default='', help='PR description')
    parser.add_argument('--base', default='HEAD~1', help='Base commit/branch')
    parser.add_argument('--head', default='HEAD', help='Head commit/branch')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--pr-output', action='store_true', 
                       help='Generate output for PR comment integration')
    
    args = parser.parse_args()
    
    # Get file changes
    file_changes = get_file_changes_from_git(args.repo, args.base, args.head)
    
    if not file_changes:
        print("No file changes found")
        return
    
    # Classify intent
    classifier = IntentClassifier()
    classification = classifier.analyze_pr_intent(args.title, args.description, file_changes)
    
    # Output results
    result = {
        'primary_intent': classification.primary_intent.value,
        'confidence': classification.confidence,
        'secondary_intents': [(intent.value, conf) for intent, conf in classification.secondary_intents],
        'reasoning': classification.reasoning,
        'affected_areas': classification.affected_areas,
        'business_impact': classification.business_impact,
        'technical_details': classification.technical_details,
        'file_changes_summary': {
            'total_files': len(file_changes),
            'files_added': len([c for c in file_changes if c.change_type == 'added']),
            'files_modified': len([c for c in file_changes if c.change_type == 'modified']),
            'files_deleted': len([c for c in file_changes if c.change_type == 'deleted']),
            'total_lines_added': sum(c.lines_added for c in file_changes),
            'total_lines_removed': sum(c.lines_removed for c in file_changes)
        }
    }
    
    # Always generate PR integration file if in GitHub Actions
    if args.pr_output or os.getenv('GITHUB_ACTIONS'):
        pr_output_file = 'intent-classification-results.json'
        with open(pr_output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"PR integration results written to {pr_output_file}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results written to {args.output}")
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
