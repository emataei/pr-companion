# Enhanced PR Visuals Workflow

This workflow automatically generates comprehensive visual analyses for pull requests, including dependency graphs, change heatmaps, and animated summaries. **It's designed to work with any repository structure and programming framework.**

## 🎯 Features

### 1. **Auto-Detection System**
- Automatically detects project type (Next.js, React, Vue, Angular, etc.)
- Finds source directories dynamically
- Adapts to any repository structure
- Works with monorepos and nested projects

### 2. **Dependency Graph Diffs**
- Generates visual dependency graphs for both base and PR branches
- Uses `madge` to analyze TypeScript/JavaScript module relationships
- Highlights structural changes in your codebase
- Fallback handling for projects without analyzable dependencies

### 3. **Change Heatmaps**
- Statistical breakdown of file modifications
- Visual representation by directory, file type, and scope
- Addition vs deletion analysis
- Smart file categorization

### 4. **Animated Summary**
- Progressive reveal of PR impact
- Complexity scoring and review time estimates
- Project-specific insights based on detected framework
- Quick visual story of changes

### 5. **Comprehensive Reporting**
- Combined markdown report with all visuals
- Automatic PR commenting with visual summaries
- Artifact storage for historical analysis
- Smart file categorization by type and purpose

## 🚀 Quick Setup (Any Repository)

### Option 1: Automated Setup Script

**Linux/Mac:**
```bash
curl -fsSL https://raw.githubusercontent.com/emadataei/codeEvalTooling/main/.github/scripts/setup.sh | bash
```

**Windows PowerShell:**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/emadataei/codeEvalTooling/main/.github/scripts/setup.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

### Option 2: Manual Setup

1. **Copy the workflow files to your repository:**
   ```bash
   mkdir -p .github/workflows .github/scripts
   
   # Copy the main workflow
   curl -o .github/workflows/enhanced-pr-visuals.yml \
     https://raw.githubusercontent.com/emadataei/codeEvalTooling/main/.github/workflows/enhanced-pr-visuals.yml
   
   # Copy the configuration template
   curl -o .github/scripts/pr-visuals-config.yml \
     https://raw.githubusercontent.com/emadataei/codeEvalTooling/main/.github/scripts/pr-visuals-config.yml
   ```

2. **The workflow will auto-detect your project structure** - no configuration needed!

3. **Test it** by creating a pull request or adding the `generate-visuals` label.

## 🏗️ Supported Project Types

The workflow automatically detects and optimizes for:

| Framework | Detection Method | Special Features |
|-----------|------------------|------------------|
| **Next.js** | `next.config.js/ts` | App Router vs Pages Router insights |
| **React** | `"react"` in package.json | Component architecture analysis |
| **Vue** | `vue.config.js` or Vue deps | Component structure insights |
| **Angular** | `angular.json` | Module dependency tracking |
| **Vite** | `vite.config.js/ts` | Build optimization insights |
| **Generic** | Any JS/TS project | Standard dependency analysis |

## 📁 Repository Structure Support

Works with any structure:
```
# Standard structure
src/
  components/
  pages/
  utils/

# Nested structure  
project/
  src/
    app/

# Monorepo
packages/
  frontend/src/
  backend/src/
apps/
  web/src/
  mobile/src/

# Custom structure
lib/
services/
modules/
```

## 🔧 Usage

### Automatic Triggers
The workflow runs automatically on:
- Pull request opened
- Pull request updated (synchronize)
- Pull request reopened

### Manual Triggers
Add the `generate-visuals` label to any PR to manually trigger the analysis.

### Sample Output

The workflow generates:

1. **Project Structure Analysis**
   - Auto-detected project type and configuration
   - Source directory mapping
   - Framework-specific insights

2. **Dependency Graphs**
   - `dependency_graph_base.png` - Base branch module structure
   - `dependency_graph_pr.png` - PR branch module structure
   - Fallback placeholders for non-analyzable projects

3. **Change Analysis**
   - `change_heatmap.png` - Multi-panel statistical visualization
   - `diff_stats.txt` - Raw git diff statistics

4. **Reports**
   - `comprehensive_pr_report.md` - Complete analysis report
   - `animated_summary.md` - Progressive summary

## ⚙️ Configuration

