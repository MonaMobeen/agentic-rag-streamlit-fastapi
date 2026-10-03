import uuid

import streamlit as st

from rag_engine import RAGService


def new_session(title: str = "New Chat") -> str:
    session_id = str(uuid.uuid4())
    st.session_state.sessions[session_id] = {
        "service": None,
        "messages": [],
        "title": title,
    }
    return session_id


def init_sessions():
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = new_session()


def get_current_session():
    current_id = st.session_state.current_session_id
    return current_id, st.session_state.sessions[current_id]


def render_sidebar(current_id: str, current: dict):
    with st.sidebar:
        st.markdown("#### 💬 Sessions")

        if st.button("➕ New Session", use_container_width=True):
            st.session_state.current_session_id = new_session()
            st.rerun()

        for sid, session in st.session_state.sessions.items():
            if sid == current_id:
                st.markdown(
                    f'<div class="session-active">● {session["title"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="session-btn">', unsafe_allow_html=True)
                if st.button(session["title"], key=f"switch_{sid}", use_container_width=True):
                    st.session_state.current_session_id = sid
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("#### 📄 Documents")

        files = st.file_uploader(
            "Upload PDF or TXT",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            key=f"uploader_{current_id}",
            label_visibility="collapsed",
        )

        if st.button("⚙️ Process documents", use_container_width=True):
            if not files:
                st.warning("Please upload at least one file first.")
            else:
                with st.spinner("Building index..."):
                    if current["service"] is None:
                        current["service"] = RAGService()
                    info = current["service"].build_index(files)

                if current["title"] == "New Chat" and files:
                    current["title"] = files[0].name[:25]

                st.success(f"Ready: {info['documents']} pages, {info['chunks']} chunks")