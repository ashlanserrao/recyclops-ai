// Page building blocks: section cards and empty states.

import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Panel({ id, title, icon: Icon, description, actions, children, className }: {
  id?: string; title: ReactNode; icon?: LucideIcon; description?: ReactNode; actions?: ReactNode;
  children: ReactNode; className?: string;
}) {
  const headingId = id ? `${id}-title` : undefined;
  return (
    <section id={id} aria-labelledby={headingId} className={cn("rounded-xl border bg-card p-5 md:p-6", className)}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 flex-1 basis-60 items-start gap-3">
          {Icon && (
            <span className="rounded-[10px] bg-surface-soft p-2 text-muted-foreground">
              <Icon className="size-4" aria-hidden="true" />
            </span>
          )}
          <div className="min-w-0">
            <h2 id={headingId} className="text-lg">{title}</h2>
            {description && <div className="mt-1 text-sm text-muted-foreground">{description}</div>}
          </div>
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
      {children}
    </section>
  );
}

export const EmptyState = ({ icon: Icon, title, children }: { icon: LucideIcon; title: string; children?: ReactNode }) => (
  <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-input p-8 text-center">
    <Icon className="size-6 text-muted-foreground" aria-hidden="true" />
    <p className="font-semibold">{title}</p>
    {children && <div className="max-w-md text-sm text-muted-foreground">{children}</div>}
  </div>
);
