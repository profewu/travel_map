export const travelNotesStorageKey = 'travelMap.pendingChangeNotes';

export function loadTravelNotes(): string {
  return localStorage.getItem(travelNotesStorageKey) ?? '';
}

export function saveTravelNotes(value: string): void {
  localStorage.setItem(travelNotesStorageKey, value);
}

export function clearTravelNotes(): void {
  localStorage.removeItem(travelNotesStorageKey);
}
