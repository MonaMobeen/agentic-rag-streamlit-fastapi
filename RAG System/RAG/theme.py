import streamlit as st

# =========================================================
# THEME STATE
# =========================================================

LOGO_SVG = (
    '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5C4.7 19 4 18.3 4 17.5z"/>'
    '<path d="M20 5.5C20 4.7 19.3 4 18.5 4H13v15h5.5c.8 0 1.5-.7 1.5-1.5z"/>'
    "</svg>"
)

# Both palettes are designed on their own (not inverted).
# Dark: near-black green surfaces, soft rose accent text.
# Light: cool sage page, white surfaces, deep oxblood accent.
PALETTES = {
    "dark": {
        "scheme": "dark",
        "bg": "#0F1614",
        "surface": "#151F1C",
        "surface_hi": "#1B2823",
        "line": "#26352F",
        "ink": "#E7EEEA",
        "muted": "#94A89F",
        "accent": "#B9414F",
        "accent_hi": "#CF5361",
        "accent_text": "#F0A6AE",
        "accent_soft": "rgba(185, 65, 79, 0.16)",
        "on_accent": "#FFFFFF",
        "sb_bg": "#0A100E",
        "sb_ink": "#D5E0DA",
        "sb_muted": "#8DA399",
        "sb_line": "rgba(255, 255, 255, 0.10)",
        "code_bg": "#0B1210",
        "user_bubble": "#1B2823",
        "success": "#5FC49A",
        "warn": "#E0B15C",
        "danger": "#F08A8A",
        "shadow": "0 12px 40px rgba(0, 0, 0, 0.35)",
    },
    "light": {
        "scheme": "light",
        "bg": "#F3F5F4",
        "surface": "#FFFFFF",
        "surface_hi": "#F7F9F8",
        "line": "#DAE1DD",
        "ink": "#18221F",
        "muted": "#5D6B65",
        "accent": "#8E2F3C",
        "accent_hi": "#74232F",
        "accent_text": "#8E2F3C",
        "accent_soft": "rgba(142, 47, 60, 0.09)",
        "on_accent": "#FFFFFF",
        "sb_bg": "#16302A",
        "sb_ink": "#DCE6E1",
        "sb_muted": "#9FB3AB",
        "sb_line": "rgba(255, 255, 255, 0.16)",
        "code_bg": "#EDF1EF",
        "user_bubble": "#E6ECE9",
        "success": "#1F7A5A",
        "warn": "#8A6414",
        "danger": "#B3261E",
        "shadow": "0 12px 40px rgba(22, 48, 42, 0.10)",
    },
}


def get_theme() -> str:
    return st.session_state.get("ui_theme", "dark")


def get_palette() -> dict:
    return PALETTES.get(get_theme(), PALETTES["dark"])


def toggle_theme():
    """Button callback: runs before the next rerun, so CSS updates at once."""
    st.session_state.ui_theme = "light" if get_theme() == "dark" else "dark"


# =========================================================
# CSS
# =========================================================

_FONTS = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Instrument+Sans:wght@400;500;600&"
    "family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap');"
)

