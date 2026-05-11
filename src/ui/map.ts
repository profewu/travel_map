import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { CsvPlaceSummary } from '../data/csvPlaceSummaries';
import { aiSuggestedLodgingPlaceByDate } from '../data/lodgingPolicy';
import type { Place, RouteSegment, TripDay } from '../data/trip';
import { fetchRouteGeometry } from '../services/routes';

export interface MapController {
  renderDay(day: TripDay): Promise<RouteRenderSummary>;
  renderOverview(days: TripDay[]): OverviewRenderSummary;
}

export interface RouteRenderSummary {
  status: 'live' | 'fallback' | 'empty';
  durationMinutes: number;
  distanceKm: number;
  noteZh: string;
}

export type LodgingRole = 'none' | 'lodging' | 'ai-suggested';

export interface OverviewMarker {
  placeId: string;
  dayLabels: string[];
  isCsvPlace: boolean;
  lodgingRole: LodgingRole;
}

export interface OverviewRenderSummary {
  totalMarkers: number;
  csvMarkers: number;
  lodgingMarkers: number;
  aiSuggestedLodgingPlaceIds: string[];
}

interface TileLayerConfig {
  url: string;
  className: string;
  attribution: string;
  maxZoom: number;
}

interface StrokeStyle {
  color: string;
  weight: number;
  opacity: number;
  dashArray?: string;
}

const gsiTileAttribution =
  '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noreferrer">地理院タイル</a>';

export const contourDetailZoomThreshold = 12;

export const mapTilePolicy: Readonly<{
  base: TileLayerConfig;
  contourDetail: TileLayerConfig;
}> = {
  base: {
    url: 'https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
    className: 'gsi-pale-tile',
    attribution: gsiTileAttribution,
    maxZoom: 18,
  },
  contourDetail: {
    url: 'https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png',
    className: 'gsi-contour-detail-tile',
    attribution: gsiTileAttribution,
    maxZoom: 18,
  },
};

export const shouldShowContourDetail = (zoom: number): boolean =>
  zoom >= contourDetailZoomThreshold;

export const routeStrokeStyles: Readonly<{
  halo: StrokeStyle;
  live: StrokeStyle;
  fallback: StrokeStyle;
}> = {
  halo: {
    color: '#fffdf7',
    weight: 11,
    opacity: 0.94,
  },
  live: {
    color: '#0057d9',
    weight: 6,
    opacity: 0.98,
  },
  fallback: {
    color: '#b0005a',
    weight: 6,
    opacity: 0.98,
    dashArray: '8 9',
  },
};

export { aiSuggestedLodgingPlaceByDate };

const lodgingCategories = new Set<Place['category']>(['hotel', 'onsen']);

function collectTripDayPlaceIds(day: TripDay): string[] {
  return [day.startPlaceId, ...day.stopIds, day.endPlaceId];
}

function resolveDayLodgingPlace(input: {
  day: TripDay;
  places: Record<string, Place>;
}): { placeId: string; role: Exclude<LodgingRole, 'none'> } | null {
  const aiSuggestedPlaceId = aiSuggestedLodgingPlaceByDate[input.day.date];

  if (!('lodgingAreaId' in input.day)) {
    return aiSuggestedPlaceId
      ? { placeId: aiSuggestedPlaceId, role: 'ai-suggested' }
      : null;
  }

  const endPlace = input.places[input.day.endPlaceId];
  if (endPlace && lodgingCategories.has(endPlace.category)) {
    return { placeId: input.day.endPlaceId, role: 'lodging' };
  }

  const lodgingAreaId = input.day.lodgingAreaId;
  if (lodgingAreaId && input.places[lodgingAreaId]) {
    return { placeId: lodgingAreaId, role: 'lodging' };
  }

  return endPlace ? { placeId: input.day.endPlaceId, role: 'lodging' } : null;
}

export function buildOverviewMarkers(input: {
  days: TripDay[];
  places: Record<string, Place>;
  csvPlaceSummaries?: Record<string, CsvPlaceSummary>;
}): OverviewMarker[] {
  const markers = new Map<string, OverviewMarker>();
  const csvPlaceSummaries = input.csvPlaceSummaries ?? {};

  const ensureMarker = (placeId: string): OverviewMarker | null => {
    if (!input.places[placeId]) {
      return null;
    }

    const existingMarker = markers.get(placeId);
    if (existingMarker) {
      return existingMarker;
    }

    const marker: OverviewMarker = {
      placeId,
      dayLabels: [],
      isCsvPlace: Boolean(csvPlaceSummaries[placeId]),
      lodgingRole: 'none',
    };
    markers.set(placeId, marker);
    return marker;
  };

  for (const day of input.days) {
    for (const placeId of collectTripDayPlaceIds(day)) {
      const marker = ensureMarker(placeId);
      if (marker && !marker.dayLabels.includes(day.labelZh)) {
        marker.dayLabels.push(day.labelZh);
      }
    }

    const lodgingPlace = resolveDayLodgingPlace({ day, places: input.places });
    if (lodgingPlace) {
      const marker = ensureMarker(lodgingPlace.placeId);
      if (marker) {
        if (!marker.dayLabels.includes(day.labelZh)) {
          marker.dayLabels.push(day.labelZh);
        }
        marker.lodgingRole =
          lodgingPlace.role === 'ai-suggested'
            ? 'ai-suggested'
            : marker.lodgingRole === 'ai-suggested'
              ? 'ai-suggested'
              : 'lodging';
      }
    }
  }

  return [...markers.values()];
}

