const fs = require('fs');
const path = require('path');

/**
 * Convert an image file to base64 data URL
 */
async function convertImageToBase64(imagePath) {
  try {
    if (!fs.existsSync(imagePath)) {
      return null;
    }
    
    const imageBuffer = fs.readFileSync(imagePath);
    const ext = path.extname(imagePath).toLowerCase();
    let mimeType = 'image/png';
    
    if (ext === '.jpg' || ext === '.jpeg') mimeType = 'image/jpeg';
    else if (ext === '.gif') mimeType = 'image/gif';
    else if (ext === '.svg') mimeType = 'image/svg+xml';
    
    return `data:${mimeType};base64,${imageBuffer.toString('base64')}`;
  } catch (error) {
    console.log(`Could not convert image ${imagePath}:`, error.message);
    return null;
  }
}

/**
 * Generate display options for an image with size-aware embedding
 */
function generateImageDisplayOptions(imagePath, title, base64Data, forceCompact = false) {
  const fileName = path.basename(imagePath);
  let content = `### ${title}\n\n`;
  
  if (base64Data && !forceCompact) {
    const sizeKB = Buffer.byteLength(base64Data.split(',')[1], 'base64') / 1024;
    
    // Embed images up to 100KB to ensure they show in PR comments
    if (sizeKB < 100) {
      content += `<div align="center">\n\n`;
      content += `<img src="${base64Data}" alt="${title}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />\n\n`;
      content += `</div>\n\n`;
      content += `<details>\n<summary>📊 Image Details</summary>\n\n`;
      content += `- **File:** \`${fileName}\`\n`;
      content += `- **Size:** ${sizeKB.toFixed(1)} KB\n`;
      content += `- **Format:** ${getImageFormat(fileName)}\n`;
      content += `- **Status:** ✅ Embedded for instant viewing\n`;
      content += `\n</details>\n\n`;
    } else {
      // Large image - provide compact reference
      content += `> **Large Image Available:** \`${fileName}\` (${sizeKB.toFixed(1)} KB)\n\n`;
      content += `Image too large for inline display. Available in workflow artifacts.\n\n`;
    }
  } else if (base64Data && forceCompact) {
    // Compact mode - just reference the image
    const sizeKB = Buffer.byteLength(base64Data.split(',')[1], 'base64') / 1024;
    content += `> **📊 Large Image Generated:** \`${fileName}\` (${sizeKB.toFixed(1)} KB)\n\n`;
    content += `> Image is too large for inline display but available in workflow artifacts.\n\n`;
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
 * Main function to generate enhanced image report with embedded PNGs
 */
async function generateEnhancedImageReport() {
  console.log('Generating enhanced image report with PNG displays...');
  
  const outputsDir = '.code-analysis/outputs';
  const rootDir = '.';
  
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
  reportContent += '*Real-time analytics with embedded images for instant viewing*\n\n';
  
  let hasImages = false;
  let totalSize = 0;
  
  // Helper function to find image in multiple locations
  function findImage(filename) {
    const locations = [rootDir, outputsDir];
    for (const location of locations) {
      const imagePath = path.join(location, filename);
      if (fs.existsSync(imagePath)) {
        return imagePath;
      }
    }
    return null;
  }
  
  // Process the main images
  const allImages = images;
  const MAX_COMMENT_SIZE = 58000; // Conservative limit for GitHub comments with base64 images
  let currentSize = reportContent.length;
  let forceCompact = false;
  
  // First pass: calculate total content size to determine if we need compact mode
  let estimatedSize = currentSize;
  const imageData = [];
  
  for (const [filename, title] of Object.entries(allImages)) {
    const imagePath = findImage(filename);
    const base64Data = imagePath ? await convertImageToBase64(imagePath) : null;
    imageData.push({ filename, title, imagePath, base64Data });
    
    if (base64Data) {
      // Estimate content size (base64 + markup)
      estimatedSize += base64Data.length + 500; // markup overhead
    }
  }
  
  // Switch to compact mode if estimated size is too large
  if (estimatedSize > MAX_COMMENT_SIZE) {
    forceCompact = true;
    console.log(`⚠️  Large content detected (${(estimatedSize/1024).toFixed(1)}KB), using compact mode`);
  }
  
  // Second pass: generate content with appropriate mode
  for (const { filename, title, imagePath, base64Data } of imageData) {
    if (base64Data) {
      hasImages = true;
      const sizeKB = Buffer.byteLength(base64Data.split(',')[1], 'base64') / 1024;
      totalSize += sizeKB;
      
      const imageContent = generateImageDisplayOptions(imagePath, title, base64Data, forceCompact);
      
      // Check if adding this content would exceed the limit
      if (currentSize + imageContent.length > MAX_COMMENT_SIZE) {
        forceCompact = true;
        console.log(`⚠️  Switching to compact mode due to size limit`);
        // Regenerate in compact mode
        const compactContent = generateImageDisplayOptions(imagePath, title, base64Data, true);
        reportContent += compactContent;
        currentSize += compactContent.length;
      } else {
        reportContent += imageContent;
        currentSize += imageContent.length;
      }
      
      console.log(`✓ ${forceCompact ? 'Referenced' : 'Embedded'} ${filename} (${sizeKB.toFixed(1)} KB)`);
    } else {
      const noImageContent = generateImageDisplayOptions(filename, title, null, forceCompact);
      reportContent += noImageContent;
      currentSize += noImageContent.length;
      console.log(`✗ Image not found: ${filename}`);
    }
    
    reportContent += '---\n\n';
    currentSize += 7; // "---\n\n"
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
    reportContent,
    totalSizeKB: totalSize
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
async function main() {
  try {
    const result = await generateEnhancedImageReport();
    console.log('\nEnhanced image report generation complete!');
    console.log(`Report: ${result.reportPath}`);
    console.log(`Images: ${result.hasImages ? result.totalImages + ' embedded' : 'None found'}`);
    console.log(`Total size: ${result.totalSizeKB.toFixed(1)} KB`);
    
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
  convertImageToBase64,
  generateImageDisplayOptions
};
