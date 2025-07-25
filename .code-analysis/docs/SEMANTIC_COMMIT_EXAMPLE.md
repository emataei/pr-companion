# Semantic Commit Log - Example Output

This shows what the new PR description section would look like:

---

## Change Story

**What:** Implements new semantic commit analysis feature with visual storytelling for PR descriptions.

**Why:** Improves reviewer experience by providing clear narrative context and visual flow of changes.

## Change Story Arc
```
  Setup(1) → Feature(3) → Docs(1) → Test(1)
```

## Impact Areas
```
api          ████████████████████ 4
ui           ███████████████░░░░░ 3
config       ██████░░░░░░░░░░░░░░░ 2
docs         ████░░░░░░░░░░░░░░░░░ 1
```

**Development Flow:** Setup → Feature → Docs → Test

**Impact:** api: 4 | ui: 3 | config: 2

---

## Key Benefits

### For Reviewers
- **Quick Context**: Understand the "what" and "why" at a glance
- **Visual Flow**: See the logical progression of changes
- **Impact Overview**: Know which system areas are affected

### For Development Teams
- **Story Consistency**: Ensures PRs tell a coherent story
- **Review Efficiency**: Reduces time to understand PR intent
- **Quality Gate**: Encourages thoughtful commit organization

### Visual Approaches Available

1. **Commit Flow Diagram**: Shows temporal progression
2. **Impact Radar**: Displays system area coverage  
3. **Story Arc**: Narrative structure visualization
4. **File Dependency Graph**: For complex changes

## Integration

This feature integrates with your existing pipeline:
- Runs after commit analysis
- Updates PR description automatically
- Falls back to comment if description update fails
- Works alongside existing PR comment system

The system is designed to complement, not replace, your current PR analysis tools.
