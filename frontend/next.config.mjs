/** @type {import('next').NextConfig} */

const nextConfig = {
  // Removed permanent redirect from / to /overview
  // Now / shows marketing homepage for unauthenticated users
  // Authenticated users are redirected via page.tsx logic

  // Enable standalone output for Docker optimization
  output: 'standalone',
  experimental: {
    outputFileTracingIncludes: {
      '/': ['./public/**/*'],
    },
  },

  // Temporarily ignore TypeScript and ESLint errors during build
  // TODO: Fix all type errors before production deployment
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
