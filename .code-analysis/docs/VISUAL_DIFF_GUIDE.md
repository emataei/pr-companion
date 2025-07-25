# Simple UI Change Detection with Screenshots

## Overview
Automated detection and reporting of UI changes in pull requests. The system identifies UI file modifications, generates visual previews, and provides a structured summary for reviewers.

## Quick Setup

### 1. No Prerequisites Required
The system works out of the box with no additional setup needed. It automatically detects UI changes in:
- React components (`.tsx`, `.jsx`)
- Vue components (`.vue`)
- Svelte components (`.svelte`)
- Stylesheets (`.css`, `.scss`, `.less`, `.sass`)

### 2. Screenshot Generation
The system automatically:
- Builds your project when UI changes are detected
- Captures screenshots of relevant pages
- Embeds them directly in PR comments
- Provides artifact downloads as backup

## What You'll Get

### Example PR Comment
```markdown
## 🎨 UI Changes Detected

**Files Changed:** 3

🧩 Components:
- src/components/UserProfile.tsx

🎨 Styles:
- src/styles/globals.css

📄 Pages:
- src/app/layout.tsx
- src/app/page.tsx

📸 Visual Preview:

### home
![home](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8qDwAAAABJRU5ErkJggg==)

📁 Backup Download:
[Download UI Screenshots](https://github.com/owner/repo/actions/runs/123456/artifacts) - Look for `ui-screenshots-pr-123`

**Review Focus:**
- Check the modified files in the Files tab
- Review the screenshots above
- Test the changes locally
- Verify responsive design if styles changed
- Check accessibility if components changed
```

## How It Works

### 1. Automatic Detection
- Monitors all file changes in pull requests
- Identifies UI-related files by extension
- Categorizes changes (components, styles, pages)

### 2. Screenshot Generation
- Builds the project using `npm run build`
- Starts a development server
- Captures screenshots of changed pages using Playwright
- Embeds images directly in PR comments using base64 encoding

### 3. Image Embedding
- Screenshots are embedded directly in PR comments
- No external hosting required
- Images are visible immediately without downloads
- Backup artifacts are still available for download

### 4. Structured Reporting
- Organizes changes by type for easier review
- Embeds visual previews directly in comments
- Provides backup download links
- Includes actionable review checklist

## Viewing Screenshots

Screenshots are automatically embedded in PR comments and visible immediately. No downloads required!

**Backup Access:**
1. Click the "Download UI Screenshots" link if needed
2. Navigate to the GitHub Actions run artifacts
3. Find the artifact named `ui-screenshots-pr-{number}`
4. Download and extract to view the images offline

## File Categories

### 🧩 Components
- `.tsx`, `.jsx` files in `/components/` folders
- Reusable UI components

### 🎨 Styles  
- `.css`, `.scss`, `.less`, `.sass` files
- Global and component-specific styles

### 📄 Pages
- Files in `/pages/`, `/app/` folders
- Route-level components and layouts

## Benefits

### For Reviewers
- **Quick Overview**: See what UI files changed at a glance
- **Inline Screenshots**: View actual changes directly in PR comments
- **Structured Review**: Organized by change type
- **Clear Checklist**: Know exactly what to review

### For Teams
- **Embedded Visuals**: No downloads needed, see changes immediately
- **Consistent Process**: Same review flow for all UI changes
- **Faster Reviews**: Visual previews speed up understanding
- **Better Quality**: Screenshots catch visual regressions

## Performance

- **Conditional Screenshots**: Only generated when UI changes are detected
- **Efficient Building**: Uses existing project build process
- **Direct Embedding**: Images appear immediately in PR comments
- **Graceful Fallback**: Continues even if screenshot generation fails

The system is designed to be simple, fast, and reliable while providing immediate visual insights for UI change reviews.
