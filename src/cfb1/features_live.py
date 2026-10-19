"""Fetch frozen CFBD features; no downstream models or market acquisition."""

import argparse
import json
from pathlib import Path
import sys

from cfb1.cfbd_features import FeatureBoundary, acquire_cfbd_features
from cfb1.cfbd_schedule import CFBDAcquisitionError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--data-through-week", type=int, required=True)
    parser.add_argument("--target-week", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--output-dir", type=Path, help="Exclusive snapshots; default report only")
    args = parser.parse_args(argv)
    try:
        boundary = FeatureBoundary(args.season, args.data_through_week, args.target_week)
        result = acquire_cfbd_features(boundary, timeout=args.timeout)
    except CFBDAcquisitionError as exc:
        print(json.dumps({"valid": False, "live_acquisition_succeeded": False,
                          "error": str(exc)}), file=sys.stderr)
        return 2
    except (ValueError, TypeError, KeyError):
        print(json.dumps({"valid": False, "error": "Invalid feature boundary or source schema"}), file=sys.stderr)
        return 2
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with (args.output_dir / "validation.json").open("x", encoding="utf-8") as f:
            json.dump(result.report, f, indent=2)
        if result.valid:
            with (args.output_dir / "df_cfbd.csv").open("x", encoding="utf-8", newline="") as f:
                result.df_cfbd.to_csv(f, index=False)
    print(json.dumps(result.report, indent=2))
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
