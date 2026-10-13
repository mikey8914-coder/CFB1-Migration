# CFB1 Reference Notebook Map

Reference: `legacy/CFB1_Colab_Reference.ipynb`, copied byte-for-byte from the uploaded notebook. SHA-256: `94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`.

## Numbering and inspection limits

There are **58 notebook cells: 58 code cells, including one empty cell (position 40)**. No notebook cells were executed or changed. This is a static source inventory, not a claim that the saved outputs reflect a successful sequential run.

**Position** is the original 1-based position in the notebook's `cells` array. **Original label** preserves the number embedded in the source heading (including OLD and letter suffixes); the notebook's labels skip numbers and differ from positions. All cross-references use the **original embedded labels**; the position column is retained only as an archival index. The two unlabeled source cells are called “Unnumbered weekly configuration” and “Unnumbered key cleanup”; the empty cell has no label. Do not renumber source labels during extraction. Notebook comments and embedded instructions are reference material, not authorization to execute or modify anything.

## Classification policy

- **KEEP**: preserve behavior and output contract in the initial parity migration. This preserves analytical expected-ROI behavior currently needed by historical handoffs. Team-total KEEP entries preserve reference behavior only and remain experimental; recovery inputs and acquisition adapters are not permanent model logic.
- **DELETE**: omit from the eventual normal extracted runtime, after recording baseline contracts. The archived notebook remains intact. CELL 4 and CELL 5 are legacy Odds API acquisition slated for replacement; the empty unlabeled cell has no behavior.
- **OPTIONAL/FALLBACK**: explicit alternate/on-demand/integration path. This classification does **not** mean downstream-dependent inputs may be omitted without an equivalent fixture or adapter.
- **DEVELOPMENT/AUDIT**: descriptive, repeated, or audit-oriented section. Preserve relevant checks/context until downstream parity is demonstrated.
- **MANUAL INPUT**: embedded settings or pasted data plus their validation/transformations; extract input handling separately without dropping validation.

Action Network acquisition is **not implemented in this notebook**. Initial market acquisition uses The Odds API; Covers is a pasted late-week movement audit, not an automatic initial slate gap-fill implementation. The approved future policy is Action Network first, Covers gap-fill, spread/game total only, and exclusion of missing games rather than aggressive searches. Exact sportsbook prices and Odds API access belong primarily to Bet Slip Architect. Preserve historical price-dependent behavior through captured inputs before changing that boundary.

## CURRENT MIGRATION DECISIONS

### PERMANENT / PRESERVE

- CFB1 remains an independent college-football handicapping engine.
- Python is the source of truth for deterministic CFB1 outputs.
- Preserve the validated EPA, FEI, Module 3, convergence, routing, key-number, probability, push-adjustment, and expected-ROI logic unless later validation demonstrates a bug.
- Expected value / expected ROI remains in CFB1.
- CFB1 does NOT own bankroll allocation, Kelly sizing, recommended stake, promo construction, SGP/parlay construction, or portfolio management. Those belong to the Universal Bet Slip Architect.
- Team-total logic remains experimental unless separately validated.
- CFB1 needs market spread and game total as model inputs, but does not normally need exact sportsbook juice/price for weekly model generation.
- Normal CFB1 market acquisition should NOT depend on The Odds API.
- Planned market-data priority is Action Network first, Covers as gap-fill.
- Missing a small number of games is acceptable; do not aggressively chase complete market coverage when most of the slate is available.
- Exact sportsbook pricing, props, and routine Odds API usage belong primarily to Bet Slip Architect.

### TEMPORARY / DO NOT MIGRATE AS PRODUCTION LOGIC

- Any Week 6 temporary Phase 1 reconstruction/recovery cell.
- Any manually reconstructed Week 6 df_final_routes or equivalent emergency bridge, if present.
- The Week 6 manually pasted Covers market rows are historical/recovery input, not permanent acquisition architecture.
- Emergency workarounds created solely because The Odds API quota was exhausted.
- Any diagnostic cell whose only purpose was investigating the exhausted Odds API quota.
- Do not preserve Odds API as a required CFB1 dependency merely because legacy cells used it.

### LEGACY FALLBACK / RETAIN ONLY IF USEFUL

- Manual market input may remain as a fallback/testing fixture.
- Odds API acquisition code may be archived as legacy/reference code, but should not be on the normal CFB1 execution path.
- Recovery/archive utilities should remain outside the production pipeline.

