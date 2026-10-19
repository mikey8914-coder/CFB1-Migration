# Market favorites, Module 3, and corrected directional convergence

## Authority and scope

Authority: `legacy/CFB1_Colab_Reference.ipynb` (SHA-256
`94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`),
`docs/NOTEBOOK_MAP.md`, `docs/BEHAVIOR_LOCK.md`, and
`docs/EPA_BCF_FEI_CONTRACT.md`. Labels below are actual embedded labels, not
array positions or remembered numbering. The frozen notebook is unchanged.

| Embedded label | Extracted responsibility | Interface |
| --- | --- | --- |
| OLD CELL 23 | Model/market favorite agreement | module3.apply_market_favorites |
| OLD CELL 24 | Havoc Trap | module3.apply_havoc_trap |
| OLD CELL 25 | Defensive line-yards extraction and team-table refresh | Existing cfbd_features.normalize_advanced_stats derivation; module3.refresh_defensive_lineyards |
| OLD CELL 26 | Refresh defensive line yards into master | module3.refresh_master_lineyards |
| OLD CELL 27 | Line Yards Push | module3.apply_lineyards_push |
| OLD CELL 28 | Explosiveness Fraud | module3.apply_explosiveness_fraud |
| OLD CELL 30 | OAY/DAY Edge | module3.apply_oay_day_edge |
| OLD CELL 31 | Descriptive Module 3 board | module3.build_module3_board |
| OLD CELL 34 | Corrected directional convergence | convergence.corrected_convergence |

Scope stops BEFORE OLD CELL 36 routing. No route, spread-size, key-number,
probability, ROI, team-total, or handoff logic is implemented. In particular,
negative signals describe offensive matchup weakness, not a team-total betting
recommendation. No existing CFBD/BCF/EPA/FEI code, shared identity map, or Covers
acquisition was changed. No October 17 recovery artifact is an input or authority.

Functions are deterministic and return DataFrame copies. They preserve unrelated
master context and exact legacy names. No new thresholds, rounding, scaling,
filters, null fills, or inferred aliases are introduced. Missing source columns
raise rather than being created. Diagnostics and derived boards are separate
from the master feature table; none is a routing decision.

## Input stage and sign conventions

Input is `df_master_bcf` after CELL 12, CELL 13/14, OLD CELL 19/20/21, carrying
raw Away_Team/Home_Team labels, canonical Away_CFBD_Name/Home_CFBD_Name,
normalized CFBD features, home/away BCF metrics, EPA outputs, and per-book FEI
outputs. Reuse the committed acquisition and model modules; do not recreate
team identity or market parsing here.

- EPA_Edge_Team was derived in CELL 12: positive Net_EPA_Edge_Home chooses home,
  negative chooses away, zero `EVEN`; magnitude is absolute. EPA_Trigger is a
  separate >=0.12 flag and is **not** a convergence requirement.
- FEI_Model_Favorite comes from OLD CELL 20's rounded home-minus-away FEI ×30.
- DK_FEI_Edge_Team comes from OLD CELL 21's rounded DK home spread minus model
  home spread: positive chooses home, negative away, zero `EVEN`. It is a value
  direction, not necessarily the model favorite or market favorite.
- Corrected convergence uses DK FEI direction specifically. It does not use FD,
  FEI_Books_Agree, a consensus, or market-favorite agreement as another filter.

## OLD CELL 23: market-favorite agreement

Sources: DK_Spread, FD_Spread, raw Home_Team/Away_Team, FEI_Model_Favorite.
Each spread is already home-oriented. For each book, negative selects Home_Team,
positive selects Away_Team, zero selects `PICKEM`.

Exact new fields, assignment order:

```text
DK_Market_Favorite
FD_Market_Favorite
DK_FEI_Market_Agree = (FEI_Model_Favorite == DK_Market_Favorite)
FD_FEI_Market_Agree = (FEI_Model_Favorite == FD_Market_Favorite)
```

