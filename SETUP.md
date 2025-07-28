# 🚀 5-Minute Setup Guide

## Step 1: Copy Files (30 seconds)
```bash
# Copy these 2 folders to your repository root:
.code-analysis/
.github/workflows/
```

## Step 2: GitHub Secrets (2 minutes)
1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

| Name | Value | Required |
|------|--------|----------|
| `AI_FOUNDRY_ENDPOINT` | Your Azure AI endpoint URL | ✅ Yes |
| `AI_FOUNDRY_TOKEN` | Your Azure AI API key | ✅ Yes |
| `AI_FOUNDRY_MODEL` | `gpt-4o` (or your model) | ✅ Yes |

## Step 3: Test (30 seconds)
1. Create any PR in your repository
2. Watch for automated comments with visual analysis
3. Done! 🎉

---

## 🆘 Troubleshooting

**No comments appearing?**
- Check Actions tab for workflow runs
- Verify secrets are set correctly
- Ensure PR has code changes (not just markdown)

**AI analysis failing?**
- Verify your Azure AI endpoint is active
- Check API key permissions
- Model name must match your deployment

**Need help?**
- Check workflow logs in Actions tab
- All features work without AI (visuals only)
- Create an issue if problems persist

---

## 🔄 What Happens Next

Every PR will automatically get:
- ⚡ **Quality score** (0-100) in ~30 seconds
- 📊 **Visual impact analysis** with embedded images
- 🏷️ **Smart labels** (feature/bugfix/refactor/etc.)
- 📝 **Documentation suggestions** 
- 🎯 **Risk assessment** with actionable insights

**Zero maintenance required** - just create PRs and get instant analysis.
