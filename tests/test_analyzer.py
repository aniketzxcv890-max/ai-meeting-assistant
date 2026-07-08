import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.analyzer import MeetingAnalyzer

# A realistic fake transcript to test with
SAMPLE_TRANSCRIPT = """
Good morning everyone. Let's get started with today's meeting.
First, John will prepare the Q3 sales report and send it to the team by Friday.
Sarah needs to review the updated budget proposal before Wednesday.
We also decided to postpone the product launch from August to September
to allow more time for testing.
Mike will set up the new project management tool by end of next week.
We agreed to hold weekly check-ins every Monday at 10am going forward.
That's all for today, thanks everyone.
"""

def test_analysis():
    analyzer = MeetingAnalyzer()
    result = analyzer.analyze(SAMPLE_TRANSCRIPT)

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(result.summary)

    print("\n" + "="*50)
    print("ACTION ITEMS")
    print("="*50)
    for i, item in enumerate(result.action_items, 1):
        print(f"{i}. Task     : {item.get('task')}")
        print(f"   Assignee : {item.get('assignee')}")
        print(f"   Deadline : {item.get('deadline')}")
        print()

    print("="*50)
    print("KEY DECISIONS")
    print("="*50)
    for i, decision in enumerate(result.key_decisions, 1):
        print(f"{i}. {decision}")

    print(f"\nModel used: {result.model_used}")

if __name__ == "__main__":
    test_analysis()