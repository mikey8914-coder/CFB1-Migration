"""Resolve legacy team aliases to the supplied CFBD team-name universe.

CELL 10 defines the market-name behavior. CELL 14 defines the distinct
BCF mapping, whose inputs have already been stripped by CELL 13.
No numeric team identifiers or additional aliases are inferred here.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib.resources import files
import json
import re
from types import MappingProxyType


_alias_data = json.loads(
    files("cfb1").joinpath("team_aliases.json").read_text(encoding="utf-8")
)
ALIAS_MAPPING_VERSION: int = _alias_data["mapping_version"]
TEAM_ALIASES: Mapping[str, str] = MappingProxyType(_alias_data["TEAM_ALIASES"])
BCF_TO_CFBD: Mapping[str, str] = MappingProxyType(_alias_data["BCF_TO_CFBD"])


def normalize_team_name(team_name: object) -> str:
    """Apply CELL 10: stringify, collapse whitespace, strip, then exact alias.

    Unknown names return the cleaned input. This does not establish that the
    name exists in CFBD; use TeamIdentityResolver to check membership.
    Case, punctuation, accents and mascots are not heuristically changed.
    """
    cleaned = re.sub(r"\s+", " ", str(team_name)).strip()
    return TEAM_ALIASES.get(cleaned, cleaned)


def normalize_bcf_team_name(team_name: str) -> str:
    """Apply only CELL 14's exact mapping to a CELL 13-prepared Team string.

    CELL 13 strips leading/trailing whitespace before this stage. Preserve
    that boundary: this function does not collapse whitespace, strip again,
    or apply market aliases. Unknown input is returned unchanged.
    """
    return BCF_TO_CFBD.get(team_name, team_name)


@dataclass(frozen=True)
class TeamIdentity:
    """An original name, its normalization result, and CFBD match status.

    An unmatched normalized_name is a legacy fallback, not a verified
    canonical identifier. Keeping raw_name preserves display/join provenance.
    """

    raw_name: object
    normalized_name: str
    matched: bool


class TeamIdentityResolver:
    """Check aliases against nonnull string names from df_cfbd.team.

    CELL 10 strips these canonical names without collapsing internal spaces.
    The caller must remove missing CFBD values first, as in the notebook's
    dropna(). No alias-value list is treated as a complete CFBD registry.
    Membership does not validate merge cardinality or statistical coverage.
    """

    def __init__(self, canonical_team_names: Iterable[str]) -> None:
        self.canonical_team_names = frozenset(
            name.strip() for name in canonical_team_names
        )

    def resolve_market_name(self, team_name: object) -> TeamIdentity:
        """Preserve CELL 10 normalization and its exact membership check."""
        normalized = normalize_team_name(team_name)
        return TeamIdentity(
            team_name, normalized, normalized in self.canonical_team_names
        )

    def resolve_bcf_name(self, team_name: str) -> TeamIdentity:
        """Preserve CELL 14 alias lookup and CFBD membership for prepared input."""
        normalized = normalize_bcf_team_name(team_name)
        return TeamIdentity(
            team_name, normalized, normalized in self.canonical_team_names
        )
