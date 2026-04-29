import {
  buildOpenMeteoUrl,
  fetchWeatherSummary,
  isWithinForecastWindow,
  weatherCodeLabelZh,
} from '../src/services/weather';

describe('weather service', () => {
  it('buildOpenMeteoUrl includes required Open-Meteo query parameters', () => {
    const url = buildOpenMeteoUrl(43.0618, 141.3545);

    expect(url).toContain('https://api.open-meteo.com/v1/forecast');
    expect(url).toContain('latitude=43.0618');
    expect(url).toContain('longitude=141.3545');
    expect(url).toContain('current=temperature_2m%2Cwind_speed_10m%2Cweather_code');
    expect(url).toContain(
      'daily=weather_code%2Cprecipitation_probability_max%2Ctemperature_2m_max%2Ctemperature_2m_min%2Cwind_speed_10m_max',
    );
    expect(url).toContain('forecast_days=16');
    expect(url).toContain('timezone=Asia%2FTokyo');
  });

  it('isWithinForecastWindow checks inclusive date window from local current date', () => {
    const now = new Date('2026-06-20T08:00:00+09:00');

    expect(isWithinForecastWindow('2026-06-25', now)).toBe(true);
    expect(isWithinForecastWindow('2026-07-05', now)).toBe(true);
    expect(isWithinForecastWindow('2026-07-06', now)).toBe(false);
    expect(isWithinForecastWindow('2026-07-10', now)).toBe(false);
    expect(isWithinForecastWindow('2026-06-19', now)).toBe(false);
  });

  it('fetchWeatherSummary returns not-yet-available before forecast window and does not call fetcher', async () => {
    const fetcher = vi.fn();

    const result = await fetchWeatherSummary({
      targetDate: '2026-07-20',
      lat: 43.0618,
      lng: 141.3545,
      now: new Date('2026-06-20T08:00:00+09:00'),
      fetcher,
    });

    expect(result.status).toBe('not-yet-available');
    expect(result.messageZh).toContain('2026-07-20');
    expect(result.messageZh).toContain('尚未進入可預報範圍');
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('fetchWeatherSummary returns unavailable when request fails inside forecast window', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('network error'));

    const result = await fetchWeatherSummary({
      targetDate: '2026-06-25',
      lat: 43.0618,
      lng: 141.3545,
      now: new Date('2026-06-20T08:00:00+09:00'),
      fetcher,
    });

    expect(result.status).toBe('unavailable');
    expect(result.messageZh).toContain('天氣資料暫不可用');
  });

  it('fetchWeatherSummary returns unavailable when HTTP response is non-ok', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    const result = await fetchWeatherSummary({
      targetDate: '2026-06-25',
      lat: 43.0618,
      lng: 141.3545,
      now: new Date('2026-06-20T08:00:00+09:00'),
      fetcher,
    });

    expect(result.status).toBe('unavailable');
    expect(result.messageZh).toContain('天氣資料暫不可用');
  });

  it('fetchWeatherSummary prefers target-date daily weather code and returns updatedAt without current-day temperature or wind', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        current: {
          time: '2026-06-20T08:00',
          temperature_2m: 22.1,
          wind_speed_10m: 11.2,
          weather_code: 0,
        },
        daily: {
          time: ['2026-06-24', '2026-06-25', '2026-06-26'],
          weather_code: [0, 61, 2],
          precipitation_probability_max: [10, 70, 30],
          temperature_2m_max: [20, 24, 21],
          temperature_2m_min: [12, 16, 14],
          wind_speed_10m_max: [8, 18, 10],
        },
      }),
    });

    const result = await fetchWeatherSummary({
      targetDate: '2026-06-25',
      lat: 43.0618,
      lng: 141.3545,
      now: new Date('2026-06-20T08:00:00+09:00'),
      fetcher,
    });

    expect(result.status).toBe('loaded');
    expect(result.weatherLabelZh).toBe('下雨');
    expect(result.weatherCode).toBe(61);
    expect(result.precipitationProbabilityMax).toBe(70);
    expect(result.updatedAt).toBe('2026-06-20T08:00');
    expect(result.temperatureMaxC).toBe(24);
    expect(result.temperatureMinC).toBe(16);
    expect(result.temperatureC).toBeUndefined();
    expect(result.windSpeedKmh).toBe(18);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it('fetchWeatherSummary falls back to current weather code only when target date is today', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        current: {
          weather_code: 0,
        },
        daily: {
          time: ['2026-06-24', '2026-06-26'],
          weather_code: [61, 2],
        },
      }),
    });

    const result = await fetchWeatherSummary({
      targetDate: '2026-06-20',
      lat: 43.0618,
      lng: 141.3545,
      now: new Date('2026-06-20T08:00:00+09:00'),
      fetcher,
    });

    expect(result.status).toBe('loaded');
    expect(result.weatherCode).toBe(0);
    expect(result.weatherLabelZh).toBe('晴朗');
  });

  it('fetchWeatherSummary does not use current weather code for a future target date', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        current: {
          weather_code: 0,
        },
        daily: {
          time: ['2026-06-24', '2026-06-26'],
          weather_code: [61, 2],
          precipitation_probability_max: [20, 30],
        },
      }),
    });

    const result = await fetchWeatherSummary({
      targetDate: '2026-06-25',
      lat: 43.0618,
      lng: 141.3545,
      now: new Date('2026-06-20T08:00:00+09:00'),
      fetcher,
    });

    expect(result.status).toBe('unavailable');
    expect(result.messageZh).toContain('天氣資料暫不可用');
  });

  it('fetchWeatherSummary returns unavailable when payload is empty', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    const result = await fetchWeatherSummary({
      targetDate: '2026-06-25',
      lat: 43.0618,
      lng: 141.3545,
      now: new Date('2026-06-20T08:00:00+09:00'),
      fetcher,
    });

    expect(result.status).toBe('unavailable');
    expect(result.messageZh).toContain('天氣資料暫不可用');
  });

  it('weatherCodeLabelZh maps known and unknown weather codes', () => {
    expect(weatherCodeLabelZh(0)).toBe('晴朗');
    expect(weatherCodeLabelZh(61)).toBe('下雨');
    expect(weatherCodeLabelZh(undefined)).toBe('天氣狀態未分類');
    expect(weatherCodeLabelZh(999)).toBe('天氣狀態未分類');
  });
});
