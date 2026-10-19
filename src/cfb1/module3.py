"""OLD CELL 23–31 signal extraction only; no routing or downstream models."""

import pandas as pd


PASSING_DOWN_SR_THRESHOLD = 0.273
DEF_HAVOC_THRESHOLD = 0.192
OFF_LINE_YARDS_THRESHOLD = 3.5
DEF_LINE_YARDS_THRESHOLD = 3.3
EXPLOSIVENESS_THRESHOLD = 1.40
OFF_SUCCESS_RATE_MAX = 0.42
DEF_SUCCESS_RATE_MAX = 0.33
OAY_HIGH_THRESHOLD = 0.54125
DAY_WEAK_THRESHOLD = 0.56825

SIGNAL_LABELS = {
    "Havoc_Trap": "HAVOC_TRAP_NEGATIVE",
    "LineYards_Push": "LINE_YARDS_POSITIVE",
    "Explosiveness_Fraud": "EXPLOSIVENESS_FRAUD_NEGATIVE",
    "OAY_DAY_Edge": "OAY_DAY_POSITIVE",
}


def apply_market_favorites(master):
    """OLD CELL 23: compare FEI favorite with each book's home-spread favorite."""
    result = master.copy()

    def favorite(row, field):
        if row[field] < 0:
            return row["Home_Team"]
        if row[field] > 0:
            return row["Away_Team"]
        return "PICKEM"

    for book in ["DK", "FD"]:
        result[f"{book}_Market_Favorite"] = result.apply(
            lambda row: favorite(row, f"{book}_Spread"), axis=1)
    for book in ["DK", "FD"]:
        result[f"{book}_FEI_Market_Agree"] = result.FEI_Model_Favorite == result[f"{book}_Market_Favorite"]
    fields = ["DK_Market_Favorite", "FD_Market_Favorite", "DK_FEI_Market_Agree", "FD_FEI_Market_Agree"]
    if result[fields].isna().any(axis=1).any():
        raise ValueError("FEI vs market favorite validation failed")
    return result


def refresh_defensive_lineyards(cfbd, lineyards):
    """OLD CELL 25 using committed FeatureTables.df_def_lineyards.

    The source derivation is already normalize_advanced_stats in cfbd_features:
    (team_row.get('defense') or {}).get('lineYards') from the bounded payload.
    Reuse its output; never fetch again or alter the committed feature layer.
    """
    duplicates = int(lineyards.duplicated(subset=["team"], keep=False).sum())
    missing_source = int(lineyards.Def_LineYards.isna().sum())
    result = cfbd.drop(columns=["Def_LineYards"], errors="ignore").merge(
        lineyards[["team", "Def_LineYards"]], on="team", how="left", validate="one_to_one")
    if duplicates or missing_source or result.Def_LineYards.isna().sum():
        raise ValueError("Defensive Line Yards validation failed")
    return result


def refresh_master_lineyards(master, cfbd, *, expected_games):
    """OLD CELL 26; expected_games is len(df_target_market), not inferred here."""
    result = master.drop(columns=["Home_Def_LineYards", "Away_Def_LineYards"], errors="ignore")
    for side in ["Home", "Away"]:
        lookup = cfbd[["team", "Def_LineYards"]].copy().rename(columns={
            "team": f"{side}_CFBD_Name", "Def_LineYards": f"{side}_Def_LineYards"})
        result = result.merge(lookup, on=f"{side}_CFBD_Name", how="left", validate="many_to_one")
    if (len(result) != expected_games or result.Home_Def_LineYards.isna().sum()
            or result.Away_Def_LineYards.isna().sum()
            or result.duplicated(subset=["Home_Team", "Away_Team"], keep=False).sum()):
        raise ValueError("Defensive Line Yards master-card merge failed")
    return result


def _validate_signal(result, inputs, outputs, label):
    if result[inputs].isna().any(axis=1).any() or result[outputs].isna().any(axis=1).any():
        raise ValueError(label + " validation failed")
    return result


def apply_havoc_trap(master):
    """OLD CELL 24: negative for the named offense, positive for its opponent."""
    result = master.copy()
    inputs = []
    for side, opponent in [("Away", "Home"), ("Home", "Away")]:
        offense, defense = f"{side}_Off_PassingDown_SR", f"{opponent}_Def_Havoc_Rate"
        inputs.extend([offense, defense])
        result[f"{side}_Havoc_Trap"] = ((result[offense] <= PASSING_DOWN_SR_THRESHOLD)
                                          & (result[defense] >= DEF_HAVOC_THRESHOLD))
    return _validate_signal(result, inputs, ["Away_Havoc_Trap", "Home_Havoc_Trap"], "Havoc Trap")


def apply_lineyards_push(master):
    """OLD CELL 27: offensive >=3.5 AND opposing defensive >=3.3."""
    result = master.copy()
    inputs = []
    for side, opponent in [("Away", "Home"), ("Home", "Away")]:
        offense, defense = f"{side}_Off_LineYards", f"{opponent}_Def_LineYards"
        inputs.extend([offense, defense])
        result[f"{side}_LineYards_Push"] = ((result[offense] >= OFF_LINE_YARDS_THRESHOLD)
                                             & (result[defense] >= DEF_LINE_YARDS_THRESHOLD))
    return _validate_signal(result, inputs, ["Away_LineYards_Push", "Home_LineYards_Push"], "Line Yards Push")


