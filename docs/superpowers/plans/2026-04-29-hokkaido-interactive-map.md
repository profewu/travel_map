# Hokkaido Interactive Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Traditional Chinese interactive map for Jonathan's 2026-06-25 to 2026-07-03 slow western Hokkaido self-drive trip.

**Architecture:** Create a Vite + TypeScript single-page app with Leaflet as the map layer. Keep trip data, external links, weather fetching, route fallback logic, and UI rendering in focused modules so each part can be tested independently.

**Tech Stack:** Vite, TypeScript, Leaflet, Open-Meteo Forecast API, OSRM route API, Vitest, Playwright.

---

## Scope Notes

- The current workspace is not a git repository. Do not run `git init` or commit unless Jonathan explicitly asks for repo setup.
- The app should be usable as a local web app, not a landing page.
- Open-Meteo forecast data is limited to a practical forecast window. The app must show `尚未進入可預報範圍` for 2026-06-25 to 2026-07-03 until those dates enter the available forecast range.
- Lodging data is curated candidate/search data, not live availability or live pricing.
- JMA, JARTIC/NEXCO, Google Maps, and hotel search actions are external links.

## File Structure

- Create: `package.json` - npm scripts and dependency metadata.
- Create: `tsconfig.json` - TypeScript compiler settings.
- Create: `vite.config.ts` - Vite/Vitest configuration.
- Create: `playwright.config.ts` - Playwright local-server configuration.
- Create: `index.html` - app root.
- Create: `src/main.ts` - app bootstrap.
- Create: `src/styles.css` - responsive map-first UI styles.
- Create: `src/data/trip.ts` - places, daily itinerary, lodging candidates, route segments.
- Create: `src/services/links.ts` - Google Maps, JMA, traffic, and lodging search URL builders.
- Create: `src/services/weather.ts` - Open-Meteo URL builder, forecast-window logic, weather-code labels, fetch wrapper.
- Create: `src/services/routes.ts` - OSRM URL builder, route fetch, fallback route builder.
- Create: `src/ui/state.ts` - selected-day state and view-model builders.
- Create: `src/ui/map.ts` - Leaflet map creation, marker rendering, route rendering.
- Create: `src/ui/panels.ts` - date list, detail panel, weather box, lodging/action rendering.
- Create: `tests/trip-data.test.ts` - trip-data invariants.
- Create: `tests/links.test.ts` - external link generation.
- Create: `tests/weather.test.ts` - weather URL, forecast-window, and failure behavior.
- Create: `tests/routes.test.ts` - OSRM success/failure route behavior.
- Create: `tests/state.test.ts` - selected-day and view model behavior.
- Create: `e2e/travel-map.spec.ts` - app smoke, map, marker, route, popup, date interaction.
- Create: `e2e/responsive.spec.ts` - desktop/mobile layout sanity.

---

### Task 1: Scaffold Tooling

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `vite.config.ts`
- Create: `playwright.config.ts`
- Create: `index.html`
- Create: `src/main.ts`
- Create: `src/styles.css`

- [ ] **Step 1: Initialize npm metadata and install dependencies**

Run:

```powershell
npm init -y
npm install leaflet
npm install -D typescript vite vitest jsdom @playwright/test @types/leaflet
npx playwright install chromium
```

Expected: commands finish with dependencies added to `package.json` and `package-lock.json`.

- [ ] **Step 2: Replace `package.json` scripts**

Edit `package.json` so it contains these scripts while preserving dependency sections created by npm:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc && vite build",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test",
    "verify": "npm run test && npm run build && npm run test:e2e"
  }
}
```

- [ ] **Step 3: Create TypeScript config**

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "types": ["vitest/globals"],
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["src", "tests", "e2e", "vite.config.ts", "playwright.config.ts"]
}
```

- [ ] **Step 4: Create Vite and Vitest config**

Create `vite.config.ts`:

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
```

- [ ] **Step 5: Create Playwright config**

Create `playwright.config.ts`:

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev -- --port 5173',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: true,
    timeout: 30_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

- [ ] **Step 6: Create app shell**

Create `index.html`:

```html
<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>北海道西半部自駕地圖</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

Create `src/main.ts`:

```ts
import './styles.css';

const app = document.querySelector<HTMLDivElement>('#app');

if (!app) {
  throw new Error('App root #app not found');
}

app.innerHTML = '<main class="app-shell"><h1>北海道西半部自駕地圖</h1></main>';
```

Create `src/styles.css`:

```css
:root {
  color: #18212f;
  background: #f6f8f7;
  font-family: "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
a {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  padding: 16px;
}
```

- [ ] **Step 7: Run unit test command once**

Run:

```powershell
npm run test
```

Expected: Vitest starts and reports no test files or no tests found. If Vitest exits nonzero because there are no tests, continue to Task 2 where the first tests are added.

- [ ] **Step 8: Record git status constraint**

Run:

```powershell
git rev-parse --is-inside-work-tree
```

Expected in this workspace: `fatal: not a git repository`. Do not initialize git.

---

### Task 2: Trip Data Model

**Files:**
- Create: `tests/trip-data.test.ts`
- Create: `src/data/trip.ts`

- [ ] **Step 1: Write failing trip-data invariant tests**

Create `tests/trip-data.test.ts`:

```ts
import {
  lodgingCandidates,
  places,
  routeSegments,
  tripDays,
} from '../src/data/trip';

describe('trip data', () => {
  it('covers the approved New Chitose round trip dates', () => {
    expect(tripDays.map((day) => day.date)).toEqual([
      '2026-06-25',
      '2026-06-26',
      '2026-06-27',
      '2026-06-28',
      '2026-06-29',
      '2026-06-30',
      '2026-07-01',
      '2026-07-02',
      '2026-07-03',
    ]);
    expect(tripDays[0].startPlaceId).toBe('new-chitose-airport');
    expect(tripDays.at(-1)?.endPlaceId).toBe('new-chitose-airport');
  });

  it('keeps the slow western route out of Hakodate, Furano, and Biei', () => {
    const forbidden = ['hakodate', '函館', 'furano', '富良野', 'biei', '美瑛'];
    const searchable = [
      ...Object.values(places).map((place) => `${place.nameZh} ${place.nameLocal ?? ''}`),
      ...tripDays.map((day) => `${day.titleZh} ${day.summaryZh}`),
    ].join(' ').toLowerCase();

    for (const token of forbidden) {
      expect(searchable).not.toContain(token.toLowerCase());
    }
  });

  it('references only existing places and route segments', () => {
    for (const day of tripDays) {
      expect(places[day.startPlaceId]).toBeDefined();
      expect(places[day.endPlaceId]).toBeDefined();
      expect(places[day.weatherPlaceId]).toBeDefined();
      for (const stopId of day.stopIds) expect(places[stopId]).toBeDefined();
      for (const segmentId of day.routeSegmentIds) expect(routeSegments[segmentId]).toBeDefined();
    }
  });

  it('offers only 3-star-or-better lodging candidates within curated areas', () => {
    expect(lodgingCandidates.length).toBeGreaterThanOrEqual(8);
    for (const hotel of lodgingCandidates) {
      expect(hotel.starLevel).toBeGreaterThanOrEqual(3);
      expect(['city', 'onsen-resort', 'airport-buffer']).toContain(hotel.type);
      expect(hotel.searchUrl).toMatch(/^https:\/\//);
    }
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm run test -- tests/trip-data.test.ts
```

Expected: FAIL because `src/data/trip.ts` does not exist.

- [ ] **Step 3: Create trip data implementation**

Create `src/data/trip.ts`:

