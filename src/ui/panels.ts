import type { LodgingCandidate, TripDay } from '../data/trip';
import {
  buildGoogleDirectionsUrl,
  buildHotelSearchUrl,
  jmaWarningUrl,
  roadTrafficUrl,
} from '../services/links';
import type { WeatherSummary } from '../services/weather';
import type { RouteRenderSummary } from './map';
import type { DayViewModel } from './state';

const escapeHtml = (value: string): string =>
  value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

const escapeAttr = escapeHtml;

const formatValue = (value: string | number | undefined, fallback = '-'): string =>
  value === undefined ? fallback : escapeHtml(String(value));

interface DayActionUrls {
  directionsUrl: string;
  hotelUrl: string;
}

function buildDayActionUrls(vm: DayViewModel, day: TripDay): DayActionUrls {
  const routeNames = vm.routeNamesZh;

  return {
    directionsUrl: buildGoogleDirectionsUrl({
      origin: vm.startNameZh,
      destination: vm.endNameZh,
      waypoints: routeNames.slice(1, -1),
    }),
    hotelUrl: buildHotelSearchUrl(
      `${vm.endNameZh} 3 星以上住宿`,
      day.date,
      nextDate(day.date),
    ),
  };
}

function formatDuration(minutes: number): string {
  if (minutes <= 0) {
    return '-';
  }

  return `${Math.round((minutes / 60) * 10) / 10} hr`;
}

function formatDistance(km: number): string {
  if (km <= 0) {
    return '-';
  }

  return `${Math.round(km * 10) / 10} km`;
}

function formatTemperature(summary: WeatherSummary): string {
  if (
    summary.temperatureMinC !== undefined &&
    summary.temperatureMaxC !== undefined
  ) {
    return `${escapeHtml(String(summary.temperatureMinC))}-${escapeHtml(
      String(summary.temperatureMaxC),
    )} C`;
  }

  if (summary.temperatureC !== undefined) {
    return `${escapeHtml(String(summary.temperatureC))} C`;
  }

  return '-';
}

function routeStatusLabel(status: RouteRenderSummary['status']): string {
  if (status === 'live') {
    return 'OSRM live';
  }

  if (status === 'fallback') {
    return '本地 fallback';
  }

  return '無路線';
}

function renderTimeline(routeNames: string[]): string {
  if (routeNames.length === 0) {
    return '<p class="empty-note">今日沒有路線節點。</p>';
  }

  return routeNames
    .map((name, index) => {
      const label =
        index === 0
          ? '起點'
          : index === routeNames.length - 1
            ? '終點'
            : `停靠 ${index}`;

      return `
        <article class="timeline-card">
          <small>${label}</small>
          <strong>${escapeHtml(name)}</strong>
          <p>${index === 0 ? '當日出發節點' : '接續導航節點'}</p>
        </article>
      `;
    })
    .join('');
}

function renderMapcodeButton(mapcode?: string, phone?: string): string {
  if (!mapcode && !phone) return '';
  const label = mapcode ? `MAPCODE: ${mapcode}` : `TEL: ${phone}`;
  const copyVal = mapcode || phone || '';
  return `
    <div class="mapcode-copy-row">
      <code>${escapeHtml(label)}</code>
      <button class="copy-btn" type="button" data-copy="${escapeAttr(copyVal)}">複製</button>
    </div>
  `;
}

