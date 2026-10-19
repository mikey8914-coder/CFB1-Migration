# CFB1 Market Data Contract

## Scope and evidence

Static inspection of `legacy/CFB1_Colab_Reference.ipynb`, SHA-256 `94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`. The notebook was neither changed nor executed. All references use original embedded cell labels. This document distinguishes the **literal legacy interface**, the **core calculations' semantic needs**, and a **proposed normalized interface**. A proposed field name or adapter is not implemented or validated.

The core weekly path here means configuration/acquisition through OLD CELL 45, plus the retained/blended model-line calculations in CELL 47 and CELL 48 where relevant. Football probability calibration remains CFB1 responsibility; all supplied-price expected ROI and other wager economics now belong to Universal Bet Slip Architect. Team totals remain experimental. CFBD/BCF statistical features and general model outputs are described in BEHAVIOR_LOCK.md; they are not market-provider input columns.

Column types below are inferred from source, not enforced runtime schemas. pandas can infer float, integer, object, nullable, or missing values depending on payload contents. **Required** distinguishes schema presence, nonnull use in calculations, optional context, and branch-specific requirements. First consumer means the first *later cell* reading that field; same-cell calculations/validation are noted where no later reader exists. Whole-table copies retain fields even when no calculation reads them.

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

## Reading the historical column catalogs

The object, column, consumer, guard, and removal tables below describe the **legacy notebook**, including branches now owned by Architect. “Required” in those catalogs means required by that historical branch, not required by new production CFB1. Proposed football-market input and handoff requirements are separately marked. Preserve football probability/push fields while excluding price-dependent requirements.

## Legacy objects and lineage

| Original label | Exact object names | Role and downstream contract |
| --- | --- | --- |
| Unnumbered weekly configuration | ODDS_API_KEY; YEAR; TARGET_WEEK; DATA_THROUGH_WEEK; TARGET_START_DATE; TARGET_END_DATE | Both CFBD and Odds API keys are required by the legacy printed startup PASS. That provider requirement is not future permanent architecture. Dates constrain the returned market card. |
| CELL 4 | odds_url; odds_params; odds_res; odds_json | requests response and parsed event-list payload; non-200 sets odds_json to an empty list. Request markets are `spreads,totals`, region `us`, bookmakers `draftkings,fanduel`. |
| CELL 4 | dk_games; fd_games; bookmaker_keys | Bookmaker availability counts/list; reports only, not eligibility gates. HTTP 200 and nonempty odds_json produce printed PASS. |
| CELL 5 | games_list; df_market | Flattened list of game dictionaries and full market DataFrame with the nine raw columns below. Variables home/away, kickoff_utc/kickoff_et, dk_spread/fd_spread/dk_total/fd_total are row-building temporaries. |
| CELL 5 | required_columns; missing_columns; duplicate_games; missing_dk_spreads; missing_fd_spreads; missing_dk_totals; missing_fd_totals | Validation/report objects, not model inputs. PASS checks columns, duplicates, nonempty card, **not zero missing lines/totals**. Names may be reassigned in later cells. |
| CELL 6 | target_start; target_end; df_target_market; outside_date_window | Inclusive Eastern-date filter, sorted Kickoff_ET/Away_Team/Home_Team with index reset. Raw fields remain present. |
| CELL 10 | TEAM_ALIASES; normalize_team_name; cfbd_teams; home_unmatched; away_unmatched; total_unmatched | Normalize team keys; enrich df_target_market with canonical-name and matched flags. |
| CELL 11 | home_cfbd; away_cfbd; df_master | Left many-to-one canonical-team merges of target market and CFBD; market fields are carried into the game master. |
| CELL 13 / CELL 14 / OLD CELL 19 | df_bcf_raw; BCF_TO_CFBD; df_bcf; bcf_home; bcf_away; df_master_bcf | Independent BCF name mapping and home/away statistical merge; existing market fields are retained. |
| OLD CELL 37 / OLD CELL 38 | df_routed_market_structure; df_large_spread_routed; enriched df_master_bcf | Derived spread structure/favorite/size views. |
| OLD CELL 36 / OLD CELL 39 / OLD CELL 40 | df_market_routes; market_route_lookup; routing_base; df_final_routes; df_evidence_routes | Game-keyed routing with spread-size-derived modifiers. These are computed tables, not manual provider outputs. |
| OLD CELL 41 / OLD CELL 42 | df_phase1_diagnostic; candidate_board; df_phase1_review | Game-keyed candidates/review board dependent on spread-based FEI edges and full-slate percentiles. |
| OLD CELL 43 | covers_csv; df_covers; covers_audit | Separate pasted opener/current-spread audit; not a refresh of df_master_bcf's initial DK/FD fields. |
| OLD CELL 44 / OLD CELL 45 | df_final_decision; df_gem_export; gem_csv | Final review/route/audit merge and compact context export. |
| CELL 47 / CELL 48 / CELL 52 | df_prob_model; df_phase1_shrinkage; df_key_value; df_cover_prob | Market-calibrated retained lines and empirical cover diagnostics. |
| CELL 53 / CELL 54 | df_odds_events; df_event_match; df_market_discovery; df_market_request_log; df_auto_pricing; df_pricing_pull_log; df_full_game_spreads; df_team_total_prices; df_first_half_prices | Separate legacy exact-price acquisition and quota logs, not created by CELL 4 or CELL 5. |
| CELL 46 | pricing_csv; df_pricing; df_pricing_valid | Manual offer validation branch. Its output is not automatically wired into df_auto_pricing consumers. |
| CELL 55 / CELL 57 / CELL 57A | spread_prices; df_spread_shortlist; df_ev | Supplied-offer shortlist, W/P/L, break-even, ROI, and canonical push-adjusted spread metrics. |
| CELL 58 / OLD CELL 59 / CELL 59A / CELL 60 | df_hist_team_total; df_tt_routes; df_tt_anchors; df_tt_shortlist; df_tt_validated; df_tt_ev | Experimental historical calibration and offered-price team-total outputs. |
| CELL 61 / CELL 61B / CELL 62 / CELL 66 / CELL 67 / CELL 73 | df_cfb1_gem_handoff; df_cfb1_gem_review; CFB1_FULL_CONTEXT_V1; CFB1_DECISION_CARD_V1; CFB1_FULL_CONTEXT_V2; CFB1_FULL_CONTEXT_FINAL; CFB1_ARCHITECT_HANDOFF | Distinct downstream views; rich context retains original market fields, while priced rows retain offer identity. CSV variants and archive/download side effects do not add acquisition requirements. |

CELL 5 reads only event `home_team`, `away_team`, `commence_time`, bookmaker `key`, market `key`, outcome `name`, and outcome `point`. It does **not** preserve the Odds API event `id`, outcome `price`, bookmaker/market timestamps, or request-time provenance in df_market. If multiple matching outcomes overwrite a row temporary, the last visited matching value wins; no consensus or best-price selection occurs during flattening.

## Raw market and normalization column catalog

CELL 5 creates columns in the order shown; CELL 6 lists every column except Kickoff_UTC as required. Raw home/away names remain provider display labels, separate from canonical merge names.

