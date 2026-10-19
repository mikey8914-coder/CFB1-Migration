"""Week-frozen notebook CFBD inputs, without downstream model calculations."""

from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic

import pandas as pd

from cfb1.cfbd_schedule import _get_array


ADVANCED_FIELDS = {
    "Off_SuccessRate": "offense.successRate",
    "Off_PassingDown_SR": "offense.passingDowns.successRate",
    "Off_Explosiveness": "offense.explosiveness",
    "Def_SuccessRate": "defense.successRate",
    "Def_PassingDown_SR": "defense.passingDowns.successRate",
    "Def_Havoc_Rate": "defense.havoc.total",
    "Off_LineYards": "offense.lineYards",
}
REQUIRED_COLUMNS = ["team", "Off_EPA", "Def_EPA", "Net_EPA_Margin", *ADVANCED_FIELDS]
PLAY_COLUMNS = ["offense", "defense", "ppa"]


@dataclass(frozen=True)
class FeatureBoundary:
    season: int
    data_through_week: int
    target_week: int

    def __post_init__(self):
        if (type(self.season) is not int or self.season < 1
                or type(self.data_through_week) is not int
                or type(self.target_week) is not int
                or not 1 <= self.data_through_week < self.target_week):
            raise ValueError("Require positive season and 1 <= data_through_week < target_week")

    def request_plan(self):
        return [
            ("/plays", {"year": self.season, "week": week, "seasonType": "regular"})
            for week in range(1, self.data_through_week + 1)
        ] + [("/stats/season/advanced", {
            "year": self.season, "seasonType": "regular",
            "startWeek": 1, "endWeek": self.data_through_week,
        })]


def aggregate_play_ppa(play_rows):
    """CELL 2: drop null triples once, then unweighted play means per side."""
    plays = pd.DataFrame(play_rows)
    missing = [c for c in PLAY_COLUMNS if c not in plays]
    if missing:
        raise ValueError("Missing required play columns: " + ", ".join(missing))
    valid = plays.dropna(subset=PLAY_COLUMNS).copy()
    # No coercion, deduplication, name trimming, play-type or opponent filters.
    offense = valid.groupby("offense", as_index=False)["ppa"].mean().rename(
        columns={"offense": "team", "ppa": "Off_EPA"})
    defense = valid.groupby("defense", as_index=False)["ppa"].mean().rename(
        columns={"defense": "team", "ppa": "Def_EPA"})
    ppa = pd.merge(offense, defense, on="team", how="outer")
    return plays, valid, offense, defense, ppa


def normalize_advanced_stats(advanced_rows):
    """CELL 3 exact nested paths; no invented replacement fields."""
    advanced = pd.json_normalize(advanced_rows)
    missing = [c for c in ["team", *ADVANCED_FIELDS.values()] if c not in advanced]
    if missing:
        raise ValueError("Missing required advanced columns: " + ", ".join(missing))
    clean = pd.DataFrame({"team": advanced["team"], **{
        name: advanced[path] for name, path in ADVANCED_FIELDS.items()
    }})
    # OLD CELL 25 reuses this exact payload; no additional season-wide fetch.
    lineyards = pd.DataFrame([
        {"team": row.get("team"),
         "Def_LineYards": (row.get("defense") or {}).get("lineYards")}
        for row in advanced_rows
    ], columns=["team", "Def_LineYards"])
    return advanced, clean, lineyards


@dataclass
class FeatureTables:
    df_ppa_plays: pd.DataFrame
    df_ppa_valid: pd.DataFrame
    df_off_ppa: pd.DataFrame
    df_def_ppa: pd.DataFrame
    df_ppa: pd.DataFrame
    df_adv: pd.DataFrame
    df_adv_clean: pd.DataFrame
    df_def_lineyards: pd.DataFrame
    df_cfbd: pd.DataFrame
    report: dict

    @property
    def valid(self):
        return self.report["valid"]


