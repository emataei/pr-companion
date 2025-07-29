const fs = require('fs');

/**
 * Shared utilities for GitHub PR comment management
 */

/**
 * Get PR number from GitHub context
 * @param {object} context - GitHub context object
 * @returns {number|null} PR number or null if not found
 */
function getPRNumber(context) {
  const prNumber = context.issue?.number || 
                   context.payload?.pull_request?.number || 
                   context.payload?.number;
  
  return prNumber;
}

/**
 * Load JSON results from file
 * @param {string} filePath - Path to JSON file
 * @param {object} defaultResults - Default results if file not found
 * @returns {object} Parsed results or default
 */
function loadResults(filePath, defaultResults = {}) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const results = JSON.parse(content);
    console.log(`Successfully loaded results from ${filePath}`);
    return results;
  } catch (error) {
    console.log(`Could not read ${filePath}:`, error.message);
    return defaultResults;
  }
}

/**
 * Create or update a PR comment
 * @param {object} github - GitHub API client
 * @param {object} context - GitHub context
 * @param {number} prNumber - PR number
 * @param {string} commentBody - Comment content
 * @param {string} identifier - Unique string to identify existing comments
 * @param {string} commentId - Optional unique comment ID for GitHub Actions workflow
 * @returns {Promise<void>}
 */
async function createOrUpdateComment(github, context, prNumber, commentBody, identifier, commentId = null) {
  try {
    console.log(`Creating/updating comment with identifier: "${identifier}"`);
    
    // Validate comment size before posting
    const maxSize = 63000; // GitHub limit is 65536, leave buffer for JSON encoding overhead
    if (commentBody.length > maxSize) {
      console.log(`⚠️  Comment too large (${commentBody.length} chars), truncating to ${maxSize} chars`);
      
      // Find a good truncation point
      let truncateAt = maxSize - 300; // Leave room for truncation message
      const lastNewline = commentBody.lastIndexOf('\n', truncateAt);
      if (lastNewline > truncateAt * 0.8) {
        truncateAt = lastNewline;
      }
      
      commentBody = commentBody.substring(0, truncateAt);
      commentBody += '\n\n---\n**⚠️ Content truncated due to GitHub comment size limits.**\n\n';
      commentBody += 'Full content available in [workflow artifacts](https://github.com/';
      commentBody += `${context.repo.owner}/${context.repo.repo}/actions).`;
      console.log(`✅ Comment truncated to ${commentBody.length} characters`);
    }
    
    // Get all comments on the PR
    const { data: comments } = await github.rest.issues.listComments({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
    });

    console.log(`Found ${comments.length} existing comments`);

    // Find existing comment by comment ID first (more reliable), then by identifier
    let existingComment = null;
    if (commentId) {
      existingComment = comments.find(comment => 
        comment.body.includes(`<!-- comment-id: ${commentId} -->`)
      );
      if (existingComment) {
        console.log(`Found existing comment by comment ID: ${commentId}`);
      }
    }
    
    // Fallback to identifier matching if no comment ID match found
    if (!existingComment) {
      existingComment = comments.find(comment => 
        comment.body.includes(identifier) || 
        comment.body.startsWith(`## ${identifier}`) ||
        comment.body.includes(`# ${identifier}`) ||
        // Also check for "Enhanced PR Visuals" in various formats
        (identifier === 'Enhanced PR Visuals' && (
          comment.body.includes('Enhanced PR Visuals') ||
          comment.body.includes('## Enhanced PR Visuals') ||
          comment.body.includes('# Enhanced PR Visuals')
        ))
      );
      if (existingComment) {
        console.log(`Found existing comment by identifier: "${identifier}"`);
      }
    }

    // Add comment ID if provided (for GitHub Actions workflow tracking)
    const finalCommentBody = commentId ? 
      `${commentBody}\n\n<!-- comment-id: ${commentId} -->` : 
      commentBody;

    if (existingComment) {
      console.log(`Updating existing comment (ID: ${existingComment.id})`);
      await github.rest.issues.updateComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        comment_id: existingComment.id,
        body: finalCommentBody
      });
      console.log('Successfully updated existing comment');
    } else {
      console.log('Creating new comment');
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        body: finalCommentBody
      });
      console.log('Successfully created new comment');
    }
  } catch (error) {
    console.error('Error posting/updating comment:', error);
    throw error;
  }
}

/**
 * Set labels on a PR
 * @param {object} github - GitHub API client
 * @param {object} context - GitHub context
 * @param {number} prNumber - PR number
 * @param {string[]} labels - Array of label names
 * @returns {Promise<void>}
 */
async function setLabels(github, context, prNumber, labels) {
  try {
    if (!context.repo || !context.repo.owner || !context.repo.repo) {
      console.log('Missing repository context for setting labels');
      return;
    }
    
    await github.rest.issues.setLabels({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
      labels: labels
    });
  } catch (error) {
    console.error('Error setting labels:', error);
    throw error;
  }
}

/**
 * Smart text truncation with proper word/sentence wrapping
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length (default: 300)
 * @param {string} suffix - Suffix to add when truncated (default: '...')
 * @returns {string} Truncated text
 */
function smartTruncate(text, maxLength = 300, suffix = '...') {
  if (!text || text.length <= maxLength) {
    return text;
  }
  
  // Try to find good breaking points in order of preference:
  // 1. End of a bullet point list item
  // 2. End of paragraph (double newline)
  // 3. End of sentence (period + space or period + newline)
  // 4. End of sentence (just period)
  // 5. Word boundary (space)
  
  const breakPoints = [
    // Look for end of bullet points (bullet + content + newline)
    text.lastIndexOf('\n• ', maxLength),
    text.lastIndexOf('\n- ', maxLength),
    text.lastIndexOf('\n* ', maxLength),
    text.lastIndexOf('\n\n', maxLength),
    text.lastIndexOf('. ', maxLength),
    text.lastIndexOf('.\n', maxLength),
    text.lastIndexOf('.', maxLength),
    text.lastIndexOf(' ', maxLength)
  ];
  
  for (const breakPoint of breakPoints) {
    if (breakPoint > maxLength * 0.6) { // Allow more flexibility for bullet points
      let truncated = text.substring(0, breakPoint);
      
      // If we broke at a bullet point, include the bullet point marker
      if (breakPoint > 0 && /\n[•\-*] /.test(text.substring(breakPoint - 3, breakPoint + 3))) {
        // Find the end of this bullet point
        const nextNewline = text.indexOf('\n', breakPoint + 1);
        if (nextNewline > 0 && nextNewline < maxLength + 100) { // Allow a bit of overflow for complete bullets
          truncated = text.substring(0, nextNewline);
        }
      }
      
      return truncated + (truncated.endsWith('.') ? suffix : '.' + suffix);
    }
  }
  
  // Fallback to hard truncation at word boundary
  const lastSpace = text.lastIndexOf(' ', maxLength);
  const truncateAt = lastSpace > 0 ? lastSpace : maxLength;
  return text.substring(0, truncateAt) + suffix;
}

module.exports = {
  getPRNumber,
  loadResults,
  createOrUpdateComment,
  setLabels,
  smartTruncate
};
