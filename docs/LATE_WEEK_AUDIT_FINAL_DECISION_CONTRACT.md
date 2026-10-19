# Late-week spread audit and final decision contract

## Authority, actual labels, and scope

Authority: `legacy/CFB1_Colab_Reference.ipynb`, SHA-256
`94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`,
`docs/NOTEBOOK_MAP.md`, `docs/BEHAVIOR_LOCK.md`,
`docs/ROUTING_KEYNUMBERS_CONTRACT.md`, and `docs/COVERS_MARKET_BOUNDARY.md`.
The actual embedded labels are **OLD CELL 43 — COVERS SPREAD MOVEMENT AUDIT**
and **OLD CELL 44 — FINAL DECISION BOARD**.

The new production modules are market_audit.py and final_decision.py. They are
static, deterministic functions; no notebook state or runtime notebook execution
is needed. No prior formulas, acquisition modules, aliases, or frozen notebook
bytes change. No October 17 recovery artifact is a production input. Scope ends
at OLD CELL 44; OLD CELL 45 exports, probability, pricing, push, expected ROI,
team-total models and final handoff remain unmigrated.

**Saved-checkpoint limitation:** the notebook's embedded OLD CELL 43 input is
explicitly labeled Source=SYNTHETIC_TEST and Data_Status=FICTIONAL. Its 14 rows
are a saved synthetic parity checkpoint, not a real historical market capture,
verified opener source, live backtest, or production feed. The exact paste is
stored only as an offline test fixture. Tests retain these labels visibly.

## Two distinct readiness contracts

1. **Current-market production readiness** stays exactly as committed in
   covers_bridge.production_ready: verified schedule/identity, required finite
   measured book points/total, and capture provenance. It requires no opener.
2. **Movement-audit readiness** additionally requires a separately sourced,
   explicitly verified opening/current pair. A displayed opening number or the
   adapter's provisional opening_home_spread is not that pair. Missing opener
   means audit unavailable; it never turns current points into invalid acquisition
   or implies zero movement/neutral confirmation.

The committed Covers bridge does not acquire validated openers. The new adapter
reuses its production_ready and audit_ready predicates, plus an explicit check
that the audited current home spread equals the selected current record's DK or
FD spread. No Covers HTML/parser logic is duplicated or modified.

The strict notebook functions still enforce full audit coverage. A separate
readiness adapter partitions usable and unavailable candidates BEFORE invoking
those functions. This is an integration policy, not a new legacy model rule.
Pending candidates receive Audit_Status=AUDIT_UNAVAILABLE in a separate table;
no new legacy Decision_Status is invented.

## OLD CELL 43: intake and strict audit

### Inputs and schema

`audit_spread_movement(covers_csv, review)` accepts supplied text and the migrated
Phase 1 review table. The review context used here is Game, Model_Side,
Review_Class. Its Game is the existing raw Away_Team + ' at ' + Home_Team key.

The source paste has these columns:

```text
Game,Away_Team,Home_Team,Open_Home_Spread,Current_Home_Spread,
Open_Total,Current_Total,Open_Home_Price,Current_Home_Price,
Open_Away_Price,Current_Away_Price,Source,Data_Status
```

Only Game, Away_Team, Home_Team, Open_Home_Spread and Current_Home_Spread are
needed by the calculations; other columns are retained if supplied. Totals and
prices are unused. Source/Data_Status are provenance annotations in the source,
not inputs to the model predicates. A direct legacy CSV call does not itself
authenticate provenance; use only independently established inputs in production.

Read pd.read_csv(StringIO(covers_csv.strip()), skipinitialspace=True). For every
object column, use astype(str).str.strip(). Coerce the two spread columns with
pd.to_numeric(errors='coerce'). Do not fill missing values or rename teams.
Required columns absent from the CSV raise during access, as in the source.

Both spreads are HOME-TEAM perspective: negative means home favored; positive
means home underdog. Opening is Open_Home_Spread; later current is
Current_Home_Spread. Never mix an away spread with a home spread, infer an
opener from current points, or use a different book's opener without verification.

### Intake validation and merge

Expected games are the unique set of review.Game. PASS requires:

- Input row count equals the number of unique expected games.
- Zero missing expected games and zero unexpected games.
- Zero duplicate Game rows using keep=False.
- Zero rows missing either numeric opening or current spread.

