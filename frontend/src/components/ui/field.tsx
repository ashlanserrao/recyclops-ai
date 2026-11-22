// Native form controls with shadcn styling: accessible by default, no scripts or injected styles.

import type { ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/utils";

const control = "h-11 w-full rounded-md border border-input bg-surface px-3 text-sm text-foreground aria-invalid:border-danger";

export const Input = ({ className, ...props }: ComponentProps<"input">) => (
  <input className={cn(control, className)} {...props} />
);

/** A number box whose empty state is NaN, so "blank" and "0" stay different. */
export const NumberInput = ({ value, onValueChange, ...props }:
  Omit<ComponentProps<"input">, "value" | "onChange" | "type"> & { value: number | null | undefined; onValueChange: (value: number) => void }) => (
  <Input type="number" inputMode="decimal" value={value == null || Number.isNaN(value) ? "" : value}
    onChange={(event) => onValueChange(event.target.valueAsNumber)} {...props} />
);

/** A checkbox with its label as one 44 px tall target. */
export const Checkbox = ({ label, className, ...props }: Omit<ComponentProps<"input">, "type"> & { label: ReactNode }) => (
  <label className={cn("flex min-h-11 cursor-pointer items-center gap-3 text-sm", className)}>
    <input type="checkbox" className="size-5 shrink-0 accent-primary" {...props} />
    {label}
  </label>
);

export const Select =({ className, ...props }: ComponentProps<"select">) => (
  <select className={cn(control, "pr-8", className)} {...props} />
);

export const Textarea = ({ className, ...props }: ComponentProps<"textarea">) => (
  <textarea className={cn(control, "h-auto min-h-20 py-2", className)} {...props} />
);

/** A labelled field: the label points at the control, the error is announced with it. */
export function Field({ id, label, error, hint, children, className }: {
  id: string; label: ReactNode; error?: string; hint?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <label htmlFor={id} className="block text-sm font-medium">{label}</label>
      {children}
      {error ? <FieldError id={`${id}-error`}>{error}</FieldError>
        : hint && <p id={`${id}-hint`} className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

export const FieldError = ({ id, children }: { id: string; children?: ReactNode }) =>
  children ? <p id={id} className="text-sm text-danger">{children}</p> : null;

/** Props that tie a control to its error or hint for screen readers. */
export const describedBy = (id: string, error?: string, hasHint = false) => ({
  "aria-invalid": error ? true : undefined,
  "aria-describedby": error ? `${id}-error` : hasHint ? `${id}-hint` : undefined,
});
