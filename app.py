import streamlit as st

from data import loader
from ui import theme, dashboard, match_analysis, player_analysis, tactical_analysis, future_sections

st.set_page_config(page_title="SquadSync", page_icon="⚽", layout="wide")
theme.inject_css()

FAN_NAV = ["Home", "Matches", "Players", "Match Centre"]
COACH_NAV = ["Team Overview", "Tactical Analysis", "Player Intelligence", "Match Analysis"]


def _go_to_match(match_id: int):
    st.session_state["selected_match_id"] = match_id
    st.session_state["nav_override"] = "Match Centre" if st.session_state["mode"] == "FAN MODE" else "Match Analysis"
    st.rerun()


def main():
    if "mode" not in st.session_state:
        st.session_state["mode"] = "FAN MODE"

    teams = loader.available_teams()
    if not teams:
        st.error(
            "No processed data found. Run `python data/build_cache.py --team barcelona` "
            "before starting the app."
        )
        return
    selected_team = teams[0] if len(teams) == 1 else st.sidebar.selectbox("Team dataset", teams, format_func=str.title)

    st.sidebar.markdown("### ⚽ SquadSync")
    mode = st.sidebar.radio("Mode", ["FAN MODE", "COACH MODE"], horizontal=True, label_visibility="collapsed")
    st.session_state["mode"] = mode

    nav_options = FAN_NAV if mode == "FAN MODE" else COACH_NAV
    default_idx = 0
    if st.session_state.get("nav_override") in nav_options:
        default_idx = nav_options.index(st.session_state.pop("nav_override"))
    section = st.sidebar.radio("Navigate", nav_options, index=default_idx, label_visibility="collapsed")

    st.sidebar.markdown("---")
    st.sidebar.page_link if False else None  # no-op guard (keeps diff minimal if Streamlit version varies)
    if st.sidebar.button("Roadmap — future modules", width="stretch"):
        st.session_state["show_roadmap"] = True
    st.sidebar.caption("Barcelona · 531 matches · La Liga, Champions League, Copa del Rey")

    if st.session_state.get("show_roadmap"):
        if st.sidebar.button("← Back to app", width="stretch"):
            st.session_state["show_roadmap"] = False
            st.rerun()
        future_sections.render_roadmap()
        return

    if mode == "FAN MODE":
        if section == "Home":
            dashboard.render_fan_home(selected_team, go_to_match=_go_to_match)
        elif section == "Matches":
            match_analysis.render_matches_browser(selected_team, go_to_match=_go_to_match)
        elif section == "Players":
            player_analysis.render_fan_player(selected_team)
        elif section == "Match Centre":
            _render_match_centre_with_picker(selected_team)
    else:
        if section == "Team Overview":
            dashboard.render_coach_overview(selected_team)
        elif section == "Tactical Analysis":
            tactical_analysis.render_coach_tactical(selected_team)
        elif section == "Player Intelligence":
            player_analysis.render_coach_player_intelligence(selected_team)
        elif section == "Match Analysis":
            _render_match_centre_with_picker(selected_team)


def _render_match_centre_with_picker(selected_team: str):
    from analytics import match as match_analytics
    ml = match_analytics.match_list(selected_team)
    ml["opponent"] = ml.apply(
        lambda r: r["away_team"] if r["home_team"] == "Barcelona" else r["home_team"], axis=1
    ).astype(str)
    ml["label"] = ml["match_date"].astype(str) + " — vs " + ml["opponent"] + " (" + ml["score"].astype(str) + ")"

    default_match_id = st.session_state.get("selected_match_id")
    options = ml["match_id"].tolist()
    labels = dict(zip(ml["match_id"], ml["label"]))
    default_idx = options.index(default_match_id) if default_match_id in options else 0

    match_id = st.selectbox(
        "Select a match", options, index=default_idx, format_func=lambda mid: labels[mid],
    )
    st.session_state["selected_match_id"] = match_id
    match_analysis.render_match_centre(selected_team, int(match_id))


if __name__ == "__main__":
    main()
