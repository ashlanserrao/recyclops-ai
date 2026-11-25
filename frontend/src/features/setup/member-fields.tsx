// One person: who they are, what they usually do outdoors, and how they get to work or college.

import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox, Input, NumberInput, Select } from "@/components/ui/field";
import type { Activity, Commute, CommuteMode, HealthFlag, Member } from "@/lib/api/types";
import { MAX_ACTIVITIES, newActivity, newCommute } from "@/lib/household";
import { ACTIVITY_KINDS, COMMUTE_MODES, HEALTH_FLAGS, INTENSITIES, MEMBER_TYPES, options } from "@/lib/labels";
import { type Errors, FormField } from "@/components/form-field";

// Walking to and from stops only applies when someone else does the driving.
const HAS_WALKING_LEG: ReadonlySet<CommuteMode> = new Set(["bus", "metro"]);

export function MemberFields({ member, index, errors, onChange, onRemove }: {
  member: Member; index: number; errors: Errors; onChange: (member: Member) => void; onRemove?: () => void;
}) {
  const at = `household.members.${index}`;
  const who = member.name.trim() || `person ${index + 1}`;
  const set = (patch: Partial<Member>) => onChange({ ...member, ...patch });
  const setActivity = (j: number, activity: Activity) =>
    set({ activities: member.activities.map((a, k) => (k === j ? activity : a)) });
  const toggleFlag = (flag: HealthFlag, on: boolean) =>
    set({ health_flags: on ? [...member.health_flags, flag] : member.health_flags.filter((f) => f !== flag) });

  return (
    <fieldset className="space-y-4 rounded-lg border p-4">
      <legend className="px-1 font-semibold">{member.name.trim() || `Person ${index + 1}`}</legend>
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField path={`${at}.name`} label="Name or nickname" errors={errors}>
          {(control) => <Input {...control} maxLength={30} autoComplete="off" value={member.name}
            onChange={(event) => set({ name: event.target.value })} />}
        </FormField>
        <FormField path={`${at}.type`} label="Who they are" errors={errors}>
          {(control) => (
            <Select {...control} value={member.type} onChange={(event) => set({ type: event.target.value as Member["type"] })}>
              {options(MEMBER_TYPES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </Select>
          )}
        </FormField>
        <FormField path={`${at}.age`} label="Age" errors={errors}>
          {(control) => <NumberInput {...control} inputMode="numeric" min={0} max={110} step={1}
            value={member.age} onValueChange={(age) => set({ age })} />}
        </FormField>
      </div>

      <fieldset>
        <legend className="text-sm font-medium">Health conditions <span className="font-normal text-muted-foreground">(if any)</span></legend>
        <div className="grid sm:grid-cols-3 sm:gap-x-4">
          {options(HEALTH_FLAGS).map(([flag, label]) => (
            <Checkbox key={flag} label={label} checked={member.health_flags.includes(flag)}
              onChange={(event) => toggleFlag(flag, event.target.checked)} />
          ))}
        </div>
      </fieldset>

      <div className="space-y-3">
        <p className="text-sm font-medium">Usual outdoor activities</p>
        {member.activities.length === 0 && <p className="text-sm text-muted-foreground">None yet.</p>}
        {member.activities.map((activity, j) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: rows keep no state; every input is controlled, so position is the identity (and the server's error path).
          <ActivityFields key={j} path={`${at}.activities.${j}`} number={j + 1} who={who}
            activity={activity} errors={errors} onChange={(next) => setActivity(j, next)}
            onRemove={() => set({ activities: member.activities.filter((_, k) => k !== j) })} />
        ))}
        {member.activities.length < MAX_ACTIVITIES && (
          <Button variant="outline" size="sm" onClick={() => set({ activities: [...member.activities, newActivity()] })}>
            <Plus aria-hidden="true" /> Add an activity<span className="sr-only"> for {who}</span>
          </Button>
        )}
      </div>

      <CommuteFields path={`${at}.commute`} commute={member.commute ?? null} errors={errors}
        onChange={(commute) => set({ commute })} />

      {onRemove && (
        <Button variant="ghost" size="sm" className="text-danger" onClick={onRemove}>
          <Trash2 aria-hidden="true" /> Remove {who}
        </Button>
      )}
    </fieldset>
  );
}

function ActivityFields({ path, number, who, activity, errors, onChange, onRemove }: {
  path: string; number: number; who: string; activity: Activity; errors: Errors;
  onChange: (activity: Activity) => void; onRemove: () => void;
}) {
  const set = (patch: Partial<Activity>) => onChange({ ...activity, ...patch });
  const rowError = errors[path];  // a whole-row problem, e.g. ending after midnight
  return (
    // The id lets a whole-row error move focus here.
    <fieldset id={path} tabIndex={-1} aria-describedby={rowError ? `${path}-error` : undefined}
      className="rounded-md bg-surface-soft p-3">
      <legend className="sr-only">Activity {number} for {who}</legend>
      <div className="grid items-end gap-3 sm:grid-cols-[1.4fr_1fr_0.8fr_1.4fr_auto]">
        <FormField path={`${path}.kind`} label="Activity" errors={errors}>
          {(control) => (
            <Select {...control} value={activity.kind} onChange={(event) => set({ kind: event.target.value as Activity["kind"] })}>
              {options(ACTIVITY_KINDS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </Select>
          )}
        </FormField>
        <FormField path={`${path}.start`} label="Starts at" errors={errors}>
          {(control) => <Input {...control} type="time" value={activity.start} onChange={(event) => set({ start: event.target.value })} />}
        </FormField>
        <FormField path={`${path}.duration_min`} label="Minutes" errors={errors}>
          {(control) => <NumberInput {...control} inputMode="numeric" min={10} max={240} step={5}
            value={activity.duration_min} onValueChange={(duration_min) => set({ duration_min })} />}
        </FormField>
        <FormField path={`${path}.intensity`} label="Effort" errors={errors}>
          {(control) => (
            <Select {...control} value={activity.intensity} onChange={(event) => set({ intensity: event.target.value as Activity["intensity"] })}>
              {options(INTENSITIES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </Select>
          )}
        </FormField>
        <Button variant="ghost" size="icon" onClick={onRemove} aria-label={`Remove activity ${number} for ${who}`}>
          <Trash2 aria-hidden="true" />
        </Button>
      </div>
      {rowError && <p id={`${path}-error`} className="mt-2 text-sm text-danger">{rowError}</p>}
    </fieldset>
  );
}

function CommuteFields({ path, commute, errors, onChange }: {
  path: string; commute: Commute | null; errors: Errors; onChange: (commute: Commute | null) => void;
}) {
  const set = (patch: Partial<Commute>) => commute && onChange({ ...commute, ...patch });
  const chooseMode = (value: string) => {
    if (value === "") return onChange(null);
    const mode = value as CommuteMode;
    const base = commute ?? newCommute();
    onChange({ ...base, mode, walking_leg_min: HAS_WALKING_LEG.has(mode) ? base.walking_leg_min : 0 });
  };
  return (
    <div className="space-y-3">
      <FormField path={`${path}.mode`} label="Regular commute" errors={errors} className="sm:max-w-xs">
        {(control) => (
          <Select {...control} value={commute?.mode ?? ""} onChange={(event) => chooseMode(event.target.value)}>
            <option value="">No regular commute</option>
            {options(COMMUTE_MODES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </Select>
        )}
      </FormField>
      {commute && (
        <div className="grid gap-3 sm:grid-cols-4">
          <FormField path={`${path}.one_way_km`} label="Km one way" errors={errors}>
            {(control) => <NumberInput {...control} min={0.5} max={100} step={0.5}
              value={commute.one_way_km} onValueChange={(one_way_km) => set({ one_way_km })} />}
          </FormField>
          <FormField path={`${path}.days_per_week`} label="Days a week" errors={errors}>
            {(control) => <NumberInput {...control} inputMode="numeric" min={1} max={7} step={1}
              value={commute.days_per_week} onValueChange={(days_per_week) => set({ days_per_week })} />}
          </FormField>
          <FormField path={`${path}.departs`} label="Leaves at" errors={errors}>
            {(control) => <Input {...control} type="time" value={commute.departs} onChange={(event) => set({ departs: event.target.value })} />}
          </FormField>
          {HAS_WALKING_LEG.has(commute.mode) && (
            <FormField path={`${path}.walking_leg_min`} label="Walk to the stop (min)" errors={errors}>
              {(control) => <NumberInput {...control} inputMode="numeric" min={0} max={60} step={1}
                value={commute.walking_leg_min} onValueChange={(walking_leg_min) => set({ walking_leg_min })} />}
            </FormField>
          )}
        </div>
      )}
    </div>
  );
}
