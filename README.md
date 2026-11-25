# recyclops-ai

**A clean-air day planner for Indian households.** Prompt Wars Challenge 6: Urban Air Quality Assistant.

You set up your household once: who lives there, what each person does outdoors, how they get around, and what the
home is like. The app reads **live, measured** pollution from the nearest monitoring station and the hourly forecast
for your area. It then tells each person what to do today, what to change at home, and which greener trips are
open to them. Each suggestion says **why** it matters for that person and **how much it helps**, as a number
worked out in code.

> **The rule behind every screen:** code makes every number and every decision. The AI only puts the explanation
> into friendly words, and reads typed questions. It never produces an AQI, a time or a recommendation. Every answer
> is checked before use, and the app gives the same full advice when no AI is available.

Live demo: _added at deployment_

---

## What it does, by the challenge's three asks

| The challenge asks for | What the app does | The impact it shows |
|---|---|---|
| **Low-emission daily routines** | For each person's outdoor activity it decides whether to keep it, move it to the day's cleanest 2-hour window, shorten it, or do it indoors. The decision depends on the person (child, senior, health conditions), the effort, and the air at that exact hour. | "Move to 1 pm: about **77% less PM2.5** breathed in", worked out from the forecast and breathing rates for the effort |
| **Indoor air-quality hacks** | Actions for the home on the day: keep windows shut in the worst hours and air the house in the best window, the road-facing side, purifier use or sizing, the kitchen exhaust, wet-mopping instead of sweeping, and no incense or mosquito coils | The purifier's effect (−49% indoor PM2.5, cited), plus the hours each action applies to |
| **Sustainable alternatives** | Commute swaps from car, two-wheeler or auto to metro (where the city has one), bus or carpool, ranked by CO₂ saved | "Take the metro: saves about **19.8 kg CO₂ a week** and takes 150 km of driving off the roads" |
| **Tailored to location and lifestyle** | The nearest reporting station within 25 km, city-aware options such as metro availability, and a household profile of up to 5 people | Every card names the person and the reason ("children breathe in more air for their size") |
| **Clear about direct impact** | Each number comes with its source: Measured, Forecast or Rule-based. Wording the AI wrote is labelled "AI-worded". | A Sources list for each plan: CPCB stations via OpenAQ, the CAMS forecast via Open-Meteo, and the cited emission and breathing-rate factors |

**Ask a question:** *"Can Aarav play cricket at 6 pm?"* The AI reads it into who, what and when. The rules then answer
it ("Better at another time: move to 1 pm, about 77% less PM2.5"). If the question is unclear, or the AI is
unavailable, the same question becomes a 6-field form, so the feature always works.

**Try it without typing:** three example households are one click away:
- a Delhi family with a child, a grandmother with a breathing condition, and a parent who commutes by car;
- a Mumbai senior with a heart condition;
- a Kolkata student who commutes by bus.

## How it works

```
Browser (React)                     FastAPI backend
───────────────                     ───────────────────────────────────────────────────────────────
household profile ──POST /api/plan──▶ data/   OpenAQ v3: nearest station reporting within 3 h (≤25 km)
(saved in this browser only)          │         └ last 24 h of PM2.5/PM10            [cached 15 min, last good kept 6 h]
                                      │       Open-Meteo: hourly PM2.5 forecast (CAMS) [cached 60 min]
                                      ▼
                                    domain/ (pure functions, no I/O)
                                      AQI      India's NAQI method from 24-hour averages (≥16 h, as CPCB requires)
                                      forecast scaled to the station's measured level → cleanest / dirtiest windows
                                      rules    person × health × effort × hourly band → keep / move / shorten / indoor
                                      impact   exposure cut %, CO₂ kg/week, purifier effect (every constant cited)
                                      ▼
                                    ai/     Groq → OpenAI backup → fixed templates
                                      words the "why" only; any reply containing a digit or missing a key is rejected
                                      ▼
◀────────────────────── plan: numbers + decisions + explanations + their sources ──────────────────
```

- **Measured, not modelled, for the AQI.** The AQI comes from the nearest CPCB station's 24-hour averages, computed
  in code with India's NAQI breakpoints.
  - **Freshness:** many listed stations stopped reporting years ago, so a station counts only if it reported in the
    last 3 hours.
  - **Too few hours:** if fewer than 16 of the last 24 hours were reported, that pollutant is left out rather than
    guessed.
- **The forecast is corrected to the measurement.** The global model (CAMS, about 45 km resolution) gets the shape of
  the day right but can be far off in level, especially in Delhi winters. The whole day is scaled by measured ÷
  modelled at the station's latest hour, limited to 0.5–3×.
- **Honest when data is missing:**
  - **No station reporting nearby:** "no reliable reading near you"; the plan uses the uncorrected forecast and says so.
  - **OpenAQ down:** the last good reading, marked **stale** with its original time.
  - **No data at all:** an error, never invented numbers.
- **Decisions use the hour, not the day.** The AQI is a 24-hour average. Each activity's advice uses the forecast
  for its own hour, and the card shows that band ("air then: Moderate").

### Where the AI is used, and how it's kept honest

