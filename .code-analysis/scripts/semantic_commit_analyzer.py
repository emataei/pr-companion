#!/usr/bin/env python3
"""
Semantic Commit Log Generator for GitHub PRs.

This script analyzes commit history and code changes to generate:
- A narrative "what & why" summary for PR descriptions
- Visual representations of the change story
- Logical grouping of commits by intent
"""

import sys
import json
import os
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Add .code-analysis to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scoring.ai_client_factory import AIClientFactory
    AI_CLIENT_AVAILABLE = True
except ImportError:
    AI_CLIENT_AVAILABLE = False

@dataclass
class CommitInfo:
    """Represents a single commit with semantic analysis."""
    hash: str
    message: str
    files_changed: List[str]
    insertions: int
    deletions: int
    intent: str  # setup, feature, fix, refactor, test, docs
    scope: str   # ui, api, config, etc.

@dataclass
class ChangeStory:
    """Represents the narrative arc of the PR."""
    title: str
    what: str           # Brief what description
    why: str            # Brief why description  
    commits_by_intent: Dict[str, List[CommitInfo]]
    impact_areas: Dict[str, int]  # area -> number of files
    visual_summary: str  # ASCII or markdown visualization

class SemanticCommitAnalyzer:
    """Analyzes commits to extract semantic meaning and narrative flow."""
    
    INTENT_PATTERNS = {
        'setup': ['initial', 'setup', 'init', 'bootstrap', 'scaffold'],
        'feature': ['add', 'implement', 'create', 'new', 'feat'],
        'fix': ['fix', 'bug', 'error', 'issue', 'resolve'],
        'refactor': ['refactor', 'refact', 'restructure', 'cleanup', 'clean'],
        'test': ['test', 'spec', 'coverage', 'mock'],
        'docs': ['doc', 'readme', 'comment', 'documentation'],
        'style': ['style', 'format', 'lint', 'prettier'],
        'config': ['config', 'setting', 'env', 'deployment']
    }
    
    SCOPE_PATTERNS = {
        'ui': ['.tsx', '.jsx', '.vue', '.css', '.scss', 'component', 'ui'],
        'api': ['/api/', 'route', 'endpoint', 'controller', 'handler'],
        'database': ['db/', 'database', 'migration', 'schema', 'model'],
        'config': ['config', '.env', 'setting', 'webpack', 'vite'],
        'test': ['test/', 'spec/', '__tests__', '.test.', '.spec.'],
        'docs': ['.md', 'readme', 'documentation', 'docs/'],
        'build': ['build', 'dist/', 'package.json', 'Dockerfile'],
        'security': ['auth', 'security', 'permission', 'token']
    }

    def __init__(self):
        self.ai_client = None
        if AI_CLIENT_AVAILABLE:
            try:
                AIClientFactory.validate_config()
                self.ai_client = AIClientFactory.create_client()
            except Exception as e:
                print(f"Warning: AI client unavailable: {e}")

    def get_commit_history(self) -> List[CommitInfo]:
        """Get commits for the current PR."""
        try:
            # Try to detect the default branch dynamically
            base_branch = os.environ.get('GITHUB_BASE_REF', 'main')
            
            # Try different branch name variations
            branches_to_try = [f'origin/{base_branch}', 'origin/main', 'origin/master']
            
            for branch in branches_to_try:
                try:
                    result = subprocess.run([
                        'git', 'log', '--oneline', '--numstat', 
                        f'{branch}..HEAD', '--pretty=format:%H|%s'
                    ], capture_output=True, text=True, check=True)
                    
                    commits = self._parse_git_log_output(result.stdout)
                    if commits:  # If we found commits, return them
                        print(f"Found {len(commits)} commits using base branch: {branch}")
                        return commits
                    else:
                        print(f"No commits found with base branch: {branch}")
                        
                except subprocess.CalledProcessError as e:
                    print(f"Failed to get commits with base branch {branch}: {e}")
                    continue
            
            print("No commits found with any base branch")
            return []
            
        except Exception as e:
            print(f"Error getting commit history: {e}")
            return []

    def _parse_git_log_output(self, git_output: str) -> List[CommitInfo]:
        """Parse git log output into CommitInfo objects."""
        commits = []
        current_commit = None
        
        for line in git_output.strip().split('\n'):
            if not line:
                continue
                
            if '|' in line:
                current_commit = self._parse_commit_line(line)
                if current_commit:
                    commits.append(current_commit)
            elif current_commit and '\t' in line:
                self._parse_file_change_line(line, current_commit)
                
        return commits

    def _parse_commit_line(self, line: str) -> Optional[CommitInfo]:
        """Parse a commit line from git log."""
        hash_msg = line.split('|', 1)
        if len(hash_msg) == 2:
            return CommitInfo(
                hash=hash_msg[0],
                message=hash_msg[1],
                files_changed=[],
                insertions=0,
                deletions=0,
                intent='',
                scope=''
            )
        return None

    def _parse_file_change_line(self, line: str, commit: CommitInfo) -> None:
        """Parse a file change line and update commit stats."""
        parts = line.split('\t')
        if len(parts) >= 3:
            insertions = int(parts[0]) if parts[0] != '-' else 0
            deletions = int(parts[1]) if parts[1] != '-' else 0
            file_path = parts[2]
            
            commit.insertions += insertions
            commit.deletions += deletions
            commit.files_changed.append(file_path)

    def classify_commit(self, commit: CommitInfo) -> None:
        """Classify commit intent and scope based on message and files."""
        message_lower = commit.message.lower()
        
        # Determine intent
        for intent, patterns in self.INTENT_PATTERNS.items():
            if any(pattern in message_lower for pattern in patterns):
                commit.intent = intent
                break
        
        if not commit.intent:
            commit.intent = 'other'
        
        # Determine scope based on files changed
        scope_scores = defaultdict(int)
        for file_path in commit.files_changed:
            for scope, patterns in self.SCOPE_PATTERNS.items():
                if any(pattern in file_path.lower() for pattern in patterns):
                    scope_scores[scope] += 1
        
        if scope_scores:
            commit.scope = max(scope_scores.items(), key=lambda x: x[1])[0]
        else:
            commit.scope = 'other'

    def generate_impact_areas(self, commits: List[CommitInfo]) -> Dict[str, int]:
        """Calculate impact across different system areas."""
        impact = defaultdict(int)
        all_files = set()
        
        for commit in commits:
            for file_path in commit.files_changed:
                all_files.add(file_path)
                
        for file_path in all_files:
            for scope, patterns in self.SCOPE_PATTERNS.items():
                if any(pattern in file_path.lower() for pattern in patterns):
                    impact[scope] += 1
                    break
            else:
                impact['other'] += 1
                
        return dict(impact)

    def create_visual_summary(self, story: ChangeStory) -> str:
        """Generate a visual representation of the change story using actual images."""
        # Skip visual summary generation to avoid duplicates
        # Mermaid visualizations are now handled in JavaScript layer
        return ""
    
    def _create_fallback_visual(self, story: ChangeStory) -> str:
        """Create fallback ASCII visualization when image generation fails."""
        visual = []
        
        # Enhanced development flow with better categorization
        if story.commits_by_intent:
            enhanced_categories = self._categorize_intents_fallback(story.commits_by_intent)
            
            visual.append("## Development Flow")
            flow_parts = []
            for category, count in enhanced_categories.items():
                flow_parts.append(f"{category}({count})")
            visual.append("  " + " → ".join(flow_parts))
            visual.append("")
        
        # Simplified impact visualization
        if story.impact_areas:
            impact_section = self._create_impact_section(story.impact_areas)
            visual.extend(impact_section)
        
        return "\n".join(visual)
    
    def _categorize_intents_fallback(self, commits_by_intent):
        """Categorize intents for fallback visualization."""
        enhanced_categories = {}
        
        category_mapping = {
            'feature_dev': ['feature', 'feat', 'add', 'implement'],
            'bug_fixes': ['fix', 'bug', 'hotfix', 'patch'],
            'testing': ['test', 'spec', 'coverage'],
            'infrastructure': ['infra', 'deploy', 'config', 'setup', 'workflow', 'ci', 'cd'],
            'documentation': ['docs', 'doc', 'readme', 'comment']
        }
        
        category_names = {
            'feature_dev': 'Feature Dev',
            'bug_fixes': 'Bug Fixes', 
            'testing': 'Testing',
            'infrastructure': 'Infrastructure',
            'documentation': 'Documentation'
        }
        
        for intent, commits in commits_by_intent.items():
            categorized = False
            for category_key, keywords in category_mapping.items():
                if intent.lower() in keywords:
                    category_name = category_names[category_key]
                    enhanced_categories[category_name] = enhanced_categories.get(category_name, 0) + len(commits)
                    categorized = True
                    break
            
            if not categorized:
                enhanced_categories['Code Quality'] = enhanced_categories.get('Code Quality', 0) + len(commits)
        
        return enhanced_categories
    
    def _create_impact_section(self, impact_areas):
        """Create impact visualization section."""
        visual = []
        visual.append("## Impact Distribution")
        visual.append("```")
        max_impact = max(impact_areas.values()) if impact_areas else 1
        
        for area, count in sorted(impact_areas.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                bar_length = int((count / max_impact) * 15)
                bar = "█" * bar_length + "░" * (15 - bar_length)
                visual.append(f"{area.ljust(15)} {bar} {count}")
        visual.append("```")
        visual.append("")
        
        return visual

    def generate_narrative_summary(self, commits: List[CommitInfo]) -> Tuple[str, str]:
        """Generate AI-powered what/why summary."""
        print(f"Starting narrative generation with {len(commits)} commits")
        print(f"AI client available: {self.ai_client is not None}")
        
        if not self.ai_client:
            print("AI client not available, using intelligent fallback")
            return self._generate_fallback_summary(commits)
        
        if not commits:
            print("No commits found, using fallback")
            return self._generate_fallback_summary(commits)
        
        commit_context = self._prepare_commit_context(commits)
        prompt = self._build_ai_prompt(commit_context)
        
        print(f"Generated prompt length: {len(prompt)} characters")
        
        try:
            messages = [
                {"role": "system", "content": "You are a code analysis assistant that creates concise PR summaries."},
                {"role": "user", "content": prompt}
            ]
            
            print(f"Sending AI request with {len(commits)} commits")
            response = self.ai_client.complete(
                messages=messages,
                model="gpt-4o-mini",  # Use the same model as other components
                temperature=0.3,
                max_tokens=200
            )
            
            ai_response = response.choices[0].message.content
            print(f"AI response received: {ai_response}")
            
            parsed_result = self._parse_ai_response(ai_response)
            print(f"Parsed result: What='{parsed_result[0]}', Why='{parsed_result[1]}'")
            
            # Check if parsing failed and fallback to intelligent analysis
            if parsed_result[0] == "Code changes implemented" or not parsed_result[0]:
                print("AI parsing failed, using intelligent fallback")
                return self._generate_fallback_summary(commits)
            
            return parsed_result
        except Exception as e:
            print(f"AI summary failed: {e}")
            print("Using intelligent fallback")
            return self._generate_fallback_summary(commits)

    def _prepare_commit_context(self, commits: List[CommitInfo]) -> List[Dict]:
        """Prepare commit data for AI analysis."""
        return [{
            'message': commit.message,
            'intent': commit.intent,
            'scope': commit.scope,
            'files': len(commit.files_changed),
            'changes': f"+{commit.insertions}/-{commit.deletions}"
        } for commit in commits]

    def _build_ai_prompt(self, commit_context: List[Dict]) -> str:
        """Build the AI prompt for narrative generation."""
        return f"""Analyze these commits and generate a brief, reviewer-friendly summary.

Commits: {json.dumps(commit_context, indent=2)}

Please respond in this exact format:

WHAT: [1-2 sentences describing what this PR accomplishes]
WHY: [1-2 sentences explaining why this change was needed]

Focus on business value and technical necessity. Avoid implementation details."""

    def _parse_ai_response(self, response: str) -> Tuple[str, str]:
        """Parse AI response to extract what/why statements."""
        lines = response.strip().split('\n')
        what_line = ""
        why_line = ""
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith(('WHAT:', 'What:', 'what:', '1.')):
                # Extract everything after the colon
                if ':' in line_stripped:
                    what_line = line_stripped.split(':', 1)[1].strip()
                else:
                    what_line = line_stripped
            elif line_stripped.startswith(('WHY:', 'Why:', 'why:', '2.')):
                # Extract everything after the colon
                if ':' in line_stripped:
                    why_line = line_stripped.split(':', 1)[1].strip()
                else:
                    why_line = line_stripped
        
        # Clean up the extracted text (remove quotes, extra spaces, etc.)
        what_line = what_line.strip(' "\'').strip()
        why_line = why_line.strip(' "\'').strip()
        
        print(f"Parsed - What: '{what_line}', Why: '{why_line}'")
        
        return what_line or "Code changes implemented", why_line or "Improvement needed"

    def _generate_fallback_summary(self, commits: List[CommitInfo]) -> Tuple[str, str]:
        """Generate intelligent summary by analyzing commit messages and changes."""
        if not commits:
            return "No commits found", "Initial changes"
        
        # Analyze commit messages for intent and actions
        all_messages = " ".join([commit.message.lower() for commit in commits])
        
        # Enhanced intent analysis
        intent_analysis = {
            'fixing': ['fix', 'bug', 'error', 'issue', 'resolve', 'correct', 'repair'],
            'adding': ['add', 'implement', 'create', 'new', 'introduce', 'build'],
            'improving': ['improve', 'enhance', 'optimize', 'update', 'upgrade', 'refactor'],
            'updating': ['update', 'modify', 'change', 'edit', 'adjust'],
            'removing': ['remove', 'delete', 'clean', 'cleanup', 'deprecate'],
            'configuring': ['config', 'setup', 'configure', 'setting', 'env'],
            'testing': ['test', 'spec', 'coverage', 'mock', 'verify'],
            'documenting': ['doc', 'readme', 'comment', 'documentation'],
            'styling': ['style', 'format', 'lint', 'prettier', 'css'],
            'securing': ['security', 'auth', 'permission', 'validate', 'sanitize']
        }
        
        # Score each intent based on commit messages
        intent_scores = {}
        for intent, keywords in intent_analysis.items():
            score = sum(1 for keyword in keywords if keyword in all_messages)
            if score > 0:
                intent_scores[intent] = score
        
        # Get primary intent
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0] if intent_scores else 'updating'
        
        # Analyze file changes for scope
        all_files = []
        total_additions = sum(commit.insertions for commit in commits)
        total_deletions = sum(commit.deletions for commit in commits)
        
        for commit in commits:
            all_files.extend(commit.files_changed)
        
        # Enhanced scope analysis
        scope_analysis = {
            'authentication': ['auth', 'login', 'user', 'session', 'token'],
            'user interface': ['ui', 'component', '.tsx', '.jsx', '.vue', 'style', '.css'],
            'API endpoints': ['api', 'route', 'endpoint', 'controller', 'handler'],
            'database': ['db', 'database', 'migration', 'schema', 'model'],
            'configuration': ['config', '.env', 'setting', 'webpack', 'package.json'],
            'testing': ['test', 'spec', '__tests__', '.test.', '.spec.'],
            'documentation': ['.md', 'readme', 'docs'],
            'build system': ['build', 'dist', 'webpack', 'vite', 'docker'],
            'security': ['security', 'permission', 'validate', 'sanitize'],
            'error handling': ['error', 'exception', 'catch', 'try'],
            'performance': ['performance', 'optimize', 'cache', 'speed'],
            'data processing': ['process', 'parse', 'format', 'transform']
        }
        
        # Score scopes based on files and commit messages
        scope_scores = {}
        for scope, keywords in scope_analysis.items():
            file_score = sum(1 for file in all_files for keyword in keywords if keyword in file.lower())
            message_score = sum(1 for keyword in keywords if keyword in all_messages)
            total_score = file_score * 2 + message_score  # Weight file changes more
            if total_score > 0:
                scope_scores[scope] = total_score
        
        # Get primary scope
        primary_scope = max(scope_scores.items(), key=lambda x: x[1])[0] if scope_scores else 'codebase'
        
        # Generate intelligent WHAT statement
        what_templates = {
            'fixing': f"Fixes issues in {primary_scope}",
            'adding': f"Adds new {primary_scope} functionality", 
            'improving': f"Improves {primary_scope} implementation",
            'updating': f"Updates {primary_scope} components",
            'removing': f"Removes deprecated {primary_scope} code",
            'configuring': f"Configures {primary_scope} settings",
            'testing': f"Adds test coverage for {primary_scope}",
            'documenting': f"Updates {primary_scope} documentation",
            'styling': f"Improves {primary_scope} styling and formatting",
            'securing': f"Enhances {primary_scope} security measures"
        }
        
        base_what = what_templates.get(primary_intent, f"Updates {primary_scope}")
        
        # Add scale information
        if len(commits) > 3:
            what = f"{base_what} across {len(commits)} commits"
        elif total_additions + total_deletions > 100:
            what = f"{base_what} with significant changes ({total_additions}+ lines)"
        else:
            what = base_what
        
        # Generate intelligent WHY statement
        why_templates = {
            'fixing': "to resolve bugs and improve system stability",
            'adding': "to extend functionality and meet new requirements",
            'improving': "to enhance performance and maintainability", 
            'updating': "to keep components current and aligned",
            'removing': "to reduce technical debt and simplify codebase",
            'configuring': "to optimize system behavior and deployment",
            'testing': "to ensure code quality and prevent regressions",
            'documenting': "to improve developer experience and onboarding",
            'styling': "to maintain consistent code style and readability",
            'securing': "to protect against vulnerabilities and ensure data safety"
        }
        
        base_why = why_templates.get(primary_intent, "to improve the overall system")
        
        # Add context from file analysis
        if len(scope_scores) > 1:
            secondary_scopes = sorted(scope_scores.items(), key=lambda x: x[1], reverse=True)[1:3]
            scope_list = [scope for scope, _ in secondary_scopes]
            why = f"{base_why} and update {', '.join(scope_list)}"
        else:
            why = base_why
        
        return what, why

    def analyze_pr(self) -> ChangeStory:
        """Main analysis method - generates complete semantic commit story."""
        commits = self.get_commit_history()
        
        # Classify all commits
        for commit in commits:
            self.classify_commit(commit)
        
        # Group by intent
        commits_by_intent = defaultdict(list)
        for commit in commits:
            commits_by_intent[commit.intent].append(commit)
        
        # Generate narrative
        what, why = self.generate_narrative_summary(commits)
        
        # Calculate impact
        impact_areas = self.generate_impact_areas(commits)
        
        # Create story
        story = ChangeStory(
            title=f"PR Analysis: {len(commits)} commits across {len(impact_areas)} areas",
            what=what,
            why=why,
            commits_by_intent=dict(commits_by_intent),
            impact_areas=impact_areas,
            visual_summary=""
        )
        
        # Generate visual
        story.visual_summary = self.create_visual_summary(story)
        
        return story

def main():
    """Main entry point."""
    analyzer = SemanticCommitAnalyzer()
    
    try:
        story = analyzer.analyze_pr()
        
        # Output results
        results = {
            'semantic_analysis': {
                'what': story.what,
                'why': story.why,
                'commit_count': sum(len(commits) for commits in story.commits_by_intent.values()),
                'intents': list(story.commits_by_intent.keys()),
                'impact_areas': story.impact_areas,
                'visual_summary': story.visual_summary
            }
        }
        
        # Ensure outputs directory exists
        os.makedirs('.code-analysis/outputs', exist_ok=True)
        
        # Write to JSON for GitHub Actions - outputs directory only
        output_path = '.code-analysis/outputs/semantic-commit-analysis.json'
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Semantic analysis saved to: {output_path}")
        
        print("Semantic commit analysis completed successfully")
        print(f"What: {story.what}")
        print(f"Why: {story.why}")
        
    except Exception as e:
        print(f"Error in semantic analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
