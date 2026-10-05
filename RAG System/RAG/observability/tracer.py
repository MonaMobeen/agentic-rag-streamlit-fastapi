"""Tracing around one agent call.

Usage (see chat_ui.py):

    trace = start_trace(session_id=..., username=..., question=...)
    with trace.span("Agent run", "agent") as span:
        answer, sources = service.ask_with_agent(question)
        span.set_output(f"{len(sources)} source(s)")
    trace.apply_run_info(getattr(service, "last_run_info", None), offset_ms=span.start_ms)
    trace_id = trace.finish(answer=answer, sources=sources)

Instrumentation must never break the app: every storage call is guarded.
"""

import time
import traceback
import uuid
from contextlib import contextmanager

from observability import store

_MAX_TEXT = 8000
_MAX_EXCERPT = 600


def _clip(text, limit=_MAX_TEXT) -> str:
    text = "" if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + "..."


def _safe(text, limit=_MAX_TEXT) -> str:
    return store.redact(_clip(text, limit))


def _as_float(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _as_int(value):
    number = _as_float(value)
    return int(number) if number is not None else None


class _Span:
    def __init__(self, start_ms: float):
        self.start_ms = start_ms
        self.output = ""
        self.metadata = {}

    def set_output(self, summary: str):
        self.output = summary

    def set_meta(self, **kwargs):
        self.metadata.update(kwargs)


class Trace:
    def __init__(self, session_id: str, username: str, question: str, attributes=None):
        self.trace_id = uuid.uuid4().hex
        self.session_id = session_id
        self.username = username
        self.question = question
        self.attributes = dict(attributes or {})
        self.created_at = time.time()
        self.steps = []
        self.run_info = {}
        self._t0 = time.perf_counter()
        self.add_step(
            "Question received",
            "request",
            start_ms=0.0,
            summary=f"{len(question)} characters",
        )

    def _now_ms(self) -> float:
        return (time.perf_counter() - self._t0) * 1000.0

    def add_step(
        self,
        name: str,
        type: str = "internal",
        start_ms=None,
        duration_ms: float = 0.0,
        status: str = "ok",
        summary: str = "",
        depth: int = 0,
        metadata=None,
    ):
        self.steps.append(
            {
                "name": _safe(name, 120),
                "type": type,
                "start_ms": self._now_ms() if start_ms is None else float(start_ms),
                "duration_ms": float(duration_ms or 0.0),
                "status": status,
                "summary": _safe(summary, 400),
                "depth": depth,
                "metadata": {
                    str(k): _safe(v, 200) for k, v in (metadata or {}).items()
                },
            }
        )

    @contextmanager
    def span(self, name: str, type: str = "internal", depth: int = 0):
        started = self._now_ms()
        sp = _Span(started)
        status = "ok"
        try:
            yield sp
        except Exception as exc:
            status = "error"
            if not sp.output:
                sp.output = type_name(exc)
            raise
        finally:
            self.add_step(
                name,
                type,
                start_ms=started,
                duration_ms=self._now_ms() - started,
                status=status,
                summary=sp.output,
                depth=depth,
                metadata=sp.metadata,
            )

    def apply_run_info(self, info, offset_ms: float = 0.0):
        """Optional hook.

        If the backend sets `service.last_run_info` (a dict) after
        ask_with_agent, record the fields below. Anything else is ignored.
        Recognised keys: model, provider, input_tokens, output_tokens,
        retrieval_ms, generation_ms, prompt_name, prompt_version,
        retrieved (list of {source, chunk_id, rank, score, excerpt, metadata}),
        steps (list of {name, type, start_ms, duration_ms, status, summary}).
        """
        if not isinstance(info, dict):
            return
        try:
            clean = {
                "model": info.get("model"),
                "provider": info.get("provider"),
                "input_tokens": _as_int(info.get("input_tokens")),
                "output_tokens": _as_int(info.get("output_tokens")),
                "retrieval_ms": _as_float(info.get("retrieval_ms")),
                "generation_ms": _as_float(info.get("generation_ms")),
                "prompt_name": info.get("prompt_name"),
                "prompt_version": info.get("prompt_version"),
            }
            for key in ("model", "provider", "prompt_name", "prompt_version"):
                if clean[key] is not None:
                    clean[key] = _safe(clean[key], 120)
            self.run_info.update({k: v for k, v in clean.items() if v is not None})

            retrieved = []
            for rank, item in enumerate(info.get("retrieved") or [], start=1):
                if isinstance(item, str):
                    item = {"source": item}
                if not isinstance(item, dict):
                    continue
                retrieved.append(
                    {
                        "rank": _as_int(item.get("rank")) or rank,
                        "source": _safe(item.get("source", ""), 200),
                        "chunk_id": _safe(item.get("chunk_id", ""), 80),
                        "score": _as_float(item.get("score")),
                        "relevance": _as_float(item.get("relevance")),
                        "excerpt": _safe(item.get("excerpt", ""), _MAX_EXCERPT),
                        "metadata": {
                            str(k): _safe(v, 120)
                            for k, v in (item.get("metadata") or {}).items()
                        }
                        if isinstance(item.get("metadata"), dict)
                        else {},
                    }
                )
            if retrieved:
                self.run_info["retrieved"] = retrieved

            for step in info.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                self.add_step(
                    str(step.get("name", "Step")),
                    str(step.get("type", "internal")),
                    start_ms=offset_ms + (_as_float(step.get("start_ms")) or 0.0),
                    duration_ms=_as_float(step.get("duration_ms")) or 0.0,
                    status=str(step.get("status", "ok")),
                    summary=str(step.get("summary", "")),
                    depth=1,
                )
        except Exception:
            # Bad hook data must not affect the user's answer.
            pass

    def finish(self, answer=None, sources=None, error=None) -> str:
        total_ms = self._now_ms()
        failed = error is not None
        sources = [str(s) for s in (sources or [])]

        self.add_step(
            "Request failed" if failed else "Response returned",
            "response",
            start_ms=total_ms,
            status="error" if failed else "ok",
            summary=type_name(error) if failed else f"{len(sources)} source(s) attached",
        )

        record = {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "username": self.username,
            "created_at": self.created_at,
            "question": _safe(self.question),
            "answer": None if failed else _safe(answer),
            "status": "error" if failed else "success",
            "error_type": type_name(error) if failed else None,
            "error_message": _safe(error, 500) if failed else None,
            "error_details": (
                _safe(
                    "".join(
                        traceback.format_exception(type(error), error, error.__traceback__)
                    ),
                    4000,
                )
                if failed
                else None
            ),
            "total_ms": total_ms,
            "searched": 1 if sources else 0,
            "sources": [_safe(s, 300) for s in sources],
            "attributes": self.attributes,
            "steps": self.steps,
        }
        record.update(self.run_info)

        try:
            store.save_trace(record)
        except Exception:
            pass
        return self.trace_id


def type_name(error) -> str:
    return type(error).__name__ if error is not None else ""


def start_trace(session_id: str, username: str, question: str, attributes=None) -> Trace:
    return Trace(session_id, username, question, attributes)