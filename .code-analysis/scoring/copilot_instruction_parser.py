"""
Copilot Instruction Parser for Quality Gate Enhancement.

This module parses GitHub Copilot instructions to extract high-level coding
principles and standards that should be incorporated into AI-powered quality analysis.
"""

import os
import re
import json
import hashlib
from typing import Dict, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class CopilotStandards:
    """Extracted coding standards from Copilot instructions."""
    # High-level principles
    error_handling_required: bool = False
    type_safety_emphasis: bool = False
    performance_focus: bool = False
    documentation_required: bool = False
    testing_emphasis: bool = False
    
    # Language-specific preferences
    preferred_patterns: Optional[List[str]] = None
    discouraged_patterns: Optional[List[str]] = None
    
    # Project-specific guidelines
    architectural_principles: Optional[List[str]] = None
    code_organization: Optional[List[str]] = None
    
    # Raw extracted sections for AI context
    key_principles: str = ""
    code_examples: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.preferred_patterns is None:
            self.preferred_patterns = []
        if self.discouraged_patterns is None:
            self.discouraged_patterns = []
        if self.architectural_principles is None:
            self.architectural_principles = []
        if self.code_organization is None:
            self.code_organization = []
        if self.code_examples is None:
            self.code_examples = []


class CopilotInstructionParser:
    """
    Parser for GitHub Copilot instructions that extracts coding standards
    and principles for use in quality gate analysis.
    """
    
    def __init__(self, instruction_file_path: str = None):
        """
        Initialize parser with path to Copilot instructions.
        
        Args:
            instruction_file_path: Path to the Copilot instructions file.
                                 If None, will auto-detect from repository root.
        """
        if instruction_file_path is None:
            # Auto-detect path relative to repository root
            script_dir = Path(__file__).parent.parent.parent  # Go up from .code-analysis/scoring/
            self.instruction_file_path = str(script_dir / ".github" / "copilot-instructions.md")
        else:
            self.instruction_file_path = instruction_file_path
            
        self.cache_file = ".code-analysis/.copilot-cache.json"
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        cache_dir = Path(self.cache_file).parent
        # Make cache directory relative to repository root if it doesn't exist
        if not cache_dir.is_absolute():
            script_dir = Path(__file__).parent.parent.parent  # Repository root
            cache_dir = script_dir / cache_dir
            self.cache_file = str(cache_dir / ".copilot-cache.json")
        cache_dir.mkdir(exist_ok=True)
    
    def get_standards(self) -> CopilotStandards:
        """
        Get coding standards, using cache if file hasn't changed.
        
        Returns:
            CopilotStandards object with extracted principles
        """
        # Check if we can use cached version
        if self._is_cache_valid():
            try:
                return self._load_from_cache()
            except Exception:
                pass  # Fall through to re-parse
        
        # Parse instructions and cache result
        standards = self._parse_instructions()
        self._save_to_cache(standards)
        return standards
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not os.path.exists(self.cache_file):
            return False
        
        if not os.path.exists(self.instruction_file_path):
            return False
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check file modification time and content hash
            current_mtime = os.path.getmtime(self.instruction_file_path)
            current_hash = self._get_file_hash()
            
            return (cache_data.get('file_mtime') == current_mtime and 
                    cache_data.get('file_hash') == current_hash)
        except Exception:
            return False
    
    def _get_file_hash(self) -> str:
        """Get hash of instruction file content."""
        try:
            with open(self.instruction_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""
    
    def _load_from_cache(self) -> CopilotStandards:
        """Load standards from cache."""
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        standards_dict = cache_data['standards']
        return CopilotStandards(**standards_dict)
    
    def _save_to_cache(self, standards: CopilotStandards):
        """Save standards to cache with metadata."""
        cache_data = {
            'file_mtime': os.path.getmtime(self.instruction_file_path),
            'file_hash': self._get_file_hash(),
            'standards': asdict(standards)
        }
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    
    def _parse_instructions(self) -> CopilotStandards:
        """
        Parse Copilot instructions and extract coding standards.
        
        Returns:
            CopilotStandards object with extracted principles
        """
        if not os.path.exists(self.instruction_file_path):
            return CopilotStandards()
        
        try:
            with open(self.instruction_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return CopilotStandards()
        
        standards = CopilotStandards()
        
        # Extract high-level principles
        self._extract_principles(content, standards)
        
        # Extract patterns and preferences
        self._extract_patterns(content, standards)
        
        # Extract architectural guidelines
        self._extract_architecture(content, standards)
        
        # Store key sections for AI context
        standards.key_principles = self._extract_key_sections(content)
        standards.code_examples = self._extract_code_examples(content)
        
        return standards
    
    def _extract_principles(self, content: str, standards: CopilotStandards):
        """Extract high-level coding principles."""
        content_lower = content.lower()
        
        # Error handling emphasis
        error_keywords = ['error handling', 'try/catch', 'exception', 'error management']
        standards.error_handling_required = any(keyword in content_lower for keyword in error_keywords)
        
        # Type safety emphasis
        type_keywords = ['type safety', 'typescript', 'type hints', 'type annotation']
        standards.type_safety_emphasis = any(keyword in content_lower for keyword in type_keywords)
        
        # Performance focus
        perf_keywords = ['performance', 'optimization', 'efficiency', 'fast', 'speed']
        standards.performance_focus = any(keyword in content_lower for keyword in perf_keywords)
        
        # Documentation requirements
        doc_keywords = ['documentation', 'jsdoc', 'docstring', 'comment', 'document']
        standards.documentation_required = any(keyword in content_lower for keyword in doc_keywords)
        
        # Testing emphasis
        test_keywords = ['test', 'testing', 'unit test', 'integration test', 'coverage']
        standards.testing_emphasis = any(keyword in content_lower for keyword in test_keywords)
    
    def _extract_patterns(self, content: str, standards: CopilotStandards):
        """Extract preferred and discouraged patterns."""
        # Look for explicit pattern mentions
        preferred_patterns = []
        discouraged_patterns = []
        
        # Find sections about preferences
        lines = content.split('\n')
        in_prefer_section = False
        in_avoid_section = False
        
        for line in lines:
            line_lower = line.lower()
            
            # Section detection
            if any(word in line_lower for word in ['prefer', 'recommended', 'best practice']):
                in_prefer_section = True
                in_avoid_section = False
            elif any(word in line_lower for word in ['avoid', 'don\'t', 'discouraged']):
                in_avoid_section = True
                in_prefer_section = False
            elif line.startswith('#') or line.startswith('##'):
                in_prefer_section = False
                in_avoid_section = False
            
            # Extract patterns
            if in_prefer_section and ('const' in line_lower or 'function' in line_lower):
                preferred_patterns.append(line.strip())
            elif in_avoid_section and ('var' in line_lower or 'any' in line_lower):
                discouraged_patterns.append(line.strip())
        
        standards.preferred_patterns = preferred_patterns
        standards.discouraged_patterns = discouraged_patterns
    
    def _extract_architecture(self, content: str, standards: CopilotStandards):
        """Extract architectural principles and code organization guidelines."""
        architectural_principles = []
        code_organization = []
        
        # Look for architecture sections
        sections = re.split(r'\n#+\s+', content)
        
        for section in sections:
            self._process_architecture_section(section, architectural_principles, code_organization)
        
        standards.architectural_principles = architectural_principles[:5]  # Limit to top 5
        standards.code_organization = code_organization[:5]
    
    def _process_architecture_section(self, section: str, arch_principles: List[str], code_org: List[str]):
        """Process a single section for architecture content."""
        section_lower = section.lower()
        
        if any(word in section_lower for word in ['architecture', 'structure', 'organization']):
            # Extract bullet points or key concepts
            lines = section.split('\n')
            for line in lines:
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    if 'architecture' in section_lower:
                        arch_principles.append(line.strip())
                    else:
                        code_org.append(line.strip())
    
    def _extract_key_sections(self, content: str) -> str:
        """Extract key sections for AI context (summarized)."""
        # Find the most important sections (usually at the beginning)
        lines = content.split('\n')
        key_content = []
        
        # Take first meaningful section after title
        capturing = False
        for line in lines:
            if line.startswith('# ') or line.startswith('## '):
                if any(word in line.lower() for word in ['guideline', 'instruction', 'standard', 'practice']):
                    capturing = True
                elif capturing and line.startswith('#'):
                    break  # Stop at next major section
            elif capturing and line.strip():
                key_content.append(line.strip())
                if len(key_content) > 10:  # Limit size
                    break
        
        return '\n'.join(key_content)
    
    def _extract_code_examples(self, content: str) -> List[str]:
        """Extract code examples from instructions."""
        # Find code blocks
        code_examples = []
        lines = content.split('\n')
        in_code_block = False
        current_example = []
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    if current_example:
                        code_examples.append('\n'.join(current_example))
                        current_example = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
            elif in_code_block:
                current_example.append(line)
        
        return code_examples[:3]  # Limit to first 3 examples
    
    def generate_ai_context(self) -> str:
        """
        Generate context string for AI quality analysis.
        
        Returns:
            Formatted string with project coding standards for AI context
        """
        standards = self.get_standards()
        
        context_parts = []
        
        # Add high-level principles
        principles = []
        if standards.error_handling_required:
            principles.append("Proper error handling is required")
        if standards.type_safety_emphasis:
            principles.append("Type safety is emphasized")
        if standards.performance_focus:
            principles.append("Performance optimization is important")
        if standards.documentation_required:
            principles.append("Code documentation is required")
        if standards.testing_emphasis:
            principles.append("Testing coverage is important")
        
        if principles:
            context_parts.append(f"Project Principles: {', '.join(principles)}")
        
        # Add specific patterns
        if standards.preferred_patterns:
            context_parts.append(f"Preferred Patterns: {'; '.join(standards.preferred_patterns[:3])}")
        
        if standards.discouraged_patterns:
            context_parts.append(f"Avoid: {'; '.join(standards.discouraged_patterns[:3])}")
        
        # Add key content if available
        if standards.key_principles:
            context_parts.append(f"Key Guidelines: {standards.key_principles[:200]}...")
        
        return "\n".join(context_parts) if context_parts else "No specific coding standards found."
