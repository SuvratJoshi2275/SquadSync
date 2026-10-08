# SquadSync — Analytics Foundation + Prototype UI (Phase 1)

Tactical Intelligence and Decision Support Platform for Football Analytics,
with an Integrated Football-Specific AI Assistant.

This is the **first-phase prototype**: a working analytics foundation over
a Barcelona-only StatsBomb-derived dataset, plus a Streamlit UI that shows
both what's functional today and the full intended product shape.

## Directory structure

```
squadsync/
├── app.py                     # Streamlit entry point — Fan/Coach mode switch,
│                                 nav, Roadmap page
├── requirements.txt
├── data/
│   ├── raw/<team>/*.csv       # source CSVs, never modified, never
│   │                            loaded fully at runtime
│   ├── processed/<team>/      # Parquet cache built by build_cache.py
│   ├── build_cache.py         # one-time ETL — UNCHANGED in this redesign
│   └── loader.py               # UNCHANGED in this redesign
├── analytics/
│   ├── team.py                # UNCHANGED
│   ├── player.py               # UNCHANGED
│   ├── tactical.py             # UNCHANGED
│   └── match.py                # small additive change — see below
├── ui/
│   ├── theme.py                 # NEW — design tokens, CSS, pitch figure builder
│   ├── components.py            # NEW — match cards, form strip, comparison bars,
│   │                               shot map, lineup pitch, passing network
│   ├── dashboard.py              # REDESIGNED — Fan Home + Coach Team Overview
│   ├── match_analysis.py         # REDESIGNED — Matches browser + Match Centre
│   ├── player_analysis.py        # REDESIGNED — Fan player page + Coach
│   │                               Player Intelligence
│   ├── tactical_analysis.py      # REDESIGNED — Coach tactical dashboard
│   ├── future_sections.py        # REDESIGNED — now a Roadmap page, not primary nav
│   └── placeholders.py           # REDESIGNED — compact roadmap card component
└── tests/
    ├── test_analytics.py       # UNCHANGED — still fully passes (see below)
    └── test_match_goals.py      # NEW — regression test for goal attribution
```

## Redesign summary (this pass)

This pass replaced the report-style dashboard with a two-mode football
product (**FAN MODE** / **COACH MODE**, switched from the top of the
sidebar) built around a proper design system and football-native visuals.

**Files changed:**
- `app.py` — rebuilt around the Fan/Coach mode switch and section
  navigation per mode; future modules moved off primary nav into a
  "Roadmap" page reachable via a sidebar button.
- `ui/dashboard.py`, `ui/match_analysis.py`, `ui/player_analysis.py`,
  `ui/tactical_analysis.py`, `ui/future_sections.py`, `ui/placeholders.py`
  — redesigned around football-product UI, not raw dataframes.
- `analytics/match.py` — one additive, backward-compatible change: added
  `match_goals()` and `match_substitutions()` (new functions; nothing
  existing was modified or removed) so the UI can render goal events and
  substitutions without reaching into raw event rows itself.

**Files new:**
- `ui/theme.py` — SquadSync design system: color tokens, compact CSS, and
  a reusable football-pitch figure builder (used by the shot map, lineup,
  and passing-network visuals so they look like a pitch, not a generic
  XY scatter chart).
- `ui/components.py` — match cards, form strip, comparison bars, shot map,
  lineup pitch, passing-network visualization. These are what translate
  analytics output into football language and enforce that no backend
  field (match_id, player_id, location_x/y, position_id, etc.) is ever
  rendered directly to the user.
- `tests/test_match_goals.py` — regression test for the new goal
  attribution logic (see "Bug found and fixed" below).

**Files intentionally left unchanged:**
`data/build_cache.py`, `data/loader.py`, `analytics/team.py`,
`analytics/player.py`, `analytics/tactical.py`, `tests/test_analytics.py`
— the working data pipeline and existing analytics were preserved exactly
as specified. CSV → Parquet → Loader → Analytics → UI is intact.

