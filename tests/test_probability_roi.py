"""Offline spread calibration, supplied-price economics, and literal notebook parity."""
import ast
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from cfb1.probability import (fit_retained_lines, model_side_line_value, spread_bucket,
    empirical_probability, cover_probability_board, candidate_probabilities,
    adjust_push_probabilities)
from cfb1.spread_history import build_spread_history
from cfb1.valuation import (profit_multiple, break_even_prob, shortlist_supplied_spreads,
    value_supplied_spreads, value_push_adjusted_spreads)

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures'


def history_payloads():
    return {int(k): v for k, v in json.loads((FIX/'spread_calibration_controlled.json').read_text()).items()}


def controlled():
    x = np.array([-.3, -.2, -.1, .1, .2, .3])
    master = pd.DataFrame({'Home_Team': [f'Home{i}' for i in range(6)],
        'Away_Team': [f'Away{i}' for i in range(6)], 'Net_EPA_Edge_Home': x,
        'DK_Spread': -2-10*x, 'FD_Spread': -2-10*x,
        'FEI_Model_Home_Spread': [4., 2., 0., -2., -4., -6.]})
    review = pd.DataFrame({'Game': master.Away_Team+' at '+master.Home_Team,
        'Model_Side': master.Home_Team, 'Review_Class': 'MATCHUP_SUPPORTED'})
    final = pd.DataFrame({'Game': review.Game, 'Current_Home_Spread': master.DK_Spread,
        'Decision_Status': 'CONFIRMED', 'Eligible_Market_Routes': 'FULL_GAME_SPREAD'})
    return master, review, final


def candidate(**overrides):
    row = {'Game': 'Away at Home', 'Home_Team': 'Home', 'Team': 'Home',
        'Sportsbook': 'Supplied', 'Market_Type': 'FULL_GAME_SPREAD', 'Line': -3.,
        'American_Odds': -110, 'Candidate_Cushion': 0., 'Key_Tradeoff': '',
        'Decision_Status': 'CONFIRMED'}
    row.update(overrides)
    return pd.DataFrame([row])


def tiny_history(errors=(-2., 0., 2.)):
    return pd.DataFrame({'Spread_Error': errors, 'Closing_Home_Spread': [-3.]*len(errors),
                         'Actual_Home_Margin': np.array(errors)+3})


def literal_cell(label, env, payloads=None):
    """Execute actual frozen source; only HTTP replaced with offline response stub."""
    if label not in ['47', '48', '51', '52', '55', '57', '57A']:
        raise ValueError('Outside this migration')
    notebook = json.loads((ROOT/'legacy/CFB1_Colab_Reference.ipynb').read_text())
    source = next(''.join(c['source']) for c in notebook['cells']
        if any(line.startswith('# CELL '+label+' —') for line in c['source']))
    env.setdefault('display', lambda *args: None)
    env.setdefault('CFBD_API_KEY', 'offline-fixture-only')
    calls = []
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(status_code=200, json=lambda: deepcopy(payloads[kwargs['params']['year']]))
    with patch.dict('sys.modules', {'requests': SimpleNamespace(get=get)}), redirect_stdout(StringIO()):
        exec(compile(ast.parse(source), 'frozen_CELL_'+label, 'exec'), env)
    return calls