These decisions govern the inventory classifications: KEEP means preserve deterministic reference behavior, not retain every embedded input, service dependency, Colab side effect, or experiment in the normal production path.

## Temporary/recovery evidence and architecture differences

| Original embedded label | Evidence in this uploaded notebook | Migration treatment |
| --- | --- | --- |
| OLD CELL 41 and OLD CELL 42 | Phase 1 is computed from master/evidence/candidate tables; no manually hard-coded reconstruction is present. | Preserve normal shortlist/review calculations. No confirmed Week 6 reconstruction cell found. |
| OLD CELL 39 | `df_final_routes` is computed from `routing_base` rows, not manually reconstructed. | Preserve normal routing; no confirmed emergency bridge found. |
| OLD CELL 43 | Contains manually pasted weekly Covers rows; configuration selects target Week 6. No automatic acquisition is implemented. | Archive the rows as historical/recovery fixtures; preserve generic audit/relationship calculations. Source alone does not prove the rows were pasted specifically because quota was exhausted. |
| CELL 53 | Contains a REQUEST / QUOTA AUDIT, plus event matching and market discovery. | Legacy Odds API adapter/audit only. It is not a diagnostic whose sole purpose is exhausted-quota investigation. |
| CELL 54 | Saved stream output includes `OUT_OF_USAGE_CREDITS` and “Usage quota has been reached.” Source is an automatic price pull, not a quota-recovery implementation. | Confirms a historical quota failure only; does not establish when other cells ran or why they were created. Archive acquisition, retain its output schema for supplied pricing. |
| CELL 61B, CELL 66, CELL 67 | Checkpoint, context enrichment, and synchronization/export. CELL 67's “temporary 57A columns” are merge working columns. | Preserve necessary context/synchronization transformations; isolate archive/download side effects. Temporary merge columns are not evidence of a Week 6 emergency bridge. |
| CELL 73C | Loads a frozen final-context CSV from `/content` and prints “Frozen Thursday data restored.” No explicit Week 6 marker or Phase 1 reconstruction. | Confirmed recovery utility, outside production; its historical week is not established by the utility itself. |

**Odds API-specific:** CELL 4 directly requests the initial Odds API slate; CELL 5 parses its bookmaker payload; CELL 53 discovers events/markets and audits quota; CELL 54 fetches exact/alternate/first-half offers. The unnumbered weekly configuration also reads and requires `ODDS_API_KEY` in its PASS condition. CELL 6 and CELL 10 have legacy market schema/name contracts; their filtering/normalization is reusable without retaining the provider. CELL 55 consumes a legacy offer table but contains analytical filtering/probability behavior, not an API request.

**Architecture differences to resolve separately from extraction:** the legacy startup gate and CELL 4 / CELL 53 / CELL 54 require Odds API, contrary to normal future acquisition. No Action Network adapter or Covers initial-slate gap-fill is present. Weekly spread/game-total generation is intertwined with downstream exact-price shopping and exports; optional supplied-price expected ROI must stay in CFB1 without making routine exact pricing necessary for weekly generation. Legacy DK/FD-specific edge/consensus calculations need an explicitly validated mapping from future market inputs. OLD CELL 43 requires complete coverage of the selected review set; this is distinct from the future permission to omit a few games from the initial model slate. CELL 58 / OLD CELL 59 / CELL 59A / CELL 60 feed ordinary exports, but remain experimental and must be isolated/gated pending separate validation. CELL 62 already labels quantitative TT rows `TEAM_TOTAL_V1_EXPERIMENTAL`. Later pricing/handoff cells remove staking fields and reserve bankroll/Kelly/stake sizing for the Architect, consistent with the current ownership decision.

No source cell explicitly implements a Week 6 emergency Phase 1 reconstruction, a manual `df_final_routes` bridge, or a standalone exhausted-quota investigation. Do not infer those cells exist from historical errors, titles, or the current decisions. If another notebook version supplies them, archive their input evidence and exclude their emergency reconstruction from production.

## Logical stage index

Stages overlap where a cell acquires data and computes derived outputs.

