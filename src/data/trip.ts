export type PlaceCategory =
  | 'airport'
  | 'city'
  | 'coast'
  | 'lake'
  | 'mountain'
  | 'onsen'
  | 'distillery'
  | 'food'
  | 'hotel'
  | 'park'
  | 'shopping'
  | 'transport';

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
  addressZh?: string;
  mapcode?: string;
  phone?: string;
}

export interface RouteSegment {
  id: string;
  fromPlaceId: string;
  toPlaceId: string;
  fallbackMinutes: number;
  fallbackKm: number;
  noteZh: string;
}

export interface ConfirmedLodging {
  provider: string;
  statusZh: string;
  bookingNumber: string;
  hotelName: string;
  checkInDate: string;
  checkOutDate: string;
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
  confirmedLodging?: ConfirmedLodging;
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
  mapcode?: string;
  phone?: string;
}

export const places: Record<string, Place> = {
  'new-chitose-airport': {
    id: 'new-chitose-airport',
    nameZh: '新千歲機場',
    nameLocal: 'New Chitose Airport',
    lat: 42.7752,
    lng: 141.6923,
    category: 'airport',
    descriptionZh:
      '北海道主要空港。本版依 CSV 的 BR116 抵達、租車與回程機場巴士資訊安排。',
    mapcode: '113 742 186*01',
    phone: '0123-23-0111',
  },
  eniwa: {
    id: 'eniwa',
    nameZh: '惠庭',
    nameLocal: 'Eniwa',
    lat: 42.8826,
    lng: 141.5778,
    category: 'city',
    descriptionZh:
      '新千歲與札幌之間的緩衝城市，適合抵達日住宿與親子活動。',
  },
  'eniwa-fairfield': {
    id: 'eniwa-fairfield',
    nameZh: '北海道惠庭萬楓酒店',
    nameLocal: 'Fairfield by Marriott Hokkaido Eniwa',
    lat: 42.8866,
    lng: 141.5656,
    category: 'hotel',
    descriptionZh:
      'CSV 6/25 住宿核心。與花路惠庭相鄰，抵達日不用急著北上札幌。',
    addressZh:
      '日本〒061-1375 Hokkaido, Eniwa, Minamishimamatsu, 828-9',
    parkingNoteZh: '以住宿停車為主，出發前仍需確認飯店最新停車規則。',
  },
  'hanaroad-eniwa': {
    id: 'hanaroad-eniwa',
    nameZh: '道與川之驛 花路惠庭',
    nameLocal: 'Michi-to-Kawa-no-Eki Hanaroad Eniwa',
    lat: 42.8872,
    lng: 141.565,
    category: 'food',
    descriptionZh:
      'CSV 提到可買惠庭銅鑼燒，適合抵達日補給與短暫伸展。',
    suggestedDurationZh: '30-45 分',
  },
  'ecorin-village': {
    id: 'ecorin-village',
    nameZh: '惠庭 ECORIN村',
    nameLocal: 'Ecorin Village',
    lat: 42.8789,
    lng: 141.6268,
    category: 'park',
    descriptionZh: '惠庭親子自然景點，可依抵達時間決定是否只做短停留。',
    suggestedDurationZh: '60-90 分',
  },
  'eniwa-honoka': {
    id: 'eniwa-honoka',
    nameZh: '惠庭溫泉 HONOKA',
    nameLocal: 'Eniwa Onsen Honoka',
    lat: 42.8818,
    lng: 141.5901,
    category: 'onsen',
    descriptionZh:
      'CSV 備註的碳酸水素溫泉、露天溫泉、足湯與桑拿候選。抵達日若體力不足可跳過。',
    suggestedDurationZh: '90-120 分',
  },
  'forest-adventure-eniwa': {
    id: 'forest-adventure-eniwa',
    nameZh: 'Forest Adventure Eniwa',
    nameLocal: 'フォレストアドベンチャー・恵庭',
    lat: 42.8966,
    lng: 141.5282,
    category: 'park',
    descriptionZh:
      'CSV 6/26 親子戶外活動，位於ルルマップ自然公園ふれらんど內。',
    addressZh:
      '275 Nishishimamatsu, Eniwa, Hokkaido 061-1356 Japan',
    suggestedDurationZh: '1.5-2.5 小時',
  },
  'kamameshi-ichie': {
    id: 'kamameshi-ichie',
    nameZh: '釜飯 ICHIE',
    nameLocal: 'いちえ',
    lat: 42.8833,
    lng: 141.5772,
    category: 'food',
    descriptionZh:
      '惠庭人氣釜飯。CSV 特別標註海膽、鮭魚卵與茶泡飯吃法。',
    suggestedDurationZh: '60-75 分',
  },
  'lake-shikotsu': {
    id: 'lake-shikotsu',
    nameZh: '支笏湖',
    nameLocal: 'Lake Shikotsu',
    lat: 42.7748,
    lng: 141.4033,
    category: 'lake',
    descriptionZh:
      'CSV 的「支芴湖」依地理與內容修正為支笏湖。可看展望台、野鳥之森與遊覽船碼頭湖色。',
    suggestedDurationZh: '60-120 分',
    mapcode: '867 063 323*85',
    phone: '0123-25-2404',
  },
  'tarumae-garo': {
    id: 'tarumae-garo',
    nameZh: '樽前GARO',
    nameLocal: '樽前ガロー',
    lat: 42.6547,
    lng: 141.2796,
    category: 'coast',
    descriptionZh:
      'CSV 6/26 苫小牧自然景點。若支笏湖停留太久，可作為可刪減點避免當日過重。',
    addressZh: '北海道苫小牧市字樽前',
    suggestedDurationZh: '45-60 分',
    parkingNoteZh: '自駕沿國道 36 號，看到樽前ガロー看板後北進。',
  },
  noboribetsu: {
    id: 'noboribetsu',
    nameZh: '登別',
    nameLocal: 'Noboribetsu',
    lat: 42.4522,
    lng: 141.1791,
    category: 'onsen',
    descriptionZh: '北海道代表溫泉區，作為 6/26 晚間休息點。',
    mapcode: '603 287 235*11',
    phone: '0143-84-3311',
  },
  'park-hotel-miyabitei': {
    id: 'park-hotel-miyabitei',
    nameZh: 'Park Hotel Miyabitei 雅亭酒店',
    nameLocal: '登別 雅亭',
    lat: 42.492,
    lng: 141.1458,
    category: 'hotel',
    descriptionZh:
      'CSV 6/26 住宿候選。作為登別溫泉區落點，可隔天早上先走地獄谷與大湯沼。',
    suggestedDurationZh: '住宿',
  },
  jigokudani: {
    id: 'jigokudani',
    nameZh: '登別地獄谷',
    nameLocal: 'Jigokudani',
    lat: 42.4924,
    lng: 141.1441,
    category: 'onsen',
    descriptionZh: 'CSV 6/27 登別核心景點，步道短且適合早上安排。',
    suggestedDurationZh: '60 分',
    mapcode: '603 287 235*11',
    phone: '0143-84-3311',
  },
  oyunuma: {
    id: 'oyunuma',
    nameZh: '大湯沼',
    nameLocal: 'Oyunuma',
    lat: 42.5011,
    lng: 141.1479,
    category: 'onsen',
    descriptionZh:
      'CSV 與地獄谷同列的登別地熱景點。安排在地獄谷後，避免重複進出登別。',
    suggestedDurationZh: '30-45 分',
  },
  'nachu-no-mori': {
    id: 'nachu-no-mori',
    nameZh: 'ナチュの森',
    nameLocal: 'Nachu no Mori',
    lat: 42.4675,
    lng: 141.2318,
    category: 'park',
    descriptionZh:
      '白老親子景點。CSV 備註有戶外遊樂花園、室內充氣遊樂場，建議帶換洗衣物。',
    addressZh: '北海道白老郡白老町虎杖浜393-12',
    suggestedDurationZh: '90-150 分',
    parkingNoteZh: '有專屬停車場；週三、週四公休需出發前再確認。',
  },
  'cape-chikyu': {
    id: 'cape-chikyu',
    nameZh: '地球岬展望台',
    nameLocal: 'Cape Chikyu',
    lat: 42.3013,
    lng: 141.0008,
    category: 'coast',
    descriptionZh:
      'CSV 的室蘭景點。放在白老後、洞爺湖前，避免從登別直接拉到小樽的長距離折返。',
    suggestedDurationZh: '30-45 分',
  },
  'lake-toya': {
    id: 'lake-toya',
    nameZh: '洞爺湖',
    nameLocal: 'Lake Toya',
    lat: 42.5655,
    lng: 140.8267,
    category: 'lake',
    descriptionZh:
      'CSV 6/27 提到的湖區。本版改為 6/27 夜宿，切開登別/白老/室蘭到小樽的過重路段。',
    mapcode: '321 518 537*00',
    phone: '0142-75-2446',
  },
  otaru: {
    id: 'otaru',
    nameZh: '小樽',
    nameLocal: 'Otaru',
    lat: 43.1907,
    lng: 140.9947,
    category: 'city',
    descriptionZh:
      'CSV 原列 6/27 小樽，本版移到 6/28，讓南部景點與小樽中間以洞爺湖拆段。',
    mapcode: '493 690 414*33',
    phone: '0134-33-1661',
  },
  'rinyu-market': {
    id: 'rinyu-market',
    nameZh: '鱗友朝市',
    nameLocal: 'Rinyu Morning Market',
    lat: 43.2056,
    lng: 141.0112,
    category: 'food',
    descriptionZh:
      'CSV 6/28 早市與帝王蟹備註。重排後放在小樽住宿隔天早上，才符合朝市節奏。',
    suggestedDurationZh: '60-90 分',
  },
  sapporo: {
    id: 'sapporo',
    nameZh: '札幌',
    nameLocal: 'Sapporo',
    lat: 43.0618,
    lng: 141.3545,
    category: 'city',
    descriptionZh:
      '後段 6/29-7/2 連住札幌，集中購物、美食、藻岩山與機場巴士準備。',
    mapcode: '9 523 036*60',
    phone: '011-213-5088',
  },
  'ario-sapporo': {
    id: 'ario-sapporo',
    nameZh: 'Ario 札幌',
    nameLocal: 'Ario Sapporo',
    lat: 43.0714,
    lng: 141.3744,
    category: 'shopping',
    descriptionZh:
      'CSV 札幌購物清單之一，包含 Workman Girl 候選。',
    suggestedDurationZh: '90-150 分',
  },
  'pokemon-center-sapporo': {
    id: 'pokemon-center-sapporo',
    nameZh: '寶可夢中心札幌',
    nameLocal: 'Pokemon Center Sapporo',
    lat: 43.068,
    lng: 141.349,
    category: 'shopping',
    descriptionZh: 'CSV 提到的北海道唯一寶可夢中心。',
    suggestedDurationZh: '45-75 分',
  },
  'sapporo-parco': {
    id: 'sapporo-parco',
    nameZh: '札幌 PARCO',
    nameLocal: 'Sapporo PARCO',
    lat: 43.0592,
    lng: 141.3542,
    category: 'shopping',
    descriptionZh:
      'CSV 提到貓福珊迪札幌 PARCO 7 樓新開幕，適合與市中心購物同日。',
    suggestedDurationZh: '45-90 分',
  },
  'sapporo-underground': {
    id: 'sapporo-underground',
    nameZh: '札幌地下街',
    nameLocal: 'Sapporo Underground Shopping Arcade',
    lat: 43.0603,
    lng: 141.3539,
    category: 'shopping',
    descriptionZh:
      'CSV 提到 KINOTOYA、3COINS 等地下街清單。作為雨天與採買緩衝。',
    suggestedDurationZh: '90-150 分',
  },
  'cocono-susukino': {
    id: 'cocono-susukino',
    nameZh: 'COCONO SUSUKINO',
    nameLocal: 'COCONO SUSUKINO',
    lat: 43.0556,
    lng: 141.3536,
    category: 'shopping',
    descriptionZh:
      'CSV 的薄野新地標，DONGURI 竹輪麵包與餐飲購物都可放在札幌連住日。',
    suggestedDurationZh: '60-120 分',
  },
  'mt-moiwa': {
    id: 'mt-moiwa',
    nameZh: '藻岩山',
    nameLocal: 'Mt. Moiwa',
    lat: 43.0229,
    lng: 141.3221,
    category: 'mountain',
    descriptionZh:
      'CSV 提醒接近黃昏搭纜車。本版放在札幌連住日，避免跟長途自駕同日。',
    suggestedDurationZh: '2-3 小時',
    mapcode: '493 503 663*33',
    phone: '011-561-8177',
  },
  'susukino-airport-bus-stop': {
    id: 'susukino-airport-bus-stop',
    nameZh: '薄野機場巴士搭乘處',
    nameLocal: 'New Chitose Airport Bus Susukino Stop',
    lat: 43.0559583,
    lng: 141.3538577,
    category: 'transport',
    descriptionZh:
      'CSV 7/1 交通備忘：行李多且住薄野附近時，機場巴士比 JR 轉地鐵更輕鬆。',
    addressZh:
      '日本〒064-0804 Hokkaido, Sapporo, Chuo Ward, Minami 4 Jonishi, 3 Chome',
    suggestedDurationZh: '出發前一天確認站牌',
  },
  yoichi: {
    id: 'yoichi',
    nameZh: '余市',
    nameLocal: 'Yoichi',
    lat: 43.1955,
    lng: 140.7835,
    category: 'distillery',
    descriptionZh: '保留作為 route service 測試用的既有西側座標，不納入本次主行程。',
  },
};