def build_feature_tables(play_rows, advanced_rows):
    """Pure transformation retaining failed-table diagnostics, never repairing rows."""
    plays, valid, offense, defense, ppa = aggregate_play_ppa(play_rows)
    advanced, clean, lineyards = normalize_advanced_stats(advanced_rows)
    cfbd = pd.merge(ppa, clean, on="team", how="inner")
    cfbd["Net_EPA_Margin"] = cfbd["Off_EPA"] - cfbd["Def_EPA"]
    duplicate_teams = int(cfbd.duplicated(subset=["team"], keep=False).sum())
    critical_nulls = {c: int(v) for c, v in cfbd[REQUIRED_COLUMNS].isna().sum().items()}
    matrix_pass = bool(len(cfbd) and not duplicate_teams and not sum(critical_nulls.values()))
    line_duplicates = int(lineyards.duplicated(subset=["team"], keep=False).sum())
    source_nulls = int(lineyards["Def_LineYards"].isna().sum())
    line_merge_pass = not duplicate_teams and not line_duplicates
    if line_merge_pass:
        cfbd = cfbd.merge(lineyards, on="team", how="left", validate="one_to_one")
    else:
        # Notebook raises MergeError. Keep diagnostic rows but no Cartesian
        # defensive merge; valid is false and master/export boundaries refuse it.
        cfbd["Def_LineYards"] = float("nan")
    missing_lineyards = int(cfbd["Def_LineYards"].isna().sum())
    lineyards_pass = bool(line_merge_pass and not source_nulls and not missing_lineyards)
    structure_pass = bool(len(ppa) and len(advanced_rows))
    ppa_names = set(ppa["team"].dropna())
    advanced_names = set(clean["team"].dropna())
    report = {
        "valid": bool(structure_pass and matrix_pass and lineyards_pass),
        "acquisition_structure_pass": structure_pass,
        "efficiency_matrix_pass": matrix_pass,
        "defensive_lineyards_pass": lineyards_pass,
        "play_records": len(plays), "valid_ppa_rows": len(valid),
        "dropped_null_play_rows": len(plays) - len(valid),
        "play_nulls": {c: int(plays[c].isna().sum()) for c in PLAY_COLUMNS},
        "advanced_null_team_rows": int(clean["team"].isna().sum()),
        "offense_teams": len(offense), "defense_teams": len(defense),
        "ppa_teams": len(ppa), "advanced_rows": len(clean),
        "advanced_unique_teams": int(clean["team"].nunique()),
        "merged_rows": len(cfbd), "merged_unique_teams": int(cfbd["team"].nunique()),
        "duplicate_team_rows": duplicate_teams,
        "critical_nulls": critical_nulls, "total_critical_nulls": sum(critical_nulls.values()),
        "defensive_lineyards_duplicate_rows": line_duplicates,
        "defensive_lineyards_source_nulls": source_nulls,
        "defensive_lineyards_merge_nulls": missing_lineyards,
        "ppa_only_teams": sorted(ppa_names - advanced_names),
        "advanced_only_teams": sorted(advanced_names - ppa_names),
    }
    return FeatureTables(plays, valid, offense, defense, ppa, advanced, clean,
                         lineyards, cfbd, report)


def acquire_cfbd_features(boundary: FeatureBoundary, *, api_key=None, timeout=60):
    """Every HTTP request must succeed; no partial live feature set is returned."""
    if not isinstance(boundary, FeatureBoundary):
        raise TypeError("Use an explicit FeatureBoundary")
    plays = []
    requests = []
    started = datetime.now(timezone.utc).isoformat()
    clock_start = monotonic()
    for path, params in boundary.request_plan():
        request_started = datetime.now(timezone.utc).isoformat()
        rows = _get_array(path, params, api_key, timeout)
        requests.append({"path": path, "params": params, "http_status": 200,
                         "started_at": request_started,
                         "completed_at": datetime.now(timezone.utc).isoformat(), "rows": len(rows)})
        if path == "/plays":
            plays.extend(rows)
        else:
            advanced = rows
    result = build_feature_tables(plays, advanced)
    result.report.update({
        "season": boundary.season, "data_through_week": boundary.data_through_week,
        "target_week": boundary.target_week, "requests": requests,
        "live_acquisition_succeeded": True, "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(monotonic() - clock_start, 3),
    })
    return result


def merge_master_features(target_market, features: FeatureTables):
    """CELL 11 associations and home edge only; no EPA triggers or later models.

    Canonical input keys must already come from the shared identity resolver.
    Defensive line yards are prefixed alongside the other acquired features.
    """
    if not features.valid:
        raise ValueError("CFBD feature validation failed; do not merge into master")
    required = ["Home_Team", "Away_Team", "Home_CFBD_Name", "Away_CFBD_Name"]
    if any(c not in target_market for c in required):
        raise ValueError("Master input lacks required raw/canonical team columns")
    master = target_market.copy()
    for side in ["Home", "Away"]:
        names = {c: f"{side}_{c}" for c in features.df_cfbd.columns if c != "team"}
        names["team"] = f"{side}_CFBD_Name"
        master = master.merge(features.df_cfbd.rename(columns=names),
                              on=f"{side}_CFBD_Name", how="left", validate="many_to_one")
    master["Net_EPA_Edge_Home"] = master["Home_Net_EPA_Margin"] - master["Away_Net_EPA_Margin"]
    if (len(master) != len(target_market)
            or master[["Home_Net_EPA_Margin", "Away_Net_EPA_Margin"]].isna().any().any()
            or master.duplicated(subset=["Home_Team", "Away_Team"], keep=False).any()):
        raise ValueError("Target-week CFBD merge failed; do not continue to model calculations")
    return master