const escapeHtml = (value: string): string =>
  value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

const formatPopupText = (value: string): string =>
  escapeHtml(value).replace(/\r?\n/g, '<br>');

const toLatLngTuple = (place: Place): [number, number] => [place.lat, place.lng];

const createConfiguredTileLayer = (config: TileLayerConfig): L.TileLayer => {
  const { url, ...options } = config;
  return L.tileLayer(url, options);
};

const emptyRouteSummary: RouteRenderSummary = {
  status: 'empty',
  durationMinutes: 0,
  distanceKm: 0,
  noteZh: '今日沒有行車路線',
};

export function createTripMap(
  container: HTMLElement,
  places: Record<string, Place>,
  routeSegments: Record<string, RouteSegment>,
  onPlaceSelected: (place: Place) => void,
  csvPlaceSummaries: Record<string, CsvPlaceSummary> = {},
): MapController {
  const map = L.map(container, { zoomControl: true }).setView([42.8, 141.1], 8);
  const baseTileLayer = createConfiguredTileLayer(mapTilePolicy.base);
  const contourDetailTileLayer = createConfiguredTileLayer(mapTilePolicy.contourDetail);

  const syncTileLayerForZoom = () => {
    const showContourDetail = shouldShowContourDetail(map.getZoom());
    const visibleLayer = showContourDetail ? contourDetailTileLayer : baseTileLayer;
    const hiddenLayer = showContourDetail ? baseTileLayer : contourDetailTileLayer;

    if (!map.hasLayer(visibleLayer)) {
      visibleLayer.addTo(map);
    }

    if (map.hasLayer(hiddenLayer)) {
      map.removeLayer(hiddenLayer);
    }
  };

  syncTileLayerForZoom();
  map.on('zoomend', syncTileLayerForZoom);

  const markerLayer = L.layerGroup().addTo(map);
  const routeLayer = L.layerGroup().addTo(map);
  let renderSequence = 0;

  function addPlaceMarker(
    place: Place,
    options: {
      dayLabels?: string[];
      lodgingRole?: LodgingRole;
      overview?: boolean;
    } = {},
  ): void {
    const label = place.nameZh.slice(0, 1);
    const csvSummary = csvPlaceSummaries[place.id];
    const csvMarkerClass = csvSummary
      ? ` marker-from-csv marker-csv-${csvSummary.markerColorIndex}`
      : '';
    const lodgingClass =
      options.lodgingRole && options.lodgingRole !== 'none'
        ? options.lodgingRole === 'ai-suggested'
          ? ' marker-lodging marker-ai-lodging'
          : ' marker-lodging'
        : '';
    const overviewClass = options.overview ? ' marker-overview' : '';
    const daySummary = options.dayLabels?.length
      ? `<span class="popup-source">行程日 ${escapeHtml(options.dayLabels.join(', '))}</span><br>`
      : '';
    const lodgingSummary =
      options.lodgingRole === 'ai-suggested'
        ? '<span class="popup-source popup-source-ai">AI 推薦住宿候選</span><br>'
        : options.lodgingRole === 'lodging'
          ? '<span class="popup-source popup-source-lodging">住宿地</span><br>'
          : '';
    const popupBody = csvSummary
      ? `${daySummary}${lodgingSummary}<span class="popup-source">CSV 補充</span><br>${formatPopupText(
          csvSummary.summaryZh,
        )}`
      : `${daySummary}${lodgingSummary}${formatPopupText(place.descriptionZh)}`;

    const marker = L.marker(toLatLngTuple(place), {
      title: place.nameZh,
      icon: L.divIcon({
        className: `trip-marker marker-${place.category}${csvMarkerClass}${lodgingClass}${overviewClass}`,
        html: `<span>${escapeHtml(label)}</span>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15],
      }),
    })
      .addTo(markerLayer)
      .bindPopup(`<strong>${escapeHtml(place.nameZh)}</strong><br>${popupBody}`);
    const markerElement = marker.getElement();
    markerElement?.setAttribute('data-place-id', place.id);
    if (csvSummary) {
      markerElement?.setAttribute('data-csv-place', 'true');
    }
    if (options.lodgingRole && options.lodgingRole !== 'none') {
      markerElement?.setAttribute('data-lodging-place', 'true');
      markerElement?.setAttribute('data-lodging-role', options.lodgingRole);
    }

    marker.on('click', () => onPlaceSelected(place));
  }

  async function renderDay(day: TripDay): Promise<RouteRenderSummary> {
    const sequence = ++renderSequence;
    markerLayer.clearLayers();
    routeLayer.clearLayers();
    let routeSummary = emptyRouteSummary;

    const placeIds = collectTripDayPlaceIds(day);
    const dayPlaces = placeIds
      .map((id) => places[id])
      .filter((place): place is Place => Boolean(place));
    const segments = day.routeSegmentIds
      .map((id) => routeSegments[id])
      .filter((segment): segment is RouteSegment => Boolean(segment));
    const dayLodgingPlace = resolveDayLodgingPlace({ day, places });

    for (const place of dayPlaces) {
      addPlaceMarker(place, {
        lodgingRole:
          dayLodgingPlace?.placeId === place.id ? dayLodgingPlace.role : 'none',
      });
    }

    if (segments.length > 0) {
      const route = await fetchRouteGeometry({ segments, places });

      if (sequence !== renderSequence) {
        return emptyRouteSummary;
      }

      routeSummary = {
        status: route.status,
        durationMinutes: route.durationMinutes,
        distanceKm: route.distanceKm,
        noteZh: route.noteZh,
      };

      if (route.points.length > 0) {
        const mainStrokeStyle =
          route.status === 'live' ? routeStrokeStyles.live : routeStrokeStyles.fallback;

        L.polyline(route.points, {
          className:
            route.status === 'live'
              ? 'route-halo route-halo-live'
              : 'route-halo route-halo-fallback',
          color: routeStrokeStyles.halo.color,
          weight: routeStrokeStyles.halo.weight,
          opacity: routeStrokeStyles.halo.opacity,
          dashArray: mainStrokeStyle.dashArray,
          interactive: false,
        }).addTo(routeLayer);

        L.polyline(route.points, {
          className:
            route.status === 'live'
              ? 'route-line route-line-live'
              : 'route-line route-line-fallback',
          color: mainStrokeStyle.color,
          weight: mainStrokeStyle.weight,
          opacity: mainStrokeStyle.opacity,
          dashArray: mainStrokeStyle.dashArray,
        })
          .bindPopup(
            `${route.durationMinutes} 分 / ${route.distanceKm} km<br>${escapeHtml(
              route.noteZh,
            )}`,
          )
          .addTo(routeLayer);
      }
    }

    if (dayPlaces.length > 0) {
      const bounds = L.latLngBounds(dayPlaces.map(toLatLngTuple));
      map.fitBounds(bounds.pad(0.22), { animate: false, maxZoom: 11 });
    }

    map.invalidateSize();
    return routeSummary;
  }

  function renderOverview(days: TripDay[]): OverviewRenderSummary {
    renderSequence += 1;
    markerLayer.clearLayers();
    routeLayer.clearLayers();

    const overviewMarkers = buildOverviewMarkers({
      days,
      places,
      csvPlaceSummaries,
    });
    const overviewPlaces = overviewMarkers
      .map((marker) => ({ marker, place: places[marker.placeId] }))
      .filter(
        (entry): entry is { marker: OverviewMarker; place: Place } =>
          Boolean(entry.place),
      );

    for (const { marker, place } of overviewPlaces) {
      addPlaceMarker(place, {
        dayLabels: marker.dayLabels,
        lodgingRole: marker.lodgingRole,
        overview: true,
      });
    }

    if (overviewPlaces.length > 0) {
      const bounds = L.latLngBounds(
        overviewPlaces.map(({ place }) => toLatLngTuple(place)),
      );
      map.fitBounds(bounds.pad(0.18), { animate: false, maxZoom: 10 });
    }

    map.invalidateSize();

    return {
      totalMarkers: overviewMarkers.length,
      csvMarkers: overviewMarkers.filter((marker) => marker.isCsvPlace).length,
      lodgingMarkers: overviewMarkers.filter(
        (marker) => marker.lodgingRole !== 'none',
      ).length,
      aiSuggestedLodgingPlaceIds: overviewMarkers
        .filter((marker) => marker.lodgingRole === 'ai-suggested')
        .map((marker) => marker.placeId),
    };
  }

  return { renderDay, renderOverview };
}
