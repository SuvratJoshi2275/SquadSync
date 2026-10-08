"""Match-level analytics.

Everything here is scoped to one match_id and reads only that match's
partition from the cache (see data/loader.py) -- never the full
events/passes/carries/pressures tables.
"""

from __future__ import annotations

import pandas as pd

from data import loader


def match_list(team: str = "barcelona") -> pd.DataFrame:
    """Compact list for the match picker: date, opponent, competition, score, result."""
    matches = loader.load_matches(team)
    ts = loader.load_team_summary(team)[["match_id", "score", "result"]]
    df = matches.merge(ts, on="match_id", how="left")
    return df[
        ["match_id", "match_date", "competition", "season", "home_team", "away_team", "score", "result"]
    ].sort_values("match_date", ascending=False)


def match_overview(match_id: int, team: str = "barcelona") -> dict:
    matches = loader.load_matches(team)
    row = matches[matches["match_id"] == match_id]
    if row.empty:
        return {}
    row = row.iloc[0]
    ts = loader.load_team_summary(team)
    ts_row = ts[ts["match_id"] == match_id]
    result = ts_row["result"].iloc[0] if not ts_row.empty else None
    barca_is_home = row["home_team"] == "Barcelona"
    opponent = row["away_team"] if barca_is_home else row["home_team"]
    venue = "Home" if barca_is_home else "Away"
    return {
        "match_id": int(match_id),
        "date": row["match_date"],
        "kick_off": row["kick_off"],
        "competition": row["competition"],
        "season": row["season"],
        "opponent": opponent,
        "venue": venue,
        "score": f"{row['home_score']}-{row['away_score']}",
        "result": result,
        "stadium": row["stadium"],
        "match_week": row["match_week"],
    }


def match_stats(match_id: int, team: str = "barcelona") -> dict:
    shots = loader.load_shots(team, match_id)
    passes = loader.load_passes(team, match_id)
    carries = loader.load_carries(team, match_id)
    pressures = loader.load_pressures(team, match_id)

    on_target_outcomes = {"Goal", "Saved", "Saved Off Target", "Saved to Post"}
    total_shots = len(shots)
    on_target = shots["outcome"].isin(on_target_outcomes).sum() if total_shots else 0
    xg_total = float(shots["xg"].sum()) if "xg" in shots.columns and total_shots else 0.0

    completed_passes = passes["outcome"].isna().sum() if len(passes) else 0

    return {
        "shots": total_shots,
        "shots_on_target": int(on_target),
        "total_xg": round(xg_total, 2),
        "passes_attempted": len(passes),
        "passes_completed": int(completed_passes),
        "pass_completion_pct": round(100 * completed_passes / len(passes), 1) if len(passes) else None,
        "carries": len(carries),
        "pressures": len(pressures),
    }


def match_lineup(match_id: int, team: str = "barcelona") -> pd.DataFrame:
    lu = loader.load_lineups(team, match_id)
    cols = ["team_name", "player_name", "jersey_number", "position", "from", "to", "start_reason", "end_reason"]
    return lu[cols].sort_values(["team_name", "jersey_number"])


def match_formation(match_id: int, team: str = "barcelona") -> pd.DataFrame:
    f = loader.load_formations(team, match_id)
    return f[["team_name", "minute", "formation"]].sort_values("minute")


def match_shot_map(match_id: int, team: str = "barcelona") -> pd.DataFrame:
    shots = loader.load_shots(team, match_id)
    return shots[
        ["minute", "team_name", "player_name", "location_x", "location_y", "outcome", "xg", "body_part", "shot_type"]
    ].sort_values("minute")


def match_passing_network(match_id: int, team: str = "barcelona", squad_team: str = "Barcelona") -> pd.DataFrame:
    """Edge list of completed pass counts between player pairs, for the
    squad_team only (default Barcelona) -- basis for a passing-network
    diagram. recipient_name comes straight from the source event."""
    passes = loader.load_passes(team, match_id)
    p = passes[(passes["team_name"] == squad_team) & (passes["outcome"].isna())]
    edges = (
        p.groupby(["player_name", "recipient_name"], observed=True)
        .size()
        .reset_index(name="pass_count")
        .sort_values("pass_count", ascending=False)
    )
    return edges


