import pandas as pd
import streamlit as st

from analytics import player
from data import loader
from ui import components

# --------------------------------------------------------------------- #
# Fan Mode — Player profile
# --------------------------------------------------------------------- #

def render_fan_player(selected_team: str):
    st.markdown("# Players")
    players = loader.load_players(selected_team).sort_values("player_name")
    name_to_id = dict(zip(players["player_name"], players["player_id"]))

    display_name = st.selectbox("Search a player", players["player_name"])
    profile = player.player_profile(int(name_to_id[display_name]), selected_team)
    if not profile:
        st.info("No data available for this player.")
        return

    nickname = players.loc[players["player_name"] == display_name, "nickname"].iloc[0]
    shown_name = nickname if pd.notna(nickname) and nickname else display_name

    st.markdown(f"## {shown_name}")
    sub = " · ".join(x for x in [
        profile.get("country"),
        f"#{int(profile['jersey_number'])}" if profile.get("jersey_number") else None,
    ] if x)
    st.markdown(f'<div class="ss-subtle">{sub}</div>', unsafe_allow_html=True)
    st.write("")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Appearances", profile["appearances"])
    c2.metric("Minutes (est.)", int(profile["minutes_played_est"]) if profile["minutes_played_est"] else "—")
    c3.metric("Goals", profile["goals"])
    c4.metric("xG", profile["xg"])

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Shots", profile["shots"])
    d2.metric("Passes", profile["passes_attempted"])
    d3.metric("Pass Accuracy", f"{profile['pass_completion_pct']}%" if profile["pass_completion_pct"] else "—")
    d4.metric("Carries", profile["carries"])

    st.caption(
        "Minutes are estimated from substitution timestamps; players who finished a match are "
        "assumed to have played to the 90th minute (extra-time matches understated)."
    )

    st.markdown("### Shot Locations")
    pid = int(name_to_id[display_name])
    all_shots = _player_shots_across_matches(selected_team, pid)
    if all_shots.empty:
        st.caption("No shot data recorded for this player.")
    else:
        st.plotly_chart(components.shot_map(all_shots), width="stretch")


def _player_shots_across_matches(selected_team: str, player_id: int) -> pd.DataFrame:
    """Player shots pulled from the (small, already-flat) shots.parquet —
    no need to touch the partitioned per-match cache for this."""
    shots = loader.load_shots(selected_team)
    return shots[shots["player_id"] == player_id]


# --------------------------------------------------------------------- #
# Coach Mode — Player Intelligence
# --------------------------------------------------------------------- #

def render_coach_player_intelligence(selected_team: str):
    st.markdown("# Player Intelligence")

    players = loader.load_players(selected_team).sort_values("player_name")
    name_to_id = dict(zip(players["player_name"], players["player_id"]))

    tab_table, tab_profile, tab_compare = st.tabs(["Squad Table", "Player Profile", "Compare"])

    with tab_table:
        table = _squad_table(selected_team)
        st.dataframe(table, width="stretch", hide_index=True)

    with tab_profile:
        name = st.selectbox("Select a player", players["player_name"], key="coach_profile_select")
        profile = player.player_profile(int(name_to_id[name]), selected_team)
        if not profile:
            st.info("No data available.")
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Appearances", profile["appearances"])
            c2.metric("Minutes (est.)", int(profile["minutes_played_est"]) if profile["minutes_played_est"] else "—")
            c3.metric("Goals", profile["goals"])
            c4.metric("xG", profile["xg"])
            c5.metric("Pressures", profile["pressures"])
            c6, c7, c8 = st.columns(3)
            c6.metric("Pass Accuracy", f"{profile['pass_completion_pct']}%" if profile["pass_completion_pct"] else "—")
            c7.metric("Carries", profile["carries"])
            c8.metric("Progressive Carries", profile["progressive_carries"])

    with tab_compare:
        chosen = st.multiselect("Select 2–4 players", players["player_name"], max_selections=4, key="coach_compare")
        if len(chosen) >= 2:
            ids = [int(name_to_id[n]) for n in chosen]
            comparison = player.compare_players(ids, selected_team)
            display_cols = [
                "appearances", "minutes_played_est", "goals", "xg", "shots",
                "passes_attempted", "pass_completion_pct", "carries", "progressive_carries", "pressures",
            ]
            renamed = comparison[display_cols].rename(columns={
                "appearances": "Apps", "minutes_played_est": "Mins (est.)", "goals": "Goals", "xg": "xG",
                "shots": "Shots", "passes_attempted": "Passes", "pass_completion_pct": "Pass %",
                "carries": "Carries", "progressive_carries": "Prog. Carries", "pressures": "Pressures",
            })
            st.dataframe(renamed.T.astype(str), width="stretch")
        else:
            st.info("Pick at least two players.")


def _squad_table(selected_team: str) -> pd.DataFrame:
    appearances = player.player_appearances(selected_team)
    leaders_passes = player.top_players("passes", n=1000, team=selected_team)[["player_id", "passes"]]
    leaders_goals = player.top_players("goals", n=1000, team=selected_team)[["player_id", "goals"]]
    pass_stats = loader.load_player_pass_stats(selected_team)[["player_id", "pass_completion_pct"]]
    carry_stats = loader.load_player_carry_stats(selected_team)[["player_id", "carries", "progressive_carries"]]
    ps = loader.load_player_summary(selected_team)[["player_id", "shots", "pressures"]]

    table = (
        appearances.merge(leaders_passes, on="player_id", how="left")
        .merge(leaders_goals, on="player_id", how="left")
        .merge(pass_stats, on="player_id", how="left")
        .merge(carry_stats, on="player_id", how="left")
        .merge(ps, on="player_id", how="left")
    )
    table = table.fillna(0)
    table = table.rename(columns={
        "player_name": "Player", "appearances": "Apps", "minutes_played_est": "Mins (est.)",
        "passes": "Passes", "pass_completion_pct": "Pass %", "goals": "Goals",
        "shots": "Shots", "carries": "Carries", "progressive_carries": "Prog. Carries", "pressures": "Pressures",
    })
    cols = ["Player", "Apps", "Mins (est.)", "Goals", "Shots", "Passes", "Pass %", "Carries", "Prog. Carries", "Pressures"]
    return table[cols].sort_values("Apps", ascending=False)
