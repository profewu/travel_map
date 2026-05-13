import { appModes, topNavigationItems } from '../src/ui/navigation';

const masterSummaryUrl =
  'file:///C:/Users/Jonathan/Documents/travel_map/hotel-research/reports/master_summary.html';

describe('top navigation modes', () => {
  it('places disaster information between table and notes in the segmented nav', () => {
    expect(topNavigationItems.map((item) => item.labelZh)).toEqual([
      '總覽',
      '路線',
      '表格',
      '住宿報表',
      '防災資訊',
      '筆記',
    ]);
    expect(appModes).toEqual(['overview', 'route', 'table', 'disaster']);
  });

  it('links the hotel report to the local master summary file', () => {
    const reportItem = topNavigationItems.find(
      (item) => item.labelZh === '住宿報表',
    );

    expect(reportItem).toEqual({
      kind: 'external',
      labelZh: '住宿報表',
      href: masterSummaryUrl,
    });
  });
});
