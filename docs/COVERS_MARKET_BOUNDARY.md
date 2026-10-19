# Covers current-market boundary

This adapter acquires football **point observations**, independently of model
logic and wager economics. It uses the committed team-identity and CFBD schedule
components. It contains no recovery alias table, Action Network adapter,
handicapping formula, probability, pricing, or bet construction.

## Three distinct readiness states

Readiness functions are evaluated from the record, not from previously exported
boolean flags. Reports/CSVs expose `manual_ready`, `production_ready`,
`audit_ready`, and `production_blockers` explicitly.

| State / function | Exact boundary |
| --- | --- |
| `manual_ready(record)` | No blocking `issues`; names resolved by the existing library to either provisional legacy aliases or supplied CFBD membership; distinct nonempty home/away names; finite DK and FD **home** spreads and a positive finite selected game total; offset-aware kickoff on `market_date` in America/New_York. Does not require official ID, verified schedule, capture timestamp, opener, or both opposing spread cells. |
| `production_ready(record)` | All manual requirements **plus** a verified association to a valid `ScheduleValidation` batch; preserved official ID including its int/string representation; exact canonical home/away roles and kickoff; explicit requested season/week matching the schedule; known offset-aware capture/retrieval time; complete consistent opposing spread sides for **both** books; selected total matching the named source book's measured total. No opening-line requirement. |
| `audit_ready(record)` | All production requirements **plus** a separately supplied verified movement-audit object with the same game ID, canonical home/away orientation, known opener definition, finite opening/current home spreads from the same source and same identified DK or FD book, and aware capture timestamps. Opening capture must not follow current capture; audit-current capture must not precede the initial market capture. |

Alias-target membership never supplies official schedule verification. An invalid
schedule batch, wrong scope, ambiguous matchup, reversed roles, kickoff/date
conflict, missing ID, or changed identity blocks production readiness. Rechecking
a record clears any previous schedule association/ID before matching again.
Unknown capture time also blocks production eligibility, without discarding the
observations or preventing controlled manual inspection.

`attach_schedule(records, validation, target_date, season=..., week=...)`
requires a `ScheduleValidation` from the committed schedule boundary, not an
unvalidated list of candidate games. A preserved copy of the matched normalized
schedule record is kept as `verified_schedule`. Use the foundation's actual
validation result; constructing an asserted-valid result from arbitrary input
is not a supported verification workflow.

**Market production readiness is not model readiness, FBS eligibility, complete
schedule coverage, or guaranteed quote freshness.** This adapter does not verify
CFBD/BCF feature availability or supply those features. Those gates remain in
their respective boundaries.

## Point observations and incomplete sides

- Dedicated spread and total tables remain mandatory; nested price spans are
  excluded. DK/FD book attribution and home-handicap signs are preserved:
  negative home favorite, positive home underdog, zero pick'em.
- `DK_Spread` / `FD_Spread` contain observed home points;
  `DK_Away_Spread` / `FD_Away_Spread` preserve observed away points.
  Missing values stay null. An away-only quote is **not** negated into a fabricated
  home observation, and missing books are never cloned from another book.
- If both spread sides parse, require equal/opposite values. A disagreement is a
  blocking issue; the existing behavior of rejecting the home spread is retained.
  Repeated book cells or ambiguous side/anchor cells are blocking issues.
- One-sided observations are retained with `<DK|FD>_incomplete_spread_sides`
  warnings and per-book `spread_side_status="incomplete"`. Home-only observations
  can pass manual readiness when all other manual inputs exist; incomplete sides
  conservatively block production readiness. Away-only observations remain in
  the all-record output but lack the required home input.
- `current_total` selects the actual measured DK total first, otherwise FD, with
  `total_source_book` explicit. It does not populate a missing `DK_Total` or
  `FD_Total`. Over/under consistency checks and existing conflict behavior remain.
  Only one selected game total is required for the current-market boundary;
  literal Colab column/type requirements remain a separate compatibility check.

## Opening lines are a separate observation role

Initial current spreads/totals can be valid production inputs with **no opener**.
The Covers displayed opener's definition/attribution remains unverified, so the
parser continues to leave `opening_home_spread` null and does not collect it as
an audited opener. This does not invalidate current-market production readiness.

Legacy **OLD CELL 43–44** movement/final-decision logic still needs real opener
and later-current observations. A boolean `production_ready` is not permission
to run that audit with missing data or assume zero movement.

`audit_ready` recognizes the following separately verified input shape; the
bridge currently has **no acquisition or verification adapter** for it:

```text
movement_audit:
  verified: true                 # established by a trusted audit input boundary
  game_id: <same official ID>
  away_team: <same canonical away>
  home_team: <same canonical home>
  opening:
    home_spread: <measured number>
    book: DraftKings | FanDuel
    source: <identified source>
    retrieved_at: <aware capture timestamp>
    definition: <verified opener convention>
  current:
    home_spread: <separate measured number>
    book: <same book>
    source: <same source>
    retrieved_at: <aware later capture timestamp>
```

