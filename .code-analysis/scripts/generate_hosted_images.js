const fs = require('fs');
const path = require('path');

/**
 * Generate markdown with hosted image URLs instead of base64 embedding
 * This avoids GitHub comment size limits and improves performance
 */

const REPO_CONFIG = {
  owner: 'emataei',
  repo: 'pr-companion',
  branch: 'feature/test-pr-workflow', // or 'main' for production
  baseUrl: 'https://raw.githubusercontent.com'
};

function generateImageMarkdown(imageName, altText, title) {
  const imageUrl = `${REPO_CONFIG.baseUrl}/${REPO_CONFIG.owner}/${REPO_CONFIG.repo}/${REPO_CONFIG.branch}/.code-analysis/outputs/${imageName}`;
  
  return {
    markdown: `![${altText}](${imageUrl} "${title}")`,
    url: imageUrl,
    html: `<img src="${imageUrl}" alt="${altText}" title="${title}" style="max-width: 100%; height: auto;" />`
  };
}

function generateEnhancedImageReport() {
  const outputDir = path.join('..', 'outputs');
  const images = [
    {
      filename: 'development_flow.png',
      title: 'PR Impact Analysis',
      altText: 'PR Impact Grid showing risk assessment and file changes'
    }
  ];

  let markdown = `## Enhanced PR Visuals\n\n`;
  markdown += `*Real-time analytics with hosted images for optimal performance*\n\n`;

  images.forEach(img => {
    const imagePath = path.join(outputDir, img.filename);
    
    if (fs.existsSync(imagePath)) {
      const imageMarkdown = generateImageMarkdown(img.filename, img.altText, img.title);
      
      markdown += `### ${img.title}\n\n`;
      markdown += `<div align="center">\n\n`;
      markdown += `${imageMarkdown.markdown}\n\n`;
      markdown += `</div>\n\n`;
      
      // Add image details without bloating the comment
      const stats = fs.statSync(imagePath);
      const sizeKB = (stats.size / 1024).toFixed(1);
      
      markdown += `<details>\n`;
      markdown += `<summary>📊 Image Details</summary>\n\n`;
      markdown += `- **File:** \`${img.filename}\`\n`;
      markdown += `- **Size:** ${sizeKB} KB\n`;
      markdown += `- **Format:** PNG (Portable Network Graphics)\n`;
      markdown += `- **URL:** [Direct Link](${imageMarkdown.url})\n`;
      markdown += `- **Status:** ✅ Hosted for instant viewing\n\n`;
      markdown += `</details>\n\n`;
    }
  });

  // Write the hosted version
  const outputPath = path.join(outputDir, 'enhanced_image_report_hosted.md');
  fs.writeFileSync(outputPath, markdown, 'utf-8');
  
  console.log(`✅ Hosted image report generated: ${outputPath}`);
  return markdown;
}

function updatePRCommentConfig() {
  // Update the AI pre-review comment to use hosted images
  const commentPath = path.join('.', 'ai-pre-review-pr-comment.js');
  
  if (fs.existsSync(commentPath)) {
    let content = fs.readFileSync(commentPath, 'utf-8');
    
    // Replace the buildImpactAnalysisSection to use hosted images
    const newFunction = `
function buildImpactAnalysisSection() {
  try {
    // Load lightweight PR impact analysis (no base64 images)
    const fs = require('fs');
    const path = require('path');
    const impactPath = path.join('.code-analysis', 'outputs', 'pr_impact_summary_lightweight.md');
    
    if (fs.existsSync(impactPath)) {
      const content = fs.readFileSync(impactPath, 'utf-8');
      return content + '\\n';
    }
    
    return ''; // No impact analysis available
  } catch (error) {
    console.log('Could not load PR impact analysis:', error.message);
    return '';
  }
}`;

    // This would require manual update or regex replacement
    console.log('📝 Update needed in ai-pre-review-pr-comment.js:');
    console.log('Replace buildImpactAnalysisSection to use pr_impact_summary_lightweight.md');
  }
}

// Generate the hosted image report
if (require.main === module) {
  generateEnhancedImageReport();
  updatePRCommentConfig();
}

module.exports = { 
  generateImageMarkdown, 
  generateEnhancedImageReport,
  REPO_CONFIG
};
