/** @type {import('next').NextConfig} */
const { withBundleAnalyzer, PerformanceBudgetPlugin } = require('./bundle-analyzer.config');

const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXTAUTH_URL:
      process.env.NODE_ENV === 'development' ? 'http://localhost:3000' : process.env.NEXTAUTH_URL,
  },

  // Performance optimizations
  compress: true,
  poweredByHeader: false,

  // Bundle optimization
  experimental: {
    optimizePackageImports: ['@tanstack/react-query', 'framer-motion'],
  },

  // Webpack configuration for performance monitoring
  webpack: (config, { dev, isServer }) => {
    // Add performance budget plugin in production
    if (!dev && !isServer) {
      config.plugins.push(new PerformanceBudgetPlugin());
    }

    // Tree-shaking optimizations
    if (config.optimization) {
      config.optimization.usedExports = true;
      config.optimization.sideEffects = false;
    }

    return config;
  },
};

module.exports = withBundleAnalyzer(nextConfig);
