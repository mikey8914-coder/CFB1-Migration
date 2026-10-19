# Routing, key-number structure, large spreads, and Phase 1

## Authority, labels, and boundary

Authority: `legacy/CFB1_Colab_Reference.ipynb`, SHA-256
`94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`,
`docs/NOTEBOOK_MAP.md`, `docs/BEHAVIOR_LOCK.md`, and
`docs/MODULE3_CONVERGENCE_CONTRACT.md`. Labels below are the actual embedded
notebook labels. The frozen notebook and earlier committed modules are unchanged.

| Label | Production entry point | Legacy outputs |
| --- | --- | --- |
| OLD CELL 36 | routing.route_markets | df_market_routes |
| OLD CELL 37 | spread_structure.classify_spread_structure | enriched df_master_bcf, df_routed_market_structure |
| OLD CELL 38 | spread_structure.classify_large_spreads | enriched df_master_bcf, df_large_spread_routed |
| OLD CELL 39 | routing.apply_large_spread_routing | df_final_routes |
| OLD CELL 40 | routing.separate_evidence | df_evidence_routes |
| OLD CELL 41 | phase1.build_phase1_shortlist | enriched master, df_phase1_diagnostic, candidate_board, cut points |
| OLD CELL 42 | phase1.build_phase1_review | df_phase1_review |

Stop at OLD CELL 42. OLD CELL 43 Covers late-week movement audit and OLD CELL 44
final decision board remain unmigrated. No probability, push, expected ROI,
pricing, team-total calculations, or final handoff is implemented. Legacy route
labels containing TEAM_TOTAL and the review action COLLECT_COVERS_LINE_MOVEMENT
are preserved as metadata only; neither causes acquisition or model execution.
No October 17 recovery input or alias is used.

The new modules contain static extracted Python, not runtime notebook execution.
The extraction retains arithmetic, rounding, list order, joins, field names and
validation predicates; print/display side effects are removed. Functions copy
inputs and return the legacy output tables. No earlier evidence-generation
logic is duplicated. Phase1Tables names the four outputs of OLD CELL 41:
master, diagnostic, candidates, cut_points.

## OLD CELL 36: routing from corrected convergence

Required source columns: Game, EPA_FEI_Agree, Shared_Side, EPA_Value, FEI_Value,
M3_Support, M3_Conflict, M3_Support_Count, M3_Conflict_Count.

Only rows whose EPA_FEI_Agree is true enter df_market_routes. Preserve EVERY
agreement, including those without any support, conflict or route. Model_Side
copies Shared_Side. Default Spread_Status is STANDARD_REVIEW; routes start empty.
Apply independent rules in this exact order:

1. M3_Support_Count >0: append FULL_GAME_SPREAD.
2. M3_Conflict_Count >0: set DOWNGRADE_FULL_GAME_SPREAD; append DERIVATIVES_FIRST.
3. If support text contains LINE_YARDS OR OAY_DAY: append TEAM_TOTAL_OVER,
   1H_TEAM_TOTAL_OVER, 1H_SPREAD_REVIEW, in that order.
4. If support text contains HAVOC_TRAP OR EXPLOSIVENESS_FRAUD: append
   OPP_TEAM_TOTAL_UNDER, OPP_1H_TEAM_TOTAL_UNDER, 1H_UNDER_REVIEW, in that order.

Deduplicate routes via list(dict.fromkeys(routes)), preserving first occurrence,
then join with comma-space. Tests use substring checks exactly as the source;
there is no new structured token parser. Counts determine the first two rules;
support text determines the next two. Upstream corrected convergence normally
makes those consistent. Conflict does not remove support-derived route labels.
There is no EPA-trigger or strength threshold here.

Exact output order:

```text
Game, Model_Side, EPA_Value, FEI_Value, M3_Support, M3_Conflict,
Spread_Status, Eligible_Market_Routes, Final_Bet_Status
```

Final_Bet_Status is always `UNPRICED — DO NOT BET YET`. This literal status is not
an ROI or pricing calculation. Blank route strings are valid; a directional
conflict/nonagreement is excluded, not silently turned into an agreement route.