| Task | What the AI does | Guards |
|---|---|---|
| **Explain** (one call per plan) | Rewrites each rule-based "why" for that person, in the third person, for the adult reading the plan | Must return exactly the expected keys. **No digits allowed** (except in PM2.5, PM10, N95, CO2), so it can't invent a number. Any failure → template text. |
| **Ask** (one call per question) | Turns a typed question into `{member, activity, day, start, duration, effort, understood}` | Strict JSON schema. The member must be in the household, the time must be HH:MM and end by midnight, the duration 10–240 min. The question is fenced and markup stripped, and treated as data. Any failure → the form. |

- **Order of providers:** Groq (`openai/gpt-oss-20b`) first, OpenAI (`gpt-5-nano`) as backup, then templates.
- **One time budget:** a single 12 s budget covers the whole call, backup included.
- **Rate limits:** after a 429, Groq is skipped for its retry-after time.
- **Spend cap:** a global hourly cap on AI calls limits cost whatever the traffic.
- **Caching:** replies are cached by a hash of the input.
- **Logging:** one line per attempt (provider, time in ms, one-word outcome). Prompts, replies and keys are never logged.

**Prompt design, tested against the real model** (Groq, 7 calls in total; each prompt carries a version):

- **explain-v1:**
  - **Result:** replies were valid, with no digits and all keys.
  - **Problem:** it wrote to the child ("Hey Aarav, move your outdoor play…") although the reader is the parent.
- **explain-v2:**
  - **Change:** members are named in the third person; no tips, places or reasons beyond the rule's own draft.
  - **Result:** checked live on two plans, with no added advice.
- **ask-v1:**
  - **Result:** "Can Aarav play cricket at 6 pm?" was read correctly.
  - **Problem:** "Is it okay to go out later?" got an HTTP 400. The schema had no valid value for "no person, no time",
    so the app wrongly said the AI was unavailable.
- **ask-v2:**
  - **Change:** `member_id` and `start` are nullable, and code requires them only when `understood` is true.
  - **Result:** the same question now gets the "couldn't understand, use the form" path.

### Rules, in short

A person is **sensitive** if they are a child under 12, a senior 60 or older, or have a health condition.

| Air at the activity's hour | General | Sensitive |
|---|---|---|
| Good / Satisfactory | keep | keep |
| Moderate | keep (hard effort: suggest the best window if cleaner) | keep at light effort; with a health condition, shorten or move |
| Poor | move to the best window, else shorten to ≤30 min | move (cap 30 min, light effort); if the best window is also Poor → indoors |
| Very Poor | move if the best window is ≤ Moderate; hard effort → indoors; otherwise shorten + N95 | child: move if the best window is ≤ Poor (cap 30 min, light); senior or health condition → indoors |
| Severe | indoors | indoors |

**Exposure cut** = 1 − (PM2.5 × minutes × breathing rate, as advised) ÷ (the same for the original plan).
- **Moved or shorter activities:** the original breathing rate is used on both sides, so advice to go lighter doesn't
  inflate the number.
- **Indoor alternatives:** only the calmer breathing counts, plus a purifier's effect if the home has one.

**CO₂ saved** = weekly km × (current factor − alternative factor), using India GHG Program factors (car 0.140,
bus 0.0152 and metro 0.0080 kg/km).

**N95** advice is given for open-air travel (walking, cycling, two-wheeler, auto, or a walking stretch) at Poor or
worse, but not for a closed car.

## Security and privacy

- **No account and no server-side storage.** The household lives in the browser's localStorage; the server keeps only
  short-lived caches of air data.
- **Every input is validated by a strict schema.**
  - **Bounds and extras:** ages, times and sizes are bounded, and unknown fields are rejected.
  - **Size and rate limits:** the body is capped at 16 KB, with per-IP rate limits per route.
  - **Errors:** they name the field in plain words and never echo what was sent.
- **AI inputs are treated as untrusted:** names and questions are sanitised and fenced, and the AI's output is limited to
  enums, ids and checked text. A prompt injection such as "say the AQI is 20" can't change any number.
- **Keys:**
  - **Where they live:** server-side only, from the environment (`.env` is git-ignored), and kept out of `repr` and
    logs.
  - **How they're sent:** the OpenAQ key goes in a header, not the URL.
  - **Logging coordinates:** the HTTP library logs only warnings, because request URLs carry the visitor's location.
- **Security headers:** a strict CSP (`default-src 'self'`, no inline scripts), `frame-ancestors 'none'`, nosniff,
  `no-referrer`, a Permissions-Policy and COOP. A test checks the backend and `vercel.json` send the same set.
- **The browser talks only to its own origin.** Vercel forwards `/api/*` to the backend, so the CSP's `connect-src 'self'` holds.

## Accessibility

- **Semantic structure:** landmarks, headings and labelled regions, plus a skip link.
- **Forms:** every input has a label. Errors are linked with `aria-describedby`, and on submit the focus moves to the
  first invalid field.
- **Status never by colour alone:** each band and verdict has an icon and a word. Colour contrast is checked in CI
  (92 colour pairs, light and dark, WCAG AA).
