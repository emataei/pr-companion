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
  // Weighted average of all confidence components
  const weights = {
    changeClassification: 0.3,
    riskAssessment: 0.4,
    impactAnalysis: 0.3
  };
  
  let totalScore = 0;
  let totalWeight = 0;
  
  for (const [component, weight] of Object.entries(weights)) {
    if (components[component] !== undefined) {
      totalScore += components[component] * weight;
      totalWeight += weight;
    }
  }
  
  return totalWeight > 0 ? Math.round(totalScore / totalWeight) : 0;
}

function getTierInfo(cognitiveResults) {
  if (!cognitiveResults) return { tier: 1, score: 50, description: 'Standard Review' };
  
  const score = cognitiveResults.total_score || 50;
  const tier = cognitiveResults.tier || 1;
  
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
  const confidence = aiPreReview.confidence_metrics?.analysis_confidence;
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
  let section = `## Cognitive Review Analysis\n\n`;
  section += `**Overall Confidence:** ${confidenceLevel.level} (${overallConfidence}%) ${confidenceLevel.indicator}\n`;
  section += `*${confidenceLevel.description}*\n\n`;
  section += `**Review Tier:** ${tierInfo.description} | **Cognitive Score:** ${tierInfo.score}/100\n\n`;
  return section;
}

function buildConfidenceBreakdown(confidenceComponents) {
  let section = `### Analysis Confidence Breakdown\n\n`;
  section += `| Component | Score | Level | Status |\n`;
  section += `|-----------|-------|-------|--------|\n`;
  
  for (const [component, score] of Object.entries(confidenceComponents)) {
    const level = getConfidenceLevel(score);
    const componentName = component.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
    const status = getStatusIndicator(score);
    section += `| ${componentName} | ${score}% | ${level.level} | ${status} |\n`;
  }
  section += `\n`;
  return section;
}

function buildChangeClassificationSection(intentClassification) {
  if (!intentClassification.primary_intent) return '';
  
  let section = '';
  const intent = intentClassification.primary_intent.toUpperCase();
  const confidence = Math.round(intentClassification.confidence * 100);
  section += `**Change Type:** ${intent} (${confidence}% confidence)\n`;
  
  if (intentClassification.secondary_intents?.length > 0) {
    const secondaryIntents = intentClassification.secondary_intents
      .filter(([intent, conf]) => conf > 0.3)
      .slice(0, 2)
      .map(([intent, conf]) => `${intent.toUpperCase()} (${Math.round(conf * 100)}%)`)
      .join(', ');
    if (secondaryIntents) {
      section += `**Secondary Types:** ${secondaryIntents}\n`;
    }
  }
  section += `\n`;
  return section;
}

function buildRiskAssessmentSection(aiPreReview) {
  if (!aiPreReview.risk_level) return '';
  
  let section = '';
  const riskLevel = aiPreReview.risk_level;
  const riskIndicator = getRiskIndicator(riskLevel);
  section += `**Risk Level:** ${riskLevel} ${riskIndicator}\n`;
  
  if (aiPreReview.risk_factors?.length > 0) {
    section += `**Risk Factors:**\n`;
    aiPreReview.risk_factors.slice(0, 3).forEach(factor => {
      section += `- ${factor}\n`;
    });
  }
  section += `\n`;
  return section;
}

function buildQualityGateSection(qualityGate) {
  if (qualityGate.score === undefined) return '';
  
  let section = '';
  const qualityStatus = qualityGate.passed ? '✓ PASS' : '❌ FAIL';
  const qualityScore = qualityGate.score || 0;
  section += `**Quality Gate:** ${qualityStatus} (${qualityScore}/100)\n`;
  
  if (qualityGate.blocking_issues?.length > 0) {
    section += `**Blocking Issues:**\n`;
    qualityGate.blocking_issues.slice(0, 3).forEach(issue => {
      section += `- ${issue.type}: ${issue.message}\n`;
    });
  }
  section += `\n`;
  return section;
}

function buildImpactAnalysisSection(impactPrediction) {
  if (!impactPrediction.impacts?.length) return '';
  
  let section = `**Impact Analysis:**\n`;
  const criticalImpacts = impactPrediction.impacts.filter(i => i.severity === 'critical');
  const highImpacts = impactPrediction.impacts.filter(i => i.severity === 'high');
  
  if (criticalImpacts.length > 0) {
    section += `**Critical Impacts:** ${criticalImpacts.length}\n`;
    criticalImpacts.slice(0, 2).forEach(impact => {
      section += `- ${impact.description}\n`;
    });
  }
  
  if (highImpacts.length > 0) {
    section += `**High Impacts:** ${highImpacts.length}\n`;
    highImpacts.slice(0, 2).forEach(impact => {
      section += `- ${impact.description}\n`;
    });
  }
  section += `\n`;
  return section;
}

function buildRecommendedActionsSection(overallConfidence, tierInfo) {
  let section = `### Recommended Review Actions\n\n`;
  
  if (overallConfidence >= 80) {
    section += `✅ **High Confidence Analysis** - Focus review on AI-highlighted areas\n`;
    section += `✅ Use AI insights to guide review priorities\n`;
  } else if (overallConfidence >= 60) {
    section += `⚠️ **Medium Confidence Analysis** - Use AI as starting point, verify conclusions\n`;
    section += `⚠️ Cross-reference AI findings with manual analysis\n`;
  } else if (overallConfidence >= 40) {
    section += `🔍 **Low Confidence Analysis** - AI classification for context only\n`;
    section += `🔍 Conduct thorough manual review beyond AI suggestions\n`;
  } else {
    section += `🚨 **Very Low Confidence** - Rely primarily on manual review\n`;
    section += `🚨 AI analysis may not be reliable for this change\n`;
  }
  
  // Tier-specific guidance
  if (tierInfo.tier === 0) {
    section += `🚀 **Auto-merge eligible** - Automated checks sufficient\n`;
  } else if (tierInfo.tier === 1) {
    section += `👤 **Standard review required** - One team member approval needed\n`;
  } else {
    section += `👥 **Expert review required** - Multiple domain experts needed\n`;
  }
  
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
  
  // Calculate confidence components
  const confidenceComponents = {
    changeClassification: intentClassification.confidence ? Math.round(intentClassification.confidence * 100) : 30,
    riskAssessment: getRiskAssessmentScore(aiPreReview),
    impactAnalysis: impactPrediction.overall_risk_score ? Math.round((1 - impactPrediction.overall_risk_score) * 100) : 40
  };
  
  const overallConfidence = calculateOverallConfidence(confidenceComponents);
  const confidenceLevel = getConfidenceLevel(overallConfidence);
  const tierInfo = getTierInfo(cognitive);
  
  // Build comment sections
  let comment = buildHeaderSection(confidenceLevel, overallConfidence, tierInfo);
  comment += buildConfidenceBreakdown(confidenceComponents);
  comment += buildChangeClassificationSection(intentClassification);
  comment += buildRiskAssessmentSection(aiPreReview);
  comment += buildQualityGateSection(qualityGate);
  comment += buildImpactAnalysisSection(impactPrediction);
  comment += buildRecommendedActionsSection(overallConfidence, tierInfo);
  
  comment += `\n---\n`;
  comment += `*Updated: ${new Date().toISOString().split('T')[0]} | Cognitive Score: ${tierInfo.score}/100 | Overall Confidence: ${overallConfidence}%*\n`;
  
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
      'Cognitive Review Analysis',
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
      'Cognitive Review Analysis',
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