| Exact column | Meaning / inferred type | Sign or orientation | Required versus optional | Created by → first later consumer |
| --- | --- | --- | --- | --- |
| Home_Team | Raw event home team; string/object | Home identity, not favorite | Legacy schema + identity required | CELL 5 → CELL 6 sort/duplicate checks; CELL 10 normalization |
| Away_Team | Raw event away team; string/object | Away identity, not underdog | Legacy schema + identity required | CELL 5 → CELL 6 sort/duplicate checks; CELL 10 normalization |
| Kickoff_UTC | pd.to_datetime(commence_time, utc=True); timezone-aware Timestamp, usually datetime64[ns, UTC] | UTC scheduled kickoff | CELL 5 schema required; no later direct calculation reads it | CELL 5 → carried through copies; no later explicit column reader |
| Kickoff_ET | Kickoff_UTC.tz_convert('America/New_York'); timezone-aware Timestamp | Eastern zone, including daylight-saving conversion | Legacy target filtering/sort/display contract required | CELL 5 → CELL 6; CELL 66 optional context selection |
| Game_Date_ET | Kickoff_ET.date(); Python date, typically pandas object | Eastern calendar date | Required for target-slate membership | CELL 5 → CELL 6 inclusive filter/report |
| DK_Spread | DraftKings home outcome point; number, often float with NaN if absent | **Home spread**: negative home favorite, positive home underdog, zero pick'em | Schema required; nonnull required by later FEI/key gates | CELL 5 → CELL 6 checks/display; CELL 11/CELL 12 display; OLD CELL 21 first FEI arithmetic |
| FD_Spread | FanDuel home outcome point; number, often float with NaN | Same home-spread perspective | Schema required; nonnull required by later FEI/key gates | CELL 5 → CELL 6 checks/display; OLD CELL 21 first FEI arithmetic |
| DK_Total | DraftKings totals outcome named Over, using point; number/nullable | Full-game combined point threshold; no team-side sign | Legacy schema required; missing-value report only, no current core numeric total gate | CELL 5 → CELL 6 checks/display; CELL 66 optional context selection |
| FD_Total | FanDuel totals Over point; number/nullable | Full-game combined total, not implied team total | Same as DK_Total | CELL 5 → CELL 6 checks/display; CELL 66 optional context selection |
| Home_CFBD_Name | Canonical home team alias; string | Home identity retained | Required merge key | CELL 10 → CELL 11; CELL 14 coverage; OLD CELL 19/OLD CELL 26 merges |
| Away_CFBD_Name | Canonical away team alias; string | Away identity retained | Required merge key | CELL 10 → CELL 11; CELL 14 coverage; OLD CELL 19/OLD CELL 26 merges |
| Home_CFBD_Matched | Canonical home name belongs to CFBD team set; bool | N/A | Generated validation flag; not provider-supplied | CELL 10 same-cell unmatched gate; carried later, no direct later flag reader |
| Away_CFBD_Matched | Canonical away name belongs to CFBD team set; bool | N/A | Generated validation flag; not provider-supplied | CELL 10 same-cell unmatched gate; carried later, no direct later flag reader |
| Game | Raw Away_Team + ' at ' + Home_Team; string | Oriented away-at-home matchup | Required later table join/display key; **not created in CELL 5** | OLD CELL 24 diagnostic rows → OLD CELL 27/OLD CELL 28/OLD CELL 30 each independently build it; persistent core boards OLD CELL 31 and OLD CELL 34; OLD CELL 36 first consumes convergence Game |

No current-total consensus is calculated from DK_Total/FD_Total. Extracting Over.point discards the Over/Under price and direction; it stores a total threshold, not an Over recommendation. No current full-game-total signal is calculated from these two columns in the inspected core path. Keep game total in the planned input contract per the migration decisions, while distinguishing that requirement from actual current arithmetic usage.

## Spread perspective and market-derived core columns

A home spread of **−7** means home is favored by 7; **+7** means home is the underdog by 7. Away spread would be the negation, but CELL 5 stores neither away-book spread column. Zero is PICKEM for market favorites. Model home **margin** uses the opposite sign: positive means home stronger. FEI_Model_Home_Spread negates FEI home differential. Edge_Home = market home spread − model home spread; positive edge favors home, negative favors away.

Columns below are **computed downstream**, not additional fields a market source must provide. Where no later reader exists, same-cell validation/display still consumes them. Numeric means points except probability/count flags noted separately.

| Exact column | Meaning / inferred type / sign | Required or optional | Producer → first later consumer |
| --- | --- | --- | --- |
| FEI_Model_Home_Spread | Negative FEI home differential, rounded 1 decimal; float; home spread | Required model-derived baseline, not acquisition input | OLD CELL 21 → OLD CELL 23 display; CELL 47 arithmetic |
| DK_FEI_Edge_Home | round(DK_Spread−FEI_Model_Home_Spread,1); signed float; +home edge | Core derived | OLD CELL 21 → carried master; later context via related values; same-cell edge-side calculation |
| FD_FEI_Edge_Home | round(FD_Spread−FEI_Model_Home_Spread,1); signed float; +home edge | Core derived | OLD CELL 21 → carried master; same-cell edge-side calculation |
| DK_FEI_Edge_Value | abs(DK_FEI_Edge_Home); nonnegative number | Core derived | OLD CELL 21 → OLD CELL 23 display; OLD CELL 34 value; OLD CELL 41 percentile |
| FD_FEI_Edge_Value | abs(FD_FEI_Edge_Home); nonnegative number | Core derived | OLD CELL 21 → OLD CELL 41 conservative edge |
| DK_FEI_Edge_Team | Home/Away/EVEN according to DK home edge; string | Required by convergence, specifically DK | OLD CELL 21 → OLD CELL 23 display; OLD CELL 34 convergence |
| FD_FEI_Edge_Team | Home/Away/EVEN according to FD home edge; string | Related audit; used same-cell book agreement | OLD CELL 21 → copied master; no later independent core selection |
| FEI_Books_Agree | DK edge-team equals FD edge-team; bool | Audit derived | OLD CELL 21 same-cell counts; no later core branch |
| DK_Market_Favorite | Negative DK home spread→home, positive→away, zero PICKEM; string | Favorite audit | OLD CELL 23 same-cell comparison/display; no later required branch |
| FD_Market_Favorite | Same favorite rule for FD; string | Favorite audit | OLD CELL 23 same-cell comparison/display; no later required branch |
| DK_FEI_Market_Agree | FEI favorite equals DK market favorite; bool | Favorite audit | OLD CELL 23 same-cell counts; no later required branch |
| FD_FEI_Market_Agree | FEI favorite equals FD market favorite; bool | Favorite audit | OLD CELL 23 same-cell counts; no later required branch |
| Consensus_Spread | round((DK_Spread+FD_Spread)/2,2); float; home spread | Core derived | OLD CELL 37 → OLD CELL 38 |
| Consensus_Spread_Abs | abs(Consensus_Spread); nonnegative float | Core derived | OLD CELL 37 same-cell key/bucket math; carried master |
| Nearest_Key_Number | nearest magnitude in [3,7,10,14]; numeric | Core derived | OLD CELL 37 → OLD CELL 38 display; CELL 66 context |
| Distance_From_Key | distance to nearest magnitude, rounded 2 decimals; nonnegative float | Core derived | OLD CELL 37 → OLD CELL 38 display; CELL 66 context |
| Within_0.5_Key | Distance_From_Key≤0.5; bool | Derived context | OLD CELL 37 → CELL 66 optional context |
| Within_1.0_Key | Distance_From_Key≤1.0; bool | Derived context | OLD CELL 37 → CELL 66 optional context |
| Spread_Size_Bucket | magnitude buckets at <3,<7,<10,<14,<17,<21,otherwise; string | Derived structure/context | OLD CELL 37 → CELL 66 optional context; same-cell routed view |
| Consensus_Favorite | Negative consensus→home, positive→away, zero PICKEM; string | Derived favorite/context | OLD CELL 38 same-cell routed view; no later explicit core reader |
| Favorite_Spread_Size | abs(consensus), zero for pick'em; nonnegative float | Routing required | OLD CELL 38 → OLD CELL 39 |
| Large_Spread_16_5 | Favorite_Spread_Size≥16.5; bool | Derived flag | OLD CELL 38 same-cell validation; later routing recomputes via size |
| Very_Large_Spread_20_5 | Favorite_Spread_Size≥20.5; bool | Derived flag | OLD CELL 38 same-cell validation; later routing recomputes via size |
| Spread_Class | VERY_LARGE_20.5_PLUS/LARGE_16.5_TO_20/BELOW_16.5; string | Routed display only | OLD CELL 38 same-cell view; no later direct reader |
| Spread_Status | Ordered support/conflict/large-size routing status; string | Required routing/final decision | OLD CELL 36 → OLD CELL 39 |
| Eligible_Market_Routes | Ordered comma-space route list; string | Required routing/final decision/pricing eligibility | OLD CELL 36 → OLD CELL 37 routed-view selection |
| Final_Bet_Status | UNPRICED — DO NOT BET YET; string | Legacy board field, not price input | OLD CELL 36 → OLD CELL 39/OLD CELL 40 reconstruct same literal; same-cell validation |
| Routing_Modifiers | Large-spread/downgrade context distinct from evidence; string | Core computed context | OLD CELL 40 same-cell audit; later core selection uses Evidence_Class |
| FEI_Edge_Conservative | Row minimum DK/FD absolute FEI edge; nonnegative number | Phase 1 required | OLD CELL 41 → CELL 66 optional retained context; same-cell quantiles |
| Consensus_Home_Spread | Row mean DK/FD spreads, unrounded here; float; home spread | Retained-line required | CELL 47 → CELL 66 context; same-cell blend |
| Market_Home_Margin | −Consensus_Home_Spread; float; +home expected margin | Retained-line required | CELL 47 → CELL 66 context; same-cell EPA fit |
| EPA_Model_Home_Margin | Intercept+beta×Net_EPA_Edge_Home fitted to market; float; +home stronger | Retained-line required | CELL 47 → CELL 66 context; same-cell blend |
| EPA_Model_Home_Spread | Negative EPA model home margin; float; home spread | Derived | CELL 47 → CELL 66 context |
| FEI_Model_Home_Margin | Negative FEI_Model_Home_Spread; float; +home stronger | Derived | CELL 47 → CELL 66 context |
| Blended_Home_Margin_Raw | 0.5 EPA margin+0.5 FEI margin; float; +home stronger | Retained-line required | CELL 47 → CELL 66 context; same-cell retained calculations |
| Blended_Home_Spread_Raw | Negative raw blended home margin; float; home spread | Retained-line required | CELL 47 → CELL 66 context |
| Blended_Edge_Home_Raw | consensus home spread−raw blended home spread; signed float | Retained-line required | CELL 47 → CELL 66 context; same-cell retention |
| Edge_Retained_25 | Raw blended edge×0.25; signed float | Diagnostic variant | CELL 47 same-cell; no later reader |
| Edge_Retained_40 | Raw blended edge×0.40; signed float | Retained-model variant | CELL 47 → CELL 66 context; same-cell retained spread |
| Edge_Retained_50 | Raw blended edge×0.50; signed float | Diagnostic variant | CELL 47 same-cell; no later reader |
| Edge_Retained_60 | Raw blended edge×0.60; signed float | Diagnostic variant | CELL 47 same-cell; no later reader |
| Shrunk_Home_Spread_25 | consensus−Edge_Retained_25; float; home spread | Diagnostic variant | CELL 47 same-cell display; no later reader |
| Shrunk_Home_Spread_40 | consensus−Edge_Retained_40; float; home spread | Retained-line required | CELL 47 → CELL 48 |
| Shrunk_Home_Spread_50 | consensus−Edge_Retained_50; float; home spread | Diagnostic variant | CELL 47 same-cell display; no later reader |
| Shrunk_Home_Spread_60 | consensus−Edge_Retained_60; float; home spread | Diagnostic variant | CELL 47 same-cell display; no later reader |
| Raw_Edge_Size | abs(Blended_Edge_Home_Raw); nonnegative float | Diagnostic/context | CELL 47 → CELL 66 optional context |
| Market_Model_Spread | Covers Current_Home_Spread for home Model_Side, negated for away; float | Retained-line/probability required | CELL 48 → CELL 52 |
| Retained_Model_Spread | Shrunk_Home_Spread_40 in selected team's perspective; float | Football probability required; historical ROI context | CELL 48 → CELL 52 |
| Model_Cushion_Points | round(Market_Model_Spread−Retained_Model_Spread,2); float; positive line value | Probability required | CELL 48 → CELL 52 |
| Keys_Between_Market_And_Model | sorted unique magnitudes of strictly intervening signed keys; string, empty allowed | Key diagnostic/context | CELL 48 → CELL 66 context |
| Key_Barrier_Present | nonempty keys-between; bool | Derived diagnostic | CELL 48 → CELL 66 context |
| Next_Adverse_Key | first key magnitude above favorite market magnitude; number/NaN | Optional favorite-only context | CELL 48 → CELL 66 context |
| Line_Value_Status | CHECK/NO_RETAINED_MODEL_EDGE/EDGE_WITH_KEY_BARRIER/EDGE_NO_KEY_BARRIER; string | Derived context | CELL 48 → CELL 52 |
| Key_Tradeoff_Note | explanatory line/key text; string | Context | CELL 48 → CELL 66 |

