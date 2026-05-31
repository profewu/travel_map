import type { LodgingCandidate, TripDay } from '../data/trip';
import type { DisasterDataset } from '../data/disaster';
import { buildItineraryDisasterSummary } from '../data/disaster';
import {
  buildGoogleDirectionsUrl,
  buildHotelSearchUrl,
  jmaWarningUrl,
  roadTrafficUrl,
} from '../services/links';
import type { WeatherSummary } from '../services/weather';
import type { ItineraryTableRow } from './itineraryTable';
import type { OverviewRenderSummary, RouteRenderSummary } from './map';
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

const renderBadge = (className: string, label: string): string =>
  `<span class="table-badge ${className}">${escapeHtml(label)}</span>`;

function renderInlineList(items: string[], emptyLabel: string): string {
  if (items.length === 0) {
    return `<span class="muted">${escapeHtml(emptyLabel)}</span>`;
  }

  return items.map((item) => `<span class="table-chip">${escapeHtml(item)}</span>`).join('');
}

function renderTableRoute(row: ItineraryTableRow): string {
  const confirmed = row.lodging.confirmed
    ? `
      <div class="table-confirmed-lodging">
        <p>${renderBadge('badge-lodging', row.lodging.confirmed.statusZh)} <strong>${escapeHtml(
          row.lodging.confirmed.hotelName,
        )}</strong></p>
        <p><span>來源</span>${escapeHtml(row.lodging.confirmed.provider)}</p>
        <p><span>日期</span>入住 ${escapeHtml(
          row.lodging.confirmed.checkInDate,
        )} / 退房 ${escapeHtml(row.lodging.confirmed.checkOutDate)}</p>
      </div>
    `
    : '';

  return `
    <div class="table-route">
      <p><span>起點</span><strong>${escapeHtml(row.route.startNameZh)}</strong></p>
      <p><span>停靠</span><strong>${renderInlineList(row.route.stopNamesZh, '直達')}</strong></p>
      <p><span>終點</span><strong>${escapeHtml(row.route.endNameZh)}</strong></p>
      <div class="table-route-lodging">
        <p>${renderBadge('badge-lodging', '住宿地')} ${escapeHtml(row.lodging.targetZh)}</p>
        ${confirmed}
      </div>
    </div>
  `;
}

function renderTableCsv(row: ItineraryTableRow): string {
  if (row.csvSummary.items.length === 0) {
    return `
      <div class="table-csv empty">
        ${renderBadge('badge-csv', 'CSV')}
        <p>${escapeHtml(row.csvSummary.textZh)}</p>
      </div>
    `;
  }

  return `
    <div class="table-csv">
      ${renderBadge('badge-csv', 'CSV')}
      <ul class="table-csv-list">
        ${row.csvSummary.items
          .map(
            (item) => `
              <li>
                <strong>${escapeHtml(item.placeNameZh)}:</strong>
                ${escapeHtml(item.summaryZh)}
              </li>
            `,
          )
          .join('')}
      </ul>
    </div>
  `;
}

function renderTableActions(row: ItineraryTableRow): string {
  const links = [
    ['Google Maps', row.actions.googleMapsUrl],
    ['JMA', row.actions.jmaUrl],
    ['道路路況', row.actions.roadUrl],
    ['住宿搜尋', row.actions.hotelSearchUrl],
  ] as const;

  return `
    <nav class="itinerary-actions" aria-label="${escapeAttr(row.labelZh)} 外部操作">
      ${links
        .map(
          ([label, href]) => `
            <a href="${escapeAttr(href)}" target="_blank" rel="noreferrer">
              ${escapeHtml(label)}
            </a>
          `,
        )
        .join('')}
    </nav>
  `;
}

