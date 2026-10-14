# DK/FD Spread Dependency Review

## Conclusion

**One normalized home spread per game is sufficient in principle for a deliberately redesigned, price-free CFB1 workflow, but it is not sufficient to preserve the current legacy football behavior in general.** The legacy model uses two distinct point spreads in three consequential ways: DK-specific FEI direction, the smaller DK/FD absolute FEI edge, and the DK/FD mean. Moving wager economics to Universal Bet Slip Architect does not eliminate these football dependencies.

For an initial behavior-preserving migration, retain two honest, role-identified spread observations in the model snapshot (or equivalent information). If production is to use only one selected Action Network/Covers line, the direction, conservative-edge, and consensus substitutions require a separate explicit modeling decision and historical validation. This review recommends no silent replacement or artificial duplication into DK/FD fields.

This is a static dependency finding, not a measurement of historical error or proof that two-book inputs improve predictive performance. No notebook cells were executed, no new calibration was fitted, and no live data was fetched. Numerical frequency and magnitude of differences on coherent historical runs remain unresolved.

## Sources and scope

Reviewed:

- docs/MARKET_DATA_CONTRACT.md
- docs/BEHAVIOR_LOCK.md
- docs/MIGRATION_ORDER.md
- legacy/CFB1_Colab_Reference.ipynb

Notebook SHA-256: `94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`. Cell references below preserve original embedded labels, including OLD. This review changes none of those sources.

The approved ownership boundary remains: CFB1 owns football handicapping and calibrated game probabilities; Universal Bet Slip Architect owns all sportsbook-price-dependent wager evaluation, including break-even, expected ROI/EV%, sizing, stakes, promotions, and portfolio decisions. That approval changes economic responsibility, not automatically the model's spread-input semantics.

## Spread numbers versus prices

- `DK_Spread` and `FD_Spread` are **full-game HOME-team point handicaps**, taken from each bookmaker's home outcome `point`. Negative means home favored, positive means home underdog, zero means pick'em. For example, −7 is a point spread, not a payout price.
- `DK_Total` and `FD_Total` are full-game combined point thresholds from the Over outcome's `point`. Their legacy current-slate uses are structural validation/display and optional context; they do not drive the DK/FD spread formulas discussed here.
- `American_Odds` is sportsbook juice, such as −110, from outcome `price` in the separate offer path. Its sign is not a home/away or favorite/underdog convention. CELL 5 discards initial outcome prices.
- Model home margins use the opposite sign from home spread: positive margin means home stronger. Later `Market_Model_Spread`, `Retained_Model_Spread`, and offered `Line` use the selected team's perspective; away-side lines negate home-side lines.
- A sportsbook's point quote can be a football input even though the sportsbook's juice is Architect-owned. Removing prices does not justify removing distinct point observations that football calculations actually use.

## Exhaustive direct raw-spread references

These are all source cells containing `DK_Spread` or `FD_Spread`. CELL 4 is additionally listed as their acquisition predecessor. Inherited DataFrame copies do not themselves introduce a new numerical use.

| Original embedded label | Exact use | Football dependence or noncomputational use |
| --- | --- | --- |
| CELL 4 | Requests `spreads,totals` for `draftkings,fanduel` into odds_json; no named DK/FD DataFrame columns yet. | Provider transport; no juice used by core market flattening. Can be replaced without retaining Odds API as architecture. |
| CELL 5 | Stores home outcome points in DK_Spread/FD_Spread; declares both columns required; reports missing counts. | Creates two numeric observations. Printed PASS does not require zero missing point values. No averaging or price choice. |
| CELL 6 | Required columns, missing-point reporting, final market-card display. | Schema/coverage/display; includes no spread-derived arithmetic. Date filtering determines slate population. |
| CELL 11 | Carries initial market table through canonical home/away CFBD joins; displays DK_Spread/FD_Spread. | Spreads do not enter its EPA edge formula. Their later availability depends on preservation through joins. |
| CELL 12 | Displays both spreads beside EPA edge/trigger outputs. | EPA trigger uses only absolute net EPA edge ≥0.12; spread numbers are display-only here. |
| OLD CELL 21 | `round(DK_Spread - FEI_Model_Home_Spread,1)` and FD equivalent; derive absolute values, edge teams, book agreement; checks missing comparisons. | **Core numerical use.** Two independent edges; DK edge side is a later model input. |
| OLD CELL 23 | Identifies each book's favorite from its spread sign, compares to FEI favorite; displays DK spread/edge. | Football audit. These favorite agreement fields do not gate corrected convergence. |
| OLD CELL 37 | Requires nonnull DK/FD inputs; `Consensus_Spread = round((DK_Spread+FD_Spread)/2,2)`; computes key proximity and size buckets; routed display retains both spreads. | **Core numerical use.** Pair mean affects key structure, favorite size, and downstream routing. |
| CELL 47 | Requires both columns; row mean defines Consensus_Home_Spread (not explicitly rounded); its negative is Market_Home_Margin; fit EPA against that margin and blend/shrink. | **Core numerical use despite “DIAGNOSTIC ONLY” title.** Retained lines feed football probabilities/context. |
| CELL 66 | Selects DK_Spread/FD_Spread, DK_Total/FD_Total if available when enriching rich context. | Context export only for the raw fields; not a new two-book formula. |

