# Hokkaido Interactive Travel Map Design

## Context

Build a local interactive map for a self-drive trip in western Hokkaido.

- Traveler arrives at New Chitose Airport on the afternoon of 2026-06-25.
- Traveler leaves from New Chitose Airport on the morning of 2026-07-03.
- Route style: slow western Hokkaido loop, not Hakodate and not Furano/Biei.
- Lodging style: mixed city hotels and onsen/resort stays.
- Lodging budget: about JPY 25,000-45,000 per room per night.
- Travel pace: balanced, with one or two primary stops per day plus food, lodging, and weather-aware adjustments.
- UI language: Traditional Chinese by default. Use English or Japanese place names only when they help navigation, search, or source matching.

The app should be a usable trip map first, not a landing page or marketing site.

## Approved Approach

Use a no-API-key interactive map with reliable live weather and external live-check links.

- Leaflet renders the map, markers, popups, and route lines.
- Open-Meteo provides live and forecast weather.
- OSRM may provide estimated route geometry and travel time when available.
- Built-in route fallbacks prevent the map from becoming blank if OSRM fails.
- JMA weather warnings, JARTIC/NEXCO road traffic, Google Maps navigation, and lodging searches are exposed as external action links instead of being falsely presented as fully embedded real-time data.

Primary references:

- Open-Meteo Forecast API: <https://open-meteo.com/en/docs>
- Leaflet reference: <https://leafletjs.com/reference>
- OSRM API documentation: <https://project-osrm.org/docs/v26.4.0/>
- Japan Meteorological Agency: <https://www.jma.go.jp/>
- NEXCO Central traffic information: <https://www.c-nexco.co.jp/en/jam/>

## Route Plan

The itinerary is fixed around a slow western Hokkaido route:

| Date | Overnight Area | Route Focus | Lodging Type |
| --- | --- | --- | --- |
| 2026-06-25 | Sapporo | New Chitose afternoon arrival, rental car pickup, Sapporo transfer | 3-4 star city hotel |
| 2026-06-26 | Sapporo | Sapporo city, food, optional Mt. Moiwa evening view | 3-4 star city hotel |
| 2026-06-27 | Otaru | Sapporo to Otaru and Yoichi, canal, seafood, Nikka Whisky Yoichi | 3-4 star city hotel |
| 2026-06-28 | Niseko | Otaru to Shakotan coast, then Niseko | Resort or onsen-capable hotel |
| 2026-06-29 | Lake Toya | Slow Niseko morning, Lake Toya transfer and lakefront stay | Onsen or lake-view hotel |
| 2026-06-30 | Noboribetsu | Lake Toya, Showa Shinzan, Usuzan, Noboribetsu | Onsen ryokan or resort hotel |
| 2026-07-01 | Lake Shikotsu or Chitose | Noboribetsu Jigokudani, onsen town, transfer toward airport side | Lake/airport-side hotel |
| 2026-07-02 | New Chitose or Chitose | Shikotsu/Chitose buffer day, shopping, rental car return preparation | Airport-area 3-4 star hotel |
| 2026-07-03 | Departure | Morning departure from New Chitose Airport | None |

Daily cards should include estimated drive time, key stops, lodging target, weather badge, and external confirmation actions.

## Interface

The first screen is the working map interface.

### Layout

- Day list on the left or top depending on viewport width.
- Leaflet map as the main surface.
- Day detail panel on the right or below the map.
- Map-first layout is approved.
- The desktop target uses a three-region layout: date list, map, detail panel.
- The mobile target stacks controls above or below the map and keeps the map usable without horizontal scrolling.

### Interactions

- Selecting a date focuses the map on that day and updates the detail panel.
- Selecting a marker opens a popup with place details, stop guidance, parking notes where useful, and external links.
- Selecting a route segment shows estimated time, distance if available, and fallback notes.
- Weather badges show temperature, precipitation probability or rain signal, wind, and update time.
- Lodging filters separate city hotels, onsen/resort stays, and airport-area stays.
- External buttons open Google Maps, JMA warnings, road traffic sources, and lodging search pages.

### UI Text

All primary labels, buttons, warnings, and itinerary text are Traditional Chinese.

Examples:

- `每日行程`
- `選取日期`
- `預估行車`
- `檢查 JMA 天氣警示`
- `檢查即時道路路況`
- `搜尋 3 星以上住宿`
- `天氣資料暫不可用`

## Data Model

Use structured local data instead of ad hoc DOM strings.

### `tripData`

Trip-level route data:

- date
- title
- start place id
- end place id
- primary stop ids
- lodging area id, optional only for departure days with no overnight lodging
- manual fallback drive estimate
- route segment ids
- notes

### `places`

Map marker data:

- stable id
- Traditional Chinese name
- optional English/Japanese name
- latitude and longitude
- category
- description
- suggested duration
- parking or access notes
- external search links

### `lodgingCandidates`

Lodging recommendation data:

- area
- hotel name
- hotel type
- minimum star level, when known from public hotel listings
- why it fits this route
- parking note
- budget risk
- booking/search link

The app should not claim live availability or live pricing unless a licensed lodging API is added later. It should present candidates and search links.

### `weatherService`

Fetch weather from Open-Meteo by day focus location.

Display:

- current or forecast temperature
- precipitation probability or precipitation signal when available
- wind speed
- weather code interpreted into a short Chinese label
- update time

### `routeService`

Use OSRM for estimated route geometry and duration where possible.

Fallback:

- draw a point-to-point polyline between route waypoints
- show manually curated drive estimates
- show an explicit fallback note

### `externalLiveChecks`

External links should be generated from the selected day and area:

- Google Maps navigation/search
- JMA weather and warning pages
- JARTIC/NEXCO traffic pages
- hotel search links for the relevant overnight area and travel dates

## Error Handling

- If weather fetch succeeds, show data and update time.
- If weather fetch fails, keep the map and itinerary visible, show `天氣資料暫不可用`, and provide a retry action.
- If OSRM succeeds, use route geometry and estimated drive time.
- If OSRM fails, use built-in route points and manual estimated drive time.
- If map tiles are slow, show the itinerary and map attribution/loading state without blocking the rest of the app.
- If an external source is unavailable, keep the link visible so the traveler can retry or open it separately.

## Testing and Verification

Verification should cover:

- local dev server starts successfully
- page loads without JavaScript errors
- Leaflet map is visible and nonblank
- route lines render
- markers render and popups open
- all dates can be selected
- day detail panel updates when dates are selected
- weather success path displays data and update time
- weather failure path displays fallback UI without breaking the trip map
- OSRM failure path keeps fallback route lines and manual drive time
- external links have usable URLs
- desktop layout does not overlap
- mobile layout does not overlap or require horizontal scrolling
- build or lint command passes when the chosen stack provides it

## Delivery

The implementation should produce a local app that Jonathan can open and use.

- If a dev server is required, start it and provide the local URL.
- If a static HTML build is sufficient, provide the local file path.
- Keep generated design and implementation docs under `docs/superpowers/`.
- Do not initialize git or commit unless Jonathan asks for repository setup.

## Out of Scope for Initial Version

- Embedded real-time lodging availability and pricing.
- Embedded paid Google Maps Places/Routes data.
- Fully automated JARTIC or JMA warning ingestion beyond practical external links.
- Hakodate, Furano, Biei, or eastern Hokkaido route variants.
- Multi-language UI beyond Traditional Chinese with navigation-oriented English/Japanese place names.
