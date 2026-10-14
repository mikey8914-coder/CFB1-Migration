# Team Identity Foundation

## Reference behavior and merge findings

The frozen notebook uses **CFBD team-name strings** as its canonical identity
namespace. It does not establish a numeric CFBD team-ID registry. Alias targets
are not a complete list of valid or currently covered teams: the actual identity
universe comes from `df_cfbd.team` for the selected data snapshot.

- **CELL 10:** `TEAM_ALIASES` has 138 market-name aliases. The original
  `normalize_team_name` stringifies input, collapses Unicode whitespace, strips
  surrounding whitespace, and performs exact lookup. An unknown name returns
  the cleaned string. Case, accents, punctuation, and mascots are not changed
  heuristically. `Home_CFBD_Name` and `Away_CFBD_Name` are separate from the raw
  `Home_Team` and `Away_Team` fields. Membership uses stripped, nonnull
  `df_cfbd.team` values. Unmatched names produce a printed STOP, not an exception
  inside the normalization function.
- **CELL 11:** canonical home and away names join CFBD data independently using
  left `many_to_one` merges. Row count must match the market slate, home/away net
  EPA must be present, and raw home/away pairs must not duplicate. Failure raises.
  Normalizing a name alone does not demonstrate statistical coverage or merge
  cardinality.
- **CELL 13 / CELL 14:** CELL 13 prepares BCF Team strings by string conversion
  and surrounding-whitespace stripping. CELL 14 then applies its separate
  `BCF_TO_CFBD` mapping, with unmapped strings unchanged. It checks CFBD
  membership, duplicate normalized names, and target-slate BCF coverage before
  permitting the merge. The five exact aliases are Appalachian State → App
  State, Connecticut → UConn, Hawaii → Hawai'i, San Jose State → San José State,
  and Southern Mississippi → Southern Miss.
- **OLD CELL 19 / OLD CELL 26:** BCF features and defensive line yards join using
  the same canonical home/away name keys with `many_to_one` cardinality. Their
  required feature and slate validations remain the responsibility of future
  ingestion/merge components.
- **CELL 53:** event matching uses raw `Away_Team + ' at ' + Home_Team` strings,
  not a new canonical game identifier. Preserve raw labels separately; this
  component does not introduce event IDs or change matchup keys.

## Component and version-controlled mappings

`src/cfb1/team_identity.py` uses only the Python standard library.
`src/cfb1/team_aliases.json` contains the exact dictionary literals extracted
from CELL 10 and CELL 14, mapping version 1, embedded-cell provenance, and the
frozen notebook SHA-256. No aliases were added, merged across sources, or
corrected. Future source-specific aliases require evidence and review rather
than a fuzzy matching fallback.

The public functions are:

- `normalize_team_name(value)`: exact CELL 10 market normalization. This retains
  even the legacy stringification of values such as None or NaN; the returned
  string is not proof of a valid team.
- `normalize_bcf_team_name(prepared_name)`: exact CELL 14 mapping, accepting the
  already-prepared CELL 13 string. It deliberately does not strip again or
  collapse internal whitespace. BCF input preparation is not implemented here.
- `TeamIdentityResolver(nonnull_cfbd_names)`: snapshots caller-supplied CFBD
  names into a stripped immutable set, without market/BCF alias conversion of
  the canonical registry. Pass nonnull strings after removing missing values,
  as the notebook does with `dropna()`.
- `resolve_market_name(value)` / `resolve_bcf_name(prepared_name)`: return a
  `TeamIdentity` with the original `raw_name`, `normalized_name`, and exact
  `matched` membership status. Unknown names are reported as unmatched, never
  guessed, automatically dropped, or converted to a different team.

Runtime alias views are read-only. An unmatched normalization result is the
legacy fallback, not a verified canonical identifier. In particular, a known
alias can remain unmatched when its canonical target is absent from the
provided CFBD snapshot.

## Example

Run from the checkout with `src` on the Python path:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

```python
from cfb1.team_identity import TeamIdentityResolver

resolver = TeamIdentityResolver(["Miami", "Miami (OH)", "UConn"])
identity = resolver.resolve_market_name(" Miami  Hurricanes ")
# raw_name == " Miami  Hurricanes "
# normalized_name == "Miami"
# matched is True

bcf_identity = resolver.resolve_bcf_name("Connecticut")
# normalized_name == "UConn"; matched is True
```

The project currently uses its existing source-layout checkout configuration;
no package installation, build dependency, or third-party runtime dependency is
required for these checks. An installed distribution/build configuration is not
introduced by this identity-only task.

## Validation and limits

The unittest suite checks every alias against the notebook's literal maps using
JSON/AST inspection without executing notebook code. It also covers whitespace,
stringification, unchanged unknown/canonical names, accents, the distinct Miami
identities, source separation, CFBD membership, raw-label preservation, and
read-only mappings. This validates extraction of the existing identity rules;
it does not establish live CFBD, Action Network, or Covers name coverage.

No scraper, schedule fetcher, master merge, event-ID scheme, odds adapter,
probability logic, or wager evaluation is implemented. Existing unmatched,
duplicate, coverage, and merge-cardinality safeguards must be retained when
those later boundaries are developed.