The unnumbered configuration requires ODDS_API_KEY in its legacy startup PASS; that is provider plumbing, not evidence that juice is a football feature. CELL 10 preserves raw team labels and generates canonical keys; it does not read spread numbers. OLD CELL 19 and OLD CELL 26 preserve market columns while enriching the master but do not calculate with DK/FD spreads.

## Direct references to DK/FD-derived fields

This completes the explicit DK/FD-named field inventory beyond raw spreads:

| Original embedded label | Fields consumed/produced | Consequence |
| --- | --- | --- |
| OLD CELL 21 | DK_FEI_Edge_Home/Value/Team, FD_FEI_Edge_Home/Value/Team; FEI_Books_Agree | Produces signed/absolute edge and directional identity from each quote. FEI_Books_Agree is equality of edge-team labels, not a required two-book agreement gate. |
| OLD CELL 23 | DK_Market_Favorite, FD_Market_Favorite, DK_FEI_Market_Agree, FD_FEI_Market_Agree; DK_FEI_Edge_Team/Value for display | Favorite diagnostics/reporting; no later core branch depends on these market-favorite agreement flags. |
| OLD CELL 34 | DK_FEI_Edge_Team and DK_FEI_Edge_Value | Corrected convergence uses EPA_Edge_Team == DK_FEI_Edge_Team and excludes EVEN. FD direction and FEI_Books_Agree are **not** extra convergence conditions. |
| OLD CELL 41 | DK_FEI_Edge_Value/FD_FEI_Edge_Value and DK_FEI_Edge_Team | Conservative strength is row minimum of both absolute rounded edges; agreement is EPA versus DK direction. Full-slate strength quantiles determine Phase 1 membership. |

No other cell directly indexes a DK/FD-named spread-derived field in source. Numerous later cells consume their renamed descendants; that is genuine transitive football dependence, not evidence that the raw pair becomes irrelevant.

## Material football effects and downstream propagation

Let D be the initial DK home spread, F the initial FD home spread, and M the FEI model home spread. These symbols describe source formulas; they are not new modules.

### Direction and convergence

OLD CELL 21 calculates `e_D = round(D-M,1)` and `e_F = round(F-M,1)`. Positive selects home, negative away, zero EVEN. OLD CELL 34 specifically uses `sign(e_D)` for agreement with the EPA side. A chosen single spread S instead of D can flip home/away/EVEN, changing which games agree and how Module 3 support/conflict is oriented.

Propagation: OLD CELL 34 → OLD CELL 36 routes → OLD CELL 39/OLD CELL 40 → OLD CELL 41/OLD CELL 42 review → OLD CELL 43/OLD CELL 44 final decisions. The statistical Module 3 flags themselves are unchanged for identical teams/features; their interpretation relative to a changed shared side is not necessarily unchanged.

### Conservative FEI edge and Phase 1

OLD CELL 41 sets `FEI_Edge_Conservative = min(abs(e_D),abs(e_F))`. A single quote does not in general reproduce that value. The full master-slate 0.75 quantile is used for inclusive top25 selection; 0.90 is also computed but not the inclusion cutoff. A changed value or changed slate can alter the threshold and candidate classes across multiple games, not just the changed matchup.

The legacy “conservative” rule uses absolute edge magnitudes; it does not require both books to favor the same edge side. Do not add a new book-agreement filter or reinterpret the minimum as a directional consensus during extraction.

### Keys, spread size, and routes

OLD CELL 37 uses the pair mean rounded to two decimals for Consensus_Spread. It computes absolute key distances to [3,7,10,14], flags distance ≤0.5/≤1.0, and size buckets at <3/<7/<10/<14/<17/<21. OLD CELL 38 classifies market favorite and sizes ≥16.5/≥20.5. OLD CELL 39 adds derivative-review routes at these thresholds and then applies conflict overrides. OLD CELL 40 keeps size modifiers separate from model evidence.

