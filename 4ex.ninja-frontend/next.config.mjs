/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
    STRIPE_PK: process.env.STRIPE_PK,
    STRIPE_PRICE_ID: process.env.STRIPE_PRICE_ID,
    NEXT_PUBLIC_URL: process.env.NEXT_PUBLIC_URL,
    MONGO_CONNECTION_STRING: process.env.MONGO_CONNECTION_STRING,
  },
  // Optimize bundle splitting for better performance
  experimental: {
    optimizePackageImports: ['framer-motion', '@tanstack/react-query', 'zustand'],
  },
  // Configure webpack for better code splitting
  webpack: (config, { dev, isServer }) => {
    if (!dev && !isServer) {
      // Split vendor libraries into separate chunks
      config.optimization.splitChunks = {
        ...config.optimization.splitChunks,
        cacheGroups: {
          ...config.optimization.splitChunks.cacheGroups,
          // Framer Motion in separate chunk (loaded only when needed)
          framerMotion: {
            name: 'framer-motion',
            test: /[\\/]node_modules[\\/]framer-motion[\\/]/,
            chunks: 'all',
            priority: 30,
            reuseExistingChunk: true,
          },
          // React Query in separate chunk
          reactQuery: {
            name: 'react-query',
            test: /[\\/]node_modules[\\/]@tanstack[\\/]react-query[\\/]/,
            chunks: 'all',
            priority: 30,
            reuseExistingChunk: true,
          },
          // Stripe SDK in separate chunk (loaded only when needed)
          stripe: {
            name: 'stripe',
            test: /[\\/]node_modules[\\/]@stripe[\\/]/,
            chunks: 'async', // Only include in async chunks
            priority: 30,
            reuseExistingChunk: true,
          },
          // NextAuth in separate chunk
          nextAuth: {
            name: 'next-auth',
            test: /[\\/]node_modules[\\/]next-auth[\\/]/,
            chunks: 'all',
            priority: 30,
            reuseExistingChunk: true,
          },
        },
      };
    }
    return config;
  },
};

export default nextConfig;
