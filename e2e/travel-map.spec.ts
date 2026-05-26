import { expect, test, type Page } from '@playwright/test';
import { places, routeSegments, tripDays } from '../src/data/trip';

const modeTab = (
  page: Page,
  mode: 'overview' | 'route' | 'table' | 'disaster',
) => page.locator(`.mode-tab[data-mode="${mode}"]`);

const hotelReportUrl = 'hotel-report.html';

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
  await expect(page.locator('.topbar')).not.toContainText('GSI pale map');
  await expect(page.locator('.topbar')).not.toContainText('Google Maps 外部導航');
  await expect(page.getByRole('link', { name: '住宿報表' })).toHaveAttribute(
    'href',
    hotelReportUrl,
  );
  await expect(page.getByRole('button', { name: '筆記' })).toBeVisible();
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

  const csvMarker = page.locator(
    '.trip-marker[data-place-id="lake-shikotsu"][data-csv-place="true"]',
  );
  await expect(csvMarker).toBeVisible();
  const csvLabelColor = await csvMarker.locator('span').evaluate((element) =>
    getComputedStyle(element).color,
  );
  expect(csvLabelColor).not.toBe('rgb(247, 242, 231)');
  const csvMarkerStyle = await csvMarker.evaluate((element) => {
    const style = getComputedStyle(element);
    const badgeStyle = getComputedStyle(element, '::after');
    return {
      borderColor: style.borderTopColor,
      borderWidth: style.borderTopWidth,
      boxShadow: style.boxShadow,
      badgeBackground: badgeStyle.backgroundColor,
      badgeWidth: badgeStyle.width,
    };
  });
  expect(csvMarkerStyle.borderColor).toBe('rgb(249, 244, 236)');
  expect(csvMarkerStyle.borderWidth).toBe('2px');
  expect(csvMarkerStyle.boxShadow).toContain('rgba(255, 210, 74');
  expect(csvMarkerStyle.badgeBackground).toBe('rgb(255, 210, 74)');
  expect(csvMarkerStyle.badgeWidth).toBe('9px');

  await csvMarker.click();
  await expect(page.locator('.leaflet-popup-content')).toContainText('航行月份');
});

test('notes modal saves pending changes in localStorage', async ({ page }) => {
  await page.goto('/?weatherNow=2026-04-29');

  await page.getByRole('button', { name: '筆記' }).click();
  await expect(page.getByRole('dialog', { name: '待變更事項筆記' })).toBeVisible();

  const notesTextbox = page.getByRole('textbox', { name: '待變更事項' });
  await page
    .getByRole('textbox', { name: '待變更事項' })
    .fill('6/28 若下雨，積丹海岸改成小樽室內備案。');
  await page.getByRole('button', { name: '儲存' }).click();

  await expect(page.getByRole('dialog', { name: '待變更事項筆記' })).toBeHidden();
  await page.reload();
  await page.getByRole('button', { name: '筆記' }).click();
  await expect(notesTextbox).toHaveValue(
    '6/28 若下雨，積丹海岸改成小樽室內備案。',
  );

  await page.getByRole('button', { name: '清除' }).click();
  await expect(notesTextbox).toHaveValue('');
});

test('weather failure state keeps the map usable', async ({ page }) => {
  await page.goto('/?weather=fail&weatherNow=2026-06-20');

  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.locator('.weather-box.warning')).toBeVisible();
  await expect(page.getByRole('button', { name: '重新讀取天氣' })).toBeVisible();
});

test('overview tab fits all itinerary markers and distinguishes CSV, lodging, and AI lodging markers', async ({
  page,
}) => {
  const itineraryPlaceIds = new Set(
    tripDays.flatMap((day) => [day.startPlaceId, ...day.stopIds, day.endPlaceId]),
  );

  await page.goto('/?weatherNow=2026-04-29');
  await page.locator('.mode-tab[data-mode="overview"]').click();

  await expect(page.locator('.overview-card')).toBeVisible();
  await expect(page.locator('.overview-card .overview-legend')).toContainText('一般行程點');
  await expect(page.locator('.overview-card .overview-legend')).toContainText('CSV 補充');
  await expect(page.locator('.route-line')).toHaveCount(0);
  await expect(page.locator('.trip-marker')).toHaveCount(itineraryPlaceIds.size);
  await expect(page.locator('.trip-marker.marker-from-csv').first()).toBeVisible();
  await expect(page.locator('.trip-marker.marker-lodging').first()).toBeVisible();
  await expect(
    page.locator('.trip-marker.marker-ai-lodging[data-place-id="eniwa-fairfield"]'),
  ).toBeVisible();

  const aiLodgingBadge = await page
    .locator('.trip-marker.marker-ai-lodging[data-place-id="eniwa-fairfield"]')
    .evaluate((element) => getComputedStyle(element, '::before').content);
  expect(aiLodgingBadge).toContain('AI');

  await page.locator('.mode-tab[data-mode="route"]').click();
  await expect(page.locator('.route-line')).toHaveCount(1);
  await expect(page.locator('.route-card')).toBeVisible();
});