class RetainedLineTests(unittest.TestCase):
    def test_fit_and_equal_blend(self):
        m, r, _ = controlled(); out = fit_retained_lines(m, r)
        self.assertAlmostEqual(out.beta, 10); self.assertAlmostEqual(out.intercept, 2)
        np.testing.assert_allclose(out.full_slate.Blended_Home_Spread_Raw,
            .5*m.DK_Spread+.5*m.FEI_Model_Home_Spread)

    def test_all_retention_levels(self):
        m, r, _ = controlled(); out = fit_retained_lines(m, r).phase1
        for n in [25, 40, 50, 60]:
            np.testing.assert_allclose(out[f'Shrunk_Home_Spread_{n}'],
                out.Consensus_Home_Spread-(n/100)*out.Blended_Edge_Home_Raw)

    def test_favorite_underdog_even(self):
        m, r, f = controlled(); out = fit_retained_lines(m, r)
        self.assertGreater(out.full_slate.Shrunk_Home_Spread_40.iloc[0], 0)
        self.assertLess(out.full_slate.Shrunk_Home_Spread_40.iloc[-1], 0)
        m.loc[2, ['DK_Spread', 'FD_Spread', 'FEI_Model_Home_Spread']] = 0
        # Explicit symmetric fit gives a neutral blended line at x=0.
        m.Net_EPA_Edge_Home = [-2., -1., 0., 0., 1., 2.]
        m.DK_Spread = m.FD_Spread = -m.Net_EPA_Edge_Home
        m.FEI_Model_Home_Spread = -m.Net_EPA_Edge_Home
        self.assertAlmostEqual(fit_retained_lines(m, r).phase1.Shrunk_Home_Spread_40.iloc[2], 0)

    def test_single_book_consensus_and_null_fit_rows(self):
        m, r, _ = controlled(); m.loc[0,'FD_Spread'] = np.nan
        m.loc[1,'Net_EPA_Edge_Home'] = np.nan
        out = fit_retained_lines(m,r)
        self.assertAlmostEqual(out.beta,10)
        self.assertEqual(out.full_slate.Consensus_Home_Spread.iloc[0],m.DK_Spread.iloc[0])
        self.assertTrue(pd.isna(out.full_slate.Shrunk_Home_Spread_40.iloc[1]))

    def test_phase1_is_subset_full_slate_fit(self):
        m,r,_=controlled(); out=fit_retained_lines(m,r.iloc[:2])
        self.assertEqual((len(out.full_slate),len(out.phase1)),(6,2))
        self.assertAlmostEqual(out.beta,10)

    def test_missing_column_fails(self):
        m,r,_=controlled()
        with self.assertRaises(ValueError): fit_retained_lines(m.drop(columns='DK_Spread'),r)

    def test_model_side_orientation_and_rounding(self):
        m,r,f=controlled(); p=fit_retained_lines(m,r).phase1
        p.loc[0,'Model_Side']=p.Away_Team.iloc[0]
        p.loc[0,'Shrunk_Home_Spread_40']=1.234567
        k=model_side_line_value(p,f)
        self.assertEqual(k.Retained_Model_Spread.iloc[0],-1.234567)
        self.assertEqual(k.Model_Cushion_Points.iloc[0],round(-f.Current_Home_Spread.iloc[0]+1.234567,2))

    def test_strict_key_barriers_and_next_key(self):
        m,r,f=controlled(); p=fit_retained_lines(m,r).phase1
        p.loc[0,'Shrunk_Home_Spread_40']=-7; f.loc[0,'Current_Home_Spread']=-3
        k=model_side_line_value(p,f)
        self.assertEqual(k.Keys_Between_Market_And_Model.iloc[0],'')
        self.assertEqual(k.Next_Adverse_Key.iloc[0],7)
        p.loc[0,'Shrunk_Home_Spread_40']=-7.1
        self.assertEqual(model_side_line_value(p,f).Keys_Between_Market_And_Model.iloc[0],'7')

    def test_invalid_side_check_and_zero_cushion(self):
        m,r,f=controlled(); p=fit_retained_lines(m,r).phase1
        p.loc[0,'Model_Side']='unknown'; p.loc[1,'Shrunk_Home_Spread_40']=f.Current_Home_Spread.iloc[1]
        k=model_side_line_value(p,f)
        self.assertEqual(k.Line_Value_Status.iloc[0],'CHECK')
        self.assertEqual(k.Line_Value_Status.iloc[1],'NO_RETAINED_MODEL_EDGE')

    def test_final_duplicate_game_rejected(self):
        m,r,f=controlled()
        with self.assertRaises(pd.errors.MergeError):
            model_side_line_value(fit_retained_lines(m,r).phase1,pd.concat([f,f.iloc[:1]]))


