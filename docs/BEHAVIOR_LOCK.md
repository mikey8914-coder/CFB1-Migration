# CFB1 Behavior Lock

## Scope and evidence

The immutable reference is `legacy/CFB1_Colab_Reference.ipynb` (SHA-256 `94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`). All cell references below use its original embedded labels, including `OLD` and suffixes. Unnumbered configuration/cleanup cells are identified by purpose.

This document records **source-derived behavior to match**, not a claim that modules or notebook outputs have been validated. The notebook was inspected without execution. The approved ownership boundary below governs new production requirements. Earlier expected-ROI ownership in NOTEBOOK_MAP.md is superseded; team totals remain experimental.

A future football-side module is validated against coherent known historical Colab inputs and intermediate football outputs. Legacy priced exports/formulas are historical references for Architect migration, not required outputs of new CFB1. Approved ownership/schema differences must be recorded separately from football behavior discrepancies. Match row identities/order, columns, types, missingness, signs, thresholds, rounding, route/status text, warnings, and guard outcomes. No fixed expected slate size, team count, signal count, fit coefficient, historical sample size, or numerical output is invented here. Counts derived from `len(...)`, sums, or input sets are dynamic checks, not fixed historical goldens. Historical saved outputs may be stale or out of execution order and must be tied to an identified run before use as goldens.

Printed PASS conditions are distinguished from exceptions and diagnostic-only counts. Passing a structural check does not demonstrate model parity. Where the source only reports a count, that is not a hard stop. Where no guard exists, no new required value is attributed to the notebook. The source-exact validation appendix records counter definitions and predicates, including required-column lists.

## Approved architecture — supersedes earlier EV ownership

**Intentional architectural change:** CFB1 owns football handicapping and calibrated game probabilities. **Universal Bet Slip Architect owns all sportsbook-price-dependent wager evaluation:** break-even probability, expected ROI/EV%, Kelly sizing, stakes, promotions, and portfolio decisions. This supersedes earlier statements that expected ROI remains in production CFB1, including the earlier CURRENT MIGRATION DECISIONS in NOTEBOOK_MAP.md. The frozen notebook remains historical evidence and is unchanged.

New production CFB1 must not require or calculate American-odds break-even, profit multiples, probability-minus-break-even edges, expected returns, price-edge statuses, price-ranked offer selections, or recommended wagers/stakes. These legacy calculations remain documented for historical replay and Architect boundary review; omission from CFB1 is an approved ownership change, **not an accidental numerical regression**. A football-side discrepancy in probabilities, push estimates, model lines, routing, or keys still requires investigation; this boundary change does not authorize changes to those calculations.

Routine CFB1 market measurements remain **spreads and game totals**, with schedule/identity fields needed to associate them. Source/retrieval timestamps provide provenance. Opening spread is conditionally needed for the preserved late-week movement audit; it is another spread observation, not juice. Historical calibration may still need historical spreads/totals, scores, classifications, and provider provenance. That football calibration dataset is distinct from live sportsbook offer acquisition. No routine Odds API key, sportsbook prices, props, or offer-shopping fields are required by new CFB1.

## Intended football-side handoff — proposed, not implemented

The handoff supplies **all football-eligible modeled/review games**, with explicit exclusions or unavailable/qualitative states. Do not first filter games by positive ROI or price attractiveness. It should contain:

- Stable game identity, canonical away/home teams, season/week and scheduled kickoff, model/data version, frozen model cutoff, market source and observation timestamps.
- Model side; home/team perspective and sign conventions; fair/retained model lines and relevant margins/cushions; spread/game-total snapshot context; applicable opener/current spread movement.
- Football-calibrated probabilities with explicit event definitions. A game-win probability must be identified separately from a probability of covering a particular line. Every line-conditional spread/total/TT probability must identify its evaluated line, team, market family, direction, and horizon (full game versus first half).
- Applicable win/push/loss probabilities, their calibration/source/version and sample context, missingness and validation status. Preserve W/P/L normalization and half-point/integer push rules; do not invent unsupported game-win, total, first-half, or experimental TT probabilities merely to populate the interface.
- EPA/FEI evidence, Module 3 support/conflict, convergence, football-side routing/review status, key-number classifications/barriers, warnings, and experimental/qualitative flags.

**Excluded from CFB1 handoff requirements:** American_Odds, Sportsbook-priced offer identity, Break_Even_Prob/Break_Even, Profit_Multiple, Probability_Edge defined against price, Expected_ROI/EV%, Kelly/stake/bankroll fields, price-edge statuses, and ROI-selected PRIMARY/VALUE_ALT roles. The Architect attaches actual offers and computes wager economics. Football-side warnings may remain; price-derived warning/status meanings must be reviewed rather than repurposed.

For actual sportsbook lines different from the frozen evaluation line, the interface must eventually provide a reproducible **price-free** probability/push evaluation at the requested point threshold, or a sufficiently specified calibrated distribution/line-indexed output. Do not reuse a cover probability at a different handicap or infer it from a fair line alone. Whether this becomes a line-query interface or distribution handoff is unresolved; neither is implemented here. Receiving a point threshold does not transfer price evaluation into CFB1.

## Price-dependent legacy decisions requiring review

| Original embedded label | Legacy coupling | Required architecture treatment / unresolved dependency |
| --- | --- | --- |
| OLD CELL 36 / OLD CELL 39 / OLD CELL 40 / OLD CELL 41 / OLD CELL 42 / OLD CELL 43 / OLD CELL 44 | Core routes, shortlist/review, and market-movement decisions use spread points, football evidence, and keys, **not American juice**. Covers pasted prices are unused. | Preserve these football decisions and their rule precedence. Keep audit opener requirements and full-slate population effects. “Market-dependent” here does not mean price-dependent. |
| CELL 46 / CELL 53 / CELL 54 | Manual and automatic exact-offer intake, validation, quota/market discovery. | Legacy/reference or Architect acquisition boundary, outside new CFB1 requirements. |
| CELL 55 | Odds bounds [-250,300], probability-minus-break-even ranking, best-price duplicate selection, and offered-line shortlist membership. | Price evaluation/selection belongs to Architect. Preserve price-free line orientation, empirical calibration, and key calculations separately. New football candidate membership is not defined by silently removing a filter. |
| CELL 57 | W/P/L calculations mixed with profit multiple, break-even, ROI/status, and price-based schema guards. | Preserve football W/P/L and source-selection behavior; migrate economics responsibility to Architect. A legacy pricing-column guard is not a new football API requirement. |
| CELL 57A | Price-free integer push redistribution followed by profit-multiple ROI recomputation. | Preserve push estimator and adjusted W/P/L; ROI recomputation belongs to Architect. |
| OLD CELL 59 | Experimental route-to-TT adjustment/calibration mixed with odds bounds, anchor nearest -110, highest-price duplicate selection, probability-edge shortlist. | Keep experimental football logic; **TT anchor/candidate selection is price-coupled and unresolved**. Do not substitute a price-free anchor or certify TT migration without separate review/validation. |
| CELL 59A / CELL 60 | Football directional support/push gating precedes price-dependent TT ROI/status. | Retain experimental eligibility/push behavior; CELL 60 economics belong to Architect. |
| CELL 61 / CELL 62 | Review subset requires positive ROI; PRIMARY ties use odds; VALUE_ALT maximizes ROI; pricing statuses use ROI. | Legacy wager selection/display is not the new football decision board. Architect owns these choices; review export membership/roles explicitly. Do not silently reinterpret PRIMARY or drop unpriced football candidates. |
| CELL 61B / CELL 66 / CELL 67 / CELL 73 | Rich football context is merged with priced rows; synchronization keys include Sportsbook/American_Odds and economics fields; final exports depend on the ROI-selected card. | Preserve football context/probability synchronization, but specify new event/line/perspective keys and completeness checks. Old price-key/schema/ROI sync assertions remain historical only. New schema is an intentional interface change. |
| CELL 69 | Live team-line probability/push recalculation mixed with odds, break-even, ROI/status. | Preserve price-free threshold recalculation/calibration; Architect evaluates the actual price. Its conservative source choice differs from CELL 57's 300-observation gate; do not unify silently. |

Remaining dependencies: validate replacement single-source versus legacy DK/FD spread roles, initial versus audit snapshots, opener availability, CELL 57 bucket-metadata propagation, CELL 57A signed-line push behavior, and team-total calibration. Preserve these uncertainties; moving economics does not solve them.

## Historical reference checkpoints and preserved football behavior

