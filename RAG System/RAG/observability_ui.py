"""AI Observability page.

Everything shown here is read from observability.db (see observability/store.py).
When a number cannot be computed from real data, the page says so and names the
data the backend would need to provide - it never shows a placeholder value.
"""

import html
import os
from datetime import datetime

import streamlit as st

from observability import metrics, store

SECTIONS = ["Overview", "Traces", "Evaluations", "Retrieval", "Models", "Errors", "Feedback"]
PAGE_SIZE = 12
VERDICTS = {"correct": "Correct", "partial": "Partially correct", "incorrect": "Incorrect"}

_RUN_INFO_HINT = (
    "service.last_run_info = {model, input_tokens, output_tokens, retrieved: [{source, score}]}"
)


# =========================================================
# STATE + CALLBACKS
# =========================================================


def _init_state():
    st.session_state.setdefault("obs_section", "Overview")
    st.session_state.setdefault("obs_trace_id", None)
    st.session_state.setdefault("obs_limit", PAGE_SIZE)


def _open_trace(trace_id: str):
    st.session_state.obs_trace_id = trace_id


def _close_trace():
    st.session_state.obs_trace_id = None


def _set_section(name: str):
    st.session_state.obs_section = name
    st.session_state.obs_limit = PAGE_SIZE


def _go_chat():
    st.session_state.page = "chat"


def _show_more():
    st.session_state.obs_limit += PAGE_SIZE


# =========================================================
# SCOPE (who can see which traces)
# =========================================================


def _admin_users() -> set:
    raw = os.getenv("OBS_ADMIN_USERS", "")
    return {name.strip().lower() for name in raw.split(",") if name.strip()}


def _scope_for(username: str):
    """None = all users (admins listed in OBS_ADMIN_USERS); otherwise only own traces."""
    return None if (username or "").lower() in _admin_users() else username


# =========================================================
# FORMATTING
# =========================================================


def _esc(value) -> str:
    return html.escape("" if value is None else str(value))


def _clip(text, limit: int) -> str:
    text = "" if text is None else str(text)
    return text if len(text) <= limit else text[: limit - 1] + "..."


def _fmt_ms(value) -> str:
    if value is None:
        return "N/A"
    return f"{value:.0f} ms" if value < 1000 else f"{value / 1000:.2f} s"


def _fmt_int(value) -> str:
    return "N/A" if value is None else f"{int(value):,}"


def _fmt_pct(value) -> str:
    return "N/A" if value is None else f"{value * 100:.0f}%"


def _when(timestamp) -> str:
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp).strftime("%b %d, %H:%M:%S")


def _tokens_text(trace: dict) -> str:
    if trace["input_tokens"] is None and trace["output_tokens"] is None:
        return "N/A"
    return f"{(trace['input_tokens'] or 0) + (trace['output_tokens'] or 0):,}"


# =========================================================
# HTML BUILDERS
# =========================================================


def _kpi(label: str, value: str, sub: str = "", unavailable: bool = False) -> str:
    css = "kpi na" if unavailable else "kpi"
    return (
        f'<div class="{css}"><div class="kpi-label">{_esc(label)}</div>'
        f'<div class="kpi-value">{_esc(value)}</div>'
        f'<div class="kpi-sub">{_esc(sub)}</div></div>'
    )


def _kpi_grid(cards: list, small: bool = False) -> str:
    css = "kpi-grid kpi-sm" if small else "kpi-grid"
    return f'<div class="{css}">{"".join(cards)}</div>'


def _na_card(title: str, reason: str, required: str) -> str:
    return (
        '<div class="obs-na">'
        f'<div class="obs-na-title">{_esc(title)}: not available yet</div>'
        f'<div class="obs-na-body">Reason: {_esc(reason)}</div>'
        f'<div class="obs-na-req">Required data: <code>{_esc(required)}</code></div>'
        "</div>"
    )


def _heading(text: str) -> str:
    return f'<div class="obs-h">{_esc(text)}</div>'


def _note(text: str) -> str:
    return f'<div class="obs-note">{_esc(text)}</div>'


