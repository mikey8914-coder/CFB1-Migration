"""OLD CELL 44 decision classifications only; no probability, pricing or ROI."""

from dataclasses import dataclass

import pandas as pd

from cfb1.market_audit import AuditBatch


def build_final_decisions(review, routes, audit):
    'OLD CELL 44 strict complete-input final board with original decision precedence.'
    df_phase1_review = review.copy()
    df_final_routes = routes.copy()
    covers_audit = audit.copy()
    df_final_decision = df_phase1_review[['Game', 'Model_Side', 'Review_Class', 'Phase1_Reason']].merge(df_final_routes[['Game', 'M3_Support', 'M3_Conflict', 'Favorite_Spread_Size', 'Spread_Status', 'Eligible_Market_Routes']], on='Game', how='left', validate='one_to_one').merge(covers_audit[['Game', 'Open_Home_Spread', 'Current_Home_Spread', 'Movement_Toward', 'Movement_Size', 'Movement_Class', 'Key_Numbers_Crossed', 'Key_Cross', 'Market_Relationship']], on='Game', how='left', validate='one_to_one')

    def final_decision_status(row):
        relationship = row['Market_Relationship']
        review_class = row['Review_Class']
        spread_status = row['Spread_Status']
        movement_class = row['Movement_Class']
        key_cross = row['Key_Cross']
        if review_class == 'CONFLICT_REVIEW':
            if relationship == 'CONFIRMS_MODEL':
                return 'CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL'
            elif relationship == 'CONFLICTS_WITH_MODEL':
                return 'CONFLICT_REVIEW_MARKET_REJECTS_MODEL'
            else:
                return 'CONFLICT_REVIEW_UNRESOLVED'
        if relationship == 'CONFLICTS_WITH_MODEL':
            if movement_class == 'MAJOR' or key_cross:
                return 'STRONG_MARKET_CONFLICT'
            return 'MARKET_CONFLICT'
        if relationship == 'NEUTRAL':
            return 'NEUTRAL_MARKET'
        if relationship == 'CONFIRMS_MODEL':
            if spread_status in ['LARGE_SPREAD_CAUTION', 'DERIVATIVES_FIRST_20.5_PLUS']:
                return 'CONFIRMED_BUT_LARGE_SPREAD'
            return 'CONFIRMED'
        return 'UNCLASSIFIED'
    df_final_decision['Decision_Status'] = df_final_decision.apply(final_decision_status, axis=1)

    def decision_note(row):
        status = row['Decision_Status']
        notes = {'CONFIRMED': 'Market movement supports the model side.', 'CONFIRMED_BUT_LARGE_SPREAD': 'Market supports the model side, but spread size requires derivative review.', 'NEUTRAL_MARKET': 'Market movement provides no additional confirmation or conflict.', 'MARKET_CONFLICT': 'Market movement is against the model side.', 'STRONG_MARKET_CONFLICT': 'Major and/or key-number movement is against the model side.', 'CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL': 'Module 3 conflicted with the model, but late market movement supports the model side.', 'CONFLICT_REVIEW_MARKET_REJECTS_MODEL': 'Module 3 conflicted with the model and the late market also moved against the model side.', 'CONFLICT_REVIEW_UNRESOLVED': 'Module 3 conflicts with the model and the market did not resolve the disagreement.'}
        return notes.get(status, 'Requires manual review.')
    df_final_decision['Decision_Note'] = df_final_decision.apply(decision_note, axis=1)
    expected_games = len(df_phase1_review)
    duplicate_games = int(df_final_decision.duplicated(subset=['Game'], keep=False).sum())
    missing_required = int(df_final_decision[['Game', 'Model_Side', 'Review_Class', 'Phase1_Reason', 'Favorite_Spread_Size', 'Spread_Status', 'Open_Home_Spread', 'Current_Home_Spread', 'Movement_Toward', 'Movement_Size', 'Movement_Class', 'Market_Relationship', 'Decision_Status', 'Decision_Note']].isna().any(axis=1).sum())
    unclassified_games = int((df_final_decision['Decision_Status'] == 'UNCLASSIFIED').sum())
    if len(df_final_decision) == expected_games and duplicate_games == 0 and (missing_required == 0) and (unclassified_games == 0):
        pass
    else:
        raise ValueError('Final Decision Board validation failed.')
    return df_final_decision


@dataclass
class DecisionBatch:
    """Classified subset and retained candidates lacking usable movement evidence."""

    decisions: pd.DataFrame
    pending_audit: pd.DataFrame


def build_available_final_decisions(review, routes, audit_batch: AuditBatch):
    """Partition availability before strict OLD CELL 44; never invent a decision.

    AUDIT_UNAVAILABLE is an adapter readiness label, not a legacy Decision_Status.
    Pending rows retain Phase 1 fields and current-market readiness unchanged.
    """
    availability = audit_batch.availability
    if (review.Game.duplicated().any() or availability.Game.duplicated().any()
            or set(review.Game) != set(availability.Game)):
        raise ValueError("Audit availability must cover each Phase 1 candidate exactly once")
    ready_games = set(availability.loc[availability.Audit_Ready, "Game"])
    if audit_batch.audit.Game.duplicated().any() or set(audit_batch.audit.Game) != ready_games:
        raise ValueError("Audit rows and readiness partition disagree")
    selected = review[review.Game.isin(ready_games)].copy()
    decisions = build_final_decisions(selected, routes, audit_batch.audit) if len(selected) else pd.DataFrame()
    pending = review[~review.Game.isin(ready_games)].merge(
        availability, on="Game", how="left", validate="one_to_one")
    return DecisionBatch(decisions, pending)