export function renderItineraryTable(rows: ItineraryTableRow[]): string {
  return `
    <section class="itinerary-table-page" aria-labelledby="itinerary-table-heading">
      <header class="itinerary-table-header">
        <p class="eyebrow">TRIP SHEET</p>
        <h2 id="itinerary-table-heading">行程總表</h2>
        <p>每天的移動、住宿、CSV 補充與 AI 建議集中成一張可掃描的行程表。</p>
      </header>
      <div class="itinerary-table-scroll">
        <table class="itinerary-table">
          <thead>
            <tr>
              <th scope="col">日期</th>
              <th scope="col">當日標題</th>
              <th scope="col">起點 / 停靠點 / 終點 / 住宿地</th>
              <th scope="col">CSV 景點說明摘要</th>
              <th scope="col">AI 建議景點說明</th>
              <th scope="col">車程 / 公里</th>
              <th scope="col">外部操作</th>
            </tr>
          </thead>
          <tbody>
            ${rows
              .map(
                (row) => `
                  <tr class="itinerary-card" data-date="${escapeAttr(row.date)}">
                    <th scope="row" data-label="日期">
                      <span class="table-date">${escapeHtml(row.date)}</span>
                      <strong>${escapeHtml(row.labelZh)}</strong>
                    </th>
                    <td data-label="當日標題">
                      <strong class="table-title">${escapeHtml(row.titleZh)}</strong>
                    </td>
                    <td data-label="起點 / 停靠點 / 終點 / 住宿地">${renderTableRoute(row)}</td>
                    <td data-label="CSV 景點說明摘要">${renderTableCsv(row)}</td>
                    <td data-label="AI 建議景點說明">
                      <div class="table-ai-note">
                        ${renderBadge('badge-ai', 'AI 建議')}
                        <p>${escapeHtml(row.aiSuggestionZh)}</p>
                      </div>
                    </td>
                    <td data-label="車程 / 公里">
                      <div class="table-drive">
                        <strong>${escapeHtml(row.drive.durationLabelZh)}</strong>
                        <span>${escapeHtml(row.drive.distanceLabelZh)}</span>
                        ${
                          row.drive.hasFatigueRisk
                            ? renderBadge('badge-fatigue', '疲勞風險')
                            : ''
                        }
                      </div>
                    </td>
                    <td data-label="外部操作">${renderTableActions(row)}</td>
                  </tr>
                `,
              )
              .join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

export function renderDisasterPanel(dataset: DisasterDataset): string {
  const summary = buildItineraryDisasterSummary(dataset.itineraryAlerts);
  const epicenter = dataset.epicenter;

  return `
    <section
      id="disaster-page"
      class="disaster-page monitoring-rail"
      data-page="disaster"
      aria-labelledby="disaster-heading"
    >
      <header class="disaster-header">
        <p class="eyebrow">DISASTER MONITOR</p>
        <h2 id="disaster-heading">防災資訊</h2>
        <p>${escapeHtml(dataset.regionNameZh)} / static mock snapshot ${escapeHtml(dataset.asOfJst)}</p>
      </header>

      <section class="disaster-itinerary-summary status-${escapeAttr(summary.status)}">
        <span>${escapeHtml(summary.labelZh)}</span>
        <strong>${escapeHtml(summary.messageZh)}</strong>
      </section>

      <section class="disaster-epicenter-card" aria-label="震央">
        <span class="disaster-marker-sample epicenter-sample" aria-hidden="true">X</span>
        <div>
          <p>震央</p>
          <h3>${escapeHtml(epicenter.nameZh)} M${escapeHtml(String(epicenter.magnitude))}</h3>
          <span>${escapeHtml(epicenter.maxIntensityZh)} / 深度 ${epicenter.depthKm} km</span>
        </div>
      </section>

      <section class="disaster-event-list" aria-label="最近地震列表">
        <div class="disaster-section-heading">
          <h3>最近地震</h3>
          <span>${dataset.events.length} events</span>
        </div>
        ${dataset.events
          .map(
            (event) => `
              <article class="disaster-event status-${escapeAttr(event.status)}" data-disaster-event-id="${escapeAttr(event.id)}">
                <time>${escapeHtml(event.occurredAtJst)}</time>
                <h4>${escapeHtml(event.titleZh)}</h4>
                <p>${escapeHtml(event.summaryZh)}</p>
                <div>
                  <span>${escapeHtml(event.regionZh)}</span>
                  <span>M${escapeHtml(String(event.magnitude))}</span>
                  <span>${escapeHtml(event.maxIntensityZh)}</span>
                </div>
              </article>
            `,
          )
          .join('')}
      </section>

      <section class="disaster-alert-list" aria-label="行程地點附近警示">
        <div class="disaster-section-heading">
          <h3>行程點附近</h3>
          <span>${summary.totalAlertCount} alerts</span>
        </div>
        ${dataset.itineraryAlerts
          .map(
            (alert) => `
              <article class="disaster-place-alert status-${escapeAttr(alert.status)}">
                <strong>${escapeHtml(alert.dayLabelZh)} ${escapeHtml(alert.placeNameZh)}</strong>
                <p>${escapeHtml(alert.messageZh)}</p>
                <span>${escapeHtml(String(alert.distanceKmToEpicenter))} km from epicenter</span>
              </article>
            `,
          )
          .join('')}
      </section>

      <section class="disaster-legend" aria-label="圖例">
        <h3>圖例</h3>
        ${dataset.legend
          .map(
            (item) => `
              <p>
                <span class="disaster-legend-symbol ${escapeAttr(item.markerClass)}" aria-hidden="true"></span>
                <strong>${escapeHtml(item.labelZh)}</strong>
                <span>${escapeHtml(item.descriptionZh)}</span>
              </p>
            `,
          )
          .join('')}
      </section>

      <p class="disaster-source-hint">${escapeHtml(dataset.sourceHintZh)}</p>
    </section>
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

export function renderOverviewMapOverlay(
  summary: OverviewRenderSummary,
): string {
  return `
    <div class="map-overlay" aria-label="全程總覽">
      <div class="glass route-card overview-card">
        <small>全程總覽</small>
        <h3>全部行程點</h3>
        <div class="metrics">
          <div class="metric">
            <span>行程點</span>
            <strong>${summary.totalMarkers}</strong>
          </div>
          <div class="metric">
            <span>CSV 補充</span>
            <strong>${summary.csvMarkers}</strong>
          </div>
          <div class="metric">
            <span>住宿地</span>
            <strong>${summary.lodgingMarkers}</strong>
          </div>
        </div>
        <div class="overview-legend" aria-label="圖例">
          <span><i class="legend-dot legend-regular"></i>一般行程點</span>
          <span><i class="legend-dot legend-csv"></i>CSV 補充</span>
          <span><i class="legend-dot legend-lodging"></i>住宿地</span>
          <span><i class="legend-dot legend-ai"></i>AI 推薦</span>
        </div>
      </div>
      <div class="floating-actions" aria-label="外部檢查">
        <a class="square-action" href="${escapeAttr(jmaWarningUrl)}" target="_blank" rel="noreferrer">JMA</a>
        <a class="square-action" href="${escapeAttr(roadTrafficUrl)}" target="_blank" rel="noreferrer">ROAD</a>
      </div>
    </div>
  `;
}

export function renderOverviewDetailPanel(
  summary: OverviewRenderSummary,
): string {
  const aiIds =
    summary.aiSuggestedLodgingPlaceIds.length > 0
      ? summary.aiSuggestedLodgingPlaceIds.join(', ')
      : '無';

  return `
    <aside class="detail-panel dashboard-right-panel">
      <p class="eyebrow">TRIP OVERVIEW</p>
      <h2>全程總覽</h2>
      <p>地圖已縮放到能容納所有行程點的範圍，不拉到北海道全圖。</p>
      <section class="info-card overview-info-card">
        <h3>圖例</h3>
        <div class="overview-legend overview-legend-panel" aria-label="總覽圖例">
          <span><i class="legend-dot legend-regular"></i>一般行程點：原始行程資料</span>
          <span><i class="legend-dot legend-csv"></i>CSV 補充：細金圈與小徽章</span>
          <span><i class="legend-dot legend-lodging"></i>住宿地：宿字徽章</span>
          <span><i class="legend-dot legend-ai"></i>AI 推薦住宿：高亮 AI 徽章</span>
        </div>
      </section>
      <section class="info-card metric-card">
        <span class="big">${summary.totalMarkers}</span>
        <span>個總覽行程點</span>
        <p>CSV 補充 ${summary.csvMarkers} 個；住宿標註 ${summary.lodgingMarkers} 個。</p>
        <p>AI 推薦住宿候選：${escapeHtml(aiIds)}</p>
      </section>
    </aside>
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