Failure raises before calculations. This is completeness of the SELECTED
movement-review set, not a requirement for 100% initial market-slate acquisition.
Then left-merge the review context onto supplied observations on Game with
validate='one_to_one'. Duplicate review keys fail cardinality. Raw model-side
labels are compared directly; strict legacy input assumes upstream identities
and orientation are already established.

### Movement and relationship

```text
Spread_Move = (Current_Home_Spread - Open_Home_Spread).round(2)
Movement_Toward = Home_Team if Spread_Move < 0
                  Away_Team if Spread_Move > 0
                  NONE otherwise
Market_Relationship = NEUTRAL if Movement_Toward == NONE
                      CONFIRMS_MODEL if Movement_Toward == Model_Side
                      CONFLICTS_WITH_MODEL otherwise
Movement_Size = abs(Spread_Move)
Movement_Class = NO_MOVE if size == 0
                 SMALL if size < 1
                 MODERATE if size < 2
                 MAJOR otherwise
```

Thus size exactly 1 is MODERATE, exactly 2 is MAJOR. Relationship has no minimum
movement-strength threshold. The rounded signed movement drives direction,
relationship and magnitude. No spread-size or EPA/FEI formula is recomputed here.

### Temporal key crossing

Exact signed list: `[-14,-10,-7,-3,3,7,10,14]`.
Use RAW numeric opening/current endpoints, not the rounded Spread_Move:

```text
low = min(opening, current)
high = max(opening, current)
crossed = abs(key) for each signed key with low < key < high
Key_Numbers_Crossed = comma-joined sorted unique crossed magnitudes
Key_Cross = (Key_Numbers_Crossed != '')
```

Crossing is strict and direction-independent. Touching, landing on, or leaving
an endpoint key does not cross that key. Zero is not a key. Crossing both -3
and +3 reports 3 once. Text uses commas without spaces, e.g. `3,7,10,14`.
A tiny raw movement straddling 3 can have Key_Cross=true while rounded movement
is zero and relationship is NEUTRAL; preserve that source distinction.

This is the temporal crossing missing from OLD CELL 36–42. It is implemented
here only from OLD CELL 43, not inferred from current book-to-book differences.
The existing spread_structure proximity/bucket functions remain unchanged;
they implement a different operation and are not misused as movement audits.

### Output and final audit gate

`covers_audit` retains all supplied columns plus Model_Side, Review_Class and,
in assignment order: Spread_Move, Movement_Toward, Market_Relationship,
Key_Numbers_Crossed, Key_Cross, Movement_Size, Movement_Class.

Final PASS requires row count equal to len(review) and zero missing rows among:
Model_Side, Review_Class, Spread_Move, Movement_Toward, Market_Relationship,
Movement_Size, Movement_Class. Failure raises. The legacy predicates test nulls,
not numeric finiteness, and do not certify timestamps or book attribution. The
production adapter adds the already-established readiness boundary before these
formulas; it does not change the formulas.

## Production opener/current adapter

`prepare_market_audit(review, market_keys, current_records, movement_audits)`
returns AuditBatch(audit, availability). Inputs:

- market_keys: Game, raw Away_Team/Home_Team, official game_id, canonical
  Away_CFBD_Name/Home_CFBD_Name from the upstream master. Every review game
  must have one complete mapping; duplicate raw keys or official IDs fail.
- current_records: committed Covers bridge records. Duplicate/missing records
  for an official ID are unavailable, not arbitrarily selected. Team orientation
  must match the canonical master mapping; no new alias lookup is performed.
- movement_audits: mapping from official game_id to the optional movement_audit
  shape already documented in COVERS_MARKET_BOUNDARY.md:

```text
verified: true
same official game_id and canonical away_team/home_team
opening: {home_spread, source, book, retrieved_at, definition}
current: {home_spread, source, book, retrieved_at}
```

The committed audit_ready requires finite points, same named source, same DK/FD
book, nonempty opening definition, offset-aware capture times, opening capture
<= current capture, and audit-current capture >= current-record capture. It
also requires current production readiness and matching official identity. The
new adapter additionally binds the audit current value to that book's measured
DK_Spread or FD_Spread. It carries source, book, official ID, definition, and
both capture times into the audited table. It does not impose a quote-age policy
or interpret raw provider data-date fields as quote timestamps.

`verified` is an explicit assertion from a trusted separately audited input
boundary, not proof the function can independently discover from the Internet.
The adapter does not fetch, fabricate or certify openers. Provenance verification
remains the caller's responsibility, consistent with the committed bridge.

