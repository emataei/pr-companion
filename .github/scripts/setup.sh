#!/bin/bash

# Enhanced PR Visuals Setup Script
# This script helps set up the PR visuals workflow in any repository

set -e

echo "🚀 Setting up Enhanced PR Visuals Workflow"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository. Please run this from your project root.${NC}"
    exit 1
fi

# Create .github directory structure
echo -e "${YELLOW}📁 Creating directory structure...${NC}"
mkdir -p .github/workflows
mkdir -p .github/scripts

# Detect current project type
echo -e "${YELLOW}🔍 Detecting project type...${NC}"
PROJECT_TYPE="generic"

if [ -f "next.config.js" ] || [ -f "next.config.ts" ]; then
    PROJECT_TYPE="nextjs"
    echo -e "${GREEN}✅ Detected Next.js project${NC}"
elif [ -f "vite.config.js" ] || [ -f "vite.config.ts" ]; then
    PROJECT_TYPE="vite"
    echo -e "${GREEN}✅ Detected Vite project${NC}"
elif [ -f "angular.json" ]; then
    PROJECT_TYPE="angular"
    echo -e "${GREEN}✅ Detected Angular project${NC}"
elif [ -f "vue.config.js" ] || grep -q '"vue"' package.json 2>/dev/null; then
    PROJECT_TYPE="vue"
    echo -e "${GREEN}✅ Detected Vue project${NC}"
elif grep -q '"react"' package.json 2>/dev/null; then
    PROJECT_TYPE="react"
    echo -e "${GREEN}✅ Detected React project${NC}"
else
    echo -e "${YELLOW}ℹ️ Generic project detected${NC}"
fi

# Find source directories
echo -e "${YELLOW}📂 Scanning for source directories...${NC}"
SOURCE_DIRS=""
for dir in "src" "app" "components" "pages" "lib" "utils"; do
    if [ -d "$dir" ]; then
        SOURCE_DIRS="$SOURCE_DIRS $dir"
        echo -e "${GREEN}   Found: $dir${NC}"
    fi
done

if [ -z "$SOURCE_DIRS" ]; then
    SOURCE_DIRS="."
    echo -e "${YELLOW}   Using project root${NC}"
fi

# Copy workflow files (assuming they exist in the source)
echo -e "${YELLOW}📋 Installing workflow files...${NC}"

if [ -f ".github/workflows/enhanced-pr-visuals.yml" ]; then
    echo -e "${YELLOW}   Workflow already exists, backing up...${NC}"
    cp .github/workflows/enhanced-pr-visuals.yml .github/workflows/enhanced-pr-visuals.yml.backup
fi

# Create a basic workflow file if the source isn't available
cat > .github/workflows/enhanced-pr-visuals.yml << 'EOF'
# This workflow should be replaced with the full enhanced-pr-visuals.yml
# For the complete workflow, copy from the codeEvalTooling repository
name: Enhanced PR Visuals (Setup Required)

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  setup-required:
    runs-on: ubuntu-latest
    steps:
      - name: Setup Message
        run: |
          echo "⚠️ Enhanced PR Visuals workflow needs to be properly configured"
          echo "Please copy the complete workflow from:"
          echo "https://github.com/emadataei/codeEvalTooling/.github/workflows/enhanced-pr-visuals.yml"
EOF

# Create configuration file
echo -e "${YELLOW}⚙️ Creating configuration...${NC}"
cat > .github/scripts/pr-visuals-config.yml << EOF
# Enhanced PR Visuals Configuration for this repository
# Auto-generated on $(date)

PROJECT_INFO:
  type: "$PROJECT_TYPE"
  source_directories: [$( echo $SOURCE_DIRS | sed 's/ /", "/g' | sed 's/^/"/;s/$/"/' )]
  
# Customize these settings as needed
IMPACT_THRESHOLDS:
  files:
    low: 5
    medium: 10
    high: 20
  lines:
    low: 100
    medium: 500
    high: 1000

VISUALS:
  heatmap:
    enabled: true
  dependency_graphs:
    enabled: true
  animated_summary:
    enabled: true
EOF

# Create README
echo -e "${YELLOW}📖 Creating documentation...${NC}"
cat > .github/scripts/README.md << EOF
# PR Visuals Setup

This repository is configured for Enhanced PR Visuals.

## Detected Configuration

- **Project Type:** $PROJECT_TYPE
- **Source Directories:** $SOURCE_DIRS

## Next Steps

1. Copy the complete workflow from the codeEvalTooling repository
2. Customize the configuration in \`pr-visuals-config.yml\` if needed
3. Test with a sample PR

## Usage

The workflow will automatically run on:
- Pull request opened
- Pull request updated
- Manual trigger with "generate-visuals" label

Generated on: $(date)
EOF

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Summary:${NC}"
echo -e "   Project Type: ${GREEN}$PROJECT_TYPE${NC}"
echo -e "   Source Dirs:  ${GREEN}$SOURCE_DIRS${NC}"
echo -e "   Config File:  ${GREEN}.github/scripts/pr-visuals-config.yml${NC}"
echo ""
echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo -e "   1. Copy the complete workflow file from the codeEvalTooling repository"
echo -e "   2. Customize settings in the config file if needed"
echo -e "   3. Test with a sample pull request"
echo ""
echo -e "${GREEN}🎉 Your repository is ready for Enhanced PR Visuals!${NC}"
