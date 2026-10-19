"""Offline threshold, direction, refresh integrity, and frozen-cell parity tests."""

import ast
from contextlib import redirect_stdout
from io import StringIO
import hashlib
import json
from pathlib import Path
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from cfb1.bcf import parse_bcf_csv, normalize_bcf, merge_bcf
from cfb1.cfbd_features import normalize_advanced_stats
from cfb1.model_signals import apply_epa_trigger, apply_fei_model, apply_fei_market_edges
from cfb1.module3 import (
    apply_market_favorites, refresh_defensive_lineyards, refresh_master_lineyards,
    apply_havoc_trap, apply_lineyards_push, apply_explosiveness_fraud,
    apply_oay_day_edge, signal_diagnostic, build_module3_board,
)
from cfb1.convergence import corrected_convergence

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"
SIGNALS = [apply_havoc_trap, apply_lineyards_push, apply_explosiveness_fraud, apply_oay_day_edge]
SUFFIXES = ["Havoc_Trap", "LineYards_Push", "Explosiveness_Fraud", "OAY_DAY_Edge"]


def all_signals(frame):
    for calculate in SIGNALS:
        frame = calculate(frame)
    return frame


def literal_cell(label, env):
    allowed = {f"OLD CELL {number}" for number in [23, 24, 25, 26, 27, 28, 30, 31, 34]}
    if label not in allowed:
        raise ValueError("Cell outside signal migration")
    notebook = json.loads((ROOT / "legacy/CFB1_Colab_Reference.ipynb").read_text())
    source = next("".join(c["source"]) for c in notebook["cells"]
                  if any(line.startswith("# " + label + " —") for line in c["source"]))
    with redirect_stdout(StringIO()):
        exec(compile(ast.parse(source), "frozen_" + label, "exec"), env)


def raw_advanced(frame):
    rows = []
    for _, row in frame.iterrows():
        for side in ["Away", "Home"]:
            rows.append({"team": row[f"{side}_CFBD_Name"], "offense": {
                "successRate": row[f"{side}_Off_SuccessRate"],
                "passingDowns": {"successRate": row[f"{side}_Off_PassingDown_SR"]},
                "explosiveness": row[f"{side}_Off_Explosiveness"],
                "lineYards": row[f"{side}_Off_LineYards"]}, "defense": {
                "successRate": row[f"{side}_Def_SuccessRate"],
                "passingDowns": {"successRate": .3},
                "havoc": {"total": row[f"{side}_Def_Havoc_Rate"]},
                "lineYards": row[f"{side}_Def_LineYards"]}})
    return rows


class SignalTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame(json.loads((FIXTURES / "module3_controlled.json").read_text()))

    def test_market_favorite_agree(self):
        result = apply_market_favorites(self.frame)
        self.assertEqual(result.DK_Market_Favorite.iloc[0], "Home0")
        self.assertTrue(result.DK_FEI_Market_Agree.iloc[0])

    def test_market_favorite_disagree(self):
        self.frame.loc[0, "DK_Spread"] = 3
        result = apply_market_favorites(self.frame)
        self.assertEqual(result.DK_Market_Favorite.iloc[0], "Away0")
        self.assertFalse(result.DK_FEI_Market_Agree.iloc[0])
        self.assertTrue(result.FD_FEI_Market_Agree.iloc[0])

    def test_even_model_and_pickem_are_different(self):
        result = apply_market_favorites(self.frame)
        self.assertEqual(result.DK_Market_Favorite.iloc[7], "PICKEM")
        self.assertFalse(result.DK_FEI_Market_Agree.iloc[7])

    def test_market_nan_spread_follows_legacy_pickem_fallthrough(self):
        # OLD CELL 23 gates outputs, not inputs. OLD CELL 21 is the input gate.
        self.frame.loc[0, "DK_Spread"] = float("nan")
        self.assertEqual(apply_market_favorites(self.frame).DK_Market_Favorite.iloc[0], "PICKEM")

    def test_market_selected_null_label_fails(self):
        self.frame.loc[0, "Home_Team"] = None
        with self.assertRaises(ValueError):
            apply_market_favorites(self.frame)

    def test_havoc_trigger_at_both_exact_thresholds(self):
        result = apply_havoc_trap(self.frame)
        self.assertTrue(result.Away_Havoc_Trap.iloc[1])
        self.assertFalse(result.Home_Havoc_Trap.iloc[1])

    def test_havoc_no_trigger_if_passing_down_success_too_high(self):
        self.frame.loc[1, "Away_Off_PassingDown_SR"] = .273000001
        self.assertFalse(apply_havoc_trap(self.frame).Away_Havoc_Trap.iloc[1])

    def test_havoc_no_trigger_if_opponent_havoc_too_low(self):
        self.frame.loc[1, "Home_Def_Havoc_Rate"] = .191999999
        self.assertFalse(apply_havoc_trap(self.frame).Away_Havoc_Trap.iloc[1])

    def test_havoc_home_symmetry(self):
        result = apply_havoc_trap(self.frame)
        self.assertTrue(result.Home_Havoc_Trap.iloc[5])
        self.assertTrue(result.Away_Havoc_Trap.iloc[5])

    def test_lineyards_combined_exact_thresholds_trigger(self):
        result = apply_lineyards_push(self.frame)
        self.assertTrue(result.Home_LineYards_Push.iloc[2])
        self.assertFalse(result.Away_LineYards_Push.iloc[2])

    def test_lineyards_offensive_threshold_alone_is_insufficient(self):
        self.frame.loc[2, "Away_Def_LineYards"] = 3.299999999
        self.assertFalse(apply_lineyards_push(self.frame).Home_LineYards_Push.iloc[2])

    def test_lineyards_defensive_threshold_alone_is_insufficient(self):
        self.frame.loc[2, "Home_Off_LineYards"] = 3.499999999
        self.assertFalse(apply_lineyards_push(self.frame).Home_LineYards_Push.iloc[2])

    def test_lineyards_away_symmetry_and_neutral(self):
        result = apply_lineyards_push(self.frame)
        self.assertTrue(result.Away_LineYards_Push.iloc[5])
        self.assertFalse(result.Away_LineYards_Push.iloc[0])
        self.assertFalse(result.Home_LineYards_Push.iloc[0])

    def test_fraud_triggers_at_all_exact_thresholds(self):
        self.assertTrue(apply_explosiveness_fraud(self.frame).Away_Explosiveness_Fraud.iloc[3])

    def test_fraud_requires_each_conjunct(self):
        for field, value in [("Away_Off_Explosiveness", 1.399999999),
                             ("Away_Off_SuccessRate", .420000001),
                             ("Home_Def_SuccessRate", .330000001)]:
            frame = self.frame.copy()
            frame.loc[3, field] = value
            with self.subTest(field=field):
                self.assertFalse(apply_explosiveness_fraud(frame).Away_Explosiveness_Fraud.iloc[3])

    def test_fraud_home_symmetry_and_no_trigger(self):
        result = apply_explosiveness_fraud(self.frame)
        self.assertTrue(result.Home_Explosiveness_Fraud.iloc[5])
        self.assertFalse(result.Home_Explosiveness_Fraud.iloc[0])

    def test_oay_day_away_exact_threshold_support(self):
        result = apply_oay_day_edge(self.frame)
        self.assertTrue(result.Away_OAY_DAY_Edge.iloc[4])
        self.assertFalse(result.Home_OAY_DAY_Edge.iloc[4])

    def test_oay_day_home_support(self):
        self.assertTrue(apply_oay_day_edge(self.frame).Home_OAY_DAY_Edge.iloc[5])

    def test_oay_day_requires_both_thresholds(self):
        for field, value in [("Away_OAY", .541249999), ("Home_DAY", .568249999)]:
            frame = self.frame.copy()
            frame.loc[4, field] = value
            with self.subTest(field=field):
                self.assertFalse(apply_oay_day_edge(frame).Away_OAY_DAY_Edge.iloc[4])

    def test_oay_day_neutral(self):
        result = apply_oay_day_edge(self.frame)
        self.assertFalse(result.Away_OAY_DAY_Edge.iloc[0])
        self.assertFalse(result.Home_OAY_DAY_Edge.iloc[0])

    def test_each_signal_rejects_every_missing_input(self):
        fields = [
            ["Away_Off_PassingDown_SR", "Home_Def_Havoc_Rate", "Home_Off_PassingDown_SR", "Away_Def_Havoc_Rate"],
            ["Away_Off_LineYards", "Home_Def_LineYards", "Home_Off_LineYards", "Away_Def_LineYards"],
            ["Away_Off_Explosiveness", "Away_Off_SuccessRate", "Home_Def_SuccessRate",
             "Home_Off_Explosiveness", "Home_Off_SuccessRate", "Away_Def_SuccessRate"],
            ["Away_OAY", "Home_DAY", "Home_OAY", "Away_DAY"],
        ]
        for calculate, columns in zip(SIGNALS, fields):
            for field in columns:
                frame = self.frame.copy()
                frame.loc[0, field] = float("nan")
                with self.subTest(function=calculate.__name__, field=field), self.assertRaises(ValueError):
                    calculate(frame)

    def test_missing_columns_are_not_invented(self):
        with self.assertRaises(KeyError):
            apply_havoc_trap(self.frame.drop(columns="Away_Off_PassingDown_SR"))

    def test_single_signal_board_label(self):
        board = build_module3_board(all_signals(self.frame))
        self.assertEqual(board.Away_Signals.iloc[1], "HAVOC_TRAP_NEGATIVE")
        self.assertEqual(board.Total_Module3_Signals.iloc[1], 1)
        self.assertEqual(board.Home_Signal_Count.iloc[1], 0)

    def test_multiple_signal_board_exact_label_order(self):
        board = build_module3_board(all_signals(self.frame))
        expected = "HAVOC_TRAP_NEGATIVE, LINE_YARDS_POSITIVE, EXPLOSIVENESS_FRAUD_NEGATIVE, OAY_DAY_POSITIVE"
        self.assertEqual(board.Away_Signals.iloc[5], expected)
        self.assertEqual(board.Home_Signals.iloc[5], expected)
        self.assertEqual(board.Total_Module3_Signals.iloc[5], 8)

    def test_neutral_board_uses_empty_strings_zero_counts(self):
        board = build_module3_board(all_signals(self.frame))
        self.assertEqual(board.Away_Signals.iloc[0], "")
        self.assertEqual(board.Home_Signals.iloc[0], "")
        self.assertEqual(board.Total_Module3_Signals.iloc[0], 0)

    def test_board_duplicate_game_labels_fail(self):
        frame = all_signals(self.frame)
        with self.assertRaises(ValueError):
            build_module3_board(pd.concat([frame, frame.iloc[:1]]))

    def test_board_missing_team_fails_required_output_gate(self):
        frame = all_signals(self.frame)
        frame.loc[0, "Away_Team"] = None
        with self.assertRaises(ValueError):
            build_module3_board(frame)

    def test_functions_preserve_input_and_do_not_add_routing_fields(self):
        before = self.frame.copy(deep=True)
        result = all_signals(apply_market_favorites(self.frame))
        assert_frame_equal(self.frame, before)
        self.assertEqual(result.context.tolist(), ["retain"] * 8)
        output = corrected_convergence(result)
        for name in ["Eligible_Market_Routes", "Final_Bet_Status", "Spread_Status", "Consensus_Spread", "Nearest_Key_Number"]:
            self.assertNotIn(name, output)
            self.assertNotIn(name, result)


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.master = pd.DataFrame(json.loads((FIXTURES / "module3_controlled.json").read_text()))
        self.advanced = raw_advanced(self.master)
        self.cfbd = pd.DataFrame([{"team": r["team"], "Off_LineYards": r["offense"]["lineYards"],
                                   "Def_LineYards": -99, "existing_feature": 4.} for r in self.advanced])
        self.lineyards = normalize_advanced_stats(self.advanced)[2]

    def test_derivation_reuses_frozen_payload_and_refresh_replaces_old_column(self):
        before = self.cfbd.copy()
        result = refresh_defensive_lineyards(self.cfbd, self.lineyards)
        self.assertEqual(result.Def_LineYards.iloc[0], self.advanced[0]["defense"]["lineYards"])
        self.assertEqual(result.existing_feature.iloc[0], 4.)
        self.assertEqual(result.columns.tolist().count("Def_LineYards"), 1)
        assert_frame_equal(before, self.cfbd)

    def test_source_duplicate_teams_raise_one_to_one(self):
        with self.assertRaises(pd.errors.MergeError):
            refresh_defensive_lineyards(self.cfbd, pd.concat([self.lineyards, self.lineyards.iloc[:1]]))

    def test_cfbd_duplicate_teams_raise_one_to_one(self):
        with self.assertRaises(pd.errors.MergeError):
            refresh_defensive_lineyards(pd.concat([self.cfbd, self.cfbd.iloc[:1]]), self.lineyards)

    def test_missing_source_lineyards_fails_even_outside_cfbd_table(self):
        line = self.lineyards.copy()
        line.loc[len(line)] = ["other", float("nan")]
        with self.assertRaises(ValueError):
            refresh_defensive_lineyards(self.cfbd, line)

    def test_absent_source_team_fails_merge_null_check(self):
        with self.assertRaises(ValueError):
            refresh_defensive_lineyards(self.cfbd, self.lineyards.iloc[1:])

    def test_master_refresh_preserves_enrichment_and_repeated_teams(self):
        frame = self.master.copy()
        frame["Home_Def_LineYards"] = -99
        cfbd = refresh_defensive_lineyards(self.cfbd, self.lineyards)
        result = refresh_master_lineyards(frame, cfbd, expected_games=len(frame))
        self.assertEqual(result.Home_Def_LineYards.iloc[0], 3.)
        self.assertEqual(result.context.tolist(), ["retain"] * 8)
        self.assertFalse(any(c.endswith("_x") or c.endswith("_y") for c in result))
        assert_frame_equal(frame, self.master.assign(Home_Def_LineYards=-99))

    def test_master_refresh_uses_target_slate_count(self):
        with self.assertRaises(ValueError):
            refresh_master_lineyards(self.master, self.lineyards, expected_games=99)

    def test_master_missing_canonical_team_fails(self):
        with self.assertRaises(ValueError):
            refresh_master_lineyards(self.master, self.lineyards.iloc[1:], expected_games=8)

    def test_master_duplicate_source_fails_many_to_one(self):
        with self.assertRaises(pd.errors.MergeError):
            refresh_master_lineyards(self.master, pd.concat([self.lineyards, self.lineyards.iloc[:1]]), expected_games=8)

    def test_master_duplicate_games_fail(self):
        master = pd.concat([self.master, self.master.iloc[:1]])
        with self.assertRaises(ValueError):
            refresh_master_lineyards(master, self.lineyards, expected_games=len(master))

    def test_derivation_missing_defense_yards_stays_null_then_fails(self):
        self.advanced[0]["defense"].pop("lineYards")
        line = normalize_advanced_stats(self.advanced)[2]
        self.assertTrue(pd.isna(line.Def_LineYards.iloc[0]))
        with self.assertRaises(ValueError):
            refresh_defensive_lineyards(self.cfbd, line)


