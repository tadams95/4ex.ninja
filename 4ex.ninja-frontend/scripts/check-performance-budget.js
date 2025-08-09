#!/usr/bin/env node

/**
 * Performance Budget Checker
 *
 * Analyzes the built application and checks against performance budgets.
 * Exits with error code if budgets are exceeded.
 */

const fs = require('fs');
const path = require('path');

// Performance budgets (in KB)
const BUDGETS = {
  // JavaScript bundles
  maxInitialJS: 200,
  maxAsyncJS: 100,

  // CSS bundles
  maxCSS: 50,

  // Images and assets
  maxImages: 300,
  maxFonts: 100,

  // Total bundle size
  maxTotalSize: 800,
};

function getFileSize(filePath) {
  try {
    const stats = fs.statSync(filePath);
    return Math.round(stats.size / 1024); // Convert to KB
  } catch (error) {
    return 0;
  }
}

function scanDirectory(dir, extension) {
  const files = [];

  try {
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        files.push(...scanDirectory(fullPath, extension));
      } else if (item.endsWith(extension)) {
        files.push({
          name: item,
          path: fullPath,
          size: getFileSize(fullPath),
        });
      }
    }
  } catch (error) {
    console.warn(`Warning: Could not scan directory ${dir}: ${error.message}`);
  }

  return files;
}

function analyzeBundle() {
  const buildDir = '.next';

  if (!fs.existsSync(buildDir)) {
    console.error('❌ Build directory not found. Please run "npm run build" first.');
    process.exit(1);
  }

  console.log('📊 Analyzing bundle performance...\n');

  // Analyze different asset types
  const staticDir = path.join(buildDir, 'static');

  const jsFiles = scanDirectory(staticDir, '.js');
  const cssFiles = scanDirectory(staticDir, '.css');

  // Calculate totals
  const totalJSSize = jsFiles.reduce((sum, file) => sum + file.size, 0);
  const totalCSSSize = cssFiles.reduce((sum, file) => sum + file.size, 0);
  const totalSize = totalJSSize + totalCSSSize;

  // Find the largest files
  const largestJS = jsFiles.sort((a, b) => b.size - a.size).slice(0, 5);
  const largestCSS = cssFiles.sort((a, b) => b.size - a.size).slice(0, 3);

  // Generate report
  const report = {
    timestamp: new Date().toISOString(),
    budgets: {
      js: {
        current: totalJSSize,
        budget: BUDGETS.maxInitialJS,
        status: totalJSSize <= BUDGETS.maxInitialJS ? 'pass' : 'fail',
      },
      css: {
        current: totalCSSSize,
        budget: BUDGETS.maxCSS,
        status: totalCSSSize <= BUDGETS.maxCSS ? 'pass' : 'fail',
      },
      total: {
        current: totalSize,
        budget: BUDGETS.maxTotalSize,
        status: totalSize <= BUDGETS.maxTotalSize ? 'pass' : 'fail',
      },
    },
    assets: {
      js: largestJS,
      css: largestCSS,
    },
    summary: {
      totalFiles: jsFiles.length + cssFiles.length,
      totalSize: totalSize,
    },
  };

  // Display results
  console.log('📦 Bundle Size Analysis:');
  console.log('┌─────────────────┬─────────┬─────────┬────────┐');
  console.log('│ Category        │ Current │ Budget  │ Status │');
  console.log('├─────────────────┼─────────┼─────────┼────────┤');

  Object.entries(report.budgets).forEach(([category, budget]) => {
    const status = budget.status === 'pass' ? '✅ PASS' : '❌ FAIL';
    const currentStr = `${budget.current}KB`.padEnd(7);
    const budgetStr = `${budget.budget}KB`.padEnd(7);
    const categoryStr = category.toUpperCase().padEnd(15);

    console.log(`│ ${categoryStr} │ ${currentStr} │ ${budgetStr} │ ${status.padEnd(6)} │`);
  });

  console.log('└─────────────────┴─────────┴─────────┴────────┘\n');

  // Show largest files
  if (largestJS.length > 0) {
    console.log('🔍 Largest JavaScript files:');
    largestJS.forEach((file, index) => {
      console.log(`  ${index + 1}. ${file.name} (${file.size}KB)`);
    });
    console.log('');
  }

  if (largestCSS.length > 0) {
    console.log('🎨 Largest CSS files:');
    largestCSS.forEach((file, index) => {
      console.log(`  ${index + 1}. ${file.name} (${file.size}KB)`);
    });
    console.log('');
  }

  // Check for budget violations
  const violations = Object.entries(report.budgets)
    .filter(([, budget]) => budget.status === 'fail')
    .map(([category, budget]) => ({
      category,
      current: budget.current,
      budget: budget.budget,
      excess: budget.current - budget.budget,
    }));

  if (violations.length > 0) {
    console.log('⚠️  Performance Budget Violations:');
    violations.forEach(violation => {
      console.log(
        `  • ${violation.category.toUpperCase()}: ${violation.current}KB exceeds budget by ${
          violation.excess
        }KB`
      );
    });
    console.log('');

    // Provide optimization suggestions
    console.log('💡 Optimization suggestions:');
    violations.forEach(violation => {
      switch (violation.category) {
        case 'js':
          console.log('  • Consider code splitting and lazy loading for non-critical JavaScript');
          console.log('  • Use dynamic imports for vendor libraries');
          console.log('  • Enable tree shaking to remove unused code');
          break;
        case 'css':
          console.log('  • Remove unused CSS with tools like PurgeCSS');
          console.log('  • Consider CSS-in-JS solutions for better tree shaking');
          break;
        case 'total':
          console.log('  • Review all asset types and consider compression');
          console.log('  • Implement proper caching strategies');
          break;
      }
    });
    console.log('');
  }

  // Save report
  fs.writeFileSync('performance-budget-report.json', JSON.stringify(report, null, 2));
  console.log('📄 Detailed report saved to: performance-budget-report.json\n');

  // Summary
  const passedBudgets = Object.values(report.budgets).filter(b => b.status === 'pass').length;
  const totalBudgets = Object.keys(report.budgets).length;

  if (violations.length === 0) {
    console.log(`✅ All ${totalBudgets} performance budgets passed!`);
    console.log(`📊 Total bundle size: ${totalSize}KB`);
    process.exit(0);
  } else {
    console.log(`❌ ${violations.length} of ${totalBudgets} performance budgets failed.`);
    console.log(
      `📊 Total bundle size: ${totalSize}KB (${totalSize - BUDGETS.maxTotalSize}KB over budget)`
    );

    // Exit with error in CI environments
    if (process.env.CI === 'true') {
      process.exit(1);
    }
  }
}

// Run the analysis
analyzeBundle();
