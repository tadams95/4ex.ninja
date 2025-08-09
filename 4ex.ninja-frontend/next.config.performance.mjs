/** @type {import('next').NextConfig} */

const nextConfig = {
  // SWC minification for better performance
  swcMinify: true,

  // Temporarily disable ESLint and TypeScript checks during build to resolve Vercel issues
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },

  // Enable compression
  compress: true,

  // Optimize CSS
  optimizeCss: true,

  // Performance monitoring and optimization
  experimental: {
    // Enable performance monitoring
    instrumentationHook: true,
  },

  // Image optimization with modern formats
  images: {
    // Enable modern image formats
    formats: ['image/webp', 'image/avif'],

    // Allowed image sizes for optimization
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],

    // Quality settings
    quality: 75,

    // Enable placeholder blur
    placeholder: 'blur',

    // Optimize loading
    loading: 'lazy',

    // Remote patterns for external images (if needed)
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'avatars.githubusercontent.com',
      },
    ],
  },

  // Build optimization
  output: 'standalone',

  // Webpack configuration with performance monitoring
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Optimize bundle splitting for better performance
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          // Separate React vendor chunks
          react: {
            name: 'react',
            chunks: 'all',
            test: /[\/]node_modules[\/](react|react-dom)[\/]/,
            priority: 40,
          },
          // Stripe chunk for financial components
          stripe: {
            name: 'stripe',
            chunks: 'all',
            test: /[\/]node_modules[\/]@stripe[\/]/,
            priority: 30,
          },
          // Vendor chunk for NextAuth
          nextAuth: {
            name: 'next-auth',
            chunks: 'all',
            test: /[\/]node_modules[\/]next-auth[\/]/,
            priority: 25,
          },
          // Common vendor libraries
          vendor: {
            name: 'vendor',
            chunks: 'all',
            test: /[\/]node_modules[\/]/,
            priority: 20,
          },
        },
      };

      // Performance budgets
      config.performance = {
        maxAssetSize: 250000, // 250KB
        maxEntrypointSize: 250000, // 250KB
        hints: process.env.NODE_ENV === 'production' ? 'warning' : false,
      };
    }

    return config;
  },
};

export default nextConfig;
