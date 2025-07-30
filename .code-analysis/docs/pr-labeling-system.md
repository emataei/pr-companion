# 🏷️ Auto-Generated PR Labels

**PR Companion automatically applies these labels to help reviewers prioritize and route PRs effectively.**

## 🎯 Review Priority Labels

| Label | Action Required | Review Time |
|-------|----------------|-------------|
| `tier:0` | **Quick approval** | 2-5 minutes |
| `tier:1` | **Junior dev review** | 15-30 minutes |
| `tier:2` | **Senior dev review** | 30-60 minutes |  
| `tier:3` | **Expert review** | 1-2 hours |
| `tier:4` | **Team discussion** | Meeting required |

## 📊 Quality Indicators

| Label | Meaning | Next Steps |
|-------|---------|------------|
| `score:excellent` (90-100) | High quality, ready to merge | Fast-track approval |
| `score:good` (70-89) | Solid work, minor feedback | Standard review |
| `score:needs-work` (50-69) | Issues found | Request changes |
| `score:poor` (<50) | Major problems | Block until fixed |

## 🎭 Change Type Labels

- `type:feature` - New functionality
- `type:bugfix` - Bug repairs  
- `type:refactor` - Code cleanup
- `type:docs` - Documentation updates
- `type:config` - Settings/build changes
- `type:test` - Test additions/updates

## 📏 Size Labels

- `size:XS` (1-10 lines) - Quick change
- `size:S` (11-50 lines) - Small change  
- `size:M` (51-200 lines) - Medium change
- `size:L` (201-500 lines) - Large change
- `size:XL` (500+ lines) - Consider splitting

---

**All labels are applied automatically** - no manual tagging required.

| Label | Review Time | Description |
|-------|-------------|-------------|
| `complexity:trivial` | 5-10 minutes | Documentation, formatting, simple fixes |
| `complexity:low` | 15-30 minutes | Straightforward code changes |
| `complexity:medium` | 30-60 minutes | Standard features with moderate logic |
| `complexity:high` | 1-2 hours | Complex algorithms or integrations |
| `complexity:critical` | 2+ hours | Core system changes, very complex |

## Quality Score Labels

These labels show how ready the PR is for review:

| Label | Meaning | What to Do |
|-------|---------|-----------|
| `score:excellent` | High quality, well documented | Quick review, likely ready to merge |
| `score:good` | Good quality, minor issues | Standard review process |
| `score:needs-work` | Multiple issues present | Provide feedback, request changes |
| `score:incomplete` | Major problems found | Send back for significant work |

## Size Labels

These labels help you plan review time:

| Label | Lines Changed | Expected Review Time |
|-------|---------------|---------------------|
| `size:XS` | < 50 lines | 10-15 minutes |
| `size:S` | 50-200 lines | 20-30 minutes |
| `size:M` | 200-500 lines | 45-60 minutes |
| `size:L` | 500-1000 lines | 1-2 hours |
| `size:XL` | > 1000 lines | 2+ hours (consider asking to split) |

## Action Labels

These labels tell you what to do with the PR:

| Label | Action Required |
|-------|----------------|
| `auto-merge-candidate` | Can approve if tests pass |
| `needs-review` | Standard review process |
| `needs-expert-review` | Route to domain expert |
| `hold-for-discussion` | Schedule team meeting |

## Quick Decision Guide

**Quick Approve**: `tier:0` + `complexity:trivial` + `score:excellent`

**Standard Review**: `tier:1-2` + `complexity:low-medium` + `score:good`

**Expert Review**: `tier:3+` OR `complexity:high+` OR `needs-expert-review`

**Send Back**: `score:needs-work` OR `score:incomplete`

**Team Meeting**: `tier:4` OR `hold-for-discussion`

---

*These labels are automatically applied based on code analysis. Use them as guidance, but always apply your judgment as a reviewer.*
