const fs = require('fs');
const { getPRNumber, loadResults, setLabels } = require('./pr-comment-utils');

/**
 * Automatically set reviewer-centric PR labels based on analysis results
 * Focus: tier, complexity, score, size, merge readiness (not code categories)
 */
async function autoLabelPR({ github, context }) {
  const prNumber = getPRNumber(context);
  if (!prNumber) {
    console.log('No PR number found, skipping auto-labeling');
    return;
  }

  console.log(`Setting reviewer-centric labels for PR #${prNumber}`);
  
  const labels = new Set();
  
  try {
    // Get PR statistics for analysis
    const prStats = await getPRStats(github, context, prNumber);
    const changedFiles = await getChangedFiles(github, context, prNumber);
    
    // Apply reviewer-centric labeling
    addTierLabel(labels, prStats, changedFiles);
    addComplexityLabel(labels, prStats, changedFiles);
    addQualityScoreLabel(labels);
    addSizeLabel(labels, prStats);
    addMergeReadinessLabel(labels, prStats, changedFiles);

    // Apply labels
    const finalLabels = Array.from(labels).filter(label => label && label.trim());
    
    if (finalLabels.length > 0) {
      console.log(`Setting reviewer-centric labels: ${finalLabels.join(', ')}`);
      await setLabels(github, context, prNumber, finalLabels);
      console.log('Labels set successfully');
    } else {
      console.log('No labels to set');
    }

    return finalLabels;
  } catch (error) {
    console.error('Error in auto-labeling:', error);
    return [];
  }
}

/**
 * Add tier label (who should review)
 */
function addTierLabel(labels, prStats, changedFiles) {
  let tierScore = 0;
  
  // Size factor (0-2 points)
  const totalChanges = prStats.additions + prStats.deletions;
  if (totalChanges > 1000) tierScore += 2;
  else if (totalChanges > 500) tierScore += 1;
  
  // Risk factor based on file types (0-2 points)
  const riskScore = calculateRiskScore(changedFiles);
  tierScore += Math.min(riskScore, 2);
  
  // Critical files factor (0-2 points)
  const hasCriticalFiles = changedFiles.some(file => 
    file.includes('package.json') || 
    file.includes('dockerfile') ||
    file.includes('.github/workflows') ||
    file.includes('tsconfig.json') ||
    file.includes('next.config')
  );
  if (hasCriticalFiles) tierScore += 1;
  
  // Architecture files
  const hasArchitectureFiles = changedFiles.some(file =>
    file.includes('/api/') ||
    file.includes('/lib/') ||
    file.includes('/utils/') ||
    file.includes('types.ts') ||
    file.includes('schema')
  );
  if (hasArchitectureFiles) tierScore += 1;
  
  // Determine tier
  if (tierScore === 0 && totalChanges < 50) {
    labels.add('tier:0');
  } else if (tierScore <= 1) {
    labels.add('tier:1');
  } else if (tierScore <= 2) {
    labels.add('tier:2');
  } else if (tierScore <= 3) {
    labels.add('tier:3');
  } else {
    labels.add('tier:4');
  }
}

/**
 * Add complexity label (mental effort required)
 */
function addComplexityLabel(labels, prStats, changedFiles) {
  let complexityScore = 0;
  
  const totalChanges = prStats.additions + prStats.deletions;
  
  // Size complexity
  if (totalChanges > 1000) complexityScore += 3;
  else if (totalChanges > 500) complexityScore += 2;
  else if (totalChanges > 200) complexityScore += 1;
  
  // File type complexity
  const hasComplexFiles = changedFiles.some(file => {
    const ext = file.split('.').pop()?.toLowerCase();
    return ['ts', 'tsx', 'js', 'jsx'].includes(ext) && 
           !file.includes('test') && 
           !file.includes('.spec.');
  });
  if (hasComplexFiles) complexityScore += 1;
  
  // Multiple file types (integration complexity)
  const fileTypes = new Set();
  changedFiles.forEach(file => {
    const ext = file.split('.').pop()?.toLowerCase();
    if (ext) fileTypes.add(ext);
  });
  if (fileTypes.size > 3) complexityScore += 1;
  
  // Documentation-only changes are trivial
  const onlyDocs = changedFiles.every(file => 
    file.endsWith('.md') || 
    file.includes('docs/') ||
    file.includes('README')
  );
  if (onlyDocs) complexityScore = 0;
  
  // Assign complexity label
  if (complexityScore === 0) {
    labels.add('complexity:trivial');
  } else if (complexityScore === 1) {
    labels.add('complexity:low');
  } else if (complexityScore === 2) {
    labels.add('complexity:medium');
  } else if (complexityScore === 3) {
    labels.add('complexity:high');
  } else {
    labels.add('complexity:critical');
  }
}

/**
 * Add quality score label (readiness for review)
 */