Legacy dual-spread roles are consequential: convergence uses **DK** FEI direction; Phase 1 uses **min(DK edge, FD edge)**; key structure uses their mean; CELL 47 fits/blends against their mean. A single replacement quote cannot reproduce two unequal book quotes without an intentional and validated compatibility decision. Do not populate fake DraftKings/FanDuel values or silently clone one new quote into both columns and claim exact parity.

## Covers fields that meet the core market contract

OLD CELL 43's pasted header contains all 13 fields below. Only home-spread fields are explicitly numerically coerced; read_csv infers other numeric dtypes. Text/object columns are stripped. It does not merge back into df_master_bcf or replace initial DK/FD snapshot lines.

| Exact column | Meaning / inferred type / sign | Requirement | First later consumer |
| --- | --- | --- | --- |
| Game | Exact raw away-at-home string; string | Required one-to-one review identity | OLD CELL 44 joins; OLD CELL 43 intake/merge first |
| Away_Team | Raw away display name; string | Required by movement-side function | No direct later reader of df_covers; carried through covers_audit |
| Home_Team | Raw home display name; string | Required by movement-side function | No direct later reader of df_covers; carried through covers_audit |
| Open_Home_Spread | Opening home line; numeric after coercion; negative home favorite | **Required nonnull for final-decision parity** | OLD CELL 44; OLD CELL 43 movement/key calculations first |
| Current_Home_Spread | Later home line; numeric after coercion; negative home favorite | **Required nonnull for final decision and retained-line comparison** | OLD CELL 44; CELL 48 uses it later |
| Open_Total | Opening combined total; inferred number/nullable; unsigned threshold | Unused optional pasted field | No later direct reader |
| Current_Total | Later combined total; inferred number/nullable | Unused optional pasted field; **does not update DK_Total/FD_Total** | No later direct reader |
| Open_Home_Price | Home opener juice; inferred number/object/nullable; American odds intended, no conversion contract | Unused optional pasted field | No later direct reader |
| Current_Home_Price | Home current juice; inferred number/object/nullable | Unused optional pasted field | No later direct reader |
| Open_Away_Price | Away opener juice; inferred number/object/nullable | Unused optional pasted field | No later direct reader |
| Current_Away_Price | Away current juice; inferred number/object/nullable | Unused optional pasted field | No later direct reader |
| Source | Pasted provenance label; string | Optional trace context; no acquisition routing based on it | No later direct reader |
| Data_Status | Pasted quality/status label; string | Optional; not a quality eligibility gate | No later direct reader |

Derived Covers fields are created in OLD CELL 43 and first consumed later by OLD CELL 44 (unless noted):

| Exact column | Meaning / type / sign | Requirement |
| --- | --- | --- |
| Spread_Move | round(Current_Home_Spread−Open_Home_Spread,2); signed float | Required to derive movement; not directly exported into OLD CELL 44 |
| Movement_Toward | Negative move→Home_Team, positive→Away_Team, zero NONE; string | Required final classification/context |
| Market_Relationship | NONE→NEUTRAL; toward Model_Side→CONFIRMS_MODEL; otherwise CONFLICTS_WITH_MODEL; string | Required final classification |
| Key_Numbers_Crossed | Strictly crossed signed keys converted to sorted unique absolute magnitudes; comma string | Required final context; CELL 67 converts empty to NONE |
| Key_Cross | Key_Numbers_Crossed != ''; bool | Required final conflict-strength branch |
| Movement_Size | abs(Spread_Move); float ≥0 | Required context; informs movement class |
| Movement_Class | 0 NO_MOVE; <1 SMALL; <2 MODERATE; otherwise MAJOR; string | Required final conflict-strength branch |
| Late_Market_Movement | Toward=…; Class=… string assembled in CELL 66 | Optional rich context; CELL 66 validation/display first; not an acquisition input |

Opener fields are optional for initial EPA/FEI/Module 3/routing/Phase 1 generation, but **Open_Home_Spread is not optional if preserving OLD CELL 43/OLD CELL 44 final decisions**. Setting opener equal to current or omitting it would manufacture neutral movement or break the audit. No Open_Total or opener-price field is needed for those decisions.

## Normalization and join keys

1. **CELL 6:** select target dates inclusively using Game_Date_ET. Sort Kickoff_ET, Away_Team, Home_Team. The notebook does not filter on a returned API week number, compare to all scheduled CFBD games, or apply an FBS classification gate here.
2. **CELL 10:** collapse whitespace, strip, apply exact TEAM_ALIASES mapping, and leave unmatched cleaned names unchanged. No fuzzy matching, case folding, or general mascot stripping. Compare canonical names with the stripped, nonnull df_cfbd.team set. Preserve raw labels for displays and Game strings. Examples: Appalachian State Mountaineers→App State; Hawaii Rainbow Warriors→Hawai'i; San Jose State Spartans→San José State; UConn Huskies→UConn.
3. **CELL 11:** rename the CFBD team key separately to Home_CFBD_Name/Away_CFBD_Name; two left `many_to_one` joins. Market membership defines the model slate. No Odds API event ID is used.
4. **CELL 14 / OLD CELL 19:** BCF canonical Team key is CFBD_Team; BCF aliases differ from market aliases. OLD CELL 19 renames to home/away canonical keys and left-merges each side `many_to_one`. OLD CELL 26 refreshes defensive line yards using the same canonical keys.
5. **Later boards:** construct Game from raw market Away_Team + ' at ' + Home_Team. OLD CELL 39 maps spread size via Game with `one_to_one`; OLD CELL 43 joins audit to review with `one_to_one`; OLD CELL 44 joins review/routes/audit by Game with `one_to_one`. CELL 47 likewise uses raw away-at-home text to join review; CELL 48 joins final decisions by Game `one_to_one`. No normalized event-level ID is shared across these tables.
6. **CELL 53:** match Odds API event Game to model Game using exact string equality, `one_to_one`; it does not call CELL 10 normalization on event names. A new provider's display labels therefore cannot simply replace raw names without preserving an explicit matchup-key/display compatibility mapping.
7. **Pricing:** Game joins supplied offers to model context; TT routes also use Team and Bet_Direction. CELL 67 synchronization requires the exact priced-row key **Game, Team, Sportsbook, Line, American_Odds**. Game-only identity is insufficient for offers at alternate lines/prices.

