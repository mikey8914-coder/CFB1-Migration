"""Offline OLD CELL 43/44 parity, explicit audit readiness, and pipeline checks."""

import ast
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import hashlib
import json
from pathlib import Path
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from cfb1.market_audit import audit_spread_movement, prepare_market_audit, AuditBatch
from cfb1.final_decision import build_final_decisions, build_available_final_decisions
from cfb1.covers_bridge import production_ready, audit_ready

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"


def literal_cell(number, env):
    if number not in [43, 44]:
        raise ValueError("Outside audit/decision scope")
    label = f"OLD CELL {number}"
    notebook = json.loads((ROOT / "legacy/CFB1_Colab_Reference.ipynb").read_text())
    source = next("".join(c["source"]) for c in notebook["cells"]
                  if any(line.startswith("# " + label + " —") for line in c["source"]))
    tree = ast.parse(source)
    if number == 43:
        tree.body = [n for n in tree.body if not (isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "covers_csv" for t in n.targets))]
    with redirect_stdout(StringIO()):
        exec(compile(tree, "frozen_" + label, "exec"), env)


def one_review(model="Beta", review_class="MATCHUP_SUPPORTED"):
    return pd.DataFrame([{"Game": "Alpha at Beta", "Model_Side": model,
                          "Review_Class": review_class, "Phase1_Reason": "MODULE3_SUPPORT"}])


def one_observation(opening=-3., current=-4.):
    return pd.DataFrame([{"Game": "Alpha at Beta", "Away_Team": "Alpha", "Home_Team": "Beta",
                          "Open_Home_Spread": opening, "Current_Home_Spread": current}])


def one_routes(status="STANDARD_REVIEW", size=4.):
    return pd.DataFrame([{"Game": "Alpha at Beta", "M3_Support": "Beta +OAY_DAY", "M3_Conflict": "",
                          "Favorite_Spread_Size": size, "Spread_Status": status,
                          "Eligible_Market_Routes": "FULL_GAME_SPREAD"}])


def current_record(game_id=123, away="A", home="B", current=-4., kickoff="2026-10-24T16:00:00Z"):
    proof = {"source": "cfbd", "game_id": game_id, "season": 2026, "week": 8,
             "away_team": away, "home_team": home, "kickoff_utc": kickoff}
    return {"game_id": game_id, "away_team": away, "home_team": home,
            "kickoff_utc": kickoff, "market_date": "2026-10-24", "retrieved_at": "2026-10-23T12:00:00Z",
            "identity_status": "cfbd_registry_matched", "schedule_join_status": "verified",
            "verified_schedule": proof, "requested_season": 2026, "requested_week": 8,
            "issues": [], "DK_Spread": current, "FD_Spread": current, "DK_Total": 50., "FD_Total": 50.,
            "current_total": 50., "total_source_book": "DraftKings",
            "books": {b: {"spread_side_status": "complete"} for b in ["DraftKings", "FanDuel"]},
            "opening_home_spread": None, "opening_spread_status": "excluded_unverified_attribution"}


def movement_pair(record, opening=-3., book="DraftKings"):
    return {"verified": True, "game_id": record["game_id"], "away_team": record["away_team"],
            "home_team": record["home_team"], "opening": {
                "home_spread": opening, "source": "verified_fixture_provider", "book": book,
                "retrieved_at": "2026-10-22T12:00:00Z", "definition": "Separately verified same-book opener"},
            "current": {"home_spread": record[{"DraftKings": "DK", "FanDuel": "FD"}[book]+"_Spread"],
                        "source": "verified_fixture_provider", "book": book,
                        "retrieved_at": "2026-10-23T12:00:00Z"}}


def one_keys():
    return pd.DataFrame([{"Game": "Alpha at Beta", "Away_Team": "Alpha", "Home_Team": "Beta",
                          "game_id": 123, "Away_CFBD_Name": "A", "Home_CFBD_Name": "B"}])


