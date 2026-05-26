import type { CsvPlaceSummary } from '../data/csvPlaceSummaries';
import { aiSuggestedLodgingPlaceByDate as defaultAiSuggestedLodgingPlaceByDate } from '../data/lodgingPolicy';
import type {
  ConfirmedLodging,
  LodgingCandidate,
  Place,
  RouteSegment,
  TripDay,
} from '../data/trip';
import {
  buildGoogleDirectionsUrl,
  buildHotelSearchUrl,
  jmaWarningUrl,
  roadTrafficUrl,
} from '../services/links';

export interface ItineraryCsvItem {
  placeId: string;
  placeNameZh: string;
  summaryZh: string;
}

export interface ItineraryTableRow {
  date: string;
  labelZh: string;
  titleZh: string;
  route: {
    startNameZh: string;
    stopNamesZh: string[];
    endNameZh: string;
    routeNamesZh: string[];
  };
  lodging: {
    targetZh: string;
    candidateNamesZh: string[];
    aiSuggestedNameZh?: string;
    confirmed?: ConfirmedLodging;
  };
  csvSummary: {
    items: ItineraryCsvItem[];
    textZh: string;
  };
  aiSuggestionZh: string;
  drive: {
    totalKm: number;
    totalMinutes: number;
    distanceLabelZh: string;
    durationLabelZh: string;
    hasFatigueRisk: boolean;
  };
  actions: {
    googleMapsUrl: string;
    jmaUrl: string;
    roadUrl: string;
    hotelSearchUrl: string;
  };
}

export interface BuildItineraryTableRowsInput {
  days: TripDay[];
  places: Record<string, Place>;
  routeSegments: Record<string, RouteSegment>;
  lodgingCandidates: LodgingCandidate[];
  csvPlaceSummaries: Record<string, CsvPlaceSummary>;
  aiSuggestedLodgingPlaceByDate?: Readonly<Record<string, string>>;
}

const MAX_CSV_ITEM_CHARS = 92;

const compactText = (value: string): string => value.replace(/\s+/g, ' ').trim();

const truncateText = (value: string, maxChars: number): string => {
  const compact = compactText(value);
  if (compact.length <= maxChars) {
    return compact;
  }

  return `${compact.slice(0, maxChars - 1)}...`;
};

const placeName = (places: Record<string, Place>, placeId: string): string =>
  places[placeId]?.nameZh ?? placeId;

const unique = <T>(items: T[]): T[] => [...new Set(items)];

function nextDate(date: string): string {
  const [year, month, day] = date.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day + 1)).toISOString().slice(0, 10);
}

function formatDistance(totalKm: number): string {
  if (totalKm <= 0) {
    return '0 km';
  }

  return `${Math.round(totalKm * 10) / 10} km`;
}

function formatDuration(totalMinutes: number): string {
  if (totalMinutes <= 0) {
    return '0 分';
  }

  if (totalMinutes < 60) {
    return `${Math.round(totalMinutes)} 分`;
  }

  return `${Math.round((totalMinutes / 60) * 10) / 10} 小時`;
}

function buildRoutePlaceIds(day: TripDay, routeSegments: Record<string, RouteSegment>): string[] {
  const routedPlaceIds = [
    day.startPlaceId,
    ...day.routeSegmentIds.map((segmentId) => routeSegments[segmentId]?.toPlaceId),
  ].filter((placeId): placeId is string => Boolean(placeId));

  if (routedPlaceIds.length > 1) {
    return routedPlaceIds;
  }

  return [day.startPlaceId, ...day.stopIds, day.endPlaceId];
}

function buildCsvSummary(input: {
  day: TripDay;
  places: Record<string, Place>;
  routeSegments: Record<string, RouteSegment>;
  csvPlaceSummaries: Record<string, CsvPlaceSummary>;
}): ItineraryTableRow['csvSummary'] {
  const routePlaceIds = unique(buildRoutePlaceIds(input.day, input.routeSegments));
  const items = routePlaceIds
    .map((placeId) => {
      const summary = input.csvPlaceSummaries[placeId];
      if (!summary) {
        return null;
      }

      return {
        placeId,
        placeNameZh: placeName(input.places, placeId),
        summaryZh: truncateText(summary.summaryZh, MAX_CSV_ITEM_CHARS),
      };
    })
    .filter((item): item is ItineraryCsvItem => Boolean(item));

  return {
    items,
    textZh:
      items.length > 0
        ? items.map((item) => `• ${item.placeNameZh}: ${item.summaryZh}`).join('\n')
        : '無 CSV 補充。',
  };
}