The legacy matchup key has no season, scheduled date, or event ID. It is only safe under the notebook's current-week/single-matchup uniqueness assumptions. A stable migrated identifier should include canonical team identity and season/event identity, with kickoff or another discriminator for repeated matchups. Do not equate that new identifier with the legacy Game display string without an explicit mapping.

## Every later direct consumer of market-derived data

“Direct” includes arithmetic, branching, joins, column selection, validation, and exports; inherited whole-table copying alone is distinguished. Core CFBD/BCF features themselves are not supplied by the market source.

| Original label | Direct use and effect |
| --- | --- |
| CELL 6 | Raw dates, kickoff ordering, names, DK/FD spread/total schema checks and missing-value reporting. |
| CELL 10 | Raw names→canonical keys and matched flags. |
| CELL 11 | Canonical merge keys; raw name duplicate checks; spread columns in display. |
| CELL 12 | Raw names choose EPA side; DK/FD spreads only in display, not EPA trigger arithmetic. |
| CELL 14 | Target canonical names define required BCF coverage. |
| OLD CELL 19 | Canonical BCF joins; raw name duplicate checks. |
| OLD CELL 20 | Raw names select FEI favorite; no market line in FEI differential formula. |
| OLD CELL 21 | Both book home spreads determine FEI edge values/teams and book agreement. |
| OLD CELL 23 | Book spreads determine market favorites; compare to FEI favorite. |
| OLD CELL 24 | Raw matchup/team labels identify havoc diagnostic rows; no market-price calculation. |
| OLD CELL 26 | Canonical names refresh defensive line yards; preserves market rows and checks raw pairs. |
| OLD CELL 27 / OLD CELL 28 / OLD CELL 30 | Raw names and Game identify signal diagnostic rows; thresholds use CFBD/BCF metrics, not price/juice. |
| OLD CELL 31 | Game/name labels for signal board and validation; no direct spread arithmetic. |
| OLD CELL 34 | DK_FEI_Edge_Team/Value plus EPA side and matchup labels drive convergence. |
| OLD CELL 36 | Game and convergence side/value/support/conflict define route rows/status. |
| OLD CELL 37 | DK/FD spreads→consensus, key proximity, buckets; route Game membership determines view. |
| OLD CELL 38 | Consensus spread→favorite/size/large flags; Game routes and nearest-key columns for view. |
| OLD CELL 39 | Game spread-size merge; thresholds and conflict overrides affect final routes. |
| OLD CELL 40 | Favorite spread size/Spread_Status become routing modifiers, separate from evidence. |
| OLD CELL 41 | Minimum DK/FD FEI edge and full-slate quantiles drive candidates; raw Game matches evidence. |
| OLD CELL 42 | Game-keyed candidates and market-influenced reason flags drive review classification. |
| OLD CELL 43 | Raw audit Game/home/away labels and opener/current home spreads determine movement, key crosses, relationship. Other pasted total/price metadata do not drive calculations. |
| OLD CELL 44 | Audit relationship/movement class/key cross and route Spread_Status determine final decisions. |
| OLD CELL 45 | Select/sort/export opener/current spread, movement, routing, decision fields. |
| CELL 46 | Optional exact-offer CSV type/team/direction/odds/duplicate/eligibility validation against decisions; no link to automatic pricing consumers. |
| CELL 47 | Both initial book spreads calibrate EPA fit/blend/retention; Game matches review; review subset created after full-slate fit. |
| CELL 48 | Covers current spread and retained home line reoriented to Model_Side; cushion and key barriers. |
| CELL 51 | **Separate historical** CFBD line/score data; closing home spread establishes empirical error distribution. |
| CELL 52 | Current model-side market spread/cushion determines history bucket/probabilities; history fields retained. |
| CELL 53 | Exact raw Game/teams match Odds API events; market discovery/availability and quota logs. |
| CELL 54 | Event IDs request actual offers; market/type/team/direction/line/price parsed, with book and timestamp metadata. |
| CELL 55 | Offered spread Line/American_Odds plus retained line/routes drive eligibility, probability/price edge, keys, shortlist ranking. |
| CELL 56 | Historical closing spreads/margins define key tax; offer Key_Tradeoff and cover probability receive audit adjustments. |
| CELL 57 | Offered Line/cushion, Home_Team orientation, and historical buckets determine W/P/L; American_Odds determine break-even, profit multiple, ROI. |
| CELL 57A | Offered Line and team/home identity determine integer push estimate; Profit_Multiple feeds adjusted ROI. |
| CELL 58 | **Separate historical** CFBD spread AND game total from one provider create implied TT and errors. Not a consumer of current DK_Total/FD_Total. |
| OLD CELL 59 | Routes, retained cushion, actual offered TT Line/price/source market choose directional TT candidates, anchors and experimental probabilities. |
| CELL 59A | Offered TT line and historical implied total determine push; model adjustment gates qualitative versus quantitative status. |
| CELL 60 | Offered American_Odds→break-even/profit multiple/experimental ROI. |
| CELL 61 | Offer identity, adjusted probabilities/ROI and warnings form compact handoff/review. |
| CELL 61B | Copies handoff, exports CSV; no new market arithmetic. |
| CELL 62 | Market_Model_Spread/Market_TT_Anchor determine primary line; offered odds break distance ties; ROI chooses value alternative. |
| CELL 66 | Optional original kickoff/DK/FD spread/total and derived model/key fields enrich pricing/context; preserves unpriced background games. |
| CELL 67 | Price-specific synchronization, canonical adjusted metrics, market/context text cleanup. |
| CELL 69 | Optional manual live line/odds, retained line, history and final home/away context recalculate probability/push/ROI. Line argument is supplied team’s spread, not always home spread. |
| CELL 73 | Offered price/identity, market relationship, opener/current home spreads and routing/context are selected into Architect export; no new handicapping calculation. |
| CELL 73C | Recovery CSV loads market/context fields wholesale; does not reconstruct acquisition or model globals. |

CELL 2/CELL 3, CELL 13, the unnumbered key cleanup, and OLD CELL 25 do not directly consume market columns. The empty unlabeled cell has no behavior. This accounts for all notebook cells without treating archive views as acquisition logic.

## Current handling of missing games and values

- **Absent events:** initial slate is whatever CELL 4 returns. There is no comparison with a full CFBD schedule, automatic Action Network/Covers gap-fill, or search for missing market games. An absent event never enters df_market/model slate. A nonempty partial slate can pass CELL 4/CELL 5/CELL 6.
- **Missing bookmaker point:** CELL 5 initializes spreads/totals to None and leaves missing values in the row. CELL 5/CELL 6 report missing-point counts but do not include zero missing points in their PASS conditions. Nonempty card, required column presence, uniqueness, and date validity are the gates. Empty or malformed data can fail earlier column access rather than reaching a friendly STOP.
- **Missing CFBD:** CELL 10 prints STOP for unmatched names; CELL 11 raises if either side has missing net EPA, duplicates, or wrong row count. It does not silently exclude unmatched games.
- **Missing BCF:** CELL 14 raises for unmatched canonical names, duplicates, or any target team missing; OLD CELL 19 raises on missing home/away FEI or count/duplicate failure.
- **Missing spreads:** OLD CELL 21 raises on missing model/book comparisons; OLD CELL 37 explicitly raises for any missing DK/FD spread inputs. The full retained slate must have both spread roles for these exact legacy calculations.
- **Missing totals:** DK_Total/FD_Total absence is reported but does not stop the current core's numerical calculations. They are structurally expected in CELL 5/CELL 6 and retained as optional CELL 66 context.
- **Missing review audit:** OLD CELL 43 requires exactly the review Game set, no missing/extra games, no duplicates, and nonnull opening/current home spreads; failure raises. It does not infer openers or partial-review statuses.
- **Missing later offers:** CELL 53 reports unmatched events and skips them; request failures in event discovery/price loops are skipped. CELL 54 raises if no pricing rows returned. CELL 46's header-only manual input is an awaiting-input condition, not a successful pricing baseline. Downstream pricing/TT branches are not guaranteed safe when empty.

Dropping a few games from acquisition is compatible with the planned architecture, but changes the legacy full-slate quantiles and CELL 47 market fit. Preserve exclusion records outside the modeled table and evaluate those effects; do not call a reduced or substituted slate numerically identical without evidence.

