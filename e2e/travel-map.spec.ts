import { expect, test } from '@playwright/test';
import { places, routeSegments, tripDays } from '../src/data/trip';

test.beforeEach(async ({ page }) => {
  await page.route('https://router.project-osrm.org/**', async (route) => {
    await route.abort();
  });
  await page.route('https://api.open-meteo.com/**', async (route) => {
    await route.abort();
  });
});

test('dashboard travel UI renders and responds to day and marker selection', async ({
  page,
}) => {
  await page.goto('/?weatherNow=2026-04-29');

  await expect(
    page.getByRole('heading', { name: '北海道 TRIP MAP' }),
  ).toBeVisible();
  await expect(page.getByText('2026/6/25 - 2026/7/3')).toBeVisible();
  await expect(page.getByText('每日行程')).toBeVisible();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.locator('.map-overlay')).toBeVisible();
  await expect(page.locator('.route-card')).toBeVisible();
  await expect(page.locator('.route-line')).toHaveCount(1);
  await expect(page.locator('.trip-marker').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: '天氣' })).toBeVisible();
  await expect(page.getByRole('button', { name: '6/28' })).toBeVisible();

  await page.getByRole('button', { name: '6/26' }).click();
  await expect(page.locator('.dashboard-right-panel h2')).toBeVisible();
  await expect(page.getByText('住宿', { exact: true })).toBeVisible();

  const trafficLink = page.getByRole('link', { name: '道路路況' });
  await expect(trafficLink).toHaveAttribute('href', /^https:\/\//);

  await page.locator('.trip-marker[data-place-id="lake-shikotsu"]').click();
  await expect(page.locator('.leaflet-popup-content')).toBeVisible();
});

test('weather failure state keeps the map usable', async ({ page }) => {
  await page.goto('/?weather=fail&weatherNow=2026-06-20');

  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.locator('.weather-box.warning')).toBeVisible();
  await expect(page.getByRole('button', { name: '重新讀取天氣' })).toBeVisible();
});

test('Google Maps directions preserve 6/26 Eniwa to Noboribetsu order', async ({
  page,
}) => {
  await page.goto('/?weatherNow=2026-04-29');
  await page.locator('.day-button[data-date="2026-06-26"]').click();

  const href = await page.locator('.google-action').getAttribute('href');
  if (!href) {
    throw new Error('missing Google Maps href');
  }

  const url = new URL(href);
  const day = tripDays.find((candidate) => candidate.date === '2026-06-26');
  if (!day) {
    throw new Error('missing 2026-06-26 trip day');
  }
  const routeNames = [
    places[day.startPlaceId].nameZh,
    ...day.routeSegmentIds.map((id) => {
      const placeId = routeSegments[id].toPlaceId;
      return places[placeId].nameZh;
    }),
  ];

  expect(url.searchParams.get('origin')).toBe(routeNames[0]);
  expect(url.searchParams.get('destination')).toBe(routeNames.at(-1));
  expect(url.searchParams.get('waypoints')).toBe(routeNames.slice(1, -1).join('|'));
});

test('invalid weatherNow query falls back without crashing', async ({ page }) => {
  await page.goto('/?weatherNow=bad-input');

  await expect(
    page.getByRole('heading', { name: '北海道 TRIP MAP' }),
  ).toBeVisible();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.getByRole('heading', { name: '天氣' })).toBeVisible();
});
