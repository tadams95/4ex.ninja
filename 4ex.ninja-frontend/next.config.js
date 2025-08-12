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
    const isProduction = process.env.NODE_ENV === 'production';
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    return [
      {
        source: '/(.*)',
        headers: [
          // Content Security Policy
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              isProduction
                ? "script-src 'self' 'unsafe-eval' *.stripe.com *.coinbase.com"
                : "script-src 'self' 'unsafe-eval' 'unsafe-inline' *.stripe.com *.coinbase.com *.vercel.app vercel.live",
              "style-src 'self' 'unsafe-inline' *.stripe.com *.coinbase.com",
              "img-src 'self' data: blob: *.stripe.com *.coinbase.com",
              "font-src 'self' data:",
              `connect-src 'self' *.stripe.com *.coinbase.com *.walletconnect.com *.walletconnect.org wss: ws: ${apiUrl} ${apiUrl.replace(
                'http',
                'ws'
              )} wss://relay.walletconnect.com wss://relay.walletconnect.org`,
              "frame-src 'self' *.stripe.com *.coinbase.com" +
                (isProduction ? '' : ' *.vercel.app'),
              "frame-ancestors 'none'",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              'upgrade-insecure-requests',
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
          // HTTPS Strict Transport Security (only in production)
          ...(isProduction
            ? [
                {
                  key: 'Strict-Transport-Security',
                  value: 'max-age=31536000; includeSubDomains; preload',
                },
              ]
            : []),
          // Permissions Policy (wallet-friendly)
          {
            key: 'Permissions-Policy',
            value:
              'camera=(), microphone=(), geolocation=(), payment=(self *.stripe.com *.coinbase.com), usb=(), interest-cohort=(), clipboard-read=(self *.coinbase.com), clipboard-write=(self *.coinbase.com)',
          },
          // Cross-Origin Policies (wallet-friendly configuration)
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'credentialless',
          },
          {
            key: 'Cross-Origin-Opener-Policy',
            value: isProduction ? 'same-origin-allow-popups' : 'unsafe-none',
          },
          {
            key: 'Cross-Origin-Resource-Policy',
            value: 'cross-origin',
          },
          // Security.txt support
          ...(isProduction
            ? [
                {
                  key: 'X-Robots-Tag',
                  value:
                    'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1',
                },
              ]
            : []),
        ],
      },
      // API routes - additional security
      {
        source: '/api/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, no-cache, must-revalidate, private',
          },
          {
            key: 'Pragma',
            value: 'no-cache',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
        ],
      },
      // Static assets - long-term caching
      {
        source: '/(.*)\\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },

  // Bundle optimization
  experimental: {
    optimizePackageImports: ['@tanstack/react-query', 'framer-motion'],
  },

  // Turbopack configuration (moved from experimental.turbo)
  turbopack: {
    rules: {
      // Configure any specific file loaders for Turbopack if needed
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },

  // Webpack configuration for performance monitoring
  webpack: (config, { dev, isServer, webpack }) => {
    // Add performance budget plugin in production
    if (!dev && !isServer) {
      config.plugins.push(new PerformanceBudgetPlugin());
    }

    // Tree-shaking optimizations
    if (config.optimization) {
      config.optimization.usedExports = true;
      config.optimization.sideEffects = false;
    }

    // Optimize Lit components for production
    if (!dev) {
      config.resolve.alias = {
        ...config.resolve.alias,
        'lit/dev-mode.js': false,
        'lit/lib/dev-mode.js': false,
      };

      // Define production mode for Lit and other libraries
      config.plugins.push(
        new webpack.DefinePlugin({
          'process.env.LIT_DEV_MODE': JSON.stringify(false),
          'process.env.NODE_ENV': JSON.stringify('production'),
        })
      );
    }

    return config;
  },
};

module.exports = withBundleAnalyzer(nextConfig);
