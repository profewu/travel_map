export interface DirectionsInput {
  origin: string;
  destination: string;
  waypoints?: string[];
}

export const jmaWarningUrl =
  'https://www.jma.go.jp/bosai/warning/#area_type=offices&area_code=016000&lang=zh-TW';
export const roadTrafficUrl = 'https://www.c-nexco.co.jp/en/jam/';

export const buildGoogleDirectionsUrl = ({
  origin,
  destination,
  waypoints,
}: DirectionsInput): string => {
  const params = new URLSearchParams({
    api: '1',
    origin,
    destination,
    travelmode: 'driving',
  });

  if (waypoints && waypoints.length > 0) {
    params.set('waypoints', waypoints.join('|'));
  }

  return `https://www.google.com/maps/dir/?${params.toString()}`;
};

export const buildGoogleSearchUrl = (query: string): string => {
  const params = new URLSearchParams({ q: query });

  return `https://www.google.com/maps/search/?api=1&${params.toString()}`;
};

export const buildHotelSearchUrl = (
  query: string,
  checkIn: string,
  checkOut: string,
): string => {
  const params = new URLSearchParams({
    q: query,
    checkin: checkIn,
    checkout: checkOut,
  });

  return `https://www.google.com/travel/hotels?${params.toString()}`;
};
