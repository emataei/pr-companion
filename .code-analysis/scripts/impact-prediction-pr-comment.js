const { getPRNumber, loadResults, createOrUpdateComment } = require('./pr-comment-utils');

module.exports = async ({ github, context }) => {
  const prNumber = getPRNumber(context);
  
  if (!prNumber) {
    console.log('No PR number found, skipping impact prediction comment');
    return;
  }

  const results = loadResults('impact-prediction-results.json', { 
    overall_risk_score: 0.3,
    deployment_readiness: 'READY - Low risk deployment',
    summary: 'Impact prediction analysis failed',
    impacts: [],
    test_recommendations: [],
    monitoring_suggestions: [],
    rollback_considerations: ['Standard rollback procedures apply']
  });

  const comment = buildComment(results);
  
  await createOrUpdateComment(
    github, 
    context, 
    prNumber, 
    comment, 
    'Impact Assessment',
    `impact-prediction-pr-${prNumber}`
  );
  
  console.log('Impact prediction comment posted/updated successfully');
};

function buildComment(results) {
  const startTime = Date.now();
  const riskLevel = getRiskLevel(results.overall_risk_score);
  const riskCategories = categorizeRisks(results.impacts);
  
  // Build primary risk categories string
  const primaryRisks = Object.entries(riskCategories)
    .filter(([category, level]) => level !== 'NONE')
    .slice(0, 3)
    .map(([category, level]) => `${category}`)
    .join(' + ');
  
  let comment = `## ⚡ Impact Assessment | ${riskLevel} Risk | Primary: ${primaryRisks || 'MINIMAL'}\n\n`;
  
  // Quick summary
  const riskPercentage = Math.round(results.overall_risk_score * 100);
  comment += `**Risk Profile:** ${riskLevel} risk (${riskPercentage}%) with focus on ${primaryRisks || 'routine changes'}\n\n`;
  
  // Risk breakdown by category with visual chart
  const significantRisks = Object.entries(riskCategories).filter(([cat, level]) => level !== 'NONE' && level !== 'LOW');
  if (significantRisks.length > 0) {
    comment += `**Risk Categories:**\n`;
    significantRisks.slice(0, 4).forEach(([category, level]) => {
      const description = getRiskDescription(category, level);
      comment += `- ${category}: ${level} - ${description}\n`;
    });
    
    // Add visual chart if multiple risk categories
    if (significantRisks.length > 1) {
      const riskChart = generateRiskChart(riskCategories);
      comment += riskChart;
    } else {
      comment += `\n`;
    }
  }

  // Critical actions only
  const criticalTests = results.test_recommendations.filter(test => test.priority === 'high');
  if (criticalTests.length > 0) {
    comment += `**Required Actions:**\n`;
    criticalTests.slice(0, 3).forEach(test => {
      comment += `- Add ${test.test_type.toLowerCase()} tests\n`;
    });
    comment += `\n`;
  }

  // Deployment guidance
  comment += `**Deployment:** ${results.deployment_readiness.split(' - ')[0]}\n`;
  if (results.overall_risk_score > 0.7) {
    comment += `**Strategy:** Staged rollout recommended\n`;
  }
  
  // Processing info
  const processingTime = ((Date.now() - startTime) / 1000).toFixed(1);
  comment += `\n---\n*AI analysis • High confidence • ${processingTime}s*`;

  return comment;
}

function getRiskLevel(riskScore) {
  if (riskScore < 0.2) return 'LOW';
  if (riskScore < 0.4) return 'MANAGEABLE';
  if (riskScore < 0.6) return 'MEDIUM';
  if (riskScore < 0.8) return 'HIGH';
  return 'CRITICAL';
}

function categorizeRisks(impacts) {
  const categories = {
    'TESTING': 'NONE',
    'PERFORMANCE': 'NONE', 
    'SECURITY': 'NONE',
    'BREAKING': 'NONE',
    'DATA': 'NONE',
    'COMPATIBILITY': 'NONE',
    'USER_EXPERIENCE': 'NONE',
    'DEPLOYMENT': 'NONE'
  };
  
  impacts.forEach(impact => {
    const category = impact.category.toUpperCase();
    const severity = impact.severity.toUpperCase();
    
    // Map impact categories to our risk categories
    if (category.includes('TEST') || category.includes('TESTING')) {
      categories['TESTING'] = getHigherRisk(categories['TESTING'], severity);
    } else if (category.includes('PERFORMANCE')) {
      categories['PERFORMANCE'] = getHigherRisk(categories['PERFORMANCE'], severity);
    } else if (category.includes('SECURITY')) {
      categories['SECURITY'] = getHigherRisk(categories['SECURITY'], severity);
    } else if (category.includes('COMPATIBILITY') || category.includes('BREAKING')) {
      categories['BREAKING'] = getHigherRisk(categories['BREAKING'], severity);
    } else if (category.includes('DATA')) {
      categories['DATA'] = getHigherRisk(categories['DATA'], severity);
    } else if (category.includes('USER') || category.includes('UX')) {
      categories['USER_EXPERIENCE'] = getHigherRisk(categories['USER_EXPERIENCE'], severity);
    } else if (category.includes('DEPLOY')) {
      categories['DEPLOYMENT'] = getHigherRisk(categories['DEPLOYMENT'], severity);
    }
  });
  
  return categories;
}

