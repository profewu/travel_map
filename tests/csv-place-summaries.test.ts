import { csvPlaceSummariesById } from '../src/data/csvPlaceSummaries';

describe('CSV place summaries', () => {
  it('matches curated places against the itinerary CSV text with aliases', () => {
    expect(csvPlaceSummariesById['kamameshi-ichie']?.summaryZh).toContain('茶泡飯');
    expect(csvPlaceSummariesById['lake-shikotsu']?.summaryZh).toContain('航行月份');
    expect(csvPlaceSummariesById['tarumae-garo']?.summaryZh).toContain('樽前加羅');
  });

  it('does not mark places that are not present in the CSV itinerary', () => {
    expect(csvPlaceSummariesById.yoichi).toBeUndefined();
  });

  it('assigns stable marker color indexes to CSV-backed places', () => {
    expect(csvPlaceSummariesById['lake-shikotsu']?.markerColorIndex).toBeGreaterThanOrEqual(0);
    expect(csvPlaceSummariesById['lake-shikotsu']?.markerColorIndex).toBeLessThan(5);
  });
});
