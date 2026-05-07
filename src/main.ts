import './styles.css';
import { lodgingCandidates, places, routeSegments, tripDays } from './data/trip';
import { fetchWeatherSummary } from './services/weather';
import { createTripMap } from './ui/map';
import { renderDayButtons, renderDetailPanel } from './ui/panels';
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
  <main class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">2026/6/25 - 2026/7/3</p>
        <h1>北海道西半部自駕地圖</h1>
      </div>
      <p class="trip-summary">新千歲、惠庭、支笏湖、登別、白老、室蘭、洞爺湖、小樽、札幌，最後由薄野搭機場巴士返程。</p>
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

const daysRoot = requireElement<HTMLDivElement>('#days');
const mapRoot = requireElement<HTMLDivElement>('#map');
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
  await map.renderDay(day);

  if (sequence !== renderSequence) {
    return;
  }

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

// Global Event Listeners
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