_STATIC_CSS = """
/* ---------- Global ---------- */
html, body, [class*="css"] {
    font-family: "Instrument Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
}
.stApp { background: var(--bg); color: var(--ink); }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stDecoration"],
[data-testid="stAppDeployButton"],
#MainMenu,
footer { display: none !important; }

[data-testid="stMainBlockContainer"],
.main .block-container {
    max-width: 820px;
    padding: 1.4rem 1.25rem 7rem 1.25rem;
}

.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stWidgetLabel"] p,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--ink); }
.stApp [data-testid="stCaptionContainer"] { color: var(--muted); }

:focus-visible { outline: 2px solid var(--accent-text) !important; outline-offset: 2px; }

button { transition: background-color .12s ease-out, border-color .12s ease-out,
                     color .12s ease-out, transform .12s ease-out; }
button:active { transform: scale(0.98); }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div { background: var(--sb-bg) !important; }
section[data-testid="stSidebar"] { border-right: 1px solid var(--sb-line); }
section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 1.6rem 1rem; }
section[data-testid="stSidebar"] :is(p, label, span, small, li, h1, h2, h3) { color: var(--sb-ink); }

.index-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--sb-muted) !important;
    margin: 0.5rem 0 0.6rem 0;
}
section[data-testid="stSidebar"] button {
    width: 100%;
    background: transparent !important;
    border: 1px solid var(--sb-line) !important;
    color: var(--sb-ink) !important;
    border-radius: 10px !important;
    min-height: 40px;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    justify-content: flex-start;
}
section[data-testid="stSidebar"] button:hover {
    background: rgba(255, 255, 255, 0.07) !important;
    border-color: #E4A9B0 !important;
}
section[data-testid="stSidebar"] button[kind="primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: var(--on-accent) !important;
    justify-content: center;
}
section[data-testid="stSidebar"] button[kind="primary"]:hover { background: var(--accent-hi) !important; }
.session-card-active {
    background: rgba(255, 255, 255, 0.09);
    border-left: 3px solid #E4A9B0;
    color: #FFFFFF;
    padding: 0.62rem 0.8rem;
    margin-bottom: 0.4rem;
    border-radius: 0 10px 10px 0;
    font-size: 0.85rem;
    font-weight: 500;
}
section[data-testid="stSidebar"] [data-baseweb="input"],
section[data-testid="stSidebar"] [data-baseweb="base-input"] {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid var(--sb-line) !important;
}
section[data-testid="stSidebar"] input { color: var(--sb-ink) !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px dashed rgba(255, 255, 255, 0.28) !important;
    border-radius: 12px;
    transition: border-color .15s ease-out, background-color .15s ease-out;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
    border-color: #E4A9B0 !important;
    background: rgba(255, 255, 255, 0.08) !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.05);
    padding: 0.2rem 0.4rem;
    margin-top: 0.3rem;
}
section[data-testid="stSidebar"] [data-testid="stAlert"] * { color: var(--ink) !important; }

/* sidebar: session rows, popover menu, document cards */
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] { gap: 0.35rem; align-items: center; }
section[data-testid="stSidebar"] [data-testid="stPopover"] button { justify-content: center; padding: 0; }
[data-testid="stPopoverBody"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    color: var(--ink);
}
[data-testid="stPopoverBody"] :is(p, label, span) { color: var(--ink); }
[data-testid="stPopoverBody"] button {
    background: transparent !important;
    border: 1px solid var(--line) !important;
    color: var(--ink) !important;
    border-radius: 8px !important;
    min-height: 36px;
}
[data-testid="stPopoverBody"] button:hover {
    border-color: var(--accent) !important;
    color: var(--accent-text) !important;
}
[class*="st-key-delete_"] button:hover {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
}
.doc-summary { font-size: 0.78rem; color: var(--sb-muted); margin: 0.7rem 0 0.4rem 0; }
.doc-card {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.5rem 0.6rem; margin-bottom: 0.4rem;
    border: 1px solid var(--sb-line); border-radius: 10px;
    background: rgba(255, 255, 255, 0.04);
}
.doc-badge {
    flex: none; width: 30px; height: 30px; border-radius: 8px;
    display: grid; place-items: center;
    font-size: 0.62rem; font-weight: 600;
    background: rgba(255, 255, 255, 0.1); color: var(--sb-ink);
}
.doc-body { min-width: 0; flex: 1; }
.doc-name {
    font-size: 0.82rem; font-weight: 500; color: var(--sb-ink);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.doc-meta { font-size: 0.72rem; color: var(--sb-muted); }
.doc-pill {
    flex: none; font-size: 0.68rem; font-weight: 600;
    padding: 0.12rem 0.5rem; border-radius: 999px;
    border: 1px solid var(--sb-line); color: var(--sb-muted);
}
.doc-pill.ok { color: #7FD9B3; border-color: rgba(127, 217, 179, 0.45); }

/* ---------- Top bar ---------- */
.topbar { display: flex; align-items: center; gap: 0.7rem; flex-wrap: wrap; }
.brand-mark {
    width: 34px; height: 34px; flex: none;
    border-radius: 10px;
    background: var(--accent);
    color: var(--on-accent);
    display: grid; place-items: center;
}
.brand-mark-lg { width: 48px; height: 48px; border-radius: 14px; margin: 0 auto 1rem auto; }
.brand-name {
    font-family: "Newsreader", Georgia, serif;
    font-size: 1.28rem; font-weight: 500; line-height: 1.2;
    letter-spacing: -0.01em; color: var(--ink);
}
.status-pill, .user-chip {
    display: inline-flex; align-items: center; gap: 0.4rem;
    font-size: 0.76rem; font-weight: 500;
    padding: 0.22rem 0.62rem;
    border-radius: 999px;
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--muted);
}
.status-pill i { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); }
.status-pill.ok { color: var(--success); }
.status-pill.ok i { background: var(--success); }
.user-chip b {
    width: 18px; height: 18px; border-radius: 50%;
    background: var(--accent-soft); color: var(--accent-text);
    display: grid; place-items: center; font-size: 0.68rem; font-weight: 600;
}

.st-key-theme_btn button,
.st-key-logout button {
    background: transparent !important;
    border: 1px solid var(--line) !important;
    color: var(--ink) !important;
    border-radius: 10px !important;
    min-height: 36px;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}
.st-key-theme_btn button:hover,
.st-key-logout button:hover {
    border-color: var(--accent) !important;
    color: var(--accent-text) !important;
}

/* ---------- Chat messages ---------- */
@keyframes rise {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: none; }
}
div[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.6rem 0 !important;
    gap: 0.85rem;
    animation: rise .2s ease-out both;
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: var(--user-bubble) !important;
    border-radius: 16px !important;
    padding: 0.75rem 1rem !important;
    margin: 0.7rem 0;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background: var(--accent) !important;
    color: var(--on-accent) !important;
    border-radius: 10px !important;
}
[data-testid="stChatMessageAvatarUser"] {
    background: var(--surface-hi) !important;
    color: var(--ink) !important;
    border-radius: 10px !important;
}
div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] :is(p, li) {
    font-family: "Newsreader", Georgia, serif;
    font-size: 1.06rem;
    line-height: 1.7;
    color: var(--ink);
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
[data-testid="stMarkdownContainer"] p {
    font-family: "Instrument Sans", sans-serif;
    font-size: 0.97rem;
    line-height: 1.6;
}

/* markdown content: tables, code */
[data-testid="stMarkdownContainer"] table {
    display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse;
}
[data-testid="stMarkdownContainer"] :is(th, td) {
    border: 1px solid var(--line); padding: 0.4rem 0.7rem; color: var(--ink);
    font-family: "Instrument Sans", sans-serif; font-size: 0.9rem;
}
[data-testid="stMarkdownContainer"] th { background: var(--surface-hi); }
[data-testid="stCode"], [data-testid="stCode"] pre {
    background: var(--code-bg) !important;
    border-radius: 10px;
    max-width: 100%;
    overflow-x: auto;
}
[data-testid="stCode"] :is(code, span) { color: var(--ink) !important; }
[data-testid="stMarkdownContainer"] :not(pre) > code {
    background: var(--code-bg); color: var(--accent-text);
    padding: 0.1em 0.38em; border-radius: 5px; font-size: 0.86em;
}

/* answer meta + sources */
.meta-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.75rem 0 0.2rem 0; }
.chip {
    display: inline-flex; align-items: center; gap: 0.35rem;
    font-family: "Instrument Sans", sans-serif;
    font-size: 0.74rem; font-weight: 500;
    padding: 0.18rem 0.55rem;
    border-radius: 999px;
    border: 1px solid var(--line);
    color: var(--muted);
}
.chip i { width: 6px; height: 6px; border-radius: 50%; background: var(--muted); }
.chip.ok { color: var(--success); }
.chip.ok i { background: var(--success); }

details.sources {
    margin-top: 0.55rem;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--surface);
    overflow: hidden;
}
details.sources summary {
    cursor: pointer; list-style: none;
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.55rem 0.8rem;
    font-family: "Instrument Sans", sans-serif;
    font-size: 0.82rem; font-weight: 600;
    color: var(--accent-text);
}
details.sources summary::-webkit-details-marker { display: none; }
details.sources summary::after {
    content: ""; margin-left: auto;
    width: 7px; height: 7px;
    border-right: 1.5px solid currentColor; border-bottom: 1.5px solid currentColor;
    transform: rotate(45deg);
    transition: transform .15s ease-out;
}
details.sources[open] summary::after { transform: rotate(-135deg); }
details.sources ol { list-style: none; margin: 0; padding: 0 0.8rem 0.55rem 0.8rem; }
details.sources li {
    display: flex; gap: 0.6rem; align-items: flex-start;
    padding: 0.4rem 0;
    border-top: 1px solid var(--line);
}
.src-n {
    flex: none; width: 20px; height: 20px; border-radius: 6px;
    background: var(--accent-soft); color: var(--accent-text);
    display: grid; place-items: center;
    font-family: "Instrument Sans", sans-serif; font-size: 0.72rem; font-weight: 600;
}
.src-t {
    font-family: "Instrument Sans", sans-serif;
    font-size: 0.85rem; line-height: 1.5; color: var(--ink); word-break: break-word;
}

/* response actions (copy / regenerate) */
[class*="st-key-actions_"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important; gap: 0.4rem !important; align-items: center;
}
[class*="st-key-actions_"] [data-testid="stColumn"],
[class*="st-key-actions_"] [data-testid="column"] {
    flex: 0 0 auto !important; width: auto !important; min-width: 0 !important;
}
[class*="st-key-actions_"] button {
    background: transparent !important;
    border: 1px solid var(--line) !important;
    color: var(--muted) !important;
    border-radius: 8px !important;
    min-height: 32px !important;
    padding: 0 0.75rem !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}
[class*="st-key-actions_"] button:hover {
    color: var(--ink) !important;
    border-color: var(--muted) !important;
}

/* loading + errors */
.agent-working {
    display: flex; align-items: center; gap: 0.7rem;
    color: var(--muted); font-size: 0.92rem; padding: 0.3rem 0;
}
.dots { display: inline-flex; gap: 4px; }
.dots i {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--accent-text);
    animation: pulse 1.1s ease-in-out infinite;
}
.dots i:nth-child(2) { animation-delay: .15s; }
.dots i:nth-child(3) { animation-delay: .3s; }
@keyframes pulse {
    0%, 80%, 100% { opacity: .25; transform: scale(.85); }
    40% { opacity: 1; transform: scale(1); }
}
.error-card {
    border: 1px solid color-mix(in srgb, var(--danger) 45%, transparent);
    background: color-mix(in srgb, var(--danger) 8%, transparent);
    border-radius: 12px;
    padding: 0.8rem 1rem;
    color: var(--ink);
    font-family: "Instrument Sans", sans-serif;
    font-size: 0.93rem; line-height: 1.55;
}
.error-card b { color: var(--danger); }
[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    background: var(--surface);
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * { color: var(--muted) !important; font-size: 0.82rem; }

/* ---------- Empty state ---------- */
.empty-state { text-align: center; padding: 3rem 0 1.4rem 0; }
.empty-mark {
    width: 52px; height: 52px; margin: 0 auto 1.1rem auto;
    border-radius: 16px; background: var(--accent); color: var(--on-accent);
    display: grid; place-items: center;
}
.empty-state h2 {
    font-family: "Newsreader", Georgia, serif;
    font-size: 2rem; font-weight: 500; line-height: 1.15;
    letter-spacing: -0.015em; margin: 0 0 0.6rem 0; padding: 0;
    color: var(--ink);
}
.empty-state p {
    max-width: 50ch; margin: 0 auto;
    color: var(--muted); font-size: 0.97rem; line-height: 1.65;
}
.empty-steps {
    list-style: none; counter-reset: step;
    display: flex; justify-content: center; flex-wrap: wrap; gap: 0.7rem;
    margin: 1.6rem 0 0 0; padding: 0;
}
.empty-steps li {
    counter-increment: step;
    display: flex; align-items: center; gap: 0.55rem;
    padding: 0.5rem 0.85rem;
    border: 1px solid var(--line); border-radius: 12px;
    background: var(--surface);
    color: var(--muted); font-size: 0.85rem;
}
.empty-steps li::before {
    content: counter(step);
    width: 20px; height: 20px; border-radius: 6px;
    background: var(--accent-soft); color: var(--accent-text);
    display: grid; place-items: center; font-size: 0.72rem; font-weight: 600;
}
.empty-steps li b { color: var(--ink); font-weight: 600; }
.suggest-label { color: var(--muted); font-size: 0.8rem; font-weight: 500; margin: 1.6rem 0 0.5rem 0; }

.st-key-suggestions button {
    min-height: 64px; height: 100%;
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    color: var(--ink) !important;
    border-radius: 14px !important;
    padding: 0.85rem 1rem !important;
    justify-content: flex-start !important;
    font-weight: 500 !important;
}
.st-key-suggestions button p { text-align: left; }
.st-key-suggestions button:hover {
    border-color: var(--accent) !important;
    background: var(--surface-hi) !important;
    transform: translateY(-1px);
}

/* ---------- Chat input ---------- */
[data-testid="stBottom"] {
    background: linear-gradient(to top, var(--bg) 72%, transparent) !important;
}
[data-testid="stBottom"] > div { background: transparent !important; }
[data-testid="stBottomBlockContainer"] { max-width: 820px; }
div[data-testid="stChatInput"] { background: transparent !important; }
div[data-testid="stChatInput"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    box-shadow: var(--shadow);
    transition: border-color .15s ease-out, box-shadow .15s ease-out;
}
div[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft), var(--shadow);
}
div[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--ink) !important;
    font-family: "Instrument Sans", sans-serif !important;
    font-size: 0.95rem !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; opacity: 1; }
div[data-testid="stChatInput"] textarea:disabled { cursor: not-allowed; }
[data-testid="stChatInputSubmitButton"] {
    background: var(--accent) !important;
    color: var(--on-accent) !important;
    border-radius: 10px !important;
}
[data-testid="stChatInputSubmitButton"]:hover { background: var(--accent-hi) !important; }
[data-testid="stChatInputSubmitButton"]:disabled { opacity: .4; }

/* ---------- Auth ---------- */
.stApp:has(.st-key-auth_card) {
    background:
        radial-gradient(900px 420px at 50% -8%, var(--accent-soft), transparent 70%),
        var(--bg);
}
[data-testid="stMainBlockContainer"]:has(.st-key-auth_card),
.main .block-container:has(.st-key-auth_card) { padding-top: 6vh; }

.auth-brand { text-align: center; margin-bottom: 1.4rem; }
.auth-title {
    font-family: "Newsreader", Georgia, serif;
    font-size: 2.3rem; font-weight: 500; line-height: 1.12;
    letter-spacing: -0.02em; color: var(--ink); margin: 0 0 0.5rem 0; padding: 0;
}
.auth-sub { color: var(--muted); font-size: 0.95rem; line-height: 1.6; margin: 0 auto; max-width: 38ch; }

.st-key-auth_card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.6rem 1.6rem 1.3rem 1.6rem;
    box-shadow: var(--shadow);
}
.auth-note { color: var(--muted); font-size: 0.84rem; line-height: 1.55; margin: 0.4rem 0 0.2rem 0; }
.st-key-auth_card button[role="tab"] { color: var(--muted) !important; font-size: 0.88rem !important; font-weight: 500 !important; }
.st-key-auth_card button[role="tab"][aria-selected="true"] { color: var(--accent-text) !important; }
.st-key-auth_card [data-baseweb="tab-highlight"] { background-color: var(--accent) !important; }
.st-key-auth_card [data-baseweb="tab-border"] { background-color: var(--line) !important; }
.st-key-auth_card [data-testid="stFormSubmitButton"] button {
    background: var(--accent) !important;
    color: var(--on-accent) !important;
    border: none !important;
    border-radius: 10px !important;
    min-height: 44px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}
.st-key-auth_card [data-testid="stFormSubmitButton"] button:hover { background: var(--accent-hi) !important; }
.st-key-auth_card [data-testid="stFormSubmitButton"] button p { color: var(--on-accent) !important; }

[data-testid="stTextInput"] label p { color: var(--ink) !important; font-size: 0.82rem !important; font-weight: 500 !important; }
[data-baseweb="input"], [data-baseweb="base-input"] {
    background: var(--surface-hi) !important;
    border-radius: 10px !important;
}
[data-baseweb="input"] {
    border: 1px solid var(--line) !important;
    transition: border-color .15s ease-out, box-shadow .15s ease-out;
}
[data-baseweb="input"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
[data-baseweb="input"] input {
    background: transparent !important;
    color: var(--ink) !important;
    min-height: 42px;
    font-size: 0.92rem !important;
}
[data-baseweb="input"] input::placeholder { color: var(--muted) !important; opacity: 1; }
[data-baseweb="input"] button { color: var(--muted) !important; background: transparent !important; }

[data-testid="stAlert"] {
    border-radius: 10px !important;
    background: var(--surface-hi) !important;
    border: 1px solid var(--line) !important;
}
[data-testid="stAlert"] * { color: var(--ink) !important; }

/* ---------- Responsive ---------- */
@media (max-width: 900px) {
    .empty-state h2 { font-size: 1.6rem; }
    .auth-title { font-size: 1.9rem; }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"],
    .main .block-container { padding: 1rem 0.8rem 7rem 0.8rem; }
    .st-key-auth_card { padding: 1.2rem 1rem; }
    .empty-state { padding-top: 1.6rem; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
}
"""


def _root_vars(palette: dict) -> str:
    items = "".join(
        f"--{key.replace('_', '-')}:{value};"
        for key, value in palette.items()
        if key != "scheme"
    )
    return f":root{{{items}color-scheme:{palette['scheme']};}}"


def inject_custom_css():
    palette = get_palette()
    st.markdown(
        f"<style>{_FONTS}{_root_vars(palette)}{_STATIC_CSS}</style>",
        unsafe_allow_html=True,
    )