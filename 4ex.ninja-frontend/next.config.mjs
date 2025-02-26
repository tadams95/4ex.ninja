/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
    STRIPE_PK: process.env.STRIPE_PK,
    STRIPE_PRICE_ID: process.env.STRIPE_PRICE_ID,
    NEXT_PUBLIC_URL: process.env.NEXT_PUBLIC_URL,
    MONGO_CONNECTION_STRING: process.env.MONGO_CONNECTION_STRING,
  },
};

export default nextConfig;