```ts
export type PlaceCategory =
  | 'airport'
  | 'city'
  | 'coast'
  | 'lake'
  | 'mountain'
  | 'onsen'
  | 'distillery'
  | 'food'
  | 'hotel-area';

export interface Place {
  id: string;
  nameZh: string;
  nameLocal?: string;
  lat: number;
  lng: number;
  category: PlaceCategory;
  descriptionZh: string;
  suggestedDurationZh?: string;
  parkingNoteZh?: string;
}

export interface RouteSegment {
  id: string;
  fromPlaceId: string;
  toPlaceId: string;
  fallbackMinutes: number;
  fallbackKm: number;
  noteZh: string;
}

export interface TripDay {
  date: string;
  labelZh: string;
  titleZh: string;
  startPlaceId: string;
  endPlaceId: string;
  weatherPlaceId: string;
  lodgingAreaId?: string;
  stopIds: string[];
  routeSegmentIds: string[];
  summaryZh: string;
  lodgingTargetZh: string;
  driveNoteZh: string;
}

export interface LodgingCandidate {
  id: string;
  areaId: string;
  nameZh: string;
  type: 'city' | 'onsen-resort' | 'airport-buffer';
  starLevel: number;
  budgetRiskZh: string;
  parkingZh: string;
  fitZh: string;
  searchUrl: string;
}

export const places: Record<string, Place> = {
  'new-chitose-airport': {
    id: 'new-chitose-airport',
    nameZh: '新千歲機場',
    nameLocal: 'New Chitose Airport',
    lat: 42.7752,
    lng: 141.6923,
    category: 'airport',
    descriptionZh: '北海道主要國際機場，適合取還車與最後一晚前泊。',
  },
  sapporo: {
    id: 'sapporo',
    nameZh: '札幌',
    nameLocal: 'Sapporo',
    lat: 43.0618,
    lng: 141.3545,
    category: 'city',
    descriptionZh: '北海道最大城市，美食、購物與第一晚調整時差最方便。',
    parkingNoteZh: '市區飯店需確認停車費與車高限制。',
  },
  'mt-moiwa': {
    id: 'mt-moiwa',
    nameZh: '藻岩山',
    nameLocal: 'Mt. Moiwa',
    lat: 43.0229,
    lng: 141.3221,
    category: 'mountain',
    descriptionZh: '札幌夜景候選，天氣好時安排傍晚前往。',
    suggestedDurationZh: '約 2 小時',
  },
  otaru: {
    id: 'otaru',
    nameZh: '小樽',
    nameLocal: 'Otaru',
    lat: 43.1907,
    lng: 140.9947,
    category: 'city',
    descriptionZh: '運河、玻璃工藝、壽司與海鮮，適合慢步調停留。',
    parkingNoteZh: '運河周邊停車場多，假日需預留找車位時間。',
  },
  yoichi: {
    id: 'yoichi',
    nameZh: '余市',
    nameLocal: 'Yoichi',
    lat: 43.1955,
    lng: 140.7835,
    category: 'distillery',
    descriptionZh: 'Nikka Whisky 余市蒸餾所與果園區域。',
    suggestedDurationZh: '約 1.5-2.5 小時',
  },
  shakotan: {
    id: 'shakotan',
    nameZh: '積丹半島',
    nameLocal: 'Shakotan Peninsula',
    lat: 43.2989,
    lng: 140.5986,
    category: 'coast',
    descriptionZh: '夏季海岸線與積丹藍重點區域，天候好時優先。',
    suggestedDurationZh: '半日',
  },
  niseko: {
    id: 'niseko',
    nameZh: '二世谷',
    nameLocal: 'Niseko',
    lat: 42.8048,
    lng: 140.6874,
    category: 'mountain',
    descriptionZh: '羊蹄山景、度假飯店、咖啡與溫泉慢遊區。',
    parkingNoteZh: '自駕停車通常便利，仍需確認住宿停車規則。',
  },
  'lake-toya': {
    id: 'lake-toya',
    nameZh: '洞爺湖',
    nameLocal: 'Lake Toya',
    lat: 42.5655,
    lng: 140.8267,
    category: 'lake',
    descriptionZh: '湖景、溫泉與夏季湖畔散步，適合安排景觀住宿。',
  },
  'showa-shinzan': {
    id: 'showa-shinzan',
    nameZh: '昭和新山 / 有珠山',
    nameLocal: 'Showa Shinzan / Usuzan',
    lat: 42.5431,
    lng: 140.8648,
    category: 'mountain',
    descriptionZh: '洞爺湖到登別途中可安排的火山地形景點。',
    suggestedDurationZh: '約 1.5-2 小時',
  },
  noboribetsu: {
    id: 'noboribetsu',
    nameZh: '登別溫泉',
    nameLocal: 'Noboribetsu Onsen',
    lat: 42.4913,
    lng: 141.1454,
    category: 'onsen',
    descriptionZh: '北海道代表溫泉區，地獄谷與溫泉街適合放慢節奏。',
  },
  'jigokudani': {
    id: 'jigokudani',
    nameZh: '登別地獄谷',
    nameLocal: 'Jigokudani',
    lat: 42.4924,
    lng: 141.1441,
    category: 'onsen',
    descriptionZh: '登別代表地熱景觀，雨天仍可短程步行。',
    suggestedDurationZh: '約 1-1.5 小時',
  },
  'lake-shikotsu': {
    id: 'lake-shikotsu',
    nameZh: '支笏湖',
    nameLocal: 'Lake Shikotsu',
    lat: 42.7748,
    lng: 141.4033,
    category: 'lake',
    descriptionZh: '接近新千歲的清澈湖區，適合作為回機場前的緩衝。',
  },
  chitose: {
    id: 'chitose',
    nameZh: '千歲',
    nameLocal: 'Chitose',
    lat: 42.8191,
    lng: 141.6523,
    category: 'city',
    descriptionZh: '機場前泊、購物、還車準備與航班風險緩衝。',
  },
};

export const routeSegments: Record<string, RouteSegment> = {
  'cts-sapporo': { id: 'cts-sapporo', fromPlaceId: 'new-chitose-airport', toPlaceId: 'sapporo', fallbackMinutes: 65, fallbackKm: 50, noteZh: '抵達日保守估計含取車後進市區。' },
  'sapporo-city': { id: 'sapporo-city', fromPlaceId: 'sapporo', toPlaceId: 'mt-moiwa', fallbackMinutes: 30, fallbackKm: 8, noteZh: '市區短程，視停車與晚餐位置調整。' },
  'sapporo-otaru': { id: 'sapporo-otaru', fromPlaceId: 'sapporo', toPlaceId: 'otaru', fallbackMinutes: 55, fallbackKm: 39, noteZh: '高速道路順暢時約 1 小時。' },
  'otaru-yoichi': { id: 'otaru-yoichi', fromPlaceId: 'otaru', toPlaceId: 'yoichi', fallbackMinutes: 35, fallbackKm: 22, noteZh: '海岸道路短程移動。' },
  'yoichi-shakotan': { id: 'yoichi-shakotan', fromPlaceId: 'yoichi', toPlaceId: 'shakotan', fallbackMinutes: 70, fallbackKm: 48, noteZh: '天候差時可縮短積丹停留。' },
  'shakotan-niseko': { id: 'shakotan-niseko', fromPlaceId: 'shakotan', toPlaceId: 'niseko', fallbackMinutes: 150, fallbackKm: 105, noteZh: '本路線較長，適合早出發。' },
  'niseko-toya': { id: 'niseko-toya', fromPlaceId: 'niseko', toPlaceId: 'lake-toya', fallbackMinutes: 85, fallbackKm: 55, noteZh: '山湖慢遊轉場。' },
  'toya-showa': { id: 'toya-showa', fromPlaceId: 'lake-toya', toPlaceId: 'showa-shinzan', fallbackMinutes: 20, fallbackKm: 8, noteZh: '洞爺湖周邊短程。' },
  'showa-noboribetsu': { id: 'showa-noboribetsu', fromPlaceId: 'showa-shinzan', toPlaceId: 'noboribetsu', fallbackMinutes: 75, fallbackKm: 55, noteZh: '下午進登別溫泉最穩。' },
  'noboribetsu-shikotsu': { id: 'noboribetsu-shikotsu', fromPlaceId: 'noboribetsu', toPlaceId: 'lake-shikotsu', fallbackMinutes: 95, fallbackKm: 75, noteZh: '回機場方向的湖區緩衝。' },
  'shikotsu-chitose': { id: 'shikotsu-chitose', fromPlaceId: 'lake-shikotsu', toPlaceId: 'chitose', fallbackMinutes: 35, fallbackKm: 27, noteZh: '前往千歲住宿或購物。' },
  'chitose-cts': { id: 'chitose-cts', fromPlaceId: 'chitose', toPlaceId: 'new-chitose-airport', fallbackMinutes: 15, fallbackKm: 7, noteZh: '離境日短程。' },
};

export const tripDays: TripDay[] = [
  { date: '2026-06-25', labelZh: '6/25', titleZh: '新千歲抵達，前往札幌', startPlaceId: 'new-chitose-airport', endPlaceId: 'sapporo', weatherPlaceId: 'sapporo', lodgingAreaId: 'sapporo', stopIds: [], routeSegmentIds: ['cts-sapporo'], summaryZh: '下午抵達後取車，先進札幌休息與晚餐。', lodgingTargetZh: '札幌 3-4 星城市飯店，優先有停車。', driveNoteZh: '預估 65 分，另加取車與市區停車時間。' },
  { date: '2026-06-26', labelZh: '6/26', titleZh: '札幌市區慢遊', startPlaceId: 'sapporo', endPlaceId: 'sapporo', weatherPlaceId: 'sapporo', lodgingAreaId: 'sapporo', stopIds: ['mt-moiwa'], routeSegmentIds: ['sapporo-city'], summaryZh: '札幌美食、購物與藻岩山夜景候選。', lodgingTargetZh: '續住札幌，降低換飯店負擔。', driveNoteZh: '市區短程，依餐廳與停車位置彈性調整。' },
  { date: '2026-06-27', labelZh: '6/27', titleZh: '小樽與余市', startPlaceId: 'sapporo', endPlaceId: 'otaru', weatherPlaceId: 'otaru', lodgingAreaId: 'otaru', stopIds: ['otaru', 'yoichi'], routeSegmentIds: ['sapporo-otaru', 'otaru-yoichi'], summaryZh: '運河散步、海鮮、玻璃工藝與余市蒸餾所。', lodgingTargetZh: '小樽 3-4 星城市飯店，優先停車便利。', driveNoteZh: '預估 90 分，另加景點停留。' },
  { date: '2026-06-28', labelZh: '6/28', titleZh: '積丹海岸到二世谷', startPlaceId: 'otaru', endPlaceId: 'niseko', weatherPlaceId: 'shakotan', lodgingAreaId: 'niseko', stopIds: ['yoichi', 'shakotan', 'niseko'], routeSegmentIds: ['otaru-yoichi', 'yoichi-shakotan', 'shakotan-niseko'], summaryZh: '天氣好時主攻積丹藍，下午轉往二世谷。', lodgingTargetZh: '二世谷度假或溫泉型飯店。', driveNoteZh: '預估 4 小時以上，需早出發。' },
  { date: '2026-06-29', labelZh: '6/29', titleZh: '二世谷慢遊，前往洞爺湖', startPlaceId: 'niseko', endPlaceId: 'lake-toya', weatherPlaceId: 'niseko', lodgingAreaId: 'lake-toya', stopIds: ['niseko', 'lake-toya'], routeSegmentIds: ['niseko-toya'], summaryZh: '上午保留羊蹄山景與咖啡，下午進洞爺湖。', lodgingTargetZh: '洞爺湖溫泉或湖景飯店。', driveNoteZh: '預估 85 分，適合慢速轉場。' },
  { date: '2026-06-30', labelZh: '6/30', titleZh: '洞爺湖到登別', startPlaceId: 'lake-toya', endPlaceId: 'noboribetsu', weatherPlaceId: 'lake-toya', lodgingAreaId: 'noboribetsu', stopIds: ['showa-shinzan', 'noboribetsu'], routeSegmentIds: ['toya-showa', 'showa-noboribetsu'], summaryZh: '湖畔、火山地形與登別溫泉。', lodgingTargetZh: '登別溫泉旅館或溫泉度假飯店。', driveNoteZh: '預估 95 分，另加昭和新山停留。' },
  { date: '2026-07-01', labelZh: '7/1', titleZh: '登別地獄谷，回支笏湖方向', startPlaceId: 'noboribetsu', endPlaceId: 'lake-shikotsu', weatherPlaceId: 'noboribetsu', lodgingAreaId: 'lake-shikotsu', stopIds: ['jigokudani', 'lake-shikotsu'], routeSegmentIds: ['noboribetsu-shikotsu'], summaryZh: '上午地獄谷與溫泉街，下午回到機場側湖區。', lodgingTargetZh: '支笏湖或千歲側飯店，視價格選擇。', driveNoteZh: '預估 95 分。' },
  { date: '2026-07-02', labelZh: '7/2', titleZh: '支笏湖與千歲緩衝', startPlaceId: 'lake-shikotsu', endPlaceId: 'chitose', weatherPlaceId: 'lake-shikotsu', lodgingAreaId: 'chitose', stopIds: ['lake-shikotsu', 'chitose'], routeSegmentIds: ['shikotsu-chitose'], summaryZh: '保留天候與購物緩衝，準備隔天離境。', lodgingTargetZh: '新千歲或千歲 3-4 星前泊飯店。', driveNoteZh: '預估 35 分，適合降低離境壓力。' },
  { date: '2026-07-03', labelZh: '7/3', titleZh: '新千歲早班離境', startPlaceId: 'chitose', endPlaceId: 'new-chitose-airport', weatherPlaceId: 'chitose', stopIds: [], routeSegmentIds: ['chitose-cts'], summaryZh: '早上前往新千歲機場，還車與登機。', lodgingTargetZh: '無。', driveNoteZh: '預估 15 分，需依租車公司還車規定提早。' },
];

export const lodgingCandidates: LodgingCandidate[] = [
  { id: 'sapporo-gracery', areaId: 'sapporo', nameZh: '札幌格拉斯麗飯店', type: 'city', starLevel: 3, budgetRiskZh: '旺季可能接近預算上緣。', parkingZh: '需確認合作停車場與車高。', fitZh: '札幌站周邊方便第一晚與市區日。', searchUrl: 'https://www.google.com/travel/hotels?q=Hotel%20Gracery%20Sapporo' },
  { id: 'sapporo-jr-inn', areaId: 'sapporo', nameZh: 'JR Inn 札幌周邊候選', type: 'city', starLevel: 3, budgetRiskZh: '通常比高級飯店穩定。', parkingZh: '需確認停車場。', fitZh: '交通與晚餐選擇方便。', searchUrl: 'https://www.google.com/travel/hotels?q=JR%20Inn%20Sapporo' },
  { id: 'otaru-authent', areaId: 'otaru', nameZh: '小樽 Authent Hotel 候選', type: 'city', starLevel: 3, budgetRiskZh: '假日與旺季偏高。', parkingZh: '通常需付費停車。', fitZh: '適合小樽市區步行。', searchUrl: 'https://www.google.com/travel/hotels?q=Authent%20Hotel%20Otaru' },
  { id: 'otaru-nord', areaId: 'otaru', nameZh: 'Hotel Nord 小樽候選', type: 'city', starLevel: 3, budgetRiskZh: '運河位置可能提高價格。', parkingZh: '需確認停車。', fitZh: '運河周邊位置佳。', searchUrl: 'https://www.google.com/travel/hotels?q=Hotel%20Nord%20Otaru' },
  { id: 'niseko-green-leaf', areaId: 'niseko', nameZh: '二世谷 Green Leaf 候選', type: 'onsen-resort', starLevel: 4, budgetRiskZh: '旺季視房型可能超過預算。', parkingZh: '度假區停車通常較便利。', fitZh: '度假感與山景體驗較完整。', searchUrl: 'https://www.google.com/travel/hotels?q=The%20Green%20Leaf%20Niseko%20Village' },
  { id: 'toya-sun-palace', areaId: 'lake-toya', nameZh: '洞爺湖 Sun Palace 候選', type: 'onsen-resort', starLevel: 4, budgetRiskZh: '景觀房與餐食方案可能超預算。', parkingZh: '通常有住宿停車。', fitZh: '湖景與溫泉體驗明確。', searchUrl: 'https://www.google.com/travel/hotels?q=Lake%20Toya%20Sun%20Palace' },
  { id: 'noboribetsu-mahoroba', areaId: 'noboribetsu', nameZh: '登別 Mahoroba 候選', type: 'onsen-resort', starLevel: 4, budgetRiskZh: '溫泉旅館常接近或超過預算上緣。', parkingZh: '通常有住宿停車。', fitZh: '登別溫泉核心體驗。', searchUrl: 'https://www.google.com/travel/hotels?q=Hotel%20Mahoroba%20Noboribetsu' },
  { id: 'chitose-air-terminal', areaId: 'chitose', nameZh: 'Air Terminal Hotel 候選', type: 'airport-buffer', starLevel: 3, budgetRiskZh: '機場前泊便利性提高價格。', parkingZh: '需依機場停車規則確認。', fitZh: '最適合早班機離境。', searchUrl: 'https://www.google.com/travel/hotels?q=Air%20Terminal%20Hotel%20New%20Chitose' },
];
```

