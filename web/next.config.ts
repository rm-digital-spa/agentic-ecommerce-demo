import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained build output for the Docker image (node server.js)
  output: "standalone",
};

export default nextConfig;