Changing the chosen line can change nearest-key/proximity/bucket/favorite or large-spread flags. A conflict override can mask a status difference but does not prove all route strings or context stay identical. OLD CELL 44 uses final spread status in its confirming-market classification; therefore effects can reach the football decision board without any price or ROI calculation.

### Retained lines and probability calibration

CELL 47 separately computes an **unrounded row mean** `(D+F)/2`, fits `np.polyfit(Net_EPA_Edge_Home, -mean, 1)` on nonnull full-slate data, combines fitted EPA margin and FEI margin equally, and retains 25/40/50/60% of the raw market-model edge. CELL 48 consumes the 40% retained home line.

A replacement quote can change regression targets, slope/intercept, blended/retained lines, and therefore other games' outputs too. Using rounded OLD CELL 37 consensus as the CELL 47 target is not automatically equivalent to its unrounded mean. The football calibration/retention behavior remains CFB1-owned after removing economics.

CELL 48 compares the retained line to the **later Covers Current_Home_Spread**, oriented to Model_Side. That later observation is not the original DK/FD mean and must not overwrite the initial fit snapshot. Changed retained lines or model sides affect cushion, strict keys-between, and line-value context.

CELL 52 empirical win/push/loss probabilities depend on retained cushion, home/away orientation, and the evaluated market-line bucket. Price-free portions of CELL 55/CELL 57/CELL 57A and CELL 69 likewise depend on retained line/side and evaluated handicap. Distinct DK/FD current observations do not define a separate historical distribution: CELL 51 takes one historical provider spread per game (priority DraftKings, ESPN Bet, Bovada), independently of today's DK/FD pair. **One historical selected spread does not imply one current spread can preserve the pair-based fit and direction.**

Downstream probabilistic differences are possible through changed orientation, evaluated threshold, retained cushion, historical bucket, or integer-push evaluation. No claim is made that every small quote difference changes empirical frequencies; probabilities are discrete empirical functions and may coincide in a given case. Equal output in some cases does not establish general parity.

### What is not numerically changed by quote substitution alone

On an identical slate with identical statistical features, CELL 11 net EPA, CELL 12 trigger, OLD CELL 20 FEI differential/multiplier/polarity, and OLD CELL 24/OLD CELL 27/OLD CELL 28/OLD CELL 30 raw matchup flags do not use DK/FD spread magnitude. Dropping games or changing team matches can still change output population and later slate-wide calculations.

OLD CELL 43's movement relationship uses opener/current Covers home spreads and Model_Side, not DK/FD spread magnitudes directly. A changed model side/review set can nevertheless change its interpretation or coverage requirements.

## Illustrative counterexamples — not historical validation results

These are arithmetic examples of documented rules, not executed notebook runs or invented historical goldens.

| Inputs / substitution | Original behavior | Single-spread effect |
| --- | --- | --- |
| M=−7; D=−6; F=−8; EPA side home; choose S=pair mean=−7 | DK edge +1→home; FD edge −1→away; minimum absolute edge=1; EPA agrees with DK. | Edge S−M=0→EVEN, magnitude=0; a one-line reinterpretation loses convergence and changes strength. Book disagreement did not block original convergence. |
| Swap D=−6,F=−8 to D=−8,F=−6, holding M=−7 | Pair mean and conservative absolute strength remain identical, but DK side changes from home to away. | Mean alone cannot encode DK-specific directional behavior. A spread range or disagreement magnitude without ordered role is also insufficient. |
| D=−16; F=−17; choose S=D | Consensus=−16.5, triggers inclusive large-spread caution threshold. | S=−16 does not trigger it; football routing may differ. |
| D=−6; F=−8; choose S=D | Consensus magnitude 7 lies exactly on key 7, bucket 7_TO_9.5. | Magnitude 6 is distance 1 from key 7, bucket 3_TO_6.5; key proximity/bucket differ. |

Using D alone preserves DK direction but can change mean/minimum. Using the mean preserves pair-mean calculations (if precision/snapshot match) but can change DK direction/minimum. Selecting whichever quote is closest to FEI might preserve minimum magnitude but not the other roles and would introduce a new model-dependent acquisition policy. None is authorized by economics ownership alone.

## Which dependencies belong only to wager evaluation?

