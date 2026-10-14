"""Offline schedule validator: python -m cfb1.schedule_validate --help."""

import argparse
import json
from pathlib import Path
import sys

from cfb1.schedule import normalize_cfbd_schedule
from cfb1.team_identity import TeamIdentityResolver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a saved CFBD weekly schedule")
    parser.add_argument("--games", required=True, type=Path, help="CFBD /games JSON array")
    parser.add_argument("--teams", required=True, type=Path, help="Nonnull CFBD team-name JSON array")
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--week", required=True, type=int)
    args = parser.parse_args(argv)
    try:
        games = json.loads(args.games.read_text(encoding="utf-8"))
        teams = json.loads(args.teams.read_text(encoding="utf-8"))
        if not isinstance(games, list):
            raise ValueError("--games must contain a JSON array")
        if not isinstance(teams, list) or not teams or any(
            not isinstance(name, str) or not name.strip() for name in teams
        ):
            raise ValueError("--teams must contain a nonempty array of nonblank strings")
        result = normalize_cfbd_schedule(
            games, season=args.season, week=args.week, resolver=TeamIdentityResolver(teams)
        )
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
