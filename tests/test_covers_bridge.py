"""Point-only market boundary tests on synthetic HTML, without network."""
from datetime import date,datetime,timezone
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
import unittest
import csv
import hashlib
import json
import tempfile

from cfb1.covers_bridge import (
    BOARD_URL, CoversFetcher, parse_board, parse_detail, enrich, attach_schedule,
    manual_ready, production_ready, production_blockers, audit_ready,
    load_cached_board, summary, main,
)
from cfb1.cfbd_schedule import CFBDAcquisitionError
from cfb1.schedule import ScheduleRecord, ScheduleValidation, ScheduleIssue
from cfb1.team_identity import TeamIdentityResolver

FIXTURES=Path(__file__).parent/'fixtures'

class CoversBridgeTests(unittest.TestCase):
    def setUp(self):
        self.html=(FIXTURES/'covers_market_sample.html').read_text()
        self.detail=(FIXTURES/'covers_matchup_sample.html').read_text()
        self.day=date(2026,10,17)
    def records(self,text=None):return parse_board(self.html if text is None else text,self.day,'2026-10-16T12:00:00Z')
    def enriched(self):
        rows=self.records()
        class Fetcher:
            def get(inner,url):return self.detail,{'retrieved_at':'2026-10-16T12:01:00Z'}
        enrich(rows,Fetcher(),self.day)
        return rows
    def attach(self,rows,games):
        attach_schedule(rows,ScheduleValidation(tuple(games),()),self.day,season=2026,week=7)
    def verified(self):
        rows=self.enriched()
        self.attach(rows,[ScheduleRecord(777,2026,7,'Miami','UConn',datetime(2026,10,17,16,tzinfo=timezone.utc))])
        return rows[0]
    def test_independent_book_points_not_prices_or_moneyline(self):
        r=self.records()[0]
        self.assertEqual((r['DK_Spread'],r['FD_Spread']),(-3.5,-4.5))
        self.assertEqual((r['DK_Total'],r['FD_Total']),(55.5,56.5))
        self.assertEqual(r['total_source_book'],'DraftKings')
        self.assertIsNone(r['opening_home_spread'])
        self.assertIsNone(r['game_id'])
    def test_missing_book_stays_missing_not_consensus_or_duplicate(self):
        r=self.records(self.html.replace('data-book="FanDuel"','data-book="OtherBook"'))[0]
        self.assertIsNone(r['FD_Spread']);self.assertIsNone(r['FD_Total'])
        self.assertEqual(r['DK_Spread'],-3.5)
        self.assertFalse(manual_ready(r))
    def test_total_fallback_is_measured_fd_value_not_book_copy(self):
        text=self.html.replace('o 55.5','unavailable').replace('u 55.5','unavailable')
        r=self.records(text)[0]
        self.assertIsNone(r['DK_Total']);self.assertEqual(r['current_total'],56.5)
        self.assertEqual(r['total_source_book'],'FanDuel')
    def test_conflicting_sides_rejected(self):
        r=self.records(self.html.replace('+3.5','+2.5'))[0]
        self.assertIsNone(r['DK_Spread']);self.assertIn('DK_spread_side_conflict',r['issues'])
    def test_conflicting_total_not_chosen(self):
        r=self.records(self.html.replace('u 55.5','u 54.5'))[0]
        self.assertIsNone(r['DK_Total']);self.assertIn('DK_total_side_conflict',r['issues'])
    def test_missing_dedicated_table_fails_closed(self):
        with self.assertRaises(ValueError):self.records(self.html.replace('id="spread-table"','id="other-table"'))
    def test_target_date_filter(self):
        self.assertEqual(self.records(self.html.replace('Oct 17','Oct 18')),[])
    def test_duplicate_source_rows_are_flagged(self):
        text=self.html.replace('</table><table id="total-table">','<tr class="oddsGameRow"><td><div class="td-cell game-time">Oct 17, 12:00</div></td><td data-book="DraftKings" data-game="1001"></td></tr></table><table id="total-table">')
        rows=self.records(text)
        self.assertEqual(len(rows),2)
        self.assertTrue(all('duplicate_source_game_id' in r['issues'] for r in rows))
    def test_detail_explicit_roles_identifier_and_utc(self):
        self.assertEqual(parse_detail(self.detail,'1001'),('Miami Hurricanes','UConn Huskies','2026-10-17T16:00:00Z'))
        with self.assertRaises(ValueError):parse_detail(self.detail,'wrong-game')
    def test_observed_single_extra_terminal_json_brace(self):
        self.assertEqual(parse_detail(self.detail.replace('}</script>','}}</script>'),'1001'),parse_detail(self.detail,'1001'))
        with self.assertRaises(ValueError):parse_detail(self.detail.replace('}</script>','} invalid</script>'),'1001')
    def test_no_inferred_title_roles_or_naive_kickoff(self):
        with self.assertRaises(ValueError):parse_detail('<script type="application/ld+json">{"@type":"SportsEvent","name":"Miami vs UConn","startDate":"2026-10-17T16:00:00Z"}</script>')
        with self.assertRaises(ValueError):parse_detail(self.detail.replace(' &#x2B;00:00',''))
    def test_existing_aliases_used_but_not_claimed_live_verified(self):
        r=self.enriched()[0]
        self.assertEqual((r['away_team'],r['home_team']),('Miami','UConn'))
        self.assertEqual(r['identity_status'],'legacy_alias_resolved_not_live_verified')
        self.assertTrue(manual_ready(r));self.assertIsNone(r['game_id'])
    def test_unknown_and_ambiguous_identity_flags(self):
        self.detail=self.detail.replace('Miami Hurricanes','Unknown Team')
        r=self.enriched()[0]
        self.assertIn('unresolved_team_identity',r['issues']);self.assertFalse(manual_ready(r))
        self.detail=(FIXTURES/'covers_matchup_sample.html').read_text()
        rows=self.records()
        class Fetcher:
            def get(inner,url):return self.detail,{'retrieved_at':'2026-10-16T12:01:00Z'}
        enrich(rows,Fetcher(),self.day,TeamIdentityResolver(['Miami Hurricanes','Miami','UConn']))
        self.assertIn('ambiguous_team_identity',rows[0]['issues'])
    def test_verified_join_preserves_official_id_and_orientation(self):
        rows=self.enriched();game=ScheduleRecord(777,2026,7,'Miami','UConn',datetime(2026,10,17,16,tzinfo=timezone.utc))
        self.attach(rows,[game])
        self.assertEqual(rows[0]['game_id'],777);self.assertEqual(rows[0]['schedule_join_status'],'verified')
    def test_ambiguous_join_or_kickoff_mismatch_never_picks_id(self):
        game=ScheduleRecord(777,2026,7,'Miami','UConn',datetime(2026,10,17,17,tzinfo=timezone.utc))
        rows=self.enriched();self.attach(rows,[game])
        self.assertEqual(rows[0]['schedule_join_status'],'kickoff_conflict');self.assertIsNone(rows[0]['game_id'])
        rows=self.enriched();self.attach(rows,[game,game])
        self.assertEqual(rows[0]['schedule_join_status'],'ambiguous');self.assertIsNone(rows[0]['game_id'])
    def test_reversed_official_orientation_is_flagged(self):
        rows=self.enriched()
        game=ScheduleRecord(777,2026,7,'UConn','Miami',datetime(2026,10,17,16,tzinfo=timezone.utc))
        self.attach(rows,[game])
        self.assertEqual(rows[0]['schedule_join_status'],'home_away_conflict')
        self.assertIsNone(rows[0]['game_id']);self.assertFalse(manual_ready(rows[0]))
    def test_duplicate_normalized_matchups_are_not_manual_ready(self):
        rows=self.records()+self.records()
        class Fetcher:
            def get(inner,url):return self.detail,{'retrieved_at':'2026-10-16T12:01:00Z'}
        enrich(rows,Fetcher(),self.day)
        self.assertTrue(all('duplicate_market_matchup' in r['issues'] for r in rows))
        self.assertTrue(all(not manual_ready(r) for r in rows))
    def test_summary_denominator_and_missing_fields(self):
        s=summary(self.records())
        self.assertEqual(s['coverage_denominator_games'],1)
        self.assertEqual(s['both_spreads_coverage_pct'],100)
        self.assertEqual(s['verified_schedule_joins'],0)
        self.assertEqual(s['missing_fields']['game_id'],1)
    def test_request_budget_and_denial_stop_without_retry(self):
        fetcher=CoversFetcher(1)
        with patch('cfb1.covers_bridge.request.urlopen',side_effect=HTTPError('https://www.covers.com',403,'blocked',{},None)) as send:
            with self.assertRaises(RuntimeError):fetcher.get('https://www.covers.com')
            with self.assertRaises(RuntimeError):fetcher.get('https://www.covers.com')
            self.assertEqual(send.call_count,1)
        self.assertTrue(fetcher.blocked)

    def test_manual_ready_is_not_production_ready(self):
        r=self.enriched()[0]
        self.assertTrue(manual_ready(r))
        self.assertFalse(production_ready(r))
        self.assertIn('schedule_association_not_verified',production_blockers(r))

    def test_verified_schedule_is_production_ready_without_opener(self):
        r=self.verified()
        self.assertTrue(production_ready(r))
        self.assertIsNone(r['opening_home_spread'])
        self.assertFalse(audit_ready(r))
        self.assertEqual(r['verified_schedule']['game_id'],777)

    def test_missing_official_id_or_changed_orientation_blocks_production(self):
        r=self.verified();r['game_id']=None
        self.assertFalse(production_ready(r))
        r=self.verified();r['home_team']='Miami'
        self.assertFalse(production_ready(r))

    def test_schedule_recheck_clears_old_verified_id(self):
        r=self.verified()
        self.attach([r],[ScheduleRecord(888,2026,7,'UConn','Miami',datetime(2026,10,17,16,tzinfo=timezone.utc))])
        self.assertIsNone(r['game_id'])
        self.assertFalse(production_ready(r))

    def test_unmatched_schedule_preserves_manual_only_readiness(self):
        r=self.verified()
        self.attach([r],[ScheduleRecord(888,2026,7,'Army','Navy',datetime(2026,10,17,16,tzinfo=timezone.utc))])
        self.assertTrue(manual_ready(r))
        self.assertFalse(production_ready(r))
        self.assertEqual(r['schedule_join_status'],'unmatched')

    def test_invalid_schedule_batch_and_wrong_week_block_production(self):
        game=ScheduleRecord(777,2026,7,'Miami','UConn',datetime(2026,10,17,16,tzinfo=timezone.utc))
        r=self.enriched()[0]
        invalid=ScheduleValidation((game,),(ScheduleIssue('duplicate_game_id',1,'duplicate'),))
        attach_schedule([r],invalid,self.day,season=2026,week=7)
        self.assertFalse(production_ready(r));self.assertIsNone(r['game_id'])
        r=self.enriched()[0]
        attach_schedule([r],ScheduleValidation((game,),()),self.day,season=2026,week=8)
        self.assertFalse(production_ready(r));self.assertEqual(r['schedule_join_status'],'invalid_batch')
        with self.assertRaises(TypeError):
            attach_schedule([r],[game],self.day,season=2026,week=7)

    def test_requested_date_and_kickoff_mismatch_block_production(self):
        r=self.verified();r['market_date']='2026-10-18'
        self.assertFalse(production_ready(r))
        r=self.verified();r['kickoff_utc']='2026-10-17T17:00:00Z'
        self.assertFalse(production_ready(r))

    def test_home_only_spread_is_preserved_but_not_production_ready(self):
        self.html=self.html.replace('+3.5','unavailable')
        r=self.enriched()[0]
        self.assertEqual(r['DK_Spread'],-3.5)
        self.assertIsNone(r['DK_Away_Spread'])
        self.assertIn('DK_incomplete_spread_sides',r['warnings'])
        self.assertTrue(manual_ready(r))
        self.attach([r],[ScheduleRecord(777,2026,7,'Miami','UConn',datetime(2026,10,17,16,tzinfo=timezone.utc))])
        self.assertFalse(production_ready(r))

    def test_away_only_spread_is_preserved_without_negating_into_home(self):
        r=self.records(self.html.replace('>-3.5<','>unavailable<'))[0]
        self.assertEqual(r['DK_Away_Spread'],3.5)
        self.assertIsNone(r['DK_Spread'])
        self.assertEqual(r['FD_Spread'],-4.5)
        self.assertEqual(r['books']['DraftKings']['spread_side_status'],'incomplete')

    def test_ambiguous_spread_side_is_not_silently_selected(self):
        text=self.html.replace('>-3.5<span','>-3.5</a><a>-2.5<span')
        r=self.records(text)[0]
        self.assertIsNone(r['DK_Spread'])
        self.assertIn('DK_ambiguous_spread_sides',r['issues'])

    def test_current_total_must_be_finite_and_honestly_attributed(self):
        for value in [float('nan'),float('inf'),-1]:
            r=self.verified();r['current_total']=value
            self.assertFalse(production_ready(r))
        r=self.verified();r['total_source_book']='Consensus'
        self.assertFalse(production_ready(r))

    def test_overflowing_point_text_is_not_a_usable_observation(self):
        r=self.records(self.html.replace('>-3.5<','>-'+'9'*400+'<'))[0]
        self.assertIsNone(r['DK_Spread'])
        self.assertEqual(r['DK_Away_Spread'],3.5)

    def test_missing_book_blocks_production_without_fabrication(self):
        self.html=self.html.replace('data-book="FanDuel"','data-book="OtherBook"')
        r=self.enriched()[0]
        self.attach([r],[ScheduleRecord(777,2026,7,'Miami','UConn',datetime(2026,10,17,16,tzinfo=timezone.utc))])
        self.assertFalse(production_ready(r))
        self.assertIsNone(r['FD_Spread']);self.assertIsNone(r['FD_Total'])

    def test_verified_movement_pair_is_separate_from_initial_quotes(self):
        r=self.verified()
        r['movement_audit']={
            'verified':True,'game_id':777,'away_team':'Miami','home_team':'UConn',
            'opening':{'home_spread':-2.5,'book':'DraftKings','source':'verified_fixture',
                       'retrieved_at':'2026-10-15T12:00:00Z','definition':'first published full-game spread'},
            'current':{'home_spread':-4.5,'book':'DraftKings','source':'verified_fixture',
                       'retrieved_at':'2026-10-17T10:00:00Z'},
        }
        self.assertTrue(audit_ready(r));self.assertEqual(r['DK_Spread'],-3.5)
        r['movement_audit']['current']['book']='FanDuel'
        self.assertFalse(audit_ready(r));self.assertTrue(production_ready(r))
        r['movement_audit']['current']['book']='DraftKings'
        r['movement_audit']['game_id']=888
        self.assertFalse(audit_ready(r))
        r['movement_audit']['game_id']=777
        del r['movement_audit']['opening']
        self.assertFalse(audit_ready(r));self.assertTrue(production_ready(r))

    def test_displayed_opener_alone_cannot_establish_audit_readiness(self):
        r=self.verified();r['opening_home_spread']=-2.5
        self.assertFalse(audit_ready(r));self.assertTrue(production_ready(r))

    def test_cached_board_capture_time_unknown_without_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'board.html';p.write_text(self.html)
            text,meta=load_cached_board(p)
            self.assertEqual(text,self.html)
            self.assertIsNone(meta['retrieved_at'])
            self.assertIn('filesystem_mtime_utc',meta)
            self.assertEqual(meta['capture_time_provenance'],'unknown')
        r=self.verified();r['retrieved_at']=None
        self.assertTrue(manual_ready(r));self.assertFalse(production_ready(r))

    def test_trusted_capture_receipt_preserves_timestamp_and_checks_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'board.html';p.write_text(self.html)
            receipt=Path(directory)/'receipt.json'
            timestamp='2026-10-16T08:00:00-04:00'
            data={'url':BOARD_URL,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retrieved_at':timestamp}
            receipt.write_text(json.dumps(data))
            _,meta=load_cached_board(p,receipt)
            self.assertEqual(meta['retrieved_at'],timestamp)
            self.assertEqual(meta['capture_time_provenance'],'supplied_capture_receipt')
            data['retrieved_at']='2026-10-16T08:00:00';receipt.write_text(json.dumps(data))
            with self.assertRaises(ValueError):load_cached_board(p,receipt)
            data['retrieved_at']=timestamp;data['sha256']='wrong';receipt.write_text(json.dumps(data))
            with self.assertRaises(ValueError):load_cached_board(p,receipt)

    def run_cli(self,*,capture=True,available=True,target='2026-10-24',empty=False):
        """All acquisition mocked; exports exist only in an auto-cleaned temp dir."""
        target_day=date.fromisoformat(target)
        html=self.html.replace('Oct 17','Oct 24') if target=='2026-10-24' else self.html
        detail=self.detail.replace('10/17/2026','10/24/2026') if target=='2026-10-24' else self.detail
        if empty:html=html.replace('Oct 24','Oct 25')
        game=ScheduleRecord(777,2026,8,'Miami','UConn',datetime.combine(target_day,datetime.min.time(),timezone.utc).replace(hour=16))
        live=SimpleNamespace(validation=ScheduleValidation((game,),()),to_dict=lambda:{'valid':True})
        def get(fetcher,url):
            self.assertEqual(url,'https://www.covers.com/sport/football/ncaaf/matchup/1001')
            return detail,{'retrieved_at':'2026-10-23T12:01:00Z'}
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory);board=d/'board.html';board.write_text(html)
            argv=['--date',target,'--season','2026','--week','8','--board-file',str(board),'--output-dir',str(d/'out')]
            if capture:
                receipt=d/'receipt.json';receipt.write_text(json.dumps({'url':BOARD_URL,'sha256':hashlib.sha256(board.read_bytes()).hexdigest(),'retrieved_at':'2026-10-23T12:00:00Z'}))
                argv+=['--board-metadata',str(receipt)]
            with patch('cfb1.covers_bridge.acquire_cfbd_schedule',return_value=live,
                       side_effect=None if available else CFBDAcquisitionError('test credentials unavailable')), \
                 patch.object(CoversFetcher,'get',get),redirect_stdout(StringIO()):
                code=main(argv)
            reports=list((d/'out').glob('*.json'))
            report=json.loads(next(p for p in reports if not p.stem.endswith('_validation')).read_text())
            production_csv=next((d/'out').glob('*_production_ready.csv'))
            with production_csv.open() as f:production_rows=list(csv.DictReader(f))
        return code,report,production_rows

    def test_cli_non_october17_production_success_without_openers(self):
        code,report,rows=self.run_cli()
        self.assertEqual(code,0);self.assertEqual(len(rows),1)
        self.assertEqual(report['summary']['requested_date'],'2026-10-24')
        self.assertEqual(report['summary']['production_ready_records'],1)
        self.assertEqual(report['summary']['audit_ready_records'],0)
        self.assertFalse(report['provisional'])
        self.assertNotIn('October 17',report['summary']['coverage_denominator'])

    def test_cli_manual_only_is_nonzero_and_reported_explicitly(self):
        code,report,rows=self.run_cli(available=False)
        self.assertEqual(code,1);self.assertEqual(rows,[])
        self.assertEqual(report['summary']['manual_ready_records'],1)
        self.assertEqual(report['summary']['production_ready_records'],0)
        self.assertEqual(report['summary']['excluded_or_blocked_records'],1)
        self.assertFalse(report['production_validation_passed'])

    def test_cli_unknown_capture_time_and_empty_slate_fail_validation(self):
        code,report,rows=self.run_cli(capture=False)
        self.assertEqual(code,1);self.assertEqual(rows,[])
        self.assertIsNone(report['board']['retrieved_at'])
        code,report,rows=self.run_cli(empty=True)
        self.assertEqual(code,1);self.assertEqual(report['summary']['games_found'],0)

    def test_cli_conflicting_side_is_counted_and_excluded(self):
        self.html=self.html.replace('+3.5','+2.5')
        code,report,rows=self.run_cli()
        self.assertEqual(code,1);self.assertEqual(rows,[])
        self.assertEqual(report['summary']['blocking_conflict_records'],1)
        self.assertEqual(report['summary']['excluded_or_blocked_records'],1)
        self.assertFalse(report['records'][0]['production_ready'])

    def test_cli_requires_explicit_week_and_season_before_network(self):
        with patch.object(CoversFetcher,'get') as fetch,redirect_stderr(StringIO()):
            for argv in [[],['--date','2026-10-24','--season','2026'],
                         ['--date','2026-10-24','--week','8']]:
                with self.assertRaises(SystemExit) as error:main(argv)
                self.assertEqual(error.exception.code,2)
            fetch.assert_not_called()

if __name__=='__main__':unittest.main()
