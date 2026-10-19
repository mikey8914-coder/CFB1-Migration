"""OLD CELL 43 deterministic movement audit, separate from Covers acquisition."""

from dataclasses import dataclass

import pandas as pd

from cfb1.covers_bridge import audit_ready, production_ready


def audit_spread_movement(covers_csv, review):
    'OLD CELL 43 strict full-review coverage. Openers must be supplied separately.'
    df_phase1_review = review.copy()
    from io import StringIO
    df_covers = pd.read_csv(StringIO(covers_csv.strip()), skipinitialspace=True)
    for col in df_covers.select_dtypes(include='object').columns:
        df_covers[col] = df_covers[col].astype(str).str.strip()
    spread_cols = ['Open_Home_Spread', 'Current_Home_Spread']
    for col in spread_cols:
        df_covers[col] = pd.to_numeric(df_covers[col], errors='coerce')
    expected_games = set(df_phase1_review['Game'])
    covers_games = set(df_covers['Game'])
    missing_games = sorted(expected_games - covers_games)
    extra_games = sorted(covers_games - expected_games)
    duplicate_games = int(df_covers.duplicated(subset=['Game'], keep=False).sum())
    missing_spread_data = int(df_covers[['Open_Home_Spread', 'Current_Home_Spread']].isna().any(axis=1).sum())
    if len(df_covers) == len(expected_games) and len(missing_games) == 0 and (len(extra_games) == 0) and (duplicate_games == 0) and (missing_spread_data == 0):
        pass
    else:
        raise ValueError('Current-week Covers data must be completed before the market audit can run.')
    covers_audit = df_covers.merge(df_phase1_review[['Game', 'Model_Side', 'Review_Class']], on='Game', how='left', validate='one_to_one')
    covers_audit['Spread_Move'] = (covers_audit['Current_Home_Spread'] - covers_audit['Open_Home_Spread']).round(2)

    def movement_side(row):
        move = row['Spread_Move']
        if move < 0:
            return row['Home_Team']
        elif move > 0:
            return row['Away_Team']
        return 'NONE'
    covers_audit['Movement_Toward'] = covers_audit.apply(movement_side, axis=1)

    def market_relationship(row):
        if row['Movement_Toward'] == 'NONE':
            return 'NEUTRAL'
        if row['Movement_Toward'] == row['Model_Side']:
            return 'CONFIRMS_MODEL'
        return 'CONFLICTS_WITH_MODEL'
    covers_audit['Market_Relationship'] = covers_audit.apply(market_relationship, axis=1)
    SIGNED_KEY_NUMBERS = [-14, -10, -7, -3, 3, 7, 10, 14]

    def crossed_keys(row):
        opening = row['Open_Home_Spread']
        current = row['Current_Home_Spread']
        low = min(opening, current)
        high = max(opening, current)
        crossed = []
        for key in SIGNED_KEY_NUMBERS:
            if low < key < high:
                crossed.append(abs(key))
        return ','.join((str(key) for key in sorted(set(crossed))))
    covers_audit['Key_Numbers_Crossed'] = covers_audit.apply(crossed_keys, axis=1)
    covers_audit['Key_Cross'] = covers_audit['Key_Numbers_Crossed'] != ''
    covers_audit['Movement_Size'] = covers_audit['Spread_Move'].abs()

    def movement_class(size):
        if size == 0:
            return 'NO_MOVE'
        elif size < 1:
            return 'SMALL'
        elif size < 2:
            return 'MODERATE'
        return 'MAJOR'
    covers_audit['Movement_Class'] = covers_audit['Movement_Size'].apply(movement_class)
    audit_missing = int(covers_audit[['Model_Side', 'Review_Class', 'Spread_Move', 'Movement_Toward', 'Market_Relationship', 'Movement_Size', 'Movement_Class']].isna().any(axis=1).sum())
    if len(covers_audit) == len(df_phase1_review) and audit_missing == 0:
        pass
    else:
        raise ValueError('Covers market audit validation failed.')
    return covers_audit


