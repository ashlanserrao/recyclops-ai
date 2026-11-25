// "Can we...?" as a form: who, which day, and the activity. Needs no AI, so it always works.

import { type Errors, FormField } from "@/components/form-field";
import { Input, NumberInput, Select } from "@/components/ui/field";
import type { Activity, AskForm, Member } from "@/lib/api/types";
import { newActivity } from "@/lib/household";
import { ACTIVITY_KINDS, INTENSITIES, options } from "@/lib/labels";

/** Starts from the first person and their first usual activity, the likeliest thing to ask about. */
export const firstForm = (members: Member[]): AskForm => ({
  member_id: members[0]?.id ?? "",
  day: "today",
  activity: members[0]?.activities[0] ?? newActivity(),
});

/** Blank entries, by the server's field paths (the server checks the rest). */
export function missingInForm({ activity }: AskForm): { field: string; message: string }[] {
  const missing = [];
  if (!activity.start) missing.push({ field: "form.activity.start", message: "Enter a start time." });
  if (Number.isNaN(activity.duration_min)) missing.push({ field: "form.activity.duration_min", message: "Enter how many minutes." });
  return missing;
}

export function AskFormFields({ form, members, errors, onChange }: {
  form: AskForm; members: Member[]; errors: Errors; onChange: (form: AskForm) => void;
}) {
  const setActivity = (patch: Partial<Activity>) => onChange({ ...form, activity: { ...form.activity, ...patch } });
  const rowError = errors["form.activity"];  // e.g. ending after midnight
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <FormField path="form.member_id" label="Who" errors={errors}>
          {(control) => (
            <Select {...control} value={form.member_id} onChange={(event) => onChange({ ...form, member_id: event.target.value })}>
              {members.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}
            </Select>
          )}
        </FormField>
        <FormField path="form.day" label="When" errors={errors}>
          {(control) => (
            <Select {...control} value={form.day} onChange={(event) => onChange({ ...form, day: event.target.value as AskForm["day"] })}>
              <option value="today">Today</option>
              <option value="tomorrow">Tomorrow</option>
            </Select>
          )}
        </FormField>
        <FormField path="form.activity.kind" label="Activity" errors={errors}>
          {(control) => (
            <Select {...control} value={form.activity.kind} onChange={(event) => setActivity({ kind: event.target.value as Activity["kind"] })}>
              {options(ACTIVITY_KINDS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </Select>
          )}
        </FormField>
        <FormField path="form.activity.start" label="Starts at" errors={errors}>
          {(control) => <Input {...control} type="time" value={form.activity.start.slice(0, 5)}
            onChange={(event) => setActivity({ start: event.target.value })} />}
        </FormField>
        <FormField path="form.activity.duration_min" label="Minutes" errors={errors}>
          {(control) => <NumberInput {...control} inputMode="numeric" min={10} max={240} step={5}
            value={form.activity.duration_min} onValueChange={(duration_min) => setActivity({ duration_min })} />}
        </FormField>
        <FormField path="form.activity.intensity" label="Effort" errors={errors}>
          {(control) => (
            <Select {...control} value={form.activity.intensity} onChange={(event) => setActivity({ intensity: event.target.value as Activity["intensity"] })}>
              {options(INTENSITIES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </Select>
          )}
        </FormField>
      </div>
      {rowError && <p id="form.activity" tabIndex={-1} className="text-sm text-danger">{rowError}</p>}
    </div>
  );
}
