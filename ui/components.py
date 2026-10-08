"""Reusable presentational components shared across Fan and Coach mode.

These turn analytics output (DataFrames/dicts with backend-style column
names) into football-product visuals. No backend field names (match_id,
player_id, location_x/y, position_id, etc.) are ever rendered to the user
by these components -- they consume those fields internally and emit
football language.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui import theme

# Schematic pitch placement for lineup positions. StatsBomb gives us the
# *position label* per player (real data) but not a per-player pitch
# coordinate for the starting shape, so this maps each named role to a
# fixed, labeled template location -- an approximation for display only,
# not a claim of tracked positioning data.
POSITION_XY = {
    "Goalkeeper": (8, 40),
    "Right Back": (25, 14), "Right Center Back": (18, 28), "Center Back": (16, 40),
    "Left Center Back": (18, 52), "Left Back": (25, 66),
    "Right Wing Back": (38, 10), "Left Wing Back": (38, 70),
    "Right Defensive Midfield": (42, 26), "Center Defensive Midfield": (38, 40),
    "Left Defensive Midfield": (42, 54),
    "Right Center Midfield": (55, 26), "Center Midfield": (55, 40), "Left Center Midfield": (55, 54),
    "Right Midfield": (58, 12), "Left Midfield": (58, 68),
    "Right Attacking Midfield": (76, 26), "Center Attacking Midfield": (72, 40),
    "Left Attacking Midfield": (76, 54),
    "Right Wing": (98, 12), "Left Wing": (98, 68),
    "Right Center Forward": (100, 30), "Secondary Striker": (95, 40),
    "Center Forward": (106, 40), "Left Center Forward": (100, 50),
}


def format_minute(minute, second=None) -> str:
    m = int(minute) if pd.notna(minute) else 0
    return f"{m}'" if m <= 90 else f"90+{m - 90}'"


# --------------------------------------------------------------------- #
# Match cards
# --------------------------------------------------------------------- #

def match_score_card(row: dict, key: str, on_click=None):
    """Compact clickable match card: date/competition, scoreline, venue."""
    barca_home = row["home_team"] == "Barcelona"
    opponent = row["away_team"] if barca_home else row["home_team"]
    barca_score, opp_score = (row["home_score"], row["away_score"]) if barca_home else (row["away_score"], row["home_score"])
    with st.container(border=True):
        st.markdown(
            f'<div class="ss-label">{row["competition"]} · {row["match_date"]}</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([3, 1, 2])
        with c1:
            st.markdown(f"**Barcelona**" + (" 🏠" if barca_home else " ✈️"))
            st.markdown(f"**{opponent}**")
        with c2:
            st.markdown(f'<div class="ss-score" style="text-align:center">{barca_score}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ss-score" style="text-align:center">{opp_score}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(theme.result_pill(row.get("result")), unsafe_allow_html=True)
            if st.button("Match Centre →", key=key, width="stretch"):
                if on_click:
                    on_click(int(row["match_id"]))


def form_strip(results: list[str]):
    dots = "".join(theme.form_dot(r) for r in results)
    st.markdown(dots, unsafe_allow_html=True)


# --------------------------------------------------------------------- #
# Comparison bars (match stats: Barca vs opponent)
# --------------------------------------------------------------------- #

def comparison_bar(label: str, left_val, right_val, left_name="Barcelona", right_name="Opponent", higher_is_better=True):
    try:
        l, r = float(left_val), float(right_val)
    except (TypeError, ValueError):
        l, r = 0, 0
    total = (l + r) or 1
    l_pct = 100 * l / total
    st.markdown(f'<div class="ss-label" style="text-align:center">{label}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(f'<div style="text-align:right;font-weight:700">{left_val}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div style="font-weight:700">{right_val}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display:flex;height:6px;border-radius:4px;overflow:hidden;background:{theme.BORDER};margin-bottom:10px">
            <div style="width:{l_pct}%;background:{theme.ACCENT}"></div>
            <div style="width:{100-l_pct}%;background:{theme.TEXT_MUTED}"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------- #
# Pitch visuals
# --------------------------------------------------------------------- #

def shot_map(shots: pd.DataFrame, team_name: str = "Barcelona") -> go.Figure:
    fig = theme.base_pitch()
    outcome_color = {
        "Goal": theme.ACCENT, "Saved": "#F2C14E", "Blocked": "#8B96A8",
        "Off T": "#EF5C6E", "Wayward": "#EF5C6E", "Post": "#F2C14E",
        "Saved Off Target": "#F2C14E", "Saved to Post": "#F2C14E",
    }
    for outcome, group in shots.groupby("outcome", observed=True):
        fig.add_trace(go.Scatter(
            x=group["location_x"], y=group["location_y"],
            mode="markers",
            marker=dict(
                size=(group["xg"] * 40 + 8).clip(upper=26),
                color=outcome_color.get(outcome, "#8B96A8"),
                line=dict(width=1, color="#06110D"),
                symbol="circle" if outcome != "Goal" else "star",
            ),
            name=outcome,
            text=[
                f"{p} — {format_minute(m)}<br>{outcome}<br>xG {x:.2f}"
                for p, m, x in zip(group["player_name"], group["minute"], group["xg"])
            ],
            hoverinfo="text",
        ))
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.05, font=dict(color=theme.TEXT_MUTED, size=10)))
    return fig


def _dedupe_positions(lineup: pd.DataFrame) -> pd.DataFrame:
    lineup = lineup.copy()
    xs, ys = [], []
    seen = {}
    for pos in lineup["position"]:
        base = POSITION_XY.get(pos, (60, 40))
        n = seen.get(pos, 0)
        seen[pos] = n + 1
        offset = (n - (seen[pos] - 1) / 2) * 8 if seen[pos] > 1 else 0
        xs.append(base[0])
        ys.append(base[1])
    lineup["px"], lineup["py"] = xs, ys
    # spread exact duplicates vertically so labels don't overlap
    for pos, grp in lineup.groupby("position"):
        if len(grp) > 1:
            spread = [(-8, 0), (8, 0), (0, -8), (0, 8)]
            for i, idx in enumerate(grp.index):
                dx, dy = spread[i % len(spread)]
                lineup.loc[idx, "py"] += dy
    return lineup


def lineup_pitch(lineup: pd.DataFrame) -> go.Figure:
    """Starting XI on a schematic pitch, using each player's recorded
    position label placed at an approximate template location."""
    lu = _dedupe_positions(lineup)
    fig = theme.base_pitch()
    fig.add_trace(go.Scatter(
        x=lu["px"], y=lu["py"], mode="markers+text",
        marker=dict(size=30, color=theme.SURFACE_2, line=dict(width=2, color=theme.ACCENT)),
        text=lu["jersey_number"].astype("Int64").astype(str),
        textfont=dict(color=theme.TEXT, size=12, family="Arial Black"),
        textposition="middle center",
        hovertext=[f"{n}<br>{p}" for n, p in zip(lu["player_name"], lu["position"])],
        hoverinfo="text",
    ))
    # Name labels below each marker
    fig.add_trace(go.Scatter(
        x=lu["px"], y=lu["py"] - 7, mode="text",
        text=lu["player_name"].str.split().str[-1],
        textfont=dict(color=theme.TEXT_MUTED, size=9),
        hoverinfo="skip",
    ))
    fig.update_layout(height=460)
    return fig


def passing_network_pitch(passes: pd.DataFrame, min_pass_count: int = 2) -> go.Figure:
    """Nodes placed at each player's average completed-pass origin
    location (real data), edges = completed pass combinations, thickness
    = volume."""
    completed = passes[passes["outcome"].isna()]
    if completed.empty:
        return theme.base_pitch()

    node_pos = completed.groupby("player_name", observed=True)[["location_x", "location_y"]].mean()
    involvement = completed.groupby("player_name", observed=True).size()

    edges = (
        completed.groupby(["player_name", "recipient_name"], observed=True)
        .size().reset_index(name="count")
    )
    edges = edges[edges["count"] >= min_pass_count]

    fig = theme.base_pitch()
    max_count = edges["count"].max() if len(edges) else 1
    for _, e in edges.iterrows():
        if e["player_name"] not in node_pos.index or e["recipient_name"] not in node_pos.index:
            continue
        x0, y0 = node_pos.loc[e["player_name"]]
        x1, y1 = node_pos.loc[e["recipient_name"]]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines",
            line=dict(width=1 + 5 * e["count"] / max_count, color="rgba(34,211,168,0.35)"),
            hoverinfo="skip",
        ))

    max_inv = involvement.max() if len(involvement) else 1
    fig.add_trace(go.Scatter(
        x=node_pos["location_x"], y=node_pos["location_y"], mode="markers+text",
        marker=dict(
            size=14 + 20 * involvement.reindex(node_pos.index).fillna(0) / max_inv,
            color=theme.SURFACE_2, line=dict(width=2, color=theme.ACCENT),
        ),
        text=[n.split()[-1] for n in node_pos.index],
        textfont=dict(color=theme.TEXT, size=10),
        textposition="top center",
        hovertext=[f"{n}<br>{involvement.get(n, 0)} completed passes" for n in node_pos.index],
        hoverinfo="text",
    ))
    fig.update_layout(height=460)
    return fig


# --------------------------------------------------------------------- #
# Timeline
# --------------------------------------------------------------------- #

EVENT_ICON = {
    "Goal": "⚽", "Own Goal For": "⚽ (OG)", "Own Goal Against": "⚽ (OG)",
    "Yellow Card": "🟨", "Red Card": "🟥", "Substitution": "🔁",
}


def match_timeline(goal_events: pd.DataFrame, sub_events: pd.DataFrame):
    """Goals and substitutions only. Card events are intentionally omitted:
    the current dataset records that a Foul Committed / Bad Behaviour event
    happened, but not the card color, so we cannot show yellow/red reliably
    without fabricating it."""
    rows = []
    for _, r in goal_events.iterrows():
        rows.append((r["minute"], "⚽", f"{r['player_name']}" + (" (Pen)" if r.get("is_penalty") else "")))
    for _, r in sub_events.iterrows():
        rows.append((r["minute"], "🔁", r["player_name"]))
    rows.sort(key=lambda x: x[0])
    if not rows:
        st.caption("No goal or substitution events recorded for this match.")
        return
    for minute, icon, text in rows:
        st.markdown(
            f'<div class="ss-event-row"><b>{format_minute(minute)}</b> &nbsp; {icon} &nbsp; {text}</div>',
            unsafe_allow_html=True,
        )
