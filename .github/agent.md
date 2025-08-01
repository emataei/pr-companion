
# Agent Memory & Instructions

**Purpose:** PR analysis, visualization, and documentation automation.
**Stack:** TypeScript/Next.js, Python, GitHub Actions. Platform: Windows (PowerShell).

## Rules
- No emojis in markdown/code (see copilot-instructions.md)
- Only `.github/workflows/code-quality-analysis.yml` sets PR labels
- PR comments must replace existing ones (no duplicates)
- Use reviewer-centric labels (tier, complexity, score, size, merge readiness)
- Docs must be user-focused, not implementation details

## Windows Commands
- Use PowerShell: `cmd1; cmd2; cmd3`
- Remove files: `rm file1; rm file2; rm file3`
- Python venv: `./venv312/Scripts/Activate.ps1` (Python 3.12)
- Local visual test: `cd local-visual-test; python scripts/generate_all_visuals.py`

## Key Files
- `.code-analysis/scripts/auto-label-pr.js`: PR labeling logic
- `docs/pr-labeling-system.md`: PR label user guide
- `.github/workflows/code-quality-analysis.yml`: Only workflow that sets labels

## User Preferences
- Concise, actionable docs
- Quick, practical solutions
- Prioritize reviewer/user experience
