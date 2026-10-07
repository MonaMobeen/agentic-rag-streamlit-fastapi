# The Agentic Reading Room

An **Agentic RAG** app. Upload your own documents, ask questions, and get answers with sources. An autonomous agent decides when to search your documents, when to answer from context, and when to say "I don't know."

Built with Streamlit, LangChain, LangGraph, Chroma and Groq. It includes a product-grade chat UI, authentication, session management, and an observability dashboard for tracing and evaluating answers.

---

## Table of contents

1. [Features](#features)
2. [How it works](#how-it-works)
3. [Tech stack](#tech-stack)
4. [Project structure](#project-structure)
5. [Getting started](#getting-started)
6. [Run with Docker](#run-with-docker)
7. [Deploying](#deploying)
8. [Observability](#observability)
9. [Configuration](#configuration)
10. [Known limitations](#known-limitations)
11. [Roadmap](#roadmap)

---

## Features

### Agentic RAG
- Upload **PDF and TXT** files and index them with one click.
- A **LangGraph ReAct agent** chooses whether to search the documents or answer directly.
- Answers show the **sources** they used.
- Sessions can ask about **other sessions** (earlier conversation history is passed along as context).

### Chat experience
- Clean, readable chat with Markdown, code blocks and tables.
- **Copy** and **Regenerate** buttons on every answer.
- **Thumbs up / down** feedback with an optional comment.
- **View trace** button that opens the exact trace behind an answer.
- Suggested prompts once documents are ready.
- A loading state while the agent works, and friendly error cards with a **Try again** button (no raw Python errors).
- Chat input is disabled until documents are processed, with a clear reason.

### Sessions and documents
- Create, switch, **rename**, **delete** and **search** sessions.
- Document cards show file type, size and **Indexed / Not indexed** status.
- Failed indexing shows a clear message instead of crashing.

### Authentication
- Sign up, log in and log out.
- Passwords are hashed with **bcrypt**.
- Simple validation and friendly error messages.

### Design system
- **Dark and light themes**, designed separately (not inverted).
- Responsive layout, visible focus states, and reduced-motion support.
- Short, purposeful animations only.

### Observability and evaluation
- Every answer creates a **trace**: question, answer, sources, latency, status and execution timeline.
- Dashboard with **Overview, Traces, Evaluations, Retrieval, Models, Errors and Feedback** sections.
- **Human evaluation**: mark answers Correct, Partially correct or Incorrect, with an optional reference answer.
- Sensitive text (emails, tokens, key-like strings, long numbers) is **redacted** before it is stored.
- Each user sees only their own traces, unless listed as an admin.
- Metrics that the backend cannot provide show **"Not available yet"** and name the data needed. Nothing is faked.

---

## How it works

```text
User
 |
Streamlit UI (auth, chat, sessions, documents)
 |
RAGService (rag_engine.py)
 |-- build_index(files): read PDF/TXT -> split into chunks -> embed -> store in Chroma
 |-- ask_with_agent(question): LangGraph agent -> search tool (Chroma) -> Groq LLM -> answer + sources
 |
Tracing (observability/tracer.py)
 |
SQLite (observability.db): traces, feedback, evaluations
 |
Observability dashboard
```

1. The user uploads files and clicks **Process documents**.
2. Files are read with `pypdf`, split with `RecursiveCharacterTextSplitter`, embedded with a Hugging Face model, and stored in **Chroma**.
3. When the user asks a question, the **agent** decides whether to call the document search tool.
4. The **Groq** model writes the final answer. The app shows the answer and its sources.
5. The call is wrapped in a trace, so latency, status, sources and feedback are saved for the dashboard.

---

## Tech stack

| Area | Tools |
| --- | --- |
| UI | Streamlit |
| Agent | LangChain, LangGraph (`create_react_agent`) |
| LLM | Groq (`langchain-groq`) |
| Embeddings | Hugging Face (`langchain-huggingface`, `sentence-transformers`, `torch`) |
| Vector store | Chroma (`langchain-chroma`, `chromadb`) |
| Documents | `pypdf`, `RecursiveCharacterTextSplitter` |
| Auth | `bcrypt`, JSON user store |
| Observability | SQLite (Python standard library) |
| API | FastAPI (`api.py`) |
| Packaging | Docker |

Python 3.14 was used for development and in the Docker image.

---

## Project structure

```text
RAG/
├── app.py                  # Entry point: routing, top bar, theme toggle, logout
├── auth.py                 # Sign up / log in logic (bcrypt, users.json)
├── auth_ui.py              # Login and sign-up screen
├── chat_ui.py              # Chat history, sources, actions, feedback, tracing hook
├── session_manager.py      # Sessions, sidebar navigation, document upload and indexing
├── theme.py                # Design system: dark and light themes, all CSS
├── observability_ui.py     # Observability dashboard and trace detail
├── observability/
│   ├── store.py            # SQLite storage and redaction
│   ├── tracer.py           # Trace and span helpers
│   └── metrics.py          # Dashboard metrics computed from stored data
├── rag_engine.py           # RAGService: indexing and the agent
├── api.py                  # FastAPI backend
├── evaluate.py             # Evaluation script
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── README.md
```

---

## Getting started

### 1. Clone and install

```bash
git clone https://github.com/MonaMobeen/rag-streamlit-fastapi.git
cd rag-streamlit-fastapi
python -m venv venv
source venv/Scripts/activate        # Git Bash on Windows
pip install -r requirements.txt
```

### 2. Add your API key

Create a `.env` file in the project folder:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run

```bash
streamlit run app.py
```

Open `http://localhost:8501`.

### 4. Use the app

1. **Create account**, then **Log in**.
2. Upload a PDF or TXT file in the sidebar and click **Process documents**.
3. Ask a question in the chat.
4. Click **View trace** under an answer to see how it was produced.

The first time you process documents, the embedding model is downloaded. This can take a few minutes on a slow connection.

---

## Run with Docker

Build the image:

```bash
docker build --load -t agentic-rag .
```

The first build is large (`torch`, `transformers`, `chromadb`). It can take a long time on a slow connection.

Run the container with your secrets:

```bash
docker run --rm -p 8501:8501 --env-file .env agentic-rag
```

Open `http://localhost:8501`.

Notes:

- Secrets are **not** baked into the image. `.env` is excluded by `.dockerignore`, so pass it at run time.
- Without a volume, users, the document index and the observability database are lost when the container stops.

---

## Deploying

The `Dockerfile` reads the `PORT` environment variable, so it works on platforms that set their own port (Railway, Render and similar).

Checklist:

1. Set the service **Root Directory** to the folder that contains the `Dockerfile` if it is not the repository root.
2. Add your keys as environment variables. Do **not** set `PORT`.
3. Choose an instance with enough memory. The embedding model and `torch` need more than 512 MB, so measure first with `docker stats`.
4. Add a persistent volume if you need users and the index to survive restarts.

---

## Observability

Open **Observability** in the sidebar.

| Section | What it shows |
| --- | --- |
| Overview | Total queries, success and error rate, average and P95 latency, charts, slowest answers, sessions |
| Traces | Searchable list of traces, with status and sort filters |
| Evaluations | Human verdicts (Correct, Partial, Incorrect) and how they compare with user feedback |
| Retrieval | How often documents were searched, and the most cited sources |
| Models | Model and prompt tables, when the backend provides them |
| Errors | Failed requests grouped by error type |
| Feedback | Helpful and not helpful counts with comments |

A trace detail page shows the question, answer, execution timeline, sources, evaluation form and feedback.

### What is real and what is "not available yet"

Measured by the app today: latency, status, errors, sources, feedback and human verdicts.

Shown as **Not available yet** until the backend exposes them: model name, token usage, retrieval scores, prompt version and LLM-as-a-Judge scores. To enable the first four, set `last_run_info` on the service after each answer:

```python
self.last_run_info = {
    "model": "model-name",
    "input_tokens": 0,
    "output_tokens": 0,
    "retrieval_ms": 0,
    "retrieved": [{"source": "file.pdf", "score": 0.9, "excerpt": "..."}],
}
```

The dashboard picks these up automatically. Model reasoning is never captured, only structured events.

---

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | Key for the Groq model |
| `OBS_DB_PATH` | No | Where `observability.db` is stored (default: project folder) |
| `OBS_REDACT` | No | Set to `0` to turn off redaction (default: on) |
| `OBS_ADMIN_USERS` | No | Comma-separated usernames who can see every user's traces |
| `PORT` | No | Set by hosting platforms, default `8501` in the Docker image |

---

## Known limitations

- Chat sessions live in `st.session_state`, so **chat history is lost on page refresh**.
- On hosting platforms without a persistent volume, users, the index and the observability database reset on restart.
- Token usage, model name and retrieval scores need the `last_run_info` hook.
- There is no automatic LLM-as-a-Judge yet. Evaluation is manual.
- No admin role exists in the auth system. Admins are set with `OBS_ADMIN_USERS`.

---

## Roadmap

- Save chat sessions permanently.
- Expose model, tokens and retrieval scores from `rag_engine.py`.
- Add LLM-as-a-Judge scoring for relevance and faithfulness.
- Add persistent storage for users and the vector index in production.
- Compare models and prompt versions in the dashboard.

---

## Security notes

- Keep `.env`, `users.json` and `observability.db` out of Git.
- Rotate your API key immediately if it was ever committed.
- Stored questions and answers are redacted, but do not upload highly sensitive documents to a shared deployment.