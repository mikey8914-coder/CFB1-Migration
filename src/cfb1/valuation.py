"""Supplied-price CELL 55/57/57A economics. No price/API acquisition or staking."""

import numpy as np
import pandas as pd

from cfb1.probability import candidate_probabilities, adjust_push_probabilities


def profit_multiple(odds):
    odds = float(odds)
    if odds > 0:
        return odds / 100.0
    return 100.0 / abs(odds)


def break_even_prob(odds):
    odds = float(odds)
    if odds < 0:
        return abs(odds) / (abs(odds) + 100.0)
    return 100.0 / (odds + 100.0)


def shortlist_supplied_spreads(offers, key_value, history):
    'CELL 55: filter externally supplied full-game offers; preserve shortlist and warning semantics.'
    df_auto_pricing = offers.copy()
    df_key_value = key_value.copy()
    df_hist_spread = history.copy()
    import numpy as np
    import pandas as pd
    if 'df_auto_pricing' not in locals():
        raise NameError('df_auto_pricing missing. Run Cell 54.')
    if 'df_key_value' not in locals():
        raise NameError('df_key_value missing. Run Cell 48.')
    if 'df_hist_spread' not in locals():
        raise NameError('df_hist_spread missing. Run Cell 51.')
    spread_prices = df_auto_pricing[df_auto_pricing['Market_Type'] == 'FULL_GAME_SPREAD'].copy()
    model_info = df_key_value[['Game', 'Model_Side', 'Market_Model_Spread', 'Retained_Model_Spread', 'Line_Value_Status', 'Decision_Status', 'Eligible_Market_Routes']].copy()
    spread_prices = spread_prices.merge(model_info, on='Game', how='inner')
    spread_prices = spread_prices[spread_prices['Team'] == spread_prices['Model_Side']].copy()
    spread_prices = spread_prices[spread_prices['Eligible_Market_Routes'].astype(str).str.contains('FULL_GAME_SPREAD', case=False, na=False)].copy()
    spread_prices = spread_prices[(spread_prices['American_Odds'] >= -250) & (spread_prices['American_Odds'] <= 300)].copy()
    spread_prices['Candidate_Cushion'] = spread_prices['Line'] - spread_prices['Retained_Model_Spread']
    spread_prices = spread_prices[spread_prices['Candidate_Cushion'] >= -0.5].copy()

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

    def empirical_cover_prob(cushion, errors):
        adjusted = errors.astype(float) + cushion
        return (adjusted > 0).mean()
    global_errors = df_hist_spread['Spread_Error'].dropna().astype(float)
    probabilities = []
    for _, row in spread_prices.iterrows():
        cushion = row['Candidate_Cushion']
        game_row = df_key_value[df_key_value['Game'] == row['Game']].iloc[0]
        model_is_home = row['Model_Side'] == game_row['Home_Team']
        oriented_global = global_errors if model_is_home else -global_errors
        global_prob = empirical_cover_prob(cushion, oriented_global)
        bucket = spread_bucket(abs(row['Line']))
        bucket_errors = df_hist_spread.loc[df_hist_spread['Closing_Home_Spread'].abs().apply(spread_bucket) == bucket, 'Spread_Error'].dropna().astype(float)
        oriented_bucket = bucket_errors if model_is_home else -bucket_errors
        bucket_prob = empirical_cover_prob(cushion, oriented_bucket)
        conservative_prob = min(global_prob, bucket_prob)
        probabilities.append((global_prob, bucket_prob, conservative_prob))
    spread_prices[['Global_Cover_Prob', 'Bucket_Cover_Prob', 'CFB1_Cover_Prob']] = probabilities

    def american_break_even(odds):
        odds = float(odds)
        if odds < 0:
            return abs(odds) / (abs(odds) + 100)
        else:
            return 100 / (odds + 100)
    spread_prices['Break_Even_Prob'] = spread_prices['American_Odds'].apply(american_break_even)
    spread_prices['Probability_Edge'] = spread_prices['CFB1_Cover_Prob'] - spread_prices['Break_Even_Prob']
    KEYS = [3, 7, 10, 14]

    def key_tradeoff(row):
        start = row['Market_Model_Spread']
        candidate = row['Line']
        if pd.isna(start) or pd.isna(candidate):
            return ''
        if start >= 0 or candidate >= 0:
            return ''
        start_mag = abs(start)
        cand_mag = abs(candidate)
        if cand_mag <= start_mag:
            return ''
        for key in KEYS:
            if abs(start_mag - key) < 0.001 and cand_mag > key:
                return f'OFF_KEY_{key}'
        crossed = []
        for key in KEYS:
            if start_mag < key and cand_mag > key:
                crossed.append(str(key))
        if crossed:
            return 'CROSSES_' + '_'.join(crossed)
        for key in KEYS:
            if start_mag < key and abs(cand_mag - key) < 0.001:
                return f'LANDS_ON_KEY_{key}'
        return ''
    spread_prices['Key_Tradeoff'] = spread_prices.apply(key_tradeoff, axis=1)

    def useful_line(row):
        market = row['Market_Model_Spread']
        model = row['Retained_Model_Spread']
        line = row['Line']
        low = min(market, model) - 0.5
        high = max(market, model) + 0.5
        return low <= line <= high
    spread_prices = spread_prices[spread_prices.apply(useful_line, axis=1)].copy()
    spread_prices = spread_prices.sort_values('American_Odds', ascending=False).drop_duplicates(subset=['Game', 'Team', 'Line'], keep='first')
    spread_prices['Abs_From_Main'] = (spread_prices['Line'] - spread_prices['Market_Model_Spread']).abs()

    def choose_shortlist(group):
        near_main = group.sort_values('Abs_From_Main').head(3)
        best_edge = group.sort_values('Probability_Edge', ascending=False).head(3)
        key_rows = group[group['Key_Tradeoff'] != '']
        combined = pd.concat([near_main, best_edge, key_rows])
        return combined.drop_duplicates().sort_values('Line', ascending=False).head(6)
    df_spread_shortlist = spread_prices.groupby('Game', group_keys=False).apply(choose_shortlist).reset_index(drop=True)
    display_df = df_spread_shortlist.copy()
    for col in ['CFB1_Cover_Prob', 'Break_Even_Prob', 'Probability_Edge']:
        display_df[col] = (display_df[col] * 100).round(1)
    return df_spread_shortlist