def _table(headers: list, rows: list) -> str:
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>" for row in rows)
    return (
        '<div class="table-wrap"><table class="obs-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _bar_chart(series: list, label: str) -> str:
    if not series or all(value == 0 for _, value in series):
        return '<div class="chart-empty">No queries in this period.</div>'

    width, height, base = 600, 150, 128
    top = max(value for _, value in series)
    count = len(series)
    gap = 6
    bar_w = (width - gap * (count + 1)) / count

    bars = []
    for i, (name, value) in enumerate(series):
        bar_h = (base - 14) * value / top
        x = gap + i * (bar_w + gap)
        y = base - bar_h
        bars.append(
            f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
            f'height="{bar_h:.1f}" rx="3"><title>{_esc(name)}: {value}</title></rect>'
        )

    return (
        f'<div class="chart"><svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{_esc(label)}">'
        f'<line class="grid" x1="0" y1="{base}" x2="{width}" y2="{base}"/>'
        f'{"".join(bars)}'
        f'<text x="{gap}" y="{height - 6}">{_esc(series[0][0])}</text>'
        f'<text x="{width - gap}" y="{height - 6}" text-anchor="end">{_esc(series[-1][0])}</text>'
        f'<text x="{width - gap}" y="12" text-anchor="end">max {top}</text>'
        "</svg></div>"
    )


def _line_chart(points: list, label: str) -> str:
    if len(points) < 2:
        return '<div class="chart-empty">Needs at least two answers to draw a trend.</div>'

    width, height, base, top_pad = 600, 150, 128, 16
    top = max(value for value, _ in points) or 1.0
    step = (width - 20) / (len(points) - 1)

    coords = []
    dots = []
    for i, (value, status) in enumerate(points):
        x = 10 + i * step
        y = base - (base - top_pad) * value / top
        coords.append(f"{x:.1f},{y:.1f}")
        css = "dot-err" if status == "error" else "dot"
        dots.append(
            f'<circle class="{css}" cx="{x:.1f}" cy="{y:.1f}" r="3.2">'
            f"<title>{_esc(_fmt_ms(value))} ({_esc(status)})</title></circle>"
        )

    return (
        f'<div class="chart"><svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{_esc(label)}">'
        f'<line class="grid" x1="0" y1="{base}" x2="{width}" y2="{base}"/>'
        f'<line class="grid" x1="0" y1="{top_pad}" x2="{width}" y2="{top_pad}"/>'
        f'<polyline class="line" points="{" ".join(coords)}"/>'
        f'{"".join(dots)}'
        f'<text x="10" y="{height - 6}">oldest</text>'
        f'<text x="{width - 10}" y="{height - 6}" text-anchor="end">latest</text>'
        f'<text x="{width - 10}" y="12" text-anchor="end">{_esc(_fmt_ms(top))}</text>'
        "</svg></div>"
    )


def _dist_row(label: str, value, count: int, css: str) -> str:
    pct = 0 if value is None else value * 100
    return (
        f'<div class="dist-row"><div class="dist-label">{_esc(label)}</div>'
        f'<svg class="dist-svg" viewBox="0 0 100 4" preserveAspectRatio="none" aria-hidden="true">'
        f'<rect class="dist-track" width="100" height="4" rx="2"/>'
        f'<rect class="dist-fill {css}" width="{pct:.1f}" height="4" rx="2"/></svg>'
        f'<div class="dist-val">{_esc(_fmt_pct(value))} ({count})</div></div>'
    )


def _status_chip(status: str) -> str:
    if status == "success":
        return '<span class="chip ok"><i></i>Success</span>'
    return '<span class="chip err"><i></i>Error</span>'


def _trace_row_html(trace: dict, fb_map: dict) -> str:
    chips = [
        _status_chip(trace["status"]),
        f'<span class="chip">{_esc(_fmt_ms(trace["total_ms"]))}</span>',
        f'<span class="chip">{len(trace["sources"])} source(s)</span>',
    ]
    if trace["model"]:
        chips.append(f'<span class="chip">{_esc(trace["model"])}</span>')
    rating = fb_map.get(trace["trace_id"])
    if rating == "up":
        chips.append('<span class="chip ok"><i></i>Helpful</span>')
    elif rating == "down":
        chips.append('<span class="chip err"><i></i>Not helpful</span>')
    chips.append(f'<span class="chip">{_esc(_when(trace["created_at"]))}</span>')

    return (
        '<div class="trace-row">'
        f'<div class="trace-q">{_esc(_clip(trace["question"], 160))}</div>'
        f'<div class="trace-meta">{"".join(chips)}</div></div>'
    )


def _render_trace_list(items: list, prefix: str, fb_map: dict):
    for trace in items:
        left, right = st.columns([6, 1], vertical_alignment="center")
        with left:
            st.markdown(_trace_row_html(trace, fb_map), unsafe_allow_html=True)
        with right:
            st.button(
                "Open",
                key=f"open_{prefix}_{trace['trace_id']}",
                on_click=_open_trace,
                args=(trace["trace_id"],),
                use_container_width=True,
            )


# =========================================================
# TRACE DETAIL
# =========================================================

_BADGES = {"ok": ("OK", "ok"), "error": ("Error", "err"), "warning": ("Warning", "warn")}


def _timeline_html(steps: list, total_ms) -> str:
    if not steps:
        return _note("No execution events were recorded for this trace.")

    ends = [(s.get("start_ms") or 0) + (s.get("duration_ms") or 0) for s in steps]
    span_total = max([total_ms or 0, *ends, 1])

    rows = []
    for step in sorted(steps, key=lambda s: s.get("start_ms") or 0):
        start = step.get("start_ms") or 0
        duration = step.get("duration_ms") or 0
        x = 100 * start / span_total
        w = max(100 * duration / span_total, 0.8)
        label, css = _BADGES.get(step.get("status", "ok"), _BADGES["ok"])
        depth = min(int(step.get("depth") or 0), 2)

        detail_bits = []
        if step.get("summary"):
            detail_bits.append(f'<div>{_esc(step["summary"])}</div>')
        for key, value in (step.get("metadata") or {}).items():
            detail_bits.append(f'<div class="step-kv"><b>{_esc(key)}</b> {_esc(value)}</div>')
        if not detail_bits:
            detail_bits.append("<div>No additional details recorded.</div>")

        rows.append(
            f'<details class="step depth-{depth}"><summary>'
            f'<span class="step-t">+{_esc(_fmt_ms(start))}</span>'
            f'<span class="step-name">{_esc(step.get("name", "Step"))}</span>'
            f'<span class="step-badge {css}">{label}</span>'
            f'<span class="step-d">{_esc(_fmt_ms(duration))}</span></summary>'
            f'<svg class="step-svg" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true">'
            f'<rect class="step-track" width="100" height="6" rx="3"/>'
            f'<rect class="step-fill {css}" x="{x:.2f}" width="{w:.2f}" height="6" rx="3"/></svg>'
            f'<div class="step-body">{"".join(detail_bits)}</div></details>'
        )
    return f'<div class="timeline">{"".join(rows)}</div>'


def _retrieval_html(trace: dict) -> str:
    retrieved = trace["retrieved"]
    if retrieved:
        cards = []
        for item in retrieved:
            score = item.get("score")
            score_text = f"{score:.3f}" if isinstance(score, (int, float)) else "N/A"
            excerpt = _clip(item.get("excerpt"), 320)
            chunk = f' <span class="ret-chunk">chunk {_esc(item["chunk_id"])}</span>' if item.get("chunk_id") else ""
            cards.append(
                '<div class="ret-card">'
                f'<div class="ret-rank">#{_esc(item.get("rank"))}</div>'
                '<div class="ret-body">'
                f'<div class="ret-name">{_esc(item.get("source") or "Unknown source")}{chunk}</div>'
                + (f'<div class="ret-excerpt">{_esc(excerpt)}</div>' if excerpt else "")
                + "</div>"
                f'<div class="ret-score"><b>{_esc(score_text)}</b><span>score</span></div></div>'
            )
        return "".join(cards)

    if trace["sources"]:
        items = "".join(
            f'<li><span class="src-n">{i}</span><span class="src-t">{_esc(s.strip().lstrip("- ").strip())}</span></li>'
            for i, s in enumerate(trace["sources"], start=1)
        )
        return (
            f'<details class="sources" open><summary>{len(trace["sources"])} source reference(s)</summary>'
            f"<ol>{items}</ol></details>"
            + _na_card(
                "Similarity scores and excerpts",
                "the backend returns source names only",
                "retrieved[].score, retrieved[].excerpt",
            )
        )

    return _note("This answer did not use any document sources.")


def _render_evaluation(trace: dict, username: str):
    st.markdown(_heading("Evaluation"), unsafe_allow_html=True)
    existing = store.get_evaluations(trace["trace_id"])

    st.markdown(
        _note(
            "Ground-truth evaluation: you judge this answer against a reference. "
            "It is a human label, not an automatic score."
        ),
        unsafe_allow_html=True,
    )

    human = existing.get("human") or {}
    options = list(VERDICTS)
    with st.form(f"eval_form_{trace['trace_id']}", border=False):
        verdict = st.selectbox(
            "Verdict",
            options,
            index=options.index(human["label"]) if human.get("label") in options else 0,
            format_func=lambda key: VERDICTS[key],
        )
        expected = st.text_area(
            "Reference (expected) answer, optional",
            value=human.get("expected_answer") or "",
            height=100,
        )
        reason = st.text_input("Notes, optional", value=human.get("reason") or "")
        saved = st.form_submit_button("Save evaluation")

    if saved:
        try:
            store.save_evaluation(
                trace["trace_id"], "human", verdict, expected, None, reason, evaluator=username
            )
            human = store.get_evaluations(trace["trace_id"]).get("human") or {}
        except Exception:
            st.error("The evaluation could not be saved. Please try again.")

    if human.get("label"):
        st.markdown(
            f'<span class="chip ok"><i></i>Human verdict: {_esc(VERDICTS.get(human["label"], human["label"]))}</span>',
            unsafe_allow_html=True,
        )

    judge = existing.get("llm_judge")
    if judge and judge.get("scores"):
        scores = ", ".join(f"{k}: {v}" for k, v in judge["scores"].items())
        st.markdown(
            f'<div class="obs-note"><b>LLM-as-a-Judge</b> (an evaluation signal, not ground truth): '
            f'{_esc(scores)}. {_esc(judge.get("reason") or "")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            _na_card(
                "LLM-as-a-Judge",
                "no evaluator model is connected to the app yet",
                "an LLM client from rag_engine.py (then results are stored with kind='llm_judge')",
            ),
            unsafe_allow_html=True,
        )


