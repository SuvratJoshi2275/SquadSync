"""
SquadSync data access layer.

Every function here reads from the Parquet cache built by build_cache.py,
never from the raw CSVs at runtime. Large tables (events/passes/carries/
pressures) are partitioned by match_id, so match-scoped reads only touch
one partition instead of the whole dataset.

If a required parquet cache is missing, functions raise a clear
FileNotFoundError telling the caller to run build_cache.py -- they do not
silently fall back to reading the raw CSV (that would defeat the point of
the cache and could load 200MB+ into memory unexpectedly).

Usage is team-namespaced throughout: every public function takes a `team`
argument (default "barcelona") so a second team's cache can be added later
purely by running build_cache.py --team <new_team>.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

try:
    import streamlit as st
    _cache_data = st.cache_data
except Exception:  # running outside Streamlit (tests, scripts)
    def _cache_data(func=None, **_kwargs):
        if func is None:
            return lambda f: lru_cache(maxsize=32)(f)
        return lru_cache(maxsize=32)(func)

DATA_DIR = Path(__file__).parent
PROCESSED_DIR = DATA_DIR / "processed"


def available_teams() -> list[str]:
    if not PROCESSED_DIR.exists():
        return []
    return sorted(p.name for p in PROCESSED_DIR.iterdir() if p.is_dir())


def _flat_path(team: str, name: str) -> Path:
    return PROCESSED_DIR / team / f"{name}.parquet"


def _partitioned_path(team: str, name: str) -> Path:
    return PROCESSED_DIR / team / name


def _require(path: Path, name: str) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Cache missing for '{name}' at {path}. "
            f"Run `python data/build_cache.py --team <team>` first."
        )


@_cache_data
def load_matches(team: str = "barcelona") -> pd.DataFrame:
    path = _flat_path(team, "matches")
    _require(path, "matches")
    df = pd.read_parquet(path)
    return df.sort_values("match_date").reset_index(drop=True)


@_cache_data
def load_players(team: str = "barcelona") -> pd.DataFrame:
    path = _flat_path(team, "players")
    _require(path, "players")
    return pd.read_parquet(path)


@_cache_data
def load_lineups(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    path = _flat_path(team, "lineups")
    _require(path, "lineups")
    df = pd.read_parquet(path)
    if match_id is not None:
        df = df[df["match_id"] == match_id]
    return df


@_cache_data
def load_formations(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    path = _flat_path(team, "formations")
    _require(path, "formations")
    df = pd.read_parquet(path)
    if match_id is not None:
        df = df[df["match_id"] == match_id]
    return df


@_cache_data
def load_shots(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    path = _flat_path(team, "shots")
    _require(path, "shots")
    df = pd.read_parquet(path)
    if match_id is not None:
        df = df[df["match_id"] == match_id]
    return df


@_cache_data
def load_player_summary(team: str = "barcelona") -> pd.DataFrame:
    path = _flat_path(team, "player_summary")
    _require(path, "player_summary")
    return pd.read_parquet(path)


@_cache_data
def load_team_summary(team: str = "barcelona") -> pd.DataFrame:
    path = _flat_path(team, "team_summary")
    _require(path, "team_summary")
    df = pd.read_parquet(path)
    return df.sort_values("date").reset_index(drop=True)


@_cache_data
def load_player_pass_stats(team: str = "barcelona") -> pd.DataFrame:
    path = _flat_path(team, "player_pass_stats")
    _require(path, "player_pass_stats")
    return pd.read_parquet(path)


@_cache_data
def load_player_carry_stats(team: str = "barcelona") -> pd.DataFrame:
    path = _flat_path(team, "player_carry_stats")
    _require(path, "player_carry_stats")
    return pd.read_parquet(path)


def _read_partition(team: str, name: str, match_id: int) -> pd.DataFrame:
    """Single-match read from a match_id-partitioned parquet dataset.
    Only the matching partition is touched -- the rest of the dataset is
    never loaded."""
    base = _partitioned_path(team, name)
    _require(base, name)
    part_dir = base / f"match_id={match_id}"
    if not part_dir.exists():
        return pd.DataFrame()
    df = pd.read_parquet(part_dir)
    df["match_id"] = match_id  # partition column is dropped by pyarrow on read
    return df


@_cache_data
def load_events(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    if match_id is None:
        raise ValueError(
            "load_events requires a match_id — the full events table is "
            "intentionally never loaded at once (200MB+ across 531 matches)."
        )
    return _read_partition(team, "events", match_id)


@_cache_data
def load_passes(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    if match_id is None:
        raise ValueError(
            "load_passes requires a match_id for row-level detail. "
            "For cross-match player totals use load_player_pass_stats()."
        )
    return _read_partition(team, "passes", match_id)


@_cache_data
def load_carries(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    if match_id is None:
        raise ValueError(
            "load_carries requires a match_id for row-level detail. "
            "For cross-match player totals use load_player_carry_stats()."
        )
    return _read_partition(team, "carries", match_id)


@_cache_data
def load_pressures(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    if match_id is None:
        raise ValueError("load_pressures requires a match_id.")
    return _read_partition(team, "pressures", match_id)
