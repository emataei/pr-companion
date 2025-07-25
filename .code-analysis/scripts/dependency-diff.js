const fs = require('fs');
const path = require('path');

/**
 * Gets changed files from environment or git
 */
function getChangedFiles() {
  // Try to get from environment first (GitHub Actions)
  const envChangedFiles = process.env.CHANGED_FILES;
  if (envChangedFiles && envChangedFiles.trim()) {
    return envChangedFiles.split(' ').filter(f => f.trim());
  }

  // Fallback: try to read from git (basic implementation)
  try {
    const { execSync } = require('child_process');
    const gitOutput = execSync('git diff --name-only HEAD~1 HEAD', { 
      encoding: 'utf8',
      cwd: process.cwd()
    });
    return gitOutput.split('\n').filter(f => f.trim());
  } catch (error) {
    console.log('Could not get changed files from git:', error.message);
    return [];
  }
}

/**
 * Generates a basic dependency diff analysis
 */
async function generateDependencyDiff(changedFiles = []) {
  console.log(`Analyzing dependencies for ${changedFiles.length} changed files`);
  
  // Filter for relevant files
  const relevantFiles = changedFiles.filter(file => 
    file.match(/\.(js|ts|jsx|tsx|py|json)$/) && 
    !file.includes('node_modules') &&
    !file.includes('.git')
  );

  // Basic analysis structure
  const analysis = {
    stats: {
      totalFiles: relevantFiles.length,
      addedDependencies: [],
      removedDependencies: [],
      modifiedDependencies: [],
      circularDependencies: []
    },
    fileChanges: relevantFiles.map(file => ({
      file,
      type: 'modified',
      dependencies: [],
      impact: 'low'
    })),
    summary: `Analyzed ${relevantFiles.length} relevant files out of ${changedFiles.length} total changes`
  };

  // Look for package.json changes
  const packageJsonChanges = relevantFiles.filter(file => 
    file.includes('package.json') || file.includes('requirements.txt')
  );

  if (packageJsonChanges.length > 0) {
    analysis.stats.modifiedDependencies.push({
      file: packageJsonChanges[0],
      change: 'Package dependencies may have changed'
    });
  }

  return analysis;
}

module.exports = {
  getChangedFiles,
  generateDependencyDiff
};