The sections and source excerpts below describe what the notebook actually does. Football calculations remain behavior locks. Price calculations, offer-selected populations, price guards, statuses, and schemas are **historical-only**, unless explicitly assigned to the Architect above. Legacy pricing guards must not block a new CFB1 football run. Source formulas and thresholds are retained as evidence, not deleted or silently rewritten.

## Team normalization

**CELL 10 → `df_target_market`, `TEAM_ALIASES`, `cfbd_teams`:** normalize with whitespace collapse (`re.sub(r'\s+', ' ', str(name)).strip()`), then explicit dictionary lookup with unchanged cleaned-name fallback. Preserve every alias, accents, punctuation, and raw `Home_Team`/`Away_Team`. For example, Appalachian State Mountaineers becomes App State, Hawaii Rainbow Warriors becomes Hawai'i, and San Jose State Spartans becomes San José State. Canonical names populate `Home_CFBD_Name` and `Away_CFBD_Name`.

`cfbd_teams` is the set of stripped, nonnull CFBD names. Match flags use set membership. Home/away unmatched tables are independently de-duplicated. `total_unmatched = len(home_unmatched) + len(away_unmatched)` must be **0** for printed PASS. A STOP is printed on failure; CELL 10 does not itself raise.

**CELL 14 → `df_bcf`:** preserve raw BCF Team and map exactly: Appalachian State → App State; Connecticut → UConn; Hawaii → Hawai'i; San Jose State → San José State; Southern Mississippi → Southern Miss. Unmapped BCF names remain unchanged. PASS requires **0 unmatched BCF rows**, **0 duplicated canonical names**, and **0 target-slate teams absent from BCF**; failure raises. Preserve the distinction between this canonical normalization and raw market `Game = Away_Team + ' at ' + Home_Team` identifiers used in exports/events.

## CFBD acquisition and master merge

**CELL 2 → `df_ppa`, `adv_json`:** request regular-season plays for every week from 1 through `DATA_THROUGH_WEEK` inclusive; valid play rows must have offense, defense, and PPA. `Off_EPA` and `Def_EPA` are means grouped by offense/defense; combine by outer team merge. Advanced stats are frozen with `startWeek=1`, `endWeek=DATA_THROUGH_WEEK`. Printed PASS requires every recorded play request HTTP 200, required play columns present, nonempty reconstructed PPA, and HTTP 200/nonempty advanced payload. Do not replace frozen inputs with full-season future data.

**CELL 3 → `df_cfbd`:** inner-merge PPA and flattened advanced stats by team; `Net_EPA_Margin = Off_EPA - Def_EPA`. Preserve the offense/defense success, passing-down, explosiveness, havoc, and offensive-line-yards fields. Printed PASS requires required columns present, **0 duplicate team rows**, **0 total critical nulls**, and a nonempty matrix. This is a print gate, not an explicit raise.

**CELL 11 → `df_master`:** two left `many_to_one` merges on home/away canonical names. `Net_EPA_Edge_Home = Home_Net_EPA_Margin - Away_Net_EPA_Margin`. PASS requires `len(df_master) == len(df_target_market)`, **0 home/away missing net EPA**, and **0 duplicated home/away pairs**; failure raises.

**OLD CELL 25 / OLD CELL 26:** reuse frozen `adv_json` for defensive line yards. Drop prior target columns before refresh, use `one_to_one` team merge into `df_cfbd`, then home/away `many_to_one` master merges. OLD CELL 25 requires **0 duplicate source teams**, **0 missing source line yards**, and **0 missing post-merge values**. OLD CELL 26 requires row count equal to `len(df_target_market)`, **0 missing home/away defensive values**, and **0 duplicate pairs**. Both raise on failure. Preserve earlier master enrichment during refresh.

## EPA trigger

**CELL 12 → enriched `df_master`:** `EPA_Edge_Value = abs(Net_EPA_Edge_Home)`. Positive home edge chooses Home_Team, negative chooses Away_Team, zero chooses `EVEN`. `EPA_Trigger = EPA_Edge_Value >= 0.12` (inclusive). PASS requires **0 missing edge values**, **0 missing edge teams**, and `trigger_count + below_count == len(df_master)`; failure raises. Actual trigger counts depend on the reference slate. Do not add an EPA-trigger requirement to convergence that the convergence source does not impose.

## BCF/FEI merge

**CELL 13 → `df_bcf_raw`:** required columns are `Team, FEI, OFEI, DFEI, SFEI, OAY, DAY`; six metrics use numeric coercion, Team is stripped. Missing/placeholder input raises. PASS requires nonempty input, **0 missing required columns**, **0 duplicate raw team rows**, and **0 numeric-conversion/null problems**. Preserve validation order, including duplicate detection before Team whitespace cleanup.

**OLD CELL 19 → `df_master_bcf`:** left `many_to_one` home/away merges of all six metrics using CELL 14 canonical names. PASS requires `len(df_master_bcf) == len(df_master)`, **0 missing home/away FEI**, and **0 duplicate home/away pairs**; failure raises. The merge guard specifically checks FEI missingness; do not describe it as a new separate null check on every merged metric.

## FEI directional model

**OLD CELL 20:** `FEI_Model_Diff_Home = round((Home_FEI - Away_FEI) * 30, 1)`. Favorite is home for a positive rounded differential, away for negative, `EVEN` for zero. Margin is its absolute value. PASS requires **0 missing differential rows**, **0 polarity errors**, and **0 incorrect EVEN rows**; failure raises.

**OLD CELL 21:** `FEI_Model_Home_Spread = round(-FEI_Model_Diff_Home, 1)`. For each DK/FD market: `FEI_Edge_Home = round(book_home_spread - FEI_Model_Home_Spread, 1)`; positive chooses home, negative away, zero EVEN; edge value is absolute. `FEI_Books_Agree` compares edge-team strings. PASS requires **0 rows with missing model spread, book spreads, or book home-edge comparisons**; failure raises.

**OLD CELL 23:** a negative book home spread favors home, positive favors away, zero is `PICKEM`. Book-market/FEI favorite agreement uses equality. PASS requires **0 missing market-favorite or agreement fields**; failure raises. Do not merge `PICKEM` and `EVEN` labels during initial extraction.

## Module 3 signals

Apply every test symmetrically to each offense and its opposing defense; preserve inclusive comparisons and flags on `df_master_bcf`.

| Original label | Signal / output | Exact threshold conjunction | Source PASS |
| --- | --- | --- | --- |
| OLD CELL 24 | Away/Home_Havoc_Trap | offensive passing-down SR **≤0.273** AND opposing defensive havoc **≥0.192** | 0 missing input rows and 0 missing output rows; otherwise raise |
| OLD CELL 27 | Away/Home_LineYards_Push | offensive line yards **≥3.5** AND opposing defensive line yards **≥3.3** | 0 missing input rows and 0 missing output rows; otherwise raise |
| OLD CELL 28 | Away/Home_Explosiveness_Fraud | offensive explosiveness **≥1.4**, offensive SR **≤0.42**, opposing defensive SR **≤0.33** | 0 missing input rows and 0 missing output rows; otherwise raise |
| OLD CELL 30 | Away/Home_OAY_DAY_Edge | offensive OAY **≥0.54125** AND opposing DAY **≥0.56825** | 0 missing input rows and 0 missing output rows; otherwise raise |

Match flag counts and diagnostic rows against historical inputs; none has a fixed expected positive count. OLD CELL 31 appends HAVOC, LINE_YARDS, EXPLOSIVENESS_FRAUD, OAY_DAY labels in that order. Its board has one row per master game; PASS requires **0 duplicate Game rows**, **0 missing required fields**, and **0 errors in `Total_Module3_Signals = Away_Signal_Count + Home_Signal_Count`**. It is an audit board, not the convergence input.

## Directional convergence

**OLD CELL 34 → `df_convergence_corrected`:** `EPA_FEI_Agree = (EPA_Edge_Team == DK_FEI_Edge_Team) and EPA_Edge_Team != 'EVEN'`. Shared_Side is that side on agreement, otherwise empty. This uses DK FEI side specifically, not FD or a newly devised consensus.

Support is the shared side's positive LINE_YARDS/OAY_DAY signals plus the opponent's negative HAVOC_TRAP/EXPLOSIVENESS_FRAUD signals. Conflict is the shared side's negatives plus the opponent's positives. Preserve loop/list order, team-name text, comma-space joining, and support/conflict counts. Disagreement leaves both lists empty.

