import streamlit as st

from auth_ui import render_auth_screen
from chat_ui import handle_new_question, render_chat_history
from session_manager import (
    get_current_session,
    init_sessions,
    render_sidebar,
)
from theme import inject_custom_css


st.set_page_config(
    page_title="Agentic RAG",
    page_icon="📜",
    layout="wide",
)

inject_custom_css()


# ---------- Auth state ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    render_auth_screen()
    st.stop()


# ---------- Main app (runs only after login) ----------
init_sessions()

current_id, current = get_current_session()

render_sidebar(current_id, current)


# ---------- Header: title + signed-in user + log out ----------
head_left, head_right = st.columns([5, 1], vertical_alignment="center")

with head_left:
    st.markdown(
        f"""
        <div class="masthead">
            <p class="masthead-title">The Agentic Reading Room</p>
            <p class="masthead-sub">
                Answers from your documents, with sources.
                Signed in as <b>{st.session_state.username}</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with head_right:
    if st.button("Log out", key="logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()


# ---------- Chat ----------
render_chat_history(current)

handle_new_question(current, current_id)