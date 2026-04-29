export type PlaceCategory =
  | 'airport'
  | 'city'
  | 'coast'
  | 'lake'
  | 'mountain'
  | 'onsen'
  | 'distillery'
  | 'food';

export interface Place {
  id: string;
  nameZh: string;
  nameLocal?: string;
  lat: number;
  lng: number;
  category: PlaceCategory;
  descriptionZh: string;
  suggestedDurationZh?: string;
  parkingNoteZh?: string;
}

export interface RouteSegment {
  id: string;
  fromPlaceId: string;
  toPlaceId: string;
  fallbackMinutes: number;
  fallbackKm: number;
  noteZh: string;
}

interface TripDayBase {
  date: string;
  labelZh: string;
  titleZh: string;
  startPlaceId: string;
  endPlaceId: string;
  weatherPlaceId: string;
  stopIds: string[];
  routeSegmentIds: string[];
  summaryZh: string;
  lodgingTargetZh: string;
  driveNoteZh: string;
}

export interface OvernightTripDay extends TripDayBase {
  lodgingAreaId: string;
}

export interface DepartureTripDay extends TripDayBase {
  date: '2026-07-03';
  lodgingAreaId?: never;
  lodgingTargetZh: '無。';
}

export type TripDay = OvernightTripDay | DepartureTripDay;

export interface LodgingCandidate {
  id: string;
  areaId: string;
  nameZh: string;
  type: 'city' | 'onsen-resort' | 'airport-buffer';
  starLevel: number;
  budgetRiskZh: string;
  parkingZh: string;
  fitZh: string;
  searchUrl: string;
}

export const places: Record<string, Place> = {
  'new-chitose-airport': {
    id: 'new-chitose-airport',
    nameZh: '新千歲機場',
    nameLocal: 'New Chitose Airport',
    lat: 42.7752,
    lng: 141.6923,
    category: 'airport',
    descriptionZh: '北海道主要空港，適合自駕取車與回程還車。',
  },
  sapporo: {
    id: 'sapporo',
    nameZh: '札幌',
    nameLocal: 'Sapporo',
    lat: 43.0618,
    lng: 141.3545,
    category: 'city',
    descriptionZh: '北海道最大城市，餐飲與購物資源完整。',
  },
  'mt-moiwa': {
    id: 'mt-moiwa',
    nameZh: '藻岩山',
    nameLocal: 'Mt. Moiwa',
    lat: 43.0229,
    lng: 141.3221,
    category: 'mountain',
    descriptionZh: '可俯瞰札幌夜景與城市地形。',
  },
  otaru: {
    id: 'otaru',
    nameZh: '小樽',
    nameLocal: 'Otaru',
    lat: 43.1907,
    lng: 140.9947,
    category: 'city',
    descriptionZh: '港町散策與運河夜景，適合慢節奏停留。',
  },
  yoichi: {
    id: 'yoichi',
    nameZh: '余市',
    nameLocal: 'Yoichi',
    lat: 43.1964,
    lng: 140.7872,
    category: 'distillery',
    descriptionZh: '以威士忌蒸餾所與果園著名。',
  },
  shakotan: {
    id: 'shakotan',
    nameZh: '積丹',
    nameLocal: 'Shakotan',
    lat: 43.2996,
    lng: 140.5724,
    category: 'coast',
    descriptionZh: '積丹藍海岸線，適合停靠觀景。',
  },
  niseko: {
    id: 'niseko',
    nameZh: '二世古',
    nameLocal: 'Niseko',
    lat: 42.8048,
    lng: 140.6874,
    category: 'mountain',
    descriptionZh: '山景與溫泉度假區，夏季也適合慢旅。',
  },
  'lake-toya': {
    id: 'lake-toya',
    nameZh: '洞爺湖',
    nameLocal: 'Lake Toya',
    lat: 42.5655,
    lng: 140.8267,
    category: 'lake',
    descriptionZh: '火山地形環湖景觀，沿線停留點多。',
  },
  'showa-shinzan-usuzan': {
    id: 'showa-shinzan-usuzan',
    nameZh: '昭和新山／有珠山',
    nameLocal: 'Showa Shinzan / Usuzan',
    lat: 42.5431,
    lng: 140.8648,
    category: 'mountain',
    descriptionZh: '洞爺湖周邊代表性火山景點。',
  },
  noboribetsu: {
    id: 'noboribetsu',
    nameZh: '登別',
    nameLocal: 'Noboribetsu',
    lat: 42.4522,
    lng: 141.1791,
    category: 'onsen',
    descriptionZh: '北海道代表溫泉區，適合安排一晚休息。',
  },
  jigokudani: {
    id: 'jigokudani',
    nameZh: '地獄谷',
    nameLocal: 'Jigokudani',
    lat: 42.4924,
    lng: 141.1441,
    category: 'onsen',
    descriptionZh: '火山地熱景觀，步道短且易走。',
  },
  'lake-shikotsu': {
    id: 'lake-shikotsu',
    nameZh: '支笏湖',
    nameLocal: 'Lake Shikotsu',
    lat: 42.7748,
    lng: 141.4033,
    category: 'lake',
    descriptionZh: '透明度高的火口湖，回程前緩衝點。',
  },
  chitose: {
    id: 'chitose',
    nameZh: '千歲',
    nameLocal: 'Chitose',
    lat: 42.8236,
    lng: 141.6523,
    category: 'city',
    descriptionZh: '機場周邊城市，利於最後一晚機場緩衝。',
  },
};

