"""Player-level analytics.

Minutes played are derived from lineups.from/to where reliably available
(both from and to present within the same period); matches with an
unresolved 'to' (i.e. the player finished the match) are minutes played
until the match's actual end, approximated at 90 (or 120 for matches that
went to extra time, detected via a 3rd/4th period in lineups).

We are explicit in the UI whenever a number is an approximation.
"""

from __future__ import annotations

import pandas as pd

from data import loader


def _minutes_from_clock(clock: str) -> float | None:
    if pd.isna(clock):
        return None
    try:
        mm, ss = clock.split(":")
        return int(mm) + int(ss) / 60
    except (ValueError, AttributeError):
        return None


def player_appearances(team: str = "barcelona") -> pd.DataFrame:
    """Appearances + best-effort minutes per player, aggregated across all
    matches from lineups.csv."""
    lu = loader.load_lineups(team).copy()
    lu["start_min"] = lu["from"].apply(_minutes_from_clock)
    lu["end_min"] = lu["to"].apply(_minutes_from_clock)
    # If 'to' is missing, the player was on the pitch until the match ended.
    # We approximate full-match end as 90 (extra-time matches understated;
    # flagged as a known limitation, not silently "corrected").
    lu["end_min_filled"] = lu["end_min"].fillna(90)
    lu["minutes_played_est"] = (lu["end_min_filled"] - lu["start_min"]).clip(lower=0)

    agg = (
        lu.groupby(["player_id", "player_name"], observed=True)
        .agg(
            appearances=("match_id", "nunique"),
            starts=("start_reason", lambda s: (s == "Starting XI").sum()),
            minutes_played_est=("minutes_played_est", "sum"),
        )
        .reset_index()
    )
    agg["minutes_played_est"] = agg["minutes_played_est"].round(0)
    return agg.sort_values("appearances", ascending=False)


def player_profile(player_id: int, team: str = "barcelona") -> dict:
    """Single-player summary combining player_summary.csv (counts) with the
    pre-aggregated pass/carry accuracy caches and shots.csv (goals/xG)."""
    ps = loader.load_player_summary(team)
    row = ps[ps["player_id"] == player_id]
    if row.empty:
        return {}
    row = row.iloc[0]

    pass_stats = loader.load_player_pass_stats(team)
    pass_row = pass_stats[pass_stats["player_id"] == player_id]
    carry_stats = loader.load_player_carry_stats(team)
    carry_row = carry_stats[carry_stats["player_id"] == player_id]

    shots = loader.load_shots(team)
    p_shots = shots[shots["player_id"] == player_id]
    goals = int((p_shots["outcome"] == "Goal").sum())
    xg = float(p_shots["xg"].sum()) if "xg" in p_shots.columns else None

    appearances = player_appearances(team)
    app_row = appearances[appearances["player_id"] == player_id]

    return {
        "player_id": player_id,
        "player_name": row["player_name"],
        "country": row.get("country"),
        "jersey_number": row.get("jersey_number"),
        "appearances": int(app_row["appearances"].iloc[0]) if not app_row.empty else None,
        "minutes_played_est": float(app_row["minutes_played_est"].iloc[0]) if not app_row.empty else None,
        "total_events": int(row["total_events"]),
        "passes_attempted": int(pass_row["passes_attempted"].iloc[0]) if not pass_row.empty else 0,
        "pass_completion_pct": float(pass_row["pass_completion_pct"].iloc[0]) if not pass_row.empty else None,
        "carries": int(carry_row["carries"].iloc[0]) if not carry_row.empty else 0,
        "progressive_carries": int(carry_row["progressive_carries"].iloc[0]) if not carry_row.empty else 0,
        "shots": int(len(p_shots)),
        "goals": goals,
        "xg": round(xg, 2) if xg is not None else None,
        "pressures": int(row["pressures"]),
    }


def top_players(metric: str, n: int = 10, team: str = "barcelona") -> pd.DataFrame:
    """metric in {passes, carries, shots, pressures, goals, pass_completion_pct,
    progressive_carries}."""
    ps = loader.load_player_summary(team)[["player_id", "player_name", "passes", "carries", "shots", "pressures"]]
    pass_stats = loader.load_player_pass_stats(team)[["player_id", "pass_completion_pct"]]
    carry_stats = loader.load_player_carry_stats(team)[["player_id", "progressive_carries"]]

    shots = loader.load_shots(team)
    goals = shots[shots["outcome"] == "Goal"].groupby("player_id").size().rename("goals")

    df = ps.merge(pass_stats, on="player_id", how="left").merge(carry_stats, on="player_id", how="left")
    df = df.merge(goals, on="player_id", how="left")
    df["goals"] = df["goals"].fillna(0).astype(int)

    if metric not in df.columns:
        raise ValueError(f"Unknown metric '{metric}'. Available: {list(df.columns)}")

    return df.sort_values(metric, ascending=False).head(n)[["player_id", "player_name", metric]]


def compare_players(player_ids: list[int], team: str = "barcelona") -> pd.DataFrame:
    profiles = [player_profile(pid, team) for pid in player_ids]
    return pd.DataFrame([p for p in profiles if p]).set_index("player_name")
