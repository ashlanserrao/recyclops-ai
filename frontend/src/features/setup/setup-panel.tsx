// The household panel: the form while editing, a one-line summary once saved.
// Example households save in one click, so anyone can see a full plan without typing.

import { Pencil, Users } from "lucide-react";
import { useEffect, useRef } from "react";
import { Panel } from "@/components/layout";
import { Button } from "@/components/ui/button";
import type { FieldError } from "@/lib/api/types";
import { DEMOS } from "@/lib/demo-households";
import { membersLine, type Profile } from "@/lib/household";
import { HouseholdForm } from "@/features/setup/household-form";

const PRIVACY = "Saved in this browser only. Each plan sends it to the server, which keeps nothing.";

export function SetupPanel({ profile, editing, serverErrors, onEdit, onSave, onCancel }: {
  profile: Profile | null; editing: boolean; serverErrors: FieldError[];
  onEdit: () => void; onSave: (profile: Profile) => void; onCancel: () => void;
}) {
  // When the form closes, its Save button goes with it: focus moves to "Edit household" instead.
  const editButton = useRef<HTMLButtonElement>(null);
  const wasEditing = useRef(editing);
  useEffect(() => {
    if (wasEditing.current && !editing) editButton.current?.focus();
    wasEditing.current = editing;
  }, [editing]);

  if (!editing && profile) {
    return (
      <Panel id="household" title="Your household" icon={Users} description={PRIVACY}
        actions={<Button ref={editButton} variant="outline" onClick={onEdit}><Pencil aria-hidden="true" /> Edit household</Button>}>
        <p>
          <span className="font-semibold">{profile.place.name ?? "Your location"}</span>
          <span className="text-muted-foreground"> · {membersLine(profile.household)}</span>
        </p>
      </Panel>
    );
  }

  return (
    <Panel id="household" title={profile ? "Edit your household" : "Set up your household"} icon={Users} description={PRIVACY}>
      <div className="mb-6 space-y-3">
        <h3 className="font-semibold">Try an example</h3>
        <ul className="grid gap-3 md:grid-cols-3">
          {DEMOS.map((demo) => (
            <li key={demo.id}>
              <button type="button" onClick={() => onSave(demo.profile)}
                className="h-full w-full cursor-pointer rounded-lg border bg-surface p-4 text-left transition-colors hover:bg-surface-soft">
                <span className="block font-semibold">{demo.label}</span>
                <span className="mt-1 block text-sm text-muted-foreground">{demo.detail}</span>
              </button>
            </li>
          ))}
        </ul>
        {profile && <p className="text-sm text-muted-foreground">An example replaces the household saved here.</p>}
      </div>
      <p className="mb-4 flex items-center gap-3 text-sm text-muted-foreground before:h-px before:flex-1 before:bg-border after:h-px after:flex-1 after:bg-border">
        Or fill in your own
      </p>
      <HouseholdForm initial={profile} serverErrors={serverErrors} onSave={onSave} onCancel={profile ? onCancel : undefined} />
    </Panel>
  );
}