export const routeSegments: Record<string, RouteSegment> = {
  'cts-sapporo': {
    id: 'cts-sapporo',
    fromPlaceId: 'new-chitose-airport',
    toPlaceId: 'sapporo',
    fallbackMinutes: 65,
    fallbackKm: 50,
    noteZh: '抵達後北上進札幌市區。',
  },
  'sapporo-moiwa': {
    id: 'sapporo-moiwa',
    fromPlaceId: 'sapporo',
    toPlaceId: 'mt-moiwa',
    fallbackMinutes: 30,
    fallbackKm: 9,
    noteZh: '札幌市內短程移動。',
  },
  'moiwa-sapporo': {
    id: 'moiwa-sapporo',
    fromPlaceId: 'mt-moiwa',
    toPlaceId: 'sapporo',
    fallbackMinutes: 30,
    fallbackKm: 9,
    noteZh: '藻岩山回札幌住宿區。',
  },
  'sapporo-otaru': {
    id: 'sapporo-otaru',
    fromPlaceId: 'sapporo',
    toPlaceId: 'otaru',
    fallbackMinutes: 55,
    fallbackKm: 38,
    noteZh: '沿海線往小樽。',
  },
  'otaru-yoichi': {
    id: 'otaru-yoichi',
    fromPlaceId: 'otaru',
    toPlaceId: 'yoichi',
    fallbackMinutes: 35,
    fallbackKm: 22,
    noteZh: '由小樽前往余市。',
  },
  'yoichi-otaru': {
    id: 'yoichi-otaru',
    fromPlaceId: 'yoichi',
    toPlaceId: 'otaru',
    fallbackMinutes: 35,
    fallbackKm: 22,
    noteZh: '余市折返小樽住宿。',
  },
  'yoichi-shakotan': {
    id: 'yoichi-shakotan',
    fromPlaceId: 'yoichi',
    toPlaceId: 'shakotan',
    fallbackMinutes: 70,
    fallbackKm: 48,
    noteZh: '海岸線彎道較多，建議白天行駛。',
  },
  'shakotan-niseko': {
    id: 'shakotan-niseko',
    fromPlaceId: 'shakotan',
    toPlaceId: 'niseko',
    fallbackMinutes: 145,
    fallbackKm: 105,
    noteZh: '西海岸轉入山區路段。',
  },
  'niseko-toya': {
    id: 'niseko-toya',
    fromPlaceId: 'niseko',
    toPlaceId: 'lake-toya',
    fallbackMinutes: 85,
    fallbackKm: 55,
    noteZh: '山區南下至洞爺湖。',
  },
  'toya-showa': {
    id: 'toya-showa',
    fromPlaceId: 'lake-toya',
    toPlaceId: 'showa-shinzan-usuzan',
    fallbackMinutes: 20,
    fallbackKm: 8,
    noteZh: '洞爺湖周邊短程。',
  },
  'showa-noboribetsu': {
    id: 'showa-noboribetsu',
    fromPlaceId: 'showa-shinzan-usuzan',
    toPlaceId: 'noboribetsu',
    fallbackMinutes: 75,
    fallbackKm: 55,
    noteZh: '火山景區後轉往溫泉區。',
  },
  'noboribetsu-jigokudani': {
    id: 'noboribetsu-jigokudani',
    fromPlaceId: 'noboribetsu',
    toPlaceId: 'jigokudani',
    fallbackMinutes: 10,
    fallbackKm: 4,
    noteZh: '登別市區至地獄谷短程。',
  },
  'jigokudani-shikotsu': {
    id: 'jigokudani-shikotsu',
    fromPlaceId: 'jigokudani',
    toPlaceId: 'lake-shikotsu',
    fallbackMinutes: 95,
    fallbackKm: 74,
    noteZh: '回程前往支笏湖。',
  },
  'shikotsu-chitose': {
    id: 'shikotsu-chitose',
    fromPlaceId: 'lake-shikotsu',
    toPlaceId: 'chitose',
    fallbackMinutes: 35,
    fallbackKm: 27,
    noteZh: '湖區下山進入千歲。',
  },
  'chitose-cts': {
    id: 'chitose-cts',
    fromPlaceId: 'chitose',
    toPlaceId: 'new-chitose-airport',
    fallbackMinutes: 15,
    fallbackKm: 7,
    noteZh: '最後進機場還車。',
  },
};

