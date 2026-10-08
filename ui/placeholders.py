"""Compact component for a single roadmap item — used by the Roadmap page,
not the primary navigation, so future modules don't dominate the product."""

import streamlit as st


def roadmap_card(title: str, description: str, planned_capabilities: list[str], status: str = "Later phase"):
    with st.container(border=True):
        st.markdown(f"**{title}**  \n<span class='ss-subtle'>{status}</span>", unsafe_allow_html=True)
        st.caption(description)
        with st.expander("Planned capabilities"):
            for cap in planned_capabilities:
                st.markdown(f"- {cap}")
