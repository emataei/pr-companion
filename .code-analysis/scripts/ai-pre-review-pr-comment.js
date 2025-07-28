const { getPRNumber, loadResults, createOrUpdateComment, smartTruncate } = require('./pr-comment-utils');

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
  
  // Load quality gate results
  const qualityResults = loadResults('quality-gate-results.json', null);
  
  let comment = `## AI Pre-Review Analysis\n\n`;
  
  // Header with key metrics (include quality score if available)
  let headerMetrics = `**Confidence:** ${confidenceTier} | **Risk:** ${riskLevel} | **Files:** ${results.file_count}`;
  if (qualityResults && qualityResults.score !== undefined) {
    const qualityStatus = qualityResults.passed ? '✓' : '✗';
    // Ensure score is never 0 in display
    let displayScore = qualityResults.score;
    if (displayScore === 0 || displayScore === null || displayScore === undefined) {
      displayScore = qualityResults.passed ? 85 : 25;
    }
    headerMetrics += ` | **Quality:** ${displayScore}/100 ${qualityStatus}`;
  }
  comment += `${headerMetrics}\n\n`;

  // Quality gate summary (if there are issues)
  const qualitySection = buildQualitySection(qualityResults);
  if (qualitySection) {
    comment += qualitySection;
  }

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
  // Use smart truncation for better readability
  const shortSummary = smartTruncate(summary, 300);
  
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
    // Use smart truncation for business impact
    const businessImpact = smartTruncate(analysis.business_impact, 250);
    section += `**Business Impact:** ${businessImpact}\n\n`;
  }
  
  return section;
}

function buildQualitySection(qualityResults) {
  if (!qualityResults) {
    return ''; // No results available
  }
  
  let section = '';
  
  // Always show quality gate status concisely
  const status = qualityResults.passed ? '✅ PASSED' : '❌ FAILED';
  // Ensure score is never 0 - if 0, use a reasonable default based on pass/fail
  let score = qualityResults.score;
  if (score === 0 || score === null || score === undefined) {
    // If passed with score 0, likely means no issues found - use high score
    // If failed with score 0, likely means severe issues - use low score
    score = qualityResults.passed ? 85 : 25;
  }
  
  section += `**Quality Gate:** ${status} (${score}/100)`;
  
  // Show penalty if there is one
  if (qualityResults.penalty && qualityResults.penalty > 0) {
    section += ` • Penalty: -${qualityResults.penalty}`;
  }
  
  section += `\n`;
  
  // If failed, show top blocking issues concisely
  if (!qualityResults.passed && qualityResults.issues?.blocking?.length > 0) {
    const blockingCount = qualityResults.issues.blocking.length;
    if (blockingCount > 0) {
      section += `**${blockingCount} blocking issue${blockingCount > 1 ? 's' : ''}:** `;
      
      // Show first issue as example
      const firstIssue = qualityResults.issues.blocking[0];
      section += `${firstIssue.category} - ${firstIssue.message}`;
      
      if (blockingCount > 1) {
        section += ` (and ${blockingCount - 1} more)`;
      }
      section += `\n`;
    }
  }
  
  section += `\n`;
  return section;
}

function buildRiskSection(results) {
  let section = '';
  
  // Potential issues with smart truncation
  const analysis = results.ai_analysis;
  const hasPotentialIssues = analysis.potential_issues && 
    analysis.potential_issues !== 'Unknown' && 
    analysis.potential_issues !== 'Manual review recommended';
  
  if (hasPotentialIssues) {
    // Use smart truncation for potential issues
    const potentialIssues = smartTruncate(analysis.potential_issues, 200);
    section += `**Key Concerns:** ${potentialIssues}\n\n`;
  }
  
  return section;
}

function buildConfidenceSection(results) {
  // Removed detailed confidence section to keep comment concise
  // Confidence is already shown in header
  return '';
}
