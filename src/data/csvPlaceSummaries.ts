export interface CsvPlaceSummary {
  placeId: string;
  summaryZh: string;
  markerColorIndex: number;
}

type CuratedCsvPlaceSummary = Omit<CsvPlaceSummary, 'markerColorIndex'>;

const curatedCsvPlaceSummaries: CuratedCsvPlaceSummary[] = [
  {
    placeId: 'new-chitose-airport',
    summaryZh: 'CSV 6/25、7/1\n抵達與回程都以新千歲機場為交通錨點，保留租車、機場巴士和航班銜接提醒。',
  },
  {
    placeId: 'eniwa',
    summaryZh: 'CSV 6/25\n抵達日先落在惠庭周邊，不急著北上札幌，適合採買、晚餐和早點休息。',
  },
  {
    placeId: 'eniwa-fairfield',
    summaryZh: 'CSV 6/25\n北海道惠庭萬楓酒店是抵達日住宿核心，鄰近花路惠庭，隔天接戶外活動較順。',
  },
  {
    placeId: 'hanaroad-eniwa',
    summaryZh: 'CSV 6/25\n道與川之驛花路惠庭可作為抵達日補給點，CSV 特別提到惠庭銅鑼燒。',
  },
  {
    placeId: 'ecorin-village',
    summaryZh: 'CSV 6/25\n惠庭 ECORIN 村列為抵達日周邊候選，適合視體力加入短停留。',
  },
  {
    placeId: 'eniwa-honoka',
    summaryZh: 'CSV 6/25\n惠庭溫泉 HONOKA 是抵達日放鬆候選，重點是溫泉、足湯、桑拿與晚餐彈性。',
  },
  {
    placeId: 'forest-adventure-eniwa',
    summaryZh: 'CSV 6/26\nForest Adventure Eniwa 是親子戶外活動，安排在惠庭住宿隔天早上。',
  },
  {
    placeId: 'kamameshi-ichie',
    summaryZh: 'CSV 6/26\n釜飯 ICHIE 是惠庭人氣美食，CSV 備註有海膽、鮭魚卵與茶泡飯吃法。',
  },
  {
    placeId: 'lake-shikotsu',
    summaryZh:
      'CSV 6/26\n支笏湖包含展望台、野鳥之森與遊覽船；航行月份約 4 月中旬至 11 月中旬，天候差時要保留彈性。',
  },
  {
    placeId: 'tarumae-garo',
    summaryZh: 'CSV 6/26\n樽前加羅是苫小牧自然景點，適合作為支笏湖後的可選短停留。',
  },
  {
    placeId: 'noboribetsu',
    summaryZh: 'CSV 6/26、6/27\n登別作為溫泉區落點，隔天早上接地獄谷、大湯沼較不繞路。',
  },
  {
    placeId: 'park-hotel-miyabitei',
    summaryZh: 'CSV 6/26\nPark Hotel Miyabitei 雅亭酒店是登別溫泉區住宿候選，方便隔天早上走核心景點。',
  },
  {
    placeId: 'jigokudani',
    summaryZh: 'CSV 6/27\n登別地獄谷是早上主景點，步道短，適合放在退房後第一站。',
  },
  {
    placeId: 'oyunuma',
    summaryZh: 'CSV 6/27\n大湯沼與地獄谷同區，建議連走，避免重複進出登別。',
  },
  {
    placeId: 'nachu-no-mori',
    summaryZh: 'CSV 6/27\nナチュの森是白老親子景點，有戶外與室內遊樂彈性，天氣差時也能保留。',
  },
  {
    placeId: 'cape-chikyu',
    summaryZh: 'CSV 6/27\n地球岬展望台放在白老後、洞爺湖前，可避免登別直接拉到小樽的長距離折返。',
  },
  {
    placeId: 'lake-toya',
    summaryZh: 'CSV 6/27\n洞爺湖用來拆開登別、白老、室蘭到小樽的過重路段，作為南部行程住宿錨點。',
  },
  {
    placeId: 'otaru',
    summaryZh: 'CSV 6/27、6/28\n小樽原列在南部景點同日，本版改到隔天，讓移動節奏更保守。',
  },
  {
    placeId: 'rinyu-market',
    summaryZh: 'CSV 6/28\n鱗友朝市適合小樽住宿隔天早上安排，才符合朝市節奏。',
  },
  {
    placeId: 'sapporo',
    summaryZh: 'CSV 6/28-7/1\n札幌作為連住與採買核心，空白日可作雨天、休息與購物緩衝。',
  },
  {
    placeId: 'ario-sapporo',
    summaryZh: 'CSV 札幌清單\nArio 購物中心列入札幌購物候選，可與 Workman Girl 等採買點同日調整。',
  },
  {
    placeId: 'pokemon-center-sapporo',
    summaryZh: 'CSV 札幌清單\n北海道唯一寶可夢中心，適合和札幌市中心購物路線整併。',
  },
  {
    placeId: 'sapporo-parco',
    summaryZh: 'CSV 札幌清單\n札幌 PARCO 可接寶可夢中心與市中心商圈，適合作為雨天備案。',
  },
  {
    placeId: 'sapporo-underground',
    summaryZh: 'CSV 札幌清單\n札幌地下街含甜點、雜貨與採買候選，適合雨天或晚上短走。',
  },
  {
    placeId: 'cocono-susukino',
    summaryZh: 'CSV 札幌清單\nCOCONO SUSUKINO 是薄野新地標，可與晚餐、地下街或藻岩山同日安排。',
  },
  {
    placeId: 'mt-moiwa',
    summaryZh: 'CSV 札幌清單\n藻岩山建議接近黃昏搭纜車，放在札幌連住日比長途自駕日更穩。',
  },
  {
    placeId: 'susukino-airport-bus-stop',
    summaryZh: 'CSV 7/1\n薄野機場巴士站作為回程交通提醒，行李多時比 JR 轉地鐵更省力。',
  },
];

export const csvPlaceSummariesById: Record<string, CsvPlaceSummary> =
  Object.fromEntries(
    curatedCsvPlaceSummaries.map((summary, index) => [
      summary.placeId,
      {
        ...summary,
        markerColorIndex: index % 5,
      },
    ]),
  );
