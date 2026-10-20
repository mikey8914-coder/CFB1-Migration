"""Standard CFB1 football output; externally supplied valuation is optional.

Legacy compact/price-card views are separate from the complete weekly handoff.
No team-total calculations, price acquisition, or stake recommendations.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from cfb1.final_decision import DecisionBatch

COMPACT_COLUMNS = [
    'Game', 'Model_Side', 'Review_Class', 'Phase1_Reason', 'M3_Support', 'M3_Conflict',
    'Favorite_Spread_Size', 'Spread_Status', 'Open_Home_Spread', 'Current_Home_Spread',
    'Movement_Toward', 'Movement_Class', 'Key_Numbers_Crossed', 'Market_Relationship',
    'Decision_Status', 'Eligible_Market_Routes', 'Decision_Note',
]
STATUS_ORDER = {'CONFIRMED': 1, 'CONFIRMED_BUT_LARGE_SPREAD': 2, 'NEUTRAL_MARKET': 3,
    'CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL': 4, 'CONFLICT_REVIEW_UNRESOLVED': 5,
    'MARKET_CONFLICT': 6, 'STRONG_MARKET_CONFLICT': 7,
    'CONFLICT_REVIEW_MARKET_REJECTS_MODEL': 8, 'UNCLASSIFIED': 9}
PRICED_COLUMNS = ['Game', 'Market_Family', 'Team', 'Direction', 'Bet_Label', 'Sportsbook',
    'Line', 'American_Odds', 'Model_Adjustment', 'Model_Probability', 'Push_Probability',
    'Break_Even_Prob', 'Expected_ROI_Final', 'Decision_Status', 'Pricing_Status', 'Warning']
CARD_COLUMNS = ['Game', 'Market_Family', 'Card_Role', 'Team', 'Direction', 'Bet_Label',
    'Sportsbook', 'Line', 'American_Odds', 'Model_Adjustment', 'Model_Probability',
    'Push_Probability', 'Break_Even', 'Expected_ROI', 'Decision_Status', 'Model_Status',
    'Warning_Final']
ARCHITECT_COLUMNS = ['Game', 'Model_Side', 'Market_Family', 'Card_Role', 'Team', 'Direction',
    'Bet_Label', 'Sportsbook', 'Line', 'American_Odds', 'Model_Adjustment', 'Model_Probability',
    'Push_Probability', 'Break_Even_Prob', 'Expected_ROI', 'Model_Status', 'Decision_Status',
    'Warning', 'Phase1_Reason', 'Module3_Support_Conflict', 'Spread_Status', 'Market_Relationship',
    'Open_Home_Spread', 'Current_Home_Spread', 'Movement_Size', 'Movement_Toward',
    'Movement_Class', 'Key_Numbers_Crossed', 'Eligible_Market_Routes', 'Decision_Note']
EXTRA_COLUMNS = ['Home_Team', 'Away_Team', 'game_id', 'Review_Class', 'M3_Support', 'M3_Conflict', 'Favorite_Spread_Size',
    'Market_Model_Spread', 'Retained_Model_Spread', 'Model_Cushion_Points', 'Line_Value_Status',
    'Loss_Probability', 'Probability_Source', 'Pricing_Status', 'EV_Status',
    'Current_Market_Ready', 'Market_Status', 'Audit_Ready', 'Audit_Status', 'Audit_Reason']
HANDOFF_COLUMNS = ARCHITECT_COLUMNS + EXTRA_COLUMNS
QUOTE_KEYS = ['Game', 'Team', 'Sportsbook', 'Line', 'American_Odds']
PROBABILITY_KEYS = ['Game', 'Team', 'Line']
ADJUSTED_TRIPLET = ['Push_Adjusted_Win_Prob', 'Push_Adjusted_Push_Prob', 'Push_Adjusted_Loss_Prob']
BASE_TRIPLET = ['CFB1_Win_Prob', 'CFB1_Push_Prob', 'CFB1_Loss_Prob']


def _require(frame, columns):
    missing = [c for c in columns if c not in frame]
    if missing:
        raise ValueError('Missing output inputs: ' + ', '.join(missing))


def _unique(frame, keys):
    _require(frame, keys)
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError('Missing or ambiguous output keys: ' + ', '.join(keys))


def compact_final_board(final_decisions):
    """Exact OLD CELL 45 projection, text cleanup, order, and validation."""
    _require(final_decisions, COMPACT_COLUMNS)
    board = final_decisions[COMPACT_COLUMNS].copy()
    for col in board.select_dtypes(include='object'):
        board[col] = board[col].fillna('').astype(str).str.strip()
    board['Display_Order'] = board.Decision_Status.map(STATUS_ORDER).fillna(99)
    board = board.sort_values(['Display_Order', 'Game']).drop(columns='Display_Order').reset_index(drop=True)
    if (board.Game.duplicated().any() or board.Decision_Status.eq('').any()
            or board.Model_Side.eq('').any() or len(board) != len(final_decisions)):
        raise ValueError('Gem export validation failed.')
    return board


def pricing_status_from_roi(roi):
    """CELL 61 uses .02, deliberately different from CELL 57's .03."""
    if pd.isna(roi):
        return 'NO_QUANTITATIVE_PRICE'
    roi = float(roi)
    if roi >= .05:
        return 'STRONG_PRICE_EDGE'
    if roi >= .02:
        return 'POSITIVE_EV'
    if roi > 0:
        return 'THIN_POSITIVE_EV'
    return 'NON_POSITIVE_EV'