class AuditTests(unittest.TestCase):
    def calculate(self, opening=-3., current=-4., model="Beta"):
        return audit_spread_movement(one_observation(opening, current).to_csv(index=False), one_review(model))

    def test_negative_home_movement_confirms_home_model(self):
        row = self.calculate().iloc[0]
        self.assertEqual((row.Spread_Move, row.Movement_Toward, row.Market_Relationship), (-1., "Beta", "CONFIRMS_MODEL"))

    def test_positive_home_movement_confirms_away_model(self):
        row = self.calculate(3., 4., "Alpha").iloc[0]
        self.assertEqual((row.Spread_Move, row.Movement_Toward, row.Market_Relationship), (1., "Alpha", "CONFIRMS_MODEL"))

    def test_movement_against_model(self):
        self.assertEqual(self.calculate(-3., -2.).Market_Relationship.iloc[0], "CONFLICTS_WITH_MODEL")

    def test_no_movement_is_neutral(self):
        row = self.calculate(-3., -3.).iloc[0]
        self.assertEqual((row.Spread_Move, row.Movement_Toward, row.Movement_Class, row.Market_Relationship),
                         (0., "NONE", "NO_MOVE", "NEUTRAL"))

    def test_movement_class_boundaries(self):
        for size, label in [(0., "NO_MOVE"), (.99, "SMALL"), (1., "MODERATE"), (1.99, "MODERATE"), (2., "MAJOR")]:
            with self.subTest(size=size):
                self.assertEqual(self.calculate(0., size).Movement_Class.iloc[0], label)

    def test_all_signed_keys_cross_in_both_directions(self):
        for key in [-14, -10, -7, -3, 3, 7, 10, 14]:
            for opening, current in [(key-.5, key+.5), (key+.5, key-.5)]:
                with self.subTest(key=key, opening=opening):
                    row = self.calculate(opening, current).iloc[0]
                    self.assertEqual(row.Key_Numbers_Crossed, str(abs(key)))
                    self.assertTrue(row.Key_Cross)

    def test_touching_or_leaving_key_endpoint_does_not_cross(self):
        for key in [-14, -10, -7, -3, 3, 7, 10, 14]:
            for opening, current in [(key-1, key), (key, key+1), (key+1, key), (key, key-1)]:
                with self.subTest(key=key, opening=opening):
                    self.assertFalse(self.calculate(opening, current).Key_Cross.iloc[0])

    def test_multiple_keys_sorted_unique_absolute_magnitudes(self):
        row = self.calculate(-15., 15.).iloc[0]
        self.assertEqual(row.Key_Numbers_Crossed, "3,7,10,14")

    def test_crossing_zero_is_not_key_crossing(self):
        self.assertFalse(self.calculate(-1., 1.).Key_Cross.iloc[0])

    def test_raw_endpoints_determine_keys_even_when_rounded_move_is_zero(self):
        row = self.calculate(2.999, 3.001).iloc[0]
        self.assertTrue(row.Key_Cross)
        self.assertEqual(row.Movement_Class, "NO_MOVE")
        self.assertEqual(row.Market_Relationship, "NEUTRAL")

    def test_spreads_are_numeric_coerced_and_text_is_trimmed(self):
        text = one_observation(" +3.5 ", " +2.5 ")
        text["Source"] = " supplied manually "
        row = audit_spread_movement(text.to_csv(index=False), one_review()).iloc[0]
        self.assertEqual(row.Spread_Move, -1.)
        self.assertEqual(row.Source, "supplied manually")

    def test_missing_or_malformed_opener_fails_strict_audit(self):
        for value in [None, "bad", ""]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.calculate(value, -4.)

    def test_missing_or_malformed_current_fails_strict_audit(self):
        for value in [None, "bad", ""]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.calculate(-3., value)

    def test_missing_spread_column_fails(self):
        text = one_observation().drop(columns="Current_Home_Spread").to_csv(index=False)
        with self.assertRaises(KeyError):
            audit_spread_movement(text, one_review())

    def test_extra_or_missing_game_fails(self):
        rows = one_observation()
        rows.Game = "Other at Team"
        with self.assertRaises(ValueError):
            audit_spread_movement(rows.to_csv(index=False), one_review())

    def test_duplicate_observation_fails(self):
        rows = one_observation()
        with self.assertRaises(ValueError):
            audit_spread_movement(pd.concat([rows, rows]).to_csv(index=False), one_review())

    def test_duplicate_review_fails_one_to_one(self):
        review = one_review()
        with self.assertRaises(pd.errors.MergeError):
            audit_spread_movement(one_observation().to_csv(index=False), pd.concat([review, review]))

    def test_null_model_context_fails(self):
        review = one_review()
        review.Model_Side = None
        with self.assertRaises(ValueError):
            audit_spread_movement(one_observation().to_csv(index=False), review)


