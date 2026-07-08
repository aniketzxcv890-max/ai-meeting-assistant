import streamlit as st
from app.database.db import init_db
from app.core.config import config

st.set_page_config(
    page_title="AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Initialize database ---
init_db()

# --- Validate environment on startup ---
errors = config.validate()
if errors:
    st.error("⚠️ Configuration Error — check your `.env` file:")
    for err in errors:
        st.error(f"• {err}")
    st.stop()

# --- Sidebar navigation ---
st.sidebar.title("🎙️ AI Meeting Assistant")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    options=["Upload Meeting", "View Results", "Meeting History"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption("Built with Whisper + Gemini 2.5 Flash")

# --- Route to correct page ---
if page == "Upload Meeting":
    from app.ui.upload_page import show
    show()
elif page == "View Results":
    from app.ui.results_page import show
    show()
elif page == "Meeting History":
    from app.ui.history_page import show
    show()