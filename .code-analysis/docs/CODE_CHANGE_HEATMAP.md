# PR Code Change Heat Map

## Overview

The PR Code Change Heat Map is a visual representation of all files modified in a pull request, providing an at-a-glance understanding of where changes are concentrated and their magnitude.

## What It Shows

The heat map displays:

- **Grid Layout**: Each cell represents one changed file
- **Color Coding**:
  - 🟢 **Green**: Files with more additions than deletions (new code)
  - 🔴 **Red**: Files with more deletions than additions (code removal/cleanup)
  - 🔵 **Blue**: Files with balanced changes (refactoring)
- **Color Intensity**: Darker colors = more lines changed
- **File Information**: 
  - Truncated filename (for readability)
  - Change statistics (+additions -deletions)

## Example

```
┌─────────────┬─────────────┬─────────────┐
│ Auth.tsx    │ api.js      │ README.md   │
│ +156 -32    │ +89 -67     │ +12 -5      │
│ (Green)     │ (Blue)      │ (Light)     │
├─────────────┼─────────────┼─────────────┤
│ utils.py    │ test.py     │ config.yml  │
│ +78 -45     │ +34 -18     │ +23 -8      │
│ (Green)     │ (Green)     │ (Light)     │
└─────────────┴─────────────┴─────────────┘
```

## Statistics Included

The heat map comment includes:

- **Total Files Changed**: Number of files in the PR
- **Total Lines Added**: Sum of all additions
- **Total Lines Deleted**: Sum of all deletions
- **Net Change**: Overall line difference
- **Most Changed File**: File with highest change count
- **File Type Distribution**: Top 5 file types modified

## How It's Generated

1. **Workflow Trigger**: Runs automatically on PR open/update
2. **Diff Analysis**: Git diff stats parsed from base branch
3. **Visualization**: matplotlib generates PNG heat map
4. **Metadata**: JSON file with detailed statistics
5. **Deployment**: Image uploaded to GitHub Pages
6. **Comment**: Posted as separate PR comment with image and stats

## Technical Details

### Script: `generate_code_change_heatmap.py`

**Key Features:**
- Parses git diff stats from `diff_stats.txt`
- Calculates optimal grid dimensions for layout
- Normalizes color intensity based on max changes
- Limits to top 50 files for readability
- Generates both image and metadata JSON

**Dependencies:**
- matplotlib (visualization)
- numpy (color calculations)
- pathlib (file handling)

**Output Files:**
- `code_change_heatmap.png` - The visual heat map
- `heatmap_metadata.json` - Statistics and metadata

### Script: `heatmap-pr-comment.js`

**Key Features:**
- Loads metadata from JSON file
- Constructs formatted PR comment
- Updates existing comment if found (avoids duplicates)
- Includes fallback for deployment delays
- Cache-busting for image URLs

**Comment Marker:**
```html
<!-- PR_HEATMAP_COMMENT -->
```

## Benefits

### For Developers
- **Quick Overview**: See change distribution at a glance
- **Risk Assessment**: Identify files with heavy modifications
- **Code Review Focus**: Prioritize reviewing densely changed areas
- **Pattern Recognition**: Spot refactoring patterns visually

### For Reviewers
- **Context**: Understand scope before diving into code
- **Priority**: Focus on high-change files first
- **Balance**: See if changes are balanced or one-sided
- **Type Distribution**: Know which languages/file types affected

### For Project Managers
- **Scope Visibility**: Quick assessment of PR size
- **Risk Indicators**: Large red areas = potential issues
- **Progress Tracking**: Visual change patterns over time
- **Resource Planning**: Estimate review time needed

## Configuration

### Adjusting File Limit

To change the maximum files displayed (default: 50):

```python
# In generate_code_change_heatmap.py
if len(file_changes) > 50:  # Change this number
    file_changes = file_changes[:50]
```

### Customizing Colors

Colors can be adjusted in `get_change_color()`:

```python
# More deletions - red tones
base_color = np.array([231, 76, 60]) / 255.0  # RGB

# More additions - green tones  
base_color = np.array([39, 174, 96]) / 255.0  # RGB

# Balanced - blue tones
base_color = np.array([52, 152, 219]) / 255.0  # RGB
```

### Cell Sizing

Adjust grid cell dimensions:

```python
# In generate_code_change_heatmap()
cell_size = 1.5  # Increase for larger cells
```

## Troubleshooting

### Heat Map Not Showing

**Issue**: Comment shows but image is broken
**Solution**: 
- Wait 5-10 minutes for GitHub Pages deployment
- Verify GitHub Pages is enabled in repo settings
- Check gh-pages branch exists

**Issue**: No comment posted
**Solution**:
- Check workflow logs for errors
- Verify files were changed in PR
- Ensure metadata file was generated

### Image Quality Issues

**Issue**: Text is too small/blurry
**Solution**: Increase DPI in save function:

```python
fig.savefig(png_path, dpi=100)  # Increase from 100 to 150
```

**Issue**: File names truncated
**Solution**: Adjust truncation length:

```python
display_name = truncate_filename(Path(filename).name, max_length=15)
# Increase max_length as needed
```

### Performance Concerns

**Issue**: Heat map generation is slow
**Solution**:
- Already limited to 50 files
- Consider further limiting for large repos
- Optimize matplotlib figure size

## Integration

The heat map is fully integrated into the unified PR analysis workflow:

```yaml
- name: Generate code change heat map
  run: python .code-analysis/scripts/generate_code_change_heatmap.py
  continue-on-error: true

# Image automatically deployed via existing PNG deployment step

- name: Comment PR with code change heat map
  uses: actions/github-script@v7
  with:
    script: |
      const script = require('./.code-analysis/scripts/heatmap-pr-comment.js');
      return await script({ github, context });
```

## Future Enhancements

Potential improvements:
- [ ] Interactive heat map with clickable cells
- [ ] Historical comparison (current vs previous PR)
- [ ] Complexity overlay (combine with cognitive analysis)
- [ ] Directory grouping for large PRs
- [ ] File type filtering options
- [ ] Export to different formats (SVG, PDF)

## License

This feature is part of the PR Companion project and follows the same license terms.