- [ ] **Step 4: Run trip-data tests**

Run:

```powershell
npm run test -- tests/trip-data.test.ts
```

Expected: PASS.

- [ ] **Step 5: Git checkpoint gate**

Run:

```powershell
git rev-parse --is-inside-work-tree
```

Expected in current workspace: FAIL. Skip commit and continue.

---

### Task 3: External Link Builders

**Files:**
- Create: `tests/links.test.ts`
- Create: `src/services/links.ts`

- [ ] **Step 1: Write failing link tests**

Create `tests/links.test.ts`:

```ts
import {
  buildGoogleDirectionsUrl,
  buildHotelSearchUrl,
  jmaWarningUrl,
  roadTrafficUrl,
} from '../src/services/links';

describe('external links', () => {
  it('builds Google Maps directions with origin, destination, and waypoints', () => {
    const url = buildGoogleDirectionsUrl({
      origin: '札幌',
      destination: '小樽',
      waypoints: ['余市'],
    });

    expect(url).toContain('https://www.google.com/maps/dir/?api=1');
    expect(url).toContain('origin=%E6%9C%AD%E5%B9%8C');
    expect(url).toContain('destination=%E5%B0%8F%E6%A8%BD');
    expect(url).toContain('waypoints=%E4%BD%99%E5%B8%82');
    expect(url).toContain('travelmode=driving');
  });

  it('builds lodging search links with exact trip dates', () => {
    const url = buildHotelSearchUrl('登別溫泉 4星 溫泉旅館', '2026-06-30', '2026-07-01');

    expect(url).toContain('https://www.google.com/travel/hotels');
    expect(url).toContain('checkin=2026-06-30');
    expect(url).toContain('checkout=2026-07-01');
  });

  it('exposes official live-check URLs', () => {
    expect(jmaWarningUrl).toMatch(/^https:\/\/www\.jma\.go\.jp\//);
    expect(roadTrafficUrl).toMatch(/^https:\/\//);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm run test -- tests/links.test.ts
```

