// "Use my location": the browser asks the person first (Permissions-Policy allows this site only).

import { devicePlace, type Place } from "@/lib/household";

const DENIED = "Location access is turned off for this site. Choose a city instead.";
const OUTSIDE = "That position is outside India, and the planner covers India only. Choose a city instead.";
const FAILED = "Couldn't get your location. Choose a city instead.";

/** The device's place, or an Error whose message says what to do next. */
export function locateDevice(): Promise<Place> {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) {
      reject(new Error(FAILED));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const place = devicePlace(coords.latitude, coords.longitude);
        if (place) resolve(place);
        else reject(new Error(OUTSIDE));
      },
      (error) => reject(new Error(error.code === error.PERMISSION_DENIED ? DENIED : FAILED)),
      // A coarse fix is enough for a station 25 km away, and it comes faster and uses less battery.
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 10 * 60_000 },
    );
  });
}
