import pandas as pd
import streamlit as st

from analytics import match, tactical
from data import loader
from ui import components, theme

# --------------------------------------------------------------------- #
# Fan Mode — Matches browser
# --------------------------------------------------------------------- #

def render_matches_browser(selected_team: str, go_to_match=None):
    st.markdown("# Matches")

    ml = match.match_list(selected_team)
    m = loader.load_matches(selected_team)[["match_id", "home_score", "away_score"]]
    ml = ml.merge(m, on="match_id", how="left")
    ml["season"] = ml["season"].astype(str)

    f1, f2, f3 = st.columns(3)
    season = f1.selectbox("Season", ["All"] + sorted(ml["season"].unique(), reverse=True))
    competition = f2.selectbox("Competition", ["All"] + sorted(ml["competition"].unique()))
    result = f3.selectbox("Result", ["All", "Win", "Draw", "Loss"])

    filtered = ml.copy()
    if season != "All":
        filtered = filtered[filtered["season"] == season]
    if competition != "All":
        filtered = filtered[filtered["competition"] == competition]
    if result != "All":
        filtered = filtered[filtered["result"] == result]

    st.caption(f"{len(filtered)} matches")
    for _, row in filtered.head(40).iterrows():
        components.match_score_card(row.to_dict(), key=f"browse_{row['match_id']}", on_click=go_to_match)
    if len(filtered) > 40:
        st.caption(f"Showing the first 40 of {len(filtered)} — narrow the filters above to see more specific matches.")


# --------------------------------------------------------------------- #
# Match Centre (flagship page)
# --------------------------------------------------------------------- #

