export type WeatherStatus = 'loaded' | 'not-yet-available' | 'unavailable';

export interface WeatherSummary {
  status: WeatherStatus;
  messageZh: string;
  updatedAt?: string;
  temperatureC?: number;
  temperatureMaxC?: number;
  temperatureMinC?: number;
  windSpeedKmh?: number;
  weatherCode?: number;
  weatherLabelZh?: string;
  precipitationProbabilityMax?: number;
}

export interface FetchWeatherInput {
  targetDate: string;
  lat: number;
  lng: number;
  now?: Date;
  fetcher?: typeof fetch;
}

interface OpenMeteoResponse {
  current?: {
    time?: string;
    temperature_2m?: number;
    wind_speed_10m?: number;
    weather_code?: number;
  };
  daily?: {
    time?: string[];
    weather_code?: number[];
    precipitation_probability_max?: number[];
    temperature_2m_max?: number[];
    temperature_2m_min?: number[];
    wind_speed_10m_max?: number[];
  };
}

const forecastDays = 16;
const openMeteoBaseUrl = 'https://api.open-meteo.com/v1/forecast';

export const buildOpenMeteoUrl = (latitude: number, longitude: number): string => {
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    current: 'temperature_2m,wind_speed_10m,weather_code',
    daily:
      'weather_code,precipitation_probability_max,temperature_2m_max,temperature_2m_min,wind_speed_10m_max',
    timezone: 'Asia/Tokyo',
    forecast_days: String(forecastDays),
    wind_speed_unit: 'kmh',
  });

  return `${openMeteoBaseUrl}?${params.toString()}`;
};

const localDateKey = (date: Date): string => {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return formatter.format(date);
};

export const isWithinForecastWindow = (
  targetDate: string,
  now: Date = new Date(),
): boolean => {
  const currentDateKey = localDateKey(now);
  const endDate = new Date(`${currentDateKey}T00:00:00+09:00`);
  endDate.setDate(endDate.getDate() + (forecastDays - 1));
  const endDateKey = localDateKey(endDate);

  return targetDate >= currentDateKey && targetDate <= endDateKey;
};

const weatherCodeMapZh: Record<number, string> = {
  0: '晴朗',
  1: '大致晴朗',
  2: '局部多雲',
  3: '陰天',
  45: '有霧',
  48: '霧凇',
  51: '毛毛雨',
  53: '中度毛毛雨',
  55: '強毛毛雨',
  56: '凍毛毛雨',
  57: '強凍毛毛雨',
  61: '下雨',
  63: '中雨',
  65: '大雨',
  66: '凍雨',
  67: '強凍雨',
  71: '下雪',
  73: '中雪',
  75: '大雪',
  77: '雪粒',
  80: '陣雨',
  81: '中度陣雨',
  82: '強陣雨',
  85: '陣雪',
  86: '強陣雪',
  95: '雷雨',
  96: '雷雨夾冰雹',
  99: '強雷雨夾冰雹',
};

export const weatherCodeLabelZh = (code: number | undefined): string => {
  if (code === undefined) {
    return '天氣狀態未分類';
  }
  return weatherCodeMapZh[code] ?? '天氣狀態未分類';
};

type Fetcher = typeof fetch;

export const fetchWeatherSummary = async (
  input: FetchWeatherInput,
): Promise<WeatherSummary> => {
  const { now = new Date(), fetcher = fetcherDefault } = input;

  if (!isWithinForecastWindow(input.targetDate, now)) {
    return {
      status: 'not-yet-available',
      messageZh: `${input.targetDate} 尚未進入可預報範圍`,
    };
  }

  try {
    const response = await fetcher(buildOpenMeteoUrl(input.lat, input.lng));
    if (!response.ok) {
      throw new Error(`request failed: ${response.status}`);
    }

    const payload = (await response.json()) as OpenMeteoResponse;
    const daily = payload.daily;
    const dateIndex = daily?.time?.indexOf(input.targetDate) ?? -1;
    const dailyCode = dateIndex >= 0 ? daily?.weather_code?.[dateIndex] : undefined;
    const currentDateKey = now ? localDateKey(now) : undefined;
    const targetIsCurrentDate = input.targetDate === currentDateKey;
    const effectiveWeatherCode =
      dailyCode ?? (targetIsCurrentDate ? payload.current?.weather_code : undefined);
    const precipitationProbabilityMax =
      dateIndex >= 0 ? daily?.precipitation_probability_max?.[dateIndex] : undefined;
    const dailyTemperatureMaxC =
      dateIndex >= 0 ? daily?.temperature_2m_max?.[dateIndex] : undefined;
    const dailyTemperatureMinC =
      dateIndex >= 0 ? daily?.temperature_2m_min?.[dateIndex] : undefined;
    const dailyWindSpeedKmh =
      dateIndex >= 0 ? daily?.wind_speed_10m_max?.[dateIndex] : undefined;
    const updatedAt = payload.current?.time;
    const temperatureC = targetIsCurrentDate
      ? payload.current?.temperature_2m
      : undefined;
    const windSpeedKmh = dailyWindSpeedKmh ?? (targetIsCurrentDate
      ? payload.current?.wind_speed_10m
      : undefined);
    const hasUsefulField =
      temperatureC !== undefined ||
      dailyTemperatureMaxC !== undefined ||
      dailyTemperatureMinC !== undefined ||
      windSpeedKmh !== undefined ||
      effectiveWeatherCode !== undefined ||
      precipitationProbabilityMax !== undefined;

    if (!hasUsefulField) {
      throw new Error('empty weather payload');
    }

    return {
      status: 'loaded',
      messageZh: '天氣資料已更新',
      updatedAt,
      temperatureC,
      temperatureMaxC: dailyTemperatureMaxC,
      temperatureMinC: dailyTemperatureMinC,
      windSpeedKmh,
      weatherCode: effectiveWeatherCode,
      weatherLabelZh: weatherCodeLabelZh(effectiveWeatherCode),
      precipitationProbabilityMax,
    };
  } catch {
    return {
      status: 'unavailable',
      messageZh: '天氣資料暫不可用',
    };
  }
};

const fetcherDefault: Fetcher = fetch;
