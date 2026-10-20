"""Offline weekly BCF file, scope, diagnostics, CLI and pipeline-boundary tests."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from cfb1.bcf import parse_bcf_csv,normalize_bcf,merge_bcf
from cfb1.bcf_weekly import (weekly_bcf_path,validate_weekly_bcf,load_weekly_bcf,
    merge_weekly_bcf,WeeklyBCFValidationError)
from cfb1.bcf_validate import main,target_slate

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures'
HEADER='Team,FEI,OFEI,DFEI,SFEI,OAY,DAY\n'
VALID=HEADER+'Miami,0.1,0.2,0.3,0.4,0.5,0.6\nConnecticut,0.2,0.3,0.4,0.5,0.6,0.7\n'


class WeeklyBCFTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.file=weekly_bcf_path(self.root,2026,6);self.file.parent.mkdir(parents=True)
        self.file.write_text(VALID)
        self.metadata={'season':2026,'week':6,'data_through_week':5,
            'source':'OFFLINE_TEST_FIXTURE','retrieved_at':'2026-10-05T12:00:00Z'}
        self.meta=self.file.with_suffix('.metadata.json');self.save_meta()
        self.names=json.loads((FIX/'cfbd_teams.json').read_text())
        self.slate=pd.DataFrame([{'Home_Team':'UConn Huskies','Away_Team':'Miami Hurricanes',
            'Home_CFBD_Name':'UConn','Away_CFBD_Name':'Miami','context':'keep'}])

    def save_meta(self):self.meta.write_text(json.dumps(self.metadata))

    def validate(self,**overrides):
        args=dict(season=2026,week=6,data_through_week=5,
            canonical_team_names=self.names,target_market=self.slate)
        args.update(overrides)
        return validate_weekly_bcf(self.file,**args)

    def test_valid_ready_target_only_no_national_requirement(self):
        out=self.validate()
        self.assertTrue(out.production_ready)
        self.assertEqual(out.report['rows_supplied'],2)
        self.assertEqual(out.report['unique_teams'],2)
        self.assertEqual(out.report['scheduled_fbs_teams_not_represented'],[])
        self.assertEqual(out.normalized.CFBD_Team.tolist(),['Miami','UConn'])

    def test_whitespace_and_canonical_bcf_mapping(self):
        self.file.write_text(VALID.replace('Connecticut',' Connecticut '))
        out=self.validate();self.assertTrue(out.production_ready)
        self.assertEqual(out.normalized.Team.iloc[1],'Connecticut')
        self.assertEqual(out.normalized.CFBD_Team.iloc[1],'UConn')

    def test_duplicate_raw_team_rejected(self):
        self.file.write_text(VALID+'Miami,1,1,1,1,1,1\n')
        out=self.validate();self.assertFalse(out.production_ready)
        self.assertEqual(out.report['duplicate_raw_teams'],['Miami'])
        self.assertIsNone(out.normalized)

    def test_duplicate_canonical_and_whitespace_collision(self):
        for name in ['UConn',' Connecticut ']:
            self.file.write_text(VALID+name+',1,1,1,1,1,1\n')
            out=self.validate();self.assertFalse(out.production_ready)
            self.assertEqual(out.report['duplicate_canonical_teams'],['UConn'])

    def test_missing_required_column(self):
        self.file.write_text(VALID.replace(',DAY',',EXTRA'))
        out=self.validate();self.assertFalse(out.production_ready)
        self.assertEqual(out.report['missing_required_fields'],['DAY'])

    def test_malformed_and_blank_numeric_fields_reported_together(self):
        self.file.write_text(VALID.replace('0.1,0.2','bad,').replace('0.6,0.7','0.6,no'))
        out=self.validate();self.assertFalse(out.production_ready)
        self.assertEqual({x['field'] for x in out.report['malformed_values']},{'FEI','OFEI','DAY'})

    def test_nonfinite_rejected_without_rating_range_rules(self):
        for value in ['inf','-inf','NaN']:
            self.file.write_text(VALID.replace('0.1',value))
            self.assertFalse(self.validate().production_ready)
        self.file.write_text(VALID.replace('0.1','-999'))
        self.assertTrue(self.validate().production_ready)

    def test_unresolved_team_and_missing_target_both_reported(self):
        self.file.write_text(VALID.replace('Miami,','Unknown University,'))
        r=self.validate().report
        self.assertFalse(r['production_ready'])
        self.assertEqual(r['unresolved_identities'][0]['team'],'Unknown University')
        self.assertEqual(r['scheduled_fbs_teams_not_represented'],['Miami'])

    def test_blank_team_not_stringified_into_verified_identity(self):
        self.file.write_text(VALID.replace('Miami,',','))
        out=self.validate();self.assertFalse(out.production_ready)
        self.assertEqual(out.report['unresolved_identities'][0]['team'],None)

    def test_known_non_slate_team_allowed_and_reported(self):
        self.file.write_text(VALID+'Appalachian State,1,1,1,1,1,1\n')
        r=self.validate().report;self.assertTrue(r['production_ready'])
        self.assertEqual(r['bcf_teams_not_on_target_slate'],['App State'])

    def test_target_missing_not_filled(self):
        self.file.write_text(HEADER+'Connecticut,1,1,1,1,1,1\n')
        out=self.validate();self.assertFalse(out.production_ready)
        self.assertEqual(out.report['scheduled_fbs_teams_not_represented'],['Miami'])
        self.assertIsNone(out.normalized)

    def test_unknown_non_slate_still_blocks_legacy_normalizer(self):
        self.file.write_text(VALID+'Unknown University,1,1,1,1,1,1\n')
        self.assertFalse(self.validate().production_ready)

    def test_season_week_and_completed_boundary_metadata_mismatch(self):
        for field,value in [('season',2025),('week',7),('data_through_week',4),('week','6')]:
            m=deepcopy(self.metadata);self.metadata[field]=value;self.save_meta()
            out=self.validate();self.assertFalse(out.production_ready)
            self.assertIn('Metadata mismatch: '+field,out.report['errors'])
            self.metadata=m

    def test_requested_boundary_conflicts_with_conventional_path(self):
        self.metadata.update(season=2027);self.save_meta()
        r=self.validate(season=2027).report
        self.assertFalse(r['production_ready'])
        self.assertIn('Conventional file path conflicts with season/week',r['errors'])

    def test_missing_metadata_source_and_naive_time_fail(self):
        self.meta.unlink();self.assertFalse(self.validate().production_ready)
        for field,value in [('source',''),('retrieved_at','2026-10-05T12:00:00'),('retrieved_at','bad')]:
            m=deepcopy(self.metadata);self.metadata[field]=value;self.save_meta()
            self.assertFalse(self.validate().production_ready);self.metadata=m

    def test_extra_columns_are_reported_and_ignored(self):
        data=pd.read_csv(StringIO(VALID));data['Notes']='context';self.file.write_text(data.to_csv(index=False))
        out=self.validate();self.assertTrue(out.production_ready)
        self.assertEqual(out.report['extra_columns_ignored'],['Notes'])
        self.assertNotIn('Notes',out.normalized)

    def test_duplicate_header_and_malformed_csv_block(self):
        for text in [VALID.replace(',DAY',',FEI'),VALID+'short,row\n',HEADER+'"unfinished']:
            self.file.write_text(text);self.assertFalse(self.validate().production_ready)

    def test_header_only_and_missing_file_not_ready(self):
        self.file.write_text(HEADER);self.assertFalse(self.validate().production_ready)
        self.file.unlink();self.assertFalse(self.validate().production_ready)

    def test_unchanged_legacy_parser_and_merge_parity(self):
        actual=load_weekly_bcf(self.file,season=2026,week=6,data_through_week=5,
            canonical_team_names=self.names,target_market=self.slate)
        expected=normalize_bcf(parse_bcf_csv(VALID),self.names,self.slate)
        assert_frame_equal(actual,expected)
        merged=merge_weekly_bcf(self.slate,self.file,season=2026,week=6,data_through_week=5,
            canonical_team_names=self.names)
        assert_frame_equal(merged,merge_bcf(self.slate,expected))
        self.assertEqual(merged.context.tolist(),['keep'])

    def test_invalid_load_raises_with_report(self):
        self.file.write_text(HEADER)
        with self.assertRaises(WeeklyBCFValidationError) as e:
            load_weekly_bcf(self.file,season=2026,week=6,data_through_week=5,
                canonical_team_names=self.names,target_market=self.slate)
        self.assertFalse(e.exception.report['production_ready'])

    def test_file_revalidated_after_edit_and_never_modified(self):
        before=self.file.read_bytes();meta=self.meta.read_bytes();out=self.validate()
        self.assertEqual(self.file.read_bytes(),before);self.assertEqual(self.meta.read_bytes(),meta)
        self.file.write_text(VALID.replace('0.1','bad'))
        new=self.validate();self.assertFalse(new.production_ready)
        self.assertNotEqual(out.report['csv_sha256'],new.report['csv_sha256'])

    def test_invalid_or_empty_context_rejected(self):
        for overrides in [dict(target_market=self.slate.iloc[:0]),dict(canonical_team_names=['Miami']),
            dict(canonical_team_names=['Miami','Miami']),dict(data_through_week=6)]:
            with self.assertRaises(ValueError):self.validate(**overrides)

    def test_dynamic_path_and_blank_template(self):
        self.assertEqual(weekly_bcf_path('data/bcf',2030,12),Path('data/bcf/2030/week_12/bcf.csv'))
        self.assertEqual((ROOT/'data/bcf/templates/bcf.csv').read_text(),HEADER)
        self.assertIsNone(json.loads((ROOT/'data/bcf/templates/bcf.metadata.example.json').read_text())['season'])


class CLITests(WeeklyBCFTests):
    # Inherit file fixtures, not test cases (subsequently restricted by load_tests below).
    def setUp(self):
        super().setUp()
        self.games=[json.loads((FIX/'cfbd_schedule.json').read_text())[1]]
        self.games[0].update(homeClassification='fbs',awayClassification='fbs')
        self.games_path=self.root/'games.json';self.games_path.write_text(json.dumps(self.games))
        self.features_path=self.root/'df_cfbd.csv';pd.DataFrame({'team':self.names}).to_csv(self.features_path,index=False)

    def cli(self,*extra):
        args=['--file',str(self.file),'--season','2026','--week','6','--data-through-week','5',
            '--features',str(self.features_path),'--games',str(self.games_path),*extra]
        out,err=StringIO(),StringIO()
        with redirect_stdout(out),redirect_stderr(err),patch('socket.socket',side_effect=AssertionError('No network')):
            status=main(args)
        return status,json.loads(out.getvalue() or err.getvalue())

    def test_cli_ready_reports_required_diagnostics(self):
        code,r=self.cli();self.assertEqual(code,0);self.assertTrue(r['production_ready'])
        for key in ['season','week','rows_supplied','unique_teams','duplicate_raw_teams',
            'duplicate_canonical_teams','unresolved_identities','malformed_values','missing_required_fields',
            'scheduled_fbs_teams_not_represented','bcf_teams_not_on_target_slate']:
            self.assertIn(key,r)

    def test_cli_not_ready_exit_one(self):
        self.file.write_text(HEADER)
        code,r=self.cli();self.assertEqual(code,1);self.assertFalse(r['production_ready'])

    def test_cli_scope_mismatch_exit_two(self):
        self.games[0]['week']=7;self.games_path.write_text(json.dumps(self.games))
        code,r=self.cli();self.assertEqual(code,2);self.assertFalse(r['production_ready'])

    def test_cli_unknown_fbs_classification_not_guessed(self):
        del self.games[0]['homeClassification'];self.games_path.write_text(json.dumps(self.games))
        self.assertEqual(self.cli()[0],2)

    def test_date_scope_and_out_of_scope_non_fbs_reported(self):
        other=deepcopy(self.games[0]);other.update(id=999,awayClassification='fcs',awayTeam='Unknown FCS')
        self.games.append(other);self.games_path.write_text(json.dumps(self.games))
        code,r=self.cli('--target-date','2026-10-10')
        self.assertEqual(code,0);self.assertEqual(len(r['excluded_schedule_games']),1)
        self.assertEqual(self.cli('--target-date','2026-10-11')[0],2)

    def test_invalid_schedule_duplicate_ids_not_treated_as_complete(self):
        self.games.append(deepcopy(self.games[0]));self.games_path.write_text(json.dumps(self.games))
        self.assertEqual(self.cli()[0],2)


def load_tests(loader,tests,pattern):
    suite=unittest.TestSuite(loader.loadTestsFromTestCase(WeeklyBCFTests))
    # Avoid running inherited unit tests twice in the CLI fixture subclass.
    for name in CLITests.__dict__:
        if name.startswith('test_'):suite.addTest(CLITests(name))
    return suite