export const routeSegments: Record<string, RouteSegment> = {
  'cts-hanaroad-eniwa': {
    id: 'cts-hanaroad-eniwa',
    fromPlaceId: 'new-chitose-airport',
    toPlaceId: 'hanaroad-eniwa',
    fallbackMinutes: 30,
    fallbackKm: 23,
    noteZh: '抵達後取車，先到惠庭補給。',
  },
  'hanaroad-ecorin': {
    id: 'hanaroad-ecorin',
    fromPlaceId: 'hanaroad-eniwa',
    toPlaceId: 'ecorin-village',
    fallbackMinutes: 15,
    fallbackKm: 8,
    noteZh: '惠庭市內短程。',
  },
  'ecorin-honoka': {
    id: 'ecorin-honoka',
    fromPlaceId: 'ecorin-village',
    toPlaceId: 'eniwa-honoka',
    fallbackMinutes: 12,
    fallbackKm: 7,
    noteZh: '若抵達較晚，可跳過溫泉直接進飯店。',
  },
  'honoka-eniwa-fairfield': {
    id: 'honoka-eniwa-fairfield',
    fromPlaceId: 'eniwa-honoka',
    toPlaceId: 'eniwa-fairfield',
    fallbackMinutes: 8,
    fallbackKm: 5,
    noteZh: '晚間回惠庭住宿。',
  },
  'eniwa-fairfield-forest-adventure': {
    id: 'eniwa-fairfield-forest-adventure',
    fromPlaceId: 'eniwa-fairfield',
    toPlaceId: 'forest-adventure-eniwa',
    fallbackMinutes: 10,
    fallbackKm: 6,
    noteZh: '惠庭住宿到森林親子活動。',
  },
  'forest-adventure-kamameshi-ichie': {
    id: 'forest-adventure-kamameshi-ichie',
    fromPlaceId: 'forest-adventure-eniwa',
    toPlaceId: 'kamameshi-ichie',
    fallbackMinutes: 15,
    fallbackKm: 8,
    noteZh: '午餐轉往惠庭市區。',
  },
  'kamameshi-ichie-lake-shikotsu': {
    id: 'kamameshi-ichie-lake-shikotsu',
    fromPlaceId: 'kamameshi-ichie',
    toPlaceId: 'lake-shikotsu',
    fallbackMinutes: 50,
    fallbackKm: 42,
    noteZh: '午後進支笏湖，遊船需看天氣與末班時間。',
  },
  'lake-shikotsu-tarumae-garo': {
    id: 'lake-shikotsu-tarumae-garo',
    fromPlaceId: 'lake-shikotsu',
    toPlaceId: 'tarumae-garo',
    fallbackMinutes: 40,
    fallbackKm: 32,
    noteZh: '支笏湖後往苫小牧側，時間不足時可刪。',
  },
  'tarumae-garo-miyabitei': {
    id: 'tarumae-garo-miyabitei',
    fromPlaceId: 'tarumae-garo',
    toPlaceId: 'park-hotel-miyabitei',
    fallbackMinutes: 60,
    fallbackKm: 48,
    noteZh: '進登別溫泉住宿，避免再北上折返。',
  },
  'miyabitei-jigokudani': {
    id: 'miyabitei-jigokudani',
    fromPlaceId: 'park-hotel-miyabitei',
    toPlaceId: 'jigokudani',
    fallbackMinutes: 8,
    fallbackKm: 2,
    noteZh: '溫泉街內短程。',
  },
  'jigokudani-oyunuma': {
    id: 'jigokudani-oyunuma',
    fromPlaceId: 'jigokudani',
    toPlaceId: 'oyunuma',
    fallbackMinutes: 10,
    fallbackKm: 2,
    noteZh: '地獄谷與大湯沼連續安排。',
  },
  'oyunuma-nachu-no-mori': {
    id: 'oyunuma-nachu-no-mori',
    fromPlaceId: 'oyunuma',
    toPlaceId: 'nachu-no-mori',
    fallbackMinutes: 25,
    fallbackKm: 21,
    noteZh: '登別往白老親子景點。',
  },
  'nachu-no-mori-cape-chikyu': {
    id: 'nachu-no-mori-cape-chikyu',
    fromPlaceId: 'nachu-no-mori',
    toPlaceId: 'cape-chikyu',
    fallbackMinutes: 45,
    fallbackKm: 35,
    noteZh: '白老到室蘭展望台。',
  },
  'cape-chikyu-lake-toya': {
    id: 'cape-chikyu-lake-toya',
    fromPlaceId: 'cape-chikyu',
    toPlaceId: 'lake-toya',
    fallbackMinutes: 70,
    fallbackKm: 58,
    noteZh: '晚間落洞爺湖，切開前往小樽的長距離。',
  },
  'toya-otaru': {
    id: 'toya-otaru',
    fromPlaceId: 'lake-toya',
    toPlaceId: 'otaru',
    fallbackMinutes: 140,
    fallbackKm: 125,
    noteZh: '單純轉場日，避免同日再塞大量景點。',
  },
  'otaru-rinyu-market': {
    id: 'otaru-rinyu-market',
    fromPlaceId: 'otaru',
    toPlaceId: 'rinyu-market',
    fallbackMinutes: 6,
    fallbackKm: 2,
    noteZh: '小樽住宿隔天早上去朝市。',
  },
  'rinyu-market-sapporo': {
    id: 'rinyu-market-sapporo',
    fromPlaceId: 'rinyu-market',
    toPlaceId: 'sapporo',
    fallbackMinutes: 55,
    fallbackKm: 40,
    noteZh: '早市後進札幌，開始連住。',
  },
  'sapporo-ario': {
    id: 'sapporo-ario',
    fromPlaceId: 'sapporo',
    toPlaceId: 'ario-sapporo',
    fallbackMinutes: 15,
    fallbackKm: 5,
    noteZh: '札幌市內購物移動。',
  },
  'ario-pokemon-center': {
    id: 'ario-pokemon-center',
    fromPlaceId: 'ario-sapporo',
    toPlaceId: 'pokemon-center-sapporo',
    fallbackMinutes: 15,
    fallbackKm: 4,
    noteZh: '依停車狀況可改搭地下鐵或計程車。',
  },
  'pokemon-center-parco': {
    id: 'pokemon-center-parco',
    fromPlaceId: 'pokemon-center-sapporo',
    toPlaceId: 'sapporo-parco',
    fallbackMinutes: 10,
    fallbackKm: 2,
    noteZh: '市中心短程。',
  },
  'parco-sapporo': {
    id: 'parco-sapporo',
    fromPlaceId: 'sapporo-parco',
    toPlaceId: 'sapporo',
    fallbackMinutes: 10,
    fallbackKm: 2,
    noteZh: '回札幌住宿。',
  },
  'sapporo-underground': {
    id: 'sapporo-underground',
    fromPlaceId: 'sapporo',
    toPlaceId: 'sapporo-underground',
    fallbackMinutes: 5,
    fallbackKm: 1,
    noteZh: '地下街以步行或大眾運輸為主。',
  },
  'underground-cocono': {
    id: 'underground-cocono',
    fromPlaceId: 'sapporo-underground',
    toPlaceId: 'cocono-susukino',
    fallbackMinutes: 10,
    fallbackKm: 2,
    noteZh: '市中心轉薄野。',
  },
  'cocono-moiwa': {
    id: 'cocono-moiwa',
    fromPlaceId: 'cocono-susukino',
    toPlaceId: 'mt-moiwa',
    fallbackMinutes: 25,
    fallbackKm: 8,
    noteZh: '接近黃昏前往藻岩山。',
  },
  'moiwa-sapporo': {
    id: 'moiwa-sapporo',
    fromPlaceId: 'mt-moiwa',
    toPlaceId: 'sapporo',
    fallbackMinutes: 30,
    fallbackKm: 9,
    noteZh: '夜景後回札幌住宿區。',
  },
  'sapporo-cocono': {
    id: 'sapporo-cocono',
    fromPlaceId: 'sapporo',
    toPlaceId: 'cocono-susukino',
    fallbackMinutes: 10,
    fallbackKm: 2,
    noteZh: '最後採買與確認薄野周邊站點。',
  },
  'cocono-susukino-bus-stop': {
    id: 'cocono-susukino-bus-stop',
    fromPlaceId: 'cocono-susukino',
    toPlaceId: 'susukino-airport-bus-stop',
    fallbackMinutes: 5,
    fallbackKm: 1,
    noteZh: '出發前一天確認機場巴士站牌位置。',
  },
  'susukino-bus-stop-cts': {
    id: 'susukino-bus-stop-cts',
    fromPlaceId: 'susukino-airport-bus-stop',
    toPlaceId: 'new-chitose-airport',
    fallbackMinutes: 80,
    fallbackKm: 50,
    noteZh: '機場巴士估算；班次、上車點與付款方式需依當日官方資訊確認。',
  },
  'sapporo-otaru': {
    id: 'sapporo-otaru',
    fromPlaceId: 'sapporo',
    toPlaceId: 'otaru',
    fallbackMinutes: 55,
    fallbackKm: 38,
    noteZh: '保留作為既有服務測試與備用路段。',
  },
  'otaru-yoichi': {
    id: 'otaru-yoichi',
    fromPlaceId: 'otaru',
    toPlaceId: 'yoichi',
    fallbackMinutes: 35,
    fallbackKm: 22,
    noteZh: '保留作為既有服務測試與備用路段。',
  },
};

