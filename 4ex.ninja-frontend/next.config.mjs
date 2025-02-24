/** @type {import('next').NextConfig} */
const nextConfig = {
  optimizeFonts: true,
  experimental: {
    optimizeFonts: true,
  },
  env: {
    STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
    STRIPE_PK: process.env.STRIPE_PK,
    STRIPE_PRICE_ID: process.env.STRIPE_PRICE_ID,
    NEXT_PUBLIC_URL: process.env.NEXT_PUBLIC_URL,
  },
};

export default nextConfig;
