#!/usr/bin/env node

/**
 * Tree-Shaking Effectiveness Monitor
 *
 * Analyzes the webpack bundle to determine tree-shaking effectiveness
 * by checking for unused exports and dead code elimination.
 */

const fs = require('fs');
const path = require('path');

/**
 * Analyzes tree-shaking effectiveness by examining bundle content
 */
function analyzeTreeShaking() {
  const buildDir = '.next';
  const staticDir = path.join(buildDir, 'static');

  if (!fs.existsSync(buildDir)) {
    console.error('❌ Build directory not found. Please run "npm run build" first.');
    process.exit(1);
  }

  console.log('🌳 Analyzing tree-shaking effectiveness...\n');

  const analysis = {
    timestamp: new Date().toISOString(),
    treeshaking: {
      totalFiles: 0,
      analyzedFiles: 0,
      potentialSavings: 0,
      effectiveness: 0,
    },
    findings: {
      unusedExports: [],
      largeBundles: [],
      recommendations: [],
    },
  };

  // Find all JavaScript bundles
  const jsBundles = findJavaScriptFiles(staticDir);
  analysis.treeshaking.totalFiles = jsBundles.length;

  let totalSize = 0;
  let unusedCodeSize = 0;

  jsBundles.forEach(bundle => {
    const content = fs.readFileSync(bundle.path, 'utf8');
    totalSize += content.length;

    // Analyze bundle content for tree-shaking effectiveness
    const bundleAnalysis = analyzeBundleContent(content, bundle.name);

    if (bundleAnalysis.hasUnusedCode) {
      analysis.treeshaking.analyzedFiles++;
      unusedCodeSize += bundleAnalysis.unusedCodeSize;

      analysis.findings.unusedExports.push({
        file: bundle.name,
        size: bundle.size,
        unusedCodeSize: bundleAnalysis.unusedCodeSize,
        unusedPercentage: Math.round((bundleAnalysis.unusedCodeSize / content.length) * 100),
        patterns: bundleAnalysis.patterns,
      });
    }

    // Flag large bundles that might benefit from splitting
    if (bundle.size > 100) {
      // 100KB
      analysis.findings.largeBundles.push({
        file: bundle.name,
        size: bundle.size,
        recommendation: generateBundleRecommendation(bundle.name, bundle.size),
      });
    }
  });

  // Calculate effectiveness
  analysis.treeshaking.potentialSavings = Math.round(unusedCodeSize / 1024); // KB
  analysis.treeshaking.effectiveness = Math.round(((totalSize - unusedCodeSize) / totalSize) * 100);

  // Generate recommendations
  analysis.findings.recommendations = generateRecommendations(analysis);

  // Display results
  displayResults(analysis);

  // Save report
  fs.writeFileSync('tree-shaking-report.json', JSON.stringify(analysis, null, 2));
  console.log('📄 Detailed report saved to: tree-shaking-report.json\n');

  return analysis;
}

/**
 * Find all JavaScript files in the static directory
 */
function findJavaScriptFiles(dir) {
  const files = [];

  function scanDir(currentDir) {
    try {
      const items = fs.readdirSync(currentDir);

      items.forEach(item => {
        const fullPath = path.join(currentDir, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
          scanDir(fullPath);
        } else if (item.endsWith('.js') && !item.includes('.map')) {
          files.push({
            name: item,
            path: fullPath,
            size: Math.round(stat.size / 1024), // KB
          });
        }
      });
    } catch (error) {
      // Ignore permission errors
    }
  }

  scanDir(dir);
  return files;
}

/**
 * Analyze bundle content for unused code patterns
 */