## Legacy sportsbook offer/juice contract — Architect responsibility

These fields are not necessary to compute EPA/FEI differential, Module 3, convergence, routing, keys, Phase 1, Covers relationship, or OLD CELL 44 final classification. They were needed by legacy break-even/EV, offer shopping, experimental TT, and priced exports. New CFB1 does not require these price-dependent branches; the Architect owns wager evaluation. The initial CELL 5 card contains **none of them**.

| Exact column | Meaning / inferred type / sign | Branch requirement | Producer → first later consumer |
| --- | --- | --- | --- |
| Event_ID | Odds API event identifier; string | Only legacy event/offer requests; not core key | CELL 53 → CELL 54 |
| Commence_Time | Event ISO timestamp string | Discovery metadata, not date gate | CELL 53 carried; no later pricing calculation |
| Bookmaker | FanDuel/DraftKings display name; string | Discovery/audit only | CELL 53 same-cell availability; no later direct reader |
| Bookmaker_Key | fanduel/draftkings identifier; string | Discovery metadata only | CELL 53 same-cell tables; no later direct reader |
| Market_Key | Discovered provider market identifier; string | Discovery/audit only | CELL 53 same-cell availability; CELL 54 uses its own requested list |
| Is_CFB1_Target_Market | Whether discovered key belongs to target list; bool | Discovery/audit only | CELL 53 same-cell pivot; no later reader |
| Market_Type | FULL_GAME_SPREAD/TEAM_TOTAL/1H_* category; string | Offered-price branch required | CELL 46 manual branch local; CELL 54 → CELL 55/OLD CELL 59 |
| Team | Offered spread team or TT target team; string | Offer orientation/identity required | CELL 46 manual branch local; CELL 54 → CELL 55 |
| Bet_Direction | SPREAD/OVER/UNDER; string | TT route matching required; price input schema | CELL 46 manual branch local; CELL 54 → OLD CELL 59 |
| Line | Offered point threshold; number/nullable | Required priced candidate; spread is **offered Team perspective**, TT unsigned | CELL 46 manual branch local; CELL 54 → CELL 55 |
| American_Odds | Offered juice; number/nullable; negative price is NOT home favorite sign | Required break-even/ROI/ranking, **not weekly core** | CELL 46 manual branch local; CELL 54 → CELL 55 |
| Sportsbook | Display book label; string | Required priced-row identity/output | CELL 46 manual branch local; CELL 54 → CELL 55 de-dup carries; OLD CELL 59 anchors |
| Sportsbook_Key | Provider book identifier; string | Metadata only | CELL 54 carried; no later explicit reader |
| Source_Market_Key | Provider main/alternate/first-half market key; string | TT anchor selection requires distinguishing main `team_totals` | CELL 54 → OLD CELL 59; not needed for core weekly path |
| Market_Last_Update | Provider market timestamp; string/nullable | Metadata only; not retrieved timestamp | CELL 54 carried; no later explicit reader |
| HTTP_Status | Request HTTP status; integer | Legacy log only | CELL 53/CELL 54 own log reports |
| Requests_Remaining | Quota header; string/None | Legacy quota log only | CELL 53/CELL 54 own log reports |
| Requests_Used | Quota header; string/None | Legacy quota log only | CELL 53/CELL 54 own log reports |
| Last_Request_Cost | Quota header; string/None | Legacy quota log only | CELL 53/CELL 54 own log reports |

Game/Home_Team/Away_Team recur on offers with the identity meaning above. American_Odds and point Line must never be confused: a −110 price is juice; a −7 line is a 7-point handicap for the named team. The legacy initial slate request may return prices in JSON, but CELL 5 discards them.

### Legacy derived pricing outputs — not new CFB1 requirements

Exact market-dependent output names below are cataloged to avoid mistaking them for provider inputs. Each field has a catalog row with its inferred type and shared stage meaning/provenance. Related fields retain a shared explanation to distinguish their branch context. The catalog records legacy branch requirements only. Football probabilities and applicable push outputs are retained; economics, offer-ranked membership, and price-required schema fields are not new CFB1 requirements. Original formulas/status thresholds remain historical reference in BEHAVIOR_LOCK.md.

