import html
import traceback
import uuid

import streamlit as st

from rag_engine import RAGService

MAX_TITLE_LEN = 40
SEARCH_THRESHOLD = 4  # show the search box once there are more sessions than this
NAV_ITEMS = [("chat", " New Chat"), ("observability", "Observability")]


# =========================================================
# SESSION STATE (same API as before)
# =========================================================


def new_session(title: str = "Untitled") -> str:
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


# =========================================================
# CALLBACKS (run before the rerun, so the UI updates at once)
# =========================================================


def _go_page(page: str):
    st.session_state.page = page


def _start_new_session():
    st.session_state.current_session_id = new_session()


def _switch_session(session_id: str):
    if session_id in st.session_state.sessions:
        st.session_state.current_session_id = session_id


def _rename_session(session_id: str):
    session = st.session_state.sessions.get(session_id)
    if not session:
        return
    new_title = st.session_state.get(f"rename_{session_id}", "").strip()
    if new_title:
        session["title"] = new_title[:MAX_TITLE_LEN]


def _delete_session(session_id: str):
    sessions = st.session_state.sessions
    sessions.pop(session_id, None)

    if st.session_state.current_session_id not in sessions:
        if sessions:
            st.session_state.current_session_id = list(sessions)[-1]
        else:
            st.session_state.current_session_id = new_session()


# =========================================================
# NAVIGATION
# =========================================================


def _render_nav():
    page = st.session_state.get("page", "chat")
    st.markdown('<p class="index-label">Workspace</p>', unsafe_allow_html=True)

    for key, label in NAV_ITEMS:
        if key == page:
            st.markdown(
                f'<div class="session-card-active">{html.escape(label)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.button(
                label,
                key=f"nav_{key}",
                on_click=_go_page,
                args=(key,),
                use_container_width=True,
            )

    st.markdown('<div class="nav-sep"></div>', unsafe_allow_html=True)


# =========================================================
# SESSION LIST
# =========================================================


def _render_session_row(session_id: str, session: dict, is_active: bool):
    title = session["title"]
    row, menu = st.columns([5, 1], vertical_alignment="center", gap="small")

    with row:
        if is_active:
            st.markdown(
                f'<div class="session-card-active">{html.escape(title)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.button(
                title,
                key=f"switch_{session_id}",
                on_click=_switch_session,
                args=(session_id,),
                use_container_width=True,
            )

    with menu:
        with st.popover(":material/more_horiz:", use_container_width=True):
            st.text_input(
                "Session name",
                value=title,
                key=f"rename_{session_id}",
                max_chars=MAX_TITLE_LEN,
            )
            st.button(
                "Save name",
                key=f"save_{session_id}",
                on_click=_rename_session,
                args=(session_id,),
                use_container_width=True,
            )
            st.button(
                "Delete session",
                key=f"delete_{session_id}",
                on_click=_delete_session,
                args=(session_id,),
                use_container_width=True,
            )


def _render_sessions(current_id: str):
    st.markdown('<p class="index-label">Sessions</p>', unsafe_allow_html=True)

    st.button(
        "New session",
        key="new_session_btn",
        type="primary",
        on_click=_start_new_session,
        use_container_width=True,
    )

    sessions = st.session_state.sessions
    query = ""
    if len(sessions) > SEARCH_THRESHOLD:
        query = st.text_input(
            "Search sessions",
            key="session_search",
            placeholder="Search sessions",
            label_visibility="collapsed",
        ).strip().lower()

    st.write("")

    # newest first
    visible = [
        (sid, session)
        for sid, session in reversed(list(sessions.items()))
        if not query or query in session["title"].lower()
    ]

    if not visible:
        st.caption("No matching sessions.")
        return

    for sid, session in visible:
        _render_session_row(sid, session, is_active=(sid == current_id))


# =========================================================
# DOCUMENTS
# =========================================================


def _format_size(num_bytes) -> str:
    if num_bytes is None:
        return ""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def _render_document_cards(files, indexed_names: set):
    cards = []
    indexed_count = 0

    for f in files:
        extension = f.name.rsplit(".", 1)[-1].upper() if "." in f.name else "FILE"
        is_indexed = f.name in indexed_names
        indexed_count += int(is_indexed)

        pill = (
            '<div class="doc-pill ok">Indexed</div>'
            if is_indexed
            else '<div class="doc-pill">Not indexed</div>'
        )
        cards.append(
            '<div class="doc-card">'
            f'<div class="doc-badge">{html.escape(extension[:4])}</div>'
            '<div class="doc-body">'
            f'<div class="doc-name">{html.escape(f.name)}</div>'
            f'<div class="doc-meta">{html.escape(_format_size(getattr(f, "size", None)))}</div>'
            "</div>"
            f"{pill}"
            "</div>"
        )

    noun = "file" if len(files) == 1 else "files"
    summary = f'<div class="doc-summary">{len(files)} {noun} selected, {indexed_count} indexed</div>'
    st.markdown(summary + "".join(cards), unsafe_allow_html=True)


def _process_documents(current: dict, files):
    created_here = current["service"] is None

    try:
        with st.spinner("Processing documents..."):
            if created_here:
                current["service"] = RAGService()
            info = current["service"].build_index(files)
    except Exception:
        # Don't leave an empty service behind, or the chat would look "ready".
        if created_here:
            current["service"] = None
        st.error("We couldn't process those documents. Check the files and try again.")
        with st.expander("Technical details"):
            st.code(traceback.format_exc(), language="text")
        return

    if current["title"] == "Untitled" and files:
        current["title"] = files[0].name[:25]

    current["indexed_files"] = sorted(
        set(current.get("indexed_files", [])) | {f.name for f in files}
    )
    current["index_info"] = info
    st.rerun()


def _render_documents(current_id: str, current: dict):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="index-label">Documents in this session</p>', unsafe_allow_html=True)

    files = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key=f"uploader_{current_id}",
        label_visibility="collapsed",
    )

    if files:
        _render_document_cards(files, set(current.get("indexed_files", [])))

    if st.button("Process documents", key="process_btn", use_container_width=True):
        if not files:
            st.warning("Upload at least one file first.")
        else:
            _process_documents(current, files)

    info = current.get("index_info")
    if info and current["service"] is not None:
        st.success(f"{info['documents']} pages, {info['chunks']} chunks indexed")


# =========================================================
# SIDEBAR
# =========================================================


def render_sidebar(current_id: str, current: dict):
    with st.sidebar:
        _render_nav()

        # Sessions and documents belong to the chat workspace.
        if st.session_state.get("page", "chat") == "chat":
            _render_sessions(current_id)
            _render_documents(current_id, current)