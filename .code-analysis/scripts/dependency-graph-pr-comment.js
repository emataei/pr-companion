const { getPRNumber, loadResults, createOrUpdateComment } = require('./pr-comment-utils');
const { generateDependencyDiff, getChangedFiles } = require('./dependency-diff');
const fs = require('fs');
const path = require('path');

module.exports = async ({ github, context }) => {
  const prNumber = getPRNumber(context);
  
  if (!prNumber) {
    console.log('No PR number found, skipping dependency graph comment');
    return;
  }

  // Generate live dependency diff from changed files
  const changedFiles = getChangedFiles();
  const dependencyDiff = await generateDependencyDiff(changedFiles);

  // Load existing results for backward compatibility
  const results = loadResults('dependency-graph-results.json', { 
    changes: [],
    total_files_analyzed: 0,
    graph_generated: false,
    circular_dependencies: [],
    high_impact_changes: [],
    graph_files: {
      png: null,
      html: null,
      ascii: null
    }
  });

  // Enhance results with live dependency diff
  if (dependencyDiff) {
    results.dependency_diff = dependencyDiff;
    results.total_files_analyzed = dependencyDiff.stats.totalFiles;
    results.circular_dependencies = dependencyDiff.stats.circularDependencies || [];
    results.graph_generated = true;
  }

  const comment = buildComment(results);
  
  await createOrUpdateComment(
    github, 
    context, 
    prNumber, 
    comment, 
    'Dependency Analysis',
    `dependency-graph-pr-${prNumber}`
  );
  
  console.log('Dependency graph comment posted/updated successfully');
};

function buildComment(results) {
  const complexityLevel = getDependencyComplexity(results);
  const riskLevel = getDependencyRisk(results);
  
  let comment = `## Dependency Analysis\n\n`;
  
  // Header with complexity and risk levels
  comment += `**Complexity:** ${complexityLevel} | **Risk:** ${riskLevel}\n`;
  comment += `**Scope:** ${results.total_files_analyzed} files, ${results.changes.length} changes\n\n`;

  // Visual graph section
  const graphSection = buildGraphSection(results);
  if (graphSection) {
    comment += graphSection;
  }

  // Critical issues first
  if (results.circular_dependencies && results.circular_dependencies.length > 0) {
    comment += `### CIRCULAR DEPENDENCIES DETECTED\n`;
    comment += `**Count:** ${results.circular_dependencies.length}\n\n`;
    comment += `\`\`\`\n`;
    results.circular_dependencies.slice(0, 2).forEach(cycle => {
      comment += `${cycle.join(' → ')}\n`;
    });
    if (results.circular_dependencies.length > 2) {
      comment += `... and ${results.circular_dependencies.length - 2} more\n`;
    }
    comment += `\`\`\`\n\n`;
  }

  // High-impact changes
  if (results.high_impact_changes && results.high_impact_changes.length > 0) {
    comment += `### High Impact Changes\n`;
    comment += `| File | Type | Impact | Dependencies |\n`;
    comment += `|------|------|--------|---------------|\n`;
    results.high_impact_changes.slice(0, 3).forEach(change => {
      const changeType = getChangeTypeLabel(change.change_type);
      const impactLevel = getImpactLevel(change.impact_score);
      comment += `| \`${change.file_name}\` | ${changeType} | ${impactLevel} | ${change.impact_score} |\n`;
    });
    if (results.high_impact_changes.length > 3) {
      comment += `| ... | ... | ... | ${results.high_impact_changes.length - 3} more |\n`;
    }
    comment += `\n`;
  }

  // Change breakdown by category
  const changesByType = groupChangesByType(results.changes);
  if (Object.keys(changesByType).length > 0) {
    comment += `**Change Categories:**\n`;
    Object.entries(changesByType).forEach(([type, changes]) => {
      comment += `- ${getChangeTypeLabel(type)}: ${changes.length}\n`;
    });
    comment += `\n`;
  }

  // Recommendations
  const recommendations = getRecommendations(results);
  if (recommendations.length > 0) {
    comment += `**Recommendations:**\n`;
    recommendations.forEach(rec => {
      comment += `- ${rec}\n`;
    });
    comment += `\n`;
  }

  // Footer
  comment += `---\n*Dependency analysis • Auto-updated*`;

  return comment;
}

