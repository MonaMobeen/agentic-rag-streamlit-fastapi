import streamlit as st


def inject_custom_css():
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #0f1117 0%, #161a23 100%);
        }

        section[data-testid="stSidebar"] {
            background-color: #12141c;
            border-right: 1px solid #262b3a;
        }

        .app-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 4px 0 18px 0;
        }
        .app-header h1 {
            font-size: 1.8rem;
            margin: 0;
            background: linear-gradient(90deg, #8b7cf6, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .app-subtitle {
            color: #8b8fa3;
            font-size: 0.9rem;
            margin-top: -10px;
        }

        .session-btn button {
            width: 100%;
            text-align: left !important;
            background-color: transparent !important;
            border: 1px solid #262b3a !important;
            color: #c9cdda !important;
            border-radius: 8px !important;
            margin-bottom: 4px;
        }
        .session-btn button:hover {
            border-color: #6366f1 !important;
            color: #ffffff !important;
        }
        .session-active {
            background: linear-gradient(90deg, #6366f1, #8b7cf6) !important;
            color: white !important;
            border-radius: 8px;
            padding: 10px 12px;
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 0.9rem;
        }

        div[data-testid="stChatMessage"] {
            border-radius: 12px;
            padding: 4px 6px;
        }

        .welcome-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #1a1d29;
            border: 1px solid #262b3a;
            border-radius: 10px;
            padding: 10px 16px;
            margin-bottom: 18px;
        }

        .auth-card {
            max-width: 420px;
            margin: 40px auto 0 auto;
            padding: 28px;
            background-color: #161a23;
            border: 1px solid #262b3a;
            border-radius: 14px;
        }

        div[data-testid="stChatInput"] textarea {
            background-color: #1a1d29 !important;
        }
    </style>
    """, unsafe_allow_html=True)