PASS requires one row per `df_master_bcf` game, **0 duplicate Game rows**, **0 required-field null rows**, and **0 agreed rows with blank Shared_Side**; failure raises. Compare support and conflict independently; both may be present. Printed support/conflict counts are data-dependent.

## Routing

**OLD CELL 36 → `df_market_routes`:** retain every agreed convergence row, including agreement-only rows with blank routes. Default status is STANDARD_REVIEW. Any support adds FULL_GAME_SPREAD; any conflict sets DOWNGRADE_FULL_GAME_SPREAD and adds DERIVATIVES_FIRST. LINE_YARDS/OAY_DAY support adds TEAM_TOTAL_OVER, 1H_TEAM_TOTAL_OVER, 1H_SPREAD_REVIEW. HAVOC_TRAP/EXPLOSIVENESS_FRAUD support adds OPP_TEAM_TOTAL_UNDER, OPP_1H_TEAM_TOTAL_UNDER, 1H_UNDER_REVIEW. De-duplicate routes with insertion order retained. Final_Bet_Status remains `UNPRICED — DO NOT BET YET`.

PASS requires row count equal to `sum(EPA_FEI_Agree)`, **0 duplicates**, **0 required null rows**, **0 blank Model_Side**; failure raises.

**OLD CELL 39 → `df_final_routes`:** merge favorite spread size one-to-one; at **≥20.5** set DERIVATIVES_FIRST_20.5_PLUS, otherwise at **≥16.5** set LARGE_SPREAD_CAUTION; both append 1H_SPREAD_REVIEW and TEAM_TOTAL_REVIEW. Apply nonempty M3_Conflict override **after** large-spread rules, setting DOWNGRADE_FULL_GAME_SPREAD and adding DERIVATIVES_FIRST. PASS requires row count equal to `len(df_market_routes)`, **0 duplicates**, **0 missing spread sizes**, and **0 required null rows**; failure raises.

**OLD CELL 40 → `df_evidence_routes`:** evidence always contains EPA_FEI_DIRECTIONAL_AGREEMENT, then support/conflict evidence where present. Spread size/downgrade are routing modifiers, not additional handicapping evidence. Evidence_Class prioritizes nonempty support over conflict, otherwise MODEL_AGREEMENT_ONLY. Preserve this precedence when both exist. PASS requires row count equal to `len(df_final_routes)`, **0 duplicates**, **0 required null rows**, **0 blank evidence**; failure raises.

## Key-number classification

**OLD CELL 37:** keys are **[3, 7, 10, 14]**. `Consensus_Spread = round((DK_Spread + FD_Spread)/2, 2)`; magnitude is absolute. Nearest key minimizes distance in this ordered list (ties select the first key); distance is rounded to 2 decimals before inclusive **≤0.5** and **≤1.0** flags. PASS requires **0 missing DK/FD input rows**, **0 missing calculated output rows**; failure raises.

| Magnitude condition, in order | Spread_Size_Bucket |
| --- | --- |
| <3 | UNDER_3 |
| <7 | 3_TO_6.5 |
| <10 | 7_TO_9.5 |
| <14 | 10_TO_13.5 |
| <17 | 14_TO_16.5 |
| <21 | 17_TO_20.5 |
| Otherwise | 21_PLUS |

The same bucket boundaries are redefined in CELL 52 and CELL 55. CELL 48 and OLD CELL 43 use signed keys **[-14,-10,-7,-3,3,7,10,14]** and strict `low < key < high`, then sorted unique magnitudes. Endpoints do not count as crossed.

**CELL 48 → `df_key_value`:** key barrier is nonempty keys-between text. Next adverse key exists only for a favorite (negative model-side market spread), using first magnitude strictly greater than its magnitude. Status: null cushion → CHECK; cushion ≤0 → NO_RETAINED_MODEL_EDGE; otherwise barrier → EDGE_WITH_KEY_BARRIER; otherwise EDGE_NO_KEY_BARRIER. Preserve notes. Required prior objects are checked, but no explicit numerical PASS gate exists here.

**CELL 55 offer tradeoffs:** only adverse favorite-to-favorite line changes are labeled. OFF_KEY uses distance <0.001 from starting key; CROSSES uses strict crossings; LANDS_ON_KEY uses candidate distance <0.001. Preserve ordering. **CELL 56 audit:** exclude pick'em; orient actual margin to market favorite; global landing rate is exact-key landings/total games; local window is **±2.0** closing favorite points, bounded below at zero. Key_Tax_V1 is maximum of global/local rates. OFF_KEY/CROSSES sum relevant taxes; LANDS_ON_KEY has zero tax; diagnostic adjusted cover probability is clipped to [0,1]. This audit probability is not the canonical CELL 57/57A ROI input. No new push deduction is authorized.

## Large-spread classification

**OLD CELL 38:** consensus spread <0 → home favorite; >0 → away favorite; zero → PICKEM with size 0. Favorite_Spread_Size is absolute consensus spread. Inclusive flags: Large_Spread_16_5 **≥16.5**, Very_Large_Spread_20_5 **≥20.5**. Routed display classes are VERY_LARGE_20.5_PLUS, LARGE_16.5_TO_20, BELOW_16.5, in that order. PASS requires **0 missing input rows**, **0 missing output rows**, **0 negative sizes**; failure raises. Large/very-large positive counts remain input-dependent.

## Phase 1 shortlist/review board

**OLD CELL 41 → `df_phase1_diagnostic`, `candidate_board`:** conservative FEI edge is row-wise minimum DK/FD absolute FEI edge. EPA/FEI **0.75 and 0.90 quantiles** are computed on the full `df_master_bcf`, before selecting agreement games. Inclusion uses the **0.75** thresholds (inclusive), not the computed 0.90 thresholds. Dual_Top25 requires non-EVEN EPA/DK-FEI agreement and both top25 tests. Only games found in `df_evidence_routes` are represented. Candidate is support OR dual top25 OR conflict; append reason labels in that order.

PASS requires diagnostic rows equal to `len(df_evidence_routes)`, **0 duplicate Game rows**, and **0 required null rows**; failure raises. Candidate/support/dual/conflict counts have no fixed targets.

**OLD CELL 42 → `df_phase1_review`:** ordered class rules are support+dual → MODEL_PLUS_MATCHUP; else dual → STRONG_MODEL_AGREEMENT; else support → MATCHUP_SUPPORTED; else conflict → CONFLICT_REVIEW; else UNCLASSIFIED. Preserve reasons and `Late_Week_Action = COLLECT_COVERS_LINE_MOVEMENT`. PASS requires rows equal to `len(candidate_board)`, **0 duplicates**, **0 required null rows**, **0 UNCLASSIFIED rows**; failure raises. No hard-coded Week 6 reconstruction or recovery bridge is present in these source cells.

## Covers market relationship

**OLD CELL 43 → `df_covers`, `covers_audit`:** manually pasted weekly rows are historical/recovery input. Preserve generic parser/audit behavior, not that fixed slate as architecture. Intake cleans strings and coerces open/current home spreads. PASS requires row count equal to the unique review-game set, **0 missing games**, **0 extra games**, **0 duplicate Game rows**, and **0 missing spread-data rows**; failure raises. This is complete coverage of the selected review set, not a mandate to chase a complete initial market slate.

`Spread_Move = round(Current_Home_Spread - Open_Home_Spread, 2)`. Negative movement is toward home; positive toward away; zero NONE. NONE → NEUTRAL; movement toward Model_Side → CONFIRMS_MODEL; otherwise CONFLICTS_WITH_MODEL. Key_Cross is nonempty strict-crossed-key text. Movement_Size is absolute rounded movement; 0 → NO_MOVE, <1 → SMALL, <2 → MODERATE, otherwise MAJOR. Final audit PASS requires rows equal to `len(df_phase1_review)` and **0 missing audit-field rows**; failure raises.

## Final decision classification

**OLD CELL 44 → `df_final_decision`:** preserve one-to-one joins of review, routes, and Covers audit, then this precedence:

| Ordered condition | Decision_Status |
| --- | --- |
| CONFLICT_REVIEW + confirming market | CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL |
| CONFLICT_REVIEW + conflicting market | CONFLICT_REVIEW_MARKET_REJECTS_MODEL |
| Other CONFLICT_REVIEW | CONFLICT_REVIEW_UNRESOLVED |
| Conflicting market + (MAJOR movement OR Key_Cross) | STRONG_MARKET_CONFLICT |
| Other conflicting market | MARKET_CONFLICT |
| Neutral market | NEUTRAL_MARKET |
| Confirming market + (LARGE_SPREAD_CAUTION OR DERIVATIVES_FIRST_20.5_PLUS) | CONFIRMED_BUT_LARGE_SPREAD |
| Other confirming market | CONFIRMED |
| Otherwise | UNCLASSIFIED |