def apply_explosiveness_fraud(master):
    """OLD CELL 28: negative for the named offense; all three tests required."""
    result = master.copy()
    inputs = []
    for side, opponent in [("Away", "Home"), ("Home", "Away")]:
        explosion = f"{side}_Off_Explosiveness"
        offense, defense = f"{side}_Off_SuccessRate", f"{opponent}_Def_SuccessRate"
        inputs.extend([explosion, offense, defense])
        result[f"{side}_Explosiveness_Fraud"] = (
            (result[explosion] >= EXPLOSIVENESS_THRESHOLD)
            & (result[offense] <= OFF_SUCCESS_RATE_MAX)
            & (result[defense] <= DEF_SUCCESS_RATE_MAX))
    return _validate_signal(result, inputs, ["Away_Explosiveness_Fraud", "Home_Explosiveness_Fraud"], "Explosiveness Fraud")


def apply_oay_day_edge(master):
    """OLD CELL 30: own OAY >=0.54125 AND opponent DAY >=0.56825."""
    result = master.copy()
    inputs = []
    for side, opponent in [("Away", "Home"), ("Home", "Away")]:
        offense, defense = f"{side}_OAY", f"{opponent}_DAY"
        inputs.extend([offense, defense])
        result[f"{side}_OAY_DAY_Edge"] = ((result[offense] >= OAY_HIGH_THRESHOLD)
                                           & (result[defense] >= DAY_WEAK_THRESHOLD))
    return _validate_signal(result, inputs, ["Away_OAY_DAY_Edge", "Home_OAY_DAY_Edge"], "OAY / DAY Edge")


def signal_diagnostic(master, signal):
    """Preserve the four readable trigger-table schemas, row order and sorting."""
    specs = {
        "Havoc_Trap": ("Offense_In_Trap", [("PassingDown_SR", "Off_PassingDown_SR", False),
                                           ("Opp_Def_Havoc", "Def_Havoc_Rate", True)],
                       ["Opp_Def_Havoc", "PassingDown_SR"], [False, True]),
        "LineYards_Push": ("Offense_With_Push", [("Off_LineYards", "Off_LineYards", False),
                                                ("Opp_Def_LineYards", "Def_LineYards", True)],
                           ["Off_LineYards", "Opp_Def_LineYards"], [False, False]),
        "Explosiveness_Fraud": ("Offense_Flagged", [("Explosiveness", "Off_Explosiveness", False),
                                                    ("Off_SuccessRate", "Off_SuccessRate", False),
                                                    ("Opp_Def_SuccessRate", "Def_SuccessRate", True)],
                                ["Explosiveness", "Off_SuccessRate"], [False, True]),
        "OAY_DAY_Edge": ("Offense_With_Edge", [("OAY", "OAY", False), ("Opp_DAY", "DAY", True)],
                         ["OAY", "Opp_DAY"], [False, False]),
    }
    offense_label, metrics, sort_fields, ascending = specs[signal]
    rows = []
    for _, row in master.iterrows():
        for side, opponent in [("Away", "Home"), ("Home", "Away")]:
            if row[f"{side}_{signal}"]:
                rows.append({"Game": f"{row['Away_Team']} at {row['Home_Team']}",
                             offense_label: row[f"{side}_Team"], **{
                                 label: row[f"{opponent if opposing else side}_{field}"]
                                 for label, field, opposing in metrics}})
    result = pd.DataFrame(rows)
    return result.sort_values(sort_fields, ascending=ascending) if len(result) else result


def build_module3_board(master):
    """OLD CELL 31 descriptive signal counts, not directional support counts."""
    rows = []
    for _, row in master.iterrows():
        away = [label for signal, label in SIGNAL_LABELS.items() if row[f"Away_{signal}"]]
        home = [label for signal, label in SIGNAL_LABELS.items() if row[f"Home_{signal}"]]
        rows.append({"Game": f"{row['Away_Team']} at {row['Home_Team']}",
                     "Away_Team": row.Away_Team, "Away_Signals": ", ".join(away),
                     "Away_Signal_Count": len(away), "Home_Team": row.Home_Team,
                     "Home_Signals": ", ".join(home), "Home_Signal_Count": len(home),
                     "Total_Module3_Signals": len(away) + len(home)})
    result = pd.DataFrame(rows)
    required = ["Game", "Away_Team", "Home_Team", "Away_Signal_Count", "Home_Signal_Count", "Total_Module3_Signals"]
    if (len(result) != len(master) or result.duplicated(subset=["Game"], keep=False).sum()
            or result[required].isna().any(axis=1).sum()
            or (result.Total_Module3_Signals != result.Away_Signal_Count + result.Home_Signal_Count).sum()):
        raise ValueError("Module 3 Signal Board validation failed")
    return result
