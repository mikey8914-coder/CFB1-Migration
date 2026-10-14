"""Identity regression checks; inspect notebook source without executing it."""

import ast
import hashlib
import json
from pathlib import Path
import unittest

from cfb1.team_identity import (
    ALIAS_MAPPING_VERSION,
    BCF_TO_CFBD,
    TEAM_ALIASES,
    TeamIdentityResolver,
    normalize_bcf_team_name,
    normalize_team_name,
)


ROOT = Path(__file__).resolve().parents[1]


def reference_aliases(label: str, variable: str) -> dict[str, str]:
    """Read literal dictionaries only, retaining the embedded CELL label."""
    notebook = json.loads(
        (ROOT / "legacy/CFB1_Colab_Reference.ipynb").read_bytes()
    )
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        if not any(line.startswith(f"# {label} —") for line in source.splitlines()):
            continue
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == variable
                for target in node.targets
            ):
                return ast.literal_eval(node.value)
    raise AssertionError(f"{variable} not found in {label}")


class TeamIdentityTests(unittest.TestCase):
    def test_mapping_matches_all_cell_10_aliases(self):
        expected = reference_aliases("CELL 10", "TEAM_ALIASES")
        self.assertEqual(dict(TEAM_ALIASES), expected)
        for raw, canonical in expected.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_team_name(raw), canonical)

    def test_mapping_matches_all_cell_14_aliases(self):
        expected = reference_aliases("CELL 14", "BCF_TO_CFBD")
        self.assertEqual(dict(BCF_TO_CFBD), expected)
        for raw, canonical in expected.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_bcf_team_name(raw), canonical)

    def test_mapping_provenance_matches_frozen_notebook(self):
        mapping = json.loads((ROOT / "src/cfb1/team_aliases.json").read_text())
        digest = hashlib.sha256(
            (ROOT / "legacy/CFB1_Colab_Reference.ipynb").read_bytes()
        ).hexdigest()
        self.assertEqual(mapping["reference"]["sha256"], digest)
        self.assertEqual(mapping["reference"]["TEAM_ALIASES"], "CELL 10")
        self.assertEqual(mapping["reference"]["BCF_TO_CFBD"], "CELL 14")
        self.assertEqual(ALIAS_MAPPING_VERSION, 1)

    def test_market_whitespace_is_collapsed_before_lookup(self):
        self.assertEqual(
            normalize_team_name(" \tSan\u00a0Jose  State\nSpartans "),
            "San José State",
        )

    def test_unknown_market_name_preserves_cleaned_fallback(self):
        self.assertEqual(normalize_team_name("  Unknown\tTeam  "), "Unknown Team")

    def test_market_stringifies_values_like_cell_10(self):
        for raw, expected in [(None, "None"), (float("nan"), "nan"), (123, "123")]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_team_name(raw), expected)

    def test_market_has_no_fuzzy_case_mascot_or_accent_rewrite(self):
        for name in ["miami hurricanes", "Miami Tigers", "San Jose State", "Hawaii"]:
            with self.subTest(name=name):
                self.assertEqual(normalize_team_name(name), name)

    def test_alias_sources_stay_distinct(self):
        self.assertEqual(normalize_team_name("Connecticut"), "Connecticut")
        self.assertEqual(normalize_bcf_team_name("Connecticut"), "UConn")
        self.assertEqual(normalize_team_name("Miami Hurricanes"), "Miami")
        self.assertEqual(normalize_bcf_team_name("Miami Hurricanes"), "Miami Hurricanes")

    def test_bcf_mapping_does_not_reclean_cell_13_input(self):
        for name in [" Connecticut ", "San  Jose State", "Unknown\tTeam"]:
            with self.subTest(name=name):
                self.assertEqual(normalize_bcf_team_name(name), name)
        self.assertEqual(normalize_bcf_team_name(" Connecticut ".strip()), "UConn")

    def test_canonical_names_pass_through(self):
        for name in ["Miami", "Miami (OH)", "App State", "Hawai'i", "San José State"]:
            with self.subTest(name=name):
                self.assertEqual(normalize_team_name(name), name)
                self.assertEqual(normalize_bcf_team_name(name), name)

    def test_miami_identities_remain_distinct(self):
        self.assertEqual(normalize_team_name("Miami Hurricanes"), "Miami")
        self.assertEqual(normalize_team_name("Miami (OH) RedHawks"), "Miami (OH)")

    def test_match_status_uses_supplied_cfbd_universe(self):
        resolver = TeamIdentityResolver([" Miami ", "Miami (OH)", "UConn"])
        identity = resolver.resolve_market_name(" Miami  Hurricanes ")
        self.assertEqual(identity.raw_name, " Miami  Hurricanes ")
        self.assertEqual(identity.normalized_name, "Miami")
        self.assertTrue(identity.matched)
        self.assertTrue(resolver.resolve_bcf_name("Connecticut").matched)
        self.assertFalse(resolver.resolve_market_name("Connecticut").matched)

    def test_known_alias_does_not_imply_cfbd_coverage(self):
        identity = TeamIdentityResolver(["Miami"]).resolve_market_name("UConn Huskies")
        self.assertEqual(identity.normalized_name, "UConn")
        self.assertFalse(identity.matched)

    def test_unknown_team_is_reported_without_automatic_exclusion(self):
        identity = TeamIdentityResolver(["Miami"]).resolve_market_name(" Unknown\tTeam ")
        self.assertEqual(identity.raw_name, " Unknown\tTeam ")
        self.assertEqual(identity.normalized_name, "Unknown Team")
        self.assertFalse(identity.matched)

    def test_cfbd_names_are_only_stripped_not_alias_normalized(self):
        resolver = TeamIdentityResolver([" Miami Hurricanes ", "Unknown  Team"])
        self.assertFalse(resolver.resolve_market_name("Miami Hurricanes").matched)
        self.assertFalse(resolver.resolve_market_name("Unknown  Team").matched)

    def test_resolver_accepts_a_generator(self):
        resolver = TeamIdentityResolver(name for name in ["Miami", "UConn"])
        self.assertTrue(resolver.resolve_market_name("Miami Hurricanes").matched)
        self.assertTrue(resolver.resolve_bcf_name("Connecticut").matched)

    def test_alias_maps_cannot_be_mutated_at_runtime(self):
        with self.assertRaises(TypeError):
            TEAM_ALIASES["invented alias"] = "Miami"
        with self.assertRaises(TypeError):
            BCF_TO_CFBD["invented alias"] = "Miami"


if __name__ == "__main__":
    unittest.main()
