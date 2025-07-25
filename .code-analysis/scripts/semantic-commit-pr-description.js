const { getPRNumber, loadResults, createOrUpdateComment } = require('./pr-comment-utils');

/**
 * Formats the semantic commit analysis into a PR description section
 */
function buildSemanticCommitSection(results) {
  if (!results.semantic_analysis) {
    return null;
  }

  const analysis = results.semantic_analysis;
  let section = `## Change Story\n\n`;
  
  // What & Why (brief and reviewer-friendly)
  section += `**What:** ${analysis.what}\n\n`;
  section += `**Why:** ${analysis.why}\n\n`;
  
  // Commit flow summary (single version)
  if (analysis.intents && analysis.intents.length > 0) {
    section += `**Development Flow:** `;
    const intentLabels = {
      'setup': 'Setup',
      'feature': 'Feature', 
      'fix': 'Fix',
      'refactor': 'Refactor',
      'test': 'Test',
      'docs': 'Docs',
      'style': 'Style',
      'config': 'Config'
    };
    
    const flowParts = analysis.intents.map(intent => 
      intentLabels[intent] || intent.charAt(0).toUpperCase() + intent.slice(1)
    );
    
    section += flowParts.join(' → ') + '\n\n';
  }

  // Impact summary with Mermaid heatmap
  if (analysis.impact_areas && Object.keys(analysis.impact_areas).length > 0) {
    const topAreas = Object.entries(analysis.impact_areas)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3);
    
    // Generate Mermaid heatmap
    const heatmapChart = generateImpactHeatmap(analysis.impact_areas);
    if (heatmapChart) {
      section += heatmapChart;
    }
    
    // Impact summary text
    const impactSummary = topAreas
      .map(([area, count]) => `${area}: ${count}`)
      .join(' | ');
    section += `**Impact:** ${impactSummary}\n\n`;
  }
  
  return section;
}

/**
 * Updates the PR description with the semantic commit section
 */
async function updatePRDescription(github, context, prNumber, semanticSection) {
  try {
    // Get current PR description
    const { data: pr } = await github.rest.pulls.get({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber
    });
    
    let body = pr.body || '';
    
    // Remove existing Change Story section if present
    body = body.replace(/## Change Story[\s\S]*?(?=##|$)/g, '').trim();
    
    // Add semantic section at the beginning
    let newBody = semanticSection;
    if (body) {
      newBody += '\n\n' + body;
    }
    
    // Update PR description
    await github.rest.pulls.update({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
      body: newBody
    });
    
    console.log('Successfully updated PR description with semantic commit story');
    
  } catch (error) {
    console.error('Error updating PR description:', error);
    // Fall back to posting as a comment if description update fails
    await createOrUpdateComment(
      github,
      context,
      prNumber,
      semanticSection,
      'Change Story',
      `semantic-commit-pr-${prNumber}`
    );
  }
}

module.exports = async ({ github, context }) => {
  const prNumber = getPRNumber(context);
  
  if (!prNumber) {
    console.log('No PR number found, skipping semantic commit analysis');
    return;
  }
  
  const results = loadResults('semantic-commit-analysis.json', {
    semantic_analysis: {
      what: 'Changes implemented',
      why: 'Improvements needed',
      commit_count: 0,
      intents: [],
      impact_areas: {},
      visual_summary: ''
    }
  });
  
  const semanticSection = buildSemanticCommitSection(results);
  
  if (!semanticSection) {
    console.log('No semantic analysis results, skipping PR description update');
    return;
  }
  
  await updatePRDescription(github, context, prNumber, semanticSection);
  
  console.log('Semantic commit story processing completed');
};

/**
 * Generate a Mermaid heatmap visualization for impact areas
 */
function generateImpactHeatmap(impactAreas) {
  const entries = Object.entries(impactAreas).sort(([,a], [,b]) => b - a);
  
  if (entries.length === 0) {
    return '';
  }
  
  // Generate a visual heatmap using Mermaid mindmap with color coding
  let chart = '**Impact Heatmap:**\n\n';
  chart += '```mermaid\nmindmap\n';
  chart += '  root((Changes))\n';
  
  const maxImpact = Math.max(...Object.values(impactAreas));
  
  entries.slice(0, 6).forEach(([area, count]) => {
    const intensity = count / maxImpact;
    let emoji = '🟢'; // Low impact
    if (intensity >= 0.8) emoji = '🔴'; // High impact
    else if (intensity >= 0.6) emoji = '🟠'; // Medium-high impact  
    else if (intensity >= 0.4) emoji = '🟡'; // Medium impact
    
    chart += `    ${emoji} ${area}\n`;
    chart += `      (${count} changes)\n`;
  });
  
  chart += '```\n\n';
  
  return chart;
}

/**
 * Generate a Mermaid bar chart for impact visualization
 */
function generateMermaidBarChart(impactAreas) {
  const entries = Object.entries(impactAreas).sort(([,a], [,b]) => b - a);
  
  if (entries.length === 0) {
    return '';
  }
  
  let chart = '**Impact Distribution:**\n\n';
  chart += '```mermaid\nxychart-beta\n';
  chart += '    title "Change Impact by Area"\n';
  chart += '    x-axis [';
  
  // Add categories (limit to top 5 for readability)
  const topEntries = entries.slice(0, 5);
  chart += topEntries.map(([area]) => `"${area}"`).join(', ');
  chart += ']\n';
  
  chart += '    y-axis "Impact Count" 0 --> ';
  chart += Math.max(...topEntries.map(([, count]) => count));
  chart += '\n';
  
  chart += '    bar [';
  chart += topEntries.map(([, count]) => count).join(', ');
  chart += ']\n';
  
  chart += '```\n\n';
  
  return chart;
}
