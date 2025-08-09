/**
 * Lighthouse CI Configuration
 *
 * Configures automated performance testing with Lighthouse CI
 * for Core Web Vitals monitoring and performance regression detection.
 */

module.exports = {
  ci: {
    // Build and serve commands
    build: {
      command: 'npm run build',
    },
    serve: {
      command: 'npm start',
      port: 3000,
    },

    // URLs to audit
    collect: {
      url: [
        'http://localhost:3000',
        'http://localhost:3000/login',
        'http://localhost:3000/register',
        'http://localhost:3000/feed',
        'http://localhost:3000/pricing',
      ],
      startServerCommand: 'npm start',
      startServerReadyPattern: 'ready - started server on',
      startServerReadyTimeout: 30000,
      numberOfRuns: 3, // Average of 3 runs for more reliable results
    },

    // Performance assertions
    assert: {
      assertions: {
        // Core Web Vitals thresholds
        'first-contentful-paint': ['error', { maxNumericValue: 2000 }], // 2s
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }], // 2.5s
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }], // 0.1
        'speed-index': ['error', { maxNumericValue: 3000 }], // 3s
        interactive: ['error', { maxNumericValue: 3000 }], // 3s

        // Performance score
        'categories:performance': ['error', { minScore: 0.8 }], // 80+

        // Accessibility and best practices
        'categories:accessibility': ['warn', { minScore: 0.9 }], // 90+
        'categories:best-practices': ['warn', { minScore: 0.9 }], // 90+

        // Bundle size related metrics
        'total-byte-weight': ['error', { maxNumericValue: 1000000 }], // 1MB
        'unused-javascript': ['warn', { maxNumericValue: 100000 }], // 100KB
        'unused-css-rules': ['warn', { maxNumericValue: 50000 }], // 50KB

        // Resource efficiency
        'render-blocking-resources': 'off', // Warning only
        'unminified-javascript': ['error', { maxLength: 0 }],
        'unminified-css': ['error', { maxLength: 0 }],
        'uses-text-compression': ['error', { maxLength: 0 }],
      },
    },

    // Upload configuration (for GitHub integration)
    upload: {
      target: 'temporary-public-storage',
      // Use GitHub integration when LHCI_GITHUB_APP_TOKEN is available
      ...(process.env.LHCI_GITHUB_APP_TOKEN && {
        target: 'lhci',
        serverBaseUrl: 'https://lhci.canary.dev',
        token: process.env.LHCI_GITHUB_APP_TOKEN,
      }),
    },

    // Server configuration for storing results
    server: {
      port: 9001,
      storage: {
        storageMethod: 'fs',
        storagePath: './.lighthouseci',
      },
    },

    // Wizard configuration
    wizard: {
      chromeFlags: ['--no-sandbox', '--headless'],
    },
  },
};