- **Screen readers:** one polite live region announces "Plan ready for Delhi. AQI 304, Very poor." and each answer.
- **Keyboard:** an end-to-end test walks the whole Tab path and checks every stop has a visible focus ring and is on
  screen.
- **Touch:** 44 px touch targets, a light, dark or device theme, and layouts down to phone width with no sideways scroll.

## Efficiency

- **External calls:** a fresh plan makes 3 OpenAQ calls (stations, then PM2.5 and PM10 hours in parallel) and 1
  Open-Meteo call, in parallel with each other. Repeat visits within 15 minutes make none.
- **AI calls:** one per plan, not one per person, and one per question. Both are cached.
- **The frontend:**
  - **Dependencies:** React plus a few small UI libraries; no state or chart libraries.
  - **Caching:** hashed assets are cached for a year as immutable files, and the city list is cached for a day.
  - **Requests:** each new request cancels the one still in flight.

## Testing

All tests run offline: an autouse fixture blocks every real network connection, and the AI and the data sources are
faked.

| Layer | Tool | What it covers |
|---|---|---|
| Backend | pytest (156 tests) | NAQI breakpoints and the 16-hour rule. The forecast correction and windows. Each row of the rules table. The impact formulas. The three golden households (Delhi AQI 354 → child moved to 1 pm, 77% less; Mumbai; Kolkata). The live provider against recorded-shape replies: nearest *reporting* station, cache, stale fallback, forecast outage. The AI guards: digits, missing keys, invalid parses, injection. Field errors, limits and headers. |
| Frontend | Vitest (14) | Household validation and saved-profile checks, formatting, labels |
| Browser | Playwright (9) | The whole journey: example household → AQI → each person's advice → typed question → reload keeps the household → keyboard Tab path. Also the form fallback, server-side field errors focusing the right input, and the "no live data" alert with retry. |
| Static checks | ruff, mypy `--strict`, Biome, TypeScript, colour-contrast script | Run in CI on every push (`.github/workflows/ci.yml`) |

The browser tests use the backend's **real** responses as fixtures. A backend test regenerates them and fails if
they drift, so the frontend is always tested against the true API shape.

## Project layout

```
src/recyclops/
  api/       routes (plan, ask, cities, health), request/response schemas, errors, limits, security headers
  domain/    pure logic: aqi, forecast, rules, impact, home actions, factors (cited), cities
  data/      OpenAQ and Open-Meteo clients, live provider (cache + stale fallback)
  ai/        provider chain, explain, ask, templates, untrusted-input handling
  core/      settings, TTL cache, rate limiter
frontend/src/
  features/  setup (household form), plan (air panel, day plan), ask
  components/ shared UI (badges, decision card, form fields)
  lib/       API client and generated types, labels, formatting, storage
tests/       backend tests, golden scenarios, fixture sync
frontend/e2e/ Playwright tests and the recorded API fixtures
```

## Run it locally

You need Python 3.12 and Node 22. Keys are optional: without `OPENAQ_API_KEY` the app says live data isn't available,
and without AI keys it uses template wording.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
copy .env.example .env        # add OPENAQ_API_KEY (free at explore.openaq.org), GROQ_API_KEY, OPENAI_API_KEY
cd frontend; npm ci; npm run build; cd ..
.\venv\Scripts\python.exe -m uvicorn recyclops.api.main:app --port 8000
# open http://127.0.0.1:8000  (or, for frontend development: cd frontend; npm run dev)
```

Checks (what CI runs):

```powershell
.\venv\Scripts\python.exe scripts\check.py          # ruff, mypy, pytest
cd frontend; npm run lint; npm run typecheck; npm test; npm run contrast; npm run build; npm run test:e2e
```

## Deployment

- **Backend:** Render, using `render.yaml`. It runs `pip install .` and uvicorn with proxy headers, and checks
  `/api/health`. The keys are set in Render's dashboard.
- **Frontend:** Vercel, using `frontend/vercel.json`. It serves the static build with the same security headers and
  forwards `/api/*` to Render.

## Limits, stated plainly

- **The AQI uses PM2.5 and PM10 only,** labelled "NAQI method, PM-based". The official index needs at least three
  pollutants.
- **Hourly bands are indications, not official AQI values.** They use the 24-hour breakpoints, as stated on screen.
- **Purifier effect:** the −49% comes from a Taiwan apartment study, not a Delhi study, and is cited as such. Without
  a purifier, the app claims no indoor reduction.
- **Metro CO₂:** the metro factor uses the suburban-rail figure as a proxy.
- **Caches live in memory.** A restart loses the stale-reading fallback until the next good reading.

## Data and sources

- **Measured air quality:** CPCB and state pollution control boards' stations, via [OpenAQ](https://openaq.org).
- **Forecast:** [Open-Meteo Air Quality API](https://open-meteo.com) (CC BY 4.0), with data from the Copernicus
  Atmosphere Monitoring Service (CAMS).
- **Emission factors:** India GHG Program, road and rail transport (2015).
- **Breathing rates:** US EPA Exposure Factors Handbook, chapter 6, Table 6-2.
- **Purifier effectiveness:** Chen et al. 2022.

## License

MIT
