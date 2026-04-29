# 2026-04-29 Hokkaido Interactive Map Worklog

## Snapshot

- Workspace: `C:\Users\Jonathan\Documents\travel_map`
- Status: implementation complete and final-reviewed
- App URL: `http://127.0.0.1:5173/`
- Active dev server: Vite on `127.0.0.1:5173`, observed listener PID `93444`
- Current date/time recorded: `2026-04-29 20:16:13 +08:00`
- Repo state: this folder is not a git repository

## User Goal

Build a Traditional Chinese interactive map for a western Hokkaido self-drive trip:

- Arrival: 2026-06-25 afternoon
- Departure: 2026-07-03 morning
- Airport pattern: New Chitose round trip
- Route style: slower western Hokkaido route
- Lodging: 3-star+ city hotels / onsen resorts, mid-range budget
- Travel info: weather, route drive time, road/weather/hotel external links

## Implemented Files

Core app:

- `src/main.ts`
- `src/styles.css`
- `src/data/trip.ts`
- `src/ui/map.ts`
- `src/ui/panels.ts`
- `src/ui/state.ts`
- `src/services/weather.ts`
- `src/services/routes.ts`
- `src/services/links.ts`

Tests:

- `tests/trip-data.test.ts`
- `tests/links.test.ts`
- `tests/weather.test.ts`
- `tests/routes.test.ts`
- `tests/state.test.ts`
- `e2e/travel-map.spec.ts`
- `e2e/responsive.spec.ts`

Docs / planning:

- `docs/superpowers/specs/2026-04-29-hokkaido-interactive-map-design.md`
- `docs/superpowers/plans/2026-04-29-hokkaido-interactive-map.md`
- `docs/superpowers/worklogs/2026-04-29-hokkaido-interactive-map-worklog.md`

Runtime / artifacts:

- `logs/dev-server.log`
- `logs/dev-server.err.log`
- `test-results/manual-desktop.png`
- `test-results/manual-630-popup.png`
- `test-results/manual-mobile.png`
- `test-results/gsi-tile-check.png`

## Route And Data Notes

- Trip days cover `2026-06-25` through `2026-07-03`.
- Major places include New Chitose, Sapporo, Mt. Moiwa, Otaru, Yoichi, Shakotan, Niseko, Lake Toya, Showa Shinzan / Usuzan, Noboribetsu, Jigokudani, Lake Shikotsu, and Chitose.
- Lodging candidates are all 3-star+ and grouped by route area.
- Departure day `2026-07-03` has no lodging area and returns no lodging candidates.
- `TripDay` is typed as overnight vs departure day so invalid lodging states are harder to express.

## Key Fixes And Decisions

### Map Tiles

Original Leaflet base layer used:

```ts
https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

This caused visible `403 Access blocked` tiles in the browser because the OSM volunteer tile server required a valid referer usage pattern.

Fixed by switching to Japan GSI tiles:

```ts
https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png
```

Attribution now shows `地理院タイル`.

Verification:

- Live screenshot: `test-results/gsi-tile-check.png`
- 16 tile responses checked from `cyberjapandata.gsi.go.jp`: all HTTP `200`
- No observed requests to `tile.openstreetmap.org`

### Weather Semantics

Open-Meteo integration now avoids mixing future selected-day forecast with current-day temperature/wind.

Current behavior:

- Future trip date uses daily selected-date:
  - `weather_code`
  - `precipitation_probability_max`
  - `temperature_2m_max`
  - `temperature_2m_min`
  - `wind_speed_10m_max`
- Current weather fallback is only used when `targetDate` is today.
- `updatedAt` alone no longer makes a weather payload `loaded`.
- Before forecast window, UI shows `YYYY-MM-DD 尚未進入可預報範圍`.
- Fetch failure shows `天氣資料暫不可用` and keeps map usable.

### Route / Google Maps Order

The `2026-06-27` day must preserve:

```text
札幌 -> 小樽 -> 余市 -> 小樽
```

This was fixed by deriving `DayViewModel.routeNamesZh` from `routeSegmentIds` and each segment's `toPlaceId`, rather than only using `stopIds`.

Google Maps link for `2026-06-27` now uses:

- origin: `札幌`
- destination: `小樽`
- waypoints: `小樽|余市`

### Test Determinism

- E2E aborts OSRM and Open-Meteo requests.
- Weather diagnostic query controls are available only in Vite dev mode via `import.meta.env.DEV`.
- `?weather=fail` forces weather failure in dev.
- `?weatherNow=YYYY-MM-DD` controls forecast-window checks in dev.
- Invalid `weatherNow` input falls back without crashing.

### Async Safety

- `src/main.ts` uses a render sequence guard to prevent stale weather/detail renders after rapid date switching.
- `src/ui/map.ts` uses its own render sequence guard to prevent stale route geometry from mutating the map.

## Verification Evidence

Latest full verification after GSI tile fix:

```powershell
npm run verify
```

Result:

- Unit tests: `5 passed`, `33 tests passed`
- Build: `tsc && vite build` passed
- E2E: `6 passed`

Latest live-server checks:

- `http://127.0.0.1:5173/` returned HTTP `200`
- Listener observed on `127.0.0.1:5173`
- Desktop manual smoke:
  - map tiles loaded
  - route line visible
  - markers visible
  - external links present
  - no horizontal overflow
- Mobile manual smoke:
  - 390px viewport
  - no horizontal overflow
  - 9 day buttons visible
  - map and detail panel visible
- 6/27 live smoke:
  - active date: `2026-06-27`
  - detail heading: `札幌至小樽，延伸余市後返小樽`
  - route text: `札幌 → 小樽 → 余市 → 小樽`
  - Google Maps href includes `waypoints=小樽|余市`

## Review Gates

Superpowers workflow used:

- Brainstorming
- Writing plan
- Subagent-driven implementation / review gates
- Receiving code review
- Verification before completion
- Final acceptance review

Final acceptance review result:

- `FINAL_APPROVED`
- Prior blockers resolved:
  - future weather no longer shows misleading current temperature/wind
  - 6/27 Google Maps route order now preserves Otaru-first loop

## Known Caveats

- This is a local app, not deployed.
- Folder is not a git repo, so there are no commits/branches.
- Live route geometry depends on public OSRM when not blocked; app falls back to built-in route estimates if OSRM fails.
- Weather depends on Open-Meteo when selected dates enter forecast window; app handles not-yet-available and unavailable states.
- Road traffic link is static/generic, not a route-specific traffic API.
- GSI tile service is external and no API key is used.

## Next Chat Prompt

Use this prompt if continuing in a new session:

```text
請從 C:\Users\Jonathan\Documents\travel_map 繼續。先讀 docs/superpowers/worklogs/2026-04-29-hokkaido-interactive-map-worklog.md。這個 Vite/TypeScript/Leaflet 北海道互動地圖已完成並通過 npm run verify。dev server 應該在 http://127.0.0.1:5173/；若斷線，重新執行 npm run dev -- --port 5173。最近修正重點：底圖已從 OSM volunteer tile 換成 GSI tile 以避免 403；天氣未來日期使用 daily forecast，不混用 current；6/27 Google Maps 導航順序保留 札幌 -> 小樽 -> 余市 -> 小樽。請先確認 live UI，再依我的新需求修改。
```
