/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Allow external images
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
};

export default nextConfig;
