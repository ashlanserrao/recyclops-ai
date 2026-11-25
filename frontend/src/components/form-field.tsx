// One labelled control in the setup form. The control's id is its API field path
// ("household.members.0.age"), so an error from the browser or the server finds it by the same name.

import type { ReactNode } from "react";
import { describedBy, Field } from "@/components/ui/field";

export type Errors = Record<string, string>;

type ControlProps = { id: string } & ReturnType<typeof describedBy>;

export function FormField({ path, label, errors, hint, className, children }: {
  path: string; label: ReactNode; errors: Errors; hint?: ReactNode; className?: string;
  children: (control: ControlProps) => ReactNode;
}) {
  const error = errors[path];
  return (
    <Field id={path} label={label} error={error} hint={hint} className={className}>
      {children({ id: path, ...describedBy(path, error, hint !== undefined) })}
    </Field>
  );
}

/** Focus the field a path names, or the nearest group around it (an activity row for a whole-row error). */
export function focusField(path: string) {
  for (let parts = path.split("."); parts.length > 0; parts = parts.slice(0, -1)) {
    const element = document.getElementById(parts.join("."));
    if (element) {
      element.focus();
      return;
    }
  }
}
