/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow cross-origin requests in development
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
        ],
      },
    ];
  },
  // Configure allowed development origins
  allowedDevOrigins: ['localhost:3000', '10.181.161.88:3000'],
  // Disable turbopack temporarily to avoid build manifest issues
  experimental: {
    turbo: false,
  },
};

module.exports = nextConfig; 