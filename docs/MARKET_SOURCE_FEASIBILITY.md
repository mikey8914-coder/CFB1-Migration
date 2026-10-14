# Market Source Feasibility

## Verdict: Not demonstrated

**Two independently identified DraftKings and FanDuel spread observations have not been demonstrated from Action Network or Covers in this environment.** All three attempted source requests failed at the outbound proxy before origin content was received. No source page, current odds payload, sportsbook-ID mapping, opener history, or game schedule was available to inspect.

This is an **environment-access limitation**, not a finding that either website lacks the data, requires authentication, or rejects public visitors. It is also not “Partially available”: no required source field was confirmed accessible during this investigation. Site capabilities remain unverified. Do not implement a production acquisition adapter from guessed response fields or book IDs.

Reviewed local requirements in:

- `docs/DK_FD_DEPENDENCY_REVIEW.md`
- `docs/MARKET_DATA_CONTRACT.md`
- `docs/BEHAVIOR_LOCK.md`

The required football observations are specifically the legacy primary/DK-role and secondary/FD-role **point spreads**, not American prices. DK direction, conservative pair edge, and pair mean can affect convergence, Phase 1, keys, routing, retained-line fitting, and probabilities. Moving wager economics to Universal Bet Slip Architect does not erase those dependencies. The frozen notebook was not executed or changed.

## Access evidence from this investigation

Checked October 14, 2026 at approximately **10:37 AM EDT** (14:37 UTC), using standard-library HTTPS requests with normal certificate validation, no credentials, and no Odds API calls. A browser/web-search connector was not available; these were shell HTTP probes, not browser-rendered page observations.

