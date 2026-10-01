import uuid

import streamlit as st

from rag_engine import RAGService

st.set_page_config(page_title="Document Q&A")
st.title("Document Q&A (RAG)")

# ---------- Session management ----------

def new_session(title: str = "New Chat") -> str:
    session_id = str(uuid.uuid4())
    st.session_state.sessions[session_id] = {
        "service": None,
        "messages": [],
        "title": title,
    }
    return session_id


if "sessions" not in st.session_state:
    st.session_state.sessions = {}

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = new_session()

current_id = st.session_state.current_session_id
current = st.session_state.sessions[current_id]

# ---------- Sidebar ----------

with st.sidebar:
    st.header("Sessions")
    if st.button("+ New Session"):
        st.session_state.current_session_id = new_session()
        st.rerun()

    for sid, session in st.session_state.sessions.items():
        label = session["title"]
        if sid == current_id:
            st.markdown(f"**-> {label}**")
        else:
            if st.button(label, key=f"switch_{sid}"):
                st.session_state.current_session_id = sid
                st.rerun()

    st.divider()
    st.header("1. Documents")
    files = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"],
        accept_multiple_files=True,
    )
    if st.button("Process documents"):
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

# ---------- Chat area ----------

for msg in current["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                st.text(msg["sources"])

question = st.chat_input("Ask a question about your documents")

if question:
    if current["service"] is None:
        st.warning("Upload and process documents first (left sidebar).")
    else:
        current["messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer, sources_list = current["service"].ask_with_agent(question)
            sources = "\n".join(sources_list) if sources_list else "Document search nahi kiya gaya"
            st.markdown(answer)
            with st.expander("Sources"):
                st.text(sources)

        current["messages"].append(
            {"role": "assistant", "content": answer, "sources": sources}
        )