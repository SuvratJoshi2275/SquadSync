import streamlit as st

from analytics import tactical, match
from ui import components


def render_coach_tactical(selected_team: str):
    st.markdown("# Tactical Analysis")
    st.caption(
        "First-stage tactical layer — every figure below is a direct measurement from the event "
        "data. No qualitative claims (e.g. \"dominated the flank\") are generated without a "
        "specific metric behind them."
    )

    tab_shape, tab_match = st.tabs(["Team Shape (All Matches)", "Match Tactical Breakdown"])

    with tab_shape:
        _render_formation_profile(selected_team)

    with tab_match:
        _render_match_breakdown(selected_team)


def _render_formation_profile(selected_team: str):
    usage = tactical.formation_usage(selected_team)
    st.markdown("### Formation Profile")
    cols = st.columns(min(4, len(usage))) if len(usage) else []
    for i, (_, row) in enumerate(usage.iterrows()):
        with cols[i % len(cols)]:
            with st.container(border=True):
                st.markdown(f"**{_fmt_formation(row['formation'])}**")
                st.caption(f"{row['matches_used']} matches · {row['pct_of_matches']}%")

    st.markdown("### Shot Zones (All Matches)")
    shot_zones = tactical.shot_zone_distribution(selected_team)
    z1, z2 = st.columns(2)
    for i, (_, r) in enumerate(shot_zones.iterrows()):
        col = z1 if i == 0 else z2
        col.metric(r["zone"], f"{r['pct_of_shots']}%")


def _render_match_breakdown(selected_team: str):
    matches = match.match_list(selected_team)
    opponent = matches.apply(
        lambda r: r["away_team"] if r["home_team"] == "Barcelona" else r["home_team"], axis=1
    ).astype(str)
    matches["label"] = matches["match_date"].astype(str) + " — vs " + opponent
    label_to_id = dict(zip(matches["label"], matches["match_id"]))
    choice = st.selectbox("Select a match", matches["label"])
    match_id = int(label_to_id[choice])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Passing Zones")
        pz = tactical.pass_zone_distribution(selected_team, match_id)
        for _, r in pz.iterrows():
            st.markdown(f"**{r['third']}**")
            st.progress(min(int(r["pct_of_passes"]), 100), text=f"{r['pct_of_passes']}% of passes")

        st.markdown("### Progression")
        cp = tactical.carry_progression(match_id, selected_team)
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("Carries", cp["carries"])
        pc2.metric("Progressive", cp["progressive_carries"])
        pc3.metric("Avg. Progress", cp.get("avg_progress_x", "—"))

    with col2:
        st.markdown("### Pressing Zones")
        prz = tactical.pressure_zone_distribution(match_id, selected_team)
        if prz.empty:
            st.caption("No pressure events recorded for this match.")
        else:
            for _, r in prz.iterrows():
                st.markdown(f"**{r['third']}**")
                st.progress(min(int(r["pct_of_pressures"]), 100), text=f"{r['pct_of_pressures']}% of pressures")

        st.markdown("### Formation Changes")
        changes = tactical.formation_changes(match_id, selected_team)
        if len(changes) <= 1:
            st.caption("No in-match formation change recorded — Barcelona kept the starting shape.")
        else:
            steps = "  →  ".join(
                f"**{_fmt_formation(r['formation'])}**" + (f" ({int(r['minute'])}')" if r["minute"] else "")
                for _, r in changes.iterrows()
            )
            st.markdown(steps)

    st.markdown("### Player Involvement")
    involvement = tactical.player_involvement(match_id, selected_team)
    display = involvement.head(11).rename(columns={
        "player_name": "Player", "passes": "Passes", "carries": "Carries",
        "pressures": "Pressures", "shots": "Shots", "involvement_score": "Involvement",
    })
    st.dataframe(display, width="stretch", hide_index=True)


def _fmt_formation(code) -> str:
    code = str(code)
    return "-".join(code) if code.isdigit() else code