Expected: FAIL because `src/services/links.ts` does not exist.

- [ ] **Step 3: Implement link builders**

Create `src/services/links.ts`:

```ts
export interface DirectionsInput {
  origin: string;
  destination: string;
  waypoints?: string[];
}

export const jmaWarningUrl = 'https://www.jma.go.jp/bosai/warning/#area_type=offices&area_code=016000&lang=zh-TW';
export const roadTrafficUrl = 'https://www.c-nexco.co.jp/en/jam/';

export function buildGoogleDirectionsUrl(input: DirectionsInput): string {
  const params = new URLSearchParams({
    api: '1',
    origin: input.origin,
    destination: input.destination,
    travelmode: 'driving',
  });

  if (input.waypoints?.length) {
    params.set('waypoints', input.waypoints.join('|'));
  }

  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export function buildGoogleSearchUrl(query: string): string {
  const params = new URLSearchParams({ q: query });
  return `https://www.google.com/maps/search/?api=1&${params.toString()}`;
}

export function buildHotelSearchUrl(query: string, checkIn: string, checkOut: string): string {
  const params = new URLSearchParams({
    q: query,
    checkin: checkIn,
    checkout: checkOut,
  });
  return `https://www.google.com/travel/hotels?${params.toString()}`;
}
```

- [ ] **Step 4: Run link tests**

Run:

```powershell
npm run test -- tests/links.test.ts
```

Expected: PASS.

---

### Task 4: Weather Service

**Files:**
- Create: `tests/weather.test.ts`
- Create: `src/services/weather.ts`

- [ ] **Step 1: Write failing weather tests**

Create `tests/weather.test.ts`:

```ts
import {
  buildOpenMeteoUrl,
  fetchWeatherSummary,
  isWithinForecastWindow,
  weatherCodeLabelZh,
} from '../src/services/weather';

