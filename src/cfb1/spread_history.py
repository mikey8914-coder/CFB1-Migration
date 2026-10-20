"""CELL 51 normalization of supplied historical CFBD line/score payloads.

No HTTP, sportsbook price acquisition, Odds API, or automatic history refresh.
"""

import pandas as pd

HISTORICAL_YEARS = [2021, 2022, 2023, 2024, 2025]
PROVIDER_PRIORITY = ["DraftKings", "ESPN Bet", "Bovada"]


def build_spread_history(yearly_games):
    """Retain the notebook's completed regular-season FBS/FBS calibration rows.

    Supply a mapping containing each fixed year's regular-season /lines array.
    Payload vintage, regular-season query scope, and provenance are the caller's
    responsibility. Missing years fail; source duplicates are not deduplicated.
    """
    if any(year not in yearly_games for year in HISTORICAL_YEARS):
        raise ValueError("Supply all regular-season historical years 2021 through 2025")
    rows = []
    for year in HISTORICAL_YEARS:
        for game in yearly_games[year]:
            if (str(game.get("homeClassification", "")).lower() != "fbs"
                    or str(game.get("awayClassification", "")).lower() != "fbs"):
                continue
            home_score, away_score = game.get("homeScore"), game.get("awayScore")
            if home_score is None or away_score is None:
                continue
            selected = None
            for provider in PROVIDER_PRIORITY:
                for line in game.get("lines", []):
                    if line.get("provider") == provider and line.get("spread") is not None:
                        selected = line
                        break
                if selected is not None:
                    break
            if selected is None:
                continue
            spread = selected.get("spread")
            actual = home_score - away_score
            expected = -spread
            error = actual - expected
            ats = "HOME_COVER" if error > 0 else ("AWAY_COVER" if error < 0 else "PUSH")
            rows.append({"Season": year, "Week": game.get("week"), "Game_ID": game.get("id"),
                         "Away_Team": game.get("awayTeam"), "Home_Team": game.get("homeTeam"),
                         "Away_Score": away_score, "Home_Score": home_score,
                         "Provider": selected.get("provider"), "Closing_Home_Spread": spread,
                         "Actual_Home_Margin": actual, "Market_Expected_Home_Margin": expected,
                         "Spread_Error": error, "ATS_Result": ats})
    return pd.DataFrame(rows)
