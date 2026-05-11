import type {
  LodgingCandidate,
  Place,
  RouteSegment,
  TripDay,
} from '../src/data/trip';
import { places, routeSegments, tripDays } from '../src/data/trip';
import type { CsvPlaceSummary } from '../src/data/csvPlaceSummaries';
import { csvPlaceSummariesById } from '../src/data/csvPlaceSummaries';
import { buildItineraryTableRows } from '../src/ui/itineraryTable';

const fixturePlaces: Record<string, Place> = {
  start: {
    id: 'start',
    nameZh: 'Start City',
    lat: 42,
    lng: 141,
    category: 'city',
    descriptionZh: 'Start point',
  },
  'scenic-stop': {
    id: 'scenic-stop',
    nameZh: 'Scenic Stop',
    lat: 42.2,
    lng: 141.2,
    category: 'park',
    descriptionZh: 'Main scenic stop',
  },
  lunch: {
    id: 'lunch',
    nameZh: 'Lunch Market',
    lat: 42.4,
    lng: 141.4,
    category: 'food',
    descriptionZh: 'Lunch stop',
  },
  end: {
    id: 'end',
    nameZh: 'End Onsen',
    lat: 42.6,
    lng: 141.6,
    category: 'onsen',
    descriptionZh: 'End point',
  },
  'airport-buffer': {
    id: 'airport-buffer',
    nameZh: 'Airport Buffer Hotel',
    lat: 42.8,
    lng: 141.8,
    category: 'hotel',
    descriptionZh: 'AI lodging buffer',
  },
};

const fixtureRoutes: Record<string, RouteSegment> = {
  'start-scenic': {
    id: 'start-scenic',
    fromPlaceId: 'start',
    toPlaceId: 'scenic-stop',
    fallbackMinutes: 65,
    fallbackKm: 58,
    noteZh: 'Mountain road',
  },
  'scenic-lunch': {
    id: 'scenic-lunch',
    fromPlaceId: 'scenic-stop',
    toPlaceId: 'lunch',
    fallbackMinutes: 55,
    fallbackKm: 47,
    noteZh: 'Coastal road',
  },
  'lunch-end': {
    id: 'lunch-end',
    fromPlaceId: 'lunch',
    toPlaceId: 'end',
    fallbackMinutes: 70,
    fallbackKm: 66,
    noteZh: 'Late drive',
  },
};

const fixtureDays: TripDay[] = [
  {
    date: '2026-06-26',
    labelZh: 'Day 2',
    titleZh: 'Scenic onsen transfer',
    startPlaceId: 'start',
    stopIds: ['scenic-stop', 'lunch'],
    endPlaceId: 'end',
    weatherPlaceId: 'end',
    routeSegmentIds: ['start-scenic', 'scenic-lunch', 'lunch-end'],
    summaryZh: 'Curated day summary',
    lodgingTargetZh: 'Stay near End Onsen',
    lodgingAreaId: 'end',
    driveNoteZh: 'Long scenic transfer',
  },
  {
    date: '2026-07-03',
    labelZh: 'Day 9',
    titleZh: 'Airport departure',
    startPlaceId: 'end',
    stopIds: [],
    endPlaceId: 'start',
    weatherPlaceId: 'start',
    routeSegmentIds: [],
    summaryZh: 'Departure day',
    lodgingTargetZh: '\u7121\u3002',
    driveNoteZh: 'Buffer day',
  },
];

const fixtureLodging: LodgingCandidate[] = [
  {
    id: 'end-hotel',
    areaId: 'end',
    nameZh: 'End Onsen Hotel',
    type: 'onsen-resort',
    starLevel: 4,
    budgetRiskZh: 'Busy weekend',
    parkingZh: 'Parking available',
    fitZh: 'Good for onsen night',
    searchUrl: 'https://example.com/end-hotel',
  },
];

const fixtureCsv: Record<string, CsvPlaceSummary> = {
  'scenic-stop': {
    placeId: 'scenic-stop',
    summaryZh: 'CSV Day 2\nScenic parking and short walk tips',
    markerColorIndex: 0,
  },
  lunch: {
    placeId: 'lunch',
    summaryZh: 'CSV Day 2\nLunch market closes early',
    markerColorIndex: 1,
  },
};

describe('itinerary table view model', () => {
  it('builds table rows with route, CSV summary, lodging, AI advice, and actions', () => {
    const rows = buildItineraryTableRows({
      days: fixtureDays,
      places: fixturePlaces,
      routeSegments: fixtureRoutes,
      lodgingCandidates: fixtureLodging,
      csvPlaceSummaries: fixtureCsv,
      aiSuggestedLodgingPlaceByDate: {
        '2026-07-03': 'airport-buffer',
      },
    });

    expect(rows).toHaveLength(2);

    const transferDay = rows[0];
    expect(transferDay.date).toBe('2026-06-26');
    expect(transferDay.labelZh).toBe('Day 2');
    expect(transferDay.titleZh).toBe('Scenic onsen transfer');
    expect(transferDay.route.startNameZh).toBe('Start City');
    expect(transferDay.route.stopNamesZh).toEqual(['Scenic Stop', 'Lunch Market']);
    expect(transferDay.route.endNameZh).toBe('End Onsen');
    expect(transferDay.lodging.targetZh).toBe('Stay near End Onsen');
    expect(transferDay.lodging.candidateNamesZh).toEqual(['End Onsen Hotel']);
    expect(transferDay.csvSummary.items.map((item) => item.placeNameZh)).toEqual([
      'Scenic Stop',
      'Lunch Market',
    ]);
    expect(transferDay.csvSummary.textZh).toContain('Scenic parking');
    expect(transferDay.csvSummary.textZh).toContain('Lunch market');
    expect(transferDay.drive.totalKm).toBe(171);
    expect(transferDay.drive.totalMinutes).toBe(190);
    expect(transferDay.drive.hasFatigueRisk).toBe(true);
    expect(transferDay.aiSuggestionZh).toContain('AI 建議');
    expect(transferDay.aiSuggestionZh).toContain('車程偏長');
    expect(transferDay.actions.googleMapsUrl).toContain(
      'https://www.google.com/maps/dir/?',
    );
    expect(transferDay.actions.googleMapsUrl).toContain('waypoints=');
    expect(transferDay.actions.jmaUrl).toContain('jma.go.jp');
    expect(transferDay.actions.roadUrl).toContain('c-nexco.co.jp');
    expect(transferDay.actions.hotelSearchUrl).toContain(
      'https://www.google.com/travel/hotels?',
    );

    const departureDay = rows[1];
    expect(departureDay.lodging.aiSuggestedNameZh).toBe('Airport Buffer Hotel');
    expect(departureDay.lodging.candidateNamesZh).toEqual([]);
    expect(departureDay.csvSummary.textZh).toBe('無 CSV 補充。');
  });

  it('builds a row for every curated trip day and includes real CSV and AI lodging data', () => {
    const rows = buildItineraryTableRows({
      days: tripDays,
      places,
      routeSegments,
      lodgingCandidates: [],
      csvPlaceSummaries: csvPlaceSummariesById,
    });

    expect(rows).toHaveLength(tripDays.length);
    expect(rows.some((row) => row.csvSummary.items.length > 0)).toBe(true);
    expect(rows.every((row) => row.aiSuggestionZh.startsWith('AI 建議'))).toBe(true);

    const departureRow = rows.find((row) => row.date === '2026-07-03');
    expect(departureRow?.lodging.aiSuggestedNameZh).toBe(
      places['eniwa-fairfield'].nameZh,
    );
  });
});
