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
  
  const results = loadResults('.code-analysis/outputs/semantic-commit-analysis.json', {
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
