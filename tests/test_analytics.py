"""
Lightweight sanity checks for the analytics layer -- not a full pytest
suite, just cross-checks against the raw CSVs so a data/aggregation bug
doesn't reach the demo.

Run: python tests/test_analytics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from analytics import team, player, match, tactical
from data import loader

RAW = Path(__file__).parent.parent / "data" / "raw" / "barcelona"


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}")
    assert cond, label


def main():
    raw_matches = pd.read_csv(RAW / "matches.csv")
    raw_team_summary = pd.read_csv(RAW / "team_summary.csv")
    raw_shots = pd.read_csv(RAW / "shots.csv")
    raw_passes = pd.read_csv(RAW / "passes.csv")

    # --- team.py ---
    record = team.team_record()
    check("matches_played matches raw row count", record["matches_played"] == len(raw_matches))
    check("wins+draws+losses == matches_played",
          record["wins"] + record["draws"] + record["losses"] == record["matches_played"])

    shooting = team.shooting_summary()
    check("total_shots matches raw shots.csv row count", shooting["total_shots"] == len(raw_shots))
    check("goals matches raw Goal outcome count",
          shooting["goals"] == int((raw_shots["outcome"] == "Goal").sum()))

    passing = team.passing_summary()
    check("passes_attempted matches raw passes.csv row count",
          passing["passes_attempted"] == len(raw_passes))
    check("passes_completed matches raw NaN-outcome count",
          passing["passes_completed"] == int(raw_passes["outcome"].isna().sum()))

    # --- player.py ---
    appearances = player.player_appearances()
    check("appearances table is non-empty", len(appearances) > 0)
    check("appearances <= total matches for every player",
          (appearances["appearances"] <= record["matches_played"]).all())

    sample_pid = int(appearances.iloc[0]["player_id"])
    profile = player.player_profile(sample_pid)
    check("player_profile returns a name", bool(profile.get("player_name")))

    # --- match.py ---
    sample_match_id = int(raw_matches.iloc[0]["match_id"])
    overview = match.match_overview(sample_match_id)
    check("match_overview resolves opponent", bool(overview.get("opponent")))

    stats = match.match_stats(sample_match_id)
    raw_match_passes = raw_passes[raw_passes["match_id"] == sample_match_id]
    check("match_stats passes_attempted matches raw filter",
          stats["passes_attempted"] == len(raw_match_passes))

    # --- tactical.py ---
    dist = tactical.pass_zone_distribution(match_id=sample_match_id)
    check("pass_zone_distribution sums to ~100%", abs(dist["pct_of_passes"].sum() - 100) < 0.5)

    formations = tactical.formation_usage()
    check("formation_usage pct sums to ~100%", abs(formations["pct_of_matches"].sum() - 100) < 1.0)

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
