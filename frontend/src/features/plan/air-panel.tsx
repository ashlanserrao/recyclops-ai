// The air right now (measured) and the day ahead (forecast), each labelled with where it comes from.

import { RefreshCw, Wind } from "lucide-react";
import { BandBadge, bandClasses, SourceBadge } from "@/components/badges";
import { Panel } from "@/components/layout";
import { Button } from "@/components/ui/button";
import type { AirOut, PlanOut, WindowOut } from "@/lib/api/types";
import { BAND_LABELS, clock, day, stamp } from "@/lib/format";
import { cn } from "@/lib/utils";

const POLLUTANTS = { pm25: "PM2.5", pm10: "PM10" } as const;

export function AirPanel({ plan, onRefresh, refreshing }: { plan: PlanOut; onRefresh: () => void; refreshing: boolean }) {
  const place = plan.city ?? "your location";
  return (
    <Panel id="air" title={`Air in ${place}`} icon={Wind} description={day(plan.day)}
      actions={
        <Button variant="outline" size="sm" onClick={onRefresh} disabled={refreshing}>
          <RefreshCw className={cn(refreshing && "animate-spin")} aria-hidden="true" />
          {refreshing ? "Refreshing…" : "Refresh"}
        </Button>
      }>
      <div className="grid gap-6 md:grid-cols-2">
        <Measured air={plan.air} />
        <Forecast plan={plan} />
      </div>
    </Panel>
  );
}

function Measured({ air }: { air: AirOut }) {
  const { aqi, station } = air;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-semibold">Now</h3>
        {air.status !== "unavailable" && <SourceBadge source="measured" />}
      </div>
      {air.status === "unavailable" || !station ? (
        <p className="rounded-lg border border-dashed border-input p-4 text-sm">
          <span className="font-semibold">No reliable reading near you.</span> No monitoring station within 25 km has
          recent data, so no AQI is shown. The plan below uses the forecast only.
        </p>
      ) : (
        <>
          {aqi ? (
            <div className={cn("flex items-center gap-4 rounded-lg border p-4", bandClasses(aqi.band))}>
              <p className="flex flex-col">
                <span className="text-xs font-semibold tracking-wide">AQI</span>
                <span className="text-5xl font-bold tabular-nums">{aqi.value}</span>
              </p>
              <div>
                <p className="text-lg font-semibold">{BAND_LABELS[aqi.band]}</p>
                <p className="text-sm">Mostly {POLLUTANTS[aqi.prominent]}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm">Not enough hours of data today for a 24-hour AQI.</p>
          )}
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
            <dt className="text-muted-foreground">Station</dt>
            <dd>{station.name}, {station.distance_km} km away</dd>
            {air.measured_at && <><dt className="text-muted-foreground">Reading</dt><dd>{stamp(air.measured_at)}</dd></>}
            {air.pm25_24h != null && <><dt className="text-muted-foreground">PM2.5 (24 h)</dt><dd>{air.pm25_24h} µg/m³</dd></>}
            {air.pm10_24h != null && <><dt className="text-muted-foreground">PM10 (24 h)</dt><dd>{air.pm10_24h} µg/m³</dd></>}
            <dt className="text-muted-foreground">Source</dt>
            <dd>{air.source}</dd>
          </dl>
          {air.status === "stale" && (
            <p className="rounded-md border border-warning/30 bg-warning-soft p-3 text-sm">
              <span className="font-semibold">Last known reading.</span> The live source isn't answering, so this is the
              reading from {air.measured_at ? stamp(air.measured_at) : "earlier"}.
            </p>
          )}
          {aqi && <p className="text-xs text-muted-foreground">{aqi.method}.</p>}
        </>
      )}
    </div>
  );
}

function Forecast({ plan }: { plan: PlanOut }) {
  const { windows, air } = plan;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-semibold">Later today</h3>
        <SourceBadge source="forecast" />
      </div>
      {windows ? (
        <>
          <ul className="space-y-2">
            <WindowRow label="Cleanest 2 hours" window={windows.best} />
            <WindowRow label="Dirtiest 2 hours" window={windows.worst} />
          </ul>
          <p className="text-xs text-muted-foreground">
            {windows.note} {air.forecast_source}, {air.forecast_corrected
              ? "scaled to match the station's measured level." : "as modelled (no station reading to adjust it to)."}
          </p>
        </>
      ) : (
        <p className="text-sm">No hourly forecast is available for the rest of today.</p>
      )}
    </div>
  );
}

function WindowRow({ label, window }: { label: string; window: WindowOut }) {
  return (
    <li className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3">
      <div>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="font-semibold">{clock(window.start)} to {clock(window.end)}</p>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span className="tabular-nums">PM2.5 ~{window.pm25} µg/m³</span>
        <BandBadge band={window.band} />
      </div>
    </li>
  );
}
