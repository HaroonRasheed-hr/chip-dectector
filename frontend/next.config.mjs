/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static HTML/CSS/JS export so the Django backend can serve the
  // frontend without running a separate Node.js process in production.
  output: "export",

  // Emit `route/index.html` instead of `route.html` so Django's catch-all
  // can serve a folder for every client-side route.
  trailingSlash: true,

  // `next/image` requires a runtime image optimizer; disable it for the
  // static export so images are served as plain files.
  images: {
    unoptimized: true,
    remotePatterns: [],
  },
};

export default nextConfig;
