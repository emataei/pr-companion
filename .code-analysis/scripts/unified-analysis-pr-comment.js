#!/usr/bin/env node

/**
 * Unified PR Analysis Comment
 * Consolidates all AI analysis into a single, comprehensive comment
 * with consistent confidence scoring and visual indicators
 */

const fs = require('fs');
const path = require('path');

// Confidence level definitions
const CONFIDENCE_LEVELS = {
  HIGH: { 
    threshold: 80, 
    description: "AI analysis is reliable, can guide review focus",
    indicator: "🟢"
  },
  MEDIUM: { 
    threshold: 60, 
    description: "AI provides useful insights, verify conclusions",
    indicator: "🟡"
  },
  LOW: { 
    threshold: 40, 
    description: "AI offers basic classification, manual review required",
    indicator: "🟠"
  },
  VERY_LOW: { 
    threshold: 0, 
    description: "Fallback analysis only, full manual review essential",
    indicator: "🔴"
  }
};

function loadResults(filePath, fallback = null) {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    }
    if (fs.existsSync(path.basename(filePath))) {
      const content = fs.readFileSync(path.basename(filePath), 'utf8');
      return JSON.parse(content);
    }
  } catch (error) {
    console.warn(`Warning: Could not load ${filePath}:`, error.message);
  }
  return fallback;
}

function getConfidenceLevel(score) {
  for (const [level, config] of Object.entries(CONFIDENCE_LEVELS)) {
    if (score >= config.threshold) {
      return { level, ...config };
    }
  }
  return { level: 'VERY_LOW', ...CONFIDENCE_LEVELS.VERY_LOW };
}

function calculateOverallConfidence(components) {
  // Weighted average of all confidence components - only use real data
  const weights = {
    changeClassification: 0.3,
    riskAssessment: 0.4,
    impactAnalysis: 0.3
  };
  
  let totalScore = 0;
  let totalWeight = 0;
  
  for (const [component, weight] of Object.entries(weights)) {
    if (components[component] !== null && components[component] !== undefined) {
      totalScore += components[component] * weight;
      totalWeight += weight;
    }
  }
  
  return totalWeight > 0 ? Math.round(totalScore / totalWeight) : 0;
}

function getTierInfo(cognitiveResults) {
  if (!cognitiveResults || !cognitiveResults.total_score) return null;
  
  const score = cognitiveResults.total_score;
  const tier = cognitiveResults.tier;
  
  const tierDescriptions = {
    0: 'Auto-Merge Eligible',
    1: 'Standard Review',
    2: 'Expert Review Required'
  };
  
  return {
    tier,
    score,
    description: tierDescriptions[tier] || 'Standard Review'
  };
}

function getRiskAssessmentScore(aiPreReview) {
  if (!aiPreReview || !aiPreReview.confidence_metrics?.analysis_confidence) return null;
  
  const confidence = aiPreReview.confidence_metrics.analysis_confidence;
  if (confidence === 'HIGH') return 85;
  if (confidence === 'MEDIUM') return 70;
  if (confidence === 'LOW') return 45;
  return 25;
}

function getStatusIndicator(score) {
  if (score >= 70) return '✓';
  if (score >= 50) return '⚠️';
  return '❌';
}

function getRiskIndicator(riskLevel) {
  if (riskLevel === 'HIGH') return '🔴';
  if (riskLevel === 'MEDIUM') return '🟡';
  return '🟢';
}

function buildHeaderSection(confidenceLevel, overallConfidence, tierInfo) {
  if (!tierInfo) return ''; // Don't show header if no cognitive data
  
  const progressBar = createProgressBar(overallConfidence);
  let section = `## AI Analysis Summary\n\n`;
  section += `<table><tr><td>\n\n`;
  section += `**${confidenceLevel.indicator} ${confidenceLevel.level} CONFIDENCE** (${overallConfidence}%)\n`;
  section += `${progressBar}\n\n`;
  section += `**${getTierEmoji(tierInfo.tier)} ${tierInfo.description}** • Complexity: ${tierInfo.score}/100\n\n`;
  section += `</td></tr></table>\n\n`;
  return section;
}

function createProgressBar(percentage) {
  const filled = Math.floor(percentage / 10);
  const empty = 10 - filled;
  return '▓'.repeat(filled) + '░'.repeat(empty);
}

function getTierEmoji(tier) {
  const emojis = { 0: '🟢', 1: '🟡', 2: '🔴' };
  return emojis[tier] || '🟡';
}

function buildConfidenceBreakdown(confidenceComponents) {
  // Only show if we have real confidence data
  const validComponents = Object.entries(confidenceComponents).filter(([key, value]) => value !== null);
  if (validComponents.length === 0) return '';
  
  let section = `### Confidence Breakdown\n\n`;
  section += `<table>\n`;
  
  for (const [component, score] of validComponents) {
    const componentName = component.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
    const status = getStatusIndicator(score);
    const bar = createMiniProgressBar(score);
    section += `<tr><td><strong>${componentName}</strong></td><td>${bar}</td><td><strong>${score}%</strong></td><td>${status}</td></tr>\n`;
  }
  section += `</table>\n\n`;
  return section;
}