export const tripDays: TripDay[] = [
  {
    date: '2026-06-25',
    labelZh: '6/25',
    titleZh: '抵達新千歲，惠庭緩衝',
    startPlaceId: 'new-chitose-airport',
    endPlaceId: 'eniwa-fairfield',
    weatherPlaceId: 'eniwa',
    lodgingAreaId: 'eniwa',
    stopIds: ['hanaroad-eniwa', 'ecorin-village', 'eniwa-honoka'],
    routeSegmentIds: [
      'cts-hanaroad-eniwa',
      'hanaroad-ecorin',
      'ecorin-honoka',
      'honoka-eniwa-fairfield',
    ],
    summaryZh:
      'BR116 抵達後租車，先用惠庭作第一晚緩衝。ECORIN 村與 HONOKA 都列為可依抵達體力刪減的近距離點。',
    lodgingTargetZh: '惠庭住宿，優先北海道惠庭萬楓酒店',
    driveNoteZh: '全日車程短；若入境或租車延誤，保留花路惠庭加飯店即可。',
  },
  {
    date: '2026-06-26',
    labelZh: '6/26',
    titleZh: '惠庭親子活動、支笏湖，進登別',
    startPlaceId: 'eniwa-fairfield',
    endPlaceId: 'park-hotel-miyabitei',
    weatherPlaceId: 'lake-shikotsu',
    lodgingAreaId: 'noboribetsu',
    stopIds: [
      'forest-adventure-eniwa',
      'kamameshi-ichie',
      'lake-shikotsu',
      'tarumae-garo',
    ],
    routeSegmentIds: [
      'eniwa-fairfield-forest-adventure',
      'forest-adventure-kamameshi-ichie',
      'kamameshi-ichie-lake-shikotsu',
      'lake-shikotsu-tarumae-garo',
      'tarumae-garo-miyabitei',
    ],
    summaryZh:
      '上午 Forest Adventure Eniwa，中午釜飯 ICHIE，下午支笏湖。樽前GARO 是順路候選，孩子累時直接去登別。',
    lodgingTargetZh: '登別溫泉旅館或雅亭酒店',
    driveNoteZh: '估算約 175 分 / 136 km，是南下日主移動；樽前GARO 可作為第一刪減點。',
  },
  {
    date: '2026-06-27',
    labelZh: '6/27',
    titleZh: '登別、白老、室蘭，夜宿洞爺湖',
    startPlaceId: 'park-hotel-miyabitei',
    endPlaceId: 'lake-toya',
    weatherPlaceId: 'noboribetsu',
    lodgingAreaId: 'lake-toya',
    stopIds: ['jigokudani', 'oyunuma', 'nachu-no-mori', 'cape-chikyu'],
    routeSegmentIds: [
      'miyabitei-jigokudani',
      'jigokudani-oyunuma',
      'oyunuma-nachu-no-mori',
      'nachu-no-mori-cape-chikyu',
      'cape-chikyu-lake-toya',
    ],
    summaryZh:
      '把 CSV 原本同日拉到小樽的段落切開：登別地獄谷與大湯沼後，走白老ナチュの森、室蘭地球岬，夜宿洞爺湖。',
    lodgingTargetZh: '已訂 Lake Toya Terrace House（Agoda 已確認）',
    confirmedLodging: {
      provider: 'Agoda',
      statusZh: '已確認',
      bookingNumber: '1730644759',
      hotelName: 'Lake Toya Terrace House',
      checkInDate: '2026-06-27',
      checkOutDate: '2026-06-28',
    },
    driveNoteZh: '估算約 158 分 / 118 km；若遇雨，地球岬可刪減直接往洞爺湖。',
  },
  {
    date: '2026-06-28',
    labelZh: '6/28',
    titleZh: '洞爺湖轉場小樽',
    startPlaceId: 'lake-toya',
    endPlaceId: 'otaru',
    weatherPlaceId: 'lake-toya',
    lodgingAreaId: 'otaru',
    stopIds: [],
    routeSegmentIds: ['toya-otaru'],
    summaryZh:
      '保守轉場日。把小樽從 6/27 移到洞爺湖隔天，避免登別、白老、室蘭、洞爺、小樽連成超長日。',
    lodgingTargetZh: '已訂 Hotel Nord Otaru（Agoda 已確認）',
    confirmedLodging: {
      provider: 'Agoda',
      statusZh: '已確認',
      bookingNumber: '1730650360',
      hotelName: 'Hotel Nord Otaru',
      checkInDate: '2026-06-28',
      checkOutDate: '2026-06-29',
    },
    driveNoteZh: '估算約 140 分 / 125 km；抵達後只安排運河散步與晚餐。',
  },
  {
    date: '2026-06-29',
    labelZh: '6/29',
    titleZh: '鱗友朝市，小樽到札幌',
    startPlaceId: 'otaru',
    endPlaceId: 'sapporo',
    weatherPlaceId: 'otaru',
    lodgingAreaId: 'sapporo',
    stopIds: ['rinyu-market'],
    routeSegmentIds: ['otaru-rinyu-market', 'rinyu-market-sapporo'],
    summaryZh:
      '小樽住宿後早上去鱗友朝市，再進札幌開始連住。CSV 的小樽還車可在此日評估。',
    lodgingTargetZh: '札幌市中心或薄野附近連住',
    driveNoteZh: '估算約 61 分 / 42 km；今日開始降低移動壓力。',
  },
  {
    date: '2026-06-30',
    labelZh: '6/30',
    titleZh: '札幌購物與親子緩衝',
    startPlaceId: 'sapporo',
    endPlaceId: 'sapporo',
    weatherPlaceId: 'sapporo',
    lodgingAreaId: 'sapporo',
    stopIds: ['ario-sapporo', 'pokemon-center-sapporo', 'sapporo-parco'],
    routeSegmentIds: [
      'sapporo-ario',
      'ario-pokemon-center',
      'pokemon-center-parco',
      'parco-sapporo',
    ],
    summaryZh:
      '利用 CSV 空白日作札幌緩衝。Ario/Workman Girl、寶可夢中心與 PARCO 可依體力拆分。',
    lodgingTargetZh: '續住札幌市中心或薄野附近',
    driveNoteZh: '市區短程，停車成本高時建議改搭地下鐵或計程車。',
  },
  {
    date: '2026-07-01',
    labelZh: '7/1',
    titleZh: '札幌地下街、薄野與藻岩山',
    startPlaceId: 'sapporo',
    endPlaceId: 'sapporo',
    weatherPlaceId: 'sapporo',
    lodgingAreaId: 'sapporo',
    stopIds: ['sapporo-underground', 'cocono-susukino', 'mt-moiwa'],
    routeSegmentIds: [
      'sapporo-underground',
      'underground-cocono',
      'cocono-moiwa',
      'moiwa-sapporo',
    ],
    summaryZh:
      '整合 CSV 7/1 的札幌清單：地下街、COCONO SUSUKINO、美食與藻岩山黃昏夜景。',
    lodgingTargetZh: '續住札幌市中心或薄野附近',
    driveNoteZh: '當日以市區移動為主，藻岩山安排黃昏前後。',
  },
  {
    date: '2026-07-02',
    labelZh: '7/2',
    titleZh: '札幌自由日與機場巴士確認',
    startPlaceId: 'sapporo',
    endPlaceId: 'susukino-airport-bus-stop',
    weatherPlaceId: 'sapporo',
    lodgingAreaId: 'sapporo',
    stopIds: ['cocono-susukino'],
    routeSegmentIds: ['sapporo-cocono', 'cocono-susukino-bus-stop'],
    summaryZh:
      '保留自由採買、整理行李與確認薄野機場巴士搭乘處。CSV 的 IC 卡、付款與公車上下車規則只保留成一般提醒，不放任何私人付款資訊。',
    lodgingTargetZh: '續住薄野或市中心，隔天步行到機場巴士站',
    driveNoteZh: '市區短程；重點是確認隔天站牌、班次與行李動線。',
  },
  {
    date: '2026-07-03',
    labelZh: '7/3',
    titleZh: '薄野機場巴士至新千歲返程',
    startPlaceId: 'susukino-airport-bus-stop',
    endPlaceId: 'new-chitose-airport',
    weatherPlaceId: 'new-chitose-airport',
    stopIds: [],
    routeSegmentIds: ['susukino-bus-stop-cts'],
    summaryZh:
      '從薄野機場巴士搭乘處前往新千歲機場，行李多時比 JR 轉地鐵更單純。',
    lodgingTargetZh: '無。',
    driveNoteZh: '估算約 80 分；務必依當日班表提早到站。',
  },
];

