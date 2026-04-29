import { places, routeSegments } from '../src/data/trip';
import {
  buildFallbackRoute,
  buildOsrmUrl,
  fetchRouteGeometry,
} from '../src/services/routes';

describe('route service', () => {
  it("buildOsrmUrl(routeSegments['sapporo-otaru'], places) uses OSRM base with lon-lat coordinates", () => {
    const url = buildOsrmUrl(routeSegments['sapporo-otaru'], places);

    expect(url).toContain('https://router.project-osrm.org/route/v1/driving/');
    expect(url).toContain('141.3545,43.0618;140.9947,43.1907');
    expect(url).toContain('overview=full');
    expect(url).toContain('geometries=geojson');
  });

  it("buildFallbackRoute([routeSegments['sapporo-otaru']], places) returns fallback route payload", () => {
    const result = buildFallbackRoute([routeSegments['sapporo-otaru']], places);

    expect(result.status).toBe('fallback');
    expect(result.points).toEqual([
      [43.0618, 141.3545],
      [43.1907, 140.9947],
    ]);
    expect(result.durationMinutes).toBe(55);
  });

  it('fetchRouteGeometry falls back when OSRM fetch fails', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('network down'));

    const result = await fetchRouteGeometry({
      segments: [routeSegments['sapporo-otaru']],
      places,
      fetcher,
    });

    expect(result.status).toBe('fallback');
    expect(result.noteZh).toContain('使用內建估算');
  });

  it('fetchRouteGeometry merges exact-equal boundary points and sums duration/distance', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: [
            {
              duration: 31,
              distance: 1234,
              geometry: {
                coordinates: [
                  [141.3545, 43.0618],
                  [140.9947, 43.1907],
                ],
              },
            },
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: [
            {
              duration: 31,
              distance: 2000,
              geometry: {
                coordinates: [
                  [140.9947, 43.1907],
                  [140.7835, 43.1955],
                ],
              },
            },
          ],
        }),
      });

    const result = await fetchRouteGeometry({
      segments: [routeSegments['sapporo-otaru'], routeSegments['otaru-yoichi']],
      places,
      fetcher,
    });

    expect(result.status).toBe('live');
    expect(result.points).toEqual([
      [43.0618, 141.3545],
      [43.1907, 140.9947],
      [43.1955, 140.7835],
    ]);
    expect(result.durationMinutes).toBe(1);
    expect(result.distanceKm).toBe(3.2);
    expect(result.noteZh).toBe(
      'OSRM 估算路線，實際時間仍請以 Google Maps 與即時路況確認。',
    );
  });

  it('fetchRouteGeometry merges near-identical boundary points with tolerance', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: [
            {
              duration: 300,
              distance: 10000,
              geometry: {
                coordinates: [
                  [141.3545, 43.0618],
                  [140.9947, 43.1907],
                ],
              },
            },
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: [
            {
              duration: 300,
              distance: 10000,
              geometry: {
                coordinates: [
                  [140.994700004, 43.190700004],
                  [140.7835, 43.1955],
                ],
              },
            },
          ],
        }),
      });

    const result = await fetchRouteGeometry({
      segments: [routeSegments['sapporo-otaru'], routeSegments['otaru-yoichi']],
      places,
      fetcher,
    });

    expect(result.status).toBe('live');
    expect(result.points).toEqual([
      [43.0618, 141.3545],
      [43.1907, 140.9947],
      [43.1955, 140.7835],
    ]);
  });
});
