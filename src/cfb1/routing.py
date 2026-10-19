"""OLD CELL 36/39/40 route metadata only; no prices or team-total models."""

import pandas as pd

from cfb1.spread_structure import LARGE_SPREAD_THRESHOLD, VERY_LARGE_SPREAD_THRESHOLD


def route_markets(convergence):
    'OLD CELL 36: preserve every agreement, ordered route labels, and conflict status.'
    df_convergence_corrected = convergence.copy()
    routing_rows = []
    for _, row in df_convergence_corrected.iterrows():
        if not row['EPA_FEI_Agree']:
            continue
        support_text = row['M3_Support']
        conflict_text = row['M3_Conflict']
        routes = []
        spread_status = 'STANDARD_REVIEW'
        if row['M3_Support_Count'] > 0:
            routes.append('FULL_GAME_SPREAD')
        if row['M3_Conflict_Count'] > 0:
            spread_status = 'DOWNGRADE_FULL_GAME_SPREAD'
            routes.append('DERIVATIVES_FIRST')
        if 'LINE_YARDS' in support_text or 'OAY_DAY' in support_text:
            routes.append('TEAM_TOTAL_OVER')
            routes.append('1H_TEAM_TOTAL_OVER')
            routes.append('1H_SPREAD_REVIEW')
        if 'HAVOC_TRAP' in support_text or 'EXPLOSIVENESS_FRAUD' in support_text:
            routes.append('OPP_TEAM_TOTAL_UNDER')
            routes.append('OPP_1H_TEAM_TOTAL_UNDER')
            routes.append('1H_UNDER_REVIEW')
        routes = list(dict.fromkeys(routes))
        routing_rows.append({'Game': row['Game'], 'Model_Side': row['Shared_Side'], 'EPA_Value': row['EPA_Value'], 'FEI_Value': row['FEI_Value'], 'M3_Support': support_text, 'M3_Conflict': conflict_text, 'Spread_Status': spread_status, 'Eligible_Market_Routes': ', '.join(routes), 'Final_Bet_Status': 'UNPRICED — DO NOT BET YET'})
    df_market_routes = pd.DataFrame(routing_rows)
    expected_games = int(df_convergence_corrected['EPA_FEI_Agree'].sum())
    duplicate_games = int(df_market_routes.duplicated(subset=['Game'], keep=False).sum())
    missing_required = int(df_market_routes[['Game', 'Model_Side', 'EPA_Value', 'FEI_Value', 'Spread_Status', 'Eligible_Market_Routes', 'Final_Bet_Status']].isna().any(axis=1).sum())
    blank_model_side = int((df_market_routes['Model_Side'] == '').sum())
    if len(df_market_routes) == expected_games and duplicate_games == 0 and (missing_required == 0) and (blank_model_side == 0):
        pass
    else:
        raise ValueError('Market Routing Board validation failed.')
    return df_market_routes


def apply_large_spread_routing(routes, master):
    'OLD CELL 39: spread-size additions, then nonempty conflict override.'
    df_market_routes = routes.copy()
    df_master_bcf = master.copy()
    market_route_lookup = df_master_bcf[['Away_Team', 'Home_Team', 'Favorite_Spread_Size']].copy()
    market_route_lookup['Game'] = market_route_lookup['Away_Team'] + ' at ' + market_route_lookup['Home_Team']
    market_route_lookup = market_route_lookup[['Game', 'Favorite_Spread_Size']]
    routing_base = df_market_routes.merge(market_route_lookup, on='Game', how='left', validate='one_to_one')
    final_route_rows = []
    for _, route_row in routing_base.iterrows():
        game = route_row['Game']
        spread_size = route_row['Favorite_Spread_Size']
        routes = []
        if route_row['Eligible_Market_Routes']:
            routes = [x.strip() for x in route_row['Eligible_Market_Routes'].split(',')]
        spread_status = route_row['Spread_Status']
        if spread_size >= VERY_LARGE_SPREAD_THRESHOLD:
            spread_status = 'DERIVATIVES_FIRST_20.5_PLUS'
            routes.append('1H_SPREAD_REVIEW')
            routes.append('TEAM_TOTAL_REVIEW')
        elif spread_size >= LARGE_SPREAD_THRESHOLD:
            spread_status = 'LARGE_SPREAD_CAUTION'
            routes.append('1H_SPREAD_REVIEW')
            routes.append('TEAM_TOTAL_REVIEW')
        if route_row['M3_Conflict'] != '':
            spread_status = 'DOWNGRADE_FULL_GAME_SPREAD'
            routes.append('DERIVATIVES_FIRST')
        routes = list(dict.fromkeys(routes))
        final_route_rows.append({'Game': game, 'Model_Side': route_row['Model_Side'], 'EPA_Value': route_row['EPA_Value'], 'FEI_Value': route_row['FEI_Value'], 'M3_Support': route_row['M3_Support'], 'M3_Conflict': route_row['M3_Conflict'], 'Favorite_Spread_Size': spread_size, 'Spread_Status': spread_status, 'Eligible_Market_Routes': ', '.join(routes), 'Final_Bet_Status': 'UNPRICED — DO NOT BET YET'})
    df_final_routes = pd.DataFrame(final_route_rows)
    active_routes = df_final_routes[df_final_routes['Eligible_Market_Routes'] != ''].copy()
    expected_games = len(df_market_routes)
    duplicate_games = int(df_final_routes.duplicated(subset=['Game'], keep=False).sum())
    missing_spread_size = int(df_final_routes['Favorite_Spread_Size'].isna().sum())
    missing_required = int(df_final_routes[['Game', 'Model_Side', 'EPA_Value', 'FEI_Value', 'Favorite_Spread_Size', 'Spread_Status', 'Eligible_Market_Routes', 'Final_Bet_Status']].isna().any(axis=1).sum())
    if len(df_final_routes) == expected_games and duplicate_games == 0 and (missing_spread_size == 0) and (missing_required == 0):
        pass
    else:
        raise ValueError('Large-spread market routing validation failed.')
    return df_final_routes