Preserve exact Decision_Note strings from source. PASS requires rows equal to `len(df_phase1_review)`, **0 duplicates**, **0 required null rows**, **0 UNCLASSIFIED rows**; failure raises. Do not reorder conflict-review handling behind general market-conflict handling.

**OLD CELL 45 → `df_gem_export`, `gem_csv`:** preserve its 17 selected columns, stripped text, CSV without index, and status display order: CONFIRMED=1, CONFIRMED_BUT_LARGE_SPREAD=2, NEUTRAL_MARKET=3, CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL=4, CONFLICT_REVIEW_UNRESOLVED=5, MARKET_CONFLICT=6, STRONG_MARKET_CONFLICT=7, CONFLICT_REVIEW_MARKET_REJECTS_MODEL=8, UNCLASSIFIED=9; unknown default=99; secondary sort Game. PASS requires same count as final decision, **0 duplicates**, **0 blank status**, **0 blank model side**; failure raises.

## Retained/blended model line

**CELL 47 → `df_prob_model`, `df_phase1_shrinkage`:** consensus home spread is row mean DK/FD. Market_Home_Margin is its negative. On nonnull EPA/market rows, `beta, intercept = np.polyfit(Net_EPA_Edge_Home, Market_Home_Margin, 1)`. EPA_Model_Home_Margin is intercept + beta×EPA edge; EPA home spread is its negative. FEI home margin is negative FEI home spread. Blend uses **0.5 EPA + 0.5 FEI**; raw home spread is negative blend margin; raw edge is consensus spread minus raw spread.

Retention levels are **[0.25, 0.40, 0.50, 0.60]**. Edge_Retained is raw edge×retention; Shrunk_Home_Spread is consensus minus retained edge. Preserve full-slate fit before selecting review games, all retention outputs, and their unrounded calculation values. This cell does not provide a fit-error PASS threshold or fixed coefficients. Its nominal missing-review fallback still later references `df_phase1_review`; do not claim that fallback is independently runnable.

**CELL 48:** select `Shrunk_Home_Spread_40` (40%); orient both current Covers home line and retained home line to the model side: home unchanged, away negated, invalid side NaN. `Model_Cushion_Points = round(Market_Model_Spread - Retained_Model_Spread, 2)`. Preserve diagnostic key/line statuses because downstream consumers use them. The CELL 48 0.4 constant is consistent with the selected `_40` column, not permission to choose a different retention.

## Full-game spread probability

**CELL 51 → `df_hist_spread`:** regular-season historical years **2021–2025**, completed FBS-vs-FBS games only. Choose first nonnull spread in provider priority **DraftKings, ESPN Bet, Bovada**. Actual_Home_Margin = Home_Score − Away_Score; Market_Expected_Home_Margin = −Closing_Home_Spread; Spread_Error = actual minus expected. Positive error → HOME_COVER, negative → AWAY_COVER, zero → PUSH. HTTP failures raise; there is no fixed required historical row count or numeric PASS. Preserve historical rows/provider provenance, not just a fitted distribution summary.

**CELL 52 → `df_cover_prob`:** historical errors are nonnull floats; orient errors home-positive, away-negated, then add Model_Cushion_Points. W/P/L are empirical fractions where adjusted errors >0 / ==0 / <0. Bucket is based on the absolute model-side market spread. Record Global/Bucket W/P/L and Historical_Bucket_N; CFB1_Cover_Prob_V1 is row minimum global/bucket cover probability. No hard probability-sum guard exists here.

**CELL 55 → `df_spread_shortlist`:** use supplied full-game offers, join retained model context, keep model-side team and FULL_GAME_SPREAD route, inclusive odds **[-250,300]**, candidate cushion `Line - Retained_Model_Spread >= -0.5`. Keep useful lines inclusively between `min(market, model)-0.5` and `max(market, model)+0.5`. Orient history by model side; candidate bucket uses absolute candidate Line; conservative cover probability is **min(global,bucket)**. Highest American_Odds wins duplicate Game/Team/Line. Combine nearest-main 3, best-edge 3, and all key-tradeoff rows, de-duplicate, sort Line descending, retain **at most 6 per game**. Preserve filtering/order effects. This cell has required-object checks, not a printed PASS condition for final shortlist size.

**CELL 57 → `df_ev`:** recalculate candidate-oriented global and bucket triplets. Missing/empty bucket falls back to global triplet. Probability_Source is SPREAD_BUCKET only when row `Historical_Bucket_N >= 300` and a nonempty matched bucket exists; otherwise GLOBAL. CFB1_Win/Push/Loss select the entire source triplet, **not the minimum probabilities**. CFB1_Cover_Prob aliases CFB1_Win_Prob. `Probability_Edge = CFB1_Win_Prob - Break_Even_Prob`.

Source hard stops require pricing columns, global_errors, and Home_Team for orientation; **0 probability-sum errors** by `np.isclose(sum,1.0,atol=1e-9)` and no retained legacy staking columns. The NumPy default relative tolerance is not explicitly overridden. CELL 55 does not itself attach Spread_Bucket or Historical_Bucket_N to its shortlist, so the normal static source path appears to take GLOBAL in CELL 57 unless another input provides those fields. Document and validate that flow; do not silently reconnect CELL 52 metadata and call it unchanged behavior.

## Push adjustment

**CELL 57A → `df_ev` enriched:** `float(Line).is_integer()` determines whole lines; missing/noninteger returns push probability 0 and N=0. Target margin is **abs(round(integer Line))**. Select historical rows whose absolute Closing_Home_Spread is within **±1.0** of target margin, inclusive. No comparable rows → (0,0). Push frequency uses Actual_Home_Margin == positive target for home model side, negative target for away model side. Preserve this literal orientation rule before any bug investigation; it uses absolute line and does not independently branch on favorite versus underdog sign.

Let base W,L be CELL 57 values and H be Historical_Push_Prob. `nonpush = W + L`; when positive, win_share=W/nonpush, loss_share=L/nonpush; otherwise shares are NaN. Push-adjusted W=(1−H)×win_share, P=H, L=(1−H)×loss_share. ROI is recalculated from adjusted W/L. Key landing rates are context only, not a second push deduction. Half-point lines therefore have zero push mass and re-normalized nonpush probabilities.

Hard stops require **0 adjusted probability-sum errors** using `np.isclose(sum,1.0,atol=1e-9)` and no legacy staking columns. Integer-row and nonzero-push counts are diagnostics without fixed targets. New CFB1 preserves these canonical adjusted spread probabilities. Legacy downstream ROI uses the adjusted values historically; new ROI evaluation belongs to the Architect.

## Legacy break-even probability — historical reference only

**CELL 55 / CELL 57 / OLD CELL 59 / CELL 60 / CELL 69:** for American odds O<0, break-even = abs(O)/(abs(O)+100); for O≥0, 100/(O+100). Profit multiple is O/100 for positive odds, 100/abs(O) for negative odds (CELL 57 uses its nonpositive branch for zero). Preserve exact source branches and validation behavior; no new zero-odds convention is supplied by this document. Break-even is the source's quoted-price probability, not a newly push-conditioned break-even formula.

For historical replay/Architect boundary review, record Break_Even_Prob, Profit_Multiple, CELL 60 Break_Even_Prob_Final, and handoff aliases. These are not new production CFB1 requirements; the Architect owns their calculation. None of these helper definitions supplies a standalone numeric PASS threshold.

## Legacy expected ROI — historical reference only

**CELL 57:** EV_Per_Dollar = W×Profit_Multiple − L; Expected_ROI aliases it. Push payout contributes zero. Status: NaN→NO_EV; ROI≥0.05→STRONG_PRICE_EDGE; ≥0.03→POSITIVE_EV; >0→THIN_POSITIVE_EV; otherwise NON_POSITIVE_EV. Warnings join nonblank key-tradeoff text and MARKET_CONFLICT/STRONG_MARKET_CONFLICT with ` | `.

**CELL 57A:** Push_Adjusted_EV_Per_Dollar = adjusted W×Profit_Multiple − adjusted L; Push_Adjusted_ROI aliases it. CELL 57 EV_Status is not recomputed here. Preserve adjusted metrics and downstream status calculations separately.

