import streamlit as st

# Design tokens
#   page      #EEF1EF  pale sage-grey reading surface
#   surface   #FFFFFF  message + form cards
#   ink       #1B2623  body text
#   green     #16302A  sidebar + auth brand panel
#   oxblood   #8E2F3C  actions, citations, active states
# Type: Newsreader (serif) for headings + answers, Instrument Sans for UI.

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&display=swap');

:root {
    --page: #EEF1EF;
    --surface: #FFFFFF;
    --ink: #1B2623;
    --muted: #5B6862;
    --line: #D3DBD7;
    --green: #16302A;
    --green-hi: #1F3F37;
    --on-green: #DCE6E1;
    --on-green-muted: #9FB3AB;
    --oxblood: #8E2F3C;
    --oxblood-hi: #74232F;
    --rose: #E4A9B0;
}

/* ---------- Global ---------- */
html, body, [class*="css"] {
    font-family: "Instrument Sans", system-ui, sans-serif;
}
.stApp { background: var(--page); color: var(--ink); }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { background: transparent !important; }
.main .block-container {
    max-width: 960px;
    padding-top: 2rem;
    padding-bottom: 6rem;
}
:focus-visible { outline: 2px solid var(--oxblood) !important; outline-offset: 2px; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background: var(--green) !important;
}
section[data-testid="stSidebar"] .block-container { padding: 2rem 1.1rem; }
section[data-testid="stSidebar"] :is(p, label, span, small, li, h1, h2, h3) {
    color: var(--on-green);
}
.index-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--on-green-muted) !important;
    margin: 0.4rem 0 0.7rem 0;
}
section[data-testid="stSidebar"] button {
    width: 100%;
    background: transparent !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: var(--on-green) !important;
    border-radius: 8px !important;
    min-height: 40px;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] button:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: var(--rose) !important;
}
.session-card-active {
    background: rgba(255, 255, 255, 0.1);
    border-left: 3px solid var(--rose);
    color: #FFFFFF;
    padding: 0.65rem 0.8rem;
    margin-bottom: 0.45rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
    font-weight: 500;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px dashed rgba(255, 255, 255, 0.3) !important;
    border-radius: 10px;
}

/* ---------- Page header ---------- */
.masthead { padding: 0.2rem 0 1.2rem 0; }
.masthead-title {
    font-family: "Newsreader", Georgia, serif;
    font-size: 2.1rem;
    font-weight: 500;
    line-height: 1.15;
    letter-spacing: -0.01em;
    color: var(--ink);
    margin: 0;
}
.masthead-sub { color: var(--muted); font-size: 0.92rem; margin: 0.35rem 0 0 0; }
.masthead-sub b { color: var(--ink); font-weight: 600; }

.st-key-logout button {
    background: transparent !important;
    border: 1px solid var(--line) !important;
    color: var(--ink) !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    min-height: 38px;
}
.st-key-logout button:hover {
    border-color: var(--oxblood) !important;
    color: var(--oxblood) !important;
}

/* ---------- Chat ---------- */
div[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    margin-bottom: 0.9rem;
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: #E1E9E5 !important;
    border-color: #CBD7D1 !important;
}
div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
    font-family: "Newsreader", Georgia, serif;
    font-size: 1.08rem;
    line-height: 1.7;
    color: var(--ink);
    max-width: 68ch;
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
[data-testid="stMarkdownContainer"] p {
    font-family: "Instrument Sans", sans-serif;
    font-size: 0.97rem;
}

