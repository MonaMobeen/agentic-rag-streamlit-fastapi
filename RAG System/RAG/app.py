import html

import streamlit as st

from auth_ui import render_auth_screen
from chat_ui import handle_new_question, render_chat_history
from session_manager import (
    get_current_session,
    init_sessions,
    render_sidebar,
)
from theme import LOGO_SVG, get_theme, inject_custom_css, toggle_theme


st.set_page_config(
    page_title="Agentic RAG",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# STATE DEFAULTS (before CSS, so the theme is known)
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "dark"

inject_custom_css()


# =========================================================
# LOGIN SCREEN
# =========================================================

if not st.session_state.logged_in:
    render_auth_screen()
    st.stop()


# =========================================================
# MAIN APP (runs only after login)
# =========================================================

init_sessions()

current_id, current = get_current_session()

render_sidebar(current_id, current)


def _logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.pop("pending_question", None)


# =========================================================
# TOP BAR
# =========================================================

ready = current["service"] is not None
username = st.session_state.username or "user"

status_html = (
    '<span class="status-pill ok"><i></i>Documents ready</span>'
    if ready
    else '<span class="status-pill"><i></i>No documents yet</span>'
)
user_html = (
    f'<span class="user-chip"><b>{html.escape(username[:1].upper())}</b>'
    f"{html.escape(username)}</span>"
)

left, theme_col, logout_col = st.columns([6, 1.3, 1.1], vertical_alignment="center")

with left:
    st.markdown(
        '<div class="topbar">'
        f'<div class="brand-mark">{LOGO_SVG}</div>'
        '<div class="brand-name">Agentic Reading Room</div>'
        f"{status_html}{user_html}"
        "</div>",
        unsafe_allow_html=True,
    )

with theme_col:
    st.button(
        "Light mode" if get_theme() == "dark" else "Dark mode",
        key="theme_btn",
        on_click=toggle_theme,
        use_container_width=True,
    )

with logout_col:
    if st.button("Log out", key="logout", use_container_width=True):
        _logout()
        st.rerun()


# =========================================================
# CHAT
# =========================================================

render_chat_history(current, current_id)

handle_new_question(current, current_id)