def render_match_centre(selected_team: str, match_id: int):
    overview = match.match_overview(match_id, selected_team)
    if not overview:
        st.error("Match not found.")
        return

    barca_home = True  # matches.csv doesn't always have Barcelona at home; determine below
    matches_row = loader.load_matches(selected_team)
    row = matches_row[matches_row["match_id"] == match_id].iloc[0]
    barca_home = row["home_team"] == "Barcelona"
    home_team, away_team = row["home_team"], row["away_team"]
    home_score, away_score = int(row["home_score"]), int(row["away_score"])

    st.markdown(
        f'<div class="ss-label">{overview["competition"]} · {overview["date"]}</div>'
        f'<div class="ss-subtle">{overview["stadium"] or ""}</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([3, 1, 3])
    c1.markdown(f'<div style="font-size:1.3rem;font-weight:700;text-align:right">{home_team}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="ss-score" style="text-align:center">{home_score} — {away_score}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div style="font-size:1.3rem;font-weight:700">{away_team}</div>', unsafe_allow_html=True)

    goal_info = match.match_goals(match_id, selected_team)
    goals = goal_info["goals"]
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        st.markdown(f"**{home_team}**")
        _render_goal_list(goals[goals["team_name"] == home_team])
    with gcol2:
        st.markdown(f"**{away_team}**")
        _render_goal_list(goals[goals["team_name"] == away_team])
    if not goal_info["opponent_goals_fully_attributed"]:
        st.caption(
            f"⚠️ {goal_info['opponent_name']}'s goal list may be incomplete: this dataset only "
            f"captures events from Barcelona's side, so opponent goals from open play aren't "
            f"individually tracked — only own goals are. Scoreline above is authoritative "
            f"({goal_info['attributed_opponent_goals']}/{goal_info['opponent_score']} of "
            f"{goal_info['opponent_name']}'s goals attributed to a scorer)."
        )

    st.markdown(theme.result_pill(overview["result"]) + f'&nbsp;&nbsp;<span class="ss-subtle">{overview["venue"]} for Barcelona</span>', unsafe_allow_html=True)

    tabs = st.tabs(["Overview", "Lineups", "Stats", "Tactics", "Events"])

    with tabs[0]:
        _render_overview_tab(match_id, selected_team, home_team, away_team)
    with tabs[1]:
        _render_lineups_tab(match_id, selected_team)
    with tabs[2]:
        _render_stats_tab(match_id, selected_team, home_team, away_team)
    with tabs[3]:
        _render_tactics_tab(match_id, selected_team)
    with tabs[4]:
        _render_events_tab(match_id, selected_team)


def _render_goal_list(goals: pd.DataFrame):
    if goals.empty:
        st.caption("No goals")
        return
    for _, g in goals.sort_values("minute").iterrows():
        pen = " (Pen)" if g["is_penalty"] else ""
        last_name = str(g["player_name"]).split()[-1]
        st.markdown(
            f'<div class="ss-event-row">⚽ {last_name} {components.format_minute(g["minute"])}{pen}</div>',
            unsafe_allow_html=True,
        )


def _render_overview_tab(match_id, selected_team, home_team, away_team):
    stats = match.match_stats(match_id, selected_team)
    barca_home = home_team == "Barcelona"

    # match_stats() is Barcelona-only (shots/passes tables aren't split
    # cleanly two-sided in the source data for the opponent side beyond
    # what's present in the event feed). We show Barcelona's numbers as
    # the primary stat block, consistent with the dataset's team-relative
    # scope, and label it explicitly rather than implying a full two-sided
    # comparison we can't fully support.
    st.markdown("**Barcelona — Match Stats**")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Shots", stats["shots"])
    m2.metric("On Target", stats["shots_on_target"])
    m3.metric("xG", stats["total_xg"])
    m4.metric("Pass Accuracy", f"{stats['pass_completion_pct']}%" if stats["pass_completion_pct"] else "—")

    m5, m6 = st.columns(2)
    m5.metric("Passes", stats["passes_attempted"])
    m6.metric("Pressures", stats["pressures"])

    st.markdown("### Shot Map")
    shot_map_df = match.match_shot_map(match_id, selected_team)
    barca_shots = shot_map_df[shot_map_df["team_name"] == "Barcelona"]
    if barca_shots.empty:
        st.caption("No shot data for Barcelona in this match.")
    else:
        st.plotly_chart(components.shot_map(barca_shots), width="stretch")


def _render_lineups_tab(match_id, selected_team):
    lineup = match.match_lineup(match_id, selected_team)
    formation = match.match_formation(match_id, selected_team)

    for tname in ["Barcelona"] + [t for t in lineup["team_name"].unique() if t != "Barcelona"]:
        team_lineup = lineup[lineup["team_name"] == tname]
        starters = team_lineup[team_lineup["start_reason"] == "Starting XI"]
        subs_in = team_lineup[team_lineup["start_reason"] != "Starting XI"]
        team_formation = formation[formation["team_name"] == tname]
        shape = team_formation.iloc[0]["formation"] if len(team_formation) else None

        st.markdown(f"### {tname}" + (f" — {_fmt_formation(shape)}" if shape else ""))
        if tname == "Barcelona" and len(starters):
            st.plotly_chart(components.lineup_pitch(starters), width="stretch")
        with st.expander(f"{tname} — full squad list"):
            display = team_lineup[["player_name", "jersey_number", "position"]].rename(
                columns={"player_name": "Player", "jersey_number": "#", "position": "Position"}
            )
            st.dataframe(display, width="stretch", hide_index=True)
        if len(subs_in):
            st.caption(f"{len(subs_in)} substitute appearance(s) recorded.")


def _render_stats_tab(match_id, selected_team, home_team, away_team):
    stats = match.match_stats(match_id, selected_team)
    st.caption(
        "Detailed statistics are tracked from Barcelona's event feed; the dataset does not "
        "provide a fully independent opponent-side event stream, so only Barcelona's numbers "
        "are shown with match-level precision."
    )
    rows = [
        ("Shots", stats["shots"]),
        ("Shots on Target", stats["shots_on_target"]),
        ("xG", stats["total_xg"]),
        ("Passes", stats["passes_attempted"]),
        ("Pass Accuracy", f"{stats['pass_completion_pct']}%" if stats["pass_completion_pct"] else "—"),
        ("Carries", stats["carries"]),
        ("Pressures", stats["pressures"]),
    ]
    for label, val in rows:
        c1, c2 = st.columns([2, 1])
        c1.markdown(f'<span class="ss-subtle">{label}</span>', unsafe_allow_html=True)
        c2.markdown(f"**{val}**")


def _render_tactics_tab(match_id, selected_team):
    st.markdown("### Passing Network — Barcelona")
    passes = loader.load_passes(selected_team, match_id)
    barca_passes = passes[passes["team_name"] == "Barcelona"]
    if barca_passes.empty:
        st.caption("No passing data for Barcelona in this match.")
    else:
        st.plotly_chart(components.passing_network_pitch(barca_passes), width="stretch")
        st.caption("Node position = average completed-pass location. Edge thickness = pass volume between the pair.")

    changes = tactical.formation_changes(match_id, selected_team)
    if len(changes) > 1:
        st.markdown("### Formation Changes")
        steps = " → ".join(f"{_fmt_formation(r['formation'])} ({int(r['minute'])}')" for _, r in changes.iterrows())
        st.markdown(steps)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Passing by Zone")
        pz = tactical.pass_zone_distribution(selected_team, match_id)
        for _, r in pz.iterrows():
            st.markdown(f"**{r['third']}** — {r['pct_of_passes']}%")
    with col2:
        st.markdown("### Pressure by Zone")
        prz = tactical.pressure_zone_distribution(match_id, selected_team)
        if prz.empty:
            st.caption("No pressure events recorded.")
        else:
            for _, r in prz.iterrows():
                st.markdown(f"**{r['third']}** — {r['pct_of_pressures']}%")


def _render_events_tab(match_id, selected_team):
    goals = match.match_goals(match_id, selected_team)["goals"]
    subs = match.match_substitutions(match_id, selected_team)
    st.markdown("### Timeline")
    components.match_timeline(goals, subs)
    st.caption(
        "Card events aren't shown: the dataset records that a foul/behaviour event happened "
        "but not the card color, so we don't display an unverified yellow/red."
    )
    with st.expander("Advanced data — full event log"):
        raw = match.match_event_timeline(match_id, selected_team)
        st.dataframe(
            raw.rename(columns={"event_type": "Event", "team_name": "Team", "player_name": "Player", "minute": "Min", "second": "Sec"}),
            width="stretch", hide_index=True,
        )


def _fmt_formation(code) -> str:
    code = str(code)
    return "-".join(code) if code.isdigit() else code
