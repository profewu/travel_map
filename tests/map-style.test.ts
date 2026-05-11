import {
  aiSuggestedLodgingPlaceByDate,
  buildOverviewMarkers,
  contourDetailZoomThreshold,
  mapTilePolicy,
  routeStrokeStyles,
  shouldShowContourDetail,
} from '../src/ui/map';
import { csvPlaceSummariesById } from '../src/data/csvPlaceSummaries';
import { places, tripDays } from '../src/data/trip';

describe('map visual policy', () => {
  it('keeps the pale GSI map as the default and only shows contour detail when zoomed in', () => {
    expect(mapTilePolicy.base.url).toContain('/xyz/pale/');
    expect(mapTilePolicy.contourDetail.url).toContain('/xyz/std/');
    expect(contourDetailZoomThreshold).toBe(12);
    expect(shouldShowContourDetail(11)).toBe(false);
    expect(shouldShowContourDetail(12)).toBe(true);
  });

  it('uses route colors with a halo and avoids map-road green/brown tones', () => {
    expect(routeStrokeStyles.halo.color).toBe('#fffdf7');
    expect(routeStrokeStyles.live.color).toBe('#0057d9');
    expect(routeStrokeStyles.fallback.color).toBe('#b0005a');
    expect(routeStrokeStyles.live.weight).toBeLessThan(routeStrokeStyles.halo.weight);
    expect(routeStrokeStyles.fallback.dashArray).toBe('8 9');
  });

  it('buildOverviewMarkers marks all itinerary points, CSV supplements, lodging, and AI lodging suggestions', () => {
    const markers = buildOverviewMarkers({
      days: tripDays,
      places,
      csvPlaceSummaries: csvPlaceSummariesById,
    });
    const byId = new Map(markers.map((marker) => [marker.placeId, marker]));
    const itineraryPlaceIds = new Set(
      tripDays.flatMap((day) => [day.startPlaceId, ...day.stopIds, day.endPlaceId]),
    );

    expect(markers).toHaveLength(itineraryPlaceIds.size);
    expect(byId.get('lake-shikotsu')?.isCsvPlace).toBe(true);
    expect(byId.get('park-hotel-miyabitei')?.lodgingRole).toBe('lodging');
    expect(byId.get('lake-toya')?.lodgingRole).toBe('lodging');
    expect(aiSuggestedLodgingPlaceByDate['2026-07-03']).toBe('eniwa-fairfield');
    expect(byId.get('eniwa-fairfield')?.lodgingRole).toBe('ai-suggested');
    expect(byId.get('eniwa-fairfield')?.dayLabels).toContain('7/3');
  });
});
