# ⚡ Quick Review Guide

**Use PR labels to make fast, effective review decisions.**

## 🚨 Instant Decisions

| If PR has... | Do this... | Time needed |
|-------------|-----------|-------------|
| `tier:0` + `score:excellent` | ✅ **Auto-approve** | 30 seconds |
| `score:poor` | ❌ **Request changes** | 5 minutes |
| `size:XL` | 🔄 **Ask to split** | N/A |
| `tier:4` | 👥 **Schedule discussion** | Meeting |

## 📋 Standard Review Flow

### Step 1: Check Quality Score
- **90-100** (Excellent) → Fast approval path
- **70-89** (Good) → Standard review  
- **50-69** (Needs work) → Focus on highlighted issues
- **<50** (Poor) → Request major changes

### Step 2: Match Your Expertise
- **tier:1** → Any developer can review
- **tier:2** → Senior+ developers  
- **tier:3** → Domain expert required
- **tier:4** → Team consensus needed

### Step 3: Allocate Time
- **XS/S** → 15-30 minutes
- **M** → 30-60 minutes
- **L** → 1-2 hours
- **XL** → Ask to split first

## 🎯 Focus Areas by Type

- **type:feature** → Test new functionality thoroughly
- **type:bugfix** → Verify fix and test edge cases  
- **type:refactor** → Check for behavior changes
- **type:security** → Extra scrutiny required
- **type:breaking** → Ensure migration path exists

## 🚀 Pro Tips

- **High scores** = Focus on architecture/design
- **Low scores** = Check basic functionality first  
- **XL size** = Always request splitting
- **tier:0** = Safe to auto-approve if tests pass

---

*Labels update automatically on every commit - refresh to see latest status.*
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
