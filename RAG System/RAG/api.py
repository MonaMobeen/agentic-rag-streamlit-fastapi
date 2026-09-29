from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from rag_engine import RAGService

app = FastAPI(title="RAG API")

state = {"service": None}


class UploadedFileAdapter:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: List[str]


@app.get("/health")
def health():
    return {"status": "ok", "index_ready": state["service"] is not None}


@app.post("/upload")
def upload(files: List[UploadFile] = File(...)):
    adapted = [UploadedFileAdapter(f.filename, f.file.read()) for f in files]
    try:
        service = RAGService()
        info = service.build_index(adapted)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    state["service"] = service
    return info


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    service = state["service"]
    if service is None:
        raise HTTPException(
            status_code=400, detail="Upload documents first using /upload"
        )

    answer, docs = service.ask(req.question)

    sources = []
    for d in docs:
        entry = f"{d.metadata.get('source', 'unknown')} (Page {d.metadata.get('page', '?')})"
        if entry not in sources:
            sources.append(entry)

    return AskResponse(answer=answer, sources=sources)