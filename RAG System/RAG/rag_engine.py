import io
import os
import re
import uuid
from functools import lru_cache
from typing import Iterable
from dotenv import load_dotenv
from pypdf import PdfReader

# Langchain Imports
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

load_dotenv()

os.getenv("GROQ_API_KEY")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "openai/gpt-oss-120b"


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def load_uploaded_dcouments(uploaded_files: Iterable) -> list[Document]:
    documents: list[Document] = []

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.getvalue()

        extension = os.path.splitext(file_name)[1].lower()

        if extension == ".pdf":
            reader = PdfReader(io.BytesIO(file_bytes))

            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""

                if text.strip():
                    documents.append(Document(
                        page_content=text,
                        metadata={
                            "source": file_name,
                            "page": page_number
                        },
                    ))
        elif extension == ".txt":
            text = file_bytes.decode("utf-8")

            if text.strip():
                documents.append(Document(
                    page_content=text,
                    metadata={
                        "source": file_name,
                        "page": 1,
                        "file_type": "text"
                    },
                ))

        else:
            raise ValueError(f"Unsupported file type: {extension}")

    if not documents:
        raise ValueError("No documents found in the uploaded files")

    return documents


def format_context(documents: list[Document]) -> str:
    blocks = []

    for index, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")

        blocks.append(f"""
        [Source {index}: {source}, Page {page}]
        {doc.page_content}
        """)

    return "\n\n".join(blocks)


def format_sources(documents: list[Document]) -> str:
    seen = []
    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        entry = f"{source} (Page {page})"
        if entry not in seen:
            seen.append(entry)
    return "\n".join(f"  - {s}" for s in seen)


# ---------- Guardrails ----------

CNIC_PATTERN = re.compile(r"\b\d{5}-?\d{7}-?\d{1}\b")
CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def redact_sensitive(text: str) -> str:
    text = CNIC_PATTERN.sub("[REDACTED - CNIC]", text)
    text = CARD_PATTERN.sub("[REDACTED - CARD/ACCOUNT NUMBER]", text)
    return text


AGENT_SYSTEM_PROMPT = (
    "You are a document question-answering assistant. "
    "Never reveal government ID numbers (such as CNIC), passport numbers, "
    "credit card numbers, or other sensitive personal identifiers, even if "
    "they appear in the retrieved documents. If asked for such information, "
    "say it is sensitive and cannot be shared. Only use information from the "
    "tools provided; do not make up facts that are not supported by them."
)


