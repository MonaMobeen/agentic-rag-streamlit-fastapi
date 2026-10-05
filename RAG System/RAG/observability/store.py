"""SQLite persistence for traces, feedback and evaluations.

Standard library only. One small INSERT per answer, so writes are
synchronous (a View Trace click right after an answer can never race it).
"""

import json
import os
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(
    os.getenv("OBS_DB_PATH")
    or Path(__file__).resolve().parent.parent / "observability.db"
)
REDACTION_ENABLED = os.getenv("OBS_REDACT", "1") != "0"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    session_id TEXT,
    username TEXT,
    created_at REAL,
    question TEXT,
    answer TEXT,
    status TEXT,
    error_type TEXT,
    error_message TEXT,
    error_details TEXT,
    total_ms REAL,
    searched INTEGER,
    model TEXT,
    provider TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    retrieval_ms REAL,
    generation_ms REAL,
    prompt_name TEXT,
    prompt_version TEXT,
    sources_json TEXT,
    retrieved_json TEXT,
    attributes_json TEXT,
    steps_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_traces_user_time ON traces (username, created_at);
CREATE INDEX IF NOT EXISTS idx_traces_session ON traces (session_id);

CREATE TABLE IF NOT EXISTS feedback (
    trace_id TEXT PRIMARY KEY,
    username TEXT,
    rating TEXT,
    comment TEXT,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS evaluations (
    trace_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    label TEXT,
    expected_answer TEXT,
    scores_json TEXT,
    reason TEXT,
    evaluator TEXT,
    created_at REAL,
    PRIMARY KEY (trace_id, kind)
);
"""

_TRACE_COLUMNS = [
    "trace_id", "session_id", "username", "created_at", "question", "answer",
    "status", "error_type", "error_message", "error_details", "total_ms",
    "searched", "model", "provider", "input_tokens", "output_tokens",
    "retrieval_ms", "generation_ms", "prompt_name", "prompt_version",
    "sources_json", "retrieved_json", "attributes_json", "steps_json",
]

_schema_lock = threading.Lock()
_schema_ready = False


# =========================================================
# REDACTION
# =========================================================

_REDACTIONS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"), "Bearer [token]"),
    (
        re.compile(r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|token)\b(\s*[:=]\s*)\S+"),
        r"\1\2[redacted]",
    ),
    (
        re.compile(r"\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{32,}\b"),
        "[secret]",
    ),
    # 10-15 digits with optional single separators (phone/ID-like), not plain dates
    (re.compile(r"(?<![\w.])\+?(?:\d[\s().-]?){10,15}(?![\w])"), "[number]"),
]


def redact(text) -> str:
    """Mask emails, tokens, key-like strings and long digit runs."""
    text = "" if text is None else str(text)
    if not REDACTION_ENABLED:
        return text
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


# =========================================================
# CONNECTION
# =========================================================


def _ensure_schema():
    global _schema_ready
    if _schema_ready:
        return
    with _schema_lock:
        if _schema_ready:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH, timeout=10)
        try:
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript(_SCHEMA)
            con.commit()
        finally:
            con.close()
        _schema_ready = True


@contextmanager
def _conn():
    _ensure_schema()
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _trace_from_row(row) -> dict:
    data = dict(row)
    data["sources"] = _loads(data.pop("sources_json", None), [])
    data["retrieved"] = _loads(data.pop("retrieved_json", None), [])
    data["attributes"] = _loads(data.pop("attributes_json", None), {})
    data["steps"] = _loads(data.pop("steps_json", None), [])
    return data


# =========================================================
# TRACES
# =========================================================


def save_trace(record: dict):
    values = {column: record.get(column) for column in _TRACE_COLUMNS}
    values["sources_json"] = json.dumps(record.get("sources") or [], default=str)
    values["retrieved_json"] = json.dumps(record.get("retrieved") or [], default=str)
    values["attributes_json"] = json.dumps(record.get("attributes") or {}, default=str)
    values["steps_json"] = json.dumps(record.get("steps") or [], default=str)

    columns = ", ".join(_TRACE_COLUMNS)
    placeholders = ", ".join(f":{column}" for column in _TRACE_COLUMNS)
    with _conn() as con:
        con.execute(
            f"INSERT OR REPLACE INTO traces ({columns}) VALUES ({placeholders})",
            values,
        )


def list_traces(username=None, limit: int = 5000) -> list:
    """Newest first. username=None means every user."""
    query = "SELECT * FROM traces"
    params = []
    if username is not None:
        query += " WHERE username = ?"
        params.append(username)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with _conn() as con:
        rows = con.execute(query, params).fetchall()
    return [_trace_from_row(row) for row in rows]


def get_trace(trace_id: str):
    with _conn() as con:
        row = con.execute("SELECT * FROM traces WHERE trace_id = ?", (trace_id,)).fetchone()
    return _trace_from_row(row) if row else None


# =========================================================
# FEEDBACK
# =========================================================


def save_feedback(trace_id: str, username: str, rating: str, comment: str = ""):
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO feedback (trace_id, username, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (trace_id, username, rating, redact(comment).strip(), time.time()),
        )


def get_feedback(trace_id: str):
    with _conn() as con:
        row = con.execute("SELECT * FROM feedback WHERE trace_id = ?", (trace_id,)).fetchone()
    return dict(row) if row else None


def list_feedback(username=None) -> list:
    query = (
        "SELECT f.*, t.question AS question FROM feedback f "
        "LEFT JOIN traces t ON t.trace_id = f.trace_id"
    )
    params = []
    if username is not None:
        query += " WHERE f.username = ?"
        params.append(username)
    query += " ORDER BY f.created_at DESC"
    with _conn() as con:
        rows = con.execute(query, params).fetchall()
    return [dict(row) for row in rows]


# =========================================================
# EVALUATIONS
# =========================================================


def save_evaluation(
    trace_id: str,
    kind: str,
    label=None,
    expected_answer: str = "",
    scores=None,
    reason: str = "",
    evaluator: str = "",
):
    """kind is 'human' (ground-truth label) or 'llm_judge' (future)."""
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO evaluations "
            "(trace_id, kind, label, expected_answer, scores_json, reason, evaluator, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                trace_id,
                kind,
                label,
                redact(expected_answer).strip(),
                json.dumps(scores) if scores else None,
                redact(reason).strip(),
                evaluator,
                time.time(),
            ),
        )


def _evaluation_from_row(row) -> dict:
    data = dict(row)
    data["scores"] = _loads(data.pop("scores_json", None), {})
    return data


def get_evaluations(trace_id: str) -> dict:
    """Returns {kind: evaluation}."""
    with _conn() as con:
        rows = con.execute("SELECT * FROM evaluations WHERE trace_id = ?", (trace_id,)).fetchall()
    return {row["kind"]: _evaluation_from_row(row) for row in rows}


def list_evaluations(username=None) -> list:
    query = "SELECT e.* FROM evaluations e JOIN traces t ON t.trace_id = e.trace_id"
    params = []
    if username is not None:
        query += " WHERE t.username = ?"
        params.append(username)
    query += " ORDER BY e.created_at DESC"
    with _conn() as con:
        rows = con.execute(query, params).fetchall()
    return [_evaluation_from_row(row) for row in rows]