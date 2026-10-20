"""Standard-only output parity, availability, serialization and offline pipeline."""
import ast
from contextlib import redirect_stdout
from io import StringIO
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from cfb1.handoff import (COMPACT_COLUMNS, HANDOFF_COLUMNS, PRICED_COLUMNS, CARD_COLUMNS,
    compact_final_board, priced_spread_handoff, spread_decision_card, architect_card,
    assemble_handoff, pricing_status_from_roi, module3_context)
from cfb1.export import serialize_handoff, export_handoff
from cfb1.final_decision import DecisionBatch, build_final_decisions
from cfb1.market_audit import audit_spread_movement
from cfb1.probability import (fit_retained_lines, model_side_line_value, candidate_probabilities,
    adjust_push_probabilities)
from cfb1.valuation import value_supplied_spreads, value_push_adjusted_spreads

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures'


def final_rows():
    from test_late_week_decisions import one_review,one_routes,one_observation
    review=one_review();routes=one_routes()
    audit=audit_spread_movement(one_observation().to_csv(index=False),review)
    return build_final_decisions(review,routes,audit)


def key_rows():
    return pd.DataFrame([{'Game':'Alpha at Beta','Model_Side':'Beta','Home_Team':'Beta',
        'Away_Team':'Alpha','Market_Model_Spread':-4.,'Retained_Model_Spread':-7.25,
        'Model_Cushion_Points':3.25,'Line_Value_Status':'EDGE_NO_KEY_BARRIER'}])


def valued_rows():
    from test_probability_roi import tiny_history
    candidates=pd.DataFrame([{'Game':'Alpha at Beta','Team':'Beta','Home_Team':'Beta',
        'Sportsbook':b,'Line':line,'American_Odds':odds,'Candidate_Cushion':line+7.25,
        'Market_Model_Spread':-4.,'Decision_Status':'CONFIRMED','Key_Tradeoff':''}
        for b,line,odds in [('Supplied A',-4.,-110),('Supplied B',-4.5,100),('Supplied C',-5.,120)]])
    h=tiny_history()
    return value_push_adjusted_spreads(value_supplied_spreads(candidates,h),h)


def context_for73(final):
    context=final.copy()
    context['Phase_1_Reason']=context.Phase1_Reason
    context['Module_3_Support_Conflict']=context.apply(module3_context,axis=1)
    context['Key_Numbers_Crossed']=context.Key_Numbers_Crossed.replace('',np.nan).fillna('NONE')
    return context


def frozen(label,env):
    """Exact source; isolate spread branches in TT-mixed 61/62; strip only I/O."""
    nb=json.loads((ROOT/'legacy/CFB1_Colab_Reference.ipynb').read_text())
    source=next(''.join(c['source']) for c in nb['cells']
        if any(line.startswith('# '+label+' —') for line in c['source']))
    tree=ast.parse(source)
    if label=='CELL 61':
        stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='tt_export' for t in n.targets))
        tail=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='handoff_columns' for t in n.targets))
        env.update(df_tt_ev=None,df_tt_validated=None,
            tt_export=pd.DataFrame(columns=PRICED_COLUMNS),qual_tt=pd.DataFrame(columns=PRICED_COLUMNS))
        tree.body=tree.body[:stop]+tree.body[tail:]
    if label=='CELL 62':
        stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='tt' for t in n.targets))
        tail=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='card_columns' for t in n.targets))
        env.update(df_tt_ev=None,df_tt_validated=None,CFB1_FULL_CONTEXT_V1=pd.DataFrame(),
            tt_card=pd.DataFrame(columns=CARD_COLUMNS),qual_card=pd.DataFrame(columns=CARD_COLUMNS))
        tree.body=tree.body[:stop]+tree.body[tail:]
    class NoIO(ast.NodeTransformer):
        def visit_Call(self,node):
            if label in ['CELL 61','CELL 62'] and isinstance(node.func,ast.Attribute) and node.func.attr=='concat':
                if node.args and isinstance(node.args[0],ast.List):
                    names=[n.id for n in node.args[0].elts if isinstance(n,ast.Name)]
                    if 'spread_export' in names or 'spread_card' in names:
                        node.args[0].elts=[n for n in node.args[0].elts if isinstance(n,ast.Name) and n.id in ['spread_export','spread_card']]
            return self.generic_visit(node)
        def visit_ImportFrom(self,node):
            return None if node.module=='google.colab' else node
        def visit_Expr(self,node):
            v=node.value
            if isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute):
                if v.func.attr=='download' or (v.func.attr=='to_csv' and v.args): return None
            return self.generic_visit(node)
    tree=NoIO().visit(tree);ast.fix_missing_locations(tree)
    env['display']=lambda *a:None
    with redirect_stdout(StringIO()):exec(compile(tree,label,'exec'),env)