### Basic Configuration
The workflow works out-of-the-box with zero configuration for most projects.

### Advanced Configuration
Edit `.github/scripts/pr-visuals-config.yml` to customize:

```yaml
# Project-specific overrides
PROJECT_INFO:
  type: "nextjs"  # Override auto-detection
  source_directories: ["src", "components"]  # Custom source dirs

# Impact thresholds  
IMPACT_THRESHOLDS:
  files:
    low: 5
    medium: 10
    high: 20

# Visual settings
VISUALS:
  heatmap:
    enabled: true
    max_files_shown: 15
  dependency_graphs:
    enabled: true
    exclude_patterns: ["vendor", "third_party"]
```

## 📊 Visual Examples

### Change Heatmap
The heatmap shows:
- Top changed files by line count
- Changes grouped by directory
- File type distribution (pie chart)
- Addition vs deletion breakdown

### Dependency Graphs
- Before/after module relationship visualization
- Identifies new dependencies
- Shows architectural changes
- Graceful fallbacks for non-JS projects

### Animated Summary
- PR complexity scoring (🟢 Low / 🟡 Medium / 🔴 High)
- Estimated review time
- Framework-specific insights
- Progressive change analysis

## 🛠️ Technical Details

### Dependencies
- **madge**: JavaScript/TypeScript dependency analysis
- **matplotlib/seaborn**: Python visualization
- **pandas**: Data processing
- **GitHub Actions**: Automation platform

### Auto-Detection Process
1. **Project Type Detection**: Scans for config files and package.json
2. **Source Directory Discovery**: Looks for standard directory names
3. **File Pattern Analysis**: Adapts to found file types
4. **Fallback Handling**: Graceful degradation for edge cases

### Performance
- Typical runtime: 2-5 minutes
- Artifact retention: 30 days
- Supports repositories up to ~1000 files efficiently
- Smart timeout and fallback handling

## 🔍 Troubleshooting

### Common Issues

1. **No dependency graph generated**
   - ✅ **Solution**: Workflow creates placeholder graphs automatically
   - The project may not have analyzable JavaScript/TypeScript dependencies

2. **Empty heatmap**
   - ✅ **Solution**: Check if PR has actual file changes
   - Verify git diff returns results

3. **Wrong project type detected**
   - ✅ **Solution**: Override in configuration file:
     ```yaml
     PROJECT_INFO:
       type: "your-framework"
     ```

4. **Missing source directories**
   - ✅ **Solution**: Specify custom directories:
     ```yaml
     PROJECT_INFO:
       source_directories: ["custom/path", "another/path"]
     ```

### Debug Mode
Add this step to your workflow for debugging:

```yaml
- name: Debug Project Detection
  run: |
    echo "Detected project type: ${{ steps.detect-structure.outputs.project_type }}"
    echo "Project directory: ${{ steps.detect-structure.outputs.project_dir }}"
    echo "Source directories: ${{ steps.detect-structure.outputs.source_dirs }}"
    find . -name "*.js" -o -name "*.ts" | head -10
```

## 🌟 Advanced Features

### Monorepo Support
The workflow can detect and analyze monorepo structures:
```yaml
# Custom configuration for monorepos
REPOSITORY_OVERRIDES:
  monorepo:
    source_dirs: ["packages/*/src", "apps/*/src"]
    project_detection_depth: 2
```

### Custom File Patterns
Extend analysis to other languages:
```yaml
FILE_PATTERNS:
  source_code:
    - "**/*.py"  # Python
    - "**/*.php" # PHP
    - "**/*.rb"  # Ruby
```

### Integration with Other Workflows
The generated artifacts can be used by other workflows:
```yaml
- name: Use PR Visuals
  uses: actions/download-artifact@v4
  with:
    name: enhanced-pr-visuals
```

## 🤝 Contributing

To improve this workflow:

1. Test changes on your own fork first
2. Update configuration files as needed
3. Add new visualization types in the scripts directory
4. Update this README with new features

## 📝 License

This workflow is part of the codeEvalTooling project and follows the same license terms.

---

## 🎉 Ready to Get Started?

Just copy the `.github` folder to your repository and create a pull request - the workflow will automatically detect your project structure and generate beautiful visual analyses!