def value_supplied_spreads(shortlist, history):
    'CELL 57: W*profit-L per unit stake, unconditioned on pushes; supplied odds only.'
    df_spread_shortlist = shortlist.copy()
    df_hist_spread = history.copy()
    global_errors = df_hist_spread['Spread_Error'].dropna().astype(float)
    import numpy as np
    import pandas as pd
    if 'df_spread_shortlist' not in locals():
        raise NameError('df_spread_shortlist missing. Run through old Cell 55 first.')
    df_ev = df_spread_shortlist.copy()
    required_cols = ['Game', 'Team', 'Sportsbook', 'Line', 'American_Odds', 'Candidate_Cushion']
    missing = [col for col in required_cols if col not in df_ev.columns]
    if missing:
        raise KeyError('Old Cell 57 is missing required columns: ' + ', '.join(missing))
    df_ev['Profit_Multiple'] = df_ev['American_Odds'].apply(profit_multiple)
    df_ev['Break_Even_Prob'] = df_ev['American_Odds'].apply(break_even_prob)
    if 'global_errors' not in locals():
        raise NameError('global_errors missing. Run the historical spread probability cells first.')
    df_ev = candidate_probabilities(df_ev, df_hist_spread)
    df_ev['Probability_Edge'] = df_ev['CFB1_Win_Prob'] - df_ev['Break_Even_Prob']
    df_ev['EV_Per_Dollar'] = df_ev['CFB1_Win_Prob'] * df_ev['Profit_Multiple'] - df_ev['CFB1_Loss_Prob']
    df_ev['Expected_ROI'] = df_ev['EV_Per_Dollar']

    def ev_status(row):
        roi = row['Expected_ROI']
        if pd.isna(roi):
            return 'NO_EV'
        if roi >= 0.05:
            return 'STRONG_PRICE_EDGE'
        if roi >= 0.03:
            return 'POSITIVE_EV'
        if roi > 0:
            return 'THIN_POSITIVE_EV'
        return 'NON_POSITIVE_EV'
    df_ev['EV_Status'] = df_ev.apply(ev_status, axis=1)

    def build_warning(row):
        warnings = []
        if 'Key_Tradeoff' in row.index and pd.notna(row['Key_Tradeoff']) and (str(row['Key_Tradeoff']).strip() != ''):
            warnings.append(str(row['Key_Tradeoff']))
        if 'Decision_Status' in row.index and row['Decision_Status'] in ['MARKET_CONFLICT', 'STRONG_MARKET_CONFLICT']:
            warnings.append(str(row['Decision_Status']))
        return ' | '.join(warnings)
    df_ev['Decision_Warning'] = df_ev.apply(build_warning, axis=1)
    legacy_staking_cols = ['Full_Kelly', 'Quarter_Kelly', 'Quarter_Kelly_Stake', 'Push_Adjusted_Full_Kelly', 'Push_Adjusted_Quarter_Kelly', 'Push_Adjusted_Stake']
    df_ev.drop(columns=[col for col in legacy_staking_cols if col in df_ev.columns], inplace=True)
    display_cols = ['Game', 'Team', 'Sportsbook', 'Line', 'American_Odds', 'Candidate_Cushion', 'Probability_Source', 'CFB1_Win_Prob', 'CFB1_Push_Prob', 'CFB1_Loss_Prob', 'Break_Even_Prob', 'Expected_ROI', 'Key_Tradeoff', 'Decision_Status', 'Decision_Warning', 'EV_Status']
    display_cols = [col for col in display_cols if col in df_ev.columns]
    display_df = df_ev[display_cols].sort_values('Expected_ROI', ascending=False).reset_index(drop=True).copy()
    for col in ['CFB1_Win_Prob', 'CFB1_Push_Prob', 'CFB1_Loss_Prob', 'Break_Even_Prob', 'Expected_ROI']:
        if col in display_df.columns:
            display_df[col] = (display_df[col] * 100).round(2)
    prob_sum = df_ev['CFB1_Win_Prob'] + df_ev['CFB1_Push_Prob'] + df_ev['CFB1_Loss_Prob']
    prob_errors = (~np.isclose(prob_sum, 1.0, atol=1e-09)).sum()
    legacy_remaining = [col for col in legacy_staking_cols if col in df_ev.columns]
    if prob_errors != 0:
        raise ValueError('Probability validation failed.')
    if legacy_remaining:
        raise ValueError('Legacy Kelly/stake columns remain in df_ev.')
    return df_ev


