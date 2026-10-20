# CFB1 retained spread, probability, and supplied-price ROI contract

## Authority and scope

The source is `legacy/CFB1_Colab_Reference.ipynb`, SHA256
`94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`.
The actual embedded labels are:

| Label | Source heading | Extracted function |
| --- | --- | --- |
| CELL 47 | BLENDED MODEL + SHRINKAGE | `probability.fit_retained_lines` |
| CELL 48 | KEY-NUMBER LINE VALUE DIAGNOSTIC | `probability.model_side_line_value` |
| CELL 51 | HISTORICAL SPREAD-ERROR DATASET | `spread_history.build_spread_history` (normalization only) |
| CELL 52 | EMPIRICAL COVER PROBABILITY | `probability.cover_probability_board` |
| CELL 55 | SMART FULL-GAME SPREAD FILTER | `valuation.shortlist_supplied_spreads` |
| CELL 57 | FULL-GAME SPREAD EV / PRICING | `probability.candidate_probabilities`, `valuation.value_supplied_spreads` |
| CELL 57A | INTEGER-LINE PUSH ADJUSTMENT | `probability.adjust_push_probabilities`, `valuation.value_push_adjusted_spreads` |

These are CELL labels, not OLD CELL labels. OLD CELL 43/44 have already been
migrated separately. Their readiness and warning semantics are unchanged.
CELL 56's separate historical key-tax diagnostic is not subtracted from EV.
CELL 69's optional selective live-check workflow is not this weekly calculation
pipeline; neither its acquisition nor its alternate selection rules are migrated.
Experimental team totals (CELL 58 onward) and final handoff/export are excluded.

The current migration instruction explicitly assigns retained lines, calibrated
probability, break-even and expected ROI **when a price is supplied** to CFB1.
This supersedes older behavior-lock/map ownership prose that assigned ROI to Bet
Slip Architect. Architect retains normal-workflow price acquisition/selection,
Kelly, staking, bankroll allocation, promo construction, parlays and portfolio
choices. The new modules accept supplied tables; they perform no HTTP, Odds API,
price discovery, timestamp invention or stake recommendation.

## CELL 47: retained model line

Input `df_master_bcf` needs `Home_Team`, `Away_Team`, `Net_EPA_Edge_Home`,
`FEI_Model_Home_Spread`, `DK_Spread`, `FD_Spread`. `df_phase1_review` supplies
`Game`, `Model_Side`, `Review_Class`. Functions receive these objects explicitly
instead of relying on notebook globals; inputs are copied.

1. `Consensus_Home_Spread = mean(DK_Spread, FD_Spread)` row-wise, pandas default
   skip-null behavior, without rounding. One available book suffices; two nulls
   yield null. `Market_Home_Margin = -Consensus_Home_Spread`.
2. Cast EPA edge and market margin to float. On rows where both are nonnull,
   `beta, intercept = np.polyfit(EPA_edge, Market_Home_Margin, 1)`.
   Fit the entire master slate, **not just Phase 1**. No additional fit-quality,
   minimum-sample or rank gate is invented; NumPy failure/warning behavior remains.
3. `EPA_Model_Home_Margin = intercept + beta * Net_EPA_Edge_Home`;
   `EPA_Model_Home_Spread = -EPA_Model_Home_Margin`.
4. `FEI_Model_Home_Margin = -FEI_Model_Home_Spread`.
5. `Blended_Home_Margin_Raw = .5 * EPA_Model_Home_Margin + .5 * FEI_Model_Home_Margin`;
   `Blended_Home_Spread_Raw = -Blended_Home_Margin_Raw`.
6. `Blended_Edge_Home_Raw = Consensus_Home_Spread - Blended_Home_Spread_Raw`.
7. For `r` in `.25, .40, .50, .60`, label `n = int(100*r)`:
   `Edge_Retained_n = r * Blended_Edge_Home_Raw`;
   `Shrunk_Home_Spread_n = Consensus_Home_Spread - Edge_Retained_n`.

