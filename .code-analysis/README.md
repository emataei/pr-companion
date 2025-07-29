# AI-Era Code Review System

> **Transform your code review process for the age of AI-generated code**

## The Problem

In the AI era, code generation is no longer the bottleneck — human comprehension is.
To sustain velocity and quality at scale, we must minimize unnecessary human review effort by aligning review depth with code risk, clarity, and impact.
A tiered review model, combined with AI-assisted code analysis and structured tagging, enables us to triage changes efficiently, focus human review only where it matters most, and reduce the code-to-approval cycle time without compromising software integrity.

## The Solution

An intelligent, tiered review system that:
- **Automatically analyzes** code complexity and risk
- **Routes changes** to appropriate reviewers based on difficulty
- **Eliminates review bottlenecks** for simple changes
- **Ensures expert attention** for complex, critical code
- **Provides enhanced PR visuals** with dependency graphs, change heatmaps, and animated summaries

## Key Features

### Cognitive Complexity Analysis
- Multi-dimensional scoring (static analysis + AI assessment)
- Risk-based tier assignment (0-2)
- Quality gate with blocking issue detection

### Enhanced PR Visuals
- **Auto-detection**: Portable across any repository structure
- **Dependency graphs**: Before/after module relationship visualization
- **Change heatmaps**: Statistical breakdown of modifications
- **Animated summaries**: Progressive reveal of PR impact
- **Comprehensive reporting**: All analyses combined into a single report

### Automatic Team Assignment
- Smart routing based on code complexity
- Configurable team assignments
- Escalation for security/critical changes

### Velocity Improvements
- **Tier 0**: Auto-merge for simple changes
- **Tier 1**: Single reviewer for standard changes
- **Tier 2**: Expert review for complex changes

### Rich Feedback
- Detailed PR comments with complexity breakdown
- Visual analysis with dependency and change insights
- Actionable quality improvement suggestions
- Clear review process guidance

## Quick Start

1. **Set up AI provider** (Azure AI Foundry or OpenAI)
2. **Copy `.code-analysis` and `.github` folders** to your repository
3. **Install dependencies** (pip install -r .github/requirements.txt)
4. **Enable workflows** - they run automatically on PRs

The system is **100% portable** - just drop the folders into any repository and it works.

## Available Workflows

### Enhanced PR Visuals (`enhanced-pr-visuals.yml`)
- **Auto-detects** project structure (Next.js, React, Vue, etc.)
- **Generates dependency graphs** using madge for JavaScript/TypeScript projects
- **Creates change heatmaps** showing modification intensity
- **Provides animated summaries** with progressive impact reveal
- **Combines everything** into a comprehensive visual report
- **Updates PR comments** using shared utilities for consistency

### Cognitive Scoring (`cognitive_scoring.yml`)
- **Analyzes code complexity** using static analysis + AI
- **Assigns review tiers** based on risk and complexity
- **Routes to appropriate reviewers** automatically
- **Provides quality feedback** with actionable suggestions

## 📖 Documentation

- **[Cognitive Review System](docs/COGNITIVE_REVIEW_SYSTEM.md)** - Complete system overview with hypothesis and benefits
- **[Setup Guide](docs/SETUP_GUIDE.md)** - Quick implementation instructions
- **[AI Provider Setup](docs/ai_provider_setup.md)** - Detailed AI configuration

## Results

### Velocity
- **60-80% reduction** in review time for simple changes
- **Clear SLAs** for each complexity tier
- **Parallel processing** for complex changes

### Quality
- **Automated quality gates** catch issues before human review
- **Expert involvement** for high-risk changes
- **Consistent standards** across all contributions

### Developer Experience
- **Predictable process** with clear expectations
- **Reduced frustration** from waiting on trivial changes
- **Focused attention** on work that matters

---