function getDependencyComplexity(results) {
  const changeCount = results.changes.length;
  const highImpactCount = results.high_impact_changes?.length || 0;
  
  if (changeCount > 15 || highImpactCount > 5) return 'VERY HIGH';
  if (changeCount > 10 || highImpactCount > 3) return 'HIGH';
  if (changeCount > 5 || highImpactCount > 1) return 'MEDIUM';
  if (changeCount > 2) return 'LOW';
  return 'VERY LOW';
}

function getDependencyRisk(results) {
  const circularDeps = results.circular_dependencies?.length || 0;
  const highImpactCount = results.high_impact_changes?.length || 0;
  
  if (circularDeps > 0) return 'CRITICAL';
  if (highImpactCount > 3) return 'HIGH';
  if (highImpactCount > 1) return 'MEDIUM';
  if (highImpactCount > 0) return 'LOW';
  return 'NONE';
}

function buildGraphSection(results) {
  let section = '';
  
  // Show live dependency diff first if available
  if (results.dependency_diff?.diagram) {
    section += buildLiveDependencySection(results.dependency_diff);
    return section;
  }
  
  // Fallback to existing graph files approach
  return buildStaticGraphSection(results.graph_files);
}

function buildLiveDependencySection(dependencyDiff) {
  let section = `### Dependency Graph (PR Changes)\n\n`;
  section += dependencyDiff.diagram;
  section += `\n`;
  
  // Add stats
  const stats = dependencyDiff.stats;
  section += `**Graph Stats:** ${stats.totalFiles} files analyzed, `;
  section += `${stats.totalDependencies} dependencies mapped`;
  
  if (stats.circularDependencies.length > 0) {
    section += `, 🔴 ${stats.circularDependencies.length} circular dependencies detected`;
  }
  
  if (stats.maxDepth > 0) {
    section += `, max depth: ${stats.maxDepth}`;
  }
  
  section += `\n\n`;
  section += `**Legend:** 🟢 Changed files, 🔴 Circular dependencies\n\n`;
  
  return section;
}

function buildStaticGraphSection(graphFiles) {
  if (!graphFiles) return '';
  
  let section = `### Dependency Graph\n`;
  const hasGraphs = graphFiles.png || graphFiles.html || graphFiles.ascii;
  
  if (!hasGraphs) return '';
  
  section += `Visual dependency graphs have been generated and are available in the workflow artifacts.\n\n`;
  
  if (graphFiles.png) {
    section += `- **Static Graph**: \`${graphFiles.png}\`\n`;
  }
  if (graphFiles.html) {
    section += `- **Interactive Graph**: \`${graphFiles.html}\`\n`;
  }
  if (graphFiles.ascii) {
    section += `- **Text Version**: \`${graphFiles.ascii}\`\n`;
  }
  
  section += `\n**Download artifacts** from the GitHub Actions workflow to view the graphs.\n\n`;
  return section;
}

function getImpactLevel(score) {
  if (typeof score === 'number') {
    if (score >= 8) return 'CRITICAL';
    if (score >= 6) return 'HIGH';
    if (score >= 4) return 'MEDIUM';
    if (score >= 2) return 'LOW';
    return 'MINIMAL';
  }
  return 'UNKNOWN';
}

function getChangeTypeLabel(changeType) {
  const labels = {
    'added': 'ADDED',
    'modified': 'MODIFIED', 
    'deleted': 'DELETED',
    'renamed': 'RENAMED',
    'moved': 'MOVED'
  };
  return labels[changeType] || 'CHANGED';
}

function getRecommendations(results) {
  const recommendations = [];
  
  if (results.circular_dependencies?.length > 0) {
    recommendations.push('Resolve circular dependencies before merging');
  }
  
  if (results.high_impact_changes?.length > 3) {
    recommendations.push('Consider splitting into smaller PRs for easier review');
  }
  
  if (results.changes.length > 20) {
    recommendations.push('Large change set - ensure comprehensive testing');
  }
  
  const deletedFiles = results.changes.filter(c => c.change_type === 'deleted').length;
  if (deletedFiles > 5) {
    recommendations.push('Verify all deleted file dependencies are properly handled');
  }
  
  return recommendations;
}

function getChangeType(changeType) {
  return getChangeTypeLabel(changeType);
}

function groupChangesByType(changes) {
  const grouped = {};
  changes.forEach(change => {
    if (!grouped[change.change_type]) {
      grouped[change.change_type] = [];
    }
    grouped[change.change_type].push(change);
  });
  return grouped;
}