There is no favorite-size threshold. `EVEN` is not `PICKEM`, so an EVEN model
and pick'em market disagree. Agreement uses raw team-label equality. A home
model favorite can still have away-directed FEI-versus-market value.

PASS requires zero rows with null among the four new fields; otherwise raise.
The notebook gates outputs, not these source columns: a float NaN spread falls
through the comparisons to `PICKEM`, and an unmatched/null model favorite can
produce false agreement without failing this output-only gate. This behavior is
preserved, not advertised as input validation. The prior OLD CELL 20/21 stages
are responsible for their input/null gates. A selected null team label produces
a null market favorite and fails the OLD CELL 23 gate.

## OLD CELL 24: Havoc Trap

For each side S and its opposing side O:

```text
S_Havoc_Trap = (S_Off_PassingDown_SR <= 0.273)
               & (O_Def_Havoc_Rate >= 0.192)
```

Constants: PASSING_DOWN_SR_THRESHOLD=0.273, DEF_HAVOC_THRESHOLD=0.192. Both
comparisons are inclusive; both must hold. Outputs are Away_Havoc_Trap and
Home_Havoc_Trap. A flag is **negative for S's offense**, not for O's defense.
Either or both offenses may be flagged; there is no mutual exclusion.

PASS requires zero missing input rows across Away_Off_PassingDown_SR,
Home_Def_Havoc_Rate, Home_Off_PassingDown_SR, Away_Def_Havoc_Rate, and zero
missing output rows. Missing values are not valid no-trigger observations:
float-NaN comparisons may initially evaluate false, but the explicit input gate
raises. No values are filled or rounded.

`havoc_diagnostic`: Game, Offense_In_Trap, PassingDown_SR, Opp_Def_Havoc.
Rows are collected master order, away before home, then sorted by
Opp_Def_Havoc descending, PassingDown_SR ascending.

## OLD CELL 25: defensive line-yards source and team refresh

Source is the SAME bounded `adv_json` acquired with startWeek=1 and
endWeek=DATA_THROUGH_WEEK. For each row:

```text
team = team_row.get('team')
defense = team_row.get('defense') or {}
Def_LineYards = defense.get('lineYards')
```

This exact derivation already exists in committed
cfbd_features.normalize_advanced_stats and FeatureTables.df_def_lineyards. Reuse
that two-column normalized table (team, Def_LineYards); do not duplicate the
source parser or issue another full-season request. The new refresh helper
accepts this normalized table, not an alternative line-yards definition.

Drop prior Def_LineYards from df_cfbd, then left-merge on exact team with
validate='one_to_one'. All other CFBD columns survive. No team-name cleaning,
deduplication, or averaging occurs. Count source duplicates using keep=False.
PASS requires zero duplicated source team rows, zero source Def_LineYards nulls,
and zero post-merge nulls. Failure raises. One-to-one violations may raise
pandas MergeError before the printed validation gate, as in the notebook.
Missing source line yards is a failure even for a source row outside df_cfbd.

## OLD CELL 26: defensive line-yards master refresh

Create team/Def_LineYards home and away lookups from df_cfbd. Rename to
Home_CFBD_Name/Home_Def_LineYards and Away_CFBD_Name/Away_Def_LineYards. Drop
both prior master defensive columns to avoid suffixes, then left-merge home
first and away second, each with validate='many_to_one'. Preserve existing EPA,
BCF/FEI, Havoc Trap, market fields and any other enrichment.

PASS requires merged row count equal to **len(df_target_market)**, zero null
Home_Def_LineYards, zero null Away_Def_LineYards, zero duplicated
(Home_Team,Away_Team) rows with keep=False. The production helper requires
explicit expected_games from that target-market length rather than silently
using the already-filtered master length. Cardinality/validation failure raises.
Repeating a team across distinct games is allowed; repeating a source team or
exact game pair is not. No missing target team is discarded by an inner join.

## OLD CELL 27: Line Yards Push

For S's offense versus opposing O's defense:

