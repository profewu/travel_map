export type DisasterProviderId = 'jma' | 'nied' | 'gsi';
export type DisasterAlertStatus = 'none' | 'attention' | 'warning';

export interface DisasterSourceMeta {
  provider: DisasterProviderId;
  providerNameZh: string;
  productNameZh: string;
  sourceUrl: string;
  isMock: true;
}

export interface DisasterGeoPoint {
  lat: number;
  lng: number;
}

export interface DisasterEpicenter extends DisasterGeoPoint {
  id: string;
  nameZh: string;
  occurredAtJst: string;
  magnitude: number;
  depthKm: number;
  maxIntensityZh: string;
  summaryZh: string;
}

export interface DisasterIntensityPoint extends DisasterGeoPoint {
  id: string;
  nameZh: string;
  intensityZh: string;
  intensityClass: '2' | '3' | '4' | '5-lower' | '5-upper';
}

export interface DisasterEvent {
  id: string;
  titleZh: string;
  occurredAtJst: string;
  regionZh: string;
  magnitude: number;
  maxIntensityZh: string;
  status: Exclude<DisasterAlertStatus, 'none'>;
  summaryZh: string;
}

export interface ItineraryDisasterAlert extends DisasterGeoPoint {
  id: string;
  placeId: string;
  placeNameZh: string;
  dayLabelZh: string;
  status: DisasterAlertStatus;
  distanceKmToEpicenter: number;
  messageZh: string;
}

export interface DisasterLegendItem {
  id: string;
  labelZh: string;
  descriptionZh: string;
  markerClass: string;
}

export interface DisasterDataset {
  asOfJst: string;
  regionNameZh: string;
  sourceHintZh: string;
  sources: DisasterSourceMeta[];
  epicenter: DisasterEpicenter;
  intensityPoints: DisasterIntensityPoint[];
  events: DisasterEvent[];
  itineraryAlerts: ItineraryDisasterAlert[];
  legend: DisasterLegendItem[];
}

export interface ItineraryDisasterSummary {
  status: DisasterAlertStatus;
  labelZh: string;
  messageZh: string;
  totalAlertCount: number;
  attentionPlaceNames: string[];
}

export interface DisasterDataProvider {
  loadDisasterDataset(): Promise<DisasterDataset>;
}

export const staticDisasterDataset: DisasterDataset = {
  asOfJst: '2026-05-11 09:30 JST',
  regionNameZh: '日本 / 北海道',
  sourceHintZh: 'JMA / NIED / GSI 可作為未來官方資料來源',
  sources: [
    {
      provider: 'jma',
      providerNameZh: '日本氣象廳',
      productNameZh: '地震情報',
      sourceUrl: 'https://www.jma.go.jp/',
      isMock: true,
    },
    {
      provider: 'nied',
      providerNameZh: '防災科研',
      productNameZh: '強震觀測',
      sourceUrl: 'https://www.kyoshin.bosai.go.jp/',
      isMock: true,
    },
    {
      provider: 'gsi',
      providerNameZh: '國土地理院',
      productNameZh: '地理院地圖',
      sourceUrl: 'https://maps.gsi.go.jp/',
      isMock: true,
    },
  ],
  epicenter: {
    id: 'eq-urakawa-2026-05-11',
    nameZh: '浦河沖',
    occurredAtJst: '2026-05-11 08:42 JST',
    lat: 42.1,
    lng: 142.8,
    magnitude: 5.2,
    depthKm: 48,
    maxIntensityZh: '震度4',
    summaryZh: '模擬地震事件，用於旅程防災監控畫面與未來 API 介面驗證。',
  },
  intensityPoints: [
    {
      id: 'int-urakawa',
      nameZh: '浦河町',
      lat: 42.17,
      lng: 142.77,
      intensityZh: '震度4',
      intensityClass: '4',
    },
    {
      id: 'int-toya',
      nameZh: '洞爺湖町',
      lat: 42.56,
      lng: 140.82,
      intensityZh: '震度3',
      intensityClass: '3',
    },
    {
      id: 'int-sapporo',
      nameZh: '札幌市',
      lat: 43.06,
      lng: 141.35,
      intensityZh: '震度2',
      intensityClass: '2',
    },
  ],
  events: [
    {
      id: 'event-urakawa-2026-05-11',
      titleZh: '浦河沖 M5.2 地震（模擬）',
      occurredAtJst: '2026-05-11 08:42 JST',
      regionZh: '浦河沖',
      magnitude: 5.2,
      maxIntensityZh: '震度4',
      status: 'attention',
      summaryZh: '北海道南部與太平洋側有震度觀測，行程道路目前以注意等級追蹤。',
    },
    {
      id: 'event-hidaka-aftershock',
      titleZh: '日高地方微震（模擬）',
      occurredAtJst: '2026-05-11 07:15 JST',
      regionZh: '日高地方',
      magnitude: 3.6,
      maxIntensityZh: '震度2',
      status: 'attention',
      summaryZh: '未達重大警示門檻，保留於近期列表供趨勢判讀。',
    },
  ],
  itineraryAlerts: [
    {
      id: 'alert-lake-toya',
      placeId: 'lake-toya',
      placeNameZh: '洞爺湖',
      dayLabelZh: '6/28',
      lat: 42.6,
      lng: 140.84,
      status: 'attention',
      distanceKmToEpicenter: 172,
      messageZh: '洞爺湖位於模擬震度3觀測圈，山區與湖畔道路請留意最新交通資訊。',
    },
    {
      id: 'alert-sapporo',
      placeId: 'sapporo',
      placeNameZh: '札幌',
      dayLabelZh: '7/1',
      lat: 43.06,
      lng: 141.35,
      status: 'attention',
      distanceKmToEpicenter: 138,
      messageZh: '札幌目前無重大警示，但可能有交通延遲與臨時管制資訊。',
    },
  ],
  legend: [
    {
      id: 'epicenter',
      labelZh: '震央',
      descriptionZh: 'X 標記顯示模擬震央位置',
      markerClass: 'legend-epicenter-marker',
    },
    {
      id: 'intensity',
      labelZh: '震度圓點',
      descriptionZh: '圓點大小與色階代表觀測震度',
      markerClass: 'legend-intensity-marker',
    },
    {
      id: 'itinerary-alert',
      labelZh: '行程警示',
      descriptionZh: '行程點附近的注意或警戒摘要',
      markerClass: 'legend-itinerary-alert-marker',
    },
  ],
};

export const staticDisasterProvider: DisasterDataProvider = {
  async loadDisasterDataset() {
    return staticDisasterDataset;
  },
};

export function buildItineraryDisasterSummary(
  alerts: ItineraryDisasterAlert[],
): ItineraryDisasterSummary {
  const activeAlerts = alerts.filter((alert) => alert.status !== 'none');
  const hasWarning = activeAlerts.some((alert) => alert.status === 'warning');
  const attentionPlaceNames = activeAlerts.map((alert) => alert.placeNameZh);

  if (activeAlerts.length === 0) {
    return {
      status: 'none',
      labelZh: '目前無重大警示 / 注意',
      messageZh: '目前無重大警示 / 注意，仍建議每日出發前確認官方資訊。',
      totalAlertCount: 0,
      attentionPlaceNames: [],
    };
  }

  return {
    status: hasWarning ? 'warning' : 'attention',
    labelZh: hasWarning ? '警戒' : '注意',
    messageZh: `目前無重大警示；${attentionPlaceNames.join('、')} 列為注意追蹤。`,
    totalAlertCount: activeAlerts.length,
    attentionPlaceNames,
  };
}
