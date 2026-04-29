import type { LodgingCandidate, TripDay } from '../data/trip';
import {
  buildGoogleDirectionsUrl,
  buildHotelSearchUrl,
  jmaWarningUrl,
  roadTrafficUrl,
} from '../services/links';
import type { WeatherSummary } from '../services/weather';
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

export function renderDayButtons(days: TripDay[], selectedDate: string): string {
  return `
    <section class="day-list" aria-label="每日行程">
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
        <h3>天氣資料</h3>
        <p>
          ${escapeHtml(summary.weatherLabelZh ?? '天氣狀態未分類')}，
          ${formatTemperature(summary)}，
          降雨 ${formatValue(summary.precipitationProbabilityMax)}%，
          風速 ${formatValue(summary.windSpeedKmh)} km/h
        </p>
        <small>更新時間：${formatValue(summary.updatedAt, '未提供')}</small>
      </section>
    `;
  }

  return `
    <section class="weather-box warning">
      <h3>天氣資料</h3>
      <p>${escapeHtml(summary.messageZh)}</p>
      <button class="retry-weather" type="button">重新整理天氣</button>
    </section>
  `;
}

function formatTemperature(summary: WeatherSummary): string {
  if (
    summary.temperatureMinC !== undefined &&
    summary.temperatureMaxC !== undefined
  ) {
    return `氣溫 ${escapeHtml(String(summary.temperatureMinC))}-${escapeHtml(
      String(summary.temperatureMaxC),
    )}°C`;
  }

  if (summary.temperatureC !== undefined) {
    return `${escapeHtml(String(summary.temperatureC))}°C`;
  }

  return '氣溫 -°C';
}

export function renderLodging(candidates: LodgingCandidate[]): string {
  const content =
    candidates.length > 0
      ? candidates
          .map(
            (hotel) => `
              <article class="hotel-card">
                <h4>${escapeHtml(hotel.nameZh)}</h4>
                <p>${hotel.starLevel} 星以上 / ${escapeHtml(hotel.fitZh)}</p>
                <p>${escapeHtml(hotel.parkingZh)}</p>
                <p>${escapeHtml(hotel.budgetRiskZh)}</p>
                <a href="${escapeAttr(hotel.searchUrl)}" target="_blank" rel="noreferrer">
                  查看住宿搜尋
                </a>
              </article>
            `,
          )
          .join('')
      : '<p class="empty-note">本日不安排住宿候選。</p>';

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
  const directionsUrl = buildGoogleDirectionsUrl({
    origin: input.vm.startNameZh,
    destination: input.vm.endNameZh,
    waypoints: routeNames.slice(1, -1),
  });
  const hotelUrl = buildHotelSearchUrl(
    `${input.vm.endNameZh} 3星以上 住宿`,
    input.day.date,
    nextDate(input.day.date),
  );

  return `
    <aside class="detail-panel">
      <p class="eyebrow">選取日期 ${escapeHtml(input.vm.labelZh)}</p>
      <h2>${escapeHtml(input.vm.titleZh)}</h2>
      <p>${escapeHtml(input.vm.summaryZh)}</p>
      <dl>
        <dt>路線</dt>
        <dd>${escapeHtml(routeNames.join(' → '))}</dd>
        <dt>預估行車</dt>
        <dd>${escapeHtml(input.vm.driveNoteZh)}</dd>
        <dt>住宿目標</dt>
        <dd>${escapeHtml(input.vm.lodgingTargetZh)}</dd>
      </dl>
      ${renderWeatherBox(input.weather)}
      <nav class="action-grid" aria-label="外部即時檢查">
        <a href="${escapeAttr(directionsUrl)}" target="_blank" rel="noreferrer">開啟 Google Maps</a>
        <a href="${escapeAttr(jmaWarningUrl)}" target="_blank" rel="noreferrer">檢查 JMA 天氣警示</a>
        <a href="${escapeAttr(roadTrafficUrl)}" target="_blank" rel="noreferrer">檢查即時道路路況</a>
        <a href="${escapeAttr(hotelUrl)}" target="_blank" rel="noreferrer">搜尋 3 星以上住宿</a>
      </nav>
      ${renderLodging(input.vm.lodgingCandidates)}
    </aside>
  `;
}

function nextDate(date: string): string {
  const [year, month, day] = date.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day + 1)).toISOString().slice(0, 10);
}
