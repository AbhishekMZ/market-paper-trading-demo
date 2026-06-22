import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base: './' keeps asset + data URLs relative so the build works when served
// from a GitHub Pages repo subpath (e.g. https://user.github.io/finance_mmg/).
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
