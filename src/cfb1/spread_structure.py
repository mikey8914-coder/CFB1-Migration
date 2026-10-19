"""OLD CELL 37/38 current spread structure; no temporal key-crossing audit."""

import pandas as pd

LARGE_SPREAD_THRESHOLD = 16.5
VERY_LARGE_SPREAD_THRESHOLD = 20.5


def classify_spread_structure(master, routes):
    'OLD CELL 37: full-slate consensus/key fields and nonempty-route display table.'
    df_master_bcf = master.copy()
    df_market_routes = routes.copy()
    SPREAD_KEY_NUMBERS = [3, 7, 10, 14]
    missing_spread_inputs = df_master_bcf[df_master_bcf[['DK_Spread', 'FD_Spread']].isna().any(axis=1)]
    df_master_bcf['Consensus_Spread'] = ((df_master_bcf['DK_Spread'] + df_master_bcf['FD_Spread']) / 2).round(2)
    df_master_bcf['Consensus_Spread_Abs'] = df_master_bcf['Consensus_Spread'].abs()
    
    def nearest_key_number(spread):
        magnitude = abs(spread)
        nearest = min(SPREAD_KEY_NUMBERS, key=lambda key: abs(magnitude - key))
        distance = abs(magnitude - nearest)
        return (nearest, round(distance, 2))
    key_results = df_master_bcf['Consensus_Spread'].apply(nearest_key_number)
    df_master_bcf['Nearest_Key_Number'] = [result[0] for result in key_results]
    df_master_bcf['Distance_From_Key'] = [result[1] for result in key_results]
    df_master_bcf['Within_0.5_Key'] = df_master_bcf['Distance_From_Key'] <= 0.5
    df_master_bcf['Within_1.0_Key'] = df_master_bcf['Distance_From_Key'] <= 1.0
    
    def spread_bucket(magnitude):
        if magnitude < 3:
            return 'UNDER_3'
        elif magnitude < 7:
            return '3_TO_6.5'
        elif magnitude < 10:
            return '7_TO_9.5'
        elif magnitude < 14:
            return '10_TO_13.5'
        elif magnitude < 17:
            return '14_TO_16.5'
        elif magnitude < 21:
            return '17_TO_20.5'
        else:
            return '21_PLUS'
    df_master_bcf['Spread_Size_Bucket'] = df_master_bcf['Consensus_Spread_Abs'].apply(spread_bucket)
    missing_outputs = df_master_bcf[df_master_bcf[['Consensus_Spread', 'Consensus_Spread_Abs', 'Nearest_Key_Number', 'Distance_From_Key', 'Within_0.5_Key', 'Within_1.0_Key', 'Spread_Size_Bucket']].isna().any(axis=1)]
    if len(missing_spread_inputs) == 0 and len(missing_outputs) == 0:
        pass
    else:
        raise ValueError('Spread / Key Number validation failed.')
    routed_games = set(df_market_routes.loc[df_market_routes['Eligible_Market_Routes'] != '', 'Game'])
    market_structure_rows = []
    for _, row in df_master_bcf.iterrows():
        game = f"{row['Away_Team']} at {row['Home_Team']}"
        if game in routed_games:
            market_structure_rows.append({'Game': game, 'DK_Spread': row['DK_Spread'], 'FD_Spread': row['FD_Spread'], 'Consensus_Spread': row['Consensus_Spread'], 'Nearest_Key_Number': row['Nearest_Key_Number'], 'Distance_From_Key': row['Distance_From_Key'], 'Spread_Size_Bucket': row['Spread_Size_Bucket']})
    df_routed_market_structure = pd.DataFrame(market_structure_rows)
    return (df_master_bcf, df_routed_market_structure)


def classify_large_spreads(master, routes):
    'OLD CELL 38: consensus favorite, inclusive size flags, and routed display classes.'
    df_master_bcf = master.copy()
    df_market_routes = routes.copy()
    LARGE_SPREAD_THRESHOLD = 16.5
    VERY_LARGE_SPREAD_THRESHOLD = 20.5
    
    def market_favorite_info(row):
        spread = row['Consensus_Spread']
        if spread < 0:
            return pd.Series([row['Home_Team'], abs(spread)])
        elif spread > 0:
            return pd.Series([row['Away_Team'], abs(spread)])
        else:
            return pd.Series(['PICKEM', 0.0])
    df_master_bcf[['Consensus_Favorite', 'Favorite_Spread_Size']] = df_master_bcf.apply(market_favorite_info, axis=1)
    df_master_bcf['Large_Spread_16_5'] = df_master_bcf['Favorite_Spread_Size'] >= LARGE_SPREAD_THRESHOLD
    df_master_bcf['Very_Large_Spread_20_5'] = df_master_bcf['Favorite_Spread_Size'] >= VERY_LARGE_SPREAD_THRESHOLD
    missing_inputs = df_master_bcf[df_master_bcf[['Consensus_Spread', 'Home_Team', 'Away_Team']].isna().any(axis=1)]
    missing_outputs = df_master_bcf[df_master_bcf[['Consensus_Favorite', 'Favorite_Spread_Size', 'Large_Spread_16_5', 'Very_Large_Spread_20_5']].isna().any(axis=1)]
    invalid_size = int((df_master_bcf['Favorite_Spread_Size'] < 0).sum())
    large_count = int(df_master_bcf['Large_Spread_16_5'].sum())
    very_large_count = int(df_master_bcf['Very_Large_Spread_20_5'].sum())
    if len(missing_inputs) == 0 and len(missing_outputs) == 0 and (invalid_size == 0):
        pass
    else:
        raise ValueError('Large-spread classification validation failed.')
    routed_games = set(df_market_routes.loc[df_market_routes['Eligible_Market_Routes'] != '', 'Game'])
    large_spread_rows = []
    for _, row in df_master_bcf.iterrows():
        game = f"{row['Away_Team']} at {row['Home_Team']}"
        if game not in routed_games:
            continue
        if row['Favorite_Spread_Size'] >= VERY_LARGE_SPREAD_THRESHOLD:
            spread_class = 'VERY_LARGE_20.5_PLUS'
        elif row['Favorite_Spread_Size'] >= LARGE_SPREAD_THRESHOLD:
            spread_class = 'LARGE_16.5_TO_20'
        else:
            spread_class = 'BELOW_16.5'
        large_spread_rows.append({'Game': game, 'Consensus_Favorite': row['Consensus_Favorite'], 'Favorite_Spread_Size': row['Favorite_Spread_Size'], 'Spread_Class': spread_class, 'Nearest_Key_Number': row['Nearest_Key_Number'], 'Distance_From_Key': row['Distance_From_Key']})
    df_large_spread_routed = pd.DataFrame(large_spread_rows)
    return (df_master_bcf, df_large_spread_routed)
