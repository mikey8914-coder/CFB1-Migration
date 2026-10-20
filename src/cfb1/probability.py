"""Frozen CELL 47/48/52/57/57A spread calculations; no acquisition or economics."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class RetainedLines:
    full_slate: pd.DataFrame
    phase1: pd.DataFrame
    beta: float
    intercept: float


def fit_retained_lines(master, review):
    'CELL 47: fit full-slate EPA points, blend equally with FEI, preserve all retentions.'
    df_master_bcf = master.copy()
    df_phase1_review = review.copy()
    import numpy as np
    import pandas as pd
    required_cols = ['Home_Team', 'Away_Team', 'Net_EPA_Edge_Home', 'FEI_Model_Home_Spread', 'DK_Spread', 'FD_Spread']
    missing_cols = [col for col in required_cols if col not in df_master_bcf.columns]
    if missing_cols:
        raise ValueError(f'Cell 47 missing required columns: {missing_cols}')
    df_prob_model = df_master_bcf.copy()
    df_prob_model['Consensus_Home_Spread'] = df_prob_model[['DK_Spread', 'FD_Spread']].mean(axis=1)
    df_prob_model['Market_Home_Margin'] = -df_prob_model['Consensus_Home_Spread']
    epa_x = df_prob_model['Net_EPA_Edge_Home'].astype(float)
    market_y = df_prob_model['Market_Home_Margin'].astype(float)
    valid_mask = epa_x.notna() & market_y.notna()
    x = epa_x[valid_mask].values
    y = market_y[valid_mask].values
    beta, intercept = np.polyfit(x, y, 1)
    df_prob_model['EPA_Model_Home_Margin'] = intercept + beta * df_prob_model['Net_EPA_Edge_Home']
    df_prob_model['EPA_Model_Home_Spread'] = -df_prob_model['EPA_Model_Home_Margin']
    df_prob_model['FEI_Model_Home_Margin'] = -df_prob_model['FEI_Model_Home_Spread']
    EPA_WEIGHT = 0.5
    FEI_WEIGHT = 0.5
    df_prob_model['Blended_Home_Margin_Raw'] = EPA_WEIGHT * df_prob_model['EPA_Model_Home_Margin'] + FEI_WEIGHT * df_prob_model['FEI_Model_Home_Margin']
    df_prob_model['Blended_Home_Spread_Raw'] = -df_prob_model['Blended_Home_Margin_Raw']
    df_prob_model['Blended_Edge_Home_Raw'] = df_prob_model['Consensus_Home_Spread'] - df_prob_model['Blended_Home_Spread_Raw']
    RETENTION_LEVELS = [0.25, 0.4, 0.5, 0.6]
    for retention in RETENTION_LEVELS:
        label = int(retention * 100)
        df_prob_model[f'Edge_Retained_{label}'] = df_prob_model['Blended_Edge_Home_Raw'] * retention
        df_prob_model[f'Shrunk_Home_Spread_{label}'] = df_prob_model['Consensus_Home_Spread'] - df_prob_model[f'Edge_Retained_{label}']
    if 'df_phase1_review' in locals():
        df_prob_model = df_prob_model.merge(df_phase1_review[['Game', 'Model_Side', 'Review_Class']], left_on=df_prob_model['Away_Team'] + ' at ' + df_prob_model['Home_Team'], right_on='Game', how='left')
    else:
        df_prob_model['Game'] = df_prob_model['Away_Team'] + ' at ' + df_prob_model['Home_Team']
        df_prob_model['Model_Side'] = ''
        df_prob_model['Review_Class'] = ''
    df_phase1_shrinkage = df_prob_model[df_prob_model['Game'].isin(set(df_phase1_review['Game']))].copy()
    df_phase1_shrinkage['Raw_Edge_Size'] = df_phase1_shrinkage['Blended_Edge_Home_Raw'].abs()
    return RetainedLines(df_prob_model, df_phase1_shrinkage, float(beta), float(intercept))


def model_side_line_value(phase1_shrinkage, final_decisions):
    'CELL 48: 40% retained line and late-current line, oriented to model side.'
    df_phase1_shrinkage = phase1_shrinkage.copy()
    df_final_decision = final_decisions.copy()
    import numpy as np
    import pandas as pd
    MODEL_EDGE_RETENTION = 0.4
    if 'df_phase1_shrinkage' not in locals():
        raise NameError('df_phase1_shrinkage does not exist. Run Cell 47 first.')
    if 'df_final_decision' not in locals():
        raise NameError('df_final_decision does not exist. Run through Cell 44 first.')
    df_key_value = df_phase1_shrinkage[['Game', 'Model_Side', 'Home_Team', 'Away_Team', 'Shrunk_Home_Spread_40']].copy()
    df_key_value = df_key_value.merge(df_final_decision[['Game', 'Current_Home_Spread', 'Decision_Status', 'Eligible_Market_Routes']], on='Game', how='left', validate='one_to_one')

    def model_side_market_spread(row):
        if row['Model_Side'] == row['Home_Team']:
            return row['Current_Home_Spread']
        elif row['Model_Side'] == row['Away_Team']:
            return -row['Current_Home_Spread']
        else:
            return np.nan

    def model_side_retained_spread(row):
        if row['Model_Side'] == row['Home_Team']:
            return row['Shrunk_Home_Spread_40']
        elif row['Model_Side'] == row['Away_Team']:
            return -row['Shrunk_Home_Spread_40']
        else:
            return np.nan
    df_key_value['Market_Model_Spread'] = df_key_value.apply(model_side_market_spread, axis=1)
    df_key_value['Retained_Model_Spread'] = df_key_value.apply(model_side_retained_spread, axis=1)
    df_key_value['Model_Cushion_Points'] = (df_key_value['Market_Model_Spread'] - df_key_value['Retained_Model_Spread']).round(2)
    SIGNED_KEY_NUMBERS = [-14, -10, -7, -3, 3, 7, 10, 14]

    def keys_between_market_and_model(row):
        market = row['Market_Model_Spread']
        model = row['Retained_Model_Spread']
        if pd.isna(market) or pd.isna(model):
            return ''
        low = min(market, model)
        high = max(market, model)
        keys = []
        for key in SIGNED_KEY_NUMBERS:
            if low < key < high:
                keys.append(abs(key))
        return ','.join((str(k) for k in sorted(set(keys))))
    df_key_value['Keys_Between_Market_And_Model'] = df_key_value.apply(keys_between_market_and_model, axis=1)
    df_key_value['Key_Barrier_Present'] = df_key_value['Keys_Between_Market_And_Model'] != ''
    KEY_MAGNITUDES = [3, 7, 10, 14]

    def next_adverse_key(row):
        spread = row['Market_Model_Spread']
        if pd.isna(spread):
            return np.nan
        if spread >= 0:
            return np.nan
        magnitude = abs(spread)
        for key in KEY_MAGNITUDES:
            if key > magnitude:
                return key
        return np.nan
    df_key_value['Next_Adverse_Key'] = df_key_value.apply(next_adverse_key, axis=1)

    def line_value_status(row):
        cushion = row['Model_Cushion_Points']
        if pd.isna(cushion):
            return 'CHECK'
        if cushion <= 0:
            return 'NO_RETAINED_MODEL_EDGE'
        if row['Key_Barrier_Present']:
            return 'EDGE_WITH_KEY_BARRIER'
        return 'EDGE_NO_KEY_BARRIER'
    df_key_value['Line_Value_Status'] = df_key_value.apply(line_value_status, axis=1)

    def tradeoff_note(row):
        status = row['Line_Value_Status']
        keys = row['Keys_Between_Market_And_Model']
        if status == 'NO_RETAINED_MODEL_EDGE':
            return 'Retained model does not show a positive line cushion.'
        if status == 'EDGE_WITH_KEY_BARRIER':
            return f'Model shows line value, but key number(s) {keys} lie between market and retained model line. Do not trade through a key solely for better juice without explicit price-value analysis.'
        if status == 'EDGE_NO_KEY_BARRIER':
            return 'Retained model shows line cushion with no listed key number between market and model.'
        return 'Requires review.'
    df_key_value['Key_Tradeoff_Note'] = df_key_value.apply(tradeoff_note, axis=1)
    return df_key_value


def spread_bucket(spread_abs):
    if spread_abs < 3:
        return 'UNDER_3'
    elif spread_abs < 7:
        return '3_TO_6.5'
    elif spread_abs < 10:
        return '7_TO_9.5'
    elif spread_abs < 14:
        return '10_TO_13.5'
    elif spread_abs < 17:
        return '14_TO_16.5'
    elif spread_abs < 21:
        return '17_TO_20.5'
    else:
        return '21_PLUS'

def empirical_probability(cushion, model_is_home, errors):
    if pd.isna(cushion):
        return (np.nan, np.nan, np.nan)
    oriented = errors if model_is_home else -errors
    adjusted = oriented + cushion
    win_prob = (adjusted > 0).mean()
    push_prob = (adjusted == 0).mean()
    loss_prob = (adjusted < 0).mean()
    return (win_prob, push_prob, loss_prob)


def cover_probability_board(history, key_value):
    'CELL 52: empirical global/bucket diagnostics, minimum cover probability only.'
    df_hist_spread = history.copy()
    df_key_value = key_value.copy()
    import numpy as np
    import pandas as pd
    if 'df_hist_spread' not in locals():
        raise NameError('df_hist_spread does not exist. Run Cell 51 first.')
    if 'df_key_value' not in locals():
        raise NameError('df_key_value does not exist. Run Cell 48 first.')
    hist_errors = df_hist_spread['Spread_Error'].dropna().astype(float)

    def spread_bucket(spread_abs):
        if spread_abs < 3:
            return 'UNDER_3'
        elif spread_abs < 7:
            return '3_TO_6.5'
        elif spread_abs < 10:
            return '7_TO_9.5'
        elif spread_abs < 14:
            return '10_TO_13.5'
        elif spread_abs < 17:
            return '14_TO_16.5'
        elif spread_abs < 21:
            return '17_TO_20.5'
        else:
            return '21_PLUS'
    df_hist_spread['Spread_Bucket'] = df_hist_spread['Closing_Home_Spread'].abs().apply(spread_bucket)

    def empirical_probability(cushion, model_is_home, errors):
        if pd.isna(cushion):
            return (np.nan, np.nan, np.nan)
        oriented = errors if model_is_home else -errors
        adjusted = oriented + cushion
        win_prob = (adjusted > 0).mean()
        push_prob = (adjusted == 0).mean()
        loss_prob = (adjusted < 0).mean()
        return (win_prob, push_prob, loss_prob)
    prob_rows = []
    for _, row in df_key_value.iterrows():
        game = row['Game']
        model_side = row['Model_Side']
        home_team = row['Home_Team']
        away_team = row['Away_Team']
        market_spread = row['Market_Model_Spread']
        cushion = row['Model_Cushion_Points']
        model_is_home = model_side == home_team
        global_win, global_push, global_loss = empirical_probability(cushion, model_is_home, hist_errors)
        bucket = spread_bucket(abs(market_spread))
        bucket_errors = df_hist_spread.loc[df_hist_spread['Spread_Bucket'] == bucket, 'Spread_Error'].dropna().astype(float)
        local_win, local_push, local_loss = empirical_probability(cushion, model_is_home, bucket_errors)
        prob_rows.append({'Game': game, 'Model_Side': model_side, 'Market_Model_Spread': market_spread, 'Retained_Model_Spread': row['Retained_Model_Spread'], 'Model_Cushion_Points': cushion, 'Spread_Bucket': bucket, 'Historical_Bucket_N': len(bucket_errors), 'Global_Cover_Prob': global_win, 'Global_Push_Prob': global_push, 'Global_Loss_Prob': global_loss, 'Bucket_Cover_Prob': local_win, 'Bucket_Push_Prob': local_push, 'Bucket_Loss_Prob': local_loss, 'Line_Value_Status': row['Line_Value_Status'], 'Decision_Status': row['Decision_Status']})
    df_cover_prob = pd.DataFrame(prob_rows)
    df_cover_prob['CFB1_Cover_Prob_V1'] = df_cover_prob[['Global_Cover_Prob', 'Bucket_Cover_Prob']].min(axis=1)
    display_df = df_cover_prob.copy()
    prob_cols = ['Global_Cover_Prob', 'Global_Push_Prob', 'Bucket_Cover_Prob', 'Bucket_Push_Prob', 'CFB1_Cover_Prob_V1']
    for col in prob_cols:
        display_df[col] = (display_df[col] * 100).round(1)
    return (df_hist_spread, df_cover_prob)


def candidate_probabilities(candidates, history):
    'CELL 57: entire GLOBAL or SPREAD_BUCKET triplet; bucket requires supplied N>=300.'
    df_ev = candidates.copy()
    df_hist_spread = history.copy()
    global_errors = df_hist_spread['Spread_Error'].dropna().astype(float)
    def _model_side_is_home(row):
        if 'Home_Team' not in row.index:
            raise KeyError('Home_Team missing from df_spread_shortlist.')
        return str(row['Team']) == str(row['Home_Team'])

    def _probability_triplet(cushion, model_is_home, errors):
        if pd.isna(cushion):
            return (np.nan, np.nan, np.nan)
        oriented = errors.astype(float) if model_is_home else -errors.astype(float)
        adjusted = oriented + float(cushion)
        win_prob = (adjusted > 0).mean()
        push_prob = (adjusted == 0).mean()
        loss_prob = (adjusted < 0).mean()
        return (float(win_prob), float(push_prob), float(loss_prob))
    global_wins = []
    global_pushes = []
    global_losses = []
    bucket_wins = []
    bucket_pushes = []
    bucket_losses = []
    probability_sources = []
    for _, row in df_ev.iterrows():
        cushion = row['Candidate_Cushion']
        model_is_home = _model_side_is_home(row)
        gw, gp, gl = _probability_triplet(cushion, model_is_home, global_errors)
        global_wins.append(gw)
        global_pushes.append(gp)
        global_losses.append(gl)
        bucket_series = None
        if 'Spread_Bucket' in row.index and pd.notna(row['Spread_Bucket']) and ('df_hist_spread' in locals()) and ('Spread_Bucket' in df_hist_spread.columns):
            bucket_series = df_hist_spread.loc[df_hist_spread['Spread_Bucket'] == row['Spread_Bucket'], 'Spread_Error'] if 'Spread_Error' in df_hist_spread.columns else None
        if bucket_series is not None and len(bucket_series) > 0:
            bw, bp, bl = _probability_triplet(cushion, model_is_home, bucket_series)
        else:
            bw, bp, bl = (gw, gp, gl)
        bucket_wins.append(bw)
        bucket_pushes.append(bp)
        bucket_losses.append(bl)
        historical_n = row['Historical_Bucket_N'] if 'Historical_Bucket_N' in row.index else np.nan
        if pd.notna(historical_n) and float(historical_n) >= 300 and (bucket_series is not None) and (len(bucket_series) > 0):
            probability_sources.append('SPREAD_BUCKET')
        else:
            probability_sources.append('GLOBAL')
    df_ev['Global_Win_Prob'] = global_wins
    df_ev['Global_Push_Prob'] = global_pushes
    df_ev['Global_Loss_Prob'] = global_losses
    df_ev['Bucket_Win_Prob'] = bucket_wins
    df_ev['Bucket_Push_Prob'] = bucket_pushes
    df_ev['Bucket_Loss_Prob'] = bucket_losses
    df_ev['Probability_Source'] = probability_sources
    df_ev['CFB1_Win_Prob'] = np.where(df_ev['Probability_Source'] == 'SPREAD_BUCKET', df_ev['Bucket_Win_Prob'], df_ev['Global_Win_Prob'])
    df_ev['CFB1_Push_Prob'] = np.where(df_ev['Probability_Source'] == 'SPREAD_BUCKET', df_ev['Bucket_Push_Prob'], df_ev['Global_Push_Prob'])
    df_ev['CFB1_Loss_Prob'] = np.where(df_ev['Probability_Source'] == 'SPREAD_BUCKET', df_ev['Bucket_Loss_Prob'], df_ev['Global_Loss_Prob'])
    df_ev['CFB1_Cover_Prob'] = df_ev['CFB1_Win_Prob']
    prob_sum = df_ev['CFB1_Win_Prob'] + df_ev['CFB1_Push_Prob'] + df_ev['CFB1_Loss_Prob']
    if (~np.isclose(prob_sum, 1.0, atol=1e-09)).sum() != 0:
        raise ValueError('Probability validation failed.')
    return df_ev


def adjust_push_probabilities(valued_candidates, history):
    'CELL 57A: preserve literal absolute-line target orientation and redistribute nonpush mass.'
    df_ev = valued_candidates.copy()
    df_hist_spread = history.copy()
    import numpy as np
    import pandas as pd
    required_objects = ['df_ev', 'df_hist_spread']
    for obj in required_objects:
        if obj not in locals():
            raise NameError(f'{obj} missing. Run the earlier CFB1 cells first.')
    PUSH_WINDOW = 1.0

    def is_integer_line(value):
        if pd.isna(value):
            return False
        return float(value).is_integer()

    def estimate_push_probability(candidate_line, model_side_is_home):
        if not is_integer_line(candidate_line):
            return (0.0, 0)
        target_margin = abs(int(round(float(candidate_line))))
        if 'Closing_Home_Spread' not in df_hist_spread.columns:
            raise KeyError('df_hist_spread is missing Closing_Home_Spread.')
        if 'Actual_Home_Margin' not in df_hist_spread.columns:
            raise KeyError('df_hist_spread is missing Actual_Home_Margin.')
        spread_mag = df_hist_spread['Closing_Home_Spread'].astype(float).abs()
        comparable = df_hist_spread[(spread_mag >= target_margin - PUSH_WINDOW) & (spread_mag <= target_margin + PUSH_WINDOW)].copy()
        if len(comparable) == 0:
            return (0.0, 0)
        if model_side_is_home:
            pushes = (comparable['Actual_Home_Margin'] == target_margin).sum()
        else:
            pushes = (comparable['Actual_Home_Margin'] == -target_margin).sum()
        push_prob = pushes / len(comparable)
        return (float(push_prob), int(len(comparable)))

    def model_side_is_home(row):
        return str(row['Team']) == str(row['Home_Team'])
    historical_push_probs = []
    historical_push_ns = []
    for _, row in df_ev.iterrows():
        push_prob, push_n = estimate_push_probability(row['Line'], model_side_is_home(row))
        historical_push_probs.append(push_prob)
        historical_push_ns.append(push_n)
    df_ev['Historical_Push_Prob'] = historical_push_probs
    df_ev['Historical_Push_N'] = historical_push_ns
    base_nonpush = df_ev['CFB1_Win_Prob'] + df_ev['CFB1_Loss_Prob']
    win_share = np.where(base_nonpush > 0, df_ev['CFB1_Win_Prob'] / base_nonpush, np.nan)
    loss_share = np.where(base_nonpush > 0, df_ev['CFB1_Loss_Prob'] / base_nonpush, np.nan)
    remaining_nonpush = 1.0 - df_ev['Historical_Push_Prob']
    df_ev['Push_Adjusted_Win_Prob'] = win_share * remaining_nonpush
    df_ev['Push_Adjusted_Push_Prob'] = df_ev['Historical_Push_Prob']
    df_ev['Push_Adjusted_Loss_Prob'] = loss_share * remaining_nonpush
    prob_sum = df_ev['Push_Adjusted_Win_Prob'] + df_ev['Push_Adjusted_Push_Prob'] + df_ev['Push_Adjusted_Loss_Prob']
    if (~np.isclose(prob_sum, 1.0, atol=1e-09)).sum() != 0:
        raise ValueError('Push-adjusted probability validation failed.')
    return df_ev
