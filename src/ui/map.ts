import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Place, RouteSegment, TripDay } from '../data/trip';
import { fetchRouteGeometry } from '../services/routes';

export interface MapController {
  renderDay(day: TripDay): Promise<void>;
}

const escapeHtml = (value: string): string =>
  value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

const toLatLngTuple = (place: Place): [number, number] => [place.lat, place.lng];

export function createTripMap(
  container: HTMLElement,
  places: Record<string, Place>,
  routeSegments: Record<string, RouteSegment>,
  onPlaceSelected: (place: Place) => void,
): MapController {
  const map = L.map(container, { zoomControl: true }).setView([42.8, 141.1], 8);

  L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', {
    attribution:
      '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noreferrer">地理院タイル</a>',
    maxZoom: 18,
  }).addTo(map);

  const markerLayer = L.layerGroup().addTo(map);
  const routeLayer = L.layerGroup().addTo(map);
  let renderSequence = 0;

  async function renderDay(day: TripDay): Promise<void> {
    const sequence = ++renderSequence;
    markerLayer.clearLayers();
    routeLayer.clearLayers();

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

      marker.on('click', () => onPlaceSelected(place));
    }

    if (segments.length > 0) {
      const route = await fetchRouteGeometry({ segments, places });

      if (sequence !== renderSequence) {
        return;
      }

      if (route.points.length > 0) {
        L.polyline(route.points, {
          className: 'route-line',
          color: route.status === 'live' ? '#0f766e' : '#b45309',
          weight: 5,
          opacity: 0.9,
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
  }

  return { renderDay };
}
