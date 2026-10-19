# EPA trigger, BCF input, and FEI directional contract

## Authority, labels, and extraction boundary

Reference: `legacy/CFB1_Colab_Reference.ipynb`, SHA-256
`94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`,
with `docs/NOTEBOOK_MAP.md`, `docs/BEHAVIOR_LOCK.md`, and
`docs/CFBD_FEATURE_CONTRACT.md`. The notebook is read, never edited.

The original embedded labels in this frozen version are:

| Requested responsibility | Actual embedded label | Production function |
| --- | --- | --- |
| EPA trigger | CELL 12 | model_signals.apply_epa_trigger |
| BCF manual ingestion | CELL 13 | bcf.parse_bcf_csv |
| BCF normalization | CELL 14 | bcf.normalize_bcf |
| BCF master merge | OLD CELL 19 | bcf.merge_bcf |
| FEI differential/polarity | OLD CELL 20 | model_signals.apply_fei_model |
| FEI versus market direction | OLD CELL 21 | model_signals.apply_fei_market_edges |

Use these actual embedded labels throughout the ingestion, normalization, and
merge sequence; do not renumber the frozen cells. Scope stops at OLD
CELL 21: OLD CELL 23 market-favorite comparison and all later Module 3,
convergence, routing, key-number, probability, ROI, and handoff logic are absent.
No Covers acquisition, CFBD feature acquisition, alias-map changes, or October
17 recovery input is part of this extraction.

All functions are deterministic, return DataFrame copies, retain legacy field
names, and preserve unrelated input context. There is no orchestration, automatic
network access, threshold tuning, or rounding refactor. The existing pandas
dependency and shared BCF identity mapping are reused without modification.

## CELL 12: net EPA trigger

Input object: `df_master`. Required computational columns are
`Net_EPA_Edge_Home`, `Home_Team`, `Away_Team`. The signed edge was already
created by CELL 11 as Home_Net_EPA_Margin - Away_Net_EPA_Margin; this segment
does not rebuild CFBD features or redefine that upstream input.

| Exact output | Exact rule |
| --- | --- |
| EPA_Edge_Value | abs(Net_EPA_Edge_Home) |
| EPA_Edge_Team | Home_Team if signed edge >0; Away_Team if <0; otherwise `EVEN` |
| EPA_Trigger | EPA_Edge_Value >= EPA_TRIGGER_THRESHOLD, with EPA_TRIGGER_THRESHOLD=0.12 |

The threshold is inclusive for both +0.12 and -0.12. There is no rounding before
comparison and no minimum edge for assigning a side. A positive 0.119999999
chooses home but does not trigger; -0.119999999 chooses away but does not
trigger. Zero has value 0, label `EVEN`, trigger false. Raw market team labels
are used as output labels, not canonical identifiers. There is no additional
`NO_TRIGGER` classification field.

`trigger_count = int(EPA_Trigger.sum())`; `below_count = len(df_master) -
trigger_count`. PASS requires zero null EPA_Edge_Value, zero null
EPA_Edge_Team, and trigger_count+below_count==len(df_master). Failure raises.
For float NaN signed input, the notebook's comparisons fall through to `EVEN`
and the trigger comparison is false, but the missing magnitude causes STOP;
the extracted function likewise never returns that row as valid. A missing
selected team label causes the missing-team output gate to fail. Missing input
columns are rejected explicitly. Nullable objects whose comparisons are
undefined may raise during calculation, as in the notebook; no nulls are filled
or converted to artificial zero edges.

## CELL 13: manual BCF ingestion

Input: manually supplied `bcf_csv` text, not a BCF web scraper. The historical
paste represents data through Week 5 for target Week 6, season 2026. The CSV
contains no season/week columns; the caller must associate it with the correct
run boundary. This segment does not infer or certify data vintage from the text.

Exact required case-sensitive schema:

```text
Team,FEI,OFEI,DFEI,SFEI,OAY,DAY
```