def priced_spread_handoff(valued):
    """CELL 61 spread branch only; no experimental branch dependency."""
    _require(valued, ['Game', 'Team', 'Sportsbook', 'Line', 'American_Odds', 'Candidate_Cushion',
        'Push_Adjusted_Win_Prob', 'Push_Adjusted_Push_Prob', 'Push_Adjusted_ROI',
        'Break_Even_Prob', 'Decision_Status', 'Decision_Warning'])
    out = valued.copy()
    out['Market_Family'] = 'FULL_GAME_SPREAD'
    out['Direction'] = 'SPREAD'
    out['Bet_Label'] = out.Team.astype(str) + ' ' + out.Line.astype(str)
    for target, source in {'Model_Adjustment':'Candidate_Cushion',
        'Model_Probability':'Push_Adjusted_Win_Prob', 'Push_Probability':'Push_Adjusted_Push_Prob',
        'Expected_ROI_Final':'Push_Adjusted_ROI'}.items():
        out[target] = out[source]
    out['Pricing_Status'] = out.Expected_ROI_Final.apply(pricing_status_from_roi)
    out['Warning'] = out.Decision_Warning.fillna('')
    out = out[PRICED_COLUMNS].sort_values(['Game', 'Market_Family', 'Expected_ROI_Final'],
        ascending=[True, True, False], na_position='last').reset_index(drop=True)
    if out.Game.isna().any():
        raise ValueError('Cell 61 contains rows with missing game names.')
    return out


