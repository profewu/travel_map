type RuntimeWithEnv = typeof globalThis & {
  process?: { env: Record<string, string | undefined> };
};

const getRuntime = () => globalThis as RuntimeWithEnv;
const originalEnv = { ...(getRuntime().process?.env ?? {}) };

const loadPlaywrightConfig = async (port?: string) => {
  const runtime = getRuntime();
  if (!runtime.process) {
    throw new Error('process env is required to load Playwright config');
  }

  runtime.process.env = { ...originalEnv };
  if (port) {
    runtime.process.env.E2E_PORT = port;
  } else {
    delete runtime.process.env.E2E_PORT;
  }

  vi.resetModules();
  const module = await import('../playwright.config');
  return module.default as {
    use?: { baseURL?: string };
    webServer?: { command?: string; url?: string };
  };
};

afterEach(() => {
  const runtime = getRuntime();
  if (runtime.process) {
    runtime.process.env = { ...originalEnv };
  }
});

describe('playwright config', () => {
  it('uses the default local Vite port when no E2E_PORT override is set', async () => {
    const config = await loadPlaywrightConfig();

    expect(config.use?.baseURL).toBe('http://127.0.0.1:5173');
    expect(config.webServer?.url).toBe('http://127.0.0.1:5173');
    expect(config.webServer?.command).toContain('--port 5173');
  });

  it('uses E2E_PORT for local environments where 5173 is occupied', async () => {
    const config = await loadPlaywrightConfig('5174');

    expect(config.use?.baseURL).toBe('http://127.0.0.1:5174');
    expect(config.webServer?.url).toBe('http://127.0.0.1:5174');
    expect(config.webServer?.command).toContain('--port 5174');
  });
});