test('table tab shows the itinerary table and route/overview remain usable', async ({
  page,
}) => {
  await page.goto('/?weatherNow=2026-04-29');

  await page.getByRole('button', { name: '表格' }).click();

  await expect(page.getByRole('heading', { name: '行程總表' })).toBeVisible();
  await expect(page.locator('.itinerary-table-page')).toBeVisible();
  await expect(page.locator('.itinerary-table')).toBeVisible();
  await expect(page.getByRole('columnheader', { name: '住宿地 / 住宿候選' })).toHaveCount(
    0,
  );
  await expect(
    page.getByRole('columnheader', { name: '起點 / 停靠點 / 終點 / 住宿地' }),
  ).toBeVisible();
  await expect(page.locator('.table-lodging')).toHaveCount(0);
  await expect(page.locator('.table-route-lodging').first()).toContainText('住宿地');
  await expect(page.locator('.itinerary-table tbody tr')).toHaveCount(
    tripDays.length,
  );
  await expect(page.locator('.badge-ai').first()).toContainText('AI 建議');
  await expect(page.getByRole('link', { name: /Google Maps/ }).first()).toHaveAttribute(
    'href',
    /^https:\/\/www\.google\.com\/maps\/dir\//,
  );
  await expect(page.getByRole('link', { name: 'JMA' }).first()).toHaveAttribute(
    'href',
    /^https:\/\//,
  );
  await expect(page.getByRole('link', { name: '道路路況' }).first()).toHaveAttribute(
    'href',
    /^https:\/\//,
  );

  await page.getByRole('button', { name: '總覽' }).click();
  await expect(page.locator('.overview-card')).toBeVisible();
  await expect(page.locator('.route-line')).toHaveCount(0);
  await expect(page.locator('.itinerary-table-page')).toBeHidden();

  await page.getByRole('button', { name: '路線' }).click();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.locator('.route-line')).toHaveCount(1);
  await expect(page.locator('.route-card')).toBeVisible();
});

test('disaster tab switches and preserves overview, route, and table behavior', async ({
  page,
}) => {
  await page.goto('/?weatherNow=2026-04-29');

  await modeTab(page, 'disaster').click();
  await expect(page.locator('[data-page="disaster"]')).toBeVisible();
  await expect(page.locator('.disaster-event-list')).toContainText('浦河沖');
  await expect(page.locator('.disaster-epicenter-marker')).toBeVisible();
  await expect(page.locator('.disaster-itinerary-summary')).toContainText('注意');
  await expect(page.locator('.map')).toHaveCSS('filter', 'none');

  const disasterTileFilter = await page
    .locator('img.leaflet-tile[src*="/xyz/pale/"]')
    .first()
    .evaluate((element) => getComputedStyle(element).filter);
  expect(disasterTileFilter).toContain('grayscale');

  await modeTab(page, 'overview').click();
  await expect(page.locator('.overview-card')).toBeVisible();
  await expect(page.locator('.route-line')).toHaveCount(0);
  await expect(page.locator('[data-page="disaster"]')).toBeHidden();

  await modeTab(page, 'route').click();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.locator('.route-line')).toHaveCount(1);
  await expect(page.locator('.route-card')).toBeVisible();

  await modeTab(page, 'table').click();
  await expect(page.locator('.itinerary-table-page')).toBeVisible();
  await expect(page.locator('.itinerary-table tbody tr')).toHaveCount(
    tripDays.length,
  );
});

test('map uses pale tiles by default, contour detail when zoomed in, and high-contrast routes', async ({
  page,
}) => {
  await page.goto('/?weatherNow=2026-04-29');

  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.locator('.route-halo')).toHaveCount(1);
  await expect(page.locator('.route-line')).toHaveCount(1);
  await expect(page.locator('img.leaflet-tile[src*="/xyz/pale/"]').first()).toBeAttached();
  await expect(page.locator('img.leaflet-tile[src*="/xyz/std/"]')).toHaveCount(0);

  const routeStroke = await page
    .locator('.route-line')
    .first()
    .evaluate((element) => element.getAttribute('stroke'));
  const routeHaloStroke = await page
    .locator('.route-halo')
    .first()
    .evaluate((element) => element.getAttribute('stroke'));

  expect(routeStroke).toBe('#b0005a');
  expect(routeHaloStroke).toBe('#fffdf7');

  for (let clickCount = 0; clickCount < 5; clickCount += 1) {
    await page.locator('.leaflet-control-zoom-in').click();
  }

  await expect(page.locator('img.leaflet-tile[src*="/xyz/std/"]').first()).toBeAttached();
  await expect(page.locator('img.leaflet-tile[src*="/xyz/pale/"]')).toHaveCount(0);
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