class ConvergenceTests(unittest.TestCase):
    def setUp(self):
        self.frame = all_signals(pd.DataFrame(json.loads((FIXTURES / "module3_controlled.json").read_text())))

    def test_same_side_without_module3_support_is_retained(self):
        row = corrected_convergence(self.frame).iloc[0]
        self.assertTrue(row.EPA_FEI_Agree)
        self.assertEqual(row.Shared_Side, "Home0")
        self.assertEqual(row.M3_Support_Count, 0)
        self.assertEqual(row.M3_Conflict_Count, 0)

    def test_agreement_does_not_require_epa_trigger(self):
        self.assertFalse(self.frame.EPA_Trigger.iloc[0])
        self.assertTrue(corrected_convergence(self.frame).EPA_FEI_Agree.iloc[0])

    def test_direction_conflict_leaves_support_and_conflict_empty(self):
        row = corrected_convergence(self.frame).iloc[6]
        self.assertFalse(row.EPA_FEI_Agree)
        self.assertEqual(row.Shared_Side, "")
        self.assertEqual(row.M3_Support, "")
        self.assertEqual(row.M3_Conflict_Count, 0)

    def test_even_even_is_not_agreement(self):
        row = corrected_convergence(self.frame).iloc[7]
        self.assertFalse(row.EPA_FEI_Agree)
        self.assertEqual(row.Shared_Side, "")

    def test_even_directional_is_not_agreement(self):
        self.frame.loc[7, "DK_FEI_Edge_Team"] = "Home7"
        self.assertFalse(corrected_convergence(self.frame).EPA_FEI_Agree.iloc[7])

    def test_uses_dk_direction_even_if_fd_disagrees(self):
        self.frame.loc[0, "FD_FEI_Edge_Team"] = "Away0"
        self.assertTrue(corrected_convergence(self.frame).EPA_FEI_Agree.iloc[0])

    def test_opponent_havoc_is_support_for_home_shared_side(self):
        row = corrected_convergence(self.frame).iloc[1]
        self.assertEqual(row.M3_Support, "Away1 -HAVOC_TRAP")
        self.assertEqual(row.M3_Support_Count, 1)

    def test_own_lineyards_is_support(self):
        self.assertEqual(corrected_convergence(self.frame).M3_Support.iloc[2], "Home2 +LINE_YARDS")

    def test_opponent_fraud_is_support(self):
        self.assertEqual(corrected_convergence(self.frame).M3_Support.iloc[3], "Away3 -EXPLOSIVENESS_FRAUD")

    def test_opponent_positive_is_conflict(self):
        row = corrected_convergence(self.frame).iloc[4]
        self.assertEqual(row.M3_Conflict, "Away4 +OAY_DAY")
        self.assertEqual(row.M3_Conflict_Count, 1)
        self.assertTrue(row.EPA_FEI_Agree)

    def test_own_negative_is_conflict(self):
        self.frame.loc[1, ["EPA_Edge_Team", "DK_FEI_Edge_Team"]] = "Away1"
        row = corrected_convergence(self.frame).iloc[1]
        self.assertEqual(row.M3_Conflict, "Away1 -HAVOC_TRAP")
        self.assertEqual(row.Shared_Side, "Away1")

    def test_multiple_support_and_conflict_preserve_exact_order_home(self):
        row = corrected_convergence(self.frame).iloc[5]
        self.assertEqual(row.M3_Support, "Home5 +LINE_YARDS, Home5 +OAY_DAY, Away5 -HAVOC_TRAP, Away5 -EXPLOSIVENESS_FRAUD")
        self.assertEqual(row.M3_Conflict, "Home5 -HAVOC_TRAP, Home5 -EXPLOSIVENESS_FRAUD, Away5 +LINE_YARDS, Away5 +OAY_DAY")
        self.assertEqual((row.M3_Support_Count, row.M3_Conflict_Count), (4, 4))

    def test_multiple_support_and_conflict_preserve_exact_order_away(self):
        self.frame.loc[5, ["EPA_Edge_Team", "DK_FEI_Edge_Team"]] = "Away5"
        row = corrected_convergence(self.frame).iloc[5]
        self.assertEqual(row.M3_Support, "Away5 +LINE_YARDS, Away5 +OAY_DAY, Home5 -HAVOC_TRAP, Home5 -EXPLOSIVENESS_FRAUD")
        self.assertEqual(row.M3_Conflict, "Away5 -HAVOC_TRAP, Away5 -EXPLOSIVENESS_FRAUD, Home5 +LINE_YARDS, Home5 +OAY_DAY")

    def test_duplicates_fail(self):
        with self.assertRaises(ValueError):
            corrected_convergence(pd.concat([self.frame, self.frame.iloc[:1]]))

    def test_missing_direction_or_magnitude_fails(self):
        for field in ["EPA_Edge_Team", "DK_FEI_Edge_Team", "EPA_Edge_Value", "DK_FEI_Edge_Value"]:
            frame = self.frame.copy()
            frame.loc[0, field] = None
            with self.subTest(field=field), self.assertRaises(ValueError):
                corrected_convergence(frame)

    def test_counts_are_directional_not_total_board_flags(self):
        board = build_module3_board(self.frame)
        convergence = corrected_convergence(self.frame)
        self.assertEqual(board.Total_Module3_Signals.iloc[6], 1)
        self.assertEqual(convergence.M3_Support_Count.iloc[6], 0)
        self.assertEqual(convergence.M3_Conflict_Count.iloc[6], 0)


class ParityTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame(json.loads((FIXTURES / "module3_controlled.json").read_text()))

    def test_identical_input_parity_all_nine_cells_and_diagnostics(self):
        advanced = raw_advanced(self.frame)
        _, _, lineyards = normalize_advanced_stats(advanced)
        cfbd = pd.DataFrame([{"team": r["team"], "Off_LineYards": r["offense"]["lineYards"]} for r in advanced])
        env = {"pd": pd, "display": lambda *a: None, "TARGET_WEEK": 6, "DATA_THROUGH_WEEK": 5,
               "df_master_bcf": self.frame.copy(), "df_target_market": self.frame.copy(),
               "df_cfbd": cfbd.copy(), "adv_json": advanced}
        result = self.frame.copy()
        for label, calculate, suffix, diagnostic in [
            ("OLD CELL 23", apply_market_favorites, None, None),
            ("OLD CELL 24", apply_havoc_trap, "Havoc_Trap", "havoc_diagnostic"),
        ]:
            result = calculate(result)
            literal_cell(label, env)
            assert_frame_equal(result, env["df_master_bcf"])
            if suffix:
                assert_frame_equal(signal_diagnostic(result, suffix), env[diagnostic])
        literal_cell("OLD CELL 25", env)
        cfbd = refresh_defensive_lineyards(cfbd, lineyards)
        assert_frame_equal(cfbd, env["df_cfbd"])
        assert_frame_equal(lineyards, env["df_def_lineyards"])
        literal_cell("OLD CELL 26", env)
        result = refresh_master_lineyards(result, cfbd, expected_games=len(self.frame))
        assert_frame_equal(result, env["df_master_bcf"])
        for label, calculate, suffix, diagnostic in [
            ("OLD CELL 27", apply_lineyards_push, "LineYards_Push", "lineyards_diagnostic"),
            ("OLD CELL 28", apply_explosiveness_fraud, "Explosiveness_Fraud", "fraud_diagnostic"),
            ("OLD CELL 30", apply_oay_day_edge, "OAY_DAY_Edge", "oay_day_diagnostic"),
        ]:
            result = calculate(result)
            literal_cell(label, env)
            assert_frame_equal(result, env["df_master_bcf"])
            assert_frame_equal(signal_diagnostic(result, suffix), env[diagnostic])
        literal_cell("OLD CELL 31", env)
        board = build_module3_board(result)
        assert_frame_equal(board, env["df_module3_board"])
        assert_frame_equal(board[board.Total_Module3_Signals > 0].copy(), env["active_module3"])
        literal_cell("OLD CELL 34", env)
        assert_frame_equal(corrected_convergence(result), env["df_convergence_corrected"])

    def test_failure_parity_for_missing_signal_inputs(self):
        for label, calculate, field in [
            ("OLD CELL 24", apply_havoc_trap, "Away_Off_PassingDown_SR"),
            ("OLD CELL 27", apply_lineyards_push, "Away_Off_LineYards"),
            ("OLD CELL 28", apply_explosiveness_fraud, "Away_Off_Explosiveness"),
            ("OLD CELL 30", apply_oay_day_edge, "Away_OAY"),
        ]:
            frame = self.frame.copy()
            frame.loc[0, field] = float("nan")
            env = {"pd": pd, "display": lambda *a: None, "TARGET_WEEK": 6, "df_master_bcf": frame.copy()}
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    calculate(frame)
                with self.assertRaises(ValueError):
                    literal_cell(label, env)

    def test_no_signal_diagnostics_remain_empty_like_notebook(self):
        frame = all_signals(self.frame.iloc[:1])
        for suffix in SUFFIXES:
            diagnostic = signal_diagnostic(frame, suffix)
            self.assertTrue(diagnostic.empty)
            self.assertEqual(diagnostic.columns.tolist(), [])


class HistoricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp = json.loads((FIXTURES / "module3_notebook_checkpoint.json").read_text())
        cfbd = pd.DataFrame(cls.cp["feature_table"])
        master = pd.DataFrame(cls.cp["master_input"])
        raw = parse_bcf_csv((FIXTURES / "bcf_notebook_week5.csv").read_text())
        bcf = normalize_bcf(raw, cfbd.team, master)
        master = apply_epa_trigger(master)
        master = apply_fei_market_edges(apply_fei_model(merge_bcf(master, bcf)))
        cls.before = master.copy()
        master = apply_havoc_trap(apply_market_favorites(master))
        cls.cfbd = refresh_defensive_lineyards(cfbd, cfbd[["team", "Def_LineYards"]])
        cls.refreshed = refresh_master_lineyards(master, cls.cfbd, expected_games=57)
        cls.master = apply_oay_day_edge(apply_explosiveness_fraud(apply_lineyards_push(cls.refreshed)))
        cls.board = build_module3_board(cls.master)
        cls.convergence = corrected_convergence(cls.master)

    def assert_sample(self, frame, label, keys):
        for expected in self.cp["samples"][label]:
            mask = pd.Series(True, index=frame.index)
            for key in keys:
                mask &= frame[key] == expected[key]
            self.assertEqual(int(mask.sum()), 1, (label, expected))
            actual = frame[mask].iloc[0]
            for field, value in expected.items():
                with self.subTest(label=label, field=field, key=expected[keys[0]]):
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        self.assertAlmostEqual(actual[field], value, delta=5e-7 + 1e-12)
                    else:
                        self.assertEqual(actual[field], value)

    def test_notebook_hash_and_saved_counts_authority(self):
        self.assertEqual(hashlib.sha256((ROOT / self.cp["notebook"]).read_bytes()).hexdigest(), self.cp["sha256"])
        self.assertIn("EPA + FEI same side:                 37", self.cp["saved_streams"]["OLD CELL 34"])

    def test_market_favorite_saved_counts_and_all_disagreement_samples(self):
        self.assertEqual(int(self.master.DK_FEI_Market_Agree.sum()), 46)
        self.assertEqual(int(self.master.FD_FEI_Market_Agree.sum()), 46)
        self.assert_sample(self.master, "OLD CELL 23", ["Away_Team", "Home_Team"])

    def test_havoc_saved_counts_and_trigger_samples(self):
        self.assertEqual((int(self.master.Away_Havoc_Trap.sum()), int(self.master.Home_Havoc_Trap.sum())), (2, 1))
        self.assert_sample(signal_diagnostic(self.master, "Havoc_Trap"), "OLD CELL 24", ["Game", "Offense_In_Trap"])

    def test_lineyards_team_and_master_saved_samples(self):
        self.assert_sample(self.cfbd, "OLD CELL 25", ["team"])
        self.assert_sample(self.refreshed, "OLD CELL 26", ["Away_Team", "Home_Team"])

    def test_lineyards_push_counts_and_saved_samples(self):
        self.assertEqual((int(self.master.Away_LineYards_Push.sum()), int(self.master.Home_LineYards_Push.sum())), (1, 1))
        self.assert_sample(signal_diagnostic(self.master, "LineYards_Push"), "OLD CELL 27", ["Game", "Offense_With_Push"])

    def test_fraud_zero_matches_saved_stream(self):
        self.assertEqual(int(self.master.Away_Explosiveness_Fraud.sum()), 0)
        self.assertEqual(int(self.master.Home_Explosiveness_Fraud.sum()), 0)
        self.assertTrue(signal_diagnostic(self.master, "Explosiveness_Fraud").empty)

    def test_oay_day_counts_and_saved_samples(self):
        self.assertEqual((int(self.master.Away_OAY_DAY_Edge.sum()), int(self.master.Home_OAY_DAY_Edge.sum())), (4, 3))
        self.assert_sample(signal_diagnostic(self.master, "OAY_DAY_Edge"), "OLD CELL 30", ["Game", "Offense_With_Edge"])

    def test_module3_board_counts_labels_and_all_saved_active_rows(self):
        self.assertEqual(len(self.board), 57)
        self.assertEqual(int((self.board.Total_Module3_Signals > 0).sum()), 12)
        self.assertEqual(int((self.board.Total_Module3_Signals >= 2).sum()), 0)
        self.assert_sample(self.board, "OLD CELL 31", ["Game"])

    def test_convergence_counts_and_all_saved_active_samples(self):
        agreed = self.convergence[self.convergence.EPA_FEI_Agree]
        self.assertEqual(len(self.convergence), 57)
        self.assertEqual(len(agreed), 37)
        self.assertEqual(int((agreed.M3_Support_Count > 0).sum()), 10)
        self.assertEqual(int((agreed.M3_Conflict_Count > 0).sum()), 0)
        self.assert_sample(self.convergence, "OLD CELL 34", ["Game"])

    def test_full_historical_identical_input_parity(self):
        cfbd = pd.DataFrame(self.cp["feature_table"])
        # Re-expression of existing normalized line yards for literal OLD CELL 25;
        # not a claim that the original raw adv_json snapshot is available.
        advanced = [{"team": row.team, "defense": {"lineYards": row.Def_LineYards}}
                    for row in cfbd.itertuples()]
        env = {"pd": pd, "display": lambda *a: None, "TARGET_WEEK": 6, "DATA_THROUGH_WEEK": 5,
               "df_master_bcf": self.before.copy(), "df_target_market": self.before.copy(),
               "df_cfbd": cfbd, "adv_json": advanced}
        for number in [23, 24, 25, 26, 27, 28, 30, 31, 34]:
            literal_cell(f"OLD CELL {number}", env)
        assert_frame_equal(self.master, env["df_master_bcf"])
        assert_frame_equal(self.board, env["df_module3_board"])
        assert_frame_equal(self.convergence, env["df_convergence_corrected"])


if __name__ == "__main__":
    unittest.main()
