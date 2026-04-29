import type { Place, RouteSegment } from '../data/trip';

export interface RouteResult {
  status: 'live' | 'fallback';
  points: Array<[number, number]>;
  durationMinutes: number;
  distanceKm: number;
  noteZh: string;
}

interface OsrmResponse {
  routes?: Array<{
    distance?: number;
    duration?: number;
    geometry?: {
      coordinates?: Array<[number, number]>;
    };
  }>;
}

interface FetchRouteGeometryInput {
  segments: RouteSegment[];
  places: Record<string, Place>;
  fetcher?: typeof fetch;
}

const fallbackNoteZh = '使用內建估算車程，請以 Google Maps 與即時路況確認。';
const liveNoteZh = 'OSRM 估算路線，實際時間仍請以 Google Maps 與即時路況確認。';
const osrmBaseUrl = 'https://router.project-osrm.org/route/v1/driving';
const fetcherDefault: typeof fetch = fetch;

const samePoint = (
  a: [number, number],
  b: [number, number],
  epsilon = 1e-5,
): boolean => Math.abs(a[0] - b[0]) <= epsilon && Math.abs(a[1] - b[1]) <= epsilon;

export const buildOsrmUrl = (
  segment: RouteSegment,
  places: Record<string, Place>,
): string => {
  const from = places[segment.fromPlaceId];
  const to = places[segment.toPlaceId];
  const coordinates = `${from.lng},${from.lat};${to.lng},${to.lat}`;
  return `${osrmBaseUrl}/${coordinates}?overview=full&geometries=geojson`;
};

export const buildFallbackRoute = (
  segments: RouteSegment[],
  places: Record<string, Place>,
): RouteResult => {
  const points: Array<[number, number]> = [];
  let durationMinutes = 0;
  let distanceKm = 0;

  for (const segment of segments) {
    const from = places[segment.fromPlaceId];
    const to = places[segment.toPlaceId];

    if (points.length === 0) {
      points.push([from.lat, from.lng]);
    }
    points.push([to.lat, to.lng]);
    durationMinutes += segment.fallbackMinutes;
    distanceKm += segment.fallbackKm;
  }

  return {
    status: 'fallback',
    points,
    durationMinutes,
    distanceKm,
    noteZh: fallbackNoteZh,
  };
};

export const fetchRouteGeometry = async (
  input: FetchRouteGeometryInput,
): Promise<RouteResult> => {
  const { segments, places, fetcher = fetcherDefault } = input;

  try {
    const points: Array<[number, number]> = [];
    let totalDurationSeconds = 0;
    let totalDistanceMeters = 0;

    for (const segment of segments) {
      const response = await fetcher(buildOsrmUrl(segment, places));
      if (!response.ok) {
        throw new Error(`OSRM request failed: ${response.status}`);
      }

      const payload = (await response.json()) as OsrmResponse;
      const route = payload.routes?.[0];
      const coordinates = route?.geometry?.coordinates;
      const durationSeconds = route?.duration;
      const distanceMeters = route?.distance;

      if (!coordinates || durationSeconds === undefined || distanceMeters === undefined) {
        throw new Error('OSRM payload missing route data');
      }

      const convertedPoints = coordinates.map(
        ([lng, lat]): [number, number] => [lat, lng],
      );

      if (convertedPoints.length > 0) {
        const lastExistingPoint = points[points.length - 1];
        const firstNewPoint = convertedPoints[0];
        const startIndex =
          lastExistingPoint && samePoint(lastExistingPoint, firstNewPoint) ? 1 : 0;
        points.push(...convertedPoints.slice(startIndex));
      }

      totalDurationSeconds += durationSeconds;
      totalDistanceMeters += distanceMeters;
    }

    return {
      status: 'live',
      points,
      durationMinutes: Math.round(totalDurationSeconds / 60),
      distanceKm: Math.round(totalDistanceMeters / 100) / 10,
      noteZh: liveNoteZh,
    };
  } catch {
    return buildFallbackRoute(segments, places);
  }
};
