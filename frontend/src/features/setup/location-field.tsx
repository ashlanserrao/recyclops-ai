// Where the plan is for: a city from the backend's list, or the device's position.

import { LocateFixed, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { describedBy, Field, Select } from "@/components/ui/field";
import { api } from "@/lib/api/client";
import type { City } from "@/lib/api/types";
import { locateDevice } from "@/lib/geolocation";
import type { Place } from "@/lib/household";

const ID = "location";

export function LocationField({ place, error, onChange }: {
  place: Place | null; error?: string; onChange: (place: Place) => void;
}) {
  const [cities, setCities] = useState<City[] | null>(null);
  const [listFailed, setListFailed] = useState(false);
  const [locating, setLocating] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    api.cities().then((list) => current && setCities(list), () => current && setListFailed(true));
    return () => {
      current = false;
    };
  }, []);

  const chooseCity = (name: string) => {
    const city = cities?.find((c) => c.name === name);
    if (city) onChange({ source: "city", name: city.name, lat: city.lat, lon: city.lon });
  };

  const locate = async () => {
    setLocating(true);
    setProblem(null);
    try {
      onChange(await locateDevice());
    } catch (failure) {
      setProblem(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setLocating(false);
    }
  };

  const shown = error ?? problem ?? undefined;
  const hint = place?.source === "device" ? "Using your device's location, rounded to about 1 km."
    : listFailed ? "The city list didn't load. Use your location, or reload the page to try again." : undefined;

  return (
    <Field id={ID} label="City" error={shown} hint={hint}>
      <div className="flex flex-wrap gap-2">
        {/* Never disabled while the list loads: a disabled control can't take focus, and an error may need to point here. */}
        <Select id={ID} className="min-w-48 flex-1" value={place?.source === "city" ? (place.name ?? "") : ""}
          onChange={(event) => chooseCity(event.target.value)} aria-busy={!cities && !listFailed}
          {...describedBy(ID, shown, hint !== undefined)}>
          <option value="" disabled>{cities ? "Choose a city" : "Loading cities…"}</option>
          {/* A demo's city is shown even before the list arrives. */}
          {!cities && place?.source === "city" && <option value={place.name ?? ""}>{place.name}</option>}
          {cities?.map((city) => <option key={city.name} value={city.name}>{city.name}</option>)}
        </Select>
        <Button variant="outline" onClick={locate} disabled={locating} aria-describedby={problem ? `${ID}-error` : undefined}>
          {locating ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : <LocateFixed aria-hidden="true" />}
          {locating ? "Finding you…" : "Use my location"}
        </Button>
      </div>
    </Field>
  );
}