export const tripDays: TripDay[] = [
  {
    date: '2026-06-25',
    labelZh: '6/25',
    titleZh: '抵達新千歲，進札幌',
    startPlaceId: 'new-chitose-airport',
    endPlaceId: 'sapporo',
    weatherPlaceId: 'sapporo',
    lodgingAreaId: 'sapporo',
    stopIds: [],
    routeSegmentIds: ['cts-sapporo'],
    summaryZh: '取車後直接進札幌，晚餐與補給為主。',
    lodgingTargetZh: '札幌市區 3 星以上飯店',
    driveNoteZh: '首日以短程為主，保留彈性。',
  },
  {
    date: '2026-06-26',
    labelZh: '6/26',
    titleZh: '札幌市區慢遊',
    startPlaceId: 'sapporo',
    endPlaceId: 'sapporo',
    weatherPlaceId: 'sapporo',
    lodgingAreaId: 'sapporo',
    stopIds: ['mt-moiwa'],
    routeSegmentIds: ['sapporo-moiwa', 'moiwa-sapporo'],
    summaryZh: '市區散步加藻岩山視野點，避免長距離駕駛。',
    lodgingTargetZh: '續住札幌',
    driveNoteZh: '市區停車場優先。',
  },
  {
    date: '2026-06-27',
    labelZh: '6/27',
    titleZh: '札幌至小樽，延伸余市後返小樽',
    startPlaceId: 'sapporo',
    endPlaceId: 'otaru',
    weatherPlaceId: 'otaru',
    lodgingAreaId: 'otaru',
    stopIds: ['yoichi'],
    routeSegmentIds: ['sapporo-otaru', 'otaru-yoichi', 'yoichi-otaru'],
    summaryZh: '白天小樽與余市，夜宿小樽維持慢節奏。',
    lodgingTargetZh: '小樽港區或運河周邊',
    driveNoteZh: '海線車流較穩定。',
  },
  {
    date: '2026-06-28',
    labelZh: '6/28',
    titleZh: '小樽經余市、積丹，進二世古',
    startPlaceId: 'otaru',
    endPlaceId: 'niseko',
    weatherPlaceId: 'shakotan',
    lodgingAreaId: 'niseko',
    stopIds: ['yoichi', 'shakotan'],
    routeSegmentIds: ['otaru-yoichi', 'yoichi-shakotan', 'shakotan-niseko'],
    summaryZh: '主打積丹海岸線，傍晚轉往山區住宿。',
    lodgingTargetZh: '二世古度假區',
    driveNoteZh: '山海轉換路段，提早出發。',
  },
  {
    date: '2026-06-29',
    labelZh: '6/29',
    titleZh: '二世古至洞爺湖',
    startPlaceId: 'niseko',
    endPlaceId: 'lake-toya',
    weatherPlaceId: 'lake-toya',
    lodgingAreaId: 'lake-toya',
    stopIds: [],
    routeSegmentIds: ['niseko-toya'],
    summaryZh: '縮短車程，下午安排湖畔步行。',
    lodgingTargetZh: '洞爺湖溫泉區',
    driveNoteZh: '中短程移動，保留休息時間。',
  },
  {
    date: '2026-06-30',
    labelZh: '6/30',
    titleZh: '洞爺湖、昭和新山有珠山，至登別',
    startPlaceId: 'lake-toya',
    endPlaceId: 'noboribetsu',
    weatherPlaceId: 'lake-toya',
    lodgingAreaId: 'noboribetsu',
    stopIds: ['showa-shinzan-usuzan'],
    routeSegmentIds: ['toya-showa', 'showa-noboribetsu'],
    summaryZh: '火山地形景點後，晚間入住登別溫泉。',
    lodgingTargetZh: '登別溫泉旅館',
    driveNoteZh: '景點停留時間可彈性調整。',
  },
  {
    date: '2026-07-01',
    labelZh: '7/1',
    titleZh: '登別地獄谷至支笏湖',
    startPlaceId: 'noboribetsu',
    endPlaceId: 'lake-shikotsu',
    weatherPlaceId: 'noboribetsu',
    lodgingAreaId: 'lake-shikotsu',
    stopIds: ['jigokudani'],
    routeSegmentIds: ['noboribetsu-jigokudani', 'jigokudani-shikotsu'],
    summaryZh: '上午地獄谷，下午前往支笏湖湖畔。',
    lodgingTargetZh: '支笏湖周邊或千歲方向',
    driveNoteZh: '午後留意山區天氣。',
  },
  {
    date: '2026-07-02',
    labelZh: '7/2',
    titleZh: '支笏湖至千歲緩衝日',
    startPlaceId: 'lake-shikotsu',
    endPlaceId: 'chitose',
    weatherPlaceId: 'chitose',
    lodgingAreaId: 'chitose',
    stopIds: [],
    routeSegmentIds: ['shikotsu-chitose'],
    summaryZh: '回到機場圈，控制最後一天風險。',
    lodgingTargetZh: '千歲市區或機場周邊',
    driveNoteZh: '車程短，安排採買與整理行李。',
  },
  {
    date: '2026-07-03',
    labelZh: '7/3',
    titleZh: '千歲至新千歲機場返程',
    startPlaceId: 'chitose',
    endPlaceId: 'new-chitose-airport',
    weatherPlaceId: 'new-chitose-airport',
    stopIds: [],
    routeSegmentIds: ['chitose-cts'],
    summaryZh: '機場還車、辦理登機，完成環線。',
    lodgingTargetZh: '無。',
    driveNoteZh: '預留還車與安檢時間。',
  },
];

