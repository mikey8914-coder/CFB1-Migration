# Standard CFB1 final output and handoff contract

## Source and boundaries

Authority: `legacy/CFB1_Colab_Reference.ipynb`, SHA256
`94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`;
`NOTEBOOK_MAP.md`, `BEHAVIOR_LOCK.md`, and the committed migration contracts.
Actual embedded labels are:

| Label | Source objects → output | Standard behavior extracted |
| --- | --- | --- |
| OLD CELL 45 — GEM-READY FINAL EXPORT | df_final_decision → df_gem_export, gem_csv | Compact board, cleanup, status order, exact CSV |
| CELL 61 — COMPACT CFB1 HANDOFF | df_ev (CELL 57A) → spread_export, standard part of df_cfb1_gem_handoff / df_cfb1_gem_review | Canonical adjusted probabilities/ROI, supplied-price labels and independent pricing status |
| CELL 61B — CFB1 FULL CONTEXT CHECKPOINT | df_cfb1_gem_handoff → CFB1_FULL_CONTEXT_V1 | Copy all priced rows before selected-card compression |
| CELL 62 — CFB1 DECISION CARD V1 | df_ev → standard part of CFB1_DECISION_CARD_V1 | Positive-ROI spread PRIMARY / VALUE_ALT selection |
| CELL 66 — BUILD CFB1 FULL CONTEXT V2 | df_gem_export, df_phase1_shrinkage, df_key_value, CFB1_FULL_CONTEXT_V1, CFB1_DECISION_CARD_V1; optionally df_final_decision | Game-context enrichment, retained-line context, append unpriced Phase 1 games |
| CELL 67 — FINAL SYNCHRONIZED CFB1 HANDOFF | CFB1_FULL_CONTEXT_V2, CFB1_DECISION_CARD_V1, df_ev → CFB1_FULL_CONTEXT_FINAL, decision_card_text | Canonical spread-metric synchronization, Module 3 text cleanup |
| CELL 73 — BUILD CFB1 -> BET SLIP ARCHITECT HANDOFF | CFB1_DECISION_CARD_V1, CFB1_FULL_CONTEXT_FINAL → CFB1_ARCHITECT_HANDOFF | Standard column projection, aliases and football context |

CELL 61/62 also contain experimental team-total branches. Those branches are
**not migrated**, are not required even as empty inputs, and are isolated from
production imports. CELL 73C's restore-from-first-matching-CSV behavior and Colab
archive/download side effects are excluded. The standard model modules and all
previously migrated formulas remain unchanged. No October 17 recovery artifact
is an input or authority.

The current instruction and `PROBABILITY_ROI_CONTRACT.md` govern the ownership
boundary: CFB1 may report break-even and expected ROI for externally supplied
prices. Old notebook-map/behavior-lock prose describing those fields as Architect
only is superseded for this boundary. Price acquisition/selection, Kelly,
recommended stakes, bankroll allocation, promos, parlays and portfolio logic
remain outside CFB1. No such acquisition or allocation is implemented here.

## Exact legacy views

### OLD CELL 45

`compact_final_board(final_decisions)` reproduces these 17 columns, in order:

```
Game, Model_Side, Review_Class, Phase1_Reason, M3_Support, M3_Conflict,
Favorite_Spread_Size, Spread_Status, Open_Home_Spread, Current_Home_Spread,
Movement_Toward, Movement_Class, Key_Numbers_Crossed, Market_Relationship,
Decision_Status, Eligible_Market_Routes, Decision_Note
```

Select all final-decision rows, no ROI or route filter. Object columns fill null
with empty string, cast string and strip. Sort by status order below then Game;
reset index. Status grouping is **not a bet rank**:

1. CONFIRMED
2. CONFIRMED_BUT_LARGE_SPREAD
3. NEUTRAL_MARKET
4. CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL
5. CONFLICT_REVIEW_UNRESOLVED
6. MARKET_CONFLICT
7. STRONG_MARKET_CONFLICT
8. CONFLICT_REVIEW_MARKET_REJECTS_MODEL
9. UNCLASSIFIED

