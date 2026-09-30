import io
import os
import uuid
from functools import lru_cache
from typing import Iterable
from dotenv import load_dotenv
from pypdf import PdfReader

# Langchain Imports
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq

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

def load_uploaded_dcouments(
    uploaded_files: Iterable
) -> list[Document]:

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
        self.tool = None
        self.agent = None
        self.retriever = None
        self.documents = []
        self.chunks = []
        self.chat_history: list[tuple[str, str]] = []
    def build_index(self, uploaded_files: Iterable) -> dict:
        self.documents = load_uploaded_dcouments(uploaded_files)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True
        )

        self.chunks = splitter.split_documents(
            self.documents
        )

        collection_name = (
            f"rag_demo_{uuid.uuid4().hex}"
        )

        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_model,
        )

        self.vector_store.add_documents(
            documents=self.chunks
        )

        self.retriever =(
            self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": self.top_k
                },
            )
        )
        self.tool = self._build_retriever_tool()
        self.agent = create_react_agent(self.llm, tools=[self.tool])

        embedding_dimension = len(
            self.embedding_model.embed_query(
                "dimension check"
            )
        )

        return {
            "documents" : len(self.documents),
            "chunks" : len(self.chunks),
            "embedding_dimension" : embedding_dimension,
            "embedding_model" : EMBEDDING_MODEL,
            "llm_model"  : GROQ_MODEL,
        }
    
    def ask(self, question: str) -> tuple[str, list[Document]]:
        if self.retriever is None:
            raise RuntimeError("Please process documents before asking question")

        retrieved_docs = self.retriever.invoke(question)
        context = format_context(retrieved_docs)

        history = "\n".join(
            f"User: {q}\nAssistant: {a}" for q, a in self.chat_history[-3:]
        ) or "No previous conversation."

        answer = self.answer_chain.invoke({
            "context": context,
            "history": history,
            "question": question,
        })

        self.chat_history.append((question, answer))
        return answer, retrieved_docs

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

    for q in ["What is the multi-tenancy principle?", "Why does it matter?"]:
        print("\nQuestion:", q)
        answer, docs = service.ask(q)
        print("Answer:", answer)
        print("Sources:\n" + format_sources(docs))





        



    
    