```text
S_LineYards_Push = (S_Off_LineYards >= 3.5)
                   & (O_Def_LineYards >= 3.3)
```

Constants: OFF_LINE_YARDS_THRESHOLD=3.5, DEF_LINE_YARDS_THRESHOLD=3.3, both
inclusive. Each test alone is insufficient. Outputs Away_LineYards_Push and
Home_LineYards_Push are **positive offensive matchups** for their named side.
Both can be true.

PASS requires zero missing input rows across Away_Off_LineYards,
Home_Def_LineYards, Home_Off_LineYards, Away_Def_LineYards, and zero missing
output rows; otherwise raise. No imputation or threshold rounding.

`lineyards_diagnostic`: Game, Offense_With_Push, Off_LineYards,
Opp_Def_LineYards. Collect away then home within master order; sort both metrics
descending, preserving the notebook's pandas sort behavior.

## OLD CELL 28: Explosiveness Fraud

```text
S_Explosiveness_Fraud = (S_Off_Explosiveness >= 1.40)
                        & (S_Off_SuccessRate <= 0.42)
                        & (O_Def_SuccessRate <= 0.33)
```

Constants: EXPLOSIVENESS_THRESHOLD=1.40, OFF_SUCCESS_RATE_MAX=0.42,
DEF_SUCCESS_RATE_MAX=0.33. All three inclusive tests must hold. Outputs
Away_Explosiveness_Fraud and Home_Explosiveness_Fraud are **negative for the
named offense**. Do not reverse defense success-rate polarity.

PASS requires no null input rows across both offensive explosiveness values,
both offensive success rates, and both opposing defensive success rates, plus
no null outputs; failure raises. A missing value cannot be treated as a valid
false signal. No alternate explosiveness definition is introduced.

`fraud_diagnostic`: Game, Offense_Flagged, Explosiveness, Off_SuccessRate,
Opp_Def_SuccessRate. Collect away before home; sort Explosiveness descending,
Off_SuccessRate ascending.

## OLD CELL 30: OAY/DAY Edge

```text
S_OAY_DAY_Edge = (S_OAY >= 0.54125) & (O_DAY >= 0.56825)
```

Constants: OAY_HIGH_THRESHOLD=0.54125, DAY_WEAK_THRESHOLD=0.56825. Both
comparisons are inclusive. Outputs Away_OAY_DAY_Edge and Home_OAY_DAY_Edge
are **positive offensive matchups** for their named side. Both can be true;
there is no winner selection or additional FEI/EPA filter in this signal.

PASS requires zero missing rows across Away_OAY, Home_DAY, Home_OAY, Away_DAY
and zero null output rows; otherwise raise. The already-ingested BCF values are
used directly, without recalculating thresholds from this slate.

`oay_day_diagnostic`: Game, Offense_With_Edge, OAY, Opp_DAY. Collect away before
home; sort OAY and Opp_DAY descending.

## OLD CELL 31: descriptive Module 3 board

Build one df_module3_board row per master row, in master order. For each offense,
append active labels in this exact order:

1. Havoc_Trap → `HAVOC_TRAP_NEGATIVE`
2. LineYards_Push → `LINE_YARDS_POSITIVE`
3. Explosiveness_Fraud → `EXPLOSIVENESS_FRAUD_NEGATIVE`
4. OAY_DAY_Edge → `OAY_DAY_POSITIVE`

Exact output order:

```text
Game, Away_Team, Away_Signals, Away_Signal_Count,
Home_Team, Home_Signals, Home_Signal_Count, Total_Module3_Signals
```

Game is raw Away_Team + ' at ' + Home_Team. Signal text uses comma-space joins;
no signal means empty string and count zero. Total_Module3_Signals is the sum
of the two side counts, including both positive and negative signals; up to eight
are possible. Opposing flags are not canceled. `active_module3` is rows with
Total_Module3_Signals >0. Its display sorts count descending, Game ascending;
the full board remains in master order.

