# CFBD feature acquisition and master-table contract

## Authority and scope

Authority: `legacy/CFB1_Colab_Reference.ipynb` (SHA-256
`94d8eca356392e9872974c2579a6fb45c3a989dbe0a5026d21f7ba70dff33431`),
`docs/NOTEBOOK_MAP.md`, and `docs/BEHAVIOR_LOCK.md`. Original embedded labels
are used below; notebook array positions are not cell labels.

This extraction covers CELL 2, CELL 3, the data-only defensive-line-yards
extraction in OLD CELL 25, and CELL 11's master associations. It does not
implement CELL 12's EPA trigger, FEI, Module 3 signals, routing, market
acquisition, or any calibration/model changes. OLD CELL 25's defensive feature
is extracted from the same frozen advanced payload, without executing Module 3.
No October 17 recovery artifacts or recovery aliases are inputs or authorities.

## Configuration and HTTP requests

The saved weekly configuration is YEAR=2026, DATA_THROUGH_WEEK=5,
TARGET_WEEK=6, TARGET_START_DATE=2026-10-06, TARGET_END_DATE=2026-10-10.
The notebook startup print gate also requires both API keys, ordered target
dates, and DATA_THROUGH_WEEK < TARGET_WEEK. The CFBD-only replacement needs
CFBD_API_KEY, not the unrelated Odds API key or target-date window.

| Endpoint | Exact parameters | Frequency |
| --- | --- | --- |
| GET /plays | year=YEAR, week=wk, seasonType=regular | One call for each integer wk in range(1, DATA_THROUGH_WEEK + 1) |
| GET /stats/season/advanced | year=YEAR, seasonType=regular, startWeek=1, endWeek=DATA_THROUGH_WEEK | One call after all plays |

Both use https://api.collegefootballdata.com with Authorization: Bearer
CFBD_API_KEY and Accept: application/json. The existing shared transport handles
key whitespace, safe errors, TLS/proxy settings, and redirect refusal. No key
values, response error bodies, or environment dumps are printed. The new module
uses this transport without changing the schedule or Covers implementations.

The boundary requires integer positive season and
1 <= DATA_THROUGH_WEEK < TARGET_WEEK, validated before network access. It neither
requests Week 0 nor TARGET_WEEK, postseason, /ppa/teams, a team-filtered subset,
or full-season advanced statistics. TARGET_WEEK is a leakage guard, not an
acquisition query parameter. A caller must select a genuinely completed boundary;
the notebook does not check wall-clock completion. Response rows do not always
contain season/week, so request scope is the provenance, not an invented row-level
week inference. The legacy endpoint use has no pagination or retry loop; the
extraction preserves that request pattern. Missing/truncated provider responses
cannot be detected from HTTP 200 alone; saved checkpoint counts help detect drift.

## CELL 2: raw plays and PPA

`ppa_play_rows` concatenates successful weekly JSON arrays in ascending week
order. `ppa_week_status[wk]` records HTTP status. `df_ppa_plays` contains all
source columns without renaming; required columns are exactly `offense`,
`defense`, `ppa`. Additional play columns are retained.

`df_ppa_valid = df_ppa_plays.dropna(subset=['offense','defense','ppa']).copy()`.
A null in any member removes the row from BOTH offense and defense aggregation.
There is no coercion of strings to numbers, null filling, deduplication by play ID,
week/game weighting, garbage-time filtering, play-type filtering, FBS/opponent
classification filtering, alias lookup, or name trimming.

| Object | Exact columns and rule |
| --- | --- |
| df_off_ppa | team, Off_EPA: group valid rows by offense, as_index=False; arithmetic mean of ppa; rename offense→team, ppa→Off_EPA |
| df_def_ppa | team, Def_EPA: group the SAME valid rows by defense; arithmetic mean of ppa; rename defense→team, ppa→Def_EPA |
| df_ppa | Outer merge df_off_ppa and df_def_ppa on exact team key |

