import html

import streamlit as st

# Kept as-is so sessions already stored with this value still render correctly.
NO_SEARCH = "Document search nahi kiya gaya"

_EMPTY_STATE_HTML = """
<div class="empty-state">
    <h3>Start with a document</h3>
    <p>
        Upload and process your files in the sidebar, then ask a question.
        The agent searches them only when it needs to, and lists the sources
        it used under each answer.
    </p>
</div>
"""


def _sources_html(sources_text: str) -> str:
    # One complete HTML block. Splitting <div> open/close across separate
    # st.markdown calls does not wrap anything in Streamlit.
    if not sources_text or sources_text == NO_SEARCH:
        return '<div class="sources sources-none">Answered without searching your documents.</div>'

    items = [line.strip().lstrip("- ").strip() for line in sources_text.splitlines()]
    items = [item for item in items if item]
    if not items:
        return '<div class="sources sources-none">Answered without searching your documents.</div>'

    rows = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return (
        '<div class="sources">'
        '<div class="sources-title">Sources</div>'
        f"<ul>{rows}</ul>"
        "</div>"
    )


def _render_sources(sources_text: str):
    st.markdown(_sources_html(sources_text), unsafe_allow_html=True)


def render_chat_history(current: dict):
    if not current["messages"]:
        st.markdown(_EMPTY_STATE_HTML, unsafe_allow_html=True)
        return

    for msg in current["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                _render_sources(msg.get("sources", ""))


def _build_augmented_question(question: str, current_id: str) -> str:
    other_sessions_text = ""
    for sid, session in st.session_state.sessions.items():
        if sid != current_id and session["messages"]:
            lines = [f"{m['role']}: {m['content']}" for m in session["messages"]]
            other_sessions_text += f"\n--- Session: {session['title']} ---\n" + "\n".join(lines)

    if not other_sessions_text:
        return question

    return (
        f"{question}\n\n"
        f"(If this question asks about a previous/other session, here is that data:\n"
        f"{other_sessions_text})"
    )


def handle_new_question(current: dict, current_id: str):
    question = st.chat_input("Ask a question about your documents")

    if not question:
        return

    if current["service"] is None:
        st.warning("Upload and process your documents in the sidebar first.")
        return

    current["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    augmented_question = _build_augmented_question(question, current_id)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, sources_list = current["service"].ask_with_agent(augmented_question)

        sources = "\n".join(sources_list) if sources_list else NO_SEARCH
        st.markdown(answer)
        _render_sources(sources)

    current["messages"].append({"role": "assistant", "content": answer, "sources": sources})