export const lodgingCandidates: LodgingCandidate[] = [
  {
    id: 'eniwa-fairfield-1',
    areaId: 'eniwa',
    nameZh: '北海道惠庭萬楓酒店',
    type: 'airport-buffer',
    starLevel: 3,
    budgetRiskZh: '機場圈飯店價格通常比札幌核心穩定，但仍需提早確認。',
    parkingZh: '以飯店停車為主，出發前確認車位與收費。',
    fitZh: '抵達日緩衝、花路惠庭補給方便',
    searchUrl: 'https://www.google.com/travel/hotels/Eniwa',
  },
  {
    id: 'eniwa-chitose-buffer-1',
    areaId: 'eniwa',
    nameZh: '惠庭／千歲緩衝飯店候選',
    type: 'airport-buffer',
    starLevel: 3,
    budgetRiskZh: '若惠庭滿房，可改查千歲或北廣島方向。',
    parkingZh: '自駕住宿需優先確認停車位。',
    fitZh: '首日不進札幌市區，降低疲勞',
    searchUrl: 'https://www.booking.com/city/jp/eniwa.zh-tw.html',
  },
  {
    id: 'noboribetsu-miyabitei-1',
    areaId: 'noboribetsu',
    nameZh: 'Park Hotel Miyabitei 雅亭酒店',
    type: 'onsen-resort',
    starLevel: 4,
    budgetRiskZh: '溫泉區熱門日價格偏高，需比市區更早查。',
    parkingZh: '溫泉旅館通常可停車，仍需確認入住規則。',
    fitZh: '接地獄谷與大湯沼最順',
    searchUrl: 'https://www.google.com/travel/hotels/Noboribetsu',
  },
  {
    id: 'noboribetsu-onsen-1',
    areaId: 'noboribetsu',
    nameZh: '登別溫泉旅館候選',
    type: 'onsen-resort',
    starLevel: 3,
    budgetRiskZh: '房型差異大，親子房與晚餐方案要分開比較。',
    parkingZh: '溫泉街停車便利度依旅館位置不同。',
    fitZh: '泡湯與休息重點日',
    searchUrl: 'https://www.jalan.net/onsen/OSN_50005/',
  },
  {
    id: 'toya-onsen-1',
    areaId: 'lake-toya',
    nameZh: 'Lake Toya Terrace House（已訂）',
    type: 'onsen-resort',
    starLevel: 3,
    budgetRiskZh: 'Agoda 已確認，後續只需追蹤取消期限與入住細節。',
    parkingZh: '需依訂房頁或住宿訊息再次確認停車安排。',
    fitZh: '6/27 洞爺湖町過夜，切開登別到小樽長距離',
    searchUrl: 'https://www.google.com/travel/hotels?q=Lake%20Toya%20Terrace%20House',
  },
  {
    id: 'otaru-canal-1',
    areaId: 'otaru',
    nameZh: 'Hotel Nord Otaru（已訂）',
    type: 'city',
    starLevel: 3,
    budgetRiskZh: 'Agoda 已確認，後續只需追蹤取消期限與入住細節。',
    parkingZh: '需依訂房頁或飯店訊息再次確認停車與過夜費用。',
    fitZh: '6/28 小樽運河旁過夜，隔天早上去鱗友朝市最順',
    searchUrl: 'https://www.google.com/travel/hotels?q=Hotel%20Nord%20Otaru',
  },
  {
    id: 'sapporo-susukino-1',
    areaId: 'sapporo',
    nameZh: '札幌薄野連住飯店候選',
    type: 'city',
    starLevel: 3,
    budgetRiskZh: '餐飲區方便但週末價格與停車費可能上浮。',
    parkingZh: '若已還車，可優先選近機場巴士站。',
    fitZh: 'COCONO SUSUKINO、美食與機場巴士動線佳',
    searchUrl: 'https://www.google.com/travel/hotels/Susukino%20Sapporo',
  },
  {
    id: 'sapporo-station-1',
    areaId: 'sapporo',
    nameZh: '札幌站前飯店候選',
    type: 'city',
    starLevel: 4,
    budgetRiskZh: '交通方便，熱門時段價格偏高。',
    parkingZh: '車站周邊需確認車高限制與收費。',
    fitZh: '地下街、寶可夢中心與購物動線好',
    searchUrl: 'https://www.booking.com/city/jp/sapporo.zh-tw.html',
  },
];