Unknown statuses sort at 99. PASS: row count equals final-decision count, no
repeated Game, no blank Decision_Status, no blank Model_Side; else ValueError.
The original check is not a new independent quality gate for model conclusions.
`gem_csv = board.to_csv(index=False)` is printed between
`----- BEGIN CFB1 FINAL BOARD CSV -----` and
`----- END CFB1 FINAL BOARD CSV -----`. The same DataFrame is displayed/exported.
No filename or JSON exists at this stage.

### CELL 61 / 61B

`priced_spread_handoff(valued)` projects the standard CELL 57A rows, all ROIs:

```
Game, Market_Family, Team, Direction, Bet_Label, Sportsbook, Line,
American_Odds, Model_Adjustment, Model_Probability, Push_Probability,
Break_Even_Prob, Expected_ROI_Final, Decision_Status, Pricing_Status, Warning
```

Market_Family=FULL_GAME_SPREAD, Direction=SPREAD, Bet_Label is `Team + ' ' +
str(Line)`. Model_Adjustment=Candidate_Cushion; Model_Probability=
Push_Adjusted_Win_Prob; Push_Probability=Push_Adjusted_Push_Prob;
Expected_ROI_Final=Push_Adjusted_ROI; Warning=Decision_Warning filled empty.
Break_Even_Prob and exact supplied odds are carried through. No recalculation.

Pricing_Status: NaN ROI→NO_QUANTITATIVE_PRICE; >=.05→STRONG_PRICE_EDGE;
>=.02→POSITIVE_EV; >0→THIN_POSITIVE_EV; otherwise NON_POSITIVE_EV.
The .02 threshold deliberately differs from CELL 57's .03 EV_Status threshold.
Sort by Game, Market_Family, ROI descending, NaNs last. The legacy review display
filters quantitative ROI>0; production `.priced` preserves **all** supplied rows.
The source's display scales percent copies, not stored values. Required adjusted
columns must exist, Game must be nonnull, no staking fields in projected output.
CELL 61B copies this complete table before compression and creates no-index CSV
text; `.priced` is that standard-only uncompressed view. No archive is written.

### CELL 62

`spread_decision_card(valued)` requires canonical adjusted rows and
Market_Model_Spread. Filter Push_Adjusted_ROI>0, group (Game,Team). PRIMARY is
nearest abs(Line-Market_Model_Spread), ties by American_Odds descending. From
remaining rows select maximum adjusted ROI as VALUE_ALT. No other rows are
selected. Preserve input order for otherwise unresolved legacy ties. Sort card
by Game, Market_Family, Card_Role. No stake is selected.

Exact columns:

```
Game, Market_Family, Card_Role, Team, Direction, Bet_Label, Sportsbook,
Line, American_Odds, Model_Adjustment, Model_Probability, Push_Probability,
Break_Even, Expected_ROI, Decision_Status, Model_Status, Warning_Final
```

Model_Status=FULL_GAME_SPREAD_V1; Break_Even aliases Break_Even_Prob;
Expected_ROI aliases adjusted ROI; Warning_Final aliases Decision_Warning.
No positive rows produces a typed-by-schema empty card rather than the mixed
notebook's empty-branch column-selection exception. This is an output adapter
extension, not a new eligibility rule.

### CELL 66 / 67 / 73

The notebook's full-context archive is dynamically wide: it selects available
Phase 1 columns (team/kickoff, book spread/total, EPA features, BCF metrics,
Module 3 booleans, structure and retained-line diagnostics), then available key
value columns. It joins these onto the 17-column compact decision context,
adds optional Movement_Size/Key_Cross, marks Decision_Card_Included and
Context_Usage (CURRENT_DECISION_CARD_GAME or BACKGROUND_PHASE1_ONLY), then
many-to-one joins pricing. Unpriced games are appended as
NO_CURRENT_PRICING_ROW / BACKGROUND_CONTEXT_ONLY. Aliases include Phase_1_Reason,
Module_3_Support_Conflict and Late_Market_Movement. It writes
`cfb1_full_context_v2.csv`, index=False. These diagnostics are already available
from prior migrated stages; the new fixed weekly schema projects the standard
handoff facts rather than reproducing an arbitrary-width archive of every
intermediate feature. This is explicit interface normalization, not full-width
CSV byte parity.