PASS: row count matches master, zero duplicate Game rows (keep=False), zero
nulls in Game/Away_Team/Home_Team/both side counts/total count, and zero errors
in total=away+home. Failure raises. Empty strings are valid. The source does
not independently validate all flag types/nulls here: it assumes validated signal
functions ran. Preserve source truthiness behavior rather than claiming a new
flag-schema gate. Empty inputs can fail during board-column access, as in the
notebook; no new empty-slate success rule was introduced.

This board is descriptive. Its counts are NOT the corrected convergence support
counts, and the board itself is not an input to OLD CELL 34.

## OLD CELL 34: corrected directional convergence

For each master row:

```text
epa_team = EPA_Edge_Team
fei_team = DK_FEI_Edge_Team
epa_fei_agree = (epa_team == fei_team and epa_team != 'EVEN')
shared_side = epa_team if epa_fei_agree else ''
```

Thus two EVEN labels do not agree. A directional conflict, or one EVEN label,
leaves Shared_Side empty. Agreement does not require EPA_Trigger, a minimum
magnitude, market-favorite agreement, or FD directional agreement.

Collect each side's positives in order LINE_YARDS then OAY_DAY, and negatives
in order HAVOC_TRAP then EXPLOSIVENESS_FRAUD. These are shortened directional
labels, distinct from the board's descriptive labels.

Relative to the shared side:

| Collection | First append | Then append |
| --- | --- | --- |
| M3_Support | Shared side's positive signals | Opponent's negative signals |
| M3_Conflict | Shared side's negative signals | Opponent's positive signals |

Each positive text item is `<raw team> +<SIGNAL>`; each negative item is
`<raw team> -<SIGNAL>`. Preserve list order, team labels, and comma-space joins.
For shared away, own=away/opponent=home; for shared home, reverse. Multiple
signals accumulate independently. Support and conflict can coexist; conflict
does not erase support or revoke EPA_FEI_Agree. No routing/downgrade/status is
assigned. Without an actual shared home/away side, both lists remain empty,
even if the descriptive Module 3 board has signals.

Exact output fields/order:

```text
Game
EPA_Team                 = EPA_Edge_Team
EPA_Value                = EPA_Edge_Value
FEI_Team                 = DK_FEI_Edge_Team
FEI_Value                = DK_FEI_Edge_Value
EPA_FEI_Agree
Shared_Side
M3_Support
M3_Conflict
M3_Support_Count          = len(support list)
M3_Conflict_Count         = len(conflict list)
```

Output is df_convergence_corrected, one row per master game in master order.
No `SUPPORTED`, `CONFLICT`, or `ROUTE` classification column is invented; the
legacy classifications are the agreement boolean, shared side, text, and counts.
`agreed` is rows with EPA_FEI_Agree. `m3_active` is agreed rows with support>0
OR conflict>0. The reported support/conflict game counts are independently
computed over agreed rows, so a game can count in both.

PASS: count equals master, zero duplicate Game rows, zero nulls in Game,
EPA_Team, EPA_Value, FEI_Team, FEI_Value, EPA_FEI_Agree, Shared_Side,
M3_Support_Count, M3_Conflict_Count, and zero agreed rows with empty Shared_Side.
Failure raises. Empty strings for nonagreement are valid. No extra null/type
validation on signal flags, side-membership check, or string fields is silently
added; validated upstream stages remain prerequisites.

## Offline fixtures and identical-input parity

New fixtures:

- `module3_controlled.json`: eight synthetic games with neutral, exact-boundary,
  single/multiple, directional conflict and EVEN cases. All four signals can be
  active for both sides in one game, testing support/conflict ordering.
- `module3_notebook_checkpoint.json`: frozen notebook hash, saved stream counts
  and displayed samples for the scoped cells, plus explicitly labeled replay
  inputs from the previous authenticated CFBD feature validation (2026 Weeks
  1–5, acquired October 19, 2026 at 18:49:34 UTC). The feature source-table hash
  is recorded. The 138 normalized team rows and 57 master rows are replay
  inputs, not a claim that original adv_json/raw play snapshots are available.

