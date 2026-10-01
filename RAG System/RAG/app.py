import streamlit as st
from rag_engine import RAGService, format_sources

st.set_page_config(page_title="Agentic Rag")
st.title("Agentic Rag")

if "service" not in st.session_state:
    st.session_state.service = None
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
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
                service = RAGService()
                info = service.build_index(files)
            st.session_state.service = service
            st.session_state.messages = []
            st.success(f"Ready: {info['documents']} pages, {info['chunks']} chunks")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                st.text(msg["sources"])

question = st.chat_input("Ask a question about your documents")

if question:
    if st.session_state.service is None:
        st.warning("Upload and process documents first (left sidebar).")
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer, sources_list = st.session_state.service.ask_with_agent(question)
            sources = "\n".join(sources_list) if sources_list else "Document search nahi kiya gaya"
            st.markdown(answer)
            with st.expander("Sources"):
                st.text(sources)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )