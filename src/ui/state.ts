import type { LodgingCandidate, RouteSegment, TripDay } from '../data/trip';

export interface DayViewModel {
  date: string;
  labelZh: string;
  titleZh: string;
  startNameZh: string;
  endNameZh: string;
  stopNamesZh: string[];
  routeNamesZh: string[];
  summaryZh: string;
  driveNoteZh: string;
  lodgingTargetZh: string;
  lodgingCandidates: LodgingCandidate[];
  actionLabelsZh: string[];
}

const ACTION_LABELS_ZH = [
  '\u958b\u555f Google Maps',
  '\u6aa2\u67e5 JMA \u5929\u6c23\u8b66\u793a',
  '\u6aa2\u67e5\u5373\u6642\u9053\u8def\u8def\u6cc1',
  '\u641c\u5c0b 3 \u661f\u4ee5\u4e0a\u4f4f\u5bbf',
] as const;

export function getInitialDayId(days: TripDay[]): string {
  return days[0]?.date ?? '';
}

export function selectDay(date: string, days: TripDay[]): TripDay {
  const fallbackDay = days[0];
  if (!fallbackDay) {
    throw new Error('tripDays is empty');
  }

  return days.find((day) => day.date === date) ?? fallbackDay;
}

export function buildDayViewModel(
  day: TripDay,
  places: Record<string, { nameZh: string }>,
  lodgingCandidates: LodgingCandidate[],
  routeSegments?: Record<string, Pick<RouteSegment, 'toPlaceId'>>,
): DayViewModel {
  const startNameZh = places[day.startPlaceId]?.nameZh ?? day.startPlaceId;
  const endNameZh = places[day.endPlaceId]?.nameZh ?? day.endPlaceId;
  const stopNamesZh = day.stopIds.map((id) => places[id]?.nameZh ?? id);
  const routeNamesZh = routeSegments
    ? [
        startNameZh,
        ...day.routeSegmentIds.map((segmentId) => {
          const placeId = routeSegments[segmentId]?.toPlaceId ?? segmentId;
          return places[placeId]?.nameZh ?? placeId;
        }),
      ]
    : [startNameZh, ...stopNamesZh, endNameZh];
  const dayLodgings =
    'lodgingAreaId' in day
      ? lodgingCandidates.filter(
          (candidate) => candidate.areaId === day.lodgingAreaId,
        )
      : [];

  return {
    date: day.date,
    labelZh: day.labelZh,
    titleZh: day.titleZh,
    startNameZh,
    endNameZh,
    stopNamesZh,
    routeNamesZh,
    summaryZh: day.summaryZh,
    driveNoteZh: day.driveNoteZh,
    lodgingTargetZh: day.lodgingTargetZh,
    lodgingCandidates: dayLodgings,
    actionLabelsZh: [...ACTION_LABELS_ZH],
  };
}
