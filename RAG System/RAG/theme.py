import streamlit as st


def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background-color: #0D1117;
        }

        /* ---------- Sidebar (the "Index") ---------- */
        section[data-testid="stSidebar"] {
            background-color: #0A0C11;
            border-right: 1px solid #1F2430;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.75rem;
        }

        .index-label {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            color: #6B7389;
            letter-spacing: 0.02em;
            margin-bottom: 10px;
        }

        section[data-testid="stSidebar"] button {
            background-color: transparent !important;
            border: 1px solid #1F2430 !important;
            color: #B7BECF !important;
            border-radius: 6px !important;
            text-align: left !important;
            font-size: 0.86rem !important;
            padding: 0.4rem 0.7rem !important;
            transition: border-color 0.15s ease, color 0.15s ease;
        }
        section[data-testid="stSidebar"] button:hover {
            border-color: #C9A463 !important;
            color: #EFE4C8 !important;
        }

        .session-card-active {
            border-left: 2px solid #C9A463;
            background-color: #161B22;
            color: #EFE4C8;
            padding: 0.5rem 0.7rem;
            margin-bottom: 0.35rem;
            border-radius: 0 6px 6px 0;
            font-size: 0.86rem;
        }

        section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
            background-color: #0F1319;
            border: 1px dashed #2A3141;
            border-radius: 8px;
            padding: 0.4rem;
        }

        /* ---------- Header ---------- */
        .masthead {
            border-bottom: 1px solid #1F2430;
            padding-bottom: 18px;
            margin-bottom: 22px;
        }
        .masthead-title {
            font-family: 'Source Serif 4', serif;
            font-weight: 600;
            font-size: 2.1rem;
            color: #EDEFF4;
            margin: 0;
        }
        .masthead-title span {
            color: #C9A463;
        }
        .masthead-sub {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.78rem;
            color: #6B7389;
            margin-top: 4px;
        }

        .user-strip {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 2px 20px 2px;
        }
        .user-strip-text {
            font-size: 0.86rem;
            color: #8891A7;
        }
        .user-strip-text b {
            color: #C9A463;
            font-weight: 500;
        }

        /* ---------- Chat transcript ---------- */
        div[data-testid="stChatMessage"] {
            background-color: #12161D;
            border: 1px solid #1F2430;
            border-radius: 8px;
        }
        div[data-testid="stChatMessage"]:has(img[alt="user avatar"]) {
            border-left: 2px solid #7C88A8;
        }
        div[data-testid="stChatMessage"]:has(img[alt="assistant avatar"]) {
            border-left: 2px solid #C9A463;
        }

        div[data-testid="stChatInput"] textarea {
            background-color: #12161D !important;
            border: 1px solid #1F2430 !important;
            font-family: 'Inter', sans-serif !important;
        }

        .citation-strip {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.76rem;
            color: #8891A7;
            border-top: 1px solid #262C3A;
            margin-top: 10px;
            padding-top: 8px;
            line-height: 1.7;
        }
        .citation-strip .no-cite {
            color: #5C6479;
            font-style: italic;
        }

        /* ---------- Auth screen ---------- */
        .auth-brand {
            padding: 48px 32px;
            height: 100%;
        }
        .auth-brand-title {
            font-family: 'Source Serif 4', serif;
            font-size: 2.6rem;
            font-weight: 600;
            color: #EDEFF4;
            line-height: 1.15;
            margin: 0 0 14px 0;
        }
        .auth-brand-title span { color: #C9A463; }
        .auth-brand-body {
            color: #8891A7;
            font-size: 0.95rem;
            line-height: 1.65;
            max-width: 340px;
        }
        .auth-panel {
            background-color: #12161D;
            border: 1px solid #1F2430;
            border-radius: 10px;
            padding: 32px 30px;
        }

        [data-testid="stTextInput"] input {
            background-color: #0F1319 !important;
            border: 1px solid #2A3141 !important;
            color: #E8EAF0 !important;
        }

        .stButton button[kind="primary"],
        div[data-testid="stTabs"] + div .stButton button {
            background-color: #C9A463 !important;
            color: #0D1117 !important;
            border: none !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)