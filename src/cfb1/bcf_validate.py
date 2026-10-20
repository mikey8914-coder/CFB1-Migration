"""Offline weekly BCF readiness command: python -m cfb1.bcf_validate --help."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pandas as pd

from cfb1.bcf_weekly import validate_weekly_bcf
from cfb1.schedule import normalize_cfbd_schedule
from cfb1.team_identity import TeamIdentityResolver


def target_slate(games, *, season, week, canonical_team_names, target_date=None):
    """Validate saved CFBD FBS/FBS scope; excluded non-FBS games are explicit.

    Classification is required, not guessed from feature/alias membership.
    The date filter is Eastern, matching the existing CFB1 market-day convention.
    """
    if not isinstance(games,list) or not games:
        raise ValueError('Supply a nonempty raw CFBD /games JSON array')
    selected, excluded = [], []
    for row in games:
        if not isinstance(row,dict) or type(row.get('season')) is not int or type(row.get('week')) is not int:
            raise ValueError('Malformed CFBD schedule scope')
        if row['season']!=season or row['week']!=week:
            raise ValueError('Schedule season/week mismatch')
        classes = []
        for camel,snake in [('homeClassification','home_classification'),('awayClassification','away_classification')]:
            if camel in row and snake in row and row[camel]!=row[snake]:
                raise ValueError('Conflicting schedule classifications')
            value = row.get(camel,row.get(snake))
            if not isinstance(value,str) or value.lower() not in {'fbs','fcs','ii','iii'}:
                raise ValueError('Explicit CFBD team classifications are required for FBS scope')
            classes.append(value.lower())
        if classes != ['fbs','fbs']:
            excluded.append({'game_id':row.get('id'),'reason':'OUTSIDE_FBS_VS_FBS_SCOPE'})
        else:
            selected.append(row)
    validation = normalize_cfbd_schedule(selected,season=season,week=week,
        resolver=TeamIdentityResolver(canonical_team_names))
    if not validation.valid:
        raise ValueError('Target CFBD schedule failed validation: '+', '.join(sorted({i.code for i in validation.issues})))
    records = list(validation.records)
    if target_date is not None:
        day = date.fromisoformat(target_date)
        inside = []
        for record in records:
            if record.kickoff_utc.astimezone(ZoneInfo('America/New_York')).date()==day:
                inside.append(record)
            else:
                excluded.append({'game_id':record.game_id,'reason':'OUTSIDE_TARGET_DATE'})
        records = inside
    if not records:
        raise ValueError('No target FBS/FBS games; cannot validate empty slate coverage')
    frame = pd.DataFrame([{'game_id':r.game_id,'Home_CFBD_Name':r.home_team,
        'Away_CFBD_Name':r.away_team} for r in records])
    return frame,excluded


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file',required=True,type=Path,help='Weekly BCF CSV')
    parser.add_argument('--metadata',type=Path,help='Default: <CSV stem>.metadata.json')
    parser.add_argument('--season',required=True,type=int)
    parser.add_argument('--week',required=True,type=int,help='Target week')
    parser.add_argument('--data-through-week',required=True,type=int)
    parser.add_argument('--features',required=True,type=Path,help='Full migrated df_cfbd.csv feature universe')
    parser.add_argument('--games',required=True,type=Path,help='Saved raw CFBD /games JSON for the target week, with classifications')
    parser.add_argument('--target-date',help='Optional YYYY-MM-DD Eastern game-date scope; otherwise entire week')
    args = parser.parse_args(argv)
    try:
        features = pd.read_csv(args.features)
        if 'team' not in features or features.team.isna().any():
            raise ValueError('Feature CSV requires nonnull team column')
        names = features.team.tolist()
        if not names or any(not isinstance(n,str) or not n.strip() for n in names) or len({n.strip() for n in names})!=len(names):
            raise ValueError('Feature universe requires unique nonblank canonical team names')
        games = json.loads(args.games.read_text(encoding='utf-8'))
        slate,excluded = target_slate(games,season=args.season,week=args.week,
            canonical_team_names=names,target_date=args.target_date)
        result = validate_weekly_bcf(args.file,season=args.season,week=args.week,
            data_through_week=args.data_through_week,canonical_team_names=names,
            target_market=slate,metadata_path=args.metadata)
        report = result.report
        report.update({'target_date':args.target_date,'target_games':len(slate),
            'slate_scope':'FBS_VS_FBS','excluded_schedule_games':excluded,
            'feature_file':str(args.features),'schedule_file':str(args.games)})
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'season':args.season,'week':args.week,'production_ready':False,
            'error':str(exc)},ensure_ascii=False,indent=2),file=sys.stderr)
        return 2
    print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if result.production_ready else 1


if __name__=='__main__':
    raise SystemExit(main())