class CalibrationTests(unittest.TestCase):
    def test_fixed_year_boundary(self):
        p=history_payloads(); p[2026]=deepcopy(p[2025]); h=build_spread_history(p)
        self.assertEqual(set(h.Season),set(range(2021,2026))); self.assertEqual(len(h),20)
        del p[2021]
        with self.assertRaises(ValueError): build_spread_history(p)

    def test_provider_priority_and_null_fallback(self):
        p=history_payloads(); g=p[2021][0]
        g['lines']=[{'provider':'Bovada','spread':9}, {'provider':'ESPN Bet','spread':8},
                    {'provider':'DraftKings','spread':None}]
        self.assertEqual(build_spread_history(p).iloc[0].Provider,'ESPN Bet')
        g['lines'].append({'provider':'DraftKings','spread':7})
        self.assertEqual(build_spread_history(p).iloc[0].Closing_Home_Spread,7)

    def test_fbs_completed_and_supported_line_only(self):
        p=history_payloads(); p[2021][0]['homeClassification']='fcs'
        p[2021][1]['awayScore']=None; p[2021][2]['lines']=[]
        self.assertEqual(len(build_spread_history(p)),17)

    def test_duplicates_preserved_and_errors_exact(self):
        p=history_payloads(); p[2021].append(deepcopy(p[2021][0])); h=build_spread_history(p)
        self.assertEqual(len(h),21); self.assertTrue(h.Game_ID.duplicated().any())
        np.testing.assert_allclose(h.Spread_Error,h.Actual_Home_Margin+h.Closing_Home_Spread)
        self.assertEqual(set(h.ATS_Result),{'HOME_COVER','AWAY_COVER','PUSH'})

    def test_bucket_boundaries(self):
        for x,label in [(0,'UNDER_3'),(2.5,'UNDER_3'),(3,'3_TO_6.5'),(7,'7_TO_9.5'),
            (10,'10_TO_13.5'),(14,'14_TO_16.5'),(17,'17_TO_20.5'),(21,'21_PLUS')]:
            with self.subTest(x=x): self.assertEqual(spread_bucket(x),label)

    def test_empirical_win_push_loss_and_away_orientation(self):
        e=pd.Series([-2.,0.,2.]); self.assertEqual(empirical_probability(0,True,e),(1/3,1/3,1/3))
        self.assertEqual(empirical_probability(1,False,e),(2/3,0,1/3))

    def test_cover_monotonicity_both_orientations(self):
        for side in [True,False]:
            wins=[empirical_probability(c,side,pd.Series([-2.,0.,2.]))[0] for c in [-3,-2,-1,0,1,2,3]]
            self.assertEqual(wins,sorted(wins))

    def test_null_cushion_empty_history_nan(self):
        self.assertTrue(all(pd.isna(x) for x in empirical_probability(np.nan,True,pd.Series([1.]))))
        self.assertTrue(all(pd.isna(x) for x in empirical_probability(0,True,pd.Series([],dtype=float))))

    def test_board_minimum_and_signed_spreads(self):
        m,r,f=controlled(); k=model_side_line_value(fit_retained_lines(m,r).phase1,f)
        h,b=cover_probability_board(build_spread_history(history_payloads()),k)
        np.testing.assert_allclose(b.CFB1_Cover_Prob_V1,b[['Global_Cover_Prob','Bucket_Cover_Prob']].min(axis=1))
        self.assertEqual(h.Spread_Bucket.iloc[0],h.Spread_Bucket.iloc[1])

    def test_global_default_without_bucket_metadata(self):
        row=candidate_probabilities(candidate(),tiny_history()).iloc[0]
        self.assertEqual(row.Probability_Source,'GLOBAL')
        self.assertEqual(row.CFB1_Win_Prob,1/3)

    def test_bucket_threshold_uses_supplied_count(self):
        h=tiny_history(); h['Spread_Bucket']=['a','b','b']
        for n,source,w in [(299,'GLOBAL',1/3),(300,'SPREAD_BUCKET',0)]:
            out=candidate_probabilities(candidate(Spread_Bucket='a',Historical_Bucket_N=n),h).iloc[0]
            self.assertEqual(out.Probability_Source,source); self.assertEqual(out.CFB1_Win_Prob,w)

    def test_missing_bucket_falls_back(self):
        out=candidate_probabilities(candidate(Spread_Bucket='missing',Historical_Bucket_N=400),tiny_history())
        self.assertEqual(out.Probability_Source.iloc[0],'GLOBAL')

    def test_null_global_errors_dropped(self):
        out=candidate_probabilities(candidate(),tiny_history((-2.,0.,2.,np.nan)))
        self.assertEqual(out.CFB1_Push_Prob.iloc[0],1/3)

    def test_null_bucket_error_fails_sum_guard(self):
        h=tiny_history((-2.,0.,np.nan)); h['Spread_Bucket']='a'
        with self.assertRaises(ValueError):
            candidate_probabilities(candidate(Spread_Bucket='a',Historical_Bucket_N=300),h)

    def test_missing_home_fails(self):
        with self.assertRaises(KeyError): candidate_probabilities(candidate().drop(columns='Home_Team'),tiny_history())

    def test_missing_cushion_empty_history_fail_guard(self):
        for c,h in [(candidate(Candidate_Cushion=np.nan),tiny_history()),(candidate(),tiny_history(()))]:
            with self.assertRaises(ValueError): candidate_probabilities(c,h)