Left-join the three review fields using `Away_Team + ' at ' + Home_Team` against
`Game`; no deduplication/merge validation is added here. Like the source, the
master should not already contain colliding review fields such as `Game`.
Phase 1 rows are those whose joined Game occurs in the review Game set;
`Raw_Edge_Size = abs(Blended_Edge_Home_Raw)` is added only to that subset.
`RetainedLines.full_slate` corresponds to `df_prob_model`, `.phase1` to
`df_phase1_shrinkage`; `.beta` and `.intercept` expose the fit. Missing required
master columns raise ValueError. Null model inputs propagate into model lines.
The source displays rounded copies at two decimals; stored calculations retain
precision. CELL 47 says no retention factor locked; CELL 48 explicitly selects 40%.

## CELL 48: model-side line and barriers

Use `df_phase1_shrinkage` fields `Game`, `Model_Side`, `Home_Team`, `Away_Team`,
`Shrunk_Home_Spread_40`. Left-join `df_final_decision` fields `Game`,
`Current_Home_Spread`, `Decision_Status`, `Eligible_Market_Routes` with
`validate='one_to_one'`; duplicate keys fail. Missing joins are retained.

For a home model side, `Market_Model_Spread = Current_Home_Spread` and
`Retained_Model_Spread = Shrunk_Home_Spread_40`; negate both for the away model
side. An unrecognized model side produces NaNs.
`Model_Cushion_Points = round(Market_Model_Spread - Retained_Model_Spread, 2)`
uses pandas rounding, and is a genuine stored rounding operation.

`Keys_Between_Market_And_Model` contains sorted distinct absolute keys whose
signed values lie strictly inside the two line endpoints, from
`[-14,-10,-7,-3,3,7,10,14]`. Serialize comma-separated magnitudes, or empty string.
This is model-versus-market structure, **not temporal opener crossing**.
`Key_Barrier_Present` is whether the string is nonempty. `Next_Adverse_Key`
exists only for a negative market-model spread: the first of `[3,7,10,14]`
strictly greater than its magnitude, else NaN (also NaN for dogs/even).

`Line_Value_Status` precedence: null cushion -> `CHECK`; cushion <= 0 ->
`NO_RETAINED_MODEL_EDGE`; positive with barrier -> `EDGE_WITH_KEY_BARRIER`;
otherwise `EDGE_NO_KEY_BARRIER`. `Key_Tradeoff_Note` retains the exact source
strings. Other output columns are the inputs and joined decision fields above.
No line-status eligibility filter is applied at this step.

## CELL 51: historical calibration normalization, no acquisition

The notebook requests CFBD `/lines` for each year 2021–2025 inclusive,
`seasonType=regular`, authenticated using its configured key, timeout 30 seconds.
The extracted deterministic function does **not** request that endpoint. A caller
must supply all five integer-keyed year arrays, with regular-season scope and
payload vintage/provenance established externally. Missing years fail. Extra
years are ignored; there is no automatic 2026 inclusion or rolling-year change.

Include only rows whose `homeClassification` and `awayClassification` lowercase
to `fbs`, both scores are nonnull, and an eligible nonnull spread exists. Select
the first line by provider precedence `DraftKings`, `ESPN Bet`, `Bovada`,
independent of provider array order. No deduplication, imputation or numeric
string conversion is added. For each retained row:

- `Actual_Home_Margin = homeScore - awayScore`.
- `Market_Expected_Home_Margin = -spread`.
- `Spread_Error = Actual_Home_Margin - Market_Expected_Home_Margin`.
- `ATS_Result`: error > 0 `HOME_COVER`, < 0 `AWAY_COVER`, exactly zero `PUSH`.