Historical BCF values reuse the already committed exact notebook manual-paste
fixture. There are no new network requests, recovery inputs, market parsers, or
identity maps. Tests do not depend on scratch files or live API access.

Pandas HTML tables embedded in the frozen notebook supply saved expectations.
Blank text remains empty string. Where saved Game strings are truncated with
an ellipsis, expansion uses a unique matching raw game-name prefix from the
full target-market display and the notebook's documented Game concatenation;
no ambiguous label is guessed. Displayed numerics use absolute tolerance 5e-7
plus 1e-12 floating-point epsilon, not invented full-precision baselines.

Parity executes only OLD CELL 23, 24, 25, 26, 27, 28, 30, 31, 34 with controlled
fixtures and stubbed display. Every intermediate DataFrame, defensive source/
refresh, signal diagnostic, board and corrected convergence matches. A second
full 57-game identical-input replay matches the same source cells. For literal
OLD CELL 25's historical replay, normalized defensive line-yard values are
re-expressed as team/defense.lineYards objects solely for formula comparison;
this is not an assertion that original raw adv_json was recovered.

Failure parity covers null inputs as well as positive results. Boundary tests
exercise every conjunction just outside and exactly at each inclusive threshold.
The historical checkpoint has no fraud or conflict positives, so synthetic cases
and literal-cell parity provide those validations instead of inventing historical
positive examples.

## Historical results: season 2026 through Week 5, target Week 6

| Check | Saved notebook | Replay |
| --- | ---: | ---: |
| Master / Module 3 / convergence rows | 57 / 57 / 57 | 57 / 57 / 57 |
| DK favorite agreement / disagreement | 46 / 11 | 46 / 11 |
| FD favorite agreement / disagreement | 46 / 11 | 46 / 11 |
| Away / home Havoc Trap | 2 / 1 | 2 / 1 |
| Away / home Line Yards Push | 1 / 1 | 1 / 1 |
| Away / home Explosiveness Fraud | 0 / 0 | 0 / 0 |
| Away / home OAY/DAY Edge | 4 / 3 | 4 / 3 |
| Active Module 3 games | 12 | 12 |
| Games with 2+ descriptive signals | 0 | 0 |
| EPA + DK FEI agreement games | 37 | 37 |
| Agreement games with M3 support | 10 | 10 |
| Agreement games with M3 conflict | 0 | 0 |

Available saved samples all match: 11 favorite-disagreement rows, 3 Havoc
trigger rows, 15 team line-yards rows, 10 master line-yards rows, 2 push rows,
7 OAY/DAY rows, all 12 active board rows, and all 10 displayed active convergence
rows. Fraud's zero count is explicit in saved output; no fraud table exists.
Refresh/null/cardinality checks pass. No mismatch was found against these
available saved values or counts.

Examples reproduce corrected direction: Stanford's negative Havoc Trap supports
Notre Dame; California's negative trap supports Virginia Tech; Rice's negative
trap supports East Carolina. Memphis +LINE_YARDS and Jacksonville State +OAY_DAY
support their own shared sides. Memphis's saved EPA magnitude is 0.053547,
below the EPA trigger threshold, yet it remains an agreement/support game.

The prior phase's James Madison–Georgia Southern upstream EPA-value discrepancy
is still an upstream-data limitation; its direction was unchanged. That game is
not among the displayed OLD CELL 34 active sample rows. Passing the saved rows
here does not certify unshown historical EPA values or resolve prior CFBD drift.
No formula or replay input was changed to force historical numeric agreement.

## Verification and promotion assessment

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests`
passes **251 tests**: 183 existing plus 68 new Module 3/convergence tests.

The scoped functions are suitable for review as production replacements for
market-favorite agreement, Module 3 signals/boards/refresh, and corrected
convergence. Exact-input parity and all available historical comparisons pass.
This does not certify unavailable original full-precision upstream data. Routing
and every later downstream decision remain unmigrated. Nothing is committed or
pushed as part of this implementation phase.
