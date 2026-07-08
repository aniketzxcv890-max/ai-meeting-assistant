import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.transcriber import MeetingTranscriber


def test_transcription(audio_path: str):
    """Run a quick transcription test and print the result."""

    transcriber = MeetingTranscriber(model_size="base")
    result = transcriber.transcribe(audio_path)

    print("\n" + "="*50)
    print("TRANSCRIPTION RESULT")
    print("="*50)
    print(f"Language detected : {result.language}")
    print(f"Duration          : {result.duration:.1f} seconds")
    print(f"Segments found    : {len(result.segments)}")
    print("\nFull transcript:")
    print("-"*50)
    print(result.full_text)
    print("\nFirst 3 segments with timestamps:")
    print("-"*50)

    readable = transcriber.get_readable_segments(result)
    for seg in readable[:3]:
        print(f"[{seg['timestamp']}] {seg['text']}")


if __name__ == "__main__":
    # Pass your audio file path as a command-line argument
    # Example: python tests/test_transcriber.py data/uploads/my_meeting.mp3
    if len(sys.argv) < 2:
        print("Usage: python tests/test_transcriber.py <path_to_audio_file>")
        sys.exit(1)

    test_transcription(sys.argv[1])