class EconomicsTests(unittest.TestCase):
    def test_negative_positive_even_odds(self):
        for odds,payout,be in [(-110,100/110,110/210),(150,1.5,.4),(100,1.,.5),(-100,1.,.5)]:
            with self.subTest(odds=odds):
                self.assertAlmostEqual(profit_multiple(odds),payout)
                self.assertAlmostEqual(break_even_prob(odds),be)

    def test_invalid_odds_literal_legacy_behavior(self):
        with self.assertRaises(ZeroDivisionError): profit_multiple(0)
        self.assertEqual(break_even_prob(0),1)
        for fn in [profit_multiple,break_even_prob]:
            with self.assertRaises(ValueError): fn('bad')
            self.assertTrue(pd.isna(fn(np.nan)))

    def test_positive_negative_and_zero_ev(self):
        for odds,cushion,sign in [(100,1,1),(100,-1,-1),(100,0,0)]:
            out=value_supplied_spreads(candidate(American_Odds=odds,Candidate_Cushion=cushion),tiny_history()).iloc[0]
            self.assertEqual(np.sign(out.Expected_ROI),sign)
            self.assertEqual(out.Expected_ROI,out.EV_Per_Dollar)

    def test_push_refunds_are_unconditional(self):
        out=value_supplied_spreads(candidate(American_Odds=100),tiny_history()).iloc[0]
        self.assertEqual(out.CFB1_Push_Prob,1/3); self.assertEqual(out.Expected_ROI,0)
        self.assertAlmostEqual(out.Probability_Edge,1/3-.5)

    def test_ev_threshold_classifications(self):
        # With one certain win, positive odds/100 equals ROI exactly.
        for odds,status in [(5,'STRONG_PRICE_EDGE'),(3,'POSITIVE_EV'),(1,'THIN_POSITIVE_EV')]:
            row=value_supplied_spreads(candidate(American_Odds=odds),tiny_history((1.,))).iloc[0]
            self.assertEqual(row.EV_Status,status)
        self.assertEqual(value_supplied_spreads(candidate(American_Odds=100),tiny_history()).EV_Status.iloc[0],'NON_POSITIVE_EV')

    def test_nan_odds_no_ev(self):
        self.assertEqual(value_supplied_spreads(candidate(American_Odds=np.nan),tiny_history()).EV_Status.iloc[0],'NO_EV')

    def test_warnings_and_no_staking_columns(self):
        c=candidate(Key_Tradeoff='OFF_KEY_3',Decision_Status='MARKET_CONFLICT',Full_Kelly=.2)
        out=value_supplied_spreads(c,tiny_history())
        self.assertEqual(out.Decision_Warning.iloc[0],'OFF_KEY_3 | MARKET_CONFLICT')
        self.assertNotIn('Full_Kelly',out.columns)

    def test_missing_supplied_price_fails(self):
        with self.assertRaises(KeyError): value_supplied_spreads(candidate().drop(columns='American_Odds'),tiny_history())

    def test_shortlist_keeps_best_supplied_price(self):
        m,r,f=controlled(); k=model_side_line_value(fit_retained_lines(m,r).phase1,f)
        offers=pd.concat([candidate(Game=k.Game.iloc[0],Home_Team=k.Home_Team.iloc[0],Team=k.Model_Side.iloc[0],
            Line=k.Retained_Model_Spread.iloc[0]+.5,American_Odds=o) for o in [-110,-105]])
        out=shortlist_supplied_spreads(offers,k,build_spread_history(history_payloads()))
        self.assertEqual(len(out),1); self.assertEqual(out.American_Odds.iloc[0],-105)
        self.assertNotIn('Historical_Bucket_N',out.columns)

    def shortlist_one(self, market=-3., retained=-8., line=-3.5, odds=-110):
        k=pd.DataFrame([{'Game':'Away at Home','Model_Side':'Home','Home_Team':'Home',
            'Market_Model_Spread':market,'Retained_Model_Spread':retained,
            'Line_Value_Status':'EDGE_WITH_KEY_BARRIER','Decision_Status':'CONFIRMED',
            'Eligible_Market_Routes':'FULL_GAME_SPREAD'}])
        offer=candidate(Line=line,American_Odds=odds).drop(columns='Decision_Status')
        return shortlist_supplied_spreads(offer,k,build_spread_history(history_payloads()))

    def test_key_tradeoff_off_cross_land_and_positive_orientation(self):
        for market,line,label in [(-3.,-3.5,'OFF_KEY_3'),(-2.5,-7.5,'CROSSES_3_7'),
                                  (-2.5,-7.,'CROSSES_3'),(-6.5,-7.,'LANDS_ON_KEY_7')]:
            with self.subTest(market=market,line=line):
                self.assertEqual(self.shortlist_one(market=market,line=line).Key_Tradeoff.iloc[0],label)
        self.assertEqual(self.shortlist_one(market=3,retained=-1,line=3.5).Key_Tradeoff.iloc[0],'')

    def test_shortlist_inclusive_odds_and_cushion_boundaries(self):
        for odds in [-250,300]:
            out=self.shortlist_one(retained=-3.,line=-3.5,odds=odds)
            self.assertEqual(len(out),1);self.assertEqual(out.Candidate_Cushion.iloc[0],-.5)

    def test_full_pipeline_has_global_source_without_metadata(self):
        h=build_spread_history(history_payloads())
        short=self.shortlist_one()
        self.assertNotIn('Spread_Bucket',short.columns)
        self.assertEqual(value_supplied_spreads(short,h).Probability_Source.iloc[0],'GLOBAL')

    def test_caller_dataframes_not_mutated(self):
        c=candidate();h=tiny_history();before_c=c.copy(deep=True);before_h=h.copy(deep=True)
        v=value_supplied_spreads(c,h);value_push_adjusted_spreads(v,h)
        assert_frame_equal(c,before_c);assert_frame_equal(h,before_h)

    def test_shortlist_filters_side_route_type_odds_and_cushion(self):
        m,r,f=controlled(); k=model_side_line_value(fit_retained_lines(m,r).phase1,f)
        base=candidate(Game=k.Game.iloc[0],Home_Team=k.Home_Team.iloc[0],Team=k.Model_Side.iloc[0],
                       Line=k.Retained_Model_Spread.iloc[0])
        offers=[base]
        for field,value in [('Team','other'),('Market_Type','TOTAL'),('American_Odds',-251),
                            ('American_Odds',301),('Line',k.Retained_Model_Spread.iloc[0]-.51)]:
            bad=base.copy();bad[field]=value;offers.append(bad)
        out=shortlist_supplied_spreads(pd.concat(offers),k,build_spread_history(history_payloads()))
        self.assertEqual(len(out),1)


