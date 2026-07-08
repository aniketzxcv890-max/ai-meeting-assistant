import streamlit as st
import os
import tempfile
from app.core.transcriber import MeetingTranscriber
from app.core.analyzer import MeetingAnalyzer
from app.database.db import (
    create_meeting,
    update_meeting_status,
    save_results,
    save_segments,
)


def show():
    st.title("🎙️ Upload Meeting Audio")
    st.markdown("Upload your meeting recording and let AI do the rest.")
    st.markdown("---")

    # --- Meeting title input ---
    title = st.text_input(
        "Meeting Title",
        placeholder="e.g. Q3 Planning Meeting",
        help="Give your meeting a descriptive name",
    )

    # --- File uploader ---
    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav", "m4a", "mp4", "ogg", "flac"],
        help="Supported formats: MP3, WAV, M4A, MP4, OGG, FLAC",
    )

    # --- Model size selector ---
    st.markdown("#### ⚙️ Whisper Settings")
    model_size = st.select_slider(
        "Transcription Model Size",
        options=["tiny", "base", "small", "medium"],
        value="base",
        help="Larger = more accurate but slower. 'base' is recommended.",
    )

    st.markdown("---")

    # --- Process button ---
    if st.button("🚀 Process Meeting", type="primary", use_container_width=True):

        # Validate inputs
        if not title.strip():
            st.error("Please enter a meeting title.")
            return

        if uploaded_file is None:
            st.error("Please upload an audio file.")
            return

        _process_meeting(title.strip(), uploaded_file, model_size)


def _process_meeting(title: str, uploaded_file, model_size: str):
    """Handle the full processing pipeline with live status updates."""

    # --- Save uploaded file to disk temporarily ---
    uploads_dir = os.path.join("data", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    file_path = os.path.join(uploads_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # --- Create meeting record in DB ---
    meeting_id = create_meeting(title=title, filename=uploaded_file.name)

    # --- Progress display ---
    st.markdown("### ⏳ Processing...")
    progress = st.progress(0)
    status_box = st.empty()   # placeholder we update in real time

    try:
        # STEP 1: Transcription
        status_box.info("🎤 Step 1/3 — Transcribing audio with Whisper...")
        update_meeting_status(meeting_id, "processing")
        progress.progress(10)

        transcriber = MeetingTranscriber(model_size=model_size)
        result = transcriber.transcribe(file_path)
        segments = transcriber.get_readable_segments(result)

        progress.progress(40)

        # STEP 2: Save segments
        status_box.info("💾 Saving transcript segments...")
        save_segments(meeting_id, segments)
        progress.progress(50)

        # STEP 3: LLM Analysis
        status_box.info("🤖 Step 2/3 — Analyzing with Gemini 2.5 Flash...")
        analyzer = MeetingAnalyzer()
        analysis = analyzer.analyze(result.full_text)
        progress.progress(85)

        # STEP 4: Save results
        status_box.info("💾 Step 3/3 — Saving results to database...")
        save_results(
            meeting_id=meeting_id,
            transcript=result.full_text,
            summary=analysis.summary,
            action_items=analysis.action_items,
            key_decisions=analysis.key_decisions,
            model_used=analysis.model_used,
        )
        update_meeting_status(meeting_id, "done", duration=result.duration)
        progress.progress(100)

        # SUCCESS
        status_box.success("✅ Meeting processed successfully!")
        st.balloons()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Duration", f"{result.duration:.0f} sec")
        with col2:
            st.metric("Segments", len(segments))

        st.info(
            f"📋 Meeting saved with ID **{meeting_id}**. "
            f"Go to **View Results** in the sidebar to see the full analysis."
        )

    except Exception as e:
        update_meeting_status(meeting_id, "error")
        progress.progress(0)
        status_box.error(f"❌ Processing failed: {str(e)}")
        st.exception(e)   # shows full traceback for debugging