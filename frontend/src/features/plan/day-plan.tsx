// The household's day: one card per person, then the home, then cleaner ways to get around.
// Every decision and number comes from the rules; only the "why" sentences may be AI-worded.

import { Bus, House, ListChecks } from "lucide-react";
import { SourceBadge } from "@/components/badges";
import { DecisionCard, ToneChip } from "@/components/decision";
import { Panel } from "@/components/layout";
import type { HomeAdviceOut, MemberPlanOut, PlanOut } from "@/lib/api/types";
import { ALTERNATIVES, HOME_ACTIONS } from "@/lib/labels";

export function DayPlan({ plan }: { plan: PlanOut }) {
  const commuters = plan.members.filter((member) => member.commute);
  return (
    <>
      <Panel id="people" title="Each person's day" icon={ListChecks} description={<Provenance aiUsed={plan.ai_used} />}>
        <ul className="grid gap-4 lg:grid-cols-2">
          {plan.members.map((member) => <PersonCard key={member.member_id} member={member} aiWorded={plan.ai_used} />)}
        </ul>
      </Panel>

      <Panel id="home" title="At home today" icon={House} description="Simple steps that keep indoor air cleaner.">
        <ul className="divide-y">
          {plan.home.map((advice) => <HomeRow key={advice.action} advice={advice} aiWorded={plan.ai_used} />)}
        </ul>
      </Panel>

      {commuters.length > 0 && (
        <Panel id="travel" title="Getting around" icon={Bus}
          description="Cleaner ways to make the same trips: less exhaust on the roads you breathe beside.">
          <div className="space-y-6">
            {commuters.map((member) => <CommuteBlock key={member.member_id} member={member} aiWorded={plan.ai_used} />)}
          </div>
        </Panel>
      )}

      <section aria-labelledby="sources-title" className="text-xs text-muted-foreground">
        <h2 id="sources-title" className="mb-1 text-sm font-semibold text-foreground">Where the numbers come from</h2>
        <ul className="list-disc space-y-0.5 pl-5">
          {plan.sources.map((source) => <li key={source}>{source}</li>)}
        </ul>
      </section>
    </>
  );
}

function Provenance({ aiUsed }: { aiUsed: boolean }) {
  return (
    <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <span className="inline-flex items-center gap-1.5">Decisions and numbers: fixed rules <SourceBadge source="rules" /></span>
      {aiUsed
        ? <span className="inline-flex items-center gap-1.5">Explanations: worded by AI <SourceBadge source="ai" /></span>
        : <span>Explanations: the app's own wording.</span>}
    </span>
  );
}

function PersonCard({ member, aiWorded }: { member: MemberPlanOut; aiWorded: boolean }) {
  const nothingOutdoors = member.decisions.length === 0 && !member.commute;
  return (
    <li className="space-y-4 rounded-lg border p-4">
      <h3 className="text-lg font-semibold">{member.name}</h3>
      {member.decisions.map((decision) => (
        <DecisionCard key={`${decision.activity.kind}-${decision.activity.start}`} decision={decision} aiWorded={aiWorded} />
      ))}
      {member.commute && (
        <div className="space-y-2">
          <p className="font-medium">Commute</p>
          {member.commute.mask === "n95"
            ? <ToneChip tone="warning">Wear a well-fitted N95 on the walk</ToneChip>
            : <p className="text-sm text-muted-foreground">
                {member.commute.swaps.length ? "Cleaner ways to make this trip are under Getting around." : "No change needed."}
              </p>}
        </div>
      )}
      {nothingOutdoors && <p className="text-sm text-muted-foreground">Nothing outdoors planned today.</p>}
    </li>
  );
}

function HomeRow({ advice, aiWorded }: { advice: HomeAdviceOut; aiWorded: boolean }) {
  return (
    <li className="space-y-1 py-3 first:pt-0 last:pb-0">
      <p className="font-medium">{HOME_ACTIONS[advice.action]}</p>
      {advice.impact && <p className="text-sm font-medium">{advice.impact}</p>}
      <p className="text-sm text-muted-foreground">{advice.why}{aiWorded && <> <SourceBadge source="ai" /></>}</p>
    </li>
  );
}

function CommuteBlock({ member, aiWorded }: { member: MemberPlanOut; aiWorded: boolean }) {
  const swaps = member.commute?.swaps ?? [];
  return (
    <div className="space-y-3">
      <h3 className="font-semibold">{member.name}'s commute</h3>
      {swaps.length === 0 ? (
        <p className="text-sm text-muted-foreground">Already one of the cleanest ways to travel.</p>
      ) : (
        <ul className="grid gap-3 md:grid-cols-3">
          {swaps.map((swap) => (
            <li key={swap.alternative} className="space-y-1 rounded-lg border p-4">
              <p className="font-semibold">{ALTERNATIVES[swap.alternative]}</p>
              <p className="text-sm font-medium">{swap.impact}</p>
              <p className="text-sm text-muted-foreground">{swap.why}{aiWorded && <> <SourceBadge source="ai" /></>}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
