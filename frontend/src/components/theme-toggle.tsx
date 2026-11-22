import { Monitor, Moon, Sun } from "lucide-react";
import { type ThemePreference, useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const OPTIONS: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "auto", label: "Match device", icon: Monitor },
];

/** Three buttons in a group; the pressed one is the current preference. */
export function ThemeToggle() {
  const { preference, setPreference } = useTheme();
  return (
    <fieldset className="flex rounded-md border bg-surface p-0.5">
      <legend className="sr-only">Colour theme</legend>
      {OPTIONS.map(({ value, label, icon: Icon }) => (
        <button key={value} type="button" aria-pressed={preference === value} aria-label={label} title={label}
          onClick={() => setPreference(value)}
          className={cn("grid size-10 place-items-center rounded-[10px] text-muted-foreground",
            preference === value && "bg-surface-soft text-foreground")}>
          <Icon className="size-4" aria-hidden="true" />
        </button>
      ))}
    </fieldset>
  );
}
