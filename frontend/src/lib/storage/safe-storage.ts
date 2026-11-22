// Storage can be blocked (private mode, site data off), and even reaching `localStorage` can throw.
// A read then gives null and a write is dropped: the app works the same, it just doesn't remember.

type Area = "local" | "session";

const area = (name: Area) => (name === "local" ? localStorage : sessionStorage);

export function readItem(name: Area, key: string): string | null {
  try {
    return area(name).getItem(key);
  } catch {
    return null;
  }
}

/** `null` removes the key. */
export function writeItem(name: Area, key: string, value: string | null) {
  try {
    if (value === null) area(name).removeItem(key);
    else area(name).setItem(key, value);
  } catch {
    // Not remembered; it lasts as long as the page.
  }
}