class HandoffTests(unittest.TestCase):
    def assemble(self,**kwargs):
        return assemble_handoff(final_rows(),key_value=key_rows(),**kwargs)

    def test_standard_confirmed_row(self):
        out=self.assemble().weekly.iloc[0]
        self.assertEqual((out.Game,out.Decision_Status,out.Retained_Model_Spread),('Alpha at Beta','CONFIRMED',-7.25))
        self.assertEqual(out.Audit_Status,'AUDIT_READY')

    def test_conflict_large_spread_and_neutral_preserved(self):
        for status in ['MARKET_CONFLICT','STRONG_MARKET_CONFLICT','CONFIRMED_BUT_LARGE_SPREAD','NEUTRAL_MARKET']:
            f=final_rows();f['Decision_Status']=status
            self.assertEqual(assemble_handoff(f).weekly.Decision_Status.iloc[0],status)

    def test_without_price_retains_game_and_null_economics(self):
        out=self.assemble().weekly
        self.assertEqual(len(out),1)
        self.assertTrue(out[['Sportsbook','American_Odds','Break_Even_Prob','Expected_ROI']].isna().all().all())
        self.assertEqual(out.Pricing_Status.iloc[0],'NO_QUANTITATIVE_PRICE')

    def test_supplied_odds_uses_canonical_adjusted_metrics(self):
        v=valued_rows();out=self.assemble(valued=v)
        self.assertEqual(len(out.weekly),3)
        check=out.weekly.merge(v,on=['Game','Team','Sportsbook','Line','American_Odds'])
        np.testing.assert_allclose(check.Expected_ROI_x,check.Push_Adjusted_ROI)
        np.testing.assert_allclose(check.Loss_Probability,check.Push_Adjusted_Loss_Prob)
        self.assertEqual(set(out.card.Card_Role),{'PRIMARY','VALUE_ALT'})

    def test_nonpositive_roi_stays_in_weekly_not_card(self):
        v=valued_rows();v['Push_Adjusted_ROI']=-.1
        out=self.assemble(valued=v)
        self.assertEqual(len(out.weekly),3);self.assertEqual(len(out.card),0)

    def test_audit_unavailable_is_not_neutral(self):
        pending=pd.DataFrame([{'Game':'Alpha at Beta','Model_Side':'Beta','Review_Class':'MATCHUP_SUPPORTED',
            'Phase1_Reason':'MODULE3_SUPPORT','Current_Market_Ready':True,'Audit_Ready':False,
            'Audit_Status':'AUDIT_UNAVAILABLE','Audit_Reason':'OPENER_UNAVAILABLE'}])
        result=assemble_handoff(DecisionBatch(pd.DataFrame(),pending),key_value=key_rows()).weekly.iloc[0]
        self.assertEqual((result.Market_Status,result.Audit_Status),('CURRENT_MARKET_READY','AUDIT_UNAVAILABLE'))
        self.assertEqual(result.Decision_Status,'')
        self.assertTrue(pd.isna(result.Market_Relationship));self.assertTrue(pd.isna(result.Open_Home_Spread))

    def test_missing_market_preserved_as_explicit_exclusion(self):
        absent=pd.DataFrame([{'Game':'Rutgers at Northwestern','Home_Team':'Northwestern','Away_Team':'Rutgers','game_id':99}])
        out=self.assemble(market_unavailable=absent).weekly
        self.assertEqual(set(out.Game),{'Alpha at Beta','Rutgers at Northwestern'})
        row=out[out.game_id.eq(99)].iloc[0]
        self.assertEqual(row.Market_Status,'MARKET_DATA_UNAVAILABLE')
        self.assertEqual(row.Audit_Status,'AUDIT_UNAVAILABLE')
        self.assertEqual(row.Decision_Status,'');self.assertTrue(pd.isna(row.Line))

    def test_only_market_unavailable_supported(self):
        out=assemble_handoff(pd.DataFrame(),market_unavailable=pd.DataFrame([{'Game':'A at B'}])).weekly
        self.assertEqual(out.Market_Status.iloc[0],'MARKET_DATA_UNAVAILABLE')

    def test_explicit_availability_overrides_no_inferred_opener(self):
        a=pd.DataFrame([{'Game':'Alpha at Beta','Current_Market_Ready':True,'Audit_Ready':False,'Audit_Reason':'OPENER_UNAVAILABLE'}])
        out=self.assemble(availability=a).weekly.iloc[0]
        self.assertEqual(out.Decision_Status,'CONFIRMED') # classification input preserved
        self.assertEqual(out.Audit_Status,'AUDIT_UNAVAILABLE')
        self.assertTrue(pd.isna(out.Open_Home_Spread))

    def test_price_free_probability_at_same_exact_line(self):
        from test_probability_roi import tiny_history
        p=candidate_probabilities(pd.DataFrame([{'Game':'Alpha at Beta','Team':'Beta','Home_Team':'Beta',
            'Line':-4.,'Candidate_Cushion':3.25}]),tiny_history())
        p=adjust_push_probabilities(p,tiny_history())
        row=self.assemble(probabilities=p).weekly.iloc[0]
        self.assertEqual(row.Model_Probability,p.Push_Adjusted_Win_Prob.iloc[0])
        self.assertTrue(pd.isna(row.Expected_ROI));self.assertTrue(pd.isna(row.American_Odds))

    def test_stable_schema_and_input_order_independence(self):
        v=valued_rows();a=self.assemble(valued=v).weekly
        b=self.assemble(valued=v.iloc[::-1]).weekly
        self.assertEqual(list(a),HANDOFF_COLUMNS);assert_frame_equal(a,b)

    def test_status_then_game_sort_is_not_bet_rank(self):
        a=final_rows();b=a.copy();b['Game']='Zulu at Omega';b['Decision_Status']='NEUTRAL_MARKET'
        c=a.copy();c['Game']='A at B';c['Decision_Status']='CONFIRMED'
        out=assemble_handoff(pd.concat([b,a,c])).weekly
        self.assertEqual(out.Game.tolist(),['A at B','Alpha at Beta','Zulu at Omega'])

    def test_no_unrequested_fields_leak(self):
        f=final_rows();f['TT_Expected_ROI']=9;f['Full_Kelly']=.1;f['Stake']=100
        out=assemble_handoff(f).weekly
        self.assertFalse(any(c.startswith('TT_') or any(t in c.lower() for t in ['kelly','stake','bankroll']) for c in out))

    def test_duplicate_final_and_price_keys_rejected(self):
        f=final_rows()
        with self.assertRaises(ValueError):assemble_handoff(pd.concat([f,f]))
        v=valued_rows()
        with self.assertRaises(ValueError):self.assemble(valued=pd.concat([v,v.iloc[:1]]))

    def test_orphan_and_wrong_side_price_rejected(self):
        for col,value in [('Game','Orphan'),('Team','Alpha'),('Decision_Status','NEUTRAL_MARKET')]:
            v=valued_rows();v[col]=value
            with self.assertRaises(ValueError):self.assemble(valued=v)

    def test_incomplete_probability_fails(self):
        v=valued_rows();v['Push_Adjusted_Loss_Prob']=.99
        with self.assertRaises(ValueError):self.assemble(valued=v)

    def test_staking_and_tts_not_required_for_assembly(self):
        self.assertEqual(len(self.assemble().weekly),1)

    def test_handoff_roi_status_uses_two_percent_not_three(self):
        self.assertEqual(pricing_status_from_roi(.02),'POSITIVE_EV')
        self.assertEqual(pricing_status_from_roi(.019),'THIN_POSITIVE_EV')

    def test_routes_can_contain_non_phase1_games(self):
        routes=final_rows()[['Game','M3_Support','M3_Conflict','Eligible_Market_Routes']]
        extra=routes.copy();extra['Game']='Other at Somewhere'
        out=assemble_handoff(final_rows(),routes=pd.concat([routes,extra]))
        self.assertEqual(out.weekly.Game.tolist(),['Alpha at Beta'])

    def test_price_free_wrong_line_or_side_is_rejected(self):
        from test_probability_roi import tiny_history
        p=candidate_probabilities(pd.DataFrame([{'Game':'Alpha at Beta','Team':'Beta','Home_Team':'Beta',
            'Line':-4.5,'Candidate_Cushion':2.75}]),tiny_history())
        with self.assertRaises(ValueError):self.assemble(probabilities=p)

    def test_pending_readiness_must_be_explicit_boolean(self):
        p=pd.DataFrame([{'Game':'Alpha at Beta','Model_Side':'Beta'}])
        with self.assertRaises(ValueError):assemble_handoff(DecisionBatch(pd.DataFrame(),p))
        p['Current_Market_Ready']='False';p['Audit_Ready']=False
        with self.assertRaises(ValueError):assemble_handoff(DecisionBatch(pd.DataFrame(),p))

    def test_current_missing_and_audit_missing_stay_distinct(self):
        p=pd.DataFrame([{'Game':'Alpha at Beta','Model_Side':'Beta','Current_Market_Ready':False,
            'Audit_Ready':False,'Audit_Reason':'CURRENT_RECORD_MISSING_OR_AMBIGUOUS'}])
        row=assemble_handoff(DecisionBatch(pd.DataFrame(),p),key_value=key_rows()).weekly.iloc[0]
        self.assertEqual(row.Market_Status,'MARKET_DATA_UNAVAILABLE')
        self.assertEqual(row.Audit_Status,'AUDIT_UNAVAILABLE')
        self.assertTrue(pd.isna(row.Line))

    def test_unavailable_market_cannot_receive_supplied_price(self):
        a=pd.DataFrame([{'Game':'Alpha at Beta','Current_Market_Ready':False,'Audit_Ready':False}])
        with self.assertRaises(ValueError):self.assemble(availability=a,valued=valued_rows())

    def test_assembly_does_not_modify_supplied_inputs(self):
        f,k,v=final_rows(),key_rows(),valued_rows();before=[x.copy(deep=True) for x in [f,k,v]]
        assemble_handoff(f,key_value=k,valued=v)
        for actual,expected in zip([f,k,v],before):assert_frame_equal(actual,expected)

    def test_empty_output_stable_schema(self):
        self.assertEqual(list(assemble_handoff(pd.DataFrame()).weekly),HANDOFF_COLUMNS)

    def test_module3_warning_text_exact(self):
        self.assertEqual(module3_context(pd.Series({'M3_Support':' A +LINE_YARDS ','M3_Conflict':' B +OAY_DAY '})),
                         'A +LINE_YARDS | CONFLICT: B +OAY_DAY')