CELL 67 replaces spread adjustment, win, push, break-even, ROI and nonempty
warning from canonical df_ev using (Game,Team,Sportsbook,Line,American_Odds).
Duplicate quote identities fail. It compares card/context adjustment, win, push,
break-even and ROI with np.isclose(equal_nan=True), default tolerances. All must
match. New assembly additionally checks membership so missing joins cannot pass
solely as two matching NaNs. No quote is joined by Game alone.

Module 3 cleanup: support plus ` | CONFLICT: ` plus conflict if both; support if
only support; `CONFLICT: ...` if only conflict; NONE if neither. Empty temporal
key-cross strings become NONE in the selected legacy card context. They remain
empty in the canonical weekly board when that was the source fact. Unavailable
movement is null, never NONE/NEUTRAL. CELL 67's filename is
`cfb1_full_context_final.csv` with no index; its legacy card copy/paste text
formats percentages to one decimal and adjustment to two decimals. New text
exports the same unrounded canonical CSV as machine output, avoiding a separate
formatted table being mistaken for full-precision model facts.

`architect_card(card, final_context)` reproduces CELL 73's column projection and
aliases Break_Even→Break_Even_Prob, Warning_Final→Warning,
Phase_1_Reason→Phase1_Reason, Module_3_Support_Conflict→Module3_Support_Conflict.
The source includes optional context columns only when present; required fields
are Game, Market_Family, Card_Role, Team, Direction, Bet_Label, Sportsbook, Line,
American_Odds, Model_Probability, Push_Probability, Break_Even_Prob, Expected_ROI,
Model_Status, Decision_Status, Warning, Eligible_Market_Routes. Source hard stops
also prohibit staking columns and quantitative values on qualitative TT rows;
there are no TT rows in this extraction. Original filename:
`cfb1_architect_handoff.csv`, no index. The production `.card` uses this standard
projection. A card's ROI selection does not define complete weekly membership.

## Complete weekly output: deliberate availability/optional-price extension

`assemble_handoff(decisions, *, routes=None, retained=None, key_value=None,
probabilities=None, valued=None, availability=None, market_unavailable=None)`
accepts DataFrames or migrated DecisionBatch (classified + pending audit).
Inputs come from migrated modules. No notebook globals or source execution.
It returns HandoffTables(weekly, priced, card).

- `.weekly` retains every classified/pending Phase 1 candidate regardless of
  supplied price, route label or ROI, plus explicit schedule market exclusions.
- `.priced` is CELL 61's standard uncompressed supplied-price table.
- `.card` is CELL 62/73's legacy-selected positive-ROI standard spread card.
  It may be empty; this never deletes a weekly candidate.

Routes/retained/key context may contain a superset of games; joins are by unique
Game. Existing nonnull final context wins; missing fields may be filled from
context. Extra probability/price games fail rather than being silently dropped.
No new classifications are calculated. Retained_Model_Spread and line-value
fields come from CELL 48, not inferred from a spread or win probability.

For unpriced games, Line=Market_Model_Spread and Model_Adjustment=
Model_Cushion_Points. Price-free probabilities are optional outputs of migrated
candidate_probabilities and optionally adjust_push_probabilities. They **must**
match the exact Game/Team/Line; no reassignment to another handicap. Prefer the
complete adjusted W/P/L triplet if present, else complete base triplet. Never
combine CELL 52's minimum win with a different push/loss sample. Missing
probabilities stay null, never 0 or 50%.

For priced games, keep every canonical supplied CELL 57A quote row, not just
positive ROI. Use the five-part quote identity. Side and Decision_Status must
match canonical context; missing pending status matches only another missing
status. Carry adjusted W/P/L, break-even, ROI, warning and base EV_Status exactly;
no formulas change. No odds → no Sportsbook, American_Odds, Break_Even_Prob,
Expected_ROI or EV_Status; Pricing_Status=NO_QUANTITATIVE_PRICE. No price is
fetched. A probability is not a supplied sportsbook price.

Readiness is separate from Decision_Status:

- Current_Market_Ready=True → Market_Status=CURRENT_MARKET_READY.
- False → MARKET_DATA_UNAVAILABLE; erase unusable current spread, offered line,
  adjustment and W/P/L. Preserve known model context, exclusion identity/reason.
