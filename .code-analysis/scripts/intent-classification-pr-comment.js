const { getPRNumber, loadResults, createOrUpdateComment } = require('./pr-comment-utils');

module.exports = async ({ github, context }) => {
  const prNumber = getPRNumber(context);
  
  if (!prNumber) {
    console.log('No PR number found, skipping intent classification comment');
    return;
  }

  const results = loadResults('.code-analysis/outputs/intent-classification-results.json', null);

  if (!results) {
    console.log('Intent classification results not found - analysis may have failed');
    return;
  }

  const comment = buildComment(results);
  
  await createOrUpdateComment(
    github, 
    context, 
    prNumber, 
    comment, 
    'Change Intent',
    `intent-classification-pr-${prNumber}`
  );
  
  console.log('Intent classification comment posted/updated successfully');
};

function buildComment(results) {
  const confidenceLevel = getConfidenceLevel(results.confidence);
  const intentLabel = getIntentLabel(results.primary_intent);
  
  // Build secondary intents string
  let secondaryIntents = '';
  if (results.secondary_intents && results.secondary_intents.length > 0) {
    const significant = results.secondary_intents
      .filter(([intent, conf]) => conf > 0.5)
      .slice(0, 2)
      .map(([intent, conf]) => `${getIntentLabel(intent)} (${Math.round(conf * 100)}%)`)
      .join(' + ');
    secondaryIntents = significant ? ` + ${significant}` : '';
  }
  
  let comment = `## Change Intent | ${intentLabel}${secondaryIntents} | Confidence: ${confidenceLevel}\n\n`;
  
  // Quick summary
  const intentDescription = getIntentDescription(results.primary_intent, results.confidence);
  comment += `**${intentDescription}**\n\n`;
  
  // Core metrics - file changes and areas (this is the primary location for this data)
  const fileChanges = results.file_changes_summary;
  comment += `**Primary:** ${results.primary_intent.toUpperCase()} (${Math.round(results.confidence * 100)}% confidence)\n`;
  comment += `**Scope:** ${fileChanges.total_files} files, +${fileChanges.total_lines_added}/-${fileChanges.total_lines_removed} lines\n`;
  
  if (results.affected_areas && results.affected_areas.length > 0 && !results.affected_areas.includes('unknown')) {
    comment += `**Areas:** ${results.affected_areas.map(area => area.toLowerCase()).join(', ')}\n`;
  }
  
  comment += `\n`;
  
  // Action items for low confidence
  if (results.confidence < 0.6) {
    comment += `**Action Needed:**\n`;
    comment += `- Add more descriptive PR title/description\n`;
    comment += `- Clarify the main purpose of this change\n\n`;
  }
  
  // Footer
  comment += `---\n*Change intent analysis • ${confidenceLevel} confidence*`;

  return comment;
}

function getIntentLabel(intent) {
  const labels = {
    'feature': 'FEATURE',
    'bug': 'BUG', 
    'bugfix': 'BUG',
    'refactor': 'REFACTOR',
    'documentation': 'DOCS',
    'ui': 'UI',
    'api': 'API',
    'infrastructure': 'INFRA',
    'infra': 'INFRA',
    'test': 'TEST',
    'testing': 'TEST',
    'security': 'SECURITY',
    'performance': 'PERFORMANCE',
    'maintenance': 'MAINTENANCE',
    'style': 'STYLE',
    'config': 'CONFIG',
    'build': 'BUILD'
  };
  
  return labels[intent.toLowerCase()] || intent.toUpperCase();
}

function getConfidenceLevel(confidence) {
  if (confidence > 0.8) return 'HIGH';
  if (confidence > 0.6) return 'MEDIUM';
  if (confidence > 0.4) return 'LOW';
  return 'VERY LOW';
}

function getIntentDescription(intent, confidence) {
  const intentType = getIntentLabel(intent);
  
  let confidenceDesc;
  if (confidence > 0.8) {
    confidenceDesc = 'clearly identified';
  } else if (confidence > 0.6) {
    confidenceDesc = 'identified with good confidence';
  } else if (confidence > 0.4) {
    confidenceDesc = 'tentatively identified';
  } else {
    confidenceDesc = 'uncertain identification';
  }
  
  const descriptions = {
    'FEATURE': `New functionality ${confidenceDesc}`,
    'BUG': `Bug fix ${confidenceDesc}`,
    'REFACTOR': `Code restructuring ${confidenceDesc}`,
    'DOCS': `Documentation update ${confidenceDesc}`,
    'UI': `User interface change ${confidenceDesc}`,
    'API': `Backend/API modification ${confidenceDesc}`,
    'INFRA': `Infrastructure change ${confidenceDesc}`,
    'TEST': `Testing improvement ${confidenceDesc}`,
    'SECURITY': `Security enhancement ${confidenceDesc}`,
    'PERFORMANCE': `Performance optimization ${confidenceDesc}`,
    'MAINTENANCE': `Maintenance work ${confidenceDesc}`,
    'STYLE': `Code style/formatting ${confidenceDesc}`,
    'CONFIG': `Configuration change ${confidenceDesc}`,
    'BUILD': `Build system change ${confidenceDesc}`
  };
  
  return descriptions[intentType] || `${intentType} change ${confidenceDesc}`;
};
