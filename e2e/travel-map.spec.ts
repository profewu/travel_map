import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('https://router.project-osrm.org/**', async (route) => {
    await route.abort();
  });
  await page.route('https://api.open-meteo.com/**', async (route) => {
    await route.abort();
  });
});

test('map-first travel UI renders and responds to day and marker selection', async ({
  page,
}) => {
  await page.goto('/?weatherNow=2026-04-29');

  await expect(
    page.getByRole('heading', { name: '北海道西半部自駕地圖' }),
  ).toBeVisible();
  await expect(page.getByText('2026/6/25 - 2026/7/3')).toBeVisible();
  await expect(page.getByText('每日行程')).toBeVisible();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.locator('.route-line')).toHaveCount(1);
  await expect(page.locator('.trip-marker').first()).toBeVisible();
  await expect(page.getByText('天氣資料')).toBeVisible();
  await expect(
    page.getByRole('button', { name: '6/28' }),
  ).toBeVisible();

  await page.getByRole('button', { name: '6/30' }).click();
  await expect(
    page.getByRole('heading', { name: '洞爺湖、昭和新山有珠山，至登別' }),
  ).toBeVisible();
  await expect(page.getByText('登別溫泉旅館', { exact: true })).toBeVisible();

  const trafficLink = page.getByRole('link', { name: '檢查即時道路路況' });
  await expect(trafficLink).toHaveAttribute('href', /^https:\/\//);

  const marker = page.locator('.trip-marker').first();
  await marker.click();
  await expect(page.locator('.leaflet-popup-content')).toContainText(
    /札幌|新千歲|小樽|洞爺|登別/,
  );
});

test('weather failure state keeps the map usable', async ({ page }) => {
  await page.goto('/?weather=fail&weatherNow=2026-06-20');

  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.getByText('天氣資料暫不可用')).toBeVisible();
  await expect(page.getByRole('button', { name: '重新整理天氣' })).toBeVisible();
});

test('Google Maps directions preserve 6/27 Otaru and Yoichi order', async ({
  page,
}) => {
  await page.goto('/?weatherNow=2026-04-29');
  await page.locator('.day-button[data-date="2026-06-27"]').click();

  const href = await page
    .getByRole('link', { name: '開啟 Google Maps' })
    .getAttribute('href');
  if (!href) {
    throw new Error('missing Google Maps href');
  }

  const url = new URL(href);
  expect(url.searchParams.get('origin')).toBe('札幌');
  expect(url.searchParams.get('destination')).toBe('小樽');
  expect(url.searchParams.get('waypoints')).toBe('小樽|余市');
});

test('invalid weatherNow query falls back without crashing', async ({ page }) => {
  await page.goto('/?weatherNow=bad-input');

  await expect(
    page.getByRole('heading', { name: '北海道西半部自駕地圖' }),
  ).toBeVisible();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.getByText('天氣資料')).toBeVisible();
});