def spread_decision_card(valued):
    """Exact CELL 62 spread selection; this view never defines weekly membership."""
    _require(valued, ['Market_Model_Spread', *PRICED_SOURCE_COLUMNS])
    spread = priced_spread_handoff(valued)
    spread = spread.rename(columns={'Expected_ROI_Final':'Expected_ROI',
        'Break_Even_Prob':'Break_Even', 'Warning':'Warning_Final'})
    spread = spread[spread.Expected_ROI > 0].copy()
    spread['Model_Status'] = 'FULL_GAME_SPREAD_V1'
    # Source rows are aligned by full quote identity, never a Game-only price join.
    _unique(valued, QUOTE_KEYS)
    spread = valued[QUOTE_KEYS + ['Market_Model_Spread']].merge(spread, on=QUOTE_KEYS,
        how='inner', validate='one_to_one')
    parts = []
    for _, group in spread.groupby(['Game', 'Team']):
        group = group.copy()
        group['Anchor_Distance'] = (group.Line-group.Market_Model_Spread).abs()
        primary = group.sort_values(['Anchor_Distance', 'American_Odds'], ascending=[True, False]).iloc[[0]].copy()
        primary['Card_Role'] = 'PRIMARY'; parts.append(primary)
        remaining = group.drop(index=primary.index)
        if len(remaining):
            alt = remaining.sort_values('Expected_ROI', ascending=False).iloc[[0]].copy()
            alt['Card_Role'] = 'VALUE_ALT'; parts.append(alt)
    if not parts:
        return pd.DataFrame(columns=CARD_COLUMNS)
    return pd.concat(parts, ignore_index=True)[CARD_COLUMNS].sort_values(
        ['Game', 'Market_Family', 'Card_Role']).reset_index(drop=True)


PRICED_SOURCE_COLUMNS = ['Game', 'Team', 'Sportsbook', 'Line', 'American_Odds',
    'Candidate_Cushion', 'Push_Adjusted_Win_Prob', 'Push_Adjusted_Push_Prob',
    'Push_Adjusted_Loss_Prob', 'Push_Adjusted_ROI', 'Break_Even_Prob', 'Decision_Status',
    'Decision_Warning']


def module3_context(row):
    """CELL 67 clean_m3, used for the CELL 73 context alias."""
    support, conflict = (str(row.get(c, '')).strip() for c in ['M3_Support', 'M3_Conflict'])
    support = '' if support.lower() == 'nan' else support
    conflict = '' if conflict.lower() == 'nan' else conflict
    if support and conflict:
        return f'{support} | CONFLICT: {conflict}'
    return support or (f'CONFLICT: {conflict}' if conflict else 'NONE')


def architect_card(card, final_context):
    """CELL 73 standard column/alias projection, accepting explicit context."""
    context_cols = ['Game', 'Model_Side', 'Review_Class', 'Phase_1_Reason',
        'Module_3_Support_Conflict', 'Open_Home_Spread', 'Current_Home_Spread',
        'Movement_Size', 'Movement_Toward', 'Movement_Class', 'Key_Numbers_Crossed',
        'Market_Relationship', 'Eligible_Market_Routes', 'Decision_Note', 'Spread_Status']
    context = final_context[[c for c in context_cols if c in final_context]].drop_duplicates('Game')
    out = card.merge(context, on='Game', how='left', validate='many_to_one', suffixes=('', '_GameContext'))
    out = out.rename(columns={'Break_Even':'Break_Even_Prob', 'Warning_Final':'Warning',
        'Phase_1_Reason':'Phase1_Reason', 'Module_3_Support_Conflict':'Module3_Support_Conflict'})
    out = out[[c for c in ARCHITECT_COLUMNS if c in out]].copy()
    for col in ['Model_Side', 'Model_Status', 'Decision_Status', 'Warning', 'Phase1_Reason',
        'Module3_Support_Conflict', 'Spread_Status', 'Market_Relationship', 'Movement_Toward',
        'Movement_Class', 'Key_Numbers_Crossed', 'Eligible_Market_Routes', 'Decision_Note']:
        if col in out:
            out[col] = out[col].fillna('')
    _require(out, ['Game', 'Market_Family', 'Card_Role', 'Team', 'Direction', 'Bet_Label',
        'Sportsbook', 'Line', 'American_Odds', 'Model_Probability', 'Push_Probability',
        'Break_Even_Prob', 'Expected_ROI', 'Model_Status', 'Decision_Status', 'Warning',
        'Eligible_Market_Routes'])
    return out


@dataclass
class HandoffTables:
    """All candidates, canonical priced rows, and legacy-selected card are distinct."""
    weekly: pd.DataFrame
    priced: pd.DataFrame
    card: pd.DataFrame


