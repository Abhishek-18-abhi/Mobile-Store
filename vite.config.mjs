
import { defineConfig } from "vite";

export default defineConfig({
  build: {
    outDir: "static/dist",
    emptyOutDir: true,
    rollupOptions: {
      input: "static/src/auth.js",
      output: {
        entryFileNames: "auth.js",
        assetFileNames: "[name][extname]",
      },
    },
  },
});
