import {
  lodgingCandidates,
  places,
  routeSegments,
  tripDays,
} from '../src/data/trip';

describe('trip data', () => {
  it('covers the approved New Chitose round trip dates', () => {
    expect(tripDays.map((day) => day.date)).toEqual([
      '2026-06-25',
      '2026-06-26',
      '2026-06-27',
      '2026-06-28',
      '2026-06-29',
      '2026-06-30',
      '2026-07-01',
      '2026-07-02',
      '2026-07-03',
    ]);
    expect(tripDays[0].startPlaceId).toBe('new-chitose-airport');
    expect(tripDays[0].endPlaceId).toBe('eniwa-fairfield');
    expect(tripDays.at(-1)?.endPlaceId).toBe('new-chitose-airport');
  });

  it('integrates the important CSV places into curated map data', () => {
    expect(Object.keys(places)).toEqual(
      expect.arrayContaining([
        'eniwa-fairfield',
        'hanaroad-eniwa',
        'ecorin-village',
        'eniwa-honoka',
        'forest-adventure-eniwa',
        'kamameshi-ichie',
        'lake-shikotsu',
        'tarumae-garo',
        'park-hotel-miyabitei',
        'jigokudani',
        'oyunuma',
        'nachu-no-mori',
        'cape-chikyu',
        'lake-toya',
        'rinyu-market',
        'mt-moiwa',
        'cocono-susukino',
        'ario-sapporo',
        'sapporo-underground',
        'pokemon-center-sapporo',
        'susukino-airport-bus-stop',
      ]),
    );

    const searchable = [
      ...Object.values(places).map(
        (place) => `${place.nameZh} ${place.nameLocal ?? ''} ${place.descriptionZh}`,
      ),
      ...tripDays.map((day) => `${day.titleZh} ${day.summaryZh} ${day.driveNoteZh}`),
    ].join(' ');

    for (const text of [
      '惠庭',
      '支笏湖',
      '樽前GARO',
      '登別地獄谷',
      '大湯沼',
      'ナチュの森',
      '地球岬',
      '鱗友朝市',
      '薄野機場巴士',
    ]) {
      expect(searchable).toContain(text);
    }
  });

  it('uses the conservative reordered day structure from the CSV', () => {
    expect(
      tripDays.map((day) => ({
        date: day.date,
        start: day.startPlaceId,
        end: day.endPlaceId,
      })),
    ).toEqual([
      {
        date: '2026-06-25',
        start: 'new-chitose-airport',
        end: 'eniwa-fairfield',
      },
      {
        date: '2026-06-26',
        start: 'eniwa-fairfield',
        end: 'park-hotel-miyabitei',
      },
      {
        date: '2026-06-27',
        start: 'park-hotel-miyabitei',
        end: 'lake-toya',
      },
      { date: '2026-06-28', start: 'lake-toya', end: 'otaru' },
      { date: '2026-06-29', start: 'otaru', end: 'sapporo' },
      { date: '2026-06-30', start: 'sapporo', end: 'sapporo' },
      { date: '2026-07-01', start: 'sapporo', end: 'sapporo' },
      {
        date: '2026-07-02',
        start: 'sapporo',
        end: 'susukino-airport-bus-stop',
      },
      {
        date: '2026-07-03',
        start: 'susukino-airport-bus-stop',
        end: 'new-chitose-airport',
      },
    ]);
  });

  it('keeps the slow western route out of Hakodate, Furano, and Biei', () => {
    const forbidden = ['hakodate', '函館', 'furano', '富良野', 'biei', '美瑛'];
    const searchable = [
      ...Object.values(places).map(
        (place) => `${place.nameZh} ${place.nameLocal ?? ''}`,
      ),
      ...tripDays.map((day) => `${day.titleZh} ${day.summaryZh}`),
    ]
      .join(' ')
      .toLowerCase();

    for (const token of forbidden) {
      expect(searchable).not.toContain(token.toLowerCase());
    }
  });

  it('references only existing places and route segments', () => {
    for (const day of tripDays) {
      expect(places[day.startPlaceId]).toBeDefined();
      expect(places[day.endPlaceId]).toBeDefined();
      expect(places[day.weatherPlaceId]).toBeDefined();
      for (const stopId of day.stopIds) {
        expect(places[stopId]).toBeDefined();
      }
      for (const segmentId of day.routeSegmentIds) {
        expect(routeSegments[segmentId]).toBeDefined();
      }
    }
  });

  it('keeps route segments consistent with each day endpoints and continuity', () => {
    for (const day of tripDays) {
      if (day.routeSegmentIds.length === 0) {
        continue;
      }

      const segments = day.routeSegmentIds.map((id) => routeSegments[id]);
      expect(segments[0].fromPlaceId).toBe(day.startPlaceId);
      expect(segments[segments.length - 1].toPlaceId).toBe(day.endPlaceId);

      for (let i = 1; i < segments.length; i += 1) {
        expect(segments[i - 1].toPlaceId).toBe(segments[i].fromPlaceId);
      }
    }
  });

  it('keeps consecutive trip days continuous through the full itinerary', () => {
    for (let i = 0; i < tripDays.length - 1; i += 1) {
      const current = tripDays[i];
      const next = tripDays[i + 1];
      expect(current.endPlaceId).toBe(next.startPlaceId);
    }
  });

  it('offers only 3-star-or-better lodging candidates within curated areas', () => {
    expect(lodgingCandidates.length).toBeGreaterThanOrEqual(8);
    for (const hotel of lodgingCandidates) {
      expect(hotel.starLevel).toBeGreaterThanOrEqual(3);
      expect(['city', 'onsen-resort', 'airport-buffer']).toContain(hotel.type);
      expect(hotel.searchUrl).toMatch(/^https:\/\//);
    }
  });

  it('keeps lodging areas valid and mapped to curated candidates', () => {
    for (const day of tripDays) {
      if (day.date === '2026-07-03') {
        expect(day.lodgingAreaId).toBeUndefined();
        expect(day.lodgingTargetZh).toBe('無。');
        continue;
      }

      expect(day.lodgingAreaId).toBeDefined();
      if (!day.lodgingAreaId) {
        throw new Error(`missing lodgingAreaId for ${day.date}`);
      }

      expect(places[day.lodgingAreaId]).toBeDefined();
      expect(
        lodgingCandidates.some(
          (candidate) => candidate.areaId === day.lodgingAreaId,
        ),
      ).toBe(true);
    }
  });
});
