import streamlit as st

from auth import login, signup

_BRAND_HTML = """
<div class="auth-brand">
    <p class="auth-product">The Agentic Reading Room</p>
    <h1 class="auth-title">Ask your documents.<br>Check every answer.</h1>
    <p class="auth-description">
        Upload your files and an agent decides when to search them,
        when it already knows enough, and when to say
        <strong>"I don't know."</strong>
    </p>
    <ul class="auth-points">
        <li><b>Searches only when it needs to.</b><br>No wasted lookups for simple questions.</li>
        <li><b>Shows its sources.</b><br>Every answer links back to the document it came from.</li>
        <li><b>Keeps sessions separate.</b><br>Each conversation has its own documents.</li>
    </ul>
</div>
"""

_CARD_HEADER_HTML = """
<div class="auth-card-title">Sign in</div>
<div class="auth-card-subtitle">Open your document workspace.</div>
"""

_SIGNUP_INTRO_HTML = """
<div class="form-intro">
    Create an account to get a private workspace for your documents.
</div>
"""


def _login_tab():
    with st.form("login_form", border=False):
        username = st.text_input(
            "Username", key="login_username", placeholder="Enter your username"
        )
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
            placeholder="Enter your password",
        )
        submitted = st.form_submit_button("Log in", use_container_width=True)

    if not submitted:
        return

    if not username or not password:
        st.warning("Enter your username and password.")
        return

    success, message = login(username, password)
    if success:
        st.session_state.logged_in = True
        st.session_state.username = username.strip().lower()
        st.rerun()
    else:
        st.error(message)


def _signup_tab():
    st.markdown(_SIGNUP_INTRO_HTML, unsafe_allow_html=True)

    with st.form("signup_form", border=False):
        username = st.text_input(
            "Username", key="signup_username", placeholder="Choose a username"
        )
        password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
            placeholder="Create a password",
        )
        confirm = st.text_input(
            "Confirm password",
            type="password",
            key="confirm_password",
            placeholder="Repeat your password",
        )
        submitted = st.form_submit_button("Create account", use_container_width=True)

    if not submitted:
        return

    if not username or not password:
        st.warning("Enter a username and password.")
    elif password != confirm:
        st.error("Passwords do not match.")
    else:
        success, message = signup(username, password)
        if success:
            st.success("Account created. Switch to the Log in tab to continue.")
        else:
            st.error(message)


def render_auth_screen():
    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.markdown(_BRAND_HTML, unsafe_allow_html=True)

    with right:
        with st.container(key="auth_card"):
            st.markdown(_CARD_HEADER_HTML, unsafe_allow_html=True)
            tab_login, tab_signup = st.tabs(["Log in", "Create account"])
            with tab_login:
                _login_tab()
            with tab_signup:
                _signup_tab()

    st.stop()