class PushTests(unittest.TestCase):
    def valued(self,**kwargs):
        return value_supplied_spreads(candidate(**kwargs),tiny_history())

    def test_half_point_push_zero_renormalizes(self):
        out=value_push_adjusted_spreads(self.valued(Line=-3.5),tiny_history()).iloc[0]
        self.assertEqual(out.Historical_Push_N,0);self.assertEqual(out.Push_Adjusted_Push_Prob,0)
        self.assertEqual(out.Push_Adjusted_Win_Prob,.5);self.assertEqual(out.Push_Adjusted_Loss_Prob,.5)

    def test_integer_key_push_mass_and_roi(self):
        out=value_push_adjusted_spreads(self.valued(Line=-3),tiny_history()).iloc[0]
        self.assertEqual(out.Historical_Push_N,3);self.assertEqual(out.Historical_Push_Prob,1/3)
        self.assertAlmostEqual(out.Push_Adjusted_ROI,(1/3)*(100/110)-1/3)
        self.assertAlmostEqual(out.Push_Adjusted_Win_Prob+out.Push_Adjusted_Push_Prob+out.Push_Adjusted_Loss_Prob,1)

    def test_inclusive_one_point_comparable_window(self):
        h=pd.DataFrame({'Closing_Home_Spread':[-2,-4,-4.01], 'Actual_Home_Margin':[3,3,3]})
        out=adjust_push_probabilities(self.valued(),h).iloc[0]
        self.assertEqual((out.Historical_Push_N,out.Historical_Push_Prob),(2,1))

    def test_literal_abs_line_push_orientation_preserved(self):
        h=pd.DataFrame({'Closing_Home_Spread':[-7,7,7], 'Actual_Home_Margin':[7,-7,-7]})
        for line in [-7,7]:
            for team,p in [('Home',1/3),('Away',2/3)]:
                row=adjust_push_probabilities(self.valued(Line=line,Team=team),h).iloc[0]
                self.assertEqual(row.Historical_Push_Prob,p)

    def test_no_comparables_zero_mass(self):
        row=adjust_push_probabilities(self.valued(Line=-100),tiny_history()).iloc[0]
        self.assertEqual((row.Historical_Push_Prob,row.Historical_Push_N),(0,0))

    def test_all_push_base_fails_guard(self):
        v=self.valued();v['CFB1_Win_Prob']=0.;v['CFB1_Loss_Prob']=0.
        with self.assertRaises(ValueError): adjust_push_probabilities(v,tiny_history())

    def test_ev_status_preserved_after_adjustment(self):
        v=self.valued(Line=-3.5);v['EV_Status']='BASE_STATUS'
        self.assertEqual(value_push_adjusted_spreads(v,tiny_history()).EV_Status.iloc[0],'BASE_STATUS')