export function renderDayButtons(days: TripDay[], selectedDate: string): string {
  return `
    <section class="day-list" aria-label="每日行程">
      <p class="panel-kicker">DAY INDEX</p>
      <h2>每日行程</h2>
      <div class="day-buttons">
        ${days
          .map(
            (day) => `
              <button
                class="day-button ${day.date === selectedDate ? 'active' : ''}"
                type="button"
                data-date="${escapeAttr(day.date)}"
                aria-pressed="${day.date === selectedDate ? 'true' : 'false'}"
              >
                <span>${escapeHtml(day.labelZh)}</span>
                <strong>${escapeHtml(day.titleZh)}</strong>
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
        <h3>天氣</h3>
        <p>
          ${escapeHtml(summary.weatherLabelZh ?? '資料更新中')}
          <span>${formatTemperature(summary)}</span>
          <span>降雨 ${formatValue(summary.precipitationProbabilityMax)}%</span>
          <span>風速 ${formatValue(summary.windSpeedKmh)} km/h</span>
        </p>
        <small>更新 ${formatValue(summary.updatedAt, '未提供')}</small>
      </section>
    `;
  }

  return `
    <section class="weather-box warning">
      <h3>天氣</h3>
      <p>${escapeHtml(summary.messageZh)}</p>
      <button class="retry-weather" type="button">重新讀取天氣</button>
    </section>
  `;
}

export function renderMapOverlay(input: {
  vm: DayViewModel;
  day: TripDay;
  routeSummary: RouteRenderSummary;
}): string {
  const { directionsUrl } = buildDayActionUrls(input.vm, input.day);
  const routeNames = input.vm.routeNamesZh;
  const routeLabel = `${input.vm.startNameZh} -> ${input.vm.endNameZh}`;
  const status = routeStatusLabel(input.routeSummary.status);

  return `
    <div class="map-overlay" aria-label="今日路線摘要">
      <div class="glass route-card">
        <small>今日路線摘要</small>
        <h3>${escapeHtml(routeLabel)}</h3>
        <div class="status-row">
          <span class="mini-pill route-status route-status-${escapeAttr(input.routeSummary.status)}">
            ${escapeHtml(status)}
          </span>
        </div>
        <div class="metrics">
          <div class="metric">
            <span>時間</span>
            <strong>${escapeHtml(formatDuration(input.routeSummary.durationMinutes))}</strong>
          </div>
          <div class="metric">
            <span>距離</span>
            <strong>${escapeHtml(formatDistance(input.routeSummary.distanceKm))}</strong>
          </div>
          <div class="metric">
            <span>節點</span>
            <strong>${routeNames.length}</strong>
          </div>
        </div>
      </div>
      <div class="floating-actions" aria-label="外部檢查捷徑">
        <a class="square-action" href="${escapeAttr(jmaWarningUrl)}" target="_blank" rel="noreferrer">JMA</a>
        <a class="square-action" href="${escapeAttr(roadTrafficUrl)}" target="_blank" rel="noreferrer">ROAD</a>
      </div>
    </div>
    <div class="glass bottom-sheet">
      <div>
        <strong>Google Maps 外部導航</strong>
        <span>保留外部 URL 交接，不改用 Google API。</span>
      </div>
      <div>
        <strong>${escapeHtml(status)}</strong>
        <span>${escapeHtml(input.routeSummary.noteZh)}</span>
      </div>
      <a class="google-btn" href="${escapeAttr(directionsUrl)}" target="_blank" rel="noreferrer">
        開啟 Google Maps
      </a>
    </div>
  `;
}

export function renderLodging(candidates: LodgingCandidate[]): string {
  const content =
    candidates.length > 0
      ? candidates
          .map(
            (hotel) => `
              <article class="hotel-card">
                <h4>${escapeHtml(hotel.nameZh)}</h4>
                <p>${hotel.starLevel} 星 / ${escapeHtml(hotel.fitZh)}</p>
                <p>${escapeHtml(hotel.parkingZh)}</p>
                <p>${escapeHtml(hotel.budgetRiskZh)}</p>
                ${renderMapcodeButton(hotel.mapcode, hotel.phone)}
                <a href="${escapeAttr(hotel.searchUrl)}" target="_blank" rel="noreferrer">
                  查看住宿
                </a>
              </article>
            `,
          )
          .join('')
      : '<p class="empty-note">今日沒有住宿候選。</p>';

  return `
    <section class="lodging-list">
      <h3>住宿候選</h3>
      ${content}
    </section>
  `;
}

export function renderDetailPanel(input: {
  vm: DayViewModel;
  day: TripDay;
  weather: WeatherSummary;
}): string {
  const routeNames = input.vm.routeNamesZh;
  const { directionsUrl, hotelUrl } = buildDayActionUrls(input.vm, input.day);

  const fatigueWarning = input.vm.hasFatigueRisk
    ? `<div class="fatigue-warning" role="alert">
         長途駕駛提醒：${input.vm.totalKm}km / ${Math.round(
        (input.vm.totalMinutes / 60) * 10,
      ) / 10}hr，請預留休息與備案。
       </div>`
    : '';

  return `
    <aside class="detail-panel dashboard-right-panel">
      ${fatigueWarning}
      <p class="eyebrow">旅程檢查 ${escapeHtml(input.vm.labelZh)}</p>
      <h2>${escapeHtml(input.vm.titleZh)}</h2>
      <p>${escapeHtml(input.vm.summaryZh)}</p>
      <section class="info-card metric-card" aria-label="駕駛距離">
        <span class="big">${Math.round(input.vm.totalKm)}</span>
        <span>km 預估駕駛距離</span>
        <p>${escapeHtml(input.vm.driveNoteZh)}</p>
      </section>
      ${renderWeatherBox(input.weather)}
      <section class="info-card">
        <h3>住宿</h3>
        <p>${escapeHtml(input.vm.lodgingTargetZh)}</p>
      </section>
      <nav class="action-grid" aria-label="外部檢查">
        <a class="google-action" href="${escapeAttr(directionsUrl)}" target="_blank" rel="noreferrer">Google Maps 導航</a>
        <a href="${escapeAttr(jmaWarningUrl)}" target="_blank" rel="noreferrer">JMA 天氣警示</a>
        <a href="${escapeAttr(roadTrafficUrl)}" target="_blank" rel="noreferrer">道路路況</a>
        <a href="${escapeAttr(hotelUrl)}" target="_blank" rel="noreferrer">搜尋 3 星以上住宿</a>
      </nav>
      <section class="timeline-list" aria-label="行程時間線">
        <h3>行程時間線</h3>
        ${renderTimeline(routeNames)}
      </section>
      ${renderLodging(input.vm.lodgingCandidates)}
    </aside>
  `;
}

function nextDate(date: string): string {
  const [year, month, day] = date.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day + 1)).toISOString().slice(0, 10);
}