`bcf_text = bcf_csv.strip()`. Empty text and the exact placeholder
`PASTE THE GEM CSV HERE` raise. Parse using `pd.read_csv(StringIO(bcf_text))`
with pandas defaults. Required columns must exist; extra columns are retained.
The source does not require a particular column order or exactly seven columns.

Validation/normalization order matters:

1. Detect missing required columns.
2. Detect duplicate raw Team rows with duplicated(subset=['Team'],keep=False),
   **before** whitespace cleanup. Count all members, do not deduplicate.
3. If schema is complete, use pd.to_numeric(errors='coerce') on each of FEI,
   OFEI, DFEI, SFEI, OAY, DAY. Count converted nulls in every metric, including
   blanks and malformed values. Store converted values back into df_bcf_raw.
4. Set Team = Team.astype(str).str.strip(). Preserve BCF naming and internal
   whitespace. Do not apply market aliases or collapse whitespace here.

Output: `df_bcf_raw`, Team strings and six pandas numeric columns (integer or
floating dtype determined by values; do not force a new numeric precision).
Metric nulls are forbidden by the conversion gate. The source does not add
range, finite-number, total-FEI decomposition, or plausibility tests. A single
missing Team can stringify to `nan` and pass the raw gate, then fails membership
at CELL 14 with a real feature universe. Two names differing only in leading or
trailing whitespace may pass the raw duplicate check, then fail canonical
uniqueness in CELL 14. Preserve both stages rather than silently correcting rows.

PASS: nonempty df_bcf_raw, zero missing columns, zero pre-strip duplicate team
rows, zero total numeric conversion/null problems. Failure raises. Production
BCFValidationError subclasses ValueError and includes structured diagnostics;
malformed CSV parsing may raise pandas parsing errors directly. No invalid row
is dropped, averaged, or imputed to make a gate pass.

## CELL 14: BCF normalization and coverage

Input: `df_bcf_raw`, `cfbd_teams`, and `df_target_market` canonical home/away
keys. The CFBD universe is the stripped nonnull team-name set from the feature
table, not merely a team registry, alias-value list, or subset playing this week.
Callers supply those names to the existing TeamIdentityResolver. The parser
already cleaned Team; this stage does not strip/collapse it again.

Create `df_bcf = df_bcf_raw.copy()` and `CFBD_Team` through the existing shared
BCF map, with unchanged-name fallback:

| BCF Team | CFBD_Team |
| --- | --- |
| Appalachian State | App State |
| Connecticut | UConn |
| Hawaii | Hawai'i |
| San Jose State | San José State |
| Southern Mississippi | Southern Miss |

Keep Team unchanged alongside CFBD_Team. The production helper uses the existing
normalize_bcf_team_name, not the separate market-name alias system.

Reject ALL BCF rows whose canonical name is not in cfbd_teams, including
non-slate rows. Target teams are the union of Home_CFBD_Name and Away_CFBD_Name;
each must appear in CFBD_Team. Canonical duplicates are detected with
keep=False, including two different raw names that map to the same identity.
PASS requires zero unmatched rows, zero duplicate canonical rows, and zero
missing target teams. Failure raises; the exception exposes each diagnostic.
No alias is inferred or added automatically.

## OLD CELL 19: BCF into master

Inputs: df_master, df_bcf. Select CFBD_Team and all six metrics from BCF for each
side. Home rename: CFBD_Team→Home_CFBD_Name and every metric→Home_<metric>.
Away rename uses Away_CFBD_Name / Away_<metric>. These are the exact outputs:

```text
Home_FEI, Home_OFEI, Home_DFEI, Home_SFEI, Home_OAY, Home_DAY
Away_FEI, Away_OFEI, Away_DFEI, Away_SFEI, Away_OAY, Away_DAY
```

Left merge home first on Home_CFBD_Name, then away on Away_CFBD_Name, each with
validate='many_to_one'. Output: df_master_bcf, retaining master rows, EPA outputs,
market values and unrelated context. Repeated teams across distinct games are
allowed; duplicated BCF canonical keys are not. Merge cardinality failure raises
pandas MergeError. Do not convert these to inner joins that hide missing games.