Each play contributes equally, including duplicate input rows. Defensive EPA is
opponent PPA allowed, not its negative. Pandas groupby defaults are preserved.
One-sided teams remain in the outer PPA table with the absent EPA side null.

CELL 2 printed PASS requires every recorded weekly status==200, all required
play columns present, len(df_ppa)>0, advanced HTTP==200, and len(adv_json)>0.
It prints STOP without raising on failure. Missing play schema produces empty
valid/PPA objects in the notebook, which may then fail in CELL 3. The replacement
raises on missing schema or failed HTTP instead of returning a partial live set.
A successful HTTP request for one empty week is not independently rejected by the
notebook if other weeks still produce a nonempty PPA table; no new completeness
claim is made for such a case.

## CELL 3: normalized team feature table

`adv_json` is the unchanged bounded advanced payload. `df_adv =
pd.json_normalize(adv_json)`. `df_adv_clean` selects and renames these exact paths:

| Output | Source |
| --- | --- |
| team | team |
| Off_SuccessRate | offense.successRate |
| Off_PassingDown_SR | offense.passingDowns.successRate |
| Off_Explosiveness | offense.explosiveness |
| Def_SuccessRate | defense.successRate |
| Def_PassingDown_SR | defense.passingDowns.successRate |
| Def_Havoc_Rate | defense.havoc.total |
| Off_LineYards | offense.lineYards |

A globally absent required path raises in the notebook; a path missing only on
some rows becomes null through json_normalize. There are no alternate field-name
fallbacks, numeric coercions, transformations, scaling, or fills.

`df_cfbd = pd.merge(df_ppa, df_adv_clean, on='team', how='inner')`.
`Net_EPA_Margin = Off_EPA - Def_EPA`, without rounding or sign changes.

CELL 3 required columns, in validation order:

```text
team, Off_EPA, Def_EPA, Net_EPA_Margin,
Off_SuccessRate, Off_PassingDown_SR, Off_Explosiveness,
Def_SuccessRate, Def_PassingDown_SR, Def_Havoc_Rate, Off_LineYards
```

The actual base table order is team, Off_EPA, Def_EPA, the seven advanced output
columns above, then Net_EPA_Margin. Printed PASS requires all required columns,
zero duplicated team rows (`duplicated(subset=['team'], keep=False)`), zero total
critical null cells, and a nonempty matrix. This is a print gate, not a raise.
Duplicates are not averaged or dropped. Inner merging intentionally omits
PPA-only and advanced-only teams; equal source universes/full FBS coverage are
NOT legacy PASS requirements. The report exposes both omitted sets. Missing
required slate teams are rejected at the master join, not invented here.
The notebook tests nullness, not numeric finiteness or statistical plausibility;
the extraction does not claim those additional validations.

## OLD CELL 25: defensive line yards from the same payload

For each adv_json row, read team_row.get('team') and
(team_row.get('defense') or {}).get('lineYards'). Build `df_def_lineyards` with
exact columns team, Def_LineYards. Drop any prior Def_LineYards from df_cfbd,
then left merge on team with validate='one_to_one'. Do not refetch advanced data.
The source and merge must have zero duplicated source team rows, zero null
source Def_LineYards, and zero null merged Def_LineYards. Failure raises;
cardinality errors may raise during the merge before the printed gate.

The extracted df_cfbd includes Def_LineYards as its last column: 13 total
columns. The replacement reports invalid duplicate-source tables without
performing a Cartesian defensive merge, and blocks master association/export.
This diagnostic behavior differs from the notebook's immediate MergeError but
never changes a passing result. Both CELL 3 and defensive-source conditions
must pass for the feature result's valid flag.

## CELL 10/11: normalization and game master