Output `df_hist_spread` column order: `Season`, `Week`, `Game_ID`, `Away_Team`,
`Home_Team`, `Away_Score`, `Home_Score`, `Provider`, `Closing_Home_Spread`,
`Actual_Home_Margin`, `Market_Expected_Home_Margin`, `Spread_Error`, `ATS_Result`.
Season comes from the requested year, other identifiers from the payload.
There is no fixed-count PASS condition; counts/statistics are diagnostics.
No original calibration rows are reconstructed from aggregate summaries.

## CELL 52: empirical probability board

No normal/logistic distribution or fitted sigma is introduced. Let `errors` be
historical `Spread_Error`, global samples drop null and cast float. For a home
model side use `errors`, for away use `-errors`. Add the **rounded CELL 48 cushion**.
Win/push/loss are the sample fractions strictly > 0, exactly == 0, strictly < 0.
No epsilon is used for push comparison. Null cushion or empty samples yield NaNs.

Spread buckets use the absolute home closing line for history and the absolute
model-side market line for the board:

| Upper bound (exclusive) | Label |
| --- | --- |
| 3 | UNDER_3 |
| 7 | 3_TO_6.5 |
| 10 | 7_TO_9.5 |
| 14 | 10_TO_13.5 |
| 17 | 14_TO_16.5 |
| 21 | 17_TO_20.5 |
| otherwise | 21_PLUS |

Thus exact 3/7/10/14/17/21 enter the next bucket. The source's final else also
assigns a NaN magnitude to 21_PLUS; no new missing-line classifier is invented.
Bucket errors here drop null and cast float; `Historical_Bucket_N` is their count.
Outputs: `Game`, `Model_Side`, `Market_Model_Spread`, `Retained_Model_Spread`,
`Model_Cushion_Points`, `Spread_Bucket`, `Historical_Bucket_N`,
`Global_Cover_Prob`, `Global_Push_Prob`, `Global_Loss_Prob`,
`Bucket_Cover_Prob`, `Bucket_Push_Prob`, `Bucket_Loss_Prob`, `Line_Value_Status`,
`Decision_Status`, `CFB1_Cover_Prob_V1`.
`CFB1_Cover_Prob_V1` is pandas row minimum of global and bucket **win only**
(skip-null default). It is not a selected normalized W/P/L triplet.
The function returns `(history_with_Spread_Bucket, board)` and mutates neither input.
Display percentages round to one decimal, not stored values. No source sum gate here.

## CELL 55: externally supplied candidate eligibility

Supplied offers need `Game`, `Market_Type`, `Team`, `Sportsbook`, `Line`,
`American_Odds`. For later CELL 57 they must also carry `Home_Team`; CELL 55's
model-info merge does not add it. Avoid colliding joined model-info fields on
supplied offers (the source merge would suffix them). There is no team resolver,
market parser, price acquisition or independent freshness certification here.

Filter/order is preserved:

1. `Market_Type == FULL_GAME_SPREAD` (case-sensitive).
2. Inner join on Game to CELL 48's `Game`, `Model_Side`, `Market_Model_Spread`,
   `Retained_Model_Spread`, `Line_Value_Status`, `Decision_Status`,
   `Eligible_Market_Routes`; Team must equal Model_Side exactly.
3. Eligible routes must contain FULL_GAME_SPREAD, case-insensitive string match.
4. Supplied odds must lie in **inclusive [-250,300]**.
5. `Candidate_Cushion = Line - Retained_Model_Spread`, unrounded, must be >= -.5.
6. Compute global and bucket win fractions as above, bucket selected using
   abs(candidate Line), dropping null history errors. `CFB1_Cover_Prob` is Python
   `min(global_win, bucket_win)` (including literal NaN ordering behavior).
7. Calculate supplied-odds `Break_Even_Prob` and `Probability_Edge` below.
8. Candidate Line must be inclusively between `min(market,model)-.5` and
   `max(market,model)+.5`.
9. Sort American odds descending; deduplicate `(Game,Team,Line)`, retaining first.
   `Abs_From_Main = abs(Line - Market_Model_Spread)`.
