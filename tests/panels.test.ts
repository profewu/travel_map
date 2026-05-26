import type { RouteRenderSummary } from '../src/ui/map';
import { csvPlaceSummariesById } from '../src/data/csvPlaceSummaries';
import { lodgingCandidates, places, routeSegments, tripDays } from '../src/data/trip';
import { buildItineraryTableRows } from '../src/ui/itineraryTable';
import { renderDetailPanel, renderItineraryTable, renderMapOverlay } from '../src/ui/panels';
import { buildDayViewModel, selectDay } from '../src/ui/state';

const day = selectDay('2026-06-26', tripDays);
const viewModel = buildDayViewModel(day, places, lodgingCandidates, routeSegments);

const liveRouteSummary: RouteRenderSummary = {
  status: 'live',
  durationMinutes: 216,
  distanceKm: 176.4,
  noteZh: 'OSRM live route ready',
};

describe('dashboard panels', () => {
  it('renderMapOverlay exposes the daily route summary and Google Maps handoff', () => {
    const root = document.createElement('div');
    root.innerHTML = renderMapOverlay({
      vm: viewModel,
      day,
      routeSummary: liveRouteSummary,
    });

    expect(root.querySelector('.map-overlay')).not.toBeNull();
    expect(root.querySelector('.route-card')).not.toBeNull();
    expect(root.textContent).toContain('OSRM live route ready');
    expect(root.textContent).toContain('176.4 km');
    expect(root.textContent).toContain('3.6 hr');

    const googleLink = root.querySelector<HTMLAnchorElement>('.google-btn');
    expect(googleLink?.href).toContain('https://www.google.com/maps/dir/?');
    expect(googleLink?.href).toContain('travelmode=driving');
  });

  it('renderDetailPanel renders the right dashboard with timeline cards and external checks', () => {
    const root = document.createElement('div');
    root.innerHTML = renderDetailPanel({
      vm: viewModel,
      day,
      weather: {
        status: 'unavailable',
        messageZh: 'weather unavailable',
      },
    });

    expect(root.querySelector('.dashboard-right-panel')).not.toBeNull();
    expect(root.querySelector('.weather-box')).not.toBeNull();
    expect(root.querySelectorAll('.timeline-card').length).toBeGreaterThanOrEqual(3);
    expect(root.querySelector('.google-action')?.textContent).toContain('Google Maps');
    expect(root.querySelector('.lodging-list')).not.toBeNull();
  });

  it('renderItineraryTable moves lodging into route column and removes the lodging column', () => {
    const root = document.createElement('div');
    root.innerHTML = renderItineraryTable(
      buildItineraryTableRows({
        days: tripDays,
        places,
        routeSegments,
        lodgingCandidates,
        csvPlaceSummaries: csvPlaceSummariesById,
      }),
    );

    expect(root.querySelector('.table-lodging')).toBeNull();
    expect(root.querySelector('.badge-candidate')).toBeNull();
    expect(root.textContent).not.toContain('住宿地 / 住宿候選');
    expect(root.querySelectorAll('thead th')).toHaveLength(7);
    expect(root.querySelectorAll('tbody tr:first-child > *')).toHaveLength(7);
    expect(root.querySelector('.table-route-lodging')?.textContent).toContain('住宿地');

    const csvItems = root.querySelectorAll('.table-csv-list li');
    expect(csvItems.length).toBeGreaterThan(0);
    expect(csvItems[0].textContent).toContain(':');
    expect(root.textContent).toContain('Lake Toya Terrace House');
    expect(root.textContent).toContain('1730644759');
    expect(root.textContent).toContain('Hotel Nord Otaru');
    expect(root.textContent).toContain('1730650360');
  });
});
