import html
import json
import time
import traceback

import streamlit as st

from observability import store
from observability.tracer import start_trace
from theme import LOGO_SVG, get_palette

try:
    import streamlit.components.v1 as components
except Exception:  # copy button simply won't render
    components = None

# Kept as-is so sessions already stored with this value still render correctly.
NO_SEARCH = "Document search nahi kiya gaya"

# label shown on the card -> question sent to the agent
SUGGESTIONS = {
    "Summarize my documents": "Summarize the uploaded documents in a few bullet points.",
    "List the key points": "What are the key points I should know from these documents?",
    "Find the main requirements": "List the main requirements mentioned in the documents.",
    "Explain the core concept": "Explain the most important concept in these documents in simple terms.",
}

_TYPING_HTML = (
    '<div class="agent-working" role="status" aria-live="polite">'
    '<span class="dots"><i></i><i></i><i></i></span>'
    "<span>The agent is working on your question...</span></div>"
)

_ERROR_TITLE = "Unable to generate a response."
_ERROR_BODY = (
    "Something went wrong while handling your question. "
    "Your question is saved, so you can try again."
)


# =========================================================
# SOURCES / META
# =========================================================


def _has_sources(sources_text: str) -> bool:
    return bool(sources_text) and sources_text != NO_SEARCH


def _render_meta(msg: dict):
    meta = msg.get("meta") or {}
    searched = _has_sources(msg.get("sources", ""))

    chips = []
    if searched:
        chips.append('<span class="chip ok"><i></i>Searched your documents</span>')
    else:
        chips.append('<span class="chip"><i></i>Answered without searching</span>')
    if meta.get("elapsed") is not None:
        chips.append(f'<span class="chip">{meta["elapsed"]:.1f} s</span>')

    st.markdown(f'<div class="meta-row">{"".join(chips)}</div>', unsafe_allow_html=True)


def _render_sources(sources_text: str, open_default: bool):
    if not _has_sources(sources_text):
        return

    items = [line.strip().lstrip("- ").strip() for line in sources_text.splitlines()]
    items = [item for item in items if item]
    if not items:
        return

    rows = "".join(
        f'<li><span class="src-n">{i}</span><span class="src-t">{html.escape(item)}</span></li>'
        for i, item in enumerate(items, start=1)
    )
    label = f"{len(items)} source{'s' if len(items) != 1 else ''}"
    is_open = " open" if open_default else ""
    # Single line, no blank lines: markdown would otherwise break the HTML block.
    st.markdown(
        f'<details class="sources"{is_open}><summary>{label}</summary><ol>{rows}</ol></details>',
        unsafe_allow_html=True,
    )


# =========================================================
# ACTIONS (copy / regenerate / feedback / view trace)
# =========================================================


def _show_html(doc: str, height: int, width: int):
    """st.components.v1.html is deprecated; prefer st.iframe when available."""
    doc = doc.strip()
    if hasattr(st, "iframe"):
        st.iframe(doc, width=width, height=height)
    elif components is not None:
        components.html(doc, width=width, height=height)


def _copy_button(text: str):
    if components is None and not hasattr(st, "iframe"):
        return

    p = get_palette()
    scheme = p["scheme"]
    payload = json.dumps(text).replace("</", "<\\/")

    _show_html(
        f"""
<!doctype html>
<html>
<head>
<meta name="color-scheme" content="{scheme}">
<style>
  html, body {{ margin: 0; background: transparent; color-scheme: {scheme}; }}
  button {{
    width: 100%; height: 32px; padding: 0 12px; cursor: pointer;
    font: 500 12.5px system-ui, -apple-system, "Segoe UI", sans-serif;
    color: {p["muted"]}; background: transparent;
    border: 1px solid {p["line"]}; border-radius: 8px;
    transition: color .12s ease-out, border-color .12s ease-out, transform .12s ease-out;
  }}
  button:hover {{ color: {p["ink"]}; border-color: {p["muted"]}; }}
  button:active {{ transform: scale(.97); }}
  button.done {{ color: {p["success"]}; border-color: {p["success"]}; }}
  button:focus-visible {{ outline: 2px solid {p["accent_text"]}; outline-offset: 2px; }}
</style>
</head>
<body>
<button id="b" type="button">Copy</button>
<script>
  const text = {payload};
  const b = document.getElementById("b");
  function fallback() {{
    const t = document.createElement("textarea");
    t.value = text; t.style.position = "fixed"; t.style.opacity = "0";
    document.body.appendChild(t); t.select();
    let ok = false;
    try {{ ok = document.execCommand("copy"); }} catch (e) {{}}
    document.body.removeChild(t);
    return ok;
  }}
  b.addEventListener("click", async () => {{
    let ok = false;
    try {{ await navigator.clipboard.writeText(text); ok = true; }}
    catch (e) {{ ok = fallback(); }}
    b.textContent = ok ? "Copied" : "Copy failed";
    b.classList.toggle("done", ok);
    setTimeout(() => {{ b.textContent = "Copy"; b.classList.remove("done"); }}, 1600);
  }});
</script>
</body>
</html>
""",
        height=36,
        width=84,
    )