describe('weather service', () => {
  it('builds an Open-Meteo URL for current and daily weather', () => {
    const url = buildOpenMeteoUrl(43.0618, 141.3545);

    expect(url).toContain('https://api.open-meteo.com/v1/forecast');
    expect(url).toContain('latitude=43.0618');
    expect(url).toContain('longitude=141.3545');
    expect(url).toContain('current=temperature_2m');
    expect(url).toContain('daily=weather_code');
    expect(url).toContain('forecast_days=16');
    expect(url).toContain('timezone=Asia%2FTokyo');
  });

  it('detects whether a trip date is in the forecast window', () => {
    const now = new Date('2026-06-20T08:00:00+09:00');

    expect(isWithinForecastWindow('2026-06-25', now)).toBe(true);
    expect(isWithinForecastWindow('2026-07-10', now)).toBe(false);
    expect(isWithinForecastWindow('2026-06-19', now)).toBe(false);
  });

  it('returns not-yet-available before trip dates enter the forecast window', async () => {
    const summary = await fetchWeatherSummary({
      lat: 43.0618,
      lng: 141.3545,
      targetDate: '2026-06-25',
      now: new Date('2026-04-29T09:00:00+09:00'),
      fetcher: vi.fn(),
    });

    expect(summary.status).toBe('not-yet-available');
    expect(summary.messageZh).toContain('尚未進入可預報範圍');
  });

  it('returns unavailable when the weather request fails', async () => {
    const summary = await fetchWeatherSummary({
      lat: 43.0618,
      lng: 141.3545,
      targetDate: '2026-06-25',
      now: new Date('2026-06-20T09:00:00+09:00'),
      fetcher: vi.fn().mockRejectedValue(new Error('network down')),
    });

    expect(summary.status).toBe('unavailable');
    expect(summary.messageZh).toBe('天氣資料暫不可用');
  });

  it('maps common weather codes to Chinese labels', () => {
    expect(weatherCodeLabelZh(0)).toBe('晴朗');
    expect(weatherCodeLabelZh(61)).toBe('下雨');
    expect(weatherCodeLabelZh(999)).toBe('天氣狀態未分類');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm run test -- tests/weather.test.ts
```

Expected: FAIL because `src/services/weather.ts` does not exist.

- [ ] **Step 3: Implement weather service**

Create `src/services/weather.ts`:

```ts
export type WeatherStatus = 'loaded' | 'not-yet-available' | 'unavailable';

export interface WeatherSummary {
  status: WeatherStatus;
  messageZh: string;
  temperatureC?: number;
  precipitationProbabilityMax?: number;
  windSpeedKmh?: number;
  weatherLabelZh?: string;
  updatedAt?: string;
}

export interface FetchWeatherInput {
  lat: number;
  lng: number;
  targetDate: string;
  now?: Date;
  fetcher?: typeof fetch;
}

interface OpenMeteoResponse {
  current?: {
    time?: string;
    temperature_2m?: number;
    wind_speed_10m?: number;
    weather_code?: number;
  };
  daily?: {
    time?: string[];
    precipitation_probability_max?: number[];
    weather_code?: number[];
  };
}

const forecastDays = 16;

export function buildOpenMeteoUrl(lat: number, lng: number): string {
  const params = new URLSearchParams({
    latitude: String(lat),
    longitude: String(lng),
    current: ['temperature_2m', 'wind_speed_10m', 'weather_code'].join(','),
    daily: ['weather_code', 'precipitation_probability_max'].join(','),
    timezone: 'Asia/Tokyo',
    forecast_days: String(forecastDays),
    wind_speed_unit: 'kmh',
  });

  return `https://api.open-meteo.com/v1/forecast?${params.toString()}`;
}

export function isWithinForecastWindow(targetDate: string, now = new Date()): boolean {
  const today = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
  const [year, month, day] = targetDate.split('-').map(Number);
  const target = new Date(Date.UTC(year, month - 1, day));
  const diffDays = Math.round((target.getTime() - today.getTime()) / 86_400_000);
  return diffDays >= 0 && diffDays <= forecastDays;
}

export function weatherCodeLabelZh(code: number | undefined): string {
  if (code === 0) return '晴朗';
  if ([1, 2, 3].includes(code ?? -1)) return '多雲';
  if ([45, 48].includes(code ?? -1)) return '有霧';
  if ([51, 53, 55, 56, 57].includes(code ?? -1)) return '毛毛雨';
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code ?? -1)) return '下雨';
  if ([71, 73, 75, 77, 85, 86].includes(code ?? -1)) return '下雪';
  if ([95, 96, 99].includes(code ?? -1)) return '雷雨';
  return '天氣狀態未分類';
}

export async function fetchWeatherSummary(input: FetchWeatherInput): Promise<WeatherSummary> {
  if (!isWithinForecastWindow(input.targetDate, input.now)) {
    return {
      status: 'not-yet-available',
      messageZh: `${input.targetDate} 尚未進入可預報範圍`,
    };
  }

  const fetcher = input.fetcher ?? fetch;

  try {
    const response = await fetcher(buildOpenMeteoUrl(input.lat, input.lng));
    if (!response.ok) throw new Error(`Open-Meteo HTTP ${response.status}`);
    const data = (await response.json()) as OpenMeteoResponse;
    const dailyIndex = data.daily?.time?.indexOf(input.targetDate) ?? -1;
    const dailyCode = dailyIndex >= 0 ? data.daily?.weather_code?.[dailyIndex] : undefined;
    const precipitationProbabilityMax =
      dailyIndex >= 0 ? data.daily?.precipitation_probability_max?.[dailyIndex] : undefined;

    return {
      status: 'loaded',
      messageZh: '天氣資料已更新',
      temperatureC: data.current?.temperature_2m,
      windSpeedKmh: data.current?.wind_speed_10m,
      precipitationProbabilityMax,
      weatherLabelZh: weatherCodeLabelZh(dailyCode ?? data.current?.weather_code),
      updatedAt: data.current?.time,
    };
  } catch {
    return {
      status: 'unavailable',
      messageZh: '天氣資料暫不可用',
    };
  }
}
```

- [ ] **Step 4: Run weather tests**

Run:

```powershell
npm run test -- tests/weather.test.ts
```

Expected: PASS.

---

### Task 5: Route Service

**Files:**
- Create: `tests/routes.test.ts`
- Create: `src/services/routes.ts`

- [ ] **Step 1: Write failing route tests**

Create `tests/routes.test.ts`:

```ts
import { places, routeSegments } from '../src/data/trip';
import { buildFallbackRoute, buildOsrmUrl, fetchRouteGeometry } from '../src/services/routes';

describe('route service', () => {
  it('builds OSRM URLs with lon-lat coordinate order', () => {
    const segment = routeSegments['sapporo-otaru'];
    const url = buildOsrmUrl(segment, places);

    expect(url).toContain('https://router.project-osrm.org/route/v1/driving/');
    expect(url).toContain('141.3545,43.0618;140.9947,43.1907');
    expect(url).toContain('overview=full');
    expect(url).toContain('geometries=geojson');
  });

  it('builds fallback geometry from segment endpoints', () => {
    const fallback = buildFallbackRoute([routeSegments['sapporo-otaru']], places);

    expect(fallback.status).toBe('fallback');
    expect(fallback.points).toEqual([
      [43.0618, 141.3545],
      [43.1907, 140.9947],
    ]);
    expect(fallback.durationMinutes).toBe(55);
  });

  it('falls back when OSRM fetch fails', async () => {
    const route = await fetchRouteGeometry({
      segments: [routeSegments['sapporo-otaru']],
      places,
      fetcher: vi.fn().mockRejectedValue(new Error('offline')),
    });

    expect(route.status).toBe('fallback');
    expect(route.noteZh).toContain('使用內建估算');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm run test -- tests/routes.test.ts
```

Expected: FAIL because `src/services/routes.ts` does not exist.

- [ ] **Step 3: Implement route service**

Create `src/services/routes.ts`:

```ts
import type { Place, RouteSegment } from '../data/trip';

export interface RouteResult {
  status: 'live' | 'fallback';
  points: Array<[number, number]>;
  durationMinutes: number;
  distanceKm: number;
  noteZh: string;
}

interface OsrmResponse {
  routes?: Array<{
    duration?: number;
    distance?: number;
    geometry?: {
      coordinates?: Array<[number, number]>;
    };
  }>;
}

export function buildOsrmUrl(segment: RouteSegment, places: Record<string, Place>): string {
  const from = places[segment.fromPlaceId];
  const to = places[segment.toPlaceId];
  const coordinates = `${from.lng},${from.lat};${to.lng},${to.lat}`;
  return `https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=full&geometries=geojson`;
}

export function buildFallbackRoute(
  segments: RouteSegment[],
  places: Record<string, Place>,
): RouteResult {
  const points: Array<[number, number]> = [];
  let durationMinutes = 0;
  let distanceKm = 0;

  for (const segment of segments) {
    const from = places[segment.fromPlaceId];
    const to = places[segment.toPlaceId];
    if (points.length === 0) points.push([from.lat, from.lng]);
    points.push([to.lat, to.lng]);
    durationMinutes += segment.fallbackMinutes;
    distanceKm += segment.fallbackKm;
  }

  return {
    status: 'fallback',
    points,
    durationMinutes,
    distanceKm,
    noteZh: '使用內建估算車程，請以 Google Maps 與即時路況確認。',
  };
}

export async function fetchRouteGeometry(input: {
  segments: RouteSegment[];
  places: Record<string, Place>;
  fetcher?: typeof fetch;
}): Promise<RouteResult> {
  const fallback = buildFallbackRoute(input.segments, input.places);
  const fetcher = input.fetcher ?? fetch;

  try {
    const allPoints: Array<[number, number]> = [];
    let durationSeconds = 0;
    let distanceMeters = 0;

    for (const segment of input.segments) {
      const response = await fetcher(buildOsrmUrl(segment, input.places));
      if (!response.ok) throw new Error(`OSRM HTTP ${response.status}`);
      const data = (await response.json()) as OsrmResponse;
      const route = data.routes?.[0];
      const coordinates = route?.geometry?.coordinates;
      if (!route || !coordinates?.length) throw new Error('OSRM route missing geometry');

      const leafletPoints = coordinates.map(([lng, lat]) => [lat, lng] as [number, number]);
      if (allPoints.length === 0) allPoints.push(...leafletPoints);
      else allPoints.push(...leafletPoints.slice(1));
      durationSeconds += route.duration ?? 0;
      distanceMeters += route.distance ?? 0;
    }

    return {
      status: 'live',
      points: allPoints,
      durationMinutes: Math.round(durationSeconds / 60),
      distanceKm: Math.round(distanceMeters / 100) / 10,
      noteZh: 'OSRM 估算路線，實際時間仍請以 Google Maps 與即時路況確認。',
    };
  } catch {
    return fallback;
  }
}
```

- [ ] **Step 4: Run route tests**

Run:

```powershell
npm run test -- tests/routes.test.ts
```

Expected: PASS.

---

### Task 6: UI State and View Models

**Files:**
- Create: `tests/state.test.ts`
- Create: `src/ui/state.ts`

- [ ] **Step 1: Write failing state tests**

Create `tests/state.test.ts`:

```ts
import { lodgingCandidates, places, tripDays } from '../src/data/trip';
import { buildDayViewModel, getInitialDayId, selectDay } from '../src/ui/state';

describe('UI state', () => {
  it('selects the first trip date by default', () => {
    expect(getInitialDayId(tripDays)).toBe('2026-06-25');
  });

  it('selects a requested day when it exists', () => {
    expect(selectDay('2026-06-28', tripDays).date).toBe('2026-06-28');
  });

  it('falls back to the first day for an unknown date', () => {
    expect(selectDay('2026-08-01', tripDays).date).toBe('2026-06-25');
  });

  it('builds a Traditional Chinese view model with lodging candidates', () => {
    const day = selectDay('2026-06-30', tripDays);
    const vm = buildDayViewModel(day, places, lodgingCandidates);

    expect(vm.titleZh).toBe(day.titleZh);
    expect(vm.startNameZh).toBe('洞爺湖');
    expect(vm.endNameZh).toBe('登別溫泉');
    expect(vm.lodgingCandidates.length).toBeGreaterThan(0);
    expect(vm.actionLabelsZh).toEqual([
      '開啟 Google Maps',
      '檢查 JMA 天氣警示',
      '檢查即時道路路況',
      '搜尋 3 星以上住宿',
    ]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm run test -- tests/state.test.ts
```

Expected: FAIL because `src/ui/state.ts` does not exist.

- [ ] **Step 3: Implement state helpers**

Create `src/ui/state.ts`:

```ts
import type { LodgingCandidate, Place, TripDay } from '../data/trip';

export interface DayViewModel {
  date: string;
  labelZh: string;
  titleZh: string;
  startNameZh: string;
  endNameZh: string;
  summaryZh: string;
  lodgingTargetZh: string;
  driveNoteZh: string;
  stopNamesZh: string[];
  lodgingCandidates: LodgingCandidate[];
  actionLabelsZh: string[];
}

export function getInitialDayId(days: TripDay[]): string {
  return days[0].date;
}

export function selectDay(date: string, days: TripDay[]): TripDay {
  return days.find((day) => day.date === date) ?? days[0];
}

export function buildDayViewModel(
  day: TripDay,
  places: Record<string, Place>,
  lodgingCandidates: LodgingCandidate[],
): DayViewModel {
  return {
    date: day.date,
    labelZh: day.labelZh,
    titleZh: day.titleZh,
    startNameZh: places[day.startPlaceId].nameZh,
    endNameZh: places[day.endPlaceId].nameZh,
    summaryZh: day.summaryZh,
    lodgingTargetZh: day.lodgingTargetZh,
    driveNoteZh: day.driveNoteZh,
    stopNamesZh: day.stopIds.map((id) => places[id].nameZh),
    lodgingCandidates: lodgingCandidates.filter((hotel) => hotel.areaId === day.lodgingAreaId),
    actionLabelsZh: ['開啟 Google Maps', '檢查 JMA 天氣警示', '檢查即時道路路況', '搜尋 3 星以上住宿'],
  };
}
```

- [ ] **Step 4: Run state tests**

Run:

```powershell
npm run test -- tests/state.test.ts
```

Expected: PASS.

---

### Task 7: Map-First UI Integration

**Files:**
- Create: `e2e/travel-map.spec.ts`
- Modify: `src/main.ts`
- Modify: `src/styles.css`
- Create: `src/ui/map.ts`
- Create: `src/ui/panels.ts`

- [ ] **Step 1: Write failing Playwright smoke test**

Create `e2e/travel-map.spec.ts`:

```ts
import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('https://router.project-osrm.org/**', (route) => route.abort());
});

test('renders the Traditional Chinese interactive travel map', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: '北海道西半部自駕地圖' })).toBeVisible();
  await expect(page.getByText('每日行程')).toBeVisible();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.locator('.route-line')).toHaveCount(1);
  await expect(page.locator('.trip-marker').first()).toBeVisible();
  await expect(page.getByText('天氣資料')).toBeVisible();
  await expect(page.getByRole('button', { name: /6\/28/ })).toBeVisible();
});

test('selecting a day updates the route and detail panel', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: /6\/30/ }).click();

  await expect(page.getByRole('heading', { name: '洞爺湖、昭和新山有珠山，至登別' })).toBeVisible();
  await expect(page.getByText('登別溫泉旅館')).toBeVisible();
  await expect(page.getByRole('link', { name: '檢查即時道路路況' })).toHaveAttribute('href', /^https:\/\//);
});

test('marker popups expose place details', async ({ page }) => {
  await page.goto('/');

  await page.locator('.trip-marker').first().click();

  await expect(page.locator('.leaflet-popup-content')).toContainText(/札幌|新千歲|小樽|洞爺|登別/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm run test:e2e -- e2e/travel-map.spec.ts
```

Expected: FAIL because the map and panels are not implemented.

- [ ] **Step 3: Implement Leaflet map module**

Create `src/ui/map.ts`:

```ts
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Place, RouteSegment, TripDay } from '../data/trip';
import { fetchRouteGeometry } from '../services/routes';

export interface MapController {
  renderDay(day: TripDay): Promise<void>;
}

export function createTripMap(
  container: HTMLElement,
  places: Record<string, Place>,
  routeSegments: Record<string, RouteSegment>,
  onPlaceSelected: (place: Place) => void,
): MapController {
  const map = L.map(container, { zoomControl: true }).setView([42.9, 141.1], 8);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map);

  const markerLayer = L.layerGroup().addTo(map);
  const routeLayer = L.layerGroup().addTo(map);

  async function renderDay(day: TripDay): Promise<void> {
    markerLayer.clearLayers();
    routeLayer.clearLayers();

    const placeIds = [day.startPlaceId, ...day.stopIds, day.endPlaceId];
    const dayPlaces = placeIds.map((id) => places[id]);
    const bounds = L.latLngBounds(dayPlaces.map((place) => [place.lat, place.lng]));

    for (const place of dayPlaces) {
      const marker = L.marker([place.lat, place.lng], {
        title: place.nameZh,
        icon: L.divIcon({
          className: `trip-marker marker-${place.category}`,
          html: `<span>${place.nameZh.slice(0, 1)}</span>`,
          iconSize: [30, 30],
          iconAnchor: [15, 15],
        }),
      })
        .addTo(markerLayer)
        .bindPopup(`<strong>${place.nameZh}</strong><br>${place.descriptionZh}`);

      marker.on('click', () => onPlaceSelected(place));
    }

    const segments = day.routeSegmentIds.map((id) => routeSegments[id]);
    const route = await fetchRouteGeometry({ segments, places });
    L.polyline(route.points, {
      className: 'route-line',
      color: route.status === 'live' ? '#0f766e' : '#b45309',
      weight: 5,
      opacity: 0.9,
    })
      .bindPopup(`${route.durationMinutes} 分 / ${route.distanceKm} km<br>${route.noteZh}`)
      .addTo(routeLayer);

    map.fitBounds(bounds.pad(0.2), { animate: false });
  }

  return { renderDay };
}
```

- [ ] **Step 4: Implement panel renderer**

Create `src/ui/panels.ts`:

```ts
import type { LodgingCandidate, Place, TripDay } from '../data/trip';
import { buildGoogleDirectionsUrl, buildHotelSearchUrl, jmaWarningUrl, roadTrafficUrl } from '../services/links';
import type { WeatherSummary } from '../services/weather';
import type { DayViewModel } from './state';

export function renderDayButtons(days: TripDay[], selectedDate: string): string {
  return `
    <section class="day-list" aria-label="每日行程">
      <h2>每日行程</h2>
      <div class="day-buttons">
        ${days
          .map(
            (day) => `
              <button class="day-button ${day.date === selectedDate ? 'active' : ''}" data-date="${day.date}">
                <span>${day.labelZh}</span>
                <strong>${day.titleZh}</strong>
              </button>
            `,
          )
          .join('')}
      </div>
    </section>
  `;
}

export function renderWeatherBox(summary: WeatherSummary): string {
  if (summary.status === 'loaded') {
    return `
      <section class="weather-box">
        <h3>天氣資料</h3>
        <p>${summary.weatherLabelZh ?? '天氣狀態未分類'}，${summary.temperatureC ?? '-'}°C，降雨 ${summary.precipitationProbabilityMax ?? '-'}%，風速 ${summary.windSpeedKmh ?? '-'} km/h</p>
        <small>更新時間：${summary.updatedAt ?? '未提供'}</small>
      </section>
    `;
  }

  return `
    <section class="weather-box warning">
      <h3>天氣資料</h3>
      <p>${summary.messageZh}</p>
      <button class="retry-weather" type="button">重新整理天氣</button>
    </section>
  `;
}

export function renderLodging(candidates: LodgingCandidate[]): string {
  return `
    <section class="lodging-list">
      <h3>住宿候選</h3>
      ${candidates
        .map(
          (hotel) => `
            <article class="hotel-card">
              <h4>${hotel.nameZh}</h4>
              <p>${hotel.starLevel} 星以上 / ${hotel.fitZh}</p>
              <p>${hotel.parkingZh}</p>
              <p>${hotel.budgetRiskZh}</p>
              <a href="${hotel.searchUrl}" target="_blank" rel="noreferrer">查看住宿搜尋</a>
            </article>
          `,
        )
        .join('')}
    </section>
  `;
}

export function renderDetailPanel(input: {
  vm: DayViewModel;
  day: TripDay;
  places: Record<string, Place>;
  weather: WeatherSummary;
}): string {
  const routeNames = [input.vm.startNameZh, ...input.vm.stopNamesZh, input.vm.endNameZh];
  const directionsUrl = buildGoogleDirectionsUrl({
    origin: input.vm.startNameZh,
    destination: input.vm.endNameZh,
    waypoints: input.vm.stopNamesZh,
  });
  const hotelUrl = buildHotelSearchUrl(`${input.vm.endNameZh} 3星以上 住宿`, input.day.date, nextDate(input.day.date));

  return `
    <aside class="detail-panel">
      <p class="eyebrow">選取日期 ${input.vm.labelZh}</p>
      <h2>${input.vm.titleZh}</h2>
      <p>${input.vm.summaryZh}</p>
      <dl>
        <dt>路線</dt><dd>${routeNames.join(' → ')}</dd>
        <dt>預估行車</dt><dd>${input.vm.driveNoteZh}</dd>
        <dt>住宿目標</dt><dd>${input.vm.lodgingTargetZh}</dd>
      </dl>
      ${renderWeatherBox(input.weather)}
      <nav class="action-grid" aria-label="外部即時檢查">
        <a href="${directionsUrl}" target="_blank" rel="noreferrer">開啟 Google Maps</a>
        <a href="${jmaWarningUrl}" target="_blank" rel="noreferrer">檢查 JMA 天氣警示</a>
        <a href="${roadTrafficUrl}" target="_blank" rel="noreferrer">檢查即時道路路況</a>
        <a href="${hotelUrl}" target="_blank" rel="noreferrer">搜尋 3 星以上住宿</a>
      </nav>
      ${renderLodging(input.vm.lodgingCandidates)}
    </aside>
  `;
}

function nextDate(date: string): string {
  const parsed = new Date(`${date}T00:00:00+09:00`);
  parsed.setDate(parsed.getDate() + 1);
  return parsed.toISOString().slice(0, 10);
}
```

- [ ] **Step 5: Replace app bootstrap**

Replace `src/main.ts`:

```ts
import './styles.css';
import { lodgingCandidates, places, routeSegments, tripDays } from './data/trip';
import { fetchWeatherSummary } from './services/weather';
import { createTripMap } from './ui/map';
import { renderDayButtons, renderDetailPanel } from './ui/panels';
import { buildDayViewModel, getInitialDayId, selectDay } from './ui/state';

const app = document.querySelector<HTMLDivElement>('#app');

if (!app) {
  throw new Error('App root #app not found');
}

let selectedDate = getInitialDayId(tripDays);
let selectedPlaceId = tripDays[0].startPlaceId;

app.innerHTML = `
  <main class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">2026/6/25 - 2026/7/3</p>
        <h1>北海道西半部自駕地圖</h1>
      </div>
      <p class="trip-summary">新千歲來回，札幌、小樽、積丹、二世谷、洞爺、登別、支笏湖慢速自駕。</p>
    </header>
    <div class="workspace">
      <div id="days"></div>
      <section class="map-panel" aria-label="互動地圖">
        <div id="map" class="map"></div>
      </section>
      <div id="details"></div>
    </div>
  </main>
`;

const daysRoot = document.querySelector<HTMLDivElement>('#days');
const mapRoot = document.querySelector<HTMLDivElement>('#map');
const detailsRoot = document.querySelector<HTMLDivElement>('#details');

if (!daysRoot || !mapRoot || !detailsRoot) {
  throw new Error('Required layout roots not found');
}

const map = createTripMap(mapRoot, places, routeSegments, (place) => {
  selectedPlaceId = place.id;
});

async function render(): Promise<void> {
  const day = selectDay(selectedDate, tripDays);
  const weatherPlace = places[day.weatherPlaceId];
  const weather = await fetchWeatherSummary({
    lat: weatherPlace.lat,
    lng: weatherPlace.lng,
    targetDate: day.date,
  });
  const vm = buildDayViewModel(day, places, lodgingCandidates);

  daysRoot.innerHTML = renderDayButtons(tripDays, day.date);
  detailsRoot.innerHTML = renderDetailPanel({ vm, day, places, weather });
  await map.renderDay(day);

  daysRoot.querySelectorAll<HTMLButtonElement>('.day-button').forEach((button) => {
    button.addEventListener('click', () => {
      selectedDate = button.dataset.date ?? selectedDate;
      void render();
    });
  });

  detailsRoot.querySelector<HTMLButtonElement>('.retry-weather')?.addEventListener('click', () => {
    void render();
  });

  document.documentElement.dataset.selectedPlace = selectedPlaceId;
}

void render();
```

- [ ] **Step 6: Replace CSS with responsive map-first layout**

Replace `src/styles.css`:

```css
:root {
  color: #18212f;
  background: #f6f8f7;
  font-family: "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
a {
  font: inherit;
}

a {
  color: #0f5f66;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr;
}

.topbar {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-bottom: 1px solid #d9e2e0;
  background: #ffffff;
}

h1,
h2,
h3,
h4,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 0;
  font-size: 24px;
}

.eyebrow {
  margin-bottom: 4px;
  color: #667085;
  font-size: 13px;
}

.trip-summary {
  max-width: 560px;
  margin-bottom: 0;
  color: #41515f;
}

.workspace {
  display: grid;
  grid-template-columns: 260px minmax(420px, 1fr) 360px;
  min-height: calc(100vh - 77px);
}

.day-list,
.detail-panel {
  height: calc(100vh - 77px);
  overflow: auto;
  padding: 16px;
  background: #ffffff;
}

.day-list {
  border-right: 1px solid #d9e2e0;
}

.day-buttons {
  display: grid;
  gap: 8px;
}

.day-button {
  width: 100%;
  min-height: 72px;
  text-align: left;
  border: 1px solid #d4ddd9;
  background: #ffffff;
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
}

.day-button span {
  display: block;
  color: #667085;
  font-size: 13px;
}

.day-button strong {
  display: block;
  margin-top: 4px;
}

.day-button.active {
  border-color: #0f766e;
  background: #e9f6f3;
}

.map-panel {
  min-height: 520px;
  background: #dfe9e7;
}

.map {
  width: 100%;
  height: 100%;
  min-height: 520px;
}

.trip-marker {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 2px solid #ffffff;
  border-radius: 999px;
  background: #0f766e;
  color: #ffffff;
  font-weight: 700;
  box-shadow: 0 4px 12px rgb(15 23 42 / 24%);
}

.marker-airport {
  background: #1d4ed8;
}

.marker-onsen {
  background: #b45309;
}

.marker-lake,
.marker-coast {
  background: #0369a1;
}

.detail-panel {
  border-left: 1px solid #d9e2e0;
}

.detail-panel dl {
  display: grid;
  grid-template-columns: 82px 1fr;
  gap: 8px 12px;
}

.detail-panel dt {
  color: #667085;
}

.detail-panel dd {
  margin: 0;
}

.weather-box,
.hotel-card {
  border: 1px solid #d9e2e0;
  border-radius: 8px;
  padding: 12px;
  margin: 14px 0;
  background: #f9fbfb;
}

.weather-box.warning {
  border-color: #f4c27a;
  background: #fff8eb;
}

.action-grid {
  display: grid;
  gap: 8px;
  margin: 14px 0;
}

.action-grid a,
.hotel-card a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  border: 1px solid #0f766e;
  border-radius: 8px;
  padding: 8px 10px;
  text-decoration: none;
  color: #0f5f66;
  background: #ffffff;
}

.retry-weather {
  min-height: 36px;
  border: 1px solid #b45309;
  border-radius: 8px;
  background: #ffffff;
  color: #92400e;
  cursor: pointer;
}

@media (max-width: 980px) {
  .topbar {
    align-items: start;
    flex-direction: column;
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .day-list,
  .detail-panel {
    height: auto;
    max-height: none;
    border: 0;
  }

  .day-buttons {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  .map {
    height: 58vh;
  }
}

@media (max-width: 560px) {
  .topbar,
  .day-list,
  .detail-panel {
    padding: 12px;
  }

  h1 {
    font-size: 20px;
  }

  .detail-panel dl {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 7: Run unit tests and e2e smoke**

Run:

```powershell
npm run test
npm run test:e2e -- e2e/travel-map.spec.ts
```

Expected: unit tests PASS and Playwright tests PASS.

---

### Task 8: Responsive and Failure-State Verification

**Files:**
- Create: `e2e/responsive.spec.ts`
- Modify: `src/main.ts`

- [ ] **Step 1: Write responsive e2e test**

Create `e2e/responsive.spec.ts`:

```ts
import { expect, test } from '@playwright/test';

test('desktop layout has no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
  await expect(page.locator('.leaflet-container')).toBeVisible();
});

test('mobile layout stacks without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
  await expect(page.getByText('每日行程')).toBeVisible();
  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.getByText('住宿候選')).toBeVisible();
});
```

- [ ] **Step 2: Run responsive test**

Run:

```powershell
npm run test:e2e -- e2e/responsive.spec.ts
```

Expected: PASS. If it fails, adjust `src/styles.css` dimensions and rerun this exact command.

- [ ] **Step 3: Add fetch mock controls for failure-state manual verification**

Modify `src/main.ts` so weather fetch can be forced to fail through `?weather=fail` and the forecast-window date can be controlled through `?weatherNow=YYYY-MM-DD`:

```ts
function weatherFetcher(): typeof fetch | undefined {
  const params = new URLSearchParams(window.location.search);
  if (params.get('weather') !== 'fail') return undefined;

  return (() => Promise.reject(new Error('forced weather failure'))) as typeof fetch;
}

function weatherNow(): Date | undefined {
  const params = new URLSearchParams(window.location.search);
  const value = params.get('weatherNow');
  return value ? new Date(`${value}T09:00:00+09:00`) : undefined;
}
```

Then change the weather call inside `render()` to:

```ts
const weather = await fetchWeatherSummary({
  lat: weatherPlace.lat,
  lng: weatherPlace.lng,
  targetDate: day.date,
  now: weatherNow(),
  fetcher: weatherFetcher(),
});
```

- [ ] **Step 4: Add e2e weather failure assertion**

Append to `e2e/travel-map.spec.ts`:

```ts
test('weather failure state keeps the map usable', async ({ page }) => {
  await page.route('https://router.project-osrm.org/**', (route) => route.abort());
  await page.goto('/?weather=fail&weatherNow=2026-06-20');

  await expect(page.locator('.leaflet-container')).toBeVisible();
  await expect(page.getByText('天氣資料暫不可用')).toBeVisible();
  await expect(page.getByRole('button', { name: '重新整理天氣' })).toBeVisible();
});
```

- [ ] **Step 5: Run e2e tests**

Run:

```powershell
npm run test:e2e
```

Expected: PASS.

---

### Task 9: Build Verification and Local Launch

**Files:**
- Modify only if tests reveal a concrete issue: `src/styles.css`, `src/main.ts`, or focused module under `src/`

- [ ] **Step 1: Run full verification**

Run:

```powershell
npm run verify
```

Expected: unit tests PASS, TypeScript build PASS, Playwright tests PASS.

- [ ] **Step 2: Start the dev server for Jonathan**

Run:

```powershell
npm run dev -- --port 5173
```

Expected: Vite prints a local URL such as `http://127.0.0.1:5173/`.

- [ ] **Step 3: Open and manually inspect the app**

Open:

```text
http://127.0.0.1:5173/
```

Check:

- The map is not blank.
- The UI is Traditional Chinese.
- `6/25` through `7/3` date buttons are visible.
- Clicking `6/30` changes the detail panel to `洞爺湖、昭和新山有珠山，至登別`.
- A marker popup opens with place text.
- Weather shows either loaded data, `尚未進入可預報範圍`, or `天氣資料暫不可用`.
- External links open new pages.

- [ ] **Step 4: Record final changed files**

Run:

```powershell
if (Get-Command rg -ErrorAction SilentlyContinue) { rg --files } else { Get-ChildItem -Recurse -File | ForEach-Object FullName }
```

Expected: output includes the app files, tests, spec, and this implementation plan.