These audit observations do not overwrite initial DK/FD spreads. Do not set
`verified=true` merely because a page displays a number. Normal CLI acquisitions
therefore report zero audit-ready records until a legitimate audit adapter is
provided. Fixture audit values in tests are synthetic and never production data.

## Truthful timestamp provenance

Live acquisition supplies its local HTTP request-start timestamp as
`retrieved_at`, with `capture_time_provenance="live_http_capture"`. It does not
claim a sportsbook update time. Raw per-book `data-date` values remain separate,
with explicitly unverified semantics.

For cached files, `load_cached_board` never substitutes filesystem time:

- Without a capture receipt, board/book/record `retrieved_at` is null and
  `capture_time_provenance="unknown"`. Records can be manual-ready, but cannot
  be production-ready because the capture time is unknown.
- `filesystem_mtime_utc` is retained only in board metadata and is labeled as
  filesystem metadata, not market capture provenance.
- An operator may explicitly supply trusted metadata using `--board-metadata`.
  The JSON must contain the exact board `url` and matching byte `sha256`.
  A supplied `retrieved_at` must have an explicit UTC offset; it is preserved.
  Missing/null time remains unknown. Invalid/mismatched receipts fail rather
  than falling back to filesystem time.

Receipt schema:

```json
{
  "url": "https://www.covers.com/sport/football/ncaaf/odds",
  "sha256": "<SHA-256 of the exact saved board bytes>",
  "retrieved_at": "<original offset-aware capture timestamp, or null>"
}
```

A matching hash binds the receipt to the file; it does **not** independently
authenticate its author's timestamp or prove quote age. Supply a real capture
receipt rather than generating a new timestamp when an old file is loaded.
No maximum quote-age or sportsbook timestamp interpretation is invented here.

## Explicit CLI scope and output semantics

Supply `--date`, `--season`, and `--week` explicitly. There is no inferred Week 7
or October 17 default. The current CFBD adapter supports regular season only;
season must equal the requested date's year, and week must be nonnegative. The
caller is responsible for selecting the correct provider week; actual schedule
scope/matchup/date validation must then pass.

With variables set to the explicitly verified slate context:

```bash
PYTHONPATH=src python -m cfb1.covers_bridge \
  --date "$SLATE_DATE" --season "$SEASON" --week "$CFBD_WEEK"
```

Optionally supply `--board-file /path/board.html` and its
`--board-metadata /path/capture.json`. A cached board avoids only the board
request: normal CLI execution still acquires CFBD schedule and Covers matchup
identity pages. Tests mock all these acquisitions. No live validation was
performed during this hardening task.

Summary/report fields distinguish:

- `manual_ready_records`, `production_ready_records`, `audit_ready_records`.
- `excluded_or_blocked_records`: all records failing production readiness,
  including incomplete data, unknown provenance, or unverified schedules.
- `blocking_conflict_records`: records carrying blocking `issues`; this is a
  subset of production exclusions, not a synonym for missing data/provenance.
- Requested date/season/week and coverage denominator generated from those
  inputs. Coverage describes **fetched Covers rows**, not full official slate
  completeness or model coverage.

**Exit 0:** a nonempty fetched slate and **every fetched record** production-ready.
**Exit 1:** validation incomplete, including an empty slate or even one excluded
record. **Exit 2:** invalid CLI arguments or cached capture receipt. Live transport
or source-schema failures also fail the command; they never imply success.
Manual-ready records or missing openers alone cannot determine production success.

The strict batch rule does not silently authorize partial-slate acceptance. A
caller can inspect the independently eligible subset and explicitly review
exclusions under the project's modest-coverage-loss policy. A successful command
still does not prove complete schedule coverage.

Exports preserve all observations and separate eligible subsets:

- `covers_<date>[_provisional].json`: complete records, states, schedule proof,
  book provenance, warnings, and blocking reasons.
- Matching `.csv`: all records, including excluded rows.
- Matching `_manual_ready.csv`: controlled inspection subset.
- Matching `_production_ready.csv`: verified current-market subset.
- Matching `_validation.json`: acquisition/summary metadata without records.

The misleading historical `_colab_ready.csv` export label is no longer generated.
Output creation remains exclusive; existing snapshots are not overwritten.
Earlier October 17 artifacts and their documentation remain unchanged historical
evidence, including the former schema/CLI behavior and recovery-only name fixes.

## Promotion scope and remaining decisions

The adapter is a candidate Covers current-market component, not a complete
market-data system. Before unattended live use, establish source reliability,
freshness/quote-age policy, and operational handling of exclusions. Opener
definition/acquisition and audit verification remain a separate task. Action
Network/source-priority orchestration and model extraction are outside this
implementation. None of these open questions authorizes fabricating observations
or treating old recovery data as current inputs.
