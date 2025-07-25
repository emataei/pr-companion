const { getPRNumber, loadResults, createOrUpdateComment } = require('./pr-comment-utils');

module.exports = async ({ github, context }) => {
  const prNumber = getPRNumber(context);
  
  if (!prNumber) {
    console.log('No PR number found, skipping AI pre-review comment');
    return;
  }

  const results = loadResults('ai-pre-review-results.json', { 
    summary: 'AI pre-review analysis failed',
    risk_level: 'UNKNOWN',
    risk_factors: [],
    file_categories: {},
    file_count: 0,
    ai_analysis: {
      summary: 'Analysis failed',
      business_impact: 'Unknown',
      technical_changes: 'Unknown',
      potential_issues: 'Manual review required'
    },
    confidence_metrics: {
      analysis_confidence: 'MEDIUM',
      prediction_reliability: 'MEDIUM',
      completeness: 'MEDIUM'
    }
  });

  const comment = buildComment(results);
  
  await createOrUpdateComment(
    github, 
    context, 
    prNumber, 
    comment, 
    'AI Pre-Review Analysis',
    `ai-pre-review-${context.payload?.pull_request?.head?.sha || 'unknown'}`
  );
  
  console.log('AI pre-review comment posted/updated successfully');
};

function buildComment(results) {
  const confidenceTier = getConfidenceTier(results);
  const riskLevel = getRiskLevel(results.risk_level);
  
  let comment = `## AI Pre-Review Analysis\n\n`;
  
  // Header with key metrics
  comment += `**Confidence:** ${confidenceTier} | **Risk:** ${riskLevel} | **Files:** ${results.file_count}\n\n`;

  // Concise summary section
  const summarySection = buildSummarySection(results);
  comment += summarySection;

  // File categories breakdown
  const categoriesSection = buildCategoriesSection(results);
  if (categoriesSection) {
    comment += categoriesSection;
  }

  // Business impact (if significant)
  const impactSection = buildImpactSection(results);
  if (impactSection) {
    comment += impactSection;
  }

  // Risk factors (if any)
  const riskSection = buildRiskSection(results);
  if (riskSection) {
    comment += riskSection;
  }

  // Footer
  comment += `---\n*AI pre-review analysis • Priority: First reviewer focus*`;

  return comment;
}

function getConfidenceTier(results) {
  const metrics = results.confidence_metrics || {};
  const scores = Object.values(metrics);
  
  if (scores.includes('VERY HIGH') || scores.filter(s => s === 'HIGH').length >= 2) {
    return 'VERY HIGH';
  }
  if (scores.includes('HIGH') || scores.filter(s => s === 'MEDIUM').length >= 2) {
    return 'HIGH';
  }
  if (scores.includes('MEDIUM')) {
    return 'MEDIUM';
  }
  if (scores.includes('LOW')) {
    return 'LOW';
  }
  return 'VERY LOW';
}

function getRiskLevel(riskLevel) {
  const levels = {
    'CRITICAL': 'CRITICAL',
    'HIGH': 'HIGH',
    'MEDIUM': 'MEDIUM', 
    'LOW': 'LOW',
    'MINIMAL': 'MINIMAL'
  };
  return levels[riskLevel] || 'UNKNOWN';
}

function buildSummarySection(results) {
  const summary = results.ai_analysis.summary;
  // Keep it concise - aim for 2-3 lines maximum
  const shortSummary = summary.length > 120 ? summary.substring(0, 117) + '...' : summary;
  
  return `**Summary:** ${shortSummary}\n\n`;
}

function buildCategoriesSection(results) {
  const categories = results.file_categories;
  if (!categories || Object.keys(categories).length === 0) return '';
  
  const categoryLabels = {
    'ui': 'UI Components',
    'api': 'API/Backend', 
    'database': 'Database',
    'config': 'Configuration',
    'test': 'Testing',
    'documentation': 'Documentation',
    'other': 'Other'
  };
  
  const categoryBreakdown = Object.entries(categories)
    .filter(([_, files]) => files && files.length > 0)
    .map(([category, files]) => `${categoryLabels[category] || 'Other'}: ${files.length}`)
    .join(' | ');
  
  return categoryBreakdown ? `**File Categories:** ${categoryBreakdown}\n\n` : '';
}

function buildImpactSection(results) {
  const analysis = results.ai_analysis;
  let section = '';
  
  const hasBusinessImpact = analysis.business_impact && 
    analysis.business_impact !== 'Unknown' && 
    analysis.business_impact !== 'See summary above';
    
  if (hasBusinessImpact) {
    // Keep business impact concise
    const businessImpact = analysis.business_impact.length > 100 
      ? analysis.business_impact.substring(0, 97) + '...' 
      : analysis.business_impact;
    section += `**Business Impact:** ${businessImpact}\n\n`;
  }
  
  return section;
}

function buildRiskSection(results) {
  let section = '';
  
  // Potential issues (keep concise)
  const analysis = results.ai_analysis;
  const hasPotentialIssues = analysis.potential_issues && 
    analysis.potential_issues !== 'Unknown' && 
    analysis.potential_issues !== 'Manual review recommended';
  
  if (hasPotentialIssues) {
    const potentialIssues = analysis.potential_issues.length > 100 
      ? analysis.potential_issues.substring(0, 97) + '...' 
      : analysis.potential_issues;
    section += `**Key Concerns:** ${potentialIssues}\n\n`;
  }
  
  // Risk factors (limit to top 2 most important)
  if (results.risk_factors && results.risk_factors.length > 0) {
    section += `**Risk Factors:**\n`;
    results.risk_factors.slice(0, 2).forEach(factor => {
      section += `- ${factor}\n`;
    });
    if (results.risk_factors.length > 2) {
      section += `- ... +${results.risk_factors.length - 2} more\n`;
    }
    section += `\n`;
  }
  
  return section;
}

function buildConfidenceSection(results) {
  // Removed detailed confidence section to keep comment concise
  // Confidence is already shown in header
  return '';
}
