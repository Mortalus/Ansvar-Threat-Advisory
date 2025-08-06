/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker production builds
  output: 'standalone',
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
  // Ensure PostCSS and CSS processing works properly in Docker
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