function createMiniProgressBar(percentage) {
  const filled = Math.floor(percentage / 20);
  const empty = 5 - filled;
  return '■'.repeat(filled) + '□'.repeat(empty);
}

function buildChangeClassificationSection(intentClassification) {
  if (!intentClassification.primary_intent) return '';
  
  let section = `### Change Type\n\n`;
  const intent = intentClassification.primary_intent.toUpperCase();
  const confidence = Math.round(intentClassification.confidence * 100);
  
  section += `<table><tr><td>\n\n`;
  section += `**${getChangeTypeEmoji(intent)} ${intent}** (${confidence}% confidence)\n\n`;
  
  if (intentClassification.secondary_intents?.length > 0) {
    const secondaryIntents = intentClassification.secondary_intents
      .filter(([intent, conf]) => conf > 0.3)
      .slice(0, 2)
      .map(([intent, conf]) => `${intent.toUpperCase()} (${Math.round(conf * 100)}%)`)
      .join(' • ');
    if (secondaryIntents) {
      section += `*Also: ${secondaryIntents}*\n\n`;
    }
  }
  section += `</td></tr></table>\n\n`;
  return section;
}

function getChangeTypeEmoji(type) {
  const emojis = {
    'FEATURE': '✨',
    'BUGFIX': '🐛',
    'REFACTOR': '♻️',
    'DOCUMENTATION': '📝',
    'TEST': '🧪',
    'CHORE': '🔧',
    'STYLE': '💄'
  };
  return emojis[type] || '🔄';
}

function buildRiskAssessmentSection(aiPreReview) {
  if (!aiPreReview.risk_level) return '';
  
  let section = `### Risk Assessment\n\n`;
  const riskLevel = aiPreReview.risk_level;
  const riskIndicator = getRiskIndicator(riskLevel);
  
  section += `<table><tr><td>\n\n`;
  section += `**${riskIndicator} ${riskLevel} RISK**\n\n`;
  
  if (aiPreReview.risk_factors?.length > 0) {
    section += `**Key Concerns:**\n`;
    aiPreReview.risk_factors.slice(0, 2).forEach(factor => {
      section += `• ${factor}\n`;
    });
  }
  section += `\n</td></tr></table>\n\n`;
  return section;
}

function buildQualityGateSection(qualityGate) {
  if (qualityGate.score === undefined) return '';
  
  let section = `### Quality Gate\n\n`;
  const qualityStatus = qualityGate.passed ? '✅ PASS' : '❌ FAIL';
  const qualityScore = qualityGate.score || 0;
  
  section += `<table><tr><td>\n\n`;
  section += `**${qualityStatus}** (${qualityScore}/100)\n\n`;
  
  if (qualityGate.blocking_issues?.length > 0) {
    section += `**Issues Found:**\n`;
    qualityGate.blocking_issues.slice(0, 2).forEach(issue => {
      section += `• ${issue.type}: ${issue.message}\n`;
    });
  }
  section += `\n</td></tr></table>\n\n`;
  return section;
}

function buildImpactAnalysisSection(impactPrediction) {
  if (!impactPrediction.impacts?.length) return '';
  
  let section = `### Impact Analysis\n\n`;
  const criticalImpacts = impactPrediction.impacts.filter(i => i.severity === 'critical');
  const highImpacts = impactPrediction.impacts.filter(i => i.severity === 'high');
  
  section += `<table><tr><td>\n\n`;
  
  if (criticalImpacts.length > 0) {
    section += `**🔴 Critical:** ${criticalImpacts.length} impacts\n`;
    criticalImpacts.slice(0, 1).forEach(impact => {
      section += `• ${impact.description}\n`;
    });
    section += `\n`;
  }
  
  if (highImpacts.length > 0) {
    section += `**🟡 High:** ${highImpacts.length} impacts\n`;
    highImpacts.slice(0, 1).forEach(impact => {
      section += `• ${impact.description}\n`;
    });
  }
  section += `\n</td></tr></table>\n\n`;
  return section;
}

function buildRecommendedActionsSection(overallConfidence, tierInfo) {
  if (!tierInfo || overallConfidence === 0) return ''; // Don't show if no real data
  
  let section = `### Next Actions\n\n`;
  
  section += `<table><tr><td>\n\n`;
  
  if (overallConfidence >= 80) {
    section += `**🟢 High Confidence**\n`;
    section += `• Focus review on AI-highlighted areas\n`;
    section += `• Use AI insights to guide priorities\n\n`;
  } else if (overallConfidence >= 60) {
    section += `**🟡 Medium Confidence**\n`;
    section += `• Use AI as starting point\n`;
    section += `• Verify AI conclusions manually\n\n`;
  } else if (overallConfidence >= 40) {
    section += `**🟠 Low Confidence**\n`;
    section += `• AI provides basic context only\n`;
    section += `• Conduct thorough manual review\n\n`;
  } else {
    section += `**� Very Low Confidence**\n`;
    section += `• Rely primarily on manual review\n`;
    section += `• AI analysis may be unreliable\n\n`;
  }
  
  // Tier-specific guidance
  if (tierInfo.tier === 0) {
    section += `**Auto-merge eligible** - Checks sufficient\n`;
  } else if (tierInfo.tier === 1) {
    section += `**Standard review** - One approval needed\n`;
  } else {
    section += `**Expert review** - Multiple experts needed\n`;
  }
  
  section += `\n</td></tr></table>\n\n`;
  return section;
}