| Exact columns | Meaning / type / sign | Producer → first later consumer |
| --- | --- | --- |
| Spread_Bucket | Inferred type: string. Historical spread-magnitude class string and bucket observation count integer | CELL 52 → CELL 57 reads conditionally if present on offers; CELL 52 does not automatically attach them to CELL 55 shortlist |
| Historical_Bucket_N | Inferred type: integer/count or integer-like numeric. Historical spread-magnitude class string and bucket observation count integer | CELL 52 → CELL 57 reads conditionally if present on offers; CELL 52 does not automatically attach them to CELL 55 shortlist |
| Global_Cover_Prob | Inferred type: numeric; nullable where source branch permits. Diagnostic empirical W/P/L fractions [0,1]; V1 minimum cover diagnostic | CELL 52 own display; CELL 55 separately recreates some cover columns, not a merge from this diagnostic |
| Global_Push_Prob | Inferred type: numeric; nullable where source branch permits. Diagnostic empirical W/P/L fractions [0,1]; V1 minimum cover diagnostic | CELL 52 own display; CELL 55 separately recreates some cover columns, not a merge from this diagnostic |
| Global_Loss_Prob | Inferred type: numeric; nullable where source branch permits. Diagnostic empirical W/P/L fractions [0,1]; V1 minimum cover diagnostic | CELL 52 own display; CELL 55 separately recreates some cover columns, not a merge from this diagnostic |
| Bucket_Cover_Prob | Inferred type: numeric; nullable where source branch permits. Diagnostic empirical W/P/L fractions [0,1]; V1 minimum cover diagnostic | CELL 52 own display; CELL 55 separately recreates some cover columns, not a merge from this diagnostic |
| Bucket_Push_Prob | Inferred type: numeric; nullable where source branch permits. Diagnostic empirical W/P/L fractions [0,1]; V1 minimum cover diagnostic | CELL 52 own display; CELL 55 separately recreates some cover columns, not a merge from this diagnostic |
| Bucket_Loss_Prob | Inferred type: numeric; nullable where source branch permits. Diagnostic empirical W/P/L fractions [0,1]; V1 minimum cover diagnostic | CELL 52 own display; CELL 55 separately recreates some cover columns, not a merge from this diagnostic |
| CFB1_Cover_Prob_V1 | Inferred type: numeric; nullable where source branch permits. Diagnostic empirical W/P/L fractions [0,1]; V1 minimum cover diagnostic | CELL 52 own display; CELL 55 separately recreates some cover columns, not a merge from this diagnostic |
| Candidate_Cushion | Offered Line−Retained_Model_Spread; signed points, positive favorable | CELL 55 → CELL 57 |
| Global_Cover_Prob | Inferred type: numeric; nullable where source branch permits. Candidate empirical cover fractions, initial conservative minimum; CFB1_Cover_Prob later overwritten in CELL 57 | CELL 55 → CELL 56 audit; CELL 57 recomputation |
| Bucket_Cover_Prob | Inferred type: numeric; nullable where source branch permits. Candidate empirical cover fractions, initial conservative minimum; CFB1_Cover_Prob later overwritten in CELL 57 | CELL 55 → CELL 56 audit; CELL 57 recomputation |
| CFB1_Cover_Prob | Inferred type: numeric; nullable where source branch permits. Candidate empirical cover fractions, initial conservative minimum; CFB1_Cover_Prob later overwritten in CELL 57 | CELL 55 → CELL 56 audit; CELL 57 recomputation |
| Break_Even_Prob | Inferred type: numeric; nullable where source branch permits. Quoted-price fraction; win probability minus break-even, signed fraction | CELL 55 → CELL 57 overwrites; CELL 57A/CELL 61 consume break-even later |
| Probability_Edge | Inferred type: numeric; nullable where source branch permits. Quoted-price fraction; win probability minus break-even, signed fraction | CELL 55 → CELL 57 overwrites; CELL 57A/CELL 61 consume break-even later |
| Key_Tradeoff | OFF_KEY/CROSSES/LANDS_ON_KEY text or empty | CELL 55 → CELL 56/CELL 57 |
| Abs_From_Main | Absolute offered-line distance from model-side current line; nonnegative points | CELL 55 same-cell shortlist, carried without later explicit reader |
| Favorite_Closing_Spread | Inferred type: numeric; nullable where source branch permits. Historical market favorite size nonnegative points; actual favorite margin signed points | CELL 56 own key-tax audit only |
| Favorite_Final_Margin | Inferred type: numeric; nullable where source branch permits. Historical market favorite size nonnegative points; actual favorite margin signed points | CELL 56 own key-tax audit only |
| Key_Number | Inferred type: integer/count or integer-like numeric. Key magnitude, global integer sample/count, empirical fraction | CELL 56 own key-tax lookup only |
| Historical_Games | Inferred type: integer/count or integer-like numeric. Key magnitude, global integer sample/count, empirical fraction | CELL 56 own key-tax lookup only |
| Exact_Key_Landings | Inferred type: integer/count or integer-like numeric. Key magnitude, global integer sample/count, empirical fraction | CELL 56 own key-tax lookup only |
| Global_Key_Landing_Rate | Inferred type: numeric; nullable where source branch permits. Key magnitude, global integer sample/count, empirical fraction | CELL 56 own key-tax lookup only |
| Local_Spread_Low | Inferred type: numeric; nullable where source branch permits. Local magnitude window, integer sample/count, fractions; max global/local key rate | CELL 56 own lookup; not a new core acquisition field |
| Local_Spread_High | Inferred type: numeric; nullable where source branch permits. Local magnitude window, integer sample/count, fractions; max global/local key rate | CELL 56 own lookup; not a new core acquisition field |
| Local_Historical_Games | Inferred type: integer/count or integer-like numeric. Local magnitude window, integer sample/count, fractions; max global/local key rate | CELL 56 own lookup; not a new core acquisition field |
| Local_Key_Landings | Inferred type: integer/count or integer-like numeric. Local magnitude window, integer sample/count, fractions; max global/local key rate | CELL 56 own lookup; not a new core acquisition field |
| Local_Key_Landing_Rate | Inferred type: numeric; nullable where source branch permits. Local magnitude window, integer sample/count, fractions; max global/local key rate | CELL 56 own lookup; not a new core acquisition field |
| CFB1_Key_Tax_V1 | Inferred type: numeric; nullable where source branch permits. Local magnitude window, integer sample/count, fractions; max global/local key rate | CELL 56 own lookup; not a new core acquisition field |
| Historical_Key_Tax | Inferred type: numeric; nullable where source branch permits. Audit fraction and clipped adjusted fraction | CELL 56 → carried to CELL 57; **not** canonical ROI probability inputs |
| Key_Adjusted_Cover_Prob | Inferred type: numeric; nullable where source branch permits. Audit fraction and clipped adjusted fraction | CELL 56 → carried to CELL 57; **not** canonical ROI probability inputs |
| Profit_Multiple | Net winnings per unit won; nonnegative numeric ratio for valid odds | CELL 57 → CELL 57A |
| Global_Win_Prob | Inferred type: numeric; nullable where source branch permits. Recomputed empirical W/P/L fractions | CELL 57 same-cell source selection; copied into CELL 57A |
| Bucket_Win_Prob | Inferred type: numeric; nullable where source branch permits. Recomputed empirical W/P/L fractions | CELL 57 same-cell source selection; copied into CELL 57A |
| Global_Push_Prob | Inferred type: numeric; nullable where source branch permits. Recomputed empirical W/P/L fractions | CELL 57 same-cell source selection; copied into CELL 57A |
| Bucket_Push_Prob | Inferred type: numeric; nullable where source branch permits. Recomputed empirical W/P/L fractions | CELL 57 same-cell source selection; copied into CELL 57A |
| Global_Loss_Prob | Inferred type: numeric; nullable where source branch permits. Recomputed empirical W/P/L fractions | CELL 57 same-cell source selection; copied into CELL 57A |
| Bucket_Loss_Prob | Inferred type: numeric; nullable where source branch permits. Recomputed empirical W/P/L fractions | CELL 57 same-cell source selection; copied into CELL 57A |
| Probability_Source | GLOBAL or SPREAD_BUCKET; string | CELL 57 → CELL 57A display; not provider Source |
| CFB1_Win_Prob | Inferred type: numeric; nullable where source branch permits. Selected source triplet, fractions | CELL 57 → CELL 57A redistribution |
| CFB1_Push_Prob | Inferred type: numeric; nullable where source branch permits. Selected source triplet, fractions | CELL 57 → CELL 57A redistribution |
| CFB1_Loss_Prob | Inferred type: numeric; nullable where source branch permits. Selected source triplet, fractions | CELL 57 → CELL 57A redistribution |
| EV_Per_Dollar | Inferred type: numeric; nullable where source branch permits. Signed expected return per dollar, alias, status/warning strings | CELL 57 → CELL 57A copies; CELL 61 reads warning and adjusted metrics |
| Expected_ROI | Inferred type: numeric; nullable where source branch permits. Signed expected return per dollar, alias, status/warning strings | CELL 57 → CELL 57A copies; CELL 61 reads warning and adjusted metrics |
| EV_Status | Inferred type: string. Signed expected return per dollar, alias, status/warning strings | CELL 57 → CELL 57A copies; CELL 61 reads warning and adjusted metrics |
| Decision_Warning | Inferred type: string. Signed expected return per dollar, alias, status/warning strings | CELL 57 → CELL 57A copies; CELL 61 reads warning and adjusted metrics |
| Historical_Push_Prob | Inferred type: numeric; nullable where source branch permits. Integer-line landing frequency fraction and sample integer | CELL 57A own redistribution/display; downstream canonical push metric consumed |
| Historical_Push_N | Inferred type: integer/count or integer-like numeric. Integer-line landing frequency fraction and sample integer | CELL 57A own redistribution/display; downstream canonical push metric consumed |
| Push_Adjusted_Win_Prob | Inferred type: numeric; nullable where source branch permits. Canonical adjusted W/P/L fractions and signed return ratio | CELL 57A → CELL 61; CELL 62/CELL 67 require adjusted metrics |
| Push_Adjusted_Push_Prob | Inferred type: numeric; nullable where source branch permits. Canonical adjusted W/P/L fractions and signed return ratio | CELL 57A → CELL 61; CELL 62/CELL 67 require adjusted metrics |
| Push_Adjusted_Loss_Prob | Inferred type: numeric; nullable where source branch permits. Canonical adjusted W/P/L fractions and signed return ratio | CELL 57A → CELL 61; CELL 62/CELL 67 require adjusted metrics |
| Push_Adjusted_EV_Per_Dollar | Inferred type: numeric; nullable where source branch permits. Canonical adjusted W/P/L fractions and signed return ratio | CELL 57A → CELL 61; CELL 62/CELL 67 require adjusted metrics |
| Push_Adjusted_ROI | Inferred type: numeric; nullable where source branch permits. Canonical adjusted W/P/L fractions and signed return ratio | CELL 57A → CELL 61; CELL 62/CELL 67 require adjusted metrics |
| TT_Target_Team | Inferred type: string. Experimental route target/direction strings; signed model adjustment points | OLD CELL 59 → CELL 59A direction/eligibility |
| TT_Direction | Inferred type: string. Experimental route target/direction strings; signed model adjustment points | OLD CELL 59 → CELL 59A direction/eligibility |
| TT_Model_Adjustment | Inferred type: numeric; nullable where source branch permits. Experimental route target/direction strings; signed model adjustment points | OLD CELL 59 → CELL 59A direction/eligibility |
| Market_TT_Anchor | Inferred type: numeric; nullable where source branch permits. Experimental offered-market anchor/fair TT numeric thresholds; direction-oriented signed edge; absolute distance points | OLD CELL 59 → CELL 59A; CELL 62 anchor |
| Retained_TT_Fair_Line | Inferred type: numeric; nullable where source branch permits. Experimental offered-market anchor/fair TT numeric thresholds; direction-oriented signed edge; absolute distance points | OLD CELL 59 → CELL 59A; CELL 62 anchor |
| TT_Candidate_Edge | Inferred type: numeric; nullable where source branch permits. Experimental offered-market anchor/fair TT numeric thresholds; direction-oriented signed edge; absolute distance points | OLD CELL 59 → CELL 59A; CELL 62 anchor |
| Distance_From_Anchor | Inferred type: numeric; nullable where source branch permits. Experimental offered-market anchor/fair TT numeric thresholds; direction-oriented signed edge; absolute distance points | OLD CELL 59 → CELL 59A; CELL 62 anchor |
| TT_Win_Prob | Inferred type: numeric; nullable where source branch permits. Experimental empirical fractions | OLD CELL 59 → CELL 59A |
| TT_Push_Prob | Inferred type: numeric; nullable where source branch permits. Experimental empirical fractions | OLD CELL 59 → CELL 59A |
| TT_Loss_Prob | Inferred type: numeric; nullable where source branch permits. Experimental empirical fractions | OLD CELL 59 → CELL 59A |
| TT_Model_Direction_Status | Inferred type: string. Experimental direction/eligibility strings and bool | CELL 59A → CELL 60 eligibility |
| TT_Quantitative_Status | Inferred type: string. Experimental direction/eligibility strings and bool | CELL 59A → CELL 60 eligibility |
| TT_Is_Integer_Line | Inferred type: bool. Experimental direction/eligibility strings and bool | CELL 59A → CELL 60 eligibility |
| TT_Historical_Push_Prob | Inferred type: numeric; nullable where source branch permits. Experimental integer TT push fraction/count | CELL 59A own redistribution; carried into CELL 60 |
| TT_Historical_Push_N | Inferred type: integer/count or integer-like numeric. Experimental integer TT push fraction/count | CELL 59A own redistribution; carried into CELL 60 |
| TT_Final_Win_Prob | Inferred type: numeric; nullable where source branch permits. Experimental adjusted fractions; null for qualitative rows | CELL 59A → CELL 60/CELL 61 |
| TT_Final_Push_Prob | Inferred type: numeric; nullable where source branch permits. Experimental adjusted fractions; null for qualitative rows | CELL 59A → CELL 60/CELL 61 |
| TT_Final_Loss_Prob | Inferred type: numeric; nullable where source branch permits. Experimental adjusted fractions; null for qualitative rows | CELL 59A → CELL 60/CELL 61 |
| Break_Even_Prob_Final | Inferred type: numeric; nullable where source branch permits. Experimental price fraction, signed expected return, status/warnings | CELL 60 → CELL 61 |
| TT_EV_Per_Dollar | Inferred type: numeric; nullable where source branch permits. Experimental price fraction, signed expected return, status/warnings | CELL 60 → CELL 61 |
| TT_Expected_ROI | Inferred type: numeric; nullable where source branch permits. Experimental price fraction, signed expected return, status/warnings | CELL 60 → CELL 61 |
| TT_EV_Status | Inferred type: string. Experimental price fraction, signed expected return, status/warnings | CELL 60 → CELL 61 |
| TT_Decision_Warning | Inferred type: string. Experimental price fraction, signed expected return, status/warnings | CELL 60 → CELL 61 |
| Market_Family | Inferred type: string. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Direction | Inferred type: string. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Bet_Label | Inferred type: string. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Model_Adjustment | Inferred type: numeric; nullable where source branch permits. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Model_Probability | Inferred type: numeric; nullable where source branch permits. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Push_Probability | Inferred type: numeric; nullable where source branch permits. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Expected_ROI_Final | Inferred type: numeric; nullable where source branch permits. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Pricing_Status | Inferred type: string. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Warning | Inferred type: string. Handoff market/direction/label strings, signed point adjustment, fractions/return/status; qualitative numeric values null | CELL 61 → CELL 61B snapshot, then CELL 62/CELL 66 |
| Card_Role | Inferred type: string. PRIMARY/VALUE_ALT/QUALITATIVE_REVIEW; signed team spread or unsigned TT anchor; distance points; fractions/ROI/status/warning aliases | CELL 62 → CELL 66/CELL 67; anchors are local working fields not all exported |
| Anchor_Line | Inferred type: numeric; nullable where source branch permits. PRIMARY/VALUE_ALT/QUALITATIVE_REVIEW; signed team spread or unsigned TT anchor; distance points; fractions/ROI/status/warning aliases | CELL 62 → CELL 66/CELL 67; anchors are local working fields not all exported |
| Anchor_Distance | Inferred type: numeric; nullable where source branch permits. PRIMARY/VALUE_ALT/QUALITATIVE_REVIEW; signed team spread or unsigned TT anchor; distance points; fractions/ROI/status/warning aliases | CELL 62 → CELL 66/CELL 67; anchors are local working fields not all exported |
| Break_Even | Inferred type: numeric; nullable where source branch permits. PRIMARY/VALUE_ALT/QUALITATIVE_REVIEW; signed team spread or unsigned TT anchor; distance points; fractions/ROI/status/warning aliases | CELL 62 → CELL 66/CELL 67; anchors are local working fields not all exported |
| Expected_ROI | Inferred type: numeric; nullable where source branch permits. PRIMARY/VALUE_ALT/QUALITATIVE_REVIEW; signed team spread or unsigned TT anchor; distance points; fractions/ROI/status/warning aliases | CELL 62 → CELL 66/CELL 67; anchors are local working fields not all exported |
| Model_Status | Inferred type: string. PRIMARY/VALUE_ALT/QUALITATIVE_REVIEW; signed team spread or unsigned TT anchor; distance points; fractions/ROI/status/warning aliases | CELL 62 → CELL 66/CELL 67; anchors are local working fields not all exported |
| Warning_Final | Inferred type: string. PRIMARY/VALUE_ALT/QUALITATIVE_REVIEW; signed team spread or unsigned TT anchor; distance points; fractions/ROI/status/warning aliases | CELL 62 → CELL 66/CELL 67; anchors are local working fields not all exported |
| Decision_Card_Included | Inferred type: bool. Bool card membership and rich-context usage string | CELL 66 → CELL 67 retains context |
| Context_Usage | Inferred type: string. Bool card membership and rich-context usage string | CELL 66 → CELL 67 retains context |
| Live_Line | Inferred type: numeric; nullable where source branch permits. Manually supplied team spread/American price, frozen team-perspective retained-line alias, and conservative source win fraction | CELL 69 on-demand result only; no normal later consumer |
| Live_Odds | Inferred type: numeric; nullable where source branch permits. Manually supplied team spread/American price, frozen team-perspective retained-line alias, and conservative source win fraction | CELL 69 on-demand result only; no normal later consumer |
| Retained_Model_Line | Inferred type: numeric; nullable where source branch permits. Manually supplied team spread/American price, frozen team-perspective retained-line alias, and conservative source win fraction | CELL 69 on-demand result only; no normal later consumer |
| CFB1_Base_Win_Prob | Inferred type: numeric; nullable where source branch permits. Manually supplied team spread/American price, frozen team-perspective retained-line alias, and conservative source win fraction | CELL 69 on-demand result only; no normal later consumer |