PASS: merged count equals len(df_master), zero missing Home_FEI, zero missing
Away_FEI, and zero duplicated (Home_Team,Away_Team) rows using keep=False.
Failure raises. This gate checks **FEI missingness specifically**, not every
merged BCF metric; all six were already validated at ingestion. Tests preserve
that distinction when the merge helper is called alone.

## OLD CELL 20: FEI differential and polarity

Input: df_master_bcf with Home_FEI, Away_FEI, and raw Home_Team/Away_Team labels.
FEI_MULTIPLIER = 30, fixed rather than caller-tunable.

```text
FEI_Model_Diff_Home = ((Home_FEI - Away_FEI) * 30).round(1)
FEI_Model_Favorite  = Home_Team if rounded differential > 0
                     Away_Team if rounded differential < 0
                     EVEN otherwise
FEI_Model_Margin   = abs(FEI_Model_Diff_Home)
```

Positive differential means home stronger; negative means away stronger. This
is not yet a sportsbook spread. Preserve pandas Series.round(1) and classify
AFTER rounding, including differentials that round to positive/negative zero.
Do not substitute Python scalar rounding or classify the unrounded value.

PASS: zero null differential rows, zero positive/home or negative/away polarity
errors, and zero zero-differential rows whose favorite is not `EVEN`. Failure
raises. NaN may initially produce an EVEN label, but missing differential fails;
there is no return of a fabricated zero margin. There is no edge threshold here.

## OLD CELL 21: FEI versus market

Required inputs: FEI_Model_Diff_Home, DK_Spread, FD_Spread, Home_Team, Away_Team.
Both market spreads are **home-perspective** values: negative means home favored,
positive home underdog. No away-spread sign conversion is inferred in this stage.

```text
FEI_Model_Home_Spread = (-FEI_Model_Diff_Home).round(1)
DK_FEI_Edge_Home     = (DK_Spread - FEI_Model_Home_Spread).round(1)
FD_FEI_Edge_Home     = (FD_Spread - FEI_Model_Home_Spread).round(1)
DK_FEI_Edge_Value    = abs(DK_FEI_Edge_Home)
FD_FEI_Edge_Value    = abs(FD_FEI_Edge_Home)
DK_FEI_Edge_Team     = home if DK edge >0, away if <0, EVEN otherwise
FD_FEI_Edge_Team     = home if FD edge >0, away if <0, EVEN otherwise
FEI_Books_Agree      = (DK_FEI_Edge_Team == FD_FEI_Edge_Team)
```

Example: model home spread -7 and market -3 yields +4 HOME value. A negative
edge selects AWAY even if the model favorite is HOME. Exact zero edge selects
`EVEN`, never `PICKEM`. Two EVEN labels agree; EVEN versus a directional team
disagrees. Agreement is label equality, not equality of edge magnitudes or an
EPA condition. No minimum FEI edge, consensus spread, favorite-agreement rule,
or EPA trigger filter is applied.

PASS: zero rows containing null in FEI_Model_Home_Spread, DK_Spread, FD_Spread,
DK_FEI_Edge_Home, FD_FEI_Edge_Home. Failure raises. No book is substituted for a
missing other book. The notebook does not separately gate edge-team nulls here;
that original predicate is retained, not silently expanded.

## Fixtures, parity, and historical validation

`bcf_segment_sample.csv` supplies controlled seven-column input. The source-exact
138-row manual paste is preserved as `bcf_notebook_week5.csv`.
`epa_bcf_fei_notebook_checkpoint.json` records the notebook hash, saved counts,
CELL 12's 15 displayed strongest edges, OLD CELL 19's 10 merge samples, OLD
CELL 20's 12 model samples, OLD CELL 21's 15 market samples, and CELL 6's full
57-game market display. Saved numeric displays use absolute tolerance 5e-7 plus
1e-12 binary-float epsilon. No unshown expected values are invented.

