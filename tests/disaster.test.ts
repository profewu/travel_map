import {
  buildItineraryDisasterSummary,
  staticDisasterDataset,
} from '../src/data/disaster';
import { renderDisasterPanel } from '../src/ui/panels';

describe('disaster information data model', () => {
  it('summarizes itinerary alert status from deterministic static data', () => {
    const summary = buildItineraryDisasterSummary(
      staticDisasterDataset.itineraryAlerts,
    );

    expect(summary.status).toBe('attention');
    expect(summary.labelZh).toBe('注意');
    expect(summary.totalAlertCount).toBe(2);
    expect(summary.messageZh).toContain('洞爺湖');
    expect(summary.messageZh).toContain('札幌');
  });
});

describe('disaster information panel', () => {
  it('renders recent events, legend, epicenter, and itinerary alert summary', () => {
    const root = document.createElement('div');
    root.innerHTML = renderDisasterPanel(staticDisasterDataset);

    expect(root.querySelector('[data-page="disaster"]')).not.toBeNull();
    expect(root.querySelector('.disaster-event-list')?.textContent).toContain(
      '浦河沖',
    );
    expect(root.querySelector('.disaster-legend')?.textContent).toContain('震央');
    expect(root.querySelector('.disaster-epicenter-card')?.textContent).toContain(
      'M5.2',
    );
    expect(root.querySelector('.disaster-itinerary-summary')?.textContent).toContain(
      '注意',
    );
    expect(root.querySelector('.disaster-source-hint')?.textContent).toContain(
      'JMA / NIED / GSI',
    );
  });
});
