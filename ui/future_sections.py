import streamlit as st

from ui.placeholders import roadmap_card

SECTIONS = {
    "Opponent Analysis": dict(
        description=(
            "Will profile an upcoming or selected opponent using the same event-level "
            "pipeline used for Barcelona, once opponent-side datasets are added."
        ),
        capabilities=[
            "Opponent formation & tactical tendencies",
            "Opponent key-player identification",
            "Head-to-head historical breakdown",
            "Strength/weakness summary vs. Barcelona's own profile",
        ],
    ),
    "Squad Intelligence": dict(
        description="Will assess player-role suitability and squad depth across positions.",
        capabilities=[
            "Player-role fit scoring (data-driven, not just position label)",
            "Squad depth chart by position",
            "Fitness/rotation load indicators (needs additional data source)",
            "Positional gap analysis",
        ],
    ),
    "Predictions": dict(
        description="Will provide match and player outcome predictions once models are trained.",
        capabilities=[
            "Match result / xG-based outcome prediction",
            "Player performance projection",
            "Model confidence & explanation (not just a bare number)",
        ],
        status="Requires ML/DL model training — not built for this demo",
    ),
    "Recommendations": dict(
        description="Will turn analytics into actionable tactical/recruitment suggestions.",
        capabilities=[
            "Tactical alternative suggestions grounded in match data",
            "Recruitment target suggestions (needs external scouting data)",
            "Lineup/formation recommendations for a given opponent",
        ],
    ),
    "AI Assistant": dict(
        description=(
            "The football-specific conversational orchestration layer. It will query and "
            "explain the analytics modules above rather than replace them, and eventually "
            "support multi-step natural-language requests and voice input."
        ),
        capabilities=[
            "Natural-language match/player search and comparison",
            "Chart and statistic explanation in plain language",
            "In-app navigation and filter control via chat",
            "Multi-step analytical requests (e.g. 'compare xG across the last 5 matches')",
            "Future RAG layer for general football knowledge",
            "Voice interaction",
        ],
        status="Backend orchestration layer not yet built",
    ),
}


def render_roadmap():
    st.markdown("# Roadmap")
    st.caption("Later-phase modules. Shown here for visibility — not part of the primary product yet.")
    for name, cfg in SECTIONS.items():
        roadmap_card(
            title=name,
            description=cfg["description"],
            planned_capabilities=cfg["capabilities"],
            status=cfg.get("status", "Later phase"),
        )
