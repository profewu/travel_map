import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Place, RouteSegment, TripDay } from '../data/trip';
import { fetchRouteGeometry } from '../services/routes';

export interface MapController {
  renderDay(day: TripDay): Promise<RouteRenderSummary>;
}

export interface RouteRenderSummary {
  status: 'live' | 'fallback' | 'empty';
  durationMinutes: number;
  distanceKm: number;
  noteZh: string;
}

const escapeHtml = (value: string): string =>
  value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

const toLatLngTuple = (place: Place): [number, number] => [place.lat, place.lng];

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
): MapController {
  const map = L.map(container, { zoomControl: true }).setView([42.8, 141.1], 8);
  const routeLineColor = {
    live: 'var(--route-line-live)',
    fallback: 'var(--route-line-fallback)',
  };

  L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', {
    className: 'gsi-pale-tile',
    attribution:
      '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noreferrer">?啁??Ｕ?扎</a>',
    maxZoom: 18,
  }).addTo(map);

  const markerLayer = L.layerGroup().addTo(map);
  const routeLayer = L.layerGroup().addTo(map);
  let renderSequence = 0;

  async function renderDay(day: TripDay): Promise<RouteRenderSummary> {
    const sequence = ++renderSequence;
    markerLayer.clearLayers();
    routeLayer.clearLayers();
    let routeSummary = emptyRouteSummary;

    const placeIds = [day.startPlaceId, ...day.stopIds, day.endPlaceId];
    const dayPlaces = placeIds
      .map((id) => places[id])
      .filter((place): place is Place => Boolean(place));
    const segments = day.routeSegmentIds
      .map((id) => routeSegments[id])
      .filter((segment): segment is RouteSegment => Boolean(segment));

    for (const place of dayPlaces) {
      const label = place.nameZh.slice(0, 1);
      const marker = L.marker(toLatLngTuple(place), {
        title: place.nameZh,
        icon: L.divIcon({
          className: `trip-marker marker-${place.category}`,
          html: `<span>${escapeHtml(label)}</span>`,
          iconSize: [30, 30],
          iconAnchor: [15, 15],
        }),
      })
        .addTo(markerLayer)
        .bindPopup(
          `<strong>${escapeHtml(place.nameZh)}</strong><br>${escapeHtml(
            place.descriptionZh,
          )}`,
        );
      marker.getElement()?.setAttribute('data-place-id', place.id);

      marker.on('click', () => onPlaceSelected(place));
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
        L.polyline(route.points, {
          className:
            route.status === 'live' ? 'route-line route-line-live' : 'route-line route-line-fallback',
          color: route.status === 'live' ? routeLineColor.live : routeLineColor.fallback,
          weight: 6,
          opacity: 0.9,
          dashArray: route.status === 'fallback' ? '9 10' : undefined,
        })
          .bindPopup(
            `${route.durationMinutes} ??/ ${route.distanceKm} km<br>${escapeHtml(
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

  return { renderDay };
}
