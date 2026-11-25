// "Can we...?": a typed question the AI reads into fields, or the same fields as a form.
// Either way the rules decide the answer; the AI never says yes or no.

import { MessageCircleQuestion } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { SourceBadge } from "@/components/badges";
import { DecisionCard, ToneChip } from "@/components/decision";
import { type Errors, FormField, useFocusField } from "@/components/form-field";
import { Panel } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/field";
import { ApiError, api } from "@/lib/api/client";
import type { AskForm, AskOut, FieldError } from "@/lib/api/types";
import { day } from "@/lib/format";
import { errorMap, type Profile } from "@/lib/household";
import { activityLine, VERDICTS } from "@/lib/labels";
import { AskFormFields, firstForm, missingInForm } from "@/features/ask/ask-form";

const UNCLEAR = "Couldn't tell who, what or when from that question. Fill in the details instead.";
const NO_AI = "Reading questions in your own words needs the AI, which isn't available right now. Fill in the details instead.";

type AskState =
  | { status: "idle" }
  | { status: "asking" }
  | { status: "answered"; answer: AskOut }
  | { status: "failed"; error: ApiError };

export function AskPanel({ profile }: { profile: Profile }) {
  const { household, place } = profile;
  const [mode, setMode] = useState<"question" | "form">("question");
  const [question, setQuestion] = useState("");
  const [form, setForm] = useState<AskForm>(() => firstForm(household.members));
  const [notice, setNotice] = useState<string | null>(null);
  const [errors, setErrors] = useState<Errors>({});
  const [state, setState] = useState<AskState>({ status: "idle" });
  const inFlight = useRef<AbortController | null>(null);
  useEffect(() => () => inFlight.current?.abort(), []);
  const focus = useFocusField();

  const showErrors = (fields: FieldError[]) => {
    setErrors(errorMap(fields));
    const first = fields[0];
    if (first) focus(first.field);
  };

  const switchToForm = (why: string | null) => {
    setMode("form");
    setNotice(why);
    setErrors({});
    focus("form.member_id");
  };

  const send = async (body: { question: string } | { form: AskForm }) => {
    inFlight.current?.abort();
    const controller = new AbortController();
    inFlight.current = controller;
    setState({ status: "asking" });
    setErrors({});
    try {
      const answer = await api.ask({ location: { lat: place.lat, lon: place.lon }, household, ...body }, controller.signal);
      if (answer.needs_form) {
        setState({ status: "idle" });
        switchToForm(answer.ai_used ? UNCLEAR : NO_AI);
      } else {
        setState({ status: "answered", answer });
      }
    } catch (error) {
      if (controller.signal.aborted) return;
      const failure = error instanceof ApiError ? error : new ApiError(String(error));
      setState({ status: "failed", error: failure });
      showErrors(failure.fields);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (mode === "question") {
      if (question.trim().length < 3) return showErrors([{ field: "question", message: "Type a question, like the example." }]);
      return send({ question: question.trim() });
    }
    const missing = missingInForm(form);
    if (missing.length) return showErrors(missing);
    return send({ form });
  };

  const example = `Can ${household.members[0]?.name ?? "we"} go for a walk at 6 pm?`;
  const asking = state.status === "asking";

  return (
    <Panel id="ask" title="Can we…?" icon={MessageCircleQuestion}
      description="Ask about one activity. The rules check the forecast and decide; the AI only reads your question.">
      <form noValidate onSubmit={submit} className="space-y-4">
        {mode === "question" ? (
          <div className="space-y-2">
            <FormField path="question" label="Your question" errors={errors} hint={`For example: "${example}"`}>
              {(control) => <Input {...control} maxLength={200} autoComplete="off" value={question}
                onChange={(event) => setQuestion(event.target.value)} />}
            </FormField>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={asking}>{asking ? "Checking…" : "Ask"}</Button>
              <Button variant="ghost" onClick={() => setQuestion(example)}>Use the example</Button>
              <Button variant="link" onClick={() => switchToForm(null)}>Use the form instead</Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {notice && <p className="rounded-md border border-warning/30 bg-warning-soft p-3 text-sm">{notice}</p>}
            <AskFormFields form={form} members={household.members} errors={errors} onChange={setForm} />
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={asking}>{asking ? "Checking…" : "Check"}</Button>
              <Button variant="link" onClick={() => { setMode("question"); setNotice(null); setErrors({}); }}>
                Type a question instead
              </Button>
            </div>
          </div>
        )}
      </form>

      <div className="mt-6" aria-busy={asking}>
        {state.status === "failed" && !state.error.fields.length && (
          <p role="alert" className="rounded-md border border-danger bg-danger-soft p-3 text-sm">{state.error.message}</p>
        )}
        {state.status === "answered" && <Answer answer={state.answer} onWrongReading={() => switchToForm(null)} />}
      </div>
      {/* Short and polite: the verdict, not the whole card. */}
      <p aria-live="polite" className="sr-only">
        {state.status === "answered" && state.answer.verdict && state.answer.asked
          ? `Answer for ${state.answer.asked.name}: ${VERDICTS[state.answer.verdict].text}.` : ""}
      </p>
    </Panel>
  );
}

function Answer({ answer, onWrongReading }: { answer: AskOut; onWrongReading: () => void }) {
  const { asked, verdict, decision } = answer;
  if (!asked || !verdict || !decision) return null;
  return (
    <section aria-labelledby="answer-title" className="space-y-4 rounded-lg border p-4">
      <h3 id="answer-title" className="sr-only">Answer</h3>
      <ToneChip tone={VERDICTS[verdict].tone}>{VERDICTS[verdict].text}</ToneChip>
      <p className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <span>Understood as: <span className="text-foreground">{asked.name}, {activityLine(asked.activity).toLowerCase()}, {day(asked.day)}</span></span>
        {answer.ai_used && (
          <>
            <SourceBadge source="aiRead" />
            <Button variant="link" size="sm" className="px-1" onClick={onWrongReading}>Not right? Use the form</Button>
          </>
        )}
      </p>
      <DecisionCard decision={decision} aiWorded={false} />
    </section>
  );
}
