"""Offline synthetic CFBD fixture tests; no notebook or API execution."""

from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cfb1.schedule import normalize_cfbd_schedule
from cfb1.team_identity import TeamIdentityResolver


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.games = json.loads((FIXTURES / "cfbd_schedule.json").read_text())
        self.teams = json.loads((FIXTURES / "cfbd_teams.json").read_text())
        self.resolver = TeamIdentityResolver(self.teams)

    def validate(self, games=None, **kwargs):
        return normalize_cfbd_schedule(
            self.games if games is None else games,
            season=2026, week=6, resolver=self.resolver, **kwargs
        )

    def assert_issue(self, result, code):
        self.assertFalse(result.valid)
        self.assertIn(code, {issue.code for issue in result.issues})

    def test_fixture_has_exact_normalized_fields_and_utc(self):
        result = self.validate()
        self.assertTrue(result.valid)
        self.assertEqual(len(result.records), 3)
        record = result.records[0]
        self.assertEqual(record.game_id, 900000001)
        self.assertEqual(record.kickoff_utc, datetime(2026, 10, 10, 16, tzinfo=timezone.utc))
        self.assertEqual(record.away_team, "Miami")
        self.assertEqual(record.home_team, "UConn")
        self.assertEqual(set(record.to_dict()), {
            "game_id", "season", "week", "away_team", "home_team", "kickoff_utc", "source"
        })
        self.assertEqual(record.to_dict()["kickoff_utc"], "2026-10-10T16:00:00Z")
        self.assertEqual(record.source, "cfbd")

    def test_repeat_and_input_reordering_have_stable_output(self):
        expected = self.validate().to_dict()
        self.assertEqual(self.validate().to_dict(), expected)
        self.assertEqual(self.validate(list(reversed(self.games))).to_dict(), expected)

    def test_preserves_source_id_type_and_survives_reschedule(self):
        previous = self.validate().records
        self.games[1]["startDate"] = "2026-10-11T16:00:00Z"
        result = self.validate(previous_records=previous)
        self.assertTrue(result.valid)
        self.assertEqual({r.game_id for r in result.records}, {r.game_id for r in previous})
        self.assertIsInstance(next(r for r in result.records if r.game_id == "900000002").game_id, str)

    def test_uses_existing_market_aliases_and_whitespace_rules(self):
        self.games[1]["awayTeam"] = " Miami\tHurricanes "
        self.games[1]["homeTeam"] = "UConn Huskies"
        result = self.validate()
        self.assertTrue(result.valid)
        self.assertEqual(result.records[0].away_team, "Miami")
        self.assertEqual(result.records[0].home_team, "UConn")

    def test_unknown_team_is_flagged_and_affected_game_excluded(self):
        self.games[1]["awayTeam"] = "Unknown School"
        result = self.validate()
        self.assert_issue(result, "unresolved_team")
        self.assertEqual(len(result.records), 2)
        self.assertNotIn(900000001, {r.game_id for r in result.records})

    def test_known_alias_missing_from_cfbd_universe_is_unresolved(self):
        self.resolver = TeamIdentityResolver(["Miami"])
        self.games[1]["homeTeam"] = "UConn Huskies"
        self.assert_issue(self.validate([self.games[1]]), "unresolved_team")

    def test_ambiguous_alias_is_not_silently_chosen(self):
        self.resolver = TeamIdentityResolver(self.teams + ["Miami Hurricanes"])
        self.games[1]["awayTeam"] = "Miami Hurricanes"
        result = self.validate([self.games[1]])
        self.assert_issue(result, "ambiguous_alias")
        self.assertEqual(result.records, ())

    def test_duplicate_ids_reject_all_occurrences(self):
        result = self.validate([self.games[1], dict(self.games[1])])
        self.assert_issue(result, "duplicate_game_id")
        self.assertEqual(result.records, ())

    def test_mixed_string_integer_id_duplicate_is_detected(self):
        other = dict(self.games[1], id=str(self.games[1]["id"]))
        result = self.validate([self.games[1], other])
        self.assert_issue(result, "duplicate_game_id")

    def test_same_matchup_with_different_ids_is_flagged(self):
        other = dict(self.games[1], id=900000010)
        self.assert_issue(self.validate([self.games[1], other]), "duplicate_matchup")

    def test_reversed_matchup_across_rows_is_flagged(self):
        other = dict(self.games[1], id=900000010, awayTeam="UConn", homeTeam="Miami")
        result = self.validate([self.games[1], other])
        self.assert_issue(result, "inconsistent_home_away")
        self.assertEqual(result.records, ())

    def test_same_id_with_different_teams_is_flagged(self):
        other = dict(self.games[1], awayTeam="App State")
        self.assert_issue(self.validate([self.games[1], other]), "inconsistent_home_away")

    def test_previous_snapshot_home_away_reversal_is_flagged(self):
        previous = self.validate().records
        self.games[1].update(awayTeam="UConn", homeTeam="Miami")
        self.assert_issue(self.validate(previous_records=previous), "inconsistent_home_away")

    def test_conflicting_previous_assignments_are_flagged(self):
        original = self.validate().records[0]
        previous = [original, replace(original, away_team="App State")]
        self.assert_issue(self.validate(previous_records=previous), "inconsistent_home_away")

    def test_same_team_on_both_sides_is_flagged(self):
        self.games[1]["homeTeam"] = "Miami Hurricanes"
        self.assert_issue(self.validate(), "inconsistent_home_away")

    def test_scope_and_regular_season_are_checked(self):
        for fields, code in [({"week": 7}, "outside_week"), ({"season": 2025}, "outside_week"),
                             ({"seasonType": "postseason"}, "outside_season_type")]:
            with self.subTest(fields=fields):
                result = self.validate([dict(self.games[1], **fields)])
                self.assert_issue(result, code)
                self.assertEqual(result.records, ())

    def test_snake_case_cfbd_sdk_shape_is_supported(self):
        game = dict(self.games[1])
        for camel, snake in [("homeTeam", "home_team"), ("awayTeam", "away_team"),
                             ("startDate", "start_date"), ("seasonType", "season_type"),
                             ("startTimeTBD", "start_time_tbd")]:
            game[snake] = game.pop(camel)
        self.assertEqual(self.validate([game]), self.validate([self.games[1]]))

    def test_conflicting_wire_and_sdk_fields_are_rejected(self):
        self.games[1]["home_team"] = "App State"
        result = self.validate([self.games[1]])
        self.assert_issue(result, "invalid_record")
        self.assertEqual(result.records, ())

    def test_tbd_kickoff_is_flagged(self):
        result = self.validate([dict(self.games[1], startTimeTBD=True)])
        self.assert_issue(result, "kickoff_tbd")
        self.assertEqual(result.records, ())

    def test_invalid_ids_names_dates_and_scope_types_are_rejected(self):
        for fields in [{"id": None}, {"id": True}, {"id": 1.5}, {"id": " "},
                       {"startDate": None}, {"startDate": "bad date"},
                       {"startDate": "2026-10-10T12:00:00"}, {"awayTeam": None},
                       {"homeTeam": " "}, {"season": True}, {"week": 6.0},
                       {"startTimeTBD": "false"}]:
            with self.subTest(fields=fields):
                result = self.validate([dict(self.games[1], **fields)])
                self.assert_issue(result, "invalid_record")
                self.assertEqual(result.records, ())

    def test_empty_and_nonobject_rows_are_invalid(self):
        self.assert_issue(self.validate([]), "empty_schedule")
        self.assert_issue(self.validate([None]), "invalid_record")
        with self.assertRaises(ValueError):
            self.validate({"error": "not games"})

    def test_neutral_site_does_not_reassign_source_home_away(self):
        self.games[1]["neutralSite"] = True
        result = self.validate([self.games[1]])
        self.assertTrue(result.valid)
        self.assertEqual((result.records[0].away_team, result.records[0].home_team), ("Miami", "UConn"))

    def run_cli(self, games_path, teams_path=FIXTURES / "cfbd_teams.json"):
        environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        return subprocess.run([
            sys.executable, "-m", "cfb1.schedule_validate", "--games", str(games_path),
            "--teams", str(teams_path), "--season", "2026", "--week", "6"
        ], cwd=ROOT, env=environment, capture_output=True, text=True)

    def test_independent_cli_valid_fixture_and_rejection_exit_codes(self):
        completed = self.run_cli(FIXTURES / "cfbd_schedule.json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["valid"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "games.json"
            path.write_text(json.dumps([dict(self.games[1], awayTeam="Unknown School")]))
            completed = self.run_cli(path)
            self.assertEqual(completed.returncode, 1)
            self.assertFalse(json.loads(completed.stdout)["valid"])
            path.write_text('{"error": "not a schedule"}')
            completed = self.run_cli(path)
            self.assertEqual(completed.returncode, 2)
            self.assertIn("error", json.loads(completed.stderr))


if __name__ == "__main__":
    unittest.main()
