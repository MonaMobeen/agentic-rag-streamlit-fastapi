import streamlit as st

from auth import login, signup


def render_auth_screen():
    left, right = st.columns([5, 4], gap="large")

    with left:
        st.markdown(
            """
            <div class="auth-brand">
                <p class="masthead-sub">DOCUMENT INTELLIGENCE</p>
                <h1 class="auth-brand-title">The <span>Agentic</span><br>Reading Room</h1>
                <p class="auth-brand-body">
                    Upload your documents and the agent decides, on its own,
                    when to search them, when to answer from memory, and when
                    to say it simply doesn't know — every claim traced back
                    to its source.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="auth-panel">', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Sign up"])

        with tab1:
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")

            if st.button("Log in", key="login_button", use_container_width=True):
                if not login_username or not login_password:
                    st.warning("Please enter username and password.")
                else:
                    success, message = login(login_username, login_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = login_username.strip().lower()
                        st.rerun()
                    else:
                        st.error(message)

        with tab2:
            signup_username = st.text_input("Username", key="signup_username")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="confirm_password")

            if st.button("Create account", key="signup_button", use_container_width=True):
                if not signup_username or not signup_password:
                    st.warning("Please enter username and password.")
                elif signup_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = signup(signup_username, signup_password)
                    if success:
                        st.success("Account created. Switch to the Login tab to continue.")
                    else:
                        st.error(message)

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()