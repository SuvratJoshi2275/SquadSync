"""
SquadSync data cache builder.

Converts raw StatsBomb-derived CSVs into an optimized Parquet cache:

  data/raw/<team>/*.csv          -> data/processed/<team>/*.parquet

Design goals (see project brief):
  - The Streamlit app must never load the full events.csv / passes.csv /
    carries.csv / pressures.csv into memory at startup.
  - Large event-level tables (events, passes, carries, pressures) are
    partitioned by match_id, so the app can read a single match's slice
    in O(1 partition) instead of scanning the whole file.
  - Common aggregates (per-player, per-match totals) are pre-computed once
    here so the UI layer never has to re-scan raw event rows for basic
    stats.
  - Architecture is team-namespaced (data/raw/<team>/...) so adding
    Arsenal, Chelsea, etc. later is just "drop CSVs in a new folder and
    re-run this script" -- no analytics code changes required.

Run:  python data/build_cache.py [--team barcelona]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Tables partitioned by match_id (large, event-level).
PARTITIONED_TABLES = ["events", "passes", "carries", "pressures"]

# Tables kept as a single small parquet file (already match- or
# player-aggregated, or genuinely small).
FLAT_TABLES = [
    "matches",
    "players",
    "lineups",
    "formations",
    "shots",
    "player_summary",
    "team_summary",
]

# Columns safe to downcast to save memory/disk. Applied where present.
INT32_CANDIDATES = ["match_id", "team_id", "player_id", "possession_team_id"]
CATEGORY_CANDIDATES = [
    "event_type", "team_name", "player_name", "position", "play_pattern",
    "outcome", "pass_type", "pass_height", "body_part", "technique",
    "shot_type", "competition", "country", "season", "result", "venue",
]


def _optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    for col in INT32_CANDIDATES:
        if col in df.columns and df[col].notna().all():
            df[col] = df[col].astype("int32")
    for col in CATEGORY_CANDIDATES:
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df


def _build_flat(team: str, name: str) -> None:
    src = RAW_DIR / team / f"{name}.csv"
    if not src.exists():
        print(f"  [skip] {name}.csv not found")
        return
    df = pd.read_csv(src)
    df = _optimize_dtypes(df)
    out_dir = PROCESSED_DIR / team
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / f"{name}.parquet", index=False)
    print(f"  [ok] {name}: {len(df):,} rows -> {name}.parquet")


def _build_partitioned(team: str, name: str) -> pd.DataFrame | None:
    src = RAW_DIR / team / f"{name}.csv"
    if not src.exists():
        print(f"  [skip] {name}.csv not found")
        return None
    df = pd.read_csv(src)
    df = _optimize_dtypes(df)
    out_dir = PROCESSED_DIR / team / name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir, partition_cols=["match_id"], index=False)
    print(f"  [ok] {name}: {len(df):,} rows -> {name}/ (partitioned by match_id)")
    return df


def _build_player_aggregates(team: str, passes: pd.DataFrame, carries: pd.DataFrame) -> None:
    """Pre-compute pass/carry accuracy & progression stats per player so the
    Player Analysis page never has to re-scan the raw event tables."""
    out_dir = PROCESSED_DIR / team
    out_dir.mkdir(parents=True, exist_ok=True)

    if passes is not None and len(passes):
        p = passes.copy()
        p["is_complete"] = p["outcome"].isna()
        agg = (
            p.groupby(["player_id", "player_name"], observed=True)
            .agg(
                passes_attempted=("event_id", "count"),
                passes_completed=("is_complete", "sum"),
            )
            .reset_index()
        )
        agg["pass_completion_pct"] = (
            100 * agg["passes_completed"] / agg["passes_attempted"]
        ).round(1)
        agg.to_parquet(out_dir / "player_pass_stats.parquet", index=False)
        print(f"  [ok] player_pass_stats: {len(agg):,} players")

    if carries is not None and len(carries):
        c = carries.copy()
        c["progress_x"] = c["end_x"] - c["location_x"]
        c["is_progressive"] = c["progress_x"] >= 10  # StatsBomb pitch is 120 units long
        agg = (
            c.groupby(["player_id", "player_name"], observed=True)
            .agg(
                carries=("event_id", "count"),
                progressive_carries=("is_progressive", "sum"),
                avg_progress_x=("progress_x", "mean"),
            )
            .reset_index()
        )
        agg["avg_progress_x"] = agg["avg_progress_x"].round(2)
        agg.to_parquet(out_dir / "player_carry_stats.parquet", index=False)
        print(f"  [ok] player_carry_stats: {len(agg):,} players")


def build(team: str) -> None:
    print(f"Building cache for team: {team}")
    passes_df, carries_df = None, None
    for name in FLAT_TABLES:
        _build_flat(team, name)
    for name in PARTITIONED_TABLES:
        df = _build_partitioned(team, name)
        if name == "passes":
            passes_df = df
        if name == "carries":
            carries_df = df
    _build_player_aggregates(team, passes_df, carries_df)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", default="barcelona")
    args = parser.parse_args()
    build(args.team)
