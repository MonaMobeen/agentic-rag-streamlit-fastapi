import io
import os
import uuid

from functools import lru_cache
from typing import Iterable
from dotenv import load_dotenv
from pypdf import PdfReader

# Langchain Imports
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq

load_dotenv()

os.getenv("GROQ_API_KEY")

EMBEDDING_MODEL = "sentence-transformenrs/all-MiniLM-L6-v2"
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
    uploaded_files: iterable
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
                3. Keep the answe clear and concise.
                4. When useful, mention the source filename and page number.

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

    def build_index(self, uploaded_files: Iterable) -> dict:
        self.documents = load_uploaded_dcouments(uploaded_files)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True
        )

        self.chunks = splitter.split_documents(
            self.document
        )

        collection_name = (
            f"rag_demo_{uuid.uuid4().hex}"
        )

        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
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

        embedding_dimension = len(
            self.embeddings.embed_query(
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
            raise RuntimeError(
                "Please process documents before asking question"
            )

        retrieved_docs = (
            self.retriever.invoke(
                question
            )
        )

        context = format_context(
            retrieved_docs
        )

        answer = self.answer_chain.invoke(
            {
                "context": context,
                "question": question,
            }
        )

        return answer, retrieved_docs








        



    
    