PASS: count equals int(EPA_FEI_Agree.sum()), zero duplicate Game rows
(keep=False), zero null required outputs Game/Model_Side/EPA_Value/FEI_Value/
Spread_Status/Eligible_Market_Routes/Final_Bet_Status, zero Model_Side==''.
Failure raises. M3 text fields are not separately null-gated here; validated
convergence is a prerequisite. As in the notebook, an entirely empty generated
board can fail column access rather than producing a new empty-slate PASS.

## OLD CELL 37: current spread and key-number structure

Input df_master_bcf requires DK_Spread and FD_Spread, already home-perspective:
negative favors home; positive favors away. Calculate on the FULL master slate:

```text
SPREAD_KEY_NUMBERS = [3, 7, 10, 14]
Consensus_Spread = ((DK_Spread + FD_Spread) / 2).round(2)
Consensus_Spread_Abs = abs(Consensus_Spread)
Nearest_Key_Number = first key minimizing abs(abs(Consensus_Spread) - key)
Distance_From_Key = round(abs(abs(Consensus_Spread) - Nearest_Key_Number), 2)
Within_0.5_Key = Distance_From_Key <= 0.5
Within_1.0_Key = Distance_From_Key <= 1.0
```

Preserve pandas Series.round(2) for consensus and Python round(distance,2) inside
the original nearest-key helper. Key ties choose the first key in the ordered
list: magnitude 5 selects 3, not 7. Proximity comparisons are inclusive and use
the rounded distance. Positive/negative equal magnitudes get the same key fields.
A distant spread still receives a nearest key; there is no NONE key sentinel.

Spread_Size_Bucket uses the following ordered **exclusive upper bounds**, not
rounded half-point membership tests:

| Magnitude | Label |
| --- | --- |
| <3 | UNDER_3 |
| otherwise <7 | 3_TO_6.5 |
| otherwise <10 | 7_TO_9.5 |
| otherwise <14 | 10_TO_13.5 |
| otherwise <17 | 14_TO_16.5 |
| otherwise <21 | 17_TO_20.5 |
| otherwise | 21_PLUS |

Thus 6.75 is still 3_TO_6.5 despite that display label. No new discretization is
introduced. The six new master fields above plus Spread_Size_Bucket retain
exact legacy names (seven derived fields total: consensus, magnitude, key,
distance, two proximity flags, bucket).

PASS: zero missing DK/FD input rows and zero null rows across all seven derived
columns. Failure raises; no book fallback or imputation is introduced. Derived
intermediates may be assigned before the gate, as in the source, but invalid
results are never returned by the function.

`df_routed_market_structure` includes only games with NONEMPTY initial
Eligible_Market_Routes, matched by raw Away_Team + ' at ' + Home_Team. It has:
Game, DK_Spread, FD_Spread, Consensus_Spread, Nearest_Key_Number,
Distance_From_Key, Spread_Size_Bucket. Master order is retained. Agreement-only
blank-route games are absent from this display, not from the full master.

### Key crossing is outside this segment

OLD CELL 37 has no temporal crossing calculation. Two current book quotes
straddling -3 simply produce their rounded consensus and nearest-key fields.
No Crossed_Keys, opener/current comparison, or movement status is invented.
The reference contains strict key-crossing behavior in OLD CELL 43 and later
CELL 48, outside this scope. Crossing regression here verifies that a straddling
DK/FD pair is not mistaken for a temporal audit. Implementing a crossing helper
now would import later behavior the user explicitly excluded.

## OLD CELL 38: large-spread classification

Constants: LARGE_SPREAD_THRESHOLD=16.5, VERY_LARGE_SPREAD_THRESHOLD=20.5.
From Consensus_Spread, return Consensus_Favorite and Favorite_Spread_Size:

- Negative: raw Home_Team, abs(spread).
- Positive: raw Away_Team, abs(spread).
- Zero: PICKEM, 0.0.

```text
Large_Spread_16_5 = Favorite_Spread_Size >= 16.5
Very_Large_Spread_20_5 = Favorite_Spread_Size >= 20.5
```

Both thresholds are inclusive. At 20.5 both flags are true. Size is always the
market favorite's spread magnitude, regardless of whether Model_Side is that
favorite or its underdog; no model-side sign transformation is introduced.

PASS: zero null inputs among Consensus_Spread/Home_Team/Away_Team, zero nulls
in the four derived fields, and zero Favorite_Spread_Size<0. Failure raises.

