import { defineConfig, devices } from '@playwright/test';

const runtime = globalThis as typeof globalThis & {
  process?: { env?: { E2E_PORT?: string } };
};

const configuredPort = runtime.process?.env?.E2E_PORT?.trim();
const e2ePort = configuredPort && /^\d+$/.test(configuredPort) ? configuredPort : '5173';
const baseURL = `http://127.0.0.1:${e2ePort}`;

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL,
    trace: 'retain-on-failure',
  },
  webServer: {
    command: `npm run dev -- --port ${e2ePort} --strictPort`,
    url: baseURL,
    reuseExistingServer: true,
    timeout: 30_000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