**CELL 60 (experimental):** TT_EV_Per_Dollar = TT_Final_Win_Prob×Profit_Multiple − TT_Final_Loss_Prob; TT_Expected_ROI aliases it. Status: ROI≤0→NEGATIVE_EV; <0.02→THIN_POSITIVE_EV; <0.05→POSITIVE_EV; otherwise STRONG_PRICE_EDGE. Warnings include strong/general market conflict or ORIGINAL_MATCHUP_CONFLICT for CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL.

**CELL 61 spread handoff pricing status:** NaN→NO_QUANTITATIVE_PRICE; ROI≥0.05→STRONG_PRICE_EDGE; ≥0.02→POSITIVE_EV; >0→THIN_POSITIVE_EV; otherwise NON_POSITIVE_EV. The **0.02 versus CELL 57's 0.03** cutoff is an actual legacy difference, not a single threshold to normalize during extraction. Preserve status outputs independently.

Expected ROI was calculated in legacy CFB1; under the approved architecture it belongs exclusively to Universal Bet Slip Architect. No bankroll allocation, Kelly fraction, recommended stake, promo, parlay/SGP, or portfolio output is added. Probability-sum and staking-field checks are described above; no fixed expected ROI or model-edge count is present in the source.

## Team-total experimental output

**CELL 58 → `df_hist_team_total`:** same historical years/FBS/completed-game filter/provider priority as CELL 51, but require one selected provider line with **both spread and game total**. Home implied TT=(game_total−home_spread)/2; away=(game_total+home_spread)/2. Error=actual team points−implied TT; append home and away observations. Positive/negative/zero error → OVER/UNDER/PUSH. HTTP failures raise; printed historical summaries supply no fixed sample count or statistical validation threshold.

**OLD CELL 59 → `df_tt_routes`, `df_tt_anchors`, `df_tt_shortlist`:** only explicit TEAM_TOTAL_OVER routes target Model_Side OVER; OPP_TEAM_TOTAL_UNDER targets opponent UNDER. Generic TEAM_TOTAL_REVIEW supplies no direction. De-duplicate route triples; raise on duplicates, missing model match, or unsupported adjustment. Adjustment=model cushion/2 for model-side OVER, negative cushion/2 for opponent UNDER. Join supplied TEAM_TOTAL offers by Game/Team/Direction; inclusive odds [-250,300]. Anchor per Game/Team/Sportsbook prefers `team_totals` rows nearest −110 price, otherwise any candidate nearest −110. Fair TT=anchor+adjustment; OVER edge=fair−line, UNDER edge=line−fair. Keep line distance from anchor **≤4.0**. W/P/L uses TT errors+edge for OVER, −errors+edge for UNDER. Keep highest odds duplicate Game/Team/Direction/Line; combine nearest-anchor 2 and best-edge 2 per group, de-duplicate. Preserve data-dependent counts; no expected successful-route count is specified.

**CELL 59A → `df_tt_validated`:** OVER supported only when adjustment>0; UNDER supported only when adjustment<0; opposite sign OPPOSED, zero NEUTRAL, unknown direction CHECK. Only SUPPORTED→QUANTITATIVE_OK; all others QUALITATIVE_REVIEW_ONLY. Integer test is distance from round(line) **<1e-9**. Push uses historical implied TT within **±1.0** of line and actual team points exactly equal to line; noninteger/no sample → (0,0). Qualitative final W/P/L all NaN. Quantitative nonpush win/loss shares are redistributed around historical push mass; if no nonpush mass, W/L are NaN.

CELL 59A **reports** half-point rows with positive push and supported rows with probability-sum deviation **>1e-9**. It does **not raise** on these counts or define a PASS condition. Do not describe diagnostics as a hard validation gate. Preserve these reported checks and verify their results against identified baselines.

**CELL 60 → `df_tt_ev`:** quantitative rows only, with ROI formula/status above. Hard stops: **0 rows with absolute W/P/L sum deviation >1e-9**, no retained TT_Full_Kelly/TT_Quarter_Kelly/TT_Quarter_Kelly_Stake columns. The absolute-difference comparison alone is not an explicit missing-value check; NaN sums may not count as >1e-9. Record that limitation rather than claiming a stronger guard. Team-total parity does not establish independent statistical validity; remain experimental until separately validated.

## Legacy final handoff schema — historical reference only

**CELL 61 → `df_cfb1_gem_handoff`, `df_cfb1_gem_review`:** spread Model_Probability/Push_Probability/Expected_ROI_Final must come from CELL 57A; TT quantitative values come from CELL 60; qualitative TT numeric probability/push/break-even/ROI are NaN. Complete handoff schema, in order:

`Game, Market_Family, Team, Direction, Bet_Label, Sportsbook, Line, American_Odds, Model_Adjustment, Model_Probability, Push_Probability, Break_Even_Prob, Expected_ROI_Final, Decision_Status, Pricing_Status, Warning`.

Review subset is positive-ROI quantitative rows plus all qualitative rows. Sort both by Game, Market_Family, Expected_ROI_Final descending within family, NaNs last. Hard stops: required adjusted-spread columns exist, **0 missing Game values**, no column containing Kelly/Stake/Bankroll case-insensitively. Display percentages are scaled/rounded copies, not stored probabilities.

**CELL 61B:** copy full handoff to CFB1_FULL_CONTEXT_V1 before compression; preserve CSV without index. Archive storage side effects remain outside production.

**CELL 62 → `CFB1_DECISION_CARD_V1`:** positive adjusted-ROI spread rows and positive-ROI quantitative TT rows only, plus qualitative representatives. Per group PRIMARY is nearest market/TT anchor, tie sorted by American_Odds descending; remaining max-ROI row is VALUE_ALT. Qualitative representative is nearest anchor with QUALITATIVE_REVIEW role and NaN quantitative fields. TT quantitative Model_Status is **TEAM_TOTAL_V1_EXPERIMENTAL**; qualitative Model_Status is QUALITATIVE_ONLY. Card schema:

`Game, Market_Family, Card_Role, Team, Direction, Bet_Label, Sportsbook, Line, American_Odds, Model_Adjustment, Model_Probability, Push_Probability, Break_Even, Expected_ROI, Decision_Status, Model_Status, Warning_Final`.

Sort by Game, Market_Family, Card_Role; require adjusted-spread fields and no staking columns. No fixed card row count is specified.

**CELL 66 → `CFB1_FULL_CONTEXT_V2`:** retain rich phase-1, Module 3, market, model, and key context; many-to-one merge onto V1 pricing and append phase-1 games without pricing. Preserve Decision_Card_Included, Context_Usage, BACKGROUND_PHASE1_ONLY rows and naming aliases. Required objects are checked; displayed context counts are not additional hard PASS conditions.

**CELL 67 → `CFB1_FULL_CONTEXT_FINAL`:** require canonical CELL 57A spread fields; verify unique lookup keys **Game, Team, Sportsbook, Line, American_Odds**. Replace final-context spread adjustment, probability, push, break-even, and ROI with canonical df_ev values. Compare the decision card to matching final-context spread rows using those same keys and `np.isclose(..., equal_nan=True)` for all five quantities; no custom atol/rtol is supplied. All sync booleans must be true or raise. Reject legacy staking columns in both final context and card. Preserve text cleanup, context coverage, and CSV schema; separate Colab download side effect. Zero mismatches in this check alone does not prove complete card/context membership if a merge dropped rows; compare membership in future baseline validation too.

**CELL 73 → `CFB1_ARCHITECT_HANDOFF`:** base rows on the actual decision card, enrich with final game context, rename Break_Even→Break_Even_Prob and Warning_Final→Warning. Ordered desired schema (context columns included where present):

`Game, Model_Side, Market_Family, Card_Role, Team, Direction, Bet_Label, Sportsbook, Line, American_Odds, Model_Adjustment, Model_Probability, Push_Probability, Break_Even_Prob, Expected_ROI, Model_Status, Decision_Status, Warning, Phase1_Reason, Module3_Support_Conflict, Spread_Status, Market_Relationship, Open_Home_Spread, Current_Home_Spread, Movement_Size, Movement_Toward, Movement_Class, Key_Numbers_Crossed, Eligible_Market_Routes, Decision_Note`.

