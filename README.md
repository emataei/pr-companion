# Code Evaluation Tooling

Advanced code analysis and PR visualization system for enhanced development workflows.

## Features

### 🎨 PR Visual Analytics
- **Impact Heatmaps** - Risk analysis and change visualization
- **Development Flow** - Workflow and process diagrams  
- **Story Arc Animation** - Animated PR progression
- **Dependency Graphs** - Code relationship mapping
- **Comprehensive Reports** - Detailed analysis summaries

### 🤖 AI-Enhanced Analysis
- Smart documentation suggestions
- Automated code review insights
- Intelligent change categorization
- Risk assessment algorithms

### 📊 Visualization Components
- Real-time embedded images in GitHub comments
- Interactive charts and graphs
- Base64-encoded images for instant viewing
- Responsive design for all devices

## Quick Start

### GitHub Actions (Production)
The system automatically runs on PRs when configured with the provided workflow files in `.github/workflows/`.

### Local Testing (Development)
Test the visualization system locally before deployment:

#### Windows
```cmd
cd local-visual-test
run_tests.bat
```

#### Unix/Linux/macOS
```bash
cd local-visual-test
./run_tests.sh
```

#### Python Direct
```bash
# Quick test (impact heatmap only)
python local-visual-test/scripts/quick_test.py

# Comprehensive test (all components)
python local-visual-test/scripts/comprehensive_visual_test.py
```

## Installation

### Dependencies
```bash
pip install -r requirements.txt

# Additional visualization dependencies
pip install matplotlib seaborn pandas numpy pillow networkx
```

### System Dependencies (for advanced graphs)
```bash
# Ubuntu/Debian
sudo apt-get install graphviz graphviz-dev

# macOS
brew install graphviz

# Windows - download from graphviz.org
```

## Project Structure

```
├── .code-analysis/           # Core analysis scripts
│   ├── scripts/             # Python analysis and visualization scripts
│   └── outputs/             # Generated reports and images
├── .github/workflows/       # GitHub Actions workflows
├── local-visual-test/       # Local testing and development
│   ├── scripts/            # Test runners and utilities
│   ├── outputs/            # Test results and generated files
│   └── sample-images/      # Example visualizations
├── sample-project/         # Example Next.js project for testing
└── requirements.txt        # Python dependencies
```

## Visualization Scripts

### Core Generators
- `generate_impact_heatmap.py` - Risk analysis visualization
- `generate_change_heatmap.py` - File change patterns
- `generate_development_flow.py` - Workflow diagrams
- `generate_story_arc.py` - Animated progression
- `generate_dependency_graphs.py` - Code relationships
- `generate_comprehensive_report.py` - Complete analysis

### Support Scripts
- `detect_project_structure.py` - Project type detection
- `generate_animated_summary.py` - Summary with animations
- `generate_documentation_suggestions.py` - AI-powered docs analysis

## Configuration

### GitHub Secrets (Optional)
For AI-enhanced features:
```
AI_FOUNDRY_ENDPOINT=your-azure-ai-endpoint
AI_FOUNDRY_TOKEN=your-api-token
AI_FOUNDRY_MODEL=gpt-4o
```

### Workflow Customization
Edit `.github/workflows/pr-visuals-and-docs.yml` to:
- Modify which visualizations are generated
- Adjust timeout and retry settings
- Customize file patterns for analysis
- Add custom analysis steps

## Testing

### Local Development
The `local-visual-test` directory provides comprehensive testing:

1. **Quick Test** - Tests impact heatmap generation with minimal setup
2. **Comprehensive Test** - Tests all visualization scripts with detailed reporting
3. **Dependency Check** - Validates all required packages are installed
4. **Output Validation** - Confirms expected files are generated with correct sizes

### Test Results
- Test results saved to `local-visual-test/outputs/test_results.json`
- Generated images saved to `.code-analysis/outputs/`
- Detailed logs show which components pass/fail

## Troubleshooting

### Common Issues

#### Missing Dependencies
```bash
# Install core dependencies
pip install matplotlib seaborn pandas numpy pillow

# For dependency graphs
pip install graphviz networkx
```

#### Permission Errors
```bash
# Linux/macOS
chmod +x local-visual-test/run_tests.sh

# Windows - run as administrator if needed
```

#### GitHub Actions Failures
1. Check workflow logs for specific error messages
2. Verify all dependencies are listed in `requirements.txt`
3. Test locally first using the local testing scripts
4. Check that required secrets are configured (for AI features)

#### Image Generation Issues
- Ensure matplotlib backend is properly configured
- Check available disk space in CI environment
- Verify font dependencies for chart generation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test locally using `local-visual-test/run_tests.sh` or `run_tests.bat`
4. Ensure all tests pass
5. Submit a pull request

### Development Workflow
1. Make changes to scripts in `.code-analysis/scripts/`
2. Test locally: `python local-visual-test/scripts/comprehensive_visual_test.py`
3. Check generated files in `.code-analysis/outputs/`
4. Update tests if adding new visualization types
5. Update documentation for any new features

## License

This project provides tools for enhanced code analysis and PR visualization in development workflows.

## Support

For issues and questions:
1. Check the local testing output for specific error messages
2. Review the comprehensive test results in `local-visual-test/outputs/`
3. Ensure all dependencies are properly installed
4. Test with the provided sample data first