Historical-only inputs expected by these branches include `Season`/`Week` (integers), `Game_ID` (CFBD game identity), `Provider` (string), `Closing_Home_Spread` (home-perspective number), `Actual_Home_Margin` (positive home win margin), `Market_Expected_Home_Margin = -Closing_Home_Spread`, `Spread_Error = actual - expected`, and `ATS_Result` (HOME_COVER/AWAY_COVER/PUSH). CELL 51 creates them; CELL 52 first consumes closing spread/error, CELL 56 first consumes actual margin in its key audit, CELL 57A consumes both margin and closing spread for pushes. They are not current market-acquisition columns.

CELL 58 additionally creates `Closing_Game_Total`, `Market_Implied_Team_Total`, `Actual_Team_Points`, `Team_Total_Error`, `TT_Result`, `Team`, `Opponent`, and `Home_Away` from historical paired spread/total and scores. Implied home TT=(total−home spread)/2, away=(total+home spread)/2; TT error is actual−implied, positive over. These are experimental calibration inputs first consumed later by OLD CELL 59 (error distribution) and CELL 59A (implied TT/actual points), not current-price fields or replacements for DK_Total/FD_Total.

Temporary merge-suffix columns (`_57A_*`, `_Card`, `_Context`, `_GameContext`), display percentage copies, and validation-match booleans are internal transformations, not provider requirements. Kelly/stake/bankroll columns are explicitly removed/rejected, never acquisition requirements.

## What can leave the normal acquisition layer

“Remove from acquisition” means omit an external input or derive it in an adapter/model stage. It does not authorize deleting an unchanged legacy column while its callers still index it.

