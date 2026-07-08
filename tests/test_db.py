import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.db import (
    init_db,
    create_meeting,
    update_meeting_status,
    save_results,
    save_segments,
    get_all_meetings,
    get_results,
    get_segments,
    delete_meeting,
    get_meeting_by_id,
)


def test_full_pipeline():
    """Simulate the full save → retrieve cycle for one meeting."""

    print("Initializing database...")
    init_db()

    # --- Step 1: Create a meeting ---
    meeting_id = create_meeting(
        title="Q3 Planning Meeting",
        filename="q3_planning.mp3"
    )
    print(f"Created meeting with ID: {meeting_id}")

    # --- Step 2: Update status to processing ---
    update_meeting_status(meeting_id, "processing")

    # --- Step 3: Save fake segments ---
    fake_segments = [
        {"start_time": 0.0,  "end_time": 4.5,  "text": "Good morning everyone."},
        {"start_time": 4.5,  "end_time": 10.2, "text": "John will submit the report by Friday."},
        {"start_time": 10.2, "end_time": 18.0, "text": "We decided to postpone the launch."},
    ]
    save_segments(meeting_id, fake_segments)
    print(f"Saved {len(fake_segments)} segments")

    # --- Step 4: Save fake analysis results ---
    save_results(
        meeting_id=meeting_id,
        transcript="Good morning everyone. John will submit the report by Friday. We decided to postpone the launch.",
        summary="The team discussed Q3 planning and assigned key tasks.",
        action_items=[
            {"task": "Submit report", "assignee": "John", "deadline": "Friday"}
        ],
        key_decisions=["Postpone product launch to Q4."],
        model_used="gemini-2.5-flash",
    )
    print("Saved analysis results")

    # --- Step 5: Mark meeting as done ---
    update_meeting_status(meeting_id, "done", duration=18.0)

    # --- Step 6: Retrieve and verify ---
    print("\n" + "="*50)
    print("RETRIEVED DATA")
    print("="*50)

    meeting = get_meeting_by_id(meeting_id)
    print(f"Meeting  : {meeting['title']}")
    print(f"Status   : {meeting['status']}")
    print(f"Duration : {meeting['duration']}s")

    results = get_results(meeting_id)
    print(f"\nSummary  : {results['summary']}")
    print(f"Actions  : {results['action_items']}")
    print(f"Decisions: {results['key_decisions']}")

    segs = get_segments(meeting_id)
    print(f"\nSegments ({len(segs)} total):")
    for s in segs:
        print(f"  [{s['start_time']}s] {s['text']}")

    all_meetings = get_all_meetings()
    print(f"\nTotal meetings in DB: {len(all_meetings)}")

    # --- Step 7: Clean up test data ---
    delete_meeting(meeting_id)
    print(f"\nDeleted test meeting {meeting_id} — DB is clean.")


if __name__ == "__main__":
    test_full_pipeline()