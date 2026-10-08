"""First-stage tactical analytics.

Scope is deliberately limited to what is directly computable from the
current dataset: formation usage, spatial distribution of passes/carries/
shots/pressures, and simple progression indicators.

This module does NOT generate qualitative tactical narratives (e.g. "Barca
dominated the left flank"). It only returns numbers/tables; any such
sentence must be produced by a future analysis/AI layer built on top of
these numbers, and only when a specific supporting metric is cited.
"""

from __future__ import annotations

import pandas as pd

from data import loader

PITCH_LENGTH = 120  # StatsBomb pitch units
PITCH_WIDTH = 80
THIRD = PITCH_LENGTH / 3


def formation_usage(team: str = "barcelona") -> pd.DataFrame:
    """How often each formation was used as the Starting XI shape, across
    all matches, plus in how many distinct matches it appeared."""
    f = loader.load_formations(team)
    starting = f[f["minute"] == 0]
    agg = (
        starting.groupby("formation", observed=True)
        .agg(matches_used=("match_id", "nunique"))
        .reset_index()
        .sort_values("matches_used", ascending=False)
    )
    agg["pct_of_matches"] = (100 * agg["matches_used"] / starting["match_id"].nunique()).round(1)
    return agg


def formation_changes(match_id: int, team: str = "barcelona") -> pd.DataFrame:
    """In-match formation changes (Tactical Shift events with a recorded
    formation) for Barcelona, in chronological order."""
    f = loader.load_formations(team, match_id)
    barca = f[f["team_name"] == "Barcelona"].sort_values("minute")
    changes = barca[barca["formation"] != barca["formation"].shift()]
    return changes[["minute", "formation"]]


def _third_label(x: float) -> str:
    if x < THIRD:
        return "Defensive Third"
    if x < 2 * THIRD:
        return "Middle Third"
    return "Attacking Third"


def pass_zone_distribution(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    """% of pass origins by pitch third. If match_id is None, computed from
    the cross-match player pass cache is NOT possible (no location data
    there) -- this function requires event-level data and is therefore
    match-scoped only, by design, to avoid an unintended full-table scan."""
    if match_id is None:
        raise ValueError("pass_zone_distribution requires match_id (location data is match-scoped).")
    passes = loader.load_passes(team, match_id)
    barca = passes[passes["team_name"] == "Barcelona"].copy()
    barca["third"] = barca["location_x"].apply(_third_label)
    dist = barca["third"].value_counts(normalize=True).mul(100).round(1).reset_index()
    dist.columns = ["third", "pct_of_passes"]
    return dist


def carry_progression(match_id: int, team: str = "barcelona") -> dict:
    """Progressive carries (net forward movement >= 10 pitch units) for
    Barcelona in a given match, plus average progress distance."""
    carries = loader.load_carries(team, match_id)
    barca = carries[carries["team_name"] == "Barcelona"].copy()
    if barca.empty:
        return {"carries": 0, "progressive_carries": 0, "avg_progress_x": None}
    barca["progress_x"] = barca["end_x"] - barca["location_x"]
    progressive = (barca["progress_x"] >= 10).sum()
    return {
        "carries": int(len(barca)),
        "progressive_carries": int(progressive),
        "progressive_pct": round(100 * progressive / len(barca), 1),
        "avg_progress_x": round(barca["progress_x"].mean(), 2),
    }


def shot_zone_distribution(team: str = "barcelona", match_id: int | None = None) -> pd.DataFrame:
    """% of shots by broad location bucket (inside/outside box, approximated
    via StatsBomb pitch coordinates: box is x >= 102, 18 <= y <= 62)."""
    shots = loader.load_shots(team, match_id) if match_id else loader.load_shots(team)
    if shots.empty:
        return pd.DataFrame(columns=["zone", "pct_of_shots"])
    in_box = (shots["location_x"] >= 102) & (shots["location_y"].between(18, 62))
    shots = shots.copy()
    shots["zone"] = in_box.map({True: "Inside Box", False: "Outside Box"})
    dist = shots["zone"].value_counts(normalize=True).mul(100).round(1).reset_index()
    dist.columns = ["zone", "pct_of_shots"]
    return dist


def pressure_zone_distribution(match_id: int, team: str = "barcelona") -> pd.DataFrame:
    """Where Barcelona applied defensive pressure, by pitch third."""
    pressures = loader.load_pressures(team, match_id)
    barca = pressures[pressures["team_name"] == "Barcelona"].copy()
    if barca.empty:
        return pd.DataFrame(columns=["third", "pct_of_pressures"])
    barca["third"] = barca["location_x"].apply(_third_label)
    dist = barca["third"].value_counts(normalize=True).mul(100).round(1).reset_index()
    dist.columns = ["third", "pct_of_pressures"]
    return dist


def player_involvement(match_id: int, team: str = "barcelona") -> pd.DataFrame:
    """Simple involvement score per Barcelona player in a match: passes +
    carries + pressures + shots, as a first-stage proxy for on-ball/
    off-ball activity. Not a weighted or validated influence metric."""
    passes = loader.load_passes(team, match_id)
    carries = loader.load_carries(team, match_id)
    pressures = loader.load_pressures(team, match_id)
    shots = loader.load_shots(team, match_id)

    def _count_by_player(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
        barca = df[df["team_name"] == "Barcelona"]
        return barca.groupby("player_name", observed=True).size().rename(col_name)

    parts = [
        _count_by_player(passes, "passes"),
        _count_by_player(carries, "carries"),
        _count_by_player(pressures, "pressures"),
        _count_by_player(shots, "shots"),
    ]
    combined = pd.concat(parts, axis=1).fillna(0).astype(int)
    combined["involvement_score"] = combined.sum(axis=1)
    return combined.reset_index().sort_values("involvement_score", ascending=False)