def _render_trace_detail(trace_id: str, scope, username: str):
    trace = store.get_trace(trace_id)

    top_left, top_mid, top_right = st.columns([4, 1.2, 1.2], vertical_alignment="center")
    with top_mid:
        st.button("Back", key="trace_back", on_click=_close_trace, use_container_width=True)
    with top_right:
        st.button("Go to chat", key="trace_to_chat", on_click=_go_chat, use_container_width=True)

    if trace is None or (scope is not None and trace["username"] != scope):
        with top_left:
            st.markdown(_heading("Trace not found"), unsafe_allow_html=True)
        st.info("This trace does not exist or you do not have access to it.")
        return

    with top_left:
        st.markdown(
            '<div class="trace-title">Trace '
            f'<code>{_esc(trace["trace_id"][:12])}</code> {_status_chip(trace["status"])}</div>'
            f'<div class="obs-sub">{_esc(_when(trace["created_at"]))} &middot; session '
            f'<code>{_esc((trace["session_id"] or "")[:8])}</code></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        _kpi_grid(
            [
                _kpi("Total duration", _fmt_ms(trace["total_ms"])),
                _kpi("Model", trace["model"] or "N/A", unavailable=not trace["model"]),
                _kpi("Tokens", _tokens_text(trace), unavailable=_tokens_text(trace) == "N/A"),
                _kpi("Sources", str(len(trace["sources"]))),
                _kpi("Document search", "Yes" if trace["searched"] else "No"),
            ],
            small=True,
        ),
        unsafe_allow_html=True,
    )

    if trace["status"] == "error":
        st.markdown(
            '<div class="error-card"><b>This request failed.</b><br>'
            f'{_esc(trace["error_type"])}: {_esc(_clip(trace["error_message"], 300))}</div>',
            unsafe_allow_html=True,
        )
        if trace["error_details"]:
            with st.expander("Technical details"):
                st.code(trace["error_details"], language="text")

    st.markdown(_heading("Question"), unsafe_allow_html=True)
    st.markdown(f'<div class="obs-quote">{_esc(trace["question"])}</div>', unsafe_allow_html=True)

    if trace["answer"]:
        st.markdown(_heading("Answer"), unsafe_allow_html=True)
        with st.container(key="obs_answer"):
            st.markdown(trace["answer"])

    st.markdown(_heading("Execution timeline"), unsafe_allow_html=True)
    st.markdown(
        _note("Structured events recorded by the app. Model reasoning is never captured."),
        unsafe_allow_html=True,
    )
    st.markdown(_timeline_html(trace["steps"], trace["total_ms"]), unsafe_allow_html=True)

    st.markdown(_heading("Retrieval"), unsafe_allow_html=True)
    st.markdown(_retrieval_html(trace), unsafe_allow_html=True)

    if trace["status"] == "success":
        _render_evaluation(trace, username)

    st.markdown(_heading("Feedback"), unsafe_allow_html=True)
    feedback = store.get_feedback(trace["trace_id"])
    if feedback:
        label = "Helpful" if feedback["rating"] == "up" else "Not helpful"
        css = "ok" if feedback["rating"] == "up" else "err"
        comment = f' &middot; "{_esc(feedback["comment"])}"' if feedback.get("comment") else ""
        st.markdown(
            f'<span class="chip {css}"><i></i>{label}</span> '
            f'<span class="obs-sub">{_esc(_when(feedback["created_at"]))}{comment}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(_note("No feedback was given for this answer."), unsafe_allow_html=True)

    if trace["attributes"]:
        st.markdown(_heading("Request attributes"), unsafe_allow_html=True)
        st.markdown(
            _table(["Attribute", "Value"], [[k, v] for k, v in trace["attributes"].items()]),
            unsafe_allow_html=True,
        )

    missing = []
    if not trace["model"]:
        missing.append("model")
    if _tokens_text(trace) == "N/A":
        missing.append("input_tokens / output_tokens")
    if not trace["retrieved"]:
        missing.append("retrieved[].score")
    if missing:
        st.markdown(
            _na_card(
                "Model, token and retrieval details",
                "the backend does not expose them to the app yet",
                _RUN_INFO_HINT,
            ),
            unsafe_allow_html=True,
        )


# =========================================================
# SECTIONS
# =========================================================


def _section_overview(traces, fb_rows, fb_map):
    o = metrics.overview(traces, fb_rows)

    helpful = (o["feedback_up"] / o["feedback_total"]) if o["feedback_total"] else None
    cards = [
        _kpi("Total queries", _fmt_int(o["total"]), f'{o["sessions"]} session(s)'),
        _kpi("Successful", _fmt_int(o["successful"]), f'{o["errors"]} failed'),
        _kpi("Error rate", _fmt_pct(o["error_rate"])),
        _kpi("Avg latency", _fmt_ms(o["avg_latency_ms"]), f'median {_fmt_ms(o["median_latency_ms"])}'),
        _kpi("P95 latency", _fmt_ms(o["p95_latency_ms"]), f'of {o["successful"]} successful'),
        _kpi(
            "Total tokens",
            _fmt_int(o["total_tokens"]),
            "" if o["total_tokens"] is not None else "backend does not report tokens",
            unavailable=o["total_tokens"] is None,
        ),
        _kpi(
            "Avg retrieval score",
            "N/A" if o["avg_retrieval_score"] is None else f'{o["avg_retrieval_score"]:.2f}',
            "" if o["avg_retrieval_score"] is not None else "backend does not report scores",
            unavailable=o["avg_retrieval_score"] is None,
        ),
        _kpi(
            "Helpful answers",
            _fmt_pct(helpful),
            f'{o["feedback_up"]} up, {o["feedback_down"]} down' if o["feedback_total"] else "no feedback yet",
            unavailable=helpful is None,
        ),
    ]
    st.markdown(_kpi_grid(cards), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown(_heading("Queries per day (last 14 days)"), unsafe_allow_html=True)
        st.markdown(
            _bar_chart(metrics.queries_by_day(traces), "Queries per day"),
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(_heading("Latency of recent answers"), unsafe_allow_html=True)
        st.markdown(
            _line_chart(metrics.latency_series(traces), "Latency of recent answers"),
            unsafe_allow_html=True,
        )

    slow = metrics.slowest(traces)
    if slow:
        st.markdown(_heading("Slowest answers"), unsafe_allow_html=True)
        _render_trace_list(slow, "slow", fb_map)

    sessions = metrics.session_table(traces, fb_map)
    if sessions:
        st.markdown(_heading("Sessions"), unsafe_allow_html=True)
        titles = {
            sid: data.get("title")
            for sid, data in st.session_state.get("sessions", {}).items()
        }
        rows = [
            [
                titles.get(s["session_id"]) or f'Session {s["session_id"][:8]}',
                s["queries"],
                _fmt_ms(s["total_ms"]),
                s["errors"],
                f'{s["up"]} up / {s["down"]} down',
                _when(s["last_at"]),
            ]
            for s in sessions[:8]
        ]
        st.markdown(
            _table(["Session", "Queries", "Total time", "Errors", "Feedback", "Last activity"], rows),
            unsafe_allow_html=True,
        )


def _section_traces(traces, fb_map):
    f1, f2, f3 = st.columns([3, 1.3, 1.3])
    with f1:
        query = st.text_input(
            "Search", placeholder="Search question, trace ID or session ID", key="obs_search"
        ).strip().lower()
    with f2:
        status = st.selectbox("Status", ["All", "Success", "Error"], key="obs_status")
    with f3:
        order = st.selectbox("Sort by", ["Newest", "Slowest"], key="obs_order")

    items = traces
    if query:
        items = [
            t
            for t in items
            if query in (t["question"] or "").lower()
            or query in t["trace_id"].lower()
            or query in (t["session_id"] or "").lower()
        ]
    if status != "All":
        items = [t for t in items if t["status"] == status.lower()]
    if order == "Slowest":
        items = sorted(items, key=lambda t: t["total_ms"] or 0, reverse=True)

    st.markdown(_note(f"{len(items)} trace(s)"), unsafe_allow_html=True)
    if not items:
        st.markdown('<div class="chart-empty">No traces match these filters.</div>', unsafe_allow_html=True)
        return

    limit = st.session_state.obs_limit
    _render_trace_list(items[:limit], "list", fb_map)
    if len(items) > limit:
        st.button("Show more", key="obs_more", on_click=_show_more)


def _section_evaluations(traces, evaluations, fb_map):
    summary = metrics.evaluation_summary(evaluations)
    answers = [t for t in traces if t["status"] == "success"]

    st.markdown(_heading("Ground-truth evaluation (human labels)"), unsafe_allow_html=True)
    if summary["human_total"]:
        st.markdown(
            _note(f'{summary["human_total"]} of {len(answers)} answers reviewed.')
            + _dist_row("Correct", summary["human_pct"]["correct"], summary["human_counts"]["correct"], "ok")
            + _dist_row("Partially correct", summary["human_pct"]["partial"], summary["human_counts"]["partial"], "warn")
            + _dist_row("Incorrect", summary["human_pct"]["incorrect"], summary["human_counts"]["incorrect"], "err"),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="chart-empty">No evaluation data yet. Open a trace and save a verdict '
            "to start collecting ground-truth evaluations.</div>",
            unsafe_allow_html=True,
        )

    st.markdown(_heading("AI evaluation vs human feedback"), unsafe_allow_html=True)
    cross = metrics.labels_vs_feedback(evaluations, fb_map)
    if sum(sum(c.values()) for c in cross.values()):
        rows = [
            [
                "Helpful (up)" if rating == "up" else "Not helpful (down)",
                cross[rating]["correct"],
                cross[rating]["partial"],
                cross[rating]["incorrect"],
            ]
            for rating in ("up", "down")
        ]
        st.markdown(
            _table(["User feedback", "Correct", "Partial", "Incorrect"], rows),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            _note("Needs answers that have both a human verdict and user feedback."),
            unsafe_allow_html=True,
        )

    st.markdown(_heading("LLM-as-a-Judge"), unsafe_allow_html=True)
    if summary["judge_total"]:
        avg = summary["judge_avg_overall"]
        st.markdown(
            _note(
                f'{summary["judge_total"]} judged answer(s). Average overall score: '
                f'{"N/A" if avg is None else f"{avg:.2f}"}. '
                "This is an evaluation signal, not ground truth."
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            _na_card(
                "LLM-as-a-Judge",
                "no evaluator model is connected to the app yet",
                "an LLM client from rag_engine.py",
            ),
            unsafe_allow_html=True,
        )

    st.markdown(_heading("Quality dimensions"), unsafe_allow_html=True)
    st.markdown(
        _na_card(
            "Relevance, faithfulness, groundedness, retrieval quality, completeness",
            "they need an evaluator model or reference answers for every query",
            "llm_judge evaluations with scores {relevance, faithfulness, ...}",
        ),
        unsafe_allow_html=True,
    )

    reviewed = {e["trace_id"] for e in evaluations if e["kind"] == "human"}
    queue = [t for t in answers if t["trace_id"] not in reviewed][:5]
    if queue:
        st.markdown(_heading("Waiting for review"), unsafe_allow_html=True)
        _render_trace_list(queue, "review", fb_map)


def _section_retrieval(traces):
    stats = metrics.retrieval_stats(traces)
    cards = [
        _kpi("Answers", _fmt_int(stats["answers"])),
        _kpi("Used document search", _fmt_pct(stats["searched_rate"]), f'{stats["searched"]} answer(s)'),
        _kpi("Avg sources per search", "N/A" if stats["avg_sources"] is None else f'{stats["avg_sources"]:.1f}'),
        _kpi(
            "Avg retrieval time",
            _fmt_ms(stats["avg_retrieval_ms"]),
            "" if stats["avg_retrieval_ms"] is not None else "backend does not report it",
            unavailable=stats["avg_retrieval_ms"] is None,
        ),
    ]
    st.markdown(_kpi_grid(cards), unsafe_allow_html=True)

    st.markdown(_heading("Most cited sources"), unsafe_allow_html=True)
    top = metrics.top_sources(traces)
    if top:
        st.markdown(_table(["Source", "Answers citing it"], [[s, n] for s, n in top]), unsafe_allow_html=True)
    else:
        st.markdown('<div class="chart-empty">No answer has used document sources yet.</div>', unsafe_allow_html=True)

    st.markdown(_heading("Similarity and relevance"), unsafe_allow_html=True)
    if any(t["retrieved"] for t in traces):
        scored = [
            (item.get("source"), item.get("score"))
            for t in traces
            for item in t["retrieved"]
            if isinstance(item.get("score"), (int, float))
        ]
        st.markdown(_note(f"{len(scored)} scored chunk(s) recorded."), unsafe_allow_html=True)
    else:
        st.markdown(
            _na_card("Similarity and relevance scores", "the backend does not expose retrieved chunks", "retrieved[].score"),
            unsafe_allow_html=True,
        )


def _section_models(traces, fb_map):
    st.markdown(_heading("Model performance"), unsafe_allow_html=True)
    models = metrics.model_table(traces, fb_map)
    if models:
        rows = [
            [
                m["key"],
                m["requests"],
                _fmt_ms(m["avg_latency_ms"]),
                _fmt_int(m["tokens"]),
                _fmt_pct(m["error_rate"]),
                _fmt_pct(m["helpful_rate"]),
            ]
            for m in models
        ]
        st.markdown(
            _table(["Model", "Requests", "Avg latency", "Tokens", "Error rate", "Helpful"], rows),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            _na_card("Model monitoring", "the backend does not report which model answered", "model, input_tokens, output_tokens"),
            unsafe_allow_html=True,
        )

    st.markdown(_heading("Prompt versions"), unsafe_allow_html=True)
    prompts = metrics.prompt_table(traces, fb_map)
    if prompts:
        rows = [
            [p["key"], p["requests"], _fmt_ms(p["avg_latency_ms"]), _fmt_pct(p["error_rate"]), _fmt_pct(p["helpful_rate"])]
            for p in prompts
        ]
        st.markdown(
            _table(["Prompt", "Requests", "Avg latency", "Error rate", "Helpful"], rows),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            _na_card("Prompt tracking", "the backend does not report prompt names or versions", "prompt_name, prompt_version"),
            unsafe_allow_html=True,
        )

    st.markdown(_heading("Cost"), unsafe_allow_html=True)
    st.markdown(
        _na_card("Cost", "no pricing data is configured, and prices are never guessed", "price per token for the model in use"),
        unsafe_allow_html=True,
    )


def _section_errors(traces, fb_map):
    failed = [t for t in traces if t["status"] == "error"]
    if not failed:
        st.markdown(
            '<div class="chart-empty">No errors recorded. Failed requests will appear here with their trace.</div>',
            unsafe_allow_html=True,
        )
        return

    groups = metrics.error_groups(traces)
    st.markdown(_heading("Errors by type"), unsafe_allow_html=True)
    st.markdown(_table(["Error type", "Count"], [[name, count] for name, count in groups]), unsafe_allow_html=True)

    st.markdown(_heading("Failed requests"), unsafe_allow_html=True)
    _render_trace_list(failed[: st.session_state.obs_limit], "err", fb_map)
    if len(failed) > st.session_state.obs_limit:
        st.button("Show more", key="obs_more_err", on_click=_show_more)


def _section_feedback(traces, fb_rows):
    up = sum(1 for r in fb_rows if r["rating"] == "up")
    down = sum(1 for r in fb_rows if r["rating"] == "down")
    answers = sum(1 for t in traces if t["status"] == "success")

    st.markdown(
        _kpi_grid(
            [
                _kpi("Helpful", _fmt_int(up)),
                _kpi("Not helpful", _fmt_int(down)),
                _kpi("Feedback rate", _fmt_pct((up + down) / answers if answers else None), f"{up + down} of {answers} answers"),
            ]
        ),
        unsafe_allow_html=True,
    )

    comments = [r for r in fb_rows if r.get("comment")]
    st.markdown(_heading("Comments"), unsafe_allow_html=True)
    if not comments:
        st.markdown('<div class="chart-empty">No feedback comments yet.</div>', unsafe_allow_html=True)
        return

    for row in comments[:20]:
        left, right = st.columns([6, 1], vertical_alignment="center")
        label = "Helpful" if row["rating"] == "up" else "Not helpful"
        css = "ok" if row["rating"] == "up" else "err"
        with left:
            st.markdown(
                '<div class="trace-row">'
                f'<div class="trace-q">{_esc(_clip(row["comment"], 200))}</div>'
                f'<div class="trace-meta"><span class="chip {css}"><i></i>{label}</span>'
                f'<span class="chip">{_esc(_clip(row.get("question"), 60))}</span>'
                f'<span class="chip">{_esc(_when(row["created_at"]))}</span></div></div>',
                unsafe_allow_html=True,
            )
        with right:
            st.button(
                "Open",
                key=f"open_fb_{row['trace_id']}",
                on_click=_open_trace,
                args=(row["trace_id"],),
                use_container_width=True,
            )


# =========================================================
# ENTRY POINT
# =========================================================


def _render_header(scope):
    pill = (
        '<span class="status-pill"><i></i>Your traces</span>'
        if scope is not None
        else '<span class="status-pill ok"><i></i>All users</span>'
    )
    st.markdown(
        '<div class="obs-head"><div>'
        '<div class="obs-title">AI Observability</div>'
        '<div class="obs-sub">What happened inside the agent, how it performed, '
        "and how good the answer was.</div></div>"
        f"{pill}</div>",
        unsafe_allow_html=True,
    )


def _render_section_nav():
    current = st.session_state.obs_section
    with st.container(key="obs_nav"):
        columns = st.columns(len(SECTIONS))
        for column, name in zip(columns, SECTIONS):
            with column:
                st.button(
                    name,
                    key=f"obs_sec_{name}",
                    type="primary" if name == current else "secondary",
                    on_click=_set_section,
                    args=(name,),
                )


def render_observability(username: str):
    _init_state()
    scope = _scope_for(username)

    _render_header(scope)

    try:
        traces = store.list_traces(scope)
        fb_rows = store.list_feedback(scope)
        evaluations = store.list_evaluations(scope)
    except Exception as exc:
        st.error("Observability data could not be loaded. Please try again.")
        with st.expander("Technical details"):
            st.code(f"{type(exc).__name__}: {exc}", language="text")
        return

    fb_map = metrics.feedback_map(fb_rows)

    trace_id = st.session_state.obs_trace_id
    if trace_id:
        _render_trace_detail(trace_id, scope, username)
        return

    if not traces:
        st.markdown(
            '<div class="obs-empty"><h3>No traces yet</h3>'
            "<p>Ask a question in Chat. Every answer creates a trace that shows up here "
            "with its latency, sources, status and your feedback.</p></div>",
            unsafe_allow_html=True,
        )
        st.button("Go to chat", key="obs_empty_chat", on_click=_go_chat, type="primary")
        return

    _render_section_nav()

    section = st.session_state.obs_section
    if section == "Overview":
        _section_overview(traces, fb_rows, fb_map)
    elif section == "Traces":
        _section_traces(traces, fb_map)
    elif section == "Evaluations":
        _section_evaluations(traces, evaluations, fb_map)
    elif section == "Retrieval":
        _section_retrieval(traces)
    elif section == "Models":
        _section_models(traces, fb_map)
    elif section == "Errors":
        _section_errors(traces, fb_map)
    else:
        _section_feedback(traces, fb_rows)