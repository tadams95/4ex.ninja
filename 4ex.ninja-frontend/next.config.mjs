/** @type {import('next').NextConfig} */
/** @type {import('next').NextConfig} */
const nextConfig = {
  // SWC minification for better performance
  swcMinify: true,

  // Enable compression
  compress: true,

  // Optimize CSS
  optimizeCss: true,

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

  // Bundle analyzer (comment out for production)
  // bundleAnalyzer: {
  //   enabled: process.env.ANALYZE === 'true'
  // },

  webpack: (config, { dev, isServer }) => {
    // Optimize chunk splitting for performance
    if (!dev && !isServer) {
      config.optimization.splitChunks = {
        ...config.optimization.splitChunks,
        chunks: 'all',
        cacheGroups: {
          ...config.optimization.splitChunks.cacheGroups,
          default: false,
          vendors: false,
          // Vendor chunk for framer-motion
          framerMotion: {
            name: 'framer-motion',
            chunks: 'all',
            test: /[\/]node_modules[\/]framer-motion[\/]/,
            priority: 40,
          },
          // Vendor chunk for React Query
          reactQuery: {
            name: 'react-query',
            chunks: 'all',
            test: /[\/]node_modules[\/]@tanstack[\/]react-query[\/]/,
            priority: 35,
          },
          // Vendor chunk for Stripe
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
    }

    return config;
  },
};

export default nextConfig;