**No core numerical use of raw DK_Spread/FD_Spread exists solely to evaluate juice or ROI.** OLD CELL 21, OLD CELL 37, OLD CELL 41, and CELL 47 provide retained football inputs; their two-quote dependency cannot be dismissed as pricing infrastructure. OLD CELL 23/CELL 66 diagnostic/context uses can be isolated without changing a quantitative rule.

Separate offer-stage dependencies do belong to Architect, sometimes mixed with football calculations:

| Original label | Price-only responsibility / review | Football calculation to preserve |
| --- | --- | --- |
| CELL 46/CELL 53/CELL 54 | Exact offer intake/validation, event-market discovery and quota plumbing | Core identity/schedule must be supplied separately; no need for these APIs. |
| CELL 55 | American_Odds bounds, best-price de-duplication, probability-minus-break-even ranking and offer shortlist | Team-line orientation, candidate cushion, empirical probability and key tradeoff at an explicitly evaluated handicap. Candidate membership needs review, not silent filter deletion. |
| CELL 57 | Profit multiple, break-even, expected ROI and ROI status/price edge | Historical source selection and calibrated W/P/L. Preserve its 300-observation bucket gate where applicable; review missing bucket metadata separately. |
| CELL 57A | Adjusted ROI from profit multiple | Integer-line push estimation and adjusted W/P/L. |
| OLD CELL 59/CELL 60 | TT anchor chosen near −110, odds bounds, highest-price duplicates, price-edge shortlist, TT break-even/ROI/status | Experimental routing/direction/adjustment/calibration/push remain football-side; a price-free TT anchor is unresolved. |
| CELL 61/CELL 62 | Positive-ROI review/card membership, odds tiebreaks, max-ROI VALUE_ALT, economic statuses | All eligible football context/probabilities must survive in the new handoff; do not retain only the wager-selected subset. |
| CELL 67/CELL 73 | Offer-specific book/price merge identity, break-even/ROI synchronization and required priced export columns | Football probability/context synchronization under new explicit game/market/team/line keys. |
| CELL 69 | Actual odds, break-even and live ROI/status | Price-free line-specific probability/push evaluation; its conservative source choice differs from CELL 57 and must not be silently unified. |

Individual DraftKings/FanDuel **offer lines** can differ from initial DK_Spread/FD_Spread or from the later Covers line. Architect attaches each actual offer and uses a CFB1 probability for that explicit point threshold, or a sufficiently specified price-free distribution/line-query interface. It must not reuse a single reference-line cover probability at a different line. Multiple evaluated handicaps are not a requirement to acquire multiple routine bookmaker prices in CFB1.

## Minimum data options and recommendation

### Option A: one selected spread — possible future modeling contract

One canonical `current_home_spread` plus `current_total`, stable matchup/home/away identity, schedule and source/retrieval provenance can support the semantic tasks of FEI-versus-market comparison, routing/keys, retained lines and line-conditional probabilities. Action Network first/Covers gap-fill can theoretically supply those point measurements; acquisition has not been tested here.

This requires an explicit replacement policy for all three roles:

1. What replaces specifically DK FEI direction?
2. What replaces min(DK absolute edge, FD absolute edge) and its slate percentiles?
3. What replaces the pair mean for key/routing structure and the full-slate EPA market fit?

Assigning S to all three is **a proposed modeling change**, not merely replacing an API or moving economics. No new single-source rule is implemented or approved by this review. If separately approved, document its intentional differences and validate calibration/routes/probabilities against coherent historical cases; do not claim exact legacy parity unless demonstrated.

If D=F on the complete retained slate and the chosen S equals that same snapshot value, point-based formulas can coincide after required schema adaptation. More general coincidental parity is possible, but one representative game is not evidence of slate-wide equivalence. Quote rounding, missing values, names, snapshots, and candidate population still matter.

### Option B: two role-identified spread observations — minimum general legacy preservation

Keep the existing normalized primary home-spread value and **one additional numeric field**:

| Proposed field | Purpose |
| --- | --- |
| current_home_spread | Initial primary-role observation, corresponding to D for exact legacy replay; home perspective. |
| secondary_home_spread | Initial secondary-role observation, corresponding to F for exact legacy replay; same matchup/perspective/snapshot policy. |
| source / retrieved_at | Existing provenance for primary observation; clarify underlying quote origin where needed. |
| secondary_source / secondary_retrieved_at | Small provenance additions for the second actual quote, so role, availability, and timing are explicit. |

Two ordered values are sufficient to recompute the DK-role direction, rounded absolute-edge minimum, rounded/unrounded means, diagnostic book differences, and all downstream descendants without requiring American odds. Book names are not mathematical primitives, but **which original value occupied the primary/DK role is meaningful**. For exact replay retain actual original role provenance. Reassigning primary to a different selected source is a separate source/model policy change even if two numeric fields still exist.