10. Per Game combine nearest three lines, highest three probability edges, all
    nonempty key-tradeoff rows; drop duplicate rows, sort Line descending, take six.

`Key_Tradeoff` applies only when market and candidate are both favorites (< 0)
and candidate has larger magnitude: check OFF_KEY first (start within strictly
.001 of 3/7/10/14), then strict interior CROSSES (join all keys with underscores),
then LANDS_ON_KEY (candidate within strictly .001). Examples: `OFF_KEY_3`,
`CROSSES_3_7`, `LANDS_ON_KEY_7`; otherwise empty string. This is candidate-versus-
main-line comparison, not opener movement. No tax is deducted from expected ROI.

`df_spread_shortlist` retains supplied and joined fields plus `Candidate_Cushion`,
`Global_Cover_Prob`, `Bucket_Cover_Prob`, `CFB1_Cover_Prob`, `Break_Even_Prob`,
`Probability_Edge`, `Key_Tradeoff`, `Abs_From_Main`.
**The source does not attach Spread_Bucket or Historical_Bucket_N here.** Therefore
the normal resulting CELL 57 flow selects GLOBAL unless the caller already
supplied those fields. This metadata gap is preserved, not silently repaired.
Display rounding only: probabilities one decimal percent, final display two
decimals. Empty-filter assignment failures and malformed input behavior are not
replaced with fabricated probability rows. Pandas <3 remains pinned because the
source groupby-apply retains grouping columns (it emits a deprecation warning).

## CELL 57: selected W/P/L and supplied-price economics

Explicit required shortlist fields are `Game`, `Team`, `Sportsbook`, `Line`,
`American_Odds`, `Candidate_Cushion`; orientation additionally requires Home_Team.
Team/home comparison casts both to strings. Global errors drop null and cast float.
Bucket samples are used only if candidate Spread_Bucket matches a nonempty
history bucket; unlike CELL 52, CELL 57 **does not drop null bucket errors**.

Compute both triplets using `oriented_errors + Candidate_Cushion`. Choose the
entire bucket triplet only when supplied `Historical_Bucket_N >= 300`, the
candidate bucket exists, and matching bucket history is nonempty. Otherwise use
the entire global triplet. Count metadata is not recalculated. `Probability_Source`
is `SPREAD_BUCKET` or `GLOBAL`. This replaces the prior diagnostic win minimum;
it does not splice minimum wins with a different push/loss sample.

Outputs include `Global_Win_Prob`, `Global_Push_Prob`, `Global_Loss_Prob`,
`Bucket_Win_Prob`, `Bucket_Push_Prob`, `Bucket_Loss_Prob`, `Probability_Source`,
`CFB1_Win_Prob`, `CFB1_Push_Prob`, `CFB1_Loss_Prob`, and `CFB1_Cover_Prob` as a
compatibility alias of selected win probability. Inputs are retained.

For supplied American odds `o`, cast float:

- `Profit_Multiple = o/100` if o > 0, else `100/abs(o)`.
- `Break_Even_Prob = abs(o)/(abs(o)+100)` if o < 0, else `100/(o+100)`.
- `Probability_Edge = CFB1_Win_Prob - Break_Even_Prob`.
- `EV_Per_Dollar = CFB1_Win_Prob * Profit_Multiple - CFB1_Loss_Prob`.
- `Expected_ROI = EV_Per_Dollar`.

ROI is **unconditional per original unit stake**: wins receive net profit, losses
lose one, pushes refund stake and contribute zero. It is not divided by 1-P.
The probability-edge diagnostic remains unconditional W minus the two-outcome
break-even probability even when pushes exist; it need not share ROI's sign.
No commission, vig removal, odds rounding, key tax or price-age rule is added.
Odds zero raises division by zero in profit_multiple although break_even_prob(0)
returns 1. Malformed strings raise ValueError, NaN odds propagate to NO_EV. Do not
interpret these literal behaviors as production validation of invalid odds.

