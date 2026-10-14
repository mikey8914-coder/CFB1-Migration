"""One live CFBD acquisition: python -m cfb1.schedule_live --help."""

import argparse
import json
from pathlib import Path
import sys

from cfb1.cfbd_schedule import CFBDAcquisitionError, acquire_cfbd_schedule
from cfb1.team_identity import TeamIdentityResolver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and validate one CFBD regular-season week")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--teams", type=Path, help="Optional canonical CFBD names JSON; otherwise fetch /teams")
    args = parser.parse_args(argv)
    try:
        resolver = None
        if args.teams is not None:
            teams = json.loads(args.teams.read_text(encoding="utf-8"))
            if not isinstance(teams, list) or not teams or any(
                not isinstance(name, str) or not name.strip() for name in teams
            ):
                raise ValueError("Canonical team file must be a nonempty array of nonblank strings")
            resolver = TeamIdentityResolver(teams)
        result = acquire_cfbd_schedule(args.season, args.week, resolver=resolver, timeout=args.timeout)
    except CFBDAcquisitionError as exc:
        print(json.dumps({"valid": False, "live_acquisition_succeeded": False, "error": str(exc)}), file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError):
        # Do not print arbitrary input/error contents that could contain secrets.
        print(json.dumps({"valid": False, "live_acquisition_succeeded": False, "error": "Invalid input or schedule configuration"}), file=sys.stderr)
        return 2
    report = result.to_dict()
    report["live_acquisition_succeeded"] = True
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result.validation.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