### What changed structurally

- **Fan Mode**: Home (identity, form strip, last match, recent match
  cards), Matches (filterable match browser as cards), Players (search →
  profile with real shot locations on a pitch), Match Centre (flagship
  page).
- **Coach Mode**: Team Overview (record, formation profile, form trend,
  competition breakdown), Tactical Analysis (formation shape, zone
  distributions, progression, pressing, in-match formation-change
  sequence), Player Intelligence (squad table + profile + compare),
  Match Analysis (same Match Centre as Fan Mode).
- **Match Centre**: football-style score header, goals listed directly
  under each team, tabs for Overview / Lineups / Stats / Tactics /
  Events. Shot map and lineup are drawn on an actual pitch outline
  (`ui/theme.base_pitch`), not a generic scatter plot. Passing network
  is a real node/edge graph (player = node at their average completed-
  pass location, edge thickness = pass volume) instead of a table.
  Raw event rows are only visible behind an explicit "Advanced data"
  expander in the Events tab.
- **Future modules** (Opponent Analysis, Squad Intelligence, Predictions,
  Recommendations, AI Assistant) moved out of primary navigation into a
  dedicated Roadmap page (sidebar button), each still describing its
  planned capabilities honestly as not-yet-built.
- **No backend fields exposed**: IDs, `location_x`/`location_y`,
  `position_id`, raw column names, etc. are consumed internally by
  `ui/components.py` and never rendered as-is; the one exception is the
  "Advanced data" expander in the Events tab, which is explicitly labeled
  and opt-in.

### Date bug (item 20) — investigated and fixed, not hidden

The team-trend chart's x-axis appeared to span back to ~1975. Root cause:
the dataset genuinely contains 4 archival matches from 1974–1984 mixed
into an otherwise 2004–2021 archive (verified directly against
`matches.csv` — not a parsing bug). Including them by default stretches
any date axis to a 47-year span and compresses the dense modern period.
Fix: the Coach Overview form trend defaults to the dense 2000+ era with
an explicit, visible checkbox — *"Include full historical archive (adds 4
matches from 1974–1984)"* — to opt into the complete history. The data is
never dropped or misrepresented, only the default view is scoped, and
the reason is stated on-screen.

### Bug found and fixed during this pass

