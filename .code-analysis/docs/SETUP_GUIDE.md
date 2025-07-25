# Quick Setup Guide

## 🚀 Getting Started

### 1. Configure AI Provider
Set up Azure AI Foundry or OpenAI credentials:
```bash
# In GitHub repository secrets
AI_FOUNDRY_ENDPOINT=https://your-endpoint.openai.azure.com/
AI_FOUNDRY_TOKEN=your-token-here
AI_FOUNDRY_MODEL=gpt-4
```

### 2. Enable Workflows
Both workflows run automatically on PR events:
- `build.yml` - Quality gate analysis
- `cognitive_scoring.yml` - Cognitive analysis & team assignment

## 🔧 Customization

### Adjust Complexity Thresholds
```json
{
  "complexity_thresholds": {
    "high_complexity": 70,
    "security_keywords": ["auth", "password", "token"],
    "critical_paths": ["src/core/", "database/"]
  }
}
```

### Test Configuration
```bash
python .code-analysis/scripts/update_pr_metadata.py \
  --pr-number 123 \
  --dry-run
```

## What You Get

- **Automatic tier assignment** based on code complexity
- **Rich PR comments** with actionable feedback
- **Quality gates** that catch issues before review
- **Predictable SLAs** for each complexity tier


### Required Permissions
- `contents: read`
- `issues: write`
- `pull-requests: write`
