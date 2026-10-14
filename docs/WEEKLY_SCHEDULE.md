# Weekly Schedule Boundary

## Legacy inspection and source choice

The frozen notebook does **not** contain a standalone weekly CFBD `/games`
schedule acquisition cell:

- **CELL 2** establishes the CFBD base host and Bearer authentication pattern
  for regular-season `/plays` and frozen advanced statistics. It is not a
  schedule fetch.
- **CELL 5** obtains kickoff from Odds API `commence_time`, converts it to UTC
  and Eastern time, and keeps raw home/away names. **CELL 6** filters that
  market-defined slate by inclusive Eastern dates, not a CFBD schedule week.
- **CELL 51** and **CELL 58** preserve CFBD `id`, `week`, `homeTeam`, and
  `awayTeam` from historical `/lines` game objects. These establish a source-ID
  precedent, not a reusable weekly schedule collector.
- **CELL 10**, **CELL 11**, and **OLD CELL 19** establish canonical CFBD name
  membership and independent home/away statistical joins. The new schedule
  boundary reuses that identity foundation without changing its mappings.

CFBD's public Python-client documentation identifies **GET `/games`** as its
games/results interface, with `year`, optional `week`, and regular/postseason
selection. Its Game model documents `id`, `season`, `week`, `home_team`,
`away_team`, `start_date`, and `start_time_tbd`.

References inspected successfully during development:

- [CFBD GamesApi documentation](https://github.com/CFBD/cfbd-python/blob/master/docs/GamesApi.md#get_games)
- [CFBD Game model documentation](https://github.com/CFBD/cfbd-python/blob/master/docs/Game.md)

The deterministic validation component consumes a **saved CFBD response** and
remains network-free. A separate live acquisition adapter now fetches CFBD
`/games` and delegates the raw response to that same boundary (see below).
No CFBD SDK or Odds API is used. Live CFBD response validation remains blocked
by missing credentials and outbound access. The fixture is synthetic, not a
captured official weekly slate.

## Interface

`src/cfb1/schedule.py` provides `normalize_cfbd_schedule(games, season=...,
week=..., resolver=..., previous_records=...)`. It returns `ScheduleValidation`
with immutable normalized records, structured issues, and a `valid` flag.
The caller supplies a `TeamIdentityResolver` built from the relevant nonnull
CFBD team-name strings. Alias targets are not used as a complete team registry.

The boundary expects CFBD game dictionaries with these fields:

| Source field | Accepted alternate serialized name | Requirement |
| --- | --- | --- |
| id | None | Positive integer or nonempty, unpadded source string; no invented fallback |
| season | None | Positive integer, exactly the requested season |
| week | None | Integer ≥0, exactly the requested week |
| awayTeam | away_team | Nonblank string, resolved using existing identity rules |
| homeTeam | home_team | Nonblank string, resolved using existing identity rules |
| startDate | start_date | ISO datetime with explicit offset or Z; converted to UTC |
| seasonType | season_type | If supplied, must be regular; missing means caller has already scoped its regular-season response |
| startTimeTBD | start_time_tbd | If supplied, must be boolean; true is flagged and excluded from verified records |

Camel-case names follow the notebook's CFBD raw-field convention; snake-case
names support serialized public-client model data. If both forms are present
with unequal values, the record is rejected rather than choosing one. Other
fields, including scores, prices, team IDs, and neutral-site metadata, do not
alter normalized home/away assignments. No FBS/FCS classification filter or
legacy Eastern date-window filter is silently introduced. Those eligibility
decisions belong to a later explicit slate policy.

## Normalized record

| Field | Type / meaning |
| --- | --- |
| game_id | Source int/string preserved; identity is scoped by source, not guessed from teams or kickoff |
| season | Requested and source-verified season integer |
| week | Requested and source-verified week integer |
| away_team | Verified canonical CFBD team-name string |
| home_team | Verified canonical CFBD team-name string |
| kickoff_utc | Aware UTC datetime; serialized as ISO with Z |
| source | cfbd |

Valid records sort by UTC kickoff, away name, home name, then source ID text.
Repeated runs and reordered valid input produce the same serialized output.
Records preserve original ID representation; comparisons treat numeric and
string spellings of the same ID as the same identity. A rescheduled kickoff
does not synthesize a different ID. Missing official IDs are flagged, not
replaced with date/name hashes or unstable row numbers.

## Identity and validation policy

The team-identity implementation and alias file remain unchanged. The schedule
wrapper rejects nonstring/blank team fields, then uses the existing market
normalizer and supplied CFBD membership. This stricter schedule-input validation
does not change CELL 10's standalone stringification behavior.

An **ambiguous alias** is reported when the stripped input is itself a supplied
canonical name and its different alias result is also a supplied canonical
name. The wrapper does not decide which identity to prefer. This is an explicit
new boundary safeguard, not fuzzy matching or a new alias mapping.

Issues include:

- `unresolved_team`: the normalized result is not verified in the CFBD universe.
- `ambiguous_alias`: both direct canonical and alias identities are plausible.
- `duplicate_game_id`: every occurrence of a repeated source ID is flagged,
  including equivalent integer/string IDs.
- `duplicate_matchup`: the same unordered teams and exact UTC kickoff occur
  more than once, even with different IDs.
- `inconsistent_home_away`: the same team occupies both sides, duplicate
  identities disagree about teams/orientation, the same simultaneous matchup
  has reversed assignments, or supplied previous snapshots conflict.
- `outside_week` / `outside_season_type`: source scope conflicts with the request.
- `kickoff_tbd`: a source-declared unknown kickoff is not treated as verified.
- `invalid_record`: missing/invalid ID, fields, types, timestamps, or conflicting
  field spellings. Naive dates are not guessed to be UTC.
- `empty_schedule`: an empty response is not evidence of a verified weekly slate.

Every affected row is excluded from `records`; all sides of a duplicate are
excluded, with no arbitrary winner. **Any issue makes the entire batch invalid.**
The surviving rows are available for diagnosis, not a silently approved partial
slate. Issue row numbers are one-based positions in the input response.

`previous_records` can supply prior validated `ScheduleRecord` snapshots to
detect changed teams/home-away roles for the same source ID. Kickoff or week
changes alone do not alter ID identity. Without prior or contradictory source
evidence, a single well-formed reversed assignment cannot be diagnosed as wrong;
the source's home/away designation remains authoritative. Neutral-site games
keep that designation rather than swapping based on venue or perceived favorite.

This does not implement master joins, statistical-feature coverage, multiple
games per team's schedule checks beyond identical matchup/time conflicts,
calendar completeness checks, or postseason support.

## Independently runnable validation

From the repository root:

```sh
PYTHONPATH=src python -m cfb1.schedule_validate \
  --games tests/fixtures/cfbd_schedule.json \
  --teams tests/fixtures/cfbd_teams.json \
  --season 2026 --week 6
```

The CLI reads a CFBD game JSON array and a nonempty canonical-name JSON array.
It prints normalized records/issues as JSON. Exit **0** means the supplied batch
passed; **1** means schedule validation issues; **2** means input/configuration
failure (reported as JSON on stderr). It performs no HTTP calls and requires no
credentials. The API supports previous snapshots; this small CLI currently
validates only its supplied batch.

All fixture IDs, matchups, and dates are synthetic test inputs; they do not
assert real 2026 games or CFBD ID allocation.

## CFBD credentials and live acquisition

`src/cfb1/cfbd_schedule.py` implements the separate standard-library HTTP layer.
It uses the existing **CFBD_API_KEY** environment binding and
`Authorization: Bearer <key>`, following CELL 2. Whitespace is stripped; invalid
header characters fail before fetching. Credentials never enter URL parameters,
fixture files, reports, or CLI arguments.

`fetch_cfbd_games(season, week)` requests:

`GET https://api.collegefootballdata.com/games?year=<season>&week=<week>&seasonType=regular`

The HTTP `seasonType` spelling was confirmed in CFBD's public
[GamesApi client source](https://github.com/CFBD/cfbd-python/blob/master/cfbd/api/games_api.py),
whose SDK argument is `season_type`. This confirms the published interface, not
successful live credentials, current service payloads, or slate coverage.

`fetch_cfbd_team_names()` requests independent CFBD `/teams` school names.
CFBD's [TeamsApi](https://github.com/CFBD/cfbd-python/blob/master/docs/TeamsApi.md)
and [Team model](https://github.com/CFBD/cfbd-python/blob/master/docs/Team.md)
document `/teams` and `school`. A malformed/empty registry fails explicitly,
without filtering rows. General registry membership does **not** establish
seasonal efficiency-matrix feature coverage; that remains a later merge check.
It is not constructed from the names in the games response or alias targets.

`acquire_cfbd_schedule` accepts an existing resolver or fetches that registry,
then fetches the games and passes **every raw row, unchanged**, into
`normalize_cfbd_schedule`. It returns the raw response rows in
`LiveScheduleResult.raw_games` as well as validation records/issues. No source
ID, side, time, or alias is rewritten by fetching, and malformed/unresolved rows
are not silently removed before validation. An issue still makes the batch
invalid; successful HTTP acquisition does not imply a valid schedule.

TLS verification and the environment proxy remain enabled. Requests have a
finite configurable timeout (default 30 seconds); no automatic retries or
redirects are followed. Redirects are blocked to avoid forwarding Authorization
to another destination. HTTP failures, connection/timeouts, invalid JSON, and
nonarray payloads raise safe acquisition errors. Error bodies/reasons and
headers are not printed because they can contain sensitive information.

## Live command and report

From the repository root:

```sh
PYTHONPATH=src python -m cfb1.schedule_live --season 2026 --week 6
```

By default it makes one `/teams` request and one `/games` request. To use a
canonical team-name snapshot from the existing CFBD feature data instead:

```sh
PYTHONPATH=src python -m cfb1.schedule_live --season 2026 --week 6 \
  --teams /path/to/canonical_cfbd_names.json --timeout 30
```

The supplied file must be a nonempty JSON array of nonblank canonical strings;
do not use the small synthetic test registry to validate a real full slate.
The key is read from the environment, never passed on the command line. Enter
its value securely in environment settings, not in chat or committed files.

The JSON report includes normalized records, all validation issues, and:

- `games_retrieved` and `games_successfully_normalized`;
- `games_rejected` (unique affected rows, not total issue count);
- `unresolved_team_identities` (team appearances) and `games_with_unresolved_teams`;
- `ambiguous_aliases`, `duplicate_or_conflicting_records`, and `malformed_records`;
- `games_missing_confirmed_kickoff` (unique raw rows with missing, naive,
  malformed, conflicting, or explicitly TBD kickoff information).

Kickoff failures are counted independently of validation's first malformed
field so a row with both a missing ID and missing time is not undercounted.
Categories can overlap; do not sum them to infer total rejected games.

Exit **0** is completed acquisition with valid schedule, **1** is completed
acquisition with schedule issues, and **2** is acquisition/input failure.
`live_acquisition_succeeded` distinguishes HTTP/input acquisition from schedule
`valid`. Counts are not reported as zero when acquisition never completed; no
verified weekly schedule exists in that case. Default output is stdout/stderr
only; no response files or secrets are automatically written.

## Actual live-verification status

A real command invocation for **2026 regular-season Week 6** returned exit 2:
`CFBD_API_KEY is missing; configure it securely in the environment`.
No authenticated game response was obtained and no actual game counts can be
reported. Process-variable presence and saved binding names were inspected
without displaying values; CFBD_API_KEY was absent and no corresponding binding
was declared.

A separate credential-free `/games` probe failed at the environment proxy with
`Tunnel connection failed: 403 Forbidden`, before reaching CFBD. The restricted
network policy had no `api.collegefootballdata.com` allowance. This is not a
CFBD authentication rejection or proof that the service is unavailable.

Before live verification, supply the CFBD_API_KEY binding securely for
`api.collegefootballdata.com` and allow that destination in outbound settings,
then rerun the command. Neither configuration nor credentials were changed in
this coding task. No Odds API calls, Action Network/Covers requests, or notebook
execution occurred.

## Validation performed

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

The original offline foundation passed **40 tests**: 17 identity tests and 23
schedule tests. With live acquisition added, the full suite passes **59 tests**
(including 19 mocked acquisition/CLI tests).
The standalone CLI also passed on the three-record synthetic fixture. Tests
cover exact output fields, UTC conversion, stable IDs/rescheduling, aliases,
unresolved and ambiguous names, duplicate IDs/matchups, current/prior orientation
conflicts, source scope, schema conflicts, TBD/naive/malformed timestamps,
neutral-site labels, and CLI exit behavior. No legacy notebook cells or model
calculations were executed or modified.

## Remaining market-attachment dependencies

Live schedule access/coverage must first be verified. Sportsbook observations
still need a validated matchup/schedule join, independent DK/FD point identities
(or a separately approved modeling change), frozen-versus-audit timestamp
semantics, and real opener coverage where the audit requires it. Action Network
and Covers field access remains unverified; no acquisition adapter or new alias
for either source is implemented here. Keep actual juice/EV evaluation in
Universal Bet Slip Architect, and retain existing football/probability behavior.
