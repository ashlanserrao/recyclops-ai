// The setup form: where, who, and the home. Blank entries are caught here; the server checks the rest
// and its field errors (passed in as serverErrors) land on the same inputs.

import { Plus } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox, NumberInput, Select } from "@/components/ui/field";
import type { FieldError, Household, Member } from "@/lib/api/types";
import { errorMap, MAX_MEMBERS, missingFields, newHousehold, newMember, type Place, type Profile } from "@/lib/household";
import { COOKING_FUELS, options } from "@/lib/labels";
import { type Errors, FormField, focusField } from "@/components/form-field";
import { LocationField } from "@/features/setup/location-field";
import { MemberFields } from "@/features/setup/member-fields";

/** Focus the first problem after React has rendered the messages, so it's announced with its error. */
function focusFirst(fields: FieldError[]) {
  const first = fields[0];
  if (first) requestAnimationFrame(() => focusField(first.field));
}

export function HouseholdForm({ initial, serverErrors, onSave, onCancel }: {
  initial: Profile | null; serverErrors: FieldError[]; onSave: (profile: Profile) => void; onCancel?: () => void;
}) {
  const [place, setPlace] = useState<Place | null>(initial?.place ?? null);
  const [household, setHousehold] = useState<Household>(initial?.household ?? newHousehold);
  const [errors, setErrors] = useState<Errors>({});

  const showErrors = (fields: FieldError[]) => {
    setErrors(errorMap(fields));
    focusFirst(fields);
  };

  useEffect(() => {
    if (!serverErrors.length) return;
    setErrors(errorMap(serverErrors));
    focusFirst(serverErrors);
  }, [serverErrors]);

  const { home, members } = household;
  const setHome = (patch: Partial<Household["home"]>) => setHousehold({ ...household, home: { ...home, ...patch } });
  const setMembers = (next: Member[]) => setHousehold({ ...household, members: next });
  const removeMember = (index: number) => {
    setMembers(members.filter((_, i) => i !== index));
    setErrors({});  // error paths are by position, and the positions just changed
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const missing = missingFields({ place, household });
    if (missing.length || !place) return showErrors(missing);
    setErrors({});
    onSave({ place, household });
  };

  const count = Object.keys(errors).length;
  const locationError = Object.entries(errors).find(([field]) => field.startsWith("location"))?.[1];

  return (
    <form noValidate onSubmit={submit} className="space-y-6">
      {count > 0 && (
        <p role="alert" className="rounded-md border border-danger bg-danger-soft px-4 py-3 text-sm">
          {count === 1 ? "One entry needs a look." : `${count} entries need a look.`} They're marked below.
        </p>
      )}

      <section aria-labelledby="where-title" className="space-y-3">
        <h3 id="where-title" className="font-semibold">Where you live</h3>
        <LocationField place={place} error={locationError} onChange={setPlace} />
      </section>

      <section aria-labelledby="who-title" className="space-y-3">
        <h3 id="who-title" className="font-semibold">Who's at home <span className="text-sm font-normal text-muted-foreground">(up to {MAX_MEMBERS})</span></h3>
        {members.map((member, index) => (
          <MemberFields key={member.id} member={member} index={index} errors={errors}
            onChange={(next) => setMembers(members.map((m, i) => (i === index ? next : m)))}
            onRemove={members.length > 1 ? () => removeMember(index) : undefined} />
        ))}
        {members.length < MAX_MEMBERS && (
          <Button variant="outline" onClick={() => setMembers([...members, newMember(members)])}>
            <Plus aria-hidden="true" /> Add a person
          </Button>
        )}
      </section>

      <section aria-labelledby="home-title" className="space-y-3">
        <h3 id="home-title" className="font-semibold">Your home</h3>
        <div className="grid gap-x-4 sm:grid-cols-2">
          <Checkbox label="Windows face a busy road" checked={home.faces_main_road}
            onChange={(event) => setHome({ faces_main_road: event.target.checked })} />
          <Checkbox label="We have an air purifier" checked={home.has_purifier}
            onChange={(event) => setHome({ has_purifier: event.target.checked, purifier_room_m2: null })} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField path="household.home.cooking_fuel" label="Cooking fuel" errors={errors}>
            {(control) => (
              <Select {...control} value={home.cooking_fuel}
                onChange={(event) => setHome({ cooking_fuel: event.target.value as Household["home"]["cooking_fuel"] })}>
                {options(COOKING_FUELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </Select>
            )}
          </FormField>
          {home.has_purifier && (
            <FormField path="household.home.purifier_room_m2" label="Purifier room size (m²)" errors={errors}
              hint="Optional. Used to check the purifier is big enough for the room.">
              {(control) => <NumberInput {...control} min={1} max={200} step={1} value={home.purifier_room_m2}
                onValueChange={(size) => setHome({ purifier_room_m2: Number.isNaN(size) ? null : size })} />}
            </FormField>
          )}
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        <Button type="submit">Save household</Button>
        {onCancel && <Button variant="ghost" onClick={onCancel}>Cancel</Button>}
      </div>
    </form>
  );
}
