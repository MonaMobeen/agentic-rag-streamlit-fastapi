import streamlit as st

from auth import login, signup
from theme import LOGO_SVG

# Client-side checks only. Your auth.py still decides what is valid.
MIN_USERNAME_LEN = 3
MIN_PASSWORD_LEN = 6

_BRAND_HTML = "".join(
    [
        '<div class="auth-brand">',
        f'<div class="brand-mark brand-mark-lg">{LOGO_SVG}</div>',
        '<h1 class="auth-title">The Agentic Reading Room</h1>',
        '<p class="auth-sub">Ask questions about your documents. '
        "Every answer shows where it came from.</p>",
        "</div>",
    ]
)

_SIGNUP_NOTE_HTML = (
    '<div class="auth-note">Create an account to get your own document workspace.</div>'
)


def _login_tab():
    with st.form("login_form", border=False):
        username = st.text_input(
            "Username",
            key="login_username",
            placeholder="Enter your username",
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

    if not username.strip() or not password:
        st.warning("Enter your username and password.")
        return

    try:
        with st.spinner("Signing you in..."):
            success, message = login(username, password)
    except Exception:
        st.error("We couldn't sign you in right now. Please try again in a moment.")
        return

    if success:
        st.session_state.logged_in = True
        st.session_state.username = username.strip().lower()
        st.rerun()
    else:
        st.error(message or "Invalid username or password.")


def _signup_tab():
    st.markdown(_SIGNUP_NOTE_HTML, unsafe_allow_html=True)

    with st.form("signup_form", border=False):
        username = st.text_input(
            "Username",
            key="signup_username",
            placeholder="Choose a username",
        )
        password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
            placeholder="Create a password",
            help=f"At least {MIN_PASSWORD_LEN} characters.",
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

    if not username.strip() or not password:
        st.warning("Enter a username and password.")
        return
    if len(username.strip()) < MIN_USERNAME_LEN:
        st.warning(f"Your username needs at least {MIN_USERNAME_LEN} characters.")
        return
    if len(password) < MIN_PASSWORD_LEN:
        st.warning(f"Your password needs at least {MIN_PASSWORD_LEN} characters.")
        return
    if password != confirm:
        st.error("Passwords do not match.")
        return

    try:
        with st.spinner("Creating your account..."):
            success, message = signup(username, password)
    except Exception:
        st.error("We couldn't create your account right now. Please try again.")
        return

    if success:
        st.success("Account created. Switch to the Log in tab to continue.")
    else:
        st.error(message or "That username can't be used. Try another one.")


def render_auth_screen():
    _, middle, _ = st.columns([1, 2.2, 1])

    with middle:
        st.markdown(_BRAND_HTML, unsafe_allow_html=True)

        with st.container(key="auth_card"):
            tab_login, tab_signup = st.tabs(["Log in", "Create account"])
            with tab_login:
                _login_tab()
            with tab_signup:
                _signup_tab()

    st.stop()