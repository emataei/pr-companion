# PR Review Quick Reference

A quick guide to understanding PR labels and making review decisions.

## At a Glance

| If you see... | Then... |
|---------------|---------|
| `tier:0` + `auto-merge-candidate` | Quick approve if tests pass |
| `tier:1` + `complexity:low` | You can review (15-30 min) |
| `tier:2` + `score:good` | Standard review (30-60 min) |
| `tier:3` + `needs-expert-review` | Route to expert/architect |
| `tier:4` + `hold-for-discussion` | Schedule team meeting |
| `score:needs-work` | Send back with feedback |
| `size:XL` | Block 2+ hours or ask to split |

## Review Decision Tree

```
PR Opened
    ↓
Check Tier Label
    ↓
tier:0? → Quick approve
tier:1-2? → You can review
tier:3+? → Route to expert
    ↓
Check Quality Score
    ↓
score:excellent/good? → Proceed with review
score:needs-work? → Send back for fixes
    ↓
Check Size
    ↓
size:XS/S/M? → Proceed
size:L/XL? → Plan extra time or ask to split
    ↓
Review & Approve!
```

## Time Planning

| Size | Expected Time | Plan For |
|------|---------------|----------|
| XS | 10-15 min | Coffee break review |
| S | 20-30 min | Between meetings |
| M | 45-60 min | Dedicated review block |
| L | 1-2 hours | Schedule dedicated time |
| XL | 2+ hours | Consider asking to split |

## Common Scenarios

**Quick Win**: `tier:0`, `auto-merge-candidate`, `size:XS`
- Just verify tests pass and approve

**Documentation**: `complexity:trivial`, `size:XS`
- Scan for typos and formatting, quick approve

**Bug Fix**: `tier:1`, `complexity:low`, `size:S`
- Focus on: Does the fix solve the problem correctly?

**New Feature**: `tier:2`, `complexity:medium`, `size:M`
- Standard review: logic, tests, documentation

**Architecture**: `tier:3`, `complexity:high`, `needs-expert-review`
- Route to architect or domain expert

**Critical**: `tier:4`, `hold-for-discussion`
- Don't review alone - schedule team discussion

---

*Use these labels as guidance, but always apply your judgment as a reviewer.*

**Standard Review**: `tier:1-2` + `complexity:low-medium` + `score:good` + `size:S-M`

**Expert Needed**: `tier:3+` OR `complexity:high+` OR `needs-expert-review`

**Send Back**: `score:needs-work` OR `score:incomplete`

**Team Discussion**: `tier:4` OR `hold-for-discussion`

---
*When in doubt, check the full [PR Labeling System Documentation](pr-labeling-system.md)*
