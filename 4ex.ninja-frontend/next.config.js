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

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          // Content Security Policy
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' *.stripe.com *.vercel.app vercel.live",
              "style-src 'self' 'unsafe-inline' *.stripe.com",
              "img-src 'self' data: blob: *.stripe.com",
              "font-src 'self' data:",
              "connect-src 'self' *.stripe.com wss: ws: " +
                (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'),
              "frame-src 'self' *.stripe.com *.vercel.app",
              "frame-ancestors 'none'",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join('; '),
          },
          // Prevent clickjacking
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          // Prevent MIME type sniffing
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          // XSS Protection
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          // Referrer Policy
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          // HTTPS Strict Transport Security
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload',
          },
          // Permissions Policy
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), payment=(self *.stripe.com)',
          },
        ],
      },
    ];
  },

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
