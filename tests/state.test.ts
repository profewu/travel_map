import { lodgingCandidates, places, routeSegments, tripDays } from '../src/data/trip';
import {
  buildDayViewModel,
  getInitialDayId,
  selectDay,
} from '../src/ui/state';

describe('ui state', () => {
  it('getInitialDayId(tripDays) returns 2026-06-25', () => {
    expect(getInitialDayId(tripDays)).toBe('2026-06-25');
  });

  it("selectDay('2026-06-28', tripDays).date returns 2026-06-28", () => {
    expect(selectDay('2026-06-28', tripDays).date).toBe('2026-06-28');
  });

  it("selectDay('2026-08-01', tripDays).date falls back to 2026-06-25", () => {
    expect(selectDay('2026-08-01', tripDays).date).toBe('2026-06-25');
  });

  it('buildDayViewModel for 2026-06-30 returns expected Traditional Chinese fields', () => {
    const day = selectDay('2026-06-30', tripDays);
    if (!('lodgingAreaId' in day)) {
      throw new Error('expected overnight day');
    }
    const viewModel = buildDayViewModel(day, places, lodgingCandidates, routeSegments);

    expect(viewModel.titleZh).toBe(day.titleZh);
    expect(viewModel.startNameZh).toBe('\u6d1e\u723a\u6e56');
    expect(viewModel.endNameZh).toBe('\u767b\u5225');
    expect(viewModel.stopNamesZh).toEqual([
      places['showa-shinzan-usuzan'].nameZh,
    ]);
    expect(viewModel.lodgingCandidates.length).toBeGreaterThan(0);
    expect(
      viewModel.lodgingCandidates.every(
        (candidate) => candidate.areaId === day.lodgingAreaId,
      ),
    ).toBe(true);
    expect(viewModel.actionLabelsZh).toEqual([
      '\u958b\u555f Google Maps',
      '\u6aa2\u67e5 JMA \u5929\u6c23\u8b66\u793a',
      '\u6aa2\u67e5\u5373\u6642\u9053\u8def\u8def\u6cc1',
      '\u641c\u5c0b 3 \u661f\u4ee5\u4e0a\u4f4f\u5bbf',
    ]);
  });

  it('buildDayViewModel preserves curated titleZh for non A-to-B day', () => {
    const day = selectDay('2026-06-26', tripDays);
    const viewModel = buildDayViewModel(day, places, lodgingCandidates);

    expect(viewModel.titleZh).toBe(day.titleZh);
    expect(viewModel.titleZh).not.toBe(
      `${places[day.startPlaceId].nameZh}\u5230${places[day.endPlaceId].nameZh}`,
    );
  });

  it('buildDayViewModel for departure day keeps lodgingCandidates empty and stopNamesZh empty', () => {
    const day = selectDay('2026-07-03', tripDays);
    const viewModel = buildDayViewModel(day, places, lodgingCandidates);

    expect(viewModel.lodgingCandidates).toEqual([]);
    expect(viewModel.stopNamesZh).toEqual([]);
    expect(viewModel.lodgingTargetZh).toBe('\u7121\u3002');
  });

  it('buildDayViewModel keeps unknown stop ids in stopNamesZh as fallback', () => {
    const baseDay = selectDay('2026-06-30', tripDays);
    const day = {
      ...baseDay,
      stopIds: [...baseDay.stopIds, 'missing-stop-id'],
    };

    const viewModel = buildDayViewModel(day, places, lodgingCandidates);
    expect(viewModel.stopNamesZh.at(-1)).toBe('missing-stop-id');
  });

  it('buildDayViewModel preserves route waypoint order for a same-city overnight day', () => {
    const day = selectDay('2026-06-27', tripDays);
    const viewModel = buildDayViewModel(
      day,
      places,
      lodgingCandidates,
      routeSegments,
    );

    expect(viewModel.routeNamesZh).toEqual(['札幌', '小樽', '余市', '小樽']);
  });
});
