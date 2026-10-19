"""OLD CELL 41/42 Phase 1 shortlist/review; no Covers audit or final decision."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class Phase1Tables:
    master: pd.DataFrame
    diagnostic: pd.DataFrame
    candidates: pd.DataFrame
    cut_points: dict


def build_phase1_shortlist(master, evidence_routes):
    'OLD CELL 41: full-slate quantiles, agreement universe, ordered shortlist reasons.'
    df_master_bcf = master.copy()
    df_evidence_routes = evidence_routes.copy()
    df_master_bcf['FEI_Edge_Conservative'] = df_master_bcf[['DK_FEI_Edge_Value', 'FD_FEI_Edge_Value']].min(axis=1)
    EPA_75 = df_master_bcf['EPA_Edge_Value'].quantile(0.75)
    EPA_90 = df_master_bcf['EPA_Edge_Value'].quantile(0.9)
    FEI_75 = df_master_bcf['FEI_Edge_Conservative'].quantile(0.75)
    FEI_90 = df_master_bcf['FEI_Edge_Conservative'].quantile(0.9)
    phase1_rows = []
    for _, row in df_master_bcf.iterrows():
        game = f"{row['Away_Team']} at {row['Home_Team']}"
        evidence_match = df_evidence_routes[df_evidence_routes['Game'] == game]
        if len(evidence_match) == 0:
            continue
        evidence_row = evidence_match.iloc[0]
        model_agreement = row['EPA_Edge_Team'] == row['DK_FEI_Edge_Team'] and row['EPA_Edge_Team'] != 'EVEN'
        epa_top25 = row['EPA_Edge_Value'] >= EPA_75
        fei_top25 = row['FEI_Edge_Conservative'] >= FEI_75
        dual_top25 = model_agreement and epa_top25 and fei_top25
        module3_support = evidence_row['Evidence_Class'] == 'MODEL_PLUS_MATCHUP_SUPPORT'
        module3_conflict = evidence_row['Evidence_Class'] == 'MODEL_WITH_MATCHUP_CONFLICT'
        reasons = []
        if module3_support:
            reasons.append('MODULE3_SUPPORT')
        if dual_top25:
            reasons.append('DUAL_TOP25_MODEL_STRENGTH')
        if module3_conflict:
            reasons.append('MODULE3_CONFLICT')
        phase1_candidate = module3_support or dual_top25 or module3_conflict
        phase1_rows.append({'Game': game, 'Model_Side': evidence_row['Model_Side'], 'EPA_Value': row['EPA_Edge_Value'], 'EPA_Top25': epa_top25, 'FEI_Value_Conservative': row['FEI_Edge_Conservative'], 'FEI_Top25': fei_top25, 'Dual_Top25': dual_top25, 'Evidence_Class': evidence_row['Evidence_Class'], 'Candidate_Reason': ', '.join(reasons), 'Phase1_Candidate': phase1_candidate})
    df_phase1_diagnostic = pd.DataFrame(phase1_rows)
    candidate_board = df_phase1_diagnostic[df_phase1_diagnostic['Phase1_Candidate']].copy()
    expected_agreement_games = len(df_evidence_routes)
    duplicate_games = int(df_phase1_diagnostic.duplicated(subset=['Game'], keep=False).sum())
    missing_required = int(df_phase1_diagnostic[['Game', 'Model_Side', 'EPA_Value', 'EPA_Top25', 'FEI_Value_Conservative', 'FEI_Top25', 'Dual_Top25', 'Evidence_Class', 'Phase1_Candidate']].isna().any(axis=1).sum())
    module3_count = int(candidate_board['Candidate_Reason'].str.contains('MODULE3_SUPPORT', regex=False).sum())
    dual_count = int(candidate_board['Candidate_Reason'].str.contains('DUAL_TOP25_MODEL_STRENGTH', regex=False).sum())
    conflict_count = int(candidate_board['Candidate_Reason'].str.contains('MODULE3_CONFLICT', regex=False).sum())
    if len(df_phase1_diagnostic) == expected_agreement_games and duplicate_games == 0 and (missing_required == 0):
        pass
    else:
        raise ValueError('Phase 1 shortlist validation failed.')
    return Phase1Tables(df_master_bcf, df_phase1_diagnostic, candidate_board, {'EPA_75': EPA_75, 'EPA_90': EPA_90, 'FEI_75': FEI_75, 'FEI_90': FEI_90})


def build_phase1_review(candidates):
    'OLD CELL 42: ordered review classes and action label only; no audit acquisition.'
    candidate_board = candidates.copy()
    phase1_final_rows = []
    for _, row in candidate_board.iterrows():
        reasons = row['Candidate_Reason']
        if 'MODULE3_SUPPORT' in reasons and 'DUAL_TOP25_MODEL_STRENGTH' in reasons:
            review_class = 'MODEL_PLUS_MATCHUP'
        elif 'DUAL_TOP25_MODEL_STRENGTH' in reasons:
            review_class = 'STRONG_MODEL_AGREEMENT'
        elif 'MODULE3_SUPPORT' in reasons:
            review_class = 'MATCHUP_SUPPORTED'
        elif 'MODULE3_CONFLICT' in reasons:
            review_class = 'CONFLICT_REVIEW'
        else:
            review_class = 'UNCLASSIFIED'
        phase1_final_rows.append({'Game': row['Game'], 'Model_Side': row['Model_Side'], 'EPA_Value': row['EPA_Value'], 'FEI_Value_Conservative': row['FEI_Value_Conservative'], 'Evidence_Class': row['Evidence_Class'], 'Review_Class': review_class, 'Phase1_Reason': reasons, 'Late_Week_Action': 'COLLECT_COVERS_LINE_MOVEMENT'})
    df_phase1_review = pd.DataFrame(phase1_final_rows)
    expected_games = len(candidate_board)
    duplicate_games = int(df_phase1_review.duplicated(subset=['Game'], keep=False).sum())
    missing_required = int(df_phase1_review[['Game', 'Model_Side', 'EPA_Value', 'FEI_Value_Conservative', 'Evidence_Class', 'Review_Class', 'Phase1_Reason', 'Late_Week_Action']].isna().any(axis=1).sum())
    unclassified_games = int((df_phase1_review['Review_Class'] == 'UNCLASSIFIED').sum())
    if len(df_phase1_review) == expected_games and duplicate_games == 0 and (missing_required == 0) and (unclassified_games == 0):
        pass
    else:
        raise ValueError('Phase 1 Review Board validation failed.')
    return df_phase1_review