For the same initially nonempty-route game set, df_large_spread_routed contains
Game, Consensus_Favorite, Favorite_Spread_Size, Spread_Class,
Nearest_Key_Number, Distance_From_Key. Spread_Class precedence:

1. >=20.5: VERY_LARGE_20.5_PLUS
2. otherwise >=16.5: LARGE_16.5_TO_20
3. otherwise: BELOW_16.5

Do not confuse these thresholds with OLD CELL 37 bucket boundaries 17 and 21.
The master has flags; Spread_Class is in the routed diagnostic table only.

## OLD CELL 39: large-spread route adjustments

Build Game/Favorite_Spread_Size lookup from the full master. Left-merge onto
ALL df_market_routes on Game with validate='one_to_one'. Missing game features
are not hidden by an inner join. Parse existing comma-separated routes using
split(',') and strip each item. Start with the prior Spread_Status.

Apply in order:

1. Size >=20.5: status DERIVATIVES_FIRST_20.5_PLUS; append 1H_SPREAD_REVIEW,
   TEAM_TOTAL_REVIEW.
2. Otherwise size >=16.5: status LARGE_SPREAD_CAUTION; append the same labels.
3. AFTER size rules, if M3_Conflict != '': override status with
   DOWNGRADE_FULL_GAME_SPREAD and append DERIVATIVES_FIRST.
4. Deduplicate in insertion order and comma-space join.

Unlike OLD CELL 36's conflict count test, the final override tests nonempty
conflict TEXT. Preserve that source predicate. Large spreads can create active
routes for previously blank-route model-only agreements. Conflict overrides the
status but does not remove large-spread or support-derived route labels.

`df_final_routes` output order:

```text
Game, Model_Side, EPA_Value, FEI_Value, M3_Support, M3_Conflict,
Favorite_Spread_Size, Spread_Status, Eligible_Market_Routes, Final_Bet_Status
```

The final status remains UNPRICED — DO NOT BET YET. `active_routes` is the subset
with nonempty route text. PASS: count equals df_market_routes, zero duplicate
Game rows, zero Favorite_Spread_Size nulls, zero null required outputs
Game/Model_Side/EPA_Value/FEI_Value/Favorite_Spread_Size/Spread_Status/
Eligible_Market_Routes/Final_Bet_Status. Cardinality or validation failure raises.

## OLD CELL 40: evidence versus routing modifiers

Every final route starts Evidence with EPA_FEI_DIRECTIONAL_AGREEMENT, then adds
MODULE3_SUPPORT for nonempty M3_Support, then MODULE3_CONFLICT for nonempty
M3_Conflict. These are evidence descriptions of already-generated convergence;
no signal or agreement is recomputed here.

Routing_Modifiers adds VERY_LARGE_SPREAD_20.5_PLUS at >=20.5, otherwise
LARGE_SPREAD_16.5_TO_20 at >=16.5; then adds FULL_GAME_SPREAD_DOWNGRADE if
Spread_Status==DOWNGRADE_FULL_GAME_SPREAD. Size and downgrade do not count as
additional handicapping evidence.

Evidence_Class precedence:

1. Nonempty support: MODEL_PLUS_MATCHUP_SUPPORT.
2. Otherwise nonempty conflict: MODEL_WITH_MATCHUP_CONFLICT.
3. Otherwise: MODEL_AGREEMENT_ONLY.

Both support and conflict can remain in Evidence, but support wins the class.
This matters for later candidate reasons; do not replace it with a conflict-first
classification. Evidence and modifier text use comma-space joining.

`df_evidence_routes` fields:
Game, Model_Side, EPA_Value, FEI_Value, Evidence_Class, Evidence,
Routing_Modifiers, Spread_Status, Eligible_Market_Routes, Final_Bet_Status.
PASS: count equals df_final_routes, zero duplicate Game rows, zero nulls in all
these fields EXCEPT Routing_Modifiers (not a separate source required field),
and zero blank Evidence strings. Failure raises. Model-only rows with large
routing modifiers remain MODEL_AGREEMENT_ONLY, not matchup-supported.

## OLD CELL 41: Phase 1 shortlist

First enrich the FULL df_master_bcf:

```text
FEI_Edge_Conservative = min(DK_FEI_Edge_Value, FD_FEI_Edge_Value), row-wise
EPA_75 = EPA_Edge_Value.quantile(0.75)
EPA_90 = EPA_Edge_Value.quantile(0.90)
FEI_75 = FEI_Edge_Conservative.quantile(0.75)
FEI_90 = FEI_Edge_Conservative.quantile(0.90)
```