function buildAiSuggestion(input: {
  lodgingTargetZh: string;
  totalKm: number;
  totalMinutes: number;
  stopCount: number;
  csvCount: number;
  hasFatigueRisk: boolean;
}): string {
  const lodgingAnchor = input.lodgingTargetZh || '住宿區';

  if (input.hasFatigueRisk) {
    return `AI 建議：車程偏長（${formatDistance(input.totalKm)} / ${formatDuration(
      input.totalMinutes,
    )}），CSV 景點先挑 1-2 個重點，晚餐與休息點盡量收斂到 ${lodgingAnchor} 周邊。`;
  }

  if (input.csvCount >= 3) {
    return `AI 建議：CSV 補充點較多，適合用「必去 / 可跳過」排序，保留 ${lodgingAnchor} 附近的彈性時間。`;
  }

  if (input.totalKm <= 50 && input.stopCount <= 1) {
    return `AI 建議：移動量輕，可以把主要停留時間留給住宿區與附近餐食，避免再塞遠距離景點。`;
  }

  return `AI 建議：行程節奏中等，先完成主路線，再依天氣與體力加入 CSV 補充點；住宿以 ${lodgingAnchor} 為錨點。`;
}

function buildActions(input: {
  day: TripDay;
  routeNamesZh: string[];
  lodgingTargetZh: string;
  lodgingSearchQueryZh?: string;
  endNameZh: string;
}): ItineraryTableRow['actions'] {
  const origin = input.routeNamesZh[0] ?? input.endNameZh;
  const destination = input.routeNamesZh.at(-1) ?? input.endNameZh;
  const waypoints = input.routeNamesZh.slice(1, -1);
  const hotelQuery =
    input.lodgingSearchQueryZh ??
    (input.lodgingTargetZh && input.lodgingTargetZh !== '無。'
      ? input.lodgingTargetZh
      : `${input.endNameZh} 3 星以上住宿`);

  return {
    googleMapsUrl: buildGoogleDirectionsUrl({
      origin,
      destination,
      waypoints,
    }),
    jmaUrl: jmaWarningUrl,
    roadUrl: roadTrafficUrl,
    hotelSearchUrl: buildHotelSearchUrl(hotelQuery, input.day.date, nextDate(input.day.date)),
  };
}

export function buildItineraryTableRows(
  input: BuildItineraryTableRowsInput,
): ItineraryTableRow[] {
  const aiLodgingByDate =
    input.aiSuggestedLodgingPlaceByDate ?? defaultAiSuggestedLodgingPlaceByDate;

  return input.days.map((day) => {
    const routePlaceIds = buildRoutePlaceIds(day, input.routeSegments);
    const startNameZh = placeName(input.places, day.startPlaceId);
    const stopNamesZh = day.stopIds.map((placeId) => placeName(input.places, placeId));
    const endNameZh = placeName(input.places, day.endPlaceId);
    const routeNamesZh = routePlaceIds.map((placeId) => placeName(input.places, placeId));
    const dayLodgingCandidates =
      'lodgingAreaId' in day
        ? input.lodgingCandidates.filter(
            (candidate) => candidate.areaId === day.lodgingAreaId,
          )
        : [];
    const total = day.routeSegmentIds.reduce(
      (acc, segmentId) => {
        const segment = input.routeSegments[segmentId];
        return {
          km: acc.km + (segment?.fallbackKm ?? 0),
          minutes: acc.minutes + (segment?.fallbackMinutes ?? 0),
        };
      },
      { km: 0, minutes: 0 },
    );
    const hasFatigueRisk = total.km > 150 || total.minutes > 180;
    const csvSummary = buildCsvSummary({
      day,
      places: input.places,
      routeSegments: input.routeSegments,
      csvPlaceSummaries: input.csvPlaceSummaries,
    });
    const aiSuggestedPlaceId = aiLodgingByDate[day.date];
    const aiSuggestedNameZh = aiSuggestedPlaceId
      ? input.places[aiSuggestedPlaceId]?.nameZh
      : undefined;

    return {
      date: day.date,
      labelZh: day.labelZh,
      titleZh: day.titleZh,
      route: {
        startNameZh,
        stopNamesZh,
        endNameZh,
        routeNamesZh,
      },
      lodging: {
        targetZh: day.lodgingTargetZh,
        candidateNamesZh: dayLodgingCandidates.map((candidate) => candidate.nameZh),
        aiSuggestedNameZh,
        confirmed: day.confirmedLodging,
      },
      csvSummary,
      aiSuggestionZh: buildAiSuggestion({
        lodgingTargetZh: day.lodgingTargetZh,
        totalKm: total.km,
        totalMinutes: total.minutes,
        stopCount: day.stopIds.length,
        csvCount: csvSummary.items.length,
        hasFatigueRisk,
      }),
      drive: {
        totalKm: total.km,
        totalMinutes: total.minutes,
        distanceLabelZh: formatDistance(total.km),
        durationLabelZh: formatDuration(total.minutes),
        hasFatigueRisk,
      },
      actions: buildActions({
        day,
        routeNamesZh,
        lodgingTargetZh: day.lodgingTargetZh,
        lodgingSearchQueryZh: day.confirmedLodging?.hotelName,
        endNameZh,
      }),
    };
  });
}
