import './styles.css';
import { csvPlaceSummariesById } from './data/csvPlaceSummaries';
import { staticDisasterDataset } from './data/disaster';
import { lodgingCandidates, places, routeSegments, tripDays } from './data/trip';
import { fetchWeatherSummary } from './services/weather';
import { createTripMap } from './ui/map';
import {
  renderDayButtons,
  renderDetailPanel,
  renderDisasterPanel,
  renderItineraryTable,
  renderMapOverlay,
  renderOverviewDetailPanel,
  renderOverviewMapOverlay,
} from './ui/panels';
import { clearTravelNotes, loadTravelNotes, saveTravelNotes } from './ui/notes';
import { buildItineraryTableRows } from './ui/itineraryTable';
import { isAppMode, topNavigationItems, type AppMode } from './ui/navigation';
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
let selectedMode: AppMode = 'route';

function renderTopNavigation(): string {
  return topNavigationItems
    .map((item) => {
      if (item.kind === 'action') {
        return `
          <button type="button" class="mode-tab notes-open-btn" id="notes-open-button">
            ${item.labelZh}
          </button>
        `;
      }

      if (item.kind === 'external') {
        return `
          <a class="mode-tab report-link" href="${item.href}" target="_blank" rel="noreferrer">
            ${item.labelZh}
          </a>
        `;
      }

      return `
        <button
          class="mode-tab ${item.mode === selectedMode ? 'active' : ''}"
          type="button"
          data-mode="${item.mode}"
          data-testid="mode-tab-${item.mode}"
          aria-pressed="${item.mode === selectedMode ? 'true' : 'false'}"
        >
          ${item.labelZh}
        </button>
      `;
    })
    .join('');
}

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
        ${renderTopNavigation()}
      </nav>
    </header>
    <dialog
      class="notes-dialog"
      id="travel-notes-dialog"
      aria-labelledby="travel-notes-heading"
    >
      <form method="dialog" class="notes-dialog-content">
        <h2 id="travel-notes-heading">待變更事項筆記</h2>
        <label class="notes-label" for="travel-notes-textarea">待變更事項</label>
        <textarea id="travel-notes-textarea" class="notes-textarea" rows="8"></textarea>
        <div class="notes-actions">
          <button type="button" class="notes-action-btn" data-action="clear">清除</button>
          <div class="notes-actions-right">
            <button type="button" class="notes-action-btn" data-action="cancel">取消</button>
            <button type="button" class="notes-action-btn primary" data-action="save">儲存</button>
          </div>
        </div>
      </form>
    </dialog>
    <div class="workspace dashboard-layout">
      <div id="days"></div>
      <section class="map-panel map-stage" aria-label="旅行地圖">
        <div id="map" class="map"></div>
        <div id="map-overlay" class="map-overlay-root"></div>
      </section>
      <div id="details"></div>
      <section id="table-page" class="table-page" hidden></section>
      <section id="disaster-page-root" class="disaster-page-root" hidden></section>
    </div>
  </main>