Preserve pandas defaults: min(axis=1) skips a single null, and quantile uses its
default interpolation/null behavior. Earlier model stages supply validated
inputs; no new imputation or partial-book availability claim is added here.
Quantiles are not calculated on agreements, active routes, or candidates alone.
90th-percentile values are reported but NOT eligibility cutoffs.

Iterate master order. Only games present in df_evidence_routes enter the
phase1 diagnostic universe. Select the first matching evidence row exactly as
the source; validation then requires complete evidence-universe cardinality.

```text
model_agreement = (EPA_Edge_Team == DK_FEI_Edge_Team and EPA_Edge_Team != 'EVEN')
EPA_Top25 = EPA_Edge_Value >= EPA_75
FEI_Top25 = FEI_Edge_Conservative >= FEI_75
Dual_Top25 = model_agreement and EPA_Top25 and FEI_Top25
module3_support = Evidence_Class == MODEL_PLUS_MATCHUP_SUPPORT
module3_conflict = Evidence_Class == MODEL_WITH_MATCHUP_CONFLICT
Phase1_Candidate = module3_support or Dual_Top25 or module3_conflict
```

Append Candidate_Reason labels in this order: MODULE3_SUPPORT,
DUAL_TOP25_MODEL_STRENGTH, MODULE3_CONFLICT when their respective conditions
hold. An evidence row with both support and conflict text is support-classed by
OLD CELL 40, so it does not independently gain MODULE3_CONFLICT here. A large
spread route alone does not make a weak model-only game a candidate.

`df_phase1_diagnostic` fields, in order:
Game, Model_Side, EPA_Value, EPA_Top25, FEI_Value_Conservative, FEI_Top25,
Dual_Top25, Evidence_Class, Candidate_Reason, Phase1_Candidate.
`candidate_board` retains diagnostic rows with Phase1_Candidate true, with
original index/order. The display sorts Dual_Top25, EPA_Value,
FEI_Value_Conservative descending; this does not reorder candidate_board itself.

PASS: diagnostic count equals len(df_evidence_routes), zero duplicate Game
rows, zero required-field null rows across the diagnostic columns EXCEPT
Candidate_Reason (which may legitimately be empty for noncandidates). Failure
raises. No strict EPA_Trigger gate or 90th-percentile requirement is introduced.

## OLD CELL 42: Phase 1 review board

Use Candidate_Reason text with this ordered classification:

1. MODULE3_SUPPORT AND DUAL_TOP25_MODEL_STRENGTH: MODEL_PLUS_MATCHUP.
2. Otherwise dual strength: STRONG_MODEL_AGREEMENT.
3. Otherwise support: MATCHUP_SUPPORTED.
4. Otherwise conflict: CONFLICT_REVIEW.
5. Otherwise UNCLASSIFIED, which fails validation.

Thus strength precedes conflict if both reasons occur. These are review classes,
not final decision or bet statuses. Exact fields:

```text
Game, Model_Side, EPA_Value, FEI_Value_Conservative, Evidence_Class,
Review_Class, Phase1_Reason, Late_Week_Action
```

Phase1_Reason copies Candidate_Reason. Late_Week_Action is the literal
COLLECT_COVERS_LINE_MOVEMENT. It does not run OLD CELL 43 or fetch Covers.
PASS: row count equals candidate_board, zero duplicate Game rows, zero null rows
in all eight outputs, zero UNCLASSIFIED rows. Failure raises. No final decision
board or audit inputs are synthesized.

## Fixtures, identical-input parity, and historical evidence

New fixtures: routing_controlled.json holds 12 synthetic master/convergence rows
covering agreement, nonagreement, support, conflict, both, large model-only games,
and Phase 1 strength. routing_notebook_checkpoint.json records the notebook
hash, saved streams and displayed tables from OLD CELL 36–42. Upstream historical
replay uses already committed Module 3/BCF fixtures, with their explicit prior
CFBD authentication provenance. No tests require live network or scratch files.

Tests execute the seven actual source cells with controlled and full historical
inputs, stub display, and compare all output DataFrames, cut points and column
orders. Production modules do not execute notebook code. Failure/boundary tests
cover cardinality, nulls, exact signed keys, ordered tie-breaking, rounding,
near/far keys, book straddling without temporal crossing, size thresholds,
conflict overrides, reason ordering, every review class, and exclusions.