CFBD feature team names are exact source join keys; they are not normalized by
market aliases. CELL 10's shared canonical resolver cleans raw market names by
whitespace collapse and explicit alias lookup. Its canonical membership universe
is stripped, nonnull names from df_cfbd; registry/schedule membership alone is
not evidence of feature availability. Preserve raw Home_Team and Away_Team.
The input to master association already carries Home_CFBD_Name and
Away_CFBD_Name; there is no implicit alias inference inside the feature module.

`home_cfbd` renames team→Home_CFBD_Name and every base metric→Home_<metric>.
`away_cfbd` does the corresponding Away_ rename. `df_master` left-merges both,
Home first, on their canonical names, each with validate='many_to_one'. Every
input game and unrelated context column survives. Distinct games may reuse a
team. `Net_EPA_Edge_Home = Home_Net_EPA_Margin - Away_Net_EPA_Margin` is the
unchanged CELL 11 association-stage formula. Positive favors the home efficiency
margin; no trigger/classification is implemented.

PASS requires row count unchanged, zero null Home_Net_EPA_Margin, zero null
Away_Net_EPA_Margin, and zero duplicate (Home_Team,Away_Team) rows, keeping all
members of duplicates. Failure raises. No missing team is silently discarded.
The extracted helper also prefixes Def_LineYards because it receives the final
team feature table. This combines feature association previously refreshed in
OLD CELL 26, without implementing that cell's later model context or signals.

## Production interface and explicit failure behavior

- `FeatureBoundary(season, data_through_week, target_week)` builds bounded queries.
- `aggregate_play_ppa`, `normalize_advanced_stats`, `build_feature_tables` are pure
  offline transformations. FeatureTables exposes the legacy-named DataFrames and
  a validation report. Structural/schema errors raise; diagnostic tables with
  duplicate/null failures return valid=false.
- `acquire_cfbd_features` returns only after every required HTTP call succeeds.
  It exposes per-request row counts, parameters, UTC start/completion times and
  duration. It has no retry or partial-result fallback.
- `merge_master_features` refuses an invalid feature result and enforces CELL 11.
- `python -m cfb1.features_live --season 2026 --data-through-week 5 --target-week 6`
  prints a report. Optional --output-dir creates exclusive validation.json and,
  only for valid results, df_cfbd.csv. Exit 0=valid, 1=validation failure,
  2=acquisition/schema/configuration failure. No downstream model is run.
- Pandas >=2.2,<3 is declared as the dependency used by the legacy DataFrame
  operations; this extraction does not replace pandas merge/groupby semantics.

## Saved historical expectations and comparison limits

CELL 2 saved counts, YEAR=2026 through Week 5:

| Measure | Saved value |
| --- | ---: |
| Week 1 plays | 35,773 |
| Week 2 plays | 23,131 |
| Week 3 plays | 22,765 |
| Week 4 plays | 21,833 |
| Week 5 plays | 20,368 |
| Total plays | 123,870 |
| Valid PPA rows | 93,364 |
| PPA teams | 313 |
| Advanced teams | 138 |
| Inner-merged teams | 138 |
| Duplicate feature rows / critical null cells | 0 / 0 |
| CELL 11 market/master games | 57 / 57 |

`tests/fixtures/cfbd_feature_notebook_checkpoint.json` transcribes the saved
CELL 3 first 10 rows, OLD CELL 25 first 15 rows, and CELL 11 first 10 rows from
the notebook's embedded HTML displays. Values are displayed to six decimals;
comparison uses absolute tolerance 0.0000005 plus 1e-12 for binary-float
representation at the rounding boundary, not an invented full-precision
baseline. The fixture also records the notebook hash, boundary and saved counts.
The fixture also includes all 57 target-market rows displayed in CELL 6,
allowing full historical slate association without fetching any market data.
The full historical raw payloads and all 138 full-precision rows are not saved,
so full-table historical numeric equality cannot be claimed. A current historical
API query may reflect provider corrections after the notebook capture.