Required fields are `Game, Market_Family, Card_Role, Team, Direction, Bet_Label, Sportsbook, Line, American_Odds, Model_Probability, Push_Probability, Break_Even_Prob, Expected_ROI, Model_Status, Decision_Status, Warning, Eligible_Market_Routes`. Hard stops: **0 missing required columns**, **0 qualitative-only numeric probability/push/break-even/ROI values**, no staking columns. Desired optional context fields are not all hard-required. Preserve CSV ordering and no-index export.

CELL 73C restores only final context from the first sorted matching CSV; do not include it in normal generation or treat it as a replacement for the above calculations. CELL 69 live recalculation is on-demand and requires a nonempty matching history bucket. It chooses the GLOBAL triplet when global win probability ≤ bucket win probability, otherwise the SPREAD_BUCKET triplet, then applies historical integer push redistribution. Unlike CELL 57, it does not use the 300-observation gate. It raises when `np.isclose(adjusted W+P+L, 1.0, atol=1e-10)` is false (default relative tolerance retained). Preserve retained lines, this source choice, football probabilities/push, and context without fitting a new model; retain the ROI calculation only as historical Architect reference; it is not a required automatic weekly step.

## Unresolved validation boundaries

- Known historical goldens, data timestamps, source payloads, and run sequence must be established before numeric parity can be claimed. This task does not execute the reference.
- Odds API setup/acquisition and exhausted-quota artifacts are not behavior to preserve as required production infrastructure. Capture useful historical input/output contracts for replay; new CFB1 must validate price-free football outputs independently of offer fixtures.
- The intended Action Network/Covers initial acquisition is absent; its mapping to legacy DK/FD fields and any excluded games requires a separately reviewed comparison, especially for full-slate fits/percentiles.
- Confirm the CELL 57 source metadata flow and CELL 57A signed-line push orientation against baseline cases before declaring them bugs or changing them.
- Printed-only checks and NaN-sensitive guards must not be promoted to stronger notebook guarantees in reports. An intentional validation improvement belongs to a later authorized change.

## Legacy source-exact validation predicates and counters

The excerpts below are statically transcribed from the reference with whitespace/quotes normalized for readability. They show dynamic count definitions, required-field lists, printed PASS predicates, and direct hard-stop conditions; they are documentation, not extracted modules or executed tests. A hard-stop predicate is a **failure condition**. Printed reports without a hard stop remain diagnostics. Model formulas and expected classifications are described in the checkpoints above.

### CELL 2

```text
required_play_columns = ['offense', 'defense', 'ppa']
missing_play_columns = [col for col in required_play_columns if col not in df_ppa_plays.columns]
```

Printed PASS when: `all_ppa_weeks_pass and ppa_structure_pass and advanced_pass`.

### CELL 3

```text
required_columns = ['team', 'Off_EPA', 'Def_EPA', 'Net_EPA_Margin', 'Off_SuccessRate', 'Off_PassingDown_SR', 'Off_Explosiveness', 'Def_SuccessRate', 'Def_PassingDown_SR', 'Def_Havoc_Rate', 'Off_LineYards']
missing_columns = [col for col in required_columns if col not in df_cfbd.columns]
duplicate_teams = df_cfbd[df_cfbd.duplicated(subset=['team'], keep=False)]
critical_nulls = df_cfbd[required_columns].isnull().sum()
total_critical_nulls = int(critical_nulls.sum())
```

Printed PASS when: `len(missing_columns) == 0 and len(duplicate_teams) == 0 and (total_critical_nulls == 0) and (len(df_cfbd) > 0)`.

### CELL 10

```text
total_unmatched = len(home_unmatched) + len(away_unmatched)
```

Printed PASS when: `total_unmatched == 0`.

### CELL 11

```text
expected_games = len(df_target_market)
duplicate_games = df_master[df_master.duplicated(subset=['Home_Team', 'Away_Team'], keep=False)]
```

Printed PASS when: `len(df_master) == expected_games and len(home_missing) == 0 and (len(away_missing) == 0) and (len(duplicate_games) == 0)`.

### CELL 12

```text
missing_edge_values = int(df_master['EPA_Edge_Value'].isna().sum())
missing_edge_teams = int(df_master['EPA_Edge_Team'].isna().sum())
```

Printed PASS when: `missing_edge_values == 0 and missing_edge_teams == 0 and (trigger_count + below_count == len(df_master))`.

### CELL 13

```text
required_bcf_columns = ['Team', 'FEI', 'OFEI', 'DFEI', 'SFEI', 'OAY', 'DAY']
missing_bcf_columns = [col for col in required_bcf_columns if col not in df_bcf_raw.columns]
duplicate_bcf_teams = pd.DataFrame()
total_numeric_problems = sum(numeric_problems.values()) if numeric_problems else 0
```

Hard stop when: `not bcf_text or bcf_text == 'PASTE THE GEM CSV HERE'`.

Printed PASS when: `len(df_bcf_raw) > 0 and len(missing_bcf_columns) == 0 and (len(duplicate_bcf_teams) == 0) and (total_numeric_problems == 0)`.

### CELL 14

```text
missing_target_bcf_teams = [team for team in target_cfbd_teams if team not in normalized_bcf_team_set]
duplicate_normalized_names = df_bcf[df_bcf.duplicated(subset=['CFBD_Team'], keep=False)]
```

Printed PASS when: `len(bcf_unmatched) == 0 and len(duplicate_normalized_names) == 0 and (len(missing_target_bcf_teams) == 0)`.

### OLD CELL 19

```text
expected_games = len(df_master)
missing_home_bcf = df_master_bcf[df_master_bcf['Home_FEI'].isna()]
missing_away_bcf = df_master_bcf[df_master_bcf['Away_FEI'].isna()]
duplicate_games = df_master_bcf[df_master_bcf.duplicated(subset=['Home_Team', 'Away_Team'], keep=False)]
```

Printed PASS when: `len(df_master_bcf) == expected_games and len(missing_home_bcf) == 0 and (len(missing_away_bcf) == 0) and (len(duplicate_games) == 0)`.

### OLD CELL 20

```text
missing_fei_model = df_master_bcf[df_master_bcf['FEI_Model_Diff_Home'].isna()]
polarity_errors = df_master_bcf[(df_master_bcf['FEI_Model_Diff_Home'] > 0) & (df_master_bcf['FEI_Model_Favorite'] != df_master_bcf['Home_Team']) | (df_master_bcf['FEI_Model_Diff_Home'] < 0) & (df_master_bcf['FEI_Model_Favorite'] != df_master_bcf['Away_Team'])]
even_errors = df_master_bcf[(df_master_bcf['FEI_Model_Diff_Home'] == 0) & (df_master_bcf['FEI_Model_Favorite'] != 'EVEN')]
```

Printed PASS when: `len(missing_fei_model) == 0 and len(polarity_errors) == 0 and (len(even_errors) == 0)`.

### OLD CELL 21

```text
required_market_fields = ['FEI_Model_Home_Spread', 'DK_Spread', 'FD_Spread', 'DK_FEI_Edge_Home', 'FD_FEI_Edge_Home']
missing_market_comparisons = df_master_bcf[df_master_bcf[required_market_fields].isna().any(axis=1)]
```

Printed PASS when: `len(missing_market_comparisons) == 0`.

### OLD CELL 23

```text
required_fields = ['DK_Market_Favorite', 'FD_Market_Favorite', 'DK_FEI_Market_Agree', 'FD_FEI_Market_Agree']
missing_values = df_master_bcf[df_master_bcf[required_fields].isna().any(axis=1)]
```

Printed PASS when: `len(missing_values) == 0`.

### OLD CELL 24

```text
missing_havoc_inputs = df_master_bcf[df_master_bcf[['Away_Off_PassingDown_SR', 'Home_Def_Havoc_Rate', 'Home_Off_PassingDown_SR', 'Away_Def_Havoc_Rate']].isna().any(axis=1)]
missing_havoc_outputs = df_master_bcf[df_master_bcf[['Away_Havoc_Trap', 'Home_Havoc_Trap']].isna().any(axis=1)]
```

Printed PASS when: `len(missing_havoc_inputs) == 0 and len(missing_havoc_outputs) == 0`.

### OLD CELL 25

```text
duplicate_teams = int(df_def_lineyards.duplicated(subset=['team'], keep=False).sum())
missing_source_values = int(df_def_lineyards['Def_LineYards'].isna().sum())
missing_after_merge = int(df_cfbd['Def_LineYards'].isna().sum())
```

Printed PASS when: `duplicate_teams == 0 and missing_source_values == 0 and (missing_after_merge == 0)`.

### OLD CELL 26

