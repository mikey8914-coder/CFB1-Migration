"""Offline boundaries, literal-cell parity, and saved historical checkpoints."""

import ast
from contextlib import redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from cfb1.bcf import BCFValidationError, merge_bcf, normalize_bcf, parse_bcf_csv
from cfb1.model_signals import apply_epa_trigger, apply_fei_market_edges, apply_fei_model

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"
HEADER = "Team,FEI,OFEI,DFEI,SFEI,OAY,DAY\n"


def run_notebook_cell(label, environment):
    """Only the six allowed source cells; substitute the manual CSV fixture."""
    allowed = {"CELL 12", "CELL 13", "CELL 14", "OLD CELL 19", "OLD CELL 20", "OLD CELL 21"}
    if label not in allowed:
        raise ValueError("Cell outside migration scope")
    notebook = json.loads((ROOT / "legacy/CFB1_Colab_Reference.ipynb").read_text())
    source = next("".join(c["source"]) for c in notebook["cells"]
                  if any(line.startswith("# " + label + " —") for line in c["source"]))
    tree = ast.parse(source)
    if label == "CELL 13":
        tree.body = [node for node in tree.body if not (isinstance(node, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "bcf_csv" for t in node.targets))]
    with redirect_stdout(StringIO()):
        exec(compile(tree, "frozen_" + label, "exec"), environment)


def fixture_master():
    rows = []
    for i, (home, away, edge, dk, fd) in enumerate([
        ("A", "B", .12, -3, -3), ("B", "A", -.12, 3, 3),
        ("A", "B", .119999999, -9, -8), ("A", "B", 0, -9, -9),
        ("A", "B", .2, -8, -10), ("B", "A", -.2, 8, 10),
    ]):
        rows.append({"Home_Team": home + str(i), "Away_Team": away + str(i),
                     "Home_CFBD_Name": home, "Away_CFBD_Name": away,
                     "Net_EPA_Edge_Home": edge, "Home_Net_EPA_Margin": edge,
                     "Away_Net_EPA_Margin": 0., "DK_Spread": float(dk),
                     "FD_Spread": float(fd), "existing_context": "keep"})
    return pd.DataFrame(rows)


