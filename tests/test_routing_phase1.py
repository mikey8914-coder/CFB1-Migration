"""Offline routing, spread structure, Phase 1 and literal notebook parity."""

import ast
from contextlib import redirect_stdout
from io import StringIO
import hashlib
import json
from pathlib import Path
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from cfb1.routing import route_markets, apply_large_spread_routing, separate_evidence
from cfb1.spread_structure import classify_spread_structure, classify_large_spreads
from cfb1.phase1 import build_phase1_shortlist, build_phase1_review

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"


def literal_cell(number, env):
    if number not in range(36, 43):
        raise ValueError("Outside routing migration scope")
    label = f"OLD CELL {number}"
    notebook = json.loads((ROOT / "legacy/CFB1_Colab_Reference.ipynb").read_text())
    source = next("".join(c["source"]) for c in notebook["cells"]
                  if any(line.startswith("# " + label + " —") for line in c["source"]))
    with redirect_stdout(StringIO()):
        exec(compile(ast.parse(source), "frozen_" + label, "exec"), env)


def pipeline(master, convergence):
    routes = route_markets(convergence)
    structured, structure_display = classify_spread_structure(master, routes)
    large, large_display = classify_large_spreads(structured, routes)
    final = apply_large_spread_routing(routes, large)
    evidence = separate_evidence(final)
    phase = build_phase1_shortlist(large, evidence)
    review = build_phase1_review(phase.candidates)
    return routes, structured, structure_display, large, large_display, final, evidence, phase, review


def historical_inputs():
    from cfb1.bcf import parse_bcf_csv, normalize_bcf, merge_bcf
    from cfb1.model_signals import apply_epa_trigger, apply_fei_model, apply_fei_market_edges
    from cfb1.module3 import (apply_market_favorites, apply_havoc_trap, refresh_master_lineyards,
                             apply_lineyards_push, apply_explosiveness_fraud, apply_oay_day_edge)
    from cfb1.convergence import corrected_convergence
    cp = json.loads((FIXTURES / "module3_notebook_checkpoint.json").read_text())
    master = pd.DataFrame(cp["master_input"])
    cfbd = pd.DataFrame(cp["feature_table"])
    bcf = normalize_bcf(parse_bcf_csv((FIXTURES / "bcf_notebook_week5.csv").read_text()), cfbd.team, master)
    master = apply_fei_market_edges(apply_fei_model(merge_bcf(apply_epa_trigger(master), bcf)))
    master = apply_havoc_trap(apply_market_favorites(master))
    master = refresh_master_lineyards(master, cfbd, expected_games=57)
    master = apply_oay_day_edge(apply_explosiveness_fraud(apply_lineyards_push(master)))
    return master, corrected_convergence(master)