class RAGService:
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        top_k: int = 4,
    ) -> None:

        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY is not set")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        self.embedding_model = get_embedding_model()
        self.llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0,
            max_retries=2,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a document question-answering assistant.
                    Answer the user's question using ONLY the context below.

                    Rules:
                    1. Do not use outside knowledge.
                    2. If the answer is not available in the context, say exactly:
                    "I couldn't find that information in the uploaded documents."
                    3. Keep the answer clear and concise.
                    4. When useful, mention the source filename and page number.

                    Conversation so far (use it only to understand follow-up questions):
                    {history}

                    Context:
                    {context}
                    """
                ),
                (
                    "human",
                    "Question: {question}"
                ),
            ]
        )

        self.answer_chain = (
            self.prompt | self.llm | StrOutputParser()
        )

        self.vector_store = None
        self.retriever = None
        self.documents = []
        self.chunks = []
        self.chat_history: list[tuple[str, str]] = []
        self.tool = None
        self.summary_tool = None
        self.agent = None

    def build_index(self, uploaded_files: Iterable) -> dict:
        new_documents = load_uploaded_dcouments(uploaded_files)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True
        )

        new_chunks = splitter.split_documents(new_documents)

        if self.vector_store is None:
            collection_name = f"rag_demo_{uuid.uuid4().hex}"
            self.vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embedding_model,
            )

        self.vector_store.add_documents(documents=new_chunks)

        self.documents = self.documents + new_documents
        self.chunks = self.chunks + new_chunks

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": self.top_k
            },
        )

        self.tool = self._build_retriever_tool()
        self.summary_tool = self._build_summary_tool()
        self.agent = create_react_agent(
            self.llm,
            tools=[self.tool, self.summary_tool],
            prompt=AGENT_SYSTEM_PROMPT,
        )

        embedding_dimension = len(
            self.embedding_model.embed_query("dimension check")
        )

        return {
            "documents": len(self.documents),
            "chunks": len(self.chunks),
            "embedding_dimension": embedding_dimension,
            "embedding_model": EMBEDDING_MODEL,
            "llm_model": GROQ_MODEL,
        }

    def _build_retriever_tool(self) -> Tool:
        def run_retriever(query: str) -> str:
            docs = self.retriever.invoke(query)
            return format_context(docs)

        return Tool(
            name="search_documents",
            description=(
                "Search the uploaded documents to find information needed "
                "to answer the user's question. Input should be a short search query."
            ),
            func=run_retriever,
        )

    def _build_summary_tool(self) -> Tool:
        def run_summary(session_text: str) -> str:
            summary_prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "Summarize the following conversation in 3-5 short bullet points. "
                 "Mention what the user asked and what was answered."),
                ("human", "{conversation}"),
            ])
            chain = summary_prompt | self.llm | StrOutputParser()
            return chain.invoke({"conversation": session_text})

        return Tool(
            name="summarize_session",
            description=(
                "Summarize a previous chat session. Input must be the full text "
                "of that session's conversation (questions and answers)."
            ),
            func=run_summary,
        )

    def _build_message_history(self, question: str) -> list[dict]:
        messages = []
        for past_q, past_a in self.chat_history[-3:]:
            messages.append({"role": "user", "content": past_q})
            messages.append({"role": "assistant", "content": past_a})
        messages.append({"role": "user", "content": question})
        return messages

    def ask(self, question: str) -> tuple[str, list[Document]]:
        if self.retriever is None:
            raise RuntimeError("Please process documents before asking question")

        retrieved_docs = self.retriever.invoke(question)
        context = format_context(retrieved_docs)

        history = "\n".join(
            f"User: {q}\nAssistant: {a}" for q, a in self.chat_history[-3:]
        ) or "No previous conversation."

        answer = redact_sensitive(self.answer_chain.invoke({
            "context": context,
            "history": history,
            "question": question,
        }))

        self.chat_history.append((question, answer))
        return answer, retrieved_docs

    def ask_agentic(self, question: str) -> tuple[str, list[Document]]:
        if self.retriever is None:
            raise RuntimeError("Please process documents before asking question")

        standalone_question = self._rewrite_question(question)

        retrieved_docs = self.retriever.invoke(standalone_question)
        is_relevant = self._grade_documents(standalone_question, retrieved_docs)

        if not is_relevant:
            broader_query = f"Explain in detail: {standalone_question}"
            retrieved_docs = self.retriever.invoke(broader_query)

        context = format_context(retrieved_docs)
        history = "\n".join(
            f"User: {q}\nAssistant: {a}" for q, a in self.chat_history[-3:]
        ) or "No previous conversation."

        answer = self.answer_chain.invoke({
            "context": context,
            "history": history,
            "question": standalone_question,
        })

        self.chat_history.append((question, answer))
        return answer, retrieved_docs

    def _rewrite_question(self, question: str) -> str:
        if not self.chat_history:
            return question

        history = "\n".join(
            f"User: {q}\nAssistant: {a}" for q, a in self.chat_history[-3:]
        )

        rewrite_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Rewrite the user's latest question into a standalone question "
             "using the conversation history, so it makes sense without the history. "
             "If it is already standalone, return it unchanged. "
             "Return ONLY the rewritten question, nothing else."),
            ("human", "History:\n{history}\n\nLatest question: {question}"),
        ])
        chain = rewrite_prompt | self.llm | StrOutputParser()
        return chain.invoke({"history": history, "question": question}).strip()

    def _grade_documents(self, question: str, documents: list[Document]) -> bool:
        if not documents:
            return False

        context = format_context(documents)
        grade_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You check whether the given context contains information "
             "relevant to answering the question. "
             "Reply with exactly one word: 'yes' or 'no'."),
            ("human", "Question: {question}\n\nContext:\n{context}"),
        ])
        chain = grade_prompt | self.llm | StrOutputParser()
        verdict = chain.invoke({"question": question, "context": context}).strip().lower()
        return verdict.startswith("yes")

    def ask_with_agent(self, question: str) -> tuple[str, list[str]]:
        if self.agent is None:
            raise RuntimeError("Please process documents before asking question")

        messages = self._build_message_history(question)
        result = self.agent.invoke({"messages": messages})

        answer = redact_sensitive(result["messages"][-1].content)

        sources = []
        for msg in result["messages"]:
            if msg.__class__.__name__ == "ToolMessage":
                found = re.findall(r"Source \d+: (.+?), Page (\d+)", msg.content)
                for name, page in found:
                    entry = f"{name} (Page {page})"
                    if entry not in sources:
                        sources.append(entry)

        self.chat_history.append((question, answer))
        return answer, sources


if __name__ == "__main__":
    class FakeUpload:
        def __init__(self, path):
            self.name = os.path.basename(path)
            with open(path, "rb") as f:
                self._data = f.read()

        def getvalue(self):
            return self._data

    pdf_path = os.path.join(
        os.path.dirname(__file__), "..",
        "Government_AI_Cloud_High_Level_Architecture_InvoZone.pdf",
    )

    service = RAGService()
    info = service.build_index([FakeUpload(pdf_path)])
    print("Index ready:", info)

    test_questions = [
        "What is the multi-tenancy principle?",
        "Why does it matter?",
        "What is 25 times 4?",
    ]

    for q in test_questions:
        print("\nQuestion:", q)
        answer, sources = service.ask_with_agent(q)
        print("Answer:", answer)
        if sources:
            print("Sources:")
            for s in sources:
                print("  -", s)
        else:
            print("Sources: (agent ne document search nahi kiya)")