class SegmentTests(unittest.TestCase):
    def setUp(self):
        self.csv = (FIXTURES / "bcf_segment_sample.csv").read_text()
        self.master = fixture_master()
        self.universe = ["A", "B", "App State", "UConn"]

    def bcf(self):
        return normalize_bcf(parse_bcf_csv(self.csv), self.universe, self.master)

    def fei(self):
        return apply_fei_model(merge_bcf(self.master, self.bcf()))

    def test_epa_positive_trigger_uses_home_raw_label(self):
        result = apply_epa_trigger(self.master)
        self.assertTrue(result.EPA_Trigger.iloc[0])
        self.assertEqual(result.EPA_Edge_Team.iloc[0], "A0")
        self.assertEqual(result.EPA_Edge_Value.iloc[0], .12)

    def test_epa_negative_trigger_uses_away_raw_label(self):
        result = apply_epa_trigger(self.master)
        self.assertTrue(result.EPA_Trigger.iloc[1])
        self.assertEqual(result.EPA_Edge_Team.iloc[1], "A1")
        self.assertEqual(result.EPA_Edge_Value.iloc[1], .12)

    def test_epa_below_threshold_has_direction_but_no_trigger(self):
        result = apply_epa_trigger(self.master)
        self.assertFalse(result.EPA_Trigger.iloc[2])
        self.assertEqual(result.EPA_Edge_Team.iloc[2], "A2")

    def test_epa_zero_is_even_and_false(self):
        result = apply_epa_trigger(self.master)
        self.assertEqual(result.EPA_Edge_Team.iloc[3], "EVEN")
        self.assertFalse(result.EPA_Trigger.iloc[3])

    def test_epa_exact_signed_thresholds_inclusive_without_rounding(self):
        self.master["Net_EPA_Edge_Home"] = [.12, -.12, .119999999, -.119999999, 0., .120000001]
        self.assertEqual(apply_epa_trigger(self.master).EPA_Trigger.tolist(), [True, True, False, False, False, True])

    def test_epa_null_edge_is_rejected_not_classified_as_valid_even(self):
        self.master.loc[0, "Net_EPA_Edge_Home"] = float("nan")
        with self.assertRaises(ValueError):
            apply_epa_trigger(self.master)

    def test_epa_missing_column_rejected(self):
        with self.assertRaisesRegex(ValueError, "Net_EPA_Edge_Home"):
            apply_epa_trigger(self.master.drop(columns="Net_EPA_Edge_Home"))

    def test_epa_selected_null_team_fails_legacy_gate(self):
        self.master.loc[0, "Home_Team"] = None
        with self.assertRaises(ValueError):
            apply_epa_trigger(self.master)

    def test_valid_seven_column_ingestion(self):
        raw = parse_bcf_csv(self.csv)
        self.assertEqual(raw.columns.tolist(), ["Team", "FEI", "OFEI", "DFEI", "SFEI", "OAY", "DAY"])
        self.assertEqual(len(raw), 4)
        self.assertEqual(raw.FEI.iloc[0], .4)
        self.assertTrue(pd.api.types.is_numeric_dtype(raw.FEI))

    def test_bcf_numeric_strings_are_coerced(self):
        raw = parse_bcf_csv(HEADER + 'A," .4 ",.2,.1,.0,.5,.4\n')
        self.assertEqual(raw.FEI.iloc[0], .4)

    def test_bcf_extra_columns_survive_ingestion(self):
        raw = parse_bcf_csv(HEADER.rstrip() + ",Note\nA,.4,.2,.1,.0,.5,.4,manual\n")
        self.assertEqual(raw.Note.iloc[0], "manual")

    def test_missing_placeholder_and_header_only_inputs_fail(self):
        for text in ["", "  ", "PASTE THE GEM CSV HERE", HEADER]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_bcf_csv(text)

    def test_missing_required_column_fails(self):
        with self.assertRaises(BCFValidationError) as cm:
            parse_bcf_csv("Team,FEI\nA,.4\n")
        self.assertIn("OFEI", cm.exception.diagnostics["missing_columns"])

    def test_duplicate_raw_team_rows_fail_without_deduplication(self):
        with self.assertRaises(BCFValidationError) as cm:
            parse_bcf_csv(HEADER + "A,.4,.2,.1,.0,.5,.4\nA,.4,.2,.1,.0,.5,.4\n")
        self.assertEqual(cm.exception.diagnostics["duplicate_raw_team_rows"], 2)

    def test_duplicate_check_precedes_whitespace_cleanup(self):
        raw = parse_bcf_csv(HEADER + " A,.4,.2,.1,.0,.5,.4\nA,.4,.2,.1,.0,.5,.4\n")
        self.assertEqual(raw.Team.tolist(), ["A", "A"])
        with self.assertRaises(BCFValidationError) as cm:
            normalize_bcf(raw, ["A"], self.master.iloc[:0])
        self.assertEqual(cm.exception.diagnostics["duplicate_normalized_rows"], 2)

    def test_malformed_or_null_numeric_fields_fail(self):
        for value in ["oops", "", "NA"]:
            with self.subTest(value=value), self.assertRaises(BCFValidationError) as cm:
                parse_bcf_csv(HEADER + f"A,{value},.2,.1,.0,.5,.4\n")
            self.assertEqual(cm.exception.diagnostics["numeric_problems"]["FEI"], 1)

    def test_missing_team_becomes_nan_text_then_fails_universe_membership(self):
        raw = parse_bcf_csv(HEADER + ",.4,.2,.1,.0,.5,.4\n")
        self.assertEqual(raw.Team.iloc[0], "nan")
        with self.assertRaises(BCFValidationError):
            normalize_bcf(raw, self.universe, self.master)

    def test_normalization_uses_shared_bcf_map_and_preserves_raw_names(self):
        raw = parse_bcf_csv(self.csv)
        result = normalize_bcf(raw, self.universe, self.master)
        self.assertEqual(result.CFBD_Team.tolist(), ["A", "B", "App State", "UConn"])
        self.assertEqual(result.Team.tolist(), raw.Team.tolist())
        self.assertNotIn("CFBD_Team", raw)

    def test_all_five_legacy_bcf_mappings(self):
        names = ["Appalachian State", "Connecticut", "Hawaii", "San Jose State", "Southern Mississippi"]
        targets = ["App State", "UConn", "Hawai'i", "San José State", "Southern Miss"]
        raw = parse_bcf_csv(HEADER + "".join(n + ",0,0,0,0,0,0\n" for n in names))
        self.assertEqual(normalize_bcf(raw, targets, self.master.iloc[:0]).CFBD_Team.tolist(), targets)

    def test_normalization_does_not_apply_market_aliases_or_collapse_spaces(self):
        for name in ["Miami Hurricanes", "Unknown  Team"]:
            raw = parse_bcf_csv(HEADER + name + ",0,0,0,0,0,0\n")
            with self.subTest(name=name), self.assertRaises(BCFValidationError):
                normalize_bcf(raw, ["Miami", "Unknown Team"], self.master.iloc[:0])

    def test_normalized_alias_collision_fails(self):
        raw = parse_bcf_csv(HEADER + "Connecticut,0,0,0,0,0,0\nUConn,0,0,0,0,0,0\n")
        with self.assertRaises(BCFValidationError) as cm:
            normalize_bcf(raw, ["UConn"], self.master.iloc[:0])
        self.assertEqual(cm.exception.diagnostics["duplicate_normalized_rows"], 2)

    def test_unmatched_non_slate_bcf_team_still_fails(self):
        raw = parse_bcf_csv(self.csv + "Unknown,0,0,0,0,0,0\n")
        with self.assertRaises(BCFValidationError) as cm:
            normalize_bcf(raw, self.universe, self.master)
        self.assertEqual(cm.exception.diagnostics["unmatched_rows"][0]["Team"], "Unknown")

    def test_missing_target_team_fails_normalization(self):
        raw = parse_bcf_csv(self.csv)
        with self.assertRaises(BCFValidationError) as cm:
            normalize_bcf(raw[raw.Team != "B"], self.universe, self.master)
        self.assertEqual(cm.exception.diagnostics["missing_target_teams"], ["B"])

    def test_bcf_merge_preserves_game_count_context_and_all_six_metrics(self):
        result = merge_bcf(self.master, self.bcf())
        self.assertEqual(len(result), 6)
        self.assertEqual(result.existing_context.tolist(), ["keep"] * 6)
        self.assertEqual(result.Home_FEI.iloc[0], .4)
        self.assertEqual(result.Away_FEI.iloc[0], .1)
        for side in ["Home", "Away"]:
            for metric in ["FEI", "OFEI", "DFEI", "SFEI", "OAY", "DAY"]:
                self.assertIn(side + "_" + metric, result)

    def test_merge_missing_fei_fails(self):
        bcf = self.bcf()
        bcf.loc[bcf.CFBD_Team == "B", "FEI"] = float("nan")
        with self.assertRaises(BCFValidationError):
            merge_bcf(self.master, bcf)

    def test_merge_missing_team_fails_without_dropping_game(self):
        bcf = self.bcf()
        with self.assertRaises(BCFValidationError):
            merge_bcf(self.master, bcf[bcf.CFBD_Team != "B"])

    def test_merge_duplicate_source_rejected_by_many_to_one(self):
        bcf = self.bcf()
        with self.assertRaises(pd.errors.MergeError):
            merge_bcf(self.master, pd.concat([bcf, bcf.iloc[:1]]))

    def test_merge_duplicate_game_pairs_rejected(self):
        with self.assertRaises(BCFValidationError):
            merge_bcf(pd.concat([self.master, self.master.iloc[:1]]), self.bcf())

    def test_merge_guard_is_fei_only_as_in_notebook(self):
        bcf = self.bcf()
        bcf.loc[0, "OFEI"] = float("nan")
        self.assertTrue(pd.isna(merge_bcf(self.master, bcf).Home_OFEI.iloc[0]))

    def test_fei_multiplier_and_home_polarity(self):
        result = self.fei()
        self.assertEqual(result.FEI_Model_Diff_Home.iloc[:2].tolist(), [9., -9.])
        self.assertEqual(result.FEI_Model_Favorite.iloc[:2].tolist(), ["A0", "A1"])
        self.assertEqual(result.FEI_Model_Margin.iloc[:2].tolist(), [9., 9.])

    def test_fei_zero_and_rounding_to_zero_classify_even(self):
        frame = merge_bcf(self.master, self.bcf())
        frame.loc[0, ["Home_FEI", "Away_FEI"]] = [0., 0.]
        frame.loc[1, ["Home_FEI", "Away_FEI"]] = [.001, 0.]
        result = apply_fei_model(frame)
        self.assertEqual(result.FEI_Model_Diff_Home.iloc[:2].tolist(), [0., 0.])
        self.assertEqual(result.FEI_Model_Favorite.iloc[:2].tolist(), ["EVEN", "EVEN"])

    def test_fei_pandas_rounding_happens_before_favorite_selection(self):
        frame = merge_bcf(self.master, self.bcf())
        frame.loc[0, ["Home_FEI", "Away_FEI"]] = [.107, 0.]
        frame.loc[1, ["Home_FEI", "Away_FEI"]] = [-.107, 0.]
        self.assertEqual(apply_fei_model(frame).FEI_Model_Diff_Home.iloc[:2].tolist(), [3.2, -3.2])

    def test_fei_null_and_missing_inputs_fail(self):
        frame = merge_bcf(self.master, self.bcf())
        frame.loc[0, "Home_FEI"] = float("nan")
        with self.assertRaises(ValueError):
            apply_fei_model(frame)
        with self.assertRaisesRegex(ValueError, "Away_FEI"):
            apply_fei_model(frame.drop(columns="Away_FEI"))

    def test_fei_market_home_spread_and_direction(self):
        result = apply_fei_market_edges(self.fei())
        self.assertEqual(result.FEI_Model_Home_Spread.iloc[:2].tolist(), [-9., 9.])
        self.assertEqual(result.DK_FEI_Edge_Home.iloc[:2].tolist(), [6., -6.])
        self.assertEqual(result.DK_FEI_Edge_Team.iloc[:2].tolist(), ["A0", "A1"])
        self.assertEqual(result.DK_FEI_Edge_Value.iloc[:2].tolist(), [6., 6.])

    def test_fei_market_zero_edge_is_even_not_pickem(self):
        result = apply_fei_market_edges(self.fei())
        self.assertEqual(result.DK_FEI_Edge_Team.iloc[3], "EVEN")
        self.assertEqual(result.FD_FEI_Edge_Team.iloc[3], "EVEN")
        self.assertTrue(result.FEI_Books_Agree.iloc[3])
        self.assertEqual(result.DK_FEI_Edge_Value.iloc[3], 0.)

    def test_fei_books_agreement_compares_labels_including_even(self):
        result = apply_fei_market_edges(self.fei())
        self.assertFalse(result.FEI_Books_Agree.iloc[2])  # EVEN vs HOME
        self.assertFalse(result.FEI_Books_Agree.iloc[4])  # HOME vs AWAY
        self.assertTrue(result.FEI_Books_Agree.iloc[0])

    def test_fei_market_null_or_missing_book_fails_without_fallback(self):
        frame = self.fei()
        frame.loc[0, "FD_Spread"] = float("nan")
        with self.assertRaises(ValueError):
            apply_fei_market_edges(frame)
        with self.assertRaisesRegex(ValueError, "FD_Spread"):
            apply_fei_market_edges(frame.drop(columns="FD_Spread"))

    def test_functions_do_not_mutate_inputs_or_add_later_stage_outputs(self):
        original = self.master.copy(deep=True)
        with_epa = apply_epa_trigger(self.master)
        output = apply_fei_market_edges(apply_fei_model(merge_bcf(with_epa, self.bcf())))
        assert_frame_equal(self.master, original)
        self.assertNotIn("EPA_Trigger", self.master)
        for field in ["DK_Market_Favorite", "FEI_Market_Agree", "Home_Havoc_Trap", "M3_Support_Count", "Consensus_Spread"]:
            self.assertNotIn(field, output)

    def test_literal_frozen_cells_match_controlled_fixture_pipeline(self):
        env = {"pd": pd, "display": lambda *args: None, "TARGET_WEEK": 6,
               "DATA_THROUGH_WEEK": 5, "df_master": self.master.copy(),
               "bcf_csv": self.csv, "cfbd_teams": set(self.universe), "df_target_market": self.master.copy()}
        extracted_epa = apply_epa_trigger(self.master)
        run_notebook_cell("CELL 12", env)
        assert_frame_equal(extracted_epa, env["df_master"])
        run_notebook_cell("CELL 13", env)
        assert_frame_equal(parse_bcf_csv(self.csv), env["df_bcf_raw"])
        run_notebook_cell("CELL 14", env)
        assert_frame_equal(self.bcf(), env["df_bcf"])
        run_notebook_cell("OLD CELL 19", env)
        merged = merge_bcf(extracted_epa, self.bcf())
        assert_frame_equal(merged, env["df_master_bcf"])
        run_notebook_cell("OLD CELL 20", env)
        modeled = apply_fei_model(merged)
        assert_frame_equal(modeled, env["df_master_bcf"])
        run_notebook_cell("OLD CELL 21", env)
        assert_frame_equal(apply_fei_market_edges(modeled), env["df_master_bcf"])

    def test_failure_gates_match_literal_notebook_for_null_epa_and_fei(self):
        for label, field, production in [("CELL 12", "Net_EPA_Edge_Home", apply_epa_trigger),
                                          ("OLD CELL 20", "Home_FEI", apply_fei_model),
                                          ("OLD CELL 21", "DK_Spread", apply_fei_market_edges)]:
            frame = self.master.copy() if label == "CELL 12" else self.fei()
            frame.loc[0, field] = float("nan")
            env = {"pd": pd, "display": lambda *args: None,
                   "df_master": frame.copy(), "df_master_bcf": frame.copy()}
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    production(frame)
                with self.assertRaises(ValueError):
                    run_notebook_cell(label, env)


class HistoricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint = json.loads((FIXTURES / "epa_bcf_fei_notebook_checkpoint.json").read_text())
        cls.csv = (FIXTURES / "bcf_notebook_week5.csv").read_text()

    def historical_pipeline(self):
        cp = self.checkpoint
        master = apply_epa_trigger(pd.DataFrame(cp["cfbd_epa_replay_input"]))
        bcf = normalize_bcf(parse_bcf_csv(self.csv), cp["canonical_team_names"], master)
        return apply_fei_market_edges(apply_fei_model(merge_bcf(master, bcf)))

    def assert_saved_sample(self, actual, sample):
        for expected in sample:
            row = actual[(actual.Home_Team == expected["Home_Team"]) & (actual.Away_Team == expected["Away_Team"])].iloc[0]
            for column, value in expected.items():
                with self.subTest(game=expected["Home_Team"], field=column):
                    if isinstance(value, (float, int)) and not isinstance(value, bool):
                        self.assertAlmostEqual(row[column], value, delta=5e-7 + 1e-12)
                    else:
                        self.assertEqual(row[column], value)

    def test_fixture_authority_and_manual_bcf_match_frozen_notebook(self):
        path = ROOT / self.checkpoint["notebook"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.checkpoint["sha256"])
        source = next("".join(c["source"]) for c in json.loads(path.read_text())["cells"]
                      if any(line.startswith("# CELL 13 —") for line in c["source"]))
        csv = next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "bcf_csv" for t in n.targets))
        self.assertEqual(self.csv.strip(), csv.strip())

    def test_saved_epa_top15_classifications_and_values(self):
        # Use the signed edges actually displayed by CELL 12, not a later
        # upstream CFBD replay, to isolate this stage's historical formula.
        saved = pd.DataFrame(self.checkpoint["epa_sample"])
        inputs = saved.drop(columns=["EPA_Edge_Team", "EPA_Edge_Value", "EPA_Trigger"])
        self.assert_saved_sample(apply_epa_trigger(inputs), self.checkpoint["epa_sample"])

    def test_upstream_cfbd_replay_discrepancy_is_explicit_and_classifications_stable(self):
        actual = self.historical_pipeline()
        differences = []
        for expected in self.checkpoint["epa_sample"]:
            row = actual[(actual.Home_Team == expected["Home_Team"]) &
                         (actual.Away_Team == expected["Away_Team"])].iloc[0]
            self.assertEqual(row.EPA_Edge_Team, expected["EPA_Edge_Team"])
            self.assertEqual(row.EPA_Trigger, expected["EPA_Trigger"])
            for field in ["Home_Net_EPA_Margin", "Away_Net_EPA_Margin", "Net_EPA_Edge_Home", "EPA_Edge_Value"]:
                if abs(row[field] - expected[field]) > 5e-7 + 1e-12:
                    differences.append((expected["Home_Team"], field))
        self.assertEqual(differences, [
            ("Georgia Southern Eagles", "Home_Net_EPA_Margin"),
            ("Georgia Southern Eagles", "Net_EPA_Edge_Home"),
            ("Georgia Southern Eagles", "EPA_Edge_Value"),
        ])

    def test_historical_replay_epa_counts_match_saved_counts(self):
        result = self.historical_pipeline()
        self.assertEqual(len(result), 57)
        self.assertEqual(int(result.EPA_Trigger.sum()), 33)
        self.assertEqual(int((~result.EPA_Trigger).sum()), 24)

    def test_historical_bcf_ingestion_normalization_and_merge_counts(self):
        raw = parse_bcf_csv(self.csv)
        self.assertEqual(len(raw), 138)
        result = self.historical_pipeline()
        self.assertEqual(len(result), 57)
        self.assertFalse(result[["Home_FEI", "Away_FEI"]].isna().any().any())
        self.assertFalse(result.duplicated(["Home_Team", "Away_Team"]).any())
        self.assert_saved_sample(result, self.checkpoint["bcf_merge_sample"])

    def test_saved_fei_model_samples(self):
        self.assert_saved_sample(self.historical_pipeline(), self.checkpoint["fei_model_sample"])

    def test_saved_fei_market_samples_and_agreement_counts(self):
        result = self.historical_pipeline()
        self.assert_saved_sample(result, self.checkpoint["fei_market_sample"])
        self.assertEqual(int(result.FEI_Books_Agree.sum()), 57)

    def test_full_historical_fei_can_replay_from_notebook_only_inputs(self):
        cp = self.checkpoint
        market = pd.DataFrame(cp["target_market"])
        # Full FEI does not need recreated EPA/CFBD numeric values.
        from cfb1.team_identity import normalize_team_name
        market["Home_CFBD_Name"] = market.Home_Team.map(normalize_team_name)
        market["Away_CFBD_Name"] = market.Away_Team.map(normalize_team_name)
        bcf = normalize_bcf(parse_bcf_csv(self.csv), cp["canonical_team_names"], market)
        actual = apply_fei_market_edges(apply_fei_model(merge_bcf(market, bcf)))
        self.assert_saved_sample(actual, cp["fei_model_sample"])
        self.assert_saved_sample(actual, cp["fei_market_sample"])
        self.assertEqual(int(actual.FEI_Books_Agree.sum()), 57)


if __name__ == "__main__":
    unittest.main()
