import streamlit as st
import pandas as pd
from app.database.db import get_all_meetings, delete_meeting


def show():
    st.title("🗂️ Meeting History")
    st.markdown("All your past meetings in one place.")
    st.markdown("---")

    meetings = get_all_meetings()

    if not meetings:
        st.info("No meetings found. Upload your first meeting to get started.")
        return

    # --- Summary metrics ---
    total     = len(meetings)
    done      = sum(1 for m in meetings if m["status"] == "done")
    errors    = sum(1 for m in meetings if m["status"] == "error")
    pending   = sum(1 for m in meetings if m["status"] == "pending")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Meetings", total)
    col2.metric("Processed",      done)
    col3.metric("Errors",         errors)
    col4.metric("Pending",        pending)

    st.markdown("---")

    # --- Meetings table ---
    df = pd.DataFrame(meetings)

    # Clean up columns for display
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    df["duration"]   = df["duration"].apply(
        lambda x: f"{int(x//60)}m {int(x%60)}s" if x else "—"
    )

    # Status badge styling
    def style_status(val):
        colors = {
            "done":       "background-color: #d4edda; color: #155724",
            "error":      "background-color: #f8d7da; color: #721c24",
            "processing": "background-color: #fff3cd; color: #856404",
            "pending":    "background-color: #d1ecf1; color: #0c5460",
        }
        return colors.get(val, "")

    display_df = df[["id", "title", "filename", "duration", "status", "created_at"]]
    display_df.columns = ["ID", "Title", "File", "Duration", "Status", "Created At"]

    st.dataframe(
        display_df.style.applymap(style_status, subset=["Status"]),
        use_container_width=True,
        hide_index=True,
    )

    # --- Delete a meeting ---
    st.markdown("---")
    st.subheader("🗑️ Delete a Meeting")

    meeting_options = {f"[{m['id']}] {m['title']}": m["id"] for m in meetings}
    selected = st.selectbox("Select meeting to delete", list(meeting_options.keys()))

    if st.button("Delete Meeting", type="secondary", use_container_width=False):
        meeting_id = meeting_options[selected]
        delete_meeting(meeting_id)
        st.success(f"Deleted meeting: {selected}")
        st.rerun()