The adapter builds the legacy five point/identity fields with the established
raw Phase 1 labels and invokes the strict source parser/formulas on the ready
subset. There is no duplicated Covers parser. Availability covers EVERY review
candidate with Game, Current_Market_Ready, Audit_Ready, Audit_Status, Audit_Reason.
Reasons distinguish missing/ambiguous current records, invalid current market,
canonical orientation mismatch, absent opener, unverified pair and current-point
mismatch. Original current records/flags are never modified.

## OLD CELL 44: strict final decision board

`build_final_decisions(review, routes, audit)` takes migrated review fields:
Game, Model_Side, Review_Class, Phase1_Reason. Left-merge routes first on Game,
validate='one_to_one', selecting M3_Support, M3_Conflict, Favorite_Spread_Size,
Spread_Status, Eligible_Market_Routes. Left-merge audit second, one-to-one,
selecting Open_Home_Spread, Current_Home_Spread, Movement_Toward,
Movement_Size, Movement_Class, Key_Numbers_Crossed, Key_Cross,
Market_Relationship. Missing required associations fail validation; no inner join
silently drops a candidate. Extra unique rows outside review are not independently
prohibited by this cell; strict OLD CELL 43 already establishes audit scope.

### Exact classification precedence

| Order | Condition | Decision_Status |
| --- | --- | --- |
| 1 | Review_Class=CONFLICT_REVIEW, confirms model | CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL |
| 2 | CONFLICT_REVIEW, conflicts with model | CONFLICT_REVIEW_MARKET_REJECTS_MODEL |
| 3 | Other CONFLICT_REVIEW | CONFLICT_REVIEW_UNRESOLVED |
| 4 | Ordinary market conflict and (Movement_Class=MAJOR OR Key_Cross) | STRONG_MARKET_CONFLICT |
| 5 | Other ordinary market conflict | MARKET_CONFLICT |
| 6 | NEUTRAL relationship | NEUTRAL_MARKET |
| 7 | Confirming relationship and Spread_Status in LARGE_SPREAD_CAUTION / DERIVATIVES_FIRST_20.5_PLUS | CONFIRMED_BUT_LARGE_SPREAD |
| 8 | Other confirmation | CONFIRMED |
| 9 | Otherwise | UNCLASSIFIED, rejected by validation |

Conflict-review handling precedes ordinary major/key conflict and large-spread
confirmation. Crossing escalates an ordinary CONFLICTING market; it does not
create conflict for a confirming/neutral market. Confirmation is not erased just
because a key was crossed. A large neutral market remains neutral.

The large-spread branch uses the upstream Spread_Status, not a fresh calculation
from late-current spread or Favorite_Spread_Size. Preserve routing overrides and
population; do not silently rebuild the model after market movement. The source
has no probability threshold, EV/ROI test, sizing rule, or final bet instruction.
Eligible_Market_Routes is carried forward unchanged as metadata.

Decision_Note is the exact source string for each status:

| Status | Note |
| --- | --- |
| CONFIRMED | Market movement supports the model side. |
| CONFIRMED_BUT_LARGE_SPREAD | Market supports the model side, but spread size requires derivative review. |
| NEUTRAL_MARKET | Market movement provides no additional confirmation or conflict. |
| MARKET_CONFLICT | Market movement is against the model side. |
| STRONG_MARKET_CONFLICT | Major and/or key-number movement is against the model side. |
| CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL | Module 3 conflicted with the model, but late market movement supports the model side. |
| CONFLICT_REVIEW_MARKET_REJECTS_MODEL | Module 3 conflicted with the model and the late market also moved against the model side. |
| CONFLICT_REVIEW_UNRESOLVED | Module 3 conflicts with the model and the market did not resolve the disagreement. |

Unknown status note falls back to Requires manual review., but UNCLASSIFIED
still fails the final gate. Output order is:

```text
Game, Model_Side, Review_Class, Phase1_Reason,
M3_Support, M3_Conflict, Favorite_Spread_Size, Spread_Status, Eligible_Market_Routes,
Open_Home_Spread, Current_Home_Spread, Movement_Toward, Movement_Size,
Movement_Class, Key_Numbers_Crossed, Key_Cross, Market_Relationship,
Decision_Status, Decision_Note
```