class ExportTests(unittest.TestCase):
    def output(self):return assemble_handoff(final_rows(),key_value=key_rows(),valued=valued_rows())

    def test_csv_json_round_trip_and_text_sync(self):
        bundle=serialize_handoff(self.output(),'2026-11-07')
        csv=pd.read_csv(StringIO(bundle.csv),keep_default_na=False)
        payload=json.loads(bundle.json);js=pd.DataFrame(payload['rows'],columns=payload['columns'])
        for col in ['Expected_ROI','Model_Probability','Loss_Probability','American_Odds']:
            np.testing.assert_allclose(csv[col].astype(float),js[col].astype(float),rtol=1e-12,atol=1e-14)
        self.assertEqual(csv.Game.tolist(),js.Game.tolist())
        self.assertIn(bundle.csv,bundle.text)
        self.assertEqual(bundle.title,'11-07 CFB — CFB1');self.assertEqual(bundle.stem,'11-07_CFB_CFB1')

    def test_json_nulls_and_no_nonstandard_nan(self):
        b=serialize_handoff(assemble_handoff(final_rows()),'2027-01-02')
        obj=json.loads(b.json);self.assertIsNone(obj['rows'][0]['Expected_ROI'])
        self.assertNotIn(': NaN',b.json)

    def test_files_match_serialized_board(self):
        out=self.output();b=serialize_handoff(out,'2026-10-24')
        with TemporaryDirectory() as d:
            paths=export_handoff(out,'2026-10-24',d)
            self.assertEqual(paths['csv'].name,'10-24_CFB_CFB1.csv')
            for ext in ['csv','json','txt']:
                self.assertEqual(paths[ext].read_text(),{'csv':b.csv,'json':b.json,'txt':b.text}[ext])

    def test_serializer_rejects_infinity_and_never_fetches(self):
        out=self.output();out.weekly.loc[0,'Expected_ROI']=np.inf
        with self.assertRaises(ValueError):serialize_handoff(out,'2026-10-24')

    def test_schema_and_invalid_date_fail(self):
        with self.assertRaises(ValueError):serialize_handoff(pd.DataFrame(),'2026-10-24')
        with self.assertRaises(ValueError):serialize_handoff(self.output(),'10-24')