function addQualityScoreLabel(labels) {
  try {
    // Check for quality gate results
    const qualityResults = findQualityResults();
    
    if (qualityResults && typeof qualityResults.overall_score === 'number') {
      const score = qualityResults.overall_score;
      
      if (score >= 8.0) {
        labels.add('score:excellent');
      } else if (score >= 6.0) {
        labels.add('score:good');
      } else if (score >= 4.0) {
        labels.add('score:needs-work');
      } else {
        labels.add('score:incomplete');
      }
    } else {
      // Default to needs-review if no quality data
      labels.add('score:good');
    }
  } catch (error) {
    console.log('Quality assessment not available, defaulting to good');
    labels.add('score:good');
  }
}

/**
 * Add size label (review time planning)
 */
function addSizeLabel(labels, prStats) {
  const totalChanges = prStats.additions + prStats.deletions;
  
  if (totalChanges < 50) {
    labels.add('size:XS');
  } else if (totalChanges < 200) {
    labels.add('size:S');
  } else if (totalChanges < 500) {
    labels.add('size:M');
  } else if (totalChanges < 1000) {
    labels.add('size:L');
  } else {
    labels.add('size:XL');
  }
}

/**
 * Add merge readiness label (review routing)
 */
function addMergeReadinessLabel(labels, prStats, changedFiles) {
  const totalChanges = prStats.additions + prStats.deletions;
  
  // Auto-merge candidates
  const isDocumentationOnly = changedFiles.every(file => 
    file.endsWith('.md') || 
    file.includes('docs/') ||
    file.includes('README')
  );
  
  const isSmallConfigChange = totalChanges < 50 && changedFiles.every(file =>
    file.endsWith('.json') ||
    file.endsWith('.yml') ||
    file.endsWith('.yaml') ||
    file.endsWith('.md')
  );
  
  if ((isDocumentationOnly || isSmallConfigChange) && totalChanges < 50) {
    labels.add('auto-merge-candidate');
    return;
  }
  
  // Expert review needed
  const needsExpertReview = changedFiles.some(file =>
    file.includes('security') ||
    file.includes('auth') ||
    file.includes('database') ||
    file.includes('migration') ||
    file.includes('.github/workflows') ||
    file.includes('dockerfile') ||
    totalChanges > 1000
  );
  
  if (needsExpertReview) {
    labels.add('needs-expert-review');
    return;
  }
  
  // Team discussion needed
  const needsTeamDiscussion = 
    totalChanges > 2000 ||
    changedFiles.some(file => 
      file.includes('package.json') && file.includes('"version"') ||
      file.includes('BREAKING') ||
      file.includes('major')
    );
  
  if (needsTeamDiscussion) {
    labels.add('hold-for-discussion');
    return;
  }
  
  // Default to standard review
  labels.add('needs-review');
}

/**
 * Calculate risk score based on file types and patterns
 */
function calculateRiskScore(files) {
  let risk = 0;
  
  files.forEach(file => {
    const lowerFile = file.toLowerCase();
    
    // High risk files
    if (lowerFile.includes('security') || 
        lowerFile.includes('auth') ||
        lowerFile.includes('password') ||
        lowerFile.includes('token')) {
      risk += 0.5;
    }
    
    // Database and data files
    if (lowerFile.includes('database') ||
        lowerFile.includes('migration') ||
        lowerFile.includes('schema')) {
      risk += 0.3;
    }
    
    // Infrastructure files
    if (lowerFile.includes('dockerfile') ||
        lowerFile.includes('docker-compose') ||
        lowerFile.includes('.github/workflows')) {
      risk += 0.3;
    }
    
    // Configuration files
    if (lowerFile.includes('config') ||
        lowerFile.includes('package.json') ||
        lowerFile.includes('tsconfig')) {
      risk += 0.2;
    }
  });
  
  return Math.min(risk, 2); // Cap at 2 points
}

/**
 * Find quality results from multiple possible locations
 */
function findQualityResults() {
  const locations = [
    '.code-analysis/outputs/quality-gate-results.json',
    'quality-gate-results.json',
    '.code-analysis/outputs/sonar-results.json'
  ];
  
  for (const location of locations) {
    try {
      if (fs.existsSync(location)) {
        const content = fs.readFileSync(location, 'utf8');
        const results = JSON.parse(content);
        if (results && typeof results.overall_score === 'number') {
          return results;
        }
      }
    } catch (error) {
      console.log(`Could not load quality results from ${location}: ${error.message}`);
    }
  }
  
  return null;
}

/**
 * Get PR statistics
 */
async function getPRStats(github, context, prNumber) {
  try {
    const { data: pr } = await github.rest.pulls.get({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber
    });
    
    return {
      additions: pr.additions || 0,
      deletions: pr.deletions || 0,
      changedFiles: pr.changed_files || 0
    };
  } catch (error) {
    console.error('Error getting PR stats:', error);
    return { additions: 0, deletions: 0, changedFiles: 0 };
  }
}

/**
 * Get list of changed files
 */
async function getChangedFiles(github, context, prNumber) {
  try {
    const { data: files } = await github.rest.pulls.listFiles({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber
    });
    
    return files.map(file => file.filename);
  } catch (error) {
    console.error('Error getting changed files:', error);
    return [];
  }
}

module.exports = autoLabelPR;
