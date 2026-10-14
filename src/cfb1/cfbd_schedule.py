"""CFBD HTTP acquisition, separate from the unchanged offline validator."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
import json
import math
import os
from urllib import error, parse, request

from cfb1.schedule import ScheduleValidation, normalize_cfbd_schedule
from cfb1.team_identity import TeamIdentityResolver


CFBD_BASE_URL = "https://api.collegefootballdata.com"


class CFBDAcquisitionError(RuntimeError):
    """A safe error message that excludes credentials and response bodies."""


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not forward Authorization to a redirect destination.
        return None


def _get_array(path: str, params: dict, api_key: str | None, timeout: float) -> list:
    key = api_key if api_key is not None else os.environ.get("CFBD_API_KEY", "")
    if not isinstance(key, str) or not key.strip():
        raise CFBDAcquisitionError("CFBD_API_KEY is missing; configure it securely in the environment")
    key = key.strip()
    if "\n" in key or "\r" in key:
        raise CFBDAcquisitionError("CFBD_API_KEY contains invalid header characters")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise CFBDAcquisitionError("CFBD timeout must be a finite positive number")
    query = parse.urlencode(params)
    url = f"{CFBD_BASE_URL}{path}" + (f"?{query}" if query else "")
    req = request.Request(url, headers={
        "Authorization": f"Bearer {key}", "Accept": "application/json"
    })
    try:
        # Default HTTPS verification/proxy handling is retained. No retries or
        # redirects can silently change the requested provider or scope.
        with request.build_opener(_NoRedirect()).open(req, timeout=timeout) as response:
            if response.status != 200:
                raise CFBDAcquisitionError(f"CFBD returned HTTP {response.status}")
            payload = json.loads(response.read())
    except error.HTTPError as exc:
        raise CFBDAcquisitionError(f"CFBD returned HTTP {exc.code}") from None
    except (error.URLError, OSError, TimeoutError):
        raise CFBDAcquisitionError("CFBD connection failed; check outbound access and TLS connectivity") from None
    except (ValueError, UnicodeError):
        raise CFBDAcquisitionError("CFBD returned invalid JSON") from None
    if not isinstance(payload, list):
        raise CFBDAcquisitionError("CFBD response must be a JSON array")
    return payload


def fetch_cfbd_games(
    season: int, week: int, *, api_key: str | None = None, timeout: float = 30
) -> list:
    """Fetch one regular-season week without filtering or repairing raw rows."""
    if type(season) is not int or season < 1 or type(week) is not int or week < 0:
        raise CFBDAcquisitionError("season must be a positive integer; week must be >= 0")
    return _get_array("/games", {"year": season, "week": week, "seasonType": "regular"}, api_key, timeout)


def fetch_cfbd_team_names(*, api_key: str | None = None, timeout: float = 30) -> list[str]:
    """Obtain an independent CFBD school registry, never inferred from games.

    Membership in this general registry is not proof of the weekly efficiency
    matrix's feature coverage. A caller may supply that stricter resolver.
    """
    teams = _get_array("/teams", {}, api_key, timeout)
    if not teams:
        raise CFBDAcquisitionError("CFBD team registry is empty")
    names = []
    for row, team in enumerate(teams, 1):
        if not isinstance(team, Mapping) or not isinstance(team.get("school"), str) or not team["school"].strip():
            raise CFBDAcquisitionError(f"CFBD team registry row {row} has no valid school name")
        names.append(team["school"])
    return names


def _confirmed_kickoff(game: object) -> bool:
    """Count kickoff failures even when another field fails validation first."""
    if not isinstance(game, Mapping):
        return False
    for camel, snake in [("startDate", "start_date"), ("startTimeTBD", "start_time_tbd")]:
        if camel in game and snake in game and game[camel] != game[snake]:
            return False
    tbd = game.get("startTimeTBD", game.get("start_time_tbd"))
    if tbd is not None and tbd is not False:
        return False
    start = game.get("startDate", game.get("start_date"))
    if not isinstance(start, str):
        return False
    try:
        kickoff = datetime.fromisoformat(start)
        return kickoff.tzinfo is not None and kickoff.utcoffset() is not None
    except (ValueError, OverflowError):
        return False


@dataclass(frozen=True)
class LiveScheduleResult:
    raw_games: tuple
    validation: ScheduleValidation

    def to_dict(self) -> dict:
        issues = self.validation.issues
        def rows(codes: set[str]) -> set[int]:
            return {issue.row for issue in issues if issue.code in codes and issue.row is not None}
        result = self.validation.to_dict()
        result["summary"] = {
            "games_retrieved": len(self.raw_games),
            "games_successfully_normalized": len(self.validation.records),
            "games_rejected": len(rows({issue.code for issue in issues})),
            "unresolved_team_identities": sum(issue.code == "unresolved_team" for issue in issues),
            "games_with_unresolved_teams": len(rows({"unresolved_team"})),
            "ambiguous_aliases": sum(issue.code == "ambiguous_alias" for issue in issues),
            "duplicate_or_conflicting_records": len(rows({"duplicate_game_id", "duplicate_matchup", "inconsistent_home_away"})),
            "malformed_records": len(rows({"invalid_record"})),
            "games_missing_confirmed_kickoff": sum(not _confirmed_kickoff(game) for game in self.raw_games),
        }
        return result


def acquire_cfbd_schedule(
    season: int,
    week: int,
    *,
    resolver: TeamIdentityResolver | None = None,
    api_key: str | None = None,
    timeout: float = 30,
) -> LiveScheduleResult:
    """Fetch, then delegate every raw game to the existing validation boundary."""
    if type(season) is not int or season < 1 or type(week) is not int or week < 0:
        raise CFBDAcquisitionError("season must be a positive integer; week must be >= 0")
    if resolver is None:
        resolver = TeamIdentityResolver(fetch_cfbd_team_names(api_key=api_key, timeout=timeout))
    games = fetch_cfbd_games(season, week, api_key=api_key, timeout=timeout)
    validation = normalize_cfbd_schedule(games, season=season, week=week, resolver=resolver)
    return LiveScheduleResult(tuple(games), validation)