def _ask_later(question: str):
    """Button callback: queue a question to be answered on the next run."""
    st.session_state.pending_question = question


def _regenerate(current: dict):
    """Button callback: drop the last answer and queue its question again."""
    messages = current["messages"]
    if messages and messages[-1]["role"] == "assistant":
        messages.pop()
    if messages and messages[-1]["role"] == "user":
        st.session_state.pending_question = messages.pop()["content"]
        st.session_state.pending_regenerated = True


def _rate(msg: dict, rating: str):
    """Button callback: save thumbs up/down for this answer's trace."""
    trace_id = msg.get("trace_id")
    if not trace_id:
        return
    if (msg.get("feedback") or {}).get("rating") == rating:
        return
    msg["feedback"] = {"rating": rating, "comment": "", "comment_done": rating == "up"}
    try:
        store.save_feedback(trace_id, st.session_state.get("username", ""), rating, "")
    except Exception:
        pass


def _view_trace(trace_id: str):
    """Button callback: open this answer's trace in the Observability page."""
    st.session_state.page = "observability"
    st.session_state.obs_trace_id = trace_id


def _render_actions(current: dict, current_id: str, index: int, msg: dict, is_last: bool):
    is_error = bool(msg.get("error"))
    trace_id = msg.get("trace_id")
    feedback = msg.get("feedback") or {}

    actions = []
    if not is_error:
        actions.append("copy")
    if is_last:
        actions.append("regen")
    if not is_error:
        actions += ["up", "down"]
    if trace_id:
        actions.append("trace")

    if not actions:
        return

    with st.container(key=f"actions_{current_id}_{index}"):
        columns = st.columns(len(actions))
        for column, action in zip(columns, actions):
            with column:
                if action == "copy":
                    _copy_button(msg["content"])
                elif action == "regen":
                    st.button(
                        "Try again" if is_error else "Regenerate",
                        key=f"regen_{current_id}_{index}",
                        on_click=_regenerate,
                        args=(current,),
                    )
                elif action in ("up", "down"):
                    st.button(
                        ":material/thumb_up:" if action == "up" else ":material/thumb_down:",
                        key=f"rate_{action}_{current_id}_{index}",
                        type="primary" if feedback.get("rating") == action else "secondary",
                        help="Helpful" if action == "up" else "Not helpful",
                        on_click=_rate,
                        args=(msg, action),
                    )
                else:
                    st.button(
                        "View trace",
                        key=f"trace_{current_id}_{index}",
                        on_click=_view_trace,
                        args=(trace_id,),
                    )


def _render_feedback_followup(msg: dict):
    feedback = msg.get("feedback")
    trace_id = msg.get("trace_id")
    if not feedback or not trace_id:
        return

    if feedback["rating"] == "down" and not feedback.get("comment_done"):
        with st.form(f"fb_form_{trace_id}", border=False):
            comment = st.text_input(
                "What went wrong? (optional)",
                key=f"fb_comment_{trace_id}",
                placeholder="For example: the answer missed a detail from the document",
            )
            sent = st.form_submit_button("Send feedback")
        if sent:
            feedback["comment"] = comment.strip()
            feedback["comment_done"] = True
            try:
                store.save_feedback(
                    trace_id,
                    st.session_state.get("username", ""),
                    "down",
                    feedback["comment"],
                )
            except Exception:
                pass
            st.rerun()
    else:
        st.caption("Thanks, your feedback was saved.")


# =========================================================
# ERRORS
# =========================================================


def _render_error(msg: dict):
    st.markdown(
        f'<div class="error-card"><b>{_ERROR_TITLE}</b><br>{_ERROR_BODY}</div>',
        unsafe_allow_html=True,
    )
    if msg.get("details"):
        with st.expander("Technical details"):
            st.code(msg["details"], language="text")


# =========================================================
# EMPTY STATE
# =========================================================