class ParityTests(unittest.TestCase):
    def test_old_cell45_exact_board_and_csv(self):
        final=final_rows();env={'df_final_decision':final.copy()};frozen('OLD CELL 45',env)
        actual=compact_final_board(final)
        assert_frame_equal(actual,env['df_gem_export']);self.assertEqual(actual.to_csv(index=False),env['gem_csv'])

    def test_61_61b_62_73_standard_branches(self):
        v=valued_rows();env={'df_ev':v.copy()}
        frozen('CELL 61',env)
        assert_frame_equal(priced_spread_handoff(v),env['df_cfb1_gem_handoff'])
        frozen('CELL 61B',env)
        assert_frame_equal(env['CFB1_FULL_CONTEXT_V1'],priced_spread_handoff(v))
        frozen('CELL 62',env)
        actual=spread_decision_card(v);assert_frame_equal(actual,env['CFB1_DECISION_CARD_V1'])
        ctx=context_for73(final_rows());env['CFB1_FULL_CONTEXT_FINAL']=ctx
        frozen('CELL 73',env)
        assert_frame_equal(architect_card(actual,ctx),env['CFB1_ARCHITECT_HANDOFF'])

    def test_66_67_context_enrichment_and_canonical_sync_projection(self):
        v=valued_rows();f=final_rows();k=key_rows();ret=pd.DataFrame([{'Game':'Alpha at Beta','Home_Team':'Beta',
            'Away_Team':'Alpha','Shrunk_Home_Spread_40':-7.25}])
        env={'df_gem_export':compact_final_board(f),'df_final_decision':f,
            'df_phase1_shrinkage':ret,'df_key_value':k,'df_ev':v,
            'CFB1_FULL_CONTEXT_V1':priced_spread_handoff(v),'CFB1_DECISION_CARD_V1':spread_decision_card(v)}
        frozen('CELL 66',env);frozen('CELL 67',env);frozen('CELL 73',env)
        out=assemble_handoff(f,key_value=k,retained=ret,valued=v)
        assert_frame_equal(out.card,env['CFB1_ARCHITECT_HANDOFF'])
        context=env['CFB1_FULL_CONTEXT_FINAL'];match=out.weekly.merge(context,on=['Game','Team','Sportsbook','Line','American_Odds'])
        np.testing.assert_allclose(match.Expected_ROI,match.Expected_ROI_Final)
        np.testing.assert_allclose(match.Retained_Model_Spread_x,match.Retained_Model_Spread_y)

    def test_saved_old45_csv_all_14_rows(self):
        from test_late_week_decisions import HistoricalTests
        HistoricalTests.setUpClass();f=HistoricalTests.final
        cp=json.loads((FIX/'handoff_notebook_checkpoint.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT/cp['notebook']).read_bytes()).hexdigest(),cp['sha256'])
        self.assertEqual(compact_final_board(f).to_csv(index=False),cp['compact_csv'])

    def test_saved_57a_values_feed_saved_standard_61_and_card_roles(self):
        cp=json.loads((FIX/'probability_notebook_checkpoint.json').read_text())
        saved=json.loads((FIX/'handoff_notebook_checkpoint.json').read_text())
        base=cp['samples']['CELL 57'][0];adjusted=cp['samples']['CELL 57A'][0]
        key=lambda r:tuple(r[c] for c in ['Game','Team','Sportsbook','Line','American_Odds'])
        lookup={key(r):r for r in base};rows=[]
        for r in adjusted:
            b=lookup[key(r)];row={**b,**r}
            for c in ['Push_Adjusted_Win_Prob','Push_Adjusted_Push_Prob','Push_Adjusted_Loss_Prob','Push_Adjusted_ROI','Break_Even_Prob']:
                row[c]=r[c]/100
            row['Market_Model_Spread']=next(x['Market_Model_Spread'] for x in cp['samples']['CELL 52'][0] if x['Game']==r['Game'])
            rows.append(row)
        v=pd.DataFrame(rows);table=priced_spread_handoff(v)
        # Saved CELL 61 shows only positive-ROI review, with truncated labels.
        expected=saved['tables']['CELL 61'][0]
        self.assertEqual(len(table[table.Expected_ROI_Final>0]),len(expected))
        actual=table[table.Expected_ROI_Final>0]
        for r in expected:
            candidates=actual[actual.Game.str.startswith(r['Game'].removesuffix('...')) & actual.Sportsbook.eq(r['Sportsbook']) & actual.American_Odds.eq(r['American_Odds'])]
            candidates=candidates[candidates.Bet_Label.eq(r['Bet_Label'])]
            self.assertEqual(len(candidates),1)
            a=candidates.iloc[0]
            self.assertAlmostEqual(a.Model_Probability*100,float(str(r['Model_Probability']).rstrip('%')),delta=.000001)
            self.assertEqual(a.Pricing_Status,r['Pricing_Status'])
        card=spread_decision_card(v)
        expect_card=saved['tables']['CELL 62'][0]
        self.assertEqual(len(card),len(expect_card))
        for r in expect_card:
            match=card[card.Game.str.startswith(r['Game'].removesuffix('...')) & card.Card_Role.eq(r['Card_Role'])]
            self.assertEqual(len(match),1)
            self.assertEqual(match.Bet_Label.iloc[0],r['Bet_Label'])


class OfflinePipelineTests(unittest.TestCase):
    def test_raw_features_to_handoff_without_notebook_state_or_network(self):
        from cfb1.cfbd_features import build_feature_tables,merge_master_features
        from cfb1.bcf import parse_bcf_csv,normalize_bcf,merge_bcf
        from cfb1.model_signals import apply_epa_trigger,apply_fei_model,apply_fei_market_edges
        from cfb1.module3 import (apply_market_favorites,apply_havoc_trap,refresh_master_lineyards,
            apply_lineyards_push,apply_explosiveness_fraud,apply_oay_day_edge)
        from cfb1.convergence import corrected_convergence
        from cfb1.routing import route_markets,apply_large_spread_routing,separate_evidence
        from cfb1.spread_structure import classify_spread_structure,classify_large_spreads
        from cfb1.phase1 import build_phase1_shortlist,build_phase1_review
        from cfb1.probability import cover_probability_board
        from cfb1.spread_history import build_spread_history
        # Only production imports and explicit inputs: no notebook execution/test pipeline helpers.
        with patch('socket.socket',side_effect=AssertionError('Network forbidden in offline integration')):
            features=build_feature_tables(json.loads((FIX/'cfbd_feature_plays.json').read_text()),
                json.loads((FIX/'cfbd_feature_advanced.json').read_text()))
            self.assertTrue(features.valid)
            market=pd.DataFrame([
                {'game_id':1,'Home_Team':'A home','Away_Team':'B away','Home_CFBD_Name':'A','Away_CFBD_Name':'B',
                 'DK_Spread':-3.,'FD_Spread':-3.,'DK_Total':50.,'FD_Total':50.},
                {'game_id':2,'Home_Team':'B home','Away_Team':'A away','Home_CFBD_Name':'B','Away_CFBD_Name':'A',
                 'DK_Spread':3.,'FD_Spread':3.,'DK_Total':50.,'FD_Total':50.}])
            master=merge_master_features(market,features)
            bcf_text='\n'.join((FIX/'bcf_segment_sample.csv').read_text().splitlines()[:3])
            bcf=normalize_bcf(parse_bcf_csv(bcf_text),features.df_cfbd.team,market)
            master=apply_fei_market_edges(apply_fei_model(merge_bcf(apply_epa_trigger(master),bcf)))
            master=apply_havoc_trap(apply_market_favorites(master))
            master=refresh_master_lineyards(master,features.df_cfbd,expected_games=2)
            master=apply_oay_day_edge(apply_explosiveness_fraud(apply_lineyards_push(master)))
            conv=corrected_convergence(master);routes=route_markets(conv)
            structure,_=classify_spread_structure(master,routes)
            large,_=classify_large_spreads(structure,routes)
            routes=apply_large_spread_routing(routes,large)
            phase=build_phase1_shortlist(large,separate_evidence(routes))
            review=build_phase1_review(phase.candidates)
            self.assertEqual(len(review),2)
            observations=market[['Home_Team','Away_Team']].copy()
            observations['Game']=observations.Away_Team+' at '+observations.Home_Team
            observations['Open_Home_Spread']=market.DK_Spread
            observations['Current_Home_Spread']=[-4.,4.]
            audit=audit_spread_movement(observations.to_csv(index=False),review)
            final=build_final_decisions(review,routes,audit)
            retained=fit_retained_lines(phase.master,review)
            keys=model_side_line_value(retained.phase1,final)
            raw=json.loads((FIX/'spread_calibration_controlled.json').read_text())
            history=build_spread_history({int(k):v for k,v in raw.items()})
            history,board=cover_probability_board(history,keys)
            self.assertEqual(len(board),2)
            samples=pd.DataFrame([{'Game':r.Game,'Team':r.Model_Side,'Home_Team':r.Home_Team,
                'Line':r.Market_Model_Spread,'Candidate_Cushion':r.Model_Cushion_Points,
                'Market_Model_Spread':r.Market_Model_Spread,'Decision_Status':r.Decision_Status,
                'Key_Tradeoff':''} for _,r in keys.iterrows()])
            probs=adjust_push_probabilities(candidate_probabilities(samples,history),history)
            prices=samples.iloc[:1].copy();prices['American_Odds']=-110;prices['Sportsbook']='OFFLINE_SUPPLIED'
            valued=value_push_adjusted_spreads(value_supplied_spreads(prices,history),history)
            result=assemble_handoff(final,routes=routes,retained=retained.phase1,key_value=keys,
                probabilities=probs,valued=valued)
            self.assertEqual(len(result.weekly),2)
            self.assertEqual(result.weekly.American_Odds.notna().sum(),1)
            self.assertEqual(result.weekly.Model_Probability.notna().sum(),2)
            self.assertEqual(set(result.weekly.Decision_Status),{'CONFIRMED'})
            self.assertEqual(set(result.weekly.Game),set(final.Game))
            with TemporaryDirectory() as d:
                files=export_handoff(result,'2026-10-24',d)
                self.assertEqual(len(json.loads(files['json'].read_text())['rows']),2)