/* sources under an answer */
.sources {
    margin-top: 1rem;
    padding: 0.7rem 0.9rem;
    background: #F6F0F1;
    border-left: 3px solid var(--oxblood);
    border-radius: 0 8px 8px 0;
}
.sources-title { font-size: 0.8rem; font-weight: 600; color: var(--oxblood); margin-bottom: 0.3rem; }
.sources ul { margin: 0; padding-left: 1.1rem; }
.sources li { font-size: 0.85rem; line-height: 1.6; color: #4A3A3D; }
.sources-none { font-size: 0.83rem; color: var(--muted); background: transparent; border-left-color: var(--line); }

/* empty state */
.empty-state {
    margin-top: 1.5rem;
    padding: 1.6rem 1.8rem;
    background: var(--surface);
    border: 1px dashed #B5C2BC;
    border-radius: 12px;
}
.empty-state h3 {
    font-family: "Newsreader", Georgia, serif;
    font-weight: 500;
    font-size: 1.35rem;
    margin: 0 0 0.4rem 0;
    color: var(--ink);
}
.empty-state p { margin: 0; color: var(--muted); font-size: 0.93rem; line-height: 1.65; max-width: 56ch; }

/* chat input */
[data-testid="stBottom"] > div { background: var(--page) !important; }
div[data-testid="stChatInput"] > div {
    background: var(--surface) !important;
    border: 1px solid #B5C2BC !important;
    border-radius: 12px !important;
}
div[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--ink) !important;
    font-family: "Instrument Sans", sans-serif !important;
    font-size: 0.95rem !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: #7B8983 !important; }

/* ---------- Auth screen ---------- */
.auth-brand {
    background: var(--green);
    color: var(--on-green);
    border-radius: 18px;
    padding: 3rem 2.6rem;
    min-height: 480px;
}
.auth-product { font-size: 0.9rem; font-weight: 600; color: var(--rose); margin: 0 0 1.6rem 0; }
.auth-title {
    font-family: "Newsreader", Georgia, serif;
    font-size: 3rem;
    font-weight: 500;
    line-height: 1.1;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    margin: 0 0 1.3rem 0;
    padding: 0;
}
.auth-description { color: var(--on-green); font-size: 0.97rem; line-height: 1.75; margin: 0; max-width: 42ch; }
.auth-description strong { color: #FFFFFF; font-weight: 600; }
.auth-points { list-style: none; margin: 2rem 0 0 0; padding: 0; }
.auth-points li {
    padding: 0.7rem 0 0.7rem 0.9rem;
    border-left: 2px solid rgba(228, 169, 176, 0.55);
    margin-bottom: 0.6rem;
    font-size: 0.86rem;
    line-height: 1.5;
    color: var(--on-green-muted);
}
.auth-points li b { color: #FFFFFF; font-weight: 600; }

.st-key-auth_card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 2rem 2rem 1.6rem 2rem;
    box-shadow: 0 12px 40px rgba(22, 48, 42, 0.08);
}
.auth-card-title {
    font-family: "Newsreader", Georgia, serif;
    font-size: 1.6rem;
    font-weight: 500;
    color: var(--ink);
    margin-bottom: 0.25rem;
}
.auth-card-subtitle { color: var(--muted); font-size: 0.88rem; margin-bottom: 1rem; }
.form-intro { color: var(--muted); font-size: 0.86rem; line-height: 1.6; margin: 0.6rem 0 0.4rem 0; }

.st-key-auth_card div[data-testid="stTabs"] button { color: var(--muted) !important; font-size: 0.88rem !important; font-weight: 500 !important; }
.st-key-auth_card div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--oxblood) !important; }
.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--oxblood) !important; }

[data-testid="stTextInput"] label { color: var(--ink) !important; font-size: 0.82rem !important; font-weight: 500 !important; }
[data-testid="stTextInput"] input {
    background: #F7F9F8 !important;
    color: var(--ink) !important;
    border: 1px solid #C3CFC9 !important;
    border-radius: 8px !important;
    min-height: 44px !important;
    font-size: 0.92rem !important;
}
[data-testid="stTextInput"] input::placeholder { color: #85928C !important; }
[data-testid="stTextInput"] input:focus {
    border-color: var(--oxblood) !important;
    box-shadow: 0 0 0 1px var(--oxblood) !important;
}

.st-key-auth_card button {
    background: var(--oxblood) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    min-height: 44px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}
.st-key-auth_card button:hover { background: var(--oxblood-hi) !important; }

.stAlert { border-radius: 8px !important; }

/* ---------- Small screens ---------- */
@media (max-width: 900px) {
    .auth-brand { padding: 2rem 1.5rem; min-height: 0; margin-bottom: 1rem; }
    .auth-title { font-size: 2.3rem; }
    .st-key-auth_card { padding: 1.4rem 1.2rem; }
}

@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}
</style>
"""


def inject_custom_css():
    st.markdown(_CSS, unsafe_allow_html=True)