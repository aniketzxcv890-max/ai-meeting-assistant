import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.db import init_db


# ── Colour helpers for terminal output ──────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def passed(name: str):
    print(f"  {GREEN}✅ PASS{RESET} — {name}")

def failed(name: str, error: str):
    print(f"  {RED}❌ FAIL{RESET} — {name}")
    print(f"         {YELLOW}{error}{RESET}")


# ── Individual test functions ────────────────────────────────────────────────
def test_env():
    """Check .env file and API key are present."""
    from app.core.config import config
    errors = config.validate()
    assert not errors, f"Config errors: {errors}"


def test_database():
    """Check DB initialises and basic CRUD works."""
    from app.database.db import (
        create_meeting, update_meeting_status,
        get_meeting_by_id, delete_meeting,
        save_results, get_results,
    )
    init_db()
    mid = create_meeting("Test Meeting", "test.mp3")
    assert mid > 0

    update_meeting_status(mid, "done", duration=60.0)
    meeting = get_meeting_by_id(mid)
    assert meeting["status"] == "done"

    save_results(
        meeting_id=mid,
        transcript="Test transcript.",
        summary="Test summary.",
        action_items=[{"task": "Do X", "assignee": "Alice", "deadline": "Friday"}],
        key_decisions=["Decision A"],
        model_used="gemini-2.5-flash",
    )
    results = get_results(mid)
    assert results["summary"] == "Test summary."
    assert isinstance(results["action_items"], list)

    delete_meeting(mid)
    assert get_meeting_by_id(mid) is None


def test_whisper_import():
    """Check Whisper is installed and importable."""
    import whisper
    # Just load the smallest model to confirm it works
    model = whisper.load_model("tiny")
    assert model is not None


def test_gemini_connection():
    """Check Gemini API key is valid with a minimal API call."""
    from app.core.analyzer import MeetingAnalyzer
    analyzer = MeetingAnalyzer()
    # Send the shortest possible prompt
    response = analyzer._call_llm("Reply with only the word: OK")
    assert len(response) > 0


def test_pdf_generation():
    """Check PDF file is created without errors."""
    from app.core.pdf_exporter import generate_pdf

    fake_results = {
        "summary": "Test summary.",
        "action_items": [{"task": "Task A", "assignee": "Bob", "deadline": "Monday"}],
        "key_decisions": ["Decision X"],
        "model_used": "gemini-2.5-flash",
        "transcript": "Test transcript text.",
    }
    fake_segments = [
        {"start_time": 0.0, "end_time": 3.0, "text": "Test transcript text."}
    ]
    pdf_path = generate_pdf(
        meeting_id=0,
        results=fake_results,
        segments=fake_segments,
        meeting_title="Test Meeting",
    )
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0

    # Clean up
    os.remove(pdf_path)


# ── Test runner ──────────────────────────────────────────────────────────────
TESTS = [
    ("Environment & config",  test_env),
    ("Database CRUD",         test_database),
    ("Whisper install",       test_whisper_import),
    ("Gemini API connection", test_gemini_connection),
    ("PDF generation",        test_pdf_generation),
]


def run_all():
    print("\n" + "="*55)
    print("  AI Meeting Assistant — Test Suite")
    print("="*55)

    results = []

    for name, test_fn in TESTS:
        try:
            test_fn()
            passed(name)
            results.append((name, True, None))
        except Exception as e:
            failed(name, str(e))
            results.append((name, False, str(e)))

    # Summary
    total   = len(results)
    passing = sum(1 for _, ok, _ in results if ok)
    failing = total - passing

    print("\n" + "-"*55)
    print(f"  Results: {GREEN}{passing} passed{RESET}  |  {RED}{failing} failed{RESET}  |  {total} total")
    print("="*55 + "\n")

    if failing > 0:
        sys.exit(1)   # non-zero exit = CI failure signal


if __name__ == "__main__":
    run_all()