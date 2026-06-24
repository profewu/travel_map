import { appModes, topNavigationItems } from '../src/ui/navigation';

const photoGuideUrl = 'photo-lens-guide.html';

describe('top navigation modes', () => {
  it('places disaster information between table and notes in the segmented nav', () => {
    expect(topNavigationItems.map((item) => item.labelZh)).toEqual([
      '總覽',
      '路線',
      '表格',
      '攝影資訊',
      '防災資訊',
      '筆記',
    ]);
    expect(appModes).toEqual(['overview', 'route', 'table', 'disaster']);
  });

  it('links the photography information page to the published lens guide file', () => {
    const reportItem = topNavigationItems.find(
      (item) => item.labelZh === '攝影資訊',
    );

    expect(reportItem).toEqual({
      kind: 'external',
      labelZh: '攝影資訊',
      href: photoGuideUrl,
    });
  });
});
