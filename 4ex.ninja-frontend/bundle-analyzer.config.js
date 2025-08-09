/**
 * Bundle Analysis Configuration
 *
 * Configures bundle analysis for performance monitoring
 * and size tracking in CI/CD pipelines.
 */

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
  openAnalyzer: false, // Don't auto-open in CI
});

// Performance budgets for bundle sizes (in KB)
const PERFORMANCE_BUDGETS = {
  // JavaScript bundles
  maxInitialJS: 200, // 200KB max for initial JS
  maxAsyncJS: 100, // 100KB max for async chunks

  // CSS bundles
  maxCSS: 50, // 50KB max for CSS

  // Images and assets
  maxImages: 300, // 300KB max for images
  maxFonts: 100, // 100KB max for fonts

  // Total bundle size
  maxTotalSize: 800, // 800KB max total size
};

// Webpack configuration for performance monitoring
const performanceConfig = {
  performance: {
    // Show warnings for assets larger than these limits
    maxAssetSize: PERFORMANCE_BUDGETS.maxAsyncJS * 1024, // Convert to bytes
    maxEntrypointSize: PERFORMANCE_BUDGETS.maxInitialJS * 1024,

    // Custom filter to ignore certain assets from performance warnings
    assetFilter: function (assetFilename) {
      // Ignore source maps and hot-update files from performance warnings
      return !assetFilename.endsWith('.map') && !assetFilename.includes('hot-update');
    },

    // Show warnings instead of errors for better CI experience
    hints: process.env.NODE_ENV === 'production' ? 'warning' : false,
  },

  // Optimization configuration for better performance
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // Vendor chunk for stable dependencies
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          maxSize: PERFORMANCE_BUDGETS.maxAsyncJS * 1024,
        },

        // Common chunk for shared code
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
          enforce: true,
          maxSize: PERFORMANCE_BUDGETS.maxAsyncJS * 1024,
        },
      },
    },
  },
};

// Function to analyze bundle and report performance budget status
function analyzeBundlePerformance(compilation) {
  const assets = compilation.getAssets();
  const warnings = [];

  // Categorize assets
  const assetCategories = {
    js: [],
    css: [],
    images: [],
    fonts: [],
    other: [],
  };

  assets.forEach(asset => {
    const { name, size } = asset;
    const sizeKB = Math.round(size / 1024);

    if (name.endsWith('.js')) {
      assetCategories.js.push({ name, size: sizeKB });
    } else if (name.endsWith('.css')) {
      assetCategories.css.push({ name, size: sizeKB });
    } else if (name.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) {
      assetCategories.images.push({ name, size: sizeKB });
    } else if (name.match(/\.(woff|woff2|ttf|eot)$/)) {
      assetCategories.fonts.push({ name, size: sizeKB });
    } else {
      assetCategories.other.push({ name, size: sizeKB });
    }
  });

  // Check performance budgets
  const totalJSSize = assetCategories.js.reduce((sum, asset) => sum + asset.size, 0);
  const totalCSSSize = assetCategories.css.reduce((sum, asset) => sum + asset.size, 0);
  const totalImageSize = assetCategories.images.reduce((sum, asset) => sum + asset.size, 0);
  const totalFontSize = assetCategories.fonts.reduce((sum, asset) => sum + asset.size, 0);
  const totalSize = totalJSSize + totalCSSSize + totalImageSize + totalFontSize;

  // Generate budget report
  const budgetReport = {
    timestamp: new Date().toISOString(),
    budgets: {
      js: {
        current: totalJSSize,
        budget: PERFORMANCE_BUDGETS.maxInitialJS,
        status: totalJSSize <= PERFORMANCE_BUDGETS.maxInitialJS ? 'pass' : 'fail',
      },
      css: {
        current: totalCSSSize,
        budget: PERFORMANCE_BUDGETS.maxCSS,
        status: totalCSSSize <= PERFORMANCE_BUDGETS.maxCSS ? 'pass' : 'fail',
      },
      images: {
        current: totalImageSize,
        budget: PERFORMANCE_BUDGETS.maxImages,
        status: totalImageSize <= PERFORMANCE_BUDGETS.maxImages ? 'pass' : 'fail',
      },
      fonts: {
        current: totalFontSize,
        budget: PERFORMANCE_BUDGETS.maxFonts,
        status: totalFontSize <= PERFORMANCE_BUDGETS.maxFonts ? 'pass' : 'fail',
      },
      total: {
        current: totalSize,
        budget: PERFORMANCE_BUDGETS.maxTotalSize,
        status: totalSize <= PERFORMANCE_BUDGETS.maxTotalSize ? 'pass' : 'fail',
      },
    },
    assets: assetCategories,
  };

  // Check for budget violations
  Object.entries(budgetReport.budgets).forEach(([category, budget]) => {
    if (budget.status === 'fail') {
      warnings.push(
        `Performance budget exceeded for ${category}: ${budget.current}KB > ${budget.budget}KB`
      );
    }
  });

  // Log budget report in CI
  if (process.env.CI) {
    console.log('📊 Performance Budget Report:');
    console.log(JSON.stringify(budgetReport, null, 2));

    if (warnings.length > 0) {
      console.warn('⚠️ Performance Budget Warnings:');
      warnings.forEach(warning => console.warn(`  - ${warning}`));
    } else {
      console.log('✅ All performance budgets passed!');
    }
  }

  return budgetReport;
}

// Webpack plugin for performance monitoring
class PerformanceBudgetPlugin {
  apply(compiler) {
    compiler.hooks.afterEmit.tap('PerformanceBudgetPlugin', compilation => {
      const report = analyzeBundlePerformance(compilation);

      // Write report to file for CI consumption
      if (process.env.CI) {
        const fs = require('fs');
        const path = require('path');

        const reportPath = path.join(process.cwd(), 'performance-budget-report.json');
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

        console.log(`📄 Performance budget report written to: ${reportPath}`);
      }
    });
  }
}

module.exports = {
  withBundleAnalyzer,
  performanceConfig,
  PerformanceBudgetPlugin,
  PERFORMANCE_BUDGETS,
  analyzeBundlePerformance,
};