The checkpoint also clearly separates **replay inputs** from notebook expected
outputs: canonical feature-universe names and 57 upstream EPA inputs come from
the previous authenticated CFBD feature-layer validation, season 2026 through
Week 5, acquired October 19, 2026 at 18:49:34 UTC. Their source-table hash and
provenance are recorded. They are not the original notebook raw CFBD payloads
and are not October 17 recovery artifacts. Current tests require no network or
external scratch files; fixture values are stored in the repository for offline reproducibility.

The literal-cell test executes only CELL 12, CELL 13, CELL 14, OLD CELL 19,
OLD CELL 20, OLD CELL 21 using controlled DataFrames. Only CELL 13's hard-coded
manual paste assignment is replaced by the fixture; formulas, validation order,
merges and predicates run unchanged. It compares DataFrames after every stage,
including column order. A separate full 57-game replay also matches the same six literal cells
on identical inputs. Separate failure-parity checks exercise null EPA, FEI,
and market inputs. No startup, CFBD/Covers acquisition, or later cell is run.

Historical results (2026 through Week 5, target Week 6):

| Check | Saved expectation | Extracted result |
| --- | ---: | ---: |
| BCF raw / normalized rows | 138 / 138 | 138 / 138 |
| Unmatched / duplicate canonical / missing slate teams | 0 / 0 / 0 | 0 / 0 / 0 |
| BCF master games | 57 | 57 |
| Missing home FEI / away FEI / duplicate pairs | 0 / 0 / 0 | 0 / 0 / 0 |
| EPA triggers / below threshold, using current historical CFBD replay | 33 / 24 | 33 / 24 |
| FEI model missing / polarity / even-label errors | 0 / 0 / 0 | 0 / 0 / 0 |
| FEI market agreement / conflict | 57 / 0 | 57 / 0 |

All 15 saved EPA classifications and derived magnitudes reproduce when using
the signed EPA inputs actually saved in CELL 12. All 10 BCF merge samples, 12
FEI model samples and 15 FEI market samples match their saved numeric/string/
boolean outputs. Full 57-game FEI replay can use the notebook's manual BCF paste
and market display directly; it does not need new CFBD numeric feature values.

### Explicit upstream EPA replay discrepancy

The previous phase established matching displayed feature samples but did not
certify unshown full-table values. This phase's additional CELL 12 comparison
finds three numeric discrepancies in **one game**, James Madison at Georgia
Southern, when using that prior current historical CFBD replay:

| Field | Saved CELL 12 display | Current historical replay |
| --- | ---: | ---: |
| Home_Net_EPA_Margin | 0.047463 | 0.0433263653585203 |
| Net_EPA_Edge_Home | -0.374985 | -0.3791217452433439 |
| EPA_Edge_Value | 0.374985 | 0.3791217452433439 |

The EPA side remains James Madison Dukes and the trigger remains true. All 15
saved sample side/trigger classifications and the full 33/24 trigger counts
remain unchanged. These differences are explicitly asserted/documented in the
replay test, not hidden by widening tolerance or changing formulas. The original
CFBD raw payload is unavailable; the exact upstream cause is unproven. The
previous phase also recorded raw play-count drift. None of this establishes an
EPA trigger extraction error: literal-cell parity on identical inputs and saved
signed-input replay both pass.

Identical-input notebook parity passes. The James Madison at Georgia Southern
EPA difference is caused by changed upstream CFBD feature values supplied to
this segment, not by migrated formula behavior. The reason those upstream
values changed cannot be established without the original raw payload. No
formula was altered to force historical numeric equality.

### Promotion assessment

This segment is suitable for review as a production replacement for EPA trigger,
BCF ingestion/normalization/merge, FEI differential, and FEI directional market
edges. Formulas, thresholds, labels, rounding, joins, and failure conditions are
preserved. Exact reproduction of every historical upstream CFBD value remains
uncertified, with the discrepancy above disclosed. No production formula or
input is adjusted to force obsolete upstream historical values.

Validation: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover
-s tests`. The complete suite passes **183 tests**: 135 existing plus 48 new
segment tests. No frozen notebook, committed CFBD feature module, Covers code,
alias map, or downstream model stage was modified.