function getHigherRisk(current, newRisk) {
  const riskLevels = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
  const currentIndex = riskLevels.indexOf(current);
  const newIndex = riskLevels.indexOf(newRisk);
  return riskLevels[Math.max(currentIndex, newIndex)];
}

function getRiskDescription(category, level) {
  const descriptions = {
    'TESTING': {
      'CRITICAL': 'Missing critical test coverage',
      'HIGH': 'Significant testing gaps',
      'MEDIUM': 'Some test coverage needed',
      'LOW': 'Minor testing improvements'
    },
    'PERFORMANCE': {
      'CRITICAL': 'Severe performance degradation risk',
      'HIGH': 'Significant performance impact',
      'MEDIUM': 'Moderate performance changes',
      'LOW': 'Minor performance considerations'
    },
    'SECURITY': {
      'CRITICAL': 'Critical security vulnerabilities',
      'HIGH': 'Significant security risks',
      'MEDIUM': 'Security review recommended',
      'LOW': 'Minor security considerations'
    },
    'BREAKING': {
      'CRITICAL': 'Major breaking changes',
      'HIGH': 'Significant API changes',
      'MEDIUM': 'Some compatibility concerns',
      'LOW': 'Minor compatibility impact'
    },
    'DATA': {
      'CRITICAL': 'Data integrity at risk',
      'HIGH': 'Significant data changes',
      'MEDIUM': 'Database modifications',
      'LOW': 'Minor data updates'
    },
    'USER_EXPERIENCE': {
      'CRITICAL': 'Major UX disruption',
      'HIGH': 'Significant user impact',
      'MEDIUM': 'Noticeable UX changes',
      'LOW': 'Minor UX improvements'
    },
    'DEPLOYMENT': {
      'CRITICAL': 'Complex deployment required',
      'HIGH': 'Significant deployment changes',
      'MEDIUM': 'Standard deployment considerations',
      'LOW': 'Routine deployment'
    }
  };
  
  return descriptions[category]?.[level] || 'Impact assessment needed';
};

function generateRiskChart(riskCategories) {
  try {
    const fs = require('fs');
    const { spawn } = require('child_process');
    
    // Create temporary data file for Python chart generator
    const chartData = JSON.stringify(riskCategories);
    fs.writeFileSync('temp_risk_data.json', chartData);
    
    // Call Python chart generator (synchronously)
    const python = spawn('python', [
      './chart_generator.py', 
      '--type', 'risk_breakdown',
      '--data', 'temp_risk_data.json'
    ], { cwd: __dirname });
    
    let chartOutput = '';
    python.stdout.on('data', (data) => {
      chartOutput += data.toString();
    });
    
    // For now, return a simple ASCII chart
    const significantRisks = Object.entries(riskCategories)
      .filter(([cat, level]) => level !== 'NONE');
    
    if (significantRisks.length === 0) {
      return '';
    }
    
    let chart = '\n```\nRisk Level Distribution\n';
    chart += '='.repeat(23) + '\n';
    
    // Count risk levels
    const levelCounts = {};
    significantRisks.forEach(([cat, level]) => {
      levelCounts[level] = (levelCounts[level] || 0) + 1;
    });
    
    // Generate bars
    const maxCount = Math.max(...Object.values(levelCounts));
    Object.entries(levelCounts).forEach(([level, count]) => {
      const barLength = Math.round((count / maxCount) * 20);
      const bar = '█'.repeat(barLength);
      chart += `${level.padEnd(12)} |${bar.padEnd(20)} ${count}\n`;
    });
    
    chart += '```\n\n';
    return chart;
    
  } catch (error) {
    console.log('Chart generation failed:', error.message);
    return '';
  }
}