class DecisionTests(unittest.TestCase):
    def calculate(self, opening=-3., current=-4., status="STANDARD_REVIEW", review_class="MATCHUP_SUPPORTED", size=4.):
        review = one_review(review_class=review_class)
        audit = audit_spread_movement(one_observation(opening, current).to_csv(index=False), review)
        return build_final_decisions(review, one_routes(status, size), audit)

    def test_confirmed_standard(self):
        self.assertEqual(self.calculate().Decision_Status.iloc[0], "CONFIRMED")

    def test_conflicted_standard_small_move(self):
        self.assertEqual(self.calculate(-3., -2.5).Decision_Status.iloc[0], "MARKET_CONFLICT")

    def test_conflicted_standard_major_move(self):
        self.assertEqual(self.calculate(-3., -1.).Decision_Status.iloc[0], "STRONG_MARKET_CONFLICT")

    def test_key_crossing_escalates_even_moderate_conflict(self):
        self.assertEqual(self.calculate(-3.5, -2.5).Decision_Status.iloc[0], "STRONG_MARKET_CONFLICT")

    def test_touching_key_does_not_escalate_conflict(self):
        self.assertEqual(self.calculate(-3.5, -3.).Decision_Status.iloc[0], "MARKET_CONFLICT")

    def test_confirmed_both_large_statuses(self):
        for status in ["LARGE_SPREAD_CAUTION", "DERIVATIVES_FIRST_20.5_PLUS"]:
            self.assertEqual(self.calculate(status=status).Decision_Status.iloc[0], "CONFIRMED_BUT_LARGE_SPREAD")

    def test_large_conflict_takes_priority_over_confirmed_large_branch(self):
        self.assertEqual(self.calculate(-3., -2.5, "DERIVATIVES_FIRST_20.5_PLUS").Decision_Status.iloc[0], "MARKET_CONFLICT")

    def test_large_major_conflict(self):
        self.assertEqual(self.calculate(-3., 0., "LARGE_SPREAD_CAUTION").Decision_Status.iloc[0], "STRONG_MARKET_CONFLICT")

    def test_large_flag_uses_prior_route_status_not_current_spread_recalculation(self):
        self.assertEqual(self.calculate(status="STANDARD_REVIEW", size=40.).Decision_Status.iloc[0], "CONFIRMED")

    def test_neutral_large_is_neutral(self):
        self.assertEqual(self.calculate(-3., -3., "DERIVATIVES_FIRST_20.5_PLUS").Decision_Status.iloc[0], "NEUTRAL_MARKET")

    def test_conflict_review_confirmation_precedes_large_status(self):
        self.assertEqual(self.calculate(status="DERIVATIVES_FIRST_20.5_PLUS", review_class="CONFLICT_REVIEW").Decision_Status.iloc[0], "CONFLICT_REVIEW_MARKET_SUPPORTS_MODEL")

    def test_conflict_review_rejection_precedes_major_key_conflict(self):
        self.assertEqual(self.calculate(-4., 4., review_class="CONFLICT_REVIEW").Decision_Status.iloc[0], "CONFLICT_REVIEW_MARKET_REJECTS_MODEL")

    def test_conflict_review_neutral_is_unresolved(self):
        self.assertEqual(self.calculate(-3., -3., review_class="CONFLICT_REVIEW").Decision_Status.iloc[0], "CONFLICT_REVIEW_UNRESOLVED")

    def test_exact_decision_note(self):
        self.assertEqual(self.calculate().Decision_Note.iloc[0], "Market movement supports the model side.")

    def test_unrecognized_relationship_fails_unclassified_gate(self):
        review = one_review()
        audit = audit_spread_movement(one_observation().to_csv(index=False), review)
        audit.Market_Relationship = "unknown"
        with self.assertRaises(ValueError):
            build_final_decisions(review, one_routes(), audit)

    def test_missing_audit_row_fails_strict_final(self):
        review = one_review()
        audit = audit_spread_movement(one_observation().to_csv(index=False), review)
        with self.assertRaises(ValueError):
            build_final_decisions(review, one_routes(), audit.iloc[:0])

    def test_missing_route_fails(self):
        review = one_review()
        audit = audit_spread_movement(one_observation().to_csv(index=False), review)
        with self.assertRaises(ValueError):
            build_final_decisions(review, one_routes().iloc[:0], audit)

    def test_duplicate_route_fails(self):
        review = one_review()
        audit = audit_spread_movement(one_observation().to_csv(index=False), review)
        routes = one_routes()
        with self.assertRaises(pd.errors.MergeError):
            build_final_decisions(review, pd.concat([routes, routes]), audit)

    def test_functions_do_not_mutate_review_or_routes(self):
        review, routes = one_review(), one_routes()
        before_review, before_routes = review.copy(), routes.copy()
        audit = audit_spread_movement(one_observation().to_csv(index=False), review)
        build_final_decisions(review, routes, audit)
        assert_frame_equal(review, before_review)
        assert_frame_equal(routes, before_routes)


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.record = current_record()
        self.proof = movement_pair(self.record)
        self.review, self.keys = one_review(), one_keys()

    def prepare(self, proofs=None, records=None):
        return prepare_market_audit(self.review, self.keys, records if records is not None else [self.record],
                                    proofs if proofs is not None else {123:self.proof})

    def test_no_opener_preserves_current_readiness_and_retains_pending_candidate(self):
        before = deepcopy(self.record)
        result = self.prepare(proofs={})
        self.assertTrue(production_ready(self.record))
        self.assertFalse(audit_ready(self.record))
        self.assertEqual(self.record, before)
        self.assertTrue(result.audit.empty)
        self.assertTrue(result.availability.Current_Market_Ready.iloc[0])
        self.assertEqual(result.availability.Audit_Reason.iloc[0], "OPENER_UNAVAILABLE")
        final = build_available_final_decisions(self.review, one_routes(), result)
        self.assertTrue(final.decisions.empty)
        self.assertEqual(len(final.pending_audit), 1)
        self.assertNotIn("Decision_Status", final.pending_audit)
        self.assertEqual(final.pending_audit.Audit_Status.iloc[0], "AUDIT_UNAVAILABLE")

    def test_separately_verified_pair_enables_audit_and_final(self):
        result = self.prepare()
        self.assertTrue(result.availability.Audit_Ready.iloc[0])
        self.assertEqual(result.audit.Open_Home_Spread.iloc[0], -3.)
        self.assertEqual(result.audit.Book.iloc[0], "DraftKings")
        final = build_available_final_decisions(self.review, one_routes(), result)
        self.assertTrue(final.pending_audit.empty)
        self.assertEqual(final.decisions.Decision_Status.iloc[0], "CONFIRMED")

    def test_displayed_opener_alone_is_not_verified_pair(self):
        self.record["opening_home_spread"] = -3.
        self.assertFalse(self.prepare(proofs={}).availability.Audit_Ready.iloc[0])

    def test_unverified_pair_not_accepted(self):
        self.proof["verified"] = False
        self.assertEqual(self.prepare().availability.Audit_Reason.iloc[0], "MOVEMENT_PAIR_NOT_VERIFIED")

    def test_unknown_definition_not_accepted(self):
        self.proof["opening"]["definition"] = ""
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_different_book_pair_not_accepted(self):
        self.proof["opening"]["book"] = "FanDuel"
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_different_source_pair_not_accepted(self):
        self.proof["opening"]["source"] = "another provider"
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_invalid_temporal_order_not_accepted(self):
        self.proof["opening"]["retrieved_at"] = "2026-10-24T12:00:00Z"
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_current_pair_before_board_capture_not_accepted(self):
        self.proof["current"]["retrieved_at"] = "2026-10-23T11:59:00Z"
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_current_pair_point_must_match_selected_book_measurement(self):
        self.proof["current"]["home_spread"] = -5.
        self.assertEqual(self.prepare().availability.Audit_Reason.iloc[0], "AUDIT_CURRENT_POINT_MISMATCH")

    def test_nonfinite_opener_is_unavailable_not_zero_movement(self):
        self.proof["opening"]["home_spread"] = float("inf")
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_malformed_current_cannot_pass_as_ready(self):
        self.record["DK_Spread"] = "bad"
        result = self.prepare()
        self.assertFalse(result.availability.Current_Market_Ready.iloc[0])
        self.assertFalse(result.availability.Audit_Ready.iloc[0])

    def test_missing_current_record_retained_as_pending(self):
        result = self.prepare(records=[])
        self.assertEqual(result.availability.Audit_Reason.iloc[0], "CURRENT_RECORD_MISSING_OR_AMBIGUOUS")
        self.assertEqual(len(build_available_final_decisions(self.review, one_routes(), result).pending_audit),1)

    def test_ambiguous_current_record_not_silently_selected(self):
        self.assertFalse(self.prepare(records=[self.record,deepcopy(self.record)]).availability.Audit_Ready.iloc[0])

    def test_wrong_canonical_orientation_not_joined_by_display_name(self):
        self.keys.Away_CFBD_Name = "B"
        self.keys.Home_CFBD_Name = "A"
        self.assertEqual(self.prepare().availability.Audit_Reason.iloc[0], "OFFICIAL_TEAM_ORIENTATION_MISMATCH")

    def test_duplicate_master_keys_are_rejected(self):
        self.keys = pd.concat([self.keys,self.keys])
        with self.assertRaises(ValueError):self.prepare()

    def test_missing_master_keys_are_rejected(self):
        self.keys.game_id = None
        with self.assertRaises(ValueError):self.prepare()

    def test_audit_partition_must_cover_every_review_candidate(self):
        result = self.prepare()
        result.availability = result.availability.iloc[:0]
        with self.assertRaises(ValueError):
            build_available_final_decisions(self.review,one_routes(),result)

    def test_ready_partition_cannot_omit_the_actual_audit_row(self):
        result = self.prepare()
        result.audit = result.audit.iloc[:0]
        with self.assertRaises(ValueError):
            build_available_final_decisions(self.review,one_routes(),result)

    def test_mixed_ready_and_unavailable_candidates_are_both_retained(self):
        second_review = self.review.copy()
        second_review["Game"] = "Gamma at Delta"
        second_review["Model_Side"] = "Delta"
        self.review = pd.concat([self.review, second_review], ignore_index=True)
        second_keys = self.keys.copy()
        second_keys.loc[0] = ["Gamma at Delta", "Gamma", "Delta", 124, "C", "D"]
        self.keys = pd.concat([self.keys, second_keys], ignore_index=True)
        records = [self.record, current_record(game_id=124, away="C", home="D")]
        batch = self.prepare(records=records)
        final = build_available_final_decisions(self.review, one_routes(), batch)
        self.assertEqual(final.decisions.Game.tolist(), ["Alpha at Beta"])
        self.assertEqual(final.pending_audit.Game.tolist(), ["Gamma at Delta"])
        self.assertTrue(final.pending_audit.Current_Market_Ready.iloc[0])

    def test_pair_game_id_mismatch_cannot_enable_audit(self):
        self.proof["game_id"] = 999
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_pair_identity_mismatch_cannot_enable_audit(self):
        self.proof["away_team"] = "different"
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_naive_opener_time_cannot_enable_audit(self):
        self.proof["opening"]["retrieved_at"] = "2026-10-22T12:00:00"
        self.assertFalse(self.prepare().availability.Audit_Ready.iloc[0])

    def test_missing_current_point_does_not_gain_a_decision(self):
        self.record["DK_Spread"] = None
        batch = self.prepare()
        self.assertFalse(batch.availability.Current_Market_Ready.iloc[0])
        self.assertTrue(build_available_final_decisions(self.review, one_routes(), batch).decisions.empty)

    def test_fd_pair_selects_fd_not_dk_point(self):
        self.record["FD_Spread"] = -4.5
        self.proof = movement_pair(self.record, book="FanDuel")
        result = self.prepare()
        self.assertEqual(result.audit.Current_Home_Spread.iloc[0], -4.5)


