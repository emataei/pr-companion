const fs = require('fs');
const path = require('path');

/**
 * Generate GitHub Pages URL for an image with cache busting via filename
 */
function generateGitHubPagesUrl(filename) {
  const owner = process.env.GITHUB_REPOSITORY_OWNER || 'emataei';
  const repo = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'pr-companion';
  const prNumber = process.env.GITHUB_PR_NUMBER || process.env.PR_NUMBER;
  
  if (prNumber) {
    // Include commit SHA in filename for stronger cache busting
    const commitSha = process.env.GITHUB_SHA || 'unknown';
    const shortSha = commitSha.substring(0, 8);
    const baseName = filename.replace(/\.[^/.]+$/, ''); // Remove extension
    const extension = filename.split('.').pop();
    const cachedFilename = `${baseName}-${shortSha}.${extension}`;
    
    return `https://${owner}.github.io/${repo}/pr/${prNumber}/${cachedFilename}`;
  }
  return null;
}

/**
 * Generate display options for an image with GitHub Pages URL only
 */
function generateImageDisplayOptions(imagePath, title, base64Data, forceCompact = false) {
  const fileName = path.basename(imagePath);
  const githubPagesUrl = generateGitHubPagesUrl(fileName);
  let content = `### ${title}\n\n`;
  
  if (githubPagesUrl && imagePath && fs.existsSync(imagePath)) {
    // Use GitHub Pages URL for dynamic images
    content += `<div align="center">\n\n`;
    content += `<img src="${githubPagesUrl}" alt="${title}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />\n\n`;
    content += `</div>\n\n`;
    content += `<details>\n<summary>Image Details</summary>\n\n`;
    content += `- **File:** \`${fileName}\`\n`;
    content += `- **URL:** [${githubPagesUrl}](${githubPagesUrl})\n`;
    content += `- **Format:** ${getImageFormat(fileName)}\n`;
    content += `- **Status:** Dynamic GitHub Pages link\n`;
    content += `\n</details>\n\n`;
  } else {
    // No image available
    content += `> **Image not generated:** \`${fileName}\`\n\n`;
    content += `**Why this might happen:**\n`;
    content += `- Dependencies missing (matplotlib, seaborn, graphviz)\n`;
    content += `- Analysis scripts encountered errors\n`;
    content += `- No data available to visualize\n`;
    content += `- Project structure not compatible with this visual type\n\n`;
    content += `**To fix:** Check the workflow logs for specific error messages.\n\n`;
  }
  
  return content;
}

/**
 * Get readable image format name
 */
function getImageFormat(fileName) {
  const ext = path.extname(fileName).toLowerCase();
  const formats = {
    '.png': 'PNG (Portable Network Graphics)',
    '.svg': 'SVG (Scalable Vector Graphics)', 
    '.jpg': 'JPEG (Joint Photographic Experts Group)',
    '.jpeg': 'JPEG (Joint Photographic Experts Group)',
    '.gif': 'GIF (Graphics Interchange Format)'
  };
  return formats[ext] || 'Unknown format';
}

/**
 * Main function to generate enhanced image report with GitHub Pages URLs
 */
function generateEnhancedImageReport() {
  console.log('Generating enhanced image report with PNG displays...');
  
  // Use the correct path to .code-analysis/outputs directory
  const outputsDir = path.resolve('.code-analysis', 'outputs');  // From repository root
  
  // Ensure outputs directory exists
  if (!fs.existsSync(outputsDir)) {
    fs.mkdirSync(outputsDir, { recursive: true });
    console.log(`Created outputs directory: ${outputsDir}`);
  }
  
  // Define images with their locations (check root first, then outputs)
  const images = {
    'development_flow.png': 'PR Impact Grid',
    'story_arc.png': 'PR Summary',
    'dependency_graph_pr.png': 'PR Dependencies'
  };
  
  console.log('Looking for images in:', path.resolve(outputsDir));
  
  let reportContent = '## Enhanced PR Visuals\n\n';
  reportContent += '*Real-time analytics with dynamic images*\n\n';
  
  let hasImages = false;
  
  // Helper function to find image in the outputs directory only
  function findImage(filename) {
    const imagePath = path.join(outputsDir, filename);
    if (fs.existsSync(imagePath)) {
      console.log(`Found image: ${imagePath}`);
      return imagePath;
    }
    console.log(`Image not found: ${imagePath}`);
    return null;
  }
  
  // Process the main images
  const allImages = images;
  hasImages = false;
  
  for (const [filename, title] of Object.entries(allImages)) {
    const imagePath = findImage(filename);
    
    if (imagePath) {
      hasImages = true;
      const imageContent = generateImageDisplayOptions(imagePath, title, null, false);
      reportContent += imageContent;
      console.log(`Found and processed ${filename}`);
    } else {
      const noImageContent = generateImageDisplayOptions(filename, title, null, false);
      reportContent += noImageContent;
      console.log(`Image not found: ${filename}`);
    }
    
    reportContent += '---\n\n';
  }
  
  // Add message if no images were generated
  if (!hasImages) {
    reportContent += generateNoImagesMessage();
  }
  
  // Save the report (removed useless file listing and summary)
  const reportPath = path.join(outputsDir, 'enhanced_image_report.md');
  fs.writeFileSync(reportPath, reportContent, 'utf8');
  
  console.log(`Enhanced image report saved to: ${reportPath}`);
  console.log(`Report contains ${hasImages ? 'embedded images' : 'no images'}`);
  
  return {
    success: true,
    hasImages,
    totalImages: Object.keys(allImages).length,
    reportPath,
    reportContent
  };
}

function generateNoImagesMessage() {
  return `### No Images Generated\n\n` +
         `**Possible reasons:**\n` +
         `- **Missing Dependencies:** matplotlib, seaborn, graphviz, or other visualization tools not installed\n` +
         `- **No Analyzable Content:** Project structure doesn't contain dependency files or code changes\n` +
         `- **Script Errors:** Analysis scripts encountered errors during execution\n` +
         `- **Empty Changes:** No significant changes detected to visualize\n\n` +
         `**To resolve:**\n` +
         `1. Check the workflow logs for specific error messages\n` +
         `2. Ensure all required dependencies are installed in the CI environment\n` +
         `3. Verify your project has dependencies that can be analyzed (package.json, requirements.txt, etc.)\n` +
         `4. Make sure there are actual code changes in the PR\n\n` +
         `*Images will appear here automatically when analysis completes successfully.*\n\n`;
}

function getFileType(fileName) {
  const ext = path.extname(fileName).toLowerCase();
  if (['.json'].includes(ext)) return 'Data';
  if (['.md'].includes(ext)) return 'Report';
  if (['.txt'].includes(ext)) return 'Text';
  if (['.png', '.jpg', '.gif', '.svg'].includes(ext)) return 'Image';
  return 'File';
}

// Main execution
function main() {
  try {
    const result = generateEnhancedImageReport();
    console.log('\nEnhanced image report generation complete!');
    console.log(`Report: ${result.reportPath}`);
    console.log(`Images: ${result.hasImages ? result.totalImages + ' linked' : 'None found'}`);
    
    // Print a preview of the report content
    console.log('\n' + '='.repeat(80));
    console.log('REPORT PREVIEW (first 500 chars):');
    console.log('='.repeat(80));
    console.log(result.reportContent.substring(0, 500) + '...');
    console.log('\nFull report saved to: ' + result.reportPath);
  } catch (error) {
    console.error('Error generating enhanced image report:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { 
  generateEnhancedImageReport,
  generateImageDisplayOptions
};