def match_event_timeline(match_id: int, team: str = "barcelona", event_types: list[str] | None = None) -> pd.DataFrame:
    """Chronological timeline of notable events. Restricted to a
    UI-relevant subset by default (goals, shots, cards/fouls, subs) to stay
    readable -- full events.csv still available via loader.load_events for
    deeper drill-down."""
    events = loader.load_events(team, match_id)
    default_types = [
        "Shot", "Substitution", "Foul Committed", "Bad Behaviour",
        "Own Goal For", "Own Goal Against", "Tactical Shift",
    ]
    types = event_types or default_types
    tl = events[events["event_type"].isin(types)].copy()
    return tl[
        ["minute", "second", "event_type", "team_name", "player_name"]
    ].sort_values(["minute", "second"])


def match_goals(match_id: int, team: str = "barcelona") -> dict:
    """Goal-scoring events for a match: player, minute, penalty flag.

    Important data limitation: this dataset's event feed (events.csv,
    shots.csv) is captured from Barcelona's side only -- the opponent's
    open-play shots are not present at all. That means opponent goals can
    only be individually attributed here when they came via an
    "Own Goal Against" event (a Barcelona player scoring into their own
    net, which the Barcelona event feed does capture). Opponent goals
    scored from normal open play are invisible to this dataset.

    Returns {"goals": DataFrame[minute, team_name, player_name,
    is_penalty], "opponent_goals_fully_attributed": bool} so callers can
    show an honest disclaimer instead of silently presenting a partial
    opponent scorer list as complete.
    """
    matches = loader.load_matches(team)
    row = matches[matches["match_id"] == match_id]
    if row.empty:
        return {"goals": pd.DataFrame(columns=["minute", "team_name", "player_name", "is_penalty"]),
                "opponent_goals_fully_attributed": True}
    row = row.iloc[0]
    home_team, away_team = row["home_team"], row["away_team"]
    home_score, away_score = int(row["home_score"]), int(row["away_score"])
    barca_team_name = "Barcelona"
    opponent_name = away_team if home_team == barca_team_name else home_team
    opponent_score = away_score if home_team == barca_team_name else home_score

    shots = loader.load_shots(team, match_id)
    goals = shots[shots["outcome"] == "Goal"].copy()
    goals["is_penalty"] = goals["shot_type"] == "Penalty"
    goals = goals[["minute", "team_name", "player_name", "is_penalty"]]

    events = loader.load_events(team, match_id)
    own_goals = events[events["event_type"].isin(["Own Goal For", "Own Goal Against"])].copy()
    if len(own_goals):
        # "Own Goal For" = Barcelona benefited (an opponent player's own
        # goal); "Own Goal Against" = Barcelona's own net, crediting the
        # opponent. Both event rows carry team_name == "Barcelona" (the
        # dataset's own perspective), so attribution is a direct mapping,
        # not a match-history lookup.
        own_goals["scoring_team"] = own_goals["event_type"].map(
            {"Own Goal For": barca_team_name, "Own Goal Against": opponent_name}
        )
        own_goals["player_name"] = own_goals["player_name"].astype(object).where(
            own_goals["player_name"].notna(), "Own Goal"
        )
        own_goals["is_penalty"] = False
        own_goals = own_goals[["minute", "scoring_team", "player_name", "is_penalty"]].rename(
            columns={"scoring_team": "team_name"}
        )
        goals = pd.concat([goals, own_goals], ignore_index=True)

    goals = goals.sort_values("minute")
    attributed_opponent_goals = int((goals["team_name"] == opponent_name).sum())
    return {
        "goals": goals,
        "opponent_goals_fully_attributed": attributed_opponent_goals >= opponent_score,
        "opponent_name": opponent_name,
        "opponent_score": opponent_score,
        "attributed_opponent_goals": attributed_opponent_goals,
    }


def match_substitutions(match_id: int, team: str = "barcelona") -> pd.DataFrame:
    """Substitution events (player coming off) with minute, from lineups.csv
    'to' timestamps -- more reliable than parsing events.csv Substitution
    rows, since lineups.csv already records who came off and when."""
    lu = loader.load_lineups(team, match_id)
    subs = lu[lu["end_reason"].astype(str).str.startswith("Substitution - Off")].copy()
    if subs.empty:
        return pd.DataFrame(columns=["minute", "team_name", "player_name"])
    subs["minute"] = subs["to"].str.split(":").str[0].astype(float)
    return subs[["minute", "team_name", "player_name"]].sort_values("minute")
