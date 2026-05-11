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

test('mobile table mode uses compact itinerary cards without horizontal overflow', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/?weatherNow=2026-04-29');

  await page.getByRole('button', { name: '表格' }).click();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow).toBe(false);
  await expect(page.getByRole('heading', { name: '行程總表' })).toBeVisible();
  await expect(page.locator('.itinerary-card').first()).toBeVisible();
  await expect(page.locator('.itinerary-table thead')).toBeHidden();
  await expect(page.locator('.badge-csv').first()).toBeVisible();
  await expect(page.locator('.badge-ai').first()).toContainText('AI 建議');
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