`;

const daysRoot = requireElement<HTMLDivElement>('#days');
const workspaceRoot = requireElement<HTMLElement>('.workspace');
const mapRoot = requireElement<HTMLDivElement>('#map');
const mapOverlayRoot = requireElement<HTMLDivElement>('#map-overlay');
const detailsRoot = requireElement<HTMLDivElement>('#details');
const tableRoot = requireElement<HTMLElement>('#table-page');
const disasterRoot = requireElement<HTMLElement>('#disaster-page-root');
const modeTabsRoot = requireElement<HTMLElement>('.mode-tabs');
const notesOpenButton = requireElement<HTMLButtonElement>('#notes-open-button');
const notesDialog = requireElement<HTMLDialogElement>('#travel-notes-dialog');
const notesTextarea = requireElement<HTMLTextAreaElement>('#travel-notes-textarea');

const map = createTripMap(mapRoot, places, routeSegments, (place) => {
  selectedPlaceId = place.id;
  document.documentElement.dataset.selectedPlace = selectedPlaceId;
}, csvPlaceSummariesById);

let renderSequence = 0;

const allowWeatherDebugControls = import.meta.env.DEV;

modeTabsRoot.addEventListener('click', (event) => {
  const button = (event.target as HTMLElement).closest<HTMLButtonElement>(
    '.mode-tab[data-mode]',
  );
  if (!button) {
    return;
  }

  const mode = button.dataset.mode;
  if (isAppMode(mode)) {
    selectedMode = mode;
    void render();
  }
});

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

function syncModeTabs(): void {
  modeTabsRoot
    .querySelectorAll<HTMLButtonElement>('.mode-tab[data-mode]')
    .forEach((button) => {
      const isActive = button.dataset.mode === selectedMode;
      button.classList.toggle('active', isActive);
      button.setAttribute('aria-pressed', String(isActive));
    });
}

async function render(): Promise<void> {
  const sequence = ++renderSequence;
  const day = selectDay(selectedDate, tripDays);

  syncModeTabs();
  const isTableMode = selectedMode === 'table';
  const isDisasterMode = selectedMode === 'disaster';
  workspaceRoot.classList.toggle('table-mode', isTableMode);
  workspaceRoot.classList.toggle('disaster-mode', isDisasterMode);
  app.querySelector('.dashboard-shell')?.classList.toggle('disaster-mode', isDisasterMode);
  tableRoot.hidden = !isTableMode;
  disasterRoot.hidden = !isDisasterMode;
  mapOverlayRoot.innerHTML = '';

  if (isTableMode) {
    daysRoot.innerHTML = '';
    detailsRoot.innerHTML = '';
    disasterRoot.innerHTML = '';
    tableRoot.innerHTML = renderItineraryTable(
      buildItineraryTableRows({
        days: tripDays,
        places,
        routeSegments,
        lodgingCandidates,
        csvPlaceSummaries: csvPlaceSummariesById,
      }),
    );

    document.documentElement.dataset.selectedPlace = selectedPlaceId;
    document.documentElement.dataset.mapMode = selectedMode;
    return;
  }

  if (isDisasterMode) {
    daysRoot.innerHTML = '';
    detailsRoot.innerHTML = '';
    tableRoot.innerHTML = '';
    map.renderDisaster(staticDisasterDataset);
    disasterRoot.innerHTML = renderDisasterPanel(staticDisasterDataset);

    document.documentElement.dataset.selectedPlace = selectedPlaceId;
    document.documentElement.dataset.mapMode = selectedMode;
    return;
  }

  daysRoot.innerHTML = renderDayButtons(tripDays, day.date);

  if (selectedMode === 'overview') {
    const overviewSummary = map.renderOverview(tripDays);
    detailsRoot.innerHTML = renderOverviewDetailPanel(overviewSummary);
    mapOverlayRoot.innerHTML = renderOverviewMapOverlay(overviewSummary);

    daysRoot.querySelectorAll<HTMLButtonElement>('.day-button').forEach((button) => {
      button.addEventListener('click', () => {
        selectedDate = button.dataset.date ?? selectedDate;
        selectedMode = 'route';
        void render();
      });
    });

    document.documentElement.dataset.selectedPlace = selectedPlaceId;
    document.documentElement.dataset.mapMode = selectedMode;
    return;
  }

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

  detailsRoot.innerHTML = renderDetailPanel({ vm, day, weather });

  const routeSummary = await map.renderDay(day);

  if (sequence !== renderSequence) {
    return;
  }

  mapOverlayRoot.innerHTML = renderMapOverlay({ vm, day, routeSummary });

  daysRoot.querySelectorAll<HTMLButtonElement>('.day-button').forEach((button) => {
    button.addEventListener('click', () => {
      selectedDate = button.dataset.date ?? selectedDate;
      selectedMode = 'route';
      void render();
    });
  });

  detailsRoot
    .querySelector<HTMLButtonElement>('.retry-weather')
    ?.addEventListener('click', () => {
      void render();
    });

  document.documentElement.dataset.selectedPlace = selectedPlaceId;
  document.documentElement.dataset.mapMode = selectedMode;
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

notesOpenButton.addEventListener('click', () => {
  notesTextarea.value = loadTravelNotes();
  notesDialog.showModal();
  notesTextarea.focus();
});

notesDialog.addEventListener('click', (event) => {
  if (event.target === notesDialog) {
    notesDialog.close();
  }
});

notesDialog
  .querySelector<HTMLButtonElement>('[data-action="save"]')
  ?.addEventListener('click', () => {
    saveTravelNotes(notesTextarea.value);
    notesDialog.close();
  });

notesDialog
  .querySelector<HTMLButtonElement>('[data-action="clear"]')
  ?.addEventListener('click', () => {
    clearTravelNotes();
    notesTextarea.value = '';
    notesTextarea.focus();
  });

notesDialog
  .querySelector<HTMLButtonElement>('[data-action="cancel"]')
  ?.addEventListener('click', () => {
    notesDialog.close();
  });

void render();