class RoutingTests(unittest.TestCase):
    def setUp(self):
        fixture = json.loads((FIXTURES / "routing_controlled.json").read_text())
        self.master, self.convergence = pd.DataFrame(fixture["master"]), pd.DataFrame(fixture["convergence"])

    def routes(self):
        return route_markets(self.convergence)

    def result(self):
        return pipeline(self.master, self.convergence)

    def test_only_epa_fei_agreements_routed(self):
        result = self.routes()
        self.assertEqual(len(result), 11)
        self.assertNotIn("Away0 at Home0", result.Game.tolist())

    def test_agreement_without_support_has_blank_routes_but_is_retained(self):
        row = self.routes().set_index("Game").loc["Away3 at Home3"]
        self.assertEqual(row.Eligible_Market_Routes, "")
        self.assertEqual(row.Spread_Status, "STANDARD_REVIEW")
        self.assertEqual(row.Final_Bet_Status, "UNPRICED — DO NOT BET YET")

    def test_positive_support_routes_exact_order(self):
        row = self.routes().set_index("Game").loc["Away1 at Home1"]
        self.assertEqual(row.Eligible_Market_Routes, "FULL_GAME_SPREAD, TEAM_TOTAL_OVER, 1H_TEAM_TOTAL_OVER, 1H_SPREAD_REVIEW")

    def test_opponent_negative_support_routes(self):
        row = self.routes().set_index("Game").loc["Away2 at Home2"]
        self.assertEqual(row.Eligible_Market_Routes, "FULL_GAME_SPREAD, OPP_TEAM_TOTAL_UNDER, OPP_1H_TEAM_TOTAL_UNDER, 1H_UNDER_REVIEW")

    def test_conflict_only_routes_derivatives(self):
        row = self.routes().set_index("Game").loc["Away4 at Home4"]
        self.assertEqual(row.Eligible_Market_Routes, "DERIVATIVES_FIRST")
        self.assertEqual(row.Spread_Status, "DOWNGRADE_FULL_GAME_SPREAD")

    def test_support_and_conflict_preserve_all_routes_and_downgrade(self):
        row = self.routes().set_index("Game").loc["Away5 at Home5"]
        self.assertEqual(row.Spread_Status, "DOWNGRADE_FULL_GAME_SPREAD")
        self.assertEqual(row.Eligible_Market_Routes, "FULL_GAME_SPREAD, DERIVATIVES_FIRST, TEAM_TOTAL_OVER, 1H_TEAM_TOTAL_OVER, 1H_SPREAD_REVIEW, OPP_TEAM_TOTAL_UNDER, OPP_1H_TEAM_TOTAL_UNDER, 1H_UNDER_REVIEW")

    def test_neutral_nonagreement_excluded_with_other_valid_rows(self):
        self.convergence.loc[1, ["EPA_FEI_Agree", "Shared_Side"]] = [False, ""]
        self.assertNotIn("Away1 at Home1", self.routes().Game.tolist())

    def test_blank_shared_side_on_agreement_fails(self):
        self.convergence.loc[1, "Shared_Side"] = ""
        with self.assertRaises(ValueError):
            self.routes()

    def test_duplicate_routed_games_fail(self):
        with self.assertRaises(ValueError):
            route_markets(pd.concat([self.convergence, self.convergence.iloc[1:2]]))

    def test_null_routed_magnitude_fails(self):
        self.convergence.loc[1, "EPA_Value"] = float("nan")
        with self.assertRaises(ValueError):
            self.routes()

    def test_exact_signed_key_numbers(self):
        for value in [3., 7., 10., 14., -3., -7., -10., -14.]:
            master = self.master.copy()
            master[["DK_Spread", "FD_Spread"]] = value
            structured, _ = classify_spread_structure(master, self.routes())
            with self.subTest(value=value):
                self.assertEqual(structured.Nearest_Key_Number.iloc[0], abs(value))
                self.assertEqual(structured.Distance_From_Key.iloc[0], 0.)
                self.assertTrue(structured["Within_0.5_Key"].iloc[0])

    def test_key_nearness_inclusive_half_and_one_point(self):
        for value, half, one in [(3.5, True, True), (4., False, True), (4.01, False, False)]:
            master = self.master.copy()
            master[["DK_Spread", "FD_Spread"]] = value
            structured, _ = classify_spread_structure(master, self.routes())
            self.assertEqual(structured["Within_0.5_Key"].iloc[0], half)
            self.assertEqual(structured["Within_1.0_Key"].iloc[0], one)

    def test_equidistant_key_uses_first_ordered_key(self):
        self.master[["DK_Spread", "FD_Spread"]] = 5.
        structured, _ = classify_spread_structure(self.master, self.routes())
        self.assertEqual(structured.Nearest_Key_Number.iloc[0], 3)

    def test_far_from_keys_still_has_nearest_but_no_proximity(self):
        self.master[["DK_Spread", "FD_Spread"]] = 30.
        structured, _ = classify_spread_structure(self.master, self.routes())
        self.assertEqual(structured.Nearest_Key_Number.iloc[0], 14)
        self.assertFalse(structured["Within_1.0_Key"].iloc[0])

    def test_book_spreads_straddling_key_are_not_a_temporal_crossing_audit(self):
        self.master.DK_Spread = -2.5
        self.master.FD_Spread = -3.5
        structured, _ = classify_spread_structure(self.master, self.routes())
        self.assertEqual(structured.Consensus_Spread.iloc[0], -3.)
        self.assertEqual(structured.Distance_From_Key.iloc[0], 0.)
        self.assertFalse(any("Cross" in c or "Movement" in c for c in structured))

    def test_consensus_rounds_before_key_distance(self):
        self.master.DK_Spread = 3.501
        self.master.FD_Spread = 3.501
        structured, _ = classify_spread_structure(self.master, self.routes())
        self.assertEqual(structured.Consensus_Spread.iloc[0], 3.5)
        self.assertTrue(structured["Within_0.5_Key"].iloc[0])

    def test_spread_bucket_boundaries(self):
        for value, label in [(0., "UNDER_3"), (3., "3_TO_6.5"), (7., "7_TO_9.5"),
                             (10., "10_TO_13.5"), (14., "14_TO_16.5"),
                             (17., "17_TO_20.5"), (21., "21_PLUS")]:
            master = self.master.copy()
            master[["DK_Spread", "FD_Spread"]] = -value
            result, _ = classify_spread_structure(master, self.routes())
            self.assertEqual(result.Spread_Size_Bucket.iloc[0], label)

    def test_spread_input_null_rejected_without_book_fallback(self):
        self.master.loc[0, "FD_Spread"] = float("nan")
        with self.assertRaises(ValueError):
            classify_spread_structure(self.master, self.routes())

    def test_routed_structure_filters_nonempty_initial_routes(self):
        _, _, display, _, large_display, *_ = self.result()
        self.assertEqual(set(display.Game), {"Away1 at Home1", "Away2 at Home2", "Away4 at Home4", "Away5 at Home5", "Away8 at Home8", "Away9 at Home9"})
        self.assertEqual(set(display.Game), set(large_display.Game))

    def test_large_spread_inclusive_thresholds(self):
        for value, large, very in [(16.49, False, False), (16.5, True, False),
                                   (17., True, False), (20.49, True, False),
                                   (20.5, True, True), (30., True, True)]:
            master, _ = classify_spread_structure(self.master, self.routes())
            master["Consensus_Spread"] = -value
            result, _ = classify_large_spreads(master, self.routes())
            self.assertEqual(result.Large_Spread_16_5.iloc[0], large)
            self.assertEqual(result.Very_Large_Spread_20_5.iloc[0], very)

    def test_large_favorite_orientation_and_pickem(self):
        for value, favorite in [(-20.5, "Home0"), (20.5, "Away0"), (0., "PICKEM")]:
            master, _ = classify_spread_structure(self.master, self.routes())
            master["Consensus_Spread"] = value
            result, _ = classify_large_spreads(master, self.routes())
            self.assertEqual(result.Consensus_Favorite.iloc[0], favorite)
            self.assertEqual(result.Favorite_Spread_Size.iloc[0], abs(value))

    def test_large_display_labels(self):
        for value, label in [(16.49, "BELOW_16.5"), (16.5, "LARGE_16.5_TO_20"), (20.5, "VERY_LARGE_20.5_PLUS")]:
            structured, _ = classify_spread_structure(self.master, self.routes())
            structured.Consensus_Spread = value
            _, display = classify_large_spreads(structured, self.routes())
            self.assertEqual(set(display.Spread_Class), {label})

    def test_large_null_input_rejected(self):
        self.master["Consensus_Spread"] = float("nan")
        with self.assertRaises(ValueError):
            classify_large_spreads(self.master, self.routes())

    def test_large_routing_creates_routes_for_model_only_game(self):
        final = self.result()[5].set_index("Game")
        self.assertEqual(final.loc["Away6 at Home6", "Spread_Status"], "DERIVATIVES_FIRST_20.5_PLUS")
        self.assertEqual(final.loc["Away6 at Home6", "Eligible_Market_Routes"], "1H_SPREAD_REVIEW, TEAM_TOTAL_REVIEW")

    def test_large_routing_exact_first_threshold(self):
        master = self.result()[3]
        master.loc[5, "Favorite_Spread_Size"] = 16.5
        convergence = self.convergence.copy()
        convergence.loc[5, ["M3_Conflict", "M3_Conflict_Count"]] = ["", 0]
        final = apply_large_spread_routing(route_markets(convergence), master).set_index("Game")
        self.assertEqual(final.loc["Away5 at Home5", "Spread_Status"], "LARGE_SPREAD_CAUTION")

    def test_conflict_override_runs_after_very_large_routing(self):
        master = self.result()[3]
        master.loc[5, "Favorite_Spread_Size"] = 25.
        final = apply_large_spread_routing(self.routes(), master).set_index("Game")
        row = final.loc["Away5 at Home5"]
        self.assertEqual(row.Spread_Status, "DOWNGRADE_FULL_GAME_SPREAD")
        routes = row.Eligible_Market_Routes.split(", ")
        self.assertEqual(routes.count("1H_SPREAD_REVIEW"), 1)
        self.assertEqual(routes.count("DERIVATIVES_FIRST"), 1)
        self.assertIn("TEAM_TOTAL_REVIEW", routes)

    def test_large_routing_missing_lookup_and_duplicate_lookup_fail(self):
        master = self.result()[3]
        with self.assertRaises(ValueError):
            apply_large_spread_routing(self.routes(), master.iloc[:1])
        with self.assertRaises(pd.errors.MergeError):
            apply_large_spread_routing(self.routes(), pd.concat([master, master.iloc[:1]]))

    def test_evidence_support_precedes_conflict_but_keeps_both_labels(self):
        row = self.result()[6].set_index("Game").loc["Away5 at Home5"]
        self.assertEqual(row.Evidence_Class, "MODEL_PLUS_MATCHUP_SUPPORT")
        self.assertEqual(row.Evidence, "EPA_FEI_DIRECTIONAL_AGREEMENT, MODULE3_SUPPORT, MODULE3_CONFLICT")
        self.assertIn("FULL_GAME_SPREAD_DOWNGRADE", row.Routing_Modifiers)

    def test_conflict_only_evidence_class(self):
        row = self.result()[6].set_index("Game").loc["Away4 at Home4"]
        self.assertEqual(row.Evidence_Class, "MODEL_WITH_MATCHUP_CONFLICT")

    def test_large_spread_is_modifier_not_extra_model_evidence(self):
        row = self.result()[6].set_index("Game").loc["Away6 at Home6"]
        self.assertEqual(row.Evidence_Class, "MODEL_AGREEMENT_ONLY")
        self.assertEqual(row.Evidence, "EPA_FEI_DIRECTIONAL_AGREEMENT")
        self.assertEqual(row.Routing_Modifiers, "VERY_LARGE_SPREAD_20.5_PLUS")

    def test_phase_support_and_conflict_included_without_strength(self):
        candidates = self.result()[7].candidates.set_index("Game")
        self.assertIn("MODULE3_SUPPORT", candidates.loc["Away1 at Home1", "Candidate_Reason"])
        self.assertIn("MODULE3_CONFLICT", candidates.loc["Away4 at Home4", "Candidate_Reason"])

    def test_phase_weak_agreement_and_nonagreement_excluded(self):
        phase = self.result()[7]
        self.assertNotIn("Away0 at Home0", phase.diagnostic.Game.tolist())
        self.assertNotIn("Away3 at Home3", phase.candidates.Game.tolist())
        self.assertNotIn("Away6 at Home6", phase.candidates.Game.tolist())

    def test_phase_full_slate_quantiles_and_conservative_edge(self):
        result = self.result()[7]
        self.assertEqual(result.cut_points["EPA_75"], self.master.EPA_Edge_Value.quantile(.75))
        self.assertEqual(result.cut_points["FEI_75"], self.master[["DK_FEI_Edge_Value", "FD_FEI_Edge_Value"]].min(axis=1).quantile(.75))
        self.assertNotEqual(result.cut_points["EPA_75"], self.master.iloc[1:].EPA_Edge_Value.quantile(.75))
        self.master.loc[7, "FD_FEI_Edge_Value"] = 0.
        self.assertEqual(self.result()[7].master.FEI_Edge_Conservative.iloc[7], 0.)

    def test_phase_exact_quantile_cutoffs_inclusive(self):
        self.master.EPA_Edge_Value = 1.
        self.master.DK_FEI_Edge_Value = 2.
        self.master.FD_FEI_Edge_Value = 2.
        phase = self.result()[7]
        self.assertTrue(phase.diagnostic.Dual_Top25.all())

    def test_phase90_cutpoints_do_not_gate_candidates(self):
        phase = self.result()[7]
        row = phase.candidates.set_index("Game").loc["Away8 at Home8"]
        self.assertTrue(row.Dual_Top25)
        self.assertLess(row.EPA_Value, phase.cut_points["EPA_90"])

    def test_phase_reason_order_and_support_over_conflict(self):
        phase = self.result()[7]
        self.assertEqual(phase.candidates.set_index("Game").loc["Away8 at Home8", "Candidate_Reason"], "MODULE3_SUPPORT, DUAL_TOP25_MODEL_STRENGTH")
        self.assertEqual(phase.candidates.set_index("Game").loc["Away5 at Home5", "Candidate_Reason"], "MODULE3_SUPPORT")

    def test_phase_evidence_cardinality_validation(self):
        master, evidence = self.result()[3], self.result()[6]
        with self.assertRaises(ValueError):
            build_phase1_shortlist(master, pd.concat([evidence, evidence.iloc[:1]]))

    def test_review_all_four_classifications(self):
        review = self.result()[8].set_index("Game")
        self.assertEqual(review.loc["Away8 at Home8", "Review_Class"], "MODEL_PLUS_MATCHUP")
        self.assertEqual(review.loc["Away7 at Home7", "Review_Class"], "STRONG_MODEL_AGREEMENT")
        self.assertEqual(review.loc["Away1 at Home1", "Review_Class"], "MATCHUP_SUPPORTED")
        self.assertEqual(review.loc["Away4 at Home4", "Review_Class"], "CONFLICT_REVIEW")
        self.assertEqual(set(review.Late_Week_Action), {"COLLECT_COVERS_LINE_MOVEMENT"})

    def test_review_precedence_strength_before_conflict(self):
        candidate = self.result()[7].candidates.iloc[:1].copy()
        candidate.Candidate_Reason = "DUAL_TOP25_MODEL_STRENGTH, MODULE3_CONFLICT"
        self.assertEqual(build_phase1_review(candidate).Review_Class.iloc[0], "STRONG_MODEL_AGREEMENT")

    def test_review_unclassified_and_duplicate_games_fail(self):
        candidates = self.result()[7].candidates.copy()
        candidates.loc[candidates.index[0], "Candidate_Reason"] = ""
        with self.assertRaises(ValueError):
            build_phase1_review(candidates)
        candidates = self.result()[7].candidates
        with self.assertRaises(ValueError):
            build_phase1_review(pd.concat([candidates, candidates.iloc[:1]]))

    def test_inputs_unchanged_and_no_audit_or_probability_outputs(self):
        master, convergence = self.master.copy(deep=True), self.convergence.copy(deep=True)
        result = self.result()
        assert_frame_equal(master, self.master)
        assert_frame_equal(convergence, self.convergence)
        self.assertEqual(result[7].master.context.tolist(), ["preserve"] * 12)
        for output in [result[5], result[6], result[8]]:
            for field in ["Movement_Class", "Decision_Status", "Expected_ROI", "Push_Adjusted_Win_Prob"]:
                self.assertNotIn(field, output)

    def test_controlled_identical_input_parity_all_seven_cells(self):
        env = {"pd": pd, "display": lambda *a: None, "TARGET_WEEK": 6,
               "df_master_bcf": self.master.copy(), "df_convergence_corrected": self.convergence.copy()}
        result = self.result()
        for number in range(36, 43):
            literal_cell(number, env)
        for actual, name in [(result[0], "df_market_routes"), (result[2], "df_routed_market_structure"),
                             (result[4], "df_large_spread_routed"), (result[5], "df_final_routes"),
                             (result[6], "df_evidence_routes"), (result[7].diagnostic, "df_phase1_diagnostic"),
                             (result[7].candidates, "candidate_board"), (result[8], "df_phase1_review"),
                             (result[7].master, "df_master_bcf")]:
            assert_frame_equal(actual, env[name])
        self.assertEqual(result[7].cut_points, {key: env[key] for key in ["EPA_75", "EPA_90", "FEI_75", "FEI_90"]})


class HistoricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp = json.loads((FIXTURES / "routing_notebook_checkpoint.json").read_text())
        cls.master, cls.convergence = historical_inputs()
        cls.result = pipeline(cls.master, cls.convergence)

    def test_checkpoint_hash(self):
        self.assertEqual(hashlib.sha256((ROOT / self.cp["notebook"]).read_bytes()).hexdigest(), self.cp["sha256"])

    def test_historical_route_and_key_counts(self):
        routes, structured, display = self.result[:3]
        self.assertEqual(len(routes), 37)
        self.assertEqual(len(display), 10)
        self.assertEqual(int(structured["Within_0.5_Key"].sum()), 41)
        self.assertEqual(int(structured["Within_1.0_Key"].sum()), 42)
        self.assertEqual(structured.Spread_Size_Bucket.value_counts().to_dict(), {
            "UNDER_3":13, "3_TO_6.5":15, "7_TO_9.5":12, "10_TO_13.5":8,
            "14_TO_16.5":3, "17_TO_20.5":2, "21_PLUS":4})

    def test_historical_displayed_quantiles_and_status_counts(self):
        cuts = self.result[7].cut_points
        self.assertEqual(f"{cuts['EPA_75']:.3f}", "0.267")
        self.assertEqual(f"{cuts['EPA_90']:.3f}", "0.420")
        self.assertEqual(f"{cuts['FEI_75']:.1f}", "10.6")
        self.assertEqual(f"{cuts['FEI_90']:.1f}", "13.2")
        active = self.result[5][self.result[5].Eligible_Market_Routes != ""]
        self.assertEqual(active.Spread_Status.value_counts().to_dict(), {
            "STANDARD_REVIEW": 6, "DERIVATIVES_FIRST_20.5_PLUS": 6})

    def test_historical_large_and_evidence_counts(self):
        large, final, evidence = self.result[3], self.result[5], self.result[6]
        self.assertEqual(int(large.Large_Spread_16_5.sum()), 6)
        self.assertEqual(int(large.Very_Large_Spread_20_5.sum()), 6)
        self.assertEqual(int((final.Eligible_Market_Routes != "").sum()), 12)
        self.assertEqual(evidence.Evidence_Class.value_counts().to_dict(), {
            "MODEL_AGREEMENT_ONLY":27, "MODEL_PLUS_MATCHUP_SUPPORT":10})

    def test_historical_phase1_counts(self):
        phase, review = self.result[7:]
        self.assertEqual((len(phase.diagnostic), len(phase.candidates), len(review)), (37, 14, 14))
        self.assertEqual(review.Review_Class.value_counts().to_dict(), {
            "MATCHUP_SUPPORTED":7, "STRONG_MODEL_AGREEMENT":4, "MODEL_PLUS_MATCHUP":3})
        self.assertEqual(int(phase.candidates.Candidate_Reason.str.contains("MODULE3_SUPPORT",regex=False).sum()),10)
        self.assertEqual(int(phase.candidates.Dual_Top25.sum()),7)

    def test_saved_display_samples_and_explicit_upstream_discrepancies(self):
        outputs = {"OLD CELL 36":self.result[0], "OLD CELL 37":self.result[2],
                   "OLD CELL 38":self.result[4], "OLD CELL 39":self.result[5],
                   "OLD CELL 40":self.result[6], "OLD CELL 41":self.result[7].candidates,
                   "OLD CELL 42":self.result[8]}
        differences=[]
        for label,tables in self.cp["samples"].items():
            actual=outputs[label].set_index("Game", drop=False)
            for table in tables:
                for expected in table:
                    row=actual.loc[expected["Game"]]
                    for field,value in expected.items():
                        with self.subTest(label=label,game=expected["Game"],field=field):
                            if isinstance(value,(int,float)) and not isinstance(value,bool):
                                if abs(row[field]-value)>5e-7+1e-12:
                                    differences.append((label,expected["Game"],field))
                            elif isinstance(value,str) and value.endswith('...'):
                                self.assertTrue(str(row[field]).startswith(value[:-3]))
                            else:self.assertEqual(row[field],value)
        self.assertEqual(differences, [
            ("OLD CELL 36", "UConn Huskies at Temple Owls", "EPA_Value"),
            ("OLD CELL 36", "James Madison Dukes at Georgia Southern Eagles", "EPA_Value"),
            ("OLD CELL 41", "James Madison Dukes at Georgia Southern Eagles", "EPA_Value"),
            ("OLD CELL 42", "James Madison Dukes at Georgia Southern Eagles", "EPA_Value"),
        ])

    def test_full_historical_identical_input_notebook_parity(self):
        env={"pd":pd,"display":lambda *a:None,"TARGET_WEEK":6,
             "df_master_bcf":self.master.copy(),"df_convergence_corrected":self.convergence.copy()}
        for number in range(36,43):literal_cell(number,env)
        for actual,name in [(self.result[0],"df_market_routes"),(self.result[2],"df_routed_market_structure"),
                            (self.result[4],"df_large_spread_routed"),(self.result[5],"df_final_routes"),
                            (self.result[6],"df_evidence_routes"),(self.result[7].diagnostic,"df_phase1_diagnostic"),
                            (self.result[7].candidates,"candidate_board"),(self.result[8],"df_phase1_review")]:
            assert_frame_equal(actual,env[name])


if __name__ == '__main__':
    unittest.main()