`EV_Status`: NaN ROI -> NO_EV; ROI >= .05 STRONG_PRICE_EDGE; >= .03 POSITIVE_EV;
> 0 THIN_POSITIVE_EV; otherwise NON_POSITIVE_EV. These comparisons are inclusive
at .03/.05. `Decision_Warning` joins nonempty Key_Tradeoff and decision status if
MARKET_CONFLICT or STRONG_MARKET_CONFLICT with ` | `; no new routing decision.
The legacy Kelly/stake columns are dropped if supplied, never calculated.

PASS gates: all selected W+P+L satisfy `np.isclose(sum,1,atol=1e-9)` with NumPy's
**default rtol**, and no legacy staking columns remain. Empty/NaN probabilities
fail. Null bucket samples can therefore fail when selected. Display copies round
W/P/L, break-even and ROI to two-decimal percentages; stored values are unrounded.

## CELL 57A: literal integer-line push adjustment

Required valued rows contain `Line`, `Team`, `Home_Team`, base `CFB1_Win_Prob`,
`CFB1_Loss_Prob`; economics also requires `Profit_Multiple`. History must contain
`Closing_Home_Spread`, `Actual_Home_Margin` for integer lines.

`float(Line).is_integer()` determines push eligibility, no tolerance; missing
line is noninteger. Noninteger or no comparable rows -> H=0, N=0.
For integer line, target `t = abs(int(round(float(Line))))`; comparables satisfy
`abs(Closing_Home_Spread)` in **inclusive [t-1,t+1]**. Push rate H is fraction
whose Actual_Home_Margin equals +t for model-home, -t for model-away.
**This literal rule does not invert target sign for a positive candidate line.**
The potential underdog interpretation limitation is preserved explicitly; no
formula correction is hidden in extraction. The window applies to every integer,
not a separate hard-coded key-number push table.

Let B=W+L. If B>0, win_share=W/B, loss_share=L/B; otherwise NaNs.
`Historical_Push_Prob=H`, `Historical_Push_N=N`;
`Push_Adjusted_Win_Prob=(1-H)*win_share`;
`Push_Adjusted_Push_Prob=H`;
`Push_Adjusted_Loss_Prob=(1-H)*loss_share`.
Thus half-point lines remove base empirical push mass and renormalize W/L.
`Push_Adjusted_EV_Per_Dollar = adjusted_W * Profit_Multiple - adjusted_L`;
`Push_Adjusted_ROI` is its alias, still per original stake with push refunds.
`Break_Even_Prob` is unchanged. Base `EV_Status`, Probability_Edge and warnings
are retained; **EV_Status is not recomputed from adjusted ROI**.
Same np.isclose sum gate and absent-staking-column PASS gate. B=0 fails; no new
fallback is introduced. Stored precision is retained; display percentages use two decimals.

## Offline and historical validation

`tests/test_probability_roi.py` contains 60 tests: fit/blend/retention, home/away/
even, nulls, one-book consensus, strict keys, duplicate joins; fixed years/FBS/
provider selection; empirical monotonicity and bucket boundaries; global/bucket
selection at N=299/300; missing data gates; odds conversion, EV signs/boundaries,
push refunds, eligibility/deduplication/tradeoffs; integer windows and literal
orientation; preserved warnings; absence of acquisition/staking; and parity.

Literal parity executes the actual frozen CELL 47/48/51/52/55/57/57A sources on
identical controlled inputs. CELL 51 HTTP is stubbed with supplied synthetic
payloads and asserted to use five regular-season year parameters. No network
requests occur. All seven cells match the extracted outputs, including both
GLOBAL and SPREAD_BUCKET, then push-adjusted economics. The full 57-game
historical-input CELL 47 replay also matches the notebook on identical inputs.

Fixtures:

- `spread_calibration_controlled.json`: explicitly controlled synthetic five-year
  payloads, 20 games; not historical observed calibration data.
