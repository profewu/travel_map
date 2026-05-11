import itineraryCsvRaw from '../../北海道行程(工作表1).csv?raw';

export interface CsvPlaceSummary {
  placeId: string;
  summaryZh: string;
  markerColorIndex: number;
}

const csvPlaceAliases: Record<string, string[]> = {
  'new-chitose-airport': ['新千歲機場交通', '第二航廈', '新千歲機場'],
  eniwa: ['惠庭'],
  'eniwa-fairfield': ['北海道惠庭萬楓酒店', 'Fairfield by Marriott Hokkaido Eniwa'],
  'hanaroad-eniwa': ['道與川之驛 花路惠庭', '花路惠庭'],
  'ecorin-village': ['惠庭 ECORIN村', 'ECORIN村'],
  'eniwa-honoka': ['惠庭溫泉HONOKA', '惠庭溫泉 HONOKA'],
  'forest-adventure-eniwa': ['Forest Adventure Eniwa'],
  'kamameshi-ichie': ['釜飯 ICHIE', '釜飯'],
  'lake-shikotsu': ['支笏湖', '支芴湖'],
  'tarumae-garo': ['樽前GARO', '樽前加羅', '樽前ガロー'],
  noboribetsu: ['登別'],
  'park-hotel-miyabitei': ['Park Hotel Miyabitei雅亭酒店', 'Park Hotel Miyabitei', '雅亭酒店'],
  jigokudani: ['登別地獄谷'],
  oyunuma: ['大湯沼'],
  'nachu-no-mori': ['ナチュの森'],
  'cape-chikyu': ['地球岬展望台'],
  'lake-toya': ['洞爺湖'],
  otaru: ['小樽'],
  'rinyu-market': ['鱗友朝市'],
  sapporo: ['札幌'],
  'ario-sapporo': ['Ario 購物中心', 'Ario'],
  'pokemon-center-sapporo': ['北海道唯一寶可夢中心', '寶可夢中心'],
  'sapporo-parco': ['札幌PARCO', 'PARCO'],
  'sapporo-underground': ['札幌地下街'],
  'cocono-susukino': ['COCONO SUSUKINO'],
  'mt-moiwa': ['藻岩山'],
  'susukino-airport-bus-stop': ['新千歲機場交通', '機場巴士', 'すすき'],
};

function parseCsvRows(input: string): string[][] {
  const rows: string[][] = [];
  let currentRow: string[] = [];
  let currentCell = '';
  let inQuotes = false;

  for (let index = 0; index < input.length; index += 1) {
    const char = input[index];
    const nextChar = input[index + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        currentCell += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === ',' && !inQuotes) {
      currentRow.push(currentCell);
      currentCell = '';
      continue;
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && nextChar === '\n') {
        index += 1;
      }
      currentRow.push(currentCell);
      rows.push(currentRow);
      currentRow = [];
      currentCell = '';
      continue;
    }

    currentCell += char;
  }

  if (currentCell.length > 0 || currentRow.length > 0) {
    currentRow.push(currentCell);
    rows.push(currentRow);
  }

  return rows;
}

const normalizeForSearch = (value: string): string =>
  value
    .toLowerCase()
    .replace(/[「」『』【】（）()［］\[\]\s　]/g, '');

function buildSummary(row: string[]): string {
  const day = row[0]?.trim();
  const text = row[1]?.trim();
  const duration = row[2]?.trim();
  const lines = [day ? `CSV ${day}` : 'CSV', text];

  if (duration) {
    lines.push(`停留時間：${duration}`);
  }

  return lines.filter(Boolean).join('\n');
}

function buildCsvPlaceSummaries(): Record<string, CsvPlaceSummary> {
  const rows = parseCsvRows(itineraryCsvRaw).filter((row) => row[1]?.trim());
  const searchableRows = rows.map((row) => ({
    normalizedText: normalizeForSearch(row[1] ?? ''),
    row,
  }));
  const summaries: Record<string, CsvPlaceSummary> = {};

  Object.entries(csvPlaceAliases).forEach(([placeId, aliases], index) => {
    const matched = searchableRows.find(({ normalizedText }) =>
      aliases.some((alias) => normalizedText.includes(normalizeForSearch(alias))),
    );

    if (!matched) {
      return;
    }

    summaries[placeId] = {
      placeId,
      summaryZh: buildSummary(matched.row),
      markerColorIndex: index % 5,
    };
  });

  return summaries;
}

export const csvPlaceSummariesById = buildCsvPlaceSummaries();
