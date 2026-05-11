import { describe, expect, it } from 'vitest';
import {
  clearTravelNotes,
  loadTravelNotes,
  saveTravelNotes,
  travelNotesStorageKey,
} from '../src/ui/notes';

describe('travel notes storage', () => {
  it('saves, loads, and clears travel notes from localStorage', () => {
    localStorage.clear();

    saveTravelNotes('6/28 rain backup: move coast stop earlier');

    expect(localStorage.getItem(travelNotesStorageKey)).toBe(
      '6/28 rain backup: move coast stop earlier',
    );
    expect(loadTravelNotes()).toBe('6/28 rain backup: move coast stop earlier');

    clearTravelNotes();

    expect(localStorage.getItem(travelNotesStorageKey)).toBeNull();
    expect(loadTravelNotes()).toBe('');
  });
});
