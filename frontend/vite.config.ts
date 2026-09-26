import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The browser always talks to "/api" on its own origin: Vite proxies it in development,
// nginx does the same in the Docker image, so cookies stay first-party and no CORS is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY ?? "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