- `probability_notebook_checkpoint.json`: saved output tables/streams, source hash,
  display precision and provenance limits. These are expected outputs, not a
  reconstructed 3730-row history or new real-market observations.

Historical saved evidence and limits:

| Check | Result / scope |
| --- | --- |
| CELL 47 historical replay | 57 full-slate / 14 Phase 1; beta 38.0159014602, intercept 4.7524057182 versus saved displayed 38.04 / 4.75 |
| Retained 40% line comparisons | 11/14 within saved two-decimal precision; 3 differ: Tennessee–Arkansas 15.973480 vs 15.98; Nevada–UTEP 11.843370 vs 11.85; James Madison–Georgia Southern 11.352050 vs 11.32 |
| Drift explanation | Earlier contracts document upstream UConn/Temple and JMU/Georgia Southern EPA differences. Full-slate regression propagates changed inputs into other retained lines. Identical-input parity still passes; no formula altered to force historical equality. |
| CELL 48 isolated saved-input replay | All 14 numeric rows match display precision; all saved barrier strings, line-value and decision classifications match, using saved six-decimal retained lines from CELL 52 and archived OLD CELL 44 inputs |
| CELL 51 | Saved annual counts sum to 3730; 20 saved sample errors satisfy the exact margin/spread identity. Full original 3730 rows are absent. |
| CELL 52 | All 14 saved conservative win minima match displayed global/bucket values; empirical full-history recomputation cannot be claimed. |
| CELL 57 | All 47 saved break-even and ROI rows pass arithmetic checks with propagated display-rounding tolerance (BE .000050001 probability, ROI .0003). Saved W/P/L sums pass display precision. |
| CELL 57A | All 47 saved adjusted ROI and redistribution rows pass arithmetic checks (win redistribution .00016 probability, ROI .0003). Saved nonzero pushes are Rice–East Carolina -10: 4.21%, N=356; Jacksonville State -3: 6.67%, N=824. Full empirical push rates cannot be independently regenerated without the omitted history. |

The earlier notebook late-week market paste is explicitly SYNTHETIC_TEST /
FICTIONAL. The later archived sportsbook offers are supplied saved odds; their
independent real/manual/synthetic origin and capture timestamps are not
established by the saved tables. They are not authenticated historical market
validation. No expected values or missing raw records are invented.

The largest retained-line difference is approximately 0.032 points and comes
from upstream CFBD input drift, not a formula change. The original 3,730-row
calibration dataset is unavailable, so saved empirical probabilities cannot be
independently regenerated from raw historical inputs. Archived sportsbook price
provenance remains unverified.

Historical API/feature drift does not justify adjusting formulas, regression
coefficients, samples or spreads to force obsolete historical agreement. No live
CFBD or sportsbook request is necessary or performed for this extraction.

Full regression: `PYTHONPATH=src python -m unittest discover -s tests` passes
**430 tests**, including all 60 new tests. Pandas emits the same grouping-column
deprecation warning in CELL 55 and its extraction; there are no test failures.

## Promotion assessment and integration boundary

This is suitable as a **legacy-equivalent production replacement for these
calculations**, with the disclosed literal semantics. It is not a new claim of
predictive calibration quality or real-market pricing validation. Production
callers must supply provenance-qualified historical payloads and exact offered
prices; current-market readiness remains separate from movement-audit readiness.
The metadata gap, literal positive-line push orientation and preserved base
EV_Status are reviewable legacy limitations, not silently changed policies.

No prior feature/signal/routing/audit/decision logic, Covers acquisition, alias,
model formula, or frozen notebook is modified. No October 17 recovery input is
used. NumPy is added as an explicit dependency because np.polyfit/isclose are now
production requirements rather than only transitive pandas dependencies.
Bet Slip Architect can call these pure functions with externally supplied odds.
Kelly/staking, live price acquisition, Odds API, team totals and final handoff/
export remain absent from this migrated segment.