While testing the new `match_goals()` against real own-goal matches
(rather than only the default match), an opponent-attribution bug
surfaced: own goals were attributed to a lookup of *any* Barcelona match
featuring that team name, which could resolve to the wrong opponent
entirely (e.g. a Sevilla match's own goal was briefly mislabeled "Real
Madrid"). Fixed by resolving the opponent directly from the selected
match's own row in `matches.csv` instead of an ambiguous cross-match
lookup, and added `tests/test_match_goals.py` to catch this class of
regression going forward.

### Known analytics/data limitation surfaced by this redesign

The dataset's event feed (`events.csv`, `shots.csv`, `passes.csv`, etc.)
is captured from **Barcelona's side only** — opponent shots and passes
are not present at all. This means:
- Opponent goals can only be individually attributed to a scorer when
  they came via an "Own Goal Against" event (a Barcelona player scoring
  into their own net). Opponent goals from normal open play have no
  event record in this dataset.
- `match_goals()` now returns an `opponent_goals_fully_attributed` flag,
  and the Match Centre shows an explicit caveat whenever the shown
  opponent goal list doesn't account for their full score — rather than
  silently presenting an incomplete list as complete. The scoreline
  itself (from `matches.csv`) is always shown and is always correct;
  only the opponent's scorer-by-scorer breakdown can be incomplete.
- Match Stats / Overview tabs are explicitly labeled as Barcelona-only
  detail for the same reason (no independent opponent-side stat line
  exists in the data to compare against).

## How to run

```bash
cd squadsync
pip install -r requirements.txt

# One-time: build the Parquet cache from the raw CSVs (only needed once,
# or after adding a new team's CSVs)
python data/build_cache.py --team barcelona

streamlit run app.py
```

## Test results

```bash
python tests/test_analytics.py      # unchanged suite — All checks passed.
python tests/test_match_goals.py    # new — All checks passed.
```

Both suites pass. `test_analytics.py` was not modified. The full app was
also driven through Streamlit's `AppTest` harness across every Fan/Coach
section, match-card click-through navigation, the Roadmap page, and
several own-goal matches — no uncaught exceptions.



## What's functional now

**Fan Mode:** Home (identity, form, last/recent match cards), Matches
(filterable browser: season/competition/result), Players (search →
profile with real career totals and shot locations on a pitch), Match
Centre (score header with per-team goal list, Overview/Lineups/Stats/
Tactics/Events tabs, shot map and passing network on a real pitch,
lineup on a schematic formation diagram).

**Coach Mode:** Team Overview (record, formation profile, form trend
with the archival-era toggle, competition breakdown), Tactical Analysis
(formation shape usage, shot zones, per-match passing/pressing zone
breakdown, progressive carries, formation-change sequence, player
involvement), Player Intelligence (sortable squad table, player profile,
2–4 player compare), Match Analysis (same Match Centre as Fan Mode).

Tactical Analysis deliberately does **not** generate qualitative
narratives ("dominated the left flank") — only numbers with a clear
metric behind them.

## What's a future-phase placeholder

Opponent Analysis, Squad Intelligence, Predictions, Recommendations, and
the AI Assistant no longer occupy primary navigation. They live on a
dedicated **Roadmap** page (sidebar button, below the mode switch), each
with an honest "not yet implemented" status and an expandable list of
planned capabilities — no fabricated predictions, scores, or AI
responses anywhere in the app.

## Known limitations of the current Barcelona-only dataset

- **Minutes played are estimated**, not authoritative: derived from
  lineup `from`/`to` timestamps, with players who finish a match assumed
  to play to the 90th minute. Matches that went to extra time are
  therefore understated for players who finished the match. Flagged in
  the UI, not silently corrected.
- **xG is only present on shot events** — no possession-value or
  expected-threat model exists yet for non-shot actions.
- **No tracking/360 data** — spatial analysis is limited to event
  locations (pass/carry/shot/pressure origins and, where recorded,
  carry end points), not full player positioning. This is why tactical
  claims are kept to measurable distributions rather than pitch-control
  or off-ball inference.
- **Single-team scope** — all analytics are Barcelona-relative; there is
  no true opponent-side dataset yet, which is why Opponent Analysis is a
  placeholder rather than partially built.
- **Formation data is the Starting XI shape plus recorded Tactical Shift
  events** — it does not capture fluid in-possession vs. out-of-possession
  shape changes.

## Architectural decisions to preserve going forward

- **Team-namespaced data layout** (`data/raw/<team>/`,
  `data/processed/<team>/`): adding Arsenal, Chelsea, etc. is "drop CSVs
  in a new folder, run `build_cache.py --team <name>`" — no analytics or
  UI code changes required. `app.py`'s team selector already reads
  whatever teams exist under `data/processed/`.
- **Never load full event-level tables into memory at runtime.**
  `events.csv`/`passes.csv`/`carries.csv`/`pressures.csv` are pre-
  partitioned by `match_id` at build time; `loader.py` intentionally
  raises if a caller tries to load them without a `match_id`, and
  cross-match player aggregates are pre-computed once in
  `player_pass_stats.parquet` / `player_carry_stats.parquet` instead of
  re-scanning raw events on every page load.
- **Analytics functions are UI-framework-agnostic** — nothing in
  `analytics/` imports Streamlit, so the same functions could back a
  FastAPI service (for the eventual live/WebSocket mode described in the
  project's data/ML architecture) without rewriting the logic.
- **The AI Assistant placeholder is scoped as an orchestration layer**,
  not a prediction engine — when it's built, it should call into
  `analytics/*` and explain the output, not duplicate the calculations.