def _attach(base, extra, fields):
    if extra is None or not len(extra):
        return base
    _unique(extra, ['Game'])
    cols = [c for c in fields if c != 'Game' and c in extra]
    joined = base.merge(extra[['Game', *cols]], on='Game', how='left',
        validate='one_to_one', suffixes=('', '__context'))
    for col in cols:
        source = col + '__context'
        if source in joined:
            joined[col] = joined[col].where(joined[col].notna(), joined[source])
            joined = joined.drop(columns=source)
    return joined


def _triplet(row):
    cols = ADJUSTED_TRIPLET if all(c in row for c in ADJUSTED_TRIPLET) else BASE_TRIPLET
    values = [row.get(c, np.nan) for c in cols]
    if not all(pd.notna(v) for v in values) or not np.isclose(sum(values), 1., atol=1e-9):
        raise ValueError('Incomplete or invalid handoff probability triplet')
    if any(v < 0 or v > 1 for v in values):
        raise ValueError('Out-of-range handoff probability')
    return values


def assemble_handoff(decisions, *, routes=None, retained=None, key_value=None,
        probabilities=None, valued=None, availability=None, market_unavailable=None):
    """Preserve every final/pending candidate and explicit schedule exclusion.

    decisions is a final-decision DataFrame or migrated DecisionBatch. Optional
    price-free probabilities must identify the exact Game/Team/Line. Valuation
    rows must be canonical CELL 57A output with externally supplied odds.
    No missing price/audit is converted into a neutral football decision.
    """
    if isinstance(decisions, DecisionBatch):
        ready, pending = decisions.decisions.copy(), decisions.pending_audit.copy()
    else:
        ready, pending = decisions.copy(), pd.DataFrame()
    if len(ready):
        compact_final_board(ready)  # Preserve the original required-field gate.
    base = pd.concat([ready, pending], ignore_index=True)
    if not len(base):
        base = pd.DataFrame(columns=['Game', 'Model_Side'])
    _unique(base, ['Game'])
    base = _attach(base, routes, COMPACT_COLUMNS)
    base = _attach(base, retained, ['Home_Team', 'Away_Team', 'game_id'])
    base = _attach(base, key_value, ['Home_Team', 'Away_Team', 'Market_Model_Spread',
        'Retained_Model_Spread', 'Model_Cushion_Points', 'Line_Value_Status', 'Current_Home_Spread'])
    if availability is not None:
        _unique(availability, ['Game'])
        if set(availability.Game) != set(base.Game):
            raise ValueError('Availability must cover all output candidates')
        # Explicit readiness is authoritative, including pending-audit columns.
        base = base.drop(columns=[c for c in availability if c != 'Game' and c in base]).merge(
            availability, on='Game', how='left', validate='one_to_one')
    ready_games = set(ready.get('Game', []))
    for col in ['Current_Market_Ready', 'Audit_Ready']:
        if col not in base:
            base[col] = pd.Series(index=base.index, dtype=object)
        mask = base.Game.isin(ready_games) & base[col].isna()
        base.loc[mask, col] = True
        if base[col].isna().any():
            raise ValueError('Pending rows require explicit readiness')
        if not base[col].map(lambda v: isinstance(v, (bool, np.bool_))).all():
            raise ValueError('Readiness must be boolean')
        base[col] = base[col].astype(bool)
    if market_unavailable is not None and len(market_unavailable):
        _unique(market_unavailable, ['Game'])
        if set(market_unavailable.Game) & set(base.Game):
            raise ValueError('Market exclusion duplicates a candidate')
        excluded = market_unavailable.copy()
        excluded['Current_Market_Ready'] = False
        excluded['Audit_Ready'] = False
        excluded['Audit_Status'] = 'AUDIT_UNAVAILABLE'
        excluded['Audit_Reason'] = 'MARKET_DATA_UNAVAILABLE'
        base = pd.concat([base, excluded], ignore_index=True)
    if base[['Current_Market_Ready', 'Audit_Ready']].isna().any().any():
        raise ValueError('Missing explicit availability for pending rows')
    if (base.Audit_Ready & ~base.Current_Market_Ready).any():
        raise ValueError('Movement audit cannot be ready without current market')
    for optional, keys in [(probabilities, PROBABILITY_KEYS), (valued, QUOTE_KEYS)]:
        if optional is not None and len(optional):
            _unique(optional, keys)
            if not set(optional.Game) <= set(base.Game):
                raise ValueError('Orphan probability or price row')
    if probabilities is not None and len(probabilities):
        expected = base[['Game', 'Model_Side', 'Market_Model_Spread']].rename(
            columns={'Model_Side':'Team', 'Market_Model_Spread':'Line'}) if 'Market_Model_Spread' in base else pd.DataFrame(columns=PROBABILITY_KEYS)
        check = probabilities[PROBABILITY_KEYS].merge(expected, on=PROBABILITY_KEYS,
            how='left', indicator=True, validate='one_to_one')
        if not check._merge.eq('both').all():
            raise ValueError('Price-free probability must match the exact model-side current line')
    rows = []
    for _, context in base.iterrows():
        game = context.Game
        row = {c: context.get(c, np.nan) for c in HANDOFF_COLUMNS}
        row['Team'] = context.get('Model_Side', '')
        row['Direction'] = 'SPREAD'; row['Market_Family'] = 'FULL_GAME_SPREAD'
        row['Card_Role'] = 'MODEL_REVIEW'
        row['Market_Status'] = 'CURRENT_MARKET_READY' if context.Current_Market_Ready else 'MARKET_DATA_UNAVAILABLE'
        row['Audit_Status'] = 'AUDIT_READY' if context.Audit_Ready else 'AUDIT_UNAVAILABLE'
        row['Audit_Reason'] = context.get('Audit_Reason', '')
        if pd.isna(row['Audit_Reason']): row['Audit_Reason'] = ''
        row['Module3_Support_Conflict'] = module3_context(context)
        row['Model_Status'] = 'FULL_GAME_SPREAD_V1' if pd.notna(row['Retained_Model_Spread']) else 'MODEL_UNAVAILABLE'
        row['Line'] = context.get('Market_Model_Spread', np.nan)
        row['Model_Adjustment'] = context.get('Model_Cushion_Points', np.nan)
        row['Warning'] = ''
        for col in ['Sportsbook','American_Odds','Break_Even_Prob','Expected_ROI','EV_Status']:
            row[col] = np.nan
        row['Pricing_Status'] = 'NO_QUANTITATIVE_PRICE'
        for col in ['Model_Probability','Push_Probability','Loss_Probability','Probability_Source']:
            row[col] = np.nan
        prices = valued[valued.Game.eq(game)] if valued is not None else pd.DataFrame()
        if len(prices) and not context.Current_Market_Ready:
            raise ValueError('Cannot attach valuation to unavailable current market')
        if len(prices):
            for _, quote in prices.iterrows():
                quote_status = '' if pd.isna(quote.Decision_Status) else str(quote.Decision_Status).strip()
                context_status = context.get('Decision_Status', '')
                context_status = '' if pd.isna(context_status) else str(context_status).strip()
                if quote.Team != row['Team'] or quote_status != context_status:
                    raise ValueError('Price row conflicts with canonical model side or decision')
                _require(prices, PRICED_SOURCE_COLUMNS)
                item = row.copy()
                for c in ['Sportsbook','Line','American_Odds','Probability_Source','EV_Status']:
                    item[c] = quote.get(c, np.nan)
                if pd.isna(item['American_Odds']):
                    raise ValueError('Valuation requires supplied external odds')
                item['Model_Adjustment'] = quote.Candidate_Cushion
                item['Model_Probability'],item['Push_Probability'],item['Loss_Probability'] = _triplet(quote)
                item['Break_Even_Prob'] = quote.Break_Even_Prob
                item['Expected_ROI'] = quote.Push_Adjusted_ROI
                item['Warning'] = quote.Decision_Warning if pd.notna(quote.Decision_Warning) else ''
                item['Pricing_Status'] = pricing_status_from_roi(item['Expected_ROI'])
                rows.append(item)
        else:
            if probabilities is not None:
                sample = probabilities[probabilities.Game.eq(game)]
                sample = sample[sample.Team.eq(row['Team']) & sample.Line.eq(row['Line'])]
                if len(sample):
                    row['Model_Probability'],row['Push_Probability'],row['Loss_Probability'] = _triplet(sample.iloc[0])
                    row['Probability_Source'] = sample.iloc[0].get('Probability_Source', np.nan)
            rows.append(row)
    out = pd.DataFrame(rows, columns=HANDOFF_COLUMNS)
    out['Bet_Label'] = out['Bet_Label'].astype(object)
    if not len(out):
        return HandoffTables(out, pd.DataFrame(columns=PRICED_COLUMNS), pd.DataFrame(columns=ARCHITECT_COLUMNS))
    for i in out.index:
        if not out.at[i,'Current_Market_Ready']:
            out.loc[i,['Current_Home_Spread','Market_Model_Spread','Line','Model_Adjustment',
                'Model_Probability','Push_Probability','Loss_Probability']] = np.nan
        if not out.at[i,'Audit_Ready']:
            out.loc[i,['Open_Home_Spread','Movement_Size','Movement_Toward','Movement_Class',
                'Key_Numbers_Crossed','Market_Relationship']] = np.nan
        side, line = out.at[i,'Team'], out.at[i,'Line']
        out.at[i,'Bet_Label'] = f'{side} {line}' if pd.notna(line) else str(side) if pd.notna(side) else ''
    out['_order'] = out.Decision_Status.map(STATUS_ORDER).fillna(99)
    out = out.sort_values(['_order','Game','Team','Line','Sportsbook','American_Odds'],
        ascending=[True,True,True,False,True,False], na_position='last', kind='stable').drop(columns='_order').reset_index(drop=True)
    for col in ['Game','Model_Side','Team','Decision_Status','Warning','Decision_Note','Phase1_Reason',
        'Review_Class','M3_Support','M3_Conflict','Eligible_Market_Routes']:
        out[col] = out[col].fillna('').astype(str).str.strip()
    if set(out.Game) != set(base.Game):
        raise ValueError('Output lost candidate membership')
    priced = pd.DataFrame(columns=PRICED_COLUMNS)
    card = pd.DataFrame(columns=ARCHITECT_COLUMNS)
    if valued is not None and len(valued):
        priced = priced_spread_handoff(valued)
        card_source = spread_decision_card(valued)
        context = base.copy()
        context['Phase_1_Reason'] = context.get('Phase1_Reason', '')
        context['Module_3_Support_Conflict'] = context.apply(module3_context, axis=1)
        if 'Key_Numbers_Crossed' in context:
            context['Key_Numbers_Crossed'] = context.Key_Numbers_Crossed.where(context.Key_Numbers_Crossed.ne(''), 'NONE').fillna('NONE')
        card = architect_card(card_source, context)
        # CELL 67 synchronization uses exact offer keys; require membership too.
        sync = card.merge(out, on=QUOTE_KEYS, how='left', validate='one_to_one',
            suffixes=('_Card','_Weekly'), indicator=True)
        if not sync._merge.eq('both').all():
            raise ValueError('Card is missing from weekly output')
        for col in ['Model_Adjustment','Model_Probability','Push_Probability','Break_Even_Prob','Expected_ROI']:
            if not np.isclose(sync[col+'_Card'].astype(float),sync[col+'_Weekly'].astype(float),equal_nan=True).all():
                raise ValueError('Card/output metric synchronization failed: '+col)
    return HandoffTables(out[HANDOFF_COLUMNS], priced, card)