def value_push_adjusted_spreads(valued_candidates, history):
    'CELL 57A: adjusted W*profit-L, push refund contributes zero; EV_Status is not refreshed.'
    df_ev = adjust_push_probabilities(valued_candidates, history)
    def is_integer_line(value):
        if pd.isna(value):
            return False
        return float(value).is_integer()
    df_ev['Push_Adjusted_EV_Per_Dollar'] = df_ev['Push_Adjusted_Win_Prob'] * df_ev['Profit_Multiple'] - df_ev['Push_Adjusted_Loss_Prob']
    df_ev['Push_Adjusted_ROI'] = df_ev['Push_Adjusted_EV_Per_Dollar']
    legacy_staking_cols = ['Full_Kelly', 'Quarter_Kelly', 'Quarter_Kelly_Stake', 'Push_Adjusted_Full_Kelly', 'Push_Adjusted_Quarter_Kelly', 'Push_Adjusted_Stake']
    df_ev.drop(columns=[col for col in legacy_staking_cols if col in df_ev.columns], inplace=True)
    display_cols = ['Game', 'Team', 'Sportsbook', 'Line', 'American_Odds', 'Historical_Push_Prob', 'Historical_Push_N', 'Push_Adjusted_Win_Prob', 'Push_Adjusted_Push_Prob', 'Push_Adjusted_Loss_Prob', 'Break_Even_Prob', 'Push_Adjusted_ROI', 'Key_Tradeoff', 'Decision_Status', 'Decision_Warning']
    display_cols = [col for col in display_cols if col in df_ev.columns]
    display_df = df_ev[display_cols].sort_values('Push_Adjusted_ROI', ascending=False).reset_index(drop=True).copy()
    for col in ['Historical_Push_Prob', 'Push_Adjusted_Win_Prob', 'Push_Adjusted_Push_Prob', 'Push_Adjusted_Loss_Prob', 'Break_Even_Prob', 'Push_Adjusted_ROI']:
        if col in display_df.columns:
            display_df[col] = (display_df[col] * 100).round(2)
    prob_sum = df_ev['Push_Adjusted_Win_Prob'] + df_ev['Push_Adjusted_Push_Prob'] + df_ev['Push_Adjusted_Loss_Prob']
    prob_errors = (~np.isclose(prob_sum, 1.0, atol=1e-09)).sum()
    integer_rows = df_ev['Line'].apply(is_integer_line)
    nonzero_push_rows = df_ev['Push_Adjusted_Push_Prob'] > 0
    legacy_remaining = [col for col in legacy_staking_cols if col in df_ev.columns]
    if prob_errors != 0:
        raise ValueError('Push-adjusted probability validation failed.')
    if legacy_remaining:
        raise ValueError('Legacy Kelly/stake columns remain after Cell 57A.')
    return df_ev
