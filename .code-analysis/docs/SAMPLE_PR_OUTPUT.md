# Sample PR Description with Semantic Commit Analysis

Based on the changes we made, here's what would appear in the PR description:

---

## Change Story

**What:** Implements feature changes to ui components

**Why:** Updates needed for ui functionality improvement

## Change Story Arc
```
  Feature(18) → Test(15) → Fix(5) → Other(3) → Docs(3) → Refactor(1)
```

## Impact Areas
```
other        ████████████████████ 17
ui           ████████████████░░░░ 14
docs         ██████████████░░░░░░ 12
config       ██░░░░░░░░░░░░░░░░░░ 2
api          ██░░░░░░░░░░░░░░░░░░ 2
build        █░░░░░░░░░░░░░░░░░░░ 1
```

**Development Flow:** Feature → Test → Fix → Other → Docs → Refactor

**Impact:** other: 17 | ui: 14 | docs: 12

---

## Benefits Demonstrated

### For Reviewers
✅ **Instant Context**: Clear "what" and "why" at the top  
✅ **Visual Story**: See the logical flow from Feature → Test → Docs  
✅ **Impact Overview**: Know that UI (14 files) and docs (12 files) are main focus  

### For the Development Process  
✅ **Story Coherence**: Commits follow logical progression  
✅ **Quality Emphasis**: Testing was prioritized (15 test commits)  
✅ **Documentation**: Proper docs added (3 doc commits)  

### Visual Insights
- **Feature-First**: Started with feature implementation (18 commits)
- **Test-Driven**: Heavy emphasis on testing (15 commits) 
- **Quality-Focused**: Fixes and documentation included
- **Multi-Area Impact**: Touches UI, API, docs, and config

## Actual Changes Made

We created a realistic PR story by adding:

1. **feat: add user data loading and enhanced UI features** - Main feature commit
2. **feat: add ProfileDemo component for better code organization** - Component extraction  
3. **test: add comprehensive tests for UserProfile component** - Testing
4. **docs: add comprehensive UserProfile component documentation** - Documentation

This creates the rich semantic analysis you see above, giving reviewers immediate insight into the change narrative and scope.
