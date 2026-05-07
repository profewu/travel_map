import './styles.css';
import { lodgingCandidates, places, routeSegments, tripDays } from './data/trip';
import { fetchWeatherSummary } from './services/weather';
import { createTripMap } from './ui/map';
import {
  renderDayButtons,
  renderDetailPanel,
  renderMapOverlay,
} from './ui/panels';
import { buildDayViewModel, getInitialDayId, selectDay } from './ui/state';

function requireElement<T extends HTMLElement>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) {
    throw new Error(`Required layout root ${selector} not found`);
  }
  return element;
}

const app = requireElement<HTMLDivElement>('#app');

let selectedDate = getInitialDayId(tripDays);
let selectedPlaceId = tripDays[0]?.startPlaceId ?? '';

app.innerHTML = `
  <main class="app-shell dashboard-shell">
    <header class="topbar dashboard-topbar">
      <div class="brand-block">
        <span class="brand-mark" aria-hidden="true">北</span>
        <div>
          <p class="eyebrow">2026/6/25 - 2026/7/3</p>
          <h1>北海道 TRIP MAP</h1>
        </div>
      </div>
      <nav class="mode-tabs" aria-label="顯示模式">
        <span class="mode-tab active">總覽</span>
        <span class="mode-tab">路線</span>
        <span class="mode-tab">檢查</span>
      </nav>
      <div class="status-pills" aria-label="目前狀態">
        <span class="pill">GSI pale map</span>
        <span class="pill muted">Google Maps 外部導航</span>
      </div>
    </header>
    <div class="workspace dashboard-layout">
      <div id="days"></div>
      <section class="map-panel map-stage" aria-label="旅行地圖">
        <div id="map" class="map"></div>
        <div id="map-overlay" class="map-overlay-root"></div>
      </section>
      <div id="details"></div>
    </div>
  </main>
`;

const daysRoot = requireElement<HTMLDivElement>('#days');
const mapRoot = requireElement<HTMLDivElement>('#map');
const mapOverlayRoot = requireElement<HTMLDivElement>('#map-overlay');
const detailsRoot = requireElement<HTMLDivElement>('#details');

const map = createTripMap(mapRoot, places, routeSegments, (place) => {
  selectedPlaceId = place.id;
  document.documentElement.dataset.selectedPlace = selectedPlaceId;
});

let renderSequence = 0;

const allowWeatherDebugControls = import.meta.env.DEV;

function weatherFetcher(): typeof fetch | undefined {
  if (!allowWeatherDebugControls) {
    return undefined;
  }

  const params = new URLSearchParams(window.location.search);
  if (params.get('weather') !== 'fail') {
    return undefined;
  }

  return (() =>
    Promise.reject(new Error('forced weather failure'))) as unknown as typeof fetch;
}

function weatherNow(): Date | undefined {
  if (!allowWeatherDebugControls) {
    return undefined;
  }

  const params = new URLSearchParams(window.location.search);
  const value = params.get('weatherNow');
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return undefined;
  }

  const parsed = new Date(`${value}T09:00:00+09:00`);
  return Number.isNaN(parsed.getTime()) ? undefined : parsed;
}

async function render(): Promise<void> {
  const sequence = ++renderSequence;
  const day = selectDay(selectedDate, tripDays);
  const weatherPlace = places[day.weatherPlaceId];
  const weather = await fetchWeatherSummary({
    lat: weatherPlace.lat,
    lng: weatherPlace.lng,
    targetDate: day.date,
    now: weatherNow(),
    fetcher: weatherFetcher(),
  });

  if (sequence !== renderSequence) {
    return;
  }

  const vm = buildDayViewModel(day, places, lodgingCandidates, routeSegments);

  daysRoot.innerHTML = renderDayButtons(tripDays, day.date);
  detailsRoot.innerHTML = renderDetailPanel({ vm, day, weather });
  mapOverlayRoot.innerHTML = '';

  const routeSummary = await map.renderDay(day);

  if (sequence !== renderSequence) {
    return;
  }

  mapOverlayRoot.innerHTML = renderMapOverlay({ vm, day, routeSummary });

  daysRoot.querySelectorAll<HTMLButtonElement>('.day-button').forEach((button) => {
    button.addEventListener('click', () => {
      selectedDate = button.dataset.date ?? selectedDate;
      void render();
    });
  });

  detailsRoot
    .querySelector<HTMLButtonElement>('.retry-weather')
    ?.addEventListener('click', () => {
      void render();
    });

  document.documentElement.dataset.selectedPlace = selectedPlaceId;
}

document.addEventListener('click', (e) => {
  const btn = (e.target as HTMLElement).closest('.copy-btn');
  if (btn instanceof HTMLButtonElement && btn.dataset.copy) {
    void navigator.clipboard.writeText(btn.dataset.copy).then(() => {
      const originalText = btn.textContent;
      btn.textContent = '已複製';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.textContent = originalText;
        btn.classList.remove('copied');
      }, 2000);
    });
  }
});

void render();
