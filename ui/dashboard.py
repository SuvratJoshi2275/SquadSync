import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import team, tactical, match as match_analytics
from data import loader
from ui import components, theme

# The dataset includes a handful of much older matches (1974-1984) mixed
# into an otherwise 2004-2021 archive. They're real matches, not bad data,
# but including them by default stretches any date axis to a 47-year span
# and squashes the dense, recent period into a sliver -- which is the
# "chart looks like it's from 1975" symptom. We default views to the dense
# modern era and let the person opt into the full archive explicitly.
MODERN_ERA_START = "2000-01-01"


def _fan_recent_matches(selected_team: str, n: int = 6) -> pd.DataFrame:
    ml = match_analytics.match_list(selected_team)
    m = loader.load_matches(selected_team)[["match_id", "home_score", "away_score"]]
    full = ml.merge(m, on="match_id", how="left")
    return full.sort_values("match_date", ascending=False).head(n)


def render_fan_home(selected_team: str, go_to_match=None):
    ts = team.team_record(selected_team)
    matches = _fan_recent_matches(selected_team, n=6)

    st.markdown("# BARCELONA")
    st.markdown(
        '<div class="ss-mode-caption">Dataset: 2004–2021 · La Liga, Champions League, Copa del Rey '
        '(plus 4 archival matches from 1974–1984)</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    recent_results = matches["result"].tolist()[:5]
    st.markdown('<div class="ss-label">Recent Form</div>', unsafe_allow_html=True)
    components.form_strip(list(reversed(recent_results)))

    st.write("")
    last = matches.iloc[0]
    st.markdown("### Last Match")
    components.match_score_card(last.to_dict(), key="fan_home_last_match", on_click=go_to_match)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Matches (dataset)", ts["matches_played"])
    c2.metric("Record", f"{ts['wins']}-{ts['draws']}-{ts['losses']}")
    c3.metric("Goals For", ts["goals_for"])
    c4.metric("Goals Against", ts["goals_against"])

    st.markdown("### Recent Matches")
    for _, row in matches.iloc[1:6].iterrows():
        components.match_score_card(row.to_dict(), key=f"fan_home_{row['match_id']}", on_click=go_to_match)


def render_coach_overview(selected_team: str):
    st.markdown("# BARCELONA")
    st.markdown('<div class="ss-mode-caption">TEAM OVERVIEW</div>', unsafe_allow_html=True)
    st.write("")

    record = team.team_record(selected_team)
    shooting = team.shooting_summary(selected_team)
    passing = team.passing_summary(selected_team)
    averages = team.per_match_averages(selected_team)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Matches", record["matches_played"])
    c2.metric("Record (W-D-L)", f"{record['wins']}-{record['draws']}-{record['losses']}")
    c3.metric("Goal Diff.", record["goal_difference"])
    c4.metric("Pass Completion", f"{passing['pass_completion_pct']}%")
    c5.metric("xG (dataset total)", shooting["total_xg"])

    st.markdown("### Per-Match Profile")
    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Goals / Match", averages["avg_goals_per_match"])
    a2.metric("Shots / Match", averages["avg_shots_per_match"])
    a3.metric("Passes / Match", averages["avg_passes_per_match"])
    a4.metric("Carries / Match", averages["avg_carries_per_match"])
    a5.metric("Pressures / Match", averages["avg_pressures_per_match"])

    st.markdown("### Formation Profile")
    usage = tactical.formation_usage(selected_team)
    cols = st.columns(min(4, len(usage)))
    for i, (_, row) in enumerate(usage.head(4).iterrows()):
        with cols[i % len(cols)]:
            with st.container(border=True):
                st.markdown(f"**{_fmt_formation(row['formation'])}**")
                st.caption(f"Used in {row['matches_used']} matches · {row['pct_of_matches']}%")

    st.markdown("### Form Trend")
    include_full_history = st.checkbox(
        "Include full historical archive (adds 4 matches from 1974–1984)", value=False
    )
    trend = team.performance_trend(selected_team, window=10)
    trend["date"] = pd.to_datetime(trend["date"])
    if not include_full_history:
        trend = trend[trend["date"] >= MODERN_ERA_START]
    fig = px.line(
        trend, x="date", y="rolling_ppg",
        labels={"rolling_ppg": "Points per game (rolling 10-match avg)", "date": ""},
        hover_data=["opponent", "result"],
    )
    fig.update_traces(line_color=theme.ACCENT)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color=theme.TEXT_MUTED, margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("### Record by Competition")
    comp = team.by_competition(selected_team)
    comp_display = comp.rename(columns={
        "competition": "Competition", "matches": "Played", "wins": "W", "draws": "D",
        "losses": "L", "goals_for": "GF", "goals_against": "GA",
    })
    st.dataframe(comp_display, width="stretch", hide_index=True)


def _fmt_formation(code: str) -> str:
    code = str(code)
    return "-".join(code) if code.isdigit() else code
