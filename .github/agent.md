# Agent Memory & Instructions

Persistent context for AI agents working on this codebase.

## Project Essentials

**Repo**: codeEvalTooling (emadataei)  
**Purpose**: PR analysis, visualization, documentation automation  
**Stack**: TypeScript/Next.js, Python, GitHub Actions  
**Platform**: Windows (PowerShell)

## Critical Rules

- **No emojis** in markdown/code (per copilot-instructions.md)
- **Only code-quality-analysis.yml** sets PR labels
- **Reviewer-centric labels** (tier, complexity, score, size, merge readiness)
- **PR comments replace** existing ones (don't duplicate)
- **Base64 embedded images** in PR comments
- **User-focused docs** (not technical implementation details)

## Windows Commands

Use PowerShell syntax:
- Multiple commands: `cmd1; cmd2; cmd3`
- Remove files: `rm file1 file2 file3`
- Install packages: `npm install pkg1 pkg2`
- **Python venv**: Use `.\venv312\Scripts\Activate.ps1` (Python 3.12 with matplotlib, seaborn, pandas, numpy)
- **Local visual testing**: Use `local-visual-test/` folder with `python scripts/generate_all_visuals.py`

## Key Files

- `.code-analysis/scripts/auto-label-pr.js` - Reviewer-centric labeling logic
- `docs/pr-labeling-system.md` - User guide for PR labels
- `.github/workflows/code-quality-analysis.yml` - Only workflow that sets labels

## Recent Critical Issues

- **2025-07-25**: `auto-label-pr.js` was accidentally emptied (384 lines lost, restored)
- User prefers concise, actionable docs over verbose explanations

## User Preferences

- Quick implementation > extensive planning
- Practical > theoretical
- Context-aware brevity
- Focus on reviewer/user experience

---

*Keep this file short and actionable. More context ≠ better context.*