class ParityTests(unittest.TestCase):
    def test_controlled_identical_input_audit_and_final_parity(self):
        rows, reviews, routes = [], [], []
        for i,(opening,current,side,review_class,status) in enumerate([
            (-3.,-4.,"H","MATCHUP_SUPPORTED","STANDARD_REVIEW"),
            (3.,4.,"A","MODEL_PLUS_MATCHUP","LARGE_SPREAD_CAUTION"),
            (-3.5,-2.5,"H","STRONG_MODEL_AGREEMENT","STANDARD_REVIEW"),
            (-3.,-3.,"H","MATCHUP_SUPPORTED","DERIVATIVES_FIRST_20.5_PLUS"),
            (-3.,-4.,"H","CONFLICT_REVIEW","STANDARD_REVIEW"),
            (3.,4.,"H","CONFLICT_REVIEW","STANDARD_REVIEW"),
            (-3.,-3.,"H","CONFLICT_REVIEW","STANDARD_REVIEW"),
        ]):
            game=f'A{i} at H{i}'
            rows.append({"Game":game,"Away_Team":f'A{i}',"Home_Team":f'H{i}',"Open_Home_Spread":opening,"Current_Home_Spread":current})
            reviews.append({"Game":game,"Model_Side":side+str(i),"Review_Class":review_class,"Phase1_Reason":"CONTROLLED"})
            routes.append({"Game":game,"M3_Support":"","M3_Conflict":"","Favorite_Spread_Size":5.,"Spread_Status":status,"Eligible_Market_Routes":""})
        review,routes=pd.DataFrame(reviews),pd.DataFrame(routes);csv=pd.DataFrame(rows).to_csv(index=False)
        env={"pd":pd,"display":lambda *a:None,"TARGET_WEEK":6,"df_phase1_review":review.copy(),"df_final_routes":routes.copy(),"covers_csv":csv}
        literal_cell(43,env)
        audit=audit_spread_movement(csv,review)
        assert_frame_equal(audit,env['covers_audit'])
        literal_cell(44,env)
        assert_frame_equal(build_final_decisions(review,routes,audit),env['df_final_decision'])

    def test_missing_opener_failure_matches_literal_source(self):
        csv=one_observation(None,-4.).to_csv(index=False)
        env={"pd":pd,"display":lambda *a:None,"TARGET_WEEK":6,"df_phase1_review":one_review(),"covers_csv":csv}
        with self.assertRaises(ValueError):audit_spread_movement(csv,one_review())
        with self.assertRaises(ValueError):literal_cell(43,env)


class HistoricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Import only test helper orchestration; production calculations use modules.
        from test_routing_phase1 import historical_inputs, pipeline
        cls.cp=json.loads((FIXTURES/'late_week_notebook_checkpoint.json').read_text())
        cls.csv=(FIXTURES/'late_week_notebook_synthetic.csv').read_text()
        master,convergence=historical_inputs();result=pipeline(master,convergence)
        cls.review,cls.routes=result[8],result[5]
        cls.audit=audit_spread_movement(cls.csv,cls.review)
        cls.final=build_final_decisions(cls.review,cls.routes,cls.audit)

    def test_checkpoint_is_explicitly_synthetic_not_real_market_validation(self):
        self.assertEqual(hashlib.sha256((ROOT/self.cp['notebook']).read_bytes()).hexdigest(),self.cp['sha256'])
        raw=pd.read_csv(StringIO(self.csv))
        self.assertEqual(set(raw.Source),{'SYNTHETIC_TEST'})
        self.assertEqual(set(raw.Data_Status),{'FICTIONAL'})

    def test_saved_audit_counts(self):
        self.assertEqual(len(self.audit),14)
        self.assertEqual(self.audit.Market_Relationship.value_counts().to_dict(),{
            'CONFIRMS_MODEL':8,'CONFLICTS_WITH_MODEL':4,'NEUTRAL':2})
        self.assertEqual(int(self.audit.Key_Cross.sum()),8)

    def test_saved_final_classification_counts(self):
        self.assertEqual(len(self.final),14)
        self.assertEqual(self.final.Decision_Status.value_counts().to_dict(),{
            'CONFIRMED':5,'CONFIRMED_BUT_LARGE_SPREAD':3,'STRONG_MARKET_CONFLICT':3,'NEUTRAL_MARKET':2,'MARKET_CONFLICT':1})

    def test_all_saved_numeric_labels_and_visible_notes_match(self):
        for label,table in [('OLD CELL 43',self.audit),('OLD CELL 44',self.final)]:
            for expected in self.cp['samples'][label]:
                actual=table[table.Game==expected['Game']].iloc[0]
                for field,value in expected.items():
                    with self.subTest(label=label,game=expected['Game'],field=field):
                        if isinstance(value,(int,float)) and not isinstance(value,bool):
                            self.assertAlmostEqual(actual[field],value,delta=5e-7+1e-12)
                        elif isinstance(value,str) and value.endswith('...'):
                            self.assertTrue(str(actual[field]).startswith(value[:-3]))
                        else:self.assertEqual(actual[field],value)

    def test_full_checkpoint_identical_input_notebook_parity(self):
        env={'pd':pd,'display':lambda *a:None,'TARGET_WEEK':6,'df_phase1_review':self.review.copy(),
             'df_final_routes':self.routes.copy(),'covers_csv':self.csv}
        literal_cell(43,env);literal_cell(44,env)
        assert_frame_equal(self.audit,env['covers_audit'])
        assert_frame_equal(self.final,env['df_final_decision'])