- Audit_Ready=False → Audit_Status=AUDIT_UNAVAILABLE; opener, movement and
  relationship fields are null. Never invent NEUTRAL, NO_MOVE, an opener, or a
  final football classification for a pending row.
- Classified strict OLD CELL 44 inputs prove their required current/audit
  availability unless explicit availability overrides it. Their supplied decision
  classification is always preserved; an override is separately visible.
- Pending DecisionBatch rows require explicit boolean readiness, as produced by
  the existing audit adapter. Movement audit cannot be ready without current
  market. A supplied valuation cannot attach to an unavailable current market.
- `market_unavailable` accepts explicit schedule exclusions, e.g. a verified game
  absent from Covers. It does not infer missing official games. Exclusions must
  have unique, disjoint Game keys. No Model_Side is fabricated for an exclusion.

Warnings are carried from canonical supplied valuation; football notes,
Module 3 support/conflict, and availability/reasons remain separate columns.
No-price rows retain their Decision_Note and evidence even without a valuation
warning. MODEL_REVIEW is an explicit weekly-only Card_Role, not a PRIMARY bet
recommendation. Selected legacy roles live in `.card` separately.

## Fixed weekly schema and order

This is a deliberate 50-column weekly interface. The first 30 columns are
CELL 73's desired standard schema; the last 20 are
explicit model/probability/availability extensions. All columns always exist.

```
Game
Model_Side
Market_Family
Card_Role
Team
Direction
Bet_Label
Sportsbook
Line
American_Odds
Model_Adjustment
Model_Probability
Push_Probability
Break_Even_Prob
Expected_ROI
Model_Status
Decision_Status
Warning
Phase1_Reason
Module3_Support_Conflict
Spread_Status
Market_Relationship
Open_Home_Spread
Current_Home_Spread
Movement_Size
Movement_Toward
Movement_Class
Key_Numbers_Crossed
Eligible_Market_Routes
Decision_Note
Home_Team
Away_Team
game_id
Review_Class
M3_Support
M3_Conflict
Favorite_Spread_Size
Market_Model_Spread
Retained_Model_Spread
Model_Cushion_Points
Line_Value_Status
Loss_Probability
Probability_Source
Pricing_Status
EV_Status
Current_Market_Ready
Market_Status
Audit_Ready
Audit_Status
Audit_Reason
```

Football/model facts: identity, model side, retained line/cushion, evidence,
routing metadata, final decision, current spread and independently verified
movement, line-specific W/P/L/source. Optional supplied-valuation facts:
Sportsbook, American_Odds, Break_Even_Prob, Expected_ROI, Pricing_Status, EV_Status
and price/key-tradeoff Warning. Line/Model_Adjustment/W/P/L refer to the current
model-side line on unpriced rows and the exact offered line on priced rows.
Retained_Model_Spread remains the same canonical football line.

Sort by legacy decision status group, Game ascending, Team ascending, Line
descending, Sportsbook ascending, American_Odds descending, stable, nulls last.
All weekly Card_Role values are MODEL_REVIEW; no football candidate is promoted
or excluded by economics. Core identifiers/notes fill missing text with empty
string and strip; numeric missing values remain null. Missing movement remains
null even in text exports. Unknown/missing statuses sort at 99, not a new rank.
Legacy route **strings** may mention derivative/team-total review; they remain
unchanged metadata. No TT model fields or TT market rows are exported.

Validation: source compact gate for classified rows; unique/nonnull context Game
keys and quote identities; exact optional-probability line identity; boolean
readiness; no orphan valuation/probabilities; complete finite-range W/P/L in
[0,1] with sum np.isclose(1,atol=1e-9), default rtol; every base Game retained;
all card members join uniquely to weekly rows and all five canonical metrics
match. Fixed schema prevents unknown TT/Kelly/stake/bankroll columns leaking.
This adds output integrity checks, not new model formulas or eligibility gates.

## Serialization and naming

