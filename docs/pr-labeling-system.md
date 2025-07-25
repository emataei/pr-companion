# PR Review Labels Guide

This guide explains the automated labels that appear on pull requests to help reviewers quickly understand what level of review is needed.

## Review Tier Labels

These labels tell you who should review the PR:

| Label | Who Reviews | When to Use |
|-------|-------------|-------------|
| `tier:0` | **Auto-merge** | Documentation fixes, typos, minor config changes |
| `tier:1` | **Junior developer** | Simple bug fixes, basic features |
| `tier:2` | **Senior developer** | Standard features, moderate changes |
| `tier:3` | **Expert/architect** | Complex logic, architecture changes |
| `tier:4` | **Team discussion** | Breaking changes, major decisions needed |

## Complexity Labels

These labels indicate how much mental effort the review will take:

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