```text
expected_games = len(df_target_market)
missing_home = int(df_master_bcf['Home_Def_LineYards'].isna().sum())
missing_away = int(df_master_bcf['Away_Def_LineYards'].isna().sum())
duplicate_games = int(df_master_bcf.duplicated(subset=['Home_Team', 'Away_Team'], keep=False).sum())
```

Printed PASS when: `len(df_master_bcf) == expected_games and missing_home == 0 and (missing_away == 0) and (duplicate_games == 0)`.

### OLD CELL 27

```text
missing_lineyards_inputs = df_master_bcf[df_master_bcf[['Away_Off_LineYards', 'Home_Def_LineYards', 'Home_Off_LineYards', 'Away_Def_LineYards']].isna().any(axis=1)]
missing_lineyards_outputs = df_master_bcf[df_master_bcf[['Away_LineYards_Push', 'Home_LineYards_Push']].isna().any(axis=1)]
```

Printed PASS when: `len(missing_lineyards_inputs) == 0 and len(missing_lineyards_outputs) == 0`.

### OLD CELL 28

```text
missing_fraud_inputs = df_master_bcf[df_master_bcf[['Away_Off_Explosiveness', 'Away_Off_SuccessRate', 'Home_Def_SuccessRate', 'Home_Off_Explosiveness', 'Home_Off_SuccessRate', 'Away_Def_SuccessRate']].isna().any(axis=1)]
missing_fraud_outputs = df_master_bcf[df_master_bcf[['Away_Explosiveness_Fraud', 'Home_Explosiveness_Fraud']].isna().any(axis=1)]
```

Printed PASS when: `len(missing_fraud_inputs) == 0 and len(missing_fraud_outputs) == 0`.

### OLD CELL 30

```text
missing_oay_day_inputs = df_master_bcf[df_master_bcf[['Away_OAY', 'Home_DAY', 'Home_OAY', 'Away_DAY']].isna().any(axis=1)]
missing_oay_day_outputs = df_master_bcf[df_master_bcf[['Away_OAY_DAY_Edge', 'Home_OAY_DAY_Edge']].isna().any(axis=1)]
```

Printed PASS when: `len(missing_oay_day_inputs) == 0 and len(missing_oay_day_outputs) == 0`.

### OLD CELL 31

```text
expected_games = len(df_master_bcf)
duplicate_games = int(df_module3_board.duplicated(subset=['Game'], keep=False).sum())
missing_required = int(df_module3_board[['Game', 'Away_Team', 'Home_Team', 'Away_Signal_Count', 'Home_Signal_Count', 'Total_Module3_Signals']].isna().any(axis=1).sum())
signal_count_errors = int((df_module3_board['Total_Module3_Signals'] != df_module3_board['Away_Signal_Count'] + df_module3_board['Home_Signal_Count']).sum())
```

Printed PASS when: `len(df_module3_board) == expected_games and duplicate_games == 0 and (missing_required == 0) and (signal_count_errors == 0)`.

### OLD CELL 34

```text
expected_games = len(df_master_bcf)
duplicate_games = int(df_convergence_corrected.duplicated(subset=['Game'], keep=False).sum())
missing_required = int(df_convergence_corrected[['Game', 'EPA_Team', 'EPA_Value', 'FEI_Team', 'FEI_Value', 'EPA_FEI_Agree', 'Shared_Side', 'M3_Support_Count', 'M3_Conflict_Count']].isna().any(axis=1).sum())
shared_side_errors = int((df_convergence_corrected['EPA_FEI_Agree'] & (df_convergence_corrected['Shared_Side'] == '')).sum())
```

Printed PASS when: `len(df_convergence_corrected) == expected_games and duplicate_games == 0 and (missing_required == 0) and (shared_side_errors == 0)`.

### OLD CELL 36

```text
expected_games = int(df_convergence_corrected['EPA_FEI_Agree'].sum())
duplicate_games = int(df_market_routes.duplicated(subset=['Game'], keep=False).sum())
missing_required = int(df_market_routes[['Game', 'Model_Side', 'EPA_Value', 'FEI_Value', 'Spread_Status', 'Eligible_Market_Routes', 'Final_Bet_Status']].isna().any(axis=1).sum())
blank_model_side = int((df_market_routes['Model_Side'] == '').sum())
```

Printed PASS when: `len(df_market_routes) == expected_games and duplicate_games == 0 and (missing_required == 0) and (blank_model_side == 0)`.

### OLD CELL 37

```text
missing_spread_inputs = df_master_bcf[df_master_bcf[['DK_Spread', 'FD_Spread']].isna().any(axis=1)]
missing_outputs = df_master_bcf[df_master_bcf[['Consensus_Spread', 'Consensus_Spread_Abs', 'Nearest_Key_Number', 'Distance_From_Key', 'Within_0.5_Key', 'Within_1.0_Key', 'Spread_Size_Bucket']].isna().any(axis=1)]
```

Printed PASS when: `len(missing_spread_inputs) == 0 and len(missing_outputs) == 0`.

### OLD CELL 38

```text
missing_inputs = df_master_bcf[df_master_bcf[['Consensus_Spread', 'Home_Team', 'Away_Team']].isna().any(axis=1)]
missing_outputs = df_master_bcf[df_master_bcf[['Consensus_Favorite', 'Favorite_Spread_Size', 'Large_Spread_16_5', 'Very_Large_Spread_20_5']].isna().any(axis=1)]
invalid_size = int((df_master_bcf['Favorite_Spread_Size'] < 0).sum())
```

Printed PASS when: `len(missing_inputs) == 0 and len(missing_outputs) == 0 and (invalid_size == 0)`.

### OLD CELL 39

```text
expected_games = len(df_market_routes)
duplicate_games = int(df_final_routes.duplicated(subset=['Game'], keep=False).sum())
missing_spread_size = int(df_final_routes['Favorite_Spread_Size'].isna().sum())
missing_required = int(df_final_routes[['Game', 'Model_Side', 'EPA_Value', 'FEI_Value', 'Favorite_Spread_Size', 'Spread_Status', 'Eligible_Market_Routes', 'Final_Bet_Status']].isna().any(axis=1).sum())
```

Printed PASS when: `len(df_final_routes) == expected_games and duplicate_games == 0 and (missing_spread_size == 0) and (missing_required == 0)`.

### OLD CELL 40

```text
expected_games = len(df_final_routes)
duplicate_games = int(df_evidence_routes.duplicated(subset=['Game'], keep=False).sum())
missing_required = int(df_evidence_routes[['Game', 'Model_Side', 'EPA_Value', 'FEI_Value', 'Evidence_Class', 'Evidence', 'Spread_Status', 'Eligible_Market_Routes', 'Final_Bet_Status']].isna().any(axis=1).sum())
blank_evidence = int((df_evidence_routes['Evidence'] == '').sum())
```

Printed PASS when: `len(df_evidence_routes) == expected_games and duplicate_games == 0 and (missing_required == 0) and (blank_evidence == 0)`.

### OLD CELL 41

```text
expected_agreement_games = len(df_evidence_routes)
duplicate_games = int(df_phase1_diagnostic.duplicated(subset=['Game'], keep=False).sum())
missing_required = int(df_phase1_diagnostic[['Game', 'Model_Side', 'EPA_Value', 'EPA_Top25', 'FEI_Value_Conservative', 'FEI_Top25', 'Dual_Top25', 'Evidence_Class', 'Phase1_Candidate']].isna().any(axis=1).sum())
```

Printed PASS when: `len(df_phase1_diagnostic) == expected_agreement_games and duplicate_games == 0 and (missing_required == 0)`.

### OLD CELL 42

```text
expected_games = len(candidate_board)
duplicate_games = int(df_phase1_review.duplicated(subset=['Game'], keep=False).sum())
missing_required = int(df_phase1_review[['Game', 'Model_Side', 'EPA_Value', 'FEI_Value_Conservative', 'Evidence_Class', 'Review_Class', 'Phase1_Reason', 'Late_Week_Action']].isna().any(axis=1).sum())
unclassified_games = int((df_phase1_review['Review_Class'] == 'UNCLASSIFIED').sum())
```

Printed PASS when: `len(df_phase1_review) == expected_games and duplicate_games == 0 and (missing_required == 0) and (unclassified_games == 0)`.

### OLD CELL 43

```text
expected_games = set(df_phase1_review['Game'])
missing_games = sorted(expected_games - covers_games)
duplicate_games = int(df_covers.duplicated(subset=['Game'], keep=False).sum())
missing_spread_data = int(df_covers[['Open_Home_Spread', 'Current_Home_Spread']].isna().any(axis=1).sum())
```

