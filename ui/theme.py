"""SquadSync design system.

Centralizes the visual identity so every page looks like one product
instead of a stack of default Streamlit pages: color tokens, compact CSS
(smaller headings, tighter spacing, card styling), and a reusable football
pitch figure builder used by the shot map, lineup, and passing-network
visuals.

Nothing here touches data/analytics — purely presentational.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

# ---- Brand tokens --------------------------------------------------------
BG = "#0B0E14"
SURFACE = "#141A24"
SURFACE_2 = "#1B2330"
BORDER = "#2A3444"
TEXT = "#E7ECF3"
TEXT_MUTED = "#8B96A8"
ACCENT = "#22D3A8"          # SquadSync signature accent (teal-green)
ACCENT_SOFT = "#1B4B42"
WIN = "#22D3A8"
DRAW = "#8B96A8"
LOSS = "#EF5C6E"
PITCH_GREEN = "#12241D"
PITCH_LINE = "#3A5A4C"

# StatsBomb pitch dimensions
PITCH_LENGTH = 120
PITCH_WIDTH = 80


def inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: {BG}; }}
        [data-testid="stSidebar"] {{ background-color: {SURFACE}; border-right: 1px solid {BORDER}; }}
        h1, h2, h3 {{ font-weight: 700 !important; letter-spacing: -0.01em; }}
        h1 {{ font-size: 1.5rem !important; margin-bottom: 0.2rem !important; }}
        h2 {{ font-size: 1.15rem !important; margin-top: 0.6rem !important; margin-bottom: 0.4rem !important; }}
        h3 {{ font-size: 0.95rem !important; text-transform: uppercase; letter-spacing: 0.06em; color: {TEXT_MUTED} !important; margin-bottom: 0.3rem !important; }}
        [data-testid="stMetricValue"] {{ font-size: 1.4rem; }}
        [data-testid="stMetricLabel"] {{ color: {TEXT_MUTED}; }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {SURFACE}; border-radius: 10px; border: 1px solid {BORDER};
        }}
        .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px; }}
        .ss-pill {{
            display: inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: 0.72rem; font-weight: 600; letter-spacing: 0.03em;
        }}
        .ss-pill-win {{ background: rgba(34,211,168,0.15); color: {WIN}; }}
        .ss-pill-draw {{ background: rgba(139,150,168,0.15); color: {DRAW}; }}
        .ss-pill-loss {{ background: rgba(239,92,110,0.15); color: {LOSS}; }}
        .ss-form-dot {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 26px; height: 26px; border-radius: 6px; margin-right: 4px;
            font-size: 0.72rem; font-weight: 700; color: #06110D;
        }}
        .ss-score {{ font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; }}
        .ss-label {{ color: {TEXT_MUTED}; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .ss-subtle {{ color: {TEXT_MUTED}; font-size: 0.85rem; }}
        .ss-event-row {{ font-size: 0.88rem; padding: 2px 0; }}
        .ss-mode-caption {{ color: {TEXT_MUTED}; font-size: 0.8rem; margin-top: -6px;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def result_pill(result: str) -> str:
    cls = {"Win": "ss-pill-win", "Draw": "ss-pill-draw", "Loss": "ss-pill-loss"}.get(result, "ss-pill-draw")
    return f'<span class="ss-pill {cls}">{result or "—"}</span>'


def form_dot(result: str) -> str:
    color = {"Win": WIN, "Draw": DRAW, "Loss": LOSS}.get(result, DRAW)
    letter = {"Win": "W", "Draw": "D", "Loss": "L"}.get(result, "?")
    return f'<span class="ss-form-dot" style="background:{color}">{letter}</span>'


def base_pitch(vertical: bool = False) -> go.Figure:
    """Empty football pitch in StatsBomb 120x80 coordinates, styled to look
    like an actual pitch rather than a generic scatter chart."""
    fig = go.Figure()
    x_max, y_max = (PITCH_WIDTH, PITCH_LENGTH) if vertical else (PITCH_LENGTH, PITCH_WIDTH)

    def line(x0, y0, x1, y1):
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=PITCH_LINE, width=1.5))

    def rect(x0, y0, x1, y1):
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=PITCH_LINE, width=1.5))

    def circle(cx, cy, r):
        fig.add_shape(type="circle", x0=cx - r, y0=cy - r, x1=cx + r, y1=cy + r, line=dict(color=PITCH_LINE, width=1.5))

    def pt(px, py, x, y):
        return (px, py) if not vertical else (y, x)

    coords = {
        "outline": (0, 0, PITCH_LENGTH, PITCH_WIDTH),
        "halfway": (PITCH_LENGTH / 2, 0, PITCH_LENGTH / 2, PITCH_WIDTH),
        "box_l": (0, 18, 18, 62),
        "box_r": (102, 18, 120, 62),
        "six_l": (0, 30, 6, 50),
        "six_r": (114, 30, 120, 50),
    }
    if not vertical:
        rect(*coords["outline"])
        line(*coords["halfway"])
        rect(*coords["box_l"])
        rect(*coords["box_r"])
        rect(*coords["six_l"])
        rect(*coords["six_r"])
        circle(60, 40, 9.15)
    else:
        rect(0, 0, PITCH_WIDTH, PITCH_LENGTH)
        line(0, PITCH_LENGTH / 2, PITCH_WIDTH, PITCH_LENGTH / 2)
        rect(18, 0, 62, 18)
        rect(18, 102, 62, 120)
        rect(30, 0, 50, 6)
        rect(30, 114, 50, 120)
        circle(40, 60, 9.15)

    fig.update_xaxes(range=[-2, x_max + 2], visible=False, fixedrange=True)
    fig.update_yaxes(range=[-2, y_max + 2], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)
    fig.update_layout(
        plot_bgcolor=PITCH_GREEN, paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )
    return fig
