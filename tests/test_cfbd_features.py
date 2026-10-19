"""Offline fixture, literal notebook parity, boundary, and acquisition tests."""

import ast
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from cfb1.cfbd_features import (
    ADVANCED_FIELDS, FeatureBoundary, acquire_cfbd_features, aggregate_play_ppa,
    build_feature_tables, merge_master_features, normalize_advanced_stats,
)
from cfb1.cfbd_schedule import CFBDAcquisitionError
from cfb1.features_live import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.plays = json.loads((FIXTURES / "cfbd_feature_plays.json").read_text())
        self.advanced = json.loads((FIXTURES / "cfbd_feature_advanced.json").read_text())
        self.market = pd.DataFrame([
            {"Home_Team": "A raw", "Away_Team": "B raw", "Home_CFBD_Name": "A",
             "Away_CFBD_Name": "B", "DK_Spread": -3.5, "FD_Spread": -3.0, "existing_context": "retain"},
        ])

    def build(self):
        return build_feature_tables(self.plays, self.advanced)

    def test_offense_is_play_weighted_mean_without_deduplication(self):
        r = self.build()
        self.assertAlmostEqual(r.df_off_ppa.set_index("team").loc["A", "Off_EPA"], 7 / 3)
        self.assertEqual(r.df_off_ppa.set_index("team").loc["B", "Off_EPA"], 0)
        self.assertEqual(r.report["valid_ppa_rows"], 6)
        self.assertEqual(r.report["play_records"], 9)

    def test_defense_is_opponent_ppa_not_negated(self):
        r = self.build()
        self.assertEqual(r.df_def_ppa.set_index("team").loc["B", "Def_EPA"], 2.25)
        self.assertEqual(r.df_def_ppa.set_index("team").loc["A", "Def_EPA"], 0)

    def test_null_triples_are_excluded_from_both_aggregations(self):
        valid = self.build().df_ppa_valid
        self.assertFalse(valid[["offense", "defense", "ppa"]].isna().any().any())
        self.assertNotIn(99, valid.ppa.tolist())

    def test_outer_ppa_join_preserves_one_sided_teams(self):
        r = self.build()
        c = r.df_ppa.set_index("team").loc["C"]
        self.assertEqual(c.Off_EPA, 2)
        self.assertTrue(pd.isna(c.Def_EPA))

    def test_advanced_paths_and_defensive_lineyards(self):
        _, clean, line = normalize_advanced_stats(self.advanced)
        self.assertEqual(list(clean.columns), ["team", *ADVANCED_FIELDS])
        self.assertEqual(clean.iloc[0].to_dict(), {
            "team": "A", "Off_SuccessRate": .45, "Off_PassingDown_SR": .3,
            "Off_Explosiveness": 1.2, "Def_SuccessRate": .4,
            "Def_PassingDown_SR": .2, "Def_Havoc_Rate": .18, "Off_LineYards": 3.4,
        })
        self.assertEqual(line.Def_LineYards.tolist(), [2.8, 3.6])

    def test_inner_merge_does_not_invent_missing_team_features(self):
        self.advanced.append({**deepcopy(self.advanced[0]), "team": "D"})
        r = self.build()
        self.assertEqual(r.df_cfbd.team.tolist(), ["A", "B"])
        self.assertEqual(r.report["ppa_only_teams"], ["C"])
        self.assertEqual(r.report["advanced_only_teams"], ["D"])
        self.assertTrue(r.valid)  # Legacy gate does not require equal source universes.

    def test_net_epa_margin_exact_subtraction(self):
        r = self.build()
        assert_frame_equal(
            r.df_cfbd[["Net_EPA_Margin"]],
            (r.df_cfbd.Off_EPA - r.df_cfbd.Def_EPA).to_frame("Net_EPA_Margin"),
        )
        self.assertAlmostEqual(r.df_cfbd.set_index("team").loc["A", "Net_EPA_Margin"], 7 / 3)
        self.assertEqual(r.df_cfbd.set_index("team").loc["B", "Net_EPA_Margin"], -2.25)

    def test_duplicate_advanced_teams_are_not_silently_deduplicated(self):
        self.advanced.append(deepcopy(self.advanced[0]))
        r = self.build()
        self.assertFalse(r.valid)
        self.assertEqual(r.report["duplicate_team_rows"], 2)
        self.assertEqual(r.report["defensive_lineyards_duplicate_rows"], 2)
        self.assertEqual(r.report["merged_rows"], 3)
        with self.assertRaises(ValueError):
            merge_master_features(self.market, r)

    def test_critical_null_is_not_imputed(self):
        self.advanced[0]["offense"]["successRate"] = None
        r = self.build()
        self.assertFalse(r.valid)
        self.assertEqual(r.report["critical_nulls"]["Off_SuccessRate"], 1)

    def test_missing_defensive_lineyards_fails_source_validation(self):
        del self.advanced[0]["defense"]["lineYards"]
        r = self.build()
        self.assertFalse(r.valid)
        self.assertTrue(r.report["efficiency_matrix_pass"])
        self.assertEqual(r.report["defensive_lineyards_source_nulls"], 1)
        self.assertEqual(r.report["defensive_lineyards_merge_nulls"], 1)

    def test_missing_ppa_side_inside_merged_universe_fails(self):
        self.advanced.append({**deepcopy(self.advanced[0]), "team": "C"})
        r = self.build()
        self.assertFalse(r.valid)
        self.assertEqual(r.report["critical_nulls"]["Def_EPA"], 1)
        self.assertEqual(r.report["critical_nulls"]["Net_EPA_Margin"], 1)

    def test_null_team_is_not_normalized_to_a_string(self):
        self.advanced[0]["team"] = None
        r = self.build()
        self.assertNotIn("None", r.df_cfbd.team.tolist())
        self.assertEqual(r.df_cfbd.team.tolist(), ["B"])

    def test_missing_schema_and_empty_payloads_fail(self):
        for plays, advanced in [([], self.advanced), ([{"offense": "A"}], self.advanced),
                                (self.plays, []), (self.plays, [{"team": "A"}])]:
            with self.subTest(plays=bool(plays), advanced=bool(advanced)):
                with self.assertRaises(ValueError):
                    build_feature_tables(plays, advanced)

    def test_all_null_ppa_is_invalid_not_a_valid_empty_matrix(self):
        for row in self.plays:
            row["ppa"] = None
        self.assertFalse(self.build().valid)

    def test_master_left_joins_preserve_rows_context_and_home_polarity(self):
        master = merge_master_features(self.market, self.build())
        self.assertEqual(len(master), 1)
        self.assertEqual(master.existing_context.iloc[0], "retain")
        self.assertEqual(master.DK_Spread.iloc[0], -3.5)
        self.assertAlmostEqual(master.Net_EPA_Edge_Home.iloc[0], 7 / 3 + 2.25)
        self.assertEqual(master.Home_Def_LineYards.iloc[0], 2.8)
        self.assertNotIn("EPA_Trigger", master)

    def test_master_missing_team_fails_without_fabrication(self):
        self.market.loc[0, "Away_CFBD_Name"] = "Missing"
        with self.assertRaisesRegex(ValueError, "merge failed"):
            merge_master_features(self.market, self.build())

    def test_master_duplicate_game_pairs_fail(self):
        with self.assertRaisesRegex(ValueError, "merge failed"):
            merge_master_features(pd.concat([self.market, self.market]), self.build())

    def test_master_repeated_team_across_distinct_games_is_many_to_one(self):
        second = self.market.copy()
        second["Away_Team"] = "another raw game"
        self.assertEqual(len(merge_master_features(pd.concat([self.market, second]), self.build())), 2)

    def test_cfbd_names_remain_exact_without_market_aliasing(self):
        for row in self.plays:
            if row["offense"] == "A":
                row["offense"] = " A "
        r = self.build()
        self.assertIn(" A ", r.df_ppa.team.tolist())
        self.assertFalse(r.valid)

    def test_request_plan_freezes_completed_weeks_excluding_week_zero_and_target(self):
        plan = FeatureBoundary(2026, 5, 6).request_plan()
        self.assertEqual([p["week"] for path, p in plan if path == "/plays"], [1, 2, 3, 4, 5])
        self.assertTrue(all(p["year"] == 2026 and p["seasonType"] == "regular" for _, p in plan))
        self.assertEqual(plan[-1], ("/stats/season/advanced", {
            "year": 2026, "seasonType": "regular", "startWeek": 1, "endWeek": 5}))

    def test_invalid_boundaries_fail_before_network(self):
        for args in [(2026, 6, 6), (2026, 7, 6), (2026, 0, 1), (True, 5, 6),
                     (2026, True, 6), (2026, 5, False), (0, 1, 2)]:
            with self.subTest(args=args), patch("cfb1.cfbd_features._get_array") as fetch:
                with self.assertRaises(ValueError):
                    acquire_cfbd_features(FeatureBoundary(*args))
                fetch.assert_not_called()

    def test_live_acquisition_uses_shared_transport_and_never_requests_target(self):
        def fetch(path, params, api_key, timeout):
            return deepcopy(self.advanced if path != "/plays" else self.plays)
        with patch("cfb1.cfbd_features._get_array", side_effect=fetch) as get:
            r = acquire_cfbd_features(FeatureBoundary(2026, 2, 3), api_key="test", timeout=12)
        self.assertTrue(r.valid)
        self.assertEqual(get.call_count, 3)
        self.assertEqual(r.report["play_records"], 18)
        self.assertEqual(r.report["valid_ppa_rows"], 12)
        self.assertEqual([c.args[1].get("week") for c in get.call_args_list], [1, 2, None])
        self.assertTrue(all(c.args[2:] == ("test", 12) for c in get.call_args_list))

    def test_http_failure_stops_without_partial_result_or_retry(self):
        with patch("cfb1.cfbd_features._get_array", side_effect=CFBDAcquisitionError("CFBD returned HTTP 502")) as get:
            with self.assertRaises(CFBDAcquisitionError):
                acquire_cfbd_features(FeatureBoundary(2026, 5, 6))
        self.assertEqual(get.call_count, 1)

    def test_cli_failure_and_invalid_scope_are_safe_and_offline(self):
        with patch("cfb1.features_live.acquire_cfbd_features") as acquire:
            with redirect_stderr(StringIO()):
                self.assertEqual(main(["--season", "2026", "--data-through-week", "6", "--target-week", "6"]), 2)
            acquire.assert_not_called()
            acquire.side_effect = CFBDAcquisitionError("CFBD returned HTTP 502")
            with redirect_stderr(StringIO()):
                self.assertEqual(main(["--season", "2026", "--data-through-week", "5", "--target-week", "6"]), 2)

    def test_empty_week_does_not_invent_a_new_legacy_gate(self):
        with patch("cfb1.cfbd_features._get_array", side_effect=[[], self.plays, self.advanced]):
            r = acquire_cfbd_features(FeatureBoundary(2026, 2, 3))
        self.assertTrue(r.valid)
        self.assertEqual(r.report["requests"][0]["rows"], 0)

    def test_later_week_failure_does_not_return_partial_features(self):
        with patch("cfb1.cfbd_features._get_array", side_effect=[self.plays, CFBDAcquisitionError("CFBD returned HTTP 502")]) as get:
            with self.assertRaises(CFBDAcquisitionError):
                acquire_cfbd_features(FeatureBoundary(2026, 2, 3))
        self.assertEqual(get.call_count, 2)

    def test_cli_exports_only_valid_feature_tables(self):
        args = ["--season", "2026", "--data-through-week", "5", "--target-week", "6"]
        for invalid in [False, True]:
            result = self.build()
            if invalid:
                result.report["valid"] = False
            with TemporaryDirectory() as directory:
                with patch("cfb1.features_live.acquire_cfbd_features", return_value=result), redirect_stdout(StringIO()):
                    self.assertEqual(main(args + ["--output-dir", directory]), 1 if invalid else 0)
                self.assertTrue((Path(directory) / "validation.json").exists())
                self.assertEqual((Path(directory) / "df_cfbd.csv").exists(), not invalid)

    def test_literal_notebook_transformations_match_fixture_outputs(self):
        notebook = json.loads((ROOT / "legacy/CFB1_Colab_Reference.ipynb").read_text())
        def run(label, env):
            source = next("".join(c["source"]) for c in notebook["cells"]
                          if any(line.startswith("# " + label + " —") for line in c["source"]))
            tree = ast.parse(source)
            tree.body = [n for n in tree.body if not (isinstance(n, ast.Import)
                         and any(a.name == "requests" for a in n.names))]
            with redirect_stdout(StringIO()):
                exec(compile(tree, "frozen_notebook_" + label, "exec"), env)
        def get(url, **kwargs):
            rows = self.advanced if url.endswith("advanced") else self.plays
            return SimpleNamespace(status_code=200, json=lambda: deepcopy(rows))
        env = {"YEAR": 2026, "DATA_THROUGH_WEEK": 1, "TARGET_WEEK": 2,
               "CFBD_API_KEY": "offline", "requests": SimpleNamespace(get=get), "display": lambda *a: None}
        run("CELL 2", env)
        run("CELL 3", env)
        r = self.build()
        for name in ["df_ppa_plays", "df_ppa_valid", "df_off_ppa", "df_def_ppa", "df_ppa", "df_adv", "df_adv_clean"]:
            assert_frame_equal(getattr(r, name), env[name])
        env["df_target_market"] = self.market.copy()
        run("CELL 11", env)
        master = merge_master_features(self.market, r).drop(columns=["Home_Def_LineYards", "Away_Def_LineYards"])
        assert_frame_equal(master, env["df_master"])
        run("OLD CELL 25", env)
        assert_frame_equal(r.df_cfbd, env["df_cfbd"])


if __name__ == "__main__":
    unittest.main()
