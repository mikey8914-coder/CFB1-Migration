"""CELL 12 / OLD CELL 20 / OLD CELL 21 only; unchanged notebook formulas."""

import pandas as pd


EPA_TRIGGER_THRESHOLD = 0.12
FEI_MULTIPLIER = 30


def _require_columns(frame, columns):
    missing = [c for c in columns if c not in frame]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))


def _directional_team(row, field):
    if row[field] > 0:
        return row["Home_Team"]
    if row[field] < 0:
        return row["Away_Team"]
    return "EVEN"


def apply_epa_trigger(master: pd.DataFrame) -> pd.DataFrame:
    """CELL 12: absolute home edge >= 0.12, with raw home/away side labels."""
    _require_columns(master, ["Net_EPA_Edge_Home", "Home_Team", "Away_Team"])
    result = master.copy()
    result["EPA_Edge_Value"] = result["Net_EPA_Edge_Home"].abs()
    result["EPA_Edge_Team"] = result.apply(lambda row: _directional_team(row, "Net_EPA_Edge_Home"), axis=1)
    result["EPA_Trigger"] = result["EPA_Edge_Value"] >= EPA_TRIGGER_THRESHOLD
    triggers = int(result.EPA_Trigger.sum())
    below = len(result) - triggers
    if (result.EPA_Edge_Value.isna().sum() or result.EPA_Edge_Team.isna().sum()
            or triggers + below != len(result)):
        raise ValueError("Net EPA trigger validation failed")
    return result


def apply_fei_model(master_bcf: pd.DataFrame) -> pd.DataFrame:
    """OLD CELL 20: round home-minus-away FEI times 30 BEFORE classification."""
    _require_columns(master_bcf, ["Home_FEI", "Away_FEI", "Home_Team", "Away_Team"])
    result = master_bcf.copy()
    result["FEI_Model_Diff_Home"] = ((result.Home_FEI - result.Away_FEI) * FEI_MULTIPLIER).round(1)
    result["FEI_Model_Favorite"] = result.apply(lambda row: _directional_team(row, "FEI_Model_Diff_Home"), axis=1)
    result["FEI_Model_Margin"] = result.FEI_Model_Diff_Home.abs()
    diff = result.FEI_Model_Diff_Home
    polarity_errors = ((diff > 0) & (result.FEI_Model_Favorite != result.Home_Team)
                       | (diff < 0) & (result.FEI_Model_Favorite != result.Away_Team))
    even_errors = (diff == 0) & (result.FEI_Model_Favorite != "EVEN")
    if diff.isna().any() or polarity_errors.any() or even_errors.any():
        raise ValueError("FEI model polarity validation failed")
    return result


def apply_fei_market_edges(master_bcf: pd.DataFrame) -> pd.DataFrame:
    """OLD CELL 21: home market spread minus model home spread, per book."""
    _require_columns(master_bcf, ["FEI_Model_Diff_Home", "DK_Spread", "FD_Spread", "Home_Team", "Away_Team"])
    result = master_bcf.copy()
    result["FEI_Model_Home_Spread"] = (-result.FEI_Model_Diff_Home).round(1)
    # Preserve original assignment order and exact downstream column names.
    for book in ["DK", "FD"]:
        result[f"{book}_FEI_Edge_Home"] = (result[f"{book}_Spread"] - result.FEI_Model_Home_Spread).round(1)
    for book in ["DK", "FD"]:
        result[f"{book}_FEI_Edge_Value"] = result[f"{book}_FEI_Edge_Home"].abs()
    for book in ["DK", "FD"]:
        result[f"{book}_FEI_Edge_Team"] = result.apply(
            lambda row: _directional_team(row, f"{book}_FEI_Edge_Home"), axis=1)
    result["FEI_Books_Agree"] = result.DK_FEI_Edge_Team == result.FD_FEI_Edge_Team
    fields = ["FEI_Model_Home_Spread", "DK_Spread", "FD_Spread", "DK_FEI_Edge_Home", "FD_FEI_Edge_Home"]
    if result[fields].isna().any(axis=1).any():
        raise ValueError("FEI market comparison contains missing values")
    return result