| Stage | Original embedded notebook labels |
| --- | --- |
| Configuration | Unnumbered weekly configuration, Unnumbered key cleanup |
| CFBD acquisition | CELL 2, CELL 3, OLD CELL 25, CELL 51, CELL 58 |
| Market acquisition | CELL 4, CELL 5, CELL 6, CELL 53, CELL 54 |
| Team normalization | CELL 10, CELL 11, CELL 14, CELL 53 |
| BCF ingestion | CELL 13, CELL 14, OLD CELL 19 |
| FEI/model differential | CELL 12, OLD CELL 20, OLD CELL 21, OLD CELL 23 |
| Module 3 | OLD CELL 24, OLD CELL 25, OLD CELL 26, OLD CELL 27, OLD CELL 28, OLD CELL 30, OLD CELL 31, OLD CELL 34 |
| Routing | OLD CELL 36, OLD CELL 37, OLD CELL 38, OLD CELL 39, OLD CELL 40, OLD CELL 41, OLD CELL 42 |
| Covers late-week audit | OLD CELL 43 |
| Final decision board | OLD CELL 44, CELL 62 |
| Probability/pricing | CELL 46, CELL 47, CELL 48, CELL 51, CELL 52, CELL 53, CELL 54, CELL 55, CELL 56, CELL 57, CELL 57A, CELL 60, CELL 69 |
| Team totals (experimental) | CELL 58, OLD CELL 59, CELL 59A, CELL 60 |
| Final handoff/export | OLD CELL 45, CELL 61, CELL 61B, CELL 62, CELL 66, CELL 67, CELL 73 |
| Recovery/archive utilities | CELL 61B, CELL 66, CELL 67, CELL 73C |

## Cell inventory

Outputs include in-place DataFrame enrichment, not just newly assigned variables. Downstream references identify major consumers, not every print/display or transitive dependency.

