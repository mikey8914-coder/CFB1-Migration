"""File-based weekly BCF input validation; no acquisition or model calculations."""
import csv
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from cfb1.bcf import BCF_COLUMNS, BCF_METRICS, BCFValidationError, parse_bcf_csv, normalize_bcf, merge_bcf
from cfb1.cfbd_features import FeatureBoundary
from cfb1.team_identity import TeamIdentityResolver


class WeeklyBCFValidationError(ValueError):
    def __init__(self, report):
        super().__init__('Weekly BCF input is not production-ready')
        self.report = report


@dataclass
class WeeklyBCFInput:
    report: dict
    normalized: pd.DataFrame | None

    @property
    def production_ready(self):
        return self.report['production_ready']


def weekly_bcf_path(root, season, week):
    if type(season) is not int or season < 1 or type(week) is not int or week < 1:
        raise ValueError('Require positive integer season and target week')
    return Path(root) / str(season) / f'week_{week:02d}' / 'bcf.csv'


def _context(names, target_market):
    names = list(names)
    if (not names or any(not isinstance(n, str) or not n.strip() for n in names)
            or len(set(n.strip() for n in names)) != len(names)):
        raise ValueError('Supply unique nonblank canonical names from the full CFBD feature universe')
    names = [n.strip() for n in names]
    if not len(target_market) or any(c not in target_market for c in ['Home_CFBD_Name','Away_CFBD_Name']):
        raise ValueError('A nonempty target slate with canonical team keys is required')
    target = target_market[['Home_CFBD_Name','Away_CFBD_Name']]
    if target.isna().any().any():
        raise ValueError('Target-slate canonical names cannot be null')
    required = set(target.Home_CFBD_Name) | set(target.Away_CFBD_Name)
    if not required <= set(names):
        raise ValueError('Target-slate teams are missing from the CFBD feature universe')
    return names, required