class LiteralParityTests(unittest.TestCase):
    def test_retained_and_line_value_cells_47_48(self):
        m,r,f=controlled();env={'df_master_bcf':m.copy(),'df_phase1_review':r.copy(),'df_final_decision':f.copy()}
        literal_cell('47',env); actual=fit_retained_lines(m,r)
        assert_frame_equal(actual.full_slate,env['df_prob_model'])
        assert_frame_equal(actual.phase1,env['df_phase1_shrinkage'])
        literal_cell('48',env)
        assert_frame_equal(model_side_line_value(actual.phase1,f),env['df_key_value'])

    def test_cell51_normalization_with_stubbed_http(self):
        payloads=history_payloads();env={};calls=literal_cell('51',env,payloads)
        self.assertEqual(len(calls),5)
        self.assertEqual([c[1]['params'] for c in calls],[{'year':y,'seasonType':'regular'} for y in range(2021,2026)])
        assert_frame_equal(build_spread_history(payloads),env['df_hist_spread'])

    def test_cell52_board(self):
        m,r,f=controlled();k=model_side_line_value(fit_retained_lines(m,r).phase1,f)
        h=build_spread_history(history_payloads());env={'df_hist_spread':h.copy(),'df_key_value':k.copy()}
        literal_cell('52',env); actual_h,actual=cover_probability_board(h,k)
        assert_frame_equal(actual_h,env['df_hist_spread']);assert_frame_equal(actual,env['df_cover_prob'])

    def test_cell55_shortlisting(self):
        m,r,f=controlled();k=model_side_line_value(fit_retained_lines(m,r).phase1,f)
        offers=pd.concat([candidate(Game=row.Game,Home_Team=row.Home_Team,Team=row.Model_Side,
            Line=row.Retained_Model_Spread+.5) for _,row in k.iterrows()],ignore_index=True)
        h=build_spread_history(history_payloads());env={'df_auto_pricing':offers.drop(columns='Decision_Status').copy(),'df_key_value':k.copy(),'df_hist_spread':h.copy()}
        literal_cell('55',env)
        assert_frame_equal(shortlist_supplied_spreads(offers.drop(columns='Decision_Status'),k,h),env['df_spread_shortlist'])

    def test_cell57_global_and_bucket_and_57a(self):
        h=tiny_history();h['Spread_Bucket']=['a','b','b']
        c=pd.concat([candidate(),candidate(Team='Away',Line=3.5,Spread_Bucket='a',Historical_Bucket_N=300,
                        Key_Tradeoff='OFF_KEY_3',Decision_Status='MARKET_CONFLICT')],ignore_index=True)
        env={'df_spread_shortlist':c.copy(),'df_hist_spread':h.copy(),'global_errors':h.Spread_Error.dropna().astype(float)}
        literal_cell('57',env);v=value_supplied_spreads(c,h)
        assert_frame_equal(v,env['df_ev'])
        literal_cell('57A',env)
        assert_frame_equal(value_push_adjusted_spreads(v,h),env['df_ev'])


class SavedCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp=json.loads((FIX/'probability_notebook_checkpoint.json').read_text())

    def test_frozen_notebook_hash_and_history_limit(self):
        self.assertEqual(hashlib.sha256((ROOT/self.cp['notebook']).read_bytes()).hexdigest(),self.cp['sha256'])
        self.assertIn('3730',self.cp['calibration_note'])

    def test_saved_history_sample_errors_and_counts(self):
        tables=self.cp['samples']['CELL 51']
        self.assertEqual(sum(r['Games'] for r in tables[0]),3730)
        for r in tables[1]:
            self.assertAlmostEqual(r['Spread_Error'],r['Actual_Home_Margin']+r['Closing_Home_Spread'])

    def test_saved_cover_board_conservative_minimum(self):
        rows=self.cp['samples']['CELL 52'][0]
        self.assertEqual(len(rows),14)
        for r in rows:
            self.assertEqual(r['CFB1_Cover_Prob_V1'],min(r['Global_Cover_Prob'],r['Bucket_Cover_Prob']))

    def test_all_47_saved_base_economics_at_display_precision(self):
        rows=self.cp['samples']['CELL 57'][0];self.assertEqual(len(rows),47)
        for r in rows:
            with self.subTest(game=r['Game'],line=r['Line']):
                self.assertAlmostEqual(break_even_prob(r['American_Odds']),r['Break_Even_Prob']/100,delta=.000050001)
                roi=r['CFB1_Win_Prob']/100*profit_multiple(r['American_Odds'])-r['CFB1_Loss_Prob']/100
                self.assertAlmostEqual(roi,r['Expected_ROI']/100,delta=.0003)
                self.assertAlmostEqual((r['CFB1_Win_Prob']+r['CFB1_Push_Prob']+r['CFB1_Loss_Prob'])/100,1,delta=.00015)

    def test_all_47_saved_adjusted_economics_and_redistribution(self):
        base=self.cp['samples']['CELL 57'][0];adj=self.cp['samples']['CELL 57A'][0]
        key=lambda r:tuple(r[f] for f in ['Game','Team','Sportsbook','Line','American_Odds'])
        lookup={key(r):r for r in base};self.assertEqual(len(adj),47)
        for r in adj:
            b=lookup[key(r)];h=r['Historical_Push_Prob']/100
            share=b['CFB1_Win_Prob']/(b['CFB1_Win_Prob']+b['CFB1_Loss_Prob'])
            self.assertAlmostEqual(share*(1-h),r['Push_Adjusted_Win_Prob']/100,delta=.00016)
            roi=r['Push_Adjusted_Win_Prob']/100*profit_multiple(r['American_Odds'])-r['Push_Adjusted_Loss_Prob']/100
            self.assertAlmostEqual(roi,r['Push_Adjusted_ROI']/100,delta=.0003)
        pushes=[r for r in adj if r['Historical_Push_Prob']>0]
        self.assertEqual({(r['Line'],r['Historical_Push_N']) for r in pushes},{(-10.,356),(-3.,824)})

    def test_historical_full_slate_identical_input_fit_parity(self):
        from test_routing_phase1 import historical_inputs,pipeline
        master,conv=historical_inputs();review=pipeline(master,conv)[8]
        actual=fit_retained_lines(master,review)
        env={'df_master_bcf':master.copy(),'df_phase1_review':review.copy()}
        literal_cell('47',env)
        assert_frame_equal(actual.full_slate,env['df_prob_model'])
        self.assertEqual((len(actual.full_slate),len(actual.phase1)),(57,14))
        # Saved historical values are comparison evidence, not replacement inputs.
        saved=self.cp['samples']['CELL 47'][0]
        deltas={r['Game']:actual.phase1.set_index('Game').loc[r['Game'],'Shrunk_Home_Spread_40']
                -r['Shrunk_Home_Spread_40'] for r in saved}
        self.assertEqual(sum(abs(d)>.005001 for d in deltas.values()),3)
        self.assertAlmostEqual(deltas['James Madison Dukes at Georgia Southern Eagles'],.03204983808113049)

    def test_production_modules_have_no_price_acquisition_or_staking_calculation(self):
        for module in ['probability.py','valuation.py','spread_history.py']:
            tree=ast.parse((ROOT/'src/cfb1'/module).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    self.assertTrue(all(n.name in {'pandas','numpy'} for n in node.names))
                if isinstance(node,ast.ImportFrom):
                    self.assertIn(node.module,{'dataclasses','cfb1.probability'})
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    self.assertFalse(any(word in node.name.lower() for word in ['kelly','stake','fetch','request']))

    def test_saved_48_from_archived_retained_input(self):
        from test_routing_phase1 import historical_inputs,pipeline
        from cfb1.market_audit import audit_spread_movement
        from cfb1.final_decision import build_final_decisions
        master,conv=historical_inputs();p=pipeline(master,conv);review,routes=p[8],p[5]
        audit=audit_spread_movement((FIX/'late_week_notebook_synthetic.csv').read_text(),review)
        final=build_final_decisions(review,routes,audit)
        inputs=[]
        for r in self.cp['samples']['CELL 52'][0]:
            away,home=r['Game'].split(' at ')
            inputs.append({'Game':r['Game'],'Model_Side':r['Model_Side'],'Home_Team':home,'Away_Team':away,
                'Shrunk_Home_Spread_40':r['Retained_Model_Spread']*(1 if r['Model_Side']==home else -1)})
        actual=model_side_line_value(pd.DataFrame(inputs),final).set_index('Game')
        for r in self.cp['samples']['CELL 48'][0]:
            a=actual.loc[r['Game']]
            for col in ['Market_Model_Spread','Retained_Model_Spread','Model_Cushion_Points']:
                self.assertAlmostEqual(a[col],r[col],delta=.005001)
            for col in ['Keys_Between_Market_And_Model','Key_Barrier_Present','Line_Value_Status','Decision_Status']:
                self.assertEqual(a[col],r[col])
