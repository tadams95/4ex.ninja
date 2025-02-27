/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXTAUTH_URL: process.env.NODE_ENV === 'development' 
      ? 'http://localhost:3000'
      : process.env.NEXTAUTH_URL,
  },
}

module.exports = nextConfig