Printed PASS when: `len(df_covers) == len(expected_games) and len(missing_games) == 0 and (len(extra_games) == 0) and (duplicate_games == 0) and (missing_spread_data == 0)`.

Printed PASS when: `len(covers_audit) == len(df_phase1_review) and audit_missing == 0`.

### OLD CELL 44

```text
expected_games = len(df_phase1_review)
duplicate_games = int(df_final_decision.duplicated(subset=['Game'], keep=False).sum())
missing_required = int(df_final_decision[['Game', 'Model_Side', 'Review_Class', 'Phase1_Reason', 'Favorite_Spread_Size', 'Spread_Status', 'Open_Home_Spread', 'Current_Home_Spread', 'Movement_Toward', 'Movement_Size', 'Movement_Class', 'Market_Relationship', 'Decision_Status', 'Decision_Note']].isna().any(axis=1).sum())
unclassified_games = int((df_final_decision['Decision_Status'] == 'UNCLASSIFIED').sum())
```

Printed PASS when: `len(df_final_decision) == expected_games and duplicate_games == 0 and (missing_required == 0) and (unclassified_games == 0)`.

### OLD CELL 45

```text
expected_games = len(df_final_decision)
duplicate_games = int(df_gem_export['Game'].duplicated().sum())
missing_status = int((df_gem_export['Decision_Status'] == '').sum())
missing_model_side = int((df_gem_export['Model_Side'] == '').sum())
```

Printed PASS when: `len(df_gem_export) == expected_games and duplicate_games == 0 and (missing_status == 0) and (missing_model_side == 0)`.

### CELL 47

```text
required_cols = ['Home_Team', 'Away_Team', 'Net_EPA_Edge_Home', 'FEI_Model_Home_Spread', 'DK_Spread', 'FD_Spread']
missing_cols = [col for col in required_cols if col not in df_master_bcf.columns]
```

Hard stop when: `missing_cols`.

### CELL 48

Hard stop when: `'df_phase1_shrinkage' not in globals()`.

Hard stop when: `'df_final_decision' not in globals()`.

### CELL 51

Hard stop when: `response.status_code != 200`.

### CELL 52

Hard stop when: `'df_hist_spread' not in globals()`.

Hard stop when: `'df_key_value' not in globals()`.

### CELL 55

Hard stop when: `'df_auto_pricing' not in globals()`.

Hard stop when: `'df_key_value' not in globals()`.

Hard stop when: `'df_hist_spread' not in globals()`.

### CELL 56

Hard stop when: `'df_hist_spread' not in globals()`.

### CELL 57

```text
required_cols = ['Game', 'Team', 'Sportsbook', 'Line', 'American_Odds', 'Candidate_Cushion']
prob_sum = df_ev['CFB1_Win_Prob'] + df_ev['CFB1_Push_Prob'] + df_ev['CFB1_Loss_Prob']
prob_errors = (~np.isclose(prob_sum, 1.0, atol=1e-09)).sum()
```

Hard stop when: `'df_spread_shortlist' not in globals()`.

Hard stop when: `missing`.

Hard stop when: `'global_errors' not in globals()`.

Hard stop when: `prob_errors != 0`.

Hard stop when: `legacy_remaining`.

Hard stop when: `'Home_Team' not in row.index`.

### CELL 57A

```text
required_objects = ['df_ev', 'df_hist_spread']
prob_sum = df_ev['Push_Adjusted_Win_Prob'] + df_ev['Push_Adjusted_Push_Prob'] + df_ev['Push_Adjusted_Loss_Prob']
prob_errors = (~np.isclose(prob_sum, 1.0, atol=1e-09)).sum()
```

Hard stop when: `prob_errors != 0`.

Hard stop when: `legacy_remaining`.

Hard stop when: `obj not in globals()`.

Hard stop when: `'Closing_Home_Spread' not in df_hist_spread.columns`.

Hard stop when: `'Actual_Home_Margin' not in df_hist_spread.columns`.

### CELL 58

Hard stop when: `response.status_code != 200`.

### OLD CELL 59

```text
required_objects = ['df_auto_pricing', 'df_key_value', 'df_hist_team_total']
duplicate_routes = int(df_tt_routes.duplicated(subset=['Game', 'TT_Target_Team', 'TT_Direction']).sum())
missing_model = df_tt_routes[df_tt_routes['Model_Side'].isna()].copy()
```

Hard stop when: `duplicate_routes > 0`.

Hard stop when: `len(missing_model) > 0`.

Hard stop when: `len(bad_routes) > 0`.

Hard stop when: `obj not in globals()`.

### CELL 59A

```text
required_objects = ['df_tt_shortlist', 'df_hist_team_total']
prob_sum = supported['TT_Final_Win_Prob'] + supported['TT_Final_Push_Prob'] + supported['TT_Final_Loss_Prob']
```

Hard stop when: `obj not in globals()`.

### CELL 60

```text
prob_sum = df_tt_ev['TT_Final_Win_Prob'] + df_tt_ev['TT_Final_Push_Prob'] + df_tt_ev['TT_Final_Loss_Prob']
prob_errors = (np.abs(prob_sum - 1) > 1e-09).sum()
```

Hard stop when: `'df_tt_validated' not in globals()`.

Hard stop when: `prob_errors != 0`.

Hard stop when: `legacy_remaining`.

### CELL 61

```text
required_objects = ['df_ev', 'df_tt_ev', 'df_tt_validated']
required_spread_cols = ['Push_Adjusted_Win_Prob', 'Push_Adjusted_Push_Prob', 'Push_Adjusted_ROI', 'Break_Even_Prob']
missing_spread_cols = [col for col in required_spread_cols if col not in df_ev.columns]
missing_game_names = df_cfb1_gem_handoff['Game'].isna().sum()
```

Hard stop when: `missing_spread_cols`.

Hard stop when: `missing_game_names != 0`.

Hard stop when: `legacy_columns`.

Hard stop when: `obj not in globals()`.

### CELL 62

```text
required_objects = ['df_ev', 'df_tt_ev', 'df_tt_validated', 'CFB1_FULL_CONTEXT_V1']
required_spread_cols = ['Push_Adjusted_Win_Prob', 'Push_Adjusted_Push_Prob', 'Push_Adjusted_ROI']
missing_cols = [c for c in required_spread_cols if c not in df_ev.columns]
```

Hard stop when: `missing_cols`.

Hard stop when: `legacy_columns`.

Hard stop when: `obj not in globals()`.

### CELL 66

```text
required_objects = ['df_gem_export', 'df_phase1_shrinkage', 'df_key_value', 'CFB1_FULL_CONTEXT_V1', 'CFB1_DECISION_CARD_V1']
missing_pricing_games = game_context[~game_context['Game'].isin(priced_games)].copy()
```

Hard stop when: `obj not in globals()`.

### CELL 67

```text
required_objects = ['CFB1_FULL_CONTEXT_V2', 'CFB1_DECISION_CARD_V1', 'df_ev']
missing_57a = [c for c in spread_fix_cols if c not in df_ev.columns]
sync_columns = ['Model_Adjustment_Match', 'Probability_Match', 'Push_Probability_Match', 'Break_Even_Match', 'ROI_Match']
all_synced = check[sync_columns].all().all()
```

Hard stop when: `missing_57a`.

Hard stop when: `dupes.any()`.

Hard stop when: `not all_synced`.

Hard stop when: `legacy_final_columns`.

Hard stop when: `legacy_card_columns`.

Hard stop when: `obj not in globals()`.

### CELL 73

```text
required_objects = ['CFB1_DECISION_CARD_V1', 'CFB1_FULL_CONTEXT_FINAL']
qualitative_quant_errors = 0
required_handoff_cols = ['Game', 'Market_Family', 'Card_Role', 'Team', 'Direction', 'Bet_Label', 'Sportsbook', 'Line', 'American_Odds', 'Model_Probability', 'Push_Probability', 'Break_Even_Prob', 'Expected_ROI', 'Model_Status', 'Decision_Status', 'Warning', 'Eligible_Market_Routes']
missing_handoff_cols = [col for col in required_handoff_cols if col not in CFB1_ARCHITECT_HANDOFF.columns]
```

Hard stop when: `qualitative_quant_errors != 0`.

Hard stop when: `legacy_columns`.

Hard stop when: `missing_handoff_cols`.

Hard stop when: `obj not in globals()`.
