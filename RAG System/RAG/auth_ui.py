import streamlit as st

from auth import login, signup


def render_auth_screen():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-header"><h1>🧠 Agentic RAG</h1></div>'
        '<p class="app-subtitle">Document Intelligence powered by AI Agents</p>',
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button", use_container_width=True):
            if not login_username or not login_password:
                st.warning("Please enter username and password.")
            else:
                success, message = login(login_username, login_password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username.strip().lower()
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        signup_username = st.text_input("Username", key="signup_username")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Create Account", key="signup_button", use_container_width=True):
            if not signup_username or not signup_password:
                st.warning("Please enter username and password.")
            elif signup_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = signup(signup_username, signup_password)
                if success:
                    st.success(message)
                    st.info("You can now login using your new account.")
                else:
                    st.error(message)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()