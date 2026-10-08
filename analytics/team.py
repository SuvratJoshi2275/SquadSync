"""Team-level analytics.

All functions take a `team` namespace (default "barcelona") and return
plain pandas DataFrames/dicts -- no Streamlit calls in here, so this module
is independently testable and reusable if the UI layer ever changes.
"""

from __future__ import annotations

import pandas as pd

from data import loader


def team_record(team: str = "barcelona") -> dict:
    """Overall matches played / W-D-L / goals for-against, from team_summary
    (goals derived from the 'score' string, e.g. '2-1' = Barca-Opponent)."""
    ts = loader.load_team_summary(team)
    gf, ga = _goals_for_against(ts)
    return {
        "matches_played": len(ts),
        "wins": int((ts["result"] == "Win").sum()),
        "draws": int((ts["result"] == "Draw").sum()),
        "losses": int((ts["result"] == "Loss").sum()),
        "goals_for": int(gf.sum()),
        "goals_against": int(ga.sum()),
        "goal_difference": int(gf.sum() - ga.sum()),
    }


def _goals_for_against(team_summary: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """team_summary['score'] is always written as '<Barca>-<Opponent>'
    regardless of home/away, per the source dataset convention."""
    parts = team_summary["score"].str.split("-", expand=True).astype(int)
    return parts[0], parts[1]


def shooting_summary(team: str = "barcelona") -> dict:
    shots = loader.load_shots(team)
    on_target_outcomes = {"Goal", "Saved", "Saved Off Target", "Saved to Post"}
    total = len(shots)
    on_target = shots["outcome"].isin(on_target_outcomes).sum()
    goals = int((shots["outcome"] == "Goal").sum())
    xg_total = float(shots["xg"].sum()) if "xg" in shots.columns else None
    return {
        "total_shots": int(total),
        "shots_on_target": int(on_target),
        "shot_accuracy_pct": round(100 * on_target / total, 1) if total else None,
        "goals": goals,
        "total_xg": round(xg_total, 2) if xg_total is not None else None,
        "xg_per_shot": round(xg_total / total, 3) if xg_total and total else None,
        "goals_minus_xg": round(goals - xg_total, 2) if xg_total is not None else None,
    }


def passing_summary(team: str = "barcelona") -> dict:
    """Aggregated from the pre-computed per-player pass cache -- avoids
    re-scanning the 367k-row passes table at request time."""
    pp = loader.load_player_pass_stats(team)
    attempted = int(pp["passes_attempted"].sum())
    completed = int(pp["passes_completed"].sum())
    return {
        "passes_attempted": attempted,
        "passes_completed": completed,
        "pass_completion_pct": round(100 * completed / attempted, 1) if attempted else None,
    }


def per_match_averages(team: str = "barcelona") -> dict:
    ts = loader.load_team_summary(team)
    gf, _ = _goals_for_against(ts)
    n = len(ts)
    return {
        "avg_goals_per_match": round(gf.mean(), 2),
        "avg_shots_per_match": round(ts["shots"].mean(), 2),
        "avg_passes_per_match": round(ts["passes"].mean(), 2),
        "avg_carries_per_match": round(ts["carries"].mean(), 2),
        "avg_pressures_per_match": round(ts["pressures"].mean(), 2),
        "matches": n,
    }


def performance_trend(team: str = "barcelona", window: int = 10) -> pd.DataFrame:
    """Rolling form: points-per-game and goal difference over the last
    `window` matches, in chronological order -- for the Dashboard trend chart."""
    ts = loader.load_team_summary(team).copy()
    gf, ga = _goals_for_against(ts)
    ts["goals_for"], ts["goals_against"] = gf, ga
    ts["points"] = ts["result"].map({"Win": 3, "Draw": 1, "Loss": 0})
    ts["rolling_ppg"] = ts["points"].rolling(window, min_periods=1).mean().round(2)
    ts["rolling_gd"] = (ts["goals_for"] - ts["goals_against"]).rolling(window, min_periods=1).mean().round(2)
    return ts[["match_id", "date", "opponent", "result", "points", "rolling_ppg", "rolling_gd"]]


def by_competition(team: str = "barcelona") -> pd.DataFrame:
    matches = loader.load_matches(team)
    ts = loader.load_team_summary(team).merge(
        matches[["match_id", "competition", "season"]], on="match_id", how="left"
    )
    gf, ga = _goals_for_against(ts)
    ts["goals_for"], ts["goals_against"] = gf, ga
    grouped = ts.groupby("competition", observed=True).agg(
        matches=("match_id", "count"),
        wins=("result", lambda s: (s == "Win").sum()),
        draws=("result", lambda s: (s == "Draw").sum()),
        losses=("result", lambda s: (s == "Loss").sum()),
        goals_for=("goals_for", "sum"),
        goals_against=("goals_against", "sum"),
    ).reset_index()
    return grouped.sort_values("matches", ascending=False)
