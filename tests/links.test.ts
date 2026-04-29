import {
  buildGoogleDirectionsUrl,
  buildHotelSearchUrl,
  jmaWarningUrl,
  roadTrafficUrl,
} from '../src/services/links';

describe('external link builders', () => {
  it('buildGoogleDirectionsUrl encodes origin, destination, waypoints, and driving mode', () => {
    const url = buildGoogleDirectionsUrl({
      origin: '札幌',
      destination: '小樽',
      waypoints: ['余市'],
    });

    expect(url).toContain('https://www.google.com/maps/dir/?api=1');
    expect(url).toContain('origin=%E6%9C%AD%E5%B9%8C');
    expect(url).toContain('destination=%E5%B0%8F%E6%A8%BD');
    expect(url).toContain('waypoints=%E4%BD%99%E5%B8%82');
    expect(url).toContain('travelmode=driving');
  });

  it('buildHotelSearchUrl includes base URL and check-in/out dates', () => {
    const url = buildHotelSearchUrl(
      '登別溫泉 4星 溫泉旅館',
      '2026-06-30',
      '2026-07-01',
    );
    const parsedUrl = new URL(url);

    expect(url).toContain('https://www.google.com/travel/hotels');
    expect(url).toContain('checkin=2026-06-30');
    expect(url).toContain('checkout=2026-07-01');
    expect(parsedUrl.searchParams.get('q')).toBe('登別溫泉 4星 溫泉旅館');
  });

  it('exports official weather warning and road traffic URLs', () => {
    expect(jmaWarningUrl.startsWith('https://www.jma.go.jp/')).toBe(true);
    expect(roadTrafficUrl.startsWith('https://')).toBe(true);
  });
});