PASS requires len(result)==len(review), zero duplicate Game rows (keep=False),
zero UNCLASSIFIED rows, and zero missing rows across Game, Model_Side,
Review_Class, Phase1_Reason, Favorite_Spread_Size, Spread_Status,
Open_Home_Spread, Current_Home_Spread, Movement_Toward, Movement_Size,
Movement_Class, Market_Relationship, Decision_Status, Decision_Note. Failure
raises. M3 strings, routes, key strings and key boolean are not new separately
required fields in the source predicate; retain the actual predicate.

### Candidates without usable audit

`build_available_final_decisions(review, routes, AuditBatch)` first checks that
availability covers exactly the review set and audited rows match the ready set.
It runs unchanged OLD CELL 44 only on ready candidates. DecisionBatch contains:

- decisions: the legacy-schema classified subset (empty if no candidate is ready).
- pending_audit: all other candidates, retaining Phase 1 fields plus readiness
  and reason. These have no invented Decision_Status or neutral movement.

A missing opener invalidates neither current-market acquisition nor the Phase 1
candidate; it prevents movement-based final classification until evidence exists.
This partition is explicit. It does not falsely report full legacy audit PASS
for a partially covered original review slate. Strict functions continue to reject
incomplete inputs when called directly. Missing route evidence for a ready
candidate remains a hard failure, not an audit-unavailable fallback.

## Offline tests, saved checkpoint, and integration

New fixtures: late_week_notebook_synthetic.csv is the exact fictional paste;
late_week_notebook_checkpoint.json holds notebook hash, saved streams and saved
OLD CELL 43/44 displayed values. No real opener provenance is inferred from it.
Truncated Game labels expand only from unique raw-matchup prefixes. Other
truncated display strings compare by visible prefix; full string identity is
separately established by identical-input source parity. Numeric display
comparison uses 5e-7 absolute tolerance plus 1e-12 binary-float epsilon.

Saved **synthetic** checkpoint results, season 2026 through Week 5 / target Week 6:

| Measure | Saved | Replay |
| --- | ---: | ---: |
| Phase 1 / audit / final rows | 14 / 14 / 14 | 14 / 14 / 14 |
| CONFIRMS_MODEL / CONFLICTS_WITH_MODEL / NEUTRAL | 8 / 4 / 2 | 8 / 4 / 2 |
| Key-crossing games | 8 | 8 |
| CONFIRMED | 5 | 5 |
| CONFIRMED_BUT_LARGE_SPREAD | 3 | 3 |
| STRONG_MARKET_CONFLICT | 3 | 3 |
| NEUTRAL_MARKET | 2 | 2 |
| MARKET_CONFLICT | 1 | 1 |

All displayed numeric/classification/note-prefix comparisons pass. Examples:
Duke's conflicting crossing of -3 is strong conflict; Ohio State's conflicting
moderate move without crossing is ordinary market conflict; Notre Dame confirms
but retains large-spread review. All three CONFLICT_REVIEW outcomes are tested
synthetically because that class is absent from this saved checkpoint.

Identical-input parity runs only OLD CELL 43 and 44 using controlled fixtures
and the saved synthetic checkpoint. Only the hard-coded covers_csv assignment
is replaced; source formulas/merges/gates run unchanged. No notebook state is
used by the production code. Prior upstream UConn and Georgia Southern EPA-value
differences do not alter this saved audit/final classification replay; no rules
or input spreads were changed to compensate for drift.

A separate network-free integration test starts with raw CFBD play/advanced
fixtures, builds normalized feature/master tables, then calls committed EPA,
BCF/FEI, Module 3/convergence, routing/Phase 1, and the new audit/final components.
It tests both a separately verified pair and the missing-opener pending path.
No notebook execution or prior notebook globals are involved in this integration.
No probability, ROI, pricing, team-total calculation or export is invoked.

## Verification and promotion assessment

Run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests`.
All **370 tests** pass: 300 existing plus 70 new audit/decision/integration tests.
They cover both home-spread signs, all signed key crossings/reversals, endpoint
touches, rounding, no movement, malformed observations, precedence, nulls,
cardinality, trusted-pair identity/book/source/time checks, partial availability,
and exact-input notebook parity.

OLD CELL 43/44 logic is suitable for review as a production replacement at this
scope. Saved checkpoint evidence certifies synthetic functional parity, not live
market performance or actual opener availability. Live movement audits require
separately sourced/audited openers; current Covers acquisition alone still cannot
provide them. Missing audit evidence remains explicit and does not invalidate
current-market production readiness. No prior production module changed, and no
probability/ROI or later logic was migrated. Nothing is staged, committed or pushed.