| Candidate resource | Purpose | Observed result |
| --- | --- | --- |
| [Action Network college-football odds page](https://www.actionnetwork.com/ncaaf/odds) | Inspect publicly displayed lines, book labels, games, totals, and kickoff context | `Tunnel connection failed: 403 Forbidden`; no origin HTML received |
| [Covers college-football odds page](https://www.covers.com/sport/football/ncaaf/odds) | Inspect fallback book-specific lines, openers, totals, and schedule | Same proxy-tunnel error; no origin HTML received |
| `https://api.actionnetwork.com/web/v1/scoreboard/ncaaf?date=20261017&period=game&bookIds=15,30` | Exploratory scoreboard request for point-level market data on a candidate upcoming slate | Same proxy-tunnel error; no JSON received |
| [GitHub](https://github.com) | Control request to a domain already allowed by environment policy | HTTP 200, text/html |

The scoreboard path/query is **an exploratory candidate, not a confirmed currently supported public API contract**. In particular, `bookIds=15,30` was not verified against any sportsbook registry, and this report makes **no claim** that those IDs identify DraftKings and FanDuel. The queried date does not establish which games or odds would be returned because there was no response. A reachable path would still need content/schema/book-identity validation.

The readable configuration metadata showed restricted network access, the package-manager preset, no custom egress rules, and no Action Network/Covers destination entries in the resolved presets. The successful control request supports diagnosis of a destination-specific egress restriction rather than complete loss of Internet access.

**Important interpretation:** the 403 was a proxy CONNECT/tunnel failure, not an HTTP response from Action Network or Covers. Therefore it is not evidence of a site paywall, anti-bot rejection, regional block, or unsupported endpoint. No authentication, browser, or user-agent workaround is justified by this result. Do not bypass the environment proxy or disable TLS validation.

No environment settings were changed: the request authorized creating this document only. Necessary next access additions are `www.actionnetwork.com`, `api.actionnetwork.com`, and `www.covers.com`. Additional redirect or page-data destinations, if needed, must be identified from actual responses and added narrowly; their names are not established here. These additions permit investigation but do not prove source reliability or authorize a private API.

## Confirmed fields versus unverified source possibilities

“Unverified” below means **not inspected successfully**, not “absent.” The requirement column describes what CFB1 needs; it does not attribute those fields or JSON names to either provider.

| Required observation or context | Action Network | Covers | Evidence necessary to confirm |
| --- | --- | --- | --- |
| Current full-game DraftKings home spread | Unverified | Unverified | A current numeric point with explicit DraftKings identity, game identity, home/away side, full-game scope, and observation time |
| Current full-game FanDuel home spread | Unverified | Unverified | Same evidence with explicit FanDuel identity, not another website's unlabeled default line |
| Distinct sportsbook identity/ID mapping | Unverified; exploratory IDs are not mapped | Unverified | Actual page label or current book registry plus payload linkage; IDs alone are insufficient |
| Opening home spread | Unverified | Unverified | Actual opener value with definition, book/source, game, perspective, and historical/current distinction |
| Later audit-current home spread | Unverified | Unverified | A separately timed spread observation for the same game/perspective and the intended audit source |
| Current game total | Unverified | Unverified | Full-game combined point threshold; bookmaker/source scope clear; not a team total or first-half total |
| Opening game total | Unverified | Unverified | Opening combined point threshold and scope; not necessary for the existing final spread-movement decision |
| Home and away team names | Unverified | Unverified | Actual labels and roles, canonical mapping, stable matchup/event identity |
| Kickoff time/timezone | Unverified | Unverified | Scheduled timestamp with explicit UTC/zone/offset or a separately validated schedule join |
| Stable source event/game ID | Unverified | Unverified | Field/URL identity verified across page/payload and repeated fetches |
| Source quote update timestamp | Unverified | Unverified | Timestamp attached to the particular book/market, with meaning and timezone verified |
| Source publication/cache timestamp | Unverified | Unverified | Any feed/page timestamp plus scope; must not be mistaken for individual quote update |
| Local retrieval timestamp | Confirmed capturable for request attempts only | Confirmed capturable for request attempts only | Collector records UTC before/after retrieval; failed-request time is **not** a valid market observation timestamp |

No exact provider field names, current DK/FD quote values, game examples, accessible opener history, or book-specific coverage counts are asserted here. Local legacy notebook fixtures do not independently confirm current external-site availability.

## What qualifies as two independent sportsbook observations

CFB1 requires two **independently identified sportsbook quotes**; different numbers are not mandatory, and distinct websites are not sufficient evidence.

- A single Action Network response could satisfy both observations if it contains separately attributed, valid DraftKings and FanDuel spread points. Those may be numerically equal while remaining distinct book observations.
- Action Network and Covers each displaying an unlabelled “current spread” or a consensus line does **not** establish a DK/FD pair. Do not assign primary/secondary roles solely according to website name.
- Action Network DraftKings and Covers DraftKings are duplicate-source representations of the **same book role**, not the missing FanDuel observation, even if timestamps or numbers differ.
- A fallback FanDuel quote from Covers could complement an Action Network DraftKings quote only after confirming same event, home perspective, full-game/main-spread scope, book identity, and acceptable snapshot timing.
- Alternate lines, first-half lines, opener versus current line, or home and away outcomes of one book are not replacements for two current main-book observations. Home and away points of one handicap are usually perspective equivalents, not independent books.
- Sites may use a common underlying data vendor. Provider independence is not required to identify two books, but website count alone proves neither book identity nor feed diversity. A common vendor must not be assumed to deliver two independently attributed quotes.

The minimum successful evidence should preserve an actual payload/page snapshot with game ID, sportsbook mapping and point values. Merely observing a DraftKings/FanDuel logo somewhere on a page does not link each logo to the particular game/spread.

## Preserving identity, provenance, and timestamps

The following is a proposed observation record, not implemented production code and not a claim about provider JSON field names:

| Proposed record item | Preservation rule |
| --- | --- |
| stable game_id / source_event_id | Match canonical away/home teams and schedule; retain source ID and original team labels for traceability |
| sportsbook_id / sportsbook_name | Keep the actual source identifier and the verified normalized name DraftKings or FanDuel; preserve registry/version evidence for numeric IDs |
| role | Assign primary/DK or secondary/FD only after identity is verified; keep role separate from acquisition website |
| home_spread / game_total | Store numeric full-game points, explicit perspective, and market scope; normalize away points by negation only after side identity is clear |
| acquisition_source / source_url | Preserve whether Action Network or Covers supplied the observation and the exact request/page location, without credentials |
| retrieved_at / retrieval_completed_at | UTC collector times on successful retrieval; never substitute for kickoff or label as book update time |
| source_updated_at | Retain only if provided and its book/market meaning is established; otherwise null with explicit “not supplied” status |
| provider/feed timestamp / HTTP Date / cache metadata | Keep separately if present; these may describe page generation/cache rather than quote freshness |
| scheduled_kickoff_utc | Preserve scheduled event time and normalization evidence; not the timestamp of odds retrieval |
| snapshot_id / initial-or-audit role | Freeze initial DK/FD observations together; attach later audit-current and opening spread observations without overwriting the initial fit input |
| opener provenance/definition | Identify whether it is book-specific, source consensus, or another opening convention; do not silently compare differently defined lines |

Local retrieval times can establish when the collector saw an observation, but cannot prove when the sportsbook last changed it. Do not fabricate source_updated_at. Without source update times, freshness confidence and acceptable retrieval-time skew must be explicitly assessed rather than declared reliable. No freshness threshold, retry policy, or acceptable time-skew value has been validated by this task.

Kickoff and team mapping may be enriched from the existing CFBD schedule if provider data is incomplete, but matching must be demonstrated using canonical identities and schedule constraints. Matching raw names alone risks wrong games, reversed sides, or repeated matchups. Normalization must preserve the frozen notebook's home/away and display-key semantics.

## Restrictions and reliability risks

### Observed blocker

Environment egress policy prevented all source requests. No source-specific access behavior or rate-limit response was observed. The usable next step is narrow network access followed by new content checks, not repeated unchanged requests or broader scraping.

### Unverified concerns that must be checked, not assumed

- Public HTML may omit full odds data and require browser rendering or a page-data request. Whether either source does this on the selected pages is unknown.
- Book selectors may depend on region, jurisdiction, user preference, or session state. Whether DraftKings and FanDuel are both exposed to an unauthenticated visitor from this environment is unknown.
- A public display does not establish a supported/stable machine interface. Any endpoint, book-ID mapping, schema, main/alternate-market selection, or update cadence may change; none was validated here.
- Login/paywall, geographic restrictions, bot mitigation, terms of access, and rate limits are unknown. Inspect actual responses and site guidance before choosing a supported collection method; do not presume bypass is needed or permitted.
- Availability may vary by game, time of week, and sportsbook. Some games may have only one identified quote, no total, or no opener. No slate-level coverage sample was collected.
- Cached lines, mismatched snapshots, suspended markets, moved kickoff times, and inconsistent opener definitions can produce mathematically valid but behaviorally wrong inputs.
- Reading bookmaker prices incidentally in a public payload does not transfer their evaluation into CFB1. Routine acquisition should retain only football point/context/provenance needs; Architect owns juice economics.

The verdict “Two sportsbook spreads reliably available” would require successful book-attributed observations and repeated freshness/coverage evidence. One successful game/response would establish an accessible example, not routine reliability. No such example was obtained in this investigation.

## Smallest practical no-Odds-API strategy — conditional recommendation

1. **Try Action Network as the primary collector.** After access is enabled, first inspect the public odds page and its supported/public data route. If one slate response contains both verified DK and FD main spreads, use that response plus totals/schedule; no second website is needed merely to obtain a second book observation.
2. **Use Covers only for missing identified book/game observations or required audit context.** Confirm the actual sportsbook label rather than substituting a Covers consensus/default spread into the missing DK/FD role. Match event, main-market scope, perspective and snapshot timing before combining sources. Do not force coverage through aggressive retries/searches.
3. **Keep opener/audit collection distinct from the frozen initial model pair.** Collect the actual opening spread and later current spread for OLD CELL 43/OLD CELL 44 behavior. Initial pairs and later audit values may come from the same website but represent different snapshot roles.
4. **Join validated schedule identity where needed.** Reuse CFBD only for independently verified schedule/team association; do not require another odds vendor for identity enrichment.
5. **Reject or explicitly exclude games missing a verified pair**, subject to the approved limited-coverage policy, and record exclusions. Do not clone one quote into two roles. Reduced-slate effects on fit/percentiles and audit-review completeness still need validation. A one-spread fallback remains a separate unresolved modeling change, not an acquisition shortcut.
6. **No routine Odds API dependency.** Neither initial probes nor this plan consume credits. If neither public source can provide the required named pair, retain manual book-attributed snapshot fixtures for testing or stop the affected acquisition stage; do not silently reintroduce Odds API or redefine the model.

This recommendation is a collection sequence to verify, not an endorsement of a working API. Until actual source payloads establish the named books and fields, the practical automated strategy remains unproven.

## Required evidence before implementing acquisition

- Add narrowly scoped egress access for the tested hosts and retry after that meaningful configuration change. Follow actual redirect/data destinations only as discovered. Saving access settings does not itself validate a request.
- Obtain successful public page/payload samples and resolve the current sportsbook identity mapping from evidence. Verify **both DraftKings and FanDuel**, not two unlabeled website quotes or arbitrary numeric IDs.
- Demonstrate several current/upcoming college-football games with correctly attributed home spreads, totals, team roles, game identity, and kickoff. Record missing fields/coverage explicitly. Test whether opener/history data is accessible and what its definition is.
- Preserve source snapshots and retrieval times; compare repeated observations over meaningful intervals to assess update behavior, staleness, source timestamp meaning, and cross-source timing. Define supported access and bounded refresh behavior from observed evidence.
- Demonstrate Covers fallback for an actual missing Action Network book/game observation, including identity and timing consistency. If Covers only supplies consensus/default lines, classify that as insufficient for the named-pair fallback.
- Replay verified input fixtures through the preserved football contracts, checking DK-role FEI direction, FD minimum-edge contribution, consensus keys/large spread thresholds, full-slate fit/retention, line-conditional probabilities and push behavior. No production module or notebook execution is part of this document task.
- Resolve incomplete-pair exclusion and snapshot/opener policy. Specify the price-free probability handoff at actual Architect point thresholds; no break-even or ROI requirement should return to CFB1.

**Implementation gate:** publicly accessible fields, book identity, observation semantics, acceptable coverage/freshness, and supported access method must be demonstrated before writing a production collector. This investigation exhausted available source checks under the current network policy; further source verification requires that access change.
