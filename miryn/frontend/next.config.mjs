/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async headers() {
    // Prevent reset-token/search query leakage through document.referrer.
    return [{ source: "/:path*", headers: [{ key: "Referrer-Policy", value: "strict-origin" }] }];
  },
  output: "standalone",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