function buildUnifiedAnalysisComment(allResults) {
  const {
    cognitive = {},
    aiPreReview = {},
    intentClassification = {},
    qualityGate = {},
    impactPrediction = {}
  } = allResults;
  
  // Calculate confidence components - only use real data, no fallbacks
  const confidenceComponents = {
    changeClassification: intentClassification.confidence ? Math.round(intentClassification.confidence * 100) : null,
    riskAssessment: getRiskAssessmentScore(aiPreReview),
    impactAnalysis: impactPrediction.overall_risk_score ? Math.round((1 - impactPrediction.overall_risk_score) * 100) : null
  };
  
  const overallConfidence = calculateOverallConfidence(confidenceComponents);
  const confidenceLevel = getConfidenceLevel(overallConfidence);
  const tierInfo = getTierInfo(cognitive);
  
  // Only build comment if we have some real data
  const hasRealData = tierInfo || 
                     intentClassification.primary_intent || 
                     aiPreReview.risk_level || 
                     (qualityGate.score !== undefined) || 
                     (impactPrediction.impacts && impactPrediction.impacts.length > 0);
  
  if (!hasRealData) {
    return `## AI Analysis Summary\n\n**⏳ Analysis in Progress**\n\nAI analysis is still running. Results will appear when analysis completes.\n\n---\n*Updated: ${new Date().toISOString().split('T')[0]}*\n`;
  }
  
  // Build comment sections - only include sections with real data
  let comment = buildHeaderSection(confidenceLevel, overallConfidence, tierInfo);
  comment += buildConfidenceBreakdown(confidenceComponents);
  comment += buildChangeClassificationSection(intentClassification);
  comment += buildRiskAssessmentSection(aiPreReview);
  comment += buildQualityGateSection(qualityGate);
  comment += buildImpactAnalysisSection(impactPrediction);
  comment += buildRecommendedActionsSection(overallConfidence, tierInfo);
  
  // Only add footer if we have real data
  if (tierInfo) {
    comment += `\n---\n`;
    comment += `*Updated: ${new Date().toISOString().split('T')[0]} • Complexity: ${tierInfo.score}/100 • Confidence: ${overallConfidence}%*\n`;
  }
  
  return comment;
}

async function main({ github, context } = {}) {
  // Load all analysis results
  const allResults = {
    cognitive: loadResults('.code-analysis/outputs/cognitive-analysis-results.json'),
    aiPreReview: loadResults('.code-analysis/outputs/ai-pre-review-results.json'),
    intentClassification: loadResults('.code-analysis/outputs/intent-classification-results.json'),
    qualityGate: loadResults('.code-analysis/outputs/quality-gate-results.json'),
    impactPrediction: loadResults('.code-analysis/outputs/impact-prediction-results.json')
  };
  
  // Debug: Log what data we actually loaded
  console.log('Loaded analysis results:', {
    cognitive: !!allResults.cognitive?.total_score,
    aiPreReview: !!allResults.aiPreReview?.risk_level,
    intentClassification: !!allResults.intentClassification?.primary_intent,
    qualityGate: allResults.qualityGate?.score !== undefined,
    impactPrediction: !!allResults.impactPrediction?.impacts?.length
  });
  
  const comment = buildUnifiedAnalysisComment(allResults);
  
  // Handle both GitHub Actions script and direct CLI usage
  if (github && context) {
    // GitHub Actions script format
    const { createOrUpdateComment } = require('./pr-comment-utils');
    const prNumber = context.payload?.pull_request?.number;
    
    if (!prNumber) {
      console.error('No PR number found in context');
      return;
    }
    
    await createOrUpdateComment(
      github,
      context,
      prNumber,
      comment,
      'AI Analysis Summary',
      `unified-analysis-${context.payload?.pull_request?.head?.sha || 'unknown'}`
    );
  } else {
    // Direct CLI usage
    const { github: ghActions, context: ghContext } = require('@actions/github');
    const { createOrUpdateComment } = require('./pr-comment-utils');
    const prNumber = ghContext.payload?.pull_request?.number || 
                     process.env.PR_NUMBER || 
                     process.argv[2];
    
    if (!prNumber) {
      console.error('No PR number provided');
      process.exit(1);
    }
    
    await createOrUpdateComment(
      ghActions,
      ghContext,
      prNumber,
      comment,
      'AI Analysis Summary',
      `unified-analysis-${ghContext.payload?.pull_request?.head?.sha || 'unknown'}`
    );
  }
  
  console.log('Unified analysis comment created/updated successfully');
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = main;
module.exports.buildUnifiedAnalysisComment = buildUnifiedAnalysisComment;
module.exports.getConfidenceLevel = getConfidenceLevel;
module.exports.calculateOverallConfidence = calculateOverallConfidence;