`serialize_handoff(handoff_or_weekly, slate_date)` is deterministic and has no I/O.
`export_handoff(..., directory)` explicitly writes CSV/JSON/TXT, returning paths.
An explicit date or ISO YYYY-MM-DD is required, no host-clock slate inference.
Title `MM-DD CFB — CFB1`; safe basename `MM-DD_CFB_CFB1`; examples for any date
are generated by strftime, not hard-coded October names. Files are UTF-8,
CSV has no index; JSON envelope contains schema_version=CFB1_STANDARD_HANDOFF_V1,
slate_date (including year), title, ordered columns, rows. Stored probabilities
are fractions, not percentages. JSON missing values are null and no NaN/Infinity
tokens are emitted; precision is pandas' 15-decimal JSON precision. CSV missing
values are blank. TXT wraps the **same exact CSV** in the legacy begin/end
markers beneath the daily title. Display/CSV/JSON membership is one canonical
weekly table; no second ROI-filtered export is silently substituted.

Writers create the caller's directory and overwrite the same day's filenames;
callers should separate runs/seasons by directory when retaining history. No
Colab download, archive restoration, upload or push occurs. Fixed schema/order,
nonblank Game and no infinite numeric values are enforced before serialization.

## Validation evidence and remaining operating dependencies

Tests execute the frozen OLD CELL 45 and standard spread branches of CELL
61/61B/62/73 with identical inputs. TT sections in 61/62 are structurally
excluded in the test harness, not ported to production. CELL 66/67 are also
executed without file/download side effects and their standard context,
retained-line and synchronized card projection is compared. Identical-input
parity passes for the standard handoff path. This proves the
standard projection, not equality of every dynamic full-context archive column.

Saved output checks:

- The complete saved OLD CELL 45 CSV matches byte-for-byte for all 14 rows.
- All visible standard CELL 61 positive-ROI review rows match saved supplied
  CELL 57A values and pricing classifications at saved display precision.
- Standard CELL 62 saved membership, PRIMARY/VALUE_ALT roles and bet labels match.
- Saved CELL 73 displays omit middle columns, so no invented full CSV parity is
  claimed; identical-input source projection verifies those fields instead.
- Checkpoint fixture records the frozen source hash. Earlier late-week market
  inputs are SYNTHETIC_TEST/FICTIONAL; archived sportsbook price provenance is
  unverified. Logic parity is not authenticated real-market validation.

The end-to-end offline test imports only production modules and supplies raw
CFBD play/advanced fixtures → feature table/master → EPA/BCF/FEI → Module 3 /
convergence → routing/Phase 1 → synthetic verified audit → final decisions →
retained line/probability → supplied-price ROI for one game → weekly handoff /
CSV/JSON/TXT. It exports **two games**, one priced and one unpriced, both with
probabilities. Socket creation is forbidden during this test. No notebook
execution or globals are used in the integration path.

Live dry run: **blocked before acquisition**. The repository contains only BCF
test/checkpoint CSVs, no production-ready weekly seven-column BCF input with a
current completed-data boundary. These are not substituted for current BCF.
No CFBD/Covers network requests are made for this task; partial acquisition
would not validate a complete current model output. Once current BCF is supplied,
other explicit inputs remain authenticated CFBD data through the configured
completed week, verified Covers current markets, and provenance-qualified
historical calibration payloads if empirical probabilities are requested. The
original 3,730-row historical dataset remains unavailable; do not manufacture it.
Supplied exact external prices are needed only for optional valuation.
Verified openers are needed only for movement-audit readiness, not current-market
readiness or standard output. Missing games can be explicit exclusions rather
than forcing 100% market coverage.

Full regression: `PYTHONPATH=src python -m unittest discover -s tests` passes
**467 tests**, including **37 new handoff/export tests**. Existing pandas
deprecation warnings remain in frozen/previously extracted operations; no test
fails. Production assembly does not execute the notebook.

The standard non-team-total path is functionally complete as composable migrated
production functions, demonstrated offline. This is not a claim of a successful
live current-week run or an automatic weekly operator/BCF feed. Experimental
team totals remain unmigrated and isolated; live price acquisition, Odds API,
Kelly/staking, bankroll/promos/parlays/portfolio remain outside the implementation.
The remaining live operational blocker is production-ready current-week BCF input.