Saved HTML can truncate text. Truncated Game labels are expanded only when an
upstream raw game has a unique matching prefix. Other truncated strings are
compared by the visible prefix; their undisplayed suffixes are not invented.
Identical-input source parity separately verifies complete production strings.
Numeric comparisons use displayed precision (absolute tolerance 5e-7 plus
1e-12 binary-float epsilon), not a reconstructed full-precision expected table.

Historical checkpoint: season 2026 through Week 5, target Week 6.

| Check | Saved | Replay |
| --- | ---: | ---: |
| Full slate / agreement-route rows | 57 / 37 | 57 / 37 |
| Initially active routes | 10 | 10 |
| Within 0.5 / 1.0 of a key | 41 / 42 | 41 / 42 |
| Favorite size >=16.5 / >=20.5 | 6 / 6 | 6 / 6 |
| Final active routes | 12 | 12 |
| Final active STANDARD_REVIEW / DERIVATIVES_FIRST_20.5_PLUS | 6 / 6 | 6 / 6 |
| MODEL_AGREEMENT_ONLY / MODEL_PLUS_MATCHUP_SUPPORT | 27 / 10 | 27 / 10 |
| Phase 1 diagnostic / shortlist / review rows | 37 / 14 / 14 | 37 / 14 / 14 |
| Candidates with support / dual-top25 / conflict reasons | 10 / 7 / 0 | 10 / 7 / 0 |
| MATCHUP_SUPPORTED / STRONG_MODEL_AGREEMENT / MODEL_PLUS_MATCHUP | 7 / 4 / 3 | 7 / 4 / 3 |

Saved/replay cut-point displays match: EPA_75=0.267, EPA_90=0.420,
FEI_75=10.6, FEI_90=13.2. Current replay full-precision cut points are
0.2669414192629591, 0.42035259610535197, 10.6, 13.2 respectively; the saved
printed cut points are not a source of additional precision.

Bucket counts match: UNDER_3=13, 3_TO_6.5=15, 7_TO_9.5=12, 10_TO_13.5=8,
14_TO_16.5=3, 17_TO_20.5=2, 21_PLUS=4. Available displayed tables contain 37
initial routes, 10 key structures, 10 large-spread classifications, 12 active
final routes, 10 matchup-evidence rows, 2 model-only-modifier rows, 14 candidates,
and 14 review rows. Route/review labels, eligibility, text visible in those
samples, and spread structure match, subject to the upstream numeric differences
explicitly listed next. Synthetic tests cover historical-absent conflict cases.

### Upstream EPA differences remain explicit

The broader saved displays expose two games whose current historical CFBD EPA
magnitudes differ from saved notebook output:

| Game | Saved EPA_Value | Current historical replay |
| --- | ---: | ---: |
| UConn Huskies at Temple Owls | 0.104439 | 0.1054004810204402 |
| James Madison Dukes at Georgia Southern Eagles | 0.374985 | 0.3791217452433439 |

UConn differs in OLD CELL 36's saved route table. James Madison differs in
OLD CELL 36, 41 and 42, totaling four displayed numeric discrepancies in these
seven cells. These values are copied from upstream EPA, not recalculated by
routing. Their exact upstream cause is not provable without the original raw
CFBD payloads. They are inherited input differences, not migrated formula
behavior: identical-input notebook parity passes for the complete pipeline.

All route, bucket, large-spread, quantile-display, shortlist and review
classification/count comparisons remain unchanged. The tests explicitly assert
the discrepancy inventory rather than hiding differences or changing formulas.
This does not certify exact equality for unavailable/unshown historical values.

## Verification and promotion assessment

Run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests`.
The full suite passes **300 tests**: 251 existing plus 49 new routing/Phase 1 tests.

The segment is suitable for review as the production replacement for OLD CELL
36–42. Formula/validation behavior, identical-input parity, and historical
classifications pass; the known upstream numeric drift remains disclosed.
OLD CELL 43 Covers audit and OLD CELL 44 final decision logic remain unmigrated.
No probability, pricing, push adjustment, ROI, team-total model or handoff stage
was added. Nothing is staged, committed or pushed in this implementation phase.
