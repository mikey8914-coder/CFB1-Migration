"""Manual BCF input, canonical normalization, and master joins.

Frozen labels are CELL 13, CELL 14, OLD CELL 19 (not OLD CELL 17/18).
No acquisition, model signals, or later notebook stages run here.
"""

from io import StringIO

import pandas as pd

from cfb1.team_identity import TeamIdentityResolver, normalize_bcf_team_name


BCF_METRICS = ["FEI", "OFEI", "DFEI", "SFEI", "OAY", "DAY"]
BCF_COLUMNS = ["Team", *BCF_METRICS]


class BCFValidationError(ValueError):
    """A failed notebook gate with structured, inspectable counts."""

    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = diagnostics


def parse_bcf_csv(bcf_csv: str) -> pd.DataFrame:
    """CELL 13: CSV inference, pre-strip duplicates, numeric coercion, strip."""
    bcf_text = bcf_csv.strip()
    if not bcf_text or bcf_text == "PASTE THE GEM CSV HERE":
        raise BCFValidationError("BCF input missing", {"missing_input": True})
    raw = pd.read_csv(StringIO(bcf_text))
    missing = [c for c in BCF_COLUMNS if c not in raw]
    duplicates = int(raw.duplicated(subset=["Team"], keep=False).sum()) if "Team" in raw else 0
    numeric_problems = {}
    if not missing:
        for col in BCF_METRICS:
            converted = pd.to_numeric(raw[col], errors="coerce")
            numeric_problems[col] = int(converted.isna().sum())
            raw[col] = converted
    if "Team" in raw:
        raw["Team"] = raw["Team"].astype(str).str.strip()
    diagnostics = {"rows": len(raw), "missing_columns": missing,
                   "duplicate_raw_team_rows": duplicates, "numeric_problems": numeric_problems}
    if not len(raw) or missing or duplicates or sum(numeric_problems.values()):
        raise BCFValidationError("BCF raw input validation failed", diagnostics)
    return raw


def normalize_bcf(raw: pd.DataFrame, canonical_team_names, target_market: pd.DataFrame) -> pd.DataFrame:
    """CELL 14: exact shared BCF map, full-universe and target coverage gates.

    canonical_team_names must come from the CFBD feature universe, not just the
    slate or alias values. The parser already strips Team; do not clean it again.
    """
    resolver = TeamIdentityResolver(canonical_team_names)
    normalized = raw.copy()
    normalized["CFBD_Team"] = normalized["Team"].map(normalize_bcf_team_name)
    unmatched = normalized.loc[
        ~normalized.CFBD_Team.isin(resolver.canonical_team_names), ["Team", "CFBD_Team"]]
    target_teams = set(target_market.Home_CFBD_Name.tolist() + target_market.Away_CFBD_Name.tolist())
    missing = sorted(target_teams - set(normalized.CFBD_Team))
    duplicates = int(normalized.duplicated(subset=["CFBD_Team"], keep=False).sum())
    if len(unmatched) or missing or duplicates:
        raise BCFValidationError("BCF name normalization failed", {
            "unmatched_rows": unmatched.to_dict(orient="records"),
            "missing_target_teams": missing, "duplicate_normalized_rows": duplicates,
        })
    return normalized


def merge_bcf(master: pd.DataFrame, bcf: pd.DataFrame) -> pd.DataFrame:
    """OLD CELL 19: two left many-to-one joins, preserving all existing context."""
    merged = master.copy()
    for side in ["Home", "Away"]:
        side_bcf = bcf[["CFBD_Team", *BCF_METRICS]].copy().rename(columns={
            "CFBD_Team": f"{side}_CFBD_Name",
            **{metric: f"{side}_{metric}" for metric in BCF_METRICS},
        })
        merged = merged.merge(side_bcf, on=f"{side}_CFBD_Name", how="left", validate="many_to_one")
    diagnostics = {
        "expected_games": len(master), "merged_games": len(merged),
        "missing_home_fei": int(merged.Home_FEI.isna().sum()),
        "missing_away_fei": int(merged.Away_FEI.isna().sum()),
        "duplicate_game_rows": int(merged.duplicated(subset=["Home_Team", "Away_Team"], keep=False).sum()),
    }
    if (len(merged) != len(master) or diagnostics["missing_home_fei"]
            or diagnostics["missing_away_fei"] or diagnostics["duplicate_game_rows"]):
        raise BCFValidationError("BCF merge validation failed", diagnostics)
    return merged
