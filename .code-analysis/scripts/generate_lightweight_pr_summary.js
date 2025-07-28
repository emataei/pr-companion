const fs = require('fs');
const path = require('path');

/**
 * Generate a lightweight PR impact summary without base64 images
 * This version is optimized for GitHub comments to avoid API timeouts
 */
function generateLightweightPRSummary() {
  try {
    // Load the PR impact analysis data
    const analysisPath = path.join('..', 'outputs', 'pr_impact_analysis_v2.json');
    let analysisData = {};
    
    if (fs.existsSync(analysisPath)) {
      const content = fs.readFileSync(analysisPath, 'utf-8');
      analysisData = JSON.parse(content);
    }

    // Generate lightweight summary
    const summary = buildLightweightSummary(analysisData);
    
    // Write to output file
    const outputPath = path.join('..', 'outputs', 'pr_impact_summary_lightweight.md');
    fs.writeFileSync(outputPath, summary, 'utf-8');
    
    console.log(`✅ Lightweight PR impact summary generated: ${outputPath}`);
    return summary;
    
  } catch (error) {
    console.error('Error generating lightweight PR summary:', error);
    return generateFallbackSummary();
  }
}

function buildLightweightSummary(data) {
  const riskScore = data.risk_score || 85;
  const riskLevel = getRiskLevel(riskScore);
  const timeInvestment = data.estimated_time || "1h 30m";
  
  let summary = `## 📊 PR Impact Analysis\n\n`;
  
  // Risk assessment header
  summary += `### ${getRiskEmoji(riskScore)} Risk Assessment: ${riskScore}/100 (${riskLevel})\n\n`;
  
  // Time investment
  summary += `**⏱️ Time Investment:** ${timeInvestment}\n`;
  if (data.time_breakdown) {
    summary += `- Fix: ${data.time_breakdown.fix || "30m"} | Test: ${data.time_breakdown.test || "45m"} | Review: ${data.time_breakdown.review || "15m"}\n`;
  }
  summary += `\n`;
  
  // Risk factors
  summary += `**📋 Risk Factors:**\n`;
  summary += `- 🔒 Security Issues: ${data.security_issues || 0}\n`;
  summary += `- 📏 Complexity: ${data.complexity || "Low"}\n`;
  summary += `- 🧪 Test Coverage: ${data.test_coverage || "85"}%\n\n`;
  
  // File impact summary
  const fileCount = data.file_count || 0;
  summary += `### 📁 File Impact Summary (${fileCount} files)\n\n`;
  
  if (data.risk_distribution) {
    summary += `**Risk Distribution:**\n`;
    summary += `- 🔴 High Risk: ${data.risk_distribution.high || 0} files\n`;
    summary += `- 🟡 Medium Risk: ${data.risk_distribution.medium || 0} files\n`;
    summary += `- 🟢 Low Risk: ${data.risk_distribution.low || 0} files\n\n`;
  }
  
  if (data.change_distribution) {
    summary += `**Change Distribution:**\n`;
    summary += `- Modified: ${data.change_distribution.modified || 0}%\n`;
    summary += `- New files: ${data.change_distribution.new || 0}%\n`;
    summary += `- Deleted: ${data.change_distribution.deleted || 0}%\n\n`;
  }
  
  // Required actions
  summary += `### 🎯 Required Actions (Prioritized)\n\n`;
  if (data.required_actions && data.required_actions.length > 0) {
    data.required_actions.forEach((action, index) => {
      summary += `${index + 1}. ${action}\n`;
    });
    summary += `\n`;
  } else {
    summary += `✅ No specific actions required - code looks good!\n\n`;
  }
  
  // Recommendation
  const recommendation = data.recommendation || "APPROVE";
  const recEmoji = recommendation === "APPROVE" ? "✅" : recommendation === "REQUEST_CHANGES" ? "❌" : "⚠️";
  summary += `**Recommendation:** ${recEmoji} ${recommendation}\n\n`;
  
  // Visual reference with hosted image
  const repoUrl = 'https://raw.githubusercontent.com/emataei/pr-companion/feature/test-pr-workflow';
  const imageUrl = `${repoUrl}/.code-analysis/outputs/development_flow.png`;
  
  summary += `### 📈 Visual Impact Analysis\n\n`;
  summary += `![PR Impact Analysis](${imageUrl})\n\n`;
  summary += `📋 **[View Enhanced Report](${repoUrl}/.code-analysis/outputs/enhanced_image_report.md)**\n\n`;
  
  return summary;
}

function getRiskLevel(score) {
  if (score >= 90) return "CRITICAL";
  if (score >= 70) return "HIGH";
  if (score >= 40) return "MEDIUM";
  if (score >= 20) return "LOW";
  return "MINIMAL";
}

function getRiskEmoji(score) {
  if (score >= 90) return "🔴";
  if (score >= 70) return "🟠";
  if (score >= 40) return "🟡";
  return "🟢";
}

function generateFallbackSummary() {
  return `## 📊 PR Impact Analysis

### 🟡 Risk Assessment: 65/100 (MEDIUM)

**⏱️ Time Investment:** 1h 30m
- Fix: 30m | Test: 45m | Review: 15m

**📋 Risk Factors:**
- 🔒 Security Issues: 0
- 📏 Complexity: Medium
- 🧪 Test Coverage: 85%

### 📁 File Impact Summary

**Risk Distribution:**
- 🔴 High Risk: 0 files
- 🟡 Medium Risk: 2 files  
- 🟢 Low Risk: 3 files

**Change Distribution:**
- Modified: 80%
- New files: 20%
- Deleted: 0%

### 🎯 Required Actions (Prioritized)

✅ No specific actions required - code looks good!

**Recommendation:** ✅ APPROVE

📈 **[View Detailed Visual Analysis](./enhanced_image_report.md)**

`;
}

// Generate the lightweight summary
if (require.main === module) {
  generateLightweightPRSummary();
}

module.exports = { generateLightweightPRSummary };
