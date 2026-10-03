import streamlit as st

from auth_ui import render_auth_screen
from chat_ui import handle_new_question, render_chat_history
from session_manager import get_current_session, init_sessions, render_sidebar
from theme import inject_custom_css

st.set_page_config(page_title="Agentic RAG", page_icon="🧠", layout="wide")
inject_custom_css()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    render_auth_screen()

init_sessions()
current_id, current = get_current_session()
render_sidebar(current_id, current)

st.markdown(
    '<div class="app-header"><h1>🧠 Agentic RAG</h1></div>'
    '<p class="app-subtitle">Document Intelligence powered by AI Agents</p>',
    unsafe_allow_html=True,
)

with st.container():
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(
            f'<div class="welcome-bar">👋 Welcome back, <b>{st.session_state.username}</b></div>',
            unsafe_allow_html=True,
        )
    with col2:
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

render_chat_history(current)
handle_new_question(current, current_id)