function analyzeBundleContent(content, filename) {
  const analysis = {
    hasUnusedCode: false,
    unusedCodeSize: 0,
    patterns: [],
  };

  // Patterns that indicate potential unused code
  const unusedPatterns = [
    // Unused webpack modules
    { pattern: /\/\*\*\* unused harmony export \w+ \*\*\*\//g, name: 'unused-harmony-exports' },

    // Large comment blocks (often indicate unused code)
    { pattern: /\/\*[\s\S]{200,}\*\//g, name: 'large-comments' },

    // Repeated function definitions (potential duplicates)
    { pattern: /function\s+(\w+)\s*\([^)]*\)\s*\{/g, name: 'function-definitions' },

    // Unused CSS-in-JS (emotion/styled-components)
    { pattern: /css`[\s\S]*?`/g, name: 'css-in-js' },

    // Development-only code that might not be stripped
    { pattern: /console\.(log|warn|error|debug)/g, name: 'console-statements' },

    // Source map references (should be removed in production)
    { pattern: /\/\/# sourceMappingURL=/g, name: 'source-maps' },
  ];

  let totalUnusedSize = 0;

  unusedPatterns.forEach(({ pattern, name }) => {
    const matches = content.match(pattern);
    if (matches) {
      const matchSize = matches.reduce((sum, match) => sum + match.length, 0);

      if (matchSize > 100) {
        // Only report if significant
        analysis.patterns.push({
          type: name,
          count: matches.length,
          size: matchSize,
          examples: matches.slice(0, 3), // First 3 examples
        });

        totalUnusedSize += matchSize;
        analysis.hasUnusedCode = true;
      }
    }
  });

  analysis.unusedCodeSize = totalUnusedSize;
  return analysis;
}

/**
 * Generate recommendations for bundle optimization
 */
function generateBundleRecommendation(filename, size) {
  if (filename.includes('vendor') || filename.includes('lib')) {
    return 'Consider dynamic imports for vendor libraries';
  }

  if (filename.includes('main') || filename.includes('app')) {
    return 'Consider code splitting for main application bundle';
  }

  if (size > 200) {
    return 'Large bundle - review for unnecessary dependencies';
  }

  return 'Consider lazy loading or code splitting';
}

/**
 * Generate optimization recommendations
 */
function generateRecommendations(analysis) {
  const recommendations = [];

  // Tree-shaking effectiveness
  if (analysis.treeshaking.effectiveness < 80) {
    recommendations.push({
      type: 'tree-shaking',
      priority: 'high',
      message: `Tree-shaking effectiveness is ${analysis.treeshaking.effectiveness}%. Consider using ES modules and sideEffects: false in package.json`,
    });
  }

  // Unused exports
  if (analysis.findings.unusedExports.length > 0) {
    recommendations.push({
      type: 'unused-code',
      priority: 'medium',
      message: `${analysis.findings.unusedExports.length} files contain unused code patterns. Review and remove unused exports.`,
    });
  }

  // Large bundles
  if (analysis.findings.largeBundles.length > 3) {
    recommendations.push({
      type: 'bundle-splitting',
      priority: 'medium',
      message: `${analysis.findings.largeBundles.length} large bundles detected. Consider implementing code splitting strategies.`,
    });
  }

  // Potential savings
  if (analysis.treeshaking.potentialSavings > 50) {
    recommendations.push({
      type: 'optimization',
      priority: 'high',
      message: `Potential savings of ${analysis.treeshaking.potentialSavings}KB detected. Review bundle analyzer for optimization opportunities.`,
    });
  }

  return recommendations;
}

/**
 * Display analysis results
 */
function displayResults(analysis) {
  console.log('🌳 Tree-Shaking Analysis Results:');
  console.log('┌─────────────────────────┬──────────┐');
  console.log('│ Metric                  │ Value    │');
  console.log('├─────────────────────────┼──────────┤');
  console.log(
    `│ Effectiveness           │ ${analysis.treeshaking.effectiveness.toString().padEnd(8)} │`
  );
  console.log(
    `│ Files Analyzed          │ ${analysis.treeshaking.analyzedFiles.toString().padEnd(8)} │`
  );
  console.log(
    `│ Potential Savings       │ ${analysis.treeshaking.potentialSavings}KB${' '.repeat(
      Math.max(0, 6 - analysis.treeshaking.potentialSavings.toString().length)
    )} │`
  );
  console.log(
    `│ Unused Code Patterns    │ ${analysis.findings.unusedExports.length.toString().padEnd(8)} │`
  );
  console.log(
    `│ Large Bundles           │ ${analysis.findings.largeBundles.length.toString().padEnd(8)} │`
  );
  console.log('└─────────────────────────┴──────────┘\n');

  // Show findings summary
  if (analysis.findings.unusedExports.length > 0) {
    console.log('🔍 Files with unused code patterns:');
    analysis.findings.unusedExports.slice(0, 5).forEach((finding, index) => {
      console.log(
        `  ${index + 1}. ${finding.file} (${finding.unusedPercentage}% unused, ${Math.round(
          finding.unusedCodeSize / 1024
        )}KB)`
      );
    });
    console.log('');
  }

  if (analysis.findings.largeBundles.length > 0) {
    console.log('📦 Large bundles requiring attention:');
    analysis.findings.largeBundles.slice(0, 5).forEach((bundle, index) => {
      console.log(`  ${index + 1}. ${bundle.file} (${bundle.size}KB) - ${bundle.recommendation}`);
    });
    console.log('');
  }

  // Show recommendations
  if (analysis.findings.recommendations.length > 0) {
    console.log('💡 Optimization Recommendations:');
    analysis.findings.recommendations.forEach((rec, index) => {
      const priority = rec.priority === 'high' ? '🔴' : rec.priority === 'medium' ? '🟡' : '🟢';
      console.log(`  ${priority} ${rec.message}`);
    });
    console.log('');
  }

  // Overall assessment
  if (analysis.treeshaking.effectiveness >= 90) {
    console.log('✅ Excellent tree-shaking effectiveness!');
  } else if (analysis.treeshaking.effectiveness >= 80) {
    console.log('🟡 Good tree-shaking effectiveness with room for improvement.');
  } else {
    console.log('🔴 Poor tree-shaking effectiveness. Significant optimizations needed.');
  }

  // CI integration
  if (process.env.CI === 'true') {
    const threshold = 75; // Minimum acceptable effectiveness
    if (analysis.treeshaking.effectiveness < threshold) {
      console.error(
        `❌ Tree-shaking effectiveness ${analysis.treeshaking.effectiveness}% is below threshold ${threshold}%`
      );
      process.exit(1);
    }
  }
}

// Run the analysis
if (require.main === module) {
  analyzeTreeShaking();
}

module.exports = { analyzeTreeShaking };