class PipelineIntegrationTests(unittest.TestCase):
    def test_feature_tables_through_available_final_board_without_notebook_state(self):
        from cfb1.cfbd_features import build_feature_tables,merge_master_features
        from cfb1.bcf import parse_bcf_csv,normalize_bcf,merge_bcf
        from cfb1.model_signals import apply_epa_trigger,apply_fei_model,apply_fei_market_edges
        from cfb1.module3 import (apply_market_favorites,apply_havoc_trap,apply_lineyards_push,
                                 apply_explosiveness_fraud,apply_oay_day_edge,refresh_master_lineyards)
        from cfb1.convergence import corrected_convergence
        from cfb1.routing import route_markets,apply_large_spread_routing,separate_evidence
        from cfb1.spread_structure import classify_spread_structure,classify_large_spreads
        from cfb1.phase1 import build_phase1_shortlist,build_phase1_review
        features=build_feature_tables(json.loads((FIXTURES/'cfbd_feature_plays.json').read_text()),
                                      json.loads((FIXTURES/'cfbd_feature_advanced.json').read_text()))
        self.assertTrue(features.valid)
        market=pd.DataFrame([{'Game':'Alpha at Beta','game_id':123,'Away_Team':'Alpha','Home_Team':'Beta',
                              'Away_CFBD_Name':'B','Home_CFBD_Name':'A','DK_Spread':-3.,'FD_Spread':-3.}])
        master=apply_epa_trigger(merge_master_features(market,features))
        raw=parse_bcf_csv((FIXTURES/'bcf_segment_sample.csv').read_text())
        raw=raw[raw.Team.isin(['A','B'])].copy()
        master=apply_fei_market_edges(apply_fei_model(merge_bcf(master,normalize_bcf(raw,features.df_cfbd.team,market))))
        master=apply_havoc_trap(apply_market_favorites(master))
        master=refresh_master_lineyards(master,features.df_cfbd,expected_games=1)
        master=apply_oay_day_edge(apply_explosiveness_fraud(apply_lineyards_push(master)))
        routes=route_markets(corrected_convergence(master))
        master,_=classify_spread_structure(master,routes);master,_=classify_large_spreads(master,routes)
        routes=apply_large_spread_routing(routes,master)
        phase=build_phase1_shortlist(master,separate_evidence(routes));review=build_phase1_review(phase.candidates)
        self.assertEqual(len(review),1)
        record=current_record(away='B',home='A',current=-3.)
        proof=movement_pair(record,opening=-2.5)
        batch=prepare_market_audit(review,market,[record],{123:proof})
        final=build_available_final_decisions(review,routes,batch)
        self.assertEqual(len(final.decisions),1)
        self.assertEqual(final.decisions.Decision_Status.iloc[0],'CONFIRMED')
        self.assertTrue(final.pending_audit.empty)
        unavailable=prepare_market_audit(review,market,[record],{})
        self.assertTrue(production_ready(record))
        self.assertEqual(len(build_available_final_decisions(review,routes,unavailable).pending_audit),1)
        for field in ['Expected_ROI','Push_Adjusted_Win_Prob','CFB1_Win_Prob']:
            self.assertNotIn(field,final.decisions)


if __name__=='__main__':
    unittest.main()