export const lodgingCandidates: LodgingCandidate[] = [
  {
    id: 'sapporo-odori-1',
    areaId: 'sapporo',
    nameZh: '札幌大通商務飯店候選',
    type: 'city',
    starLevel: 3,
    budgetRiskZh: '旺季房價波動中等',
    parkingZh: '附合作停車場',
    fitZh: '首晚市區補給方便',
    searchUrl: 'https://www.google.com/travel/hotels/Sapporo',
  },
  {
    id: 'sapporo-sta-1',
    areaId: 'sapporo',
    nameZh: '札幌站前飯店候選',
    type: 'city',
    starLevel: 4,
    budgetRiskZh: '週末可能上浮',
    parkingZh: '可步行至車站商圈',
    fitZh: '交通與用餐密度高',
    searchUrl: 'https://www.booking.com/city/jp/sapporo.zh-tw.html',
  },
  {
    id: 'otaru-canal-1',
    areaId: 'otaru',
    nameZh: '小樽運河周邊飯店候選',
    type: 'city',
    starLevel: 3,
    budgetRiskZh: '假日較搶手',
    parkingZh: '部分提供付費停車',
    fitZh: '夜間散步方便',
    searchUrl: 'https://www.agoda.com/zh-tw/city/otaru-jp.html',
  },
  {
    id: 'niseko-resort-1',
    areaId: 'niseko',
    nameZh: '二世古度假旅宿候選',
    type: 'onsen-resort',
    starLevel: 4,
    budgetRiskZh: '度假區價格偏高',
    parkingZh: '多數含停車',
    fitZh: '山景與放鬆行程',
    searchUrl: 'https://www.google.com/travel/hotels/Niseko',
  },
  {
    id: 'toya-onsen-1',
    areaId: 'lake-toya',
    nameZh: '洞爺湖溫泉飯店候選',
    type: 'onsen-resort',
    starLevel: 4,
    budgetRiskZh: '景觀房價差較大',
    parkingZh: '通常有免費停車',
    fitZh: '湖景休息夜',
    searchUrl: 'https://www.jalan.net/onsen/OSN_50002/',
  },
  {
    id: 'noboribetsu-onsen-1',
    areaId: 'noboribetsu',
    nameZh: '登別溫泉旅館候選',
    type: 'onsen-resort',
    starLevel: 4,
    budgetRiskZh: '熱門時段價格偏高',
    parkingZh: '溫泉街周邊停車可行',
    fitZh: '泡湯與休息重點日',
    searchUrl: 'https://www.google.com/travel/hotels/Noboribetsu',
  },
  {
    id: 'shikotsu-lakeside-1',
    areaId: 'lake-shikotsu',
    nameZh: '支笏湖湖畔旅宿候選',
    type: 'onsen-resort',
    starLevel: 3,
    budgetRiskZh: '房間數較少需提早找',
    parkingZh: '湖區旅宿多附停車',
    fitZh: '回程前放鬆緩衝',
    searchUrl: 'https://www.booking.com/landmark/jp/lake-shikotsu.zh-tw.html',
  },
  {
    id: 'chitose-airport-1',
    areaId: 'chitose',
    nameZh: '千歲機場緩衝飯店候選',
    type: 'airport-buffer',
    starLevel: 3,
    budgetRiskZh: '平日相對穩定',
    parkingZh: '機場接駁或停車服務',
    fitZh: '返程日風險控制',
    searchUrl: 'https://www.google.com/travel/hotels/Chitose',
  },
  {
    id: 'chitose-airport-2',
    areaId: 'chitose',
    nameZh: '千歲站前商務飯店候選',
    type: 'airport-buffer',
    starLevel: 3,
    budgetRiskZh: '高峰期仍可能客滿',
    parkingZh: '車站周邊多停車位',
    fitZh: '晚到早飛都方便',
    searchUrl: 'https://www.agoda.com/zh-tw/city/chitose-jp.html',
  },
];