def separate_evidence(final_routes):
    'OLD CELL 40: matchup support precedes conflict; spread size is a routing modifier.'
    df_final_routes = final_routes.copy()
    evidence_route_rows = []
    for _, row in df_final_routes.iterrows():
        evidence = []
        routing_modifiers = []
        evidence.append('EPA_FEI_DIRECTIONAL_AGREEMENT')
        if row['M3_Support'] != '':
            evidence.append('MODULE3_SUPPORT')
        if row['M3_Conflict'] != '':
            evidence.append('MODULE3_CONFLICT')
        if row['Favorite_Spread_Size'] >= VERY_LARGE_SPREAD_THRESHOLD:
            routing_modifiers.append('VERY_LARGE_SPREAD_20.5_PLUS')
        elif row['Favorite_Spread_Size'] >= LARGE_SPREAD_THRESHOLD:
            routing_modifiers.append('LARGE_SPREAD_16.5_TO_20')
        if row['Spread_Status'] == 'DOWNGRADE_FULL_GAME_SPREAD':
            routing_modifiers.append('FULL_GAME_SPREAD_DOWNGRADE')
        if row['M3_Support'] != '':
            evidence_class = 'MODEL_PLUS_MATCHUP_SUPPORT'
        elif row['M3_Conflict'] != '':
            evidence_class = 'MODEL_WITH_MATCHUP_CONFLICT'
        else:
            evidence_class = 'MODEL_AGREEMENT_ONLY'
        evidence_route_rows.append({'Game': row['Game'], 'Model_Side': row['Model_Side'], 'EPA_Value': row['EPA_Value'], 'FEI_Value': row['FEI_Value'], 'Evidence_Class': evidence_class, 'Evidence': ', '.join(evidence), 'Routing_Modifiers': ', '.join(routing_modifiers), 'Spread_Status': row['Spread_Status'], 'Eligible_Market_Routes': row['Eligible_Market_Routes'], 'Final_Bet_Status': 'UNPRICED — DO NOT BET YET'})
    df_evidence_routes = pd.DataFrame(evidence_route_rows)
    expected_games = len(df_final_routes)
    duplicate_games = int(df_evidence_routes.duplicated(subset=['Game'], keep=False).sum())
    missing_required = int(df_evidence_routes[['Game', 'Model_Side', 'EPA_Value', 'FEI_Value', 'Evidence_Class', 'Evidence', 'Spread_Status', 'Eligible_Market_Routes', 'Final_Bet_Status']].isna().any(axis=1).sum())
    blank_evidence = int((df_evidence_routes['Evidence'] == '').sum())
    if len(df_evidence_routes) == expected_games and duplicate_games == 0 and (missing_required == 0) and (blank_evidence == 0):
        pass
    else:
        raise ValueError('Evidence vs Routing validation failed.')
    module3_evidence = df_evidence_routes[df_evidence_routes['Evidence_Class'] != 'MODEL_AGREEMENT_ONLY'].copy()
    model_only_routed = df_evidence_routes[(df_evidence_routes['Evidence_Class'] == 'MODEL_AGREEMENT_ONLY') & (df_evidence_routes['Routing_Modifiers'] != '')].copy()
    return df_evidence_routes
