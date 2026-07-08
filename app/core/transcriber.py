import whisper
import os
import time
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data structure for a single transcript segment (one sentence / phrase)
# ---------------------------------------------------------------------------
@dataclass
class TranscriptSegment:
    start_time: float   # seconds from beginning of audio
    end_time: float
    text: str


# ---------------------------------------------------------------------------
# Data structure for the full transcription result
# ---------------------------------------------------------------------------
@dataclass
class TranscriptionResult:
    full_text: str                      # Complete transcript as one string
    segments: list[TranscriptSegment]   # Per-sentence breakdown
    language: str                       # Detected language (e.g. "en")
    duration: float                     # Audio duration in seconds


# ---------------------------------------------------------------------------
# Main transcriber class
# ---------------------------------------------------------------------------
class MeetingTranscriber:
    """
    Wraps OpenAI Whisper to transcribe audio files.

    Usage:
        transcriber = MeetingTranscriber(model_size="base")
        result = transcriber.transcribe("path/to/audio.mp3")
        print(result.full_text)
    """

    VALID_MODELS = ["tiny", "base", "small", "medium", "large"]

    def __init__(self, model_size: str = "base"):
        """
        Load the Whisper model once when the class is created.

        Model size vs speed vs accuracy tradeoff:
          tiny   → fastest, least accurate  (good for testing)
          base   → good balance             (recommended for development)
          small  → better accuracy          (recommended for production)
          medium → high accuracy            (slower)
          large  → best accuracy            (requires good GPU)
        """
        if model_size not in self.VALID_MODELS:
            raise ValueError(f"model_size must be one of {self.VALID_MODELS}")

        print(f"Loading Whisper model: {model_size} ...")
        self.model = whisper.load_model(model_size)
        self.model_size = model_size
        print("Whisper model loaded.")


    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """
        Transcribe an audio file and return a structured result.

        Args:
            audio_path: Path to the audio file (mp3, wav, m4a, etc.)

        Returns:
            TranscriptionResult with full text, segments, language, duration

        Raises:
            FileNotFoundError: If the audio file doesn't exist
            RuntimeError: If transcription fails
        """
        # --- Validate the file exists ---
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
         # --- ADD THESE CHECKS ---
        # File size guard
        size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        if size_mb > 500:
            raise ValueError(f"File too large: {size_mb:.1f} MB. Maximum is 500 MB.")

            # Extension guard
        valid_extensions = {".mp3", ".wav", ".m4a", ".mp4", ".ogg", ".flac", ".webm"}
        ext = os.path.splitext(audio_path)[1].lower()
        if ext not in valid_extensions:
            raise ValueError(
                f"Unsupported file type: '{ext}'. "
                f"Supported: {', '.join(valid_extensions)}"
            )
        # --- END NEW CHECKS ---

        print(f"Transcribing: {audio_path} ({size_mb:.1f} MB)")
        start = time.time()

        try:
            # --- Run Whisper ---
            # fp16=False avoids a warning on machines without a GPU
            raw = self.model.transcribe(audio_path, fp16=False, verbose=False)

        except Exception as e:
            raise RuntimeError(f"Whisper transcription failed: {e}") from e

        elapsed = round(time.time() - start, 1)
        print(f"Transcription complete in {elapsed}s")

        # --- Parse segments ---
        segments = [
            TranscriptSegment(
                start_time=round(seg["start"], 2),
                end_time=round(seg["end"], 2),
                text=seg["text"].strip(),
            )
            for seg in raw.get("segments", [])
        ]

        # --- Calculate duration from last segment ---
        duration = segments[-1].end_time if segments else 0.0

        return TranscriptionResult(
            full_text=raw["text"].strip(),
            segments=segments,
            language=raw.get("language", "unknown"),
            duration=duration,
        )

    def format_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format for display."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def get_readable_segments(self, result: TranscriptionResult) -> list[dict]:
        """
        Convert segments into a list of dicts ready for display or saving.

        Returns list like:
            [{"timestamp": "00:05", "text": "Hello everyone..."}, ...]
        """
        return [
            {
                "timestamp": self.format_timestamp(seg.start_time),
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "text": seg.text,
            }
            for seg in result.segments
        ]