def _render_empty_state(current: dict):
    st.markdown(
        '<div class="empty-state">'
        f'<div class="empty-mark">{LOGO_SVG}</div>'
        "<h2>Ask questions about your documents</h2>"
        "<p>The agent searches your files when it needs to, answers from context "
        "when it can, and says so when it doesn't know. Sources appear under "
        "every answer that used them.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if current["service"] is None:
        st.markdown(
            '<ol class="empty-steps">'
            "<li><b>Upload</b> files in the sidebar</li>"
            "<li><b>Process</b> them</li>"
            "<li><b>Ask</b> a question</li>"
            "</ol>",
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="suggest-label">Try asking</div>', unsafe_allow_html=True)
    with st.container(key="suggestions"):
        columns = st.columns(2)
        for i, (label, question) in enumerate(SUGGESTIONS.items()):
            with columns[i % 2]:
                st.button(
                    label,
                    key=f"suggest_{i}",
                    on_click=_ask_later,
                    args=(question,),
                    use_container_width=True,
                )


# =========================================================
# CHAT HISTORY
# =========================================================


def render_chat_history(current: dict, current_id: str):
    messages = current["messages"]

    if not messages:
        _render_empty_state(current)
        return

    assistant_indexes = [i for i, m in enumerate(messages) if m["role"] == "assistant"]
    last_assistant = assistant_indexes[-1] if assistant_indexes else None

    for i, msg in enumerate(messages):
        is_last = i == last_assistant

        with st.chat_message(msg["role"]):
            if msg.get("error"):
                _render_error(msg)
            else:
                st.markdown(msg["content"])

            if msg["role"] != "assistant":
                continue

            if not msg.get("error"):
                _render_meta(msg)
                _render_sources(msg.get("sources", ""), open_default=is_last)

            _render_actions(current, current_id, i, msg, is_last)
            _render_feedback_followup(msg)


# =========================================================
# NEW QUESTION
# =========================================================


def _build_augmented_question(question: str, current_id: str) -> str:
    other_sessions_text = ""
    for sid, session in st.session_state.sessions.items():
        if sid != current_id and session["messages"]:
            lines = [
                f"{m['role']}: {m['content']}"
                for m in session["messages"]
                if not m.get("error")
            ]
            if lines:
                other_sessions_text += f"\n--- Session: {session['title']} ---\n" + "\n".join(lines)

    if not other_sessions_text:
        return question

    return (
        f"{question}\n\n"
        f"(If this question asks about a previous/other session, here is that data:\n"
        f"{other_sessions_text})"
    )


def handle_new_question(current: dict, current_id: str):
    ready = current["service"] is not None

    typed = st.chat_input(
        "Ask a question about your documents"
        if ready
        else "Upload and process documents in the sidebar to start",
        disabled=not ready,
    )
    # Typed text wins; otherwise use a question queued by a suggestion or Regenerate.
    question = typed or st.session_state.pop("pending_question", None)

    if not question:
        return

    regenerated = bool(st.session_state.pop("pending_regenerated", False))

    if not ready:
        st.warning("Upload and process your documents in the sidebar first.")
        return

    current["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    augmented_question = _build_augmented_question(question, current_id)

    trace = start_trace(
        session_id=current_id,
        username=st.session_state.get("username", ""),
        question=question,
        attributes={
            "regenerated": regenerated,
            "cross_session_context_chars": len(augmented_question) - len(question),
        },
    )

    answer = None
    sources_list = None
    failure = None
    error = None

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(_TYPING_HTML, unsafe_allow_html=True)

        started = time.perf_counter()
        try:
            with trace.span("Agent run (ask_with_agent)", "agent") as span:
                answer, sources_list = current["service"].ask_with_agent(augmented_question)
                span.set_output(f"{len(sources_list or [])} source(s) returned")
            # Optional hook: used only if the backend exposes service.last_run_info.
            trace.apply_run_info(
                getattr(current["service"], "last_run_info", None),
                offset_ms=span.start_ms,
            )
        except Exception as exc:
            error = exc
            failure = f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"
        elapsed = time.perf_counter() - started

        placeholder.empty()

    trace_id = trace.finish(answer=answer, sources=sources_list, error=error)

    if failure is not None:
        current["messages"].append(
            {
                "role": "assistant",
                "content": _ERROR_TITLE,
                "sources": "",
                "error": True,
                "details": failure,
                "trace_id": trace_id,
            }
        )
    else:
        sources = "\n".join(sources_list) if sources_list else NO_SEARCH
        current["messages"].append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "meta": {"elapsed": elapsed},
                "trace_id": trace_id,
            }
        )

    # Re-render from history so the new message gets its actions and sources.
    st.rerun()