A long observation table with role/source/timestamp and one `home_spread` value column can represent the same two observations without widening the game table; it is not genuinely one spread observation per game. Primary spread plus an **unrounded** pair mean could recover the secondary algebraically, but adds equivalent information and hides quote provenance. Primary plus unsigned “difference” or range alone loses role/order. Derived conservative edge is model-dependent and not a clean provider field. The smallest transparent addition is the second point value with its provenance.

This recommendation does not require aggressively searching for two bookmaker quotes in normal acquisition. If only one honest source observation is available, the remaining legacy calculation policy is unresolved: document/exclude/defer the affected football stage as appropriate rather than fabricate a second quote, silently change the model, or claim production readiness. Source-role policy and acceptable coverage must be resolved explicitly before implementation.

### Separate temporal observations remain necessary

The initial fit snapshot, later audit-current spread, and opening spread are different roles, even if each uses one selected source. One mutable “latest” value cannot preserve all of them.

- Freeze initial quote(s) for OLD CELL 21/OLD CELL 37/OLD CELL 41/CELL 47.
- Retain `audit_current_home_spread` (or a separately identified later observation) for OLD CELL 43/CELL 48.
- Retain actual `open_home_spread` for OLD CELL 43/OLD CELL 44 final movement decisions.

Only point spreads are needed; opener/current juice is not. These temporal requirements are independent of whether the initial model ultimately uses one or two source quotes. Historical calibration also needs its own selected spread/score data; neither timestamp provenance nor current_total can replace that dataset.

## Approved architecture changes versus regressions to investigate

| Change | Classification |
| --- | --- |
| Remove American odds, break-even, expected ROI/EV%, Kelly/stakes, price-ranked wager selection and mandatory price-key exports from CFB1 | **Approved intentional architecture change**; preserve historical formulas and assign evaluation to Architect. |
| Replace Odds API transport with normalized Action Network/Covers input carrying equivalent point observations and identities | Acquisition architecture change; compare inputs/outputs and record source/coverage differences. Equivalent inputs may preserve football behavior; a new provider alone does not prove equivalence. |
| Replace unequal DK/FD spreads with one selected quote/mean, change primary direction source, or drop minimum-edge conservatism | **Separate modeling policy change, not currently approved by economics ownership.** Unexplained football differences are potential regressions. |
| Require both book edge teams to agree because two quotes are present | New convergence gate; absent from OLD CELL 34; unauthorized behavioral change. |
| Change rounded key consensus to unrounded (or round CELL 47 fit target prematurely) | Potential numerical regression unless separately reviewed. |
| Exclude games or substitute late-current/opening lines for initial quotes | Source/population/timing change that affects quantiles/fit/decisions; not a consequence of moving ROI. |
| Preserve raw Module 3 flags but flip shared model side without accounting for support/conflict | Potential football regression; signal orientation must follow the reviewed directional policy. |
| Export only old positive-ROI decision-card games while removing ROI columns | Incorrectly retains Architect-selected membership in the football handoff; requires explicit redesign/completeness checks. |
| Infer unsupported game-win/total/TT/first-half probabilities from a fair line to simplify handoff | New probability/model logic; not authorized by this review. |

## Unresolved risks before declaring one-spread production sufficient

1. A selected-source directional/minimum/consensus policy has not been approved or validated. Economics separation alone does not resolve these roles.
2. No coherent historical replay quantified quote disagreement, changed convergence/candidates, threshold crossings, fit coefficients, retained lines, or calibration results. The examples establish possible effects only.
3. Source observation timing, raw-to-canonical identity, missing secondary quotes, initial/audit/opening snapshots, and reduced-slate fit/percentile effects require explicit contracts.
4. The football handoff needs line-specific probability/push evaluation for actual Architect handicaps; reference-line probability alone is insufficient. Interface and supported probability events remain to be specified.
5. Existing CELL 57 bucket-metadata propagation, CELL 57A signed-line push behavior, CELL 69 source-choice differences, and experimental TT anchors/calibration still need review. Do not correct or certify them under the guise of removing DK/FD naming.

**Production recommendation:** use one normalized home-spread *field/observation format*, with two role-identified initial observations where preserving general legacy behavior is required. A genuinely single initial spread per game is a viable future simplification only after separate modeling approval and validation. Neither sportsbook juice nor routine Odds API acquisition is necessary for that football contract.
