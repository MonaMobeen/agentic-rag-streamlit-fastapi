import streamlit as st


def _render_sources(sources_text: str):
    st.markdown('<div class="citation-strip">', unsafe_allow_html=True)
    if sources_text and sources_text != "Document search nahi kiya gaya":
        for line in sources_text.split("\n"):
            line = line.strip().lstrip("- ")
            if line:
                st.markdown(f"&mdash; {line}", unsafe_allow_html=True)
    else:
        st.markdown('<span class="no-cite">No document was consulted for this answer.</span>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_chat_history(current: dict):
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
        st.warning("Upload and process documents first, in the sidebar.")
        return

    current["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    augmented_question = _build_augmented_question(question, current_id)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, sources_list = current["service"].ask_with_agent(augmented_question)

        sources = "\n".join(sources_list) if sources_list else "Document search nahi kiya gaya"
        st.markdown(answer)
        _render_sources(sources)

    current["messages"].append({"role": "assistant", "content": answer, "sources": sources})