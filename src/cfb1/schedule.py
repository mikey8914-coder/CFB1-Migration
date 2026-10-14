"""Deterministic weekly schedule boundary for saved CFBD /games responses."""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from cfb1.team_identity import TeamIdentityResolver


@dataclass(frozen=True)
class ScheduleRecord:
    game_id: int | str
    season: int
    week: int
    away_team: str
    home_team: str
    kickoff_utc: datetime
    source: str = "cfbd"

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "season": self.season,
            "week": self.week,
            "away_team": self.away_team,
            "home_team": self.home_team,
            "kickoff_utc": self.kickoff_utc.isoformat().replace("+00:00", "Z"),
            "source": self.source,
        }


@dataclass(frozen=True)
class ScheduleIssue:
    code: str
    row: int | None
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "row": self.row, "message": self.message}


@dataclass(frozen=True)
class ScheduleValidation:
    records: tuple[ScheduleRecord, ...]
    issues: tuple[ScheduleIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "records": [record.to_dict() for record in self.records],
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _integer(value: object, minimum: int) -> bool:
    return type(value) is int and value >= minimum


def _field(game: Mapping, camel: str, snake: str):
    """Accept raw JSON or serialized SDK names, but never choose a conflict."""
    if camel in game and snake in game and game[camel] != game[snake]:
        raise ValueError(f"Conflicting {camel} and {snake} values")
    return game.get(camel, game.get(snake))


def normalize_cfbd_schedule(
    games: Iterable[Mapping],
    *,
    season: int,
    week: int,
    resolver: TeamIdentityResolver,
    previous_records: Iterable[ScheduleRecord] = (),
) -> ScheduleValidation:
    """Validate one regular-season week without fetching or inferring identities.

    Source IDs retain their original int/string representation. Affected rows
    are excluded from records, including *all* sides of duplicate conflicts.
    Issues make the entire batch invalid; callers must not ignore them and
    treat the surviving records as a complete verified weekly slate.
    previous_records optionally detects changed teams/orientation for an ID
    across snapshots; a changed kickoff alone does not change game identity.
    """
    if not _integer(season, 1) or not _integer(week, 0):
        raise ValueError("season must be a positive integer; week must be >= 0")
    if isinstance(games, (str, bytes, Mapping)):
        raise ValueError("games must be an iterable of CFBD game objects")
    issues: list[ScheduleIssue] = []
    candidates: list[tuple[int, ScheduleRecord]] = []

    def flag(code: str, row: int | None, message: str) -> None:
        issues.append(ScheduleIssue(code, row, message))

    def team(value: object, row: int, side: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{side} team must be a nonempty string")
        identity = resolver.resolve_market_name(value)
        raw_canonical = value.strip()
        if (
            raw_canonical in resolver.canonical_team_names
            and identity.normalized_name in resolver.canonical_team_names
            and raw_canonical != identity.normalized_name
        ):
            flag("ambiguous_alias", row, f"{side} name {value!r} has two CFBD identities")
        if not identity.matched:
            flag("unresolved_team", row, f"{side} name {value!r} is not verified in CFBD")
        return identity.normalized_name

    for row, game in enumerate(games, 1):
        if not isinstance(game, Mapping):
            flag("invalid_record", row, "Expected a CFBD game object")
            continue
        try:
            game_id = game.get("id")
            if not (
                _integer(game_id, 1)
                or isinstance(game_id, str) and bool(game_id) and game_id == game_id.strip()
            ):
                raise ValueError("Missing or invalid source game id; no ID is synthesized")
            if (
                not _integer(game.get("season"), 1)
                or not _integer(game.get("week"), 0)
            ):
                raise ValueError("Source season/week must be integers")
            if game["season"] != season or game["week"] != week:
                flag("outside_week", row, "Source season/week differs from requested scope")
            season_type = _field(game, "seasonType", "season_type")
            if season_type is not None and season_type != "regular":
                flag("outside_season_type", row, "Only regular-season games are supported")
            tbd = _field(game, "startTimeTBD", "start_time_tbd")
            if tbd is not None and type(tbd) is not bool:
                raise ValueError("startTimeTBD must be a boolean when supplied")
            if tbd:
                flag("kickoff_tbd", row, "Source marks kickoff time TBD")
            away = team(_field(game, "awayTeam", "away_team"), row, "away")
            home = team(_field(game, "homeTeam", "home_team"), row, "home")
            if away == home:
                flag("inconsistent_home_away", row, "Home and away resolve to the same team")
            start = _field(game, "startDate", "start_date")
            if not isinstance(start, str):
                raise ValueError("Missing or invalid source startDate")
            kickoff = datetime.fromisoformat(start)
            if kickoff.tzinfo is None or kickoff.utcoffset() is None:
                raise ValueError("Kickoff requires an explicit UTC offset or Z")
            candidates.append((row, ScheduleRecord(
                game_id, season, week, away, home, kickoff.astimezone(timezone.utc)
            )))
        except (ValueError, TypeError) as error:
            flag("invalid_record", row, str(error))

    if not candidates and not issues:
        flag("empty_schedule", None, "No games supplied for the requested week")

    by_id = defaultdict(list)
    by_matchup = defaultdict(list)
    for row, record in candidates:
        by_id[str(record.game_id)].append((row, record))
        key = (frozenset((record.away_team, record.home_team)), record.kickoff_utc)
        by_matchup[key].append((row, record))

    for group in by_id.values():
        if len(group) > 1:
            assignments = {(r.away_team, r.home_team) for _, r in group}
            for row, _ in group:
                flag("duplicate_game_id", row, "Source game id appears more than once")
                if len(assignments) > 1:
                    flag("inconsistent_home_away", row, "Same game id has conflicting teams/orientation")
    for group in by_matchup.values():
        if len(group) > 1:
            assignments = {(r.away_team, r.home_team) for _, r in group}
            for row, _ in group:
                flag("duplicate_matchup", row, "Same teams and kickoff occur more than once")
                if len(assignments) > 1:
                    flag("inconsistent_home_away", row, "Same matchup has reversed home/away assignments")

    previous = defaultdict(set)
    for record in previous_records:
        previous[(record.source, str(record.game_id))].add(
            (record.season, record.away_team, record.home_team)
        )
    for row, record in candidates:
        assignments = previous.get((record.source, str(record.game_id)), set())
        if assignments and assignments != {(record.season, record.away_team, record.home_team)}:
            flag("inconsistent_home_away", row, "Game identity conflicts with a previous snapshot")

    rejected = {issue.row for issue in issues}
    records = tuple(sorted(
        (record for row, record in candidates if row not in rejected),
        key=lambda record: (record.kickoff_utc, record.away_team, record.home_team, str(record.game_id)),
    ))
    return ScheduleValidation(records, tuple(issues))
