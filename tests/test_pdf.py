import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.pdf_exporter import generate_pdf


def test_pdf_generation():
    """Generate a sample PDF and confirm the file is created."""

    fake_results = {
        "summary": (
            "The team held a Q3 planning meeting to discuss upcoming targets. "
            "John will lead the sales report, Sarah will review the budget, "
            "and the product launch has been moved to September."
        ),
        "action_items": [
            {"task": "Prepare Q3 sales report", "assignee": "John",  "deadline": "Friday"},
            {"task": "Review budget proposal",  "assignee": "Sarah", "deadline": "Wednesday"},
            {"task": "Set up project tool",     "assignee": "Mike",  "deadline": "Next week"},
        ],
        "key_decisions": [
            "Product launch postponed from August to September.",
            "Weekly check-ins every Monday at 10am.",
            "Budget increase approved for Q4 hiring.",
        ],
        "model_used": "gemini-2.5-flash",
        "transcript": "Good morning everyone. Let's get started...",
    }

    fake_segments = [
        {"start_time": 0.0,  "end_time": 4.0,  "text": "Good morning everyone."},
        {"start_time": 4.0,  "end_time": 10.0, "text": "John will prepare the Q3 sales report by Friday."},
        {"start_time": 10.0, "end_time": 18.0, "text": "Sarah needs to review the budget by Wednesday."},
        {"start_time": 18.0, "end_time": 26.0, "text": "We decided to postpone the product launch to September."},
        {"start_time": 26.0, "end_time": 34.0, "text": "Mike will set up the project tool by next week."},
    ]

    print("Generating test PDF...")
    pdf_path = generate_pdf(
        meeting_id=999,
        results=fake_results,
        segments=fake_segments,
        meeting_title="Q3 Planning Meeting (Test)",
    )

    # Verify file was created
    assert os.path.exists(pdf_path), "PDF file was not created!"
    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"PDF created successfully: {pdf_path}")
    print(f"File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    test_pdf_generation()