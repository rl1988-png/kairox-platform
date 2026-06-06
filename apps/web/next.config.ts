import type { NextConfig } from 'next';
import path from 'path';
import { fileURLToPath } from 'url';

const monorepoRoot = path.join(path.dirname(fileURLToPath(import.meta.url)), '../..');
const standaloneOutput = process.env.KAIROX_WEB_STANDALONE === 'true';
const apiProxyTarget = process.env.API_PROXY_URL?.replace(/\/$/, '');

const nextConfig: NextConfig = {
  transpilePackages: ['@kairox/shared'],
  outputFileTracingRoot: monorepoRoot,
  // Next.js DevTools badge ("N" bottom-left) — only in dev; hidden for clean mobile UI
  devIndicators: false,
  ...(standaloneOutput ? { output: 'standalone' as const } : {}),
  async rewrites() {
    if (!apiProxyTarget) return [];
    return [
      { source: '/api/:path*', destination: `${apiProxyTarget}/api/:path*` },
      { source: '/health', destination: `${apiProxyTarget}/health` },
    ];
  },
};

export default nextConfig;
