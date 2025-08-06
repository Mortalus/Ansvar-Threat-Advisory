/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remove standalone output for dev mode to ensure CSS processing works
  // output: 'standalone',
  experimental: {
    outputFileTracingRoot: process.cwd(),
  },
  typescript: {
    // Temporarily ignore TypeScript errors during build for demo purposes
    // Remove this in production after fixing all TypeScript issues
    ignoreBuildErrors: false,
  },
  eslint: {
    // Allow production builds to successfully complete even if ESLint errors exist
    ignoreDuringBuilds: false,
  },
  // Ensure CSS modules and PostCSS work in Docker
  webpack: (config, { isServer }) => {
    // Ensure CSS is processed correctly
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }
    return config;
  },
}

module.exports = nextConfig