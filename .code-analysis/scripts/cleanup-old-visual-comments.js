const { getPRNumber } = require('./pr-comment-utils');

async function cleanupOldVisualComments({ github, context }) {
  const prNumber = getPRNumber(context);
  if (!prNumber) {
    console.log('No PR number found, skipping cleanup');
    return;
  }

  try {
    // Get all comments on the PR
    const { data: comments } = await github.rest.issues.listComments({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
    });

    console.log(`Found ${comments.length} existing comments to check`);

    // Find old combined visual comments to remove
    const oldCommentPatterns = [
      'Enhanced PR Visuals',
      'Real-time analytics with embedded images',
      'PR Impact Heatmap.*Development Flow.*PR Summary', // Old combined format
    ];

    for (const comment of comments) {
      const isOldVisualComment = oldCommentPatterns.some(pattern => 
        new RegExp(pattern, 'i').test(comment.body)
      );

      // Only delete if it's clearly an old combined visual comment AND it's large
      if (isOldVisualComment && comment.body.length > 30000) {
        console.log(`Deleting old combined visual comment (${comment.body.length} chars)`);
        await github.rest.issues.deleteComment({
          owner: context.repo.owner,
          repo: context.repo.repo,
          comment_id: comment.id,
        });
        
        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }

    console.log('✅ Cleanup completed');
  } catch (error) {
    console.error('Failed to cleanup old comments:', error.message);
  }
}

module.exports = cleanupOldVisualComments;