Offline tests execute only the named frozen cells with fixture-backed HTTP
stubs (the requests import is removed), no Colab startup or real network. They
compare all relevant DataFrames to the extraction. They also test hand-calculated
means, null/duplicate behavior, source omissions, master cardinality, and the
request plan's exclusion of TARGET_WEEK. The notebook remains unmodified.

## Live historical validation (October 19, 2026)

The new authenticated normal CLI ran YEAR=2026, DATA_THROUGH_WEEK=5,
TARGET_WEEK=6. Six requests (five /plays, one bounded advanced query) returned
HTTP 200, without retries, in 18.802 seconds. UTC acquisition interval:
2026-10-19T18:49:34.315241+00:00 to 2026-10-19T18:49:53.117648+00:00.
The CLI exited 0. It used no Covers or recovery input.

| Measure | Saved notebook | Live result | Difference |
| --- | ---: | ---: | ---: |
| Week 1 plays | 35,773 | 35,754 | -19 |
| Week 2 plays | 23,131 | 23,119 | -12 |
| Week 3 plays | 22,765 | 22,757 | -8 |
| Week 4 plays | 21,833 | 21,826 | -7 |
| Week 5 plays | 20,368 | 20,361 | -7 |
| Total plays | 123,870 | 123,817 | -53 |
| Valid PPA rows | 93,364 | 93,353 | -11 |
| Null-triple rows excluded | 30,506 | 30,464 | -42 |
| Offense / defense / PPA teams | PPA=313 | 313 / 313 / 313 | PPA unchanged |
| Advanced / merged unique teams | 138 / 138 | 138 / 138 | 0 / 0 |
| Duplicate merged teams / critical nulls | 0 / 0 | 0 / 0 | 0 / 0 |
| Defensive-line-yards source duplicates / source nulls / merged nulls | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| Master games | 57 | 57 | 0 |
| Master duplicate pairs / missing home / missing away | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

There are 175 PPA-only teams omitted by the legacy inner join, and zero
advanced-only teams. This is the source-universe distinction reflected by the
313-to-138 merge, not 175 missing FBS model rows.

All **160 explicitly displayed numeric comparisons** pass within display
precision: CELL 3's 10 teams × 10 numeric metrics = 100; OLD CELL 25's 15 teams
× 2 line-yards metrics = 30; CELL 11's first 10 games × 3 net-EPA metrics = 30.
Arizona State defensive line yards is exactly a displayed rounding boundary:
live 2.9359375 vs displayed 2.935938. It passes with the stated binary-float
epsilon; the comparison does not demand nonexistent saved precision.

All 57 CELL 6 game rows were joined to the live feature table through the existing
shared canonical resolver, with no market acquisition or model execution. The
full game count and zero missing/duplicate master conditions match CELL 11.
Only the 10 saved CELL 11 game values, not all 57 historical numerical game
outputs, have a displayed baseline.

The 53-play and 11-valid-PPA count differences are genuine discrepancies with
the saved output, not silently redefined expectations. The original raw payloads
are unavailable, so the cause cannot be established as provider correction,
missing responses, or historical execution provenance from this evidence alone.
Identical notebook formulas pass offline literal-cell parity, all requests are
bounded as specified, and displayed live numeric samples match; none of those
facts proves equality for unshown historical feature values.

Historical live API validation establishes formula, schema, structural, boundary,
and saved-output parity where comparison values exist. It does not guarantee
exact historical raw-record counts because upstream CFBD responses may change
after the original notebook run. Do not alter production calculations to force
obsolete raw counts.

**Promotion assessment:** the extracted acquisition/transformation contract is
validated for the tested inputs, and the historical live matrix/master pass the
legacy structural gates. It is ready for code review as a production replacement
candidate. Exact historical snapshot parity is not certified: review and accept
or resolve the documented count discrepancy before claiming full historical
reproduction. No alternate definitions were introduced to force agreement.

Verification command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest
discover -s tests`. All 135 tests pass (107 existing + 28 feature tests).