def validate_weekly_bcf(path, *, season, week, data_through_week,
        canonical_team_names, target_market, metadata_path=None):
    """Report all inspectable defects; no bad rows dropped, filled or deduplicated.

    Extras are reported and ignored. Only the seven BCF fields reach the legacy
    parser/normalizer. Read again for each run; no stale validation cache.
    """
    FeatureBoundary(season, data_through_week, week)
    names, target = _context(canonical_team_names, target_market)
    resolver = TeamIdentityResolver(names)
    path = Path(path)
    metadata_path = Path(metadata_path) if metadata_path else path.with_suffix('.metadata.json')
    report = {'season':season, 'week':week, 'data_through_week':data_through_week,
        'file':str(path), 'metadata_file':str(metadata_path), 'metadata':None,
        'csv_sha256':None, 'production_ready':False, 'rows_supplied':0,
        'unique_raw_teams':0, 'unique_teams':0, 'duplicate_raw_teams':[],
        'duplicate_canonical_teams':[], 'unresolved_identities':[], 'malformed_values':[],
        'missing_required_fields':[], 'duplicate_headers':[], 'extra_columns_ignored':[],
        'scheduled_fbs_teams_not_represented':sorted(target), 'bcf_teams_not_on_target_slate':[],
        'errors':[]}
    try:
        def reject_constant(value):
            raise ValueError('Nonstandard JSON numeric constant: '+value)
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'),parse_constant=reject_constant)
        if not isinstance(metadata, dict): raise ValueError('Metadata must be an object')
        report['metadata'] = metadata
        for field, expected in [('season',season),('week',week),('data_through_week',data_through_week)]:
            if type(metadata.get(field)) is not int or metadata[field] != expected:
                report['errors'].append('Metadata mismatch: '+field)
        if not isinstance(metadata.get('source'),str) or not metadata['source'].strip():
            report['errors'].append('Metadata requires a nonblank source URL or citation')
        stamp = metadata.get('retrieved_at')
        if not isinstance(stamp,str): raise ValueError('Metadata requires retrieved_at with timezone')
        when = datetime.fromisoformat(stamp)
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError('Metadata retrieved_at requires timezone')
    except (OSError, ValueError, TypeError) as exc:
        report['errors'].append('Metadata unavailable or invalid: '+str(exc))
    # Conventional paths cannot silently conflict with explicitly supplied scope.
    match = re.fullmatch(r'week_(\d+)',path.parent.name)
    if match and path.parent.parent.name.isdigit():
        if (int(path.parent.parent.name),int(match[1])) != (season,week):
            report['errors'].append('Conventional file path conflicts with season/week')
    try:
        content = path.read_bytes()
        report['csv_sha256'] = sha256(content).hexdigest()
        text = content.decode('utf-8-sig')
        rows = list(csv.reader(StringIO(text),strict=True))
        rows = [r for r in rows if r]  # CSV blank lines have no data fields.
        if not rows: raise ValueError('Empty BCF input')
        header = rows[0]
        report['duplicate_headers'] = sorted({h for h in header if header.count(h)>1})
        report['missing_required_fields'] = [c for c in BCF_COLUMNS if c not in header]
        report['extra_columns_ignored'] = [c for c in header if c not in BCF_COLUMNS]
        report['rows_supplied'] = len(rows)-1
        if report['duplicate_headers']:report['errors'].append('Duplicate CSV headers')
        if any(len(row)!=len(header) for row in rows[1:]):
            raise ValueError('CSV row length differs from header')
        if report['missing_required_fields']:report['errors'].append('Missing required CSV fields')
        if report['duplicate_headers'] or report['missing_required_fields']:
            return WeeklyBCFInput(report,None)
        raw = pd.read_csv(StringIO(text))
        if not len(raw):report['errors'].append('No rating rows supplied')
        prepared_names = raw.Team.astype(str).str.strip()
        canonical = prepared_names.map(lambda n:resolver.resolve_bcf_name(n).normalized_name)
        report['unique_raw_teams'] = int(raw.Team.nunique(dropna=False))
        report['unique_teams'] = int(canonical.nunique())
        report['duplicate_raw_teams'] = sorted(set(raw.loc[raw.Team.duplicated(keep=False),'Team'].astype(str)))
        report['duplicate_canonical_teams'] = sorted(set(canonical[canonical.duplicated(keep=False)]))
        for i,(original,identity) in enumerate(zip(raw.Team,canonical),2):
            if pd.isna(original) or identity not in resolver.canonical_team_names:
                report['unresolved_identities'].append({'row':i,'team':None if pd.isna(original) else str(original),'canonical':identity})
        for col in BCF_METRICS:
            numeric = pd.to_numeric(raw[col],errors='coerce')
            bad = numeric.isna() | ~np.isfinite(numeric)
            for pos in np.flatnonzero(bad.to_numpy()):
                value = raw.iloc[pos][col]
                report['malformed_values'].append({'row':int(pos)+2,'field':col,
                    'value':None if pd.isna(value) else str(value)})
        report['scheduled_fbs_teams_not_represented'] = sorted(target-set(canonical))
        report['bcf_teams_not_on_target_slate'] = sorted(set(canonical)-target)
        for key in ['duplicate_raw_teams','duplicate_canonical_teams','unresolved_identities',
                    'malformed_values','scheduled_fbs_teams_not_represented']:
            if report[key]: report['errors'].append(key)
        normalized = None
        if not report['errors']:
            # The authoritative existing BCF ingestion and shared canonical gates.
            seven = raw[BCF_COLUMNS].to_csv(index=False)
            normalized = normalize_bcf(parse_bcf_csv(seven),names,target_market)
            report['production_ready'] = True
        return WeeklyBCFInput(report,normalized)
    except (OSError, UnicodeError, ValueError, TypeError, csv.Error, pd.errors.ParserError) as exc:
        if isinstance(exc,BCFValidationError):
            report['legacy_diagnostics'] = exc.diagnostics
        report['errors'].append('CSV unavailable or invalid: '+str(exc))
        return WeeklyBCFInput(report,None)


def load_weekly_bcf(path, *, season, week, data_through_week,
        canonical_team_names, target_market, metadata_path=None):
    """Pipeline boundary: return normalized BCF or raise with full readiness report."""
    result = validate_weekly_bcf(path,season=season,week=week,data_through_week=data_through_week,
        canonical_team_names=canonical_team_names,target_market=target_market,metadata_path=metadata_path)
    if not result.production_ready:
        raise WeeklyBCFValidationError(result.report)
    return result.normalized


def merge_weekly_bcf(master, path, *, season, week, data_through_week,
        canonical_team_names, metadata_path=None):
    """Narrow file interface to the existing OLD CELL 19 merge, without formulas."""
    normalized = load_weekly_bcf(path,season=season,week=week,data_through_week=data_through_week,
        canonical_team_names=canonical_team_names,target_market=master,metadata_path=metadata_path)
    return merge_bcf(master,normalized)