| Legacy field/object | Effect on EPA/FEI/Module 3/convergence/routing/keys/Phase 1/final decisions | Safe future disposition |
| --- | --- | --- |
| ODDS_API_KEY; odds_url/params/res/json; provider events/market discovery/quota objects | Service/payload plumbing, not quantitative features | Archive adapters; remove provider requirement from normal execution. |
| Prices in initial Odds JSON; all four Covers home/away price fields | CELL 5 drops initial prices; Covers core does not use pasted price fields | Omit from normalized weekly acquisition. |
| Event_ID; Commence_Time; Bookmaker/Bookmaker_Key; Market_Key; Is_CFB1_Target_Market; Sportsbook_Key; Market_Last_Update; HTTP_Status; Requests_Remaining/Used; Last_Request_Cost | Needed only for old offer acquisition/audit or unused metadata | Omit from weekly contract; retain trace only where useful in separate external offer adapter. |
| Market_Type; Team; Bet_Direction; Line; American_Odds; Sportsbook; Source_Market_Key | Not needed by OLD CELL 44 weekly decision; needed by later supplied-price branches/export | Keep in an Architect-side offer table, outside new CFB1 requirements. Expected ROI evaluation belongs to Universal Bet Slip Architect, not new CFB1. |
| Open_Total; Current_Total from Covers; Data_Status | Not used by generic movement/final decision formulas | Omit from audit computational minimum. Keep provenance separately and retain one current game total in planned weekly schema. |
| Kickoff_ET; Game_Date_ET | Required by literal CELL 6 date/filter/sort | Derive from a single UTC kickoff in compatibility adapter; do not discard scheduled identity/date membership. |
| Home_CFBD_Name; Away_CFBD_Name; matched flags | Computed canonical joins/checks | Derive from canonical mapping; not fields the market provider must supply. Preserve raw/display mapping for legacy Game joins. |
| Game display string | Required literal joins, but collision-prone | Retain/derive display text alongside stable migrated game_id mapping. Do not change names or joins silently. |
| DK_Total; FD_Total | Structurally required by CELL 5/CELL 6, optionally exported in CELL 66; no core arithmetic uses either | Replace redundant book-specific totals with current_total in proposed normalized schema. A literal legacy replay still needs schema adaptation and honest source labeling. |
| DK_Spread; FD_Spread | Both used in FEI, conservative edge, consensus, retained fit; convergence specifically uses DK side | Replace book-specific naming only with explicit mapping/selection policy and parity checks. **Cannot delete either from an unchanged notebook path or promise exact two-book behavior from one quote.** |
| Open_Home_Spread | Drives audit movement/key crossings and final decisions | Conditional late-week requirement; cannot remove when preserving final decision logic. |
| Current_Home_Spread | Later snapshot drives audit/final decisions and CELL 48 retained-line cushion | Required late-week observation; not a substitute that should overwrite frozen initial DK/FD lines. |
| Consensus/FEI-edge/key/favorite/route/retained/probability columns | Downstream calculations, not source measurements | Compute in model stages; do not ask providers to return model features. |

Numerical EPA and raw FEI differential/Module 3 signal thresholds do not use sportsbook price or line magnitude, but their row population and team identities come from the market-defined slate. Convergence uses the market-based FEI edge direction; routing/key/Phase 1/final decisions therefore still need valid point spreads. Preserve that distinction when describing “market-independent” calculations.

## Covers boundary implementation — explicit readiness and provenance

The hardened Covers adapter separates `manual_ready`, `production_ready`, and
`audit_ready`. See [COVERS_MARKET_BOUNDARY.md](COVERS_MARKET_BOUNDARY.md) for exact
rules, receipt schema, CLI requirements, exports, and conservative exit semantics.
It reuses the committed identity/schedule foundation; alias membership alone
does not verify a game. Production eligibility requires a valid official
schedule association, preserved ID/orientation/date/scope, required measured
current points, consistent opposing spread sides, and a known capture timestamp.
Cached file mtime is filesystem metadata only; absent trusted capture metadata,
retrieval time remains null and records cannot pass production readiness.

Openers remain optional for **current-market** production eligibility. Verified
same-game/same-book opening and later-current observations are a separate audit
requirement, preserving OLD CELL 43/44's dependency without blocking initial
market acquisition. No opener-acquisition convention is invented. Market-ready
does not mean model-ready, complete-FBS coverage, or guaranteed quote freshness.
October 17 recovery artifacts remain historical inputs, not runtime defaults.

The adapter still exposes explicit legacy DK/FD roles; the general normalized
schema below remains a proposal rather than a completed common-source interface.

## Proposed MINIMAL normalized football-market schema — not implemented

Propose **one row per stable game, source, and retrieved observation**, retaining the frozen initial observation and later audit observation separately. Multiple honest source observations can coexist. Caller-selected snapshot/role and source priority must be explicit, not inferred from replacing whatever row happens to be latest.

| Proposed exact name | Meaning / proposed type | Required scope | Compatibility mapping / rule |
| --- | --- | --- | --- |
| game_id | Stable canonical matchup/event identifier; string | Required | Resolve independently of display names; include season/event identity and repeated-matchup discriminator. Derive a legacy Game display string separately. |
| away_team | Canonical CFBD-compatible away identity; string | Required | Maps Away_CFBD_Name; retain display alias mapping for Away_Team/legacy Game in an adapter. |
| home_team | Canonical CFBD-compatible home identity; string | Required | Maps Home_CFBD_Name; do not infer home from favorite. |
| kickoff_utc | Scheduled event timestamp, timezone-aware UTC | Required for equivalent target-date membership | Derive Kickoff_ET and Game_Date_ET; preserve Eastern inclusive-date filtering and sorting. Stable external schedule enrichment may supply it if absent from a market source. Retrieved time is not kickoff time. |
| current_home_spread | Full-game home-team handicap points; numeric | Required nonnull for an eligible modeled game | Negative home favorite, positive home underdog, zero pick'em. Source-specific initial observations feed explicitly designated legacy spread roles; later observation feeds Current_Home_Spread. |
| current_total | Full-game combined point threshold; numeric | Required by planned market-input policy | No juice/direction attached. Current source does not numerically use both book totals; do not describe single-total replacement as changing an existing current-total calculation. |
| source | Honest acquisition provenance identifier; string | Required | Action Network or Covers plus enough underlying quote provenance when needed. Not Odds API event ID, not Probability_Source, and not a fabricated DK/FD designation. |
| retrieved_at | Observation retrieval timestamp, timezone-aware UTC | Required | New provenance requirement; CELL 5 does not provide it. Distinct from kickoff and provider Market_Last_Update. Preserve frozen vs later observation timestamps. |
| open_home_spread | Actual opening home-team handicap; numeric | **Optional during initial slate generation; required for unchanged late-week audit/final decisions** | Maps Open_Home_Spread. Same source/game/perspective and known opener definition required; do not synthesize from current spread. If kept in a separate audit-observation table, that table still must supply it. |

The eight base columns form the proposed weekly normalized input. `open_home_spread` is the ninth conditional late-week field. No opener total, opener/current price, per-book juice, props, promo, or alternate-market column belongs in this minimum. Raw display aliases, exclusion records, and provider transport metadata can live in separate trace/adapter records; they are not additional handicapping inputs.

### Limits of the proposal

- **Single selected spread versus unchanged dual-book logic:** eight normalized columns can hold multiple distinct source rows. For exact legacy replay, preserve both original spread values and their designated roles, the original display-key mapping, and the initial versus audit snapshots through a documented compatibility adapter. A single Action Network-first quote per game is a reasonable future selection policy, but changes DK direction/FD conservative edge/consensus semantics if the two legacy quotes differ. That requires explicit validation rather than silent copying or fake book labels.
- **Opener:** optional acquisition-time coverage does not make it optional for final decision parity. If no opener can be supplied, stop/defer the late-week audited decision for that game; a new fallback classification requires separate authorization. Initial slate exclusion and complete coverage of its selected review set are different policies.
- **Time and perspective:** freeze the initial snapshot for quantiles/fit, then attach the later observation to the audit. Do not recalculate earlier model inputs from the audit's current line unless explicitly approved. Normalize away-perspective source lines by negation, using positively identified home/away teams.
- **Coverage:** use Action Network first, Covers gap-fill; modest excluded-game count is acceptable. Document exclusions and their influence on full-slate quantiles/fit. Source availability, opener semantics, schedule linkage, and normalization must be verified later; none was fetched or tested in this task.
- **Architect boundary:** actual offers and their Game/Team/Line/American_Odds/Sportsbook identity belong to the Architect. CFB1 supplies point-threshold-specific calibrated probabilities/push and football context without computing break-even/expected ROI. The historical priced export is not the new production handoff; do not require its economics fields to validate new CFB1.

## Answers for the approved migration boundary

1. **Minimal routine football-market columns:** game_id, away_team, home_team, kickoff_utc, current_home_spread, current_total; source and retrieved_at supply provenance. Add open_home_spread for preserved late-week decisions. Literal legacy replay still needs two designated spread roles, aliases, dates, and original snapshot mapping. No American_Odds, price, book offer identity, break-even or ROI column is required by new CFB1.
2. **Sign conventions remain locked:** initial/Covers home spread, model home margin, team-perspective retained/queried lines, and integer push orientation must remain explicit. Removing price evaluation does not authorize changing them.
3. **Price-dependent cells requiring review:** CELL 55, CELL 57 economics, CELL 57A ROI, OLD CELL 59 anchor/offer selection, CELL 60, CELL 61/CELL 62 selection/status, CELL 67 price-key/economics synchronization, CELL 69 economics, and CELL 73 priced export. See the approved-boundary review table above. Move economics/offer evaluation to Architect while preserving football calibration/push and making membership/schema changes explicit.
4. **Action Network + Covers feasibility:** theoretically sufficient for price-free football inputs with schedule/identity matching, spread perspective, total, provenance, and audit opener/current lines. Neither live availability nor dual-book parity has been verified. The price-free handoff must support line-specific probabilities when actual Architect offers differ from the modeled line.
