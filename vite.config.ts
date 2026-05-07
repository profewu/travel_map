import { defineConfig } from 'vitest/config';

const runtime = globalThis as typeof globalThis & {
  process?: { env?: { VITE_BASE?: string } };
};

export default defineConfig({
  base: runtime.process?.env?.VITE_BASE || '/',
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/**/*.test.ts'],
  },
});
