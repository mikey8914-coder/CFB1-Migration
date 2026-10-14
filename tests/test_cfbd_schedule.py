"""Mocked CFBD HTTP and live-command tests; no real network or credentials."""

from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

from cfb1.cfbd_schedule import (
    CFBDAcquisitionError, _NoRedirect, acquire_cfbd_schedule,
    fetch_cfbd_games, fetch_cfbd_team_names,
)
from cfb1.schedule import normalize_cfbd_schedule
from cfb1.schedule_live import main
from cfb1.team_identity import TeamIdentityResolver


FIXTURES = Path(__file__).parent / "fixtures"
TEST_KEY = "test-only-not-a-real-credential"


class Response(BytesIO):
    def __init__(self, body, status=200):
        super().__init__(body)
        self.status = status


class CFBDAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.games = json.loads((FIXTURES / "cfbd_schedule.json").read_text())
        self.teams = json.loads((FIXTURES / "cfbd_teams.json").read_text())
        self.resolver = TeamIdentityResolver(self.teams)
        self.opener_patch = patch("cfb1.cfbd_schedule.request.build_opener")
        self.opener = self.opener_patch.start().return_value
        self.addCleanup(self.opener_patch.stop)

    def response(self, value):
        self.opener.open.return_value = Response(json.dumps(value).encode())

    def test_correct_auth_scope_and_timeout_without_key_in_url(self):
        self.response(self.games)
        actual = fetch_cfbd_games(2026, 6, api_key=" " + TEST_KEY + " ", timeout=12)
        self.assertEqual(actual, self.games)
        req = self.opener.open.call_args.args[0]
        self.assertEqual(urlparse(req.full_url).path, "/games")
        self.assertEqual(parse_qs(urlparse(req.full_url).query), {
            "year": ["2026"], "week": ["6"], "seasonType": ["regular"]
        })
        self.assertEqual(req.get_header("Authorization"), "Bearer " + TEST_KEY)
        self.assertEqual(req.get_header("Accept"), "application/json")
        self.assertNotIn(TEST_KEY, req.full_url)
        self.assertEqual(self.opener.open.call_args.kwargs["timeout"], 12)

    def test_environment_credential_is_reused(self):
        self.response(self.games)
        with patch.dict(os.environ, {"CFBD_API_KEY": TEST_KEY}):
            fetch_cfbd_games(2026, 6)
        self.assertEqual(self.opener.open.call_args.args[0].get_header("Authorization"), "Bearer " + TEST_KEY)

    def test_missing_credential_fails_before_network(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(CFBDAcquisitionError):
            fetch_cfbd_games(2026, 6)
        self.opener.open.assert_not_called()

    def test_invalid_scope_fails_before_network(self):
        for season, week in [(True, 6), (2026, -1), (2026, 6.0), (0, 6)]:
            with self.subTest(season=season, week=week), self.assertRaises(CFBDAcquisitionError):
                fetch_cfbd_games(season, week, api_key=TEST_KEY)
        self.opener.open.assert_not_called()

    def test_acquisition_checks_scope_before_registry_fetch(self):
        with self.assertRaises(CFBDAcquisitionError):
            acquire_cfbd_schedule(2026, -1, api_key=TEST_KEY)
        self.opener.open.assert_not_called()

    def test_invalid_timeout_and_key_header_are_rejected(self):
        for timeout in [0, -1, float("nan"), float("inf"), True]:
            with self.subTest(timeout=timeout), self.assertRaises(CFBDAcquisitionError):
                fetch_cfbd_games(2026, 6, api_key=TEST_KEY, timeout=timeout)
        with self.assertRaises(CFBDAcquisitionError):
            fetch_cfbd_games(2026, 6, api_key="bad\nheader")
        self.opener.open.assert_not_called()

    def test_redirect_handler_does_not_forward_authorization(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.org"))

    def test_http_error_body_and_reason_are_not_exposed_or_retried(self):
        for code in [301, 401, 403, 429, 500]:
            with self.subTest(code=code):
                self.opener.open.reset_mock()
                self.opener.open.side_effect = HTTPError("https://api.collegefootballdata.com/games", code, TEST_KEY, {}, BytesIO(TEST_KEY.encode()))
                with self.assertRaises(CFBDAcquisitionError) as caught:
                    fetch_cfbd_games(2026, 6, api_key=TEST_KEY)
                self.assertIn(str(code), str(caught.exception))
                self.assertNotIn(TEST_KEY, str(caught.exception))
                self.assertEqual(self.opener.open.call_count, 1)

    def test_network_and_timeout_errors_are_safe(self):
        for failure in [URLError(TEST_KEY), TimeoutError(TEST_KEY), OSError(TEST_KEY)]:
            with self.subTest(failure=type(failure).__name__):
                self.opener.open.side_effect = failure
                with self.assertRaises(CFBDAcquisitionError) as caught:
                    fetch_cfbd_games(2026, 6, api_key=TEST_KEY)
                self.assertNotIn(TEST_KEY, str(caught.exception))

    def test_invalid_json_and_wrong_top_level_payload_are_rejected(self):
        for body in [TEST_KEY.encode(), b'{"error": "not games"}', b'null', b'123', b'"not games"', b'\xff']:
            with self.subTest(body=body):
                self.opener.open.return_value = Response(body)
                with self.assertRaises(CFBDAcquisitionError) as caught:
                    fetch_cfbd_games(2026, 6, api_key=TEST_KEY)
                self.assertNotIn(TEST_KEY, str(caught.exception))

    def test_non_200_response_object_is_rejected(self):
        self.opener.open.return_value = Response(b'[]', status=204)
        with self.assertRaises(CFBDAcquisitionError):
            fetch_cfbd_games(2026, 6, api_key=TEST_KEY)

    def test_independent_team_registry_school_names(self):
        self.response([{"school": name} for name in self.teams])
        self.assertEqual(fetch_cfbd_team_names(api_key=TEST_KEY), self.teams)
        self.assertEqual(self.opener.open.call_args.args[0].full_url, "https://api.collegefootballdata.com/teams")

    def test_malformed_registry_is_not_silently_filtered(self):
        for teams in [[], [None], [{"school": ""}], [{"school": 123}], [{"name": "Miami"}]]:
            with self.subTest(teams=teams):
                self.response(teams)
                with self.assertRaises(CFBDAcquisitionError):
                    fetch_cfbd_team_names(api_key=TEST_KEY)

    def test_passes_all_games_to_unchanged_validation(self):
        self.response(self.games)
        result = acquire_cfbd_schedule(2026, 6, resolver=self.resolver, api_key=TEST_KEY)
        self.assertEqual(result.raw_games, tuple(self.games))
        self.assertEqual(result.validation, normalize_cfbd_schedule(self.games, season=2026, week=6, resolver=self.resolver))
        self.assertEqual(result.to_dict()["summary"]["games_retrieved"], 3)
        self.assertEqual(result.to_dict()["summary"]["games_successfully_normalized"], 3)
        self.assertEqual(self.opener.open.call_count, 1)

    def test_default_uses_independent_registry_not_schedule_names(self):
        games = [dict(self.games[1], awayTeam="Unknown School")]
        self.opener.open.side_effect = [
            Response(json.dumps([{"school": name} for name in self.teams]).encode()),
            Response(json.dumps(games).encode()),
        ]
        result = acquire_cfbd_schedule(2026, 6, api_key=TEST_KEY)
        self.assertFalse(result.validation.valid)
        self.assertEqual(result.to_dict()["summary"]["unresolved_team_identities"], 1)
        self.assertEqual(self.opener.open.call_count, 2)

    def test_reports_unresolved_malformed_duplicate_conflict_and_missing_kickoff(self):
        duplicate = dict(self.games[1], id=900000010)
        reversed_game = dict(self.games[1], id=900000011, homeTeam="Miami", awayTeam="UConn")
        games = [self.games[1], duplicate, reversed_game,
                 dict(self.games[0], awayTeam="Unknown School"),
                 dict(self.games[2], startTimeTBD=True),
                 dict(self.games[2], id=None, startDate=None), None]
        self.response(games)
        result = acquire_cfbd_schedule(2026, 6, resolver=self.resolver, api_key=TEST_KEY)
        summary = result.to_dict()["summary"]
        self.assertEqual(result.raw_games, tuple(games))
        self.assertFalse(result.validation.valid)
        self.assertEqual(summary["games_retrieved"], 7)
        self.assertEqual(summary["games_successfully_normalized"], 0)
        self.assertEqual(summary["games_rejected"], 7)
        self.assertEqual(summary["unresolved_team_identities"], 1)
        self.assertEqual(summary["duplicate_or_conflicting_records"], 3)
        self.assertEqual(summary["games_missing_confirmed_kickoff"], 3)
        self.assertEqual(summary["malformed_records"], 2)

    def test_empty_games_are_invalid_not_verified_zero_game_slate(self):
        self.response([])
        result = acquire_cfbd_schedule(2026, 6, resolver=self.resolver, api_key=TEST_KEY)
        self.assertFalse(result.validation.valid)
        self.assertEqual(result.to_dict()["summary"]["games_retrieved"], 0)
        self.assertEqual(result.validation.issues[0].code, "empty_schedule")

    def cli(self, *extra):
        stdout, stderr = StringIO(), StringIO()
        with patch.dict(os.environ, {"CFBD_API_KEY": TEST_KEY}), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["--season", "2026", "--week", "6", "--teams", str(FIXTURES / "cfbd_teams.json"), *extra])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_live_command_reports_success_and_validation_failure(self):
        self.response(self.games)
        code, out, err = self.cli()
        self.assertEqual(code, 0, err)
        self.assertTrue(json.loads(out)["live_acquisition_succeeded"])
        self.assertEqual(json.loads(out)["summary"]["games_retrieved"], 3)
        self.assertNotIn(TEST_KEY, out + err)
        self.response([dict(self.games[1], homeTeam="Unknown School")])
        code, out, err = self.cli()
        self.assertEqual(code, 1)
        self.assertTrue(json.loads(out)["live_acquisition_succeeded"])
        self.assertFalse(json.loads(out)["valid"])
        self.assertEqual(json.loads(out)["summary"]["unresolved_team_identities"], 1)

    def test_live_command_reports_transport_failure_without_key(self):
        self.opener.open.side_effect = HTTPError("https://api.collegefootballdata.com/games", 401, TEST_KEY, {}, None)
        code, out, err = self.cli()
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertFalse(json.loads(err)["live_acquisition_succeeded"])
        self.assertNotIn(TEST_KEY, err)


if __name__ == "__main__":
    unittest.main()
