import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('https://router.project-osrm.org/**', async (route) => {
    await route.abort();
  });
  await page.route('https://api.open-meteo.com/**', async (route) => {
    await route.abort();
  });
});

test('desktop layout has no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/?weatherNow=2026-04-29');

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow).toBe(false);
  await expect(page.locator('.leaflet-container')).toBeVisible();
});

test('mobile layout stacks without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/?weatherNow=2026-04-29');

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow).toBe(false);
  await expect(page.getByText('每日行程')).toBeVisible();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.getByText('住宿候選')).toBeVisible();
});
