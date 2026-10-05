"""Dashboard numbers computed from stored data.

Everything returns None (or an empty list) when the underlying data does not
exist, so the UI can say "not available yet" instead of showing a made-up value.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from statistics import median


def _num(value):
    if isinstance(value, bool):
        return None
    return float(value) if isinstance(value, (int, float)) else None


def percentile(values, pct: float):
    data = sorted(v for v in values if v is not None)
    if not data:
        return None
    position = (len(data) - 1) * pct / 100.0
    lower = int(position)
    upper = min(lower + 1, len(data) - 1)
    return data[lower] + (data[upper] - data[lower]) * (position - lower)


def feedback_map(feedback_rows) -> dict:
    return {row["trace_id"]: row["rating"] for row in feedback_rows}


# =========================================================
# OVERVIEW
# =========================================================


def overview(traces, feedback_rows) -> dict:
    total = len(traces)
    successes = [t for t in traces if t["status"] == "success"]
    errors = [t for t in traces if t["status"] == "error"]
    latencies = [_num(t["total_ms"]) for t in successes if _num(t["total_ms"]) is not None]

    token_rows = [
        t for t in traces if t["input_tokens"] is not None or t["output_tokens"] is not None
    ]
    total_tokens = (
        sum((t["input_tokens"] or 0) + (t["output_tokens"] or 0) for t in token_rows)
        if token_rows
        else None
    )

    scores = [
        _num(item.get("score"))
        for t in traces
        for item in (t["retrieved"] or [])
        if _num(item.get("score")) is not None
    ]

    up = sum(1 for row in feedback_rows if row["rating"] == "up")
    down = sum(1 for row in feedback_rows if row["rating"] == "down")
    sessions = {t["session_id"] for t in traces if t["session_id"]}

    return {
        "total": total,
        "successful": len(successes),
        "errors": len(errors),
        "error_rate": (len(errors) / total) if total else None,
        "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
        "median_latency_ms": median(latencies) if latencies else None,
        "p95_latency_ms": percentile(latencies, 95),
        "total_tokens": total_tokens,
        "avg_retrieval_score": (sum(scores) / len(scores)) if scores else None,
        "sessions": len(sessions),
        "queries_per_session": (total / len(sessions)) if sessions else None,
        "feedback_up": up,
        "feedback_down": down,
        "feedback_total": up + down,
        "feedback_rate": ((up + down) / len(successes)) if successes else None,
    }


def queries_by_day(traces, days: int = 14) -> list:
    """[(label, count)] for the last `days` days, oldest first, zeros included."""
    today = datetime.now().date()
    counts = Counter(datetime.fromtimestamp(t["created_at"]).date() for t in traces)
    series = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        series.append((day.strftime("%b %d"), counts.get(day, 0)))
    return series


def latency_series(traces, limit: int = 40) -> list:
    """[(total_ms, status)] for the latest `limit` traces, oldest first."""
    recent = sorted(traces, key=lambda t: t["created_at"])[-limit:]
    return [
        (_num(t["total_ms"]) or 0.0, t["status"])
        for t in recent
        if _num(t["total_ms"]) is not None
    ]


def slowest(traces, n: int = 5) -> list:
    done = [t for t in traces if t["status"] == "success" and _num(t["total_ms"]) is not None]
    return sorted(done, key=lambda t: t["total_ms"], reverse=True)[:n]


# =========================================================
# SESSIONS
# =========================================================


def session_table(traces, fb_map) -> list:
    groups = defaultdict(list)
    for t in traces:
        if t["session_id"]:
            groups[t["session_id"]].append(t)

    rows = []
    for session_id, items in groups.items():
        times = [t["created_at"] for t in items]
        ratings = [fb_map.get(t["trace_id"]) for t in items]
        rows.append(
            {
                "session_id": session_id,
                "queries": len(items),
                "errors": sum(1 for t in items if t["status"] == "error"),
                "total_ms": sum(_num(t["total_ms"]) or 0.0 for t in items),
                "first_at": min(times),
                "last_at": max(times),
                "up": ratings.count("up"),
                "down": ratings.count("down"),
            }
        )
    return sorted(rows, key=lambda r: r["last_at"], reverse=True)


# =========================================================
# RETRIEVAL
# =========================================================


def retrieval_stats(traces) -> dict:
    successes = [t for t in traces if t["status"] == "success"]
    searched = [t for t in successes if t["searched"]]
    retrieval_ms = [_num(t["retrieval_ms"]) for t in traces if _num(t["retrieval_ms"]) is not None]
    return {
        "answers": len(successes),
        "searched": len(searched),
        "searched_rate": (len(searched) / len(successes)) if successes else None,
        "avg_sources": (
            sum(len(t["sources"]) for t in searched) / len(searched) if searched else None
        ),
        "avg_retrieval_ms": (sum(retrieval_ms) / len(retrieval_ms)) if retrieval_ms else None,
    }


def top_sources(traces, n: int = 8) -> list:
    """[(source, number of answers that cited it)]"""
    counter = Counter()
    for t in traces:
        cleaned = {s.strip().lstrip("- ").strip() for s in t["sources"] if s and s.strip()}
        counter.update(cleaned)
    return counter.most_common(n)


# =========================================================
# MODELS / PROMPTS
# =========================================================


def _group_table(traces, key_fn, fb_map) -> list:
    groups = defaultdict(list)
    for t in traces:
        key = key_fn(t)
        if key is not None:
            groups[key].append(t)

    rows = []
    for key, items in groups.items():
        latencies = [
            _num(t["total_ms"])
            for t in items
            if t["status"] == "success" and _num(t["total_ms"]) is not None
        ]
        token_rows = [t for t in items if t["input_tokens"] is not None or t["output_tokens"] is not None]
        ratings = [fb_map.get(t["trace_id"]) for t in items]
        rated = ratings.count("up") + ratings.count("down")
        rows.append(
            {
                "key": key,
                "requests": len(items),
                "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
                "tokens": (
                    sum((t["input_tokens"] or 0) + (t["output_tokens"] or 0) for t in token_rows)
                    if token_rows
                    else None
                ),
                "error_rate": sum(1 for t in items if t["status"] == "error") / len(items),
                "helpful_rate": (ratings.count("up") / rated) if rated else None,
            }
        )
    return sorted(rows, key=lambda r: r["requests"], reverse=True)


def model_table(traces, fb_map) -> list:
    return _group_table(traces, lambda t: t["model"] or None, fb_map)


def prompt_table(traces, fb_map) -> list:
    def key(t):
        if not t["prompt_name"] and not t["prompt_version"]:
            return None
        return f"{t['prompt_name'] or 'prompt'} {t['prompt_version'] or ''}".strip()

    return _group_table(traces, key, fb_map)


# =========================================================
# ERRORS / FEEDBACK / EVALUATIONS
# =========================================================


def error_groups(traces) -> list:
    counter = Counter(t["error_type"] or "Unknown" for t in traces if t["status"] == "error")
    return counter.most_common()


def evaluation_summary(evaluations) -> dict:
    human = [e for e in evaluations if e["kind"] == "human" and e["label"]]
    counts = Counter(e["label"] for e in human)
    total = len(human)

    judged = [e for e in evaluations if e["kind"] == "llm_judge"]
    overall = [
        _num(e["scores"].get("overall_score"))
        for e in judged
        if isinstance(e.get("scores"), dict) and _num(e["scores"].get("overall_score")) is not None
    ]

    return {
        "human_total": total,
        "human_counts": {label: counts.get(label, 0) for label in ("correct", "partial", "incorrect")},
        "human_pct": {
            label: (counts.get(label, 0) / total) if total else None
            for label in ("correct", "partial", "incorrect")
        },
        "judge_total": len(judged),
        "judge_avg_overall": (sum(overall) / len(overall)) if overall else None,
    }


def labels_vs_feedback(evaluations, fb_map) -> dict:
    """{'up': {label: n}, 'down': {label: n}} for human-labelled answers that also got feedback."""
    table = {"up": Counter(), "down": Counter()}
    for e in evaluations:
        if e["kind"] != "human" or not e["label"]:
            continue
        rating = fb_map.get(e["trace_id"])
        if rating in table:
            table[rating][e["label"]] += 1
    return table