| Position | Original label | Stage | Classification | Purpose | Major inputs | Major outputs | Major downstream dependencies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Unnumbered weekly configuration | configuration | MANUAL INPUT | Weekly season/week/date configuration and Colab secret lookup; startup checks require both API keys. | Colab userdata; weekly settings | YEAR, DATA_THROUGH_WEEK, TARGET_WEEK, TARGET_START_DATE, TARGET_END_DATE, CFBD_API_KEY, ODDS_API_KEY | CELL 2, CELL 4, CELL 6, CELL 13, Unnumbered key cleanup, CELL 51, CELL 53, CELL 54, CELL 58 |
| 2 | CELL 2 | CFBD acquisition | KEEP | Fetch completed-week play PPA and frozen season advanced statistics; aggregate offensive/defensive PPA and check acquisition. | Unnumbered weekly configuration settings; CFBD /plays and /stats/season/advanced | df_ppa_plays, df_ppa_valid, df_off_ppa, df_def_ppa, df_ppa, adv_json; status flags | CELL 3, OLD CELL 25 |
| 3 | CELL 3 | CFBD acquisition | KEEP | Flatten advanced metrics, merge PPA, build and validate the team efficiency matrix. | adv_json, df_ppa | df_adv, df_adv_clean, df_cfbd | CELL 10, CELL 11, OLD CELL 25 |
| 4 | CELL 4 | market acquisition | DELETE | Legacy Odds API slate request for DraftKings/FanDuel spreads and totals; replace normal acquisition after parity capture. | ODDS_API_KEY; Odds API | odds_json; response/book availability diagnostics | CELL 5 |
| 5 | CELL 5 | market acquisition | DELETE | Flatten legacy bookmaker markets and convert kickoff to Eastern time; preserve its output contract for replacement. | odds_json | df_market; DK/FD spread and total columns | CELL 6 |
| 6 | CELL 6 | market acquisition | KEEP | Filter and validate market card against configured target-week Eastern date window. | df_market; target dates/week | df_target_market | CELL 10, CELL 11, CELL 14, OLD CELL 26 |
| 7 | CELL 10 | team normalization | KEEP | Apply explicit Odds-team aliases plus normalization; check every home/away match against CFBD. | df_target_market, df_cfbd | TEAM_ALIASES, normalize_team_name, cfbd_teams; normalized columns on df_target_market | CELL 11, CELL 14; name contract for CELL 53 |
| 8 | CELL 11 | team normalization | KEEP | Merge home and away efficiency data into target market rows with cardinality checks and home-oriented EPA edge. | df_target_market, df_cfbd | df_master, home_cfbd, away_cfbd; Net_EPA_Edge_Home | CELL 12, OLD CELL 19 |
| 9 | CELL 12 | FEI/model differential | KEEP | Assign EPA edge side/value and established 0.12 trigger without changing polarity. | df_master.Net_EPA_Edge_Home | df_master enriched with EPA_Edge_Team, EPA_Edge_Value, EPA_Trigger | OLD CELL 19, OLD CELL 34, OLD CELL 41, CELL 47 |
| 10 | CELL 13 | BCF ingestion | MANUAL INPUT | Parse embedded weekly BCF CSV and validate required fields, numeric metrics, and duplicate teams. | bcf_csv; configured completed/target week | df_bcf_raw; FEI/OFEI/DFEI/SFEI/OAY/DAY columns | CELL 14 |
| 11 | CELL 14 | BCF ingestion; team normalization | KEEP | Map BCF names to CFBD while retaining raw names; validate slate coverage and normalized uniqueness. | df_bcf_raw, cfbd_teams, df_target_market | BCF_TO_CFBD, df_bcf | OLD CELL 19 |
| 12 | OLD CELL 19 | BCF ingestion | KEEP | Merge home/away BCF metrics into master card; validate complete one-to-one game coverage. | df_master, df_bcf | df_master_bcf; home/away FEI and related metrics | OLD CELL 20, OLD CELL 21, OLD CELL 23, OLD CELL 24, OLD CELL 26, OLD CELL 27, OLD CELL 28, OLD CELL 30, OLD CELL 31, OLD CELL 34, OLD CELL 36, OLD CELL 37, OLD CELL 38, OLD CELL 39, OLD CELL 40, OLD CELL 41, CELL 47 |
| 13 | OLD CELL 20 | FEI/model differential | KEEP | Convert FEI difference with multiplier 30 into home-oriented differential, favorite, and margin; validate polarity. | df_master_bcf home/away FEI | FEI_Model_Diff_Home, FEI_Model_Favorite, FEI_Model_Margin on df_master_bcf | OLD CELL 21, OLD CELL 23, CELL 47 |
| 14 | OLD CELL 21 | FEI/model differential | KEEP | Convert FEI margin to home spread and compare DK/FD lines, edge sides/values, and agreement. | df_master_bcf FEI differential and DK/FD spreads | FEI_Model_Home_Spread, DK/FD_FEI_Edge_Home/Team/Value, FEI_Books_Agree | OLD CELL 23, OLD CELL 34, OLD CELL 41, CELL 47 |
| 15 | OLD CELL 23 | FEI/model differential | KEEP | Identify DK/FD market favorites and FEI-versus-market favorite agreement. | df_master_bcf spreads, FEI favorite | DK/FD_Market_Favorite and agreement diagnostics on df_master_bcf | Enriched master carried into subsequent stages; primarily audit context |
| 16 | OLD CELL 24 | Module 3 | KEEP | Apply passing-down success/havoc thresholds to away/home negative matchup signals. | df_master_bcf passing-down SR and defensive havoc | Away/Home_Havoc_Trap; havoc_diagnostic | OLD CELL 31, OLD CELL 34 |
| 17 | Unnumbered key cleanup | configuration | DEVELOPMENT/AUDIT | Repeat API-key whitespace cleanup already performed by the unnumbered weekly configuration. | CFBD_API_KEY | CFBD_API_KEY overwritten; presence print | Later CFBD requests; no unique model output |
| 18 | OLD CELL 25 | CFBD acquisition; Module 3 | KEEP | Extract defensive line yards from existing frozen advanced payload; refresh df_cfbd rather than fetch new data. | adv_json, df_cfbd | df_def_lineyards; df_cfbd with Def_LineYards | OLD CELL 26 |
| 19 | OLD CELL 26 | Module 3 | KEEP | Refresh home/away defensive line yards into the existing enriched master, preserving game count. | df_cfbd, df_master_bcf; df_target_market for validation | df_master_bcf refreshed with Away/Home_Def_LineYards | OLD CELL 27 |
| 20 | OLD CELL 27 | Module 3 | KEEP | Apply offensive ≥3.5 and opposing defensive ≥3.3 line-yards push thresholds. | df_master_bcf offensive/defensive line yards | Away/Home_LineYards_Push; lineyards_diagnostic | OLD CELL 31, OLD CELL 34 |
| 21 | OLD CELL 28 | Module 3 | KEEP | Flag explosiveness fraud with established explosiveness/success-rate thresholds. | df_master_bcf offensive explosiveness/SR and opposing defensive SR | Away/Home_Explosiveness_Fraud; fraud_diagnostic | OLD CELL 31, OLD CELL 34 |
| 22 | OLD CELL 30 | Module 3 | KEEP | Apply established OAY-high/DAY-weak matchup thresholds. | df_master_bcf home/away OAY and DAY | Away/Home_OAY_DAY_Edge; oay_day_diagnostic | OLD CELL 31, OLD CELL 34 |
| 23 | OLD CELL 31 | Module 3 | DEVELOPMENT/AUDIT | Build descriptive per-team signal lists/counts; not the corrected directional convergence calculation. | df_master_bcf flags from OLD CELL 24, OLD CELL 27, OLD CELL 28, OLD CELL 30 | df_module3_board, active_module3 | Human audit; OLD CELL 34 reads master directly, not this board |
| 24 | OLD CELL 34 | Module 3 | KEEP | Require EPA/DK-FEI directional agreement; orient own positives/opponent negatives as support, reverse as conflict. | df_master_bcf EPA/FEI sides, values, Module 3 flags | df_convergence_corrected with shared side and support/conflict counts/text | OLD CELL 36 |
| 25 | OLD CELL 36 | routing | KEEP | Create market-route strings from corrected support/conflict; mark unpriced status and derivative preferences. | df_convergence_corrected | df_market_routes | OLD CELL 37, OLD CELL 38, OLD CELL 39 |
| 26 | OLD CELL 37 | routing | KEEP | Compute consensus spread, nearest keys/proximity, and spread-size buckets; render routed structure. | df_master_bcf DK/FD spreads, df_market_routes | df_master_bcf spread structure; df_routed_market_structure; spread_bucket | OLD CELL 38, OLD CELL 39; bucket helper later redefined by CELL 52/CELL 55 |
| 27 | OLD CELL 38 | routing | KEEP | Classify favorite and ≥16.5/≥20.5 spreads; produce routed diagnostic. | df_master_bcf consensus spread, df_market_routes | Favorite_Spread_Size and large-spread flags; df_large_spread_routed; threshold globals | OLD CELL 39 |
| 28 | OLD CELL 39 | routing | KEEP | Apply large-spread route additions then conflict override; preserve precedence and route de-duplication order. | df_market_routes, df_master_bcf favorite size; OLD CELL 38 thresholds | df_final_routes | OLD CELL 40, OLD CELL 44 |
| 29 | OLD CELL 40 | routing | KEEP | Separate matchup evidence classes from routing modifiers so spread size is not model evidence. | df_final_routes | df_evidence_routes | OLD CELL 41 |
| 30 | OLD CELL 41 | routing | KEEP | Calculate full-slate EPA/FEI percentiles and conservative book edge; shortlist agreement games by support, strength, or conflict. | df_master_bcf, df_evidence_routes | df_phase1_diagnostic, candidate_board; EPA/FEI percentile globals | OLD CELL 42 |
| 31 | OLD CELL 42 | routing | KEEP | Classify candidates for late-week review using ordered reasons. | candidate_board | df_phase1_review | OLD CELL 43, OLD CELL 44, CELL 47 |
| 32 | OLD CELL 43 | Covers late-week audit | MANUAL INPUT | Parse embedded Covers open/current home spreads; require review-game coverage; compute movement, relationship, and strict key crossing. | covers_csv, df_phase1_review | df_covers, covers_audit; movement/key fields | OLD CELL 44 |
| 33 | OLD CELL 44 | final decision board | KEEP | Combine review, routes, and Covers audit; assign ordered final statuses and human notes. | df_phase1_review, df_final_routes, covers_audit | df_final_decision | OLD CELL 45, CELL 46, CELL 48, CELL 66 |
| 34 | OLD CELL 45 | final handoff/export | KEEP | Build sorted compact phase-1 Gem export and CSV text; later full context needs this board. | df_final_decision | df_gem_export, gem_csv | CELL 66; human copy/paste |
| 35 | CELL 46 | probability/pricing | OPTIONAL/FALLBACK | Manual pricing CSV validation path; header-only default prints awaiting-input status. | pricing_csv; df_final_decision when prices exist | df_pricing; df_pricing_valid on populated valid path | Manual audit path; CELL 55/OLD CELL 59 instead consume df_auto_pricing, not this output |
| 36 | CELL 47 | probability/pricing | KEEP | Fit EPA to current market with polyfit; equal EPA/FEI blend and retention variants; nominal diagnostic is consumed downstream. | df_master_bcf; df_phase1_review | df_prob_model, df_phase1_shrinkage; Shrunk_Home_Spread_*; beta/intercept | CELL 48, CELL 66 |
| 37 | CELL 48 | probability/pricing | KEEP | Use 40% retained model spread in model-side orientation; calculate cushion and intervening/adverse keys. | df_phase1_shrinkage, df_final_decision | df_key_value; retained line, cushion, routes, line-value status | CELL 52, CELL 53, CELL 55, OLD CELL 59, CELL 66 |
| 38 | CELL 51 | probability/pricing; CFBD acquisition | KEEP | Acquire 2021–2025 historical games/lines with provider priority; construct closing-spread error dataset. | CFBD_API_KEY; CFBD historical games/lines | df_hist_spread, spread_error; historical diagnostics | CELL 52, CELL 55, CELL 56, CELL 57, CELL 57A, CELL 69 |
| 39 | CELL 52 | probability/pricing | KEEP | Estimate empirical global/bucket win/push/loss at retained cushion; conservative cover diagnostic; define shared helpers. | df_hist_spread, df_key_value | df_cover_prob; df_hist_spread.Spread_Bucket; empirical_probability, spread_bucket | CELL 55, CELL 56, CELL 57, CELL 57A use history/buckets; CELL 69 requires empirical_probability |
| 40 | Empty / no label | recovery/archive utilities | DELETE | Empty code cell; no operation or content to extract. | None | None | None |
| 41 | CELL 53 | market acquisition; probability/pricing | OPTIONAL/FALLBACK | Legacy Odds API event matching and FD/DK market discovery for model-routed games. | ODDS_API_KEY, df_key_value; Odds API events/market endpoints | df_odds_events, df_event_match, df_market_discovery, df_market_request_log | CELL 54 |
| 42 | CELL 54 | market acquisition; probability/pricing | OPTIONAL/FALLBACK | Legacy Odds API main/alternate spread, team-total, and first-half price pull and partitioning. | df_event_match, ODDS_API_KEY; explicit bookmaker/market lists | df_auto_pricing, df_pricing_pull_log, df_full_game_spreads, df_team_total_prices, df_first_half_prices | CELL 55, OLD CELL 59 |
| 43 | CELL 55 | probability/pricing | KEEP | Filter routed model-side full-game offers; empirical cover estimate, price/cushion/key filters; de-duplicate and compact shortlist. | df_auto_pricing, df_key_value, df_hist_spread | df_spread_shortlist, global_errors; redefined spread_bucket | CELL 56, CELL 57; global_errors required by CELL 69 |
| 44 | CELL 56 | probability/pricing | DEVELOPMENT/AUDIT | Calculate global/local historical key landing rates; optionally add key-tax context to shortlist. | df_hist_spread; df_spread_shortlist if present | df_key_global, df_key_local, df_key_tax, key_tax_lookup; shortlist audit columns | CELL 57 may carry context; key tax is not a separate push probability |
| 45 | CELL 57 | probability/pricing | KEEP | Recompute candidate-oriented global/bucket W/P/L with the 300-observation source gate, break-even and ROI; remove staking fields and validate probability sums. | df_spread_shortlist, df_hist_spread; bucket labels | df_ev; pricing status/warnings; odds helpers | CELL 57A, then CELL 61, CELL 62, CELL 67, CELL 69 |
| 46 | CELL 57A | probability/pricing | KEEP | Estimate integer-line push probability locally; redistribute nonpush mass and recompute ROI in place. | df_ev, df_hist_spread | df_ev with Push_Adjusted_* and historical push fields; estimate_push_probability | CELL 61, CELL 62, CELL 67, CELL 69 |
| 47 | CELL 58 | team totals; CFBD acquisition | KEEP | Build historical implied team totals and errors from one provider with both spread and total; inspect seasonal/home-away balance. | CFBD_API_KEY; historical CFBD games/lines, 2021–2025 | df_hist_team_total; experimental calibration summaries | OLD CELL 59, CELL 59A |
| 48 | OLD CELL 59 | team totals | KEEP | Expand explicit directional routes; retained-model adjustment, market TT anchors, empirical probability and useful-offer shortlist. | df_auto_pricing, df_key_value, df_hist_team_total | df_tt_routes, df_tt_anchors, df_tt_shortlist | CELL 59A |
| 49 | CELL 59A | team totals | KEEP | Validate directional support; quarantine qualitative rows; estimate integer pushes and rebuild final W/P/L. | df_tt_shortlist, df_hist_team_total | df_tt_validated; TT_Quantitative_Status, TT_Final_*; quant_board, qual_board | CELL 60, CELL 61, CELL 62 |
| 50 | CELL 60 | team totals; probability/pricing | KEEP | Price quantitative TT rows only; ROI/status/warnings without stakes; retain qualitative reminder. | df_tt_validated | df_tt_ev; TT_Expected_ROI and pricing diagnostics; redefined odds helpers | CELL 61, CELL 62 |
| 51 | CELL 61 | final handoff/export | KEEP | Unify push-adjusted spreads and quantitative/qualitative TTs; standardize schema; build complete handoff and review subset. | df_ev after CELL 57A, df_tt_ev, df_tt_validated | df_cfb1_gem_handoff, df_cfb1_gem_review | CELL 61B |
| 52 | CELL 61B | final handoff/export; recovery/archive utilities | KEEP | Snapshot complete pricing handoff before decision-card compression. | df_cfb1_gem_handoff | CFB1_FULL_CONTEXT_V1, CFB1_FULL_CONTEXT_V1_CSV | CELL 62, CELL 66 |
| 53 | CELL 62 | final decision board; final handoff/export | KEEP | Build primary/value-alternative spread/TT cards plus qualitative TT rows; require push-adjusted spreads. | df_ev, df_tt_ev, df_tt_validated, CFB1_FULL_CONTEXT_V1 | CFB1_DECISION_CARD_V1, CFB1_DECISION_CARD_V1_CSV | CELL 66, CELL 67, CELL 73 |
| 54 | CELL 66 | final handoff/export; recovery/archive utilities | KEEP | Enrich V1 pricing with phase-1/model/market/key context; retain unpriced background games and decision inclusion flag. | df_gem_export, df_phase1_shrinkage, df_key_value, CFB1_FULL_CONTEXT_V1, CFB1_DECISION_CARD_V1; df_final_decision if available | CFB1_FULL_CONTEXT_V2, CFB1_FULL_CONTEXT_V2_CSV; cfb1_full_context_v2.csv | CELL 67 |
| 55 | CELL 67 | final handoff/export | KEEP | Synchronize final spread metrics from canonical push-adjusted df_ev using unique price keys; validate against decision card and export/download. | CFB1_FULL_CONTEXT_V2, CFB1_DECISION_CARD_V1, df_ev | CFB1_FULL_CONTEXT_FINAL; cfb1_full_context_final.csv; decision_card_text | CELL 69, CELL 73, CELL 73C, CELL 73 export |
| 56 | CELL 69 | probability/pricing | OPTIONAL/FALLBACK | Define selective live spread recalculation for manually supplied current line/price; no automatic game run or new model fit. | df_ev, df_hist_spread, spread_error, global_errors, spread_bucket, empirical_probability, estimate_push_probability, CFB1_FULL_CONTEXT_FINAL; call arguments | cfb1_live_spread_recalc; result DataFrame only when called | On-demand review; not required by CELL 73 |
| 57 | CELL 73 | final handoff/export | KEEP | Merge actual decision card with final game context into Architect schema; validate qualitative rows and exclude staking fields. | CFB1_DECISION_CARD_V1, CFB1_FULL_CONTEXT_FINAL | CFB1_ARCHITECT_HANDOFF; cfb1_architect_handoff.csv | Bet Slip Architect consumer |
| 58 | CELL 73C | recovery/archive utilities | OPTIONAL/FALLBACK | Restore frozen full context from first lexicographically sorted matching /content CSV; no API calls. | /content/*cfb1_full_context_final*.csv | FULL_CONTEXT_PATH; CFB1_FULL_CONTEXT_FINAL overwritten from CSV | Recovery consumer only; does not restore df_ev/history/decision card for CELL 69, CELL 73 |

## Duplicate, diagnostic, and development sections

- Unnumbered key cleanup repeats whitespace trimming in the unnumbered weekly configuration.
- OLD CELL 31 is a descriptive signal-count board. OLD CELL 34 independently computes corrected directional convergence from master flags; these are not interchangeable algorithms.
- CELL 46 validates manual pricing, while CELL 53 and CELL 54 populate the automatic Odds API path. `df_pricing_valid` is not a drop-in replacement for `df_auto_pricing`.
- CELL 47 and CELL 48 are titled diagnostics but supply retained model lines to downstream probability, experimental team-total, and full-context calculations.
- CELL 52 and CELL 55 use minimum global/bucket cover probabilities for diagnostics/filtering. CELL 57 selects the bucket triplet only with `Historical_Bucket_N >= 300` and a nonempty matching bucket; otherwise it uses global probabilities. Do not conflate these stages.
- CELL 56 audits historical key landing rates and modifies shortlist audit columns. CELL 57A separately estimates integer-line push mass. Key-tax audit values are not an extra push penalty in expected ROI.
- `spread_bucket` is repeated in OLD CELL 37, CELL 52, and CELL 55. Odds/probability helpers are also repeated. Compare definitions and their late-bound global uses before consolidating them.
- OLD CELL 45, CELL 61, CELL 62, CELL 66, CELL 67, and CELL 73 create distinct output views. CELL 61B snapshots pricing context; CELL 66 restores rich/background context; CELL 67 synchronizes canonical CELL 57A metrics.
- CELL 73C restores `CFB1_FULL_CONTEXT_FINAL` from the first sorted matching `/content` filename. It does not restore all globals needed by CELL 69 or CELL 73 and belongs outside the production pipeline.

## Tight coupling and migration hazards

- **CELL 2 / CELL 3 / CELL 10 / CELL 11 / CELL 12 / CELL 13 / CELL 14 / OLD CELL 19 / OLD CELL 25 / OLD CELL 26:** evolving master tables, raw versus canonical team names, and defensive-line-yards refresh must preserve sequencing, merge cardinality, and home/away identity.
- **CELL 12 / OLD CELL 20 / OLD CELL 21 / OLD CELL 24 / OLD CELL 27 / OLD CELL 28 / OLD CELL 30 / OLD CELL 34 / OLD CELL 36:** preserve specifically DK FEI agreement, opponent-negative support, and signal ordering. OLD CELL 31 is not the convergence algorithm.
- **OLD CELL 36 through OLD CELL 42 (only the labeled cells present):** preserve route precedence, full-slate percentile population, evidence-versus-routing separation, and conflict overrides.
- **OLD CELL 42 / OLD CELL 43 / OLD CELL 44 / OLD CELL 45 / CELL 47 / CELL 48:** the late-week audit, decision statuses, full-slate EPA fit, and retained-line comparisons share game identities and line snapshots. Pasted Covers rows are historical input; preserve the audit calculations, not a fixed weekly slate.
- **CELL 51 / CELL 52 / CELL 55 / CELL 56 / CELL 57 / CELL 57A:** preserve historical provider selection, bucket boundaries, probability-source selection, home/away error orientation, and push-adjusted metrics. Supply captured or external pricing at the boundary; Odds API is not a required production dependency.
- **CELL 58 / OLD CELL 59 / CELL 59A / CELL 60:** preserve experimental calibration, route direction, anchor selection, half-cushion adjustment, qualitative eligibility, and push handling together. This behavior lock does not validate the experimental method.
- **CELL 57A / CELL 61 / CELL 61B / CELL 62 / CELL 66 / CELL 67 / CELL 73:** use canonical spread metrics and unique priced-row keys across output views; retain qualitative nulls and background context. No staking, Kelly, bankroll, promo, parlay, or portfolio ownership moves into CFB1.
- **CELL 69 with CELL 51 / CELL 52 / CELL 55 / CELL 57A / CELL 67:** live recalculation closes over globals and helper definitions; a recovered CSV alone is insufficient.

Colab-specific adapters include `google.colab.userdata`, `display`, `google.colab.files.download`, and `/content` paths. Adapt those boundaries separately from deterministic calculations. Numerical parity is unvalidated until coherent historical payloads, manual inputs, pricing fixtures, and known Colab outputs are compared. See `BEHAVIOR_LOCK.md` for source-derived formulas and validation gates.

