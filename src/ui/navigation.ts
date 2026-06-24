export type AppMode = 'overview' | 'route' | 'table' | 'disaster';

export interface ModeNavigationItem {
  kind: 'mode';
  mode: AppMode;
  labelZh: string;
}

export interface ActionNavigationItem {
  kind: 'action';
  action: 'notes';
  labelZh: string;
}

export interface ExternalNavigationItem {
  kind: 'external';
  href: string;
  labelZh: string;
}

export type TopNavigationItem =
  | ModeNavigationItem
  | ExternalNavigationItem
  | ActionNavigationItem;

export const appModes: AppMode[] = ['overview', 'route', 'table', 'disaster'];

export const topNavigationItems: TopNavigationItem[] = [
  { kind: 'mode', mode: 'overview', labelZh: '總覽' },
  { kind: 'mode', mode: 'route', labelZh: '路線' },
  { kind: 'mode', mode: 'table', labelZh: '表格' },
  {
    kind: 'external',
    href: 'photo-lens-guide.html',
    labelZh: '攝影資訊',
  },
  { kind: 'mode', mode: 'disaster', labelZh: '防災資訊' },
  { kind: 'action', action: 'notes', labelZh: '筆記' },
];

export function isAppMode(value: string | undefined): value is AppMode {
  return appModes.includes(value as AppMode);
}