@dataclass
class AuditBatch:
    """Legacy audit rows plus explicit readiness for EVERY Phase 1 candidate."""

    audit: pd.DataFrame
    availability: pd.DataFrame


def prepare_market_audit(review, market_keys, current_records, movement_audits):
    """Adapt verified current records and independently verified same-book pairs.

    market_keys associates Phase 1 raw Game/team labels with official game_id
    and canonical Away_CFBD_Name/Home_CFBD_Name from the upstream master.
    movement_audits maps official game IDs to the committed bridge's optional
    movement_audit shape. No opener is inferred, fetched, or read from HTML.
    """
    required = ["Game", "Away_Team", "Home_Team", "game_id", "Away_CFBD_Name", "Home_CFBD_Name"]
    if any(c not in market_keys for c in required):
        raise ValueError("Audit adapter requires official master game keys")
    if review.Game.duplicated().any() or market_keys.Game.duplicated().any() or market_keys.game_id.duplicated().any():
        raise ValueError("Ambiguous Phase 1 or official master game keys")
    keys = review[["Game"]].merge(market_keys[required], on="Game", how="left", validate="one_to_one")
    if keys[required].isna().any().any():
        raise ValueError("Missing official master keys for a Phase 1 candidate")
    records_by_id = {}
    for record in current_records:
        records_by_id.setdefault(record.get("game_id"), []).append(record)
    rows, status = [], []
    for key in keys.to_dict(orient="records"):
        records = records_by_id.get(key["game_id"], [])
        reason = ""
        current_ok = False
        if len(records) != 1:
            reason = "CURRENT_RECORD_MISSING_OR_AMBIGUOUS"
        else:
            record = records[0]
            current_ok = production_ready(record)
            if not current_ok:
                reason = "CURRENT_MARKET_NOT_PRODUCTION_READY"
            elif (record.get("away_team"), record.get("home_team")) != (key["Away_CFBD_Name"], key["Home_CFBD_Name"]):
                reason = "OFFICIAL_TEAM_ORIENTATION_MISMATCH"
            else:
                proof = movement_audits.get(key["game_id"])
                if not proof or not proof.get("opening"):
                    reason = "OPENER_UNAVAILABLE"
                elif not audit_ready({**record, "movement_audit": proof}):
                    reason = "MOVEMENT_PAIR_NOT_VERIFIED"
                else:
                    prefix = {"DraftKings": "DK", "FanDuel": "FD"}[proof["current"]["book"]]
                    if proof["current"]["home_spread"] != record.get(prefix + "_Spread"):
                        reason = "AUDIT_CURRENT_POINT_MISMATCH"
                    else:
                        rows.append({"Game": key["Game"], "Away_Team": key["Away_Team"],
                                     "Home_Team": key["Home_Team"],
                                     "Open_Home_Spread": proof["opening"]["home_spread"],
                                     "Current_Home_Spread": proof["current"]["home_spread"],
                                     "Source": proof["current"]["source"],
                                     "Book": proof["current"]["book"], "game_id": key["game_id"],
                                     "Opening_Definition": proof["opening"]["definition"],
                                     "Opening_Retrieved_At": proof["opening"]["retrieved_at"],
                                     "Current_Retrieved_At": proof["current"]["retrieved_at"]})
        status.append({"Game": key["Game"], "Current_Market_Ready": current_ok,
                       "Audit_Ready": not bool(reason),
                       "Audit_Status": "AUDIT_READY" if not reason else "AUDIT_UNAVAILABLE",
                       "Audit_Reason": reason})
    availability = pd.DataFrame(status, columns=["Game", "Current_Market_Ready", "Audit_Ready", "Audit_Status", "Audit_Reason"])
    ready_games = set(availability.loc[availability.Audit_Ready, "Game"])
    if rows:
        selected_review = review[review.Game.isin(ready_games)].copy()
        # Reuse the legacy numeric/text normalization and formulas, not a new parser.
        audit = audit_spread_movement(pd.DataFrame(rows).to_csv(index=False), selected_review)
    else:
        audit = pd.DataFrame(columns=["Game"])
    return AuditBatch(audit, availability)
