const { getPRNumber, loadResults, createOrUpdateComment } = require('./pr-comment-utils');

module.exports = async ({ github, context }) => {
  const prNumber = getPRNumber(context);
  
  if (!prNumber) {
    console.log('No PR number found, skipping cognitive analysis comment');
    return;
  }

  const results = loadResults('cognitive-analysis-results.json', { 
    tier: 0, 
    total_score: 0, 
    reasoning: 'Failed to load results',
    complexity_categories: {
      architectural: 'LOW',
      logical: 'LOW', 
      integration: 'LOW',
      domain: 'LOW'
    }
  });

  const comment = buildComment(results);
  
  await createOrUpdateComment(
    github, 
    context, 
    prNumber, 
    comment, 
    'Cognitive Complexity Analysis',
    `cognitive-analysis-${context.payload?.pull_request?.head?.sha || 'unknown'}`
  );
  
  console.log('Cognitive analysis comment posted/updated successfully');
  
  console.log('Cognitive analysis comment posted/updated successfully');
};

function buildComment(results) {
  const complexityTier = getComplexityTier(results);
  const reviewTier = getReviewTier(results.tier);
  
  let comment = `## Cognitive Complexity Analysis\n\n`;
  
  // Header with complexity and review tiers
  comment += `**Complexity:** ${complexityTier} | **Review:** ${reviewTier}\n`;
  comment += `**Score:** ${results.total_score} points\n\n`;

  // Complexity category breakdown
  const categorySection = buildCategorySection(results);
  if (categorySection) {
    comment += categorySection;
  }

  // AST metrics summary
  const astSection = buildASTSection(results);
  if (astSection) {
    comment += astSection;
  }

  // Review guidelines (removed complex files section)
  const reviewSection = buildReviewSection(results.tier);
  comment += reviewSection;

  // Footer
  comment += `---\n*Cognitive complexity analysis • Auto-updated*`;

  return comment;
}

function getComplexityTier(results) {
  const score = results.total_score;
  const categories = results.complexity_categories || {};
  
  // Check if any category is CRITICAL
  const hasCritical = Object.values(categories).some(cat => cat === 'CRITICAL');
  if (hasCritical || score > 80) return 'CRITICAL';
  
  // Check if any category is HIGH
  const hasHigh = Object.values(categories).some(cat => cat === 'HIGH');
  if (hasHigh || score > 60) return 'HIGH';
  
  // Check if any category is MEDIUM
  const hasMedium = Object.values(categories).some(cat => cat === 'MEDIUM');
  if (hasMedium || score > 30) return 'MEDIUM';
  
  if (score > 10) return 'LOW';
  return 'VERY LOW';
}

function getReviewTier(tier) {
  const tiers = {
    0: 'AUTO-MERGE',
    1: 'STANDARD', 
    2: 'EXPERT'
  };
  return tiers[tier] || 'EXPERT';
}

function buildCategorySection(results) {
  const categories = results.complexity_categories;
  if (!categories) return '';
  
  let section = `### Complexity Categories\n`;
  section += `| Category | Level | Description |\n`;
  section += `|----------|-------|-------------|\n`;
  
  const categoryDescriptions = {
    architectural: 'System design and structure changes',
    logical: 'Business logic and algorithmic complexity',
    integration: 'Inter-component and external system interactions', 
    domain: 'Domain-specific knowledge requirements'
  };
  
  Object.entries(categories).forEach(([category, level]) => {
    const desc = categoryDescriptions[category] || 'General complexity';
    section += `| ${capitalize(category)} | ${level} | ${desc} |\n`;
  });
  
  section += `\n`;
  return section;
}

function buildASTSection(results) {
  if (!results.ast_metrics?.summary) return '';
  
  const summary = results.ast_metrics.summary;
  let section = `### Code Metrics\n`;
  section += `| Metric | Value | Impact |\n`;
  section += `|--------|-------|--------|\n`;
  section += `| Cyclomatic Complexity | ${summary.total_cyclomatic_complexity} | ${getImpactLevel(summary.total_cyclomatic_complexity, [10, 20])} |\n`;
  section += `| Max Nesting Depth | ${summary.max_nesting_depth} | ${getImpactLevel(summary.max_nesting_depth, [3, 5])} |\n`;
  section += `| Total Functions | ${summary.total_functions} | ${getImpactLevel(summary.total_functions, [5, 15])} |\n`;
  section += `| Control Structures | ${summary.total_control_structures} | ${getImpactLevel(summary.total_control_structures, [15, 30])} |\n`;
  section += `\n`;
  
  return section;
}

function buildReviewSection(tier) {
  let section = `### Review Guidelines\n\n`;
  
  if (tier === 0) {
    section += `**AUTO-MERGE ELIGIBLE**\n`;
    section += `- Low complexity change suitable for automated merge\n`;
    section += `- Focus: Verify tests pass and no breaking changes\n`;
    section += `- Timeline: Immediate upon CI success\n\n`;
  } else if (tier === 1) {
    section += `**STANDARD REVIEW REQUIRED**\n`;
    section += `- Moderate complexity requiring human review\n`;
    section += `- Focus: Code correctness, style, basic logic\n`;
    section += `- Timeline: 12-24 hours for review completion\n\n`;
  } else {
    section += `**EXPERT REVIEW REQUIRED**\n`;
    section += `- High complexity requiring domain expertise\n`;
    section += `- Focus: Architecture, performance, security implications\n`;
    section += `- Timeline: 48+ hours, may need multiple reviewers\n\n`;
  }
  
  return section;
}

function getImpactLevel(value, thresholds) {
  if (value > thresholds[1]) return 'HIGH';
  if (value > thresholds[0]) return 'MEDIUM';
  return 'LOW';
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
